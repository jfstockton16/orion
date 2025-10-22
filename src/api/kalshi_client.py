"""Kalshi API client for fetching markets and placing orders"""

import asyncio
import aiohttp
import base64
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from src.utils.logger import setup_logger
from src.utils.validation import (
    validate_ticker,
    validate_kalshi_price_cents,
    validate_quantity,
    validate_side,
    validate_order_type,
    ValidationError
)

logger = setup_logger("kalshi")


class KalshiClient:
    """Client for interacting with Kalshi API using RSA-PSS signing"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        private_key_pem: Optional[str] = None,
        base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    ):
        """
        Initialize Kalshi client with API key and private key for RSA-PSS signing

        Args:
            api_key: Kalshi API key ID
            private_key_path: Path to RSA private key file (PEM format)
            private_key_pem: RSA private key as PEM string (alternative to path)
            base_url: Kalshi API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.private_key = None

        # Load private key
        if private_key_pem:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
                password=None,
                backend=default_backend()
            )
        elif private_key_path:
            try:
                with open(private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
            except Exception as e:
                logger.error(f"Failed to load private key from {private_key_path}: {e}")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _sign_request(self, method: str, path: str) -> Dict[str, str]:
        """
        Sign API request using RSA-PSS (Kalshi API v2 standard)

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path WITHOUT query string (e.g., /markets, /portfolio/orders)

        Returns:
            Dictionary with authentication headers
        """
        if not self.api_key or not self.private_key:
            logger.warning("Missing API key or private key for signing")
            return {}

        # Create timestamp in milliseconds
        timestamp_ms = str(int(time.time() * 1000))

        # Create message to sign: timestamp + METHOD + path (no query params)
        # Per Kalshi docs: signature over "timestamp + METHOD + PATH"
        message = f"{timestamp_ms}{method.upper()}{path}"

        try:
            # Sign using RSA-PSS with SHA-256
            signature = self.private_key.sign(
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Base64 encode the signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')

            # Return required headers
            return {
                'KALSHI-ACCESS-KEY': self.api_key,
                'KALSHI-ACCESS-TIMESTAMP': timestamp_ms,
                'KALSHI-ACCESS-SIGNATURE': signature_b64,
                'Content-Type': 'application/json'
            }

        except Exception as e:
            logger.error(f"Error signing request: {e}")
            return {}

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated API request

        Args:
            method: HTTP method
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            json_data: JSON body for POST/PUT requests

        Returns:
            Response JSON or None
        """
        # Get path without query params for signing
        path = endpoint if endpoint.startswith('/') else f'/{endpoint}'

        # Sign the request
        headers = self._sign_request(method, path)
        if not headers:
            logger.error("Failed to sign request - missing credentials")
            return None

        try:
            session = await self._ensure_session()
            url = f"{self.base_url}{path}"

            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout on {method} {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            return None

    async def get_markets(self, limit: int = 100, status: str = "open") -> List[Dict[str, Any]]:
        """
        Fetch markets from Kalshi

        Args:
            limit: Maximum number of markets to fetch
            status: Market status filter (open, closed, settled)

        Returns:
            List of market dictionaries
        """
        params = {
            'limit': limit,
            'status': status
        }

        data = await self._request('GET', '/markets', params=params)
        if data:
            markets = data.get('markets', [])
            logger.debug(f"Fetched {len(markets)} markets from Kalshi")
            return markets
        return []

    async def get_market(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ticker

        Args:
            ticker: Market ticker symbol

        Returns:
            Market dictionary or None
        """
        data = await self._request('GET', f'/markets/{ticker}')
        return data.get('market') if data else None

    async def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch orderbook for a specific market

        Args:
            ticker: Market ticker

        Returns:
            Orderbook dictionary with yes/no prices
        """
        return await self._request('GET', f'/markets/{ticker}/orderbook')

    async def get_best_price(self, ticker: str, side: str) -> Optional[float]:
        """
        Get best yes or no price for a market

        Args:
            ticker: Market ticker
            side: 'yes' or 'no'

        Returns:
            Best price or None
        """
        orderbook = await self.get_orderbook(ticker)
        if not orderbook:
            return None

        try:
            if side.lower() == 'yes':
                # Best yes ask price
                yes_asks = orderbook.get('yes', {}).get('asks', [])
                if yes_asks:
                    return float(yes_asks[0][0]) / 100  # Kalshi prices in cents
            else:
                # Best no ask price
                no_asks = orderbook.get('no', {}).get('asks', [])
                if no_asks:
                    return float(no_asks[0][0]) / 100

            return None

        except (IndexError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing orderbook: {e}")
            return None

    async def place_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        price: int,
        order_type: str = "limit"
    ) -> Optional[Dict[str, Any]]:
        """
        Place an order on Kalshi

        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            price: Price in cents (1-99)
            order_type: Order type (limit, market)

        Returns:
            Order response or None
        """
        try:
            # Validate inputs
            ticker = validate_ticker(ticker)
            side = validate_side(side, allowed_sides=['yes', 'no'])
            action = validate_side(action, allowed_sides=['buy', 'sell'])
            count = validate_quantity(count, min_qty=1, max_qty=10000)
            price = validate_kalshi_price_cents(price)
            order_type = validate_order_type(order_type)

            payload = {
                'ticker': ticker,
                'client_order_id': f"{ticker}_{int(datetime.now().timestamp())}",
                'side': side,
                'action': action,
                'count': count,
                'type': order_type,
            }

            # Add price based on side (only include the relevant field)
            if order_type == 'limit':
                if side == 'yes':
                    payload['yes_price'] = price
                else:
                    payload['no_price'] = price

            result = await self._request('POST', '/portfolio/orders', json_data=payload)

            if result:
                logger.info(f"Order placed: {result.get('order', {}).get('order_id')}")
                return result
            return None

        except ValidationError as e:
            logger.error(f"Order validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def get_balance(self) -> Optional[Dict[str, float]]:
        """
        Get account balance

        Returns:
            Dictionary with balance information
        """
        data = await self._request('GET', '/portfolio/balance')
        if data:
            return {
                'balance': float(data.get('balance', 0)) / 100,  # Convert cents to dollars
                'payout': float(data.get('payout', 0)) / 100
            }
        return None

    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get open positions

        Returns:
            List of position dictionaries
        """
        data = await self._request('GET', '/portfolio/positions')
        return data.get('positions', []) if data else []

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific order

        Args:
            order_id: Order ID to check

        Returns:
            Order status dictionary or None
        """
        return await self._request('GET', f'/portfolio/orders/{order_id}')

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successfully cancelled, False otherwise
        """
        result = await self._request('DELETE', f'/portfolio/orders/{order_id}')
        if result is not None:  # DELETE returns 204 with no content
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        return False

    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Kalshi market data to standard format

        Args:
            market: Raw market data from Kalshi

        Returns:
            Normalized market dictionary
        """
        return {
            'exchange': 'kalshi',
            'market_id': market.get('ticker'),
            'question': market.get('title', ''),
            'description': market.get('subtitle', ''),
            'end_date': market.get('close_time'),
            'active': market.get('status') == 'open',
            'volume': float(market.get('volume', 0)),
            'liquidity': float(market.get('open_interest', 0)),
            'yes_price': None,  # To be filled from orderbook
            'no_price': None,   # To be filled from orderbook
            'raw_data': market
        }
