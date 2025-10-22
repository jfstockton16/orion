"""Kalshi API client for fetching markets and placing orders"""

import asyncio
import aiohttp
import base64
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger("kalshi")


class KalshiClient:
    """Client for interacting with Kalshi API"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, base_url: str = "https://api.elections.kalshi.com/trade-api/v2"):
        """
        Initialize Kalshi client

        Args:
            api_key: Kalshi API key
            api_secret: Kalshi API secret
            base_url: Kalshi API base URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _sign_request(self, method: str, path: str, body: str = "") -> str:
        """
        Sign API request using HMAC

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            body: Request body

        Returns:
            Signature string
        """
        if not self.api_secret:
            return ""

        timestamp = str(int(datetime.now().timestamp() * 1000))
        message = f"{timestamp}{method.upper()}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def login(self) -> bool:
        """
        Authenticate with Kalshi API

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key or not self.api_secret:
            logger.warning("No API credentials provided for Kalshi")
            return False

        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/login"
            payload = {
                'email': self.api_key,
                'password': self.api_secret
            }

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('token')
                    logger.info("Successfully authenticated with Kalshi")
                    return True
                else:
                    logger.error(f"Failed to authenticate with Kalshi: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error authenticating with Kalshi: {e}")
            return False

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        return headers

    async def get_markets(self, limit: int = 100, status: str = "open") -> List[Dict[str, Any]]:
        """
        Fetch markets from Kalshi

        Args:
            limit: Maximum number of markets to fetch
            status: Market status filter (open, closed, settled)

        Returns:
            List of market dictionaries
        """
        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/markets"
            params = {
                'limit': limit,
                'status': status
            }

            headers = await self._get_headers()

            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    markets = data.get('markets', [])
                    logger.debug(f"Fetched {len(markets)} markets from Kalshi")
                    return markets
                elif response.status == 401:
                    logger.warning("Unauthorized - attempting to re-login")
                    if await self.login():
                        return await self.get_markets(limit, status)
                    return []
                else:
                    logger.error(f"Failed to fetch markets: {response.status}")
                    return []

        except asyncio.TimeoutError:
            logger.error("Timeout fetching Kalshi markets")
            return []
        except Exception as e:
            logger.error(f"Error fetching Kalshi markets: {e}")
            return []

    async def get_market(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ticker

        Args:
            ticker: Market ticker symbol

        Returns:
            Market dictionary or None
        """
        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/markets/{ticker}"
            headers = await self._get_headers()

            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('market')
                else:
                    logger.error(f"Failed to fetch market {ticker}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching market {ticker}: {e}")
            return None

    async def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch orderbook for a specific market

        Args:
            ticker: Market ticker

        Returns:
            Orderbook dictionary with yes/no prices
        """
        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/markets/{ticker}/orderbook"
            headers = await self._get_headers()

            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch orderbook for {ticker}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching orderbook for {ticker}: {e}")
            return None

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
            session = await self._ensure_session()
            url = f"{self.base_url}/portfolio/orders"
            headers = await self._get_headers()

            payload = {
                'ticker': ticker,
                'client_order_id': f"{ticker}_{int(datetime.now().timestamp())}",
                'side': side.lower(),
                'action': action.lower(),
                'count': count,
                'type': order_type.lower(),
            }

            if order_type.lower() == 'limit':
                payload['yes_price'] = price if side.lower() == 'yes' else None
                payload['no_price'] = price if side.lower() == 'no' else None

            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Order placed: {result.get('order', {}).get('order_id')}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Failed to place order: {response.status} - {error}")
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
        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/portfolio/balance"
            headers = await self._get_headers()

            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'balance': float(data.get('balance', 0)) / 100,  # Convert cents to dollars
                        'payout': float(data.get('payout', 0)) / 100
                    }
                else:
                    logger.error(f"Failed to fetch balance: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get open positions

        Returns:
            List of position dictionaries
        """
        try:
            session = await self._ensure_session()
            url = f"{self.base_url}/portfolio/positions"
            headers = await self._get_headers()

            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('positions', [])
                else:
                    logger.error(f"Failed to fetch positions: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

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
