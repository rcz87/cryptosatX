# Crypto Futures Signal API

## Overview
This project provides a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL) using a multi-factor weighted scoring system. It features a Multi-Modal Signal Score (MSS) for identifying emerging cryptocurrencies, a Binance New Listings Monitor, a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation, and a Scalping Analysis Engine with 8 real-time data layers optimized for GPT Actions integration. The API aims to be a robust tool for informed and automated crypto trading decisions, with significant market potential and full compatibility with GPT Actions.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application uses a modular FastAPI architecture, separating API routes, business logic, and external service integrations.

### UI/UX Decisions
The API provides clean JSON responses, offers a debug mode, and includes OpenAPI documentation (`/docs`, `/redoc`) with a GPT Actions-compatible schema.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` and connection pooling; SQLite for Replit compatibility.
- **Database Migrations**: Alembic for version-controlled PostgreSQL schema changes.
- **Environment Management**: python-dotenv.

### Technical Implementations
- **Alembic Database Migrations**: Implemented for version-controlled PostgreSQL schema management, supporting async operations and SSL.
- **Performance Optimization with Caching**: An in-memory caching layer with intelligent TTL management for 5 data types (Price, Liquidations, Funding Rate, Social Sentiment, Fear & Greed Index). Includes cache statistics, per-symbol invalidation, and batch operations.
- **Universal Symbol Normalizer**: Centralized system for consistent symbol formatting across data providers.
- **Scalping Analysis Engine**: Provides high-frequency trading analysis using 8 real-time data layers, optimized for GPT Actions.
- **Market Summary Service**: RPC operation providing aggregate market conditions and bilingual (Indonesian/English) explanations with actionable trading recommendations for major cryptocurrencies.
- **Natural Language Processing (NLP) Router**: Supports bilingual natural language queries, automatically routing to relevant data layers (e.g., Signal, Scalping, News). Includes dynamic mode detection (Conservative, Aggressive, Ultra) from natural language inputs.
- **Signal Engine**: Uses an 8-factor weighted scoring system (0-100) based on various market indicators. Features a 3-Mode Threshold System (Conservative, Aggressive, Ultra) for selectable risk profiles. Includes weight normalization and startup validation for consistent scoring.
- **Signal Engine Error Handling & Quality Tracking**: Comprehensive service-level error tracking with 3-tier categorization, data quality scoring, and detailed failure reports.
- **Hybrid AI Signal Judge**: Integrates GPT-4 and a rule-based fallback for signal validation, providing `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, and `Volatility Metrics`.
- **AI Verdict Accuracy Tracking**: Monitors price movements and P&L to validate AI verdict effectiveness, storing results in PostgreSQL.
- **Multi-Modal Signal Score (MSS)**: A 3-phase framework for discovering emerging cryptocurrencies based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko.
- **Unified RPC Endpoint**: A single POST `/invoke` endpoint provides RPC access to all operations.
- **RPC Timeout Protection**: Prevents hanging requests with configurable timeouts and graceful error handling.
- **GPT Actions Compatibility Improvements**: Enhanced RPC and REST endpoints for GPT Actions, including method name alignment, response size optimization via smart pagination (e.g., RSI list), multi-layer validation, and controlled news feed parameters.
- **GPT Actions Testing & Monitoring System**: Infrastructure for ensuring GPT Actions compatibility, including real-time response size monitoring, advanced rate limiting, 6 dedicated monitoring endpoints, and an automated test suite.
- **Binance New Listings Monitor**: RPC-enabled endpoint for detecting new perpetual futures listings.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in PostgreSQL with JSON backup.
- **Telegram Notifier**: Provides human-friendly signal alerts.
- **LunarCrush v4 Features**: Includes Coins Discovery, Topics API, Topics List, and Theme Analyzer.
- **Social Hype Engine**: A 6-feature analytics system for detecting viral trends and pump risks.

## External Dependencies
- **CoinAPI**: Market data, OHLCV, order book, quotes, price aggregation, whale detection, with production-ready error handling.
- **OpenAI GPT-4**: AI signal judge, market sentiment analysis, signal validation, with production-ready error handling.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming.
- **LunarCrush Builder**: Social sentiment, community engagement, social momentum, real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database.