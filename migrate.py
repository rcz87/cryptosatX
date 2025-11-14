#!/usr/bin/env python3
"""
Database Migration Helper Script

Usage:
    python migrate.py upgrade      # Apply pending migrations
    python migrate.py downgrade    # Rollback last migration
    python migrate.py current      # Show current migration version
    python migrate.py history      # Show migration history
    python migrate.py create <message>  # Create new migration
"""

import subprocess
import sys


def run_command(cmd):
    """Run alembic command and capture output"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "upgrade":
        print("🔄 Applying database migrations...")
        run_command("alembic upgrade head")
    elif command == "downgrade":
        print("⏪ Rolling back last migration...")
        run_command("alembic downgrade -1")
    elif command == "current":
        print("📍 Current migration version:")
        run_command("alembic current")
    elif command == "history":
        print("📜 Migration history:")
        run_command("alembic history")
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a migration message")
            print("Usage: python migrate.py create <message>")
            sys.exit(1)
        message = "_".join(sys.argv[2:])
        print(f"📝 Creating new migration: {message}")
        run_command(f'alembic revision -m "{message}"')
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
