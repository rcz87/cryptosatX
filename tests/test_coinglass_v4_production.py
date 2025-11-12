"""
CORRECT Comprehensive Coinglass v4 Endpoints Test
Tests ALL actual endpoints used in production
"""
import asyncio
import httpx
import os
from datetime import datetime

COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY', '')
BASE_URL = "https://open-api-v4.coinglass.com"

# Actual v4 endpoints used in production code
V4_ENDPOINTS = {
    "1. Liquidation Data": {
        "url": "/api/futures/liquidation/coin-list",
        "params": {"exchange": "Binance"},
        "description": "Liquidation volumes (longs vs shorts)"
    },
    "2. Long/Short Ratio": {
        "url": "/api/futures/global-long-short-account-ratio/history",
        "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1", "limit": 1},
        "description": "Global account long/short ratios"
    },
    "3. Open Interest Trend": {
        "url": "/api/futures/open-interest/ohlc-aggregated-history",
        "params": {"symbol": "BTC", "interval": "h1", "limit": 24},
        "description": "OI trend analysis (24h change)"
    },
    "4. Top Trader Positioning": {
        "url": "/api/futures/top-long-short-position-ratio/history",
        "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "h1", "limit": 1},
        "description": "Smart money positioning"
    },
    "5. Fear & Greed Index": {
        "url": "/api/index/fear-greed-history",
        "params": {},
        "description": "Crypto market sentiment index"
    },
}

async def test_v4_endpoint(client, name, config):
    """Test single v4 endpoint"""
    url = f"{BASE_URL}{config['url']}"
    headers = {
        "CG-API-KEY": COINGLASS_API_KEY,
        "accept": "application/json"
    }
    
    try:
        response = await client.get(url, headers=headers, params=config['params'], timeout=15.0)
        
        if response.status_code == 200:
            data = response.json()
            code = data.get("code")
            has_data = bool(data.get("data"))
            
            status = "✅ OK" if str(code) == "0" and has_data else f"⚠️ Code {code}"
            
            return {
                "name": name,
                "status": status,
                "http_code": 200,
                "api_code": code,
                "has_data": has_data,
                "description": config['description'],
                "working": str(code) == "0" and has_data
            }
        elif response.status_code == 401:
            return {
                "name": name,
                "status": "❌ UNAUTHORIZED",
                "http_code": 401,
                "error": "API Key invalid or subscription expired",
                "working": False
            }
        elif response.status_code == 404:
            return {
                "name": name,
                "status": "❌ NOT FOUND",
                "http_code": 404,
                "error": "Endpoint not available (may require higher tier)",
                "working": False
            }
        else:
            return {
                "name": name,
                "status": f"❌ HTTP {response.status_code}",
                "http_code": response.status_code,
                "error": response.text[:200],
                "working": False
            }
            
    except Exception as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "error": str(e)[:200],
            "working": False
        }

async def test_production_endpoints():
    """Test all v4 production endpoints"""
    print("=" * 100)
    print("COINGLASS V4 API - PRODUCTION ENDPOINTS VERIFICATION")
    print("=" * 100)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient() as client:
        tasks = [
            test_v4_endpoint(client, name, config)
            for name, config in V4_ENDPOINTS.items()
        ]
        results = await asyncio.gather(*tasks)
    
    # Display results
    print("-" * 100)
    print(f"{'ENDPOINT':<35} {'STATUS':<20} {'DESCRIPTION'}")
    print("-" * 100)
    
    working_count = 0
    for result in results:
        name = result['name']
        status = result['status']
        desc = result.get('description', 'N/A')
        
        print(f"{name:<35} {status:<20} {desc}")
        
        if result.get('working'):
            working_count += 1
        elif 'error' in result:
            print(f"{'':>35} {'':>20} Error: {result['error'][:60]}")
    
    # Summary
    total = len(results)
    success_rate = (working_count / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total Endpoints Tested: {total}")
    print(f"✅ Working:             {working_count} ({success_rate:.1f}%)")
    print(f"❌ Failed:              {total - working_count} ({100 - success_rate:.1f}%)")
    print("=" * 100)
    
    if success_rate >= 80:
        print("✅ OVERALL STATUS: EXCELLENT - 80%+ endpoints working")
    elif success_rate >= 60:
        print("✅ OVERALL STATUS: GOOD - 60%+ endpoints working")
    elif success_rate >= 40:
        print("⚠️ OVERALL STATUS: PARTIAL - 40-60% working")
    else:
        print("❌ OVERALL STATUS: CRITICAL - <40% working (check API key/subscription)")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Return status for scripting
    return success_rate >= 60

if __name__ == "__main__":
    success = asyncio.run(test_production_endpoints())
    exit(0 if success else 1)
