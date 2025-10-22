#!/usr/bin/env python3
"""
Example: Bidirectional Arbitrage Detection

Demonstrates how the bot detects arbitrage in BOTH directions:
1. Kalshi YES + Polymarket NO
2. Polymarket YES + Kalshi NO

And automatically selects the more profitable direction.
"""

import sys
sys.path.insert(0, '/home/user/orion')

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
        'max_days_to_resolution': 30,
        'high_return_threshold': 0.05
    },
    'risk': {
        'max_open_positions': 20,
        'max_exposure_per_event': 0.10
    }
}


def main():
    print("\n" + "="*70)
    print("  BIDIRECTIONAL ARBITRAGE DETECTION")
    print("="*70 + "\n")

    detector = ArbitrageDetector(config)
    bankroll = 100000

    # Shared market data
    kalshi_market = {
        'market_id': 'KALSHI-BTC-100K',
        'question': 'Will Bitcoin reach $100,000 by end of month?',
        'end_date': '2024-12-31',
        'liquidity': 50000
    }

    polymarket_market = {
        'market_id': 'POLY-BTC-100K',
        'question': 'Will Bitcoin reach $100,000 by end of month?',
        'end_date': '2024-12-31',
        'liquidity': 100000
    }

    # =========================================================================
    # SCENARIO 1: Only Direction 1 has arbitrage
    # =========================================================================
    print("📊 SCENARIO 1: Arbitrage in Direction 1 Only\n")
    print("-" * 70)

    kalshi_yes = 0.45
    kalshi_no = 0.56  # Note: prices don't sum to 1.0 (market maker spread)
    polymarket_yes = 0.55
    polymarket_no = 0.46

    print(f"Prices:")
    print(f"  Kalshi:     YES = {kalshi_yes:.2f}, NO = {kalshi_no:.2f}")
    print(f"  Polymarket: YES = {polymarket_yes:.2f}, NO = {polymarket_no:.2f}\n")

    print(f"Direction 1: Kalshi YES ({kalshi_yes}) + Poly NO ({polymarket_no})")
    spread1 = kalshi_yes + polymarket_no
    print(f"  Combined: {spread1:.2f} → Edge: {1.0 - spread1:.2f} (1.0% - fees)")

    print(f"\nDirection 2: Poly YES ({polymarket_yes}) + Kalshi NO ({kalshi_no})")
    spread2 = polymarket_yes + kalshi_no
    print(f"  Combined: {spread2:.2f} → Edge: {1.0 - spread2:.2f} ❌ No arbitrage\n")

    # Detect best direction
    opportunity = detector.detect_best_direction(
        kalshi_market=kalshi_market,
        polymarket_market=polymarket_market,
        kalshi_yes_price=kalshi_yes,
        kalshi_no_price=kalshi_no,
        polymarket_yes_price=polymarket_yes,
        polymarket_no_price=polymarket_no,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opportunity:
        print(f"✅ OPPORTUNITY FOUND!")
        print(f"   Direction: {opportunity.trade_direction}")
        print(f"   Edge: {opportunity.edge*100:.2f}%")
        print(f"   Expected profit: ${opportunity.expected_profit:.2f}\n")
    else:
        print("❌ No profitable opportunity\n")

    # =========================================================================
    # SCENARIO 2: Only Direction 2 has arbitrage
    # =========================================================================
    print("\n" + "="*70)
    print("📊 SCENARIO 2: Arbitrage in Direction 2 Only\n")
    print("-" * 70)

    kalshi_yes = 0.55
    kalshi_no = 0.46
    polymarket_yes = 0.45
    polymarket_no = 0.56

    print(f"Prices:")
    print(f"  Kalshi:     YES = {kalshi_yes:.2f}, NO = {kalshi_no:.2f}")
    print(f"  Polymarket: YES = {polymarket_yes:.2f}, NO = {polymarket_no:.2f}\n")

    print(f"Direction 1: Kalshi YES ({kalshi_yes}) + Poly NO ({polymarket_no})")
    spread1 = kalshi_yes + polymarket_no
    print(f"  Combined: {spread1:.2f} → Edge: {1.0 - spread1:.2f} ❌ No arbitrage")

    print(f"\nDirection 2: Poly YES ({polymarket_yes}) + Kalshi NO ({kalshi_no})")
    spread2 = polymarket_yes + kalshi_no
    print(f"  Combined: {spread2:.2f} → Edge: {1.0 - spread2:.2f} (9.0% - fees)\n")

    opportunity = detector.detect_best_direction(
        kalshi_market=kalshi_market,
        polymarket_market=polymarket_market,
        kalshi_yes_price=kalshi_yes,
        kalshi_no_price=kalshi_no,
        polymarket_yes_price=polymarket_yes,
        polymarket_no_price=polymarket_no,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opportunity:
        print(f"✅ OPPORTUNITY FOUND!")
        print(f"   Direction: {opportunity.trade_direction}")
        print(f"   Edge: {opportunity.edge*100:.2f}%")
        print(f"   Expected profit: ${opportunity.expected_profit:.2f}\n")
    else:
        print("❌ No profitable opportunity\n")

    # =========================================================================
    # SCENARIO 3: BOTH directions have arbitrage
    # =========================================================================
    print("\n" + "="*70)
    print("📊 SCENARIO 3: Arbitrage in BOTH Directions\n")
    print("-" * 70)

    kalshi_yes = 0.44
    kalshi_no = 0.48
    polymarket_yes = 0.46
    polymarket_no = 0.47

    print(f"Prices:")
    print(f"  Kalshi:     YES = {kalshi_yes:.2f}, NO = {kalshi_no:.2f}")
    print(f"  Polymarket: YES = {polymarket_yes:.2f}, NO = {polymarket_no:.2f}\n")

    print(f"Direction 1: Kalshi YES ({kalshi_yes}) + Poly NO ({polymarket_no})")
    spread1 = kalshi_yes + polymarket_no
    edge1 = 1.0 - spread1
    print(f"  Combined: {spread1:.2f} → Edge: {edge1:.2f} ({edge1*100:.1f}%)")

    print(f"\nDirection 2: Poly YES ({polymarket_yes}) + Kalshi NO ({kalshi_no})")
    spread2 = polymarket_yes + kalshi_no
    edge2 = 1.0 - spread2
    print(f"  Combined: {spread2:.2f} → Edge: {edge2:.2f} ({edge2*100:.1f}%)\n")

    opportunity = detector.detect_best_direction(
        kalshi_market=kalshi_market,
        polymarket_market=polymarket_market,
        kalshi_yes_price=kalshi_yes,
        kalshi_no_price=kalshi_no,
        polymarket_yes_price=polymarket_yes,
        polymarket_no_price=polymarket_no,
        similarity_score=1.0,
        bankroll=bankroll
    )

    if opportunity:
        print(f"✅ BOTH DIRECTIONS PROFITABLE!")
        print(f"   Bot selected: {opportunity.trade_direction}")
        print(f"   (Highest expected profit)")
        print(f"   Edge: {opportunity.edge*100:.2f}%")
        print(f"   Expected profit: ${opportunity.expected_profit:.2f}\n")
    else:
        print("❌ No profitable opportunity\n")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("  KEY TAKEAWAYS")
    print("="*70 + "\n")

    print("✅ The bot automatically checks BOTH directions:")
    print("   1. Kalshi YES + Polymarket NO")
    print("   2. Polymarket YES + Kalshi NO\n")

    print("✅ Selects the MORE PROFITABLE direction")
    print("   (Based on expected profit after fees)\n")

    print("✅ You never miss an arbitrage opportunity")
    print("   regardless of which way prices are misaligned!\n")

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
