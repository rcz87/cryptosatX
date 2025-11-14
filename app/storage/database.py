"""
Database configuration and connection management
Uses async PostgreSQL with asyncpg for optimal performance
Falls back to SQLite for Replit compatibility

Database migrations are managed with Alembic.
Run migrations with: alembic upgrade head
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from asyncpg import Pool
import aiosqlite
import sqlite3


class Database:
    """
    Async database manager with PostgreSQL and SQLite support
    Handles connection pooling and schema initialization
    """

    def __init__(self):
        self.pool: Pool | None = None
        self.sqlite_conn: aiosqlite.Connection | None = None
        self.database_url = os.getenv("DATABASE_URL")
        self.use_postgres = bool(
            self.database_url and not self.database_url.startswith("sqlite")
        )

        # For Replit, use SQLite by default if no DATABASE_URL
        if not self.database_url:
            self.database_url = "sqlite:///cryptosatx.db"
            self.use_postgres = False
            print("[INFO] Using SQLite database for Replit compatibility")
        else:
            print(
                f"[INFO] Using {'PostgreSQL' if self.use_postgres else 'SQLite'} database"
            )

    async def connect(self):
        """Initialize connection pool or SQLite connection"""
        if self.use_postgres:
            if self.pool is None:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=30,
                )
                print("[SUCCESS] PostgreSQL connection pool created")
        else:
            if self.sqlite_conn is None:
                db_path = self.database_url.replace("sqlite:///", "")
                self.sqlite_conn = await aiosqlite.connect(db_path)
                # Enable foreign keys and WAL mode for better performance
                await self.sqlite_conn.execute("PRAGMA foreign_keys = ON")
                await self.sqlite_conn.execute("PRAGMA journal_mode = WAL")
                print("[SUCCESS] SQLite connection established")

        # Initialize schema on first connect
        # For PostgreSQL: Validates Alembic migrations are applied
        # For SQLite: Creates manual schema for Replit compatibility
        await self.init_schema()

    async def disconnect(self):
        """Close connection pool or SQLite connection"""
        if self.use_postgres:
            if self.pool:
                await self.pool.close()
                self.pool = None
                print("[SUCCESS] PostgreSQL connection pool closed")
        else:
            if self.sqlite_conn:
                await self.sqlite_conn.close()
                self.sqlite_conn = None
                print("[SUCCESS] SQLite connection closed")

    async def init_schema(self):
        """
        Initialize database schema for SQLite only.
        
        PostgreSQL schema is managed by Alembic migrations.
        Run: alembic upgrade head
        
        This method is only called for SQLite to maintain Replit compatibility.
        """
        if self.use_postgres:
            # PostgreSQL schema is managed by Alembic migrations
            # Check if alembic_version table exists to verify migrations are run
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                    """
                )
                if not result:
                    print("[WARNING] Alembic migrations not detected. Run: alembic upgrade head")
                else:
                    print("[INFO] Database schema managed by Alembic migrations")
            return
        
        # SQLite schema creation below (for Replit compatibility)
        else:
            # SQLite schema
            await self.sqlite_conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    score REAL NOT NULL,
                    confidence TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    
                    -- Additional metrics (JSON as TEXT for SQLite)
                    reasons TEXT,
                    metrics TEXT,
                    comprehensive_metrics TEXT,
                    lunarcrush_metrics TEXT,
                    coinapi_metrics TEXT,
                    smc_analysis TEXT,
                    ai_validation TEXT,
                    
                    -- Indexing for fast queries
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            
            # Create signal_outcomes table for accuracy tracking (SQLite)
            await self.sqlite_conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    risk_mode TEXT,
                    
                    entry_price REAL NOT NULL,
                    entry_timestamp TEXT NOT NULL,
                    
                    price_1h REAL,
                    price_4h REAL,
                    price_24h REAL,
                    
                    outcome_1h TEXT,
                    outcome_4h TEXT,
                    outcome_24h TEXT,
                    
                    pnl_1h REAL,
                    pnl_4h REAL,
                    pnl_24h REAL,
                    
                    tracked_at_1h TEXT,
                    tracked_at_4h TEXT,
                    tracked_at_24h TEXT,
                    
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE
                );
            """
            )

            # Create indexes for SQLite
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);",
                "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_signals_signal ON signals(signal);",
                "CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON signals(symbol, timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_verdict ON signal_outcomes(verdict);",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_symbol_verdict ON signal_outcomes(symbol, verdict);",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON signal_outcomes(entry_timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_signal_id ON signal_outcomes(signal_id);",
            ]

            for index_sql in indexes:
                await self.sqlite_conn.execute(index_sql)

            await self.sqlite_conn.commit()

        print("[SUCCESS] Database schema initialized")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator:
        """Get database connection from pool or SQLite connection"""
        if self.use_postgres:
            if not self.pool:
                await self.connect()

            async with self.pool.acquire() as connection:
                yield connection
        else:
            if not self.sqlite_conn:
                await self.connect()

            yield self.sqlite_conn


# Global database instance
db = Database()


async def get_db_connection():
    """
    Dependency for getting database connection
    Usage in FastAPI routes:
        async def my_route(conn = Depends(get_db_connection)):
            ...
    """
    async with db.acquire() as conn:
        yield conn
