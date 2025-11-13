#!/usr/bin/env python3
"""
Test script for Advanced Analytics endpoints
Tests ML-powered pattern recognition and performance optimization
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000"
TEST_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "ADA"]


class AdvancedAnalyticsTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []

    async def test_endpoint(self, endpoint: str, description: str) -> Dict:
        """Test a single endpoint and return results"""
        start_time = time.time()

        try:
            response = await self.client.get(f"{self.base_url}{endpoint}")
            response_time = time.time() - start_time

            result = {
                "endpoint": endpoint,
                "description": description,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
                "data": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
            }

            print(f"✅ {description}: {response.status_code} ({response_time:.2f}s)")

        except Exception as e:
            result = {
                "endpoint": endpoint,
                "description": description,
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e),
            }

            print(f"❌ {description}: {str(e)}")

        self.test_results.append(result)
        return result

    async def test_pattern_recognition(self):
        """Test chart pattern recognition endpoints"""
        print("\n🔍 Testing Pattern Recognition Endpoints")
        print("=" * 50)

        # Test single symbol pattern detection
        await self.test_endpoint(
            "/analytics/patterns/BTC?timeframe=1h",
            "Single Symbol Pattern Detection (BTC)",
        )

        # Test batch pattern detection
        symbols_param = "&".join([f"symbols={symbol}" for symbol in TEST_SYMBOLS[:3]])
        await self.test_endpoint(
            f"/analytics/patterns/batch?{symbols_param}&timeframe=1h",
            "Batch Pattern Detection",
        )

        # Test different timeframes
        for timeframe in ["5m", "15m", "1h", "4h"]:
            await self.test_endpoint(
                f"/analytics/patterns/ETH?timeframe={timeframe}",
                f"Pattern Detection - {timeframe} timeframe",
            )

    async def test_predictive_analytics(self):
        """Test predictive analytics endpoints"""
        print("\n🤖 Testing Predictive Analytics Endpoints")
        print("=" * 50)

        # Test price prediction
        for horizon in ["1h", "4h", "24h", "7d"]:
            await self.test_endpoint(
                f"/analytics/prediction/BTC?horizon={horizon}",
                f"Price Prediction - {horizon} horizon",
            )

        # Test sentiment analysis
        for symbol in TEST_SYMBOLS[:3]:
            await self.test_endpoint(
                f"/analytics/sentiment/{symbol}", f"Sentiment Analysis - {symbol}"
            )

        # Test anomaly detection
        await self.test_endpoint("/analytics/anomalies/BTC", "Anomaly Detection - BTC")

    async def test_comprehensive_analysis(self):
        """Test comprehensive analysis endpoints"""
        print("\n📊 Testing Comprehensive Analysis Endpoints")
        print("=" * 50)

        # Test comprehensive analysis for different symbols
        for symbol in TEST_SYMBOLS[:2]:
            await self.test_endpoint(
                f"/analytics/comprehensive/{symbol}?timeframe=1h&horizon=24h",
                f"Comprehensive Analysis - {symbol}",
            )

    async def test_performance_optimization(self):
        """Test performance optimization endpoints"""
        print("\n⚡ Testing Performance Optimization Endpoints")
        print("=" * 50)

        # Test system metrics
        await self.test_endpoint(
            "/analytics/performance/metrics", "System Performance Metrics"
        )

        # Test cache metrics
        await self.test_endpoint(
            "/analytics/performance/cache", "Cache Performance Metrics"
        )

        # Test auto-scale recommendations
        await self.test_endpoint(
            "/analytics/performance/recommendations", "Auto-scale Recommendations"
        )

        # Test load balancing
        test_servers = ["server1", "server2", "server3"]
        servers_param = "&".join([f"servers={server}" for server in test_servers])
        await self.test_endpoint(
            f"/analytics/performance/load-balance?{servers_param}",
            "Load Balancing Test",
        )

        # Test rate limiting
        await self.test_endpoint(
            "/analytics/performance/rate-limit/test_client?limit=10&window=60",
            "Rate Limiting Test",
        )

    async def test_cache_operations(self):
        """Test cache operations"""
        print("\n💾 Testing Cache Operations")
        print("=" * 50)

        # Test cache invalidation
        await self.test_endpoint(
            "/analytics/performance/cache/invalidate?pattern=analytics:*",
            "Cache Invalidation",
        )

        # Test response optimization
        test_data = {"test": "data", "numbers": [1, 2, 3, 4, 5]}
        await self.client.post(
            f"{self.base_url}/analytics/optimize-response?endpoint=/test",
            json=test_data,
        )
        print("✅ Response Optimization Test")

    async def test_health_checks(self):
        """Test health check endpoints"""
        print("\n🏥 Testing Health Check Endpoints")
        print("=" * 50)

        await self.test_endpoint(
            "/analytics/health/analytics", "Analytics Health Check"
        )

    async def test_caching_behavior(self):
        """Test caching behavior by making repeated requests"""
        print("\n🔄 Testing Caching Behavior")
        print("=" * 50)

        endpoint = "/analytics/patterns/BTC?timeframe=1h"

        # First request (should be slower)
        start_time = time.time()
        await self.test_endpoint(endpoint, "First Request (Cache Miss)")
        first_time = time.time() - start_time

        # Second request (should be faster due to cache)
        start_time = time.time()
        await self.test_endpoint(endpoint, "Second Request (Cache Hit)")
        second_time = time.time() - start_time

        # Third request (should also be fast)
        start_time = time.time()
        await self.test_endpoint(endpoint, "Third Request (Cache Hit)")
        third_time = time.time() - start_time

        print(f"\n📈 Caching Performance Analysis:")
        print(f"   First request:  {first_time:.3f}s")
        print(f"   Second request: {second_time:.3f}s")
        print(f"   Third request:  {third_time:.3f}s")

        if second_time < first_time * 0.8:
            print("   ✅ Caching appears to be working correctly")
        else:
            print("   ⚠️  Caching may not be working as expected")

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Advanced Analytics API Tests")
        print("=" * 60)

        start_time = time.time()

        try:
            # Run all test suites
            await self.test_health_checks()
            await self.test_pattern_recognition()
            await self.test_predictive_analytics()
            await self.test_comprehensive_analysis()
            await self.test_performance_optimization()
            await self.test_cache_operations()
            await self.test_caching_behavior()

        except Exception as e:
            print(f"❌ Test suite failed: {e}")

        total_time = time.time() - start_time

        # Generate summary report
        self.generate_summary_report(total_time)

    def generate_summary_report(self, total_time: float):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 60)
        print("📊 ADVANCED ANALYTICS TEST SUMMARY REPORT")
        print("=" * 60)

        successful_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]

        print(f"Total Tests: {len(self.test_results)}")
        print(f"Successful: {len(successful_tests)} ✅")
        print(f"Failed: {len(failed_tests)} ❌")
        print(
            f"Success Rate: {(len(successful_tests) / len(self.test_results) * 100):.1f}%"
        )
        print(f"Total Time: {total_time:.2f}s")

        if successful_tests:
            avg_response_time = sum(r["response_time"] for r in successful_tests) / len(
                successful_tests
            )
            print(f"Average Response Time: {avg_response_time:.3f}s")

            fastest_test = min(successful_tests, key=lambda x: x["response_time"])
            slowest_test = max(successful_tests, key=lambda x: x["response_time"])

            print(
                f"Fastest Test: {fastest_test['description']} ({fastest_test['response_time']:.3f}s)"
            )
            print(
                f"Slowest Test: {slowest_test['description']} ({slowest_test['response_time']:.3f}s)"
            )

        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(
                    f"   • {test['description']}: {test.get('error', 'Unknown error')}"
                )

        # Performance analysis
        print("\n📈 Performance Analysis:")
        response_times = [r["response_time"] for r in successful_tests]
        if response_times:
            print(f"   Min Response Time: {min(response_times):.3f}s")
            print(f"   Max Response Time: {max(response_times):.3f}s")
            print(
                f"   Median Response Time: {sorted(response_times)[len(response_times)//2]:.3f}s"
            )

        # Feature coverage
        print("\n🔧 Feature Coverage:")
        features_tested = set()
        for test in self.test_results:
            if "pattern" in test["endpoint"].lower():
                features_tested.add("Pattern Recognition")
            elif "prediction" in test["endpoint"].lower():
                features_tested.add("Predictive Analytics")
            elif "sentiment" in test["endpoint"].lower():
                features_tested.add("Sentiment Analysis")
            elif "anomalies" in test["endpoint"].lower():
                features_tested.add("Anomaly Detection")
            elif "performance" in test["endpoint"].lower():
                features_tested.add("Performance Optimization")
            elif "cache" in test["endpoint"].lower():
                features_tested.add("Caching System")

        for feature in sorted(features_tested):
            print(f"   ✅ {feature}")

        print("\n" + "=" * 60)

        # Save detailed report
        self.save_detailed_report()

    def save_detailed_report(self):
        """Save detailed test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"advanced_analytics_test_report_{timestamp}.json"

        report_data = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": len(self.test_results),
                "successful": len([r for r in self.test_results if r["success"]]),
                "failed": len([r for r in self.test_results if not r["success"]]),
                "success_rate": len([r for r in self.test_results if r["success"]])
                / len(self.test_results)
                * 100,
            },
            "test_results": self.test_results,
        }

        try:
            with open(filename, "w") as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"📄 Detailed report saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save detailed report: {e}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Main test runner"""
    tester = AdvancedAnalyticsTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
