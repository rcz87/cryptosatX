"""
Database Migration Script
Migrates signal history from JSON file to PostgreSQL
Run once to transfer existing data
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

from app.storage.database import db
from app.storage.signal_db import signal_db


async def migrate_json_to_postgres():
    """Migrate existing JSON signals to PostgreSQL database"""
    
    print("=" * 60)
    print("SIGNAL HISTORY MIGRATION: JSON → PostgreSQL")
    print("=" * 60)
    
    # Initialize database connection
    await db.connect()
    
    # Load JSON data
    json_file = Path("signal_data/signal_history.json")
    
    if not json_file.exists():
        print("✅ No JSON file found - nothing to migrate")
        await db.disconnect()
        return
    
    try:
        with open(json_file, 'r') as f:
            history = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        await db.disconnect()
        return
    
    if not history:
        print("✅ JSON file is empty - nothing to migrate")
        await db.disconnect()
        return
    
    print(f"📊 Found {len(history)} signals in JSON file")
    print(f"🔄 Starting migration...\n")
    
    # Migrate each signal
    migrated = 0
    errors = 0
    
    for entry in history:
        try:
            signal_data = entry.get("data", {})
            
            # Skip if signal_data is empty or missing required fields
            if not signal_data.get("symbol") or not signal_data.get("signal"):
                print(f"⚠️  Skipping invalid entry: {entry.get('id', 'unknown')}")
                continue
            
            # Save to database
            signal_id = await signal_db.save_signal(signal_data)
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"   Migrated {migrated} signals...")
                
        except Exception as e:
            errors += 1
            print(f"❌ Error migrating signal: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ Migration Complete!")
    print(f"   Total signals migrated: {migrated}")
    print(f"   Errors: {errors}")
    print(f"   Success rate: {(migrated / len(history) * 100):.1f}%")
    print(f"{'=' * 60}\n")
    
    # Verify migration
    total_in_db = await signal_db.get_signal_count()
    print(f"📊 Total signals now in database: {total_in_db}")
    
    # Cleanup
    await db.disconnect()
    
    return {
        "total_json": len(history),
        "migrated": migrated,
        "errors": errors,
        "total_in_db": total_in_db
    }


if __name__ == "__main__":
    # Run migration
    result = asyncio.run(migrate_json_to_postgres())
    
    if result:
        print(f"\n✅ Migration successful!")
        print(f"   You can now use PostgreSQL for signal history")
        print(f"   JSON file is kept as backup")
