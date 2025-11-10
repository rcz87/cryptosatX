"""
CryptoSatX Main Entry Point for Replit Deployment
Production-ready FastAPI application with enhanced features
"""
import os
import asyncio
from app.main import app
import uvicorn
from app.utils.logger import default_logger

# Configure logging for Replit
logger = default_logger

# Replit specific setup
if __name__ == "__main__":
    # Get port from Replit environment
    port = int(os.environ.get("PORT", 5000))
    
    # Log startup information
    logger.info(f"Starting CryptoSatX on Replit")
    logger.info(f"Port: {port}")
    logger.info(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    logger.info(f"Repl ID: {os.getenv('REPL_ID', 'unknown')}")
    logger.info(f"Repl Slug: {os.getenv('REPL_SLUG', 'unknown')}")
    
    # Configure for Replit deployment
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        workers=1,     # Replit supports single worker
        log_level="info",
        access_log=True,
        use_colors=False,  # Better for Replit logs
    )
