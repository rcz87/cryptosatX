# Crypto Futures Signal API

## Overview
This project provides a production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals. It aggregates diverse market data (price action, funding rates, open interest, social sentiment) to offer LONG/SHORT/NEUTRAL recommendations via a multi-factor weighted scoring system. The API is designed for compatibility with GPT Actions, aiming to provide a robust tool for informed trading decisions with significant market potential. Key capabilities include an advanced Multi-Modal Signal Score (MSS) system for identifying high-potential emerging cryptocurrencies and a Binance New Listings Monitor for early detection of fresh perpetual futures listings. The system also includes an experimental GPT-4 Signal Judge for structured validation of signals.

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
- **Multi-Modal Signal Score (MSS)**: A 3-phase analytical framework for discovering emerging cryptocurrencies by filtering based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns (BOS, CHoCH, FVG, swing points, liquidity zones) across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic coin discovery, allowing analysis of any cryptocurrency and filtering.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for performance.
- **Comprehensive Coinglass Integration**: Over 60 production endpoints verified operational covering various market data, liquidations, funding rates, open interest, and technical indicators.
- **Real-Time WebSocket Streaming**: WebSocket endpoint for live liquidation data across all exchanges.
- **Unified RPC Endpoint with Flat Parameters**: Single POST `/invoke` endpoint provides access to ALL 192+ operations via RPC interface, bypassing GPT Actions' 30-operation limit. Supports both nested (`args: {...}`) and flat (root-level) parameters.
- **API Endpoints**: Includes endpoints for enhanced trading signals (`/signals/{symbol}`), aggregated raw market data (`/market/{symbol}`), GPT Actions flat parameter endpoints (`POST /gpt/signal`, etc.), unified RPC endpoint (`POST /invoke`), direct Coinglass and LunarCrush data access, Smart Money analysis, MSS functionality, Binance New Listings, and WebSocket streaming.
- **Signal History Storage**: Stores LONG/SHORT signals and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup.
- **Telegram Notifier**: Provides human-friendly signal alerts.
- **OpenAI V2 Integration**: Experimental `/openai/v2/*` endpoints for a GPT-4 Signal Judge, providing structured validation with verdicts (CONFIRM/DOWNSIZE/SKIP/WAIT), key agreements/conflicts detection, risk adjustment suggestions, and Telegram-ready summaries.

### Feature Specifications
- **Comprehensive Integrations**: Leverages Coinglass v4 for market data; LunarCrush v4 for social sentiment; CoinAPI for comprehensive market data and whale detection; Binance Futures for futures market data; and CoinGecko for coin discovery.
- **LunarCrush v4 Features**: Coins Discovery endpoint with Galaxy Score and AltRank filtering, Topics API for social metrics and trend analysis, tracking over 7,634 coins.
- **Output**: Signals include recommendation, composite score, confidence level, top 3 contributing factors, and raw metrics (in debug mode). MSS alerts include a 3-phase breakdown and tier classification.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` driver and connection pooling.
- **Environment Management**: python-dotenv.

## External Dependencies
- **CoinAPI Startup**: Market data, OHLCV, order book depth, recent trades, real-time quotes, multi-exchange price aggregation, and whale detection.
- **Coinglass v4 Standard**: Provides access to liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis (RSI, various indicators), macro calendar, news feed, and real-time WebSocket streaming.
- **Coinglass WebSocket**: Real-time liquidation streaming at `wss://open-ws.coinglass.com/ws-api`.
- **LunarCrush Builder**: Social sentiment, community engagement metrics, social momentum analysis, and real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Public API for futures market data, coin discovery, 24hr statistics, funding rates, open interest, and new listings information.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, and category-based coin search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database for signal history storage.