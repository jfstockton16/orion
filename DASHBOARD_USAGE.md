# Orion Dashboard - Control Interface

## Overview

The enhanced Orion Dashboard provides a comprehensive control interface for managing your arbitrage trading engine. You can monitor performance, adjust parameters, and control paper trading vs live trading modes.

**🔑 KEY FEATURE**: Paper trading and live trading data are completely separated! You can test strategies risk-free without impacting your live trading statistics.

## Features

### 🎮 Engine Control Panel
- **Engine Status**: Real-time indicator showing if the engine is running
- **Paper Trading Toggle**: Switch between paper trading (simulation) and live trading
  - **Data Separation**: Toggling between modes shows different data sets
  - **Paper mode**: Safe testing with simulated balance
  - **Live mode**: Real trading with actual exchange balances
- **Auto-Execute Toggle**: Enable/disable automatic trade execution
- **Paper Balance Input**: Set custom starting balance for paper trading (min $1,000, max $10M)
- **Control Instructions**: Clear guidance on how to start/stop the engine

### ⚙️ Trading Parameters
Adjust key trading parameters directly from the dashboard:

**Trading Thresholds:**
- Minimum Edge Required (%)
- Max Trade Size (% of bankroll)
- Min Trade Size (USD)
- Target Liquidity Depth (USD)
- Slippage Tolerance (%)

**Risk Management:**
- Max Open Positions
- Max Daily Loss (%)
- Market Polling Interval (seconds)

### 📋 Current Configuration Display
Quick view of active configuration including:
- Current trading settings
- Risk management parameters
- Execution mode (Paper/Live)
- Auto-execute status

### 📊 Performance Monitoring
- Total balance and P&L tracking
- Open positions count
- Win rate statistics
- Account balances by exchange
- Recent arbitrage opportunities
- Performance charts over time

## How to Use

### 1. Start the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### 2. Control the Trading Engine

**Paper Trading Mode (Default - Recommended for Testing):**
```bash
# In a separate terminal
python main.py
```

This runs the engine in paper trading mode (no real trades, just simulation).

**Live Trading Mode (Real Money):**
```bash
# Make sure you understand the risks!
python main.py --auto-execute
```

**Stop the Engine:**
Press `Ctrl+C` in the terminal running the engine.

### 3. Adjust Trading Parameters

1. Click to expand the "📊 Adjust Trading Parameters" section
2. Modify the parameters as needed
3. Click "💾 Save Parameters to config.yaml"
4. Restart the trading engine for changes to take effect

### 4. Toggle Paper Trading / Auto-Execute

Use the toggle switches in the Engine Control Panel:
- **Paper Trading Mode**: When ON, trades are simulated only
- **Auto-Execute Trades**: When ON, detected opportunities are executed automatically

Changes to these settings update both the runtime config and config.yaml.

## Configuration Files

### `config/config.yaml`
Main configuration file with all trading parameters. Modified when you save parameters from the dashboard.

### `config/runtime_config.json`
Runtime state file that tracks:
- Current paper trading mode
- Auto-execute status
- Engine running status
- Paper trading balance
- Last update timestamp

This file is automatically created when you first toggle settings in the dashboard.

## Paper vs Live Trading - Data Separation

### How It Works

All database records are tagged with a `trading_mode` field (`'paper'` or `'live'`):
- **Paper mode**: Uses simulated balance you set in the dashboard
- **Live mode**: Uses actual exchange balances

When you toggle between modes, the dashboard automatically filters all data:
- Opportunities detected
- Trades executed
- Balance snapshots
- Performance statistics
- P&L calculations

### Benefits

✅ **Test Risk-Free**: Try different strategies without real money
✅ **Separate Analytics**: Paper and live stats don't mix
✅ **Easy Switching**: Toggle in dashboard to view different data
✅ **Clean Transition**: When ready for live trading, your paper data stays intact for reference

### Database Migration

If you're upgrading from a previous version, run the migration script:

```bash
python migrate_database.py
```

This adds the `trading_mode` column to existing tables and marks all existing data as `'paper'` mode.

## Safety Features

1. **Paper Trading Default**: The system defaults to paper trading mode to prevent accidental real trades
2. **Explicit Live Trading**: You must explicitly enable live trading mode
3. **Parameter Validation**: All parameters have min/max bounds to prevent extreme configurations
4. **Auto-Refresh**: Dashboard refreshes every 30 seconds to show latest data

## Tips

1. **Always Test First**: Use paper trading mode to test your parameters before going live
2. **Monitor Performance**: Keep the dashboard open while the engine runs to monitor performance
3. **Start Conservative**: Begin with conservative parameters (higher min edge, lower trade sizes)
4. **Review Opportunities**: Check the "Recent Arbitrage Opportunities" table to see what the engine is detecting
5. **Watch Risk Metrics**: Keep an eye on your max daily loss and open positions limits

## Troubleshooting

**Dashboard won't start:**
- Make sure you've installed requirements: `pip install -r requirements.txt`
- Check that the config directory exists

**Changes not taking effect:**
- Remember to restart the trading engine after changing parameters
- Check that config.yaml was updated correctly

**No data showing:**
- The engine needs to run for a while to collect data
- Check that the database is initialized: The engine creates it on first run

**Engine status shows "Stopped":**
- This is normal if you haven't started the engine yet
- Start the engine with `python main.py` in a separate terminal
- The status indicator is informational only - it doesn't reflect real-time engine status

## Example Workflow

### Testing with Paper Trading

1. **Start Dashboard**: `streamlit run dashboard.py`
2. **Set Paper Balance**: Enter your desired test balance (e.g., $50,000)
3. **Verify Settings**: Check the "Current Configuration" section
4. **Ensure Paper Mode**: Verify "Paper Trading Mode" toggle is ON
5. **Adjust Parameters**: Fine-tune trading parameters and save
6. **Start Engine**: Run `python main.py --dry-run` in another terminal
7. **Monitor**: Watch the dashboard - you'll see "📝 PAPER MODE" badge
8. **Analyze**: Review paper trading performance over several days/weeks
9. **Iterate**: Adjust parameters based on paper results

### Going Live

1. **Review Paper Results**: Ensure satisfactory performance in paper mode
2. **Toggle to Live**: Switch "Paper Trading Mode" OFF in dashboard
3. **Warning Appears**: Dashboard shows "⚠️ LIVE TRADING MODE ACTIVE"
4. **Set Conservative Limits**: Start with small position sizes
5. **Enable Auto-Execute**: Toggle ON when ready
6. **Start Live Engine**: Run `python main.py` (without --dry-run)
7. **Monitor Closely**: Dashboard now shows "💵 LIVE MODE" badge
8. **Scale Gradually**: Increase limits as confidence grows

### Switching Between Modes

You can toggle between Paper and Live modes in the dashboard to view different data sets:
- Toggle ON = See paper trading data only
- Toggle OFF = See live trading data only

**Note**: The toggle only changes what data you're viewing. To actually change how the engine runs, you need to restart it with or without the `--dry-run` flag.

## Safety Reminder

Always understand the risks of algorithmic trading. Start with paper trading, use appropriate position sizes, and never risk more than you can afford to lose.
