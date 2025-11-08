"""
Health check routes
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Crypto Futures Signal API"
    }


@router.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "Crypto Futures Signal API",
        "version": "1.0.0",
        "description": "Production-ready crypto futures signal API with multi-provider integration",
        "endpoints": {
            "health": "/health",
            "signals": "/signals/{symbol}",
            "market": "/market/{symbol}",
            "gpt_schema": "/gpt/action-schema"
        }
    }
