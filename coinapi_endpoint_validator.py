#!/usr/bin/env python3
"""
CoinAPI RPC Integrity Validator
SYSTEM DIRECTIVE: Test EVERY CoinAPI endpoint with real RPC calls.
Never claim "all working" without actual execution proof.
"""

import json
import requests
from typing import Dict, List

# CoinAPI operations from catalog (7 total)
COINAPI_ENDPOINTS = [
    "coinapi.ohlcv.latest",
    "coinapi.ohlcv.historical",
    "coinapi.orderbook",
    "coinapi.trades",
    "coinapi.quote",
    "coinapi.multi_exchange",
    "coinapi.dashboard",
]

def test_endpoint(operation: str, symbol: str = "BTC") -> Dict:
    """
    Execute REAL RPC call and validate response.
    Returns: {"endpoint": str, "status": str, "error": str (optional)}
    """
    try:
        payload = {"operation": operation, "symbol": symbol}
        response = requests.post(
            "http://localhost:8000/invoke",
            json=payload,
            timeout=15
        )
        data = response.json()
        
        # Check if operation succeeded
        if data.get("ok"):
            # Additional validation: check if result has actual data
            result = data.get("result", {})
            if result and isinstance(result, dict):
                return {
                    "endpoint": operation,
                    "status": "✅ ACTIVE",
                    "response_keys": list(result.keys())[:5] if result else []
                }
            elif result:
                return {
                    "endpoint": operation,
                    "status": "✅ ACTIVE",
                    "response_type": str(type(result).__name__)
                }
            else:
                return {
                    "endpoint": operation,
                    "status": "⚠️ EMPTY_RESPONSE",
                    "error": "Handler returned empty/null result"
                }
        else:
            # Extract error message
            error_obj = data.get("error", {})
            if isinstance(error_obj, dict):
                error_msg = error_obj.get("message", str(error_obj))
            else:
                error_msg = str(error_obj)
            
            # Classify error type
            if "NotImplementedError" in error_msg or "not implemented" in error_msg.lower():
                return {
                    "endpoint": operation,
                    "status": "⚠️ STUBBED",
                    "error": "Handler not implemented yet"
                }
            elif "TypeError" in error_msg:
                return {
                    "endpoint": operation,
                    "status": "⚠️ STUBBED",
                    "error": f"TypeError: {error_msg[:100]}"
                }
            elif "NoneType" in error_msg:
                return {
                    "endpoint": operation,
                    "status": "⚠️ STUBBED",
                    "error": f"NoneType error: {error_msg[:100]}"
                }
            elif "Premium" in error_msg or "Forbidden" in error_msg:
                return {
                    "endpoint": operation,
                    "status": "🔒 PREMIUM",
                    "error": "Requires premium subscription"
                }
            elif "Missing required parameter" in error_msg:
                return {
                    "endpoint": operation,
                    "status": "⚠️ PARAM_ERROR",
                    "error": error_msg[:120]
                }
            else:
                return {
                    "endpoint": operation,
                    "status": "⚠️ ERROR",
                    "error": error_msg[:120]
                }
                
    except requests.exceptions.Timeout:
        return {
            "endpoint": operation,
            "status": "⚠️ TIMEOUT",
            "error": "Request timeout after 15s"
        }
    except Exception as e:
        return {
            "endpoint": operation,
            "status": "⚠️ FAILED",
            "error": str(e)[:120]
        }

def main():
    print("=" * 70)
    print("🔍 CoinAPI RPC INTEGRITY VALIDATOR")
    print("=" * 70)
    print(f"Testing {len(COINAPI_ENDPOINTS)} endpoints with REAL execution...\n")
    
    results = []
    
    for operation in COINAPI_ENDPOINTS:
        print(f"Testing: {operation}...", end=" ")
        result = test_endpoint(operation, symbol="BTC")
        results.append(result)
        
        # Print immediate feedback
        status = result["status"]
        print(status)
        if "error" in result:
            print(f"  └─ {result['error']}")
    
    # Calculate statistics
    total = len(results)
    active = sum(1 for r in results if "✅ ACTIVE" in r["status"])
    stubbed = sum(1 for r in results if "⚠️ STUBBED" in r["status"])
    empty = sum(1 for r in results if "⚠️ EMPTY" in r["status"])
    premium = sum(1 for r in results if "🔒 PREMIUM" in r["status"])
    error = sum(1 for r in results if "⚠️ ERROR" in r["status"] or "⚠️ FAILED" in r["status"])
    param_error = sum(1 for r in results if "⚠️ PARAM_ERROR" in r["status"])
    timeout = sum(1 for r in results if "⚠️ TIMEOUT" in r["status"])
    
    # Success rate
    success_rate = (active / total * 100) if total > 0 else 0
    
    # Save results to JSON
    output = {
        "timestamp": "2025-11-13T14:59:00Z",
        "validation_mode": "HONESTY_FIRST",
        "total_endpoints": total,
        "statistics": {
            "active": active,
            "stubbed": stubbed,
            "empty_response": empty,
            "premium_only": premium,
            "parameter_error": param_error,
            "timeout": timeout,
            "other_errors": error,
            "success_rate_percent": round(success_rate, 1)
        },
        "results": results
    }
    
    with open("coinapi_health.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total Endpoints Tested: {total}")
    print(f"✅ Active & Working:    {active}")
    print(f"⚠️  Stubbed/NotImpl:     {stubbed}")
    print(f"⚠️  Empty Response:      {empty}")
    print(f"⚠️  Parameter Errors:    {param_error}")
    print(f"⚠️  Other Errors:        {error}")
    print(f"⚠️  Timeout:             {timeout}")
    print(f"🔒 Premium Only:        {premium}")
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    print("=" * 70)
    
    # List inactive endpoints
    inactive = [r for r in results if "✅ ACTIVE" not in r["status"]]
    if inactive:
        print("\n⚠️  INACTIVE/STUBBED ENDPOINTS:")
        for r in inactive:
            print(f"  • {r['endpoint']}")
            print(f"    Status: {r['status']}")
            if "error" in r:
                print(f"    Error: {r['error']}")
    else:
        print("\n✅ ALL ENDPOINTS VERIFIED ACTIVE!")
    
    print(f"\n📁 Audit report saved to: coinapi_health.json")
    print("\n👉 HONESTY-FIRST MODE: All claims verified by actual execution.")
    
    return success_rate == 100.0

if __name__ == "__main__":
    all_active = main()
    exit(0 if all_active else 1)
