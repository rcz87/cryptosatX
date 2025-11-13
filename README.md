# CryptoSatX - AI-Powered Crypto Futures Signal API

Production-ready FastAPI backend for generating real-time cryptocurrency futures trading signals with AI-powered verdict validation and advanced risk management.

## 🚀 Features

### Core Signal Engine
- **8-Factor Weighted Scoring System** (0-100 scale)
  - Liquidations, Funding Rate, Price Momentum
  - Long/Short Ratio, Smart Money, OI Trend
  - Social Sentiment, Fear & Greed Index

### AI Verdict Layer (GPT-4 Powered)
- **CONFIRM/DOWNSIZE/SKIP/WAIT** verdict system
- Risk-based position sizing (0x-1.5x multipliers)
- Telegram-ready AI summaries
- Intelligent fallback to rule-based analysis

### Phase 2 Enhancements (NEW)
- **AI Verdict Accuracy Tracking**
  - Automated price monitoring (1h/4h/24h intervals)
  - Win rate calculations per verdict type
  - P&L tracking with outcome classification
  - Performance analytics endpoints

- **Volatility-Adjusted Position Sizing**
  - ATR-based volatility measurement
  - Dynamic position sizing (0.25x-2.0x multipliers)
  - ATR-based stop loss calculations
  - Risk-reward optimized take profit levels

### Additional Capabilities
- **Smart Money Concepts (SMC)**: Institutional pattern detection
- **Multi-Modal Signal Score (MSS)**: Emerging cryptocurrency discovery
- **Real-Time WebSocket Streaming**: Live liquidation data
- **Unified RPC Endpoint**: 172+ operations via single POST endpoint
- **PostgreSQL Database**: Signal history & outcome tracking
- **Telegram Notifications**: Real-time alerts with risk indicators

## 📊 API Endpoints

### Signal Generation
- `GET /signals/{symbol}` - Generate trading signal with AI verdict
- `GET /market/{symbol}` - Raw market data aggregation
- `POST /gpt/signal` - GPT Actions compatible endpoint
- `POST /invoke` - Unified RPC interface (all operations)

### Analytics (Phase 2)
- `GET /analytics/verdict-performance` - Win rates per verdict type
- `GET /analytics/verdict-compare` - Compare verdict effectiveness
- `GET /analytics/outcomes-history` - Historical outcome data
- `GET /analytics/tracking-stats` - System tracking statistics

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative documentation (ReDoc)

## 🔧 Tech Stack

- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async/await
- **Database**: PostgreSQL (Neon) with connection pooling
- **AI**: OpenAI GPT-4 for signal validation
- **HTTP Client**: httpx for concurrent requests
- **Validation**: Pydantic v2

## 🔌 External Integrations

- **CoinAPI**: Market data, OHLCV, order book depth
- **Coinglass v4**: Liquidations, funding rates, open interest
- **LunarCrush v4**: Social sentiment, community metrics
- **OpenAI GPT-4**: AI-powered signal validation
- **Binance Futures**: Futures market data, new listings
- **CoinGecko**: Coin discovery, market cap filtering
- **OKX**: Candlestick/OHLCV data

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/rcz87/cryptosatX.git
cd cryptosatX

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
python main.py
```

## 🔐 Environment Variables

Required API keys:
- `COINAPI_KEY` - CoinAPI subscription
- `COINGLASS_API_KEY` - Coinglass v4 access
- `LUNARCRUSH_API_KEY` - LunarCrush Builder plan
- `OPENAI_API_KEY` - OpenAI GPT-4 access
- `DATABASE_URL` - PostgreSQL connection string

Optional:
- `TELEGRAM_BOT_TOKEN` - For alert notifications
- `TELEGRAM_CHAT_ID` - Target chat for alerts

## 🚀 Deployment

Deployed on Replit with Reserved VM:
- Production URL: `https://guardiansofthetoken.org`
- Auto-scaling: No (Reserved VM for consistent performance)
- Database: Managed PostgreSQL (Neon)

## 📈 Usage Example

```python
import requests

# Get signal for BTC
response = requests.get("https://guardiansofthetoken.org/signals/BTC")
data = response.json()

print(f"Signal: {data['signal']}")  # LONG/SHORT/NEUTRAL
print(f"AI Verdict: {data['aiVerdictLayer']['verdict']}")  # CONFIRM/SKIP/etc
print(f"Risk Mode: {data['aiVerdictLayer']['riskMode']}")  # NORMAL/AVOID/etc

# Volatility metrics (Phase 2)
vol = data['aiVerdictLayer']['volatilityMetrics']
print(f"Position Size: {vol['recommendedPositionMultiplier']}x")
print(f"Stop Loss: ${vol['stopLossPrice']}")
print(f"Take Profit: ${vol['takeProfitPrice']}")
```

## 🎯 GPT Actions Integration

Compatible with GPT Actions schema. Use the unified RPC endpoint for all operations:

```json
POST /invoke
{
  "operation": "get_signal",
  "symbol": "BTC"
}
```

Supports 172+ operations via single endpoint, bypassing GPT Actions' 30-operation limit.

## 📊 Performance Tracking

Monitor AI verdict accuracy after deployment:
- Win rates by verdict type (CONFIRM vs SKIP vs DOWNSIZE)
- Average P&L per verdict category
- Signal outcome classification (WIN/LOSS/NEUTRAL)
- 1h, 4h, and 24h price tracking

## 🤝 Contributing

This is a production system. For issues or feature requests, please contact the maintainer.

## 📄 License

Proprietary - All rights reserved

## 📧 Contact

Project maintained by rcz87
- GitHub: https://github.com/rcz87/cryptosatX
- Production: https://guardiansofthetoken.org

---

**Last Updated**: November 2025 (Phase 2 - AI Verdict Accuracy Tracking & Volatility Sizing)
