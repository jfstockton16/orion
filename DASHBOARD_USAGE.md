# Orion Dashboard - Control Interface

## Overview

The enhanced Orion Dashboard provides a comprehensive control interface for managing your arbitrage trading engine. You can monitor performance, adjust parameters, and control paper trading vs live trading modes.

## Features

### 🎮 Engine Control Panel
- **Engine Status**: Real-time indicator showing if the engine is running
- **Paper Trading Toggle**: Switch between paper trading (simulation) and live trading
- **Auto-Execute Toggle**: Enable/disable automatic trade execution
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
- Last update timestamp

This file is automatically created when you first toggle settings in the dashboard.

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

1. **Start Dashboard**: `streamlit run dashboard.py`
2. **Verify Settings**: Check the "Current Configuration" section
3. **Adjust If Needed**: Modify parameters in the expander and save
4. **Start Engine**: Run `python main.py` in another terminal (paper trading)
5. **Monitor**: Watch opportunities and trades in the dashboard
6. **Analyze**: Review performance metrics after some time
7. **Go Live**: When confident, enable auto-execute and run with `--auto-execute` flag

## Safety Reminder

Always understand the risks of algorithmic trading. Start with paper trading, use appropriate position sizes, and never risk more than you can afford to lose.
