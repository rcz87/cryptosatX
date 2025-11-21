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
    """
    return {
        "status": "healthy",
        "timestamp": get_wib_time(),
        "service": "Crypto Futures Signal API"
    }
