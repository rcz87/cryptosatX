"""
Comprehensive test for ALL 60 Coinglass Standard Plan endpoints
Based on Coinglass v4 API documentation
"""
import asyncio
import httpx
import os
from datetime import datetime

COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY', '')
BASE_URL = "https://open-api-v4.coinglass.com"

# All 60 Coinglass Standard Plan endpoints organized by category
ALL_ENDPOINTS = {
    "1. LIQUIDATIONS (7 endpoints)": [
        {"name": "Liquidation Coin List", "path": "/api/futures/liquidation/coin-list", "params": {"exchange": "Binance"}},
        {"name": "Liquidation History", "path": "/api/futures/liquidation/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
        {"name": "Liquidation Chart", "path": "/api/futures/liquidation/chart", "params": {"symbol": "BTC"}},
        {"name": "Liquidation Symbol", "path": "/api/futures/liquidation/symbol", "params": {"symbol": "BTC"}},
        {"name": "Liquidation Heatmap", "path": "/api/futures/liquidation/heatmap", "params": {"symbol": "BTC"}},
        {"name": "Liquidation Aggregated", "path": "/api/futures/liquidation/aggregated", "params": {"symbol": "BTC"}},
        {"name": "Liquidation Exchange List", "path": "/api/futures/liquidation/exchange-list", "params": {}},
    ],
    
    "2. FUNDING RATES (6 endpoints)": [
        {"name": "Funding Rate List", "path": "/api/futures/funding-rate/list", "params": {}},
        {"name": "Funding Rate History", "path": "/api/futures/funding-rate/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
        {"name": "Funding Rate Chart", "path": "/api/futures/funding-rate/chart", "params": {"symbol": "BTC"}},
        {"name": "Funding Rate OHLC", "path": "/api/futures/funding-rate/ohlc", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h8"}},
        {"name": "Funding Rate Predicted", "path": "/api/futures/funding-rate/predicted", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
        {"name": "Funding Rate Aggregated", "path": "/api/futures/funding-rate/aggregated", "params": {"symbol": "BTC"}},
    ],
    
    "3. OPEN INTEREST (6 endpoints)": [
        {"name": "OI List", "path": "/api/futures/open-interest/list", "params": {}},
        {"name": "OI History", "path": "/api/futures/open-interest/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
        {"name": "OI Chart", "path": "/api/futures/open-interest/chart", "params": {"symbol": "BTC"}},
        {"name": "OI OHLC", "path": "/api/futures/open-interest/ohlc", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
        {"name": "OI OHLC Aggregated History", "path": "/api/futures/open-interest/ohlc-aggregated-history", "params": {"symbol": "BTC", "interval": "h1"}},
        {"name": "OI Aggregated", "path": "/api/futures/open-interest/aggregated", "params": {"symbol": "BTC"}},
    ],
    
    "4. LONG/SHORT RATIO (4 endpoints)": [
        {"name": "Global Account Ratio History", "path": "/api/futures/global-long-short-account-ratio/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
        {"name": "Top Position Ratio History", "path": "/api/futures/top-long-short-position-ratio/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
        {"name": "Long Short Ratio Chart", "path": "/api/futures/long-short-ratio/chart", "params": {"symbol": "BTC"}},
        {"name": "Long Short Ratio Aggregated", "path": "/api/futures/long-short-ratio/aggregated", "params": {"symbol": "BTC"}},
    ],
    
    "5. TAKER BUY/SELL VOLUME (1 endpoint)": [
        {"name": "Taker Volume History", "path": "/api/futures/taker-buy-sell-volume/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1"}},
    ],
    
    "6. ORDERBOOK DEPTH (5 endpoints)": [
        {"name": "Orderbook List", "path": "/api/futures/orderbook/list", "params": {"exchange": "Binance"}},
        {"name": "Orderbook History", "path": "/api/futures/orderbook/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
        {"name": "Orderbook Chart", "path": "/api/futures/orderbook/chart", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
        {"name": "Orderbook Pro", "path": "/api/futures/orderbook/pro", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
        {"name": "Big Order Alert", "path": "/api/futures/big-order/alert", "params": {"exchange": "Binance"}},
    ],
    
    "7. HYPERLIQUID DEX (3 endpoints)": [
        {"name": "Hyperliquid Funding Rate", "path": "/api/dex/hyperliquid/funding-rate", "params": {}},
        {"name": "Hyperliquid Open Interest", "path": "/api/dex/hyperliquid/open-interest", "params": {}},
        {"name": "Hyperliquid Volume", "path": "/api/dex/hyperliquid/volume", "params": {}},
    ],
    
    "8. ON-CHAIN TRACKING (2 endpoints)": [
        {"name": "BTC Exchange Balance", "path": "/api/onchain/btc-balance", "params": {}},
        {"name": "ETH Exchange Balance", "path": "/api/onchain/eth-balance", "params": {}},
    ],
    
    "9. TECHNICAL INDICATORS (12 endpoints)": [
        {"name": "RSI List", "path": "/api/indicator/rsi-list", "params": {}},
        {"name": "Whale Index", "path": "/api/indicator/whale-index", "params": {"symbol": "BTC"}},
        {"name": "Bubble Index", "path": "/api/indicator/bubble-index", "params": {"symbol": "BTC"}},
        {"name": "CoinGlass Index (CGDI)", "path": "/api/indicator/coin-glass-index", "params": {}},
        {"name": "Golden Ratio", "path": "/api/indicator/golden-ratio", "params": {"symbol": "BTC"}},
        {"name": "Fear Greed Indicator", "path": "/api/indicator/fear-greed", "params": {}},
        {"name": "CGDI History", "path": "/api/indicator/cgdi", "params": {}},
        {"name": "CDRI History", "path": "/api/indicator/cdri", "params": {}},
        {"name": "Whale Ratio", "path": "/api/indicator/whale-ratio", "params": {"symbol": "BTC"}},
        {"name": "MVRV Ratio", "path": "/api/indicator/mvrv", "params": {"symbol": "BTC"}},
        {"name": "NUPL", "path": "/api/indicator/nupl", "params": {"symbol": "BTC"}},
        {"name": "SOPR", "path": "/api/indicator/sopr", "params": {"symbol": "BTC"}},
    ],
    
    "10. MARKET SENTIMENT (3 endpoints)": [
        {"name": "Fear & Greed History", "path": "/api/index/fear-greed-history", "params": {}},
        {"name": "Bitcoin Bubble Index", "path": "/api/index/bitcoin-bubble", "params": {}},
        {"name": "Altcoin Season Index", "path": "/api/index/altcoin-season", "params": {}},
    ],
    
    "11. MACRO & NEWS (3 endpoints)": [
        {"name": "News List", "path": "/api/news/list", "params": {}},
        {"name": "Economic Calendar", "path": "/api/calendar/economic", "params": {}},
        {"name": "Earnings Calendar", "path": "/api/calendar/earnings", "params": {}},
    ],
    
    "12. MARKET DATA (5 endpoints)": [
        {"name": "Futures Ticker", "path": "/api/futures/ticker", "params": {"exchange": "Binance"}},
        {"name": "Futures Pairs", "path": "/api/futures/pairs", "params": {"exchange": "Binance"}},
        {"name": "Kline/Candlestick", "path": "/api/futures/kline", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1h"}},
        {"name": "Basis Data", "path": "/api/futures/basis", "params": {"symbol": "BTC"}},
        {"name": "Premium Index", "path": "/api/futures/premium-index", "params": {"exchange": "Binance", "symbol": "BTCUSDT"}},
    ],
    
    "13. ADDITIONAL ENDPOINTS (3 endpoints)": [
        {"name": "Exchange Info", "path": "/api/futures/exchange/info", "params": {}},
        {"name": "Symbol Info", "path": "/api/futures/symbol/info", "params": {"symbol": "BTC"}},
        {"name": "Supported Coins", "path": "/api/futures/supported-coins", "params": {}},
    ],
}

async def test_endpoint(client, category, endpoint_config):
    """Test single endpoint"""
    url = f"{BASE_URL}{endpoint_config['path']}"
    headers = {
        "CG-API-KEY": COINGLASS_API_KEY,
        "accept": "application/json"
    }
    
    try:
        response = await client.get(url, headers=headers, params=endpoint_config['params'], timeout=15.0)
        
        if response.status_code == 200:
            data = response.json()
            code = data.get("code")
            has_data = bool(data.get("data"))
            
            if str(code) == "0" and has_data:
                status = "✅ OK"
                working = True
            elif str(code) == "0":
                status = "⚠️ Empty"
                working = False
            else:
                status = f"⚠️ Code {code}"
                working = False
            
            return {
                "category": category,
                "name": endpoint_config['name'],
                "status": status,
                "http_code": 200,
                "api_code": code,
                "has_data": has_data,
                "working": working
            }
        elif response.status_code == 401:
            return {
                "category": category,
                "name": endpoint_config['name'],
                "status": "❌ 401 Auth",
                "http_code": 401,
                "working": False,
                "note": "API key issue"
            }
        elif response.status_code == 404:
            return {
                "category": category,
                "name": endpoint_config['name'],
                "status": "❌ 404",
                "http_code": 404,
                "working": False,
                "note": "Not available or requires higher tier"
            }
        elif response.status_code == 403:
            return {
                "category": category,
                "name": endpoint_config['name'],
                "status": "❌ 403 Forbidden",
                "http_code": 403,
                "working": False,
                "note": "Requires upgrade"
            }
        else:
            return {
                "category": category,
                "name": endpoint_config['name'],
                "status": f"❌ HTTP {response.status_code}",
                "http_code": response.status_code,
                "working": False
            }
            
    except Exception as e:
        return {
            "category": category,
            "name": endpoint_config['name'],
            "status": "❌ ERROR",
            "working": False,
            "error": str(e)[:100]
        }

async def test_all_60_endpoints():
    """Test all 60 Coinglass endpoints comprehensively"""
    print("=" * 120)
    print("COMPREHENSIVE COINGLASS STANDARD PLAN - ALL 60 ENDPOINTS TEST")
    print("=" * 120)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient() as client:
        all_tasks = []
        endpoint_count = 0
        
        for category, endpoints in ALL_ENDPOINTS.items():
            for endpoint_config in endpoints:
                all_tasks.append(test_endpoint(client, category, endpoint_config))
                endpoint_count += 1
        
        print(f"Testing {endpoint_count} endpoints concurrently...\n")
        results = await asyncio.gather(*all_tasks)
    
    # Group results by category
    by_category = {}
    for result in results:
        cat = result['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(result)
    
    # Print results
    total_working = 0
    total_404 = 0
    total_403 = 0
    total_401 = 0
    total_empty = 0
    total_other = 0
    
    for category, cat_results in by_category.items():
        print(f"\n{category}")
        print("-" * 120)
        
        for r in cat_results:
            name = r['name']
            status = r['status']
            print(f"  {status:15} {name}")
            
            if r.get('working'):
                total_working += 1
            elif '404' in r['status']:
                total_404 += 1
            elif '403' in r['status']:
                total_403 += 1
            elif '401' in r['status']:
                total_401 += 1
            elif 'Empty' in r['status']:
                total_empty += 1
            else:
                total_other += 1
    
    # Summary
    total = len(results)
    print("\n" + "=" * 120)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 120)
    print(f"Total Endpoints:      {total}")
    print(f"✅ Working:           {total_working} ({total_working/total*100:.1f}%)")
    print(f"⚠️ Empty Data:        {total_empty} ({total_empty/total*100:.1f}%)")
    print(f"❌ 404 Not Found:     {total_404} ({total_404/total*100:.1f}%)")
    print(f"❌ 403 Forbidden:     {total_403} ({total_403/total*100:.1f}%)")
    print(f"❌ 401 Unauthorized:  {total_401} ({total_401/total*100:.1f}%)")
    print(f"❌ Other Errors:      {total_other} ({total_other/total*100:.1f}%)")
    print("=" * 120)
    
    success_rate = (total_working / total * 100) if total > 0 else 0
    available_rate = ((total_working + total_empty) / total * 100) if total > 0 else 0
    
    print(f"\nSuccess Rate (working + has data):     {success_rate:.1f}%")
    print(f"Availability Rate (accessible):         {available_rate:.1f}%")
    print(f"Not Available (404/403):                {(total_404 + total_403)/total*100:.1f}%")
    
    if success_rate >= 50:
        print("\n✅ OVERALL STATUS: GOOD - Majority of endpoints working")
    elif available_rate >= 50:
        print("\n⚠️ OVERALL STATUS: PARTIAL - Many endpoints accessible but returning empty data")
    else:
        print("\n❌ OVERALL STATUS: LIMITED - Most endpoints not available (may need upgrade)")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)

if __name__ == "__main__":
    asyncio.run(test_all_60_endpoints())
