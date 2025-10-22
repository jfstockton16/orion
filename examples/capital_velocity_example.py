#!/usr/bin/env python3
"""
Example: Capital Velocity and Compounding Analysis

Demonstrates how the bot prioritizes fast-resolving arbitrage opportunities
to maximize compounding velocity.
"""

import sys
sys.path.insert(0, '/home/user/orion')

from datetime import datetime, timedelta
from src.arbitrage.detector import ArbitrageDetector

# Configuration
config = {
    'trading': {
        'threshold_spread': 0.01,
        'min_trade_size_usd': 100,
        'max_trade_size_pct': 0.05,
        'target_liquidity_depth': 5000
    },
    'fees': {
        'kalshi_fee_pct': 0.005,
        'polymarket_fee_pct': 0.02,
        'blockchain_cost_usd': 5
    },
    'capital': {
        'max_days_to_resolution': 30,  # Reject > 30 days
        'high_return_threshold': 0.05  # Unless return >= 5%
    },
    'risk': {
        'max_open_positions': 20,
        'max_exposure_per_event': 0.10
    }
}


def create_market(question, days_ahead):
    """Create a sample market"""
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    return {
        'market_id': f'TEST-{days_ahead}D',
        'question': question,
        'end_date': end_date,
        'liquidity': 50000,
        'exchange': 'test'
    }


def main():
    print("\n" + "="*70)
    print("  CAPITAL VELOCITY & COMPOUNDING ANALYSIS")
    print("="*70 + "\n")

    detector = ArbitrageDetector(config)
    bankroll = 100000

    # Scenario 1: 7-day event with 1.5% edge
    print("📊 SCENARIO 1: Short-term Opportunity (7 days)")
    print("-" * 70)

    market_short = create_market("Will Bitcoin hit $100k in next week?", 7)
    opp_short = detector.detect_opportunity(
        kalshi_market=market_short,
        polymarket_market=market_short,
        kalshi_yes_price=0.48,
        polymarket_no_price=0.51,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opp_short:
        print(f"✅ ACCEPTED")
        print(f"   Days to resolution: {opp_short.days_to_resolution}")
        print(f"   Edge: {opp_short.edge*100:.2f}%")
        print(f"   Annualized ROI: {opp_short.annualized_roi*100:.1f}%")
        print(f"   Expected profit: ${opp_short.expected_profit:.2f}")
        print(f"\n   ✅ GREAT FOR COMPOUNDING - Capital turns over quickly!\n")
    else:
        print("❌ REJECTED\n")

    # Scenario 2: 60-day event with 1.5% edge
    print("\n📊 SCENARIO 2: Medium-term Opportunity (60 days, 1.5% edge)")
    print("-" * 70)

    market_medium = create_market("Election outcome in 2 months", 60)
    opp_medium = detector.detect_opportunity(
        kalshi_market=market_medium,
        polymarket_market=market_medium,
        kalshi_yes_price=0.48,
        polymarket_no_price=0.51,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opp_medium:
        print(f"✅ ACCEPTED")
        print(f"   Days to resolution: {opp_medium.days_to_resolution}")
        print(f"   Edge: {opp_medium.edge*100:.2f}%")
        print(f"   Annualized ROI: {opp_medium.annualized_roi*100:.1f}%")
    else:
        print(f"❌ REJECTED")
        print(f"   Reason: Exceeds 30-day maximum for modest returns")
        print(f"   Capital locked too long with only ~1.5% return\n")

    # Scenario 3: 60-day event with 6% edge (high return exception)
    print("\n📊 SCENARIO 3: Medium-term with High Return (60 days, 6% edge)")
    print("-" * 70)

    opp_high = detector.detect_opportunity(
        kalshi_market=market_medium,
        polymarket_market=market_medium,
        kalshi_yes_price=0.45,
        polymarket_no_price=0.49,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opp_high:
        print(f"✅ ACCEPTED (High-return exception)")
        print(f"   Days to resolution: {opp_high.days_to_resolution}")
        print(f"   Edge: {opp_high.edge*100:.2f}%")
        print(f"   Annualized ROI: {opp_high.annualized_roi*100:.1f}%")
        print(f"   Expected profit: ${opp_high.expected_profit:.2f}")
        print(f"\n   ✅ 6% return justifies longer lock-up period!\n")
    else:
        print("❌ REJECTED (fees consumed edge)\n")

    # Scenario 4: 90-day event with 10% edge
    print("\n📊 SCENARIO 4: Long-term with Exceptional Return (90 days, 10% edge)")
    print("-" * 70)

    market_long = create_market("Major event in 3 months", 90)
    opp_long = detector.detect_opportunity(
        kalshi_market=market_long,
        polymarket_market=market_long,
        kalshi_yes_price=0.42,
        polymarket_no_price=0.48,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opp_long:
        print(f"✅ ACCEPTED (Exceptional return)")
        print(f"   Days to resolution: {opp_long.days_to_resolution}")
        print(f"   Edge: {opp_long.edge*100:.2f}%")
        print(f"   Annualized ROI: {opp_long.annualized_roi*100:.1f}%")
        print(f"   Expected profit: ${opp_long.expected_profit:.2f}")
        print(f"\n   ✅ 10% return is worth the wait!\n")
    else:
        print("❌ REJECTED\n")

    # Compounding comparison
    print("\n" + "="*70)
    print("  COMPOUNDING COMPARISON")
    print("="*70 + "\n")

    print("Strategy A: Take 7-day trades at 1.5% each")
    print("  Compound 12 times in 90 days: (1.015)^12 = 1.196 = 19.6% total\n")

    print("Strategy B: Take one 90-day trade at 10%")
    print("  Single trade: 1.10 = 10% total\n")

    print("Winner: Strategy A (fast compounding) by 9.6 percentage points!\n")

    print("This is why the bot prioritizes fast-resolving opportunities.")
    print("Capital velocity is crucial for maximizing returns.\n")

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
