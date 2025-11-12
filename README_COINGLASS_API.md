# Coinglass v4 API Integration

## Quick Reference

### Base URL
```
https://open-api-v4.coinglass.com
```

### Authentication
```bash
Header: CG-API-KEY: your_api_key_here
```

### Verified Working Endpoints (4/5 = 80%)

1. **Liquidation Data** ✅
   - Endpoint: `/api/futures/liquidation/coin-list`
   - Params: `exchange=Binance`
   - Returns: 24h liquidation volumes (longs vs shorts)

2. **Long/Short Ratio** ✅
   - Endpoint: `/api/futures/global-long-short-account-ratio/history`
   - Params: `exchange=Binance, symbol=BTCUSDT, interval=h1, limit=1`
   - Returns: Global account sentiment

3. **Open Interest Trend** ❌ → ✅ OKX Fallback
   - Primary: `/api/futures/open-interest/ohlc-aggregated-history` (404)
   - Fallback: OKX Public API `/api/v5/rubik/stat/contracts/open-interest-history`
   - Returns: OI trend analysis

4. **Top Trader Positioning** ✅
   - Endpoint: `/api/futures/top-long-short-position-ratio/history`
   - Params: `exchange=Binance, symbol=BTCUSDT, interval=h1, limit=1`
   - Returns: Smart money bias

5. **Fear & Greed Index** ✅
   - Endpoint: `/api/index/fear-greed-history`
   - Params: None
   - Returns: Market sentiment (0-100)

## Testing

Run comprehensive API test:
```bash
python3 tests/test_coinglass_v4_production.py
```

Expected output:
```
✅ Working: 4 (80%)
❌ Failed: 1 (20%)
Overall Status: EXCELLENT
```

## Implementation Files

- `app/services/coinglass_premium_service.py` - Main service
- `app/services/okx_service.py` - Fallback provider
- `app/core/signal_engine.py` - Integration point

## Response Format

All endpoints return:
```json
{
  "code": 0,
  "msg": "success",
  "data": [...]
}
```

Success code is integer `0`, not string `"0"`

## Rate Limits

- Standard Plan: 60 requests/minute
- Current usage: ~10-15 req/min
- Buffer: 75% available

## Fallback Strategy

```
Coinglass v4 → OKX Public → Safe defaults
```

All endpoints have graceful degradation.

## Documentation

See `COINGLASS_VERIFICATION_REPORT.md` for comprehensive details.
