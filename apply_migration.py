"""
Apply SQLite migration for comprehensive monitoring tables
"""
import asyncio
import aiosqlite

async def apply_migration():
    # Read SQL file
    with open('migrations/sqlite_comprehensive_monitoring.sql', 'r') as f:
        sql = f.read()

    # Connect to database
    async with aiosqlite.connect('cryptosatx.db') as db:
        # Execute SQL statements
        await db.executescript(sql)
        await db.commit()

        # Verify tables created
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%monitoring%' OR name='coin_watchlist'"
        ) as cursor:
            tables = await cursor.fetchall()

        print("✅ Migration applied successfully!")
        print("\nNew tables created:")
        for table in tables:
            print(f"  - {table[0]}")

        # Count existing tables
        async with db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'") as cursor:
            count = await cursor.fetchone()
            print(f"\nTotal tables in database: {count[0]}")

if __name__ == "__main__":
    asyncio.run(apply_migration())
