"""
Dynamic GPT Actions Schema Builder
Auto-generates GPT Actions schema from FastAPI OpenAPI by filtering tags
"""
from typing import Dict, List, Any, Set
import copy


def build_gpt_actions_schema(
    app_openapi: Dict[str, Any],
    include_tags: Set[str] | None = None,
    exclude_paths: Set[str] | None = None,
    base_url: str = "https://guardiansofthetoken.org"
) -> Dict[str, Any]:
    """
    Build GPT Actions schema dynamically from FastAPI OpenAPI
    
    Args:
        app_openapi: Full OpenAPI schema from FastAPI app
        include_tags: Tags to include (e.g., {"Coinglass Data", "Core"})
        exclude_paths: Specific paths to exclude
        base_url: Production base URL
    
    Returns:
        GPT Actions-compatible OpenAPI schema
    """
    if include_tags is None:
        include_tags = {
            "Signals",
            "Market Data",
            "Coinglass Data",
            "Smart Money",
            "MSS Discovery",
            "LunarCrush",
            "Narratives",
            "New Listings",
            "Alerts"
        }
    
    if exclude_paths is None:
        exclude_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        }
    
    filtered_schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX - Complete Crypto Signal & Data API",
            "description": (
                "🚀 Complete access to CryptoSatX API including:\n\n"
                "**Core Features:**\n"
                "- AI-powered trading signals (8-factor analysis)\n"
                "- Smart Money Concept (SMC) analysis\n"
                "- Multi-Modal Signal Score (MSS) discovery\n\n"
                "**Coinglass Data (65 endpoints):**\n"
                "- Market data & liquidations (13 endpoints)\n"
                "- Funding rates & open interest (11 endpoints)\n"
                "- Long/short ratios & orderbook (9 endpoints)\n"
                "- Hyperliquid DEX & on-chain tracking (6 endpoints)\n"
                "- Technical indicators (12 endpoints)\n"
                "- Macro, news, options, ETF data (14 endpoints)\n\n"
                "**Social & Discovery:**\n"
                "- LunarCrush social sentiment\n"
                "- Narrative tracking\n"
                "- Binance new listings\n\n"
                "All endpoints return real trading data (no mocks/placeholders)."
            ),
            "version": "3.0.0"
        },
        "servers": [
            {"url": base_url, "description": "Production API"}
        ],
        "paths": {},
        "components": copy.deepcopy(app_openapi.get("components", {}))
    }
    
    original_paths = app_openapi.get("paths", {})
    
    for path, path_item in original_paths.items():
        if path in exclude_paths:
            continue
        
        should_include = False
        
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                operation_tags = operation.get("tags", [])
                
                if any(tag in include_tags for tag in operation_tags):
                    should_include = True
                    break
        
        if should_include:
            filtered_schema["paths"][path] = copy.deepcopy(path_item)
    
    return filtered_schema
