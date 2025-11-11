"""
Database configuration and connection management
Uses async PostgreSQL with asyncpg for optimal performance
Falls back to SQLite for Replit compatibility
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
        self.use_postgres = bool(self.database_url and not self.database_url.startswith("sqlite"))
        
        # For Replit, use SQLite by default if no DATABASE_URL
        if not self.database_url:
            self.database_url = "sqlite:///cryptosatx.db"
            self.use_postgres = False
            print("🔄 Using SQLite database for Replit compatibility")
        else:
            print(f"🗄️ Using {'PostgreSQL' if self.use_postgres else 'SQLite'} database")
    
    async def connect(self):
        """Initialize connection pool or SQLite connection"""
        if self.use_postgres:
            if self.pool is None:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=30
                )
                print("✅ PostgreSQL connection pool created")
        else:
            if self.sqlite_conn is None:
                db_path = self.database_url.replace("sqlite:///", "")
                self.sqlite_conn = await aiosqlite.connect(db_path)
                # Enable foreign keys and WAL mode for better performance
                await self.sqlite_conn.execute("PRAGMA foreign_keys = ON")
                await self.sqlite_conn.execute("PRAGMA journal_mode = WAL")
                print("✅ SQLite connection established")
        
        # Initialize schema on first connect
        await self.init_schema()
    
    async def disconnect(self):
        """Close connection pool or SQLite connection"""
        if self.use_postgres:
            if self.pool:
                await self.pool.close()
                self.pool = None
                print("✅ PostgreSQL connection pool closed")
        else:
            if self.sqlite_conn:
                await self.sqlite_conn.close()
                self.sqlite_conn = None
                print("✅ SQLite connection closed")
    
    async def init_schema(self):
        """
        Initialize database schema
        Creates signals table if it doesn't exist
        """
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS signals (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        signal VARCHAR(10) NOT NULL,
                        score DECIMAL(5,2) NOT NULL,
                        confidence VARCHAR(10) NOT NULL,
                        price DECIMAL(20,8) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        
                        -- Additional metrics (JSON for flexibility)
                        reasons JSONB,
                        metrics JSONB,
                        comprehensive_metrics JSONB,
                        lunarcrush_metrics JSONB,
                        coinapi_metrics JSONB,
                        smc_analysis JSONB,
                        ai_validation JSONB,
                        
                        -- Indexing for fast queries
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    
                    -- Create indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
                    CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
                    CREATE INDEX IF NOT EXISTS idx_signals_signal ON signals(signal);
                    CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON signals(symbol, timestamp DESC);
                    
                    -- MSS-specific indexes for optimal query performance (Nov 2025)
                    CREATE INDEX IF NOT EXISTS idx_signals_mss_timestamp ON signals(signal, timestamp DESC) WHERE signal LIKE 'MSS_%';
                    CREATE INDEX IF NOT EXISTS idx_signals_mss_score ON signals(score DESC) WHERE signal LIKE 'MSS_%';
                """)
        else:
            # SQLite schema
            await self.sqlite_conn.execute("""
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
            """)
            
            # Create indexes for SQLite
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);",
                "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_signals_signal ON signals(signal);",
                "CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON signals(symbol, timestamp DESC);"
            ]
            
            for index_sql in indexes:
                await self.sqlite_conn.execute(index_sql)
            
            await self.sqlite_conn.commit()
        
        print("✅ Database schema initialized")
    
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
