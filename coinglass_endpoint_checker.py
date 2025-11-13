import json
import requests

# --- daftar lengkap endpoint Coinglass (65 total) ---
COINGLASS_ENDPOINTS = [
    # Liquidations
    "coinglass.liquidations.symbol", "coinglass.liquidations.heatmap", 
    "coinglass.liquidation.history", "coinglass.liquidation.order", 
    "coinglass.liquidation.exchange_list", "coinglass.liquidation.aggregated_history",

    # Funding Rate
    "coinglass.funding_rate.history", "coinglass.funding_rate.exchange_list", 
    "coinglass.funding_rate.accumulated_exchange_list", 
    "coinglass.funding_rate.oi_weight_history", "coinglass.funding_rate.vol_weight_history",

    # Open Interest
    "coinglass.open_interest.history", "coinglass.open_interest.exchange_list", 
    "coinglass.open_interest.aggregated_history",
    "coinglass.open_interest.aggregated_stablecoin_history",
    "coinglass.open_interest.aggregated_coin_margin_history",
    "coinglass.open_interest.exchange_history_chart",

    # Indicators
    "coinglass.indicators.fear_greed", "coinglass.indicators.rsi",
    "coinglass.indicators.rsi_list", "coinglass.indicators.ma",
    "coinglass.indicators.ema", "coinglass.indicators.bollinger",
    "coinglass.indicators.macd", "coinglass.indicators.basis",
    "coinglass.indicators.whale_index", "coinglass.indicators.cgdi",
    "coinglass.indicators.cdri", "coinglass.indicators.golden_ratio",

    # Whale Data
    "coinglass.orderbook.whale_walls", "coinglass.orderbook.whale_history",
    "coinglass.chain.whale_transfers", "coinglass.chain.exchange_flows",
    "coinglass.hyperliquid.whale_alerts", "coinglass.hyperliquid.whale_positions",
    "coinglass.hyperliquid.positions.symbol",

    # Market Data
    "coinglass.markets", "coinglass.exchanges", "coinglass.supported_coins",
    "coinglass.perpetual_market.symbol", "coinglass.pairs_markets.symbol",
    "coinglass.price_change", "coinglass.price_history", 
    "coinglass.delisted_pairs",

    # Advanced / Others
    "coinglass.etf.flows", "coinglass.onchain.reserves",
    "coinglass.long_short_ratio.account_history",
    "coinglass.long_short_ratio.position_history",
    "coinglass.net_position.history",
    "coinglass.options.open_interest", "coinglass.options.volume",
    "coinglass.taker_buy_sell.exchange_list",
    "coinglass.news.feed", "coinglass.calendar.economic",
    "coinglass.index.bull_market_peak", "coinglass.index.rainbow_chart",
    "coinglass.index.stock_to_flow", "coinglass.borrow.interest_rate",
    "coinglass.exchange.assets"
]

# --- hasil audit disimpan di sini ---
results = []

print("🚀 Memulai pengecekan semua endpoint Coinglass...\n")

for op in COINGLASS_ENDPOINTS:
    try:
        # test call sederhana untuk coin SOL
        payload = {"operation": op, "symbol": "SOL"}
        response = requests.post("http://localhost:8000/invoke", json=payload, timeout=10)
        res = response.json()
        
        # validasi data
        if res.get("ok"):
            results.append({"endpoint": op, "status": "✅ ACTIVE"})
            print(f"✅ {op} — ACTIVE")
        else:
            error_msg = res.get("error", {}).get("message", "") if isinstance(res.get("error"), dict) else str(res.get("error", ""))
            if "NotImplemented" in error_msg:
                results.append({"endpoint": op, "status": "⚠️ STUBBED"})
                print(f"⚠️ {op} — STUBBED (handler missing)")
            elif "Premium" in error_msg or "Forbidden" in error_msg:
                results.append({"endpoint": op, "status": "🔒 PREMIUM"})
                print(f"🔒 {op} — PREMIUM ONLY")
            else:
                results.append({"endpoint": op, "status": "⚠️ ERROR", "error": error_msg[:100]})
                print(f"⚠️ {op} — ERROR: {error_msg[:70]}")
    except Exception as e:
        err = str(e)
        results.append({"endpoint": op, "status": "⚠️ FAILED", "error": err[:100]})
        print(f"⚠️ {op} — FAILED: {err[:70]}")

# --- simpan hasil ke file ---
with open("coinglass_health.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n✅ Audit selesai! Hasil disimpan di: coinglass_health.json")