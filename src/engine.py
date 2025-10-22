"""Main arbitrage engine orchestration"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.api.kalshi_client import KalshiClient
from src.api.polymarket_client import PolymarketClient
from src.arbitrage.matcher import EventMatcher
from src.arbitrage.detector import ArbitrageDetector
from src.execution.executor import TradeExecutor
from src.execution.capital_manager import CapitalManager
from src.execution.circuit_breaker import CircuitBreaker, TradingHaltException
from src.database.models import init_database
from src.database.repository import ArbitrageRepository
from src.monitoring.alerts import AlertManager
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("engine")


class ArbitrageEngine:
    """Main arbitrage engine orchestrator"""

    def __init__(self, config: Config, dry_run: bool = True):
        """
        Initialize arbitrage engine

        Args:
            config: Configuration object
            dry_run: If True, simulate trades without execution
        """
        self.config = config
        self.dry_run = dry_run

        # Initialize components
        self.kalshi = KalshiClient(
            api_key=config.kalshi_api_key,
            api_secret=config.kalshi_api_secret,
            base_url=config.kalshi_base_url
        )

        self.polymarket = PolymarketClient(
            api_key=config.polymarket_api_key,
            private_key=config.polymarket_private_key,
            proxy_url=config.polymarket_proxy_url
        )

        self.matcher = EventMatcher(
            similarity_threshold=0.85,
            date_tolerance_days=1
        )

        self.detector = ArbitrageDetector(config._config)

        self.executor = TradeExecutor(
            kalshi_client=self.kalshi,
            polymarket_client=self.polymarket,
            config=config._config,
            dry_run=dry_run
        )

        self.capital_manager = CapitalManager(config._config)

        # Initialize circuit breaker for loss protection
        self.circuit_breaker = CircuitBreaker(
            max_daily_loss_pct=config.get('risk.max_daily_loss_pct', 0.05),
            max_drawdown_pct=0.15,  # Additional 15% drawdown protection
            reset_hour=0  # Reset at midnight
        )

        self.alert_manager = AlertManager({
            **config._config,
            'telegram_bot_token': config.telegram_bot_token,
            'telegram_chat_id': config.telegram_chat_id
        })

        # Initialize database
        engine, SessionFactory = init_database(config.database_url)
        self.session = SessionFactory()
        self.repository = ArbitrageRepository(self.session)

        # Scheduler for periodic tasks
        self.scheduler = AsyncIOScheduler()

        # State
        self.running = False
        self.poll_interval = config.get('polling.interval_sec', 30)

        logger.info(
            f"Arbitrage Engine initialized (dry_run={dry_run})"
        )

    async def start(self):
        """Start the arbitrage engine"""
        logger.info("Starting Arbitrage Engine...")

        self.running = True

        # Authenticate with exchanges
        if not self.dry_run:
            await self._authenticate()

        # Test alert system
        if await self.alert_manager.test_connection():
            logger.info("Alert system connected")

        # Schedule periodic tasks
        self._schedule_tasks()

        # Start scheduler
        self.scheduler.start()

        # Run main loop
        await self._run_loop()

    async def stop(self):
        """Stop the arbitrage engine"""
        logger.info("Stopping Arbitrage Engine...")

        self.running = False

        # Shutdown scheduler
        self.scheduler.shutdown()

        # Close API clients
        await self.kalshi.close()
        await self.polymarket.close()

        # Close database session
        self.session.close()

        logger.info("Arbitrage Engine stopped")

    async def _authenticate(self):
        """Authenticate with exchanges"""
        logger.info("Authenticating with exchanges...")

        # Kalshi login
        if await self.kalshi.login():
            logger.info("Kalshi authentication successful")
        else:
            logger.error("Kalshi authentication failed")

        # Polymarket doesn't require separate login (uses wallet)
        logger.info("Polymarket ready (wallet-based)")

    def _schedule_tasks(self):
        """Schedule periodic background tasks"""

        # Update balances every 5 minutes
        self.scheduler.add_job(
            self._update_balances,
            'interval',
            minutes=5,
            id='update_balances'
        )

        # Save balance snapshot every 15 minutes
        self.scheduler.add_job(
            self._save_balance_snapshot,
            'interval',
            minutes=15,
            id='save_snapshot'
        )

        # Send daily summary at midnight
        self.scheduler.add_job(
            self._send_daily_summary,
            'cron',
            hour=0,
            minute=0,
            id='daily_summary'
        )

        # Reset daily metrics at midnight
        self.scheduler.add_job(
            self._reset_daily_metrics,
            'cron',
            hour=0,
            minute=1,
            id='reset_daily'
        )

        logger.info("Scheduled background tasks")

    async def _run_loop(self):
        """Main execution loop"""
        logger.info(f"Starting main loop (interval: {self.poll_interval}s)")

        iteration = 0

        while self.running:
            try:
                iteration += 1
                logger.info(f"=== Iteration {iteration} ===")

                # Run one scan cycle
                await self._scan_and_execute()

                # Wait for next iteration
                await asyncio.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await self.alert_manager.send_error_alert("Main Loop Error", str(e))
                await asyncio.sleep(self.poll_interval)

    async def _scan_and_execute(self):
        """Scan for opportunities and execute trades"""

        # Check circuit breaker before trading
        try:
            portfolio = self.capital_manager.get_portfolio_state()
            self.circuit_breaker.check_breaker(
                current_balance=portfolio.total_balance,
                current_pnl=portfolio.total_pnl
            )
        except TradingHaltException as e:
            logger.error(f"🛑 Trading halted by circuit breaker: {e}")
            await self.alert_manager.send_error_alert(
                "Circuit Breaker Triggered",
                str(e)
            )
            # Stop the engine
            self.running = False
            return

        # 1. Fetch markets from both exchanges
        logger.info("Fetching markets...")
        kalshi_markets, poly_markets = await asyncio.gather(
            self.kalshi.get_markets(limit=100),
            self.polymarket.get_markets(limit=100)
        )

        logger.info(
            f"Fetched {len(kalshi_markets)} Kalshi markets, "
            f"{len(poly_markets)} Polymarket markets"
        )

        if not kalshi_markets or not poly_markets:
            logger.warning("No markets fetched, skipping iteration")
            return

        # 2. Normalize markets
        normalized_kalshi = [self.kalshi.normalize_market(m) for m in kalshi_markets]
        normalized_poly = [self.polymarket.normalize_market(m) for m in poly_markets]

        # 3. Find matching events
        logger.info("Matching events across exchanges...")
        matched_markets = self.matcher.find_matches(
            normalized_kalshi,
            normalized_poly
        )

        if not matched_markets:
            logger.info("No matching markets found")
            return

        # 4. Get current prices
        logger.info("Fetching current prices...")
        kalshi_prices = {}
        poly_prices = {}

        for km, pm, _ in matched_markets:
            # Fetch prices concurrently for each matched pair
            k_price, p_price = await asyncio.gather(
                self.kalshi.get_best_price(km['market_id'], 'yes'),
                self.polymarket.get_best_price(pm['market_id'], 'sell')  # NO price
            )

            if k_price is not None:
                kalshi_prices[km['market_id']] = k_price

            if p_price is not None:
                poly_prices[pm['market_id']] = p_price

        # 5. Detect arbitrage opportunities
        logger.info("Scanning for arbitrage opportunities...")
        bankroll = self.capital_manager.get_available_capital()

        opportunities = self.detector.scan_opportunities(
            matched_markets,
            kalshi_prices,
            poly_prices,
            bankroll
        )

        if not opportunities:
            logger.info("No profitable opportunities found")
            return

        # 6. Execute top opportunities
        auto_execute = self.config.get('trading.auto_execute', False)

        for opp in opportunities[:5]:  # Execute top 5 opportunities
            # Generate position ID
            position_id = f"arb_{int(datetime.now().timestamp())}_{opp.kalshi_market_id[:8]}"

            # Save opportunity to database
            self.repository.save_opportunity(opp, position_id)

            # Send alert
            await self.alert_manager.send_opportunity_alert(opp)

            # Execute if auto-execute enabled
            if auto_execute or self.dry_run:
                await self._execute_opportunity(opp, position_id)
            else:
                logger.info(
                    f"Auto-execute disabled, skipping execution of {position_id}"
                )

    async def _execute_opportunity(self, opportunity, position_id: str):
        """
        Execute an arbitrage opportunity

        Args:
            opportunity: ArbitrageOpportunity object
            position_id: Position identifier
        """
        logger.info(f"Executing opportunity {position_id}...")

        # Check if we can open position
        if not self.capital_manager.can_open_position(opportunity.position_size_usd):
            logger.warning(f"Cannot open position {position_id} - capital constraints")
            return

        # Allocate capital
        if not self.capital_manager.allocate_capital(opportunity.position_size_usd, position_id):
            logger.error(f"Failed to allocate capital for {position_id}")
            return

        # Execute trade
        result = await self.executor.execute_arbitrage(opportunity)

        # Save trade result
        self.repository.save_trade(result)

        # Send execution alert
        await self.alert_manager.send_execution_alert(result, opportunity)

        # If execution failed, release capital
        if not result.success:
            self.capital_manager.release_capital(position_id, 0)
            logger.error(f"Execution failed for {position_id}: {result.error_message}")
        else:
            logger.info(f"Successfully executed {position_id}")

    async def _update_balances(self):
        """Update account balances from exchanges"""
        logger.debug("Updating balances...")

        try:
            kalshi_balance_data = await self.kalshi.get_balance()
            poly_balance_data = await self.polymarket.get_balance()

            kalshi_balance = kalshi_balance_data.get('balance', 0) if kalshi_balance_data else 0
            poly_balance = poly_balance_data.get('USDC', 0) if poly_balance_data else 0

            self.capital_manager.update_balances(kalshi_balance, poly_balance)

        except Exception as e:
            logger.error(f"Error updating balances: {e}")

    async def _save_balance_snapshot(self):
        """Save current portfolio state to database"""
        logger.debug("Saving balance snapshot...")

        try:
            portfolio = self.capital_manager.get_portfolio_state()
            self.repository.save_balance_snapshot(portfolio)

        except Exception as e:
            logger.error(f"Error saving balance snapshot: {e}")

    async def _send_daily_summary(self):
        """Send daily performance summary"""
        logger.info("Sending daily summary...")

        try:
            summary = self.repository.get_performance_summary(days=1)
            portfolio = self.capital_manager.get_portfolio_state()

            summary.update(portfolio.to_dict())

            await self.alert_manager.send_daily_summary(summary)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")

    async def _reset_daily_metrics(self):
        """Reset daily metrics"""
        logger.info("Resetting daily metrics...")
        self.capital_manager.reset_daily_metrics()
