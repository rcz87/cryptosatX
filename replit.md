# Crypto Futures Signal API

## Overview
This project is a production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals. It aggregates diverse market data (price action, funding rates, open interest, social sentiment) to provide LONG/SHORT/NEUTRAL recommendations based on a multi-factor weighted scoring system. The API is designed for compatibility with GPT Actions, aiming to provide a robust tool for informed trading decisions with significant market potential. Key features include an advanced Multi-Modal Signal Score (MSS) system for identifying high-potential emerging cryptocurrencies and a Binance New Listings Monitor for early detection of fresh perpetual futures listings.

## Recent Changes (November 12, 2025)
- **🚀 UNIFIED RPC ENDPOINT - GPT Actions Solution**: Implemented single POST `/invoke` endpoint that provides access to ALL 155 operations via RPC-style interface, bypassing GPT Actions' 30-operation limit. Operation catalog maps to service-layer callables across 16 namespaces (admin, analytics, coinapi, coinglass, health, history, lunarcrush, market, monitoring, mss, narratives, new_listings, openai, signals, smart_money, smc). GPT Actions schema available at `/invoke/schema` with 100 operations in enum and 5 comprehensive examples. Architect-approved for production. All tests passing (signals, coinglass, smart_money).
- **Coinglass Integration COMPLETE**: Verified all 65 Coinglass Standard plan endpoints operational (100% success rate). ALL endpoints callable by GPT Actions via unified RPC endpoint.
- **Dual API Architecture**: Maintained all 170+ REST endpoints for direct access PLUS unified RPC endpoint for GPT Actions integration. Zero breaking changes to existing API.
- **GPT Actions Schema**: Use `https://guardiansofthetoken.org/invoke/schema` for GPT Actions integration with unified RPC endpoint. Alternative: `https://guardiansofthetoken.org/openapi.json` for full REST API (170 operations, may hit 30-operation limit). NOTE: If error "Could not find a valid URL in servers" appears, follow workaround in `GPT_ACTIONS_WORKAROUND.md`.
- **Fixed Premium Data Detection**: Changed premium data availability logic from strict AND (all endpoints required) to flexible OR (accepts 2+ out of 4 endpoints). This resolves false negatives when OI Trend endpoint returns 404 for certain coins.
- **Added Response Flags**: Added `premiumDataAvailable`, `comprehensiveDataAvailable`, `lunarcrushDataAvailable`, and `coinapiDataAvailable` flags to API responses for better GPT Actions compatibility.
- **OKX Fallback**: Implemented automatic fallback to OKX Public API for funding rate and open interest when Coinglass data is unavailable, with source tracking.
- **Enhanced Logging**: Added detailed logging for premium endpoint success/failure to improve debugging and monitoring.
- **Production Deployment**: Successfully deployed all fixes to production (https://guardiansofthetoken.org). All GPT Actions flags working correctly.
- **Comprehensive Endpoint Verification**: Production testing confirms 65/65 Coinglass endpoints accessible (100% success). Complete coverage of market data, liquidations, funding rates, open interest, orderbook, whale tracking, indicators, news, ETF, and WebSocket streaming.

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
- **Comprehensive Coinglass Integration**: 65 production endpoints (verified 100% operational) covering liquidations, funding rates, open interest, trader positioning, orderbook depth, Hyperliquid DEX, on-chain tracking, technical indicators (12 indicators across 535 coins), market sentiment, macro calendar, news feed, order flow analysis, and real-time WebSocket streaming. All endpoints callable via GPT Actions.
- **Real-Time WebSocket Streaming**: WebSocket endpoint for live liquidation data across all exchanges with auto-reconnect and ping/pong keepalive.
- **Unified RPC Endpoint**: Single POST `/invoke` endpoint provides access to ALL 155 operations via RPC interface, bypassing GPT Actions' 30-operation limit. Supports operation catalog with namespace.action naming (e.g., "signals.get", "coinglass.liquidations.symbol"). Schema at `/invoke/schema`, operations list at `/invoke/operations`.
- **API Endpoints**: Includes endpoints for enhanced trading signals (`/signals/{symbol}`), aggregated raw market data (`/market/{symbol}`), GPT Actions schema (`/gpt/action-schema`), unified RPC endpoint (`POST /invoke`), direct Coinglass and LunarCrush data access, Smart Money analysis (`/smart-money/*`), MSS functionality (`/mss/*`), Binance New Listings, and WebSocket streaming (`/ws/liquidations`).
- **Signal History Storage**: Stores LONG/SHORT signals and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup, using `asyncpg`.
- **Telegram Notifier**: Provides human-friendly signal alerts for both core signals and MSS discoveries.

### Feature Specifications
- **Comprehensive Integrations**: Leverages Coinglass v4 for market data, liquidations, and open interest; LunarCrush v4 for social sentiment (7,634+ coins, Topics API); CoinAPI for comprehensive market data and whale detection; Binance Futures for futures market data; and CoinGecko for coin discovery.
- **LunarCrush v4 Features**: 
  - Coins Discovery endpoint with Galaxy Score and AltRank filtering
  - Topics API for social metrics and trend analysis
  - 7,634+ coins tracked with rich social data
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
- **Coinglass v4 Standard ($299/month)**: 65 production endpoints (verified 100% working) covering:
  - **Market Data**: Liquidations (7 endpoints), funding rates (6 endpoints), open interest (6 endpoints)
  - **Positioning**: Trader ratios (4 endpoints), taker buy/sell volume (1 endpoint)
  - **Whale Intelligence**: Orderbook depth (5 endpoints), Hyperliquid DEX (3 endpoints), on-chain tracking (2 endpoints)
  - **Technical Analysis**: RSI list (535 coins), 11 technical indicators including Whale Index, CGDI, CDRI, Golden Ratio
  - **Macro & News**: Fear & Greed Index, Economic Calendar (675+ events), News Feed (20+ sources)
  - **Real-Time Streaming**: WebSocket API for live liquidation data across all exchanges
- **Coinglass WebSocket**: Real-time liquidation streaming at wss://open-ws.coinglass.com/ws-api with ping/pong keepalive every 20 seconds.
- **LunarCrush Builder ($240/month)**: Social sentiment, community engagement metrics, social momentum analysis, and real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Public API for futures market data, coin discovery, 24hr statistics, funding rates, open interest, and new listings information.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, and category-based coin search.