"""Arbitrage opportunity detection engine"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from src.utils.logger import setup_logger
from src.arbitrage.risk_analyzer import RiskAnalyzer, RiskAssessment, RiskLevel

logger = setup_logger("detector")


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""

    # Market information
    kalshi_market_id: str
    polymarket_market_id: str
    question: str
    end_date: Optional[str]

    # Pricing
    kalshi_yes_price: float
    polymarket_no_price: float
    spread: float  # P_yes(Kalshi) + P_no(Poly) - should be < 1
    edge: float  # 1 - spread (profit margin)

    # Sizing
    position_size_usd: float
    kalshi_contracts: int
    polymarket_size: float

    # Expected returns
    expected_profit: float
    expected_roi: float

    # Fees
    kalshi_fee: float
    polymarket_fee: float
    total_fees: float

    # Metadata
    detected_at: datetime
    similarity_score: float
    liquidity_kalshi: float
    liquidity_polymarket: float

    # Risk assessment
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    risk_warnings: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'kalshi_market_id': self.kalshi_market_id,
            'polymarket_market_id': self.polymarket_market_id,
            'question': self.question,
            'end_date': self.end_date,
            'kalshi_yes_price': self.kalshi_yes_price,
            'polymarket_no_price': self.polymarket_no_price,
            'spread': self.spread,
            'edge': self.edge,
            'position_size_usd': self.position_size_usd,
            'expected_profit': self.expected_profit,
            'expected_roi': self.expected_roi,
            'total_fees': self.total_fees,
            'detected_at': self.detected_at.isoformat(),
            'similarity_score': self.similarity_score,
        }


class ArbitrageDetector:
    """Detects arbitrage opportunities between exchanges"""

    def __init__(self, config: Dict):
        """
        Initialize arbitrage detector

        Args:
            config: Configuration dictionary
        """
        self.threshold_spread = config.get('trading', {}).get('threshold_spread', 0.01)
        self.min_trade_size = config.get('trading', {}).get('min_trade_size_usd', 100)
        self.max_trade_size_pct = config.get('trading', {}).get('max_trade_size_pct', 0.05)
        self.target_liquidity = config.get('trading', {}).get('target_liquidity_depth', 5000)

        self.kalshi_fee_pct = config.get('fees', {}).get('kalshi_fee_pct', 0.007)
        self.polymarket_fee_pct = config.get('fees', {}).get('polymarket_fee_pct', 0.02)
        self.gas_cost = config.get('fees', {}).get('blockchain_cost_usd', 5)

        # Initialize risk analyzer
        self.risk_analyzer = RiskAnalyzer(config)

    def calculate_spread(self, kalshi_yes: float, poly_no: float) -> float:
        """
        Calculate spread for arbitrage

        For a true arbitrage:
        - Buy YES on Kalshi at price P_yes
        - Buy NO on Polymarket at price P_no
        - If P_yes + P_no < 1.0, there's an arbitrage

        Args:
            kalshi_yes: YES price on Kalshi (0-1)
            poly_no: NO price on Polymarket (0-1)

        Returns:
            Spread value (lower is better)
        """
        return kalshi_yes + poly_no

    def calculate_edge(self, spread: float, fees: float = 0) -> float:
        """
        Calculate edge (profit margin) after fees

        Args:
            spread: Price spread
            fees: Total fees as percentage

        Returns:
            Edge value (higher is better)
        """
        return 1.0 - spread - fees

    def calculate_position_size(
        self,
        edge: float,
        bankroll: float,
        kelly_fraction: float = 0.25
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion

        Args:
            edge: Profit edge (0-1)
            bankroll: Available bankroll
            kelly_fraction: Fraction of Kelly to use (conservative)

        Returns:
            Position size in USD
        """
        # Full Kelly: f = edge / variance
        # For arbitrage, variance is low, so we use fractional Kelly
        # Limited by max_trade_size_pct

        max_size = bankroll * self.max_trade_size_pct
        kelly_size = bankroll * edge * kelly_fraction

        # Use smaller of Kelly size or max size
        size = min(kelly_size, max_size)

        # Ensure minimum trade size
        if size < self.min_trade_size:
            return 0  # Too small to trade

        return size

    def calculate_fees(self, position_size: float) -> Tuple[float, float, float]:
        """
        Calculate trading fees

        Args:
            position_size: Position size in USD

        Returns:
            Tuple of (kalshi_fee, polymarket_fee, total_fee)
        """
        kalshi_fee = position_size * self.kalshi_fee_pct
        polymarket_fee = position_size * self.polymarket_fee_pct + self.gas_cost

        total_fee = kalshi_fee + polymarket_fee

        return kalshi_fee, polymarket_fee, total_fee

    def detect_opportunity(
        self,
        kalshi_market: Dict,
        polymarket_market: Dict,
        kalshi_yes_price: float,
        polymarket_no_price: float,
        similarity_score: float,
        bankroll: float
    ) -> Optional[ArbitrageOpportunity]:
        """
        Detect and calculate arbitrage opportunity

        Args:
            kalshi_market: Kalshi market data
            polymarket_market: Polymarket market data
            kalshi_yes_price: YES price on Kalshi (0-1)
            polymarket_no_price: NO price on Polymarket (0-1)
            similarity_score: Market matching similarity
            bankroll: Available bankroll

        Returns:
            ArbitrageOpportunity object or None
        """
        # Calculate spread
        spread = self.calculate_spread(kalshi_yes_price, polymarket_no_price)

        # Calculate raw edge (before fees)
        raw_edge = 1.0 - spread

        # Check if spread meets threshold (before fees)
        if raw_edge < self.threshold_spread:
            return None

        # Perform risk assessment BEFORE sizing
        risk_assessment = self.risk_analyzer.analyze_opportunity(
            kalshi_market,
            polymarket_market,
            similarity_score,
            raw_edge,
            bankroll * self.max_trade_size_pct  # Max possible size
        )

        # Check if risk level is acceptable
        if not risk_assessment.should_execute():
            logger.warning(
                f"Opportunity rejected due to {risk_assessment.overall_risk.value} risk level. "
                f"Warnings: {'; '.join(risk_assessment.warnings)}"
            )
            return None

        # Calculate position size
        position_size = self.calculate_position_size(raw_edge, bankroll)

        # Adjust position size based on risk
        position_size *= risk_assessment.recommended_size_multiplier

        if position_size == 0:
            return None

        # Log risk warnings
        if risk_assessment.warnings:
            logger.warning(f"Risk warnings for this opportunity:")
            for warning in risk_assessment.warnings:
                logger.warning(f"  {warning}")

        # Calculate fees
        kalshi_fee, poly_fee, total_fees = self.calculate_fees(position_size)
        total_fee_pct = total_fees / position_size

        # Calculate edge after fees
        net_edge = raw_edge - total_fee_pct

        # If edge is negative after fees, not profitable
        if net_edge <= 0:
            logger.debug(
                f"Opportunity found but not profitable after fees: "
                f"raw_edge={raw_edge:.4f}, fees={total_fee_pct:.4f}, net_edge={net_edge:.4f}"
            )
            return None

        # Calculate expected profit
        expected_profit = position_size * net_edge
        expected_roi = net_edge  # As a percentage

        # Calculate contract sizes
        # Kalshi: contracts are binary (0 or 100 cents payout)
        kalshi_contracts = int(position_size / kalshi_yes_price)

        # Polymarket: size in USDC
        polymarket_size = position_size / polymarket_no_price

        # Check liquidity
        kalshi_liquidity = kalshi_market.get('liquidity', 0)
        poly_liquidity = polymarket_market.get('liquidity', 0)

        if kalshi_liquidity < self.target_liquidity or poly_liquidity < self.target_liquidity:
            logger.debug(
                f"Opportunity found but insufficient liquidity: "
                f"Kalshi={kalshi_liquidity}, Poly={poly_liquidity}"
            )
            return None

        # Calculate time-based metrics for capital efficiency
        days_to_resolution = None
        annualized_roi = None

        end_date = kalshi_market.get('end_date') or polymarket_market.get('end_date')
        if end_date:
            try:
                from datetime import datetime
                # Parse end date
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        end_dt = datetime.strptime(end_date.split('.')[0].replace('Z', ''), fmt)
                        days_to_resolution = (end_dt - datetime.now()).days
                        break
                    except ValueError:
                        continue

                # Calculate annualized ROI
                if days_to_resolution and days_to_resolution > 0:
                    annualized_roi = net_edge * (365.0 / days_to_resolution)
                else:
                    annualized_roi = net_edge
            except Exception:
                pass  # Keep as None if can't parse

        # Create opportunity with risk assessment
        opportunity = ArbitrageOpportunity(
            kalshi_market_id=kalshi_market.get('market_id'),
            polymarket_market_id=polymarket_market.get('market_id'),
            question=kalshi_market.get('question', ''),
            end_date=kalshi_market.get('end_date'),
            kalshi_yes_price=kalshi_yes_price,
            polymarket_no_price=polymarket_no_price,
            spread=spread,
            edge=net_edge,
            position_size_usd=position_size,
            kalshi_contracts=kalshi_contracts,
            polymarket_size=polymarket_size,
            expected_profit=expected_profit,
            expected_roi=expected_roi,
            kalshi_fee=kalshi_fee,
            polymarket_fee=poly_fee,
            total_fees=total_fees,
            detected_at=datetime.now(),
            similarity_score=similarity_score,
            liquidity_kalshi=kalshi_liquidity,
            liquidity_polymarket=poly_liquidity,
            risk_level=risk_assessment.overall_risk.value,
            risk_score=risk_assessment.risk_score,
            risk_warnings=risk_assessment.warnings,
            days_to_resolution=days_to_resolution,
            annualized_roi=annualized_roi
        )

        # Build log message
        log_msg = (
            f"ARBITRAGE OPPORTUNITY DETECTED!\n"
            f"  Question: {opportunity.question[:60]}...\n"
            f"  Spread: {spread:.4f} | Edge: {net_edge:.4f} ({net_edge*100:.2f}%)\n"
            f"  Position Size: ${position_size:.2f}\n"
            f"  Expected Profit: ${expected_profit:.2f}\n"
            f"  Kalshi YES: {kalshi_yes_price:.4f} | Poly NO: {polymarket_no_price:.4f}"
        )

        # Add time-based metrics if available
        if days_to_resolution is not None:
            log_msg += f"\n  Days to Resolution: {days_to_resolution}"
        if annualized_roi is not None:
            log_msg += f"\n  Annualized ROI: {annualized_roi*100:.1f}%"

        logger.info(log_msg)

        return opportunity

    def scan_opportunities(
        self,
        matched_markets: List[Tuple[Dict, Dict, float]],
        kalshi_prices: Dict[str, float],
        polymarket_prices: Dict[str, float],
        bankroll: float
    ) -> List[ArbitrageOpportunity]:
        """
        Scan for arbitrage opportunities across all matched markets

        Args:
            matched_markets: List of (kalshi_market, poly_market, similarity)
            kalshi_prices: Dict of market_id -> yes_price for Kalshi
            polymarket_prices: Dict of market_id -> no_price for Polymarket
            bankroll: Available bankroll

        Returns:
            List of ArbitrageOpportunity objects
        """
        opportunities = []

        for kalshi_market, poly_market, similarity in matched_markets:
            kalshi_id = kalshi_market.get('market_id')
            poly_id = poly_market.get('market_id')

            # Get prices
            kalshi_yes = kalshi_prices.get(kalshi_id)
            poly_no = polymarket_prices.get(poly_id)

            if kalshi_yes is None or poly_no is None:
                logger.debug(f"Missing prices for {kalshi_id} or {poly_id}")
                continue

            # Detect opportunity
            opp = self.detect_opportunity(
                kalshi_market,
                poly_market,
                kalshi_yes,
                poly_no,
                similarity,
                bankroll
            )

            if opp:
                opportunities.append(opp)

        # Sort by expected profit (descending)
        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)

        logger.info(f"Found {len(opportunities)} profitable arbitrage opportunities")

        return opportunities
