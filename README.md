# 💰 Orion Cross-Exchange Arbitrage Engine

**Production-ready** automated arbitrage bot for prediction markets, detecting and executing profitable opportunities between **Kalshi** and **Polymarket**.

> ⚠️ **IMPORTANT**: This bot trades real money. Read the [Production Setup Guide](PRODUCTION_SETUP.md) and [Security Policy](SECURITY.md) before deployment.

## 🎯 Features

### Core Trading
- **Real-time Market Monitoring**: Continuously scans Kalshi and Polymarket for matching events
- **Intelligent Event Matching**: Fuzzy matching algorithm to identify equivalent markets across exchanges
- **Automated Execution**: Execute both legs of arbitrage trades simultaneously
- **Capital Management**: Automatic bankroll allocation and rebalancing
- **Live Dashboard**: Real-time monitoring via Streamlit web interface
- **Alert System**: Telegram notifications for opportunities and executions
- **Complete Audit Trail**: SQLite database logging all transactions

### 🔒 Security Features (NEW)
- **🔐 Encrypted Credential Storage**: AES-256 encryption for API keys and private keys (NEVER plain text!)
- **✅ Input Validation**: Comprehensive validation prevents injection attacks
- **🔒 No Known Vulnerabilities**: All dependencies updated with latest security patches
- **📝 Audit Logging**: Complete trail of all operations
- **🛡️ Secure by Default**: Encrypted credentials required for production use

