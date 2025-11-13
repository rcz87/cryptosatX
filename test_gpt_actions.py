#!/usr/bin/env python3
"""
Test script to verify GPT Actions integration with CryptoSatX API
This script tests the exact API calls that GPT should make
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "https://guardiansofthetoken.org"
INVOKE_ENDPOINT = f"{BASE_URL}/invoke"
SCHEMA_ENDPOINT = f"{BASE_URL}/invoke/schema"


def test_schema():
    """Test schema endpoint accessibility"""
    print("🔍 Testing Schema Endpoint...")
    try:
        response = requests.get(SCHEMA_ENDPOINT)
        if response.status_code == 200:
            schema = response.json()
            operations_count = len(
                schema.get("paths", {})
                .get("/invoke", {})
                .get("post", {})
                .get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("properties", {})
                .get("operation", {})
                .get("enum", [])
            )
            print(f"✅ Schema accessible - {operations_count} operations available")
            return True
        else:
            print(f"❌ Schema failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Schema error: {e}")
        return False


def test_api_call(operation, params=None):
    """Test individual API call"""
    if params is None:
        params = {}

    payload = {"operation": operation, **params}

    print(f"🔄 Testing: {operation}")
    try:
        start_time = time.time()
        response = requests.post(INVOKE_ENDPOINT, json=payload)
        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            duration = (end_time - start_time) * 1000

            if data.get("ok"):
                print(f"✅ {operation} - Success ({duration:.0f}ms)")
                return {
                    "success": True,
                    "duration_ms": duration,
                    "data": data.get("data", {}),
                    "operation": data.get("operation"),
                }
            else:
                print(f"❌ {operation} - API Error: {data.get('error', 'Unknown')}")
                return {"success": False, "error": data.get("error")}
        else:
            print(f"❌ {operation} - HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        print(f"❌ {operation} - Exception: {e}")
        return {"success": False, "error": str(e)}


def test_gpt_template_scenarios():
    """Test scenarios that GPT templates should trigger"""
    print("\n🎯 Testing GPT Template Scenarios...")

    scenarios = [
        {
            "name": "Template 1: Trading Signal Analysis",
            "calls": [
                ("signals.get", {"symbol": "BTC"}),
                (
                    "coinglass.liquidations.symbol",
                    {"symbol": "BTC", "time_type": "h24"},
                ),
                ("coinglass.funding_rate.history", {"symbol": "BTC"}),
                ("coinglass.indicators.fear_greed", {}),
            ],
        },
        {
            "name": "Template 2: Smart Money Scan",
            "calls": [
                ("smart_money.scan", {"limit": 15}),
                ("coinglass.open_interest.history", {"symbol": "BTC"}),
                ("coinglass.hyperliquid.whale_alerts", {}),
            ],
        },
        {
            "name": "Template 3: MSS Discovery",
            "calls": [
                ("mss.discover", {"min_mss_score": 75, "max_results": 10}),
                ("lunarcrush.coin", {"symbol": "BTC"}),
                ("new_listings.binance", {"days": 7}),
            ],
        },
    ]

    results = {}

    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}")
        scenario_results = []

        for operation, params in scenario["calls"]:
            result = test_api_call(operation, params)
            scenario_results.append(result)
            time.sleep(0.5)  # Rate limiting

        results[scenario["name"]] = scenario_results

    return results


def analyze_gpt_response_accuracy():
    """Compare API data with typical GPT response format"""
    print("\n🔬 Analyzing GPT Response Accuracy...")

    # Get BTC signal data
    result = test_api_call("signals.get", {"symbol": "BTC"})

    if result["success"]:
        data = result["data"]

        print("📋 API Data Structure:")
        print(f"  Symbol: {data.get('symbol')}")
        print(f"  Signal: {data.get('signal')}")
        print(f"  Score: {data.get('score')}")
        print(f"  Confidence: {data.get('confidence')}")
        print(f"  Price: ${data.get('price'):,.2f}")
        print(f"  Timestamp: {data.get('timestamp')}")

        print("\n🎯 Key Factors Available:")
        reasons = data.get("reasons", [])
        for i, reason in enumerate(reasons, 1):
            print(f"  {i}. {reason}")

        print("\n📊 Premium Metrics:")
        premium = data.get("premiumMetrics", {})
        if premium:
            print(f"  Liquidation Imbalance: {premium.get('liquidationImbalance')}")
            print(f"  Long/Short Sentiment: {premium.get('longShortSentiment')}")
            print(f"  Smart Money Bias: {premium.get('smartMoneyBias')}")
            print(f"  Fear & Greed Index: {premium.get('fearGreedIndex')}")

        return True
    else:
        print(f"❌ Failed to get data: {result.get('error')}")
        return False


def generate_gpt_actions_report():
    """Generate comprehensive report for GPT Actions setup"""
    print("\n📝 Generating GPT Actions Report...")

    report = {
        "timestamp": datetime.now().isoformat(),
        "schema_test": test_schema(),
        "template_tests": test_gpt_template_scenarios(),
        "accuracy_analysis": analyze_gpt_response_accuracy(),
    }

    # Save report
    with open("gpt_actions_test_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✅ Report saved to: gpt_actions_test_report.json")

    # Summary
    print("\n🎯 Summary:")
    print(f"  Schema Accessible: {'✅' if report['schema_test'] else '❌'}")

    for scenario, results in report["template_tests"].items():
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        print(f"  {scenario}: {success_count}/{total_count} operations working")

    print(f"  Data Accuracy: {'✅' if report['accuracy_analysis'] else '❌'}")

    return report


if __name__ == "__main__":
    print("🚀 CryptoSatX GPT Actions Integration Test")
    print("=" * 50)

    # Run comprehensive test
    report = generate_gpt_actions_report()

    print("\n🔧 Next Steps:")
    print("1. If all tests pass: GPT Actions should work correctly")
    print("2. If schema fails: Check domain accessibility")
    print("3. If operations fail: Verify API endpoint status")
    print("4. Configure GPT Actions with schema URL:")
    print(f"   {SCHEMA_ENDPOINT}")
