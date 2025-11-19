"""
CryptoSatX Main Entry Point for Replit Deployment
Production-ready FastAPI application with enhanced features
"""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 80)
print("🔍 DEBUGGING: Module Import Path Resolution")
print("=" * 80)
print(f"📂 __file__: {__file__}")
print(f"📂 Resolved parent: {Path(__file__).resolve().parent}")
print(f"📂 sys.path[0]: {sys.path[0]}")
print(f"📂 sys.path (first 5): {sys.path[:5]}")
print("=" * 80)

from app.main import app
import uvicorn
from app.utils.logger import default_logger

print(f"✅ Imported app from: {app.__module__}")
print(f"✅ App file location: {getattr(app, '__file__', 'N/A')}")
print(f"✅ App type: {type(app)}")
print(f"✅ Number of routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
print("=" * 80)

# Configure logging for Replit
logger = default_logger

# Replit specific setup
if __name__ == "__main__":
    # Get port from Replit environment
    port = int(os.environ.get("PORT", 8001))  # Use 8001 to avoid conflicts

    # Log startup information
    logger.info(f"Starting CryptoSatX on Replit")
    logger.info(f"Port: {port}")
    logger.info(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    logger.info(f"Repl ID: {os.getenv('REPL_ID', 'unknown')}")
    logger.info(f"Repl Slug: {os.getenv('REPL_SLUG', 'unknown')}")

    # Configure for Replit deployment
    uvicorn.run(
        app,  # Use imported app object directly (not string reference)
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        workers=1,  # Replit supports single worker
        log_level="info",
        access_log=True,
        use_colors=False,  # Better for Replit logs
    )
