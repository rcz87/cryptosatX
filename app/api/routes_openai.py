"""
OpenAI Integration Routes
Enhanced trading signals with GPT-4 analysis and validation
"""

import os
from fastapi import APIRouter, Query, Depends, HTTPException, Request
from typing import Optional, List
import time
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.openai_service import get_openai_service
from app.core.signal_engine import signal_engine
from app.middleware.auth import get_api_key, get_optional_api_key
from app.utils.logger import default_logger, log_api_call

router = APIRouter(prefix="/openai", tags=["OpenAI Integration"])

# Rate limiter (10 requests per minute for OpenAI endpoints to prevent abuse)
limiter = Limiter(key_func=get_remote_address)


@router.get("/analyze/{symbol}")
@limiter.limit("10/minute")
async def analyze_signal_with_openai(
    request: Request,
    symbol: str,
    include_validation: bool = Query(True, description="Include GPT signal validation"),
    include_market_context: bool = Query(
        True, description="Include market context in analysis"
    ),
    api_key: str = Depends(get_optional_api_key),
):
    """
    🧠 **GPT-4 Signal Analysis** - Enhanced AI insights

    Analyze trading signal using GPT-4 for comprehensive insights:
    - Technical analysis validation
    - Market sentiment assessment
    - Risk factor identification
    - Trading recommendations
    - Confidence scoring

    ## **Example:**
    ```
    GET /openai/analyze/BTC?include_validation=true&include_market_context=true
    ```

    ## **Response Includes:**
    - Original signal data
    - GPT-4 analysis and insights
    - Validated signal (if enabled)
    - Risk assessment
    - Trading recommendations
    """
    start_time = time.time()

    try:
        # Check if OpenAI is configured
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service not configured. Set OPENAI_API_KEY environment variable.",
            )

        # Get base signal
        signal_data = await signal_engine.build_signal(symbol.upper(), debug=False)

        # Get OpenAI service
        openai_svc = await get_openai_service()

        # Prepare market context if requested
        market_context = None
        if include_market_context:
            market_context = {
                "comprehensive_metrics": signal_data.get("comprehensiveMetrics"),
                "premium_metrics": signal_data.get("premiumMetrics"),
                "lunarcrush_metrics": signal_data.get("lunarCrushMetrics"),
                "coinapi_metrics": signal_data.get("coinAPIMetrics"),
            }

        # Get GPT analysis
        gpt_analysis = await openai_svc.analyze_signal_with_gpt(
            symbol.upper(), signal_data, market_context
        )

        response = {
            "symbol": symbol.upper(),
            "timestamp": signal_data.get("timestamp"),
            "original_signal": signal_data,
            "gpt_analysis": gpt_analysis,
        }

        # Add validation if requested
        if include_validation and gpt_analysis.get("success"):
            # Identify conflicting indicators
            conflicting_indicators = []

            # Check for conflicts between original signal and GPT sentiment
            gpt_sentiment = gpt_analysis.get("gpt_analysis", {}).get(
                "overall_sentiment", "neutral"
            )
            original_signal = signal_data.get("signal", "NEUTRAL")

            if (original_signal == "LONG" and gpt_sentiment == "bearish") or (
                original_signal == "SHORT" and gpt_sentiment == "bullish"
            ):
                conflicting_indicators.append(
                    f"Signal ({original_signal}) conflicts with GPT sentiment ({gpt_sentiment})"
                )

            # Get validation
            validation = await openai_svc.validate_signal_with_gpt(
                symbol.upper(),
                signal_data,
                conflicting_indicators if conflicting_indicators else None,
            )

            response["validation"] = validation

        duration = time.time() - start_time
        log_api_call(
            default_logger,
            f"/openai/analyze/{symbol}",
            symbol=symbol,
            duration=duration,
            status="success",
            extra_data={
                "include_validation": include_validation,
                "include_market_context": include_market_context,
                "gpt_success": gpt_analysis.get("success", False),
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error in OpenAI signal analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sentiment/market")
@limiter.limit("10/minute")
async def get_market_sentiment_analysis(
    request: Request,
    symbols: str = Query("BTC,ETH,SOL", description="Comma-separated list of symbols"),
    api_key: str = Depends(get_optional_api_key),
):
    """
    📊 **Market Sentiment Analysis** - GPT-4 market insights

    Get comprehensive market sentiment analysis using GPT-4:
    - Overall market psychology
    - Key market drivers
    - Risk factors
    - Trading opportunities
    - Positioning strategies

    ## **Example:**
    ```
    GET /openai/sentiment/market?symbols=BTC,ETH,SOL,AVAX,DOGE
    ```
    """
    start_time = time.time()

    try:
        # Check if OpenAI is configured
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service not configured. Set OPENAI_API_KEY environment variable.",
            )

        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        # Get market data for all symbols
        market_data = {}
        for symbol in symbol_list:
            try:
                signal_data = await signal_engine.build_signal(symbol, debug=False)
                market_data[symbol] = {
                    "signal": signal_data.get("signal"),
                    "score": signal_data.get("score"),
                    "confidence": signal_data.get("confidence"),
                    "price": signal_data.get("price"),
                    "metrics": signal_data.get("metrics", {}),
                    "comprehensive_metrics": signal_data.get("comprehensiveMetrics"),
                    "premium_metrics": signal_data.get("premiumMetrics"),
                }
            except Exception as e:
                market_data[symbol] = {"error": str(e)}

        # Get OpenAI service
        openai_svc = await get_openai_service()

        # Generate sentiment analysis
        sentiment_analysis = await openai_svc.generate_market_sentiment_analysis(
            symbol_list, market_data
        )

        response = {
            "symbols": symbol_list,
            "timestamp": sentiment_analysis.get("timestamp"),
            "market_data": market_data,
            "sentiment_analysis": sentiment_analysis,
            "data_points": len([s for s in market_data.values() if "error" not in s]),
        }

        duration = time.time() - start_time
        log_api_call(
            default_logger,
            "/openai/sentiment/market",
            symbols=symbol_list,
            duration=duration,
            status="success",
            extra_data={"data_points": response["data_points"]},
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error in market sentiment analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.post("/validate/{symbol}")
@limiter.limit("10/minute")
async def validate_trading_signal(
    request: Request,
    symbol: str,
    signal_data: dict,
    conflicting_indicators: Optional[List[str]] = None,
    api_key: str = Depends(get_api_key),
):
    """
    ✅ **Signal Validation** - GPT-4 signal confirmation

    Validate trading signal using GPT-4 for risk management:
    - Signal confirmation or rejection
    - Confidence assessment
    - Risk evaluation
    - Reasoning explanation

    ## **Required:** API key authentication

    ## **Example:**
    ```
    POST /openai/validate/BTC
    Headers: X-API-Key: your-api-key
    Body: {
      "signal": "LONG",
      "score": 75.5,
      "confidence": "high",
      "reasons": ["Strong bullish momentum", "High funding rate"]
    }
    ```
    """
    start_time = time.time()

    try:
        # Check if OpenAI is configured
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service not configured. Set OPENAI_API_KEY environment variable.",
            )

        # Get OpenAI service
        openai_svc = await get_openai_service()

        # Validate signal
        validation = await openai_svc.validate_signal_with_gpt(
            symbol.upper(), signal_data, conflicting_indicators
        )

        response = {
            "symbol": symbol.upper(),
            "timestamp": validation.get("timestamp"),
            "original_signal": signal_data,
            "validation": validation,
        }

        duration = time.time() - start_time
        log_api_call(
            default_logger,
            f"/openai/validate/{symbol}",
            symbol=symbol,
            duration=duration,
            status="success",
            extra_data={
                "original_signal": signal_data.get("signal"),
                "validated_signal": validation.get("validated_signal"),
                "validation_success": validation.get("success", False),
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error in signal validation: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/config")
async def get_openai_config(api_key: str = Depends(get_api_key)):
    """
    ⚙️ **OpenAI Configuration** - Service status and settings

    Get current OpenAI service configuration and status.

    ## **Required:** API key authentication
    """
    try:
        config = {
            "service_enabled": bool(os.getenv("OPENAI_API_KEY")),
            "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            "timeout": int(os.getenv("OPENAI_TIMEOUT", "30")),
            "features": {
                "signal_analysis": True,
                "market_sentiment": True,
                "signal_validation": True,
            },
        }

        return {
            "status": "configured" if config["service_enabled"] else "not_configured",
            "config": config,
            "endpoints": {
                "analyze": "/openai/analyze/{symbol}",
                "sentiment": "/openai/sentiment/market",
                "validation": "/openai/validate/{symbol}",
                "config": "/openai/config",
            },
        }

    except Exception as e:
        default_logger.error(f"Error getting OpenAI config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Config retrieval failed: {str(e)}"
        )


@router.get("/health")
async def openai_health_check():
    """
    🏥 **OpenAI Health Check** - Service availability

    Check if OpenAI service is properly configured and accessible.
    """
    try:
        is_configured = bool(os.getenv("OPENAI_API_KEY"))

        if is_configured:
            # Try to initialize service
            try:
                openai_svc = await get_openai_service()
                status = "healthy"
                message = "OpenAI service is configured and ready"
            except Exception as e:
                status = "error"
                message = f"OpenAI service configuration error: {str(e)}"
        else:
            status = "not_configured"
            message = "OpenAI API key not configured"

        return {
            "service": "openai",
            "status": status,
            "message": message,
            "timestamp": time.time(),
        }

    except Exception as e:
        return {
            "service": "openai",
            "status": "error",
            "message": str(e),
            "timestamp": time.time(),
        }
