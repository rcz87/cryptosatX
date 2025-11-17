# Crypto Futures Signal API

## Overview
This project provides a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL) using a multi-factor weighted scoring system. It features a Multi-Modal Signal Score (MSS) for identifying emerging cryptocurrencies, a Binance New Listings Monitor, a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation, and a Scalping Analysis Engine optimized for GPT Actions integration. The API aims to be a robust tool for informed and automated crypto trading decisions, with significant market potential and full compatibility with GPT Actions.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application uses a modular FastAPI architecture, separating API routes, business logic, and external service integrations. It provides clean JSON responses, offers a debug mode, and includes OpenAPI documentation with a GPT Actions-compatible schema.

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
- **Alembic Database Migrations**: For version-controlled PostgreSQL schema management.
- **Performance Optimization with Caching**: An in-memory caching layer with intelligent TTL management for 5 data types.
- **Universal Symbol Normalizer**: For consistent symbol formatting across data providers.
- **Scalping Analysis Engine**: High-frequency trading analysis using 8 real-time data layers, optimized for GPT Actions. Includes aggressive compression for GPT Actions.
- **Market Summary Service**: Provides aggregate market conditions and bilingual (Indonesian/English) explanations.
- **Natural Language Processing (NLP) Router**: Supports bilingual natural language queries, routing to relevant data layers and detecting risk modes.
- **Signal Engine**: Uses an 8-factor weighted scoring system with a 3-Mode Threshold System for selectable risk profiles. Includes comprehensive error handling and data quality tracking.
- **Hybrid AI Signal Judge**: Integrates GPT-4 and a rule-based fallback for signal validation, providing `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, and `Volatility Metrics`. Includes AI verdict accuracy tracking.
- **Multi-Modal Signal Score (MSS)**: A 3-phase framework for discovering emerging cryptocurrencies based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes with **dynamic coin discovery** (upgraded from 38 hardcoded coins to 100-200+ coins auto-discovered from CoinGecko by 24h volume). Features:
  - **Dynamic Discovery**: Auto-fetches top coins by trading volume using CoinGecko API (geo-friendly, no restrictions)
  - **Intelligent Caching**: 5-minute TTL to reduce API calls and improve performance  
  - **Configurable Scale**: `MAX_SMART_MONEY_COINS` environment variable (default: 100, max: 250)
  - **Fallback Mechanism**: Automatically falls back to hardcoded SCAN_LIST if API fails
  - **Toggle Control**: `SMART_MONEY_DYNAMIC_DISCOVERY` environment variable (default: true)
- **Dynamic Coin Discovery**: Integrates CoinGecko API (replaced geo-blocked Binance Futures with geo-friendly CoinGecko).
- **Unified RPC Endpoint**: A single POST `/invoke` endpoint provides RPC access to all operations with timeout protection.
- **GPT Actions Compatibility Improvements**: Enhanced RPC and REST endpoints for GPT Actions, including method name alignment, response size optimization, and multi-layer validation.
- **GPT Actions Testing & Monitoring System**: Infrastructure for ensuring GPT Actions compatibility, including real-time response size monitoring, rate limiting, monitoring endpoints, and an automated test suite.
- **Automated Regression Testing System**: Production-ready test suite with 10 comprehensive GPT Actions integration tests, including strict HTTP 200 assertions and size validation.
- **AI Verdict Database Constraint Fixes**: Critical data integrity improvements to `ai_verdict_performance` table with foreign key and unique constraints.
- **Binance New Listings Monitor**: RPC-enabled endpoint for detecting new perpetual futures listings.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in PostgreSQL.
- **Telegram Notifier**: Provides human-friendly signal alerts.
- **LunarCrush v4 Features**: Includes Coins Discovery, Topics API, Topics List, and Theme Analyzer.
- **Social Hype Engine**: A 6-feature analytics system for detecting viral trends and pump risks.
- **Enhanced Logging System**: Comprehensive logging improvements for production monitoring and debugging, including timezone conversion (UTC to WIB), detailed request logging with sensitive data redaction, and structured JSON output.
- **4-Phase Automated Scanning & Performance Tracking System**: Comprehensive 24/7 market monitoring infrastructure including:
    - **Phase 1 - Auto-Scanner with APScheduler**: Background task scheduler for automated scans.
    - **Phase 2 - Parallel Batch Processor & Smart Cache**: High-performance scanner with a 3-layer caching system.
    - **Phase 3 - Unified Ranking System**: Composite 0-100 scoring combining 6 signal sources with weighted contributions and multi-timeframe analysis.
    - **Phase 4 - Performance Validation & Analytics**: Automated outcome tracking with WIN/LOSS/NEUTRAL classification and performance metrics.
- **Phase 5 - Real-Time Spike Detection System**: Advanced multi-signal early-warning system for detecting market opportunities, featuring Price Spike Detector, Liquidation Spike Detector, and Social Spike Monitor, coordinated to reduce false positives. Fully integrated with GPT Actions.
- **RPC Dispatcher Fixes & Integration Improvements**: Resolved critical method signature mismatches and implemented type safety for GPT Actions compatibility across all 202+ operations.

## External Dependencies
- **CoinAPI**: Market data, OHLCV, order book, quotes, price aggregation, whale detection.
- **OpenAI GPT-4**: AI signal judge, market sentiment analysis, signal validation.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming.
- **LunarCrush Builder**: Social sentiment, community engagement, social momentum, real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database.