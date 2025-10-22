"""Risk analysis for arbitrage opportunities"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from src.utils.logger import setup_logger

logger = setup_logger("risk_analyzer")


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment for an arbitrage opportunity"""

    overall_risk: RiskLevel
    risk_factors: List[Dict[str, str]]
    warnings: List[str]
    score: float  # 0-1, higher = riskier
    recommended_size_multiplier: float  # Reduce position size by this factor

    def should_execute(self) -> bool:
        """Determine if trade should be executed given risk level"""
        return self.overall_risk in [RiskLevel.LOW, RiskLevel.MEDIUM]


class RiskAnalyzer:
    """Analyzes risks for arbitrage opportunities"""

    def __init__(self, config: Dict):
        """
        Initialize risk analyzer

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def analyze_opportunity(
        self,
        kalshi_market: Dict,
        polymarket_market: Dict,
        similarity_score: float,
        edge: float,
        position_size: float
    ) -> RiskAssessment:
        """
        Perform comprehensive risk analysis

        Args:
            kalshi_market: Kalshi market data
            polymarket_market: Polymarket market data
            similarity_score: Event matching similarity
            edge: Net edge after fees
            position_size: Proposed position size

        Returns:
            RiskAssessment object
        """
        risk_factors = []
        warnings = []
        risk_score = 0.0

        # 1. Event Definition Risk
        event_risk = self._analyze_event_definition_risk(
            kalshi_market,
            polymarket_market,
            similarity_score
        )
        risk_factors.extend(event_risk['factors'])
        warnings.extend(event_risk['warnings'])
        risk_score += event_risk['score']

        # 2. Resolution Timing Risk
        timing_risk = self._analyze_timing_risk(
            kalshi_market,
            polymarket_market
        )
        risk_factors.extend(timing_risk['factors'])
        warnings.extend(timing_risk['warnings'])
        risk_score += timing_risk['score']

        # 3. Liquidity Risk
        liquidity_risk = self._analyze_liquidity_risk(
            kalshi_market,
            polymarket_market,
            position_size
        )
        risk_factors.extend(liquidity_risk['factors'])
        warnings.extend(liquidity_risk['warnings'])
        risk_score += liquidity_risk['score']

        # 4. Edge Adequacy Risk
        edge_risk = self._analyze_edge_risk(edge)
        risk_factors.extend(edge_risk['factors'])
        warnings.extend(edge_risk['warnings'])
        risk_score += edge_risk['score']

        # 5. Regulatory Risk
        regulatory_risk = self._analyze_regulatory_risk(polymarket_market)
        risk_factors.extend(regulatory_risk['factors'])
        warnings.extend(regulatory_risk['warnings'])
        risk_score += regulatory_risk['score']

        # Determine overall risk level
        if risk_score >= 0.7:
            overall_risk = RiskLevel.CRITICAL
            size_multiplier = 0.1
        elif risk_score >= 0.5:
            overall_risk = RiskLevel.HIGH
            size_multiplier = 0.3
        elif risk_score >= 0.3:
            overall_risk = RiskLevel.MEDIUM
            size_multiplier = 0.7
        else:
            overall_risk = RiskLevel.LOW
            size_multiplier = 1.0

        return RiskAssessment(
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            warnings=warnings,
            score=risk_score,
            recommended_size_multiplier=size_multiplier
        )

    def _analyze_event_definition_risk(
        self,
        kalshi_market: Dict,
        polymarket_market: Dict,
        similarity_score: float
    ) -> Dict:
        """Analyze risk of event definition mismatch"""
        factors = []
        warnings = []
        score = 0.0

        kalshi_q = kalshi_market.get('question', '').lower()
        poly_q = polymarket_market.get('question', '').lower()

        # Check for key differences in wording
        risky_keywords = {
            'primary': 'general election vs primary',
            'general': 'general election vs primary',
            'runoff': 'runoff vs first round',
            'plurality': 'win condition differences',
            'majority': 'win condition differences',
            'at least': 'threshold differences',
            'more than': 'threshold differences',
            'by end of': 'timing ambiguity',
            'before': 'timing ambiguity'
        }

        for keyword, risk_type in risky_keywords.items():
            kalshi_has = keyword in kalshi_q
            poly_has = keyword in poly_q

            if kalshi_has != poly_has:
                factors.append({
                    'type': 'event_definition',
                    'severity': 'high',
                    'description': f'Keyword mismatch: "{keyword}" - {risk_type}'
                })
                warnings.append(
                    f'⚠️ Event definition risk: One market mentions "{keyword}", other does not'
                )
                score += 0.25

        # Low similarity score is a red flag
        if similarity_score < 0.90:
            factors.append({
                'type': 'event_definition',
                'severity': 'high',
                'description': f'Low similarity score: {similarity_score:.2f}'
            })
            warnings.append(
                f'⚠️ Markets may not be equivalent (similarity: {similarity_score:.2f})'
            )
            score += 0.3

        # Check description/subtitle for additional context
        kalshi_desc = kalshi_market.get('description', '').lower()
        poly_desc = polymarket_market.get('description', '').lower()

        if kalshi_desc and poly_desc:
            if 'primary' in kalshi_desc and 'general' in poly_desc:
                factors.append({
                    'type': 'event_definition',
                    'severity': 'critical',
                    'description': 'Primary vs General election mismatch'
                })
                warnings.append(
                    '🚨 CRITICAL: Markets appear to be for different elections (primary vs general)'
                )
                score += 0.5

        return {
            'factors': factors,
            'warnings': warnings,
            'score': min(score, 1.0)
        }

    def _analyze_timing_risk(
        self,
        kalshi_market: Dict,
        polymarket_market: Dict
    ) -> Dict:
        """Analyze resolution timing mismatch risk"""
        factors = []
        warnings = []
        score = 0.0

        kalshi_end = kalshi_market.get('end_date', '')
        poly_end = polymarket_market.get('end_date', '')

        # Check if end dates are significantly different
        # (In practice, you'd parse and compare actual dates)
        if kalshi_end and poly_end:
            if kalshi_end != poly_end:
                factors.append({
                    'type': 'timing',
                    'severity': 'medium',
                    'description': f'Different end dates: Kalshi {kalshi_end} vs Poly {poly_end}'
                })
                warnings.append(
                    f'⚠️ Resolution timing may differ: Kalshi {kalshi_end}, Poly {poly_end}'
                )
                score += 0.15

        # Check for early resolution risk
        kalshi_q = kalshi_market.get('question', '').lower()
        if 'by end of' in kalshi_q or 'before' in kalshi_q:
            factors.append({
                'type': 'timing',
                'severity': 'low',
                'description': 'Time-bounded question may resolve early'
            })
            score += 0.05

        return {
            'factors': factors,
            'warnings': warnings,
            'score': score
        }

    def _analyze_liquidity_risk(
        self,
        kalshi_market: Dict,
        polymarket_market: Dict,
        position_size: float
    ) -> Dict:
        """Analyze liquidity and slippage risk"""
        factors = []
        warnings = []
        score = 0.0

        kalshi_liq = kalshi_market.get('liquidity', 0)
        poly_liq = polymarket_market.get('liquidity', 0)

        # Check if position size is too large relative to liquidity
        min_liquidity_ratio = 0.1  # Position should be < 10% of liquidity

        if kalshi_liq > 0:
            kalshi_ratio = position_size / kalshi_liq
            if kalshi_ratio > min_liquidity_ratio:
                factors.append({
                    'type': 'liquidity',
                    'severity': 'high',
                    'description': f'Kalshi position {kalshi_ratio*100:.1f}% of liquidity'
                })
                warnings.append(
                    f'⚠️ High slippage risk on Kalshi: position is {kalshi_ratio*100:.1f}% of liquidity'
                )
                score += 0.2

        if poly_liq > 0:
            poly_ratio = position_size / poly_liq
            if poly_ratio > min_liquidity_ratio:
                factors.append({
                    'type': 'liquidity',
                    'severity': 'high',
                    'description': f'Polymarket position {poly_ratio*100:.1f}% of liquidity'
                })
                warnings.append(
                    f'⚠️ High slippage risk on Polymarket: position is {poly_ratio*100:.1f}% of liquidity'
                )
                score += 0.2

        return {
            'factors': factors,
            'warnings': warnings,
            'score': score
        }

    def _analyze_edge_risk(self, edge: float) -> Dict:
        """Analyze if edge is adequate given risks"""
        factors = []
        warnings = []
        score = 0.0

        # Very thin edges are risky
        if edge < 0.005:  # < 0.5%
            factors.append({
                'type': 'edge',
                'severity': 'high',
                'description': f'Very thin edge: {edge*100:.2f}%'
            })
            warnings.append(
                f'⚠️ Edge is very thin ({edge*100:.2f}%) - vulnerable to price movement'
            )
            score += 0.3
        elif edge < 0.01:  # < 1%
            factors.append({
                'type': 'edge',
                'severity': 'medium',
                'description': f'Thin edge: {edge*100:.2f}%'
            })
            warnings.append(
                f'⚠️ Edge is thin ({edge*100:.2f}%) - limited margin for error'
            )
            score += 0.15

        return {
            'factors': factors,
            'warnings': warnings,
            'score': score
        }

    def _analyze_regulatory_risk(self, polymarket_market: Dict) -> Dict:
        """Analyze regulatory compliance risks"""
        factors = []
        warnings = []
        score = 0.0

        # Polymarket has geographic restrictions for US users
        factors.append({
            'type': 'regulatory',
            'severity': 'medium',
            'description': 'Polymarket has restrictions for US users'
        })
        warnings.append(
            '⚠️ Ensure compliance with Polymarket geographic restrictions'
        )
        score += 0.1

        # Election markets may have additional restrictions
        poly_q = polymarket_market.get('question', '').lower()
        if any(word in poly_q for word in ['election', 'vote', 'campaign', 'political']):
            factors.append({
                'type': 'regulatory',
                'severity': 'medium',
                'description': 'Political prediction markets have regulatory scrutiny'
            })
            score += 0.05

        return {
            'factors': factors,
            'warnings': warnings,
            'score': score
        }
