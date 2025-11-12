"""
RPC Request/Response Models
Pydantic models for unified /invoke endpoint
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class RPCRequest(BaseModel):
    """Unified RPC request model"""
    operation: str = Field(..., description="Operation name (e.g., 'signals.get', 'coinglass.liquidations.symbol')")
    args: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific arguments")


class RPCResponse(BaseModel):
    """Unified RPC response model"""
    ok: bool = Field(..., description="Success status")
    operation: str = Field(..., description="Operation name that was executed")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata (execution time, data sources, etc.)")
    error: Optional[str] = Field(None, description="Error message if ok=False")


class OperationArgsBase(BaseModel):
    """Base class for operation arguments"""
    pass


class SymbolArgs(OperationArgsBase):
    """Arguments for operations requiring symbol"""
    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH, SOL)")
    debug: Optional[bool] = Field(False, description="Enable debug mode")


class TopicArgs(OperationArgsBase):
    """Arguments for operations requiring topic"""
    topic: str = Field(..., description="Topic name")


class AssetArgs(OperationArgsBase):
    """Arguments for operations requiring asset"""
    asset: str = Field(..., description="Asset name")


class ExchangeArgs(OperationArgsBase):
    """Arguments for operations requiring exchange"""
    exchange: str = Field(..., description="Exchange name")


class SmartMoneyScanArgs(OperationArgsBase):
    """Arguments for smart money scan"""
    min_accumulation_score: Optional[int] = Field(5, ge=0, le=10)
    min_distribution_score: Optional[int] = Field(5, ge=0, le=10)
    coins: Optional[str] = Field(None, description="Comma-separated coin list")


class MSSAnalyzeArgs(OperationArgsBase):
    """Arguments for MSS analysis"""
    symbol: str
    include_raw: Optional[bool] = False


class DateRangeArgs(OperationArgsBase):
    """Arguments for date range queries"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = 100


class OHLCVArgs(OperationArgsBase):
    """Arguments for OHLCV data"""
    symbol: str
    interval: Optional[str] = "1h"
    limit: Optional[int] = 100


class MonitoringConfigArgs(OperationArgsBase):
    """Arguments for monitoring configuration"""
    interval: Optional[int] = 300
    threshold: Optional[float] = 100.0
    coins: Optional[List[str]] = None
