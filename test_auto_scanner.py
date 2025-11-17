"""
Test script for Auto Scanner
Verifies auto_scanner can be imported and configured properly
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_auto_scanner():
    """Test auto-scanner functionality"""
    print("=" * 60)
    print("AUTO-SCANNER TEST")
    print("=" * 60)

    # Import auto_scanner
    print("\n1. Importing auto_scanner...")
    from app.services.auto_scanner import auto_scanner
    print("   ✓ Import successful")

    # Check configuration
    print("\n2. Configuration:")
    print(f"   - Enabled: {auto_scanner.enabled}")
    print(f"   - Smart Money Interval: {auto_scanner.smart_money_interval} hours")
    print(f"   - MSS Interval: {auto_scanner.mss_interval} hours")
    print(f"   - RSI Interval: {auto_scanner.rsi_interval} hours")
    print(f"   - Accumulation Threshold: {auto_scanner.accumulation_threshold}")
    print(f"   - Distribution Threshold: {auto_scanner.distribution_threshold}")
    print(f"   - MSS Threshold: {auto_scanner.mss_threshold}")

    # Get stats
    print("\n3. Statistics:")
    stats = auto_scanner.get_stats()
    print(f"   - Total Scans: {stats['total_scans']}")
    print(f"   - Smart Money Scans: {stats['smart_money_scans']}")
    print(f"   - MSS Scans: {stats['mss_scans']}")
    print(f"   - Alerts Sent: {stats['alerts_sent']}")

    # Test if it can start (even if disabled, should not crash)
    print("\n4. Testing startup (will warn if disabled)...")
    try:
        await auto_scanner.start()
        if auto_scanner.enabled:
            print("   ✓ Auto-scanner started successfully")
            print("   ℹ️ Note: Scheduler is now running in background")

            # Show scheduled jobs
            jobs = auto_scanner.scheduler.get_jobs()
            if jobs:
                print(f"\n5. Scheduled Jobs ({len(jobs)}):")
                for job in jobs:
                    print(f"   - {job.name} (ID: {job.id})")
                    if job.next_run_time:
                        print(f"     Next run: {job.next_run_time}")

            # Stop it
            print("\n6. Stopping auto-scanner...")
            await auto_scanner.stop()
            print("   ✓ Auto-scanner stopped")
        else:
            print("   ⚠️ Auto-scanner is DISABLED")
            print("   ℹ️ Set AUTO_SCAN_ENABLED=true in .env to enable")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_auto_scanner())
