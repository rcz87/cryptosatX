# Crypto Futures Signal API

## Overview
This project delivers a production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals. It consolidates diverse market data (price action, funding rates, open interest, social sentiment) to provide LONG/SHORT/NEUTRAL recommendations through a multi-factor weighted scoring system. The API is designed for compatibility with GPT Actions, aiming to be a robust tool for informed trading decisions. Key capabilities include an advanced Multi-Modal Signal Score (MSS) system for identifying high-potential emerging cryptocurrencies, a Binance New Listings Monitor for early detection of fresh perpetual futures listings, and an advanced Hybrid AI Signal Judge (GPT-4 + rule-based fallback) for structured validation of signals with a verdict system and comprehensive risk management. The project has significant market potential as a tool for automated and informed crypto trading.

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
- **Hybrid AI Signal Judge**: Integrates GPT-4 for signal validation with an intelligent fallback to a rule-based system if GPT-4 fails or times out. It provides a `Verdict` (CONFIRM/DOWNSIZE/SKIP/WAIT), `Risk Mode`, `Position Multiplier`, `AI Summary`, `Layer Checks` (supporting factors and risk warnings), and `Volatility Metrics` (ATR-based position sizing, Stop Loss, Take Profit, ATR value, and Trade Plan Summary).
- **AI Verdict Accuracy Tracking**: An automated system monitors price movements and calculates P&L to validate AI verdict effectiveness over time, storing results in a PostgreSQL database and offering analytics endpoints.
- **Multi-Modal Signal Score (MSS)**: A 3-phase analytical framework for discovering emerging cryptocurrencies based on tokenomics, community momentum, and institutional validation.
- **Smart Money Concept (SMC) Analyzer**: Detects institutional trading patterns across multiple timeframes.
- **Dynamic Coin Discovery**: Integrates Binance Futures and CoinGecko for dynamic cryptocurrency discovery and analysis.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for performance.
- **Comprehensive Coinglass Integration**: Over 60 production endpoints for market data, liquidations, funding rates, open interest, and technical indicators.
- **Real-Time WebSocket Streaming**: Provides a WebSocket endpoint for live liquidation data.
- **Unified RPC Endpoint with Flat Parameters**: A single POST `/invoke` endpoint provides access to all operations via an RPC interface, supporting both nested and flat parameters.
- **API Endpoints**: Includes endpoints for enhanced trading signals, aggregated raw market data, GPT Actions flat parameter endpoints, direct Coinglass and LunarCrush data access, Smart Money analysis, MSS functionality, Binance New Listings, WebSocket streaming, and OpenAI V2 Signal Judge validation.
- **Signal History Storage**: Stores LONG/SHORT signals and high-scoring MSS signals in a PostgreSQL database (Neon) with JSON file backup.
- **Telegram Notifier**: Provides human-friendly signal alerts with AI verdict information, risk mode indicators, position sizing guidance, and supporting/conflicting factor analysis.

### Feature Specifications
- **Comprehensive Integrations**: Leverages Coinglass v4, LunarCrush v4, CoinAPI, Binance Futures, and CoinGecko.
- **LunarCrush v4 Features**: Coins Discovery endpoint with Galaxy Score and AltRank filtering, Topics API for individual coin social metrics, and **Topics List** endpoint for real-time trending topics discovery (viral detection, momentum analysis, auto-discovery of 1000+ social topics with 1h/24h rank changes).
- **Output**: Signals include recommendation, composite score, confidence level, top contributing factors, and raw metrics (in debug mode). MSS alerts include a 3-phase breakdown and tier classification.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Neon) with `asyncpg` driver and connection pooling.
- **Environment Management**: python-dotenv.

## External Dependencies
- **CoinAPI Startup**: Market data, OHLCV, order book depth, recent trades, real-time quotes, multi-exchange price aggregation, and whale detection.
- **Coinglass v4 Standard**: Liquidations, funding rates, open interest, trader positioning, whale intelligence, technical analysis, macro calendar, news feed, and real-time WebSocket streaming.
- **Coinglass WebSocket**: Real-time liquidation streaming at `wss://open-ws.coinglass.com/ws-api`.
- **LunarCrush Builder**: Social sentiment, community engagement metrics, social momentum analysis, and real-time coin discovery.
- **OKX Public API**: Candlestick/OHLCV data.
- **Binance Futures API**: Public API for futures market data, coin discovery, 24hr statistics, funding rates, open interest, and new listings information.
- **CoinGecko API**: Coin discovery, market cap filtering, volume analysis, and category-based coin search.
- **Neon (PostgreSQL)**: Managed PostgreSQL database for signal history storage.

## Production Status & Future Improvements

### Current Production Readiness
**Overall Score: 6.5/10** (Conditional Production Ready)

**Category Breakdown:**
- Security: 6/10 - CORS policy needs restriction, eval() usage needs replacement
- Reliability: 7/10 - Good error handling, rate limiting needs activation
- Performance: 8/10 - Excellent async patterns and connection pooling
- Observability: 5/10 - Basic logging, needs metrics and tracing
- Maintainability: 8/10 - Clean code structure and well organized
- Scalability: 6/10 - Single worker deployment, no horizontal scaling yet

**Verdict:** System is production-ready for small-to-medium traffic. Critical security issues must be addressed before scaling to large traffic volumes.

### Critical Security Issues (High Priority)

**🔴 Must Fix Before Large-Scale Production:**

