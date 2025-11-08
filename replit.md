# Crypto Futures Signal API

## Overview
This project is a production-ready FastAPI backend designed to generate real-time cryptocurrency futures trading signals. It aggregates data from multiple sources (CoinAPI, Coinglass v4, LunarCrush, OKX) to provide comprehensive signals based on price action, funding rates, open interest, and social sentiment. The API aims to offer LONG/SHORT/NEUTRAL recommendations, utilizing a multi-factor weighted scoring system, and is compatible with GPT Actions for OpenAI integration. The business vision is to provide a robust tool for informed trading decisions with market potential in automated trading and signal provision services.

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability

## System Architecture
The application is built with FastAPI and features a modular architecture separating API routes, core business logic, and external service integrations.

### UI/UX Decisions
The API design focuses on programmatic access, providing clean JSON responses. Debug mode (`?debug=true`) is available for detailed metrics, aiding in development and troubleshooting. OpenAPI documentation is exposed via `/docs` for interactive exploration and `/redoc` for static documentation. A GPT Actions-compatible OpenAPI schema is provided for seamless integration with AI agents.

### Technical Implementations
- **Signal Engine**: Employs an 8-factor weighted scoring system (0-100 scale) for signal generation. Factors include Liquidations, Funding Rate, Price Momentum, Long/Short Ratio, Smart Money, OI Trend, Social Sentiment, and Fear & Greed. Configurable thresholds (≥65 LONG, ≤35 SHORT, 35-65 NEUTRAL) determine the final signal.
- **Concurrent Data Fetching**: Utilizes `asyncio.gather` for optimal performance when fetching data from multiple external APIs.
- **Error Handling**: Implements robust error handling with safe defaults for all API integrations.
- **API Endpoints**:
    - `GET /signals/{symbol}`: Provides the enhanced trading signal.
    - `GET /market/{symbol}`: Aggregates raw market data from all providers.
    - `GET /gpt/action-schema`: Exposes the OpenAPI schema for GPT Actions.
    - Dedicated endpoints for direct access to Coinglass and LunarCrush data, maximizing subscription utilization.

### Feature Specifications
- **Comprehensive LunarCrush Integration**: Incorporates 4 advanced LunarCrush endpoints (`Comprehensive Coin Metrics`, `Time-Series Analysis`, `Change Detection`, `Social Momentum`) for in-depth social sentiment analysis, trend detection, and spike identification.
- **Maximized Coinglass Integration**: Leverages comprehensive Coinglass v4 endpoints for market data, multi-timeframe liquidations, and an all-in-one dashboard.
- **Output**: Signals include recommendation (LONG/SHORT/NEUTRAL), composite score, confidence level, top 3 contributing factors, and raw metrics in debug mode.

### System Design Choices
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async support
- **HTTP Client**: httpx for asynchronous API calls
- **Validation**: Pydantic v2 for data validation
- **Environment Management**: python-dotenv for configuration

## External Dependencies
- **CoinAPI Startup ($78/mo)**: Maximized with comprehensive market data integration including multi-timeframe OHLCV candlestick data, order book depth analysis, recent trades volume tracking, real-time bid/ask quotes, and multi-exchange price aggregation. Provides market depth metrics, buy/sell pressure analysis, whale walls detection, and volatility measurements for enhanced signal accuracy.
- **Coinglass v4**: Integrated for funding rates, open interest data, liquidations, long/short ratios, and top trader positioning. Utilizes both base and premium endpoints.
- **LunarCrush**: Provides social sentiment, community engagement metrics, and advanced social momentum analysis.
- **OKX Public API**: Utilized for candlestick/OHLCV data, requiring no API key for public endpoints.

## Recent Changes

### Nov 8, 2025 - CoinAPI Startup Plan Maximization 🚀
**ENHANCEMENT**: Maximized CoinAPI Startup subscription ($78/month) with comprehensive market data integration

✅ **Successfully Implemented:**
- Created `coinapi_comprehensive_service.py` with 6 advanced endpoints
- Integrated comprehensive market data into **Enhanced Signal Engine**
- Added `/coinapi/*` routes for direct API access (7 endpoints total)
- Implemented order book depth analysis, trade volume tracking, and volatility metrics
- All endpoints use async/await with connection pooling for optimal performance

**Working CoinAPI Endpoints:**
- ✅ **OHLCV Latest** (`/coinapi/ohlcv/{symbol}/latest`):
  - Real-time candlestick data with configurable periods (1MIN, 5MIN, 1HRS, 1DAY)
  - Returns OHLC prices, volume, and trade counts
  - Use case: Multi-timeframe price analysis, support/resistance detection
  
- ✅ **OHLCV Historical** (`/coinapi/ohlcv/{symbol}/historical`):
  - Historical candlestick data with trend analysis
  - Calculates price change %, volatility metrics, average volume
  - Returns time-series arrays for charting
  
- ✅ **Recent Trades** (`/coinapi/trades/{symbol}`):
  - Last 100 trades with buy/sell side detection
  - Calculates buy pressure % vs sell pressure %
  - Volume analysis and average trade size
  - Use case: Volume spike detection, market momentum
  
- ✅ **Current Quote** (`/coinapi/quote/{symbol}`):
  - Real-time bid/ask prices and sizes
  - Spread calculation (amount and percentage)
  - Use case: Liquidity assessment, entry/exit timing
  
- ⚠️ **Order Book Depth** (`/coinapi/orderbook/{symbol}`):
  - Order book imbalance (-100 to +100)
  - Whale walls detection (orders >5x average)
  - Market depth analysis
  - Note: Endpoint works standalone but may have API limits
  
- ✅ **Multi-Exchange Prices** (`/coinapi/multi-exchange/{symbol}`):
  - Compare prices across BINANCE, COINBASE, KRAKEN
  - Detects arbitrage opportunities (>0.5% variance)
  - Returns average price and variance metrics
  
- ✅ **Dashboard** (`/coinapi/dashboard/{symbol}`):
  - All-in-one endpoint combining OHLCV, trades, quotes
  - Perfect for building trading UIs

**Signal Engine Integration:**
- Signal endpoint now includes comprehensive CoinAPI section
- New `coinAPIMetrics` in `/signals/{symbol}` response:
  - Order book imbalance and spread analysis
  - Buy/sell pressure from recent trades (e.g., 26.73% buy vs 73.27% sell)
  - 7-day volatility percentage
- Flexible fallback system - works even if some endpoints fail

**Value Delivered:**
- **Market Depth Analysis** - Order book metrics and whale walls
- **Buy/Sell Pressure** - Real-time trade flow analysis
- **Volatility Tracking** - 7-day historical volatility
- **Multi-Exchange Validation** - Cross-exchange price comparison
- **Production-Ready** - Graceful error handling and concurrent data fetching

**API Maximization Summary:**
All three premium subscriptions now fully utilized:
- 💰 **Coinglass Standard** ($300/mo) - Market data, liquidations, funding rates
- 💰 **LunarCrush Standard** - Social sentiment, momentum, spike detection  
- 💰 **CoinAPI Startup** ($78/mo) - OHLCV, order book, trades, quotes, multi-exchange