"""
Minimal OpenAPI Schema for GPT Actions - ONLY /invoke endpoint
This ensures GPT Actions sees only 1 operation (not 258+)
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os

router = APIRouter()


@router.get("/openapi-gpt.json", include_in_schema=False)
async def minimal_gpt_schema():
    """
    Minimal OpenAPI schema with ONLY /invoke endpoint
    For GPT Actions compatibility (30 operation limit)
    """
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    # Get all operations for the enum
    from app.utils.operation_catalog import get_all_operations
    all_operations = get_all_operations()
    
    return JSONResponse(
        content={
            "openapi": "3.1.0",
            "info": {
                "title": "CryptoSatX RPC API",
                "version": "3.0.0",
                "description": "Single RPC endpoint with 188+ crypto operations. Use operation parameter to call any function."
            },
            "servers": [{"url": base_url}],
            "paths": {
                "/invoke": {
                    "post": {
                        "operationId": "invoke",
                        "summary": "Unified RPC endpoint - 188+ operations",
                        "description": "Call any of 188+ crypto operations via single endpoint. Specify operation name + parameters.",
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
                                                "enum": all_operations,
                                                "description": f"Operation name - {len(all_operations)} operations available"
                                            },
                                            "symbol": {
                                                "type": "string",
                                                "description": "Crypto symbol (BTC, ETH, SOL)",
                                                "example": "BTC"
                                            },
                                            "interval": {
                                                "type": "string",
                                                "description": "Time interval (1m, 5m, 15m, 1h, 4h, 1d)",
                                                "example": "1h"
                                            },
                                            "limit": {
                                                "type": "integer",
                                                "description": "Result limit",
                                                "example": 10
                                            },
                                            "exchange": {
                                                "type": "string",
                                                "description": "Exchange (Binance, OKX, Bybit)",
                                                "example": "Binance"
                                            },
                                            "send_telegram": {
                                                "type": "boolean",
                                                "default": False,
                                                "description": "Send full report to Telegram (overcomes GPT timeout limits)"
                                            },
                                            "debug": {
                                                "type": "boolean",
                                                "default": False,
                                                "description": "Enable debug output"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "ok": {"type": "boolean"},
                                                "operation": {"type": "string"},
                                                "data": {"type": "object"},
                                                "error": {"type": "string"},
                                                "meta": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache"
        }
    )
