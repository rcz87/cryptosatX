"""
Top 30 Operations Schema - Exactly 30 operations for GPT Actions compatibility
This bypasses the 30-operation limit while covering all major functionality
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os

router = APIRouter()

TOP_30_OPERATIONS = [
    "signals.get",
    "health.check",
    "market.get",
    "coinglass.liquidations.symbol",
    "coinglass.funding_rate.history",
    "coinglass.open_interest.history",
    "coinglass.indicators.fear_greed",
    "coinglass.indicators.rsi_list",
    "coinglass.indicators.whale_index",
    "coinglass.long_short_ratio.account_history",
    "coinglass.long_short_ratio.position_history",
    "coinglass.etf.flows",
    "coinglass.onchain.reserves",
    "coinglass.orderbook.whale_walls",
    "smart_money.scan",
    "smart_money.scan_accumulation",
    "smart_money.analyze",
    "mss.discover",
    "mss.analyze",
    "mss.scan",
    "lunarcrush.coin",
    "lunarcrush.coin_momentum",
    "lunarcrush.coins_discovery",
    "coinapi.quote",
    "coinapi.ohlcv.latest",
    "coinapi.orderbook",
    "coinapi.trades",
    "coinglass.liquidations.heatmap",
    "coinglass.markets",
    "coinglass.supported_coins"
]

@router.get("/openapi-top30.json", include_in_schema=False)
async def get_top30_schema():
    """
    OpenAPI Schema with TOP 30 operations only - GPT Actions compatible!
    Exactly 30 operations = within GPT Actions limit
    """
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    return JSONResponse(
        content={
            "openapi": "3.1.0",
            "info": {
                "title": "CryptoSatX - Top 30 Operations (GPT Actions)",
                "version": "1.0.0",
                "description": "Top 30 most important crypto operations. Exactly 30 operations for GPT Actions compatibility."
            },
            "servers": [{"url": base_url, "description": "Production"}],
            "paths": {
                "/invoke": {
                    "post": {
                        "operationId": "invokeRPC",
                        "summary": "Call any of 30 top operations",
                        "description": "RPC endpoint - call any operation with operation name + parameters",
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
                                                "enum": TOP_30_OPERATIONS,
                                                "description": "Operation name (30 top operations)"
                                            },
                                            "symbol": {
                                                "type": "string",
                                                "description": "Crypto symbol (BTC, ETH, SOL)"
                                            },
                                            "interval": {
                                                "type": "string",
                                                "description": "Time interval (1m, 5m, 15m, 1h, 4h, 1d)"
                                            },
                                            "limit": {
                                                "type": "integer",
                                                "description": "Result limit"
                                            },
                                            "exchange": {
                                                "type": "string",
                                                "description": "Exchange (Binance, OKX, Bybit)"
                                            },
                                            "send_telegram": {
                                                "type": "boolean",
                                                "default": False,
                                                "description": "Send results to Telegram"
                                            },
                                            "min_accumulation_score": {
                                                "type": "integer",
                                                "description": "Min score 0-10"
                                            },
                                            "min_distribution_score": {
                                                "type": "integer",
                                                "description": "Min score 0-10"
                                            },
                                            "min_mss_score": {
                                                "type": "integer",
                                                "description": "Min score 0-100"
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "description": "Max results"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "ok": {"type": "boolean"},
                                                "operation": {"type": "string"},
                                                "data": {"type": "object"},
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
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache"
        }
    )
