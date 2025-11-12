# Crypto Futures Signal API

## Overview
This project is a production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals. It aggregates diverse market data (price action, funding rates, open interest, social sentiment) to provide LONG/SHORT/NEUTRAL recommendations based on a multi-factor weighted scoring system. The API is designed for compatibility with GPT Actions, aiming to provide a robust tool for informed trading decisions, with significant market potential in automated trading and signal provision services. It includes an advanced Multi-Modal Signal Score (MSS) system to identify high-potential emerging cryptocurrencies, plus a Binance New Listings Monitor for early detection of fresh perpetual futures listings before retail adoption.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application is built with FastAPI following a modular architecture, separating API routes, core business logic, and external service integrations.

### UI/UX Decisions
The API provides clean JSON responses and offers debug mode (`?debug=true`) for detailed metrics. OpenAPI documentation is available at `/docs` and `/redoc`, including a GPT Actions-compatible schema.

### Technical Implementations
- **Signal Engine**: An 8-factor weighted scoring system (0-100 scale) generates signals based on Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed.
- **Multi-Modal Signal Score (MSS)**: A 3-phase analytical framework for discovering emerging cryptocurrencies by filtering based on tokenomics (Discovery), community momentum (Social Confirmation), and institutional validation (Institutional Validation). Scores are stored with a "MSS_" prefix in the `signals` table.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns (BOS, CHoCH, FVG, swing points, liquidity zones) across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic coin discovery, allowing analysis of any cryptocurrency and filtering by market cap, volume, and category.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for performance.
- **Error Handling**: Robust error handling with safe defaults.
- **API Endpoints**: Includes endpoints for enhanced trading signals (`/signals/{symbol}`), aggregated raw market data (`/market/{symbol}`), GPT Actions schema (`/gpt/action-schema`), direct Coinglass and LunarCrush data access, Smart Money analysis (`/smart-money/*`), and MSS functionality (`/mss/*`).
- **Signal History Storage**: Stores LONG/SHORT signals (and high-scoring MSS signals) in a PostgreSQL database (Neon) with JSON file backup. Uses asyncpg for high-performance async operations.
- **Analytics & Insights**: Provides endpoints for signal performance metrics, trend analysis, and symbol-specific insights.
- **API Key Authentication**: Optional header-based API key protection for sensitive endpoints.
- **Structured JSON Logging**: Production-grade JSON logging.
- **Telegram Notifier**: Provides human-friendly signal alerts for both core signals and MSS discoveries.

### Feature Specifications
- **Comprehensive Integrations**: Leverages Coinglass v4 for market data, liquidations, and open interest; LunarCrush for social sentiment; CoinAPI for comprehensive market data and whale detection; Binance Futures for futures market data; and CoinGecko for coin discovery.
- **Output**: Signals include recommendation, composite score, confidence level, top 3 contributing factors, and raw metrics (in debug mode). MSS alerts include a 3-phase breakdown and tier classification.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async support
- **HTTP Client**: httpx for asynchronous API calls
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with asyncpg driver, using connection pooling.
- **Environment Management**: python-dotenv.
- **Lifecycle Management**: Modern `lifespan` context manager for startup/shutdown.

### Database Schema
The PostgreSQL `signals` table stores:
- **Core Fields**: symbol, signal, score, confidence, price, timestamp.
- **Metrics Storage**: JSONB fields for flexible storage of detailed metrics (reasons, comprehensive_metrics, lunarcrush_metrics, coinapi_metrics, smc_analysis, ai_validation).
- **Indexes**: Optimized indexes on symbol, timestamp, signal type, and created_at.

## External Dependencies
- **CoinAPI Startup**: Market data, OHLCV, order book depth, recent trades, real-time quotes, multi-exchange price aggregation, and whale detection.
- **Coinglass v4**: Funding rates, open interest, liquidations, long/short ratios, and top trader positioning.
- **LunarCrush**: Social sentiment, community engagement metrics, and social momentum analysis.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Public API for futures market data, coin discovery, 24hr statistics, funding rates, and open interest.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, and category-based coin search.
---

## Recent Updates

### **November 12, 2025 - LunarCrush Builder Tier Optimization** 🚀

**API Utilization Maximized: 25% → ~50%+**

Optimized LunarCrush integration for Builder subscription ($240/month), removing Enterprise-only features and adding real-time discovery capabilities.

