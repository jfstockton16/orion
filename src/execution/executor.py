"""Trade execution engine"""

import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from src.api.kalshi_client import KalshiClient
from src.api.polymarket_client import PolymarketClient
from src.arbitrage.detector import ArbitrageOpportunity
from src.utils.logger import setup_logger

logger = setup_logger("executor")


@dataclass
class ExecutionResult:
    """Result of trade execution"""

    success: bool
    position_id: str
    kalshi_order_id: Optional[str] = None
    polymarket_order_id: Optional[str] = None
    kalshi_filled: bool = False
    polymarket_filled: bool = False
    actual_cost: float = 0.0
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'position_id': self.position_id,
            'kalshi_order_id': self.kalshi_order_id,
            'polymarket_order_id': self.polymarket_order_id,
            'kalshi_filled': self.kalshi_filled,
            'polymarket_filled': self.polymarket_filled,
            'actual_cost': self.actual_cost,
            'error_message': self.error_message,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }


class TradeExecutor:
    """Executes arbitrage trades across exchanges"""

    def __init__(
        self,
        kalshi_client: KalshiClient,
        polymarket_client: PolymarketClient,
        config: Dict,
        dry_run: bool = True
    ):
        """
        Initialize trade executor

        Args:
            kalshi_client: Kalshi API client
            polymarket_client: Polymarket API client
            config: Configuration dictionary
            dry_run: If True, simulate trades without execution
        """
        self.kalshi = kalshi_client
        self.polymarket = polymarket_client
        self.config = config
        self.dry_run = dry_run

        self.slippage_tolerance = config.get('trading', {}).get('slippage_tolerance', 0.002)

    async def execute_arbitrage(
        self,
        opportunity: ArbitrageOpportunity
    ) -> ExecutionResult:
        """
        Execute arbitrage trade

        Args:
            opportunity: ArbitrageOpportunity to execute

        Returns:
            ExecutionResult
        """
        position_id = f"arb_{int(datetime.now().timestamp())}"

        logger.info(
            f"{'[DRY RUN] ' if self.dry_run else ''}Executing arbitrage trade {position_id}"
        )

        if self.dry_run:
            # Simulate execution
            return ExecutionResult(
                success=True,
                position_id=position_id,
                kalshi_order_id=f"kalshi_sim_{position_id}",
                polymarket_order_id=f"poly_sim_{position_id}",
                kalshi_filled=True,
                polymarket_filled=True,
                actual_cost=opportunity.position_size_usd,
                executed_at=datetime.now()
            )

        # Execute both legs concurrently
        try:
            kalshi_task = self._execute_kalshi_leg(opportunity)
            poly_task = self._execute_polymarket_leg(opportunity)

            kalshi_result, poly_result = await asyncio.gather(
                kalshi_task,
                poly_task,
                return_exceptions=True
            )

            # Check for errors
            kalshi_success = not isinstance(kalshi_result, Exception) and kalshi_result is not None
            poly_success = not isinstance(poly_result, Exception) and poly_result is not None

            if not kalshi_success or not poly_success:
                error_msg = []
                if not kalshi_success:
                    error_msg.append(f"Kalshi: {kalshi_result}")
                if not poly_success:
                    error_msg.append(f"Polymarket: {poly_result}")

                # Need to cancel/rollback if one side failed
                await self._handle_partial_fill(
                    kalshi_success, poly_success,
                    kalshi_result if kalshi_success else None,
                    poly_result if poly_success else None
                )

                return ExecutionResult(
                    success=False,
                    position_id=position_id,
                    error_message="; ".join(error_msg)
                )

            # Both filled successfully
            return ExecutionResult(
                success=True,
                position_id=position_id,
                kalshi_order_id=kalshi_result.get('order_id') if kalshi_result else None,
                polymarket_order_id=poly_result.get('order_id') if poly_result else None,
                kalshi_filled=True,
                polymarket_filled=True,
                actual_cost=opportunity.position_size_usd,
                executed_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return ExecutionResult(
                success=False,
                position_id=position_id,
                error_message=str(e)
            )

    async def _execute_kalshi_leg(
        self,
        opportunity: ArbitrageOpportunity
    ) -> Optional[Dict]:
        """
        Execute Kalshi leg of arbitrage

        Args:
            opportunity: ArbitrageOpportunity

        Returns:
            Order result or None
        """
        try:
            # Calculate limit price with slippage tolerance
            limit_price = opportunity.kalshi_yes_price * (1 + self.slippage_tolerance)
            limit_price_cents = min(99, int(limit_price * 100))

            logger.info(
                f"Placing Kalshi order: {opportunity.kalshi_contracts} contracts @ "
                f"{limit_price_cents} cents"
            )

            result = await self.kalshi.place_order(
                ticker=opportunity.kalshi_market_id,
                side='yes',
                action='buy',
                count=opportunity.kalshi_contracts,
                price=limit_price_cents,
                order_type='limit'
            )

            if result:
                logger.info(f"Kalshi order placed: {result.get('order', {}).get('order_id')}")
                return result.get('order')
            else:
                logger.error("Kalshi order failed")
                return None

        except Exception as e:
            logger.error(f"Error placing Kalshi order: {e}")
            raise

    async def _execute_polymarket_leg(
        self,
        opportunity: ArbitrageOpportunity
    ) -> Optional[Dict]:
        """
        Execute Polymarket leg of arbitrage

        Args:
            opportunity: ArbitrageOpportunity

        Returns:
            Order result or None
        """
        try:
            # Calculate limit price with slippage tolerance
            limit_price = opportunity.polymarket_no_price * (1 + self.slippage_tolerance)
            limit_price = min(0.99, limit_price)

            logger.info(
                f"Placing Polymarket order: {opportunity.polymarket_size:.2f} size @ "
                f"{limit_price:.4f}"
            )

            # Note: Polymarket uses token IDs, not market IDs directly
            # In practice, you'd need to resolve the NO token ID for the market
            token_id = self._get_no_token_id(opportunity.polymarket_market_id)

            result = await self.polymarket.place_order(
                token_id=token_id,
                side='BUY',
                size=opportunity.polymarket_size,
                price=limit_price,
                order_type='LIMIT'
            )

            if result:
                logger.info(f"Polymarket order placed: {result.get('order_id')}")
                return result
            else:
                logger.error("Polymarket order failed")
                return None

        except Exception as e:
            logger.error(f"Error placing Polymarket order: {e}")
            raise

    def _get_no_token_id(self, market_id: str) -> str:
        """
        Get NO token ID for a Polymarket market

        Args:
            market_id: Polymarket market ID

        Returns:
            NO token ID
        """
        # In production, this would query the market data
        # For now, return market_id as placeholder
        # Polymarket markets have separate token IDs for YES and NO
        return f"{market_id}_NO"

    async def _handle_partial_fill(
        self,
        kalshi_filled: bool,
        poly_filled: bool,
        kalshi_order: Optional[Dict],
        poly_order: Optional[Dict]
    ) -> None:
        """
        Handle case where only one leg filled - CRITICAL FOR RISK MANAGEMENT

        This method immediately unwinds any filled position if the other leg fails,
        preventing naked directional exposure.

        Args:
            kalshi_filled: Whether Kalshi order filled
            poly_filled: Whether Polymarket order filled
            kalshi_order: Kalshi order data
            poly_order: Polymarket order data
        """
        logger.error(
            f"🚨 PARTIAL FILL DETECTED - Kalshi: {kalshi_filled}, Poly: {poly_filled}"
        )

        # Critical: Unwind any filled positions immediately
        unwind_tasks = []

        if kalshi_filled and kalshi_order:
            logger.warning(
                f"⚠️  Unwinding Kalshi position: {kalshi_order.get('order_id')}"
            )
            unwind_tasks.append(self._unwind_kalshi_position(kalshi_order))

        if poly_filled and poly_order:
            logger.warning(
                f"⚠️  Unwinding Polymarket position: {poly_order.get('order_id')}"
            )
            unwind_tasks.append(self._unwind_polymarket_position(poly_order))

        if unwind_tasks:
            # Execute all unwinds concurrently
            results = await asyncio.gather(*unwind_tasks, return_exceptions=True)

            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Unwind task {i} failed: {result}")
                elif result:
                    logger.info(f"✅ Unwind task {i} succeeded")
                else:
                    logger.error(f"❌ Unwind task {i} returned False")

    async def _unwind_kalshi_position(self, kalshi_order: Dict) -> bool:
        """
        Unwind a Kalshi position by placing an offsetting order

        Args:
            kalshi_order: Original Kalshi order data

        Returns:
            True if successfully unwound, False otherwise
        """
        try:
            ticker = kalshi_order.get('ticker')
            side = kalshi_order.get('side')  # 'yes' or 'no'
            count = kalshi_order.get('count')

            if not all([ticker, side, count]):
                logger.error("Insufficient order data to unwind Kalshi position")
                return False

            # Place offsetting market order (sell what we bought)
            logger.info(f"Placing offsetting Kalshi order: SELL {count} {side} @ market")

            result = await self.kalshi.place_order(
                ticker=ticker,
                side=side,
                action='sell',  # Offset the buy
                count=count,
                price=50,  # Mid-price for market-like execution
                order_type='limit'  # Use aggressive limit instead of true market
            )

            if result:
                logger.info(f"✅ Kalshi position unwound: {result.get('order', {}).get('order_id')}")
                return True
            else:
                logger.error("❌ Failed to unwind Kalshi position")
                return False

        except Exception as e:
            logger.error(f"Error unwinding Kalshi position: {e}")
            return False

    async def _unwind_polymarket_position(self, poly_order: Dict) -> bool:
        """
        Unwind a Polymarket position by placing an offsetting order

        Args:
            poly_order: Original Polymarket order data

        Returns:
            True if successfully unwound, False otherwise
        """
        try:
            token_id = poly_order.get('token_id')
            size = poly_order.get('size')

            if not all([token_id, size]):
                logger.error("Insufficient order data to unwind Polymarket position")
                return False

            # Place offsetting order (sell what we bought)
            logger.info(f"Placing offsetting Polymarket order: SELL {size} @ market")

            # Use mid-price for quick execution
            result = await self.polymarket.place_order(
                token_id=token_id,
                side='SELL',  # Offset the buy
                size=float(size),
                price=0.5,  # Mid-price for market-like execution
                order_type='LIMIT'
            )

            if result:
                logger.info(f"✅ Polymarket position unwound: {result.get('order_id')}")
                return True
            else:
                logger.error("❌ Failed to unwind Polymarket position")
                return False

        except Exception as e:
            logger.error(f"Error unwinding Polymarket position: {e}")
            return False

    async def check_order_status(
        self,
        kalshi_order_id: Optional[str],
        poly_order_id: Optional[str]
    ) -> Tuple[bool, bool]:
        """
        Check fill status of both orders

        Args:
            kalshi_order_id: Kalshi order ID
            poly_order_id: Polymarket order ID

        Returns:
            Tuple of (kalshi_filled, poly_filled)
        """
        kalshi_filled = False
        poly_filled = False

        # Check Kalshi order status
        if kalshi_order_id:
            try:
                kalshi_status = await self.kalshi.get_order_status(kalshi_order_id)
                if kalshi_status:
                    status = kalshi_status.get('status', '').lower()
                    kalshi_filled = status in ['filled', 'complete', 'executed']
            except Exception as e:
                logger.error(f"Error checking Kalshi order status: {e}")

        # Check Polymarket order status
        if poly_order_id:
            try:
                poly_status = await self.polymarket.get_order_status(poly_order_id)
                if poly_status:
                    status = poly_status.get('status', '').lower()
                    poly_filled = status in ['filled', 'complete', 'matched']
            except Exception as e:
                logger.error(f"Error checking Polymarket order status: {e}")

        return kalshi_filled, poly_filled

    async def close(self):
        """Close API clients"""
        await self.kalshi.close()
        await self.polymarket.close()
