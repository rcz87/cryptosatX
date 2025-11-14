"""
Batch Operations Routes
Provides endpoints for fetching data untuk multiple symbols efficiently dengan caching optimization.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from app.services.cached_data_service import cached_data_service
from app.utils.logger import default_logger

router = APIRouter()
logger = default_logger


class BatchSignalRequest(BaseModel):
    """Request model untuk batch signal fetching"""
    symbols: List[str]
    mode: Optional[str] = "aggressive"
    include_ai_verdict: Optional[bool] = False


class BatchPriceRequest(BaseModel):
    """Request model untuk batch price fetching"""
    symbols: List[str]


@router.post("/batch/signals", summary="Get Signals for Multiple Symbols")
async def get_batch_signals(request: BatchSignalRequest) -> Dict[str, Any]:
    """
    Fetch trading signals untuk multiple cryptocurrency symbols simultaneously.
    Menggunakan caching layer untuk optimal performance.
    
    Args:
    - symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH', 'SOL'])
    - mode: Signal mode - 'conservative', 'aggressive', or 'ultra' (default: 'aggressive')
    - include_ai_verdict: Include AI verdict analysis (default: False)
    
    Returns:
    - Batch response dengan signals untuk each symbol
    - Performance metrics (cache hits, execution time)
    
    Example:
    ```json
    {
      "symbols": ["BTC", "ETH", "SOL", "XRP", "BNB"],
      "mode": "aggressive",
      "include_ai_verdict": false
    }
    ```
    """
    try:
        if not request.symbols or len(request.symbols) == 0:
            raise HTTPException(status_code=400, detail="At least one symbol required")
        
        if len(request.symbols) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols per batch request")
        
        # Import signal engine
        from app.core.rpc_dispatcher import dispatch_rpc_operation
        
        # Fetch signals concurrently untuk all symbols
        tasks = []
        for symbol in request.symbols:
            task = dispatch_rpc_operation(
                "signals.get",
                {"symbol": symbol, "mode": request.mode}
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        signals = {}
        errors = {}
        cache_hits = 0
        
        for idx, (symbol, result) in enumerate(zip(request.symbols, results)):
            if isinstance(result, Exception):
                errors[symbol.upper()] = str(result)
                continue
            
            if result.get("ok"):
                signals[symbol.upper()] = result.get("data", {})
                if "cached" in result.get("data", {}):
                    cache_hits += 1
            else:
                errors[symbol.upper()] = result.get("error", "Unknown error")
        
        success_count = len(signals)
        total_count = len(request.symbols)
        
        return {
            "ok": True,
            "data": {
                "signals": signals,
                "errors": errors if errors else None,
                "summary": {
                    "total_requested": total_count,
                    "successful": success_count,
                    "failed": len(errors),
                    "success_rate_percent": round((success_count / total_count * 100), 2),
                },
                "performance": {
                    "cache_optimization": f"{cache_hits}/{total_count} from cache",
                    "cache_hit_rate_percent": round((cache_hits / total_count * 100), 2) if total_count > 0 else 0
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch signal fetching: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to fetch batch signals")


@router.post("/batch/prices", summary="Get Prices for Multiple Symbols")
async def get_batch_prices(request: BatchPriceRequest) -> Dict[str, Any]:
    """
    Fetch spot prices untuk multiple cryptocurrency symbols simultaneously.
    Uses 5-second cache untuk optimal performance.
    
    Args:
    - symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH', 'SOL'])
    
    Returns:
    - Batch response dengan prices untuk each symbol
    - Cache statistics
    
    Example:
    ```json
    {
      "symbols": ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOT"]
    }
    ```
    """
    try:
        if not request.symbols or len(request.symbols) == 0:
            raise HTTPException(status_code=400, detail="At least one symbol required")
        
        if len(request.symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols per batch request")
        
        # Fetch prices concurrently dengan caching
        tasks = []
        for symbol in request.symbols:
            task = cached_data_service.get_spot_price_cached(symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        prices = {}
        errors = {}
        
        for symbol, result in zip(request.symbols, results):
            if isinstance(result, Exception):
                errors[symbol.upper()] = "Service error"
                continue
            
            if result.get("success"):
                prices[symbol.upper()] = {
                    "price": result.get("price", 0),
                    "source": result.get("source", "unknown")
                }
            else:
                errors[symbol.upper()] = result.get("error", "Unknown error")
        
        success_count = len(prices)
        total_count = len(request.symbols)
        
        return {
            "ok": True,
            "data": {
                "prices": prices,
                "errors": errors if errors else None,
                "summary": {
                    "total_requested": total_count,
                    "successful": success_count,
                    "failed": len(errors),
                    "success_rate_percent": round((success_count / total_count * 100), 2),
                },
                "cache_info": {
                    "ttl_seconds": 5,
                    "description": "Prices cached for 5 seconds for high-frequency updates"
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch price fetching: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to fetch batch prices")


@router.get("/batch/quick-scan", summary="Quick Market Scan")
async def quick_market_scan(
    symbols: str = Query(
        default="BTC,ETH,SOL,XRP,BNB",
        description="Comma-separated list of symbols"
    )
) -> Dict[str, Any]:
    """
    Quick market scan untuk popular cryptocurrencies.
    Returns prices, signals, dan market sentiment dalam satu request.
    Optimized dengan aggressive caching.
    
    Query Parameters:
    - symbols: Comma-separated symbols (default: BTC,ETH,SOL,XRP,BNB)
    
    Example:
    GET /batch/quick-scan?symbols=BTC,ETH,SOL
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbol_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 symbols for quick scan")
        
        # Fetch prices concurrently
        price_tasks = [
            cached_data_service.get_spot_price_cached(sym)
            for sym in symbol_list
        ]
        
        # Fetch fear & greed index
        fear_greed_task = cached_data_service.get_fear_greed_cached()
        
        # Execute all tasks concurrently
        all_tasks = price_tasks + [fear_greed_task]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Process price results
        price_results = results[:-1]
        fear_greed_result = results[-1]
        
        market_overview = {}
        for symbol, price_data in zip(symbol_list, price_results):
            if isinstance(price_data, Exception) or not price_data.get("success"):
                continue
            
            market_overview[symbol] = {
                "price": price_data.get("price", 0),
                "source": price_data.get("source", "unknown")
            }
        
        # Add fear & greed
        market_sentiment = "neutral"
        if not isinstance(fear_greed_result, Exception) and fear_greed_result.get("success"):
            market_sentiment = fear_greed_result.get("sentiment", "neutral")
        
        return {
            "ok": True,
            "data": {
                "market_overview": market_overview,
                "market_sentiment": market_sentiment,
                "fear_greed_index": fear_greed_result if not isinstance(fear_greed_result, Exception) else None,
                "symbols_scanned": len(market_overview),
                "cache_optimized": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick market scan: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to perform market scan")
