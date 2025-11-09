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
    # Production custom domain with SSL certificate ready
    # guardiansofthetoken.org is the primary custom domain
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    # Auto-detect if running on Replit (for development/testing)
    replit_domain = os.getenv("REPLIT_DOMAINS")
    if replit_domain and "localhost" in base_url:
        # Development environment - use Replit domain
        base_url = f"https://{replit_domain.split(',')[0]}"
    elif not base_url or base_url == "http://localhost:8000":
        # Fallback for local development
        base_url = "http://localhost:8000"
    
    schema = {
        "openapi": "3.1.0",
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
                            "description": "Cryptocurrency symbol. Supports ALL major cryptocurrencies: BTC, ETH, SOL, BNB, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, XRP, LTC, BCH, ETC, FIL, TRX, VET, THETA, FTM, SAND, MANA, APE, SHIB, LUNA, GALA, AXS, ENJ, CHZ, BAT, ZIL, COMP, MKR, SUSHI, AAVE, YFI, CRV, 1INCH, SNX, REN, KNC, BAL, LRC, and many more.",
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
                            "description": "Cryptocurrency symbol. Supports ALL major cryptocurrencies: BTC, ETH, SOL, BNB, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, XRP, LTC, BCH, ETC, FIL, TRX, VET, THETA, FTM, SAND, MANA, APE, SHIB, LUNA, GALA, AXS, ENJ, CHZ, BAT, ZIL, COMP, MKR, SUSHI, AAVE, YFI, CRV, 1INCH, SNX, REN, KNC, BAL, LRC, and many more.",
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
            },
            "/smart-money/scan": {
                "get": {
                    "summary": "Scan Smart Money Activity",
                    "description": "Scan 50+ cryptocurrencies for whale accumulation/distribution patterns. Detects coins being accumulated or distributed by smart money before retail traders enter/exit. Returns coins with accumulation score (buy-before-retail signals) and distribution score (short-before-dump signals). Supports ALL major cryptocurrencies: BTC, ETH, SOL, BNB, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, XRP, LTC, BCH, ETC, FIL, TRX, VET, THETA, FTM, SAND, MANA, APE, SHIB, LUNA, GALA, AXS, ENJ, CHZ, BAT, ZIL, COMP, MKR, SUSHI, AAVE, YFI, CRV, 1INCH, SNX, REN, KNC, BAL, LRC, and many more.",
                    "operationId": "scanSmartMoney",
                    "parameters": [
                        {
                            "name": "min_accumulation_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum accumulation score (0-10). Default 5. Higher = stronger buy signal.",
                            "schema": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 0,
                                "maximum": 10
                            }
                        },
                        {
                            "name": "min_distribution_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum distribution score (0-10). Default 5. Higher = stronger short signal.",
                            "schema": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 0,
                                "maximum": 10
                            }
                        },
                        {
                            "name": "coins",
                            "in": "query",
                            "required": False,
                            "description": "Comma-separated list of specific coins to scan (e.g., 'BTC,ETH,SOL,AVAX,DOGE,SHIB'). Supports ALL major cryptocurrencies. If not provided, scans all 50+ default coins including BTC, ETH, SOL, BNB, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, XRP, LTC, BCH, ETC, FIL, TRX, VET, THETA, FTM, SAND, MANA, APE, SHIB, LUNA, GALA, AXS, ENJ, CHZ, BAT, ZIL, COMP, MKR, SUSHI, AAVE, YFI, CRV, 1INCH, SNX, REN, KNC, BAL, LRC, and more.",
                            "schema": {
                                "type": "string",
                                "example": "BTC,ETH,SOL,AVAX,DOGE,SHIB"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Smart money scan results with accumulation and distribution signals",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "accumulation": {
                                                "type": "array",
                                                "description": "Coins showing whale accumulation patterns (buy signals)"
                                            },
                                            "distribution": {
                                                "type": "array",
                                                "description": "Coins showing whale distribution patterns (short signals)"
                                            },
                                            "summary": {
                                                "type": "object",
                                                "properties": {
                                                    "accumulationSignals": {"type": "integer"},
                                                    "distributionSignals": {"type": "integer"}
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
            "/smart-money/scan/accumulation": {
                "get": {
                    "summary": "Find Accumulation Opportunities",
                    "description": "Find coins being accumulated by whales (buy-before-retail signals). Returns only coins with strong accumulation patterns: high buy pressure, negative funding, low social activity, sideways price action.",
                    "operationId": "scanAccumulation",
                    "parameters": [
                        {
                            "name": "min_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum accumulation score (0-10). Default 6. Score ≥7 = strong accumulation.",
                            "schema": {
                                "type": "integer",
                                "default": 6,
                                "minimum": 0,
                                "maximum": 10
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Coins with whale accumulation patterns"
                        }
                    }
                }
            },
            "/smart-money/scan/distribution": {
                "get": {
                    "summary": "Find Distribution Opportunities",
                    "description": "Find coins being distributed by whales (short-before-dump signals). Returns only coins with strong distribution patterns: high sell pressure, overcrowded longs, social FOMO, recent pumps.",
                    "operationId": "scanDistribution",
                    "parameters": [
                        {
                            "name": "min_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum distribution score (0-10). Default 6. Score ≥7 = strong distribution.",
                            "schema": {
                                "type": "integer",
                                "default": 6,
                                "minimum": 0,
                                "maximum": 10
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Coins with whale distribution patterns"
                        }
                    }
                }
            }
        }
    }
    
    return schema
