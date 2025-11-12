"""
GPT Actions Compatible Routes
Flat parameter structure for GPT Actions compatibility
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

router = APIRouter(prefix="/gpt", tags=["GPT Actions"])


class GPTSignalRequest(BaseModel):
    """Flat structure for GPT Actions"""
    symbol: str = Field(..., description="Cryptocurrency symbol (BTC, ETH, SOL, etc.)")
    debug: Optional[bool] = Field(False, description="Enable debug mode")


class GPTSmartMoneyRequest(BaseModel):
    """Flat structure for smart money scan"""
    min_accumulation_score: Optional[int] = Field(5, ge=0, le=10)


class GPTMSSRequest(BaseModel):
    """Flat structure for MSS discovery"""
    min_mss_score: Optional[int] = Field(75, ge=0, le=100)
    max_results: Optional[int] = Field(10, ge=1, le=50)


@router.post("/signal", summary="Get Trading Signal (GPT Actions Compatible)")
async def get_signal_gpt(request: GPTSignalRequest) -> Dict[str, Any]:
    """
    Get trading signal - GPT Actions flat parameter version
    
    This endpoint uses flat parameters instead of nested args object
    for compatibility with GPT Actions.
    """
    from app.core.signal_engine import signal_engine
    
    try:
        debug = request.debug if request.debug is not None else False
        result = await signal_engine.build_signal(request.symbol, debug=debug)
        return {
            "ok": True,
            "data": result,
            "operation": "signals.get"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-money-scan", summary="Smart Money Scan (GPT Actions Compatible)")
async def smart_money_scan_gpt(request: GPTSmartMoneyRequest) -> Dict[str, Any]:
    """
    Scan for smart money accumulation/distribution
    
    Flat parameter version for GPT Actions compatibility.
    """
    from app.services.smart_money_service import smart_money_service
    
    try:
        result = await smart_money_service.scan_all_coins(
            min_accumulation_score=request.min_accumulation_score
        )
        return {
            "ok": True,
            "data": result,
            "operation": "smart_money.scan"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mss-discover", summary="MSS Discovery (GPT Actions Compatible)")
async def mss_discover_gpt(request: GPTMSSRequest) -> Dict[str, Any]:
    """
    Discover high-potential cryptocurrencies using MSS
    
    Flat parameter version for GPT Actions compatibility.
    """
    from app.services.mss_service import mss_service
    
    try:
        result = await mss_service.discover_gems(
            min_mss_score=request.min_mss_score,
            max_results=request.max_results
        )
        return {
            "ok": True,
            "data": result,
            "operation": "mss.discover"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health Check (GPT Actions Compatible)")
async def health_check_gpt() -> Dict[str, Any]:
    """Simple health check for GPT Actions"""
    from app.core.signal_engine import signal_engine
    
    return {
        "ok": True,
        "data": {
            "status": "healthy",
            "version": "3.0.0",
            "message": "CryptoSatX API is operational"
        },
        "operation": "health.check"
    }
