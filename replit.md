# Crypto Futures Signal API

## Overview
This project delivers a FastAPI-based backend for generating real-time cryptocurrency futures trading signals. It offers LONG/SHORT/NEUTRAL recommendations through a multi-factor weighted scoring system and an advanced Multi-Modal Signal Score (MSS) for identifying emerging cryptocurrencies. Key features include a Binance New Listings Monitor, a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation, and a dedicated Scalping Analysis Engine with 8 real-time data layers optimized for GPT Actions integration. The API is designed for compatibility with GPT Actions, serving as a robust tool for informed and automated crypto trading decisions with significant market potential.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application employs a modular FastAPI architecture, separating API routes, business logic, and external service integrations.

### UI/UX Decisions
The API provides clean JSON responses, offers a debug mode (`?debug=true`), and includes OpenAPI documentation at `/docs` and `/redoc`, with a GPT Actions-compatible schema.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` and connection pooling.
- **Environment Management**: python-dotenv.

### Technical Implementations
- **Performance Optimization with Caching (2025-11-14)**: In-memory caching layer using async cache service with intelligent TTL management for optimal API rate limiting and response times. Implements 5-tier caching strategy: Price data (5s TTL), Liquidations (10s), Funding Rate (15s), Social Sentiment (60s), Fear & Greed Index (300s). Features include automatic cache cleanup every 5 minutes, cache statistics monitoring via `/cache/stats` endpoint, per-symbol cache invalidation, and batch operation support. Batch endpoints (`/batch/prices`, `/batch/signals`, `/batch/quick-scan`) enable concurrent multi-symbol fetching with cache optimization, reducing API calls by up to 80% for frequently accessed data. Provides cache performance grading (A+ to F) with actionable recommendations for TTL tuning.
- **Universal Symbol Normalizer**: Centralized system converting short-form tickers (e.g., "SOL") to provider-specific formats for consistent data retrieval across services.
- **Scalping Analysis Engine**: Dedicated endpoints (`/scalping/quick/{symbol}`, `/scalping/analyze`, `/scalping/info`) provide high-frequency trading analysis using 8 real-time data layers: Price & OHLCV, Orderbook History, RSI, Volume Delta, Liquidations, Funding Rate, Long/Short Ratio, Smart Money Flow, Hyperliquid Whale Positions, Fear & Greed Index, OHLCV Trend Analysis, Recent Trades, and Sentiment Analysis. Features concurrent data fetching and GPT Actions optimization.
- **Market Summary Service (2025-11-14)**: RPC operation `market.summary` provides aggregate market condition across 5 major cryptocurrencies (BTC, ETH, SOL, XRP, BNB). Returns overall market sentiment (BULLISH/BEARISH/NEUTRAL/MIXED), individual coin signals with scores and prices, aggregate metrics (average funding rate, signal distribution, market bias), bilingual Indonesian/English explanation of market conditions, and actionable trading recommendations based on current state. Features parallel data fetching (~11s execution), 100% data quality tracking, and GPT-optimized responses for queries like "kenapa market merah semua?" or "why is crypto crashing?". Includes intelligent analysis of funding rates, liquidation risks, and position biases.
- **Natural Language Processing (NLP) Router**: A single endpoint (`/nlp/analyze`) supports bilingual (Indonesian/English) natural language queries with intelligent mode detection, automatically routing to relevant data layers (e.g., Signal, Scalping, News, Whale Positions, Sentiment, Funding Rate, Liquidations, Long/Short Ratio, RSI, Smart Money, OHLCV Trend, Spot Price, Volume Delta). **Natural Language Mode Selection (2025-11-14):** NLP router now detects signal modes from natural language queries in both Indonesian and English. Supports mode keywords (konservatif/conservative, agresif/aggressive, ultra/extreme), numeric patterns (mode 1/2/3, m1/m2/m3), and descriptive aliases (aman/safe, seimbang/balanced, scalping). Automatically extracts mode from queries like "signal BTC mode 3", "analisis ETH agresif", "sinyal XRP konservatif", "scalping SOL ultra" and passes to appropriate analysis layers. Defaults to aggressive mode when no mode specified. Works with all layer types including new "signal" layer for LONG/SHORT/NEUTRAL recommendations and "scalping" layer for data aggregation.
- **Signal Engine**: An 8-factor weighted scoring system (0-100) generates signals based on Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed. **Weight Normalization Fix (2025-11-14):** Corrected weight distribution from 110% to exactly 100% by strategically reducing less reliable factors (social sentiment, fear/greed, OI trend). Added startup validation to ensure weights always sum to 100%. Current distribution prioritizes price action (20%), liquidations (24%), and funding rate (18%) while reducing sentiment-based factors. Minimal impact on existing signals with improved normalization accuracy. **3-Mode Threshold System (2025-11-14):** Implemented selectable risk profiles with mode parameter support via RPC API (`signals.get` operation). Three modes available: (1) Conservative (0-48/48-52/52-100) for beginners with reliable signals and minimal false positives; (2) Aggressive [DEFAULT] (0-45/45-55/55-100) for balanced risk/reward, catching trends earlier; (3) Ultra (0-49/49-51/51-100) for pro scalpers with maximum actionable signals and high-frequency trading. Mode parameter accepts both numeric (1/2/3) and string values (conservative/aggressive/ultra/safe/balanced/extreme/scalping). All modes share the same 8-factor scoring system with identical weights; only signal determination thresholds differ. Response includes comprehensive mode_info object with thresholds, risk level, description, and best-use recommendations. Fully GPT Actions compatible for ChatGPT-driven mode selection.
- **Signal Engine Error Handling & Quality Tracking**: Comprehensive service-level error tracking with 3-tier categorization (CRITICAL/IMPORTANT/OPTIONAL). Tracks all 16 data sources individually, calculates data quality score (0-100%), and enforces minimum 50% quality threshold (configurable). Provides detailed failure reports with service names, tiers, and error messages in every signal response. Features price data hard-fail protection, fallback tracking for funding/OI services, and enhanced logging with quality metrics. Enables transparent monitoring of data provider reliability and signal integrity.
- **Hybrid AI Signal Judge**: Integrates GPT-4 and a rule-based fallback for signal validation, providing a `Verdict`, `Risk Mode`, `Position Multiplier`, `AI Summary`, `Layer Checks`, and `Volatility Metrics`.
- **AI Verdict Accuracy Tracking**: Monitors price movements and P&L to validate AI verdict effectiveness, storing results in PostgreSQL.
- **Multi-Modal Signal Score (MSS)**: A 3-phase framework for discovering emerging cryptocurrencies based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic cryptocurrency discovery.
- **Unified RPC Endpoint**: A single POST `/invoke` endpoint provides RPC access to all operations, including Coinglass, CoinAPI, LunarCrush, and Binance New Listings monitor.
- **RPC Timeout Protection**: Both RPC dispatchers (standard and flat) include timeout protection using `asyncio.wait_for()` to prevent hanging requests. Default timeout is 30 seconds with operation-specific overrides (45s for signal generation, 60s for MSS/smart money scans, 180s for backtesting). Features graceful timeout handling with user-friendly error messages, context-aware suggestions, and safe JSON serialization for all request parameters.
- **Binance New Listings Monitor**: RPC-enabled endpoint (`new_listings.binance`) for detecting new perpetual futures listings with trading statistics.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup.
- **Telegram Notifier**: Provides human-friendly signal alerts with AI verdict, risk mode, position sizing, and factor analysis.
- **LunarCrush v4 Features**: Includes Coins Discovery, Topics API, Topics List for trending topics, and Theme Analyzer for AI-free sentiment detection.
- **Social Hype Engine**: A 6-feature analytics system for detecting viral trends and pump risks, including a Social Hype Score, platform-specific hype analysis, Hype Momentum Tracker, Hype vs Price Correlation, Historical Hype Database, and Hype Spike Alerts.

## External Dependencies
- **CoinAPI Startup (2025-11-14 UPGRADED)**: Market data, OHLCV, order book, quotes, price aggregation, whale detection. Enhanced with production-ready error handling: 5-tier error categorization (401/429/404/timeout/network/parsing), user-friendly error messages without internal details exposure, critical error alerts via Telegram, API key validation on initialization, and emoji-based logging (🔴/⚠️/⏱️/🌐) for structured monitoring. Features graceful degradation with safe defaults and automatic rate limit handling.
- **OpenAI GPT-4 (2025-11-14 UPGRADED)**: AI signal judge, market sentiment analysis, signal validation. Enhanced with production-ready error handling matching CoinAPI pattern: 5-tier error categorization (401/429/400-422/500+/network), user-friendly error messages with zero internal detail exposure, Telegram critical alerts for auth failures and unexpected errors, timeout protection, and emoji-based logging (🔴/⚠️/⏱️/🌐/❌). All str(e) exposures eliminated across 7 error points (3 main methods + 2 parsers + 2 legacy functions). Features graceful degradation with safe fallback responses and consistent error handling pattern.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming.
- **LunarCrush Builder**: Social sentiment, community engagement, social momentum, real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database for signal history storage.