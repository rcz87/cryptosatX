#!/usr/bin/env python3
"""
Test Telegram integration with CryptoSatX application
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.services.telegram_notifier import telegram_notifier


async def test_telegram_integration():
    """Test the full Telegram integration"""
    print("🚀 Testing CryptoSatX Telegram Integration")
    print("=" * 50)

    # Check configuration
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print(f"🤖 Bot Token: {'✅ Configured' if bot_token else '❌ Missing'}")
    print(f"💬 Chat ID: {'✅ Configured' if chat_id else '❌ Missing'}")
    print(f"🔧 Notifier Enabled: {'✅ Yes' if telegram_notifier.enabled else '❌ No'}")

    if not telegram_notifier.enabled:
        print("\n❌ Telegram notifier is not enabled")
        return False

    # Test 1: Send test message
    print("\n📋 Test 1: Sending test message...")
    result = await telegram_notifier.send_test_message()

    if result.get("success"):
        print("✅ Test message sent successfully!")
        print(
            f"📄 Response: {result.get('telegram_response', {}).get('ok', 'Unknown')}"
        )
    else:
        print(f"❌ Failed to send test message: {result.get('message')}")
        return False

    # Test 2: Send custom alert
    print("\n📋 Test 2: Sending custom alert...")
    custom_result = await telegram_notifier.send_custom_alert(
        "CryptoSatX System Test",
        "🔥 Bitcoin is showing strong bullish momentum!\n\n"
        "📊 Signal Score: 85/100\n"
        "🎯 Target: $45,000\n"
        "🛡️ Stop Loss: $42,500\n\n"
        "This is a test message from CryptoSatX AI Engine.",
        "🚀",
    )

    if custom_result.get("success"):
        print("✅ Custom alert sent successfully!")
    else:
        print(f"❌ Failed to send custom alert: {custom_result.get('message')}")
        return False

    # Test 3: Send sample trading signal
    print("\n📋 Test 3: Sending sample trading signal...")
    sample_signal = {
        "symbol": "BTC",
        "signal": "LONG",
        "score": 85.2,
        "confidence": "HIGH",
        "price": 43250.75,
        "reasons": [
            "Strong bullish momentum detected",
            "Volume increase of 45% in last hour",
            "RSI oversold condition recovering",
        ],
        "timestamp": "2025-01-10T11:24:00Z",
    }

    signal_result = await telegram_notifier.send_signal_alert(sample_signal)

    if signal_result.get("success"):
        print("✅ Trading signal sent successfully!")
    else:
        print(f"❌ Failed to send trading signal: {signal_result.get('message')}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All Telegram integration tests passed!")
    print("✅ Your CryptoSatX bot is ready to send trading signals!")

    return True


if __name__ == "__main__":
    asyncio.run(test_telegram_integration())
