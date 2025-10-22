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
**Implied Arbitrage:** 1.7% edge

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
Kalshi YES:          $0.063
Polymarket NO:       $0.920
─────────────────────────────
Combined cost:       $0.983
Guaranteed payout:   $1.000
─────────────────────────────
Raw edge (pre-fee):  $0.017 (1.7%)
```

**Bot Action:** Calculates profitability with fees

---

### Step 3: Fee Modeling 💸

```
Position size: $100,000 total ($50k per side)

Fee Breakdown:
├─ Kalshi (0.5%):      $250
├─ Polymarket (2%):    $1,000
├─ Gas/Bridge:         $10
└─ Total fees:         $1,260 (1.26%)

Net Edge: 1.7% - 1.26% = 0.44%
Expected Profit: $440
```

**Bot Decision:**
- ✅ Net edge (0.44%) is BELOW default 1% threshold
- ⚠️ Trade would be REJECTED in standard config
- ⚠️ Could proceed if threshold lowered to 0.3%

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
Base size = $100k × 0.05 = $5,000 (max 5% per trade)

# Risk-adjusted sizing
High risk → Reduce to 30%
Adjusted size = $5,000 × 0.30 = $1,500

# BUT: Liquidity constraint
Kalshi liquidity = $50k
Max safe position = $50k × 10% = $5k
Polymarket liquidity = $100k
Max safe position = $100k × 10% = $10k

# Final position limited by risk AND liquidity
Final position: $1,500 per side = $3,000 total
```

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
1. Net edge (0.44%) < threshold (1.0%)
2. Risk level: HIGH
3. Warnings:
   - ⚠️ Edge is very thin - vulnerable to price movement
   - ⚠️ High slippage risk on Kalshi (100% of liquidity)
   - ⚠️ Markets may not be equivalent - manual verification needed
   - ⚠️ Ensure compliance with Polymarket geographic restrictions
```

---

## How to Make This Trade Execute

### Option 1: Lower Threshold (Not Recommended)

```yaml
# config/config.yaml
trading:
  threshold_spread: 0.003  # Accept 0.3% edge
```

**Result:** Trade would be flagged but still face HIGH risk warnings

---

### Option 2: Manual Override

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
- [ ] Checked current liquidity is adequate
- [ ] Calculated actual fees (may differ from estimates)
- [ ] Verified compliance with Polymarket restrictions
- [ ] Accept 0.44% ROI is accurate (no hidden costs)

---

### Option 3: Wait for Better Conditions

**Ideal Trade Would Have:**
```
✅ Net edge > 1.0%
✅ Similarity > 95%
✅ Position < 10% of liquidity
✅ Clear event definition match
✅ Adequate time to verify details
```

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
  $0.063 × 500 = $31.50
  $0.064 × 1000 = $64.00
  $0.065 × 2000 = $130.00
  Total: $225.50 depth

To fill $50k: Would need to go 200+ levels deep!
Average fill price: ~$0.08 (not $0.063)
```

**Actual spread after slippage:**
```
Kalshi avg fill:  $0.080 (slippage: +27%)
Polymarket fill:  $0.920
─────────────────────────────
Actual spread:    1.000
Net edge:         0.00% ❌
```

**Result:** **NO ARBITRAGE** after slippage!

---

### 3. Fee Reality

**Detailed Fee Calculation:**
```
Kalshi side ($50k):
├─ Trading fee (0.5%): $250
├─ Bank transfer in: $0
└─ Total: $250

Polymarket side ($50k):
├─ Trading fee (2%): $1,000
├─ USD → USDC bridge: $25
├─ Gas (deposit): $15
├─ Gas (trade): $8
├─ Gas (withdraw): $15
└─ Total: $1,063

Combined fees: $1,313 (1.31% of $100k)

Net edge: 1.7% - 1.31% - 0.3% (slippage) = 0.09%

Profit on $100k: $90 😬
```

**Is it worth it?**
- Capital locked for days/weeks
- Execution risk
- Platform risk
- Regulatory risk

**For $90 profit? Probably not.**

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

### What Makes This Trade Marginal:

1. ✅ **Good:** Clear arbitrage structure
2. ✅ **Good:** Liquid markets on both sides
3. ⚠️ **Concern:** Thin edge (1.7% pre-fee)
4. ⚠️ **Concern:** High fees eat most of edge
5. ⚠️ **Concern:** Liquidity may not support size
6. ❌ **Bad:** Risk of event definition mismatch

### What Would Make This Trade Great:

1. Edge > 3% (to absorb fees)
2. Similarity score = 100% (identical wording)
3. Position < 5% of liquidity
4. Verified event resolution match
5. Simple binary outcome (not complex conditions)

### Bot's Value:

The bot correctly identifies that while this **looks** like 1.7% free money, the **reality** is:
- Only ~0.44% edge after fees
- High execution risk
- Potential event mismatch
- Liquidity concerns

**By flagging these issues, the bot prevents you from taking a marginal trade that could easily go wrong.**

---

## Conclusion

**The Cuomo trade is a perfect example of why "arbitrage" isn't always risk-free.**

The Orion bot would:
1. ✅ Detect the opportunity
2. ✅ Calculate accurate fees
3. ✅ Identify risk factors
4. ✅ Flag for manual review
5. ✅ Recommend passing or trading small

**This is exactly what you want from automated trading software - it finds opportunities but doesn't blindly execute marginal trades.**

The bot serves as:
- Opportunity scanner ✅
- Risk analyzer ✅
- Sanity check ✅
- Execution assistant ✅

But YOU make the final call on marginal trades. 🎯
