"""
Optimized GPT Actions Integration - Ultra-Slim Routing Layer
All business logic delegated to services
"""
from fastapi import APIRouter, Query, Depends
import os
import time

from app.core.signal_engine import signal_engine
from app.middleware.auth import get_optional_api_key
from app.utils.logger import default_logger, log_api_call
from app.utils.gpt_schema_builder import build_maximal_gpt_schema
from app.services.risk_assessment_service import risk_assessment_service
from app.services.gpt_orchestration_service import gpt_orchestration_service
from app.utils.trading_strategies import WHALE_SCAN_COINS

router = APIRouter(prefix="/gpt", tags=["Optimized GPT Actions"])


@router.get("/actions/maximal-schema")
async def get_maximal_gpt_schema():
    """🚀 MAXIMAL GPT Actions Schema - Ultimate API Capabilities"""
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    replit_domain = os.getenv("REPLIT_DOMAINS")
    if replit_domain and "localhost" in base_url:
        base_url = f"https://{replit_domain.split(',')[0]}"
    elif not base_url or base_url == "http://localhost:8000":
        base_url = "http://localhost:8000"
    return build_maximal_gpt_schema(base_url)


@router.get("/actions/ultimate-signal/{symbol}")
async def get_ultimate_signal(
    symbol: str,
    include_ai_validation: bool = Query(True),
    include_smc: bool = Query(True),
    include_whale_data: bool = Query(True),
    risk_level: str = Query("moderate"),
    api_key: str = Depends(get_optional_api_key),
):
    """🚀 ULTIMATE SIGNAL - Maximum AI-Powered Trading Signal"""
    start_time = time.time()
    try:
        symbol = symbol.upper()
        response = await gpt_orchestration_service.build_ultimate_signal(
            symbol, include_ai_validation, include_smc, include_whale_data, risk_level
        )
        duration = time.time() - start_time
        log_api_call(
            default_logger,
            f"/gpt/actions/ultimate-signal/{symbol}",
            symbol=symbol,
            duration=duration,
            status="success",
        )
        return response
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate ultimate signal: {str(e)}",
            "symbol": symbol.upper(),
        }


@router.get("/actions/portfolio-optimizer")
async def optimize_portfolio(
    risk_tolerance: int = Query(5),
    investment_amount: float = Query(10000),
    time_horizon: str = Query("medium_term"),
    api_key: str = Depends(get_optional_api_key),
):
    """💼 AI Portfolio Optimizer - Maximum Returns with Controlled Risk"""
    try:
        return await gpt_orchestration_service.build_portfolio_optimization(
            risk_tolerance, investment_amount, time_horizon
        )
    except Exception as e:
        return {"success": False, "error": f"Portfolio optimization failed: {str(e)}"}


@router.get("/smart-money/accumulation")
async def find_whale_accumulation(
    min_score: int = Query(8),
    exclude_overbought_coins: bool = Query(True),
    api_key: str = Depends(get_optional_api_key),
):
    """📈 Whale Accumulation Finder"""
    try:
        return await gpt_orchestration_service.find_whale_accumulation(
            min_score, exclude_overbought_coins, WHALE_SCAN_COINS
        )
    except Exception as e:
        return {"success": False, "error": f"Whale accumulation scan failed: {str(e)}"}


@router.get("/portfolio/optimize")
async def optimize_portfolio_public(
    risk_tolerance: int = Query(5),
    investment_amount: float = Query(10000),
    time_horizon: str = Query("medium_term"),
    api_key: str = Depends(get_optional_api_key),
):
    """💼 Portfolio Optimizer - Public endpoint"""
    return await optimize_portfolio(risk_tolerance, investment_amount, time_horizon, api_key)


@router.get("/risk/assess/{symbol}")
async def assess_risk(
    symbol: str,
    position_size: float = Query(None),
    api_key: str = Depends(get_optional_api_key),
):
    """⚠️ Risk Assessment"""
    try:
        symbol = symbol.upper()
        signal = await signal_engine.build_signal(symbol, debug=False)
        return risk_assessment_service.assess_coin_risk(symbol, signal, position_size)
    except Exception as e:
        return {"success": False, "error": f"Risk assessment failed: {str(e)}"}


@router.get("/strategies/recommend")
async def recommend_strategies(
    symbol: str = Query(None),
    strategy_type: str = Query("all"),
    timeframe: str = Query("swing"),
    api_key: str = Depends(get_optional_api_key),
):
    """🎯 Trading Strategy Recommendations"""
    try:
        return await gpt_orchestration_service.recommend_trading_strategies(
            symbol, strategy_type, timeframe
        )
    except Exception as e:
        return {"success": False, "error": f"Strategy recommendation failed: {str(e)}"}
