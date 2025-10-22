"""Event matching logic to find equivalent markets across exchanges"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger("matcher")


class EventMatcher:
    """Matches events across different exchanges"""

    def __init__(self, similarity_threshold: float = 0.85, date_tolerance_days: int = 1):
        """
        Initialize event matcher

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider a match
            date_tolerance_days: Maximum days difference for end dates
        """
        self.similarity_threshold = similarity_threshold
        self.date_tolerance_days = date_tolerance_days

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove punctuation except question marks
        text = re.sub(r'[^\w\s?]', '', text)

        # Common replacements
        replacements = {
            'will': '',
            'the': '',
            'be': '',
            'by': '',
            'on': '',
            'in': '',
            'at': '',
        }

        for old, new in replacements.items():
            text = text.replace(f' {old} ', f' {new} ')

        # Remove extra spaces again
        text = ' '.join(text.split())

        return text

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        return SequenceMatcher(None, norm1, norm2).ratio()

    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.split('.')[0].replace('Z', ''), fmt.replace('.%f', ''))
            except (ValueError, AttributeError):
                continue

        return None

    def dates_match(self, date1: Optional[str], date2: Optional[str]) -> bool:
        """
        Check if two dates match within tolerance

        Args:
            date1: First date string
            date2: Second date string

        Returns:
            True if dates match within tolerance
        """
        dt1 = self.parse_date(date1)
        dt2 = self.parse_date(date2)

        if dt1 is None or dt2 is None:
            # If we can't parse dates, be lenient
            return True

        diff = abs((dt1 - dt2).days)
        return diff <= self.date_tolerance_days

    def extract_keywords(self, text: str) -> set:
        """
        Extract important keywords from text

        Args:
            text: Input text

        Returns:
            Set of keywords
        """
        # Normalize text
        norm = self.normalize_text(text)

        # Common stop words to ignore
        stop_words = {
            'will', 'the', 'be', 'by', 'on', 'in', 'at', 'to', 'a', 'an',
            'is', 'are', 'was', 'were', 'have', 'has', 'had', 'for', 'of'
        }

        # Extract words
        words = set(norm.split())

        # Remove stop words and short words
        keywords = {w for w in words if len(w) > 2 and w not in stop_words}

        return keywords

    def keyword_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate keyword overlap ratio

        Args:
            text1: First text
            text2: Second text

        Returns:
            Overlap ratio between 0 and 1
        """
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)

        return len(intersection) / len(union) if union else 0.0

    def is_match(
        self,
        market1: Dict,
        market2: Dict,
        use_keywords: bool = True
    ) -> Tuple[bool, float]:
        """
        Determine if two markets match

        Args:
            market1: First market (from exchange 1)
            market2: Second market (from exchange 2)
            use_keywords: Also use keyword matching

        Returns:
            Tuple of (is_match, similarity_score)
        """
        # Extract questions
        q1 = market1.get('question', '')
        q2 = market2.get('question', '')

        if not q1 or not q2:
            return False, 0.0

        # Calculate text similarity
        text_similarity = self.calculate_similarity(q1, q2)

        # Calculate keyword overlap if enabled
        if use_keywords:
            keyword_similarity = self.keyword_overlap(q1, q2)
            # Weighted average: 70% text, 30% keywords
            combined_similarity = 0.7 * text_similarity + 0.3 * keyword_similarity
        else:
            combined_similarity = text_similarity

        # Check date match
        dates_ok = self.dates_match(
            market1.get('end_date'),
            market2.get('end_date')
        )

        # Must pass similarity threshold AND date check
        is_match = combined_similarity >= self.similarity_threshold and dates_ok

        logger.debug(
            f"Match check: '{q1[:50]}...' vs '{q2[:50]}...' = "
            f"{combined_similarity:.2f} (dates_ok={dates_ok})"
        )

        return is_match, combined_similarity

    def find_matches(
        self,
        kalshi_markets: List[Dict],
        polymarket_markets: List[Dict]
    ) -> List[Tuple[Dict, Dict, float]]:
        """
        Find all matching market pairs

        Args:
            kalshi_markets: List of Kalshi markets
            polymarket_markets: List of Polymarket markets

        Returns:
            List of tuples (kalshi_market, polymarket_market, similarity_score)
        """
        matches = []

        for km in kalshi_markets:
            best_match = None
            best_score = 0.0

            for pm in polymarket_markets:
                is_match, score = self.is_match(km, pm)

                if is_match and score > best_score:
                    best_match = pm
                    best_score = score

            if best_match:
                matches.append((km, best_match, best_score))
                logger.info(
                    f"Found match: {km.get('question', '')[:50]} <-> "
                    f"{best_match.get('question', '')[:50]} (score: {best_score:.2f})"
                )

        logger.info(f"Found {len(matches)} matching market pairs")
        return matches
