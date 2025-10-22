#!/usr/bin/env python3
"""
Example: Cuomo NYC Mayoral Election Arbitrage

This demonstrates how the bot would analyze and handle the real-world
Cuomo arbitrage opportunity between Kalshi and Polymarket.
"""

import sys
sys.path.insert(0, '/home/user/orion')

from src.arbitrage.matcher import EventMatcher
from src.arbitrage.detector import ArbitrageDetector

# Market data for the Cuomo trade
kalshi_market = {
    'market_id': 'NYC-MAYOR-CUOMO-2025',
    'question': 'Will Andrew Cuomo win the NYC mayoral election?',
    'description': 'Resolves YES if Andrew Cuomo wins the general election for NYC Mayor',
    'end_date': '2025-11-04',
    'active': True,
    'volume': 500000,
    'liquidity': 50000,
    'exchange': 'kalshi'
}

polymarket_market = {
    'market_id': '0x1234abcd',
    'question': 'Will Andrew Cuomo win the NYC mayoral election?',
    'description': 'Resolves YES if Andrew Cuomo is elected NYC Mayor',
    'end_date': '2025-11-04',
    'active': True,
    'volume': 750000,
    'liquidity': 100000,
    'exchange': 'polymarket'
}

# Actual prices from the example
KALSHI_YES_PRICE = 0.063  # 6.3%
POLYMARKET_NO_PRICE = 0.920  # 92%

# Configuration
config = {
    'trading': {
        'threshold_spread': 0.01,  # 1% minimum
        'min_trade_size_usd': 100,
        'max_trade_size_pct': 0.05,  # Max 5% per trade
        'target_liquidity_depth': 5000,
        'slippage_tolerance': 0.002
    },
    'fees': {
        'kalshi_fee_pct': 0.005,  # 0.5% (lower end of range)
        'polymarket_fee_pct': 0.02,  # 2%
        'blockchain_cost_usd': 5  # Gas + bridge costs
    },
    'risk': {
        'max_open_positions': 20,
        'max_exposure_per_event': 0.10,
        'max_daily_loss_pct': 0.05
    }
}


def main():
    print("\n" + "="*70)
    print("  CUOMO NYC MAYORAL ELECTION ARBITRAGE ANALYSIS")
    print("="*70 + "\n")

    # Step 1: Event Matching
    print("📊 STEP 1: EVENT MATCHING\n")
    matcher = EventMatcher(similarity_threshold=0.85)

    is_match, similarity = matcher.is_match(kalshi_market, polymarket_market)

    print(f"Kalshi:     {kalshi_market['question']}")
    print(f"Polymarket: {polymarket_market['question']}")
    print(f"\nSimilarity Score: {similarity:.2%}")
    print(f"Match Status: {'✅ MATCHED' if is_match else '❌ NO MATCH'}\n")

    # Step 2: Price Analysis
    print("\n" + "-"*70)
    print("💰 STEP 2: PRICE ANALYSIS\n")

    spread = KALSHI_YES_PRICE + POLYMARKET_NO_PRICE
    raw_edge = 1.0 - spread

    print(f"Kalshi YES price:      ${KALSHI_YES_PRICE:.3f} ({KALSHI_YES_PRICE*100:.1f}%)")
    print(f"Polymarket NO price:   ${POLYMARKET_NO_PRICE:.3f} ({POLYMARKET_NO_PRICE*100:.1f}%)")
    print(f"\nCombined cost:         ${spread:.3f}")
    print(f"Guaranteed payout:     $1.000")
    print(f"Raw edge (pre-fees):   ${raw_edge:.3f} ({raw_edge*100:.2f}%)\n")

    # Step 3: Arbitrage Detection with Risk Analysis
    print("\n" + "-"*70)
    print("🔍 STEP 3: ARBITRAGE DETECTION & RISK ANALYSIS\n")

    detector = ArbitrageDetector(config)
    bankroll = 100000  # $100k starting capital

    opportunity = detector.detect_opportunity(
        kalshi_market=kalshi_market,
        polymarket_market=polymarket_market,
        kalshi_yes_price=KALSHI_YES_PRICE,
        polymarket_no_price=POLYMARKET_NO_PRICE,
        similarity_score=similarity,
        bankroll=bankroll
    )

    if opportunity:
        print("✅ ARBITRAGE OPPORTUNITY DETECTED!\n")

        print(f"Position Size:         ${opportunity.position_size_usd:,.2f}")
        print(f"  Kalshi contracts:    {opportunity.kalshi_contracts:,}")
        print(f"  Polymarket size:     {opportunity.polymarket_size:.2f} USDC\n")

        print(f"Fee Breakdown:")
        print(f"  Kalshi fee:          ${opportunity.kalshi_fee:.2f}")
        print(f"  Polymarket fee:      ${opportunity.polymarket_fee:.2f}")
        print(f"  Total fees:          ${opportunity.total_fees:.2f} ({opportunity.total_fees/opportunity.position_size_usd*100:.2f}%)\n")

        print(f"Net Edge:              {opportunity.edge*100:.2f}%")
        print(f"Expected Profit:       ${opportunity.expected_profit:.2f}")
        print(f"Expected ROI:          {opportunity.expected_roi*100:.2f}%\n")

        print(f"Risk Assessment:")
        print(f"  Risk Level:          {opportunity.risk_level.upper()}")
        print(f"  Risk Score:          {opportunity.risk_score:.2f}")

        if opportunity.risk_warnings:
            print(f"\n  ⚠️  Risk Warnings:")
            for warning in opportunity.risk_warnings:
                print(f"      {warning}")

        # Scaling analysis
        print("\n" + "-"*70)
        print("📈 SCALING ANALYSIS\n")

        # Calculate how much we could deploy at different scales
        scales = [10000, 50000, 100000]

        print("If we deployed different amounts:\n")
        for scale in scales:
            scale_ratio = scale / opportunity.position_size_usd
            scaled_profit = opportunity.expected_profit * scale_ratio

            print(f"  ${scale:,} deployment → ${scaled_profit:,.2f} profit")

        print("\n⚠️  IMPORTANT CONSIDERATIONS:")
        print("  • Event definition must match exactly (primary vs general)")
        print("  • Both markets must resolve to same outcome")
        print("  • Watch for slippage on large orders")
        print("  • Consider USD↔USDC bridge costs")
        print("  • Verify regulatory compliance (US users on Polymarket)")
        print("  • Monitor for resolution timing differences")

    else:
        print("❌ NO PROFITABLE OPPORTUNITY")
        print("\nReason: Edge is insufficient after fees and risk adjustments")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
