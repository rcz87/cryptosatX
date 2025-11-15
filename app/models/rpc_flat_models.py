"""
RPC Flat Models - GPT Actions Compatible
Uses flat parameters instead of nested args for GPT Actions compatibility
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class FlatInvokeRequest(BaseModel):
    """
    Flat parameter request model for GPT Actions compatibility

    All parameters are at root level (not nested under 'args')
    """
    # REQUIRED: Operation identifier
    operation: str = Field(
        ...,
        description="Operation to execute (e.g., 'signals.get', 'coinglass.liquidations.symbol')"
    )

    # OPTIONAL: Common parameters (flat at root level)
    symbol: Optional[str] = Field(
        None,
        description="Cryptocurrency symbol (BTC, ETH, SOL, etc.)"
    )
    interval: Optional[str] = Field(
        None,
        description="Time interval (1m, 5m, 15m, 1h, 4h, 1d)"
    )
    timeframe: Optional[str] = Field(
        None,
        description="Timeframe for analysis (1MIN, 5MIN, 15MIN, 1HRS, 4HRS, 1DAY)"
    )
    limit: Optional[int] = Field(
        None,
        description="Result limit (default varies by operation)"
    )
    exchange: Optional[str] = Field(
        None,
        description="Exchange name (Binance, OKX, Bybit, etc.)"
    )
    debug: Optional[bool] = Field(
        False,
        description="Enable debug mode for detailed output"
    )
    mode: Optional[str] = Field(
        "aggressive",
        description="Signal mode: 'conservative'/'1' (safe, minimal false positives), 'aggressive'/'2' (balanced, default), 'ultra'/'3' (maximum signals, scalping)"
    )

    # Additional flat parameters
    topic: Optional[str] = Field(None, description="Topic name for topic-based operations")
    asset: Optional[str] = Field(None, description="Asset name (BTC, ETH)")
    time_type: Optional[str] = Field(None, description="Time type (h1, h4, h12, h24, all)")
    min_accumulation_score: Optional[int] = Field(None, description="Minimum accumulation score (0-10)")
    min_distribution_score: Optional[int] = Field(None, description="Minimum distribution score (0-10)")
    min_mss_score: Optional[int] = Field(None, description="Minimum MSS score (0-100)")
    max_results: Optional[int] = Field(None, description="Maximum number of results")
    coins: Optional[str] = Field(None, description="Comma-separated coin list")
    min_galaxy_score: Optional[int] = Field(None, description="Minimum Galaxy score (LunarCrush)")
    include_raw: Optional[bool] = Field(None, description="Include raw data in response")
    include_content: Optional[bool] = Field(None, description="Include full article content in news feed (false for GPT Actions)")
    signal_filter: Optional[Literal["OVERSOLD", "OVERBOUGHT", "NEUTRAL"]] = Field(None, description="Filter RSI signals: OVERSOLD, OVERBOUGHT, or NEUTRAL")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "operation": "signals.get",
                    "symbol": "BTC",
                    "debug": False
                },
                {
                    "operation": "coinglass.liquidations.symbol",
                    "symbol": "SOL",
                    "interval": "1h",
                    "limit": 100
                },
                {
                    "operation": "smart_money.scan",
                    "min_accumulation_score": 7,
                    "min_distribution_score": 7
                }
            ]
        }


class FlatRPCResponse(BaseModel):
    """Unified RPC response"""
    ok: bool = Field(..., description="Success status")
    operation: str = Field(..., description="Operation that was executed")
    data: Optional[dict] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if ok=False")
    meta: Optional[dict] = Field(None, description="Metadata (execution time, etc.)")
