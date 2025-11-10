#!/usr/bin/env python3
"""
Test script for MSS Telegram notifications
Demonstrates alert formatting with simulated high-scoring coin
"""
import asyncio
from app.services.telegram_mss_notifier import telegram_mss_notifier


async def test_high_score_alert():
    """
    Simulate a high-scoring MSS discovery alert
    This demonstrates what users will receive when MSS >= 75
    """
    print("🔔 Testing MSS Telegram Alert with High-Scoring Coin...")
    print("=" * 60)
    
    # Simulated high-scoring discovery
    test_data = {
        "symbol": "PEPE",
        "mss_score": 82.5,  # High score to trigger alert
        "signal": "STRONG_LONG",
        "confidence": "very_high",
        "phases": {
            "phase1_discovery": {
                "score": 28.0,
                "breakdown": {
                    "fdv_usd": 45_000_000,
                    "age_hours": 36,
                    "circulating_supply_pct": 65.0,
                    "current_price": 0.00000123,
                    "market_cap_usd": 29_250_000
                }
            },
            "phase2_confirmation": {
                "score": 29.5,
                "breakdown": {
                    "alt_rank": 45,
                    "galaxy_score": 78,
                    "sentiment_score": 0.82,
                    "volume_24h_change_pct": 145.3
                }
            },
            "phase3_validation": {
                "score": 25.0,
                "breakdown": {
                    "whale_accumulation": True,
                    "top_trader_long_ratio": 2.1,
                    "oi_trend": "increasing",
                    "funding_rate": 0.0125
                }
            }
        }
    }
    
    # Send alert
    result = await telegram_mss_notifier.send_mss_discovery_alert(
        symbol=test_data["symbol"],
        mss_score=test_data["mss_score"],
        signal=test_data["signal"],
        confidence=test_data["confidence"],
        phases=test_data["phases"],
        price=test_data["phases"]["phase1_discovery"]["breakdown"]["current_price"],
        market_cap=test_data["phases"]["phase1_discovery"]["breakdown"]["market_cap_usd"],
        fdv=test_data["phases"]["phase1_discovery"]["breakdown"]["fdv_usd"]
    )
    
    print("\n📊 Test Data:")
    print(f"   Symbol: {test_data['symbol']}")
    print(f"   MSS Score: {test_data['mss_score']}/100")
    print(f"   Signal: {test_data['signal']}")
    print(f"   Confidence: {test_data['confidence']}")
    
    print("\n📋 Phase Breakdown:")
    print(f"   Phase 1 (Discovery): {test_data['phases']['phase1_discovery']['score']:.1f}/30")
    print(f"   Phase 2 (Social): {test_data['phases']['phase2_confirmation']['score']:.1f}/35")
    print(f"   Phase 3 (Whale): {test_data['phases']['phase3_validation']['score']:.1f}/35")
    
    print("\n" + "=" * 60)
    if result.get("success"):
        print("✅ SUCCESS: Telegram alert sent!")
        print(f"   Message ID: {result.get('telegram_response', {}).get('result', {}).get('message_id', 'N/A')}")
        print("\n📱 Check your Telegram for the formatted MSS discovery alert!")
    else:
        print(f"❌ FAILED: {result.get('message')}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_high_score_alert())
