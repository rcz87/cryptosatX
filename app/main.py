"""
Main FastAPI application
Crypto Futures Signal API with multi-provider integration
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limiter import limiter
from app.utils.logger import get_logger

# Initialize module logger
logger = get_logger(__name__)

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
    routes_admin,  # ADDED FOR ADMIN ENDPOINTS
    routes_scalping,  # ADDED FOR SCALPING GPT ACTIONS
    routes_nlp,  # ADDED FOR NATURAL LANGUAGE PROCESSING
    routes_cache,  # ADDED FOR CACHE MANAGEMENT
    routes_batch,  # ADDED FOR BATCH OPERATIONS
    routes_gpt_monitoring,  # ADDED FOR GPT ACTIONS MONITORING
    routes_unified,  # ADDED FOR PHASE 3 - UNIFIED RANKING SYSTEM
    routes_performance,  # ADDED FOR PHASE 4 - PERFORMANCE TRACKING & ANALYTICS
    routes_spike_detection,  # ADDED FOR PHASE 5 - REAL-TIME SPIKE DETECTION
    routes_spike_gpt,  # ADDED FOR PHASE 5 - SPIKE DETECTION GPT ACTIONS
    routes_comprehensive_monitoring,  # ADDED FOR COMPREHENSIVE COIN MONITORING SYSTEM
    routes_smart_entry,  # ADDED FOR PRO SMART ENTRY ENGINE
)

from app.middleware import (
    ResponseSizeMonitorMiddleware,
    GPTRateLimiterMiddleware,
    gpt_rate_limiter,
    DetailedRequestLoggerMiddleware,
)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Import database here to avoid circular imports
    from app.storage.database import db

    # Startup banner with environment validation
    logger.info("=" * 50)
    logger.info("🚀 CryptoSatX - Enhanced Crypto Signal API Starting...")
    logger.info("=" * 50)
    logger.info("Environment variables loaded:")
    logger.info(f"  - COINAPI_KEY: {'✓' if os.getenv('COINAPI_KEY') else '✗'}")
    logger.info(f"  - COINGLASS_API_KEY: {'✓' if os.getenv('COINGLASS_API_KEY') else '✗'}")
    logger.info(f"  - LUNARCRUSH_API_KEY: {'✓' if os.getenv('LUNARCRUSH_API_KEY') else '✗'}")
    logger.info(f"  - TELEGRAM_BOT_TOKEN: {'✓' if os.getenv('TELEGRAM_BOT_TOKEN') else '✗'}")
    logger.info(f"  - API_KEYS: {'✓' if os.getenv('API_KEYS') else '✗ (public mode)'}")
    logger.info(f"  - OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
    logger.info(f"  - DATABASE_URL: {'✓' if os.getenv('DATABASE_URL') else '✗'}")
    logger.info(f"  - BASE_URL: {os.getenv('BASE_URL', 'Not set')}")
    logger.info("=" * 50)
    logger.info("🚀 Enhanced Features: SMC Analysis | Signal History | Telegram Alerts | OpenAI GPT-4 | PostgreSQL Database")
    logger.info("=" * 50)

    # Initialize database connection
    await db.connect()
    
    # Initialize cache service and start cleanup task
    from app.core.cache_service import cache_service, start_cache_cleanup_task
    cache_cleanup_task = asyncio.create_task(start_cache_cleanup_task())
    logger.info("🗄️  Cache service initialized with auto-cleanup")

    # Initialize auto-scanner for 24/7 market monitoring
    # DISABLED: Auto scanner consumes ~200-300 API calls/hour
    # Uncomment below to enable automated scanning (Smart Money, MSS, RSI, LunarCrush)
    # from app.services.auto_scanner import auto_scanner
    # await auto_scanner.start()
    logger.info(f"  - AUTO_SCAN_ENABLED: ✗ (disabled to save API quota)")
    logger.info("  - Auto Scanner: DISABLED (manual signals via GPT Actions still work)")

    # Initialize performance tracker for automated outcome tracking
    from app.services.performance_tracker import performance_tracker
    await performance_tracker.start()
    logger.info("🎯 Performance tracker started - tracking signal outcomes at 1h, 4h, 24h, 7d, 30d intervals")

    # Initialize Real-Time Spike Detection System (PHASE 5 - EARLY ENTRY SYSTEM)
    # DISABLED: Spike detectors consume ~12,780 API calls/hour (99% of total usage!)
    # - Price Spike: 12,000 calls/hour (100 coins × 30s interval)
    # - Social Monitor: 600 calls/hour (50 coins × 5min interval)  
    # - Liquidation: 180 calls/hour (60s interval)
    # Uncomment below to enable real-time spike detection and auto Telegram alerts
    logger.info("=" * 50)
    logger.info("🚀 PHASE 5: Real-Time Spike Detection System - DISABLED")
    logger.info("=" * 50)
    logger.info("⚠️  Spike Detectors DISABLED to save API quota (saves ~12,780 calls/hour)")
    logger.info("✅ Manual signal endpoints still work 100% (GET /signals/{symbol})")
    logger.info("✅ GPT Actions fully functional - call anytime for on-demand signals")
    logger.info("=" * 50)

    # # Start Real-Time Price Spike Detector (>8% in 5min)
    # from app.services.realtime_spike_detector import realtime_spike_detector
    # asyncio.create_task(realtime_spike_detector.start())
    # logger.info("⚡ Real-Time Price Spike Detector STARTED - monitoring >8% moves in 5min, top 100 coins, 30s interval")

    # # Start Liquidation Spike Detector (>$50M market-wide, >$20M per coin)
    # from app.services.liquidation_spike_detector import liquidation_spike_detector
    # asyncio.create_task(liquidation_spike_detector.start())
    # logger.info("💥 Liquidation Spike Detector STARTED - monitoring large liquidation events, 60s interval")

    # # Start Social Spike Monitor (>100% social volume spike)
    # from app.services.social_spike_monitor import social_spike_monitor
    # asyncio.create_task(social_spike_monitor.start())
    # logger.info("📱 Social Spike Monitor STARTED - monitoring viral moments, 5min interval")

    # # Spike Coordinator is passive (receives signals from detectors)
    # from app.services.spike_coordinator import spike_coordinator
    # logger.info("🎯 Spike Coordinator ACTIVE - multi-signal correlation engine ready")

    # logger.info("=" * 50)
    # logger.info("✅ PHASE 5 Complete: Real-Time Spike Detection System ACTIVE")
    # logger.info("📊 Monitoring: Top 100 coins for >8% price moves, liquidations, social spikes")
    # logger.info("📱 Alerts: Instant Telegram notifications (no cooldown)")
    # logger.info("🎯 Correlation: Multi-signal validation for high-confidence alerts")
    # logger.info("=" * 50)

    yield

    # Shutdown: close database connection and cleanup resources
    logger.info("🛑 Shutting down CryptoSatX API...")

    # Stop performance tracker
    from app.services.performance_tracker import performance_tracker
    await performance_tracker.stop()
    logger.info("🛑 Performance tracker stopped")

    # Stop auto-scanner (DISABLED - not started)
    # from app.services.auto_scanner import auto_scanner
    # await auto_scanner.stop()
    # logger.info("🛑 Auto-scanner stopped")

    # Stop spike detection system (DISABLED - not started)
    # from app.services.realtime_spike_detector import realtime_spike_detector
    # from app.services.liquidation_spike_detector import liquidation_spike_detector
    # from app.services.social_spike_monitor import social_spike_monitor
    # realtime_spike_detector.stop()
    # liquidation_spike_detector.stop()
    # social_spike_monitor.stop()
    # logger.info("🛑 Spike detection system stopped")

    # Cancel cache cleanup task
    cache_cleanup_task.cancel()
    try:
        await cache_cleanup_task
    except asyncio.CancelledError:
        pass

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

# Register shared rate limiter from middleware module (avoids circular imports)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Request Logging middleware (logs all HTTP requests with details)
app.add_middleware(DetailedRequestLoggerMiddleware)

# Add GPT Actions middleware (MUST be after CORS, before SlowAPI)
app.add_middleware(GPTRateLimiterMiddleware, limiter=gpt_rate_limiter)
# Re-enabled with streaming-safe implementation
app.add_middleware(ResponseSizeMonitorMiddleware)

# Add SlowAPI rate limiting middleware (MUST be after CORS)
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers (PRIORITIZE API ROUTES FIRST)
# Health router first
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
app.include_router(routes_comprehensive_monitoring.router, tags=["Comprehensive Coin Monitoring"])  # ADDED FOR MULTI-COIN MULTI-TIMEFRAME MONITORING
app.include_router(routes_smart_entry.router, tags=["PRO Smart Entry Engine"])  # ADDED FOR PROFESSIONAL ENTRY ANALYSIS
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
app.include_router(
    routes_admin.router, tags=["Admin & System"]
)  # ADDED FOR ADMIN ENDPOINTS
app.include_router(
    routes_scalping.router, tags=["Scalping Analysis"]
)  # ADDED FOR SCALPING GPT ACTIONS
app.include_router(
    routes_nlp.router, tags=["Natural Language Processing"]
)  # ADDED FOR NLP UNIVERSAL INTERFACE
app.include_router(
    routes_cache.router, tags=["Cache Management"]
)  # ADDED FOR PERFORMANCE OPTIMIZATION
app.include_router(
    routes_batch.router, tags=["Batch Operations"]
)  # ADDED FOR MULTI-SYMBOL FETCHING
app.include_router(
    routes_gpt_monitoring.router, tags=["GPT Monitoring"]
)  # ADDED FOR GPT ACTIONS MONITORING & STATISTICS
app.include_router(
    routes_unified.router, tags=["Unified Ranking System"]
)  # ADDED FOR PHASE 3 - UNIFIED SCORING & CROSS-VALIDATION
app.include_router(
    routes_performance.router, tags=["Performance Tracking & Analytics"]
)  # ADDED FOR PHASE 4 - AUTOMATED OUTCOME TRACKING & WIN RATE ANALYTICS
app.include_router(
    routes_spike_detection.router, tags=["Real-Time Spike Detection"]
)  # ADDED FOR PHASE 5 - EARLY ENTRY SPIKE DETECTION SYSTEM
app.include_router(
    routes_spike_gpt.router, tags=["GPT Actions"]
)  # ADDED FOR PHASE 5 - SPIKE DETECTION GPT ACTIONS (user-friendly endpoints)
app.include_router(
    routes_gpt_schema.router, tags=["GPT Schema - Limited Operations"]
)  # ADDED FOR GPT ACTIONS TOP 30 SCHEMA

# Dashboard router LAST as catch-all fallback (handles root "/" and SPA routes)
# MUST be after all API routers to prevent route interception
app.include_router(routes_dashboard.router, tags=["Dashboard"])


# CRITICAL: Clear OpenAPI schema cache to force regeneration after code changes
# Without this, schema remains cached even after adding new routes
app.openapi_schema = None

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


# GPT-optimized OpenAPI endpoint (< 45 KB target)
@app.get("/openapi-gpt.json", include_in_schema=False)
async def get_gpt_optimized_openapi():
    """
    Optimized OpenAPI schema for GPT Actions (< 45 KB)
    Filters to include only GPT-relevant endpoints
    """
    from fastapi.openapi.utils import get_openapi
    from app.utils.gpt_schema_builder import build_gpt_actions_schema

    # Generate full schema
    full_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Filter to GPT-relevant tags only
    gpt_schema = build_gpt_actions_schema(
        app_openapi=full_schema,
        include_tags={
            "GPT Actions",
            "Scalping Analysis",
            "GPT Monitoring",
            "Unified RPC - GPT Actions",
            "Health",
            "Real-Time Spike Detection",  # PHASE 5 - Early Entry System
            "Comprehensive Coin Monitoring",  # NEW - Multi-coin Multi-timeframe Monitoring
            "PRO Smart Entry Engine",  # NEW - Professional Entry Analysis with 8-source Confluence
        },
        base_url="https://guardiansofthetoken.org"
    )

    return gpt_schema

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
