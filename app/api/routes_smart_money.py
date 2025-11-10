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


# ==================== NEW ENDPOINTS - EXTENDED FUNCTIONALITY ====================


@router.get("/analyze/{symbol}")
async def analyze_coin(symbol: str):
    """
    🔍 **Analyze ANY Coin** - Dynamic Smart Money Analysis
    
    Analyze any cryptocurrency symbol, not limited to the default scan list.
    Perfect for when you want to check a specific coin that's trending or mentioned.
    
    ## **What This Analyzes**:
    - Accumulation vs Distribution score
    - Whale buying/selling pressure
    - Funding rates and open interest
    - Social sentiment vs price action
    - Clear interpretation and recommendation
    
    ## **Use Cases**:
    - "What's happening with PEPE right now?"
    - "Is WIF being accumulated or distributed?"
    - "Should I buy this new coin that's trending?"
    
    ## **Example**:
    ```
    GET /smart-money/analyze/PEPE
    GET /smart-money/analyze/WIF
    GET /smart-money/analyze/BONK
    ```
    
    ## **Returns**:
    - Complete analysis with scores
    - Dominant pattern (accumulation/distribution/neutral)
    - Human-readable interpretation
    - Key metrics (funding rate, OI, volume)
    
    **Perfect for:** Quick analysis of any coin you're curious about
    """
    result = await smart_money_service.analyze_any_coin(symbol)
    return result


@router.get("/discover")
async def discover_coins(
    max_market_cap: float = Query(
        default=100000000,
        description="Maximum market cap in USD (default $100M for small caps)"
    ),
    min_volume: float = Query(
        default=500000,
        description="Minimum 24h volume in USD (default $500K)"
    ),
    source: str = Query(
        default="all",
        description="Data source: 'binance', 'coingecko', or 'all'"
    ),
    limit: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
):
    """
    🆕 **Coin Discovery** - Find New & Small Cap Opportunities
    
    Discover new or small market cap coins from Binance Futures and CoinGecko.
    Perfect for finding early opportunities before they pump.
    
    ## **What This Finds**:
    - Small cap coins with real volume (not dead coins)
    - New listings on Binance Futures
    - Trending coins from CoinGecko
    - Coins with futures trading available
    
    ## **Filters**:
    - Market cap (find coins under $100M, $50M, etc.)
    - Volume (ensure liquidity)
    - Source (Binance, CoinGecko, or both)
    
    ## **Examples**:
    ```
    # Find all small caps with decent volume
    GET /smart-money/discover
    
    # Find micro caps under $50M
    GET /smart-money/discover?max_market_cap=50000000
    
    # Only Binance Futures coins
    GET /smart-money/discover?source=binance
    
    # High volume small caps
    GET /smart-money/discover?min_volume=1000000&limit=20
    ```
    
    ## **Returns**:
    - List of discovered coins
    - Price, market cap, volume data
    - Whether coin has futures trading
    - Data source for each coin
    
    **Perfect for:** Finding hidden gems before retail discovers them
    """
    result = await smart_money_service.discover_new_coins(
        max_market_cap=max_market_cap,
        min_volume=min_volume,
        source=source,
        limit=limit
    )
    return result


@router.get("/futures/list")
async def list_futures_coins(
    min_volume: float = Query(
        default=1000000,
        description="Minimum 24h volume in USDT (default $1M)"
    )
):
    """
    📊 **Binance Futures Coin List**
    
    Get complete list of all coins available on Binance Futures
    with volume and price change data.
    
    ## **What This Provides**:
    - All perpetual futures symbols
    - 24h volume in USDT
    - Price changes
    - High/Low prices
    
    ## **Use Case**:
    "Show me all coins trading on Binance Futures with volume"
    
    ## **Example**:
    ```
    # All futures coins with $1M+ volume
    GET /smart-money/futures/list
    
    # High volume coins only
    GET /smart-money/futures/list?min_volume=10000000
    ```
    
    **Perfect for:** Knowing which coins have futures trading available
    """
    result = await smart_money_service.get_futures_coins_list(min_volume=min_volume)
    return result


@router.get("/scan/auto")
async def auto_scan(
    criteria: str = Query(
        default="volume",
        description="Selection criteria: 'volume', 'gainers', 'losers', 'small_cap'"
    ),
    limit: int = Query(
        default=20,
        ge=5,
        le=50,
        description="Number of coins to scan"
    ),
    min_accumulation_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum accumulation score"
    ),
    min_distribution_score: int = Query(
        default=5,
        ge=0,
        le=10,
        description="Minimum distribution score"
    )
):
    """
    🤖 **Auto Smart Money Scan** - Intelligent Coin Selection
    
    Automatically select and scan coins based on smart criteria,
    then analyze them for accumulation/distribution patterns.
    
    ## **Selection Criteria**:
    
    ### **volume** (Default)
    - Scans highest volume coins
    - Most liquid and reliable signals
    - Best for mainstream opportunities
    
    ### **gainers**
    - Scans top gainers (24h)
    - Find momentum before continuation
    - Detect if pump is accumulation or distribution
    
    ### **losers**
    - Scans top losers (24h)
    - Find capitulation bottoms (accumulation)
    - Spot distribution dumps early
    
    ### **small_cap**
    - Scans small market cap coins
    - Early opportunities before mainstream
    - Higher risk but bigger potential
    
    ## **Examples**:
    ```
    # Scan top volume coins
    GET /smart-money/scan/auto?criteria=volume
    
    # Find accumulation in top gainers
    GET /smart-money/scan/auto?criteria=gainers&min_accumulation_score=6
    
    # Find distribution in losers
    GET /smart-money/scan/auto?criteria=losers&min_distribution_score=6
    
    # Scan small caps for hidden gems
    GET /smart-money/scan/auto?criteria=small_cap&limit=30
    ```
    
    ## **Returns**:
    - Selected coins based on criteria
    - Full accumulation/distribution analysis
    - Ranked by signal strength
    
    **Perfect for:** "Just find me the best opportunities right now"
    """
    # Auto-select coins
    selection = await smart_money_service.auto_select_coins(
        criteria=criteria,
        limit=limit
    )
    
    if not selection.get("success"):
        return selection
    
    # Scan selected coins
    selected_coins = selection.get("selectedCoins", [])
    
    if not selected_coins:
        return {
            "success": True,
            "criteria": criteria,
            "message": "No coins matched the criteria",
            "accumulation": [],
            "distribution": []
        }
    
    # Perform smart money scan on selected coins
    scan_result = await smart_money_service.scan_markets(
        min_accumulation_score=min_accumulation_score,
        min_distribution_score=min_distribution_score,
        coins=selected_coins
    )
    
    if not scan_result.get("success"):
        return scan_result
    
    return {
        "success": True,
        "criteria": criteria,
        "coinsSelected": selected_coins,
        "coinsScanned": scan_result.get("coinsScanned", 0),
        "summary": scan_result.get("summary", {}),
        "accumulation": scan_result.get("accumulation", []),
        "distribution": scan_result.get("distribution", []),
        "timestamp": scan_result.get("timestamp", "")
    }
