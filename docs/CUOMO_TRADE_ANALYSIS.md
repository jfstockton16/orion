# Cuomo NYC Mayoral Election - Arbitrage Analysis

## Trade Overview

**Event:** "Will Andrew Cuomo win the NYC mayoral election?"

**Markets:**
- **Kalshi** (USD, CFTC-regulated)
- **Polymarket** (USDC, crypto-based)

**Prices:**
- Kalshi YES = $0.063 (6.3%)
- Polymarket NO = $0.92 (92%)

**Combined Probability:** 98.3%
**Implied Arbitrage:** 1.7% edge (raw, before fees)

---

## 🚨 CRITICAL: Proper Bet Sizing

**YOU CANNOT BET 50/50 ON EACH SIDE!**

Since probabilities are different (6.3% vs 92%), you must balance **payouts**, not **amounts**:

```
Example with $13,000 total capital:

❌ WRONG: $6,500 on each side
✅ RIGHT:
   - $1,000 on 6.3% side → pays $15,873
   - $12,000 on 92% side → pays $13,043

Formula: Bet_A = Total × (Price_A / (Price_A + Price_B))
         Bet_B = Total × (Price_B / (Price_A + Price_B))
```

**After proper sizing + fees: This trade LOSES money (-1.63% expected value)**

---

## How Orion Bot Processes This Trade

### Step 1: Event Matching ✅

```python
EventMatcher analyzes:
├─ Question similarity: ~0.95 (PASS)
├─ End date matching: Same date (PASS)
└─ Keyword analysis: Both mention "mayoral election"

Result: MARKETS MATCHED
```

**Bot Action:** Proceeds to arbitrage detection

---

### Step 2: Price Analysis 💰

```
Kalshi YES:          $0.063 (6.3%)
Polymarket NO:       $0.920 (92%)
─────────────────────────────
Combined cost:       $0.983
Guaranteed payout:   $1.000
─────────────────────────────
Raw edge (pre-fee):  $0.017 (1.7%)
```

**Critical Insight:** You CANNOT bet equal amounts on each side because the probabilities are different! You must balance the **payouts**, not the **bet amounts**.

**Bot Action:** Calculates proper bet sizing and profitability with fees

---

### Step 3: Bet Sizing & Fee Modeling 💸

#### Proper Bet Balancing

Since prices are different (6.3% vs 92%), you must calculate bet sizes to **equalize payouts**:

```
Target total capital: $13,000

Method: Solve for bet amounts where both outcomes yield same payout

Side A (Kalshi YES @ $0.063):
  - Bet amount: $1,000
  - Shares purchased: $1,000 / $0.063 = 15,873 shares
  - Payout if wins: 15,873 × $1.00 = $15,873

Side B (Polymarket NO @ $0.92):
  - Bet amount: $12,000
  - Shares purchased: $12,000 / $0.92 = 13,043 shares
  - Payout if wins: 13,043 × $1.00 = $13,043

Total invested: $1,000 + $12,000 = $13,000
Minimum payout: $13,043 (worst case)
Guaranteed profit: $43 (0.33% ROI before fees)
```

**Key Formula:**
```python
# For arbitrary probabilities p1 and p2 where p1 + p2 < 1.0:
# Let B1 = bet on side 1, B2 = bet on side 2
#
# Constraint: B1/p1 = B2/p2 (equal payouts)
#
# For total capital C:
# B1 = C × p1 / (p1 + p2)
# B2 = C × p2 / (p1 + p2)
#
# Example with p1=0.063, p2=0.92, C=$13,000:
# B1 = $13,000 × 0.063 / 0.983 = $833
# B2 = $13,000 × 0.92 / 0.983 = $12,167
```

#### Fee Breakdown

```
Bet amounts: $1,000 (Kalshi) + $12,000 (Polymarket) = $13,000

Fee Breakdown:
├─ Kalshi (0.5%):      $1,000 × 0.005 = $5
├─ Polymarket (2%):    $12,000 × 0.02 = $240
├─ Gas/Bridge:         ~$10
└─ Total fees:         $255 (1.96% of capital)

Raw edge:           $43 (0.33%)
Less fees:          -$255 (1.96%)
─────────────────────────────
Net P&L:            -$212
Net edge:           -1.63% ❌
```

