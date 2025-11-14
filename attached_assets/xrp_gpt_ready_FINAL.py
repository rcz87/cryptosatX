import requests, json

BASE_URL = "https://guardiansofthetoken.org/invoke"
SYMBOL = "XRP"

def call_api(operation, **params):
    """Fungsi pemanggil endpoint"""
    payload = {"operation": operation}
    payload.update(params)
    try:
        timeout = 45 if "smart_money" in operation or "market.get" in operation else 20
        res = requests.post(BASE_URL, json=payload, timeout=timeout)
        res.raise_for_status()
        data = res.json()
        print(f"[{operation}] ✅ OK")
        return data.get("data", data)
    except Exception as e:
        print(f"[{operation}] ❌ ERROR → {str(e)[:60]}")
        return None

def main():
    print(f"\n🚀 FETCHING DATA REAL-TIME UNTUK {SYMBOL}\n{'-'*50}")

    endpoints = [
        ("coinapi.ohlcv.latest", {"symbol": SYMBOL}),
        ("market.get", {"symbol": SYMBOL}),
        ("coinapi.orderbook", {"symbol": SYMBOL}),
        ("coinglass.orderbook.whale_walls", {"symbol": SYMBOL}),
        ("coinglass.liquidation.aggregated_history", {"symbol": SYMBOL, "exchange_list": "Binance", "interval": "1h", "limit": 10}),
        ("coinglass.funding_rate.history", {"exchange": "Binance", "symbol": f"{SYMBOL}USDT", "interval": "h8", "limit": 10}),
        ("smart_money.scan", {"symbol": SYMBOL}),
        ("coinglass.long_short_ratio.position_history", {"exchange": "Binance", "symbol": f"{SYMBOL}USDT", "interval": "h1", "limit": 10}),
        ("coinglass.indicators.rsi", {"symbol": SYMBOL, "period": "14", "interval": "h4"}),
        ("coinglass.taker_buy_sell.exchange_list", {"symbol": f"{SYMBOL}USDT"}),
        ("coinglass.indicators.fear_greed", {})
    ]

    status = {}
    for op, params in endpoints:
        data = call_api(op, **params)
        status[op] = bool(data)

    print("\n✅ STATUS ENDPOINT:")
    success = sum(1 for v in status.values() if v)
    total = len(status)
    
    for k, v in status.items():
        print(f" - {k:<50}: {'🟢 OK' if v else '🔴 FAIL'}")
    
    print(f"\n{'='*60}")
    print(f"📊 SUCCESS: {success}/{total} ({int(success/total*100)}%)")
    print(f"{'='*60}")
    
    if success >= 10:
        print("\n🎉 READY FOR GPT ACTIONS!\n")

if __name__ == "__main__":
    main()
