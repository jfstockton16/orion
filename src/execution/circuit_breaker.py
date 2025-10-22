"""Circuit breaker to halt trading on excessive losses"""

from datetime import datetime, timedelta
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger("circuit_breaker")


class TradingHaltException(Exception):
    """Exception raised when circuit breaker is triggered"""
    pass


class CircuitBreaker:
    """
    Circuit breaker that halts trading when loss limits are exceeded.

    This prevents runaway losses by monitoring P&L and triggering
    automatic trading halts.
    """

    def __init__(
        self,
        max_daily_loss_pct: float = 0.05,
        max_drawdown_pct: float = 0.15,
        reset_hour: int = 0
    ):
        """
        Initialize circuit breaker

        Args:
            max_daily_loss_pct: Maximum daily loss as percentage of starting balance (e.g., 0.05 = 5%)
            max_drawdown_pct: Maximum drawdown from peak (e.g., 0.15 = 15%)
            reset_hour: Hour to reset daily metrics (0-23, default: midnight)
        """
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.reset_hour = reset_hour

        # State variables
        self.daily_start_balance: Optional[float] = None
        self.daily_start_date: Optional[datetime] = None
        self.peak_balance: Optional[float] = None
        self.circuit_open = False
        self.halt_reason: Optional[str] = None

        # Statistics
        self.total_halts = 0
        self.last_halt_time: Optional[datetime] = None

    def check_breaker(self, current_balance: float, current_pnl: float = 0.0) -> None:
        """
        Check if circuit breaker should trigger

        Args:
            current_balance: Current account balance
            current_pnl: Current unrealized P&L (optional)

        Raises:
            TradingHaltException: If loss limits exceeded
        """
        if self.circuit_open:
            raise TradingHaltException(f"Trading halted: {self.halt_reason}")

        # Initialize on first check
        if self.daily_start_balance is None:
            self._reset_daily_metrics(current_balance)

        # Check if we need to reset daily metrics (new day)
        if self._should_reset_daily():
            logger.info("Resetting daily circuit breaker metrics")
            self._reset_daily_metrics(current_balance)

        # Update peak balance
        if self.peak_balance is None or current_balance > self.peak_balance:
            self.peak_balance = current_balance

        # Check daily loss limit
        daily_loss = self.daily_start_balance - current_balance
        daily_loss_pct = daily_loss / self.daily_start_balance if self.daily_start_balance > 0 else 0

        if daily_loss_pct >= self.max_daily_loss_pct:
            self._trigger_circuit_breaker(
                f"Daily loss limit exceeded: {daily_loss_pct*100:.2f}% "
                f"(max: {self.max_daily_loss_pct*100:.2f}%)"
            )

        # Check drawdown from peak
        if self.peak_balance and self.peak_balance > 0:
            drawdown = (self.peak_balance - current_balance) / self.peak_balance

            if drawdown >= self.max_drawdown_pct:
                self._trigger_circuit_breaker(
                    f"Maximum drawdown exceeded: {drawdown*100:.2f}% "
                    f"(max: {self.max_drawdown_pct*100:.2f}%)"
                )

    def _trigger_circuit_breaker(self, reason: str) -> None:
        """
        Trigger the circuit breaker

        Args:
            reason: Reason for triggering

        Raises:
            TradingHaltException: Always raised
        """
        self.circuit_open = True
        self.halt_reason = reason
        self.total_halts += 1
        self.last_halt_time = datetime.now()

        logger.error(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
        logger.error("🛑 ALL TRADING HALTED - Manual intervention required")

        raise TradingHaltException(reason)

    def _should_reset_daily(self) -> bool:
        """
        Check if daily metrics should be reset

        Returns:
            True if new trading day
        """
        if self.daily_start_date is None:
            return True

        now = datetime.now()

        # Check if we've passed the reset hour
        if now.date() > self.daily_start_date.date():
            # New day
            return True

        if now.date() == self.daily_start_date.date():
            # Same day - check if we've passed reset hour
            if self.daily_start_date.hour < self.reset_hour <= now.hour:
                return True

        return False

    def _reset_daily_metrics(self, current_balance: float) -> None:
        """
        Reset daily tracking metrics

        Args:
            current_balance: Current balance to use as new baseline
        """
        self.daily_start_balance = current_balance
        self.daily_start_date = datetime.now()

        logger.info(
            f"Daily metrics reset - Starting balance: ${current_balance:,.2f}"
        )

    def manual_reset(self) -> None:
        """
        Manually reset circuit breaker (use with caution!)

        This should only be called after investigating the cause of the halt
        and implementing fixes.
        """
        logger.warning("⚠️  Manual circuit breaker reset requested")

        if self.circuit_open:
            logger.warning(
                f"Resetting circuit breaker (was halted: {self.halt_reason})"
            )

        self.circuit_open = False
        self.halt_reason = None

        logger.info("✅ Circuit breaker reset - Trading resumed")

    def get_status(self) -> dict:
        """
        Get current circuit breaker status

        Returns:
            Dictionary with circuit breaker status
        """
        daily_loss_pct = 0.0
        drawdown_pct = 0.0

        if self.daily_start_balance and self.daily_start_balance > 0:
            if hasattr(self, '_current_balance'):
                daily_loss = self.daily_start_balance - self._current_balance
                daily_loss_pct = daily_loss / self.daily_start_balance

        if self.peak_balance and self.peak_balance > 0:
            if hasattr(self, '_current_balance'):
                drawdown_pct = (self.peak_balance - self._current_balance) / self.peak_balance

        return {
            'circuit_open': self.circuit_open,
            'halt_reason': self.halt_reason,
            'daily_start_balance': self.daily_start_balance,
            'peak_balance': self.peak_balance,
            'daily_loss_pct': daily_loss_pct,
            'drawdown_pct': drawdown_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'total_halts': self.total_halts,
            'last_halt_time': self.last_halt_time.isoformat() if self.last_halt_time else None
        }

    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed

        Returns:
            True if circuit breaker is closed (trading allowed)
        """
        return not self.circuit_open
