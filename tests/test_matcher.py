"""Tests for event matcher"""

import pytest
from src.arbitrage.matcher import EventMatcher


@pytest.fixture
def matcher():
    """Create matcher instance"""
    return EventMatcher(similarity_threshold=0.85, date_tolerance_days=1)


def test_normalize_text(matcher):
    """Test text normalization"""
    text1 = "Will the Fed raise rates by December 2024?"
    text2 = "will the fed raise rates by december 2024"

    norm1 = matcher.normalize_text(text1)
    norm2 = matcher.normalize_text(text2)

    assert norm1 == norm2


def test_calculate_similarity(matcher):
    """Test similarity calculation"""
    text1 = "Will Bitcoin reach $100k in 2024?"
    text2 = "Will Bitcoin reach $100k in 2024?"

    similarity = matcher.calculate_similarity(text1, text2)
    assert similarity == 1.0

    text3 = "Will Ethereum reach $10k in 2024?"
    similarity2 = matcher.calculate_similarity(text1, text3)
    assert 0.5 < similarity2 < 0.9


def test_keyword_extraction(matcher):
    """Test keyword extraction"""
    text = "Will the Federal Reserve raise interest rates by March 2024?"
    keywords = matcher.extract_keywords(text)

    assert 'federal' in keywords
    assert 'reserve' in keywords
    assert 'raise' in keywords
    assert 'interest' in keywords
    assert 'rates' in keywords

    # Stop words should be removed
    assert 'the' not in keywords
    assert 'by' not in keywords


def test_date_matching(matcher):
    """Test date matching"""
    date1 = "2024-12-31"
    date2 = "2024-12-31"

    assert matcher.dates_match(date1, date2) is True

    date3 = "2024-12-30"
    assert matcher.dates_match(date1, date3) is True  # Within 1 day

    date4 = "2024-12-28"
    assert matcher.dates_match(date1, date4) is False  # > 1 day


def test_market_matching(matcher):
    """Test market matching"""
    market1 = {
        'question': 'Will Bitcoin reach $100,000 by end of 2024?',
        'end_date': '2024-12-31'
    }

    market2 = {
        'question': 'Will Bitcoin reach $100k by the end of 2024?',
        'end_date': '2024-12-31'
    }

    is_match, score = matcher.is_match(market1, market2)

    assert is_match is True
    assert score > 0.85


def test_market_not_matching(matcher):
    """Test markets that shouldn't match"""
    market1 = {
        'question': 'Will Bitcoin reach $100,000 by end of 2024?',
        'end_date': '2024-12-31'
    }

    market2 = {
        'question': 'Will Ethereum reach $10,000 by end of 2024?',
        'end_date': '2024-12-31'
    }

    is_match, score = matcher.is_match(market1, market2)

    assert is_match is False
    assert score < 0.85
