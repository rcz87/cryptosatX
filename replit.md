# Crypto Futures Signal API

## Overview
This project is a FastAPI-based backend for generating real-time cryptocurrency futures trading signals (LONG/SHORT/NEUTRAL). It leverages a multi-factor weighted scoring system, a Multi-Modal Signal Score (MSS) for emerging cryptocurrencies, a Binance New Listings Monitor, and a Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for signal validation. The API is designed to be a robust tool for informed and automated crypto trading decisions, with a focus on GPT Actions integration and significant market potential.

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
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes with dynamic coin discovery (auto-fetches top coins by volume from CoinGecko). Features intelligent caching and rate limit safety.
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
- **Enterprise-Grade Resilience & Rate Limit Protection**: Features a Circuit Breaker Pattern for LunarCrush API, Retry Logic with Exponential Backoff for CoinGecko, and Graceful Degradation (signal generation continues with 70%+ data quality even if optional services fail).

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
---

## ✨ Latest Features (November 19, 2025)

### 🎯 **Duration-Based Auto-Stop Monitoring**
- **Feature:** Flexible duration monitoring with auto-expiration
- **Usage:** Monitor any coin for custom duration (1-1440 minutes)
- **Auto-Stop:** System automatically removes coin after duration expires
- **API:** `POST /comprehensive-monitoring/watchlist/add` with `duration_minutes` parameter
- **Example:** "Monitor BTC for 5 minutes" → auto-stops after 5 min
- **Benefits:**
  - No manual stop required
  - Perfect for quick analysis sessions
  - Prevents forgotten monitoring tasks
  - GPT Actions compatible via RPC

**Implementation Details:**
- Database: Added `duration_minutes` + `started_at` columns to `coin_watchlist`
- Monitoring Loop: Checks expiration every 60 seconds
- RPC Support: `duration_minutes`, `priority`, `check_interval_seconds` parameters available
- Flexible: Set `duration_minutes=null` for continuous monitoring

---

## 🚀 Production Deployment Status (November 19, 2025)

### ✅ PRO Features - 100% OPERATIONAL

**1. Smart Entry Engine** (4 Production Routes)
- `GET /smart-entry/analyze/{symbol}` - 8-source confluence analysis with entry zones, SL/TP, R:R ratio
- `POST /smart-entry/analyze-batch` - Batch analysis for multiple symbols (max 20)
- `GET /smart-entry/test/{symbol}` - Telegram alert preview and testing
- `GET /smart-entry/health` - System health check with live BTC test

**2. Comprehensive Monitoring System** (13 Production Routes)
- Watchlist Management: add, remove, list, bulk operations
- Monitoring Control: start, stop, status checks
- Rule Management: create, update, delete custom rules
- Alert System: retrieve, acknowledge alerts
- Statistics: real-time monitoring stats

### ✅ All Bug Fixes Deployed & Verified

**Bug #1 - Smart Entry Price Method**
- Fixed missing `get_current_price()` method in CoinAPI service
- Status: Deployed & Tested ✅

**Bug #2 - Database API Compatibility**
- Updated 13 database calls in routes_comprehensive_monitoring.py to proper asyncpg pattern
- Status: Deployed & Tested ✅

**Bug #3 - Database Schema**
- Created 3 PostgreSQL tables: coin_watchlist, monitoring_rules, monitoring_alerts
- Status: Deployed & Tested ✅

**Bug #4 - JSONB Type Conversion**
- Fixed metrics_enabled dict to JSON string conversion with json.dumps()
- Status: Deployed & Tested ✅

**Bug #5 - Duration-Based Monitoring RuntimeError**
- Fixed dict modification during iteration with `list(self.watchlist.items())`
- Status: Deployed & Tested ✅

**Bug #6 - Expired Coins Resurrection**
- Added expiration filter in `_load_watchlist()` to prevent resurrection on restart
- Status: Deployed & Tested ✅

**Bug #7 - API JSON Serialization**
- Fixed `/watchlist` endpoints to parse metrics_enabled JSON to dict
- Status: Deployed & Tested ✅

