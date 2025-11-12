#!/usr/bin/env python3
"""
Simple test to verify Telegram bot token
"""
import requests
import json
import os


def test_token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Please add your Telegram bot token to Replit Secrets")
        return False
    
    url = f"https://api.telegram.org/bot{token}/getMe"

    print(f"Testing token: {token[:20]}...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data["result"]
                print(f"✅ Bot is valid!")
                print(f"🤖 Bot Name: {bot_info['first_name']}")
                print(f"👤 Username: @{bot_info['username']}")
                return True
            else:
                print(f"❌ Invalid token: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    test_token()
