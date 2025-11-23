# Crypto Futures Signal API

## Overview
This project provides a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL). It utilizes a multi-factor weighted scoring system, a Multi-Modal Signal Score (MSS) for emerging cryptocurrencies, a Binance New Listings Monitor, and a Hybrid AI Signal Judge (GPT-5.1 + rule-based fallback) for signal validation. The API aims to be a robust tool for informed and automated crypto trading decisions, with a focus on GPT Actions integration and significant market potential within the crypto trading landscape.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability
- API Quota Optimization: Background tasks & auto Telegram alerts disabled to save 99% API quota while maintaining full GPT Actions functionality
- All 188 endpoints available for on-demand manual calls via GPT Actions
- No auto-alerts to Telegram (manual alert endpoint available if needed)
- Communication: Bahasa Indonesia with natural, conversational language (not overly technical)
- Documentation: Simplified, practical, and action-oriented

## Recent Changes (November 23, 2025)
- ✅ **Fixed GPT-5.1 Integration**: Updated from deprecated gpt-4-turbo to gpt-5.1 model in OpenAI V2 service
- ✅ **Fixed signals.debug Operation**: Added missing handler in rpc_flat_dispatcher for signals.debug endpoint (was registered in catalog but had no implementation)
- ✅ **Fixed smart_money.scan_tiered**: Added missing handler to support 3-tier filtering system for efficient 1000+ coin scanning (8-10s execution time)
- ✅ **Updated Operation Count**: Standardized documentation from outdated 187/202 references to correct 188 total operations
- ✅ **Verified All 188 Operations**: Comprehensive testing confirms all endpoints returning valid data (coinglass, lunarcrush, smart_money, spike, mss, analytics, signals all working)
- ✅ **Built CoinAPI Dynamic Symbol Mapping**: Created comprehensive mapping file (637 BINANCE SPOT symbols) with alias support (e.g., HYPE→HYPER) for accurate symbol resolution
- ✅ **Enhanced Optional Service Handling**: Improved graceful degradation - LunarCrush and other OPTIONAL services no longer block signal generation when unavailable
- ✅ **Fixed Timezone Configuration**: Converted ALL timestamps from UTC to WIB (Asia/Jakarta, UTC+7) across entire application - signal_engine, API routes, storage, analytics, performance tracking - ensuring consistent Indonesia timezone
- ✅ **Improved Error Logging**: Separated log levels by service tier (CRITICAL=ERROR, IMPORTANT=WARNING, OPTIONAL=DEBUG) for clearer production monitoring

## System Architecture
The application uses a modular FastAPI architecture, separating API routes, business logic, and external service integrations. It provides clean JSON responses, offers a debug mode, and includes OpenAPI documentation with a GPT Actions-compatible schema.

### UI/UX Decisions
The API provides clean JSON responses and offers OpenAPI documentation (`/docs`, `/redoc`) with a GPT Actions-compatible schema.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` and connection pooling; SQLite for Replit compatibility.
- **Database Migrations**: Alembic for version-controlled PostgreSQL schema changes.
- **Environment Management**: python-dotenv.

### Technical Implementations
- **Multi-Tier Price Fallback System**: Implemented with CoinAPI, CoinGecko, and OKX for robust price data acquisition.
- **Unified RPC Endpoint**: Single POST `/invoke` endpoint for RPC access.
- **GPT Actions Compatibility**: Enhanced RPC and REST endpoints, method name alignment, response size optimization, and multi-layer validation.
- **Hybrid AI Signal Judge (GPT-5.1)**: Integrates OpenAI GPT-5.1 with rule-based fallback for signal validation, providing `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, and `Volatility Metrics`. Includes an Enhanced Reasoning Mode with multi-layer analysis.
- **Multi-Modal Signal Score (MSS)**: A 3-phase framework for discovering emerging cryptocurrencies.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes with dynamic coin discovery, intelligent caching, and rate limit safety.
- **Binance New Listings Monitor**: RPC-enabled endpoint for detecting new perpetual futures listings.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in PostgreSQL.
- **Telegram Notifier**: Provides human-friendly signal alerts.
- **Social Hype Engine**: 6-feature analytics system for detecting viral trends and pump risks using LunarCrush v4 data.
- **Real-Time Spike Detection System**: Advanced multi-signal early-warning system integrating Price Spike Detector, Liquidation Spike Detector, and Social Spike Monitor.
- **Enterprise-Grade Resilience & Rate Limit Protection**: Features a Circuit Breaker Pattern for LunarCrush API, Retry Logic with Exponential Backoff for CoinGecko, and Graceful Degradation.
- **Enhanced Technical Analysis Engine**: Integrates professional-grade technical indicators like MA, EMA, RSI, MACD, MA Crossover Detection, and Volume Confirmation Analysis.
- **Analytics API for Performance Tracking**: Comprehensive analytics service with REST and RPC endpoints for querying signal performance data.

## External Dependencies
- **CoinAPI**: Market data, OHLCV, order book, quotes, price aggregation, whale detection, symbol discovery, derivatives metrics.
- **OpenAI GPT-5.1**: AI signal judge with self-evaluation capabilities, market sentiment analysis, signal validation.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming.
- **LunarCrush Builder v4**: Social sentiment, community engagement, social momentum, real-time coin discovery, comprehensive metrics, pump risk analysis, hype-price correlation.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database.