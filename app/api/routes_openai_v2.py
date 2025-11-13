"""
OpenAI V2 Routes - Phase 1: Enhanced Signal Judge
Development endpoints - separate from production

Endpoints:
- POST /openai/v2/validate/{symbol} - Signal Judge with verdict system
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import time
import os

from app.core.signal_engine import signal_engine
from app.services.openai_service_v2 import get_openai_service_v2
from app.middleware.auth import get_optional_api_key
from app.utils.logger import default_logger, log_api_call

router = APIRouter(prefix="/openai/v2", tags=["OpenAI V2 (Development)"])


@router.post("/validate/{symbol}")
async def validate_signal_with_verdict_endpoint(
    symbol: str,
    include_comprehensive: bool = Query(
        True, description="Include comprehensive Coinglass metrics in validation"
    ),
    api_key: str = Depends(get_optional_api_key),
):
    """
    🧠 **Signal Judge V2** - Enhanced validation with verdict system
    
    **⚠️ DEVELOPMENT ENDPOINT - Phase 1 Testing**
    
    This is the enhanced Signal Judge that provides:
    - **Verdict**: CONFIRM / DOWNSIZE / SKIP / WAIT
    - **AI Confidence**: 0-100 score
    - **Key Agreements**: Factors supporting the signal
    - **Key Conflicts**: Conflicting indicators detected
    - **Risk Adjustment**: Position sizing recommendations
    - **Telegram Summary**: Ready-to-send alert text
    
    ## **Verdict Definitions:**
    - **CONFIRM**: Strong alignment, proceed with full position
    - **DOWNSIZE**: Mixed signals, reduce to 0.5x position size
    - **SKIP**: Too many conflicts, do not trade
    - **WAIT**: Potential setup but unclear timing
    
    ## **Example:**
    ```
    POST /openai/v2/validate/BTC?include_comprehensive=true
    ```
    
    ## **Response Format:**
    ```json
    {
      "success": true,
      "symbol": "BTC",
      "original_signal": "LONG",
      "original_score": 87,
      "verdict": "CONFIRM",
      "ai_confidence": 85,
      "key_agreements": [
        "H4 and H1 trends aligned (bullish)",
        "Funding and OI support long bias"
      ],
      "key_conflicts": [
        "RSI H1 overbought (73)"
      ],
      "adjusted_risk_suggestion": {
        "risk_factor": "NORMAL",
        "position_size_multiplier": 1.0,
        "reasoning": "Strong setup with minor overbought condition"
      },
      "telegram_summary": "BTC LONG confirmed. Strong bullish alignment across timeframes despite minor RSI overbought. Full position size recommended."
    }
    ```
    
    **Use Case**: Call this BEFORE sending Telegram alerts to filter signals.
    If verdict = SKIP → don't send alert. If DOWNSIZE → reduce position size.
    """
    start_time = time.time()
    
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service not configured. Set OPENAI_API_KEY environment variable.",
            )
        
        default_logger.info(f"🧠 Signal Judge V2 - Validating {symbol}")
        
        signal_data = await signal_engine.build_signal(symbol.upper(), debug=False)
        
        comprehensive_metrics = None
        if include_comprehensive and signal_data.get("comprehensiveDataAvailable"):
            comprehensive_metrics = signal_data.get("comprehensiveMetrics")
        
        openai_svc_v2 = await get_openai_service_v2()
        
        validation_result = await openai_svc_v2.validate_signal_with_verdict(
            symbol.upper(),
            signal_data,
            comprehensive_metrics,
        )
        
        elapsed = round((time.time() - start_time) * 1000)
        default_logger.info(
            f"✅ Signal Judge V2 complete for {symbol} - Verdict: {validation_result.get('verdict')} ({elapsed}ms)"
        )
        
        response = {
            **validation_result,
            "processing_time_ms": elapsed,
            "endpoint_version": "v2",
            "development_mode": True,
        }
        
        log_api_call(
            logger=default_logger,
            endpoint="/openai/v2/validate",
            symbol=symbol,
            duration=elapsed / 1000,
            status="success",
        )
        
        return response
        
    except Exception as e:
        default_logger.error(f"❌ Signal Judge V2 error for {symbol}: {e}")
        log_api_call(
            logger=default_logger,
            endpoint="/openai/v2/validate",
            symbol=symbol,
            duration=(time.time() - start_time),
            status="error",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Signal validation failed: {str(e)}",
        )


@router.get("/health")
async def health_check_v2():
    """
    ✅ **Health Check** - V2 Development endpoints status
    
    Check if OpenAI V2 service is configured and ready.
    """
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    
    return {
        "status": "healthy" if openai_configured else "misconfigured",
        "version": "v2",
        "mode": "development",
        "openai_configured": openai_configured,
        "endpoints": [
            "POST /openai/v2/validate/{symbol}",
            "GET /openai/v2/health",
        ],
        "phase": "Phase 1: Signal Judge",
    }


@router.get("/compare/{symbol}")
async def compare_v1_v2_validation(
    symbol: str,
    api_key: str = Depends(get_optional_api_key),
):
    """
    🔍 **Compare V1 vs V2** - Side-by-side validation comparison
    
    **Development Tool**: Compare production validation (V1) with Signal Judge (V2)
    
    Returns both validations for analysis and testing.
    """
    try:
        from app.services.openai_service import get_openai_service
        
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service not configured.",
            )
        
        default_logger.info(f"🔍 Comparing V1 vs V2 for {symbol}")
        
        signal_data = await signal_engine.build_signal(symbol.upper(), debug=False)
        
        openai_svc_v1 = await get_openai_service()
        v1_result = await openai_svc_v1.validate_signal_with_gpt(
            symbol.upper(),
            signal_data,
        )
        
        comprehensive_metrics = None
        if signal_data.get("comprehensiveDataAvailable"):
            comprehensive_metrics = signal_data.get("comprehensiveMetrics")
        
        openai_svc_v2 = await get_openai_service_v2()
        v2_result = await openai_svc_v2.validate_signal_with_verdict(
            symbol.upper(),
            signal_data,
            comprehensive_metrics,
        )
        
        return {
            "symbol": symbol.upper(),
            "original_signal": signal_data.get("signal"),
            "original_score": signal_data.get("score"),
            "v1_validation": {
                "validated_signal": v1_result.get("validated_signal"),
                "confidence": v1_result.get("confidence"),
                "reasoning": v1_result.get("reasoning"),
            },
            "v2_validation": {
                "verdict": v2_result.get("verdict"),
                "ai_confidence": v2_result.get("ai_confidence"),
                "key_agreements": v2_result.get("key_agreements"),
                "key_conflicts": v2_result.get("key_conflicts"),
                "adjusted_risk_suggestion": v2_result.get("adjusted_risk_suggestion"),
                "telegram_summary": v2_result.get("telegram_summary"),
            },
            "comparison_notes": "V1 provides simple validation. V2 provides structured verdict with risk management.",
        }
        
    except Exception as e:
        default_logger.error(f"❌ Comparison error for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}",
        )