def build_maximal_gpt_schema(base_url: str) -> dict:
    """
    Build MAXIMAL GPT Actions Schema
    
    Complete OpenAPI schema with ALL CryptoSatX features including:
    - Enhanced AI signals with OpenAI GPT-4 validation
    - Smart Money Concept analysis
    - Real-time market data from 5 providers
    - Advanced risk management
    - Portfolio optimization
    - Automated trading strategies
    - Social sentiment analysis
    - Whale activity tracking
    - Technical indicators
    - Market psychology insights
    
    Args:
        base_url: Production base URL for the API
        
    Returns:
        Complete OpenAPI 3.1.0 schema dict
    """
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "CryptoSatX MAXIMAL - Ultimate AI Crypto Signal Engine",
            "description": "🚀 MAXIMAL VERSION: Ultimate crypto trading intelligence with OpenAI GPT-4, Smart Money Concepts, whale tracking, and institutional-grade analysis. Features real-time signals, risk management, portfolio optimization, and automated trading strategies.",
            "version": "3.0.0-MAXIMAL",
            "contact": {
                "name": "CryptoSatX Support",
                "url": "https://guardiansofthetoken.org",
            },
        },
        "servers": [
            {"url": base_url, "description": "CryptoSatX Production API"}
        ],
        "paths": {
            # === CORE SIGNAL ENDPOINTS ===
            "/signals/{symbol}": {
                "get": {
                    "summary": "🎯 Get MAXIMAL AI Signal",
                    "description": "Generate ultimate trading signal using 10-factor AI analysis with OpenAI GPT-4 validation. Returns signal with confidence scoring, risk assessment, and AI reasoning.",
                    "operationId": "getMaximalSignal",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Cryptocurrency symbol. Supports 100+ cryptocurrencies including BTC, ETH, SOL, AVAX, DOGE, SHIB, and all major altcoins.",
                            "schema": {"type": "string", "example": "BTC"},
                        },
                        {
                            "name": "include_ai_validation",
                            "in": "query",
                            "description": "Include OpenAI GPT-4 validation and reasoning",
                            "schema": {"type": "boolean", "default": True},
                        },
                        {
                            "name": "risk_level",
                            "in": "query",
                            "description": "Risk tolerance level (conservative, moderate, aggressive)",
                            "schema": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "default": "moderate",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "🚀 MAXIMAL signal with AI validation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string"},
                                            "signal": {
                                                "type": "string",
                                                "enum": ["LONG", "SHORT", "NEUTRAL"],
                                            },
                                            "score": {"type": "number"},
                                            "confidence": {"type": "string"},
                                            "aiValidation": {
                                                "type": "object",
                                                "properties": {
                                                    "recommendation": {
                                                        "type": "string"
                                                    },
                                                    "confidence": {"type": "string"},
                                                    "reasoning": {"type": "string"},
                                                    "riskAssessment": {
                                                        "type": "string"
                                                    },
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            # === OPENAI ENHANCED ENDPOINTS ===
            "/openai/analyze/{symbol}": {
                "get": {
                    "summary": "🧠 OpenAI GPT-4 Analysis",
                    "description": "Get comprehensive market analysis using OpenAI GPT-4. Includes sentiment analysis, risk assessment, opportunity detection, and trading recommendations with confidence scoring.",
                    "operationId": "getOpenAIAnalysis",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "ETH"},
                        },
                        {
                            "name": "include_validation",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                        {
                            "name": "include_market_context",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                    ],
                    "responses": {
                        "200": {"description": "🧠 OpenAI GPT-4 comprehensive analysis"}
                    },
                }
            },
            "/openai/sentiment/market": {
                "get": {
                    "summary": "📊 Market Sentiment Analysis",
                    "description": "Analyze overall market sentiment using OpenAI GPT-4. Evaluates market psychology, identifies trends, and provides strategic positioning recommendations.",
                    "operationId": "getMarketSentiment",
                    "parameters": [
                        {
                            "name": "symbols",
                            "in": "query",
                            "description": "Comma-separated symbols to analyze (max 10)",
                            "schema": {
                                "type": "string",
                                "example": "BTC,ETH,SOL,AVAX,DOGE",
                            },
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "📊 Comprehensive market sentiment analysis"
                        }
                    },
                }
            },
            # === SMART MONEY CONCEPT ENDPOINTS ===
            "/smc/analyze/{symbol}": {
                "get": {
                    "summary": "🏦 Smart Money Concept Analysis",
                    "description": "Identify institutional trading patterns including Break of Structure (BOS), Change of Character (CHoCH), Fair Value Gaps (FVG), and Order Blocks. Detects whale footprints and smart money movements.",
                    "operationId": "analyzeSMC",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "SOL"},
                        },
                        {
                            "name": "timeframe",
                            "in": "query",
                            "description": "Analysis timeframe for institutional patterns",
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "1MIN",
                                    "5MIN",
                                    "15MIN",
                                    "1HRS",
                                    "4HRS",
                                    "1DAY",
                                ],
                                "default": "1HRS",
                            },
                        },
                        {
                            "name": "include_order_blocks",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "🏦 Smart Money Concept institutional analysis"
                        }
                    },
                }
            },
            # === WHALE & SMART MONEY TRACKING ===
            "/smart-money/scan": {
                "get": {
                    "summary": "🐋 Whale Activity Scanner",
                    "description": "Scan 100+ cryptocurrencies for whale accumulation/distribution patterns. Detects institutional buying before retail FOMO and distribution before dumps. Uses on-chain data, funding rates, and volume analysis.",
                    "operationId": "scanWhaleActivity",
                    "parameters": [
                        {
                            "name": "min_accumulation_score",
                            "in": "query",
                            "description": "Minimum accumulation score (0-10). 7+ = strong institutional buying",
                            "schema": {
                                "type": "integer",
                                "default": 7,
                                "minimum": 0,
                                "maximum": 10,
                            },
                        },
                        {
                            "name": "min_distribution_score",
                            "in": "query",
                            "description": "Minimum distribution score (0-10). 7+ = strong institutional selling",
                            "schema": {
                                "type": "integer",
                                "default": 7,
                                "minimum": 0,
                                "maximum": 10,
                            },
                        },
                        {
                            "name": "coins",
                            "in": "query",
                            "description": "Specific coins to scan (comma-separated). If not provided, scans all 100+ coins.",
                            "schema": {
                                "type": "string",
                                "example": "BTC,ETH,SOL,AVAX,DOGE,SHIB,MATIC,DOT",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "🐋 Whale activity scan results with institutional signals"
                        }
                    },
                }
            },
            "/smart-money/accumulation": {
                "get": {
                    "summary": "📈 Whale Accumulation Finder",
                    "description": "Find coins being accumulated by institutions and whales. Identifies buy-before-retail opportunities with high profit potential.",
                    "operationId": "findAccumulation",
                    "parameters": [
                        {
                            "name": "min_score",
                            "in": "query",
                            "description": "Minimum accumulation score (0-10). 8+ = maximum conviction",
                            "schema": {
                                "type": "integer",
                                "default": 8,
                                "minimum": 0,
                                "maximum": 10,
                            },
                        },
                        {
                            "name": "exclude_overbought_coins",
                            "in": "query",
                            "description": "Exclude overbought coins to reduce risk",
                            "schema": {"type": "boolean", "default": True},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "📈 High-conviction whale accumulation opportunities"
                        }
                    },
                }
            },
            # === PORTFOLIO OPTIMIZATION ===
            "/portfolio/optimize": {
                "get": {
                    "summary": "💼 Portfolio Optimization",
                    "description": "Get AI-optimized portfolio allocation based on current market conditions, risk tolerance, and investment goals. Uses modern portfolio theory with crypto-specific adjustments.",
                    "operationId": "optimizePortfolio",
                    "parameters": [
                        {
                            "name": "risk_tolerance",
                            "in": "query",
                            "description": "Risk tolerance level (1-10, where 1=very conservative, 10=very aggressive)",
                            "schema": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 10,
                            },
                        },
                        {
                            "name": "investment_amount",
                            "in": "query",
                            "description": "Total investment amount in USD",
                            "schema": {"type": "number", "example": 10000},
                        },
                        {
                            "name": "time_horizon",
                            "in": "query",
                            "description": "Investment time horizon",
                            "schema": {
                                "type": "string",
                                "enum": ["short_term", "medium_term", "long_term"],
                                "default": "medium_term",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "💼 AI-optimized portfolio allocation with risk metrics"
                        }
                    },
                }
            },
            # === RISK MANAGEMENT ===
            "/risk/assess/{symbol}": {
                "get": {
                    "summary": "⚠️ Risk Assessment",
                    "description": "Comprehensive risk assessment for cryptocurrency including volatility, liquidity, correlation, and market regime analysis. Provides risk score and mitigation strategies.",
                    "operationId": "assessRisk",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "BTC"},
                        },
                        {
                            "name": "position_size",
                            "in": "query",
                            "description": "Position size in USD for risk calculation",
                            "schema": {"type": "number", "example": 5000},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "⚠️ Comprehensive risk assessment with mitigation strategies"
                        }
                    },
                }
            },
            # === MARKET DATA AGGREGATION ===
            "/market/comprehensive/{symbol}": {
                "get": {
                    "summary": "📊 Comprehensive Market Data",
                    "description": "Get complete market data from all providers (CoinAPI, Coinglass, LunarCrush, OKX) including price, volume, funding, open interest, social metrics, and technical indicators.",
                    "operationId": "getComprehensiveData",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "ETH"},
                        },
                        {
                            "name": "include_technicals",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                        {
                            "name": "include_social",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "📊 Complete market data aggregation from all sources"
                        }
                    },
                }
            },
            # === TRADING STRATEGIES ===
            "/strategies/recommend": {
                "get": {
                    "summary": "🎯 Trading Strategy Recommendations",
                    "description": "Get AI-recommended trading strategies based on current market conditions, volatility, and regime. Includes entry/exit points, stop-loss, and take-profit levels.",
                    "operationId": "getStrategies",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "query",
                            "description": "Specific symbol for strategy (optional, if not provided analyzes market-wide)",
                            "schema": {"type": "string", "example": "BTC"},
                        },
                        {
                            "name": "strategy_type",
                            "in": "query",
                            "description": "Preferred strategy type",
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "momentum",
                                    "mean_reversion",
                                    "breakout",
                                    "trend_following",
                                    "all",
                                ],
                                "default": "all",
                            },
                        },
                        {
                            "name": "timeframe",
                            "in": "query",
                            "description": "Trading timeframe",
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "scalping",
                                    "day_trading",
                                    "swing",
                                    "position",
                                ],
                                "default": "swing",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "🎯 AI-recommended trading strategies with specific parameters"
                        }
                    },
                }
            },
            # === AUTOMATED TRADING ===
            "/trading/automate/{symbol}": {
                "post": {
                    "summary": "🤖 Automated Trading Setup",
                    "description": "Setup automated trading bot with AI-driven signals, risk management, and strategy execution. Requires API key authentication.",
                    "operationId": "setupAutomatedTrading",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "BTC"},
                        }
                    ],
                    "security": [{"apiKey": []}],
                    "requestBody": {
                        "description": "Automated trading configuration",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "strategy": {
                                            "type": "string",
                                            "example": "momentum",
                                        },
                                        "position_size": {
                                            "type": "number",
                                            "example": 1000,
                                        },
                                        "risk_percentage": {
                                            "type": "number",
                                            "example": 2.0,
                                        },
                                        "take_profit": {
                                            "type": "number",
                                            "example": 5.0,
                                        },
                                        "stop_loss": {"type": "number", "example": 2.0},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "🤖 Automated trading bot configured successfully"
                        }
                    },
                }
            },
            # === TELEGRAM INTEGRATION ===
            "/telegram/send-alert/{symbol}": {
                "post": {
                    "summary": "📱 Send Professional Alert",
                    "description": "Generate comprehensive trading signal and send professional alert to Telegram with charts, analysis, and actionable insights.",
                    "operationId": "sendTelegramAlert",
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "example": "ETH"},
                        }
                    ],
                    "security": [{"apiKey": []}],
                    "responses": {
                        "200": {
                            "description": "📱 Professional alert sent to Telegram successfully"
                        }
                    },
                }
            },
            # === SYSTEM HEALTH & MONITORING ===
            "/health/maximal": {
                "get": {
                    "summary": "🏥 MAXIMAL System Health",
                    "description": "Complete system health check including all data providers, AI services, and performance metrics.",
                    "operationId": "maximalHealthCheck",
                    "responses": {
                        "200": {
                            "description": "🏥 Complete system health status with performance metrics"
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {},
            "securitySchemes": {
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for protected endpoints. Get your key at /admin/api-keys",
                }
            },
        },
        "tags": [
            {"name": "Core Signals", "description": "🎯 AI-powered trading signals"},
            {"name": "OpenAI Integration", "description": "🧠 GPT-4 enhanced analysis"},
            {
                "name": "Smart Money",
                "description": "🏦 Institutional pattern detection",
            },
            {"name": "Whale Tracking", "description": "🐋 Whale activity monitoring"},
            {"name": "Portfolio", "description": "💼 Portfolio optimization"},
            {
                "name": "Risk Management",
                "description": "⚠️ Risk assessment & mitigation",
            },
            {"name": "Market Data", "description": "📊 Comprehensive market data"},
            {
                "name": "Strategies",
                "description": "🎯 Trading strategy recommendations",
            },
            {"name": "Automation", "description": "🤖 Automated trading"},
            {"name": "Alerts", "description": "📱 Telegram notifications"},
            {"name": "System", "description": "🏥 Health & monitoring"},
        ],
    }
