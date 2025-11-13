#!/usr/bin/env python3
"""
Test script for the newly implemented missing endpoints
Tests the 4 endpoints that were returning 404 errors:
- /smart-money/accumulation
- /portfolio/optimize
- /risk/assess/{symbol}
- /strategies/recommend
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINTS_TO_TEST = [
    {
        "name": "Whale Accumulation Finder",
        "path": "/gpt/smart-money/accumulation",
        "params": {"min_score": 8, "exclude_overbought": True},
        "method": "GET",
    },
    {
        "name": "Portfolio Optimization",
        "path": "/gpt/portfolio/optimize",
        "params": {
            "risk_tolerance": 5,
            "investment_amount": 10000,
            "time_horizon": "medium_term",
        },
        "method": "GET",
    },
    {
        "name": "Risk Assessment",
        "path": "/gpt/risk/assess/BTC",
        "params": {"position_size": 5000},
        "method": "GET",
    },
    {
        "name": "Trading Strategy Recommendations",
        "path": "/gpt/strategies/recommend",
        "params": {"symbol": "BTC", "strategy_type": "all", "timeframe": "swing"},
        "method": "GET",
    },
]


async def test_endpoint(session, endpoint):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint['path']}"
    params = endpoint.get("params", {})
    method = endpoint.get("method", "GET")

    print(f"\n🧪 Testing: {endpoint['name']}")
    print(f"📡 URL: {url}")
    print(f"📋 Params: {params}")

    try:
        if method == "GET":
            async with session.get(url, params=params) as response:
                status = response.status
                content = await response.text()

                print(f"📊 Status Code: {status}")

                if status == 200:
                    try:
                        data = json.loads(content)
                        print(f"✅ SUCCESS: {endpoint['name']}")

                        # Validate response structure
                        if "success" in data:
                            print(f"   Success field: {data['success']}")

                        # Show key data points
                        if endpoint["name"] == "Whale Accumulation Finder":
                            if data.get("success") and "accumulationAnalysis" in data:
                                opportunities = data["accumulationAnalysis"].get(
                                    "opportunities", []
                                )
                                print(f"   Opportunities found: {len(opportunities)}")

                        elif endpoint["name"] == "Portfolio Optimization":
                            if data.get("success") and "portfolioOptimization" in data:
                                allocations = data["portfolioOptimization"].get(
                                    "optimalAllocation", []
                                )
                                print(
                                    f"   Portfolio allocations: {len(allocations)} coins"
                                )

                        elif endpoint["name"] == "Risk Assessment":
                            if data.get("success") and "riskAssessment" in data:
                                risk_score = data["riskAssessment"].get(
                                    "overallRiskScore"
                                )
                                risk_level = data["riskAssessment"].get("riskLevel")
                                print(f"   Risk Score: {risk_score} ({risk_level})")

                        elif endpoint["name"] == "Trading Strategy Recommendations":
                            if (
                                data.get("success")
                                and "strategyRecommendations" in data
                            ):
                                strategies = data["strategyRecommendations"].get(
                                    "recommendedStrategies", []
                                )
                                print(f"   Strategies recommended: {len(strategies)}")

                    except json.JSONDecodeError:
                        print(f"⚠️  WARNING: Invalid JSON response")
                        print(f"   Response preview: {content[:200]}...")

                elif status == 404:
                    print(f"❌ FAILED: {endpoint['name']} - Still returning 404")
                    print(f"   Response: {content[:200]}...")

                else:
                    print(f"⚠️  WARNING: {endpoint['name']} - Status {status}")
                    print(f"   Response: {content[:200]}...")

                return status == 200

    except aiohttp.ClientError as e:
        print(f"🔥 ERROR: {endpoint['name']} - Connection failed")
        print(f"   Error: {str(e)}")
        return False
    except Exception as e:
        print(f"🔥 ERROR: {endpoint['name']} - Unexpected error")
        print(f"   Error: {str(e)}")
        return False


async def main():
    """Main test function"""
    print("🚀 CRYPTOSATX - Missing Endpoints Test")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📋 Testing {len(ENDPOINTS_TO_TEST)} endpoints")
    print("=" * 50)

    # Create HTTP session
    async with aiohttp.ClientSession() as session:
        results = []

        # Test each endpoint
        for endpoint in ENDPOINTS_TO_TEST:
            success = await test_endpoint(session, endpoint)
            results.append(
                {"name": endpoint["name"], "path": endpoint["path"], "success": success}
            )

        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        successful = sum(1 for r in results if r["success"])
        total = len(results)

        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['name']}")
            print(f"     {result['path']}")

        print(f"\n🎯 Overall Result: {successful}/{total} endpoints working")

        if successful == total:
            print("🎉 ALL ENDPOINTS SUCCESSFULLY IMPLEMENTED!")
            print("✅ The MAXIMAL schema is now complete!")
        else:
            print("⚠️  Some endpoints still need attention")

        print("=" * 50)


if __name__ == "__main__":
    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        import aiohttp

        asyncio.run(main())
    except ImportError:
        print("❌ aiohttp not installed. Install with: pip install aiohttp")
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        print("💡 Make sure the server is running on http://localhost:8000")
        print("   Run: python -m uvicorn app.main:app --reload")
