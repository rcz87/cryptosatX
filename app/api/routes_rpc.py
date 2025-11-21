"""
RPC Endpoints - Unified API for all operations
Supports both traditional nested args and flat parameters for GPT Actions
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional, Any, Dict
from pydantic import BaseModel
from app.models.rpc_flat_models import FlatInvokeRequest, FlatRPCResponse
from app.core.rpc_flat_dispatcher import flat_rpc_dispatcher
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/rpc/info", summary="API Health & Info")
async def root():
    """Get API information and health status"""
    return {
        "name": "Crypto Futures Signal API",
        "version": "1.0.0",
        "description": "Production-ready crypto futures signal API with multi-provider integration",
        "endpoints": {
            "health": "/health",
            "signals": "/signals/{symbol}",
            "market": "/market/{symbol}",
            "gpt_schema": "/gpt/action-schema"
        }
    }


@router.get("/invoke/operations", summary="List all available operations")
async def list_operations():
    """List all 187+ operations available"""
    from app.utils.operation_catalog import get_all_operations
    
    operations = get_all_operations()
    
    # Group by namespace
    by_namespace: Dict[str, list] = {}
    for op in operations:
        namespace = op.split('.')[0]
        if namespace not in by_namespace:
            by_namespace[namespace] = []
        by_namespace[namespace].append(op)
    
    return {
        "total_operations": len(operations),
        "namespaces": list(by_namespace.keys()),
        "operations_by_namespace": by_namespace,
        "usage_example": {
            "endpoint": "/invoke",
            "method": "POST",
            "body": {
                "operation": "signals.get",
                "args": {"symbol": "BTC"}
            }
        }
    }


@router.post("/invoke", summary="Unified RPC Endpoint - All 192+ Operations", response_model=FlatRPCResponse)
async def invoke_rpc(request: FlatInvokeRequest) -> FlatRPCResponse:
    """
    ✅ **Unified RPC Endpoint - FLAT PARAMETERS (GPT Actions Compatible)**

    Single endpoint for all 192+ crypto operations.
    
    **FLAT PARAMETERS** - All parameters at root level (not nested)
    
    Example:
    ```json
    {
        "operation": "signals.get",
        "symbol": "BTC",
        "send_telegram": false
    }
    ```
    
    **Available Operations:**
    - `signals.get` - Get trading signal for coin
    - `coinglass.*` - 65+ Coinglass operations
    - `smart_money.*` - Smart money analysis
    - `mss.*` - Multi-Modal Signal Score discovery
    - `lunarcrush.*` - Social sentiment analysis
    - And 150+ more...
    
    **Parameters:**
    - `operation` (required) - Operation name
    - `symbol` - Cryptocurrency symbol (BTC, ETH, SOL)
    - `send_telegram` - Send results to Telegram (default: false)
    - Other parameters depend on operation
    
    **Response:**
    - `ok` - Success status
    - `data` - Operation result
    - `error` - Error message if failed
    - `meta` - Execution metadata
    """
    
    try:
        # Dispatch to RPC handler
        response = await flat_rpc_dispatcher.dispatch(request)
        return response
    except Exception as e:
        logger.error(f"RPC Error: {str(e)}", exc_info=True)
        return FlatRPCResponse(
            ok=False,
            operation=request.operation,
            data=None,
            error=str(e),
            meta={"error_type": type(e).__name__}
        )
