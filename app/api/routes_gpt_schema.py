"""Top 30 Schema for GPT Actions - Exactly at 30 operation limit"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Exactly 30 top operations
TOP_30 = [
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
    "coinglass.orderbook.whale_walls",
    "smart_money.scan",
    "smart_money.analyze",
    "mss.discover",
    "mss.analyze",
    "lunarcrush.coin",
    "lunarcrush.coin_momentum",
    "lunarcrush.coins_discovery",
    "coinapi.quote",
    "coinapi.ohlcv.latest",
    "coinapi.orderbook",
    "coinapi.trades",
    "coinglass.liquidations.heatmap",
    "coinglass.markets",
    "coinglass.supported_coins",
    "coinglass.onchain.reserves",
    "coinglass.indicators.bollinger",
    "smart_money.scan_accumulation"
]

@router.get("/openapi-gpt.json", include_in_schema=False)
async def gpt_schema():
    """Top 30 Operations Schema for GPT Actions"""
    return JSONResponse({
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX - RPC API for GPT Actions",
            "version": "1.0.0",
            "description": "Top 30 operations via /invoke RPC endpoint"
        },
        "servers": [{"url": "https://guardiansofthetoken.org"}],
        "paths": {
            "/invoke": {
                "post": {
                    "operationId": "invoke",
                    "summary": "Invoke any of 30 top operations",
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
                                            "enum": TOP_30,
                                            "description": "Operation (30 top)"
                                        },
                                        "symbol": {
                                            "type": "string",
                                            "example": "BTC"
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "example": 10
                                        },
                                        "send_telegram": {
                                            "type": "boolean",
                                            "default": False
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
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        }
    })
