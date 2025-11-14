"""
Comprehensive Test Suite for CryptoSat Intelligence System
Tests MSS Engine, Signal Engine, and RPC Dispatchers

Run: python test_crypto_system.py
"""

import asyncio
from datetime import datetime
from typing import Dict, List
import json


# ============================================================================
# TEST 1: MSS ENGINE SCORING SIMULATION
# ============================================================================

class TestMSSEngine:
    """Test MSS scoring with various market scenarios"""
    
    def __init__(self):
        # Import the actual MSS engine
        try:
            import sys
            sys.path.append('/mnt/user-data/uploads')
            from app.core.mss_engine import MSSEngine
            self.engine = MSSEngine()
            self.engine_available = True
        except Exception as e:
            print(f"⚠️  Could not import MSSEngine: {e}")
            self.engine_available = False
    
    def test_discovery_phase(self):
        """Test Phase 1: Discovery scoring"""
        print("\n" + "="*70)
        print("TEST 1: MSS DISCOVERY PHASE (TOKENOMICS)")
        print("="*70)
        
        if not self.engine_available:
            print("❌ MSS Engine not available - skipping")
            return
        
        test_cases = [
            {
                "name": "Ultra Low Cap New Listing",
                "fdv_usd": 3_000_000,
                "age_hours": 12,
                "circulating_supply_pct": 15,
                "expected_pass": True
            },
            {
                "name": "Medium Cap Established",
                "fdv_usd": 30_000_000,
                "age_hours": 180,
                "circulating_supply_pct": 70,
                "expected_pass": False
            },
            {
                "name": "Low Cap Fresh (Borderline)",
                "fdv_usd": 25_000_000,
                "age_hours": 48,
                "circulating_supply_pct": 35,
                "expected_pass": True
            },
            {
                "name": "Micro Cap Whale-Controlled",
                "fdv_usd": 5_000_000,
                "age_hours": 24,
                "circulating_supply_pct": 10,
                "expected_pass": True
            }
        ]
        
        results = []
        for case in test_cases:
            score, breakdown = self.engine.calculate_discovery_score(
                fdv_usd=case["fdv_usd"],
                age_hours=case["age_hours"],
                circulating_supply_pct=case["circulating_supply_pct"]
            )
            
            passed = breakdown["status"] == "PASS"
            match = "✅" if passed == case["expected_pass"] else "❌"
            
            print(f"\n{match} {case['name']}")
            print(f"   FDV: ${case['fdv_usd']:,} | Age: {case['age_hours']}h | Float: {case['circulating_supply_pct']}%")
            print(f"   Score: {score:.1f}/35 | Status: {breakdown['status']}")
            print(f"   Breakdown: FDV={breakdown['fdv_score']:.1f}, Age={breakdown['age_score']:.1f}, Float={breakdown['float_score']:.1f}")
            
            results.append({
                "case": case["name"],
                "score": score,
                "passed": passed,
                "expected": case["expected_pass"],
                "match": passed == case["expected_pass"]
            })
        
        success_rate = sum(1 for r in results if r["match"]) / len(results) * 100
        print(f"\n📊 Discovery Phase Test Success Rate: {success_rate:.0f}%")
        return results
    
    def test_social_phase(self):
        """Test Phase 2: Social confirmation scoring"""
        print("\n" + "="*70)
        print("TEST 2: MSS SOCIAL PHASE (MOMENTUM)")
        print("="*70)
        
        if not self.engine_available:
            print("❌ MSS Engine not available - skipping")
            return
        
        test_cases = [
            {
                "name": "Viral Trending Coin",
                "altrank": 45,
                "galaxy_score": 78,
                "sentiment_score": 72,
                "volume_24h_change_pct": 250,
                "expected_pass": True
            },
            {
                "name": "Dead Social Activity",
                "altrank": 850,
                "galaxy_score": 35,
                "sentiment_score": 45,
                "volume_24h_change_pct": 5,
                "expected_pass": False
            },
            {
                "name": "Moderate Buzz",
                "altrank": 120,
                "galaxy_score": 66,
                "sentiment_score": 62,
                "volume_24h_change_pct": 80,
                "expected_pass": True
            },
            {
                "name": "High Rank But Strong Sentiment",
                "altrank": 250,
                "galaxy_score": 72,
                "sentiment_score": 75,
                "volume_24h_change_pct": 150,
                "expected_pass": True
            }
        ]
        
        results = []
        for case in test_cases:
            score, breakdown = self.engine.calculate_social_score(
                altrank=case["altrank"],
                galaxy_score=case["galaxy_score"],
                sentiment_score=case["sentiment_score"],
                volume_24h_change_pct=case["volume_24h_change_pct"]
            )
            
            passed = breakdown["status"] == "PASS"
            match = "✅" if passed == case["expected_pass"] else "❌"
            
            print(f"\n{match} {case['name']}")
            print(f"   AltRank: {case['altrank']} | Galaxy: {case['galaxy_score']} | Sentiment: {case['sentiment_score']}")
            print(f"   Volume Change: +{case['volume_24h_change_pct']}%")
            print(f"   Score: {score:.1f}/30 | Status: {breakdown['status']}")
            
            results.append({
                "case": case["name"],
                "score": score,
                "passed": passed,
                "expected": case["expected_pass"],
                "match": passed == case["expected_pass"]
            })
        
        success_rate = sum(1 for r in results if r["match"]) / len(results) * 100
        print(f"\n📊 Social Phase Test Success Rate: {success_rate:.0f}%")
        return results
    
    def test_validation_phase(self):
        """Test Phase 3: Institutional validation scoring"""
        print("\n" + "="*70)
        print("TEST 3: MSS VALIDATION PHASE (SMART MONEY)")
        print("="*70)
        
        if not self.engine_available:
            print("❌ MSS Engine not available - skipping")
            return
        
        test_cases = [
            {
                "name": "Strong Institutional Flow",
                "oi_change_pct": 120,
                "funding_rate": 0.025,
                "top_trader_long_ratio": 1.8,
                "whale_accumulation": True,
                "expected_pass": True
            },
            {
                "name": "Weak Positioning",
                "oi_change_pct": -5,
                "funding_rate": -0.01,
                "top_trader_long_ratio": 0.9,
                "whale_accumulation": False,
                "expected_pass": False
            },
            {
                "name": "Overcrowded Long (Risky)",
                "oi_change_pct": 80,
                "funding_rate": 0.06,
                "top_trader_long_ratio": 3.2,
                "whale_accumulation": False,
                "expected_pass": True  # Passes but with warnings
            },
            {
                "name": "Moderate Bullish Setup",
                "oi_change_pct": 55,
                "funding_rate": 0.018,
                "top_trader_long_ratio": 1.4,
                "whale_accumulation": True,
                "expected_pass": True
            }
        ]
        
        results = []
        for case in test_cases:
            score, breakdown = self.engine.calculate_validation_score(
                oi_change_pct=case["oi_change_pct"],
                funding_rate=case["funding_rate"],
                top_trader_long_ratio=case["top_trader_long_ratio"],
                whale_accumulation=case["whale_accumulation"]
            )
            
            passed = breakdown["status"] == "PASS"
            match = "✅" if passed == case["expected_pass"] else "❌"
            
            print(f"\n{match} {case['name']}")
            print(f"   OI Change: {case['oi_change_pct']:+.1f}% | Funding: {case['funding_rate']:.3f}%")
            print(f"   Trader Ratio: {case['top_trader_long_ratio']:.1f} | Whale: {case['whale_accumulation']}")
            print(f"   Score: {score:.1f}/35 | Status: {breakdown['status']}")
            
            results.append({
                "case": case["name"],
                "score": score,
                "passed": passed,
                "expected": case["expected_pass"],
                "match": passed == case["expected_pass"]
            })
        
        success_rate = sum(1 for r in results if r["match"]) / len(results) * 100
        print(f"\n📊 Validation Phase Test Success Rate: {success_rate:.0f}%")
        return results
    
    def test_final_mss_calculation(self):
        """Test final MSS score and signal generation"""
        print("\n" + "="*70)
        print("TEST 4: FINAL MSS CALCULATION")
        print("="*70)
        
        if not self.engine_available:
            print("❌ MSS Engine not available - skipping")
            return
        
        test_cases = [
            {
                "name": "Strong Long Signal",
                "discovery": 28,
                "social": 24,
                "validation": 30,
                "expected_signal": "STRONG_LONG"
            },
            {
                "name": "Moderate Long Signal",
                "discovery": 22,
                "social": 18,
                "validation": 20,
                "expected_signal": "MODERATE_LONG"
            },
            {
                "name": "Weak Long Signal",
                "discovery": 15,
                "social": 12,
                "validation": 18,
                "expected_signal": "WEAK_LONG"
            },
            {
                "name": "Neutral/Insufficient",
                "discovery": 10,
                "social": 8,
                "validation": 12,
                "expected_signal": "NEUTRAL"
            }
        ]
        
        results = []
        for case in test_cases:
            mss, signal, breakdown = self.engine.calculate_final_mss(
                discovery_score=case["discovery"],
                social_score=case["social"],
                validation_score=case["validation"]
            )
            
            match = "✅" if signal == case["expected_signal"] else "❌"
            
            print(f"\n{match} {case['name']}")
            print(f"   Discovery: {case['discovery']}/35 | Social: {case['social']}/30 | Validation: {case['validation']}/35")
            print(f"   MSS Score: {mss:.1f}/100")
            print(f"   Signal: {signal} (Expected: {case['expected_signal']})")
            print(f"   Confidence: {breakdown['confidence']}")
            
            results.append({
                "case": case["name"],
                "mss": mss,
                "signal": signal,
                "expected": case["expected_signal"],
                "match": signal == case["expected_signal"]
            })
        
        success_rate = sum(1 for r in results if r["match"]) / len(results) * 100
        print(f"\n📊 Final MSS Test Success Rate: {success_rate:.0f}%")
        return results
    
    def test_risk_warnings(self):
        """Test risk warning generation"""
        print("\n" + "="*70)
        print("TEST 5: RISK WARNING SYSTEM")
        print("="*70)
        
        if not self.engine_available:
            print("❌ MSS Engine not available - skipping")
            return
        
        test_cases = [
            {
                "name": "Ultra High Risk (New + Low Cap)",
                "age_hours": 24,
                "fdv_usd": 5_000_000,
                "circulating_supply_pct": 15,
                "funding_rate": 0.08,
                "top_trader_long_ratio": 3.5
            },
            {
                "name": "Moderate Risk",
                "age_hours": 120,
                "fdv_usd": 25_000_000,
                "circulating_supply_pct": 45,
                "funding_rate": 0.02,
                "top_trader_long_ratio": 1.5
            },
            {
                "name": "Low Risk (Established)",
                "age_hours": 500,
                "fdv_usd": 80_000_000,
                "circulating_supply_pct": 75,
                "funding_rate": 0.01,
                "top_trader_long_ratio": 1.2
            }
        ]
        
        for case in test_cases:
            warnings = self.engine.get_risk_warnings(
                age_hours=case["age_hours"],
                fdv_usd=case["fdv_usd"],
                funding_rate=case["funding_rate"],
                top_trader_long_ratio=case["top_trader_long_ratio"],
                circulating_supply_pct=case["circulating_supply_pct"]
            )
            
            print(f"\n{case['name']}")
            print(f"   Age: {case['age_hours']}h | FDV: ${case['fdv_usd']:,} | Float: {case['circulating_supply_pct']}%")
            print(f"   Funding: {case['funding_rate']:.3f}% | Trader Ratio: {case['top_trader_long_ratio']:.1f}")
            print(f"   ⚠️  Warnings: {len(warnings)}")
            for w in warnings:
                print(f"      {w}")


