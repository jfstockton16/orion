"""Streamlit dashboard for live monitoring"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.models import init_database
from src.database.repository import ArbitrageRepository
from src.utils.config import get_config

# Page configuration
st.set_page_config(
    page_title="Orion Arbitrage Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric { font-size: 24px !important; font-weight: bold; }
    .profit { color: #00C853; }
    .loss { color: #D32F2F; }
    .neutral { color: #757575; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_session():
    """Get database session"""
    config = get_config()
    engine, Session = init_database(config.database_url)
    return Session()


def load_data(session: Session, days: int = 7):
    """Load data from database"""
    repo = ArbitrageRepository(session)

    # Get recent opportunities
    opportunities = repo.get_recent_opportunities(limit=1000)

    # Get open positions
    open_positions = repo.get_open_positions()

    # Get performance summary
    summary = repo.get_performance_summary(days=days)

    # Get latest balance
    latest_balance = repo.get_latest_balance()

    return {
        'opportunities': opportunities,
        'open_positions': open_positions,
        'summary': summary,
        'balance': latest_balance
    }


def main():
    """Main dashboard function"""

    st.title("💰 Orion Cross-Exchange Arbitrage Dashboard")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        days_lookback = st.slider("Days to display", 1, 30, 7)
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)

        st.markdown("---")
        st.header("About")
        st.info("""
        **Orion Arbitrage Engine**

        Cross-exchange arbitrage between:
        - Kalshi
        - Polymarket

        Real-time opportunity detection and automated execution.
        """)

    # Load data
    session = get_db_session()
    data = load_data(session, days=days_lookback)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    balance = data['balance']
    summary = data['summary']

    with col1:
        if balance:
            st.metric(
                "Total Balance",
                f"${balance.total_balance:,.2f}",
                delta=f"${balance.total_pnl:,.2f}",
                delta_color="normal"
            )
        else:
            st.metric("Total Balance", "$0.00")

    with col2:
        st.metric(
            "Open Positions",
            len(data['open_positions']),
            delta=None
        )

    with col3:
        total_pnl = summary.get('total_pnl', 0)
        pnl_color = "profit" if total_pnl >= 0 else "loss"
        st.metric(
            f"{days_lookback}d P&L",
            f"${total_pnl:,.2f}",
            delta=None
        )

    with col4:
        win_rate = summary.get('win_rate', 0) * 100
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta=None
        )

    st.markdown("---")

    # Account balances
    st.subheader("💳 Account Balances")

    if balance:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Kalshi", f"${balance.kalshi_balance:,.2f}")

        with col2:
            st.metric("Polymarket", f"${balance.polymarket_balance:,.2f}")

        with col3:
            st.metric("Locked Capital", f"${balance.locked_capital:,.2f}")

    st.markdown("---")

    # Performance chart
    st.subheader("📈 Performance Over Time")

    # Create sample time series (in production, query balance snapshots)
    if balance:
        # For demo purposes, create a simple chart
        dates = pd.date_range(
            end=datetime.now(),
            periods=days_lookback,
            freq='D'
        )
        balances = [100000 + i * 500 for i in range(days_lookback)]  # Dummy data

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=balances,
            mode='lines+markers',
            name='Total Balance',
            line=dict(color='#00C853', width=2)
        ))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Balance ($)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent opportunities
    st.subheader("🔍 Recent Arbitrage Opportunities")

    if data['opportunities']:
        opps_df = pd.DataFrame([{
            'Detected': opp.detected_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Question': opp.question[:60] + '...',
            'Edge': f"{opp.edge*100:.2f}%",
            'Size': f"${opp.position_size_usd:.2f}",
            'Expected Profit': f"${opp.expected_profit:.2f}",
            'Status': opp.status,
            'Spread': f"{opp.spread:.4f}"
        } for opp in data['opportunities'][:20]])

        st.dataframe(opps_df, use_container_width=True)
    else:
        st.info("No opportunities detected yet.")

    st.markdown("---")

    # Open positions
    st.subheader("📊 Open Positions")

    if data['open_positions']:
        positions_df = pd.DataFrame([{
            'Position ID': pos.position_id,
            'Status': pos.status,
            'Cost': f"${pos.actual_cost:.2f}" if pos.actual_cost else "N/A",
            'Kalshi Filled': '✅' if pos.kalshi_filled else '❌',
            'Poly Filled': '✅' if pos.polymarket_filled else '❌',
            'Created': pos.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for pos in data['open_positions']])

        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No open positions.")

    st.markdown("---")

    # Performance metrics
    st.subheader("📊 Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Trading Activity**")
        metrics_data = {
            'Opportunities Detected': summary.get('opportunities_detected', 0),
            'Trades Executed': summary.get('trades_executed', 0),
            'Trades Successful': summary.get('trades_successful', 0),
            'Trades Closed': summary.get('trades_closed', 0)
        }

        for metric, value in metrics_data.items():
            st.metric(metric, value)

    with col2:
        st.markdown("**Financial Metrics**")
        financial_data = {
            'Total Volume': f"${summary.get('total_volume', 0):,.2f}",
            'Total P&L': f"${summary.get('total_pnl', 0):,.2f}",
            'Average Profit': f"${summary.get('avg_profit', 0):,.2f}",
            'Win Rate': f"{summary.get('win_rate', 0)*100:.1f}%"
        }

        for metric, value in financial_data.items():
            st.markdown(f"**{metric}:** {value}")

    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()


if __name__ == "__main__":
    main()
