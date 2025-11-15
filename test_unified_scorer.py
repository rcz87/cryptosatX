"""
Test script for Unified Scoring System
Validates unified scorer, signal validator, and tier classification
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_unified_scorer():
    """Test unified scoring system"""
    print("=" * 70)
    print("UNIFIED SCORING SYSTEM TEST")
    print("=" * 70)

    # Import components
    print("\n1. Importing components...")
    try:
        from app.core.unified_scorer import unified_scorer
        from app.core.signal_validator import signal_validator
        print("   ✓ unified_scorer imported")
        print("   ✓ signal_validator imported")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return

    # Test symbols
    test_symbols = ["BTC", "ETH", "SOL"]

    # Test unified scoring for single symbol
    print("\n2. Testing Unified Scoring (Single Symbol)...")
    for symbol in test_symbols[:1]:  # Test with BTC only
        print(f"\n   Testing {symbol}:")
        try:
            result = await unified_scorer.calculate_unified_score(symbol)

            print(f"   ✓ Unified Score: {result['unified_score']}/100")
            print(f"   ✓ Tier: {result['tier']}")
            print(f"   ✓ Recommendation: {result['recommendation']}")
            print(f"   ✓ Confidence: {result['confidence']}")

            print(f"\n   Score Breakdown:")
            for component, score in result['breakdown'].items():
                print(f"     - {component}: {score}/100")

            print(f"\n   Weighted Contributions:")
            for component, contribution in result['weighted_contributions'].items():
                print(f"     - {component}: {contribution} points")

        except Exception as e:
            print(f"   ✗ Error scoring {symbol}: {e}")
            import traceback
            traceback.print_exc()

    # Test bulk scoring
    print("\n3. Testing Bulk Scoring...")
    try:
        results = await unified_scorer.calculate_bulk_scores(test_symbols)

        print(f"   ✓ Scored {len(results)} symbols")
        print(f"\n   Rankings:")
        for idx, result in enumerate(results, 1):
            print(
                f"   {idx}. {result['symbol']}: {result['unified_score']}/100 "
                f"({result['tier']}) - {result['confidence']} confidence"
            )

    except Exception as e:
        print(f"   ✗ Bulk scoring failed: {e}")
        import traceback
        traceback.print_exc()

    # Test signal validation
    print("\n4. Testing Signal Validation...")
    for symbol in test_symbols[:1]:  # Test with BTC only
        print(f"\n   Validating BUY signal for {symbol}:")
        try:
            validation = await signal_validator.validate_buy_signal(symbol)

            print(f"   ✓ Action: {validation['action']}")
            print(f"   ✓ Confidence: {validation['confidence']}%")
            print(f"   ✓ Confirmations: {validation['confirmations']}/4")
            print(f"   ✓ Agreeing scanners: {validation['agreeing_scanners']}")

            print(f"\n   Scanner Signals:")
            for scanner, signal in validation['scanner_signals'].items():
                print(f"     - {scanner}: {signal}")

        except Exception as e:
            print(f"   ✗ Validation failed: {e}")
            import traceback
            traceback.print_exc()

    # Test tier classification
    print("\n5. Testing Tier Classification...")
    test_scores = [
        (90, "TIER_1_MUST_BUY"),
        (75, "TIER_2_STRONG_BUY"),
        (60, "TIER_3_WATCHLIST"),
        (40, "TIER_4_NEUTRAL")
    ]

    for score, expected_tier in test_scores:
        tier = unified_scorer._classify_tier(score)
        status = "✓" if tier == expected_tier else "✗"
        print(f"   {status} Score {score} → {tier} (expected: {expected_tier})")

    # Test weight configuration
    print("\n6. Checking Weight Configuration...")
    weights = unified_scorer.WEIGHTS
    total_weight = sum(weights.values())

    print(f"   Weights:")
    for component, weight in weights.items():
        print(f"     - {component}: {weight*100:.0f}%")

    print(f"\n   Total weight: {total_weight:.3f}")
    if abs(total_weight - 1.0) < 0.001:
        print("   ✓ Weights sum to 1.0 (valid)")
    else:
        print(f"   ⚠️ Weights sum to {total_weight}, not 1.0!")

    # Test confidence levels
    print("\n7. Checking Confidence Levels...")
    confidence_levels = signal_validator.CONFIDENCE_LEVELS

    print(f"   Confidence by confirmations:")
    for confirmations, confidence in confidence_levels.items():
        print(f"     - {confirmations} scanner(s): {confidence}% confidence")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_unified_scorer())
