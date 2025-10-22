"""Alert system with Telegram integration"""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from src.arbitrage.detector import ArbitrageOpportunity
from src.execution.executor import ExecutionResult
from src.utils.logger import setup_logger

logger = setup_logger("alerts")


class AlertManager:
    """Manages alerts via multiple channels"""

    def __init__(self, config: Dict):
        """
        Initialize alert manager

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.alert_channels = config.get('monitoring', {}).get('alert_channels', [])
        self.alert_threshold = config.get('monitoring', {}).get('alert_threshold_spread', 0.015)
        self.min_opportunity_usd = config.get('monitoring', {}).get('alert_min_opportunity_usd', 500)

        # Telegram configuration
        self.telegram_enabled = 'telegram' in self.alert_channels
        self.telegram_bot: Optional[Bot] = None
        self.telegram_chat_id: Optional[str] = None

        if self.telegram_enabled:
            token = config.get('telegram_bot_token')
            chat_id = config.get('telegram_chat_id')

            if token and chat_id:
                self.telegram_bot = Bot(token=token)
                self.telegram_chat_id = chat_id
                logger.info("Telegram alerts enabled")
            else:
                logger.warning("Telegram enabled but credentials missing")
                self.telegram_enabled = False

    async def send_opportunity_alert(self, opportunity: ArbitrageOpportunity) -> None:
        """
        Send alert for new arbitrage opportunity

        Args:
            opportunity: ArbitrageOpportunity object
        """
        # Check if opportunity meets alert threshold
        if opportunity.edge < self.alert_threshold:
            return

        if opportunity.expected_profit < self.min_opportunity_usd:
            return

        message = self._format_opportunity_message(opportunity)

        await self._send_alert(message, priority="high")

    async def send_execution_alert(
        self,
        result: ExecutionResult,
        opportunity: Optional[ArbitrageOpportunity] = None
    ) -> None:
        """
        Send alert for trade execution

        Args:
            result: ExecutionResult object
            opportunity: Original opportunity (optional)
        """
        message = self._format_execution_message(result, opportunity)

        priority = "high" if not result.success else "normal"
        await self._send_alert(message, priority=priority)

    async def send_error_alert(self, error_type: str, error_message: str) -> None:
        """
        Send alert for system errors

        Args:
            error_type: Type of error
            error_message: Error message
        """
        message = (
            f"🚨 ERROR ALERT\n\n"
            f"Type: {error_type}\n"
            f"Message: {error_message}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await self._send_alert(message, priority="critical")

    async def send_daily_summary(self, summary: Dict) -> None:
        """
        Send daily performance summary

        Args:
            summary: Performance summary dictionary
        """
        message = self._format_daily_summary(summary)
        await self._send_alert(message, priority="low")

    def _format_opportunity_message(self, opp: ArbitrageOpportunity) -> str:
        """
        Format opportunity alert message

        Args:
            opp: ArbitrageOpportunity

        Returns:
            Formatted message string
        """
        return (
            f"💰 ARBITRAGE OPPORTUNITY\n\n"
            f"Question: {opp.question[:100]}...\n\n"
            f"📊 Pricing:\n"
            f"  Kalshi YES: {opp.kalshi_yes_price:.4f}\n"
            f"  Polymarket NO: {opp.polymarket_no_price:.4f}\n"
            f"  Spread: {opp.spread:.4f}\n\n"
            f"💵 Trade Details:\n"
            f"  Edge: {opp.edge*100:.2f}%\n"
            f"  Position Size: ${opp.position_size_usd:.2f}\n"
            f"  Expected Profit: ${opp.expected_profit:.2f}\n"
            f"  Expected ROI: {opp.expected_roi*100:.2f}%\n\n"
            f"🏦 Markets:\n"
            f"  Kalshi: {opp.kalshi_market_id}\n"
            f"  Polymarket: {opp.polymarket_market_id}\n\n"
            f"⏰ Detected: {opp.detected_at.strftime('%H:%M:%S')}"
        )

    def _format_execution_message(
        self,
        result: ExecutionResult,
        opportunity: Optional[ArbitrageOpportunity]
    ) -> str:
        """
        Format execution alert message

        Args:
            result: ExecutionResult
            opportunity: ArbitrageOpportunity (optional)

        Returns:
            Formatted message string
        """
        status_emoji = "✅" if result.success else "❌"

        message = f"{status_emoji} TRADE EXECUTION\n\n"
        message += f"Position: {result.position_id}\n"
        message += f"Status: {'SUCCESS' if result.success else 'FAILED'}\n\n"

        if result.success:
            message += (
                f"📝 Orders:\n"
                f"  Kalshi: {result.kalshi_order_id}\n"
                f"  Polymarket: {result.polymarket_order_id}\n\n"
                f"  Kalshi Filled: {'✅' if result.kalshi_filled else '❌'}\n"
                f"  Poly Filled: {'✅' if result.polymarket_filled else '❌'}\n\n"
                f"  Cost: ${result.actual_cost:.2f}\n"
            )

            if opportunity:
                message += f"  Expected Profit: ${opportunity.expected_profit:.2f}\n"

        else:
            message += f"❌ Error: {result.error_message}\n"

        if result.executed_at:
            message += f"\n⏰ Executed: {result.executed_at.strftime('%H:%M:%S')}"

        return message

    def _format_daily_summary(self, summary: Dict) -> str:
        """
        Format daily summary message

        Args:
            summary: Summary dictionary

        Returns:
            Formatted message string
        """
        return (
            f"📈 DAILY SUMMARY\n\n"
            f"🔍 Opportunities:\n"
            f"  Detected: {summary.get('opportunities_detected', 0)}\n"
            f"  Executed: {summary.get('trades_executed', 0)}\n"
            f"  Successful: {summary.get('trades_successful', 0)}\n\n"
            f"💰 Performance:\n"
            f"  Total P&L: ${summary.get('total_pnl', 0):.2f}\n"
            f"  Volume: ${summary.get('total_volume', 0):.2f}\n"
            f"  Win Rate: {summary.get('win_rate', 0)*100:.1f}%\n\n"
            f"📊 Balance:\n"
            f"  Total: ${summary.get('total_balance', 0):.2f}\n"
            f"  Kalshi: ${summary.get('kalshi_balance', 0):.2f}\n"
            f"  Polymarket: ${summary.get('polymarket_balance', 0):.2f}\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    async def _send_alert(self, message: str, priority: str = "normal") -> None:
        """
        Send alert through configured channels

        Args:
            message: Alert message
            priority: Priority level (low, normal, high, critical)
        """
        logger.info(f"Sending {priority} priority alert")

        # Send to all configured channels
        tasks = []

        if self.telegram_enabled:
            tasks.append(self._send_telegram(message))

        # Could add more channels here (email, Discord, etc.)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, message: str) -> None:
        """
        Send message via Telegram

        Args:
            message: Message to send
        """
        if not self.telegram_bot or not self.telegram_chat_id:
            logger.warning("Telegram not properly configured")
            return

        try:
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.debug("Telegram alert sent successfully")

        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")

        except Exception as e:
            logger.error(f"Unexpected error sending Telegram alert: {e}")

    async def test_connection(self) -> bool:
        """
        Test alert system connections

        Returns:
            True if all channels are working
        """
        logger.info("Testing alert connections...")

        all_ok = True

        if self.telegram_enabled:
            try:
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text="✅ Orion Arbitrage Bot - Alert system test"
                )
                logger.info("Telegram test successful")
            except Exception as e:
                logger.error(f"Telegram test failed: {e}")
                all_ok = False

        return all_ok
