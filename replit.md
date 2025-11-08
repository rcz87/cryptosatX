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
- **CoinAPI**: Used for real-time spot prices of cryptocurrencies.
- **Coinglass v4**: Integrated for funding rates, open interest data, liquidations, long/short ratios, and top trader positioning. Utilizes both base and premium endpoints.
- **LunarCrush**: Provides social sentiment, community engagement metrics, and advanced social momentum analysis.
- **OKX Public API**: Utilized for candlestick/OHLCV data, requiring no API key for public endpoints.