### 💰 Financial Safety (NEW)
- **🚨 Circuit Breaker**: Automatic trading halt on excessive losses (5% daily limit)
- **⚖️ Partial Fill Protection**: Automatic position unwinding prevents naked exposure
- **📊 Order Verification**: Real-time order status checking from exchanges
- **🎯 Position Limits**: Configurable exposure limits per event and overall
- **⏸️ Manual Kill Switch**: Emergency stop procedures documented

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Orion Arbitrage Engine                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Kalshi     │◄────►│  Polymarket  │               │
│  │  API Client  │      │  API Client  │               │
│  └──────┬───────┘      └──────┬───────┘               │
│         │                     │                        │
│         └──────────┬──────────┘                        │
│                    │                                   │
│         ┌──────────▼──────────┐                        │
│         │  Event Matcher      │                        │
│         │  (Fuzzy Matching)   │                        │
│         └──────────┬──────────┘                        │
│                    │                                   │
│         ┌──────────▼──────────┐                        │
│         │ Arbitrage Detector  │                        │
│         │ (Spread Calculation)│                        │
│         └──────────┬──────────┘                        │
│                    │                                   │
│         ┌──────────▼──────────┐                        │
│         │  Capital Manager    │                        │
│         │  (Risk Management)  │                        │
│         └──────────┬──────────┘                        │
│                    │                                   │
│         ┌──────────▼──────────┐                        │
│         │  Trade Executor     │                        │
│         │  (Order Placement)  │                        │
│         └──────────┬──────────┘                        │
│                    │                                   │
│    ┌───────────────┼───────────────┐                  │
│    │               │               │                  │
│    ▼               ▼               ▼                  │
│ ┌────────┐   ┌──────────┐   ┌──────────┐             │
│ │Database│   │Dashboard │   │ Telegram │             │
│ │ (SQLite│   │(Streamlit│   │  Alerts  │             │
│ └────────┘   └──────────┘   └──────────┘             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Kalshi API credentials (API key + secret)
- Polymarket wallet (private key)
- Telegram bot (optional, for alerts)

## 🚀 Quick Start

> **📖 For detailed setup instructions, see [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)**

### 1. Clone and Install

```bash
git clone <repository-url>
cd orion
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 🔐 Encrypt Your Credentials (REQUIRED)

**CRITICAL**: Never use plain text credentials! Use the encryption utility:

```bash
python -m src.utils.secrets_manager
```

Follow the prompts to encrypt:
- Kalshi API Key & Secret
- Polymarket Private Key & API Key
- Telegram credentials (optional)

The utility will output encrypted values for your `.env` file.

### 3. Configure Environment

```bash
cp .env.example .env
nano .env  # Add encrypted credentials from step 2
```

Your `.env` should look like:
```bash
# Master password (store securely in password manager!)
MASTER_PASSWORD=your_strong_master_password

# Encrypted credentials (from encryption utility)
KALSHI_API_KEY_ENCRYPTED=gAAAAABl...
KALSHI_API_SECRET_ENCRYPTED=gAAAAABl...
POLYMARKET_PRIVATE_KEY_ENCRYPTED=gAAAAABl...
POLYMARKET_API_KEY_ENCRYPTED=gAAAAABl...

# Database
DATABASE_URL=sqlite:///data/arbitrage.db
```

### 4. Initialize Database

```bash
python main.py --init-db
```

### 5. Test in Dry-Run Mode (24+ hours recommended)

Test without executing real trades:

```bash
python main.py --dry-run
```

Monitor logs: `tail -f logs/arbitrage.log`

### 6. Alert-Only Mode (3-7 days recommended)

Detect opportunities but don't execute:

```yaml
# config/config.yaml
trading:
  auto_execute: false  # Keep false!
```

```bash
python main.py
```

### 7. Enable Live Trading (Use Extreme Caution)

**⚠️ WARNING: This will execute real trades with real money!**

```yaml
# config/config.yaml - Start VERY conservative
trading:
  auto_execute: true
  max_trade_size_pct: 0.02   # 2% max per trade
  threshold_spread: 0.015     # 1.5% minimum edge

risk:
  max_open_positions: 5        # Very conservative
  max_daily_loss_pct: 0.03     # 3% circuit breaker
```

```bash
python main.py
# You'll get a 5-second warning before trading starts
```

### 8. Launch Dashboard (Recommended)

```bash
streamlit run dashboard.py
```

Access at: http://localhost:8501

**NEW**: The dashboard now includes a full **Control Interface** for managing the engine! See [DASHBOARD_USAGE.md](DASHBOARD_USAGE.md) for details.

## ⚙️ Configuration

Edit `config/config.yaml` to customize behavior:

### Trading Parameters

```yaml
trading:
  threshold_spread: 0.01          # Min 1% edge required
  max_trade_size_pct: 0.05        # Max 5% per trade
  min_trade_size_usd: 100
  target_liquidity_depth: 5000
  slippage_tolerance: 0.002
  auto_execute: false             # Set true for live trading
```

### Capital Management

```yaml
capital:
  initial_bankroll: 100000
  kalshi_allocation_pct: 0.50
  polymarket_allocation_pct: 0.50
  reserve_pct: 0.10
  rebalance_interval_hr: 4
```

### Risk Management

```yaml
risk:
  max_open_positions: 20
  max_exposure_per_event: 0.10    # Max 10% per event
  max_daily_loss_pct: 0.05        # Stop at 5% daily loss
```

## 🖥️ Command-Line Usage

```bash
# Run with custom config
python main.py --config my_config.yaml

# Override spread threshold
python main.py --threshold 0.02

# Set log level
python main.py --log-level DEBUG

# Enable auto-execution
python main.py --auto-execute true

# Dry-run mode (simulate trades)
python main.py --dry-run
```

## 📊 Dashboard Features

The Streamlit dashboard provides:

### Monitoring (Original)
- **Real-time Balance**: View Kalshi, Polymarket, and total balances
- **Open Positions**: Monitor active arbitrage positions
- **Opportunity Feed**: Recent detected opportunities
- **Performance Metrics**: P&L, win rate, volume
- **Performance Charts**: Balance over time
- **Auto-refresh**: Updates every 30 seconds

### 🎮 Control Interface (NEW)
- **Engine Status Indicator**: See if the engine is running (visual indicator)
- **Paper Trading Toggle**: Switch between simulation and live trading modes
- **Auto-Execute Toggle**: Enable/disable automatic trade execution
- **Parameter Editor**: Adjust trading parameters in real-time
  - Trading thresholds (min edge, trade sizes, liquidity)
  - Risk management (max positions, daily loss limits, polling interval)
- **Save Configuration**: Update config.yaml directly from the dashboard
- **Current Configuration Display**: Quick view of active settings
- **Control Instructions**: Built-in guide for starting/stopping the engine

> **📖 For complete dashboard usage guide, see [DASHBOARD_USAGE.md](DASHBOARD_USAGE.md)**

## 🔔 Alerts

Configure Telegram alerts to receive:

- New arbitrage opportunities (> threshold)
- Trade execution confirmations
- Error notifications
- Daily performance summaries

### Setting Up Telegram

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add credentials to `.env`

## 📁 Project Structure

```
orion/
├── src/
│   ├── api/                       # Exchange API clients
│   │   ├── kalshi_client.py       # Kalshi REST API
│   │   └── polymarket_client.py   # Polymarket CLOB API
│   ├── arbitrage/                 # Core arbitrage logic
│   │   ├── matcher.py             # Event matching
│   │   ├── detector.py            # Opportunity detection
│   │   └── risk_analyzer.py       # Risk assessment
│   ├── execution/                 # Trade execution
│   │   ├── executor.py            # Order placement
│   │   ├── capital_manager.py     # Capital & risk mgmt
│   │   └── circuit_breaker.py     # 🆕 Loss protection
│   ├── database/                  # Data persistence
│   │   ├── models.py              # SQLAlchemy models
│   │   └── repository.py          # Data access layer
│   ├── monitoring/                # Alerts & monitoring
│   │   └── alerts.py
│   ├── utils/                     # Utilities
│   │   ├── config.py              # Configuration
│   │   ├── logger.py              # Logging
│   │   ├── secrets_manager.py     # 🆕 Credential encryption
│   │   └── validation.py          # 🆕 Input validation
│   └── engine.py                  # Main orchestrator
├── config/
│   └── config.yaml                # Configuration
├── docs/                          # 🆕 Documentation
│   ├── CAPITAL_VELOCITY_GUIDE.md  # Compounding strategy
│   ├── CUOMO_TRADE_ANALYSIS.md    # Real trade example
│   └── RISK_GUIDE.md              # Risk framework
├── data/                          # SQLite database
├── logs/                          # Log files
├── tests/                         # Unit tests
├── main.py                        # CLI entry point
├── dashboard.py                   # Streamlit dashboard with controls
├── DASHBOARD_USAGE.md             # 🆕 Dashboard control guide
├── requirements.txt               # Dependencies
├── pyproject.toml                 # 🆕 Modern Python packaging
├── Dockerfile                     # Docker image
├── PRODUCTION_SETUP.md            # 🆕 Production deployment guide
├── SECURITY.md                    # 🆕 Security policy
├── PRODUCTION_READY_CHANGES.md    # 🆕 Technical audit report
└── README.md                      # This file
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t orion-arbitrage .
```

### Run Container

```bash
docker run -d \
  --name orion \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -p 8501:8501 \
  orion-arbitrage
```

### Docker Compose

```yaml
version: '3.8'
services:
  orion:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8501:8501"
    restart: unless-stopped
```

## 🧪 Testing

Run unit tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## 📈 Performance Metrics

The bot tracks:

- **Total P&L**: Cumulative profit/loss
- **Win Rate**: Percentage of profitable trades
- **ROI**: Return on investment
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Volume**: Total capital deployed

## ⚠️ Risk Warnings

1. **Market Risk**: Prediction market outcomes are uncertain
2. **Execution Risk**: Orders may not fill at expected prices
3. **Counterparty Risk**: Exchange solvency and operational risks
4. **Regulatory Risk**: Ensure compliance with local laws
5. **Technical Risk**: Bugs, API changes, network issues

**USE AT YOUR OWN RISK**. This software is provided as-is with no guarantees.

## 🔒 Security Features & Best Practices

### Built-In Security Controls

✅ **Encrypted Credentials** - AES-256 encryption for all API keys and private keys
✅ **Input Validation** - Comprehensive validation prevents injection attacks
✅ **Circuit Breaker** - Automatic trading halt on excessive losses
✅ **Partial Fill Protection** - Automatic position unwinding
✅ **Audit Logging** - Complete trail of all operations
✅ **Updated Dependencies** - No known security vulnerabilities

### Required Security Practices

1. **🔐 Always Use Encrypted Credentials**
   ```bash
   # Use the encryption utility (REQUIRED)
   python -m src.utils.secrets_manager
   # NEVER put plain text credentials in .env
   ```

2. **🔑 Master Password Security**
   - Use 20+ character password
   - Store in password manager (1Password, Bitwarden, etc.)
   - Never commit to version control
   - Rotate monthly

3. **🔄 Regular Maintenance**
   - Rotate API keys monthly
   - Update dependencies weekly: `pip install --upgrade -r requirements.txt`
   - Review logs daily: `grep ERROR logs/arbitrage.log`
   - Backup database regularly

4. **🛡️ Defense in Depth**
   - Enable 2FA on exchange accounts
   - Use separate wallets for trading (Polymarket)
   - Run on secure network (VPN recommended)
   - Monitor for suspicious activity

5. **📊 Start Conservative**
   - Begin with dry-run mode (24+ hours)
   - Then alert-only mode (3-7 days)
   - Start with small position sizes (2-3%)
   - Gradually scale up if profitable

> **📖 For complete security documentation, see [SECURITY.md](SECURITY.md)**

## ✅ Production Ready Status

**Version 1.0.0** - Production Ready as of October 2025

### Recent Security Improvements

This engine has undergone a comprehensive security audit and received major upgrades:

✅ **Critical Security Fixes**
- Encrypted credential storage (AES-256)
- Input validation across all API calls
- Updated all vulnerable dependencies
- Comprehensive audit logging

✅ **Financial Safety Features**
- Circuit breaker for loss protection
- Partial fill unwinding (prevents naked exposure)
- Real-time order status verification
- Configurable position limits

✅ **Production Documentation**
- [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) - Complete deployment guide
- [SECURITY.md](SECURITY.md) - Security policy and best practices
- [PRODUCTION_READY_CHANGES.md](PRODUCTION_READY_CHANGES.md) - Technical audit report

**Risk Assessment**: 🟢 LOW (with conservative settings)

**Deployment Recommendation**: Start with dry-run → alert-only → conservative live trading

> **📊 See [PRODUCTION_READY_CHANGES.md](PRODUCTION_READY_CHANGES.md) for the complete technical audit report and all improvements made.**

---

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Support

For issues and questions:

- **Production Setup**: See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)
- **Security Issues**: See [SECURITY.md](SECURITY.md)
- **GitHub Issues**: [repository/issues]
- **Documentation**: See `docs/` folder

## 🗺️ Roadmap

- [x] Web-based configuration UI (Dashboard control interface)
- [ ] Add more exchanges (Insight, Manifold)
- [ ] Machine learning for spread prediction
- [ ] Advanced position hedging strategies
- [ ] Portfolio optimization (maximize Sharpe)
- [ ] Market-making mode
- [ ] Historical backtesting engine
- [ ] Real-time engine start/stop from dashboard

## 📊 Example Output

```
==========================================================================
  💰 ORION CROSS-EXCHANGE ARBITRAGE ENGINE
==========================================================================
  Mode: LIVE TRADING
  Auto-Execute: True
  Threshold: 1.00%
  Poll Interval: 30s
==========================================================================

2024-01-15 10:30:45 - INFO - Arbitrage Engine initialized
2024-01-15 10:30:46 - INFO - Kalshi authentication successful
2024-01-15 10:30:46 - INFO - Starting main loop

2024-01-15 10:31:15 - INFO - Fetched 87 Kalshi markets, 124 Polymarket markets
2024-01-15 10:31:16 - INFO - Found 12 matching market pairs

2024-01-15 10:31:18 - INFO - ARBITRAGE OPPORTUNITY DETECTED!
  Question: Will the Fed raise rates in March 2024?
  Spread: 0.9850 | Edge: 1.50%
  Position Size: $2,500.00
  Expected Profit: $37.50
  Kalshi YES: 0.4900 | Poly NO: 0.4950

2024-01-15 10:31:20 - INFO - Successfully executed arb_1705318280_FEDRATE
```

## 🎓 How It Works

### Arbitrage Strategy

The bot exploits price discrepancies by:

1. **Buying YES on Kalshi** at price P_yes
2. **Buying NO on Polymarket** at price P_no

If `P_yes + P_no < 1.0`, you have a guaranteed profit when the market resolves.

**Example**:
- Kalshi YES: $0.48
- Polymarket NO: $0.51
- Total cost: $0.99
- Payout: $1.00
- **Risk-free profit: $0.01 (1%)**

### Position Sizing

Uses Kelly Criterion (fractional) for optimal sizing:
- Maximum per trade: 5% of bankroll
- Adjusted for fees and slippage
- Respects liquidity constraints

## 📚 Additional Resources

- [Kalshi API Docs](https://docs.kalshi.com)
- [Polymarket CLOB Docs](https://docs.polymarket.com)
- [Prediction Market Arbitrage Guide](https://example.com)

---

**Built with ❤️ for the prediction market community**
