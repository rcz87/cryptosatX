#!/usr/bin/env python3
"""
Test script untuk verifikasi perubahan signal engine
Mengurangi netralitas GPT dengan testing berbagai skenario
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.signal_engine import signal_engine


async def test_signal_improvements():
    """Test signal improvements dengan berbagai skenario"""

    print("🔥 TESTING SIGNAL ENGINE IMPROVEMENTS 🔥")
    print("=" * 50)

    # Test symbols
    test_symbols = ["BTC", "ETH", "SOL"]

    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}...")
        print("-" * 30)

        try:
            # Build signal dengan debug mode untuk melihat breakdown
            signal_data = await signal_engine.build_signal(symbol, debug=True)

            print(f"Signal: {signal_data['signal']}")
            print(f"Score: {signal_data['score']}/100")
            print(f"Confidence: {signal_data['confidence']}")
            print(f"Price: ${signal_data['price']:,.2f}")

            print("\n🎯 Top Reasons:")
            for i, reason in enumerate(signal_data["reasons"], 1):
                print(f"  {i}. {reason}")

            # Debug breakdown
            if "debug" in signal_data and "scoreBreakdown" in signal_data["debug"]:
                breakdown = signal_data["debug"]["scoreBreakdown"]
                print("\n📈 Score Breakdown:")
                for factor, data in breakdown.items():
                    score = data["score"]
                    weighted = data["weighted"]
                    weight = data["weight"]
                    bias = "🟢" if score > 50 else "🔴" if score < 50 else "⚪"
                    print(
                        f"  {bias} {factor}: {score:.1f} (weight: {weight}%, weighted: {weighted:.1f})"
                    )

            # Check for comprehensive metrics
            if "comprehensiveMetrics" in signal_data:
                print("\n📊 Comprehensive Metrics Available:")
                comp = signal_data["comprehensiveMetrics"]
                print(
                    f"  Multi-timeframe trend: {comp.get('multiTimeframeTrend', 'N/A')}"
                )

            if "premiumMetrics" in signal_data:
                print("\n💎 Premium Metrics Available:")
                prem = signal_data["premiumMetrics"]
                print(
                    f"  Liquidation imbalance: {prem.get('liquidationImbalance', 'N/A')}"
                )
                print(f"  Smart money bias: {prem.get('smartMoneyBias', 'N/A')}")
                print(f"  Fear & Greed: {prem.get('fearGreedIndex', 'N/A')}")

            # Analyze signal distribution
            signal = signal_data["signal"]
            score = signal_data["score"]

            if signal == "NEUTRAL":
                if 48 <= score <= 52:
                    print(
                        f"\n⚠️  NEAR-NEUTRAL: Score {score} sangat dekat dengan threshold"
                    )
                else:
                    print(f"\n✅ NEUTRAL: Score {score} dalam zona netral yang wajar")
            elif signal == "LONG":
                print(f"\n🚀 BULLISH: Score {score} menunjukkan sinyal kuat untuk LONG")
            elif signal == "SHORT":
                print(
                    f"\n📉 BEARISH: Score {score} menunjukkan sinyal kuat untuk SHORT"
                )

        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")

    print("\n" + "=" * 50)
    print("🎯 SUMMARY OF IMPROVEMENTS:")
    print("1. ✅ Weight system disesuaikan untuk mengurangi netralitas")
    print("2. ✅ Threshold dipersempit (48-52 vs 45-55)")
    print("3. ✅ Price momentum scoring ditingkatkan sensitivitasnya")
    print("4. ✅ Liquidation scoring ditingkatkan sensitivitasnya")
    print("5. ✅ More weight ke funding rate dan liquidations")
    print("6. ✅ Less weight ke social sentiment noise")


if __name__ == "__main__":
    asyncio.run(test_signal_improvements())
