import requests, json, time

BASE_URL = "https://guardiansofthetoken.org/invoke"
SYMBOL = "XRP"
PAIR = f"{SYMBOL}USDT"

def call_api(operation, **params):
    """Fungsi pemanggil endpoint - OPTIMIZED untuk GPT Actions"""
    payload = {"operation": operation}
    payload.update(params)
    try:
        # Timeout lebih panjang untuk heavy endpoints
        timeout = 45 if "smart_money" in operation or "market.get" in operation else 20
        
        res = requests.post(BASE_URL, json=payload, timeout=timeout)
        res.raise_for_status()
        data = res.json()
        
        if data.get("ok"):
            print(f"[{operation}] ✅ OK")
            return data.get("data", data)
        else:
            print(f"[{operation}] ❌ {data.get('error', 'Unknown error')[:50]}")
            return None
    except requests.Timeout:
        print(f"[{operation}] ⏱️  TIMEOUT - heavy processing")
        return None
    except Exception as e:
        print(f"[{operation}] ❌ ERROR → {str(e)[:50]}")
        return None


def main():
    print(f"\n🚀 REAL-TIME DATA FETCH FOR {SYMBOL}")
    print(f"{'='*60}\n")

    # 1️⃣ PRICE & OHLCV
    print("📊 Fetching Price Data...")
    price_data = call_api("coinapi.ohlcv.latest", symbol=SYMBOL)
    
    # 2️⃣ FULL MARKET SIGNAL (comprehensive)
    print("🎯 Fetching Full Market Signal...")
    market_data = call_api("market.get", symbol=SYMBOL)

    # 3️⃣ ORDERBOOK & WHALE ACTIVITY
    print("📖 Fetching Orderbook...")
    orderbook = call_api("coinapi.orderbook", symbol=SYMBOL)
    whale_walls = call_api("coinglass.orderbook.whale_walls", symbol=SYMBOL)

    # 4️⃣ LIQUIDATION DATA
    print("💥 Fetching Liquidations...")
    liquidation = call_api("coinglass.liquidation.aggregated_history", 
                          symbol=SYMBOL, 
                          exchange_list="Binance", 
                          interval="1h", 
                          limit=10)

    # 5️⃣ FUNDING RATE
    print("💰 Fetching Funding Rates...")
    funding = call_api("coinglass.funding_rate.history", 
                      exchange="Binance", 
                      symbol=PAIR, 
                      interval="h8", 
                      limit=10)

    # 6️⃣ SMART MONEY ANALYSIS
    print("🧠 Analyzing Smart Money...")
    smart_money = call_api("smart_money.scan", symbol=SYMBOL)

    # 7️⃣ LONG/SHORT RATIO
    print("📊 Fetching Long/Short Ratio...")
    ls_ratio = call_api("coinglass.long_short_ratio.position_history", 
                       exchange="Binance", 
                       symbol=PAIR, 
                       interval="h1", 
                       limit=10)

    # 8️⃣ TECHNICAL INDICATORS
    print("📈 Fetching Technical Indicators...")
    rsi = call_api("coinglass.indicators.rsi", 
                  symbol=SYMBOL, 
                  period="14", 
                  interval="h4")
    
    # 9️⃣ TAKER BUY/SELL VOLUME (alternative endpoint)
    print("📊 Fetching Volume Delta...")
    volume_delta = call_api("coinglass.taker_buy_sell.exchange_list", 
                           symbol=PAIR)

    # 🔟 FEAR & GREED INDEX
    print("😱 Fetching Fear & Greed...")
    fear_greed = call_api("coinglass.indicators.fear_greed")

    # 📊 STATUS SUMMARY
    print(f"\n{'='*60}")
    print("✅ DATA COLLECTION STATUS:")
    print(f"{'='*60}\n")
    
    status = {
        "Price Feed (OHLCV)": bool(price_data),
        "Market Signal (Full)": bool(market_data),
        "Orderbook Depth": bool(orderbook),
        "Whale Walls": bool(whale_walls),
        "Liquidations": bool(liquidation),
        "Funding Rates": bool(funding),
        "Smart Money": bool(smart_money),
        "Long/Short Ratio": bool(ls_ratio),
        "RSI Indicator": bool(rsi),
        "Volume Delta": bool(volume_delta),
        "Fear & Greed Index": bool(fear_greed)
    }

    total = len(status)
    success = sum(1 for v in status.values() if v)
    
    for k, v in status.items():
        symbol = '🟢' if v else '🔴'
        status_text = 'OK' if v else 'FAIL'
        print(f" {symbol} {k:<25}: {status_text}")
    
    print(f"\n{'='*60}")
    print(f"📊 SUCCESS RATE: {success}/{total} ({int(success/total*100)}%)")
    print(f"{'='*60}\n")
    
    if success >= 9:
        print("🎉 READY FOR GPT ACTIONS & SCALPING EXECUTION!\n")
    else:
        print("⚠️  Some endpoints failed - check logs above\n")
    
    return {
        "status": status,
        "success_rate": f"{success}/{total}",
        "ready": success >= 9
    }


if __name__ == "__main__":
    result = main()