**Key Improvements:**
- ✅ **Real-Time Coin Discovery (v2)** - NO CACHE! Instant data vs 1-hour delay in v1
- ✅ **Better MSS Scanning** - Detect gems immediately, not 1 hour later
- ✅ **Cleaned Service Layer** - Removed unavailable endpoints (Topics, Categories, Creators, AI)
- ✅ **Simplified Routes** - 5 focused endpoints matching Builder tier capabilities
- ✅ **Validated Implementation** - All endpoints tested & working
- ✅ **Clear Documentation** - Builder vs Enterprise tier differences explained

**Available Endpoints (Builder Tier):**
1. `GET /narratives/discover/realtime` - Real-time coin list (v2 - instant data!)
2. `GET /narratives/coin/{symbol}` - Complete coin data (60+ metrics)
3. `GET /narratives/momentum/{symbol}` - Advanced social momentum analysis
4. `GET /narratives/timeseries/{symbol}` - Historical trends & patterns
5. `GET /narratives/change/{symbol}` - Social spike detection & alerts

**NOT Available (Enterprise Only):**
- Topics/Narratives API
- Categories/Sectors API
- Creators/Influencers API
- AI Insights API

**Technical Implementation:**
- `app/services/lunarcrush_comprehensive_service.py` - Cleaned up to 600 lines (from 900+)
- `app/api/routes_narratives.py` - 5 focused endpoints with comprehensive docs
- Real-time discovery uses `/coins/list/v2` (instant) vs `/coins/list/v1` (cached)
- Limit validation fixed: accepts 1-200 coins (was 10-200)
- Documentation updated: "estimated" utilization instead of claiming measured metrics

**Impact:**
- MSS scanning faster with real-time data
- API utilization increased from ~25% to ~50%+
- Code cleaner & more maintainable
- Clear Builder tier boundaries

---

### **November 11, 2025 - Git Sync & Production Deployment**

**Git Sync Completed:**
- ✅ Merged GitHub updates while preserving local improvements
- ✅ Maintained 15-endpoint GPT Actions schema (routes_gpt.py: 653 lines)
- ✅ All features intact: MSS, Smart Money, New Listings, Signals
- ✅ Production server verified and operational
- ✅ GitHub repository now in sync with latest codebase

**Binance New Listings Status:**
- ⚠️ **Binance API Blocked (HTTP 451)** - Replit server IP restricted by Binance
- ✅ Code ready, but API unavailable from production server
- ❌ Removed demo data fallback per user request (real trading only)
- 💡 Alternative: Use MSS /scan endpoint for new coin discovery across all exchanges

---

## Binance New Listings Monitor (November 11, 2025) ⚠️

### Early Detection for Fresh Perpetual Listings

**Implementation Status: 🔴 API Blocked**

Binance Futures API returns HTTP 451 (region restriction) from Replit production servers. Endpoint returns clear error instead of fake data.

**Note:** For real new coin discovery, use `/mss/scan` endpoint which works with CoinGecko + multiple exchanges.

### Core Components

**1. Binance Listings Monitor Service**
- ✅ `app/services/binance_listings_monitor.py` - Detects new perpetual listings
- ✅ Tracks onboard dates from Binance exchangeInfo API
- ✅ Calculates listing age in hours
- ✅ Enriches with 24h trading stats (volume, price change, trade count)
- ✅ Extracts `baseAsset` for MSS integration

**2. API Endpoints**
- ✅ `GET /new-listings/binance` - Get new Binance perpetual listings with stats
- ✅ `GET /new-listings/analyze` - Auto-analyze new listings with MSS + Telegram alerts
- ✅ `GET /new-listings/watch` - Filtered watch list (high MSS scores only)

**3. Key Features**
- ✅ **Smart Base Asset Handling**: Extracts base asset (e.g., "ZK") from pair (e.g., "ZKUSDT") for MSS analysis
- ✅ **Graceful Degradation**: Handles missing stats data without crashes
- ✅ **MSS Integration**: Auto-runs 3-phase MSS analysis on new listings
- ✅ **Telegram Alerts**: Sends alerts for high-scoring new listings (MSS ≥65)
- ✅ **Production Error Handling**: Robust logging for debugging