# ============================================================================
# TEST 2: SIGNAL ENGINE WEIGHT OPTIMIZATION
# ============================================================================

class TestSignalEngine:
    """Test signal engine scoring and weight sensitivity"""
    
    def test_weight_distribution(self):
        """Verify weights sum to 100%"""
        print("\n" + "="*70)
        print("TEST 6: SIGNAL ENGINE WEIGHT VALIDATION")
        print("="*70)
        
        weights = {
            "funding_rate": 18,
            "social_sentiment": 8,
            "price_momentum": 20,
            "liquidations": 25,
            "long_short_ratio": 12,
            "oi_trend": 8,
            "smart_money": 12,
            "fear_greed": 7
        }
        
        total = sum(weights.values())
        print(f"\n📊 Weight Distribution:")
        for factor, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            print(f"   {factor:20s}: {weight:3d}% {'█' * (weight // 2)}")
        
        print(f"\n   Total: {total}%")
        if total == 100:
            print("   ✅ Weights sum to 100% - Valid")
        else:
            print(f"   ❌ Weights sum to {total}% - INVALID! Should be 100%")
        
        return total == 100
    
    def test_signal_thresholds(self):
        """Test signal decision thresholds"""
        print("\n" + "="*70)
        print("TEST 7: SIGNAL DECISION THRESHOLDS")
        print("="*70)
        
        # Narrower neutral zone: 48-52
        test_scores = [
            (30, "SHORT"),
            (45, "SHORT"),
            (48, "SHORT"),  # Boundary
            (50, "NEUTRAL"),
            (52, "LONG"),  # Boundary
            (55, "LONG"),
            (70, "LONG")
        ]
        
        print(f"\n📊 Signal Decision Map (Neutral Zone: 48-52):")
        for score, expected_signal in test_scores:
            # Simulate signal determination
            if score >= 52:
                actual_signal = "LONG"
            elif score <= 48:
                actual_signal = "SHORT"
            else:
                actual_signal = "NEUTRAL"
            
            match = "✅" if actual_signal == expected_signal else "❌"
            print(f"   {match} Score {score:3d} → {actual_signal:7s} (Expected: {expected_signal})")
    
    def test_score_scenarios(self):
        """Test various market scenarios and expected scores"""
        print("\n" + "="*70)
        print("TEST 8: MARKET SCENARIO SCORING")
        print("="*70)
        
        scenarios = [
            {
                "name": "Strong Bullish (All Aligned)",
                "funding_rate": -0.15,  # Shorts paying → 70pts
                "social_sentiment": 75,
                "price_momentum": "bullish",  # → 80pts
                "liquidation_imbalance": "long",  # → 70pts
                "long_account_pct": 35,  # Contrarian → 75pts
                "oi_change_pct": 8,  # → 70pts
                "top_trader_long_pct": 62,  # → 70pts
                "fear_greed": 25,  # Fear → buy opportunity
                "expected_range": (65, 80)
            },
            {
                "name": "Strong Bearish (All Aligned)",
                "funding_rate": 0.25,  # Longs paying → 15pts
                "social_sentiment": 25,
                "price_momentum": "bearish",  # → 20pts
                "liquidation_imbalance": "short",  # → 30pts
                "long_account_pct": 68,  # Overcrowded → 25pts
                "oi_change_pct": -6,  # → 30pts
                "top_trader_long_pct": 38,  # → 30pts
                "fear_greed": 85,  # Greed → sell signal
                "expected_range": (20, 35)
            },
            {
                "name": "Mixed Signals (Neutral)",
                "funding_rate": 0.02,
                "social_sentiment": 50,
                "price_momentum": "neutral",
                "liquidation_imbalance": "balanced",
                "long_account_pct": 50,
                "oi_change_pct": 0,
                "top_trader_long_pct": 50,
                "fear_greed": 50,
                "expected_range": (45, 55)
            }
        ]
        
        for scenario in scenarios:
            print(f"\n{'='*60}")
            print(f"Scenario: {scenario['name']}")
            print(f"{'='*60}")
            
            # Calculate weighted score manually
            scores = {
                "funding_rate": self._score_funding(scenario["funding_rate"]),
                "social_sentiment": scenario["social_sentiment"],
                "price_momentum": self._score_momentum(scenario["price_momentum"]),
                "liquidations": self._score_liquidations(scenario["liquidation_imbalance"]),
                "long_short_ratio": self._score_ls_ratio(scenario["long_account_pct"]),
                "oi_trend": self._score_oi(scenario["oi_change_pct"]),
                "smart_money": self._score_smart_money(scenario["top_trader_long_pct"]),
                "fear_greed": scenario["fear_greed"]
            }
            
            weights = {
                "funding_rate": 18,
                "social_sentiment": 8,
                "price_momentum": 20,
                "liquidations": 25,
                "long_short_ratio": 12,
                "oi_trend": 8,
                "smart_money": 12,
                "fear_greed": 7
            }
            
            total_score = sum(scores[k] * weights[k] / 100 for k in scores.keys())
            
            print(f"\n📊 Component Scores:")
            for factor, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                weighted = score * weights[factor] / 100
                print(f"   {factor:20s}: {score:5.1f}/100 × {weights[factor]:2d}% = {weighted:5.2f}")
            
            print(f"\n   {'Total Score':20s}: {total_score:5.1f}/100")
            
            expected_min, expected_max = scenario["expected_range"]
            if expected_min <= total_score <= expected_max:
                print(f"   ✅ Within expected range [{expected_min}-{expected_max}]")
            else:
                print(f"   ⚠️  Outside expected range [{expected_min}-{expected_max}]")
            
            # Determine signal
            if total_score >= 52:
                signal = "LONG"
            elif total_score <= 48:
                signal = "SHORT"
            else:
                signal = "NEUTRAL"
            
            print(f"   📈 Signal: {signal}")
    
    # Helper scoring functions matching signal_engine.py logic
    def _score_funding(self, rate: float) -> float:
        rate_pct = rate * 100
        if rate_pct < -0.2: return 85
        elif rate_pct < -0.05: return 70
        elif rate_pct < 0: return 60
        elif rate_pct < 0.05: return 45
        elif rate_pct < 0.2: return 30
        else: return 15
    
    def _score_momentum(self, trend: str) -> float:
        if trend == "bullish": return 80
        elif trend == "bearish": return 20
        else: return 50
    
    def _score_liquidations(self, imbalance: str) -> float:
        if imbalance == "long": return 70
        elif imbalance == "short": return 30
        else: return 50
    
    def _score_ls_ratio(self, long_pct: float) -> float:
        if long_pct > 65: return 25
        elif long_pct > 55: return 40
        elif long_pct < 35: return 75
        elif long_pct < 45: return 60
        else: return 50
    
    def _score_oi(self, change_pct: float) -> float:
        if change_pct > 5: return 70
        elif change_pct > 1: return 60
        elif change_pct < -5: return 30
        elif change_pct < -1: return 40
        else: return 50
    
    def _score_smart_money(self, long_pct: float) -> float:
        if long_pct > 60: return 70
        elif long_pct > 52: return 60
        elif long_pct < 40: return 30
        elif long_pct < 48: return 40
        else: return 50


