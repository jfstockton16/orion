"""Polymarket API client using official py-clob-client SDK"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, OrderType
from py_clob_client.exceptions import PolyApiException
from src.utils.logger import setup_logger
from src.utils.validation import (
    validate_price,
    validate_size_usd,
    validate_market_id,
    ValidationError
)

logger = setup_logger("polymarket")


class PolymarketClient:
    """
    Client for interacting with Polymarket CLOB API using official SDK

    This wrapper provides async methods around the py-clob-client SDK
    and normalizes the interface to match our application's needs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        private_key: Optional[str] = None,
        chain_id: int = 137,  # Polygon mainnet
        host: str = "https://clob.polymarket.com"
    ):
        """
        Initialize Polymarket client

        Args:
            api_key: Polymarket API key (for CLOB API access)
            api_secret: Polymarket API secret
            api_passphrase: Polymarket API passphrase
            private_key: Ethereum wallet private key for signing orders (without 0x prefix)
            chain_id: Blockchain chain ID (137 for Polygon mainnet, 80001 for Mumbai testnet)
            host: CLOB API host URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.private_key = private_key
        self.chain_id = chain_id
        self.host = host
        self.client: Optional[ClobClient] = None

        # Market cache for token ID resolution
        self._market_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize client if credentials provided
        if private_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the py-clob-client"""
        try:
            # Create API credentials object if available
            creds = None
            if self.api_key and self.api_secret and self.api_passphrase:
                creds = ApiCreds(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    api_passphrase=self.api_passphrase
                )

            # Initialize CLOB client
            # The SDK handles all EIP-712 signing internally
            self.client = ClobClient(
                host=self.host,
                chain_id=self.chain_id,
                key=self.private_key,
                creds=creds
            )

            logger.info("Polymarket CLOB client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Polymarket client: {e}")
            self.client = None

    async def get_markets(self, limit: int = 100, active: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch active markets from Polymarket

        Args:
            limit: Maximum number of markets to fetch
            active: Only fetch active markets

        Returns:
            List of market dictionaries
        """
        if not self.client:
            logger.error("Client not initialized")
            return []

        try:
            # Run in executor since SDK is synchronous
            loop = asyncio.get_event_loop()
            markets = await loop.run_in_executor(
                None,
                lambda: self.client.get_markets()
            )

            # Filter and limit
            if active:
                markets = [m for m in markets if m.get('active', False)]

            markets = markets[:limit]

            # Cache markets for token ID lookups
            for market in markets:
                self._market_cache[market.get('condition_id', '')] = market

            logger.debug(f"Fetched {len(markets)} markets from Polymarket")
            return markets

        except Exception as e:
            logger.error(f"Error fetching Polymarket markets: {e}")
            return []

    async def get_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ID

        Args:
            market_id: Market condition ID

        Returns:
            Market dictionary or None
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        # Check cache first
        if market_id in self._market_cache:
            return self._market_cache[market_id]

        try:
            loop = asyncio.get_event_loop()
            market = await loop.run_in_executor(
                None,
                lambda: self.client.get_market(market_id)
            )

            if market:
                self._market_cache[market_id] = market

            return market

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
        if not self.client:
            logger.error("Client not initialized")
            return None

        try:
            loop = asyncio.get_event_loop()
            orderbook = await loop.run_in_executor(
                None,
                lambda: self.client.get_order_book(token_id)
            )
            return orderbook

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
        order_type: str = "GTC"
    ) -> Optional[Dict[str, Any]]:
        """
        Place an order on Polymarket using the official SDK

        The SDK handles all EIP-712 signing automatically.

        Args:
            token_id: Token ID to trade
            side: 'BUY' or 'SELL'
            size: Order size (number of contracts)
            price: Limit price (0.0 to 1.0)
            order_type: Order type (GTC, FOK, GTD)

        Returns:
            Order response or None
        """
        if not self.client:
            logger.error("Cannot place order - client not initialized")
            return None

        try:
            # Validate inputs
            validate_price(price)
            validate_size_usd(size, min_size=1.0, max_size=1000000.0)

            # Create order args
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side.upper(),
                fee_rate_bps=0,  # Will be filled by SDK
            )

            # Map order type
            sdk_order_type = OrderType.GTC  # Good til cancelled
            if order_type.upper() == "FOK":
                sdk_order_type = OrderType.FOK  # Fill or kill
            elif order_type.upper() == "GTD":
                sdk_order_type = OrderType.GTD  # Good til date

            # Place order using SDK (handles EIP-712 signing)
            logger.info(
                f"Placing Polymarket order: {side} {size} @ {price} "
                f"(token: {token_id})"
            )

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.create_order(order_args, sdk_order_type)
            )

            if result:
                logger.info(f"Order placed: {result.get('orderID')}")
                return result
            else:
                logger.error("Polymarket order failed - no result returned")
                return None

        except PolyApiException as e:
            logger.error(f"Polymarket API error placing order: {e}")
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
            Dictionary with USDC balance and allowance
        """
        if not self.client:
            logger.error("Cannot get balance - client not initialized")
            return None

        try:
            loop = asyncio.get_event_loop()
            balance_data = await loop.run_in_executor(
                None,
                lambda: self.client.get_balance()
            )

            return balance_data

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific order

        Args:
            order_id: Order ID to check

        Returns:
            Order status dictionary or None
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        try:
            loop = asyncio.get_event_loop()
            order = await loop.run_in_executor(
                None,
                lambda: self.client.get_order(order_id)
            )
            return order

        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successfully cancelled, False otherwise
        """
        if not self.client:
            logger.error("Cannot cancel order - client not initialized")
            return False

        try:
            logger.info(f"Cancelling Polymarket order: {order_id}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.cancel_order(order_id)
            )

            if result:
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def get_token_ids_for_market(self, market_id: str) -> Optional[Dict[str, str]]:
        """
        Get YES and NO token IDs for a market

        Args:
            market_id: Market condition ID

        Returns:
            Dictionary with 'yes' and 'no' token IDs, or None
        """
        market = await self.get_market_by_id(market_id)
        if not market:
            return None

        try:
            tokens = market.get('tokens', [])
            if len(tokens) >= 2:
                # Polymarket markets have 2 tokens: YES and NO
                # They're usually ordered as [YES, NO] but we should check the outcome field
                token_ids = {}
                for token in tokens:
                    outcome = token.get('outcome', '').lower()
                    token_id = token.get('token_id')
                    if outcome and token_id:
                        token_ids[outcome] = token_id

                # Return with standardized keys
                return {
                    'yes': token_ids.get('yes'),
                    'no': token_ids.get('no')
                }

            return None

        except Exception as e:
            logger.error(f"Error extracting token IDs from market {market_id}: {e}")
            return None

    async def close(self):
        """Close the client connection"""
        # py-clob-client doesn't require explicit cleanup
        self.client = None
        logger.debug("Polymarket client closed")

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
            'market_id': market.get('condition_id') or market.get('id'),
            'question': market.get('question', ''),
            'description': market.get('description', ''),
            'end_date': market.get('end_date_iso'),
            'active': market.get('active', False),
            'tokens': market.get('tokens', []),
            'volume': float(market.get('volume', 0)),
            'liquidity': float(market.get('liquidity', 0)),
            'raw_data': market
        }
