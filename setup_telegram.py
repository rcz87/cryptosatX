#!/usr/bin/env python3
"""
Telegram Bot Setup Utility for CryptoSatX
This script helps you get your Telegram Chat ID and test the bot integration.
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TelegramSetup:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    async def get_bot_info(self):
        """Get bot information to verify the token is valid"""
        if not self.bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
            return None

        url = f"https://api.telegram.org/bot{self.bot_token}/getMe"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                data = response.json()

                if data.get("ok"):
                    bot_info = data["result"]
                    print(f"✅ Bot token is valid!")
                    print(f"🤖 Bot Name: {bot_info['first_name']}")
                    print(f"👤 Bot Username: @{bot_info['username']}")
                    print(f"🆔 Bot ID: {bot_info['id']}")
                    return bot_info
                else:
                    print(
                        f"❌ Invalid bot token: {data.get('description', 'Unknown error')}"
                    )
                    return None

        except Exception as e:
            print(f"❌ Error connecting to Telegram API: {str(e)}")
            return None

    async def get_updates(self):
        """Get recent updates to find your chat ID"""
        if not self.bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                data = response.json()

                if data.get("ok"):
                    updates = data["result"]
                    if updates:
                        print(f"\n📨 Found {len(updates)} recent updates:")
                        chat_ids = set()

                        for update in updates:
                            message = update.get("message", {})
                            chat = message.get("chat", {})

                            chat_id = chat.get("id")
                            chat_type = chat.get("type", "unknown")
                            chat_title = chat.get("title") or chat.get(
                                "first_name", "Unknown"
                            )

                            if chat_id:
                                chat_ids.add(chat_id)
                                print(
                                    f"  💬 Chat ID: {chat_id} ({chat_type}) - {chat_title}"
                                )
                                if message.get("text"):
                                    print(f"      Message: {message['text']}")

                        if chat_ids:
                            print(
                                f"\n🎯 Your Chat ID(s): {', '.join(map(str, chat_ids))}"
                            )
                            print(
                                "💡 Add one of these to your .env file as TELEGRAM_CHAT_ID"
                            )
                        else:
                            print("\n❌ No chat IDs found in updates")
                    else:
                        print("\n📭 No recent updates found")
                        print(
                            "💡 Send a message to your bot first, then run this again"
                        )
                else:
                    print(
                        f"❌ Error getting updates: {data.get('description', 'Unknown error')}"
                    )

        except Exception as e:
            print(f"❌ Error getting updates: {str(e)}")

    async def test_message(self, chat_id):
        """Send a test message to verify the bot works"""
        if not self.bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        message = """🚀 <b>CRYPTOSATX BOT TEST</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━
✅ Your Telegram bot is working correctly!

🤖 Bot Configuration:
• Token: ✅ Valid
• Chat ID: ✅ {chat_id}
• Connection: ✅ Active

📊 Ready to send:
• Trading signals
• Market alerts
• System notifications

⚡ Powered by CryptoSatX AI Engine
━━━━━━━━━━━━━━━━━━━━━━━""".format(
            chat_id=chat_id
        )

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                data = response.json()

                if data.get("ok"):
                    print(f"✅ Test message sent successfully to chat {chat_id}!")
                    return True
                else:
                    print(
                        f"❌ Failed to send message: {data.get('description', 'Unknown error')}"
                    )
                    return False

        except Exception as e:
            print(f"❌ Error sending test message: {str(e)}")
            return False


async def main():
    """Main setup process"""
    print("🚀 CryptoSatX Telegram Bot Setup")
    print("=" * 50)

    setup = TelegramSetup()

    # Step 1: Verify bot token
    print("\n📋 Step 1: Verifying bot token...")
    bot_info = await setup.get_bot_info()

    if not bot_info:
        print("\n❌ Please check your bot token and try again")
        return

    # Step 2: Get chat ID
    print("\n📋 Step 2: Getting your Chat ID...")
    print("💡 Make sure you've sent a message to your bot first!")
    await setup.get_updates()

    # Step 3: Test with provided chat ID (if exists)
    current_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if current_chat_id:
        print(f"\n📋 Step 3: Testing with existing Chat ID: {current_chat_id}")
        success = await setup.test_message(current_chat_id)
        if success:
            print("🎉 Your Telegram integration is ready!")
        else:
            print("⚠️ Test failed - check your Chat ID")
    else:
        print("\n📋 Step 3: Manual test")
        print("💡 Once you have your Chat ID, you can test by running:")
        print("   python setup_telegram.py --test <CHAT_ID>")

    print("\n" + "=" * 50)
    print("📖 Next Steps:")
    print("1. Add your Chat ID to .env file as TELEGRAM_CHAT_ID=your_chat_id")
    print("2. Restart your CryptoSatX application")
    print("3. The bot will automatically send trading signals and alerts")


if __name__ == "__main__":
    asyncio.run(main())
