"""
GPT Actions Endpoint for Scalping Analysis
Optimized for natural language queries from ChatGPT
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import copy
import logging
from app.utils.logger import get_wib_time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scalping", tags=["Scalping"])


def compress_for_gpt_mode(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compress scalping analysis result for GPT Actions (< 50KB target)
    
    Reduces response size by:
    - Trimming orderbook to top 3 levels only
    - Compressing liquidations to summary metrics
    - Simplifying volume delta to net flow
    - Reducing whale/smart money to directional bias
    - Removing verbose metadata and debug info
    """
    compressed = copy.deepcopy(result)
    
    # 1. Compress orderbook_history - Keep only top 3 bid/ask levels
    if compressed.get("orderbook_history"):
        ob = compressed["orderbook_history"]
        if ob.get("bids") and isinstance(ob["bids"], list):
            ob["bids"] = ob["bids"][:3]
        if ob.get("asks") and isinstance(ob["asks"], list):
            ob["asks"] = ob["asks"][:3]
        # Remove verbose metadata
        ob.pop("metadata", None)
        ob.pop("provider", None)
        ob.pop("raw_data", None)
    
    # 2. Compress liquidations - Summary metrics only
    if compressed.get("liquidations"):
        liq = compressed["liquidations"]
        if liq.get("data") and isinstance(liq["data"], list):
            # Keep only summary stats
            events = liq["data"]
            total_long = sum(e.get("longLiquidation", 0) for e in events)
            total_short = sum(e.get("shortLiquidation", 0) for e in events)
            total_volume = total_long + total_short
            
            liq["data"] = {
                "summary": {
                    "totalLongLiquidations": total_long,
                    "totalShortLiquidations": total_short,
                    "totalVolume": total_volume,
                    "netDirection": "LONG_SQUEEZE" if total_long > total_short else "SHORT_SQUEEZE",
                    "ratio": round(total_long / total_short, 2) if total_short > 0 else 999,
                    "eventCount": len(events)
                }
            }
        liq.pop("metadata", None)
        liq.pop("provider", None)
    
    # 3. Compress volume_delta - Net flow only
    if compressed.get("volume_delta"):
        vd = compressed["volume_delta"]
        if vd.get("data"):
            # Keep only net metrics, remove per-exchange breakdown
            vd_data = vd["data"]
            if isinstance(vd_data, dict):
                vd["data"] = {
                    "netBuys": vd_data.get("netBuys", 0),
                    "netSells": vd_data.get("netSells", 0),
                    "netDelta": vd_data.get("netDelta", 0),
                    "signal": vd_data.get("signal", "NEUTRAL")
                }
        vd.pop("exchanges", None)
        vd.pop("intervals", None)
        vd.pop("metadata", None)
    
    # 4. Compress whale_positions - Bias + confidence only
    if compressed.get("whale_positions"):
        wp = compressed["whale_positions"]
        if wp.get("topPositions") and isinstance(wp["topPositions"], list):
            positions = wp["topPositions"]
            long_value = sum(p.get("positionValue", 0) for p in positions if p.get("side") == "LONG")
            short_value = sum(p.get("positionValue", 0) for p in positions if p.get("side") == "SHORT")
            total_value = long_value + short_value
            
            if total_value > 0:
                ratio = long_value / short_value if short_value > 0 else 999
                bias = "LONG" if ratio > 1.5 else "SHORT" if ratio < 0.67 else "NEUTRAL"
                
                wp["topPositions"] = {
                    "bias": bias,
                    "longValue": long_value,
                    "shortValue": short_value,
                    "ratio": round(ratio, 2) if ratio != 999 else 999,
                    "positionCount": len(positions)
                }
        wp.pop("metadata", None)
        wp.pop("raw", None)
    
    # 5. Compress smart_money - Directional signal only
    if compressed.get("smart_money"):
        sm = compressed["smart_money"]
        if sm.get("analysis"):
            analysis = sm["analysis"]
            # Keep only essential signal metrics
            compressed_analysis = {
                "signal": analysis.get("signal", "NEUTRAL"),
                "confidence": analysis.get("confidence", 0),
                "bias": analysis.get("institutional_bias", {}).get("direction", "NEUTRAL"),
                "score": analysis.get("smart_money_score", 0)
            }
            sm["analysis"] = compressed_analysis
        sm.pop("timeframes", None)
        sm.pop("detailed_analysis", None)
        sm.pop("metadata", None)
    
    # 6. Compress sentiment - Key metrics only
    if compressed.get("sentiment"):
        sent = compressed["sentiment"]
        if sent.get("data"):
            sent_data = sent["data"]
            compressed_sent = {
                "galaxyScore": sent_data.get("galaxy_score", 0),
                "altRank": sent_data.get("alt_rank", 0),
                "sentiment": sent_data.get("sentiment", "NEUTRAL"),
                "socialVolume24h": sent_data.get("social_volume_24h", 0)
            }
            sent["data"] = compressed_sent
        sent.pop("trending_topics", None)
        sent.pop("raw", None)
    
    # 7. Compress OHLCV - Last 3 candles only
    if compressed.get("ohlcv"):
        ohlcv = compressed["ohlcv"]
        if ohlcv.get("data") and isinstance(ohlcv["data"], list):
            ohlcv["data"] = ohlcv["data"][-3:]  # Last 3 candles only
        ohlcv.pop("metadata", None)
    
    # 8. Compress trades - Summary only
    if compressed.get("trades"):
        trades = compressed["trades"]
        if trades.get("data") and isinstance(trades["data"], list):
            trade_list = trades["data"]
            buy_volume = sum(t.get("size", 0) for t in trade_list if t.get("side") == "BUY")
            sell_volume = sum(t.get("size", 0) for t in trade_list if t.get("side") == "SELL")
            
            trades["data"] = {
                "buyVolume": buy_volume,
                "sellVolume": sell_volume,
                "netVolume": buy_volume - sell_volume,
                "tradeCount": len(trade_list),
                "bias": "BUY" if buy_volume > sell_volume else "SELL"
            }
        trades.pop("metadata", None)
    
    # 9. Compress RSI - Current value only (remove history array)
    if compressed.get("rsi"):
        rsi = compressed["rsi"]
        # Keep only current RSI and signal, remove massive history array
        compressed_rsi = {
            "currentRsi": rsi.get("currentRsi", 0),
            "signal": rsi.get("signal", "NEUTRAL"),
            "success": rsi.get("success", True)
        }
        compressed["rsi"] = compressed_rsi
    
    # 10. Compress Fear/Greed - Current index only (remove history array)
    if compressed.get("fear_greed"):
        fg = compressed["fear_greed"]
        # Keep only current index and sentiment, remove massive history array
        compressed_fg = {
            "currentIndex": fg.get("currentIndex", 50),
            "sentiment": fg.get("sentiment", "NEUTRAL"),
            "success": fg.get("success", True)
        }
        compressed["fear_greed"] = compressed_fg
    
    # 11. Compress funding - Essential metrics only
    if compressed.get("funding"):
        fund = compressed["funding"]
        if isinstance(fund, dict):
            compressed_fund = {
                "currentRate": fund.get("currentRate", fund.get("fundingRate", 0)),
                "predictedRate": fund.get("predictedRate", 0),
                "signal": fund.get("signal", "NEUTRAL"),
                "success": fund.get("success", True)
            }
            compressed["funding"] = compressed_fund
    
    # 12. Compress Long/Short Ratio - Summary only
    if compressed.get("ls_ratio"):
        lsr = compressed["ls_ratio"]
        if isinstance(lsr, dict):
            compressed_lsr = {
                "ratio": lsr.get("ratio", lsr.get("longShortRatio", 1)),
                "longPercent": lsr.get("longPercent", lsr.get("longAccount", 50)),
                "shortPercent": lsr.get("shortPercent", lsr.get("shortAccount", 50)),
                "signal": lsr.get("signal", "NEUTRAL"),
                "success": lsr.get("success", True)
            }
            compressed["ls_ratio"] = compressed_lsr
    
    # 13. Remove any remaining verbose fields
    for key in list(compressed.keys()):
        if compressed.get(key) and isinstance(compressed[key], dict):
            compressed[key].pop("debug", None)
            compressed[key].pop("raw_response", None)
            compressed[key].pop("provider_metadata", None)
            compressed[key].pop("history", None)  # Remove all history arrays
            compressed[key].pop("metadata", None)
    
    return compressed


