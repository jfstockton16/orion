# Orion Setup Guide for Complete Beginners (Mac Mini)

**What this does:** Automatically finds and exploits price differences between Kalshi and Polymarket prediction markets to make profit.

**Warning:** This trades real money. You can lose money. Start with small amounts you can afford to lose.

---

## Before You Start

You need:
- A Mac Mini (or any Mac)
- A Kalshi account with API credentials
- A Polymarket account with a wallet
- About 30 minutes

---

## Step 1: Install Python

Open **Terminal** (press Command+Space, type "Terminal", press Enter).

Copy and paste each line below, then press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

When that finishes:

```bash
brew install python@3.11
```

Verify it worked:

```bash
python3 --version
```

You should see something like "Python 3.11.x". If not, ask for help.

---

## Step 2: Download Orion

Still in Terminal, copy and paste:

```bash
cd ~/Desktop
git clone https://github.com/jfstockton16/orion.git
cd orion
```

If you get "command not found: git":

```bash
brew install git
```

Then try the clone command again.

---

## Step 3: Install Required Software

Copy and paste:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

This takes 2-3 minutes. Wait for it to finish (you'll see a new prompt when done).

---

## Step 4: Get Your API Keys

### For Kalshi:
1. Go to kalshi.com and log in
2. Go to Settings → API
3. Create a new API key
4. **Save both the API Key and API Secret** (you'll need them next)

### For Polymarket:
1. Go to polymarket.com and log in
2. Export your wallet's private key (Settings → Security)
3. Get your API key from Settings → Developer
4. **Save both the Private Key and API Key**

**IMPORTANT:** Never share these keys with anyone. They control your money.

---

## Step 5: Encrypt Your Keys (Keep Them Safe)

Run this command:

```bash
python -m src.utils.secrets_manager
```

When prompted, enter:
1. A master password (make it strong, like "MyD0g!sN@medFluffy2024")
2. Your Kalshi API key
3. Your Kalshi API secret
4. Your Polymarket private key
5. Your Polymarket API key
6. Press Enter to skip Telegram (optional)

**Write down your master password somewhere safe!** You'll need it.

The program will show encrypted text that looks like `gAAAAABl...` - that's good!

---

## Step 6: Create Your Configuration File

Copy and paste:

```bash
cp .env.example .env
open -a TextEdit .env
```

TextEdit will open. Replace the placeholder text with:

```
MASTER_PASSWORD=your_master_password_from_step5

KALSHI_API_KEY_ENCRYPTED=paste_the_encrypted_key_here
KALSHI_API_SECRET_ENCRYPTED=paste_the_encrypted_secret_here
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2

POLYMARKET_PRIVATE_KEY_ENCRYPTED=paste_the_encrypted_private_key_here
POLYMARKET_API_KEY_ENCRYPTED=paste_the_encrypted_api_key_here
POLYMARKET_PROXY_URL=https://clob.polymarket.com

DATABASE_URL=sqlite:///data/arbitrage.db
```

**Important:** Use the encrypted values from Step 5 (the long strings starting with `gAAAAA`), NOT your actual keys!

Save the file (Command+S) and close TextEdit.

---

## Step 7: Set How Much to Trade

Open the configuration:

```bash
open -a TextEdit config/config.yaml
```

Find the line that says `initial_bankroll: 100000` and change it to your actual starting amount. For example, if you have $5,000:

```yaml
initial_bankroll: 5000
```

Find these safety settings and make sure they say:

```yaml
auto_execute: false
max_trade_size_pct: 0.02
max_daily_loss_pct: 0.03
```

This means:
- Won't trade automatically yet (alert only)
- Max 2% of your money per trade
- Stops if you lose 3% in one day

Save (Command+S) and close.

---

## Step 8: Initialize the Database

Back in Terminal:

```bash
python main.py --init-db
```

You should see: "Database initialized". If you see an error, something went wrong in previous steps.

---

## Step 9: Test It (Practice Mode)

Run the bot in practice mode for at least 24 hours:

```bash
python main.py --dry-run
```

You'll see messages like:
```
Fetched 87 Kalshi markets, 124 Polymarket markets
Found 12 matching market pairs
ARBITRAGE OPPORTUNITY DETECTED!
```

This is good! It's finding opportunities but NOT actually trading.

**Let it run for a full day.** Press Command+T to open a new Terminal tab if you need to use your computer.

To stop it: Press Control+C

---

## Step 10: Monitor in Your Web Browser (Optional)

Open a new Terminal tab (Command+T) and run:

```bash
cd ~/Desktop/orion
source venv/bin/activate
streamlit run dashboard.py
```

Open Safari and go to: http://localhost:8501

You'll see a dashboard showing:
- Your balances
- Detected opportunities
- Performance charts

---

## Step 11: Enable Real Trading (DANGER ZONE)

**Only do this after 24+ hours of dry-run testing!**

Open the configuration:

```bash
open -a TextEdit config/config.yaml
```

Change:
```yaml
auto_execute: false
```

To:
```yaml
auto_execute: true
```

Save (Command+S) and close.

Now when you run it:

```bash
python main.py
```

You'll see a 5-second warning. **This will now trade real money.**

---

## Daily Checklist

Every day:
1. Check the dashboard (http://localhost:8501)
2. Look at Terminal for errors (anything with "ERROR" or "🚨")
3. Verify your balances on Kalshi and Polymarket match the dashboard

---

## How to Stop Everything

Press Control+C in the Terminal window where the bot is running.

If it doesn't stop:

```bash
pkill -f "python main.py"
```

---

## Troubleshooting

**"Failed to decrypt secret - check MASTER_PASSWORD"**
- You typed the master password wrong in the .env file
- Make sure it exactly matches what you used in Step 5

**"Failed to place order: 401"**
- Your API keys are wrong or expired
- Go back to Step 4 and get new ones

**"Circuit breaker triggered"**
- The bot detected you're losing money and stopped itself (this is good!)
- Check what went wrong before restarting

**Nothing happens when I run commands**
- Make sure you're in the right folder: `cd ~/Desktop/orion`
- Make sure the virtual environment is activated: `source venv/bin/activate`

---

## Important Warnings

1. **Start small** - Test with money you can afford to lose
2. **Monitor daily** - Don't just set it and forget it
3. **Circuit breaker is your friend** - If it stops trading, find out why before restarting
4. **No guarantees** - You can lose money. This is not investment advice.

---

## Getting Help

If something doesn't work:
1. Read the error message carefully
2. Check you followed every step exactly
3. Look in the `logs/arbitrage.log` file for details
4. Ask for help with the specific error message you're seeing

---

## Step 12: Set Up Easy Launch (One-Time Setup)

**THIS IS THE BEST PART!** After this step, you'll never need to use Terminal again.

In Terminal, copy and paste these commands ONE LAST TIME:

```bash
cd ~/Desktop/orion
chmod +x "Start Orion.command"
chmod +x "Stop Orion.command"
chmod +x scripts/start_orion.sh
chmod +x scripts/stop_orion.sh
```

Now you have two special files in your `orion` folder:
- **Start Orion.command** - Starts everything
- **Stop Orion.command** - Stops everything

**First time only:** When you double-click these files, macOS will say "cannot be opened because it is from an unidentified developer."

Here's how to fix that:
1. Right-click (or Control+click) on **Start Orion.command**
2. Select "Open"
3. Click "Open" in the popup
4. Do the same for **Stop Orion.command**

After doing this once, double-clicking will work forever.

**Optional but recommended:** Create desktop shortcuts:

Right-click and drag these files to your Desktop while holding the Option+Command keys. This creates aliases (shortcuts) on your Desktop.

Or simply copy them:
```bash
cp "Start Orion.command" ~/Desktop/
cp "Stop Orion.command" ~/Desktop/
cp "Orion Dashboard.html" ~/Desktop/
```

---

## Summary of Daily Usage (No Terminal Required!)

**To start Orion and the dashboard:**
1. Double-click **Start Orion.command** (on Desktop or in the orion folder)
2. Wait about 10 seconds
3. Your browser will automatically open to the dashboard

**To view the dashboard (if Orion is already running):**
- Double-click **Orion Dashboard.html**
- Or go to: http://localhost:8501 in Safari

**To stop Orion:**
- Double-click **Stop Orion.command**

**To check logs (Terminal required, optional):**
```bash
tail -f ~/Desktop/orion/logs/arbitrage.log
```

That's it! No more Terminal commands needed for daily use.

---

## OLD METHOD: Summary of Commands (For Reference)

You don't need these anymore, but they still work if you prefer Terminal:

**To start the bot:**
```bash
cd ~/Desktop/orion
source venv/bin/activate
python main.py
```

**To start the dashboard:**
```bash
cd ~/Desktop/orion
source venv/bin/activate
streamlit run dashboard.py
```

**To stop the bot:**
Press Control+C

**To check logs:**
```bash
tail -f logs/arbitrage.log
```

---

That's it! You're running Orion. Start cautious, monitor closely, and good luck!