1. **CORS Policy Restriction** (`app/main.py:99-105`)
   - Current: `allow_origins=["*"]` - allows any domain
   - Risk: CSRF attacks, credential theft
   - Fix: Restrict to specific domains:
     ```python
     allow_origins=[
         "https://guardiansofthetoken.org",
         "https://www.guardiansofthetoken.org"
     ]
     ```

2. **Replace eval() Code Execution** (`app/services/alert_service.py:193`)
   - Current: `eval(rule.condition, {"__builtins__": {}}, safe_metrics)`
   - Risk: Code injection vulnerability despite sandboxing
   - Fix: Use safe expression parser (simpleeval or asteval library)

3. **Enable Rate Limiting Middleware**
   - Current: Rate limiter code exists but not activated
   - Risk: API abuse, DDoS attacks
   - Fix: Add middleware in `app/main.py`:
     ```python
     from app.middleware.rate_limiter import rate_limit_middleware
     app.add_middleware(rate_limit_middleware)
     ```

4. **HTTPS Enforcement**
   - Current: No HTTPS redirect or HSTS headers
   - Risk: Man-in-the-middle attacks, credential interception
   - Fix: Add HTTPS redirect middleware and HSTS headers

5. **Production Authentication Enforcement**
   - Current: Auto-disables authentication if env vars not set
   - Risk: Unprotected production endpoints
   - Fix: Enforce required authentication in production environment

### Medium Priority Improvements

**🟡 Recommended for Next Sprint:**

1. **Replace Print Statements with Proper Logging**
   - Issue: 183 print statements found throughout codebase
   - Impact: Inefficient production monitoring
   - Fix: Implement structured logging with Python's `logging` module

2. **Add Request Size Limits**
   - Issue: No max request size validation
   - Impact: Memory exhaustion attacks
   - Fix: Add uvicorn limits: `limit_concurrency=100, limit_max_requests=10000`

3. **Implement Secrets Manager**
   - Issue: API keys stored as plain text in environment variables
   - Impact: Key exposure if environment is compromised
   - Fix: Consider AWS Secrets Manager or HashiCorp Vault

4. **Add Circuit Breaker Pattern**
   - Issue: External API calls can hang indefinitely
   - Impact: Cascading failures
   - Fix: Implement circuit breaker with timeout strategy

5. **Standardize Error Response Format**
   - Issue: Inconsistent error handling across endpoints
   - Impact: Poor API client experience
   - Fix: Create uniform error response schema

### Low Priority Enhancements

**🟢 Nice-to-Have Improvements:**

1. **Comprehensive Input Validation**
   - Add Pydantic validators for all inputs, especially symbol validation
   - Prevent special character injection

2. **Enhanced Health Check Endpoint**
   - Add database connection checks
   - Add external API dependency health checks

3. **Remove Debug Artifacts**
   - Clean up debug print statements in production code
   - Wrap debug logs with `if DEBUG:` checks

4. **API Response Caching**
   - Implement Redis caching for frequently accessed market data
   - Reduce external API call frequency

5. **API Versioning Strategy**
   - Implement `/v1/`, `/v2/` URL prefixes
   - Enable backward compatibility for breaking changes

6. **Automated Backup Strategy**
   - Setup scheduled PostgreSQL backups
   - Note: Neon provides automated backups by default

7. **Fix .replit Configuration**
   - Issue: `--workers` parameter incomplete in run command
   - Fix: Set proper worker count or remove parameter

### Infrastructure Recommendations

**For Future Scaling:**

1. **Migration Considerations**
   - Consider dedicated VPS/cloud (AWS/GCP/DigitalOcean) for better control
   - Setup CDN (CloudFlare) for DDoS protection and caching
   - Implement load balancer when traffic increases
   - Setup staging environment mirroring production

2. **Monitoring & Observability**
   - Setup Grafana + Prometheus for metrics collection
   - Setup Sentry for error tracking and alerting
   - Setup uptime monitoring (UptimeRobot, Pingdom)
   - Implement log aggregation (ELK stack or Datadog)
   - Add distributed tracing (OpenTelemetry)

3. **Security Hardening**
   - Schedule regular security audits
   - Implement dependency scanning (Snyk, Dependabot)
   - Establish API key rotation policy
   - Setup WAF (Web Application Firewall)
   - Implement per-API-key rate limiting

### Development Priorities

**Immediate Action Items (Before Traffic Scaling):**
1. Fix CORS policy - restrict to specific origins
2. Replace eval() with safe parser
3. Enable rate limiting middleware
4. Add HTTPS redirect & HSTS headers
5. Enforce production authentication

**Next Sprint (Q1 Improvements):**
1. Replace print statements with proper logging
2. Add request size limits
3. Implement Prometheus metrics
4. Setup error tracking (Sentry)
5. Add comprehensive input validation

**Future Enhancements (Q2-Q3):**
1. API response caching with Redis
2. API versioning implementation
3. Circuit breaker pattern
4. Secrets manager integration
5. Distributed tracing setup

### Strengths to Maintain

**Keep These Best Practices:**
- ✅ Clean modular architecture with separation of concerns
- ✅ Consistent async/await patterns for optimal performance
- ✅ Comprehensive type hints and Pydantic validation
- ✅ Well-documented API with OpenAPI/Swagger
- ✅ Database connection pooling and proper indexing
- ✅ Graceful error handling in critical paths
- ✅ Environment-based configuration management