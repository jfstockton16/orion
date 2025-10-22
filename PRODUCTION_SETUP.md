# Orion Arbitrage Engine - Production Setup Guide

## 🚨 CRITICAL: Read Before Running

This bot trades real money. Improper configuration can lead to financial losses. Follow these steps exactly.

---

## Prerequisites

- Python 3.11+
- Active Kalshi account with API access
- Active Polymarket account with funded wallet
- (Optional) Telegram bot for alerts

---

## Step 1: Initial Setup

### 1.1 Clone and Install

```bash
# Navigate to project directory
cd /home/user/orion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Verify Installation

```bash
python -c "import aiohttp, web3, sqlalchemy; print('✅ All dependencies installed')"
```

---

## Step 2: Secure Credential Management

### 2.1 Encrypt Your API Credentials

**CRITICAL: Never store private keys in plain text!**

```bash
# Run the encryption utility
python -m src.utils.secrets_manager
```

Follow the prompts to encrypt:
- Kalshi API Key
- Kalshi API Secret
- Polymarket Private Key
- Polymarket API Key
- Telegram Bot Token (optional)
- Telegram Chat ID (optional)

The script will output encrypted credentials for your `.env` file.

### 2.2 Create `.env` File

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

**Add the encrypted credentials from step 2.1:**

```env
# Master password (STORE THIS SECURELY!)
MASTER_PASSWORD=your_strong_master_password_here

# Encrypted credentials (from encryption utility)
KALSHI_API_KEY_ENCRYPTED=<encrypted_value>
KALSHI_API_SECRET_ENCRYPTED=<encrypted_value>
POLYMARKET_PRIVATE_KEY_ENCRYPTED=<encrypted_value>
POLYMARKET_API_KEY_ENCRYPTED=<encrypted_value>

# Optional: Telegram alerts
TELEGRAM_BOT_TOKEN_ENCRYPTED=<encrypted_value>
TELEGRAM_CHAT_ID_ENCRYPTED=<encrypted_value>

# Exchange URLs (usually don't need to change)
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
POLYMARKET_PROXY_URL=https://clob.polymarket.com

# Database
DATABASE_URL=sqlite:///data/arbitrage.db
```

**⚠️  CRITICAL SECURITY:**
- Never commit `.env` to version control
- Store `MASTER_PASSWORD` in a password manager
- Use different passwords for dev/prod
- Rotate credentials monthly

---

## Step 3: Configure Trading Parameters

Edit `config/config.yaml`:

```yaml
trading:
  threshold_spread: 0.015  # Minimum 1.5% edge (conservative)
  max_trade_size_pct: 0.03  # Max 3% per trade (start conservative)
  min_trade_size_usd: 100
  auto_execute: false  # KEEP FALSE until you're confident!

capital:
  initial_bankroll: 10000  # Your actual starting capital
  kalshi_allocation_pct: 0.50
  polymarket_allocation_pct: 0.50
  max_days_to_resolution: 30  # Capital efficiency filter
  high_return_threshold: 0.05  # 5% exception for slow trades

risk:
  max_open_positions: 10  # Conservative limit
  max_exposure_per_event: 0.10  # 10% max per event
  max_daily_loss_pct: 0.05  # CIRCUIT BREAKER: 5% daily loss limit
```

**Key Safety Parameters:**
- `auto_execute: false` - Start in alert-only mode
- `max_daily_loss_pct: 0.05` - Circuit breaker halts trading at 5% loss
- `max_trade_size_pct: 0.03` - Limits position size to 3% of bankroll

---

## Step 4: Initialize Database

```bash
python main.py --init-db
```

You should see:
```
✅ Database initialized at sqlite:///data/arbitrage.db
```

---

## Step 5: Test Alert System (Optional)

If using Telegram alerts:

```bash
python main.py --test-alerts
```

You should receive a test message in Telegram.

---

## Step 6: Dry Run (Paper Trading)

**CRITICAL: Test with dry-run mode first!**

```bash
# Run in simulation mode
python main.py --dry-run
```

Monitor the logs for:
- Market fetching
- Event matching
- Opportunity detection
- Simulated trades

**Run dry-run for at least 24 hours** to verify:
- ✅ Bot connects to exchanges
- ✅ Opportunities are detected
- ✅ Risk analysis works
- ✅ Circuit breaker triggers correctly
- ✅ No errors in logs

---

## Step 7: Live Trading (Use With Caution)

### 7.1 Pre-Flight Checklist

Before enabling live trading, verify:

- [ ] Dry-run tested for 24+ hours with no errors
- [ ] Exchange accounts funded
- [ ] API keys have correct permissions
- [ ] Master password backed up securely
- [ ] Circuit breaker configured (`max_daily_loss_pct`)
- [ ] Position limits set conservatively
- [ ] Alert system tested and working
- [ ] Understand the risk of financial loss

### 7.2 Start With Alerts Only

```bash
# Edit config.yaml
nano config/config.yaml
```

Keep `auto_execute: false` - this will detect opportunities and send alerts, but NOT execute trades.

```bash
python main.py
```

**Monitor for several hours:**
- Are the opportunities real?
- Do spreads make sense?
- Are risk assessments accurate?

### 7.3 Enable Auto-Execution (Final Step)

**⚠️  YOU ARE NOW TRADING REAL MONEY**

```bash
# Edit config.yaml
nano config/config.yaml

# Set auto_execute to true
trading:
  auto_execute: true