**Bot Decision:**
- ❌ Trade LOSES money after fees!
- ❌ Would be REJECTED immediately
- 💡 This is why fee analysis is critical

#### Alternative Example (Better Prices)

If the prices were slightly more favorable, the math would work:

```
Kalshi YES @ 6.96¢:    Bet $1,000 → Payout $14,367
Polymarket NO @ 92.0¢:  Bet $12,000 → Payout $13,044

Total invested: $13,000
Guaranteed payout: $13,044 (minimum)
Raw profit: $44
Fees: ~$255
Net P&L: -$211 ❌ Still unprofitable!
```

**Reality:** Even with better prices, fees kill this trade at $13k scale. You'd need:
- Either MUCH lower fees (< 0.5% total)
- Or a wider spread (e.g., 5% + 90% = 95%, leaving 5% edge)
- Or much larger scale to make fees < 1% of capital

---

### Step 4: Risk Analysis 🚨

```python
RiskAnalyzer evaluates:

1. Event Definition Risk:
   ├─ Similarity: 95% ✅
   ├─ Keywords: Both say "mayoral election" ✅
   └─ BUT: Need to verify PRIMARY vs GENERAL ⚠️

2. Timing Risk:
   ├─ Same end date ✅
   └─ Resolution sources: Need manual check ⚠️

3. Liquidity Risk:
   ├─ Kalshi: $50k liquidity → $50k position = 100% ❌
   ├─ Polymarket: $100k liquidity → $50k position = 50% ⚠️
   └─ HIGH SLIPPAGE RISK

4. Edge Risk:
   ├─ Net edge: 0.44% (THIN) ⚠️
   └─ Little margin for error

5. Regulatory Risk:
   ├─ Polymarket US restrictions ⚠️
   └─ Political market scrutiny ⚠️
```

**Overall Risk Score: 0.45 (MEDIUM-HIGH)**

**Risk Level: HIGH**

---

### Step 5: Position Sizing 📊

```python
# Base calculation (Kelly Criterion)
Base size = $100k × 0.05 = $5,000 (max 5% total capital per trade)

# Risk-adjusted sizing (High risk → Reduce to 30%)
Adjusted total = $5,000 × 0.30 = $1,500

# Proper bet allocation (using p1=0.063, p2=0.92, total=0.983):
Side A (Kalshi):  $1,500 × (0.063 / 0.983) = $96
Side B (Polymarket): $1,500 × (0.920 / 0.983) = $1,404

# Liquidity constraints:
Kalshi liquidity = $50k → Max safe = $5k (10%)
Polymarket liquidity = $100k → Max safe = $10k (10%)

# Both positions are well within liquidity limits ✅

Final position:
├─ Kalshi YES: $96
├─ Polymarket NO: $1,404
└─ Total capital: $1,500

Expected payout: ~$1,524 (either outcome)
Expected profit: $24 before fees
After fees (~$30): LOSING TRADE ❌
```

**Key Insight:** At small scale, fixed costs (gas, bridge) dominate and make the trade unprofitable.

---

### Step 6: Final Decision 🎯

**Configuration: Default (Conservative)**

```yaml
trading:
  threshold_spread: 0.01    # Require 1% edge
  auto_execute: false        # Manual review required
```

**Result:**
```
❌ TRADE REJECTED

Reasons:
1. NEGATIVE expected value (-1.63% after fees)
2. Fees ($255) exceed raw profit ($43)
3. Risk level: HIGH
4. Warnings:
   - ❌ Trade loses money at current prices and fee structure
   - ⚠️ Would need 3%+ spread to be profitable with these fees
   - ⚠️ Markets may not be equivalent - manual verification needed
   - ⚠️ Ensure compliance with Polymarket geographic restrictions
   - 💡 Proper bet sizing is asymmetric (not 50/50)!
```

---

## How to Make This Trade Execute

### Option 1: Get Better Prices (Required)

