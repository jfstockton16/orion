"""Capital and risk management"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger("capital")


@dataclass
class PortfolioState:
    """Current portfolio state"""

    # Balances
    kalshi_balance: float = 0.0
    polymarket_balance: float = 0.0
    total_balance: float = 0.0

    # Allocations
    kalshi_allocated: float = 0.0
    polymarket_allocated: float = 0.0

    # Open positions
    open_positions: int = 0
    locked_capital: float = 0.0

    # Performance
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0

    # Risk metrics
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'kalshi_balance': self.kalshi_balance,
            'polymarket_balance': self.polymarket_balance,
            'total_balance': self.total_balance,
            'kalshi_allocated': self.kalshi_allocated,
            'polymarket_allocated': self.polymarket_allocated,
            'open_positions': self.open_positions,
            'locked_capital': self.locked_capital,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'last_updated': self.last_updated.isoformat()
        }


class CapitalManager:
    """Manages capital allocation and risk"""

    def __init__(self, config: Dict):
        """
        Initialize capital manager

        Args:
            config: Configuration dictionary
        """
        self.initial_bankroll = config.get('capital', {}).get('initial_bankroll', 100000)
        self.kalshi_allocation_pct = config.get('capital', {}).get('kalshi_allocation_pct', 0.5)
        self.polymarket_allocation_pct = config.get('capital', {}).get('polymarket_allocation_pct', 0.5)
        self.reserve_pct = config.get('capital', {}).get('reserve_pct', 0.1)
        self.rebalance_threshold = config.get('capital', {}).get('rebalance_threshold', 0.15)

        self.max_open_positions = config.get('risk', {}).get('max_open_positions', 20)
        self.max_exposure_per_event = config.get('risk', {}).get('max_exposure_per_event', 0.10)
        self.max_daily_loss_pct = config.get('risk', {}).get('max_daily_loss_pct', 0.05)

        # Initialize portfolio state
        self.portfolio = PortfolioState(
            total_balance=self.initial_bankroll,
            kalshi_balance=self.initial_bankroll * self.kalshi_allocation_pct,
            polymarket_balance=self.initial_bankroll * self.polymarket_allocation_pct,
            kalshi_allocated=self.initial_bankroll * self.kalshi_allocation_pct,
            polymarket_allocated=self.initial_bankroll * self.polymarket_allocation_pct
        )

        # Position tracking
        self.positions: Dict[str, Dict] = {}
        self.daily_start_balance = self.initial_bankroll

    def get_available_capital(self) -> float:
        """
        Get available capital for new trades

        Returns:
            Available capital in USD
        """
        total = self.portfolio.total_balance
        locked = self.portfolio.locked_capital
        reserve = total * self.reserve_pct

        available = total - locked - reserve

        return max(0, available)

    def can_open_position(self, position_size: float) -> bool:
        """
        Check if we can open a new position

        Args:
            position_size: Proposed position size

        Returns:
            True if position can be opened
        """
        # Check position count limit
        if self.portfolio.open_positions >= self.max_open_positions:
            logger.warning(f"Max open positions reached: {self.max_open_positions}")
            return False

        # Check available capital
        available = self.get_available_capital()
        if position_size > available:
            logger.warning(
                f"Insufficient capital: need ${position_size:.2f}, "
                f"have ${available:.2f}"
            )
            return False

        # Check per-event exposure limit
        max_position = self.portfolio.total_balance * self.max_exposure_per_event
        if position_size > max_position:
            logger.warning(
                f"Position size ${position_size:.2f} exceeds "
                f"max per-event exposure ${max_position:.2f}"
            )
            return False

        # Check daily loss limit
        daily_loss_pct = abs(self.portfolio.daily_pnl) / self.daily_start_balance
        if daily_loss_pct >= self.max_daily_loss_pct:
            logger.error(
                f"Daily loss limit reached: {daily_loss_pct*100:.2f}% >= "
                f"{self.max_daily_loss_pct*100:.2f}%"
            )
            return False

        return True

    def allocate_capital(self, position_size: float, position_id: str) -> bool:
        """
        Allocate capital for a new position

        Args:
            position_size: Position size to allocate
            position_id: Unique position identifier

        Returns:
            True if allocation successful
        """
        if not self.can_open_position(position_size):
            return False

        # Lock capital
        self.portfolio.locked_capital += position_size
        self.portfolio.open_positions += 1

        # Track position
        self.positions[position_id] = {
            'size': position_size,
            'opened_at': datetime.now(),
            'status': 'open'
        }

        logger.info(
            f"Allocated ${position_size:.2f} for position {position_id}. "
            f"Locked: ${self.portfolio.locked_capital:.2f}, "
            f"Open positions: {self.portfolio.open_positions}"
        )

        return True

    def release_capital(
        self,
        position_id: str,
        pnl: float,
        position_size: Optional[float] = None
    ) -> None:
        """
        Release capital from a closed position

        Args:
            position_id: Position identifier
            pnl: Realized profit/loss
            position_size: Position size (if not tracked)
        """
        if position_id in self.positions:
            pos = self.positions[position_id]
            size = pos['size']
            pos['status'] = 'closed'
            pos['closed_at'] = datetime.now()
            pos['pnl'] = pnl
        else:
            size = position_size or 0

        # Release locked capital
        self.portfolio.locked_capital = max(0, self.portfolio.locked_capital - size)
        self.portfolio.open_positions = max(0, self.portfolio.open_positions - 1)

        # Update P&L
        self.portfolio.realized_pnl += pnl
        self.portfolio.total_pnl = self.portfolio.realized_pnl + self.portfolio.unrealized_pnl
        self.portfolio.daily_pnl += pnl

        # Update total balance
        self.portfolio.total_balance += pnl

        logger.info(
            f"Released ${size:.2f} from position {position_id}. "
            f"P&L: ${pnl:.2f}, Total P&L: ${self.portfolio.total_pnl:.2f}"
        )

    def update_balances(self, kalshi_balance: float, polymarket_balance: float) -> None:
        """
        Update account balances from exchanges

        Args:
            kalshi_balance: Current Kalshi balance
            polymarket_balance: Current Polymarket balance
        """
        self.portfolio.kalshi_balance = kalshi_balance
        self.portfolio.polymarket_balance = polymarket_balance
        self.portfolio.total_balance = kalshi_balance + polymarket_balance
        self.portfolio.last_updated = datetime.now()

        logger.debug(
            f"Balances updated: Kalshi=${kalshi_balance:.2f}, "
            f"Poly=${polymarket_balance:.2f}, Total=${self.portfolio.total_balance:.2f}"
        )

    def needs_rebalancing(self) -> bool:
        """
        Check if portfolio needs rebalancing

        Returns:
            True if rebalancing needed
        """
        if self.portfolio.total_balance == 0:
            return False

        # Calculate current allocation ratios
        kalshi_ratio = self.portfolio.kalshi_balance / self.portfolio.total_balance
        target_kalshi = self.kalshi_allocation_pct

        # Check drift from target
        drift = abs(kalshi_ratio - target_kalshi)

        return drift > self.rebalance_threshold

    def get_rebalance_amounts(self) -> Dict[str, float]:
        """
        Calculate rebalancing amounts

        Returns:
            Dictionary with transfer amounts
        """
        total = self.portfolio.total_balance

        target_kalshi = total * self.kalshi_allocation_pct
        target_poly = total * self.polymarket_allocation_pct

        current_kalshi = self.portfolio.kalshi_balance
        current_poly = self.portfolio.polymarket_balance

        # Calculate transfers needed
        kalshi_delta = target_kalshi - current_kalshi
        poly_delta = target_poly - current_poly

        return {
            'kalshi_delta': kalshi_delta,
            'polymarket_delta': poly_delta,
            'transfer_to_kalshi': kalshi_delta > 0,
            'transfer_amount': abs(kalshi_delta)
        }

    def reset_daily_metrics(self) -> None:
        """Reset daily metrics at start of new day"""
        self.daily_start_balance = self.portfolio.total_balance
        self.portfolio.daily_pnl = 0.0
        logger.info(f"Daily metrics reset. Starting balance: ${self.daily_start_balance:.2f}")

    def get_portfolio_state(self) -> PortfolioState:
        """Get current portfolio state"""
        return self.portfolio
