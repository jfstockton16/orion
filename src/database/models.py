"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class OpportunityLog(Base):
    """Log of detected arbitrage opportunities"""

    __tablename__ = 'opportunities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(100), unique=True, nullable=False, index=True)

    # Market information
    kalshi_market_id = Column(String(100), nullable=False)
    polymarket_market_id = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    end_date = Column(String(50))
    similarity_score = Column(Float)

    # Pricing
    kalshi_yes_price = Column(Float, nullable=False)
    polymarket_no_price = Column(Float, nullable=False)
    spread = Column(Float, nullable=False)
    edge = Column(Float, nullable=False)

    # Position sizing
    position_size_usd = Column(Float, nullable=False)
    kalshi_contracts = Column(Integer)
    polymarket_size = Column(Float)

    # Expected returns
    expected_profit = Column(Float)
    expected_roi = Column(Float)

    # Fees
    total_fees = Column(Float)

    # Status
    status = Column(String(20), default='detected')  # detected, executing, executed, failed
    executed = Column(Boolean, default=False)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)

    # Additional metadata
    metadata_json = Column(JSON)

    def __repr__(self):
        return f"<Opportunity {self.position_id}: {self.question[:50]}>"


class TradeLog(Base):
    """Log of executed trades"""

    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(100), nullable=False, index=True)

    # Order IDs
    kalshi_order_id = Column(String(100))
    polymarket_order_id = Column(String(100))

    # Execution details
    kalshi_filled = Column(Boolean, default=False)
    polymarket_filled = Column(Boolean, default=False)
    actual_cost = Column(Float)

    # Status
    status = Column(String(20))  # pending, filled, partial, failed, closed
    success = Column(Boolean, default=False)

    # Error tracking
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    closed_at = Column(DateTime)

    # P&L (filled when position closes)
    realized_pnl = Column(Float)

    # Additional data
    metadata_json = Column(JSON)

    def __repr__(self):
        return f"<Trade {self.position_id}: {self.status}>"


class BalanceSnapshot(Base):
    """Periodic snapshots of account balances"""

    __tablename__ = 'balance_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Balances
    kalshi_balance = Column(Float, nullable=False)
    polymarket_balance = Column(Float, nullable=False)
    total_balance = Column(Float, nullable=False)

    # Allocations
    locked_capital = Column(Float, default=0.0)
    open_positions = Column(Integer, default=0)

    # P&L
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)

    # Timestamp
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional metadata
    metadata_json = Column(JSON)

    def __repr__(self):
        return f"<BalanceSnapshot ${self.total_balance:.2f} @ {self.snapshot_at}>"


class PerformanceMetrics(Base):
    """Daily/periodic performance metrics"""

    __tablename__ = 'performance_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Period
    period = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Trading metrics
    opportunities_detected = Column(Integer, default=0)
    trades_executed = Column(Integer, default=0)
    trades_successful = Column(Integer, default=0)
    trades_failed = Column(Integer, default=0)

    # Financial metrics
    total_volume = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    total_fees_paid = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)

    # Returns
    roi = Column(Float, default=0.0)
    annualized_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)

    # Win rate
    win_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)

    # Timestamp
    calculated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PerformanceMetrics {self.period} {self.period_start.date()}>"


def init_database(database_url: str = "sqlite:///data/arbitrage.db"):
    """
    Initialize database and create tables

    Args:
        database_url: SQLAlchemy database URL

    Returns:
        Tuple of (engine, Session)
    """
    # Create engine
    engine = create_engine(database_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    Session = sessionmaker(bind=engine)

    return engine, Session