**4. Use Cases**
- Early entry on Binance new listings (like ZRX, ZROU, ZRC, ZORA)
- Automated monitoring for high-potential new coins
- Pre-retail discovery for alpha generation

**GPT Actions Use Cases:**
- "What new coins were listed on Binance today?"
- "Analyze new Binance listings with MSS"
- "Show me the watch list for new high-scoring listings"

---

## MSS Alpha System - Multi-Modal Signal Score (November 10, 2025) 🚀

### Major Feature: High-Potential Cryptocurrency Discovery

Implemented 3-phase analytical framework for discovering high-potential cryptocurrencies before retail adoption.

**Core Philosophy:**
Unlike traditional signals that analyze established coins, MSS focuses on **emerging assets** through phased filtering:
1. **Phase 1: Discovery (0-30pts)** - Tokenomics filtering (FDV, age, supply)
2. **Phase 2: Social Confirmation (0-35pts)** - Community momentum validation
3. **Phase 3: Institutional Validation (0-35pts)** - Whale/smart money positioning

**Implementation Status: 🟢 Production Ready (All Systems Operational)**

### Core Components

**1. MSS Engine & Service**
- ✅ `app/core/mss_engine.py` - 3-phase weighted scoring algorithm
- ✅ `app/services/mss_service.py` - Service orchestrator
- ✅ `app/api/routes_mss.py` - REST endpoints

**2. API Endpoints**
- ✅ `GET /mss/info` - System information
- ✅ `GET /mss/discover` - Coin discovery by FDV/age filters
- ✅ `GET /mss/analyze/{symbol}` - Full 3-phase MSS analysis
- ✅ `GET /mss/scan` - Auto-scan for high-potential opportunities
- ✅ `GET /mss/history` - Latest MSS signals (paginated)
- ✅ `GET /mss/history/{symbol}` - Symbol-specific signal history
- ✅ `GET /mss/top-scores` - Highest-scoring discoveries
- ✅ `GET /mss/analytics` - Analytics summary
- ✅ `GET /mss/telegram/test` - Test Telegram notifications

### Telegram Integration (Nov 10, 2025)

- ✅ **TelegramMSSNotifier** service with rich HTML formatting
- ✅ Auto-alerts for MSS scores ≥ 75 (configurable)
- ✅ 3-phase breakdown visualization with progress bars
- ✅ Tier classification (Diamond ≥80, Gold 65-79, Silver 50-64, Bronze <50)
- ✅ AI-generated insights based on phase scores
- ✅ Includes market data (price, market cap, FDV)
- ✅ Whale activity and institutional positioning indicators

### Database Storage Integration (Nov 10, 2025)

- ✅ **MSSSignalDatabaseService** (`app/storage/mss_db.py`)
- ✅ Reuses existing `signals` table with "MSS_" signal prefix
- ✅ Auto-saves high-scoring signals (MSS ≥ 75)
- ✅ Complete phase breakdown stored in JSONB fields
- ✅ MSS-specific PostgreSQL indexes:
  - `idx_signals_mss_timestamp` - Fast chronological queries
  - `idx_signals_mss_score` - Efficient score filtering
- ✅ Graceful error handling - DB failures don't block API
- ✅ Query endpoints: history, top-scores, analytics

### GPT Actions Integration (Nov 10, 2025)

- ✅ Extended OpenAPI schema with 6 MSS endpoints
- ✅ Schema available at `GET /gpt/action-schema` (version 2.0.0)
- ✅ Production-ready for OpenAI GPT Custom Actions
- ✅ Base URL: `https://guardiansofthetoken.org`
- ✅ Complete parameter documentation with examples

**GPT Actions Use Cases:**
- "Find me new crypto gems under $20M market cap"
- "Analyze PEPE for early accumulation signals"
- "Show me top Diamond tier discoveries"
- "What cryptocurrencies are whales buying?"

### External Services Integration

- ✅ **CoinGecko** - Coin discovery, market cap filtering
- ✅ **Binance Futures** - Volume, OI, funding rates
- ✅ **LunarCrush** - Social sentiment & AltRank
- ✅ **Coinglass Premium** - Top trader positioning
- ✅ **CoinAPI Comprehensive** - Whale detection via orderbook

### Documentation

- Comprehensive guide: `MSS_SYSTEM_GUIDE.md`
- All endpoints in OpenAPI schema at `/docs`
- GPT Actions schema at `/gpt/action-schema`
