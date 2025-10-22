"""Tests for arbitrage detector"""

import pytest
from src.arbitrage.detector import ArbitrageDetector


@pytest.fixture
def detector():
    """Create detector instance"""
    config = {
        'trading': {
            'threshold_spread': 0.01,
            'min_trade_size_usd': 100,
            'max_trade_size_pct': 0.05,
            'target_liquidity_depth': 5000
        },
        'fees': {
            'kalshi_fee_pct': 0.007,
            'polymarket_fee_pct': 0.02,
            'blockchain_cost_usd': 5
        }
    }
    return ArbitrageDetector(config)


def test_calculate_spread(detector):
    """Test spread calculation"""
    spread = detector.calculate_spread(0.48, 0.51)
    assert spread == 0.99
    assert spread < 1.0


def test_calculate_edge(detector):
    """Test edge calculation"""
    edge = detector.calculate_edge(0.99, 0)
    assert edge == 0.01

    edge_with_fees = detector.calculate_edge(0.99, 0.005)
    assert edge_with_fees == 0.005


def test_position_sizing(detector):
    """Test position sizing"""
    size = detector.calculate_position_size(
        edge=0.02,
        bankroll=10000,
        kelly_fraction=0.25
    )

    assert size > 0
    assert size <= 500  # Max 5% of bankroll


def test_no_trade_on_small_edge(detector):
    """Test that small edges don't trigger trades"""
    kalshi_market = {
        'market_id': 'TEST-1',
        'question': 'Test question',
        'end_date': '2024-12-31',
        'liquidity': 10000
    }

    poly_market = {
        'market_id': 'TEST-2',
        'question': 'Test question',
        'end_date': '2024-12-31',
        'liquidity': 10000
    }

    # Spread too small (0.005 edge)
    opportunity = detector.detect_opportunity(
        kalshi_market,
        poly_market,
        kalshi_yes_price=0.495,
        polymarket_no_price=0.500,
        similarity_score=0.95,
        bankroll=10000
    )

    assert opportunity is None


def test_detect_valid_opportunity(detector):
    """Test detection of valid opportunity"""
    kalshi_market = {
        'market_id': 'TEST-1',
        'question': 'Test question',
        'end_date': '2024-12-31',
        'liquidity': 10000
    }

    poly_market = {
        'market_id': 'TEST-2',
        'question': 'Test question',
        'end_date': '2024-12-31',
        'liquidity': 10000
    }

    # Good spread (0.02 edge before fees)
    opportunity = detector.detect_opportunity(
        kalshi_market,
        poly_market,
        kalshi_yes_price=0.48,
        polymarket_no_price=0.50,
        similarity_score=0.95,
        bankroll=10000
    )

    assert opportunity is not None
    assert opportunity.spread == 0.98
    assert opportunity.position_size_usd > 0
