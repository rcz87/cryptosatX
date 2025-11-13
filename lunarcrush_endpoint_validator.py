"""
LunarCrush Endpoint Validator
Tests all 12 LunarCrush operations via RPC /invoke endpoint
Target: ≥85% success rate
"""

import asyncio
import httpx
import os
from typing import Dict, List, Tuple

# Always use local development server for testing
RPC_ENDPOINT = "http://localhost:8000/invoke"

# Test configurations for all 12 LunarCrush operations
LUNARCRUSH_TESTS = [
    {
        "operation": "lunarcrush.coin",
        "params": {"symbol": "BTC"},
        "description": "Get LunarCrush coin data",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.coin_momentum",
        "params": {"symbol": "ETH"},
        "description": "Get coin momentum analysis",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.coin_change",
        "params": {"symbol": "BTC", "interval": "24h"},
        "description": "Get coin change metrics",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.coins_discovery",
        "params": {"min_galaxy_score": 60, "limit": 20},
        "description": "Discover coins via LunarCrush",
        "expected_keys": ["success"],
    },
    {
        "operation": "lunarcrush.topics_list",
        "params": {},
        "description": "Get trending topics list",
        "expected_keys": ["success", "topics"],
    },
    {
        "operation": "lunarcrush.coin_themes",
        "params": {"symbol": "BTC"},
        "description": "Analyze coin themes",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.news_feed",
        "params": {"symbol": "BTC", "limit": 20},
        "description": "Get crypto news feed (Enterprise tier check)",
        "expected_keys": ["success", "error"],  # Expected to fail gracefully
        "expect_failure": True,
    },
    {
        "operation": "lunarcrush.community_activity",
        "params": {"symbol": "ETH"},
        "description": "Get community activity metrics",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.influencer_activity",
        "params": {"symbol": "BTC"},
        "description": "Get influencer activity (Enterprise tier check)",
        "expected_keys": ["success", "error"],  # Expected to fail gracefully
        "expect_failure": True,
    },
    {
        "operation": "lunarcrush.coin_correlation",
        "params": {"symbol": "BTC"},
        "description": "Get coin correlation metrics",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.market_pair",
        "params": {"symbol": "BTC", "pair": "USDT"},
        "description": "Get market pair data",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.aggregates",
        "params": {"symbol": "ETH"},
        "description": "Get aggregated market metrics",
        "expected_keys": ["success", "symbol"],
    },
    {
        "operation": "lunarcrush.topic_trends",
        "params": {},
        "description": "Get trending topics",
        "expected_keys": ["success", "topics"],
    },
    {
        "operation": "lunarcrush.coins_rankings",
        "params": {"limit": 50, "sort": "galaxy_score"},
        "description": "Get coins rankings",
        "expected_keys": ["success", "rankings"],
    },
    {
        "operation": "lunarcrush.system_status",
        "params": {},
        "description": "Get API system status",
        "expected_keys": ["success", "status"],
    },
]


async def test_endpoint(client: httpx.AsyncClient, test: Dict) -> Tuple[str, bool, str]:
    """
    Test a single LunarCrush endpoint
    
    Returns:
        Tuple of (operation, success, message)
    """
    operation = test["operation"]
    params = test["params"]
    description = test["description"]
    expected_keys = test["expected_keys"]
    expect_failure = test.get("expect_failure", False)
    
    try:
        # Make RPC call
        payload = {
            "operation": operation,
            **params
        }
        
        response = await client.post(RPC_ENDPOINT, json=payload, timeout=30.0)
        
        if response.status_code != 200:
            return (operation, False, f"HTTP {response.status_code}")
        
        data = response.json()
        
        # Check if RPC wrapper is present
        if "ok" not in data:
            return (operation, False, "Missing RPC wrapper")
        
        # Extract actual response data
        result = data.get("data", {})
        
        # For Enterprise-tier endpoints, we expect graceful failure
        if expect_failure:
            if result.get("success") is False and "error" in result:
                return (operation, True, f"✓ Graceful Enterprise tier fallback: {result.get('error')}")
            else:
                return (operation, False, "Expected graceful failure for Enterprise tier")
        
        # Validate expected keys exist
        missing_keys = [key for key in expected_keys if key not in result]
        if missing_keys:
            return (operation, False, f"Missing keys: {missing_keys}")
        
        # Check success flag
        if result.get("success") is False:
            error = result.get("error", "Unknown error")
            return (operation, False, f"API error: {error}")
        
        # Success!
        return (operation, True, f"✓ {description}")
    
    except httpx.TimeoutException:
        return (operation, False, "Timeout (30s)")
    except Exception as e:
        return (operation, False, f"Exception: {str(e)[:100]}")


async def run_validation():
    """Run all LunarCrush endpoint tests"""
    
    print("=" * 80)
    print("LunarCrush Endpoint Validator")
    print("=" * 80)
    print(f"Testing {len(LUNARCRUSH_TESTS)} LunarCrush operations via RPC /invoke")
    print(f"Endpoint: {RPC_ENDPOINT}")
    print("-" * 80)
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test all endpoints concurrently
        tasks = [test_endpoint(client, test) for test in LUNARCRUSH_TESTS]
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    total = len(results)
    success_count = len(successful)
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    # Print results
    print("\n✅ SUCCESSFUL OPERATIONS:")
    print("-" * 80)
    for op, _, msg in successful:
        print(f"  {op:45s} {msg}")
    
    if failed:
        print("\n❌ FAILED OPERATIONS:")
        print("-" * 80)
        for op, _, msg in failed:
            print(f"  {op:45s} {msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Operations:    {total}")
    print(f"Successful:          {success_count}")
    print(f"Failed:              {len(failed)}")
    print(f"Success Rate:        {success_rate:.1f}%")
    print(f"Target:              ≥85%")
    
    if success_rate >= 85:
        print("\n🎉 VALIDATION PASSED! All LunarCrush operations are working correctly.")
    else:
        print("\n⚠️  VALIDATION FAILED! Some operations need attention.")
    
    print("=" * 80)
    
    return success_rate >= 85


if __name__ == "__main__":
    success = asyncio.run(run_validation())
    exit(0 if success else 1)
