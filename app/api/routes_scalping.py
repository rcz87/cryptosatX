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
    include_whale_positions: bool = Field(default=True, description="Include Hyperliquid whale positions (DEX institutional bias)")
    include_fear_greed: bool = Field(default=True, description="Include fear & greed index")
    include_coinapi: bool = Field(default=True, description="Include extended CoinAPI data (OHLCV, trades)")
    include_sentiment: bool = Field(default=True, description="Include LunarCrush sentiment and social momentum")


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
    whale_positions: Optional[Dict[str, Any]] = None
    fear_greed: Optional[Dict[str, Any]] = None
    ohlcv: Optional[Dict[str, Any]] = None
    trades: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    
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
        
        # OPTIONAL - Hyperliquid Whale Positions (Layer 7.5)
        if request.include_whale_positions:
            tasks.append(("whale_positions", coinglass_comprehensive.get_hyperliquid_whale_positions()))
        
        # OPTIONAL - Fear & Greed
        if request.include_fear_greed:
            tasks.append(("fear_greed", coinglass_comprehensive.get_fear_greed_index()))
        
        # OPTIONAL - Extended CoinAPI (OHLCV + Trades)
        if request.include_coinapi:
            tasks.append(("ohlcv", coinapi.get_ohlcv_latest(symbol, period="1HRS", limit=24)))
            tasks.append(("trades", coinapi.get_trades(symbol, limit=100)))
        
        # OPTIONAL - LunarCrush Sentiment
        if request.include_sentiment:
            from app.services.lunarcrush_service import lunarcrush_service
            tasks.append(("sentiment", lunarcrush_service.get_coin_sentiment(symbol)))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        # Map results back
        for i, (key, _) in enumerate(tasks):
            if not isinstance(results[i], Exception) and results[i]:
                result[key] = results[i]
        
        # Count availability
        critical_keys = ["price", "orderbook_history", "liquidations", "rsi", "volume_delta"]
        recommended_keys = ["funding", "ls_ratio"]
        optional_keys = []
        if request.include_smart_money:
            optional_keys.append("smart_money")
        if request.include_whale_positions:
            optional_keys.append("whale_positions")
        if request.include_fear_greed:
            optional_keys.append("fear_greed")
        if request.include_coinapi:
            optional_keys.extend(["ohlcv", "trades"])
        if request.include_sentiment:
            optional_keys.append("sentiment")
        
        critical_available = sum(1 for k in critical_keys if result.get(k))
        recommended_available = sum(1 for k in recommended_keys if result.get(k))
        optional_available = sum(1 for k in optional_keys if result.get(k))
        
        result["critical_data_available"] = critical_available
        result["recommended_data_available"] = recommended_available
        result["ready"] = critical_available >= 4  # Need at least 4/5 critical
        
        # Calculate whale bias if available
        whale_bias_summary = None
        if result.get("whale_positions") and result["whale_positions"].get("success"):
            wp = result["whale_positions"]
            positions = wp.get("topPositions", [])
            if positions:
                long_value = sum(p["positionValue"] for p in positions if p["side"] == "LONG")
                short_value = sum(p["positionValue"] for p in positions if p["side"] == "SHORT")
                total_value = long_value + short_value
                
                if total_value > 0:
                    long_pct = (long_value / total_value) * 100
                    short_pct = (short_value / total_value) * 100
                    ratio = long_value / short_value if short_value > 0 else 999
                    
                    if ratio > 1.5:
                        bias = "LONG"
                        confidence = min((ratio - 1) / 2, 0.9)
                    elif ratio < 0.67:
                        bias = "SHORT"
                        confidence = min((1/ratio - 1) / 2, 0.9)
                    else:
                        bias = "NEUTRAL"
                        confidence = 0.5
                    
                    whale_bias_summary = {
                        "bias": bias,
                        "longValue": long_value,
                        "shortValue": short_value,
                        "longPercent": long_pct,
                        "shortPercent": short_pct,
                        "ratio": ratio if ratio != 999 else 999,
                        "confidence": round(confidence, 2),
                        "interpretation": f"Whales {bias} bias ({long_pct:.1f}% LONG vs {short_pct:.1f}% SHORT)"
                    }
        
        # Generate summary
        result["summary"] = {
            "data_layers": {
                "critical": f"{critical_available}/{len(critical_keys)}",
                "recommended": f"{recommended_available}/{len(recommended_keys)}",
                "optional": f"{optional_available}/{len(optional_keys)}"
            },
            "readiness": "READY" if result["ready"] else "PARTIAL",
            "message": (
                "All critical data available - ready for scalping execution"
                if critical_available == len(critical_keys)
                else f"Partial data - {critical_available}/{len(critical_keys)} critical layers available"
            )
        }
        
        # Add whale bias to summary if available
        if whale_bias_summary:
            result["summary"]["whale_bias"] = whale_bias_summary
        
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
        include_whale_positions=False,
        include_fear_greed=False,
        include_coinapi=False,
        include_sentiment=False
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
                {"name": "OHLCV Trend Analysis", "polling": "on-demand", "provider": "CoinAPI"},
                {"name": "Recent Trades", "polling": "on-demand", "provider": "CoinAPI"},
                {"name": "Sentiment Analysis", "polling": "on-demand", "provider": "LunarCrush"},
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
