# Capital Velocity & Compounding Strategy

## The Compounding Problem

**Question:** Should you take a 1% return in 7 days or a 3% return in 90 days?

**Naive Answer:** 3% is bigger than 1%, so take the 90-day trade.

**Correct Answer:** The 7-day trade compounds **12 times** in 90 days, giving you ~12.7% total vs just 3%. **Capital velocity matters!**

## Why This Bot Prioritizes Fast Resolution

The Orion arbitrage bot is optimized for **compounding velocity** rather than absolute returns per trade.

### The Math

**Scenario A: Fast Turnaround**
- 1.5% edge, 7-day resolution
- Can execute ~52 times per year
- Annualized ROI: ~110% (compounded)

**Scenario B: Slow Turnaround**
- 3% edge, 90-day resolution
- Can execute ~4 times per year
- Annualized ROI: ~12.5% (compounded)

**Winner: Scenario A** — despite lower per-trade return!

## Bot's Time-Based Rules

### Default Configuration

```yaml
capital:
  max_days_to_resolution: 30      # Reject trades > 30 days out
  high_return_threshold: 0.05     # UNLESS return >= 5%
```

### Decision Logic

| Days | Edge | Decision | Reasoning |
|------|------|----------|-----------|
| 7 | 1.0% | ✅ ACCEPT | Fast compounding (52x/year) |
| 7 | 0.5% | ✅ ACCEPT | Still compounds quickly |
| 14 | 1.5% | ✅ ACCEPT | Good velocity (26x/year) |
| 30 | 2.0% | ✅ ACCEPT | Acceptable (12x/year) |
| 45 | 2.0% | ❌ REJECT | Too slow for modest return |
| 45 | 6.0% | ✅ ACCEPT | High return exception |
| 90 | 3.0% | ❌ REJECT | Poor capital efficiency |
| 90 | 10.0% | ✅ ACCEPT | Exceptional return justifies wait |

### Annualized ROI Calculation

The bot calculates annualized ROI for comparison:

```python
annualized_roi = edge * (365 / days_to_resolution)
```

Examples:
- 1% in 7 days = **52.1% annualized**
- 2% in 30 days = **24.3% annualized**
- 5% in 90 days = **20.3% annualized**
- 10% in 180 days = **20.3% annualized**

## Real-World Example

### Cuomo Trade Revisited

**Original Trade:**
- Edge: 1.7% → ~0.44% after fees
- Days to resolution: ~180 days (if election date)
- Annualized ROI: 0.44% × (365/180) = **0.89%**

**Bot Decision:** ❌ REJECT

**Reasoning:**
1. Capital locked for 6 months
2. Less than 1% annualized return
3. Opportunity cost: Could compound smaller trades 12+ times
4. Not worth the event definition risk

### Better Alternative

**7-Day Trade:**
- Edge: 0.5% after fees
- Days to resolution: 7 days
- Annualized ROI: 0.5% × (365/7) = **26.1%**

**Bot Decision:** ✅ ACCEPT

**Compounding Impact:**
- Execute similar trade weekly for 6 months
- ~26 trades × 0.5% ≈ **13.9% total** (compounded)
- **15x better** than the Cuomo trade!

## Practical Implications

### What This Means for Trading

1. **Prioritize Quick Events**
   - Sports games (resolve in hours/days)
   - Short-term political events
   - Earnings announcements
   - Weekly economic data

2. **Avoid Slow Events** (unless exceptional return)
   - Elections months away
   - Long-term predictions
   - Quarterly/annual events

3. **Calculate Opportunity Cost**
   - Always ask: "What else could I do with this capital?"
   - Compare annualized ROIs, not raw edges

### Compounding Table

Here's what happens to $100k with different strategies:

| Strategy | Per Trade | Frequency | After 1 Year |
|----------|-----------|-----------|--------------|
| Weekly 0.5% | 0.5% | 52x | $129,200 |
| Biweekly 1% | 1.0% | 26x | $129,750 |
| Monthly 2% | 2.0% | 12x | $126,800 |
| Quarterly 5% | 5.0% | 4x | $121,550 |
| Annually 20% | 20.0% | 1x | $120,000 |

**Winner:** Small, frequent trades win through compounding!

## Configuration Examples

### Aggressive Compounding (Recommended)

```yaml
capital:
  max_days_to_resolution: 14      # Only 2-week max
  high_return_threshold: 0.08     # Require 8%+ for longer
```

**Effect:** Maximizes compounding velocity, only takes exceptional long-term trades

### Conservative Compounding (Default)

```yaml
capital:
  max_days_to_resolution: 30      # Monthly max
  high_return_threshold: 0.05     # Require 5%+ for longer
```

**Effect:** Balanced approach, allows some medium-term opportunities

### Patient Investing

```yaml
capital:
  max_days_to_resolution: 90      # Quarterly max
  high_return_threshold: 0.03     # Require 3%+ for longer
```

**Effect:** Will take longer-term trades if return is adequate

## Dashboard Metrics

The bot tracks capital velocity:

- **Average Days to Resolution**: How long capital is locked
- **Turnover Rate**: How many times you've recycled capital
- **Annualized ROI**: Actual compounded returns
- **Capital Efficiency Score**: Profit per day of capital deployment

### Example Dashboard

```
Capital Efficiency Metrics:
────────────────────────────────
Avg Days to Resolution:     12.3 days
Annual Turnover Rate:       29.7x
Compounded Returns YTD:     +18.4%
Annualized ROI:             24.7%
Best Trade (by annual):     52.1% (7-day, 1% edge)
Worst Trade (by annual):    8.2% (45-day, 1% edge)
```

## Advanced: Optimal Position Sizing by Time

The bot can weight position sizes by expected annualized return:

```python
# Larger positions for faster trades
if annualized_roi > 0.50:  # >50% annualized
    position_multiplier = 1.5  # 50% larger
elif annualized_roi > 0.30:  # >30% annualized
    position_multiplier = 1.2  # 20% larger
elif annualized_roi < 0.15:  # <15% annualized
    position_multiplier = 0.7  # 30% smaller
```

This further optimizes for capital velocity.

## Summary: The Compounding Mindset

Traditional arbitrage thinking:
- ❌ "This trade has a 3% edge, that one has 1%"
- ❌ "Always take the higher edge"
- ❌ "Don't worry about time"

**Orion compounding thinking:**
- ✅ "This 3% trade takes 90 days, that 1% takes 7 days"
- ✅ "The 1% trade gives 52% annualized, the 3% gives 12%"
- ✅ "Time is money - compound faster"

## Key Takeaway

**The bot automatically rejects trades with poor capital velocity, even if the raw edge looks good. This is by design to maximize your long-term compounded returns.**

When you see:
```
❌ REJECTED: Capital locked 60 days for only 2.00% return.
   Annualized ROI: 12.2%
```

The bot is **protecting** you from opportunity cost and helping you find better uses for your capital.
