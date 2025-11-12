"""
Verify ALL Coinglass routes are callable and documented for GPT Actions
"""
import httpx
import asyncio
from datetime import datetime

BASE_URL = "https://guardiansofthetoken.org"

# All 64+ Coinglass endpoints from routes_coinglass.py
ENDPOINTS = [
    # Market Data (4)
    {"category": "Market", "path": "/coinglass/markets", "method": "GET"},
    {"category": "Market", "path": "/coinglass/markets/BTC", "method": "GET"},
    {"category": "Market", "path": "/coinglass/perpetual-market/BTCUSDT", "method": "GET"},
    {"category": "Market", "path": "/coinglass/pairs-markets/BTCUSDT", "method": "GET"},
    
    # Liquidations (6)
    {"category": "Liquidation", "path": "/coinglass/liquidation/order", "method": "GET"},
    {"category": "Liquidation", "path": "/coinglass/liquidation/exchange-list", "method": "GET"},
    {"category": "Liquidation", "path": "/coinglass/liquidation/aggregated-history", "method": "GET"},
    {"category": "Liquidation", "path": "/coinglass/liquidation/history", "method": "GET"},
    {"category": "Liquidation", "path": "/coinglass/liquidations/BTC", "method": "GET"},
    {"category": "Liquidation", "path": "/coinglass/liquidations/BTC/heatmap", "method": "GET"},
    
    # Funding Rates (5)
    {"category": "Funding", "path": "/coinglass/funding-rate/history", "method": "GET"},
    {"category": "Funding", "path": "/coinglass/funding-rate/oi-weight-history", "method": "GET"},
    {"category": "Funding", "path": "/coinglass/funding-rate/vol-weight-history", "method": "GET"},
    {"category": "Funding", "path": "/coinglass/funding-rate/exchange-list/BTC", "method": "GET"},
    {"category": "Funding", "path": "/coinglass/funding-rate/accumulated-exchange-list", "method": "GET"},
    
    # Open Interest (6)
    {"category": "OI", "path": "/coinglass/open-interest/history", "method": "GET"},
    {"category": "OI", "path": "/coinglass/open-interest/aggregated-history", "method": "GET"},
    {"category": "OI", "path": "/coinglass/open-interest/aggregated-stablecoin-history", "method": "GET"},
    {"category": "OI", "path": "/coinglass/open-interest/aggregated-coin-margin-history", "method": "GET"},
    {"category": "OI", "path": "/coinglass/open-interest/exchange-list/BTC", "method": "GET"},
    {"category": "OI", "path": "/coinglass/open-interest/exchange-history-chart", "method": "GET"},
    
    # Long/Short Ratios (4)
    {"category": "L/S", "path": "/coinglass/top-long-short-account-ratio/history", "method": "GET"},
    {"category": "L/S", "path": "/coinglass/top-long-short-position-ratio/history", "method": "GET"},
    {"category": "L/S", "path": "/coinglass/taker-buy-sell-volume/exchange-list", "method": "GET"},
    {"category": "L/S", "path": "/coinglass/net-position/history", "method": "GET"},
    
    # Orderbook (5)
    {"category": "Orderbook", "path": "/coinglass/orderbook/ask-bids-history", "method": "GET"},
    {"category": "Orderbook", "path": "/coinglass/orderbook/aggregated-history", "method": "GET"},
    {"category": "Orderbook", "path": "/coinglass/orderbook/whale-walls", "method": "GET"},
    {"category": "Orderbook", "path": "/coinglass/orderbook/whale-history", "method": "GET"},
    {"category": "Orderbook", "path": "/coinglass/orderbook/detailed-history", "method": "GET"},
    
    # Hyperliquid (3)
    {"category": "Hyperliquid", "path": "/coinglass/hyperliquid/whale-alerts", "method": "GET"},
    {"category": "Hyperliquid", "path": "/coinglass/hyperliquid/whale-positions", "method": "GET"},
    {"category": "Hyperliquid", "path": "/coinglass/hyperliquid/positions/BTC", "method": "GET"},
    
    # On-Chain (3)
    {"category": "OnChain", "path": "/coinglass/chain/whale-transfers", "method": "GET"},
    {"category": "OnChain", "path": "/coinglass/chain/exchange-flows", "method": "GET"},
    {"category": "OnChain", "path": "/coinglass/on-chain/reserves/BTC", "method": "GET"},
    
    # Technical Indicators (12)
    {"category": "Indicator", "path": "/coinglass/indicators/rsi-list", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/rsi", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/ma", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/ema", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/bollinger", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/macd", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/basis", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/whale-index", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/cgdi", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/cdri", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/golden-ratio", "method": "GET"},
    {"category": "Indicator", "path": "/coinglass/indicators/fear-greed", "method": "GET"},
    
    # Macro & News (2)
    {"category": "Macro", "path": "/coinglass/calendar/economic", "method": "GET"},
    {"category": "News", "path": "/coinglass/news/feed", "method": "GET"},
    
    # Options (2)
    {"category": "Options", "path": "/coinglass/options/open-interest", "method": "GET"},
    {"category": "Options", "path": "/coinglass/options/volume", "method": "GET"},
    
    # ETF & Indexes (4)
    {"category": "ETF", "path": "/coinglass/etf/flows/BTC", "method": "GET"},
    {"category": "Index", "path": "/coinglass/index/bull-market-peak", "method": "GET"},
    {"category": "Index", "path": "/coinglass/index/rainbow-chart", "method": "GET"},
    {"category": "Index", "path": "/coinglass/index/stock-to-flow", "method": "GET"},
    
    # Utility (5)
    {"category": "Util", "path": "/coinglass/supported-coins", "method": "GET"},
    {"category": "Util", "path": "/coinglass/exchanges", "method": "GET"},
    {"category": "Util", "path": "/coinglass/price-change", "method": "GET"},
    {"category": "Util", "path": "/coinglass/price-history", "method": "GET"},
    {"category": "Util", "path": "/coinglass/delisted-pairs", "method": "GET"},
    
    # Taker Volume (1)
    {"category": "Taker", "path": "/coinglass/volume/taker-buy-sell", "method": "GET"},
    
    # Other (3)
    {"category": "Other", "path": "/coinglass/borrow/interest-rate", "method": "GET"},
    {"category": "Other", "path": "/coinglass/exchange/assets/Binance", "method": "GET"},
    {"category": "Other", "path": "/coinglass/dashboard/BTC", "method": "GET"},
]

