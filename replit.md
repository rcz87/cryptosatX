# Crypto Futures Signal API

## Overview
This project is a production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals. It aggregates diverse market data (price action, funding rates, open interest, social sentiment) to provide LONG/SHORT/NEUTRAL recommendations based on a multi-factor weighted scoring system. The API is designed for compatibility with GPT Actions, aiming to provide a robust tool for informed trading decisions with significant market potential. Key features include an advanced Multi-Modal Signal Score (MSS) system for identifying high-potential emerging cryptocurrencies and a Binance New Listings Monitor for early detection of fresh perpetual futures listings.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application is built with FastAPI following a modular architecture, separating API routes, core business logic, and external service integrations.

### UI/UX Decisions
The API provides clean JSON responses and offers a debug mode (`?debug=true`) for detailed metrics. OpenAPI documentation is available at `/docs` and `/redoc`, including a GPT Actions-compatible schema.

### Technical Implementations
- **Signal Engine**: An 8-factor weighted scoring system (0-100 scale) generates signals based on Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed.
- **Multi-Modal Signal Score (MSS)**: A 3-phase analytical framework for discovering emerging cryptocurrencies by filtering based on tokenomics (Discovery), community momentum (Social Confirmation), and institutional validation (Institutional Validation).
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns (BOS, CHoCH, FVG, swing points, liquidity zones) across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic coin discovery, allowing analysis of any cryptocurrency and filtering by market cap, volume, and category.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for performance.
- **API Endpoints**: Includes endpoints for enhanced trading signals (`/signals/{symbol}`), aggregated raw market data (`/market/{symbol}`), GPT Actions schema (`/gpt/action-schema`), direct Coinglass and LunarCrush data access, Smart Money analysis (`/smart-money/*`), MSS functionality (`/mss/*`), and Binance New Listings.
- **Signal History Storage**: Stores LONG/SHORT signals and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup, using `asyncpg`.
- **Telegram Notifier**: Provides human-friendly signal alerts for both core signals and MSS discoveries.

### Feature Specifications
- **Comprehensive Integrations**: Leverages Coinglass v4 for market data, liquidations, and open interest; LunarCrush for social sentiment; CoinAPI for comprehensive market data and whale detection; Binance Futures for futures market data; and CoinGecko for coin discovery.
- **Output**: Signals include recommendation, composite score, confidence level, top 3 contributing factors, and raw metrics (in debug mode). MSS alerts include a 3-phase breakdown and tier classification.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` driver and connection pooling.
- **Environment Management**: python-dotenv.

### Database Schema
The PostgreSQL `signals` table stores:
- **Core Fields**: symbol, signal, score, confidence, price, timestamp.
- **Metrics Storage**: JSONB fields for flexible storage of detailed metrics (reasons, comprehensive_metrics, lunarcrush_metrics, coinapi_metrics, smc_analysis, ai_validation).
- **Indexes**: Optimized indexes on symbol, timestamp, signal type, and created_at.

## External Dependencies
- **CoinAPI Startup**: Market data, OHLCV, order book depth, recent trades, real-time quotes, multi-exchange price aggregation, and whale detection.
- **Coinglass v4**: Funding rates, open interest, liquidations, long/short ratios, top trader positioning, options data, ETF flows, exchange reserves, and Bitcoin-specific indicators (Rainbow Chart, Stock-to-Flow).
- **LunarCrush**: Social sentiment, community engagement metrics, social momentum analysis, and real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Public API for futures market data, coin discovery, 24hr statistics, funding rates, open interest, and new listings information.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, and category-based coin search.