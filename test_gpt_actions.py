"""
GPT Actions Integration Test Suite
Tests endpoints for GPT Actions compatibility including response size validation
"""

import asyncio
import json
import sys
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
import os

# Use localhost for development testing, production URL for deployed testing
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
MAX_RESPONSE_SIZE = 50 * 1024
TIMEOUT = 60.0

class GPTActionsTestSuite:
    """Test suite for GPT Actions integration"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def test_endpoint(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """Test a single endpoint and check response size"""
        url = f"{self.base_url}{path}"

        print(f"\n{'='*80}")
        print(f"Testing: {description or path}")
        print(f"Method: {method.upper()} {path}")
        if data:
            print(f"Payload: {json.dumps(data, indent=2)}")
        print(f"{'='*80}")

        result = {
            "endpoint": path,
            "method": method,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "response_size_bytes": 0,
            "response_size_kb": 0.0,
            "within_limit": False,
            "status_code": None,
            "error": None,
            "response_time_ms": 0
        }

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                start_time = asyncio.get_event_loop().time()

                if method.lower() == "get":
                    response = await client.get(url)
                else:
                    response = await client.post(url, json=data or {})

                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000

                result["status_code"] = response.status_code
                result["response_time_ms"] = round(response_time, 2)

                response_text = response.text
                response_size = len(response_text.encode('utf-8'))

                result["response_size_bytes"] = response_size
                result["response_size_kb"] = round(response_size / 1024, 2)
                result["within_limit"] = response_size <= MAX_RESPONSE_SIZE
                result["success"] = response.status_code == 200

                try:
                    result["response_preview"] = response.json()
                except:
                    result["response_preview"] = response_text[:200] + "..." if len(response_text) > 200 else response_text

                print(f"✅ Status: {response.status_code}")
                print(f"⏱️  Response Time: {result['response_time_ms']} ms")
                print(f"📊 Response Size: {result['response_size_kb']} KB ({result['response_size_bytes']} bytes)")

                if result["within_limit"]:
                    print(f"✅ Size Check: PASSED (< 50KB)")
                else:
                    print(f"❌ Size Check: FAILED (exceeds 50KB limit)")
                    print(f"⚠️  Size exceeds limit by {result['response_size_kb'] - 50:.2f} KB")

        except httpx.TimeoutException:
            result["error"] = "Request timeout"
            print(f"❌ Error: Request timeout ({TIMEOUT}s)")
        except httpx.ConnectError as e:
            result["error"] = f"Connection error: {str(e)}"
            print(f"❌ Error: Cannot connect to server - {str(e)}")
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error: {str(e)}")

        self.results.append(result)
        return result

    async def test_scalping_gpt_mode_regression(self):
        """
        REGRESSION TEST: Verify scalping endpoints stay under GPT Actions 50KB limit
        
        This test will FAIL if response sizes exceed limits, preventing regressions.
        Limits:
        - /scalping/analyze (gpt_mode=true): < 45 KB
        - /scalping/quick: < 40 KB
        """
        print("\n" + "="*80)
        print("🔒 REGRESSION TEST: GPT Mode Size Limits")
        print("="*80)
        print("Testing scalping endpoints with strict size assertions...")
        print("="*80)
        
        # Test 1: Scalping Analyze with GPT Mode
        print("\n📊 Test 1: /scalping/analyze (gpt_mode=true)")
        print("-" * 80)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/scalping/analyze",
                json={
                    "symbol": "ETH",
                    "mode": "aggressive",
                    "include_smart_money": True,
                    "include_fear_greed": True,
                    "gpt_mode": True  # Critical: GPT mode enabled
                }
            )
            
            size_bytes = len(response.text.encode('utf-8'))
            size_kb = size_bytes / 1024
            limit_kb = 45
            
            print(f"Status: {response.status_code}")
            print(f"Response Size: {size_kb:.2f} KB ({size_bytes} bytes)")
            print(f"Limit: < {limit_kb} KB")
            
            if size_kb < limit_kb:
                print(f"✅ PASS - Size is {limit_kb - size_kb:.2f} KB under limit")
            else:
                print(f"❌ FAIL - Size exceeds limit by {size_kb - limit_kb:.2f} KB!")
                print(f"\n⚠️  REGRESSION DETECTED!")
                print(f"Expected: < {limit_kb} KB")
                print(f"Actual: {size_kb:.2f} KB")
                print(f"This endpoint must be optimized before deployment!")
                raise AssertionError(
                    f"/scalping/analyze response size ({size_kb:.2f} KB) exceeds "
                    f"GPT Actions limit of {limit_kb} KB by {size_kb - limit_kb:.2f} KB"
                )
        
        # Test 2: Scalping Quick (auto gpt_mode)
        print("\n📊 Test 2: /scalping/quick/BTC (auto gpt_mode)")
        print("-" * 80)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{self.base_url}/scalping/quick/BTC")
            
            size_bytes = len(response.text.encode('utf-8'))
            size_kb = size_bytes / 1024
            limit_kb = 40
            
            print(f"Status: {response.status_code}")
            print(f"Response Size: {size_kb:.2f} KB ({size_bytes} bytes)")
            print(f"Limit: < {limit_kb} KB")
            
            if size_kb < limit_kb:
                print(f"✅ PASS - Size is {limit_kb - size_kb:.2f} KB under limit")
            else:
                print(f"❌ FAIL - Size exceeds limit by {size_kb - limit_kb:.2f} KB!")
                print(f"\n⚠️  REGRESSION DETECTED!")
                print(f"Expected: < {limit_kb} KB")
                print(f"Actual: {size_kb:.2f} KB")
                print(f"This endpoint must be optimized before deployment!")
                raise AssertionError(
                    f"/scalping/quick response size ({size_kb:.2f} KB) exceeds "
                    f"GPT Actions limit of {limit_kb} KB by {size_kb - limit_kb:.2f} KB"
                )
        
        print("\n" + "="*80)
        print("✅ REGRESSION TEST PASSED - All scalping endpoints within size limits")
        print("="*80)

    async def run_all_tests(self):
        """Run all GPT Actions endpoint tests"""

        print("\n" + "="*80)
        print("🤖 GPT ACTIONS INTEGRATION TEST SUITE")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Max Response Size: 50KB ({MAX_RESPONSE_SIZE} bytes)")
        print(f"Timeout: {TIMEOUT}s")
        print("="*80)

        await self.test_endpoint(
            "GET",
            "/gpt/health",
            description="GPT Actions Health Check"
        )

        await self.test_endpoint(
            "POST",
            "/gpt/signal",
            data={"symbol": "BTC", "debug": False},
            description="Get Trading Signal (BTC)"
        )

        await self.test_endpoint(
            "POST",
            "/gpt/smart-money-scan",
            data={"min_accumulation_score": 5},
            description="Smart Money Accumulation Scan"
        )

        await self.test_endpoint(
            "POST",
            "/gpt/mss-discover",
            data={"min_mss_score": 75, "max_results": 10},
            description="MSS Discovery (Emerging Cryptocurrencies)"
        )

        await self.test_endpoint(
            "GET",
            "/scalping/quick/BTC",
            description="Quick Scalping Analysis (BTC)"
        )

        await self.test_endpoint(
            "POST",
            "/scalping/analyze",
            data={
                "symbol": "ETH",
                "mode": "aggressive",
                "include_smart_money": True,
                "include_fear_greed": True,
                "gpt_mode": True
            },
            description="Complete Scalping Analysis (ETH) - GPT Optimized"
        )

        await self.test_endpoint(
            "POST",
            "/invoke",
            data={
                "operation": "signals.get",
                "symbol": "SOL"
            },
            description="Unified RPC - Get Signal (SOL)"
        )

        await self.test_endpoint(
            "POST",
            "/invoke",
            data={
                "operation": "coinglass.liquidation.aggregated_history",
                "symbol": "BTC",
                "interval": "1h"
            },
            description="Unified RPC - Liquidation History"
        )

        await self.test_endpoint(
            "GET",
            "/analytics/history/latest?limit=5",
            description="Analytics - Latest 5 Signals"
        )

        await self.test_endpoint(
            "GET",
            "/openapi-gpt.json",
            description="Optimized OpenAPI Schema for GPT Actions (< 45KB)"
        )

        # Run regression tests with strict size assertions
        await self.test_scalping_gpt_mode_regression()

        self.generate_report()

    def generate_report(self):
        """Generate test summary report"""
        print("\n\n" + "="*80)
        print("📊 TEST SUMMARY REPORT")
        print("="*80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        within_limit = sum(1 for r in self.results if r["within_limit"])
        exceeded_limit = total - within_limit

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"\n📊 Response Size Checks:")
        print(f"✅ Within 50KB Limit: {within_limit}")
        print(f"❌ Exceeded Limit: {exceeded_limit}")

        if exceeded_limit > 0:
            print(f"\n⚠️  WARNING: {exceeded_limit} endpoint(s) exceed 50KB GPT Actions limit!")
            print("\nEndpoints exceeding limit:")
            for r in self.results:
                if not r["within_limit"] and r["success"]:
                    print(f"  - {r['endpoint']}: {r['response_size_kb']} KB")

        successful_results = [r for r in self.results if r["success"]]
        if successful_results:
            avg_response_time = sum(r["response_time_ms"] for r in successful_results) / len(successful_results)
            avg_response_size = sum(r["response_size_kb"] for r in successful_results) / len(successful_results)

            print(f"\n⏱️  Performance Metrics:")
            print(f"Average Response Time: {avg_response_time:.2f} ms")
            print(f"Average Response Size: {avg_response_size:.2f} KB")

        output_file = "gpt_actions_test_results.json"
        with open(output_file, "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": failed,
                    "within_size_limit": within_limit,
                    "exceeded_size_limit": exceeded_limit,
                    "test_date": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2)

        print(f"\n💾 Detailed results saved to: {output_file}")
        print("="*80 + "\n")

        return 0 if failed == 0 and exceeded_limit == 0 else 1

async def main():
    """Main test execution"""
    suite = GPTActionsTestSuite(base_url=BASE_URL)
    await suite.run_all_tests()
    return suite.generate_report()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)
