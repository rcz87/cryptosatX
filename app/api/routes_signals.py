"""
Signal and market data routes
"""
from fastapi import APIRouter, HTTPException
from app.core.signal_engine import signal_engine
from app.services.coinapi_service import coinapi_service
from app.services.coinglass_service import coinglass_service
from app.services.coinglass_premium_service import coinglass_premium
from app.services.lunarcrush_service import lunarcrush_service
from app.services.okx_service import okx_service

# ADDED FOR CRYPTOSATX ENHANCEMENT - Signal history auto-save
from app.storage.signal_history import signal_history
import asyncio

# ADDED FOR AI VALIDATION - OpenAI integration
from app.services.openai_service import get_openai_service

# ADDED FOR PHASE 2 - Outcome tracking
from app.services.outcome_tracker import outcome_tracker
from datetime import datetime

router = APIRouter()


async def persist_signal_with_tracking(signal: dict):
    """
    Helper coroutine to persist signal and initiate outcome tracking
    Runs in background without blocking API response
    
    Flow:
    1. Save signal to database (await to get signal_id)
    2. Extract AI verdict metadata
    3. Record outcome entry for tracking
    4. Schedule background tracking at 1h, 4h, 24h intervals
    """
    try:
        # Step 1: Save signal and get signal_id
        save_result = await signal_history.save_signal(signal)
        
        if not save_result.get("success"):
            print(f"[ERROR] Failed to save signal: {save_result.get('message')}")
            return
        
        signal_id = save_result.get("signal_id")
        if not signal_id:
            print("[ERROR] No signal_id returned from save_signal")
            return
        
        print(f"[SUCCESS] Signal saved with ID: {signal_id}")
        
        # Step 2: Extract AI verdict metadata (with safe defaults)
        ai_verdict = signal.get("aiVerdictLayer", {})
        verdict = ai_verdict.get("verdict", "UNKNOWN")
        risk_mode = ai_verdict.get("riskMode", "NORMAL")
        
        # Skip tracking if verdict is SKIP/WAIT (not actionable)
        if verdict in ["SKIP", "WAIT"]:
            print(f"[INFO] Skipping outcome tracking for {verdict} verdict")
            return
        
        # Step 3: Record outcome entry
        # Extract price (signals use "price" field, not "currentPrice")
        entry_price = float(signal.get("price") or signal.get("currentPrice") or 0)
        
        # Validate non-zero price (critical for P&L calculation)
        if entry_price <= 0:
            print(f"[ERROR] Invalid entry price ({entry_price}) for {signal.get('symbol')} - cannot track outcome")
            return
        
        entry_timestamp = datetime.utcnow()
        
        outcome_id = await outcome_tracker.record_signal_entry(
            signal_id=signal_id,
            symbol=signal.get("symbol", ""),
            signal_type=signal.get("signal", ""),
            verdict=verdict,
            risk_mode=risk_mode,
            entry_price=entry_price,
            entry_timestamp=entry_timestamp
        )
        
        if not outcome_id:
            print("[ERROR] Failed to record outcome entry")
            return
        
        print(f"[SUCCESS] Outcome entry recorded: {outcome_id}")
        
        # Step 4: Schedule background tracking
        await outcome_tracker.schedule_outcome_tracking(outcome_id)
        print(f"[SUCCESS] Outcome tracking scheduled for {signal.get('symbol')}")
        
    except Exception as e:
        print(f"[ERROR] persist_signal_with_tracking failed: {e}")
        import traceback
        traceback.print_exc()


