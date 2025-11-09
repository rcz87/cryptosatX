# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Signal History Routes
Track and analyze historical signals - does not modify existing routes
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.storage.signal_history import signal_history
from app.middleware.auth import get_api_key, get_optional_api_key
from app.utils.logger import default_logger, log_api_call
import time

router = APIRouter(prefix="/history", tags=["Signal History"])


@router.get("/signals")
async def get_signal_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTC)"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type: LONG, SHORT, NEUTRAL"),
    limit: int = Query(50, ge=1, le=500, description="Max number of signals to return"),
    api_key: str = Depends(get_optional_api_key)
):
    """
    📜 **Get Signal History** - Review past trading signals
    
    Retrieve historical signals for analysis, backtesting, or performance tracking.
    
    ## **Filters:**
    - **symbol**: Get signals for specific crypto (e.g., `BTC`, `ETH`)
    - **signal_type**: Filter by `LONG`, `SHORT`, or `NEUTRAL`
    - **limit**: Number of signals to return (max 500)
    
    ## **Use Cases:**
    - Performance tracking and analysis
    - Backtesting signal accuracy
    - Pattern recognition across signals
    - Learning from historical decisions
    
    ## **Examples:**
    ```
    GET /history/signals?symbol=BTC&limit=20
    GET /history/signals?signal_type=LONG&limit=50
    GET /history/signals?symbol=ETH&signal_type=SHORT
    ```
    """
    start_time = time.time()
    
    try:
        result = await signal_history.get_history(
            symbol=symbol,
            limit=limit,
            signal_type=signal_type
        )
        
        duration = time.time() - start_time
        log_api_call(
            default_logger,
            "/history/signals",
            symbol=symbol,
            duration=duration,
            status="success",
            extra_data={
                "total": result.get("total", 0),
                "filtered": result.get("filtered", 0)
            }
        )
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve history: {str(e)}",
            "signals": []
        }


@router.get("/statistics")
async def get_signal_statistics(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    api_key: str = Depends(get_optional_api_key)
):
    """
    📊 **Signal Statistics** - Analyze signal patterns and performance
    
    Get aggregate statistics about generated signals:
    - Total signals generated
    - Distribution (LONG/SHORT/NEUTRAL percentages)
    - Average signal scores
    - Symbol distribution
    - Date ranges
    
    ## **Examples:**
    ```
    GET /history/statistics
    GET /history/statistics?symbol=BTC
    ```
    """
    start_time = time.time()
    
    try:
        result = await signal_history.get_statistics(symbol=symbol)
        
        duration = time.time() - start_time
        log_api_call(
            default_logger,
            "/history/statistics",
            symbol=symbol,
            duration=duration,
            status="success",
            extra_data={"total": result.get("total", 0)}
        )
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get statistics: {str(e)}"
        }


@router.delete("/clear")
async def clear_signal_history(
    confirm: bool = Query(False, description="Must be true to clear history"),
    api_key: str = Depends(get_api_key)
):
    """
    🗑️ **Clear Signal History** - Delete all stored signals
    
    ⚠️ **WARNING**: This action cannot be undone!
    
    Requires API key authentication and explicit confirmation.
    
    ## **Usage:**
    ```
    DELETE /history/clear?confirm=true
    ```
    
    Set `confirm=true` and provide API key via `X-API-Key` header.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set confirm=true to clear history."
        )
    
    result = await signal_history.clear_history(confirm=True)
    
    log_api_call(
        default_logger,
        "/history/clear",
        duration=0,
        status="success" if result.get("success") else "error"
    )
    
    return result


@router.get("/info")
async def history_info():
    """
    📚 **History System Information**
    
    Learn about the signal history storage system.
    """
    return {
        "name": "Signal History System",
        "description": "Automatic storage of all generated trading signals",
        "features": [
            "Automatic signal capture",
            "Filter by symbol and signal type",
            "Statistical analysis",
            "Performance tracking",
            "Backtesting support"
        ],
        "storage": {
            "type": "JSON file storage",
            "location": "signal_data/signal_history.json",
            "max_signals": 1000,
            "retention": "Rolling window (newest 1000 signals)"
        },
        "endpoints": {
            "GET /history/signals": "Retrieve signal history",
            "GET /history/statistics": "Get aggregate statistics",
            "DELETE /history/clear": "Clear all history (requires API key)"
        }
    }
