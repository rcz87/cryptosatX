"""
Main FastAPI application
Crypto Futures Signal API with multi-provider integration
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import routes_health, routes_signals, routes_gpt, routes_coinglass, routes_lunarcrush, routes_coinapi, routes_smart_money

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    print("=" * 50)
    print("Crypto Futures Signal API Starting...")
    print("=" * 50)
    print(f"Environment variables loaded:")
    print(f"  - COINAPI_KEY: {'✓' if os.getenv('COINAPI_KEY') else '✗'}")
    print(f"  - COINGLASS_API_KEY: {'✓' if os.getenv('COINGLASS_API_KEY') else '✗'}")
    print(f"  - LUNARCRUSH_API_KEY: {'✓' if os.getenv('LUNARCRUSH_API_KEY') else '✗'}")
    print(f"  - BASE_URL: {os.getenv('BASE_URL', 'Not set')}")
    print("=" * 50)
    
    yield
    
    print("Shutting down Crypto Futures Signal API...")


# Create FastAPI app
app = FastAPI(
    title="Crypto Futures Signal API",
    description="Production-ready API for crypto trading signals with multi-provider data integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_health.router, tags=["Health"])
app.include_router(routes_signals.router, tags=["Signals"])
app.include_router(routes_gpt.router, tags=["GPT Actions"])
app.include_router(routes_coinglass.router, tags=["Coinglass Data"])
app.include_router(routes_lunarcrush.router, tags=["LunarCrush Social Data"])
app.include_router(routes_coinapi.router, tags=["CoinAPI Market Data"])
app.include_router(routes_smart_money.router, tags=["Smart Money Scanner"])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