The current 6.3% + 92% = 98.3% spread is TOO TIGHT after fees.

**What you need:**
```
Target spread: < 95% (leaves 5% gross edge)

Example winning scenario:
├─ Kalshi YES @ 5.0¢
├─ Polymarket NO @ 90.0¢
├─ Combined: 95%
└─ Gross edge: 5% ($650 profit on $13k)

Fees: ~$255 (1.96%)
Net edge: ~3.0% ($390 profit) ✅
```

### Option 2: Lower Fees (Hard)

- Negotiate lower fees (VIP tier)
- Use lower-fee venues
- Batch multiple trades to amortize fixed costs

---

### Option 3: Manual Override (Not Recommended)

```bash
# Run with manual review
python main.py --dry-run

# Review the opportunity
# If comfortable with risks, execute manually via API
```

**Checklist Before Manual Execution:**
- [ ] Verified markets are for SAME election (not primary vs general)
- [ ] Read full rules on both platforms
- [ ] Confirmed resolution sources match
- [ ] Understood proper bet sizing (NOT 50/50 split!)
- [ ] Calculated bet amounts to equalize payouts
- [ ] Checked current liquidity is adequate for calculated bet sizes
- [ ] Calculated actual fees (may differ from estimates)
- [ ] Verified compliance with Polymarket restrictions
- [ ] Confirmed NET profit after ALL fees is positive
- [ ] Accept the asymmetric position sizes (e.g., $1k vs $12k)

---

## Real-World Execution Considerations

### 1. The Primary vs General Problem ⚠️

**CRITICAL CHECK:**
```
Kalshi market:     "NYC Mayor - PRIMARY election"
Polymarket market: "NYC Mayor - GENERAL election"

These are DIFFERENT events!
- Primary: June 2025
- General: November 2025
- Different candidates compete
```

**Before trading:**
- Read FULL market descriptions
- Check exact resolution criteria
- Verify both markets resolve on same outcome

---

### 2. Liquidity Reality Check

**Orderbook Depth:**
```
Kalshi YES side:
  $0.063 × 500 shares = $31.50 total
  $0.064 × 1,000 shares = $64.00 total
  $0.065 × 2,000 shares = $130.00 total
  Total depth at reasonable prices: $225.50
```

**With proper bet sizing ($1,000 on Kalshi side):**
```
Need to buy: $1,000 / $0.063 = ~15,873 shares
Available at $0.063: 500 shares = $31.50
Available at $0.064: 1,000 shares = $64.00
Available at $0.065: 2,000 shares = $130.00

To fill $1,000: Need to go DEEP into orderbook!
Average fill price: ~$0.070 (slippage: +11%)

Revised calculation:
├─ Kalshi avg fill: $0.070 (was $0.063)
├─ Polymarket fill: $0.920
├─ Combined: 0.990
└─ Raw edge: 1.0% (was 1.7%)

After fees (-1.96%): Net -0.96% ❌
```

**Result:** **Slippage makes bad trade even worse!**

**Key lesson:** Even though $1,000 << $50k liquidity, the BID side may be thin!

---

### 3. Fee Reality

**Detailed Fee Calculation (with proper bet sizing):**
```
Example position: $13,000 total

Kalshi side ($1,000):
├─ Trading fee (0.5%): $5
├─ Bank transfer in: $0
└─ Total: $5

Polymarket side ($12,000):
├─ Trading fee (2%): $240
├─ USD → USDC bridge: $25
├─ Gas (deposit): $15
├─ Gas (trade): $8
├─ Gas (withdraw): $15
└─ Total: $303

Combined fees: $308 (2.37% of $13k)

Raw edge (at 98.3%):   1.7% = $221
Less fees:             -$308
Less slippage:         -$100 (est)
─────────────────────────────
Net P&L:               -$187 ❌

Profit on $13k: NEGATIVE!
```

**Is it worth it?**
- Capital locked for days/weeks
- Execution risk
- Platform risk
- Regulatory risk
- **AND you LOSE money**

**Result: This trade doesn't work at these prices.**

---

## Recommended Approach for This Trade