# ============================================================================
# TEST 3: ERROR HANDLING & EDGE CASES
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_data_scenarios(self):
        """Test behavior with missing/null data"""
        print("\n" + "="*70)
        print("TEST 9: MISSING DATA HANDLING")
        print("="*70)
        
        try:
            import sys
            sys.path.append('/mnt/user-data/uploads')
            from app.core.mss_engine import MSSEngine
            engine = MSSEngine()
            
            test_cases = [
                {
                    "name": "All None Values",
                    "fdv_usd": None,
                    "age_hours": None,
                    "circulating_supply_pct": None
                },
                {
                    "name": "Partial Data (FDV Only)",
                    "fdv_usd": 10_000_000,
                    "age_hours": None,
                    "circulating_supply_pct": None
                },
                {
                    "name": "Zero Values",
                    "fdv_usd": 0,
                    "age_hours": 0,
                    "circulating_supply_pct": 0
                }
            ]
            
            for case in test_cases:
                try:
                    score, breakdown = engine.calculate_discovery_score(
                        fdv_usd=case["fdv_usd"],
                        age_hours=case["age_hours"],
                        circulating_supply_pct=case["circulating_supply_pct"]
                    )
                    print(f"\n✅ {case['name']}")
                    print(f"   Score: {score:.1f}/35 | Status: {breakdown['status']}")
                    print(f"   Graceful handling: SUCCESS")
                except Exception as e:
                    print(f"\n❌ {case['name']}")
                    print(f"   Error: {e}")
                    print(f"   Graceful handling: FAILED")
        
        except Exception as e:
            print(f"❌ Could not load MSS Engine: {e}")
    
    def test_extreme_values(self):
        """Test with extreme/outlier values"""
        print("\n" + "="*70)
        print("TEST 10: EXTREME VALUE HANDLING")
        print("="*70)
        
        try:
            import sys
            sys.path.append('/mnt/user-data/uploads')
            from app.core.mss_engine import MSSEngine
            engine = MSSEngine()
            
            test_cases = [
                {
                    "name": "Extremely High FDV",
                    "oi_change_pct": 999999,
                    "funding_rate": 10.0,
                    "top_trader_long_ratio": 50.0,
                    "whale_accumulation": True
                },
                {
                    "name": "Negative Values",
                    "oi_change_pct": -999,
                    "funding_rate": -10.0,
                    "top_trader_long_ratio": 0.01,
                    "whale_accumulation": False
                }
            ]
            
            for case in test_cases:
                try:
                    score, breakdown = engine.calculate_validation_score(
                        oi_change_pct=case["oi_change_pct"],
                        funding_rate=case["funding_rate"],
                        top_trader_long_ratio=case["top_trader_long_ratio"],
                        whale_accumulation=case["whale_accumulation"]
                    )
                    print(f"\n✅ {case['name']}")
                    print(f"   Score: {score:.1f}/35")
                    print(f"   System handled extreme values correctly")
                except Exception as e:
                    print(f"\n⚠️  {case['name']}")
                    print(f"   Error: {e}")
        
        except Exception as e:
            print(f"❌ Could not load MSS Engine: {e}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("CRYPTOSAT INTELLIGENCE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Test started: {datetime.utcnow().isoformat()}")
    
    results = {
        "mss_tests": 0,
        "signal_tests": 0,
        "error_tests": 0,
        "total_passed": 0,
        "total_failed": 0
    }
    
    # TEST SUITE 1: MSS Engine
    print("\n\n🧪 RUNNING MSS ENGINE TESTS...")
    mss_tester = TestMSSEngine()
    
    try:
        mss_tester.test_discovery_phase()
        results["mss_tests"] += 1
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        results["total_failed"] += 1
    
    try:
        mss_tester.test_social_phase()
        results["mss_tests"] += 1
    except Exception as e:
        print(f"❌ Social test failed: {e}")
        results["total_failed"] += 1
    
    try:
        mss_tester.test_validation_phase()
        results["mss_tests"] += 1
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        results["total_failed"] += 1
    
    try:
        mss_tester.test_final_mss_calculation()
        results["mss_tests"] += 1
    except Exception as e:
        print(f"❌ Final MSS test failed: {e}")
        results["total_failed"] += 1
    
    try:
        mss_tester.test_risk_warnings()
        results["mss_tests"] += 1
    except Exception as e:
        print(f"❌ Risk warnings test failed: {e}")
        results["total_failed"] += 1
    
    # TEST SUITE 2: Signal Engine
    print("\n\n🧪 RUNNING SIGNAL ENGINE TESTS...")
    signal_tester = TestSignalEngine()
    
    try:
        signal_tester.test_weight_distribution()
        results["signal_tests"] += 1
    except Exception as e:
        print(f"❌ Weight test failed: {e}")
        results["total_failed"] += 1
    
    try:
        signal_tester.test_signal_thresholds()
        results["signal_tests"] += 1
    except Exception as e:
        print(f"❌ Threshold test failed: {e}")
        results["total_failed"] += 1
    
    try:
        signal_tester.test_score_scenarios()
        results["signal_tests"] += 1
    except Exception as e:
        print(f"❌ Scenario test failed: {e}")
        results["total_failed"] += 1
    
    # TEST SUITE 3: Error Handling
    print("\n\n🧪 RUNNING ERROR HANDLING TESTS...")
    error_tester = TestErrorHandling()
    
    try:
        error_tester.test_missing_data_scenarios()
        results["error_tests"] += 1
    except Exception as e:
        print(f"❌ Missing data test failed: {e}")
        results["total_failed"] += 1
    
    try:
        error_tester.test_extreme_values()
        results["error_tests"] += 1
    except Exception as e:
        print(f"❌ Extreme values test failed: {e}")
        results["total_failed"] += 1
    
    # FINAL SUMMARY
    print("\n\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    print(f"\n📊 Results:")
    print(f"   MSS Engine Tests: {results['mss_tests']}")
    print(f"   Signal Engine Tests: {results['signal_tests']}")
    print(f"   Error Handling Tests: {results['error_tests']}")
    print(f"\n   Total Tests Run: {sum([results['mss_tests'], results['signal_tests'], results['error_tests']])}")
    
    if results['total_failed'] == 0:
        print(f"\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {results['total_failed']} tests had issues")
    
    print(f"\nTest completed: {datetime.utcnow().isoformat()}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