@router.get("/signals/{symbol}")
async def get_signal(symbol: str, debug: bool = False, include_ai_validation: bool = False):
    """
    Get enhanced trading signal with premium data and weighted scoring.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
        debug: Include detailed score breakdown and all raw metrics (default: False)
        include_ai_validation: Include OpenAI GPT-4 validation and reasoning (default: False)
        
    Returns:
        Enhanced signal with:
        - LONG/SHORT/NEUTRAL recommendation
        - Score (0-100) with weighted multi-factor analysis
        - Top 3 reasons for the signal
        - Premium metrics (liquidations, L/S ratio, smart money, etc.)
        - AI validation (if requested)
        - Debug info if requested
        
    Examples:
        Basic signal request:
            GET /signals/BTC
            
        With debug mode:
            GET /signals/ETH?debug=true
            
        With AI validation:
            GET /signals/SOL?include_ai_validation=true
            
    Response Structure (core fields always present):
        {
            "symbol": "BTC",
            "timestamp": "2025-11-14T12:00:00",
            "signal": "LONG" | "SHORT" | "NEUTRAL",
            "score": 72.5,
            "confidence": "high" | "medium" | "low",
            "price": 45123.45,
            "reasons": ["Liquidation imbalance favors longs", ...],
            "mode": "aggressive",
            "mode_info": {...},
            "metrics": {
                "fundingRate": 0.0001,
                "openInterest": 1234567890,
                "socialScore": 65.5,
                "priceTrend": "bullish"
            },
            "data_quality": {...}
        }
        
    Conditional Fields (depends on data availability):
        - "premiumMetrics": {...}  // When premium data available
        - "comprehensiveMetrics": {...}  // When comprehensive Coinglass data available
        - "lunarCrushMetrics": {...}  // When LunarCrush data available
        - "coinAPIMetrics": {...}  // When CoinAPI data available
        - "aiVerdictLayer": {...}  // When AI validation enabled
        - "debug": {...}  // When debug=true
    """
    try:
        signal = await signal_engine.build_signal(symbol, debug=debug)
        
        # PHASE 2: Persist signal and initiate outcome tracking (non-blocking)
        # Only track actionable signals (LONG/SHORT) with AI verdict
        if signal.get("signal") in ["LONG", "SHORT"] and signal.get("aiVerdictLayer"):
            asyncio.create_task(persist_signal_with_tracking(signal))
        
        # ADDED FOR AI VALIDATION - Get OpenAI GPT-4 validation if requested
        if include_ai_validation:
            try:
                openai_svc = await get_openai_service()
                validation = await openai_svc.validate_signal_with_gpt(symbol, signal)
                
                if validation.get("success"):
                    signal["ai_validation"] = {
                        "original_signal": validation.get("original_signal"),
                        "validated_signal": validation.get("validated_signal"),
                        "confidence": validation.get("confidence"),
                        "reasoning": validation.get("reasoning"),
                        "model_used": validation.get("model_used"),
                    }
                else:
                    signal["ai_validation"] = {
                        "success": False,
                        "error": validation.get("error", "AI validation failed")
                    }
            except Exception as ai_error:
                # Don't fail the entire request if AI validation fails
                signal["ai_validation"] = {
                    "success": False,
                    "error": f"AI validation unavailable: {str(ai_error)}"
                }
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.get("/debug/premium/{symbol}")
async def debug_premium_endpoints(symbol: str):
    """Debug endpoint to test all premium endpoints individually"""
    try:
        results = {
            "liquidation": await coinglass_premium.get_liquidation_data(symbol),
            "longShortRatio": await coinglass_premium.get_long_short_ratio(symbol),
            "oiTrend": await coinglass_premium.get_oi_trend(symbol),
            "topTrader": await coinglass_premium.get_top_trader_ratio(symbol),
            "fearGreed": await coinglass_premium.get_fear_greed_index()
        }
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


@router.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """
    Get raw market data from all providers for a cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
        
    Returns:
        Raw data from CoinAPI, Coinglass, LunarCrush, and OKX
    """
    try:
        # Fetch data from all sources
        price_data = await coinapi_service.get_spot_price(symbol)
        funding_data = await coinglass_service.get_funding_rate(symbol)
        oi_data = await coinglass_service.get_open_interest(symbol)
        social_data = await lunarcrush_service.get_social_score(symbol)
        candles_data = await okx_service.get_candles(symbol, "15m", 50)
        
        return {
            "symbol": symbol.upper(),
            "coinapi": price_data,
            "coinglass": {
                "funding": funding_data,
                "openInterest": oi_data
            },
            "lunarcrush": social_data,
            "okx": candles_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")
