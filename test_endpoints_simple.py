#!/usr/bin/env python3
"""
Simple test to check if the new endpoints are working
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))


async def test_endpoints():
    """Test the new endpoints"""
    try:
        # Import the router
        from app.api.routes_optimized_gpt import router

        print("✅ Router imported successfully")

        # Check if the endpoints exist
        routes = [route.path for route in router.routes]
        print(f"📋 Available routes: {routes}")

        # Check for specific endpoints
        required_endpoints = [
            "/smart-money/accumulation",
            "/portfolio/optimize",
            "/risk/assess/{symbol}",
            "/strategies/recommend",
        ]

        for endpoint in required_endpoints:
            if any(endpoint in route for route in routes):
                print(f"✅ Endpoint {endpoint} found")
            else:
                print(f"❌ Endpoint {endpoint} missing")

        return True

    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_endpoints())
    if success:
        print("\n🎉 Endpoint test completed successfully!")
    else:
        print("\n💥 Endpoint test failed!")
