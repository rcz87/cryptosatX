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
            }
        }
    }
    
    return schema
