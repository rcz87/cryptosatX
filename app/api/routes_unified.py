"""
Unified Ranking API Routes

Provides endpoints for composite scoring and cross-validation
of cryptocurrency signals.

Endpoints:
- GET /unified/score/{symbol} - Get unified score for single coin
- POST /unified/ranking - Get ranked list of coins
- GET /unified/validate/{symbol} - Validate signal with cross-confirmation
- GET /unified/top-tier/{tier} - Get top coins by tier
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.unified_scorer import unified_scorer, get_unified_score, get_unified_ranking
from app.core.signal_validator import signal_validator, validate_buy, validate_sell
from app.utils.logger import default_logger

router = APIRouter(prefix="/unified", tags=["Unified Ranking"])
logger = default_logger


class RankingRequest(BaseModel):
    """Request model for bulk ranking"""
    symbols: List[str]
    min_score: Optional[float] = None
    limit: Optional[int] = 50


class ValidationRequest(BaseModel):
    """Request model for signal validation"""
    symbol: str
    signal_type: Optional[str] = "BUY"  # "BUY" or "SELL"


@router.get("/score/{symbol}", summary="Get Unified Score for Symbol")
async def get_symbol_unified_score(symbol: str) -> Dict[str, Any]:
    """
    Get composite unified score (0-100) for a cryptocurrency

    Combines signals from:
    - Smart Money accumulation (30%)
    - MSS score (25%)
    - Technical RSI (15%)
    - Social momentum (15%)
    - Whale activity (10%)
    - Volume spike (5%)

    Returns:
    - Unified score (0-100)
    - Tier classification (TIER_1, TIER_2, TIER_3, TIER_4)
    - Recommendation (STRONG BUY, BUY, WATCH, etc.)
    - Confidence level
    - Score breakdown by component

    Example:
    ```
    GET /unified/score/BTC
    ```
    """
    try:
        logger.info(f"Getting unified score for {symbol}")

        result = await get_unified_score(symbol)

        return {
            "ok": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting unified score for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate unified score: {str(e)}"
        )


@router.post("/ranking", summary="Get Ranked List of Coins")
async def get_unified_ranking_list(request: RankingRequest) -> Dict[str, Any]:
    """
    Get ranked list of coins sorted by unified score

    Calculate unified scores for multiple coins and return them
    ranked from highest to lowest score.

    Args:
    - symbols: List of symbols to rank (max 100)
    - min_score: Optional minimum score filter (0-100)
    - limit: Max results to return (default 50)

    Returns:
    - Ranked list sorted by unified_score descending
    - Summary statistics
    - Tier distribution

    Example:
    ```json
    {
      "symbols": ["BTC", "ETH", "SOL", ...],
      "min_score": 70,
      "limit": 10
    }
    ```
    """
    try:
        if not request.symbols:
            raise HTTPException(status_code=400, detail="At least one symbol required")

        if len(request.symbols) > 100:
            raise HTTPException(
                status_code=400,
                detail="Maximum 100 symbols per ranking request"
            )

        logger.info(
            f"Calculating unified ranking for {len(request.symbols)} symbols "
            f"(min_score: {request.min_score}, limit: {request.limit})"
        )

        # Calculate rankings
        results = await get_unified_ranking(request.symbols, request.min_score)

        # Apply limit
        limited_results = results[:request.limit]

        # Calculate statistics
        tier_counts = {}
        for result in limited_results:
            tier = result.get("tier", "TIER_4_NEUTRAL")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        avg_score = (
            sum(r["unified_score"] for r in limited_results) / len(limited_results)
            if limited_results else 0
        )

        return {
            "ok": True,
            "data": {
                "rankings": limited_results,
                "summary": {
                    "total_analyzed": len(request.symbols),
                    "results_returned": len(limited_results),
                    "average_score": round(avg_score, 1),
                    "tier_distribution": tier_counts,
                    "filters_applied": {
                        "min_score": request.min_score,
                        "limit": request.limit
                    }
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating unified ranking: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate ranking: {str(e)}"
        )


@router.get("/validate/{symbol}", summary="Validate Signal with Cross-Confirmation")
async def validate_symbol_signal(
    symbol: str,
    signal_type: str = Query("BUY", description="Signal type: BUY or SELL")
) -> Dict[str, Any]:
    """
    Validate buy/sell signal by checking agreement across multiple scanners

    Cross-validates signal from:
    - Smart Money scanner
    - MSS discovery
    - Technical indicators
    - Social momentum

    Confidence levels:
    - 1 scanner agrees: 60% confidence
    - 2 scanners agree: 75% confidence
    - 3+ scanners agree: 85-95% confidence

    Args:
    - symbol: Cryptocurrency symbol
    - signal_type: "BUY" or "SELL"

    Returns:
    - Validated action (STRONG_BUY, BUY, WATCH, etc.)
    - Confidence level (60-95%)
    - Number of confirmations
    - Scanner agreement details

    Example:
    ```
    GET /unified/validate/BTC?signal_type=BUY
    ```
    """
    try:
        logger.info(f"Validating {signal_type} signal for {symbol}")

        if signal_type.upper() not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=400,
                detail="signal_type must be 'BUY' or 'SELL'"
            )

        # Validate signal
        if signal_type.upper() == "BUY":
            result = await validate_buy(symbol)
        else:
            result = await validate_sell(symbol)

        return {
            "ok": True,
            "data": {
                "symbol": symbol.upper(),
                "signal_type": signal_type.upper(),
                **result
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating signal for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate signal: {str(e)}"
        )


@router.get("/top-tier/{tier}", summary="Get Top Coins by Tier")
async def get_top_tier_coins(
    tier: str,
    symbols: Optional[List[str]] = Query(None),
    limit: int = Query(20, description="Max results to return")
) -> Dict[str, Any]:
    """
    Get top coins filtered by tier classification

    Args:
    - tier: Tier filter (TIER_1, TIER_2, TIER_3, TIER_4)
    - symbols: Optional list of symbols to scan (if not provided, uses default list)
    - limit: Max results (default 20)

    Tier Classifications:
    - TIER_1: Score ≥85 (Must Buy - Very strong signal)
    - TIER_2: Score ≥70 (Strong Buy - Good signal)
    - TIER_3: Score ≥55 (Watchlist - Moderate signal)
    - TIER_4: Score <55 (Neutral - Weak signal)

    Returns:
    - Top coins in specified tier
    - Sorted by unified_score descending

    Example:
    ```
    GET /unified/top-tier/TIER_1?limit=10
    ```
    """
    try:
        # Validate tier
        valid_tiers = ["TIER_1", "TIER_2", "TIER_3", "TIER_4"]
        if tier.upper() not in [t.split("_")[0] + "_" + t.split("_")[1] for t in valid_tiers]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {valid_tiers}"
            )

        # Default symbols if not provided
        if not symbols:
            # Use default top coins
            symbols = [
                "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "LINK",
                "UNI", "AAVE", "ATOM", "AVAX", "FTM", "NEAR", "ALGO", "VET", "ICP", "FIL",
                "LTC", "BCH", "ETC", "XLM", "HBAR", "SAND", "MANA", "AXS", "GALA", "APT"
            ]

        if len(symbols) > 100:
            symbols = symbols[:100]  # Limit to 100

        logger.info(
            f"Getting top TIER_{tier} coins from {len(symbols)} symbols (limit: {limit})"
        )

        # Calculate rankings
        results = await get_unified_ranking(symbols)

        # Filter by tier
        tier_key = f"TIER_{tier}" if not tier.startswith("TIER_") else tier
        filtered = [
            r for r in results
            if r.get("tier", "").startswith(tier_key.split("_")[0] + "_" + tier_key.split("_")[1])
        ][:limit]

        return {
            "ok": True,
            "data": {
                "tier": tier_key,
                "results": filtered,
                "count": len(filtered),
                "scanned": len(symbols)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top tier coins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top tier coins: {str(e)}"
        )


@router.get("/stats", summary="Get Unified Scoring Statistics")
async def get_unified_stats() -> Dict[str, Any]:
    """
    Get statistics and configuration for unified scoring system

    Returns:
    - Weight configuration
    - Tier thresholds
    - Confidence levels
    - System info
    """
    try:
        return {
            "ok": True,
            "data": {
                "weights": unified_scorer.WEIGHTS,
                "tier_thresholds": unified_scorer.TIER_THRESHOLDS,
                "confidence_levels": signal_validator.CONFIDENCE_LEVELS,
                "validation_thresholds": signal_validator.THRESHOLDS,
                "system_info": {
                    "version": "1.0.0",
                    "scanners_integrated": 6,
                    "max_symbols_per_ranking": 100,
                    "tiers_available": 4
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting unified stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
