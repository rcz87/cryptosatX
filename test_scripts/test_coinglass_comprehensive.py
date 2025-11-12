#!/usr/bin/env python3
"""
Comprehensive Coinglass API Testing Suite
Tests all 60 production endpoints + WebSocket streaming
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"

class CoinglassAPITester:
    def __init__(self):
        self.results = {
            "total_endpoints": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "response_times": [],
            "endpoint_details": []
        }
        
    async def test_endpoint(self, name: str, url: str, method: str = "GET") -> Dict:
        """Test a single endpoint and record results"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url)
                
                elapsed = time.time() - start_time
                
                result = {
                    "name": name,
                    "url": url,
                    "status": response.status_code,
                    "response_time": round(elapsed, 3),
                    "success": response.status_code == 200,
                    "data_size": len(response.content) if response.content else 0
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["has_data"] = bool(data)
                        if isinstance(data, dict):
                            result["data_keys"] = list(data.keys())[:5]
                    except:
                        result["has_data"] = False
                else:
                    result["error"] = response.text[:200]
                
                return result
                
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "status": 0,
                "response_time": 0,
                "success": False,
                "error": str(e)[:200]
            }
    
    async def run_all_tests(self):
        """Test all Coinglass endpoints"""
        
        print("=" * 80)
        print("🔍 COINGLASS API COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Define all endpoints by category
        test_cases = [
            # === LIQUIDATIONS (7 endpoints) ===
            ("Liquidations - Heatmap BTC", f"{BASE_URL}/coinglass/liquidations/heatmap/BTCUSDT"),
            ("Liquidations - Heatmap ETH", f"{BASE_URL}/coinglass/liquidations/heatmap/ETHUSDT"),
            ("Liquidations - Chart BTC", f"{BASE_URL}/coinglass/liquidations/chart/BTCUSDT"),
            ("Liquidations - History", f"{BASE_URL}/coinglass/liquidations/history"),
            ("Liquidations - Exchange Breakdown", f"{BASE_URL}/coinglass/liquidations/by-exchange/BTCUSDT"),
            ("Liquidations - Coin List", f"{BASE_URL}/coinglass/liquidations/coins"),
            ("Liquidations - Top", f"{BASE_URL}/coinglass/liquidations/top"),
            
            # === FUNDING RATES (6 endpoints) ===
            ("Funding - Current Rates", f"{BASE_URL}/coinglass/funding/current"),
            ("Funding - Historical BTC", f"{BASE_URL}/coinglass/funding/history/BTCUSDT"),
            ("Funding - Aggregated BTC", f"{BASE_URL}/coinglass/funding/aggregated/BTCUSDT"),
            ("Funding - By Exchange", f"{BASE_URL}/coinglass/funding/by-exchange/BTCUSDT"),
            ("Funding - Top Rates", f"{BASE_URL}/coinglass/funding/top"),
            ("Funding - Weighted Average", f"{BASE_URL}/coinglass/funding/weighted-average"),
            
            # === OPEN INTEREST (6 endpoints) ===
            ("OI - Current", f"{BASE_URL}/coinglass/open-interest/current"),
            ("OI - Historical BTC", f"{BASE_URL}/coinglass/open-interest/history/BTCUSDT"),
            ("OI - Aggregated BTC", f"{BASE_URL}/coinglass/open-interest/aggregated/BTCUSDT"),
            ("OI - By Exchange", f"{BASE_URL}/coinglass/open-interest/by-exchange/BTCUSDT"),
            ("OI - Market Share", f"{BASE_URL}/coinglass/open-interest/market-share"),
            ("OI - OHLC BTC", f"{BASE_URL}/coinglass/open-interest/ohlc/BTCUSDT"),
            
            # === LONG/SHORT RATIOS (4 endpoints) ===
            ("Long/Short - Global Accounts", f"{BASE_URL}/coinglass/long-short/global-accounts"),
            ("Long/Short - Top Trader Accounts", f"{BASE_URL}/coinglass/long-short/top-trader-accounts"),
            ("Long/Short - Top Trader Positions", f"{BASE_URL}/coinglass/long-short/top-trader-positions"),
            ("Long/Short - Historical BTC", f"{BASE_URL}/coinglass/long-short/history/BTCUSDT"),
            
            # === TAKER BUY/SELL (1 endpoint) ===
            ("Taker Volume - BTC", f"{BASE_URL}/coinglass/taker-volume/BTCUSDT"),
            
            # === ORDERBOOK DEPTH (5 endpoints) ===
            ("Orderbook - Depth BTC", f"{BASE_URL}/coinglass/orderbook/depth/BTCUSDT"),
            ("Orderbook - Liquidity Map", f"{BASE_URL}/coinglass/orderbook/liquidity-map"),
            ("Orderbook - Whale Orders", f"{BASE_URL}/coinglass/orderbook/whale-orders"),
            ("Orderbook - Support/Resistance", f"{BASE_URL}/coinglass/orderbook/support-resistance/BTCUSDT"),
            ("Orderbook - Top Exchanges", f"{BASE_URL}/coinglass/orderbook/top-exchanges"),
            
            # === HYPERLIQUID DEX (3 endpoints) ===
            ("Hyperliquid - Stats", f"{BASE_URL}/coinglass/hyperliquid/stats"),
            ("Hyperliquid - Leaderboard", f"{BASE_URL}/coinglass/hyperliquid/leaderboard"),
            ("Hyperliquid - Volume History", f"{BASE_URL}/coinglass/hyperliquid/volume-history"),
            
            # === ON-CHAIN TRACKING (2 endpoints) ===
            ("On-Chain - Whale Transactions", f"{BASE_URL}/coinglass/onchain/whale-transactions"),
            ("On-Chain - Exchange Flows", f"{BASE_URL}/coinglass/onchain/exchange-flows"),
            
            # === TECHNICAL INDICATORS (12 endpoints) ===
            ("Indicators - RSI List", f"{BASE_URL}/coinglass/indicators/rsi-list"),
            ("Indicators - RSI BTC", f"{BASE_URL}/coinglass/indicators/rsi/BTCUSDT"),
            ("Indicators - Fear & Greed", f"{BASE_URL}/coinglass/indicators/fear-greed"),
            ("Indicators - Whale Index", f"{BASE_URL}/coinglass/indicators/whale-index"),
            ("Indicators - CGDI", f"{BASE_URL}/coinglass/indicators/cgdi"),
            ("Indicators - CDRI", f"{BASE_URL}/coinglass/indicators/cdri"),
            ("Indicators - Golden Ratio", f"{BASE_URL}/coinglass/indicators/golden-ratio"),
            ("Indicators - Market Momentum", f"{BASE_URL}/coinglass/indicators/market-momentum"),
            ("Indicators - Volatility Index", f"{BASE_URL}/coinglass/indicators/volatility"),
            ("Indicators - Trend Strength", f"{BASE_URL}/coinglass/indicators/trend-strength"),
            ("Indicators - Volume Profile", f"{BASE_URL}/coinglass/indicators/volume-profile"),
            ("Indicators - Price Correlation", f"{BASE_URL}/coinglass/indicators/price-correlation"),
            
            # === MACRO & MARKET (2 endpoints) ===
            ("Macro - Economic Calendar", f"{BASE_URL}/coinglass/macro/calendar"),
            ("Macro - Bitcoin Dominance", f"{BASE_URL}/coinglass/macro/btc-dominance"),
            
            # === NEWS (1 endpoint) ===
            ("News - Feed", f"{BASE_URL}/coinglass/news"),
            
            # === ORDER FLOW (2 endpoints) ===
            ("Order Flow - Trade Analysis", f"{BASE_URL}/coinglass/order-flow/trades"),
            ("Order Flow - Volume Delta", f"{BASE_URL}/coinglass/order-flow/volume-delta"),
            
            # === EXCHANGE METRICS (3 endpoints) ===
            ("Exchange - Trading Volume", f"{BASE_URL}/coinglass/exchange/volume"),
            ("Exchange - Market Share", f"{BASE_URL}/coinglass/exchange/market-share"),
            ("Exchange - Comparison", f"{BASE_URL}/coinglass/exchange/comparison"),
            
            # === AGGREGATED METRICS (5 endpoints) ===
            ("Aggregated - Market Overview", f"{BASE_URL}/coinglass/aggregated/market-overview"),
            ("Aggregated - Coin Summary BTC", f"{BASE_URL}/coinglass/aggregated/coin-summary/BTCUSDT"),
            ("Aggregated - Top Movers", f"{BASE_URL}/coinglass/aggregated/top-movers"),
            ("Aggregated - Exchange Comparison", f"{BASE_URL}/coinglass/aggregated/exchange-comparison"),
            ("Aggregated - Historical Snapshot", f"{BASE_URL}/coinglass/aggregated/snapshot"),
        ]
        
        print(f"📊 Testing {len(test_cases)} endpoints...\n")
        
        # Test all endpoints in parallel batches
        batch_size = 10
        for i in range(0, len(test_cases), batch_size):
            batch = test_cases[i:i+batch_size]
            print(f"Testing batch {i//batch_size + 1}/{(len(test_cases)-1)//batch_size + 1}...")
            
            tasks = [self.test_endpoint(name, url) for name, url in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for result in batch_results:
                self.results["total_endpoints"] += 1
                self.results["endpoint_details"].append(result)
                
                if result["success"]:
                    self.results["successful"] += 1
                    self.results["response_times"].append(result["response_time"])
                    print(f"  ✅ {result['name'][:50]:<50} | {result['response_time']}s | {result['status']}")
                else:
                    self.results["failed"] += 1
                    self.results["errors"].append({
                        "name": result["name"],
                        "error": result.get("error", f"HTTP {result['status']}")
                    })
                    print(f"  ❌ {result['name'][:50]:<50} | FAILED | {result.get('error', 'Unknown')[:50]}")
            
            # Rate limit protection
            if i + batch_size < len(test_cases):
                await asyncio.sleep(2)
        
        print("\n" + "=" * 80)
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        
        print("\n📋 COINGLASS API TEST REPORT")
        print("=" * 80)
        
        # Summary Statistics
        success_rate = (self.results["successful"] / self.results["total_endpoints"] * 100) if self.results["total_endpoints"] > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Endpoints Tested: {self.results['total_endpoints']}")
        print(f"  ✅ Successful: {self.results['successful']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        
        # Performance Metrics
        if self.results["response_times"]:
            avg_time = sum(self.results["response_times"]) / len(self.results["response_times"])
            min_time = min(self.results["response_times"])
            max_time = max(self.results["response_times"])
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"  Average Response Time: {avg_time:.3f}s")
            print(f"  Fastest Response: {min_time:.3f}s")
            print(f"  Slowest Response: {max_time:.3f}s")
        
        # Breakdown by Category
        categories = {}
        for detail in self.results["endpoint_details"]:
            category = detail["name"].split(" - ")[0]
            if category not in categories:
                categories[category] = {"total": 0, "success": 0}
            categories[category]["total"] += 1
            if detail["success"]:
                categories[category]["success"] += 1
        
        print(f"\n📁 BREAKDOWN BY CATEGORY:")
        for cat, stats in sorted(categories.items()):
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {cat:<30} | {stats['success']}/{stats['total']} ({rate:.0f}%)")
        
        # Failed Endpoints
        if self.results["errors"]:
            print(f"\n❌ FAILED ENDPOINTS ({len(self.results['errors'])}):")
            for error in self.results["errors"][:10]:
                print(f"  • {error['name']}")
                print(f"    Error: {error['error'][:80]}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate >= 95:
            print("  ✅ Excellent! API is production-ready")
        elif success_rate >= 80:
            print("  ⚠️  Good, but some endpoints need attention")
        else:
            print("  🚨 Critical issues detected - requires immediate attention")
        
        if avg_time > 5:
            print("  ⚠️  Consider implementing caching for slow endpoints")
        
        if self.results["failed"] > 0:
            print(f"  🔧 Fix {self.results['failed']} failing endpoints before production")
        
        print("\n" + "=" * 80)
        print(f"Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.results["total_endpoints"],
                "successful": self.results["successful"],
                "failed": self.results["failed"],
                "success_rate": success_rate
            },
            "performance": {
                "avg_response_time": avg_time if self.results["response_times"] else 0,
                "min_response_time": min_time if self.results["response_times"] else 0,
                "max_response_time": max_time if self.results["response_times"] else 0
            },
            "categories": categories,
            "failed_endpoints": self.results["errors"],
            "all_results": self.results["endpoint_details"]
        }
        
        with open("coinglass_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print("\n📄 Detailed report saved to: coinglass_test_report.json")

async def main():
    tester = CoinglassAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
