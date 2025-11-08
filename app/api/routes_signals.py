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

router = APIRouter()


@router.get("/signals/{symbol}")
async def get_signal(symbol: str, debug: bool = False):
    """
    Get enhanced trading signal with premium data and weighted scoring
    
    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
        debug: Include detailed score breakdown and all raw metrics (default: False)
        
    Returns:
        Enhanced signal with:
        - LONG/SHORT/NEUTRAL recommendation
        - Score (0-100) with weighted multi-factor analysis
        - Top 3 reasons for the signal
        - Premium metrics (liquidations, L/S ratio, smart money, etc.)
        - Debug info if requested
    """
    try:
        signal = await signal_engine.build_signal(symbol, debug=debug)
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
