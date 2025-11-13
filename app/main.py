"""
Main FastAPI application
Crypto Futures Signal API with multi-provider integration
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api import (
    routes_health,
    routes_signals,
    routes_gpt,
    routes_coinglass,
    routes_lunarcrush,
    routes_coinapi,
    routes_smart_money,
    routes_mss,
    routes_new_listings,
    routes_narratives,
)

# ADDED FOR CRYPTOSATX ENHANCEMENT - Import new routes
from app.api import (
    routes_smc,
    routes_history,
    routes_enhanced_gpt,
    routes_monitoring,
    routes_openai,
    routes_openai_v2,  # ADDED FOR PHASE 1 DEVELOPMENT
    routes_optimized_gpt,
    routes_analytics,  # ADDED FOR DATABASE ANALYTICS
    routes_rpc,  # ADDED FOR UNIFIED RPC ENDPOINT
    routes_gpt_actions,  # ADDED FOR GPT ACTIONS FLAT PARAMS
    routes_dashboard,  # ADDED FOR INTERACTIVE DASHBOARD
)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Import database here to avoid circular imports
    from app.storage.database import db

    print("=" * 50)
    print("CryptoSatX - Enhanced Crypto Signal API Starting...")
    print("=" * 50)
    print(f"Environment variables loaded:")
    print(f"  - COINAPI_KEY: {'✓' if os.getenv('COINAPI_KEY') else '✗'}")
    print(f"  - COINGLASS_API_KEY: {'✓' if os.getenv('COINGLASS_API_KEY') else '✗'}")
    print(f"  - LUNARCRUSH_API_KEY: {'✓' if os.getenv('LUNARCRUSH_API_KEY') else '✗'}")
    print(
        f"  - TELEGRAM_BOT_TOKEN: {'✓' if os.getenv('TELEGRAM_BOT_TOKEN') else '✗'}"
    )  # ADDED
    print(
        f"  - API_KEYS: {'✓' if os.getenv('API_KEYS') else '✗ (public mode)'}"
    )  # ADDED
    print(f"  - OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")  # ADDED
    print(
        f"  - DATABASE_URL: {'✓' if os.getenv('DATABASE_URL') else '✗'}"
    )  # ADDED FOR DATABASE
    print(f"  - BASE_URL: {os.getenv('BASE_URL', 'Not set')}")
    print("=" * 50)
    print(
        "🚀 Enhanced Features: SMC Analysis | Signal History | Telegram Alerts | OpenAI GPT-4 | PostgreSQL Database"
    )  # UPDATED
    print("=" * 50)

    # Initialize database connection
    await db.connect()

    yield

    # Shutdown: close database connection and cleanup resources
    print("Shutting down CryptoSatX API...")
    
    # Close ATR calculator HTTP client
    from app.services.atr_calculator import atr_calculator
    await atr_calculator.close()
    
    await db.disconnect()


# Create FastAPI app
app = FastAPI(
    title="CryptoSatX - Enhanced Crypto Signal API",  # UPDATED
    description="AI-powered crypto trading signals with Smart Money Concept, signal history, and Telegram alerts",  # UPDATED
    version="2.0.0",  # UPDATED VERSION
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers (EXISTING - DO NOT MODIFY)
# Dashboard router FIRST to handle root path "/"
app.include_router(routes_dashboard.router, tags=["Dashboard"])
app.include_router(routes_health.router, tags=["Health"])
app.include_router(routes_signals.router, tags=["Signals"])
app.include_router(routes_gpt.router, tags=["GPT Actions"])
app.include_router(routes_coinglass.router, tags=["Coinglass Data"])
app.include_router(routes_lunarcrush.router, tags=["LunarCrush Social Data"])
app.include_router(routes_coinapi.router, tags=["CoinAPI Market Data"])
app.include_router(routes_smart_money.router, tags=["Smart Money Scanner"])

# ADDED FOR CRYPTOSATX ENHANCEMENT - New feature routes
app.include_router(routes_smc.router, tags=["Smart Money Concept (SMC)"])
app.include_router(routes_history.router, tags=["Signal History"])
app.include_router(routes_enhanced_gpt.router, tags=["Enhanced GPT Integration"])
app.include_router(routes_monitoring.router, tags=["Automated Monitoring"])
app.include_router(routes_openai.router, tags=["OpenAI GPT-4 Integration"])
app.include_router(routes_openai_v2.router, tags=["OpenAI V2 (Development)"])  # PHASE 1 DEVELOPMENT
app.include_router(
    routes_optimized_gpt.router, tags=["Optimized GPT Actions - MAXIMAL"]
)
app.include_router(
    routes_analytics.router, tags=["Analytics & Insights"]
)  # ADDED FOR DATABASE ANALYTICS
app.include_router(
    routes_mss.router, prefix="/mss", tags=["MSS Alpha System"]
)  # ADDED FOR MSS SYSTEM
app.include_router(
    routes_new_listings.router, tags=["Binance New Listings"]
)  # ADDED FOR NEW LISTINGS MONITOR
app.include_router(
    routes_narratives.router,
    prefix="/narratives",
    tags=["Narratives & Market Intelligence"],
)  # ADDED FOR NARRATIVE DETECTION
app.include_router(
    routes_rpc.router, tags=["Unified RPC - GPT Actions"]
)  # ADDED FOR UNIFIED RPC ENDPOINT - GPT ACTIONS
app.include_router(
    routes_gpt_actions.router, tags=["GPT Actions (Flat Params)"]
)  # ADDED FOR GPT ACTIONS COMPATIBILITY


# Override OpenAPI schema to inject servers field for GPT Actions compatibility
# This MUST be done AFTER all routes are registered to ensure proper schema generation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Inject servers field required by GPT Actions
    openapi_schema["servers"] = [
        {"url": "https://guardiansofthetoken.org", "description": "Production server"}
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
