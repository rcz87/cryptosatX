import requests, json, time

BASE_URL = "https://guardiansofthetoken.org/invoke"
SYMBOL = "XRP"

def call_api(operation, **params):
    """Fungsi pemanggil endpoint"""
    payload = {"operation": operation}
    payload.update(params)
    try:
        res = requests.post(BASE_URL, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        print(f"[{operation}] ✅ OK")
        return data.get("data", data)
    except Exception as e:
        print(f"[{operation}] ❌ ERROR → {e}")
        return None


def main():
    print(f"\n🚀 FETCHING DATA REAL-TIME UNTUK {SYMBOL}\n{'-'*50}")

    # 1️⃣ PRICE & MOMENTUM
    price_data = call_api("coinapi.ohlcv.latest", symbol=SYMBOL)
    market_data = call_api("market.get", symbol=SYMBOL)

    # 2️⃣ ORDERBOOK PRESSURE
    orderbook = call_api("coinapi.orderbook", symbol=SYMBOL)
    whale_walls = call_api("coinglass.orderbook.whale_walls", symbol=SYMBOL)

    # 3️⃣ LIQUIDATION STREAM
    liquidation = call_api("coinglass.liquidation.aggregated_history", 
                          symbol=SYMBOL, exchange_list="Binance", interval="1m", limit=10)

    # 4️⃣ FUNDING RATE
    funding = call_api("coinglass.funding_rate.history", 
                      exchange="Binance", symbol=f"{SYMBOL}USDT", interval="h8", limit=10)

    # 5️⃣ SMART MONEY (CORRECTED)
    smart_money = call_api("smart_money.analyze", symbol=SYMBOL)

    # 6️⃣ LONG/SHORT RATIO
    ls_ratio = call_api("coinglass.long_short_ratio.position_history", 
                       exchange="Binance", symbol=f"{SYMBOL}USDT", interval="h1", limit=10)

    # 7️⃣ RSI & VOLUME DELTA (CORRECTED)
    rsi = call_api("coinglass.indicators.rsi", symbol=SYMBOL, period="14", interval="h4")
    volume_delta = call_api("coinglass.volume.taker_buy_sell", 
                           exchange="Binance", symbol=f"{SYMBOL}USDT", interval="h4", limit=10)

    # 8️⃣ FEAR & GREED INDEX (CORRECTED)
    fear_greed = call_api("coinglass.indicators.fear_greed")

    print("\n✅ SEMUA DATA TERAMBIL, CEK STATUS:")
    status = {
        "Price Feed": bool(price_data),
        "Market Signal": bool(market_data),
        "Orderbook": bool(orderbook),
        "Whale Walls": bool(whale_walls),
        "Liquidations": bool(liquidation),
        "Funding": bool(funding),
        "Smart Money": bool(smart_money),
        "Long/Short Ratio": bool(ls_ratio),
        "RSI": bool(rsi),
        "Volume Delta": bool(volume_delta),
        "Fear & Greed": bool(fear_greed)
    }

    for k, v in status.items():
        print(f" - {k:<20}: {'🟢 OK' if v else '🔴 FAIL'}")

    print("\n🧠 Ready untuk Scalping Execution Layer (Replit Connected)\n")

if __name__ == "__main__":
    main()
