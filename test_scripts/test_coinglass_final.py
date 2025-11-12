#!/usr/bin/env python3
"""
FINAL Coinglass API Comprehensive Testing
Tests ALL 64 production endpoints with CORRECT URLs from OpenAPI spec
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict

BASE_URL = "http://localhost:8000"

class CoinglassFinalTester:
    def __init__(self):
        self.results = {
            "total_endpoints": 0,
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "endpoint_details": [],
            "categories": {}
        }
        
    async def test_endpoint(self, name: str, url: str) -> Dict:
        """Test single endpoint"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                elapsed = time.time() - start_time
                
                result = {
                    "name": name,
                    "url": url,
                    "status": response.status_code,
                    "response_time": round(elapsed, 3),
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["has_data"] = bool(data)
                    except:
                        result["has_data"] = False
                else:
                    result["error"] = response.text[:100]
                
                return result
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "status": 0,
                "response_time": 0,
                "success": False,
                "error": str(e)[:100]
            }
    
    async def run_all_tests(self):
        """Test all 64 Coinglass endpoints with CORRECT URLs"""
        
        print("=" * 90)
        print("🔍 COINGLASS API - FINAL COMPREHENSIVE TESTING (64 Endpoints)")
        print("=" * 90)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # ACTUAL endpoint URLs from OpenAPI spec
        test_cases = [
            # === MARKET DATA (4 endpoints) ===
            ("Market - All Coins", f"{BASE_URL}/coinglass/markets"),
            ("Market - BTC", f"{BASE_URL}/coinglass/markets/BTCUSDT"),
            ("Market - Perpetual BTC", f"{BASE_URL}/coinglass/perpetual-market/BTCUSDT"),
            ("Market - Pairs Markets", f"{BASE_URL}/coinglass/pairs-markets/BTCUSDT"),
            
            # === LIQUIDATIONS (6 endpoints) ===
            ("Liquidation - Order", f"{BASE_URL}/coinglass/liquidation/order"),
            ("Liquidation - Exchange List", f"{BASE_URL}/coinglass/liquidation/exchange-list"),
            ("Liquidation - Aggregated History", f"{BASE_URL}/coinglass/liquidation/aggregated-history"),
            ("Liquidation - History", f"{BASE_URL}/coinglass/liquidation/history"),
            ("Liquidation - Symbol BTC", f"{BASE_URL}/coinglass/liquidations/BTCUSDT"),
            ("Liquidation - Heatmap BTC", f"{BASE_URL}/coinglass/liquidations/BTCUSDT/heatmap"),
            
            # === FUNDING RATES (4 endpoints) ===
            ("Funding - History", f"{BASE_URL}/coinglass/funding-rate/history"),
            ("Funding - OI Weight History", f"{BASE_URL}/coinglass/funding-rate/oi-weight-history"),
            ("Funding - Vol Weight History", f"{BASE_URL}/coinglass/funding-rate/vol-weight-history"),
            ("Funding - Exchange List BTC", f"{BASE_URL}/coinglass/funding-rate/exchange-list/BTCUSDT"),
            
            # === OPEN INTEREST (6 endpoints) ===
            ("OI - History", f"{BASE_URL}/coinglass/open-interest/history"),
            ("OI - Aggregated History", f"{BASE_URL}/coinglass/open-interest/aggregated-history"),
            ("OI - Aggregated Stablecoin", f"{BASE_URL}/coinglass/open-interest/aggregated-stablecoin-history"),
            ("OI - Aggregated Coin Margin", f"{BASE_URL}/coinglass/open-interest/aggregated-coin-margin-history"),
            ("OI - Exchange List BTC", f"{BASE_URL}/coinglass/open-interest/exchange-list/BTCUSDT"),
            ("OI - Exchange History Chart", f"{BASE_URL}/coinglass/open-interest/exchange-history-chart"),
            
            # === LONG/SHORT RATIOS (3 endpoints) ===
            ("Long/Short - Account Ratio", f"{BASE_URL}/coinglass/top-long-short-account-ratio/history"),
            ("Long/Short - Position Ratio", f"{BASE_URL}/coinglass/top-long-short-position-ratio/history"),
            ("Long/Short - Net Position", f"{BASE_URL}/coinglass/net-position/history"),
            
            # === TAKER VOLUME (2 endpoints) ===
            ("Taker - Buy/Sell Volume", f"{BASE_URL}/coinglass/volume/taker-buy-sell"),
            ("Taker - Exchange List", f"{BASE_URL}/coinglass/taker-buy-sell-volume/exchange-list"),
            
            # === ORDERBOOK (5 endpoints) ===
            ("Orderbook - Ask/Bids History", f"{BASE_URL}/coinglass/orderbook/ask-bids-history"),
            ("Orderbook - Aggregated History", f"{BASE_URL}/coinglass/orderbook/aggregated-history"),
            ("Orderbook - Whale Walls", f"{BASE_URL}/coinglass/orderbook/whale-walls"),
            ("Orderbook - Whale History", f"{BASE_URL}/coinglass/orderbook/whale-history"),
            ("Orderbook - Detailed History", f"{BASE_URL}/coinglass/orderbook/detailed-history"),
            
            # === HYPERLIQUID (3 endpoints) ===
            ("Hyperliquid - Whale Alerts", f"{BASE_URL}/coinglass/hyperliquid/whale-alerts"),
            ("Hyperliquid - Whale Positions", f"{BASE_URL}/coinglass/hyperliquid/whale-positions"),
            ("Hyperliquid - Positions BTC", f"{BASE_URL}/coinglass/hyperliquid/positions/BTCUSDT"),
            
            # === ON-CHAIN (3 endpoints) ===
            ("On-Chain - Whale Transfers", f"{BASE_URL}/coinglass/chain/whale-transfers"),
            ("On-Chain - Exchange Flows", f"{BASE_URL}/coinglass/chain/exchange-flows"),
            ("On-Chain - Reserves BTC", f"{BASE_URL}/coinglass/on-chain/reserves/BTC"),
            
            # === TECHNICAL INDICATORS (12 endpoints) ===
            ("Indicator - RSI List", f"{BASE_URL}/coinglass/indicators/rsi-list"),
            ("Indicator - RSI", f"{BASE_URL}/coinglass/indicators/rsi"),
            ("Indicator - MA", f"{BASE_URL}/coinglass/indicators/ma"),
            ("Indicator - EMA", f"{BASE_URL}/coinglass/indicators/ema"),
            ("Indicator - Bollinger", f"{BASE_URL}/coinglass/indicators/bollinger"),
            ("Indicator - MACD", f"{BASE_URL}/coinglass/indicators/macd"),
            ("Indicator - Basis", f"{BASE_URL}/coinglass/indicators/basis"),
            ("Indicator - Whale Index", f"{BASE_URL}/coinglass/indicators/whale-index"),
            ("Indicator - CGDI", f"{BASE_URL}/coinglass/indicators/cgdi"),
            ("Indicator - CDRI", f"{BASE_URL}/coinglass/indicators/cdri"),
            ("Indicator - Golden Ratio", f"{BASE_URL}/coinglass/indicators/golden-ratio"),
            ("Indicator - Fear & Greed", f"{BASE_URL}/coinglass/indicators/fear-greed"),
            
            # === MACRO & NEWS (2 endpoints) ===
            ("Macro - Economic Calendar", f"{BASE_URL}/coinglass/calendar/economic"),
            ("News - Feed", f"{BASE_URL}/coinglass/news/feed"),
            
            # === OPTIONS (2 endpoints) ===
            ("Options - Open Interest", f"{BASE_URL}/coinglass/options/open-interest"),
            ("Options - Volume", f"{BASE_URL}/coinglass/options/volume"),
            
            # === ETF & INDEXES (4 endpoints) ===
            ("ETF - Flows BTC", f"{BASE_URL}/coinglass/etf/flows/BTC"),
            ("Index - Bull Market Peak", f"{BASE_URL}/coinglass/index/bull-market-peak"),
            ("Index - Rainbow Chart", f"{BASE_URL}/coinglass/index/rainbow-chart"),
            ("Index - Stock to Flow", f"{BASE_URL}/coinglass/index/stock-to-flow"),
            
            # === UTILITY (5 endpoints) ===
            ("Util - Supported Coins", f"{BASE_URL}/coinglass/supported-coins"),
            ("Util - Exchanges", f"{BASE_URL}/coinglass/exchanges"),
            ("Util - Price Change", f"{BASE_URL}/coinglass/price-change"),
            ("Util - Price History", f"{BASE_URL}/coinglass/price-history"),
            ("Util - Delisted Pairs", f"{BASE_URL}/coinglass/delisted-pairs"),
            
            # === OTHER (3 endpoints) ===
            ("Other - Borrow Interest Rate", f"{BASE_URL}/coinglass/borrow/interest-rate"),
            ("Other - Exchange Assets", f"{BASE_URL}/coinglass/exchange/assets/binance"),
            ("Other - Dashboard BTC", f"{BASE_URL}/coinglass/dashboard/BTCUSDT"),
        ]
        
        print(f"📊 Testing {len(test_cases)} endpoints in batches...\n")
        
        # Test in batches
        batch_size = 10
        for i in range(0, len(test_cases), batch_size):
            batch = test_cases[i:i+batch_size]
            print(f"Batch {i//batch_size + 1}/{(len(test_cases)-1)//batch_size + 1}...")
            
            tasks = [self.test_endpoint(name, url) for name, url in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for result in batch_results:
                self.results["total_endpoints"] += 1
                self.results["endpoint_details"].append(result)
                
                # Track by category
                category = result["name"].split(" - ")[0]
                if category not in self.results["categories"]:
                    self.results["categories"][category] = {"total": 0, "success": 0}
                self.results["categories"][category]["total"] += 1
                
                if result["success"]:
                    self.results["successful"] += 1
                    self.results["response_times"].append(result["response_time"])
                    self.results["categories"][category]["success"] += 1
                    status = "✅"
                else:
                    self.results["failed"] += 1
                    status = "❌"
                
                print(f"  {status} {result['name'][:55]:<55} | {result.get('response_time', 0):.3f}s")
            
            if i + batch_size < len(test_cases):
                await asyncio.sleep(1)
        
        print("\n" + "=" * 90)
        self.generate_report()
    
    def generate_report(self):
        """Generate final comprehensive report"""
        
        print("\n📋 COINGLASS API - FINAL TEST REPORT")
        print("=" * 90)
        
        success_rate = (self.results["successful"] / self.results["total_endpoints"] * 100)
        
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"  Total Endpoints: {self.results['total_endpoints']}")
        print(f"  ✅ Successful: {self.results['successful']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        
        # Performance
        if self.results["response_times"]:
            avg = sum(self.results["response_times"]) / len(self.results["response_times"])
            print(f"\n⚡ PERFORMANCE:")
            print(f"  Average: {avg:.3f}s | Min: {min(self.results['response_times']):.3f}s | Max: {max(self.results['response_times']):.3f}s")
        
        # Category breakdown
        print(f"\n📁 CATEGORY BREAKDOWN:")
        for cat, stats in sorted(self.results["categories"].items()):
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            icon = "✅" if rate == 100 else "⚠️" if rate >= 50 else "❌"
            print(f"  {icon} {cat:<20} | {stats['success']:2}/{stats['total']:2} ({rate:5.1f}%)")
        
        # Recommendations
        print(f"\n💡 ASSESSMENT:")
        if success_rate >= 95:
            print("  🎉 EXCELLENT - Production ready!")
        elif success_rate >= 80:
            print("  ✅ GOOD - Minor fixes needed")
        elif success_rate >= 50:
            print("  ⚠️  MODERATE - Several endpoints need attention")
        else:
            print("  🚨 CRITICAL - Major issues detected")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.results["total_endpoints"],
                "successful": self.results["successful"],
                "failed": self.results["failed"],
                "success_rate": success_rate
            },
            "performance": {
                "avg": sum(self.results["response_times"]) / len(self.results["response_times"]) if self.results["response_times"] else 0
            },
            "categories": self.results["categories"],
            "all_results": self.results["endpoint_details"]
        }
        
        with open("coinglass_final_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved: coinglass_final_report.json")
        print("=" * 90)

async def main():
    tester = CoinglassFinalTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
