# Crypto Futures Signal API

## Overview
This project provides a FastAPI backend for generating real-time cryptocurrency futures trading signals. It integrates diverse market data to offer LONG/SHORT/NEUTRAL recommendations via a multi-factor weighted scoring system. Key features include an advanced Multi-Modal Signal Score (MSS) for identifying emerging cryptocurrencies, a Binance New Listings Monitor, and a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation and risk management. The API is designed for compatibility with GPT Actions, aiming to be a robust tool for informed and automated crypto trading decisions with significant market potential.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application uses a modular FastAPI architecture, separating API routes, business logic, and external service integrations.

### Symbol Normalization
**Universal Symbol Normalizer** (November 2025) - Centralized system supporting short-form ticker input (e.g., "SOL") with automatic conversion to provider-specific formats. Enables natural language queries via GPT Actions without requiring full symbol names.

**Supported Formats:**
- CoinGlass: `SOL` → `SOLUSDT`
- LunarCrush: `SOL` / `SOLUSDT` → `SOL`
- CoinAPI: `SOL` → `BINANCE_SPOT_SOL_USDT`
- Binance: `SOL` → `SOLUSDT`
- OKX: `SOL` → `SOL-USDT-SWAP`
- CoinGecko: `SOL` / `SOLUSDT` → `solana`

**Dictionary Coverage:** 55+ popular cryptocurrencies including BTC, ETH, SOL, BNB, AVAX, DOGE, PEPE, ARB, OP, and more.

**Implementation:** All services updated to use `app/utils/symbol_normalizer.py` for consistent symbol conversion. Backward compatible with full symbol formats (e.g., "BTCUSDT" still works).

### UI/UX Decisions
The API delivers clean JSON responses and includes a debug mode (`?debug=true`). OpenAPI documentation is available at `/docs` and `/redoc`, with a GPT Actions-compatible schema.

### Technical Implementations
- **Signal Engine**: An 8-factor weighted scoring system (0-100 scale) generates signals based on Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed.
- **Hybrid AI Signal Judge**: Integrates GPT-4 for signal validation with a rule-based fallback, providing a `Verdict` (CONFIRM/DOWNSIZE/SKIP/WAIT), `Risk Mode`, `Position Multiplier`, `AI Summary`, `Layer Checks`, and `Volatility Metrics` (ATR-based).
- **AI Verdict Accuracy Tracking**: Monitors price movements and P&L to validate AI verdict effectiveness, storing results in PostgreSQL.
- **Multi-Modal Signal Score (MSS)**: A 3-phase framework for discovering emerging cryptocurrencies based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic cryptocurrency discovery.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for enhanced performance.
- **Comprehensive Coinglass Integration**: Over 60 production endpoints for market data, liquidations, funding rates, and open interest.
- **Real-Time WebSocket Streaming**: Provides a WebSocket endpoint for live liquidation data.
- **Unified RPC Endpoint**: A single POST `/invoke` endpoint offers RPC access to all operations with flat parameters, including 64 Coinglass operations, 7 CoinAPI operations, 17 LunarCrush endpoints, and Binance New Listings monitor (89 total). Validated at 96.6% success rate with smart cleanup (November 2025).
- **Binance New Listings Monitor**: RPC-enabled endpoint (`new_listings.binance`) for detecting new perpetual futures listings with trading statistics. Supports lookback periods of 1-168 hours. Note: May be geo-blocked in some regions (HTTP 451) - use LunarCrush coin discovery as alternative.
- **API Endpoints**: Includes endpoints for enhanced trading signals, aggregated raw market data, GPT Actions, direct Coinglass and LunarCrush data, Smart Money analysis, MSS, Binance New Listings, WebSocket streaming, and OpenAI V2 Signal Judge validation.
- **Signal History Storage**: Stores LONG/SHORT and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup.
- **Telegram Notifier**: Provides human-friendly signal alerts with AI verdict, risk mode, position sizing, and factor analysis.
- **LunarCrush v4 Features**: Includes Coins Discovery, Topics API, Topics List for trending topics, and Theme Analyzer for AI-free sentiment detection.
- **Social Hype Engine** (November 2025): Complete 6-feature analytics system for detecting viral trends and pump risks:
  1. **Social Hype Score (0-100)**: Composite metric from social volume, engagement, contributors, dominance, and sentiment with log-scale normalization
  2. **Platform-Specific Hype**: Individual scores for Twitter, TikTok, Reddit, YouTube, News with pump risk classification (LOW/MODERATE/HIGH/EXTREME)
  3. **Hype Momentum Tracker**: Detects ACCELERATING/STABLE/FADING trends with BUY/HOLD/SELL signals and strength scoring (0-10)
  4. **Hype vs Price Correlation**: Pattern detection (HYPE_PUMP, HYPE_BUILDING, ORGANIC_GROWTH, etc.) with confidence scores and trading recommendations
  5. **Historical Hype Database**: PostgreSQL storage of all hype metrics with optimized indexes for trend analysis and spike detection
  6. **Hype Spike Alerts**: Auto-detects >20% hype increases within 6-hour windows, triggers Telegram notifications with severity classification (MODERATE/HIGH/EXTREME)
