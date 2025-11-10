# Crypto Futures Signal API

## Overview
This project is a production-ready FastAPI backend designed to generate real-time cryptocurrency futures trading signals. It aggregates data from multiple sources to provide comprehensive signals based on price action, funding rates, open interest, and social sentiment. The API aims to offer LONG/SHORT/NEUTRAL recommendations, utilizing a multi-factor weighted scoring system, and is compatible with GPT Actions for OpenAI integration. The business vision is to provide a robust tool for informed trading decisions with market potential in automated trading and signal provision services.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application is built with FastAPI and features a modular architecture separating API routes, core business logic, and external service integrations.

### UI/UX Decisions
The API design focuses on programmatic access, providing clean JSON responses. Debug mode (`?debug=true`) is available for detailed metrics. OpenAPI documentation is exposed via `/docs` and `/redoc`. A GPT Actions-compatible OpenAPI schema is provided for seamless integration with AI agents.

### Technical Implementations
- **Signal Engine**: Employs an 8-factor weighted scoring system (0-100 scale) for signal generation, including Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed. Configurable thresholds determine the final signal.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for optimal performance.
- **Error Handling**: Implements robust error handling with safe defaults.
- **API Endpoints**: Includes endpoints for enhanced trading signals (`/signals/{symbol}`), aggregated raw market data (`/market/{symbol}`), and a GPT Actions schema (`/gpt/action-schema`), alongside dedicated endpoints for direct Coinglass and LunarCrush data access.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns like BOS, CHoCH, FVG, swing points, and liquidity zones across multiple timeframes.
- **Signal History Storage**: Dual-storage system using PostgreSQL as primary database with JSON file backup. **IMPORTANT**: Only LONG/SHORT signals (sent to Telegram) are saved to database - NEUTRAL signals are NOT stored. This ensures database contains only actionable trading signals.
- **Database Architecture**: PostgreSQL (Neon) with asyncpg driver for high-performance async operations. Schema includes comprehensive signal tracking with JSONB fields for flexible metrics storage and optimized indexes for fast queries.
- **Analytics & Insights**: Advanced analytics endpoints (`/analytics/*`) providing signal performance metrics, trend analysis, symbol-specific insights, and date-range queries with pagination support.
- **API Key Authentication**: Optional protection for sensitive endpoints using header-based API keys.
- **Structured JSON Logging**: Production-grade logging with JSON format for console and file output.
- **Telegram Notifier**: Provides human-friendly signal alerts with emojis.

### Feature Specifications
- **Comprehensive LunarCrush Integration**: Incorporates 4 advanced LunarCrush endpoints for in-depth social sentiment analysis.
- **Maximized Coinglass Integration**: Leverages comprehensive Coinglass v4 endpoints for market data, multi-timeframe liquidations, and an all-in-one dashboard.
- **Output**: Signals include recommendation (LONG/SHORT/NEUTRAL), composite score, confidence level, top 3 contributing factors, and raw metrics in debug mode.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async support
- **HTTP Client**: httpx for asynchronous API calls
- **Validation**: Pydantic v2 for data validation
- **Database**: PostgreSQL (Neon) with asyncpg for async operations
- **Connection Pooling**: asyncpg connection pool (2-10 connections) for optimal performance
- **Environment Management**: python-dotenv for configuration
- **Lifecycle Management**: Modern `lifespan` context manager for startup/shutdown events with automatic database initialization.

### Database Schema
The PostgreSQL database includes a `signals` table with the following structure:
- **Primary Key**: Auto-incrementing signal ID
- **Core Fields**: symbol, signal, score, confidence, price, timestamp
- **Metrics Storage**: JSONB fields for flexible storage (reasons, metrics, comprehensive_metrics, lunarcrush_metrics, coinapi_metrics, smc_analysis, ai_validation)
- **Indexes**: Optimized indexes on symbol, timestamp, signal type, and created_at for fast queries
- **Migration Support**: Migration script (`app/storage/migrate_to_db.py`) for transferring existing JSON data to PostgreSQL

## External Dependencies
- **CoinAPI Startup**: Integrated for comprehensive market data, including multi-timeframe OHLCV, order book depth analysis, recent trades volume tracking, real-time bid/ask quotes, and multi-exchange price aggregation.
- **Coinglass v4**: Integrated for funding rates, open interest data, liquidations, long/short ratios, and top trader positioning.
- **LunarCrush**: Provides social sentiment, community engagement metrics, and advanced social momentum analysis.
- **OKX Public API**: Utilized for candlestick/OHLCV data.