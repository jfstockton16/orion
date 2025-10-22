"""Database repository for data access"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from src.database.models import (
    OpportunityLog, TradeLog, BalanceSnapshot, PerformanceMetrics
)
from src.arbitrage.detector import ArbitrageOpportunity
from src.execution.executor import ExecutionResult
from src.execution.capital_manager import PortfolioState
from src.utils.logger import setup_logger

logger = setup_logger("database")


class ArbitrageRepository:
    """Repository for arbitrage data access"""

    def __init__(self, session: Session):
        """
        Initialize repository

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def save_opportunity(self, opportunity: ArbitrageOpportunity, position_id: str) -> OpportunityLog:
        """
        Save arbitrage opportunity to database

        Args:
            opportunity: ArbitrageOpportunity object
            position_id: Unique position identifier

        Returns:
            OpportunityLog object
        """
        try:
            opp_log = OpportunityLog(
                position_id=position_id,
                kalshi_market_id=opportunity.kalshi_market_id,
                polymarket_market_id=opportunity.polymarket_market_id,
                question=opportunity.question,
                end_date=opportunity.end_date,
                similarity_score=opportunity.similarity_score,
                kalshi_yes_price=opportunity.kalshi_yes_price,
                polymarket_no_price=opportunity.polymarket_no_price,
                spread=opportunity.spread,
                edge=opportunity.edge,
                position_size_usd=opportunity.position_size_usd,
                kalshi_contracts=opportunity.kalshi_contracts,
                polymarket_size=opportunity.polymarket_size,
                expected_profit=opportunity.expected_profit,
                expected_roi=opportunity.expected_roi,
                total_fees=opportunity.total_fees,
                detected_at=opportunity.detected_at,
                metadata_json=opportunity.to_dict()
            )

            self.session.add(opp_log)
            self.session.commit()

            logger.debug(f"Saved opportunity {position_id} to database")
            return opp_log

        except Exception as e:
            logger.error(f"Error saving opportunity: {e}")
            self.session.rollback()
            raise

    def save_trade(self, result: ExecutionResult) -> TradeLog:
        """
        Save trade execution result

        Args:
            result: ExecutionResult object

        Returns:
            TradeLog object
        """
        try:
            trade_log = TradeLog(
                position_id=result.position_id,
                kalshi_order_id=result.kalshi_order_id,
                polymarket_order_id=result.polymarket_order_id,
                kalshi_filled=result.kalshi_filled,
                polymarket_filled=result.polymarket_filled,
                actual_cost=result.actual_cost,
                status='filled' if result.success else 'failed',
                success=result.success,
                error_message=result.error_message,
                filled_at=result.executed_at,
                metadata_json=result.to_dict()
            )

            self.session.add(trade_log)
            self.session.commit()

            # Update opportunity status
            self._update_opportunity_status(result.position_id, result.success)

            logger.debug(f"Saved trade {result.position_id} to database")
            return trade_log

        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            self.session.rollback()
            raise

    def _update_opportunity_status(self, position_id: str, success: bool) -> None:
        """
        Update opportunity status after execution

        Args:
            position_id: Position identifier
            success: Whether execution was successful
        """
        try:
            opp = self.session.query(OpportunityLog).filter_by(
                position_id=position_id
            ).first()

            if opp:
                opp.status = 'executed' if success else 'failed'
                opp.executed = success
                opp.executed_at = datetime.utcnow()
                self.session.commit()

        except Exception as e:
            logger.error(f"Error updating opportunity status: {e}")
            self.session.rollback()

    def close_position(self, position_id: str, pnl: float) -> None:
        """
        Mark position as closed and record P&L

        Args:
            position_id: Position identifier
            pnl: Realized profit/loss
        """
        try:
            trade = self.session.query(TradeLog).filter_by(
                position_id=position_id
            ).first()

            if trade:
                trade.status = 'closed'
                trade.closed_at = datetime.utcnow()
                trade.realized_pnl = pnl
                self.session.commit()

                logger.info(f"Closed position {position_id} with P&L: ${pnl:.2f}")

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            self.session.rollback()

    def save_balance_snapshot(self, portfolio: PortfolioState) -> BalanceSnapshot:
        """
        Save portfolio balance snapshot

        Args:
            portfolio: PortfolioState object

        Returns:
            BalanceSnapshot object
        """
        try:
            snapshot = BalanceSnapshot(
                kalshi_balance=portfolio.kalshi_balance,
                polymarket_balance=portfolio.polymarket_balance,
                total_balance=portfolio.total_balance,
                locked_capital=portfolio.locked_capital,
                open_positions=portfolio.open_positions,
                realized_pnl=portfolio.realized_pnl,
                unrealized_pnl=portfolio.unrealized_pnl,
                total_pnl=portfolio.total_pnl,
                daily_pnl=portfolio.daily_pnl,
                metadata_json=portfolio.to_dict()
            )

            self.session.add(snapshot)
            self.session.commit()

            logger.debug("Saved balance snapshot to database")
            return snapshot

        except Exception as e:
            logger.error(f"Error saving balance snapshot: {e}")
            self.session.rollback()
            raise

    def get_recent_opportunities(self, limit: int = 100) -> List[OpportunityLog]:
        """
        Get recent opportunities

        Args:
            limit: Maximum number to return

        Returns:
            List of OpportunityLog objects
        """
        return self.session.query(OpportunityLog).order_by(
            desc(OpportunityLog.detected_at)
        ).limit(limit).all()

    def get_open_positions(self) -> List[TradeLog]:
        """
        Get all open positions

        Returns:
            List of TradeLog objects
        """
        return self.session.query(TradeLog).filter(
            TradeLog.status.in_(['filled', 'partial'])
        ).all()

    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        Get performance summary for last N days

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with performance metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Count opportunities and trades
        opps = self.session.query(OpportunityLog).filter(
            OpportunityLog.detected_at >= cutoff
        ).all()

        trades = self.session.query(TradeLog).filter(
            TradeLog.created_at >= cutoff
        ).all()

        successful_trades = [t for t in trades if t.success]
        closed_trades = [t for t in trades if t.status == 'closed' and t.realized_pnl is not None]

        total_pnl = sum(t.realized_pnl for t in closed_trades)
        total_volume = sum(t.actual_cost for t in trades if t.actual_cost)

        return {
            'period_days': days,
            'opportunities_detected': len(opps),
            'trades_executed': len(trades),
            'trades_successful': len(successful_trades),
            'trades_closed': len(closed_trades),
            'total_pnl': total_pnl,
            'total_volume': total_volume,
            'win_rate': len(successful_trades) / len(trades) if trades else 0,
            'avg_profit': total_pnl / len(closed_trades) if closed_trades else 0
        }

    def get_latest_balance(self) -> Optional[BalanceSnapshot]:
        """
        Get most recent balance snapshot

        Returns:
            BalanceSnapshot object or None
        """
        return self.session.query(BalanceSnapshot).order_by(
            desc(BalanceSnapshot.snapshot_at)
        ).first()
