# Risk Management Guide for Cross-Exchange Arbitrage

## Overview

While cross-exchange arbitrage is often presented as "risk-free," real-world implementation carries several important risks that must be managed carefully.

## Key Risk Categories

### 1. Event Definition Risk (CRITICAL)

**The Problem:**
Markets that appear similar may actually be for different events.

**Real Example - Cuomo Trade:**
```
Kalshi:     "Will Andrew Cuomo win the NYC mayoral PRIMARY?"
Polymarket: "Will Andrew Cuomo win the NYC mayoral GENERAL election?"
```

These are DIFFERENT events:
- Primary happens in June
- General happens in November
- Different candidates, different outcomes

**How the Bot Handles It:**

The risk analyzer checks for:
- Keyword mismatches: "primary" vs "general", "runoff", "plurality", "majority"
- Low similarity scores (< 90%)
- Description/subtitle differences

**Risk Mitigation:**
```yaml
# In config/config.yaml
trading:
  min_similarity_for_auto_execute: 0.95  # Require very high match

risk:
  manual_review_keywords:
    - primary
    - general
    - runoff
    - plurality
```

**Action Required:**
- Always manually review markets before first execution
- Read the FULL market rules on both platforms
- Check resolution sources
- Verify the exact event and timing

---

### 2. Fee Structure Risk

**The Problem:**
Fees can eliminate thin arbitrage edges.

**Real Fees:**
- **Kalshi**: 0.5% - 0.7% trading fee
- **Polymarket**: Up to 2% trading fee
- **Gas costs**: $5 - $50+ depending on network congestion
- **Bridge costs**: USD ↔ USDC conversion fees
- **Withdrawal fees**: Moving funds between platforms

**Example Calculation:**
```
Raw edge:           1.7%
Kalshi fee (0.5%):  $250
Poly fee (2%):      $1,000
Gas:                $10
Total fees:         $1,260 (1.26%)

Net edge: 1.7% - 1.26% = 0.44%
```

**How the Bot Handles It:**

The detector includes comprehensive fee modeling:
```python
# Automatically deducts all fees before reporting edge
net_edge = raw_edge - total_fee_percentage

# Only proceeds if net edge > threshold
if net_edge < config.threshold_spread:
    return None  # Reject trade
```

**Configuration:**
```yaml
fees:
  kalshi_fee_pct: 0.005        # 0.5% (verify current rate)
  polymarket_fee_pct: 0.02     # 2.0% (verify current rate)
  blockchain_cost_usd: 10      # Average gas cost
  bridge_cost_pct: 0.001       # USD/USDC conversion
  withdrawal_fee_usd: 0        # If applicable
```

---

### 3. Liquidity & Slippage Risk

**The Problem:**
Your order may move the market price against you.

**Example:**
```
Orderbook shows:
  Best bid: $0.92 (500 contracts)
  Next bid: $0.91 (1000 contracts)
  Next bid: $0.90 (2000 contracts)

Your order: 2000 contracts
Fills at:
  500 @ $0.92 = $460
  1000 @ $0.91 = $910
  500 @ $0.90 = $450

Average fill: $0.913 (worse than expected $0.92)
```

**How the Bot Handles It:**

1. **Liquidity Check:**
```python
# Position should be < 10% of available liquidity
if position_size > 0.10 * market_liquidity:
    # Reduce position or reject
```

2. **Slippage Protection:**
```python
# Use limit orders only (no market orders)
# Add slippage tolerance to limit price
limit_price = expected_price * (1 + slippage_tolerance)
```

3. **Risk-Adjusted Sizing:**
```python
# Reduce position size for low liquidity
if liquidity_ratio > 0.05:
    position_size *= 0.5  # Cut size in half
```

**Configuration:**
```yaml
trading:
  target_liquidity_depth: 5000    # Minimum $ per side
  slippage_tolerance: 0.002       # 0.2% max slippage
  max_position_liquidity_ratio: 0.10  # Max 10% of book
```

---

### 4. Resolution Timing Risk

**The Problem:**
Markets may resolve at different times, creating temporary exposure.

**Example:**
```
Event: Presidential election
Kalshi:     Resolves when AP calls it (Nov 5, 11pm)
Polymarket: Resolves when certified (Dec 15)

Gap: 40 days of single-sided exposure
```

**Risks During Gap:**
- Price movements
- Counterparty risk
- Opportunity cost
- Margin requirements

**How the Bot Handles It:**

Currently: **Limited protection** - logs warning only

**Recommended Manual Process:**
1. Check resolution sources for both markets
2. Estimate timing gap
3. Factor into profitability:
   ```
   Time-adjusted ROI = (profit - cost_of_capital) / capital / days
   ```

**Future Enhancement:**
```python
# Adjust position size based on timing gap
if resolution_gap_days > 30:
    position_size *= 0.5
```

---

### 5. Regulatory & Compliance Risk

**The Problem:**
Different platforms have different jurisdictions and restrictions.

**Kalshi:**
- CFTC-regulated (US)
- US persons allowed
- Limited markets (only CFTC-approved)
- KYC/AML required

**Polymarket:**
- Offshore (Polygon blockchain)
- Geographic restrictions for US users
- Broader market selection
- Uses crypto (USDC)

**Legal Considerations:**

1. **US Users on Polymarket:**
   - Officially restricted
   - Enforcement risk
   - Check current legal status

2. **Tax Implications:**
   - Kalshi: Treated as commodities trading
   - Polymarket: May be treated as crypto gains
   - Consult tax professional

3. **Position Limits:**
   - Some markets have position limits
   - Check per-user caps

**How to Stay Compliant:**

