"""
Unified RPC Endpoint for GPT Actions - UPGRADED with FLAT PARAMETERS
Single /invoke endpoint that maps to 192+ operations
Bypasses GPT Actions 30-operation limit
NOW SUPPORTS FLAT PARAMETERS for GPT Actions compatibility!
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Union

# Legacy nested args support (backward compatible)
from app.models.rpc_models import RPCRequest, RPCResponse
from app.core.rpc_dispatcher import rpc_dispatcher

# NEW: Flat parameters support (GPT Actions compatible)
from app.models.rpc_flat_models import FlatInvokeRequest, FlatRPCResponse
from app.core.rpc_flat_dispatcher import flat_rpc_dispatcher

from app.utils.operation_catalog import get_all_operations, OPERATION_CATALOG

router = APIRouter()


@router.post("/invoke", summary="Unified RPC Endpoint (Supports Both Nested & Flat)")
async def invoke_operation(request: Union[FlatInvokeRequest, RPCRequest]) -> Union[FlatRPCResponse, RPCResponse]:
    """
    🚀 **Unified RPC Endpoint - UPGRADED with Flat Parameters Support**

    Access to 192+ operations through ONE endpoint.
    Bypasses GPT Actions 30-operation limit.

    **✅ NEW: GPT Actions Compatible - Flat Parameters (RECOMMENDED)**
    ```json
    {
      "operation": "signals.get",
      "symbol": "BTC",
      "debug": false
    }
    ```

    **⚠️ LEGACY: Nested Args (Still Supported - Backward Compatible)**
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
    # Auto-detect request type and dispatch accordingly
    
    # Check if request is legacy nested format (RPCRequest) vs flat (FlatInvokeRequest)
    if isinstance(request, RPCRequest) and request.args:
        # Legacy nested args format - use old dispatcher
        response = await rpc_dispatcher.dispatch(
            operation=request.operation,
            args=request.args
        )
        return response
    else:
        # NEW: Flat parameters format (GPT Actions compatible)
        response = await flat_rpc_dispatcher.dispatch(request)
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


