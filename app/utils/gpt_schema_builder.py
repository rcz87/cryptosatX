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
