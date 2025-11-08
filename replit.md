# Crypto Futures Signal API

## Overview
Production-ready FastAPI backend for crypto futures trading signals. This API integrates data from multiple sources (CoinAPI, Coinglass v4, LunarCrush, OKX) to generate comprehensive trading signals combining price action, funding rates, open interest, and social sentiment.

## Purpose
- Provide real-time trading signals for cryptocurrency futures markets
- Aggregate data from multiple reliable crypto data providers
- Generate LONG/SHORT/NEUTRAL recommendations based on multi-factor analysis
- Expose GPT Actions-compatible OpenAPI schema for OpenAI integration

## Current State
✅ Fully implemented and ready to run
✅ Modular architecture with clean separation of concerns
✅ Error handling with safe defaults for all API integrations
✅ OpenAPI documentation available at /docs
✅ GPT Actions schema endpoint for seamless OpenAI integration

## Project Architecture

### Directory Structure
```
/app
  /api            - API route handlers
    routes_health.py      - Health check endpoints
    routes_signals.py     - Signal and market data endpoints
    routes_gpt.py         - GPT Actions schema endpoint
  /core           - Core business logic
    signal_engine.py      - Signal generation engine
  /services       - External API integrations
    coinapi_service.py    - CoinAPI integration (spot prices)
    coinglass_service.py  - Coinglass v4 (funding rate & OI)
    lunarcrush_service.py - LunarCrush (social sentiment)
    okx_service.py        - OKX public API (candlestick data)
  main.py         - FastAPI application entry point
```

### Data Sources
1. **CoinAPI** - Real-time spot prices for cryptocurrencies
2. **Coinglass v4** - Funding rates and open interest data
3. **LunarCrush** - Social sentiment and community engagement metrics
4. **OKX Public API** - Candlestick/OHLCV data (no auth required)

### Signal Generation Logic
The Signal Engine combines multiple factors:
- **Funding Rate**: Indicates market sentiment (positive = longs paying shorts)
- **Open Interest**: Shows total market exposure
- **Social Sentiment**: Community engagement and buzz (0-100 scale)
- **Price Trend**: Recent price action from candlestick analysis

**Signal Output**: LONG, SHORT, or NEUTRAL with detailed reasoning

## Recent Changes
- **Nov 8, 2025**: Initial project creation
  - Implemented all 4 data provider services
  - Created signal engine with multi-factor analysis
  - Set up FastAPI with CORS and route organization
  - Added GPT Actions OpenAPI schema endpoint
  - Configured environment variable management

## API Endpoints

### Core Endpoints
- `GET /` - API information and endpoint list
- `GET /health` - Health check
- `GET /signals/{symbol}` - Get trading signal for a crypto (e.g., /signals/BTC)
- `GET /market/{symbol}` - Get raw market data from all providers
- `GET /gpt/action-schema` - OpenAPI schema for GPT Actions integration

### Documentation
- `/docs` - Interactive Swagger UI documentation
- `/redoc` - ReDoc documentation

## Environment Variables Required

Create a `.env` file based on `.env.example`:

```bash
# Required API Keys
COINAPI_KEY=your_coinapi_key_here
COINGLASS_API_KEY=your_coinglass_api_key_here
LUNARCRUSH_API_KEY=your_lunarcrush_api_key_here

# Optional Configuration
BASE_URL=https://your-replit-url.repl.co
PORT=8000
```

### Getting API Keys
1. **CoinAPI**: https://www.coinapi.io/ - Sign up for free tier
2. **Coinglass**: https://www.coinglass.com/api - Request API access
3. **LunarCrush**: https://lunarcrush.com/developers/api - Create account
4. **OKX**: No API key needed (using public endpoints)

## Running the Application

The application runs automatically via the configured workflow on port 8000.

Manual run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage Examples

### Get Trading Signal
```bash
curl https://your-app-url.repl.co/signals/BTC
```

Response:
```json
{
  "symbol": "BTC",
  "timestamp": "2025-11-08T10:30:00",
  "price": 45000.00,
  "fundingRate": 0.0001,
  "openInterest": 1500000000,
  "socialScore": 75.5,
  "signal": "LONG",
  "reason": "Positive funding rate | High social sentiment (76/100) | Bullish price action | OI: $1,500,000,000"
}
```

### GPT Actions Integration
1. Get the schema: `GET /gpt/action-schema`
2. In OpenAI GPT Builder, add this API as an Action
3. Use the returned OpenAPI schema to configure the action
4. GPT can now call your API to get trading signals

## Future Enhancements
- Smart Money Concepts (SMC) integration for advanced signal logic
- Rate limiting and caching to reduce API calls
- WebSocket support for real-time signal updates
- Database persistence for historical signal tracking
- Multi-timeframe analysis and correlation
- Backtesting capabilities
- Alert/notification system

## Tech Stack
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async support
- **HTTP Client**: httpx for async API calls
- **Validation**: Pydantic v2
- **Environment**: python-dotenv for config management

## User Preferences
- Clean, modular code structure
- Comprehensive error handling with safe defaults
- Production-ready code (no mock data)
- Full async/await for performance
- Extensive comments for maintainability
