"""
GPT Actions integration routes
Provides OpenAPI schema for connecting this API to OpenAI GPT Actions
"""
import os
from fastapi import APIRouter

router = APIRouter()


@router.get("/gpt/action-schema")
async def get_gpt_action_schema():
    """
    Returns OpenAPI-compatible schema for GPT Actions integration
    
    This endpoint provides the schema that can be used to register
    this API as a GPT Action in OpenAI's GPT builder.
    """
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Crypto Futures Signal API",
            "description": "Get real-time crypto trading signals based on price, funding rate, open interest, and social sentiment",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": base_url,
                "description": "Production server"
            }
        ],
        "paths": {
            "/signals/{symbol}": {
                "get": {
                    "summary": "Get Trading Signal",
                    "description": "Get comprehensive trading signal for a cryptocurrency including price, funding rate, open interest, social sentiment, and recommendation (LONG/SHORT/NEUTRAL)",
                    "operationId": "getSignal",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH, SOL, AVAX)",
                            "schema": {
                                "type": "string",
                                "example": "BTC"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response with trading signal",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string"},
                                            "timestamp": {"type": "string"},
                                            "price": {"type": "number"},
                                            "fundingRate": {"type": "number"},
                                            "openInterest": {"type": "number"},
                                            "socialScore": {"type": "number"},
                                            "signal": {
                                                "type": "string",
                                                "enum": ["LONG", "SHORT", "NEUTRAL"]
                                            },
                                            "reason": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/market/{symbol}": {
                "get": {
                    "summary": "Get Market Data",
                    "description": "Get raw market data from all providers (CoinAPI, Coinglass, LunarCrush, OKX)",
                    "operationId": "getMarketData",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol",
                            "schema": {
                                "type": "string",
                                "example": "BTC"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Raw market data from all sources"
                        }
                    }
                }
            },
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Check if the API is running",
                    "operationId": "healthCheck",
                    "responses": {
                        "200": {
                            "description": "API is healthy"
                        }
                    }
                }
            }
        }
    }
    
    return schema
