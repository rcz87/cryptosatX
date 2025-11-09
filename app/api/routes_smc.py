# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Smart Money Concept (SMC) Analysis Routes
New endpoints for SMC analysis - does not modify existing routes
"""
from fastapi import APIRouter, Query, Depends
from app.services.smc_analyzer import smc_analyzer
from app.middleware.auth import get_optional_api_key
from app.utils.logger import default_logger, log_api_call
import time

router = APIRouter(prefix="/smc", tags=["Smart Money Concept (SMC)"])


@router.get("/analyze/{symbol}")
async def analyze_smc(
    symbol: str,
    timeframe: str = Query("1HRS", description="Timeframe: 1MIN, 5MIN, 1HRS, 1DAY"),
    api_key: str = Depends(get_optional_api_key)
):
    """
    🧠 **Smart Money Concept Analysis** - Institutional Trading Patterns
    
    Analyzes price action using SMC principles to identify institutional behavior:
    
    ## **What You Get:**
    - **BOS (Break of Structure)**: Price breaking key levels in trend direction
    - **CHoCH (Change of Character)**: Potential trend reversal signals
    - **FVG (Fair Value Gaps)**: Price imbalances where smart money operates
    - **Swing Points**: Key support/resistance from institutional activity
    - **Liquidity Zones**: Areas where stop losses cluster
    - **Market Structure**: Overall trend and strength assessment
    
    ## **Use Cases:**
    - Entry timing at institutional levels
    - Trend confirmation and reversal detection
    - Risk management around liquidity zones
    - Understanding smart money positioning
    
    ## **Timeframes:**
    - `1MIN`, `5MIN` - Scalping and day trading
    - `1HRS` - Swing trading (default)
    - `1DAY` - Position trading
    
    ## **Example:**
    ```
    GET /smc/analyze/BTC?timeframe=1HRS
    ```
    
    Returns comprehensive SMC analysis with actionable insights.
    """
    start_time = time.time()
    
    try:
        result = await smc_analyzer.analyze_smc(symbol.upper(), timeframe)
        
        duration = time.time() - start_time
        log_api_call(
            default_logger, 
            f"/smc/analyze/{symbol}", 
            symbol=symbol,
            duration=duration,
            status="success" if result.get("success") else "error",
            extra_data={"timeframe": timeframe}
        )
        
        return result
    
    except Exception as e:
        log_api_call(
            default_logger,
            f"/smc/analyze/{symbol}",
            symbol=symbol,
            duration=time.time() - start_time,
            status="error",
            extra_data={"error": str(e)}
        )
        return {
            "success": False,
            "error": f"SMC analysis failed: {str(e)}"
        }


@router.get("/info")
async def smc_info():
    """
    📚 **SMC Methodology Information**
    
    Learn about Smart Money Concept analysis and how to interpret the results.
    """
    return {
        "name": "Smart Money Concept (SMC) Analyzer",
        "description": "Identifies institutional trading patterns and market structure",
        "concepts": {
            "BOS": {
                "name": "Break of Structure",
                "description": "Price breaking previous swing high/low in trend direction",
                "signal": "Trend continuation"
            },
            "CHoCH": {
                "name": "Change of Character",
                "description": "Price breaking counter-trend swing point",
                "signal": "Potential trend reversal"
            },
            "FVG": {
                "name": "Fair Value Gap",
                "description": "Price imbalance where institutions operate",
                "signal": "Entry/exit zones for smart money"
            },
            "SwingPoints": {
                "description": "Key highs and lows from institutional activity",
                "signal": "Support/resistance levels"
            },
            "LiquidityZones": {
                "description": "Areas where stop losses cluster",
                "signal": "Price magnets for liquidity sweeps"
            }
        },
        "interpretation": {
            "bullish_structure": "BOS above swing highs + bullish FVGs",
            "bearish_structure": "BOS below swing lows + bearish FVGs",
            "reversal_signals": "CHoCH + FVG in opposite direction"
        },
        "timeframes": ["1MIN", "5MIN", "15MIN", "1HRS", "4HRS", "1DAY"]
    }