### Scenario A: You See This Opportunity

1. **Don't rush** - arbitrage doesn't disappear instantly
2. **Verify event match** - Read full rules on both platforms
3. **Check actual liquidity** - Look at orderbook, not just totals
4. **Calculate real costs** - Include ALL fees and slippage
5. **Start small** - Trade $1k to test execution
6. **Scale if profitable** - Only increase if first trade works

### Scenario B: Bot Flags This

```
Bot Alert:
💰 OPPORTUNITY DETECTED
Edge: 0.44% (after fees)
Risk: HIGH
Action: MANUAL_REVIEW_REQUIRED
```

**Your Decision Tree:**
```
Is similarity = 100%?
├─ No → PASS
└─ Yes
    ├─ Can I verify event match?
    │   ├─ No → PASS
    │   └─ Yes
    │       ├─ Is liquidity adequate?
    │       │   ├─ No → PASS
    │       │   └─ Yes
    │       │       └─ Is edge > 1% after slippage?
    │       │           ├─ No → PASS
    │       │           └─ Yes → EXECUTE (small size)
```

---

## Key Learnings

### Critical Insight: Bet Sizing

**🚨 MOST IMPORTANT LESSON:**

You CANNOT bet equal amounts on each side when probabilities differ!

```
❌ WRONG: Bet $6,500 on each side
✅ RIGHT: Bet to equalize payouts

Formula:
Side A bet = Total × (Price_A / (Price_A + Price_B))
Side B bet = Total × (Price_B / (Price_A + Price_B))

Example (6.3% + 92% = 98.3%):
Side A: $13,000 × (0.063 / 0.983) = $833
Side B: $13,000 × (0.920 / 0.983) = $12,167
```

### What Makes This Trade Unprofitable:

1. ❌ **Fatal:** Spread too tight (98.3% combined)
2. ❌ **Fatal:** Fees (2.37%) exceed raw edge (1.7%)
3. ⚠️ **Concern:** Slippage further reduces edge
4. ⚠️ **Concern:** Risk of event definition mismatch
5. ⚠️ **Concern:** Asymmetric bet sizing (92% of capital on one side)

### What Would Make This Trade Profitable:

1. Spread < 95% (need 5%+ gross edge to cover fees)
2. Lower fees (< 1% total, or negotiate VIP rates)
3. Similarity score = 100% (identical wording)
4. Deep orderbook (to avoid slippage)
5. Verified event resolution match

### Bot's Value:

The bot correctly identifies that while this **looks** like 1.7% free money, the **reality** is:
- **NEGATIVE expected value** after fees (-1.63%)
- High execution risk
- Potential event mismatch
- Slippage concerns
- **Requires asymmetric bet sizing** (not 50/50!)

**By calculating proper bet sizing and accurate fees, the bot prevents you from losing money on what looks like arbitrage.**

---

## Conclusion

**The Cuomo trade is a perfect example of why "arbitrage" isn't always profitable.**

### Key Takeaways:

1. **Bet sizing is critical** - You must balance payouts, not bet amounts
2. **Fees matter enormously** - 2% fees kill a 1.7% edge instantly
3. **Spread must be wide** - Need 5%+ gross edge to be profitable with typical fees
4. **Math is unforgiving** - A trade that looks profitable at first glance loses money when calculated correctly

### The Orion bot would:
1. ✅ Detect the opportunity
2. ✅ **Calculate correct bet sizing** (asymmetric amounts)
3. ✅ Calculate accurate fees
4. ✅ Identify NEGATIVE expected value
5. ✅ **REJECT the trade** automatically
6. ✅ Flag why it's unprofitable

**This is exactly what you want from automated trading software - it does the complex math correctly and prevents you from taking losing trades.**

The bot serves as:
- Opportunity scanner ✅
- **Bet size calculator** ✅ (NOT 50/50!)
- Fee analyzer ✅
- Risk analyzer ✅
- **Sanity check** ✅ (rejects negative EV)
- Execution assistant ✅

**The #1 lesson: Never assume equal bet sizes! Always calculate proper payout-balanced positions.** 🎯
