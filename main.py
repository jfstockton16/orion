#!/usr/bin/env python3
"""
Orion Cross-Exchange Arbitrage Engine
Main entry point
"""

import asyncio
import argparse
import sys
from pathlib import Path
from src.engine import ArbitrageEngine
from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger("main")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Orion Cross-Exchange Arbitrage Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in dry-run mode (no real trades)
  python main.py --dry-run

  # Run with auto-execution enabled
  python main.py --auto-execute true

  # Custom configuration file
  python main.py --config custom_config.yaml

  # Set custom threshold
  python main.py --threshold 0.02

  # Run dashboard only
  streamlit run dashboard.py
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--auto-execute',
        type=str,
        choices=['true', 'false'],
        help='Enable/disable automatic trade execution (overrides config)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (simulate trades without execution)'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        help='Minimum spread threshold for arbitrage (overrides config)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--test-alerts',
        action='store_true',
        help='Test alert system and exit'
    )

    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database and exit'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Orion Arbitrage Engine v1.0.0'
    )

    return parser.parse_args()


def validate_environment(config):
    """
    Validate that required environment variables and files exist

    Args:
        config: Configuration object

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check API credentials (unless in dry-run mode)
    if not config.kalshi_api_key:
        errors.append("KALSHI_API_KEY not set in environment")

    if not config.kalshi_api_secret:
        errors.append("KALSHI_API_SECRET not set in environment")

    if not config.polymarket_private_key and not config.polymarket_api_key:
        errors.append("POLYMARKET_PRIVATE_KEY or POLYMARKET_API_KEY not set")

    # Check data directory exists
    data_dir = Path('data')
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Created data directory")

    # Check logs directory exists
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Created logs directory")

    return errors


async def test_alerts(config):
    """Test alert system"""
    from src.monitoring.alerts import AlertManager

    logger.info("Testing alert system...")

    alert_manager = AlertManager({
        **config._config,
        'telegram_bot_token': config.telegram_bot_token,
        'telegram_chat_id': config.telegram_chat_id
    })

    success = await alert_manager.test_connection()

    if success:
        logger.info("✅ Alert system test successful")
        return 0
    else:
        logger.error("❌ Alert system test failed")
        return 1


def init_database(config):
    """Initialize database"""
    from src.database.models import init_database

    logger.info("Initializing database...")

    try:
        engine, Session = init_database(config.database_url)
        logger.info(f"✅ Database initialized at {config.database_url}")
        return 0
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return 1


async def main_async(args):
    """Main async function"""

    # Load configuration
    try:
        config = get_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Override config with command-line arguments
    if args.auto_execute is not None:
        auto_execute = args.auto_execute == 'true'
        config._config['trading']['auto_execute'] = auto_execute
        logger.info(f"Auto-execute override: {auto_execute}")

    if args.threshold is not None:
        config._config['trading']['threshold_spread'] = args.threshold
        logger.info(f"Threshold override: {args.threshold}")

    # Handle special modes
    if args.init_db:
        return init_database(config)

    if args.test_alerts:
        return await test_alerts(config)

    # Validate environment
    if not args.dry_run:
        validation_errors = validate_environment(config)

        if validation_errors:
            logger.error("Environment validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")

            logger.info("\nRunning in DRY-RUN mode due to missing credentials")
            args.dry_run = True

    # Print startup banner
    print("\n" + "=" * 70)
    print("  💰 ORION CROSS-EXCHANGE ARBITRAGE ENGINE")
    print("=" * 70)
    print(f"  Mode: {'DRY-RUN (Simulation)' if args.dry_run else 'LIVE TRADING'}")
    print(f"  Auto-Execute: {config.get('trading.auto_execute', False)}")
    print(f"  Threshold: {config.get('trading.threshold_spread', 0.01) * 100:.2f}%")
    print(f"  Poll Interval: {config.get('polling.interval_sec', 30)}s")
    print("=" * 70 + "\n")

    if not args.dry_run:
        print("⚠️  WARNING: LIVE TRADING MODE ENABLED")
        print("   This bot will execute real trades with real money.")
        print("   Press Ctrl+C within 5 seconds to cancel...\n")

        try:
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return 0

    # Initialize and start engine
    try:
        engine = ArbitrageEngine(config, dry_run=args.dry_run)
        await engine.start()

    except KeyboardInterrupt:
        logger.info("\n⏹️  Shutdown requested by user")
        await engine.stop()
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


def main():
    """Main entry point"""
    args = parse_args()

    # Set up logging
    global logger
    logger = setup_logger(
        "main",
        level=args.log_level,
        log_file="logs/arbitrage.log"
    )

    # Run async main
    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
