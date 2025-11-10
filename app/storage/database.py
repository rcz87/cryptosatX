"""
Database configuration and connection management
Uses async PostgreSQL with asyncpg for optimal performance
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from asyncpg import Pool

class Database:
    """
    Async PostgreSQL database manager using asyncpg
    Handles connection pooling and schema initialization
    """
    
    def __init__(self):
        self.pool: Pool | None = None
        self.database_url = os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
    
    async def connect(self):
        """Initialize connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                timeout=30
            )
            print("✅ Database connection pool created")
            
            # Initialize schema on first connect
            await self.init_schema()
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("✅ Database connection pool closed")
    
    async def init_schema(self):
        """
        Initialize database schema
        Creates signals table if it doesn't exist
        """
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
            """)
            print("✅ Database schema initialized")
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            yield connection


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