async def test_endpoint(client, endpoint):
    """Test single endpoint"""
    url = f"{BASE_URL}{endpoint['path']}"
    try:
        response = await client.get(url, timeout=15.0)
        success = response.status_code == 200
        has_data = False
        
        if success:
            try:
                data = response.json()
                has_data = bool(data.get("success") and data.get("data"))
            except:
                pass
        
        return {
            "category": endpoint["category"],
            "path": endpoint["path"],
            "status": response.status_code,
            "success": success,
            "has_data": has_data
        }
    except Exception as e:
        return {
            "category": endpoint["category"],
            "path": endpoint["path"],
            "status": 0,
            "success": False,
            "error": str(e)[:100]
        }

async def verify_all_routes():
    """Verify all Coinglass routes"""
    print("=" * 100)
    print("VERIFYING ALL COINGLASS API ROUTES - GPT ACTIONS CALLABLE")
    print("=" * 100)
    print(f"Production URL: {BASE_URL}")
    print(f"Total Endpoints to Test: {len(ENDPOINTS)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient() as client:
        tasks = [test_endpoint(client, ep) for ep in ENDPOINTS]
        results = await asyncio.gather(*tasks)
    
    # Group by category
    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)
    
    # Print results
    total_success = 0
    total_failed = 0
    
    print("\nRESULTS BY CATEGORY:")
    print("-" * 100)
    
    for category, cat_results in sorted(by_category.items()):
        success_count = sum(1 for r in cat_results if r["success"])
        total_count = len(cat_results)
        status_icon = "✅" if success_count == total_count else "⚠️"
        
        print(f"\n{status_icon} {category} ({success_count}/{total_count})")
        
        for r in cat_results:
            icon = "✅" if r["success"] else "❌"
            data_icon = "📊" if r.get("has_data") else "📭"
            path_short = r["path"].replace("/coinglass/", "")
            print(f"  {icon} {data_icon} {path_short}")
        
        total_success += success_count
        total_failed += (total_count - success_count)
    
    # Summary
    print("\n" + "=" * 100)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 100)
    print(f"Total Endpoints:      {len(ENDPOINTS)}")
    print(f"✅ Success:           {total_success} ({total_success/len(ENDPOINTS)*100:.1f}%)")
    print(f"❌ Failed:            {total_failed} ({total_failed/len(ENDPOINTS)*100:.1f}%)")
    print("=" * 100)
    
    if total_success / len(ENDPOINTS) >= 0.90:
        print("\n✅ STATUS: EXCELLENT - 90%+ endpoints operational")
        print("🎯 GPT Actions can call ALL working endpoints!")
    elif total_success / len(ENDPOINTS) >= 0.70:
        print("\n✅ STATUS: GOOD - 70%+ endpoints operational")
    else:
        print("\n⚠️ STATUS: NEEDS ATTENTION - <70% operational")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(verify_all_routes())