class ScalpingAnalysisRequest(BaseModel):
    """Request model for scalping analysis"""
    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH, SOL, XRP)")
    mode: Optional[str] = Field(
        default="aggressive",
        description="Signal mode: 'conservative'/'1' (safe), 'aggressive'/'2' (balanced, default), 'ultra'/'3' (maximum signals)"
    )
    include_smart_money: bool = Field(default=True, description="Include smart money analysis (takes ~25s)")
    include_whale_positions: bool = Field(default=True, description="Include Hyperliquid whale positions (DEX institutional bias)")
    include_fear_greed: bool = Field(default=True, description="Include fear & greed index")
    include_coinapi: bool = Field(default=True, description="Include extended CoinAPI data (OHLCV, trades)")
    include_sentiment: bool = Field(default=True, description="Include LunarCrush sentiment and social momentum")
    gpt_mode: bool = Field(default=False, description="GPT Actions optimization mode - reduces response size to < 50KB by limiting data verbosity")


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
        "timestamp": get_wib_time(),
        "ready": False,
        "critical_data_available": 0,
        "recommended_data_available": 0,
        "summary": {}
    }
    
    try:
        # Adjust limits based on GPT mode
        liquidations_limit = 5 if request.gpt_mode else 20
        funding_limit = 3 if request.gpt_mode else 10
        ls_ratio_limit = 3 if request.gpt_mode else 10
        ohlcv_limit = 6 if request.gpt_mode else 24
        trades_limit = 20 if request.gpt_mode else 100

        # Fetch all layers concurrently
        tasks = []

        # CRITICAL layers
        tasks.append(("price", coinapi.get_spot_price(symbol)))
        tasks.append(("orderbook_history", coinglass_comprehensive.get_orderbook_detailed_history(
            exchange="Binance", symbol=pair, interval="1h", limit=1
        )))
        tasks.append(("liquidations", coinglass_comprehensive.get_liquidation_aggregated_history(
            symbol=symbol, exchange_list="Binance", interval="1m", limit=liquidations_limit
        )))
        tasks.append(("rsi", coinglass_comprehensive.get_rsi_indicator(
            exchange="Binance", symbol=pair, interval="1h"
        )))
        tasks.append(("volume_delta", coinglass_comprehensive.get_taker_buy_sell_volume_exchange_list(
            symbol=symbol
        )))

        # RECOMMENDED layers
        tasks.append(("funding", coinglass_comprehensive.get_funding_rate_history(
            exchange="Binance", symbol=pair, interval="h8", limit=funding_limit
        )))
        tasks.append(("ls_ratio", coinglass_comprehensive.get_top_long_short_position_ratio_history(
            exchange="Binance", symbol=pair, interval="h1", limit=ls_ratio_limit
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
            tasks.append(("ohlcv", coinapi.get_ohlcv_latest(symbol, period="1HRS", limit=ohlcv_limit)))
            tasks.append(("trades", coinapi.get_trades(symbol, limit=trades_limit)))

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
        
        # Apply GPT mode compression if enabled
        if request.gpt_mode:
            result = compress_for_gpt_mode(result)
        
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
    Optimized for GPT Actions with response size < 40 KB.

    **Response time:** ~5-8 seconds (vs ~30s for full analysis)
    """)
async def quick_scalping_check(symbol: str):
    """
    Quick scalping check - only critical layers, no smart money
    Fast response for GPT Actions rapid queries
    Automatically uses GPT mode for size optimization
    """
    request = ScalpingAnalysisRequest(
        symbol=symbol,
        include_smart_money=False,
        include_whale_positions=False,
        include_fear_greed=False,
        include_coinapi=False,
        include_sentiment=False,
        gpt_mode=True  # Enable GPT mode for size optimization
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