1. **Know Your Jurisdiction:**
```yaml
# config/config.yaml
compliance:
  jurisdiction: "US"  # or "non-US"
  respect_platform_restrictions: true
```

2. **Only Trade Allowed Markets:**
- Verify market legality in your jurisdiction
- Check platform terms of service
- Understand position limits

3. **Maintain Records:**
- Bot logs all trades to database
- Keep records for tax reporting
- Document arbitrage strategy

---

### 6. Platform/Counterparty Risk

**The Problem:**
Exchange could have technical issues, become insolvent, or restrict withdrawals.

**Historical Examples:**
- Exchange outages during high volatility
- Withdrawal delays
- Platform insolvency

**Mitigation Strategies:**

1. **Diversify Exposure:**
```yaml
capital:
  max_per_exchange_pct: 0.60  # Never > 60% on one platform
```

2. **Regular Withdrawals:**
- Don't let capital accumulate unnecessarily
- Withdraw profits regularly
- Keep minimum needed balance

3. **Monitor Platform Health:**
- Track withdrawal times
- Watch for API issues
- Monitor social media for problems

---

### 7. Execution Risk

**The Problem:**
One leg of the trade fills but the other doesn't.

**Example:**
```
1. Buy YES on Kalshi: ✅ FILLED
2. Buy NO on Polymarket: ❌ REJECTED (insufficient balance)

Result: Directional exposure (not arbitrage)
```

**How the Bot Handles It:**

1. **Pre-Flight Checks:**
```python
# Verify balances before placing orders
if kalshi_balance < required_kalshi:
    return "Insufficient Kalshi balance"
if poly_balance < required_poly:
    return "Insufficient Polymarket balance"
```

2. **Concurrent Execution:**
```python
# Place both orders simultaneously
kalshi_order, poly_order = await asyncio.gather(
    place_kalshi_order(),
    place_polymarket_order()
)
```

3. **Rollback on Failure:**
```python
if not both_filled:
    # Cancel/offset the filled order
    await unwind_position(filled_order)
```

**Best Practices:**
- Maintain adequate balance on both exchanges
- Use limit orders (not market orders)
- Monitor fill rates
- Have rollback procedures

---

## Risk Scoring System

The bot assigns risk scores (0-1) based on:

| Factor | Low Risk | Medium Risk | High Risk | Critical |
|--------|----------|-------------|-----------|----------|
| Similarity | > 95% | 90-95% | 85-90% | < 85% |
| Edge | > 2% | 1-2% | 0.5-1% | < 0.5% |
| Liquidity | > 10x | 5-10x | 2-5x | < 2x |
| Definition | Identical | Very close | Similar | Different |

**Overall Risk Level:**
- **Low** (< 0.3): Auto-execute OK
- **Medium** (0.3-0.5): Reduce position 30%
- **High** (0.5-0.7): Reduce position 70%
- **Critical** (> 0.7): Do not execute

---

## Recommended Configuration for Conservative Trading

```yaml
# config/config.yaml

trading:
  threshold_spread: 0.015         # Require 1.5% edge minimum
  max_trade_size_pct: 0.03        # Max 3% per trade (not 5%)
  min_similarity_score: 0.95      # Require very high match
  auto_execute: false             # Manual review for safety

risk:
  max_open_positions: 10          # Limit open positions
  max_exposure_per_event: 0.05    # Max 5% per event (not 10%)
  max_daily_loss_pct: 0.02        # Stop at 2% daily loss

fees:
  kalshi_fee_pct: 0.007           # Use conservative (higher) fee estimate
  polymarket_fee_pct: 0.02
  blockchain_cost_usd: 15         # Account for gas spikes
  safety_buffer_pct: 0.005        # Add 0.5% safety margin
```

---

## Manual Review Checklist

Before executing any arbitrage trade:

- [ ] Read FULL market rules on both platforms
- [ ] Verify event definitions are identical
- [ ] Check resolution sources match
- [ ] Confirm end dates are same
- [ ] Calculate fees accurately
- [ ] Verify sufficient liquidity
- [ ] Check for position limits
- [ ] Confirm regulatory compliance
- [ ] Review historical resolution times
- [ ] Verify adequate balance on both exchanges
- [ ] Check for any platform announcements/issues

---

## When to Override the Bot

**DON'T Execute If:**
- Similarity score < 95%
- Edge after fees < 1%
- Position would be > 10% of liquidity
- Event definitions contain "primary" vs "general"
- You don't fully understand the market rules
- Platform has recent technical issues
- Regulatory status is uncertain

**DO Execute If:**
- All risk checks pass
- Manually verified event match
- Adequate liquidity
- Net edge > 1.5%
- Clear resolution criteria
- Both platforms operational
- Compliance confirmed

---

## Emergency Procedures

**If One Leg Fails:**
1. Immediately cancel unfilled order
2. Assess filled position
3. Options:
   - Close position at market
   - Offset with opposite trade
   - Hold if favorable

**If Platform Goes Down:**
1. Stop all new trades immediately
2. Document open positions
3. Contact platform support
4. Prepare to hedge on other venues if needed

**If Prices Move Against You:**
1. Check if arbitrage still exists
2. Calculate actual P&L
3. Consider cutting position if loss exceeds threshold
4. Review what went wrong

---

## Summary

Cross-exchange arbitrage is **NOT risk-free**, but risks can be managed through:

1. ✅ Careful event matching and verification
2. ✅ Accurate fee modeling
3. ✅ Liquidity-aware position sizing
4. ✅ Risk-based adjustments
5. ✅ Regulatory compliance
6. ✅ Platform diversification
7. ✅ Robust execution logic

**Golden Rule:** When in doubt, don't trade. Miss opportunities rather than take uncertain risks.
