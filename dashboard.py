"""Streamlit dashboard for live monitoring and control"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import os
import yaml
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


def load_runtime_config():
    """Load runtime configuration"""
    runtime_config_path = 'config/runtime_config.json'

    if os.path.exists(runtime_config_path):
        with open(runtime_config_path, 'r') as f:
            return json.load(f)

    # Default runtime config
    return {
        'paper_trading': True,
        'auto_execute': False,
        'engine_running': False,
        'paper_balance': 100000,  # Default paper trading balance
        'last_updated': None
    }


def save_runtime_config(config_data):
    """Save runtime configuration"""
    runtime_config_path = 'config/runtime_config.json'

    # Ensure config directory exists
    os.makedirs('config', exist_ok=True)

    config_data['last_updated'] = datetime.now().isoformat()

    with open(runtime_config_path, 'w') as f:
        json.dump(config_data, f, indent=2)


def load_trading_config():
    """Load trading parameters from config.yaml"""
    config_path = 'config/config.yaml'

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    return {}


def save_trading_config(config_data):
    """Save trading parameters to config.yaml"""
    config_path = 'config/config.yaml'

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


def load_data(session: Session, days: int = 7, trading_mode: str = 'paper'):
    """Load data from database filtered by trading mode"""
    repo = ArbitrageRepository(session)

    # Get recent opportunities for this mode
    opportunities = repo.get_recent_opportunities(limit=1000, trading_mode=trading_mode)

    # Get open positions for this mode
    open_positions = repo.get_open_positions(trading_mode=trading_mode)

    # Get performance summary for this mode
    summary = repo.get_performance_summary(days=days, trading_mode=trading_mode)

    # Get latest balance for this mode
    latest_balance = repo.get_latest_balance(trading_mode=trading_mode)

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

    # Load configurations
    runtime_config = load_runtime_config()
    trading_config = load_trading_config()

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

    # ========== ENGINE CONTROL PANEL ==========
    st.header("🎮 Engine Control Panel")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Engine status indicator
        engine_running = runtime_config.get('engine_running', False)
        status_color = "🟢" if engine_running else "🔴"
        st.markdown(f"### {status_color} Engine Status")
        st.markdown(f"**{'Running' if engine_running else 'Stopped'}**")

        if runtime_config.get('last_updated'):
            last_update = datetime.fromisoformat(runtime_config['last_updated'])
            st.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        # Paper trading toggle
        paper_trading = st.toggle(
            "Paper Trading Mode",
            value=runtime_config.get('paper_trading', True),
            help="Enable to simulate trades without real execution"
        )

        if paper_trading != runtime_config.get('paper_trading'):
            runtime_config['paper_trading'] = paper_trading
            save_runtime_config(runtime_config)
            st.success("✅ Paper trading mode updated!")
            st.rerun()

    with col3:
        # Auto-execute toggle
        auto_execute = st.toggle(
            "Auto-Execute Trades",
            value=runtime_config.get('auto_execute', False),
            help="Automatically execute detected opportunities"
        )

        if auto_execute != runtime_config.get('auto_execute'):
            runtime_config['auto_execute'] = auto_execute

            # Also update the config.yaml
            if 'trading' in trading_config:
                trading_config['trading']['auto_execute'] = auto_execute
                save_trading_config(trading_config)

            save_runtime_config(runtime_config)
            st.success("✅ Auto-execute setting updated!")
            st.rerun()

    # Paper Trading Balance Configuration
    if paper_trading:
        st.markdown("---")
        st.subheader("📝 Paper Trading Configuration")

        col1, col2 = st.columns([2, 1])

        with col1:
            paper_balance = st.number_input(
                "Paper Trading Starting Balance (USD)",
                min_value=1000,
                max_value=10000000,
                value=int(runtime_config.get('paper_balance', 100000)),
                step=5000,
                help="Starting balance for paper trading simulation"
            )

            if paper_balance != runtime_config.get('paper_balance'):
                runtime_config['paper_balance'] = paper_balance

                # Also update config.yaml for the engine
                if 'capital' in trading_config:
                    trading_config['capital']['initial_bankroll'] = paper_balance
                    save_trading_config(trading_config)

                save_runtime_config(runtime_config)
                st.success(f"✅ Paper trading balance set to ${paper_balance:,}")

        with col2:
            st.metric("Current Paper Balance", f"${paper_balance:,}")

        st.info("💡 **Tip**: Paper trading data is completely separate from live trading data. You can test strategies risk-free!")
    else:
        st.warning("⚠️ **LIVE TRADING MODE ACTIVE** - Real money will be used. Ensure you have proper risk management in place.")

    # Engine control instructions
    st.info("""
    **💡 How to Control the Engine:**

    1. **Start Engine**: Run `python main.py` (paper trading) or `python main.py --auto-execute` (live trading)
    2. **Stop Engine**: Press `Ctrl+C` in the terminal running the engine
    3. **Paper Trading**: Enabled by default - simulates trades without real execution
    4. **Auto-Execute**: When enabled, trades are executed automatically

    Note: Restart the engine after changing parameters below for changes to take effect.
    """)

    st.markdown("---")

    # ========== TRADING PARAMETERS ==========
    st.header("⚙️ Trading Parameters")

    with st.expander("📊 Adjust Trading Parameters", expanded=False):
        st.markdown("**Modify parameters below and click 'Save Parameters' to update config.yaml**")

        param_col1, param_col2 = st.columns(2)

        with param_col1:
            st.subheader("Trading Thresholds")

            threshold_spread = st.number_input(
                "Minimum Edge Required (%)",
                min_value=0.1,
                max_value=10.0,
                value=trading_config.get('trading', {}).get('threshold_spread', 0.01) * 100,
                step=0.1,
                help="Minimum profit margin required to consider a trade"
            ) / 100

            max_trade_size_pct = st.number_input(
                "Max Trade Size (% of bankroll)",
                min_value=1.0,
                max_value=20.0,
                value=trading_config.get('trading', {}).get('max_trade_size_pct', 0.05) * 100,
                step=0.5,
                help="Maximum percentage of bankroll to risk per trade"
            ) / 100

            min_trade_size_usd = st.number_input(
                "Min Trade Size (USD)",
                min_value=10,
                max_value=1000,
                value=int(trading_config.get('trading', {}).get('min_trade_size_usd', 100)),
                step=10,
                help="Minimum trade size in USD"
            )

            target_liquidity_depth = st.number_input(
                "Target Liquidity Depth (USD)",
                min_value=1000,
                max_value=50000,
                value=int(trading_config.get('trading', {}).get('target_liquidity_depth', 5000)),
                step=500,
                help="Minimum liquidity required per side"
            )

        with param_col2:
            st.subheader("Risk Management")

            max_open_positions = st.number_input(
                "Max Open Positions",
                min_value=1,
                max_value=50,
                value=int(trading_config.get('risk', {}).get('max_open_positions', 20)),
                step=1,
                help="Maximum number of concurrent positions"
            )

            max_daily_loss_pct = st.number_input(
                "Max Daily Loss (%)",
                min_value=1.0,
                max_value=20.0,
                value=trading_config.get('risk', {}).get('max_daily_loss_pct', 0.05) * 100,
                step=0.5,
                help="Stop trading if daily loss exceeds this percentage"
            ) / 100

            polling_interval = st.number_input(
                "Market Polling Interval (seconds)",
                min_value=10,
                max_value=300,
                value=int(trading_config.get('polling', {}).get('interval_sec', 30)),
                step=5,
                help="How often to check markets for opportunities"
            )

            slippage_tolerance = st.number_input(
                "Slippage Tolerance (%)",
                min_value=0.05,
                max_value=2.0,
                value=trading_config.get('trading', {}).get('slippage_tolerance', 0.002) * 100,
                step=0.05,
                help="Maximum acceptable slippage"
            ) / 100

        # Save button
        if st.button("💾 Save Parameters to config.yaml", type="primary"):
            # Update trading config
            if 'trading' not in trading_config:
                trading_config['trading'] = {}
            if 'risk' not in trading_config:
                trading_config['risk'] = {}
            if 'polling' not in trading_config:
                trading_config['polling'] = {}

            trading_config['trading']['threshold_spread'] = threshold_spread
            trading_config['trading']['max_trade_size_pct'] = max_trade_size_pct
            trading_config['trading']['min_trade_size_usd'] = min_trade_size_usd
            trading_config['trading']['target_liquidity_depth'] = target_liquidity_depth
            trading_config['trading']['slippage_tolerance'] = slippage_tolerance
            trading_config['risk']['max_open_positions'] = max_open_positions
            trading_config['risk']['max_daily_loss_pct'] = max_daily_loss_pct
            trading_config['polling']['interval_sec'] = polling_interval

            # Save to file
            save_trading_config(trading_config)

            st.success("✅ Parameters saved to config.yaml! Restart the engine for changes to take effect.")

    st.markdown("---")

    # Determine current trading mode
    current_mode = 'paper' if runtime_config.get('paper_trading', True) else 'live'

    # Load data filtered by trading mode
    session = get_db_session()
    data = load_data(session, days=days_lookback, trading_mode=current_mode)

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

    # Current Parameters Summary with Mode Indicator
    mode_badge = "📝 PAPER MODE" if current_mode == 'paper' else "💵 LIVE MODE"
    st.subheader(f"📋 Current Configuration - {mode_badge}")
    config_col1, config_col2, config_col3 = st.columns(3)

    with config_col1:
        st.markdown("**Trading Settings**")
        st.markdown(f"• Min Edge: {trading_config.get('trading', {}).get('threshold_spread', 0.01)*100:.1f}%")
        st.markdown(f"• Max Trade Size: {trading_config.get('trading', {}).get('max_trade_size_pct', 0.05)*100:.1f}%")
        st.markdown(f"• Min Trade: ${trading_config.get('trading', {}).get('min_trade_size_usd', 100):,.0f}")

    with config_col2:
        st.markdown("**Risk Management**")
        st.markdown(f"• Max Positions: {trading_config.get('risk', {}).get('max_open_positions', 20)}")
        st.markdown(f"• Max Daily Loss: {trading_config.get('risk', {}).get('max_daily_loss_pct', 0.05)*100:.1f}%")
        st.markdown(f"• Poll Interval: {trading_config.get('polling', {}).get('interval_sec', 30)}s")

    with config_col3:
        st.markdown("**Execution Mode**")
        mode_icon = "📝" if runtime_config.get('paper_trading', True) else "💵"
        mode_text = "Paper Trading" if runtime_config.get('paper_trading', True) else "Live Trading"
        st.markdown(f"• Mode: {mode_icon} {mode_text}")

        auto_icon = "✅" if runtime_config.get('auto_execute', False) else "⏸️"
        auto_text = "Enabled" if runtime_config.get('auto_execute', False) else "Disabled"
        st.markdown(f"• Auto-Execute: {auto_icon} {auto_text}")

        if current_mode == 'paper':
            st.markdown(f"• Paper Balance: ${runtime_config.get('paper_balance', 100000):,}")

    st.caption(f"**Data shown**: All statistics below are for **{mode_text}** only")

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
