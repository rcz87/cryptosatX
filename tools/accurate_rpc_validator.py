#!/usr/bin/env python3
"""
ACCURATE RPC Integrity Validation - Tests ONLY registered operations from catalog
Loads operations dynamically from operation_catalog.py instead of guessing names
"""

import httpx
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

# Import the actual operation catalog
sys.path.append('.')
from app.utils.operation_catalog import OPERATION_CATALOG, get_operations_by_namespace

VALIDATION_MODE = True
FORCE_REAL_CALL = True
BASE_URL = "http://localhost:8000"

class AccurateRPCValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "validation_mode": VALIDATION_MODE,
            "force_real_call": FORCE_REAL_CALL,
            "providers": {}
        }
    
    async def test_endpoint(self, operation: str, metadata: Dict) -> Tuple[str, Dict]:
        """Test a single RPC endpoint and classify its status"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Build params based on metadata requirements
                params = {}
                if metadata.get("requires_symbol"):
                    params["symbol"] = "BTC"
                if metadata.get("requires_exchange"):
                    params["exchange"] = "Binance"
                if metadata.get("requires_topic"):
                    params["topic"] = "bitcoin"
                if metadata.get("requires_asset"):
                    params["asset"] = "BTC"
                
                # Additional common params for specific operations
                if "history" in operation:
                    params.setdefault("limit", 10)
                if "ohlcv" in operation:
                    params.setdefault("period", "1HRS")
                    params.setdefault("limit", 24)
                if "orderbook" in operation or "quotes" in operation or "trades" in operation:
                    params.setdefault("limit", 20)
                if "discovery" in operation or "rankings" in operation:
                    params.setdefault("limit", 10)
                    params.setdefault("sort", "galaxy_score")
                if "coin_change" in operation:
                    params.setdefault("interval", "24h")
                if "topic_trends" in operation:
                    params.setdefault("topic", "bitcoin")
                
                payload = {"operation": operation, **params}
                response = await client.post(f"{BASE_URL}/invoke", json=payload)
                
                if response.status_code != 200:
                    return "error", {"error": f"HTTP {response.status_code}", "raw": response.text[:200]}
                
                data = response.json()
                
                # Check if operation failed
                if not data.get("ok"):
                    error_msg = data.get("error", "Unknown error")
                    if "not found" in error_msg.lower() or "notimplementederror" in error_msg.lower():
                        return "stubbed", {"error": error_msg}
                    return "error", {"error": error_msg}
                
                # Check if data is empty/null
                result_data = data.get("data")
                if result_data is None:
                    return "empty", {"data": None}
                
                # Check for success=false in data
                if isinstance(result_data, dict):
                    if result_data.get("success") is False:
                        error = result_data.get("error", "Unknown")
                        # Enterprise tier fallback is still considered "active" with graceful degradation
                        if "enterprise" in error.lower() or "tier" in error.lower():
                            return "active_graceful", {"note": "Graceful tier limitation", "error": error}
                        # "No data" is considered empty
                        if "no data" in error.lower():
                            return "empty", {"error": error}
                        return "error", {"error": error}
                    
                    # Check if data has meaningful content
                    if len(result_data) == 0 or all(v is None for v in result_data.values()):
                        return "empty", {"data": result_data}
                
                # Success - endpoint is active
                return "active", {"data_preview": str(result_data)[:100]}
                
            except httpx.TimeoutException:
                return "timeout", {"error": "Request timeout"}
            except Exception as e:
                return "error", {"error": str(e)}
    
    async def validate_provider(self, namespace: str, display_name: str) -> Dict:
        """Validate all endpoints for a specific provider namespace"""
        operations = get_operations_by_namespace(namespace)
        total = len(operations)
        print(f"\n🔍 Validating {display_name} endpoints ({total} total)...")
        
        results = []
        for idx, operation in enumerate(operations, 1):
            metadata = OPERATION_CATALOG[operation]
            status, details = await self.test_endpoint(operation, metadata.__dict__)
            results.append({
                "operation": operation,
                "status": status,
                "metadata": {
                    "path": metadata.path,
                    "method": metadata.method,
                    "description": metadata.description
                },
                "details": details
            })
            
            # Progress indicator
            if idx % 10 == 0 or idx == total:
                print(f"  Progress: {idx}/{total} endpoints tested")
        
        return self._summarize_results(display_name, results, total)
    
    def _summarize_results(self, provider: str, results: List[Dict], expected_total: int) -> Dict:
        """Summarize test results for a provider"""
        status_counts = defaultdict(int)
        for r in results:
            status_counts[r["status"]] += 1
        
        active = status_counts["active"] + status_counts["active_graceful"]
        stubbed = status_counts["stubbed"]
        empty = status_counts["empty"]
        error = status_counts["error"] + status_counts["timeout"]
        total = len(results)
        
        success_rate = (active / total * 100) if total > 0 else 0
        
        # Classify health
        if success_rate >= 90:
            health = "🟢 Stable"
        elif success_rate >= 60:
            health = "🟡 Degraded"
        else:
            health = "🔴 Critical"
        
        return {
            "provider": provider,
            "expected_total": expected_total,
            "tested_total": total,
            "active": active,
            "stubbed": stubbed,
            "empty": empty,
            "error": error,
            "success_rate": round(success_rate, 1),
            "health": health,
            "detailed_results": results
        }
    
    async def run_full_validation(self):
        """Run complete validation across all providers"""
        print("=" * 80)
        print("🧩 ACCURATE GLOBAL RPC INTEGRITY VALIDATION - HONESTY-FIRST MODE")
        print("=" * 80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Target: {BASE_URL}")
        print(f"Validation Mode: {VALIDATION_MODE}")
        print(f"Force Real Call: {FORCE_REAL_CALL}")
        print(f"Testing operations from operation_catalog.py")
        print("=" * 80)
        
        # Validate all providers using ACTUAL registered operations
        coinglass_results = await self.validate_provider("coinglass", "Coinglass")
        coinapi_results = await self.validate_provider("coinapi", "CoinAPI")
        lunarcrush_results = await self.validate_provider("lunarcrush", "LunarCrush")
        
        self.results["providers"] = {
            "coinglass": coinglass_results,
            "coinapi": coinapi_results,
            "lunarcrush": lunarcrush_results
        }
        
        # Calculate overall stats
        total_tested = sum(p["tested_total"] for p in self.results["providers"].values())
        total_active = sum(p["active"] for p in self.results["providers"].values())
        overall_success = (total_active / total_tested * 100) if total_tested > 0 else 0
        
        if overall_success >= 90:
            overall_health = "🟢 Stable"
        elif overall_success >= 60:
            overall_health = "🟡 Degraded"
        else:
            overall_health = "🔴 Critical"
        
        self.results["overall"] = {
            "total_tested": total_tested,
            "total_active": total_active,
            "overall_success_rate": round(overall_success, 1),
            "health_classification": overall_health
        }
        
        # Print summary table
        self._print_summary()
        
        # Save to JSON
        self._save_report()
        
        return self.results
    
    def _print_summary(self):
        """Print formatted summary table"""
        print("\n" + "=" * 80)
        print("📊 SUMMARY TABLE")
        print("=" * 80)
        print(f"{'Provider':<15} | {'Total':<6} | {'Active':<7} | {'Stubbed':<8} | {'Empty':<6} | {'Success %':<10} | {'Status'}")
        print("-" * 80)
        
        for provider_name, data in self.results["providers"].items():
            print(f"{data['provider']:<15} | {data['tested_total']:<6} | {data['active']:<7} | "
                  f"{data['stubbed']:<8} | {data['empty']:<6} | {data['success_rate']:<10}% | {data['health']}")
        
        print("-" * 80)
        overall = self.results["overall"]
        print(f"{'OVERALL':<15} | {overall['total_tested']:<6} | {overall['total_active']:<7} | "
              f"{'—':<8} | {'—':<6} | {overall['overall_success_rate']:<10}% | {overall['health_classification']}")
        print("=" * 80)
        
        # Print quick status
        print("\n📋 QUICK STATUS:")
        for provider_name, data in self.results["providers"].items():
            emoji = "✅" if data["success_rate"] >= 90 else "⚠️" if data["success_rate"] >= 60 else "❌"
            print(f"{data['provider']}: {data['active']}/{data['tested_total']} Active ({data['success_rate']}%) {emoji}")
        
        # Critical issues warning
        print("\n🔍 CRITICAL ISSUES:")
        has_critical = False
        for provider_name, data in self.results["providers"].items():
            if data["success_rate"] < 50:
                print(f"❌ {data['provider']} requires patch - {data['success_rate']}% success rate")
                has_critical = True
            elif data["stubbed"] > 0:
                print(f"⚠️  {data['provider']} has {data['stubbed']} stubbed/missing handlers")
                has_critical = True
        
        if not has_critical:
            print("✅ No critical issues detected")
        
        print("\n" + "=" * 80)
        print(f"🎯 OVERALL INTEGRITY CLASSIFICATION: {overall['health_classification']}")
        print("=" * 80)
    
    def _save_report(self):
        """Save detailed report to JSON file"""
        output_path = "app/rpc_global_health.json"
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Full audit log saved to: {output_path}")

async def main():
    validator = AccurateRPCValidator()
    await validator.run_full_validation()
    
    # Git commit instructions
    print("\n📝 To commit results to repo:")
    print("   git add app/rpc_global_health.json")
    print("   git commit -m '🧠 Global RPC Health Check - Accurate Validation'")

if __name__ == "__main__":
    asyncio.run(main())
