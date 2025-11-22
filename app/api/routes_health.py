"""
Health check routes
"""
from fastapi import APIRouter
from app.utils.logger import get_wib_time

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    Returns API information and status
    """
    return {
        "status": "healthy",
        "timestamp": get_wib_time(),
        "service": "Crypto Futures Signal API",
        "name": "CryptoSatX - AI Trading Signals",
        "version": "3.0.0",
        "description": "Production-ready crypto futures signal API with multi-provider integration",
        "endpoints": {
            "dashboard": "/dashboard",
            "health": "/health",
            "signals": "/signals/{symbol}",
            "market": "/market/{symbol}",
            "gpt_schema": "/gpt/action-schema",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }
