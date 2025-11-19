# Crypto Futures Signal API

## Overview
This project is a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL). It uses a multi-factor weighted scoring system, a Multi-Modal Signal Score (MSS) for emerging cryptocurrencies, a Binance New Listings Monitor, and a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation. The API aims to be a robust tool for informed and automated crypto trading decisions, with a focus on GPT Actions integration and significant market potential.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

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
- **Alembic Database Migrations**: For version-controlled PostgreSQL schema management.
- **Performance Optimization**: In-memory caching with intelligent TTL management.
- **Universal Symbol Normalizer**: Consistent symbol formatting across data providers.
- **Scalping Analysis Engine**: High-frequency trading analysis optimized for GPT Actions.
- **Market Summary Service**: Provides aggregate market conditions and bilingual explanations.
- **Natural Language Processing (NLP) Router**: Supports bilingual natural language queries, routing to relevant data layers and detecting risk modes.
- **Signal Engine**: 8-factor weighted scoring system with a 3-Mode Threshold System for risk profiles, including error handling and data quality tracking.
- **Hybrid AI Signal Judge**: Integrates GPT-4 and a rule-based fallback for signal validation, providing `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, and `Volatility Metrics`.
- **Multi-Modal Signal Score (MSS)**: 3-phase framework for discovering emerging cryptocurrencies (tokenomics, community momentum, institutional validation).
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes with dynamic coin discovery. Features intelligent caching and rate limit safety.
- **Dynamic Coin Discovery**: Integrates CoinGecko API for geo-friendly coin fetching.
- **Unified RPC Endpoint**: Single POST `/invoke` endpoint for RPC access with timeout protection.
- **GPT Actions Compatibility**: Enhanced RPC and REST endpoints, method name alignment, response size optimization, and multi-layer validation.
- **GPT Actions Testing & Monitoring System**: Infrastructure for compatibility, real-time response size monitoring, rate limiting, and an automated test suite.
- **Automated Regression Testing System**: Production-ready test suite with comprehensive GPT Actions integration tests.
- **AI Verdict Database Constraint Fixes**: Critical data integrity improvements to `ai_verdict_performance` table.
- **Binance New Listings Monitor**: RPC-enabled endpoint for detecting new perpetual futures listings.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in PostgreSQL.
- **Telegram Notifier**: Provides human-friendly signal alerts.
- **LunarCrush v4 Features**: Includes Coins Discovery, Topics API, Topics List, and Theme Analyzer.
- **Social Hype Engine**: 6-feature analytics system for detecting viral trends and pump risks.
- **Enhanced Logging System**: Comprehensive logging for production monitoring and debugging, with timezone conversion, detailed request logging, and structured JSON output.
- **4-Phase Automated Scanning & Performance Tracking System**: 24/7 market monitoring infrastructure including a background task scheduler (Phase 1), parallel batch processor with caching (Phase 2), unified ranking system (Phase 3), and performance validation (Phase 4).
- **Phase 5 - Real-Time Spike Detection System**: Advanced multi-signal early-warning system for detecting market opportunities, integrating Price Spike Detector, Liquidation Spike Detector, and Social Spike Monitor.
- **RPC Dispatcher Fixes & Integration Improvements**: Resolved method signature mismatches and implemented type safety for GPT Actions compatibility.
- **Enterprise-Grade Resilience & Rate Limit Protection**: Features a Circuit Breaker Pattern for LunarCrush API, Retry Logic with Exponential Backoff for CoinGecko, and Graceful Degradation.
- **Enhanced Technical Analysis Engine**: Integrates professional-grade technical indicators like MA, EMA, RSI, MACD, MA Crossover Detection, and Volume Confirmation Analysis into the signal engine.
- **Risk Threshold Optimization**: Adjusted risk thresholds to align with signal engine logic, improving signal capture.
- **Duration-Based Auto-Stop Monitoring**: Enables flexible duration monitoring with automatic expiration for watchlist items.

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