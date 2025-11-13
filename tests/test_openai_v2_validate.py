"""
Test script for OpenAI V2 Signal Judge validation
Compare V1 vs V2 validation outputs

Usage:
    python tests/test_openai_v2_validate.py
"""

import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"
TEST_SYMBOLS = ["BTC", "ETH", "SOL"]


async def test_v1_validation(symbol: str):
    """Test production V1 validation endpoint"""
    print(f"\n🔵 Testing V1 Validation: {symbol}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/openai/validate/{symbol}",
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ V1 Success:")
                print(f"   Signal: {result.get('original_signal')} → {result.get('validated_signal')}")
                print(f"   Confidence: {result.get('confidence')}")
                print(f"   Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
                return result
            else:
                print(f"❌ V1 Error: {response.status_code}")
                print(f"   {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ V1 Exception: {e}")
            return None


async def test_v2_validation(symbol: str):
    """Test development V2 Signal Judge endpoint"""
    print(f"\n🟢 Testing V2 Signal Judge: {symbol}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/openai/v2/validate/{symbol}?include_comprehensive=true",
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ V2 Success:")
                print(f"   Original Signal: {result.get('original_signal')} (Score: {result.get('original_score')})")
                print(f"   Verdict: {result.get('verdict')}")
                print(f"   AI Confidence: {result.get('ai_confidence')}/100")
                print(f"   Key Agreements:")
                for agreement in result.get('key_agreements', [])[:3]:
                    print(f"      ✓ {agreement}")
                print(f"   Key Conflicts:")
                for conflict in result.get('key_conflicts', [])[:3]:
                    print(f"      ⚠ {conflict}")
                risk_suggestion = result.get('adjusted_risk_suggestion', {})
                print(f"   Risk Adjustment: {risk_suggestion.get('risk_factor')} (size: {risk_suggestion.get('position_size_multiplier', 1.0)}x)")
                print(f"   Telegram Summary: {result.get('telegram_summary', 'N/A')[:150]}...")
                return result
            else:
                print(f"❌ V2 Error: {response.status_code}")
                print(f"   {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ V2 Exception: {e}")
            return None


async def test_v1_v2_comparison(symbol: str):
    """Test comparison endpoint"""
    print(f"\n🔍 Testing V1 vs V2 Comparison: {symbol}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/openai/v2/compare/{symbol}",
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Comparison Success:")
                print(f"   Original Signal: {result.get('original_signal')} (Score: {result.get('original_score')})")
                print(f"\n   V1 Validation:")
                v1 = result.get('v1_validation', {})
                print(f"      Signal: {v1.get('validated_signal')}")
                print(f"      Confidence: {v1.get('confidence')}")
                print(f"\n   V2 Validation:")
                v2 = result.get('v2_validation', {})
                print(f"      Verdict: {v2.get('verdict')}")
                print(f"      AI Confidence: {v2.get('ai_confidence')}/100")
                print(f"      Agreements: {len(v2.get('key_agreements', []))}")
                print(f"      Conflicts: {len(v2.get('key_conflicts', []))}")
                return result
            else:
                print(f"❌ Comparison Error: {response.status_code}")
                print(f"   {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Comparison Exception: {e}")
            return None


async def test_health_check():
    """Test V2 health check"""
    print(f"\n❤️ Testing V2 Health Check")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/openai/v2/health")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Health Check Success:")
                print(f"   Status: {result.get('status')}")
                print(f"   Version: {result.get('version')}")
                print(f"   Mode: {result.get('mode')}")
                print(f"   OpenAI Configured: {result.get('openai_configured')}")
                print(f"   Phase: {result.get('phase')}")
                print(f"   Endpoints: {len(result.get('endpoints', []))}")
                return result
            else:
                print(f"❌ Health Check Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Health Check Exception: {e}")
            return None


async def main():
    """Run all tests"""
    print("=" * 80)
    print("OpenAI V2 Signal Judge - Testing Suite")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 80)
    
    await test_health_check()
    
    for symbol in TEST_SYMBOLS:
        print(f"\n{'=' * 80}")
        print(f"Testing Symbol: {symbol}")
        print(f"{'=' * 80}")
        
        v1_result = await test_v1_validation(symbol)
        
        v2_result = await test_v2_validation(symbol)
        
        comparison_result = await test_v1_v2_comparison(symbol)
        
        await asyncio.sleep(2)
    
    print(f"\n{'=' * 80}")
    print("Testing Complete!")
    print("=" * 80)
    print("\n📊 Summary:")
    print("- V1 endpoints: Production validation (simple)")
    print("- V2 endpoints: Enhanced Signal Judge (structured verdict)")
    print("- Comparison endpoint: Side-by-side analysis")
    print("\n💡 Next Steps:")
    print("1. Review V2 verdict quality vs V1 validation")
    print("2. Test with more symbols and market conditions")
    print("3. When ready, migrate production to use V2 logic")
    print("\n⚠️ Note: V2 endpoints are in development mode - do not affect production")


if __name__ == "__main__":
    asyncio.run(main())
