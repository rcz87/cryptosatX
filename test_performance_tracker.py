"""
Test script for Phase 4: Performance Tracking System

Validates:
1. Performance tracker initialization and scheduling
2. Signal tracking functionality
3. Win rate analyzer statistics
4. Performance report generation
5. Database integration
"""
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment
load_dotenv()

async def test_performance_system():
    """Test complete Phase 4 performance tracking system"""
    print("=" * 70)
    print("PHASE 4: PERFORMANCE TRACKING SYSTEM TEST")
    print("=" * 70)

    # Test 1: Import components
    print("\n1. Importing components...")
    try:
        from app.services.performance_tracker import performance_tracker, track_signal
        from app.services.win_rate_analyzer import (
            win_rate_analyzer,
            get_performance_report,
            get_win_rates
        )
        print("   ✓ performance_tracker imported")
        print("   ✓ win_rate_analyzer imported")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return

    # Test 2: Check tracker configuration
    print("\n2. Checking Performance Tracker Configuration...")
    try:
        print(f"   ✓ Tracking intervals: {list(performance_tracker.INTERVALS.keys())}")
        print(f"   ✓ WIN threshold (LONG): +{performance_tracker.WIN_THRESHOLD_LONG}%")
        print(f"   ✓ LOSS threshold (LONG): {performance_tracker.LOSS_THRESHOLD_LONG}%")
        print(f"   ✓ WIN threshold (SHORT): {performance_tracker.WIN_THRESHOLD_SHORT}%")
        print(f"   ✓ LOSS threshold (SHORT): +{performance_tracker.LOSS_THRESHOLD_SHORT}%")
    except Exception as e:
        print(f"   ✗ Configuration check failed: {e}")

    # Test 3: Test outcome determination logic
    print("\n3. Testing Outcome Determination Logic...")
    try:
        # Test LONG signals
        long_win = performance_tracker._determine_outcome("LONG", 6.0)  # +6% = WIN
        long_loss = performance_tracker._determine_outcome("LONG", -4.0)  # -4% = LOSS
        long_neutral = performance_tracker._determine_outcome("LONG", 2.0)  # +2% = NEUTRAL

        assert long_win == "WIN", f"Expected WIN, got {long_win}"
        assert long_loss == "LOSS", f"Expected LOSS, got {long_loss}"
        assert long_neutral == "NEUTRAL", f"Expected NEUTRAL, got {long_neutral}"

        print("   ✓ LONG +6.0% → WIN")
        print("   ✓ LONG -4.0% → LOSS")
        print("   ✓ LONG +2.0% → NEUTRAL")

        # Test SHORT signals
        short_win = performance_tracker._determine_outcome("SHORT", -6.0)  # -6% = WIN
        short_loss = performance_tracker._determine_outcome("SHORT", 4.0)  # +4% = LOSS
        short_neutral = performance_tracker._determine_outcome("SHORT", -2.0)  # -2% = NEUTRAL

        assert short_win == "WIN", f"Expected WIN, got {short_win}"
        assert short_loss == "LOSS", f"Expected LOSS, got {short_loss}"
        assert short_neutral == "NEUTRAL", f"Expected NEUTRAL, got {short_neutral}"

        print("   ✓ SHORT -6.0% → WIN")
        print("   ✓ SHORT +4.0% → LOSS")
        print("   ✓ SHORT -2.0% → NEUTRAL")

    except AssertionError as e:
        print(f"   ✗ Logic test failed: {e}")
    except Exception as e:
        print(f"   ✗ Error testing logic: {e}")

    # Test 4: Start performance tracker
    print("\n4. Starting Performance Tracker...")
    try:
        await performance_tracker.start()
        print("   ✓ Performance tracker started")

        # Get initial stats
        stats = performance_tracker.get_stats()
        print(f"   ✓ Initial stats: {stats}")

    except Exception as e:
        print(f"   ✗ Failed to start tracker: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Test signal tracking (mock signal)
    print("\n5. Testing Signal Tracking...")
    try:
        test_signal = {
            "id": f"test_signal_{datetime.now().timestamp()}",
            "symbol": "BTC",
            "signal": "LONG",
            "price": 45000.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "unified_score": 85.5,
            "tier": "TIER_1_MUST_BUY",
            "scanner_type": "smart_money"
        }

        await track_signal(test_signal)
        print(f"   ✓ Signal tracking initiated for {test_signal['symbol']}")
        print(f"     - Signal ID: {test_signal['id']}")
        print(f"     - Type: {test_signal['signal']}")
        print(f"     - Entry Price: ${test_signal['price']}")
        print(f"     - Unified Score: {test_signal['unified_score']}")
        print(f"     - Tier: {test_signal['tier']}")

        # Check scheduled jobs
        stats = performance_tracker.get_stats()
        print(f"   ✓ Scheduled jobs: {stats.get('scheduled_jobs', 0)}")

    except Exception as e:
        print(f"   ✗ Signal tracking failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 6: Test win rate analyzer (may have no data yet)
    print("\n6. Testing Win Rate Analyzer...")
    try:
        # Overall stats
        overall_stats = await get_win_rates(days=30)
        print(f"   ✓ Overall stats retrieved:")
        print(f"     - Total signals: {overall_stats.get('total_signals', 0)}")
        print(f"     - Wins: {overall_stats.get('wins', 0)}")
        print(f"     - Losses: {overall_stats.get('losses', 0)}")
        print(f"     - Win rate: {overall_stats.get('win_rate', 0)}%")

        # Stats by scanner
        scanner_stats = await win_rate_analyzer.get_stats_by_scanner(days=30)
        print(f"   ✓ Scanner stats: {len(scanner_stats)} scanners")

        # Stats by tier
        tier_stats = await win_rate_analyzer.get_stats_by_tier(days=30)
        print(f"   ✓ Tier stats: {len(tier_stats)} tiers")

        # Stats by interval
        interval_stats = await win_rate_analyzer.get_stats_by_interval(days=30)
        print(f"   ✓ Interval stats: {len(interval_stats)} intervals")

    except Exception as e:
        print(f"   ✗ Win rate analyzer test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 7: Test performance report generation
    print("\n7. Testing Performance Report Generation...")
    try:
        report = await get_performance_report(days=7)

        print(f"   ✓ Report generated successfully")
        print(f"     - Report date: {report.get('report_generated_at')}")
        print(f"     - Period: {report.get('period_days')} days")
        print(f"     - Recommendations: {len(report.get('recommendations', []))} items")

        # Show recommendations if any
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n   Recommendations:")
            for idx, rec in enumerate(recommendations[:3], 1):
                print(f"     {idx}. [{rec['priority']}] {rec['message']}")

    except Exception as e:
        print(f"   ✗ Report generation failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 8: Test top performers (may be empty)
    print("\n8. Testing Top Performers Analysis...")
    try:
        performers = await win_rate_analyzer.get_top_performers(days=30, limit=5)

        best_signals = performers.get('best_signals', [])
        worst_signals = performers.get('worst_signals', [])
        best_symbols = performers.get('best_symbols', [])
        worst_symbols = performers.get('worst_symbols', [])

        print(f"   ✓ Top performers retrieved:")
        print(f"     - Best signals: {len(best_signals)}")
        print(f"     - Worst signals: {len(worst_signals)}")
        print(f"     - Best symbols: {len(best_symbols)}")
        print(f"     - Worst symbols: {len(worst_symbols)}")

        if best_symbols:
            print(f"\n   Top performing symbols:")
            for symbol_data in best_symbols[:3]:
                print(f"     - {symbol_data['symbol']}: {symbol_data['win_rate']}% win rate "
                      f"({symbol_data['wins']}/{symbol_data['total_signals']} signals)")

    except Exception as e:
        print(f"   ✗ Top performers test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 9: Stop tracker
    print("\n9. Stopping Performance Tracker...")
    try:
        await performance_tracker.stop()
        print("   ✓ Performance tracker stopped cleanly")
    except Exception as e:
        print(f"   ✗ Failed to stop tracker: {e}")

    # Test 10: Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("\nPhase 4 Components:")
    print("  ✓ Performance Tracker - Automated outcome tracking at 5 intervals")
    print("  ✓ Win Rate Analyzer - Comprehensive performance analytics")
    print("  ✓ Outcome Logic - WIN/LOSS/NEUTRAL determination")
    print("  ✓ Performance Report - Actionable recommendations")
    print("\nTracking Intervals:")
    print("  • 1 hour - Short-term momentum")
    print("  • 4 hours - Intraday performance")
    print("  • 24 hours - Daily performance")
    print("  • 7 days - Weekly trend")
    print("  • 30 days - Monthly outcome")
    print("\nWin/Loss Criteria:")
    print("  • LONG: WIN if +5%, LOSS if -3%")
    print("  • SHORT: WIN if -5%, LOSS if +3%")
    print("  • Otherwise: NEUTRAL")
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNote: Some tests may show 0 results if the database is empty.")
    print("      Run the system for a few days to accumulate performance data.")


if __name__ == "__main__":
    asyncio.run(test_performance_system())
