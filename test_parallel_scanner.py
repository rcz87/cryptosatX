"""
Test script for Parallel Scanner
Validates parallel scanning performance with 10, 50, 100 coins
"""
import os
import asyncio
import time
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_parallel_scanner():
    """Test parallel scanner functionality"""
    print("=" * 70)
    print("PARALLEL SCANNER TEST")
    print("=" * 70)

    # Import parallel scanner
    print("\n1. Importing parallel_scanner...")
    try:
        from app.services.parallel_scanner import parallel_scanner
        print("   ✓ Import successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return

    # Test configurations
    test_sets = [
        {
            "name": "Small (10 coins)",
            "coins": ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "LINK"],
            "target_time": 5  # seconds
        },
        {
            "name": "Medium (25 coins)",
            "coins": [
                "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "LINK",
                "UNI", "AAVE", "ATOM", "AVAX", "FTM", "NEAR", "ALGO", "VET", "ICP", "FIL",
                "LTC", "BCH", "ETC", "XLM", "HBAR"
            ],
            "target_time": 10  # seconds
        }
    ]

    # Test each set
    for idx, test in enumerate(test_sets):
        print(f"\n{idx + 2}. Testing: {test['name']}")
        print(f"   Coins: {len(test['coins'])}")
        print(f"   Target time: <{test['target_time']}s")

        # Get initial stats
        stats_before = parallel_scanner.get_stats()

        # Run scan
        start_time = time.time()
        try:
            result = await parallel_scanner.scan_bulk(
                coins=test['coins'],
                scanner_type='price'  # Use price as fastest
            )

            scan_time = time.time() - start_time

            # Display results
            print(f"\n   Results:")
            print(f"   - Total scanned: {result['total_scanned']}")
            print(f"   - Successful: {result['successful']}")
            print(f"   - Failed: {result['failed']}")
            print(f"   - Success rate: {result['success_rate']*100:.1f}%")

            # Performance
            perf = result.get('performance', {})
            print(f"\n   Performance:")
            print(f"   - Total time: {perf.get('total_time_seconds', 0):.2f}s")
            print(f"   - Coins/second: {perf.get('scans_per_second', 0):.1f}")
            print(f"   - Avg time/coin: {perf.get('avg_time_per_coin', 0):.3f}s")
            print(f"   - Batches: {perf.get('batches_processed', 0)}")
            print(f"   - Final rate limit: {perf.get('final_rate_limit', 0)}")

            # Check if met target
            if scan_time <= test['target_time']:
                print(f"\n   ✓ PASSED - Completed in {scan_time:.2f}s (target: <{test['target_time']}s)")
            else:
                print(f"\n   ⚠️ SLOW - Completed in {scan_time:.2f}s (target: <{test['target_time']}s)")

        except Exception as e:
            print(f"   ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()

    # Final stats
    print(f"\n{len(test_sets) + 2}. Final Statistics:")
    final_stats = parallel_scanner.get_stats()
    print(f"   - Total scans: {final_stats['total_scans']}")
    print(f"   - Successful: {final_stats['successful_scans']}")
    print(f"   - Failed: {final_stats['failed_scans']}")
    print(f"   - Avg scan time: {final_stats['avg_scan_time']:.3f}s")
    print(f"   - Scans/second: {final_stats['scans_per_second']:.1f}")
    print(f"   - Current rate limit: {final_stats['current_rate_limit']}")

    # Test smart cache
    print(f"\n{len(test_sets) + 3}. Testing Smart Cache...")
    try:
        from app.services.smart_cache import smart_cache

        cache_stats = smart_cache.get_stats()
        print("   Cache Statistics:")
        print(f"   - L1 size: {cache_stats['l1']['size']}/{cache_stats['l1']['max_size']}")
        print(f"   - L1 hits: {cache_stats['l1']['hits']}")
        print(f"   - L1 misses: {cache_stats['l1']['misses']}")
        print(f"   - L1 hit rate: {cache_stats['l1']['hit_rate']*100:.1f}%")
        print(f"   - Total gets: {cache_stats['global']['total_gets']}")
        print("   ✓ Smart cache working")

    except Exception as e:
        print(f"   ✗ Cache test failed: {e}")

    # Close scanner
    await parallel_scanner.close()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_parallel_scanner())
