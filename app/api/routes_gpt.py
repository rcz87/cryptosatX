"""
GPT Actions integration routes
Provides OpenAPI schema for connecting this API to OpenAI GPT Actions
DYNAMIC SCHEMA GENERATION - Auto-includes all tagged routes
"""
import os
import httpx
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import datetime
from app.utils.gpt_schema_builder import build_gpt_actions_schema
from app.utils.telegram_formatters import format_mss_alert, format_smart_money_alert

router = APIRouter()

# Import services (lazy loaded to avoid circular imports)
def get_services():
    """Lazy load services to avoid circular imports"""
    from app.core.signal_engine import signal_engine
    from app.services.telegram_notifier import telegram_notifier
    from app.services.mss_service import MSSService
    from app.services.smart_money_service import smart_money_service
    
    # Create MSS service instance if needed
    mss_service = MSSService()
    
    return signal_engine, telegram_notifier, mss_service, smart_money_service


@router.get("/gpt-openapi.json")
async def get_gpt_openapi_schema(request: Request):
    """
    ✅ OpenAPI schema with servers field for GPT Actions compatibility
    
    This endpoint returns the complete OpenAPI schema with the servers field
    required by GPT Actions. Use this endpoint when GPT Actions shows error:
    'Could not find a valid URL in servers'
    
    **RECOMMENDED FOR GPT ACTIONS:** Use this endpoint instead of /openapi.json
    """
    from fastapi.openapi.utils import get_openapi
    
    # Get FastAPI app instance
    app = request.app
    
    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add servers field for GPT Actions compatibility
    openapi_schema["servers"] = [
        {
            "url": "https://guardiansofthetoken.org",
            "description": "Production server"
        }
    ]
    
    return openapi_schema


@router.get("/gpt/complete-schema-v3")
async def get_complete_gpt_schema_v3(request: Request):
    """
    🚀 **COMPLETE GPT Actions Schema V3** - Includes ALL 65+ Coinglass endpoints
    
    **USE THIS ENDPOINT FOR GPT ACTIONS INTEGRATION**
    
    Dynamically generates OpenAPI schema from FastAPI routes by filtering tags.
    Automatically includes:
    - All 65 Coinglass endpoints (liquidations, funding, OI, indicators, etc.)
    - Core signal & market data endpoints
    - Smart Money, MSS, LunarCrush, Narratives, New Listings
    
    This endpoint provides the COMPLETE schema for GPT Actions integration.
    Schema is auto-generated from app routes, so it's always up-to-date.
    """
    # Get base URL
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    # Auto-detect if running on Replit (for development/testing)
    replit_domain = os.getenv("REPLIT_DOMAINS")
    if replit_domain and "localhost" in base_url:
        base_url = f"https://{replit_domain.split(',')[0]}"
    elif not base_url or base_url == "http://localhost:8000":
        base_url = "http://localhost:8000"
    
    # Get full OpenAPI schema directly from app
    # Force regeneration to get latest routes
    app = request.app
    
    # Clear OpenAPI cache to force fresh generation
    if hasattr(app, 'openapi_schema'):
        app.openapi_schema = None
    if hasattr(app, '_openapi'):
        delattr(app, '_openapi')
    
    # Get fresh OpenAPI schema
    app_openapi = app.openapi()
    
    print(f"[DEBUG GPT SCHEMA] Generated fresh OpenAPI schema")
    print(f"[DEBUG GPT SCHEMA] OpenAPI has {len(app_openapi.get('paths', {}))} total paths")
    
    # Build filtered GPT Actions schema with all relevant tags
    schema = build_gpt_actions_schema(
        app_openapi=app_openapi,
        include_tags={
            "Signals",
            "Market Data",
            "Coinglass Data",
            "Smart Money",
            "MSS Discovery",
            "LunarCrush",
            "Narratives",
            "New Listings",
            "Alerts",
            "Smart Money Scanner",
            "MSS Alpha System",
            "LunarCrush Social Data",
            "Binance New Listings",
            "Narratives & Market Intelligence",
            "CoinAPI Market Data",
            "Smart Money Concept (SMC)",
            "Signal History"
        },
        base_url=base_url
    )
    
    print(f"[DEBUG GPT SCHEMA] Built filtered schema with {len(schema.get('paths', {}))} paths")
    coinglass_count = len([p for p in schema.get('paths', {}) if 'coinglass' in p])
    print(f"[DEBUG GPT SCHEMA] Coinglass endpoints in filtered schema: {coinglass_count}")
    
    return schema


