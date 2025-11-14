"""
GPT Actions Endpoint for Scalping Analysis
Optimized for natural language queries from ChatGPT
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

router = APIRouter(prefix="/scalping", tags=["Scalping"])


class ScalpingAnalysisRequest(BaseModel):
    """Request model for scalping analysis"""
    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH, SOL, XRP)")
    include_smart_money: bool = Field(default=True, description="Include smart money analysis (takes ~25s)")
    include_fear_greed: bool = Field(default=True, description="Include fear & greed index")


class ScalpingAnalysisResponse(BaseModel):
    """Response model for scalping analysis"""
    symbol: str
    timestamp: str
    ready: bool
    critical_data_available: int
    recommended_data_available: int
    
    # Data layers
    price: Optional[Dict[str, Any]] = None
    orderbook: Optional[Dict[str, Any]] = None
    orderbook_history: Optional[Dict[str, Any]] = None
    liquidations: Optional[Dict[str, Any]] = None
    funding: Optional[Dict[str, Any]] = None
    ls_ratio: Optional[Dict[str, Any]] = None
    rsi: Optional[Dict[str, Any]] = None
    volume_delta: Optional[Dict[str, Any]] = None
    smart_money: Optional[Dict[str, Any]] = None
    fear_greed: Optional[Dict[str, Any]] = None
    
    # Analysis summary
    summary: Dict[str, Any]


@router.post("/analyze", 
    response_model=ScalpingAnalysisResponse,
    summary="Complete Scalping Analysis",
    description="""
    **🎯 Get complete real-time scalping analysis for any cryptocurrency**
    
    This endpoint aggregates data from 8 critical layers:
    
    **CRITICAL (polling every 3-5s):**
    - 📊 Price & OHLCV - Real-time momentum
    - ⚡ Orderbook Pressure - Bid/Ask imbalance
    - 💣 Liquidations - Panic/Squeeze signals
    - 📈 RSI & Volume Delta - Entry timing
    
    **RECOMMENDED (polling 1-10m):**
    - 💰 Funding Rate - Position bias
    - 🧮 Long/Short Ratio - Contrarian signals
    - 🐋 Smart Money - Whale activity
    
    **OPTIONAL (polling 1h):**
    - 🧊 Fear & Greed - Macro sentiment
    
    **Example queries for GPT:**
    - "Give me scalping analysis for XRP"
    - "What's the entry for SOL right now?"
    - "Analyze BTC for quick scalp"
    """)
async def analyze_for_scalping(request: ScalpingAnalysisRequest):
    """
    Complete scalping analysis with all data layers
    Optimized for GPT Actions natural language queries
    """
    from app.services.coinapi_service import CoinAPIService
    from app.services.coinglass_comprehensive_service import coinglass_comprehensive
    from app.services.smart_money_service import smart_money_service
    from app.utils.symbol_normalizer import normalize_symbol
    
    # Initialize CoinAPI service
    coinapi = CoinAPIService()
    
    symbol = request.symbol.upper()
    pair = f"{symbol}USDT"
    
    result = {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "ready": False,
        "critical_data_available": 0,
        "recommended_data_available": 0,
        "summary": {}
    }
    
    try:
        # Fetch all layers concurrently
        tasks = []
        
        # CRITICAL layers
        tasks.append(("price", coinapi.get_spot_price(symbol)))
        tasks.append(("orderbook_history", coinglass_comprehensive.get_orderbook_detailed_history(
            exchange="Binance", symbol=pair, interval="1h", limit=1
        )))
        tasks.append(("liquidations", coinglass_comprehensive.get_liquidation_aggregated_history(
            symbol=symbol, exchange_list="Binance", interval="1m", limit=20
        )))
        tasks.append(("rsi", coinglass_comprehensive.get_rsi_indicator(
            exchange="Binance", symbol=pair, interval="1h"
        )))
        tasks.append(("volume_delta", coinglass_comprehensive.get_taker_buy_sell_volume_exchange_list(
            symbol=symbol
        )))
        
        # RECOMMENDED layers
        tasks.append(("funding", coinglass_comprehensive.get_funding_rate_history(
            exchange="Binance", symbol=pair, interval="h8", limit=10
        )))
        tasks.append(("ls_ratio", coinglass_comprehensive.get_top_long_short_position_ratio_history(
            exchange="Binance", symbol=pair, interval="h1", limit=10
        )))
        
        # OPTIONAL - Smart Money (heavy, optional)
        if request.include_smart_money:
            tasks.append(("smart_money", smart_money_service.scan_smart_money(symbol)))
        
        # OPTIONAL - Fear & Greed
        if request.include_fear_greed:
            tasks.append(("fear_greed", coinglass_comprehensive.get_fear_greed_index()))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        # Map results back
        for i, (key, _) in enumerate(tasks):
            if not isinstance(results[i], Exception) and results[i]:
                result[key] = results[i]
        
        # Count availability
        critical_keys = ["price", "orderbook_history", "liquidations", "rsi", "volume_delta"]
        recommended_keys = ["funding", "ls_ratio"]
        if request.include_smart_money:
            recommended_keys.append("smart_money")
        
        critical_available = sum(1 for k in critical_keys if result.get(k))
        recommended_available = sum(1 for k in recommended_keys if result.get(k))
        
        result["critical_data_available"] = critical_available
        result["recommended_data_available"] = recommended_available
        result["ready"] = critical_available >= 4  # Need at least 4/5 critical
        
        # Generate summary
        result["summary"] = {
            "data_layers": {
                "critical": f"{critical_available}/{len(critical_keys)}",
                "recommended": f"{recommended_available}/{len(recommended_keys)}",
            },
            "readiness": "READY" if result["ready"] else "PARTIAL",
            "message": (
                "All critical data available - ready for scalping execution"
                if critical_available == len(critical_keys)
                else f"Partial data - {critical_available}/{len(critical_keys)} critical layers available"
            )
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scalping analysis failed: {str(e)}"
        )


@router.get("/quick/{symbol}",
    summary="Quick Scalping Check",
    description="""
    **⚡ Quick scalping readiness check (no smart money analysis)**
    
    Fast endpoint for checking if critical data is available.
    Perfect for rapid polling without heavy processing.
    
    **Response time:** ~5-8 seconds (vs ~30s for full analysis)
    """)
async def quick_scalping_check(symbol: str):
    """
    Quick scalping check - only critical layers, no smart money
    Fast response for GPT Actions rapid queries
    """
    request = ScalpingAnalysisRequest(
        symbol=symbol,
        include_smart_money=False,
        include_fear_greed=False
    )
    
    return await analyze_for_scalping(request)


@router.get("/info",
    summary="Scalping Engine Info",
    description="Get information about the scalping engine and available data layers")
async def scalping_info():
    """Information about scalping engine capabilities"""
    return {
        "name": "CryptoSatX Scalping Engine",
        "version": "2.0.0",
        "data_layers": {
            "critical": [
                {"name": "Price & OHLCV", "polling": "3s", "provider": "CoinAPI"},
                {"name": "Orderbook Pressure", "polling": "3-5s", "provider": "CoinAPI"},
                {"name": "Liquidations", "polling": "5s", "provider": "CoinGlass"},
                {"name": "RSI Indicator", "polling": "5s", "provider": "CoinGlass"},
                {"name": "Volume Delta", "polling": "5s", "provider": "CoinGlass"},
            ],
            "recommended": [
                {"name": "Funding Rate", "polling": "1-2m", "provider": "CoinGlass"},
                {"name": "Long/Short Ratio", "polling": "1m", "provider": "CoinGlass"},
                {"name": "Smart Money", "polling": "10m", "provider": "Internal"},
            ],
            "optional": [
                {"name": "Fear & Greed Index", "polling": "1h", "provider": "CoinGlass"},
            ]
        },
        "endpoints": {
            "/scalping/analyze": "Complete analysis with all layers (~30s)",
            "/scalping/quick/{symbol}": "Quick check without smart money (~8s)",
            "/scalping/info": "This endpoint"
        },
        "supported_symbols": "All major cryptocurrencies (BTC, ETH, SOL, XRP, etc)",
        "response_format": "JSON optimized for GPT Actions"
    }