@router.get("/invoke/schema", summary="Get GPT Actions OpenAPI Schema (Flat Parameters)")
async def get_gpt_actions_schema(request: Request):
    """
    📄 **GPT Actions Compatible OpenAPI Schema - FLAT PARAMETERS**

    Returns OpenAPI 3.1 schema optimized for GPT Actions with FLAT parameters.
    Single /invoke operation with 192+ operations accessible via operation enum.

    **✅ USES FLAT PARAMETERS (GPT Actions Compatible!)**

    **For GPT Actions:**
    1. Copy this URL: `https://guardiansofthetoken.org/invoke/schema`
    2. Import into GPT Actions
    3. GPT can now call any of 192 operations via single /invoke endpoint
    4. All parameters are FLAT (not nested under 'args')
    
    **Cache Control:** This endpoint serves fresh schema on every request to prevent CDN caching issues.
    """
    import os
    from app.utils.operation_catalog import OPERATION_CATALOG

    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")

    # Get top operations for enum (limit to keep schema manageable)
    # Priority: Core signals, Coinglass key endpoints, Smart Money, MSS, LunarCrush
    priority_operations = [
        # Core
        "signals.get", "market.get", "health.check",

        # Coinglass - Most Important
        "coinglass.liquidations.symbol",
        "coinglass.liquidations.heatmap",
        "coinglass.funding_rate.history",
        "coinglass.open_interest.history",
        "coinglass.indicators.fear_greed",
        "coinglass.indicators.rsi_list",
        "coinglass.indicators.whale_index",
        "coinglass.orderbook.whale_walls",
        "coinglass.chain.whale_transfers",
        "coinglass.markets",
        "coinglass.supported_coins",
        # Removed: "coinglass.perpetual_market.symbol" (Deprecated - HTTP 404)
        "coinglass.etf.flows",
        "coinglass.onchain.reserves",
        "coinglass.long_short_ratio.account_history",
        "coinglass.long_short_ratio.position_history",

        # Smart Money
        "smart_money.scan",
        "smart_money.scan_accumulation",
        "smart_money.analyze",

        # MSS
        "mss.discover",
        "mss.analyze",
        "mss.scan",

        # LunarCrush
        "lunarcrush.coin",
        "lunarcrush.coin_momentum",
        "lunarcrush.coins_discovery",

        # CoinAPI
        "coinapi.quote",
        "coinapi.ohlcv.latest",
        "coinapi.orderbook",
        "coinapi.trades",
    ]

    # Add remaining operations (up to 100 total for GPT Actions compatibility)
    operation_names = priority_operations.copy()
    remaining = [op for op in OPERATION_CATALOG.keys() if op not in priority_operations]
    operation_names.extend(remaining[:70])  # Total ~100 operations
    
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX Unified RPC API - Flat Parameters",
            "version": "3.0.0-flat",
            "description": (
                "✅ **GPT Actions Compatible** - Single RPC endpoint with FLAT parameters.\n\n"
                "Access to 192+ crypto market operations through ONE endpoint.\n\n"
                "**Key Features:**\n"
                "- 67+ Coinglass endpoints (liquidations, funding, OI, whale tracking, indicators)\n"
                "- Smart Money accumulation/distribution detection\n"
                "- MSS (Multi-Modal Signal Score) discovery system\n"
                "- LunarCrush social sentiment (7,600+ coins)\n"
                "- CoinAPI comprehensive market data\n"
                "- Real-time AI trading signals\n\n"
                "**✅ Flat Parameters (GPT Actions Compatible):**\n"
                "All parameters are at root level, not nested.\n"
                "Example: {\"operation\": \"signals.get\", \"symbol\": \"BTC\"}\n\n"
                "**Operations Count:** " + str(len(operation_names)) + " available"
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
                    "operationId": "invokeOperation",
                    "summary": "Unified RPC with FLAT parameters (GPT Actions compatible)",
                    "description": (
                        "Single endpoint for all 192+ operations.\n\n"
                        "✅ **USES FLAT PARAMETERS** (not nested args).\n\n"
                        "Select operation via enum and provide parameters at root level.\n\n"
                        "Example: {\"operation\": \"signals.get\", \"symbol\": \"BTC\"}"
                    ),
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
                                            "description": "Operation to execute (select from enum)",
                                            "enum": operation_names
                                        },
                                        "send_telegram": {
                                            "type": "boolean",
                                            "description": "Send results to Telegram",
                                            "default": False
                                        },
                                        "symbol": {
                                            "type": "string",
                                            "description": "Cryptocurrency symbol (BTC, ETH, SOL, etc.)",
                                            "nullable": True
                                        },
                                        "interval": {
                                            "type": "string",
                                            "description": "Time interval (1m, 5m, 15m, 1h, 4h, 1d)",
                                            "nullable": True
                                        },
                                        "timeframe": {
                                            "type": "string",
                                            "description": "Timeframe (1MIN, 5MIN, 15MIN, 1HRS, 4HRS, 1DAY)",
                                            "nullable": True
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Result limit",
                                            "nullable": True
                                        },
                                        "exchange": {
                                            "type": "string",
                                            "description": "Exchange name (Binance, OKX, Bybit, etc.)",
                                            "nullable": True
                                        },
                                        "debug": {
                                            "type": "boolean",
                                            "description": "Enable debug mode",
                                            "nullable": True
                                        },
                                        "time_type": {
                                            "type": "string",
                                            "description": "Time type (h1, h4, h12, h24, all)",
                                            "nullable": True
                                        },
                                        "min_accumulation_score": {
                                            "type": "integer",
                                            "description": "Minimum accumulation score (0-10)",
                                            "nullable": True
                                        },
                                        "min_distribution_score": {
                                            "type": "integer",
                                            "description": "Minimum distribution score (0-10)",
                                            "nullable": True
                                        },
                                        "min_mss_score": {
                                            "type": "integer",
                                            "description": "Minimum MSS score (0-100)",
                                            "nullable": True
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "description": "Maximum number of results",
                                            "nullable": True
                                        },
                                        "asset": {
                                            "type": "string",
                                            "description": "Asset name (BTC, ETH)",
                                            "nullable": True
                                        },
                                        "topic": {
                                            "type": "string",
                                            "description": "Topic name",
                                            "nullable": True
                                        }
                                    }
                                },
                                "examples": {
                                    "getSignalBTC": {
                                        "summary": "Get BTC trading signal (FLAT params)",
                                        "description": "✅ Flat parameters - symbol at root level",
                                        "value": {
                                            "operation": "signals.get",
                                            "symbol": "BTC"
                                        }
                                    },
                                    "getSignalSOL": {
                                        "summary": "Get SOL trading signal (FLAT params)",
                                        "description": "✅ Flat parameters - no nested args",
                                        "value": {
                                            "operation": "signals.get",
                                            "symbol": "SOL"
                                        }
                                    },
                                    "liquidationsSOL": {
                                        "summary": "Get SOL liquidations (FLAT params)",
                                        "description": "✅ Coinglass liquidations with flat parameters",
                                        "value": {
                                            "operation": "coinglass.liquidations.symbol",
                                            "symbol": "SOL",
                                            "time_type": "h24"
                                        }
                                    },
                                    "fearGreedIndex": {
                                        "summary": "Get Fear & Greed Index",
                                        "description": "✅ No parameters needed for some operations",
                                        "value": {
                                            "operation": "coinglass.indicators.fear_greed"
                                        }
                                    },
                                    "scanSmartMoney": {
                                        "summary": "Scan smart money accumulation (FLAT params)",
                                        "description": "✅ Flat parameters for smart money scan",
                                        "value": {
                                            "operation": "smart_money.scan",
                                            "min_accumulation_score": 7,
                                            "min_distribution_score": 7
                                        }
                                    },
                                    "mssDiscover": {
                                        "summary": "Discover high-potential coins (FLAT params)",
                                        "description": "✅ MSS discovery with flat parameters",
                                        "value": {
                                            "operation": "mss.discover",
                                            "min_mss_score": 75,
                                            "max_results": 10
                                        }
                                    },
                                    "lunarCrushCoin": {
                                        "summary": "Get LunarCrush social data (FLAT params)",
                                        "description": "✅ Social metrics for coin",
                                        "value": {
                                            "operation": "lunarcrush.coin",
                                            "symbol": "BTC"
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
    
    # Return with Cache-Control headers to prevent CDN/proxy caching
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        content=schema,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/invoke/openapi.json", summary="OpenAPI Schema for GPT Actions (Clean URL)")
async def get_openapi_json():
    """
    📄 **OpenAPI Schema - NEW ENDPOINT (Fresh CDN Cache!)**

    Alternative endpoint for GPT Actions schema import - avoids CDN caching issues.
    
    **For GPT Actions Import:**
    Use URL: `https://guardiansofthetoken.org/invoke/openapi.json`
    
    Returns same complete schema with FLAT parameters and 192+ operations.
    Fresh response every time - no CDN caching!
    """
    import os
    from app.utils.operation_catalog import OPERATION_CATALOG
    from fastapi.responses import JSONResponse

    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")

    # Get top operations for enum (same as /invoke/schema)
    priority_operations = [
        # Core
        "signals.get", "market.get", "health.check",

        # Coinglass - Most Important
        "coinglass.liquidations.symbol",
        "coinglass.liquidations.heatmap",
        "coinglass.funding_rate.history",
        "coinglass.open_interest.history",
        "coinglass.indicators.fear_greed",
        "coinglass.indicators.rsi_list",
        "coinglass.indicators.whale_index",
        "coinglass.orderbook.whale_walls",
        "coinglass.chain.whale_transfers",
        "coinglass.markets",
        "coinglass.supported_coins",
        "coinglass.etf.flows",
        "coinglass.onchain.reserves",
        "coinglass.long_short_ratio.account_history",
        "coinglass.long_short_ratio.position_history",

        # Smart Money
        "smart_money.scan",
        "smart_money.scan_accumulation",
        "smart_money.analyze",

        # MSS
        "mss.discover",
        "mss.analyze",
        "mss.scan",

        # LunarCrush
        "lunarcrush.coin",
        "lunarcrush.coin_momentum",
        "lunarcrush.coins_discovery",

        # CoinAPI
        "coinapi.quote",
        "coinapi.ohlcv.latest",
        "coinapi.orderbook",
        "coinapi.trades",
    ]

    operation_names = priority_operations.copy()
    remaining = [op for op in OPERATION_CATALOG.keys() if op not in priority_operations]
    operation_names.extend(remaining[:70])
    
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX Unified RPC API - Flat Parameters",
            "version": "3.0.0-flat",
            "description": (
                "✅ **GPT Actions Compatible** - Single RPC endpoint with FLAT parameters.\n\n"
                "Access to 192+ crypto market operations through ONE endpoint.\n\n"
                "**Key Features:**\n"
                "- 67+ Coinglass endpoints (liquidations, funding, OI, whale tracking, indicators)\n"
                "- Smart Money accumulation/distribution detection\n"
                "- MSS (Multi-Modal Signal Score) discovery system\n"
                "- LunarCrush social sentiment (7,600+ coins)\n"
                "- CoinAPI comprehensive market data\n"
                "- Real-time AI trading signals\n\n"
                "**✅ Flat Parameters (GPT Actions Compatible):**\n"
                "All parameters are at root level, not nested.\n"
                "Example: {\"operation\": \"signals.get\", \"symbol\": \"BTC\"}\n\n"
                "**Operations Count:** " + str(len(operation_names)) + " available"
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
                    "operationId": "invokeOperation",
                    "summary": "Unified RPC with FLAT parameters (GPT Actions compatible)",
                    "description": (
                        "Single endpoint for all 192+ operations.\n\n"
                        "✅ **USES FLAT PARAMETERS** (not nested args).\n\n"
                        "Select operation via enum and provide parameters at root level.\n\n"
                        "Example: {\"operation\": \"signals.get\", \"symbol\": \"BTC\"}"
                    ),
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
                                            "description": "Operation to execute (select from enum)",
                                            "enum": operation_names
                                        },
                                        "send_telegram": {
                                            "type": "boolean",
                                            "description": "Send results to Telegram",
                                            "default": False
                                        },
                                        "symbol": {
                                            "type": "string",
                                            "description": "Cryptocurrency symbol (BTC, ETH, SOL, etc.)",
                                            "nullable": True
                                        },
                                        "interval": {
                                            "type": "string",
                                            "description": "Time interval (1m, 5m, 15m, 1h, 4h, 1d)",
                                            "nullable": True
                                        },
                                        "timeframe": {
                                            "type": "string",
                                            "description": "Timeframe (1MIN, 5MIN, 15MIN, 1HRS, 4HRS, 1DAY)",
                                            "nullable": True
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Result limit",
                                            "nullable": True
                                        },
                                        "exchange": {
                                            "type": "string",
                                            "description": "Exchange name (Binance, OKX, Bybit, etc.)",
                                            "nullable": True
                                        },
                                        "debug": {
                                            "type": "boolean",
                                            "description": "Enable debug mode",
                                            "nullable": True
                                        },
                                        "time_type": {
                                            "type": "string",
                                            "description": "Time type (h1, h4, h12, h24, all)",
                                            "nullable": True
                                        },
                                        "min_accumulation_score": {
                                            "type": "integer",
                                            "description": "Minimum accumulation score (0-10)",
                                            "nullable": True
                                        },
                                        "min_distribution_score": {
                                            "type": "integer",
                                            "description": "Minimum distribution score (0-10)",
                                            "nullable": True
                                        },
                                        "min_mss_score": {
                                            "type": "integer",
                                            "description": "Minimum MSS score (0-100)",
                                            "nullable": True
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "description": "Maximum results to return",
                                            "nullable": True
                                        },
                                        "asset": {
                                            "type": "string",
                                            "description": "Asset symbol or type",
                                            "nullable": True
                                        },
                                        "topic": {
                                            "type": "string",
                                            "description": "Topic name",
                                            "nullable": True
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
    
    # Return with aggressive cache-control and CDN bypass headers
    return JSONResponse(
        content=schema,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Expires": "0"  # Nginx bypass
        }
    )
