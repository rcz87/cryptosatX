"""
Smart Money Scanner API Routes

Endpoints for detecting whale accumulation and distribution patterns.
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from app.services.smart_money_service import smart_money_service

router = APIRouter(prefix="/smart-money", tags=["Smart Money Scanner"])


@router.get("/scan")
async def scan_smart_money(
    min_accumulation_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum accumulation score to flag (0-10). Higher = stronger accumulation signal."
    ),
    min_distribution_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum distribution score to flag (0-10). Higher = stronger distribution signal."
    ),
    coins: Optional[str] = Query(
        default=None,
        description="Comma-separated list of coins to scan (e.g., 'BTC,ETH,SOL'). If not provided, scans default list of 30+ coins."
    )
):
    """
    🔍 **Smart Money Scanner** - Detect Whale Accumulation & Distribution
    
    Scans 30+ cryptocurrencies to identify coins being accumulated or distributed by whales
    BEFORE retail traders enter/exit. Perfect for finding early opportunities.
    
    ## **Accumulation Signals** (Buy Before Retail):
    - High buy pressure (whale buying)
    - Low funding rate (not crowded yet)
    - Low social activity (retail unaware)
    - Sideways price (no pump yet)
    
    ## **Distribution Signals** (Short Before Dump):
    - High sell pressure (whale selling)
    - High funding rate (longs overcrowded)
    - High social activity (retail FOMO)
    - Recent pump (potential top)
    
    ## **Score System**:
    - **0-3**: Weak signal
    - **4-6**: Moderate signal
    - **7-8**: Strong signal ⭐
    - **9-10**: Very strong signal ⭐⭐⭐
    
    ## **Usage Examples**:
    
    ```
    # Scan all coins with default thresholds
    GET /smart-money/scan
    
    # Find only strong accumulation signals
    GET /smart-money/scan?min_accumulation_score=7
    
    # Scan specific coins
    GET /smart-money/scan?coins=BTC,ETH,SOL,AVAX
    
    # More sensitive detection (lower threshold)
    GET /smart-money/scan?min_accumulation_score=4&min_distribution_score=4
    ```
    
    ## **Returns**:
    - Top accumulation candidates ranked by score
    - Top distribution candidates ranked by score
    - Summary statistics
    - Detailed reasons for each signal
    
    **Perfect for:** Finding entry/exit points before retail crowd
    """
    # Parse coins if provided
    coin_list = None
    if coins:
        coin_list = [c.strip().upper() for c in coins.split(",")]
    
    # Scan markets
    result = await smart_money_service.scan_markets(
        min_accumulation_score=min_accumulation_score,
        min_distribution_score=min_distribution_score,
        coins=coin_list
    )
    
    return result


@router.get("/scan/accumulation")
async def scan_accumulation_only(
    min_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum accumulation score (0-10)"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Max number of results to return"
    ),
    coins: Optional[str] = Query(default=None, description="Comma-separated coins to scan")
):
    """
    🟢 **Accumulation Scanner** - Find Coins Being Quietly Accumulated
    
    Returns ONLY coins showing accumulation patterns, ranked by strength.
    Perfect for finding buy opportunities before retail FOMO.
    
    ## **What This Finds**:
    - Coins with high buy pressure but low social buzz
    - Sideways price action while whales accumulate
    - Low funding rates (market not crowded)
    - Early stage accumulation before pump
    
    ## **Use Case**:
    "Find me coins to BUY before retail discovers them"
    
    ## **Example**:
    ```
    GET /smart-money/scan/accumulation?min_score=6&limit=5
    ```
    Returns top 5 strongest accumulation signals
    """
    coin_list = [c.strip().upper() for c in coins.split(",")] if coins else None
    
    result = await smart_money_service.scan_markets(
        min_accumulation_score=min_score,
        min_distribution_score=999,  # Very high to exclude distribution
        coins=coin_list
    )
    
    # Return only accumulation signals, limited
    return {
        "success": True,
        "timestamp": result["timestamp"],
        "coinsScanned": result["coinsScanned"],
        "signalsFound": len(result["accumulation"]),
        "signals": result["accumulation"][:limit]
    }


@router.get("/scan/distribution")
async def scan_distribution_only(
    min_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum distribution score (0-10)"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Max number of results to return"
    ),
    coins: Optional[str] = Query(default=None, description="Comma-separated coins to scan")
):
    """
    🔴 **Distribution Scanner** - Find Coins Being Dumped by Whales
    
    Returns ONLY coins showing distribution patterns, ranked by strength.
    Perfect for finding short opportunities before retail exits.
    
    ## **What This Finds**:
    - Coins with high sell pressure despite hype
    - Recent pumps with whale selling
    - High funding rates (retail longing at top)
    - High social activity (retail FOMO while whales exit)
    
    ## **Use Case**:
    "Find me coins to SHORT before retail panic sells"
    
    ## **Example**:
    ```
    GET /smart-money/scan/distribution?min_score=6&limit=5
    ```
    Returns top 5 strongest distribution signals
    """
    coin_list = [c.strip().upper() for c in coins.split(",")] if coins else None
    
    result = await smart_money_service.scan_markets(
        min_accumulation_score=999,  # Very high to exclude accumulation
        min_distribution_score=min_score,
        coins=coin_list
    )
    
    # Return only distribution signals, limited
    return {
        "success": True,
        "timestamp": result["timestamp"],
        "coinsScanned": result["coinsScanned"],
        "signalsFound": len(result["distribution"]),
        "signals": result["distribution"][:limit]
    }


@router.get("/info")
async def smart_money_info():
    """
    📖 **Smart Money Scanner Info**
    
    Returns information about the scanner, coin list, and scoring methodology.
    """
    return {
        "name": "Smart Money Scanner",
        "version": "1.0.0",
        "description": "Detects whale accumulation and distribution patterns across 30+ cryptocurrencies",
        "defaultCoins": smart_money_service.SCAN_LIST,
        "totalCoins": len(smart_money_service.SCAN_LIST),
        "scoringSystem": {
            "accumulation": {
                "factors": [
                    "Buy pressure (0-3 points)",
                    "Funding rate (0-2 points)",
                    "Social activity (0-2 points)",
                    "Price action (0-2 points)",
                    "Trend confirmation (0-1 point)"
                ],
                "maxScore": 10,
                "interpretation": {
                    "0-3": "Weak accumulation",
                    "4-6": "Moderate accumulation",
                    "7-8": "Strong accumulation ⭐",
                    "9-10": "Very strong accumulation ⭐⭐⭐"
                }
            },
            "distribution": {
                "factors": [
                    "Sell pressure (0-3 points)",
                    "Funding rate (0-2 points)",
                    "Social activity (0-2 points)",
                    "Recent pump (0-2 points)",
                    "Momentum shift (0-1 point)"
                ],
                "maxScore": 10,
                "interpretation": {
                    "0-3": "Weak distribution",
                    "4-6": "Moderate distribution",
                    "7-8": "Strong distribution ⭐",
                    "9-10": "Very strong distribution ⭐⭐⭐"
                }
            }
        },
        "endpoints": {
            "fullScan": "/smart-money/scan",
            "accumulationOnly": "/smart-money/scan/accumulation",
            "distributionOnly": "/smart-money/scan/distribution",
            "info": "/smart-money/info"
        },
        "useCases": [
            "Find coins to buy before retail FOMO",
            "Find coins to short before retail panic",
            "Detect whale movement early",
            "Follow smart money instead of retail crowd"
        ]
    }