**Bug #8 - Missing Import**
- Added `import json` to routes_comprehensive_monitoring.py
- Status: Deployed & Tested ✅

### 📊 Production Verification Results (Nov 19, 2025)

```bash
# Smart Entry Engine (https://guardiansofthetoken.org)
✅ Health Check: status=healthy (BTC confluence 11%)
✅ BTCUSDT Analysis: Direction=SHORT, Confluence=11/100, Entry zones calculated
✅ SOLUSDT Analysis: Direction=SHORT, Confluence=11/100, R:R=0.71, Position=1.6%
✅ Batch Analysis: 3 symbols analyzed (BTCUSDT, ETHUSDT, SOLUSDT)
✅ Test Endpoint: Telegram preview generated successfully

# Comprehensive Monitoring System
✅ Watchlist: 3 coins tracked (ETHUSDT, SOLUSDT, BTCUSDT)
✅ Statistics: 3 total coins, 3 active
✅ All CRUD operations: add, remove, list, bulk - fully functional
```

### 🌐 Final Deployment Status
- **Production URL**: https://guardiansofthetoken.org
- **Deployment Type**: Replit VM (stateful, always-on for continuous monitoring)
- **Total Routes**: 17 production endpoints (4 Smart Entry + 13 Comprehensive Monitoring)
- **Total RPC Operations**: 196+ operations via `/invoke` endpoint
- **Database**: PostgreSQL (Neon) with asyncpg, 3 monitoring tables
- **Latest Features**: Duration-based auto-stop monitoring (Nov 19, 2025)
- **Status**: 🟢 **FULLY OPERATIONAL - Production Ready for Republish**

### 🔧 Deployment Configuration
- **Target**: VM deployment (`.replit` configured)
- **Port Mapping**: 8000 → 80 (external access)
- **Auto-restart**: Enabled via Replit workflows
- **Database**: Neon PostgreSQL (production), SQLite (fallback)
- **Monitoring**: Comprehensive watchlist system with auto-expiration
- **Files Excluded**: Test files, logs, temporary data (via `.gitignore`)

### 🎯 RPC Integration Status (November 19, 2025)
All 17 routes terbaru sudah terintegrasi penuh dengan RPC system:
- ✅ **Smart Entry Engine** - 4 operations (`smart_entry.analyze`, `smart_entry.analyze_batch`, `smart_entry.test`, `smart_entry.health`)
- ✅ **Comprehensive Monitoring** - 14 operations (watchlist, rules, alerts, spike monitoring)

**Smart Entry RPC Operations:**
1. `smart_entry.analyze` - Analyze single symbol with confluence scoring
   - Parameters: `symbol`, `timeframe` (default: "1h"), `send_telegram` (default: false)
   - Timeout: 45s
   - Returns: Full analysis with entry zones, SL/TP, R:R ratio, position sizing

2. `smart_entry.analyze_batch` - Batch analyze multiple symbols (max 20)
   - Parameters: `symbols` (array), `timeframe`, `min_confluence` (default: 60), `send_telegram`
   - Timeout: 60s
   - Returns: Sorted opportunities by confluence score

3. `smart_entry.test` - Get Telegram alert preview
   - Parameters: `symbol`
   - Timeout: 30s
   - Returns: Full and compact Telegram message previews

4. `smart_entry.health` - Health check for Smart Entry Engine
   - Parameters: none
   - Timeout: 30s
   - Returns: System status with BTC test analysis

**Example RPC Call:**
```json
POST /invoke
{
  "operation": "smart_entry.analyze",
  "symbol": "BTCUSDT",
  "timeframe": "1h"
}
```

### 🔍 Post-Deployment Investigation (Nov 19, 2025)
Initial reports of Smart Entry returning `None` values were investigated and found to be **false alarm**:
- **Root Cause**: Test script using incorrect API field names
- **Actual Status**: Smart Entry Engine was working perfectly since first deployment
- **Resolution**: No code changes required - all features operational as designed

