#!/usr/bin/env python3
"""
Database migration script to add trading_mode column
Run this once to upgrade existing databases
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str = "data/arbitrage.db"):
    """
    Add trading_mode column to existing tables

    Args:
        db_path: Path to SQLite database
    """
    print(f"Migrating database: {db_path}")

    if not Path(db_path).exists():
        print(f"✅ Database doesn't exist yet - no migration needed")
        print(f"   (New database will be created with trading_mode column)")
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if migration is needed
        cursor.execute("PRAGMA table_info(opportunities)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'trading_mode' in columns:
            print("✅ Database already migrated - trading_mode column exists")
            conn.close()
            return 0

        print("📝 Adding trading_mode column to tables...")

        # Add trading_mode to opportunities table
        print("  - Migrating 'opportunities' table...")
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'paper' NOT NULL
        """)

        # Add index for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_opportunities_trading_mode
            ON opportunities(trading_mode)
        """)

        # Add trading_mode to trades table
        print("  - Migrating 'trades' table...")
        cursor.execute("""
            ALTER TABLE trades
            ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'paper' NOT NULL
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_trading_mode
            ON trades(trading_mode)
        """)

        # Add trading_mode to balance_snapshots table
        print("  - Migrating 'balance_snapshots' table...")
        cursor.execute("""
            ALTER TABLE balance_snapshots
            ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'paper' NOT NULL
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_balance_snapshots_trading_mode
            ON balance_snapshots(trading_mode)
        """)

        # Commit changes
        conn.commit()
        conn.close()

        print("✅ Migration completed successfully!")
        print("")
        print("📊 Summary:")
        print("   - Added 'trading_mode' column to all tables")
        print("   - Created indexes for better query performance")
        print("   - Existing data marked as 'paper' mode by default")
        print("")
        print("💡 Next steps:")
        print("   1. Review the data in your dashboard")
        print("   2. Paper trading and live trading data are now separated")
        print("   3. Toggle between modes in the dashboard to see different data")

        return 0

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/arbitrage.db"

    print("=" * 70)
    print("  DATABASE MIGRATION - Add trading_mode column")
    print("=" * 70)
    print()

    exit_code = migrate_database(db_path)

    print()
    print("=" * 70)
    sys.exit(exit_code)
