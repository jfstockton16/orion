# API Setup Guide for Orion Arbitrage Bot

This guide explains how to obtain and configure API credentials for Kalshi, Polymarket, and Telegram.

## Table of Contents
- [Kalshi API Setup](#kalshi-api-setup)
- [Polymarket API Setup](#polymarket-api-setup)
- [Telegram Bot Setup](#telegram-bot-setup)
- [Configuration Files](#configuration-files)

---

## Kalshi API Setup

### What You Need
- **API Key ID**: Your unique API key identifier
- **RSA Private Key**: A `.pem` file for signing requests

### How to Get Credentials

1. **Create Kalshi Account**
   - Go to [kalshi.com](https://kalshi.com)
   - Sign up and verify your account

2. **Navigate to API Settings**
   - Log in to your Kalshi account
   - Go to **Settings → API**

3. **Generate API Credentials**
   - Click "Create API Key"
   - Download the **private key file** (`.pem` format) - **SAVE THIS SECURELY!**
   - Copy your **API Key ID** (looks like: `abc123def456...`)

### Important Notes
- ⚠️ **The private key is only shown once!** Save it immediately
- Keep your `.pem` file secure - it grants access to your account
- Kalshi uses **RSA-PSS signing** (not email/password)

### Add to .env File

Option 1: Using a private key file
```bash
KALSHI_API_KEY=your_api_key_id_here
KALSHI_PRIVATE_KEY_PATH=/path/to/kalshi_private_key.pem
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
```

Option 2: Using inline PEM string
```bash
KALSHI_API_KEY=your_api_key_id_here
KALSHI_PRIVATE_KEY_PEM=-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...
-----END PRIVATE KEY-----
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
```

---

## Polymarket API Setup

### What You Need
- **Ethereum Wallet Private Key**: For signing orders (EIP-712)
- **CLOB API Credentials**: API Key, Secret, and Passphrase

### How to Get Credentials

#### Step 1: Ethereum Wallet
You need an Ethereum wallet with funds on **Polygon network**.

1. **Using Metamask** (recommended):
   - Install [Metamask](https://metamask.io)
   - Create or import a wallet
   - Export private key: Account menu → Account Details → Export Private Key
   - **Remove the `0x` prefix** before adding to `.env`

2. **Fund Your Wallet**:
   - Add Polygon network to Metamask
   - Bridge USDC to Polygon using [Polymarket's bridge](https://polymarket.com)

#### Step 2: CLOB API Credentials

1. **Go to Polymarket**
   - Visit [polymarket.com](https://polymarket.com)
   - Connect your wallet

2. **Enable API Access**
   - Go to **Settings → Developer** or **Settings → API**
   - Click "Create API Key"

3. **Save Credentials**
   You'll receive:
   - **API Key**: `your_api_key`
   - **API Secret**: `your_api_secret`
   - **Passphrase**: `your_passphrase`

   **⚠️ Save these immediately - they're only shown once!**

### Add to .env File

```bash
# Ethereum wallet (without 0x prefix)
POLYMARKET_PRIVATE_KEY=abc123def456...

# CLOB API credentials
POLYMARKET_API_KEY=your_polymarket_api_key
POLYMARKET_API_SECRET=your_polymarket_api_secret
POLYMARKET_API_PASSPHRASE=your_polymarket_passphrase

# Network configuration
POLYMARKET_CHAIN_ID=137  # Polygon mainnet
POLYMARKET_PROXY_URL=https://clob.polymarket.com
```

### Important Notes
- Your wallet must have **USDC on Polygon** to trade
- Keep your private key secure - it controls your funds
- Test with small amounts first
- For testnet: Use `POLYMARKET_CHAIN_ID=80001` (Mumbai)

---

## Telegram Bot Setup (Optional)

Telegram alerts notify you of trading opportunities and execution results.

### How to Create a Bot

1. **Talk to BotFather**
   - Open Telegram
   - Search for `@BotFather`
   - Send `/newbot`

2. **Configure Your Bot**
   - Choose a name (e.g., "Orion Arbitrage Bot")
   - Choose a username (e.g., "orion_arb_bot")
   - **Save the bot token** BotFather gives you

3. **Get Your Chat ID**

   Option A: Use a bot
   - Search for `@userinfobot` on Telegram
   - Start a chat
   - It will show your Chat ID

   Option B: Manual method
   - Start a chat with your new bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the JSON response

### Add to .env File

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

### Test Your Setup

After configuration, test alerts:
```bash
python main.py --test-alerts
```

You should receive a test message on Telegram!

---

## Configuration Files

### File Structure

```
orion/
├── .env                    # Your credentials (NEVER commit this!)
├── .env.example            # Template with placeholders
├── config/
│   └── config.yaml         # Trading parameters
├── kalshi_private_key.pem  # Your Kalshi private key (optional location)
└── ...
```

### Complete .env Example

```bash
# Kalshi
KALSHI_API_KEY=your_kalshi_api_key_id
KALSHI_PRIVATE_KEY_PATH=./kalshi_private_key.pem
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2

# Polymarket
POLYMARKET_PRIVATE_KEY=your_eth_private_key_without_0x
POLYMARKET_API_KEY=your_polymarket_api_key
POLYMARKET_API_SECRET=your_polymarket_api_secret
POLYMARKET_API_PASSPHRASE=your_polymarket_passphrase
POLYMARKET_CHAIN_ID=137
POLYMARKET_PROXY_URL=https://clob.polymarket.com

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DATABASE_URL=sqlite:///data/arbitrage.db
```

---

## Security Best Practices

### 🔒 Protecting Your Credentials

1. **Never commit `.env` to git**
   - It's already in `.gitignore`
   - Double-check before pushing

2. **Use strong permissions**
   ```bash
   chmod 600 .env
   chmod 600 kalshi_private_key.pem
   ```

3. **Use encryption for production**
   - Consider using the built-in secrets manager
   - See `src/utils/secrets_manager.py`

4. **Regular key rotation**
   - Rotate API keys every 90 days
   - Generate new keys if compromised

5. **Test environment first**
   - Use testnet/demo accounts initially
   - Verify everything works before going live

---

## Troubleshooting

### Kalshi Authentication Fails

**Error**: `Failed to sign request - missing credentials`

**Solutions**:
- Verify `KALSHI_API_KEY` is set
- Check private key path is correct
- Ensure private key file is readable: `ls -l kalshi_private_key.pem`
- Verify PEM format starts with `-----BEGIN PRIVATE KEY-----`

### Polymarket Client Not Initialized

**Error**: `Client not initialized`

**Solutions**:
- Verify `POLYMARKET_PRIVATE_KEY` is set (without `0x` prefix)
- Check API credentials are correct
- Ensure wallet has USDC on Polygon
- Try reinstalling: `pip install --upgrade py-clob-client`

### Telegram Alerts Not Working

**Error**: `Telegram not properly configured`

**Solutions**:
- Verify bot token format: `number:alphanumeric`
- Check chat ID is a number (may be negative)
- Ensure you've started a chat with your bot
- Test with: `python main.py --test-alerts`

---

## Getting Help

If you encounter issues:

1. **Check logs**: `tail -f logs/arbitrage.log`
2. **Test individual components**: See examples in `examples/` directory
3. **Verify API status**:
   - [Kalshi Status](https://status.kalshi.com)
   - [Polymarket Discord](https://discord.gg/polymarket)
4. **Review official docs**:
   - [Kalshi API Docs](https://trading-api.readme.io/)
   - [Polymarket Docs](https://docs.polymarket.com/)

---

## Next Steps

After setting up your API credentials:

1. ✅ Verify setup: `python main.py --init-db`
2. ✅ Test in dry-run: `python main.py --dry-run`
3. ✅ Monitor for 24 hours
4. ✅ Review PRODUCTION_SETUP.md before going live

**Good luck, and trade safely!** 🚀
