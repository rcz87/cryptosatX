# Crypto Futures Signal API

## Overview
This project is a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL). It uses a multi-factor weighted scoring system, a Multi-Modal Signal Score (MSS) for emerging cryptocurrencies, a Binance New Listings Monitor, and a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation. The API aims to be a robust tool for informed and automated crypto trading decisions, with a focus on GPT Actions integration and significant market potential.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability
- **API Quota Optimization**: Background tasks disabled to save 99% API quota while maintaining full GPT Actions functionality

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
- **Hybrid AI Signal Judge (GPT-5.1)**: Integrates OpenAI GPT-5.1 (upgraded November 2025) with rule-based fallback for signal validation, providing `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, and `Volatility Metrics`. Features 45% fewer hallucinations and improved accuracy vs GPT-4.
- **GPT-5.1 Self-Evaluation System**: AI Judge now includes historical performance context for self-learning. Analyzes past signal outcomes (win rate, ROI, verdict effectiveness) to improve future decisions and reduce false positives.
- **GPT-5.1 Enhanced Reasoning Mode**: Implements multi-layer analysis via advanced prompt engineering. Features explicit layer-by-layer validation (Technical → On-Chain → Sentiment → Whale Activity → Coherence Check) with evidence tracking for complete transparency in AI verdict decisions.
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
- **Analytics API for Performance Tracking**: Comprehensive analytics service with REST and RPC endpoints for querying signal performance data. Supports GPT-5.1 self-evaluation by providing historical context (win rates, ROI, verdict effectiveness) to improve AI decision-making over time.

## Background Task Configuration (API Quota Optimization)

**Current Status: DISABLED (saves ~12,780 API calls/hour)**

To optimize API quota usage and prevent rapid consumption of external API limits, the following background monitoring systems are **currently disabled** in `app/main.py`:

### Disabled Systems:
1. **Auto Scanner** (~200-300 calls/hour)
   - Smart Money Scan (whale activity detection)
   - MSS Discovery (new listing gems)
   - RSI Screener (technical screening)
   - LunarCrush Trending (social momentum tracking)
   
2. **Real-Time Spike Detectors** (~12,780 calls/hour)
   - Price Spike Detector: ~12,000 calls/hour (100 coins × 30s interval)
   - Social Spike Monitor: ~600 calls/hour (50 coins × 5min interval)
   - Liquidation Detector: ~180 calls/hour (60s interval)

### What Still Works (100% Functional):
- ✅ **Manual Signal Endpoints**: `GET /signals/{symbol}`, `POST /invoke`, all GPT Actions endpoints
- ✅ **On-Demand Signals**: Called only when user/GPT requests
- ✅ **Performance Tracker**: Tracks signal outcomes at 1h, 4h, 24h, 7d, 30d intervals
- ✅ **Cache Cleanup**: 5-minute interval (uses no external APIs)
- ✅ **Telegram Alerts**: Sent for manual LONG/SHORT signals
- ✅ **All API Endpoints**: 268 routes fully operational

### Expected API Usage:
- **With Background Tasks Disabled**: ~50-100 calls/hour (depends on manual requests)
- **With Background Tasks Enabled**: ~12,780+ calls/hour (automated scanning)
- **Savings**: 99% reduction in API quota consumption

### How to Re-enable Background Tasks:
If you need 24/7 automated monitoring and have sufficient API quota, uncomment the following sections in `app/main.py`:

1. **Auto Scanner** (lines ~106-112):
   ```python
   from app.services.auto_scanner import auto_scanner
   await auto_scanner.start()
   ```

2. **Spike Detectors** (lines ~133-150):
   ```python
   from app.services.realtime_spike_detector import realtime_spike_detector
   asyncio.create_task(realtime_spike_detector.start())
   
   from app.services.liquidation_spike_detector import liquidation_spike_detector
   asyncio.create_task(liquidation_spike_detector.start())
   
   from app.services.social_spike_monitor import social_spike_monitor
   asyncio.create_task(social_spike_monitor.start())
   ```

3. **Shutdown Handlers** (lines ~169-181):
   ```python
   await auto_scanner.stop()
   realtime_spike_detector.stop()
   liquidation_spike_detector.stop()
   social_spike_monitor.stop()
   ```

Then restart the workflow to apply changes.

## External Dependencies
- **CoinAPI**: Market data, OHLCV, order book, quotes, price aggregation, whale detection.
- **OpenAI GPT-5.1**: AI signal judge with self-evaluation capabilities, market sentiment analysis, signal validation. Upgraded from GPT-4 in November 2025 for improved accuracy (45% fewer hallucinations).
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming.
- **LunarCrush Builder**: Social sentiment, community engagement, social momentum, real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database.