"""
Unified RPC Endpoint for GPT Actions
Single /invoke endpoint that maps to 100+ operations
Bypasses GPT Actions 30-operation limit
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from app.models.rpc_models import RPCRequest, RPCResponse
from app.core.rpc_dispatcher import rpc_dispatcher
from app.utils.operation_catalog import get_all_operations

router = APIRouter()


@router.post("/invoke", response_model=RPCResponse, summary="Unified RPC Endpoint")
async def invoke_operation(request: RPCRequest) -> RPCResponse:
    """
    🚀 **Unified RPC Endpoint - All Operations in One**
    
    This endpoint provides access to ALL API operations through a single RPC interface.
    Perfect for GPT Actions integration (bypasses 30-operation limit).
    
    **How to use:**
    ```json
    {
      "operation": "signals.get",
      "args": {
        "symbol": "BTC",
        "debug": false
      }
    }
    ```
    
    **Available Operations (20+ namespaces):**
    
    **Core Signals:**
    - `signals.get` - Get trading signal for symbol
    - `market.get` - Get aggregated market data
    
    **Coinglass Data (65+ operations):**
    - `coinglass.markets` - Get all markets
    - `coinglass.liquidations.symbol` - Get liquidations for symbol
    - `coinglass.funding_rate.history` - Get funding rate history
    - `coinglass.open_interest.history` - Get open interest history
    - `coinglass.indicators.fear_greed` - Get Fear & Greed Index
    - `coinglass.indicators.rsi_list` - Get RSI list (535 coins)
    - `coinglass.supported_coins` - Get supported coins
    
    **Smart Money:**
    - `smart_money.scan` - Scan whale accumulation/distribution
    - `smart_money.scan_accumulation` - Find accumulation opportunities
    - `smart_money.scan_distribution` - Find distribution opportunities
    - `smart_money.analyze` - Analyze smart money for symbol
    
    **MSS (Multi-Modal Signal Score):**
    - `mss.discover` - Discover high-potential cryptocurrencies
    - `mss.analyze` - Analyze MSS for symbol
    - `mss.scan` - Scan market with MSS
    
    **LunarCrush Social:**
    - `lunarcrush.coin` - Get coin social metrics (60+ data points)
    - `lunarcrush.coins_discovery` - Discover coins via social data
    
    **CoinAPI Market Data:**
    - `coinapi.quote` - Get current quote
    
    **Health:**
    - `health.check` - API health check
    
    **Response Format:**
    ```json
    {
      "ok": true,
      "operation": "signals.get",
      "data": { ...operation result... },
      "meta": {
        "execution_time_ms": 245.67,
        "namespace": "signals"
      }
    }
    ```
    
    **Error Response:**
    ```json
    {
      "ok": false,
      "operation": "signals.get",
      "error": "Missing required argument: symbol",
      "meta": {...}
    }
    ```
    """
    # Dispatch to handler
    response = await rpc_dispatcher.dispatch(
        operation=request.operation,
        args=request.args
    )
    
    return response


@router.get("/invoke/operations", summary="List Available Operations")
async def list_operations() -> Dict[str, Any]:
    """
    📋 **List All Available RPC Operations**
    
    Returns comprehensive list of all operations available via /invoke endpoint.
    Organized by namespace for easy discovery.
    """
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


@router.get("/invoke/schema", summary="Get GPT Actions OpenAPI Schema")
async def get_gpt_actions_schema(request: Request) -> Dict[str, Any]:
    """
    📄 **GPT Actions Compatible OpenAPI Schema**
    
    Returns OpenAPI 3.1 schema optimized for GPT Actions integration.
    Single /invoke operation with complete enum of available operations.
    
    **For GPT Actions:**
    1. Copy this URL: `https://guardiansofthetoken.org/invoke/schema`
    2. Import into GPT Actions
    3. GPT can now call any of 100+ operations via single /invoke endpoint
    """
    import os
    from app.utils.operation_catalog import OPERATION_CATALOG
    
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    # Get all operation names for enum
    operation_names = list(OPERATION_CATALOG.keys())
    
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX Unified RPC API",
            "version": "3.0.0",
            "description": (
                "Single unified RPC endpoint providing access to 100+ crypto market operations.\n\n"
                "**Key Features:**\n"
                "- 65+ Coinglass endpoints (liquidations, funding, OI, indicators)\n"
                "- Smart Money whale tracking\n"
                "- MSS (Multi-Modal Signal Score) discovery system\n"
                "- LunarCrush social sentiment (7,600+ coins)\n"
                "- CoinAPI comprehensive market data\n"
                "- Real-time trading signals\n\n"
                "**How to Use:**\n"
                "Call POST /invoke with operation name + args.\n"
                "Example: {\"operation\": \"signals.get\", \"args\": {\"symbol\": \"BTC\"}}"
            )
        },
        "servers": [
            {
                "url": base_url,
                "description": "Production server"
            }
        ],
        "paths": {
            "/invoke": {
                "post": {
                    "operationId": "invoke",
                    "summary": "Unified RPC operation invocation",
                    "description": "Single endpoint for all operations. Select operation via enum and provide args.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["operation"],
                                    "properties": {
                                        "operation": {
                                            "type": "string",
                                            "description": "Operation to execute",
                                            "enum": operation_names[:100]  # Limit to 100 for schema size
                                        },
                                        "args": {
                                            "type": "object",
                                            "description": "Operation-specific arguments",
                                            "additionalProperties": True
                                        }
                                    }
                                },
                                "examples": {
                                    "getSignal": {
                                        "summary": "Get BTC trading signal",
                                        "value": {
                                            "operation": "signals.get",
                                            "args": {"symbol": "BTC"}
                                        }
                                    },
                                    "scanSmartMoney": {
                                        "summary": "Scan smart money activity",
                                        "value": {
                                            "operation": "smart_money.scan",
                                            "args": {"min_accumulation_score": 7}
                                        }
                                    },
                                    "mssDiscover": {
                                        "summary": "Discover high-potential coins",
                                        "value": {
                                            "operation": "mss.discover",
                                            "args": {"min_mss_score": 75, "max_results": 10}
                                        }
                                    },
                                    "coinglassLiquidations": {
                                        "summary": "Get SOL liquidations",
                                        "value": {
                                            "operation": "coinglass.liquidations.symbol",
                                            "args": {"symbol": "SOL"}
                                        }
                                    },
                                    "lunarcrushCoin": {
                                        "summary": "Get PEPE social metrics",
                                        "value": {
                                            "operation": "lunarcrush.coin",
                                            "args": {"symbol": "PEPE"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Operation result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ok": {"type": "boolean"},
                                            "operation": {"type": "string"},
                                            "data": {"type": "object"},
                                            "meta": {"type": "object"},
                                            "error": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return schema