# Legacy manual schema for fallback/reference
@router.get("/gpt/action-schema/manual")
async def get_manual_gpt_schema():
    """
    Manual/static GPT Actions schema (legacy fallback)
    Use /gpt/action-schema instead for auto-generated schema
    """
    base_url = os.getenv("BASE_URL", "https://guardiansofthetoken.org")
    
    replit_domain = os.getenv("REPLIT_DOMAINS")
    if replit_domain and "localhost" in base_url:
        base_url = f"https://{replit_domain.split(',')[0]}"
    elif not base_url or base_url == "http://localhost:8000":
        base_url = "http://localhost:8000"
    
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX - Crypto Futures Signal & Discovery API",
            "description": "Get real-time crypto trading signals, discover high-potential cryptocurrencies before retail adoption using MSS (Multi-Modal Signal Score) system, and track smart money movements",
            "version": "2.0.0"
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
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH, SOL, DOGE, SHIB, PEPE). Supports all major cryptocurrencies on Binance Futures.",
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
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH, SOL, DOGE, SHIB, PEPE). Supports all major cryptocurrencies on Binance Futures.",
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
                    "description": "Scan cryptocurrencies for whale accumulation/distribution patterns. Returns buy-before-retail signals (accumulation) and short-before-dump signals (distribution) based on smart money activity.",
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
                            "description": "Comma-separated list of coins to scan (e.g., 'BTC,ETH,SOL,AVAX,DOGE,SHIB'). If not provided, scans all 50+ default major cryptocurrencies.",
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
            },
            "/mss/analyze/{symbol}": {
                "get": {
                    "summary": "MSS Analysis - Discover High-Potential Cryptocurrencies",
                    "description": "3-phase MSS analysis: tokenomics, social momentum, whale positioning. Returns score 0-100. Diamond ≥80, Gold 65-79, Silver 50-64. Find hidden gems before retail adoption.",
                    "operationId": "analyzeMSS",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol to analyze (e.g., BTC, PEPE, SHIB, DOGE, etc.). Works with ANY cryptocurrency listed on Binance Futures.",
                            "schema": {
                                "type": "string",
                                "example": "PEPE"
                            }
                        },
                        {
                            "name": "include_raw",
                            "in": "query",
                            "required": False,
                            "description": "Include complete phase breakdown details. Default false for cleaner output.",
                            "schema": {
                                "type": "boolean",
                                "default": False
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "MSS analysis result with score, signal, confidence, and phase breakdown",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string"},
                                            "mss_score": {
                                                "type": "number",
                                                "description": "Multi-Modal Signal Score (0-100)"
                                            },
                                            "signal": {
                                                "type": "string",
                                                "enum": ["STRONG_LONG", "MODERATE_LONG", "LONG", "WEAK_LONG", "NEUTRAL"],
                                                "description": "Signal strength based on MSS score"
                                            },
                                            "confidence": {
                                                "type": "string",
                                                "enum": ["very_high", "high", "medium", "low", "insufficient"],
                                                "description": "Confidence level based on phase validation"
                                            },
                                            "warnings": {
                                                "type": "array",
                                                "description": "Risk warnings (high FDV, negative funding, etc.)"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/lunarcrush/coin/{symbol}": {
                "get": {
                    "summary": "Get Comprehensive Social & Market Metrics (60+ Metrics)",
                    "description": "Get comprehensive LunarCrush social and market metrics for any cryptocurrency. Returns 60+ data points including Galaxy Score™ (0-100 quality metric), AltRank™ (momentum ranking), social volume, engagement, sentiment, tweet/Reddit volumes, correlation rank, and price data. Perfect for deep social intelligence analysis.",
                    "operationId": "getLunarCrushCoin",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH, PEPE, SHIB). Supports 7,635+ coins tracked by LunarCrush.",
                            "schema": {
                                "type": "string",
                                "example": "BTC"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Comprehensive coin data with 60+ social and market metrics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "galaxyScore": {"type": "number", "description": "Galaxy Score™ 0-100 (proprietary quality metric)"},
                                            "altRank": {"type": "integer", "description": "AltRank™ momentum ranking (lower = better)"},
                                            "socialVolume": {"type": "integer", "description": "24h social mentions across platforms"},
                                            "sentiment": {"type": "number", "description": "Average sentiment score 0-100"},
                                            "tweetVolume": {"type": "integer"},
                                            "redditVolume": {"type": "integer"},
                                            "price": {"type": "number"},
                                            "marketCap": {"type": "number"},
                                            "percentChange24h": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/lunarcrush/coin/{symbol}/momentum": {
                "get": {
                    "summary": "Advanced Social Momentum Analysis",
                    "description": "Comprehensive social momentum score combining current strength, 24h changes, and 7-day trends. Returns momentum score 0-100 with level classification (strong/moderate/weak). Includes Galaxy Score, social volume, sentiment trajectory, and spike detection. Use for entry timing confirmation.",
                    "operationId": "getLunarCrushMomentum",
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
                            "description": "Social momentum analysis with score and trend data"
                        }
                    }
                }
            },
            "/lunarcrush/coin/{symbol}/change": {
                "get": {
                    "summary": "Detect Social Spikes & Viral Moments",
                    "description": "Get social metrics change/delta over time. Detects sudden social spikes (>300% = extreme, >100% = high, >50% = moderate). Returns social volume % change, engagement change, sentiment shift, and Galaxy Score delta. Perfect for viral moment detection and spike alerts.",
                    "operationId": "getLunarCrushChange",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol",
                            "schema": {
                                "type": "string",
                                "example": "PEPE"
                            }
                        },
                        {
                            "name": "timeframe",
                            "in": "query",
                            "required": False,
                            "description": "Time period for change analysis. Default 24h.",
                            "schema": {
                                "type": "string",
                                "enum": ["1h", "24h", "7d"],
                                "default": "24h"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Social metrics change with spike level classification"
                        }
                    }
                }
            },
            "/lunarcrush/coin/{symbol}/time-series": {
                "get": {
                    "summary": "Historical Social & Market Trends",
                    "description": "Get historical time-series data for social and market metrics. Returns arrays of price OHLC, social volume trends, sentiment changes, and Galaxy Score historical data over time. Use for trend analysis, spike detection, and correlation studies.",
                    "operationId": "getLunarCrushTimeSeries",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol",
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "interval",
                            "in": "query",
                            "required": False,
                            "description": "Time interval for data points. Default 1d.",
                            "schema": {
                                "type": "string",
                                "enum": ["1h", "1d", "1w"],
                                "default": "1d"
                            }
                        },
                        {
                            "name": "days_back",
                            "in": "query",
                            "required": False,
                            "description": "Number of days of historical data (1-365). Default 30.",
                            "schema": {
                                "type": "integer",
                                "default": 30,
                                "minimum": 1,
                                "maximum": 365
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Time-series arrays for trend analysis"
                        }
                    }
                }
            },
            "/lunarcrush/coins/discovery": {
                "get": {
                    "summary": "Discover Coins with Advanced Filtering (7,635+ Coins)",
                    "description": "Discover and filter from 7,635+ tracked cryptocurrencies using Galaxy Score, AltRank, sentiment, market cap, categories, and more. Returns comprehensive data for each coin. Use for building watchlists, screening opportunities, and market research.",
                    "operationId": "discoverLunarCrushCoins",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Number of coins to return (max 100). Default 20.",
                            "schema": {
                                "type": "integer",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "categories",
                            "in": "query",
                            "required": False,
                            "description": "Filter by categories (e.g., 'layer-1', 'defi', 'meme', 'ai'). Comma-separated.",
                            "schema": {
                                "type": "string",
                                "example": "layer-1,defi"
                            }
                        },
                        {
                            "name": "min_galaxy_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum Galaxy Score (0-100). Higher = better quality.",
                            "schema": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "max_alt_rank",
                            "in": "query",
                            "required": False,
                            "description": "Maximum AltRank (lower = better momentum). E.g., 100 for top 100.",
                            "schema": {
                                "type": "integer",
                                "minimum": 1
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of discovered coins with filtering applied"
                        }
                    }
                }
            },
            "/lunarcrush/topic/{topic}": {
                "get": {
                    "summary": "Topic Analysis & Social Intelligence",
                    "description": "Get social metrics and analysis for specific topics/keywords (e.g., 'bitcoin', 'ethereum', 'defi'). Returns topic rank, related topics, cross-platform social data, and trend information. Use for narrative analysis and topic research.",
                    "operationId": "getLunarCrushTopic",
                    "parameters": [
                        {
                            "name": "topic",
                            "in": "path",
                            "required": True,
                            "description": "Topic or keyword to analyze (e.g., 'bitcoin', 'ethereum', 'ai', 'defi')",
                            "schema": {
                                "type": "string",
                                "example": "ethereum"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Topic analysis with social intelligence"
                        }
                    }
                }
            },
            "/narratives/discover/realtime": {
                "get": {
                    "summary": "Real-Time Gem Discovery (NO CACHE - Instant Data)",
                    "description": "Real-time coin discovery with ZERO cache delay (v2 endpoint). Instantly discover emerging cryptocurrencies with fresh data updated every minute. Filter by Galaxy Score, social volume, categories. Perfect for catching viral moments and early entries before competition. NO 1-HOUR DELAY like competitors!",
                    "operationId": "discoverRealtimeGems",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Number of coins (max 100). Default 20.",
                            "schema": {
                                "type": "integer",
                                "default": 20,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "min_galaxy_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum Galaxy Score for filtering (0-100). Recommended: 65+ for quality.",
                            "schema": {
                                "type": "number",
                                "default": 60,
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "sort",
                            "in": "query",
                            "required": False,
                            "description": "Sort by metric. Default social_volume for trending.",
                            "schema": {
                                "type": "string",
                                "enum": ["social_volume", "market_cap", "galaxy_score", "alt_rank"],
                                "default": "social_volume"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Real-time coin discovery results with fresh data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "dataFreshness": {
                                                "type": "string",
                                                "example": "real-time (v2 - no cache)"
                                            },
                                            "totalCoins": {"type": "integer"},
                                            "coins": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/mss/scan": {
                "get": {
                    "summary": "MSS Auto-Scan - Find New Crypto Gems",
                    "description": "Auto-discover and rank new cryptocurrencies by MSS score. Scans for coins under specified FDV and age thresholds, validates through 3-phase MSS system, and returns top-ranked opportunities. Perfect for finding early-stage gems with institutional backing before retail FOMO.",
                    "operationId": "scanMSS",
                    "parameters": [
                        {
                            "name": "max_fdv_usd",
                            "in": "query",
                            "required": False,
                            "description": "Maximum Fully Diluted Valuation in USD. Default 50M. Lower values = earlier stage coins.",
                            "schema": {
                                "type": "number",
                                "default": 50000000,
                                "example": 20000000
                            }
                        },
                        {
                            "name": "max_age_hours",
                            "in": "query",
                            "required": False,
                            "description": "Maximum coin age in hours since listing. Default 72h (3 days).",
                            "schema": {
                                "type": "number",
                                "default": 72,
                                "example": 48
                            }
                        },
                        {
                            "name": "min_mss_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum MSS score threshold. Default 65 (Gold tier+). Use 80 for Diamond tier only.",
                            "schema": {
                                "type": "number",
                                "default": 65,
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Maximum results to return. Default 10.",
                            "schema": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Ranked list of high-potential cryptocurrencies by MSS score",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "results": {
                                                "type": "array",
                                                "description": "Coins ranked by MSS score (highest first)"
                                            },
                                            "summary": {
                                                "type": "object",
                                                "properties": {
                                                    "discovered": {"type": "integer"},
                                                    "analyzed": {"type": "integer"},
                                                    "qualified": {"type": "integer"}
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
            "/mss/top-scores": {
                "get": {
                    "summary": "MSS Top Scores - Best Opportunities",
                    "description": "Get highest-scoring MSS discoveries from database history. Shows Diamond (≥80), Gold (65-79), and Silver (50-64) tier opportunities with complete phase breakdown. Perfect for reviewing previously discovered gems and tracking performance over time.",
                    "operationId": "getTopMSSScores",
                    "parameters": [
                        {
                            "name": "min_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum MSS score. Default 75. Use 80 for Diamond tier only.",
                            "schema": {
                                "type": "number",
                                "default": 75,
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Maximum results. Default 50.",
                            "schema": {
                                "type": "integer",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 100
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Highest-scoring MSS signals with tier distribution"
                        }
                    }
                }
            },
            "/mss/history": {
                "get": {
                    "summary": "MSS Signal History",
                    "description": "Get recent MSS signal history across all cryptocurrencies. Shows chronological discovery timeline with scores, signals, and phase breakdowns. Useful for tracking discovery patterns and reviewing past opportunities.",
                    "operationId": "getMSSHistory",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Maximum signals to return. Default 100.",
                            "schema": {
                                "type": "integer",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 500
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Recent MSS signals sorted by timestamp (most recent first)"
                        }
                    }
                }
            },
            "/mss/history/{symbol}": {
                "get": {
                    "summary": "MSS Symbol History",
                    "description": "Get MSS signal history for a specific cryptocurrency. Track how a coin's MSS score evolved over time, see phase score changes, and identify accumulation patterns.",
                    "operationId": "getMSSSymbolHistory",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol (e.g., PEPE, SHIB, DOGE)",
                            "schema": {
                                "type": "string",
                                "example": "PEPE"
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "Maximum signals. Default 50.",
                            "schema": {
                                "type": "integer",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 200
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Symbol-specific MSS signal history"
                        }
                    }
                }
            },
            "/mss/analytics": {
                "get": {
                    "summary": "MSS Analytics Summary",
                    "description": "Get comprehensive MSS analytics: signal distribution, tier performance, score statistics, and trend analysis. Optionally filter by specific cryptocurrency and time period.",
                    "operationId": "getMSSAnalytics",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "query",
                            "required": False,
                            "description": "Optional symbol filter (e.g., PEPE). If not provided, shows analytics for all cryptocurrencies.",
                            "schema": {
                                "type": "string",
                                "example": "PEPE"
                            }
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "description": "Number of days to analyze. Default 7.",
                            "schema": {
                                "type": "integer",
                                "default": 7,
                                "minimum": 1,
                                "maximum": 90
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Analytics summary with tier distribution and score stats"
                        }
                    }
                }
            },
            "/new-listings/binance": {
                "get": {
                    "summary": "Binance New Listings - Early Detection",
                    "description": "Detect newly listed Binance perpetual futures (1-168h lookback). Get listing age, volume, price change. Perfect for early entry before retail FOMO.",
                    "operationId": "getBinanceNewListings",
                    "parameters": [
                        {
                            "name": "hours",
                            "in": "query",
                            "required": False,
                            "description": "Lookback period in hours (1-168). Default 72h (3 days).",
                            "schema": {
                                "type": "integer",
                                "default": 72,
                                "minimum": 1,
                                "maximum": 168
                            }
                        },
                        {
                            "name": "include_stats",
                            "in": "query",
                            "required": False,
                            "description": "Include 24h trading stats (volume, price change). Default true.",
                            "schema": {
                                "type": "boolean",
                                "default": True
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of new Binance perpetual listings with stats"
                        }
                    }
                }
            },
            "/new-listings/analyze": {
                "get": {
                    "summary": "Analyze New Listings with MSS",
                    "description": "Auto-analyze new Binance listings with full 3-phase MSS scoring. Sends Telegram alerts for high-scoring discoveries (MSS ≥65). Perfect for automated monitoring.",
                    "operationId": "analyzeNewListings",
                    "parameters": [
                        {
                            "name": "hours",
                            "in": "query",
                            "required": False,
                            "description": "Lookback period in hours. Default 72h.",
                            "schema": {
                                "type": "integer",
                                "default": 72,
                                "minimum": 1,
                                "maximum": 168
                            }
                        },
                        {
                            "name": "min_volume_usd",
                            "in": "query",
                            "required": False,
                            "description": "Minimum 24h volume in USD. Default $100K.",
                            "schema": {
                                "type": "number",
                                "default": 100000,
                                "minimum": 0
                            }
                        },
                        {
                            "name": "auto_alert",
                            "in": "query",
                            "required": False,
                            "description": "Send Telegram alerts for high MSS scores. Default true.",
                            "schema": {
                                "type": "boolean",
                                "default": True
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "New listings with MSS analysis and alert status"
                        }
                    }
                }
            },
            "/new-listings/watch": {
                "get": {
                    "summary": "Watch List - High-Potential New Listings",
                    "description": "Filtered watch list showing only recent high-MSS new listings. Shows coins under 48h old with MSS ≥60. Perfect for quick opportunity screening.",
                    "operationId": "watchNewListings",
                    "parameters": [
                        {
                            "name": "min_mss_score",
                            "in": "query",
                            "required": False,
                            "description": "Minimum MSS score filter. Default 60.",
                            "schema": {
                                "type": "number",
                                "default": 60,
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "max_age_hours",
                            "in": "query",
                            "required": False,
                            "description": "Maximum listing age in hours. Default 24h.",
                            "schema": {
                                "type": "integer",
                                "default": 24,
                                "minimum": 1,
                                "maximum": 72
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "High-potential new listings watch list"
                        }
                    }
                }
            },
            "/alerts/send/{symbol}": {
                "post": {
                    "summary": "Send Telegram Alert",
                    "description": "Generate trading signal and send formatted alert to Telegram. Perfect for manual alert triggers. Alert includes signal (LONG/SHORT/NEUTRAL), score, price, top factors, and recommendations. Only LONG/SHORT signals are sent (NEUTRAL filtered). Alert auto-saves to database.",
                    "operationId": "sendAlert",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH, SOL). Supports all major cryptocurrencies.",
                            "schema": {
                                "type": "string",
                                "example": "BTC"
                            }
                        },
                        {
                            "name": "alert_type",
                            "in": "query",
                            "required": False,
                            "description": "Type of alert to send. Options: 'signal' (trading signal), 'mss' (MSS analysis), 'smart_money' (whale activity). Default: signal.",
                            "schema": {
                                "type": "string",
                                "enum": ["signal", "mss", "smart_money"],
                                "default": "signal"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Alert sent successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "alert_type": {"type": "string"},
                                            "signal": {"type": "object"},
                                            "telegram_status": {"type": "string"}
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


@router.post("/alerts/send/{symbol}")
async def send_telegram_alert(
    symbol: str,
    alert_type: str = "signal"
):
    """
    📱 Send Telegram Alert
    
    Generate and send formatted alert to Telegram.
    Supports 3 alert types:
    - signal: Trading signal (8-factor scoring)
    - mss: MSS analysis (3-phase Diamond tier discovery)
    - smart_money: Whale accumulation/distribution
    
    Only LONG/SHORT signals are sent (NEUTRAL filtered).
    Alerts auto-save to database.
    """
    signal_engine, telegram_notifier, mss_service, smart_money_service = get_services()
    
    try:
        symbol = symbol.upper()
        
        # Check if Telegram is configured
        if not telegram_notifier.enabled:
            return {
                "success": False,
                "message": "Telegram notifications not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.",
                "symbol": symbol,
                "alert_type": alert_type
            }
        
        # Generate alert based on type
        if alert_type == "signal":
            # Trading signal alert
            signal = await signal_engine.build_signal(symbol, debug=False)
            
            # Filter NEUTRAL signals
            if signal.get("signal") == "NEUTRAL":
                return {
                    "success": False,
                    "message": f"{symbol} has NEUTRAL signal (score: {signal.get('score')}). Only LONG/SHORT signals are sent to Telegram.",
                    "symbol": symbol,
                    "alert_type": alert_type,
                    "signal": signal.get("signal"),
                    "score": signal.get("score")
                }
            
            # Send to Telegram
            telegram_result = await telegram_notifier.send_signal_alert(signal)
            
            return {
                "success": telegram_result.get("success", False),
                "message": telegram_result.get("message", "Alert sent"),
                "symbol": symbol,
                "alert_type": alert_type,
                "signal": signal.get("signal"),
                "score": signal.get("score"),
                "confidence": signal.get("confidence"),
                "telegram_status": "sent" if telegram_result.get("success") else "failed"
            }
        
        elif alert_type == "mss":
            # MSS analysis alert
            mss_result = await mss_service.calculate_mss_score(symbol)
            
            mss_score = mss_result.get("mss_score", 0)
            tier = mss_result.get("tier", "bronze")
            signal_strength = mss_result.get("signal", "NEUTRAL")
            
            # Format MSS alert message
            message = format_mss_alert(symbol, mss_result)
            
            # Send to Telegram
            telegram_result = await telegram_notifier._send_telegram_message(message)
            
            return {
                "success": True,
                "message": "MSS alert sent to Telegram",
                "symbol": symbol,
                "alert_type": alert_type,
                "mss_score": mss_score,
                "tier": tier,
                "signal": signal_strength,
                "telegram_status": "sent"
            }
        
        elif alert_type == "smart_money":
            # Smart money whale activity alert
            scan_result = await smart_money_service.scan_markets(
                coins=[symbol],
                min_accumulation_score=5,
                min_distribution_score=5
            )
            
            accumulation = scan_result.get("accumulation", [])
            distribution = scan_result.get("distribution", [])
            
            # Format smart money alert
            message = format_smart_money_alert(symbol, accumulation, distribution)
            
            # Send to Telegram
            telegram_result = await telegram_notifier._send_telegram_message(message)
            
            return {
                "success": True,
                "message": "Smart money alert sent to Telegram",
                "symbol": symbol,
                "alert_type": alert_type,
                "accumulation_signals": len(accumulation),
                "distribution_signals": len(distribution),
                "telegram_status": "sent"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid alert_type: {alert_type}. Use 'signal', 'mss', or 'smart_money'.")
    
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send alert: {str(e)}",
            "symbol": symbol,
            "alert_type": alert_type
        }
