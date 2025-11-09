# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Enhanced GPT Integration Routes
Advanced GPT Actions integration - complements existing /gpt/action-schema
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
import os
from app.core.signal_engine import signal_engine
from app.services.smc_analyzer import smc_analyzer
from app.storage.signal_history import signal_history
from app.services.telegram_notifier import telegram_notifier
from app.middleware.auth import get_optional_api_key, get_api_key  # Import both auth functions
from app.utils.logger import default_logger, log_api_call
import time

router = APIRouter(prefix="/gpt", tags=["Enhanced GPT Integration"])


@router.get("/actions/comprehensive-schema")
async def get_comprehensive_gpt_schema():
    """
    📋 **Comprehensive GPT Actions Schema** - Full API capabilities
    
    Extended OpenAPI schema including all CryptoSatX features:
    - Original signal endpoints
    - SMC analysis
    - Signal history
    - Market data
    
    Use this for advanced GPT Actions integration with full feature set.
    """
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    replit_domain = os.getenv("REPLIT_DOMAINS")
    if replit_domain and "localhost" in base_url:
        base_url = f"https://{replit_domain.split(',')[0]}"
    elif not base_url or base_url == "http://localhost:8000":
        base_url = "http://localhost:8000"
    
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX - AI Crypto Signal Engine (Enhanced)",
            "description": "Comprehensive crypto trading signals with AI analysis, SMC patterns, and institutional insights",
            "version": "2.0.0"
        },
        "servers": [{"url": base_url, "description": "Production server"}],
        "paths": {
            "/signals/{symbol}": {
                "get": {
                    "summary": "Get AI Trading Signal",
                    "description": "Generate comprehensive trading signal using 8-factor AI analysis",
                    "operationId": "getSignal",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "BTC"}
                        },
                        {
                            "name": "debug",
                            "in": "query",
                            "schema": {"type": "boolean", "default": False}
                        }
                    ]
                }
            },
            "/smc/analyze/{symbol}": {
                "get": {
                    "summary": "Smart Money Concept Analysis",
                    "description": "Identify institutional trading patterns (BOS, CHoCH, FVG)",
                    "operationId": "analyzeSMC",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "ETH"}
                        },
                        {
                            "name": "timeframe",
                            "in": "query",
                            "schema": {"type": "string", "default": "1HRS", "enum": ["1MIN", "5MIN", "1HRS", "1DAY"]}
                        }
                    ]
                }
            },
            "/history/statistics": {
                "get": {
                    "summary": "Signal Performance Statistics",
                    "description": "Get historical signal statistics and distribution",
                    "operationId": "getStatistics",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ]
                }
            },
            "/coinglass/markets": {
                "get": {
                    "summary": "Market Data Overview",
                    "description": "Get comprehensive market data from Coinglass",
                    "operationId": "getMarkets"
                }
            },
            "/smart-money/scan": {
                "get": {
                    "summary": "Smart Money Scanner",
                    "description": "Scan for whale accumulation/distribution across markets",
                    "operationId": "scanSmartMoney"
                }
            }
        }
    }


@router.get("/actions/signal-with-context/{symbol}")
async def get_signal_with_full_context(
    symbol: str,
    include_smc: bool = Query(True, description="Include SMC analysis"),
    include_history: bool = Query(True, description="Include recent history"),
    timeframe: str = Query("1HRS", description="SMC timeframe"),
    api_key: str = Depends(get_optional_api_key)
):
    """
    🎯 **Signal with Full Context** - All-in-one endpoint for GPT
    
    Get trading signal with comprehensive context in one call:
    - AI-generated signal (8-factor analysis)
    - Smart Money Concept analysis
    - Recent signal history for the symbol
    - Complete market context
    
    Perfect for GPT Actions that need full decision context.
    
    ## **Example:**
    ```
    GET /gpt/actions/signal-with-context/BTC?include_smc=true&include_history=true
    ```
    """
    start_time = time.time()
    
    try:
        # Get main signal
        signal = await signal_engine.build_signal(symbol.upper(), debug=False)
        
        response = {
            "symbol": symbol.upper(),
            "timestamp": signal.get("timestamp"),
            "mainSignal": signal
        }
        
        # Initialize smc_result to avoid unbound variable
        smc_result = None
        
        # Add SMC analysis if requested
        if include_smc:
            smc_result = await smc_analyzer.analyze_smc(symbol.upper(), timeframe)
            response["smcAnalysis"] = smc_result
        
        # Add recent history if requested
        if include_history:
            history_result = await signal_history.get_history(
                symbol=symbol.upper(),
                limit=10
            )
            response["recentHistory"] = {
                "count": history_result.get("filtered", 0),
                "signals": history_result.get("signals", [])[:5]  # Last 5 signals
            }
        
        # Add interpretation for GPT
        ai_signal = signal.get("signal", "NEUTRAL")  # Ensure not None
        response["interpretation"] = {
            "primarySignal": ai_signal,
            "confidence": signal.get("confidence"),
            "smcAlignment": None,
            "summary": f"{ai_signal} signal with {signal.get('confidence')} confidence (score: {signal.get('score')})"
        }
        
        if include_smc and smc_result and smc_result.get("success"):
            smc_trend = smc_result.get("marketStructure", {}).get("trend")
            response["interpretation"]["smcAlignment"] = (
                "aligned" if _signals_aligned(ai_signal, smc_trend) else "divergent"
            )
        
        duration = time.time() - start_time
        log_api_call(
            default_logger,
            f"/gpt/actions/signal-with-context/{symbol}",
            symbol=symbol,
            duration=duration,
            status="success",
            extra_data={"include_smc": include_smc, "include_history": include_history}
        )
        
        return response
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get signal with context: {str(e)}"
        }


@router.post("/actions/send-alert/{symbol}")
async def trigger_telegram_alert(
    symbol: str,
    api_key: str = Depends(get_api_key)
):
    """
    📱 **Trigger Telegram Alert** - Send signal to Telegram
    
    Generate signal and send formatted alert to configured Telegram chat.
    
    Requires:
    - API key authentication
    - TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment
    
    ## **Example:**
    ```
    POST /gpt/actions/send-alert/BTC
    Headers: X-API-Key: your-api-key
    ```
    """
    try:
        # Generate signal
        signal = await signal_engine.build_signal(symbol.upper(), debug=False)
        
        # Send to Telegram
        telegram_result = await telegram_notifier.send_signal_alert(signal)
        
        return {
            "success": True,
            "signal": signal,
            "telegram": telegram_result
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send alert: {str(e)}"
        }


def _signals_aligned(ai_signal: str, smc_trend: str) -> bool:
    """Check if AI signal aligns with SMC trend"""
    if ai_signal == "LONG" and smc_trend == "bullish":
        return True
    if ai_signal == "SHORT" and smc_trend == "bearish":
        return True
    if ai_signal == "NEUTRAL" and smc_trend == "neutral":
        return True
    return False
