# 💰 Orion Cross-Exchange Arbitrage Engine

Automated arbitrage bot for prediction markets, detecting and executing profitable opportunities between **Kalshi** and **Polymarket**.

## 🎯 Features

- **Real-time Market Monitoring**: Continuously scans Kalshi and Polymarket for matching events
- **Intelligent Event Matching**: Fuzzy matching algorithm to identify equivalent markets across exchanges
- **Automated Execution**: Execute both legs of arbitrage trades simultaneously
- **Risk Management**: Position sizing, exposure limits, and daily loss protection
- **Capital Management**: Automatic bankroll allocation and rebalancing
- **Live Dashboard**: Real-time monitoring via Streamlit web interface
- **Alert System**: Telegram notifications for opportunities and executions
- **Complete Audit Trail**: SQLite database logging all transactions

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

### 1. Clone and Install

```bash
git clone <repository-url>
cd orion
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
nano .env
```

Required environment variables:
```bash
# Kalshi
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_api_secret

# Polymarket
POLYMARKET_PRIVATE_KEY=your_ethereum_private_key
POLYMARKET_API_KEY=your_polymarket_api_key

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Initialize Database

```bash
python main.py --init-db
```

### 4. Test Alert System (Optional)

```bash
python main.py --test-alerts
```

### 5. Run in Dry-Run Mode

Test the bot without executing real trades:

```bash
python main.py --dry-run
```

### 6. Start Live Trading

⚠️ **WARNING**: This will execute real trades with real money!

```bash
python main.py --auto-execute true
```

### 7. Launch Dashboard

In a separate terminal:

```bash
streamlit run dashboard.py
```

Access at: http://localhost:8501

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

- **Real-time Balance**: View Kalshi, Polymarket, and total balances
- **Open Positions**: Monitor active arbitrage positions
- **Opportunity Feed**: Recent detected opportunities
- **Performance Metrics**: P&L, win rate, volume
- **Performance Charts**: Balance over time
- **Auto-refresh**: Updates every 30 seconds

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
│   ├── api/                    # Exchange API clients
│   │   ├── kalshi_client.py
│   │   └── polymarket_client.py
│   ├── arbitrage/              # Core arbitrage logic
│   │   ├── matcher.py          # Event matching
│   │   └── detector.py         # Opportunity detection
│   ├── execution/              # Trade execution
│   │   ├── executor.py         # Order placement
│   │   └── capital_manager.py  # Capital & risk mgmt
│   ├── database/               # Data persistence
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repository.py       # Data access layer
│   ├── monitoring/             # Alerts & monitoring
│   │   └── alerts.py
│   ├── utils/                  # Utilities
│   │   ├── config.py
│   │   └── logger.py
│   └── engine.py               # Main orchestrator
├── config/
│   └── config.yaml             # Configuration
├── data/                       # SQLite database
├── logs/                       # Log files
├── tests/                      # Unit tests
├── main.py                     # CLI entry point
├── dashboard.py                # Streamlit dashboard
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker image
└── README.md                   # This file
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

## 🔒 Security Best Practices

1. **Never commit** `.env` or private keys to version control
2. **Use AWS Secrets Manager** or similar for production
3. **Rotate API keys** regularly
4. **Monitor logs** for suspicious activity
5. **Enable 2FA** on exchange accounts
6. **Start small** and increase position sizes gradually

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

- GitHub Issues: [repository/issues]
- Documentation: See `docs/` folder
- Discord: [invite-link]

## 🗺️ Roadmap

- [ ] Add more exchanges (Insight, Manifold)
- [ ] Machine learning for spread prediction
- [ ] Advanced position hedging strategies
- [ ] Web-based configuration UI
- [ ] Portfolio optimization (maximize Sharpe)
- [ ] Market-making mode
- [ ] Historical backtesting engine

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
