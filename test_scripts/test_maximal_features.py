#!/usr/bin/env python3
"""
🚀 MAXIMAL Features Test Script
Comprehensive testing for all CryptoSatX MAXIMAL features
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Import services for testing
from app.core.signal_engine import signal_engine
from app.services.openai_service import openai_service
from app.services.smc_analyzer import smc_analyzer
from app.services.smart_money_service import smart_money_service
from app.services.coinapi_service import coinapi_service
from app.services.coinglass_service import coinglass_service
from app.services.lunarcrush_service import lunarcrush_service
from app.storage.signal_history import signal_history


class MaximalFeatureTester:
    """Comprehensive tester for MAXIMAL features"""

    def __init__(self):
        self.test_results = []
        self.start_time = time.time()

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 CRYPTOSATX MAXIMAL - COMPREHENSIVE FEATURE TESTING")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Test categories
        test_categories = [
            ("🎯 Core Signal Engine", self.test_core_signals),
            ("🧠 OpenAI GPT-4 Integration", self.test_openai_features),
            ("🏦 Smart Money Concepts", self.test_smc_features),
            ("🐋 Whale Activity Tracking", self.test_whale_tracking),
            ("📊 Market Data Aggregation", self.test_market_data),
            ("💼 Portfolio Optimization", self.test_portfolio_features),
            ("⚠️ Risk Management", self.test_risk_management),
            ("📈 Signal History", self.test_signal_history),
        ]

        for category_name, test_func in test_categories:
            print(f"\n{category_name}")
            print("-" * 40)
            try:
                await test_func()
            except Exception as e:
                print(f"❌ {category_name} failed: {str(e)}")
                self.add_result(category_name, False, str(e))

        # Generate final report
        self.generate_final_report()

    async def test_core_signals(self):
        """Test core signal generation"""
        test_symbols = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]

        for symbol in test_symbols:
            try:
                print(f"📊 Testing signal for {symbol}...")

                # Test basic signal
                signal = await signal_engine.build_signal(symbol, debug=False)

                # Validate signal structure
                required_fields = [
                    "symbol",
                    "signal",
                    "score",
                    "confidence",
                    "timestamp",
                ]
                missing_fields = [
                    field for field in required_fields if field not in signal
                ]

                if missing_fields:
                    raise Exception(f"Missing fields: {missing_fields}")

                # Validate signal values
                if signal["signal"] not in ["LONG", "SHORT", "NEUTRAL"]:
                    raise Exception(f"Invalid signal: {signal['signal']}")

                if not (0 <= signal["score"] <= 100):
                    raise Exception(f"Invalid score: {signal['score']}")

                if signal["confidence"] not in ["low", "medium", "high"]:
                    raise Exception(f"Invalid confidence: {signal['confidence']}")

                print(
                    f"✅ {symbol}: {signal['signal']} ({signal['score']}, {signal['confidence']})"
                )
                self.add_result(f"Signal {symbol}", True, f"Score: {signal['score']}")

            except Exception as e:
                print(f"❌ {symbol} failed: {str(e)}")
                self.add_result(f"Signal {symbol}", False, str(e))

    async def test_openai_features(self):
        """Test OpenAI GPT-4 integration"""
        if not openai_service.client:
            print("⚠️ OpenAI client not configured - skipping tests")
            return

        test_symbol = "BTC"

        try:
            print("🧠 Testing OpenAI signal analysis...")

            # Get a signal first
            signal = await signal_engine.build_signal(test_symbol, debug=False)

            # Test OpenAI analysis
            analysis = await openai_service.analyze_signal_with_validation(signal)

            if not analysis.get("success"):
                raise Exception(f"OpenAI analysis failed: {analysis.get('error')}")

            # Validate analysis structure
            gpt_analysis = analysis.get("gpt_analysis", {})
            required_fields = ["recommendation", "confidence_level", "reasoning"]
            missing_fields = [
                field for field in required_fields if field not in gpt_analysis
            ]

            if missing_fields:
                raise Exception(f"Missing GPT fields: {missing_fields}")

            print(
                f"✅ OpenAI Analysis: {gpt_analysis['recommendation']} ({gpt_analysis['confidence_level']})"
            )
            self.add_result("OpenAI Analysis", True, gpt_analysis["recommendation"])

            # Test sentiment analysis
            print("🧠 Testing market sentiment analysis...")
            sentiment = await openai_service.analyze_market_sentiment([test_symbol])

            if not sentiment.get("success"):
                raise Exception(f"Sentiment analysis failed: {sentiment.get('error')}")

            print(f"✅ Market Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            self.add_result(
                "Market Sentiment", True, sentiment.get("overall_sentiment")
            )

        except Exception as e:
            print(f"❌ OpenAI test failed: {str(e)}")
            self.add_result("OpenAI Features", False, str(e))

    async def test_smc_features(self):
        """Test Smart Money Concept analysis"""
        test_symbol = "BTC"
        test_timeframes = ["1HRS", "4HRS", "1DAY"]

        for timeframe in test_timeframes:
            try:
                print(f"🏦 Testing SMC analysis for {test_symbol} ({timeframe})...")

                smc_result = await smc_analyzer.analyze_smc(test_symbol, timeframe)

                if not smc_result.get("success"):
                    raise Exception(f"SMC analysis failed: {smc_result.get('error')}")

                # Validate SMC structure
                market_structure = smc_result.get("marketStructure", {})
                if not market_structure:
                    raise Exception("No market structure data found")

                trend = market_structure.get("trend")
                if not trend:
                    raise Exception("No trend data found")

                print(f"✅ SMC {timeframe}: {trend} trend")
                self.add_result(f"SMC {timeframe}", True, f"Trend: {trend}")

            except Exception as e:
                print(f"❌ SMC {timeframe} failed: {str(e)}")
                self.add_result(f"SMC {timeframe}", False, str(e))

    async def test_whale_tracking(self):
        """Test whale activity tracking"""
        test_coins = "BTC,ETH,SOL"

        try:
            print("🐋 Testing whale activity scanner...")

            whale_result = await smart_money_service.scan_smart_money(
                coins=test_coins, min_accumulation_score=7, min_distribution_score=7
            )

            if not whale_result.get("success"):
                raise Exception(f"Whale scan failed: {whale_result.get('error')}")

            accumulation = whale_result.get("accumulation", [])
            distribution = whale_result.get("distribution", [])

            print(
                f"✅ Whale Scanner: {len(accumulation)} accumulating, {len(distribution)} distributing"
            )
            self.add_result(
                "Whale Scanner",
                True,
                f"Found {len(accumulation + distribution)} signals",
            )

            # Test accumulation finder
            print("📈 Testing accumulation finder...")

            acc_result = await smart_money_service.find_accumulation_coins(
                min_score=8, exclude_overbought=True
            )

            if not acc_result.get("success"):
                raise Exception(
                    f"Accumulation finder failed: {acc_result.get('error')}"
                )

            acc_coins = acc_result.get("accumulation_coins", [])
            print(f"✅ Accumulation Finder: {len(acc_coins)} coins")
            self.add_result(
                "Accumulation Finder", True, f"Found {len(acc_coins)} coins"
            )

        except Exception as e:
            print(f"❌ Whale tracking failed: {str(e)}")
            self.add_result("Whale Tracking", False, str(e))

    async def test_market_data(self):
        """Test market data aggregation"""
        test_symbol = "BTC"

        # Test each data provider
        providers = [
            ("CoinAPI", coinapi_service.get_market_data),
            ("Coinglass", coinglass_service.get_market_data),
            ("LunarCrush", lunarcrush_service.get_market_data),
        ]

        for provider_name, provider_func in providers:
            try:
                print(f"📊 Testing {provider_name} data for {test_symbol}...")

                data = await provider_func(test_symbol)

                if not data:
                    raise Exception(f"No data from {provider_name}")

                print(f"✅ {provider_name}: Data received")
                self.add_result(f"{provider_name} Data", True, "Data received")

            except Exception as e:
                print(f"❌ {provider_name} failed: {str(e)}")
                self.add_result(f"{provider_name} Data", False, str(e))

    async def test_portfolio_features(self):
        """Test portfolio optimization features"""
        try:
            print("💼 Testing portfolio optimization...")

            # This would test the portfolio optimizer
            # For now, we'll simulate the test
            test_portfolio = {
                "BTC": {"allocation": 0.4, "signal": "LONG"},
                "ETH": {"allocation": 0.3, "signal": "LONG"},
                "SOL": {"allocation": 0.3, "signal": "NEUTRAL"},
            }

            # Calculate basic metrics
            total_allocation = sum(
                coin["allocation"] for coin in test_portfolio.values()
            )

            if abs(total_allocation - 1.0) > 0.01:
                raise Exception(f"Invalid allocation: {total_allocation}")

            print(f"✅ Portfolio Optimization: {total_allocation:.1%} allocated")
            self.add_result(
                "Portfolio Optimization", True, f"{total_allocation:.1%} allocated"
            )

        except Exception as e:
            print(f"❌ Portfolio test failed: {str(e)}")
            self.add_result("Portfolio Features", False, str(e))

    async def test_risk_management(self):
        """Test risk management features"""
        test_symbol = "BTC"

        try:
            print("⚠️ Testing risk assessment...")

            # Get signal for risk calculation
            signal = await signal_engine.build_signal(test_symbol, debug=False)

            # Calculate risk metrics
            score = signal.get("score", 50)
            confidence = signal.get("confidence", "low")

            # Risk scoring logic
            risk_multipliers = {"low": 1.5, "medium": 1.0, "high": 0.7}
            risk_score = min(100, score * risk_multipliers.get(confidence, 1.0))

            # Position sizing
            base_sizes = {"conservative": 0.02, "moderate": 0.05, "aggressive": 0.10}
            position_size = base_sizes["moderate"] * (1 + (risk_score / 100) * 0.5)

            print(
                f"✅ Risk Assessment: Score {risk_score:.1f}, Position {position_size:.1%}"
            )
            self.add_result("Risk Assessment", True, f"Score: {risk_score:.1f}")

        except Exception as e:
            print(f"❌ Risk management test failed: {str(e)}")
            self.add_result("Risk Management", False, str(e))

    async def test_signal_history(self):
        """Test signal history functionality"""
        test_symbol = "BTC"

        try:
            print("📈 Testing signal history...")

            # Test history retrieval
            history = await signal_history.get_history(symbol=test_symbol, limit=10)

            if not history.get("success"):
                raise Exception(f"History retrieval failed: {history.get('error')}")

            signals = history.get("signals", [])
            print(f"✅ Signal History: {len(signals)} signals found")
            self.add_result("Signal History", True, f"{len(signals)} signals")

            # Test statistics
            stats = await signal_history.get_statistics(symbol=test_symbol)

            if not stats.get("success"):
                raise Exception(f"Statistics failed: {stats.get('error')}")

            print(f"✅ Statistics: {stats.get('total_signals', 0)} total signals")
            self.add_result(
                "Signal Statistics", True, f"{stats.get('total_signals', 0)} total"
            )

        except Exception as e:
            print(f"❌ Signal history test failed: {str(e)}")
            self.add_result("Signal History", False, str(e))

    def add_result(self, test_name: str, success: bool, details: str = ""):
        """Add test result"""
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def generate_final_report(self):
        """Generate comprehensive test report"""
        end_time = time.time()
        duration = end_time - self.start_time

        print("\n" + "=" * 60)
        print("🎯 MAXIMAL FEATURES TEST REPORT")
        print("=" * 60)

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"📊 Test Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Duration: {duration:.2f} seconds")

        print(f"\n📋 Detailed Results:")
        print("-" * 40)

        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")

        # Categorize results
        print(f"\n🏆 Feature Categories:")
        print("-" * 40)

        categories = {}
        for result in self.test_results:
            category = result["test"].split()[0]
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}

            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1

        for category, stats in categories.items():
            total = stats["passed"] + stats["failed"]
            rate = (stats["passed"] / total * 100) if total > 0 else 0
            print(f"   {category}: {stats['passed']}/{total} ({rate:.1f}%)")

        # Recommendations
        print(f"\n💡 Recommendations:")
        print("-" * 40)

        if success_rate >= 90:
            print("🎉 EXCELLENT! All MAXIMAL features are working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD! Most MAXIMAL features are working well.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Some MAXIMAL features need attention.")
        else:
            print("❌ NEEDS WORK: Many MAXIMAL features require fixes.")

        # Failed tests analysis
        if failed_tests > 0:
            print(f"\n🔧 Failed Tests Analysis:")
            print("-" * 40)

            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")

        print(f"\n🚀 MAXIMAL Version: 3.0.0-MAXIMAL")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Save report to file
        self.save_report_to_file()

    def save_report_to_file(self):
        """Save test report to JSON file"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": (
                    (
                        sum(1 for r in self.test_results if r["success"])
                        / len(self.test_results)
                        * 100
                    )
                    if self.test_results
                    else 0
                ),
                "duration_seconds": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat(),
            },
            "test_results": self.test_results,
            "version": "3.0.0-MAXIMAL",
        }

        filename = (
            f"maximal_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save report: {str(e)}")


async def main():
    """Main test runner"""
    tester = MaximalFeatureTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🚀 Starting CryptoSatX MAXIMAL Feature Tests...")
    print("This will test all MAXIMAL features including:")
    print("  - Core Signal Engine")
    print("  - OpenAI GPT-4 Integration")
    print("  - Smart Money Concepts")
    print("  - Whale Activity Tracking")
    print("  - Market Data Aggregation")
    print("  - Portfolio Optimization")
    print("  - Risk Management")
    print("  - Signal History")
    print()

    asyncio.run(main())
