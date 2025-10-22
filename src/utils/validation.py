"""Input validation and sanitization utilities"""

import re
from typing import Any, Optional
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_ticker(ticker: str, max_length: int = 50) -> str:
    """
    Validate and sanitize market ticker

    Args:
        ticker: Market ticker symbol
        max_length: Maximum allowed length

    Returns:
        Sanitized ticker

    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise ValidationError("Ticker must be a non-empty string")

    if len(ticker) > max_length:
        raise ValidationError(f"Ticker exceeds maximum length of {max_length}")

    # Allow only alphanumeric, hyphens, and underscores
    if not re.match(r'^[A-Za-z0-9_-]+$', ticker):
        raise ValidationError("Ticker contains invalid characters")

    return ticker.upper()


def validate_price(price: float, min_price: float = 0.01, max_price: float = 0.99) -> float:
    """
    Validate price is within acceptable range

    Args:
        price: Price to validate (0.00 to 1.00)
        min_price: Minimum allowed price
        max_price: Maximum allowed price

    Returns:
        Validated price

    Raises:
        ValidationError: If price is invalid
    """
    if not isinstance(price, (int, float, Decimal)):
        raise ValidationError(f"Price must be numeric, got {type(price)}")

    price = float(price)

    if price < 0 or price > 1.0:
        raise ValidationError(f"Price {price} outside valid range [0.0, 1.0]")

    if price < min_price:
        raise ValidationError(f"Price {price} below minimum {min_price}")

    if price > max_price:
        raise ValidationError(f"Price {price} above maximum {max_price}")

    # Check for NaN or Infinity
    if not (price == price):  # NaN check
        raise ValidationError("Price is NaN")

    if price == float('inf') or price == float('-inf'):
        raise ValidationError("Price is infinite")

    return price


def validate_kalshi_price_cents(price_cents: int) -> int:
    """
    Validate Kalshi price in cents

    Args:
        price_cents: Price in cents (1-99)

    Returns:
        Validated price in cents

    Raises:
        ValidationError: If price is invalid
    """
    if not isinstance(price_cents, int):
        raise ValidationError(f"Kalshi price must be integer, got {type(price_cents)}")

    if price_cents < 1 or price_cents > 99:
        raise ValidationError(f"Kalshi price {price_cents} outside valid range [1, 99]")

    return price_cents


def validate_quantity(quantity: int, min_qty: int = 1, max_qty: int = 100000) -> int:
    """
    Validate order quantity

    Args:
        quantity: Number of contracts
        min_qty: Minimum allowed quantity
        max_qty: Maximum allowed quantity

    Returns:
        Validated quantity

    Raises:
        ValidationError: If quantity is invalid
    """
    if not isinstance(quantity, int):
        raise ValidationError(f"Quantity must be integer, got {type(quantity)}")

    if quantity < min_qty:
        raise ValidationError(f"Quantity {quantity} below minimum {min_qty}")

    if quantity > max_qty:
        raise ValidationError(f"Quantity {quantity} exceeds maximum {max_qty}")

    return quantity


def validate_size_usd(size: float, min_size: float = 10.0, max_size: float = 1000000.0) -> float:
    """
    Validate trade size in USD

    Args:
        size: Trade size in USD
        min_size: Minimum trade size
        max_size: Maximum trade size

    Returns:
        Validated size

    Raises:
        ValidationError: If size is invalid
    """
    if not isinstance(size, (int, float, Decimal)):
        raise ValidationError(f"Size must be numeric, got {type(size)}")

    size = float(size)

    if size < min_size:
        raise ValidationError(f"Size ${size} below minimum ${min_size}")

    if size > max_size:
        raise ValidationError(f"Size ${size} exceeds maximum ${max_size}")

    if size < 0:
        raise ValidationError(f"Size ${size} cannot be negative")

    return size


def validate_side(side: str, allowed_sides: Optional[list] = None) -> str:
    """
    Validate order side

    Args:
        side: Order side (e.g., 'buy', 'sell', 'yes', 'no')
        allowed_sides: List of allowed sides (optional)

    Returns:
        Sanitized side (lowercase)

    Raises:
        ValidationError: If side is invalid
    """
    if not isinstance(side, str):
        raise ValidationError(f"Side must be string, got {type(side)}")

    side = side.lower().strip()

    if not side:
        raise ValidationError("Side cannot be empty")

    if allowed_sides and side not in allowed_sides:
        raise ValidationError(f"Side '{side}' not in allowed sides: {allowed_sides}")

    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type

    Args:
        order_type: Order type (e.g., 'limit', 'market')

    Returns:
        Sanitized order type

    Raises:
        ValidationError: If order type is invalid
    """
    allowed_types = ['limit', 'market']

    if not isinstance(order_type, str):
        raise ValidationError(f"Order type must be string, got {type(order_type)}")

    order_type = order_type.lower().strip()

    if order_type not in allowed_types:
        raise ValidationError(f"Order type '{order_type}' not in allowed types: {allowed_types}")

    return order_type


def sanitize_string(value: str, max_length: int = 1000, allow_special: bool = False) -> str:
    """
    Sanitize string input to prevent injection attacks

    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        allow_special: Whether to allow special characters

    Returns:
        Sanitized string

    Raises:
        ValidationError: If string is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"Expected string, got {type(value)}")

    if len(value) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")

    # Remove null bytes
    value = value.replace('\x00', '')

    if not allow_special:
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', ';', '|', '`', '$', '\n', '\r']
        for char in dangerous_chars:
            value = value.replace(char, '')

    return value.strip()


def validate_market_id(market_id: str, exchange: str = None) -> str:
    """
    Validate market ID format

    Args:
        market_id: Market identifier
        exchange: Exchange name (optional)

    Returns:
        Validated market ID

    Raises:
        ValidationError: If market ID is invalid
    """
    if not market_id or not isinstance(market_id, str):
        raise ValidationError("Market ID must be a non-empty string")

    if len(market_id) > 200:
        raise ValidationError("Market ID exceeds maximum length")

    # Basic sanitization - allow alphanumeric, hyphens, underscores
    if not re.match(r'^[A-Za-z0-9_-]+$', market_id):
        raise ValidationError("Market ID contains invalid characters")

    return market_id


def validate_percentage(value: float, min_pct: float = 0.0, max_pct: float = 1.0) -> float:
    """
    Validate percentage value (0.0 to 1.0)

    Args:
        value: Percentage value
        min_pct: Minimum allowed percentage
        max_pct: Maximum allowed percentage

    Returns:
        Validated percentage

    Raises:
        ValidationError: If percentage is invalid
    """
    if not isinstance(value, (int, float, Decimal)):
        raise ValidationError(f"Percentage must be numeric, got {type(value)}")

    value = float(value)

    if value < min_pct or value > max_pct:
        raise ValidationError(f"Percentage {value} outside valid range [{min_pct}, {max_pct}]")

    return value