```

Start the engine:

```bash
python main.py
```

You'll see a 5-second warning:
```
⚠️  WARNING: LIVE TRADING MODE ENABLED
   This bot will execute real trades with real money.
   Press Ctrl+C within 5 seconds to cancel...
```

---

## Step 8: Monitoring & Maintenance

### 8.1 Real-Time Monitoring

```bash
# View logs in real-time
tail -f logs/arbitrage.log
```

### 8.2 Dashboard (Optional)

```bash
# In a separate terminal
streamlit run dashboard.py --server.port=8501
```

Access at: `http://localhost:8501`

### 8.3 Check Circuit Breaker Status

Monitor logs for circuit breaker warnings:

```
🚨 CIRCUIT BREAKER TRIGGERED: Daily loss limit exceeded: 5.23% (max: 5.00%)
🛑 ALL TRADING HALTED - Manual intervention required
```

**If circuit breaker triggers:**
1. STOP the bot immediately
2. Review trades in database
3. Identify what went wrong
4. Fix the issue
5. Only then consider resetting circuit breaker

---

## Safety Best Practices

### Daily Checklist
- [ ] Check logs for errors
- [ ] Verify balances on exchanges
- [ ] Review executed trades
- [ ] Check P&L vs. database
- [ ] Monitor circuit breaker status

### Weekly Checklist
- [ ] Review risk parameters
- [ ] Analyze trade performance
- [ ] Check for dependency updates
- [ ] Backup database
- [ ] Rotate logs

### Monthly Checklist
- [ ] Rotate API credentials
- [ ] Full performance review
- [ ] Update dependencies (`pip install --upgrade -r requirements.txt`)
- [ ] Review and adjust trading parameters

---

## Emergency Procedures

### Halt Trading Immediately

```bash
# Press Ctrl+C to stop the bot
# Or:
pkill -f "python main.py"
```

### Circuit Breaker Triggered

```
🛑 Trading halted by circuit breaker
```

**DO NOT simply restart the bot!**

1. Stop the bot
2. Review logs: `cat logs/arbitrage.log | grep ERROR`
3. Check database for recent trades
4. Identify root cause
5. Implement fix
6. Manual review before restart

### Partial Fill Detected

```
🚨 PARTIAL FILL DETECTED - Kalshi: True, Poly: False
⚠️  Unwinding Kalshi position
```

The bot will automatically:
1. Attempt to unwind the filled position
2. Send alert
3. Log details for review

**Manual verification:**
- Check exchange positions
- Verify unwind executed
- Review P&L impact

---

## Performance Tuning

### Start Conservative

| Parameter | Conservative | Aggressive |
|-----------|-------------|------------|
| threshold_spread | 0.015 (1.5%) | 0.010 (1%) |
| max_trade_size_pct | 0.03 (3%) | 0.05 (5%) |
| max_daily_loss_pct | 0.03 (3%) | 0.05 (5%) |
| max_open_positions | 10 | 20 |

**Gradually increase** aggressiveness only after:
- 1+ week of profitable operation
- Understanding risk patterns
- Confidence in the system

---

## Troubleshooting

### "Failed to decrypt secret - check MASTER_PASSWORD"

- Verify `MASTER_PASSWORD` in `.env` is correct
- Re-encrypt credentials if password changed

### "Trading halted by circuit breaker"

- Normal safety mechanism
- Review logs before resetting
- Identify cause of losses
- Only reset if you understand why

### "Failed to place order: 401"

- API credentials expired or invalid
- Check exchange account status
- Verify API key permissions

### "Partial fill detected"

- Network issue or exchange problem
- Bot will auto-unwind
- Verify unwind succeeded on exchange

---

## Support & Logs

### Log Files

```
logs/
├── arbitrage.log  # Main application log
```

Important log markers:
- `ERROR` - Something went wrong
- `🚨` - Critical issue
- `⚠️` - Warning
- `✅` - Success
- `🛑` - Trading halted

### Database

```
data/
└── arbitrage.db  # SQLite database
```

Query recent trades:
```bash
sqlite3 data/arbitrage.db "SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;"
```

---

## Security Checklist

Before going live:

- [ ] All credentials encrypted
- [ ] `.env` file not in version control
- [ ] Master password stored securely
- [ ] API keys have minimum required permissions
- [ ] Database backed up regularly
- [ ] Logs rotated and reviewed
- [ ] Circuit breaker configured
- [ ] Alert system tested
- [ ] Network firewall configured (if applicable)
- [ ] Monitoring in place

---

## Disclaimer

**⚠️  FINANCIAL RISK WARNING**

- This bot trades real money on real exchanges
- You can lose your entire capital
- No guarantees of profit
- Past performance ≠ future results
- Use at your own risk
- Start with small amounts
- Only risk capital you can afford to lose

**The developers are NOT responsible for:**
- Financial losses
- Exchange connectivity issues
- Market conditions
- Bugs or errors (use at own risk)
- Regulatory compliance (check your jurisdiction)

---

## Next Steps

1. ✅ Complete dry-run testing (24+ hours)
2. ✅ Start with alerts-only mode
3. ✅ Monitor for several days
4. ✅ Enable auto-execute with small limits
5. ✅ Gradually scale up if profitable
6. ✅ Continuous monitoring and adjustment

**Remember: Slow and steady. Start conservative. Monitor constantly.**

Good luck, and trade safely! 💰
