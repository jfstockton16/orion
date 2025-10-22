# Orion Daily Usage Guide (No Terminal Required!)

This guide is for **after** you've completed the initial setup in [SETUP_FOR_DUMMIES.md](SETUP_FOR_DUMMIES.md).

---

## Starting Orion (Every Day)

### Step 1: Start the Engine and Dashboard

**Simply double-click:** `Start Orion.command`

- You can find this file on your Desktop (if you copied it there)
- Or in the `~/Desktop/orion/` folder

**What happens:**
1. A Terminal window will open (don't close it!)
2. The arbitrage engine will start
3. The Streamlit dashboard will start
4. Your web browser will automatically open to the dashboard

**Wait about 10 seconds** for everything to start up.

---

## Viewing the Dashboard

If Orion is already running, you can open the dashboard anytime:

**Option 1:** Double-click `Orion Dashboard.html` (on your Desktop)

**Option 2:** Open Safari and go to: `http://localhost:8501`

---

## What You'll See on the Dashboard

- **Current balances** on Kalshi and Polymarket
- **Open arbitrage positions** (active trades)
- **Recent opportunities** detected
- **Performance charts** showing profit/loss over time
- **Control panel** to adjust settings

The dashboard auto-refreshes every 30 seconds.

---

## Stopping Orion (End of Day)

**Simply double-click:** `Stop Orion.command`

This cleanly shuts down both the engine and dashboard.

**You'll see:**
- "Stopping Orion Engine... ✓"
- "Stopping Dashboard... ✓"
- "ORION HAS BEEN STOPPED"

Then you can close the Terminal window.

---

## Daily Checklist

Every day you should:

1. **Start Orion** - Double-click `Start Orion.command`
2. **Check the Dashboard** - Look at balances and recent activity
3. **Review Logs for Errors** - Look for any red "ERROR" messages in the Terminal window
4. **Verify Balances** - Log into Kalshi and Polymarket websites to confirm balances match the dashboard
5. **Stop Orion** - When done for the day, double-click `Stop Orion.command`

---

## Understanding What's Happening

### Alert-Only Mode (Recommended at First)

If Auto-Execute is turned OFF in the dashboard (the safe default):
- Orion **detects** arbitrage opportunities
- Orion **alerts** you (in logs, dashboard, and Telegram if configured)
- Orion **does NOT** execute trades automatically
- You can manually review and decide whether to trade

### Live Trading Mode (Advanced Users Only)

If Auto-Execute is turned ON in the dashboard:
- Orion **automatically executes** real trades
- This uses **real money**
- Monitor closely!

---

## Troubleshooting

### "The file cannot be opened because it is from an unidentified developer"

**First time only:**
1. Right-click (Control+click) on the file
2. Select "Open"
3. Click "Open" in the warning dialog

After doing this once, double-clicking will work.

### Dashboard shows "Connection Error"

- Make sure you double-clicked `Start Orion.command` first
- Wait 10-15 seconds for the dashboard to fully start
- Try refreshing the browser page
- Check that the Terminal window is still open and running

### Engine stops unexpectedly

**Circuit Breaker Triggered:**
- This is a safety feature
- It means you hit the daily loss limit (default: 3%)
- Check the logs to see what happened
- Review your settings before restarting

**API Error:**
- Your API keys might be expired
- Check that your Kalshi/Polymarket accounts are still active
- You may need to generate new API keys

### Can't find the .command files

They should be in:
- `~/Desktop/orion/Start Orion.command`
- `~/Desktop/orion/Stop Orion.command`

If you copied them to your Desktop:
- `~/Desktop/Start Orion.command`
- `~/Desktop/Stop Orion.command`

---

## Checking Logs (Optional, for Advanced Users)

If you want to see detailed logs:

**Option 1: In the Terminal Window**
- The Terminal window that opened when you started Orion shows real-time activity
- Just look at it while it's running

**Option 2: Open Log Files**
1. Open Terminal
2. Type: `tail -f ~/Desktop/orion/logs/arbitrage.log`
3. Press Enter

You'll see a live feed of all engine activity.

Press `Control+C` to stop viewing logs.

---

## Adjusting Settings (Use the Dashboard!)

**Don't manually edit config files!** Use the Dashboard's Control Panel instead.

1. Open the Dashboard: http://localhost:8501
2. Click on the **Control Panel** tab (at the top)
3. Adjust any settings you want:

**Important settings you can change:**

- **Auto-Execute**: Turn ON for live trading, OFF for alert-only mode
- **Paper Trading**: Turn ON for simulation mode (testing)
- **Minimum Edge**: Minimum profit required (1.0% = 1%)
- **Max Trade Size**: Max % of bankroll per trade (2% recommended)
- **Max Open Positions**: How many trades at once (start with 5)
- **Max Daily Loss**: Circuit breaker % (3% recommended)
- **Bankroll**: Your total capital amount
- **Polling Interval**: How often to check for opportunities (30 seconds)

4. **Click "Save Configuration"** at the bottom

Changes take effect on the next polling cycle (or immediately if you restart Orion).

---

## Safety Reminders

1. **Start in alert-only mode** (Auto-Execute OFF in dashboard)
2. **Monitor daily** - Don't set it and forget it
3. **Start with small position sizes** (2-5% max per trade)
4. **Verify balances** match between dashboard and exchange websites
5. **Understand circuit breakers** - If Orion stops itself, investigate before restarting
6. **No guarantees** - You can lose money

---

## Quick Reference

| Action | How To Do It |
|--------|-------------|
| Start Orion | Double-click `Start Orion.command` |
| View Dashboard | Double-click `Orion Dashboard.html` or go to http://localhost:8501 |
| Stop Orion | Double-click `Stop Orion.command` |
| Check if Running | Look for Terminal window, or check if dashboard loads |
| View Logs | Look at Terminal window, or open `logs/arbitrage.log` |

---

## Getting Help

If something goes wrong:

1. **Read the error message** in the Terminal window
2. **Check the logs:** `~/Desktop/orion/logs/arbitrage.log`
3. **Review the troubleshooting section** in [SETUP_FOR_DUMMIES.md](SETUP_FOR_DUMMIES.md)
4. **Stop and restart** Orion to see if that fixes it
5. **Ask for help** with the specific error message you're seeing

---

## Next Steps

Once you're comfortable with alert-only mode:

1. Review detected opportunities for 3-7 days
2. Verify they make sense (prices, spreads, etc.)
3. Check historical performance in the dashboard
4. When ready for live trading:
   - Open the Dashboard: http://localhost:8501
   - Go to the **Control Panel** tab
   - Toggle **"Auto-Execute"** to **ON**
   - **Keep position sizes conservative** (2-3% max per trade)
   - Click **"Save Configuration"**
   - Monitor closely for the first week

---

**That's it! You're all set. Happy arbitraging!**
