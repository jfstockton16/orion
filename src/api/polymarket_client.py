"""Polymarket API client for fetching markets and placing orders"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from web3 import Web3
from eth_account import Account
from src.utils.logger import setup_logger

logger = setup_logger("polymarket")


class PolymarketClient:
    """Client for interacting with Polymarket CLOB API"""

    def __init__(self, api_key: Optional[str] = None, private_key: Optional[str] = None, proxy_url: str = "https://clob.polymarket.com"):
        """
        Initialize Polymarket client

        Args:
            api_key: Polymarket API key
            private_key: Ethereum wallet private key for signing
            proxy_url: Polymarket CLOB proxy URL
        """
        self.api_key = api_key
        self.private_key = private_key
        self.proxy_url = proxy_url
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize Web3 for signing if private key provided
        if private_key:
            self.w3 = Web3()
            self.account = Account.from_key(private_key)
        else:
            self.w3 = None
            self.account = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_markets(self, limit: int = 100, active: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch active markets from Polymarket

        Args:
            limit: Maximum number of markets to fetch
            active: Only fetch active markets

        Returns:
            List of market dictionaries
        """
        try:
            session = await self._ensure_session()
            url = f"{self.proxy_url}/markets"
            params = {
                'limit': limit,
                'active': str(active).lower()
            }

            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Fetched {len(data)} markets from Polymarket")
                    return data
                else:
                    logger.error(f"Failed to fetch markets: {response.status}")
                    return []

        except asyncio.TimeoutError:
            logger.error("Timeout fetching Polymarket markets")
            return []
        except Exception as e:
            logger.error(f"Error fetching Polymarket markets: {e}")
            return []

    async def get_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ID

        Args:
            market_id: Market ID

        Returns:
            Market dictionary or None
        """
        try:
            session = await self._ensure_session()
            url = f"{self.proxy_url}/markets/{market_id}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch market {market_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    async def get_orderbook(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch orderbook for a specific token

        Args:
            token_id: Token ID

        Returns:
            Orderbook dictionary with bids and asks
        """
        try:
            session = await self._ensure_session()
            url = f"{self.proxy_url}/book"
            params = {'token_id': token_id}

            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch orderbook for {token_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching orderbook for {token_id}: {e}")
            return None

    async def get_best_price(self, token_id: str, side: str) -> Optional[float]:
        """
        Get best bid or ask price for a token

        Args:
            token_id: Token ID
            side: 'buy' or 'sell'

        Returns:
            Best price or None
        """
        orderbook = await self.get_orderbook(token_id)
        if not orderbook:
            return None

        try:
            if side.lower() == 'buy':
                # Best ask (lowest sell price)
                asks = orderbook.get('asks', [])
                if asks:
                    return float(asks[0]['price'])
            else:
                # Best bid (highest buy price)
                bids = orderbook.get('bids', [])
                if bids:
                    return float(bids[0]['price'])

            return None

        except (IndexError, KeyError, ValueError) as e:
            logger.error(f"Error parsing orderbook: {e}")
            return None

    async def place_order(
        self,
        token_id: str,
        side: str,
        size: float,
        price: float,
        order_type: str = "LIMIT"
    ) -> Optional[Dict[str, Any]]:
        """
        Place an order on Polymarket

        Args:
            token_id: Token ID
            side: 'BUY' or 'SELL'
            size: Order size
            price: Limit price
            order_type: Order type (LIMIT, MARKET, etc.)

        Returns:
            Order response or None
        """
        if not self.account:
            logger.error("Cannot place order without private key")
            return None

        try:
            session = await self._ensure_session()
            url = f"{self.proxy_url}/order"

            # Build order payload
            order = {
                'token_id': token_id,
                'side': side.upper(),
                'size': str(size),
                'price': str(price),
                'type': order_type,
                'timestamp': int(datetime.now().timestamp())
            }

            # Sign order (simplified - real implementation would follow Polymarket's signing spec)
            # In production, you'd use Polymarket's SDK for proper order signing

            async with session.post(url, json=order, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Order placed: {result.get('order_id')}")
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
            Dictionary with USDC and token balances
        """
        if not self.account:
            logger.error("Cannot get balance without private key")
            return None

        try:
            session = await self._ensure_session()
            url = f"{self.proxy_url}/balance"
            params = {'address': self.account.address}

            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch balance: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Polymarket market data to standard format

        Args:
            market: Raw market data from Polymarket

        Returns:
            Normalized market dictionary
        """
        return {
            'exchange': 'polymarket',
            'market_id': market.get('id'),
            'question': market.get('question', ''),
            'description': market.get('description', ''),
            'end_date': market.get('end_date_iso'),
            'active': market.get('active', False),
            'tokens': market.get('tokens', []),
            'volume': float(market.get('volume', 0)),
            'liquidity': float(market.get('liquidity', 0)),
            'raw_data': market
        }