- **Output**: Signals include recommendation, composite score, confidence, top contributing factors, and raw metrics (in debug mode). MSS alerts provide a 3-phase breakdown and tier classification.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` and connection pooling.
- **Environment Management**: python-dotenv.

## External Dependencies
- **CoinAPI Startup**: Market data, OHLCV, order book, quotes, price aggregation, whale detection.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed.
- **Coinglass WebSocket**: Real-time liquidation streaming at `wss://open-ws.coinglass.com/ws-api`.
- **LunarCrush Builder**: Social sentiment, community engagement, social momentum, real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Futures market data, coin discovery, 24hr statistics, funding rates, open interest, new listings.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, category search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database for signal history storage.

## Known Limitations & Workarounds

### LunarCrush API v4 (Builder Tier - November 2025)
**Pricing:** Builder tier at $240/month includes full social sentiment data access with 100 req/min and 20,000 req/day limits.

**Implementation Strategy:** Dual-endpoint concurrent fetch for comprehensive data:
- **Primary:** `/coins/list/v2` - Real-time coin data with market metrics + social volume/dominance/sentiment (no cache)
- **Secondary:** `/topic/{topic}/v1` - Platform-specific breakdown (Twitter, Reddit, TikTok, YouTube, News)
- **Performance:** Concurrent API calls via `asyncio.gather` for optimal latency

**API v4 Endpoint Differences:**
- `/coins/{symbol}/v1` - Market data only (price, market cap, galaxy score) - NO social metrics
- `/coins/list/v2` - Complete data (market + social) - ✅ Used in production
- `/topic/{topic}/v1` - Social breakdown by platform - ✅ Used in production

**Validated Metrics (100% Accuracy):**
- Social Volume, Engagement, Contributors, Dominance ✅
- Platform-specific volumes (Twitter, Reddit, TikTok, YouTube, News) ✅
- Sentiment analysis (overall + per-platform) ✅
- Galaxy Score, Alt Rank, Market data ✅

### LunarCrush API Constraints
- **Multi-Chain Token Disambiguation**: Symbols like "BEAT" may map to multiple tokens across different chains (e.g., MetaBeat on Polygon vs Audiera BEAT on BNB Chain). Current implementation defaults to first/most established token. **Workaround**: Specify chain/project name in query (e.g., "Audiera BEAT" or "BEAT on BNB Chain").
- **New Token Indexing Delay**: Newly listed tokens (<7 days) require 24-48 hours for full social metrics indexing. **Workaround**: Use CoinGlass for funding/OI data (faster) and cross-verify with exchange APIs.

### Geographic Restrictions
- **Binance API**: May be geo-blocked (HTTP 451) in certain regions due to regulatory compliance. **Workaround**: Use LunarCrush coin discovery, CoinGlass market data, or OKX/CoinGecko as alternatives.

### Data Accuracy for Edge Cases
- **Established Coins** (BTC, ETH, SOL, major altcoins): 100% accurate across all metrics.
- **New/Micro-Cap Coins**: Galaxy Score and Alt Rank accurate; social volume may lag or default to older tokens with same ticker. Manual verification recommended for trending coins.
- **Multi-Chain Tokens**: Specify chain explicitly to avoid ambiguity.