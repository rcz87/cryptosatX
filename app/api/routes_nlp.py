"""
Natural Language Processing Router
Universal natural language interface for all crypto analysis layers
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.services.nlp_command_router import process_natural_command


router = APIRouter(prefix="/nlp", tags=["Natural Language"])


class NLPQueryRequest(BaseModel):
    """Natural language query request"""
    query: str = Field(
        ..., 
        description="Natural language query in Indonesian or English",
        examples=[
            "Analisa SOL",
            "Berita BTC",
            "Whale posisi ETH",
            "Sentimen XRP",
            "Funding rate BNB",
            "Liquidation DOGE"
        ]
    )


class NLPQueryResponse(BaseModel):
    """Natural language query response"""
    query: str
    detected_symbol: str
    detected_layer: str
    interpretation: str
    data: Dict[str, Any]


@router.post("/analyze",
    response_model=NLPQueryResponse,
    summary="Natural Language Query Analysis",
    description="""
    **🗣️ Universal Natural Language Interface untuk Semua Layer**
    
    Kamu bisa ngomong bebas dalam bahasa Indonesia atau English:
    
    **📊 Scalping Analysis:**
    - "Analisa SOL"
    - "Analyze BTC"
    - "Entry point XRP"
    - "Scalping ETH"
    
    **📰 News & Updates:**
    - "Berita BTC"
    - "News ETH"
    - "Update SOL"
    
    **🐋 Whale Positions:**
    - "Whale posisi ETH"
    - "Institutional BTC"
    - "Paus XRP"
    
    **💭 Sentiment Analysis:**
    - "Sentimen SOL"
    - "Social BTC"
    - "Hype PEPE"
    
    **💰 Funding Rate:**
    - "Funding BTC"
    - "Rate ETH"
    
    **💣 Liquidations:**
    - "Liquidation BTC"
    - "Likuidasi ETH"
    - "Panic SOL"
    
    **📈 Technical Indicators:**
    - "RSI BTC"
    - "Long short ratio ETH"
    - "Volume SOL"
    - "Chart XRP"
    - "Trend DOGE"
    
    **💎 Smart Money:**
    - "Smart money BTC"
    - "Institutional ETH"
    
    **💵 Price:**
    - "Harga BTC"
    - "Price ETH"
    - "Spot SOL"
    
    System akan otomatis:
    1. Deteksi symbol crypto (BTC, ETH, SOL, dll)
    2. Deteksi layer yang diminta (analisa, berita, whale, dll)
    3. Route ke endpoint yang tepat
    4. Return data lengkap
    """)
async def nlp_analyze(request: NLPQueryRequest):
    """
    Process natural language query and return analysis
    
    Supports both Indonesian and English queries with automatic:
    - Symbol detection
    - Layer routing
    - Data aggregation
    """
    try:
        result = await process_natural_command(request.query)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"NLP processing failed: {str(e)}"
        )


@router.get("/analyze",
    response_model=NLPQueryResponse,
    summary="Natural Language Query (GET)",
    description="Same as POST /nlp/analyze but via GET with query parameter")
async def nlp_analyze_get(
    query: str = Query(
        ...,
        description="Natural language query",
        examples=["Analisa SOL", "Berita BTC", "Whale ETH"]
    )
):
    """
    GET version of natural language analysis
    Useful for quick testing via browser
    """
    try:
        result = await process_natural_command(query)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"NLP processing failed: {str(e)}"
        )


@router.get("/info",
    summary="NLP Router Information",
    description="Get information about supported keywords and symbols")
async def nlp_info():
    """Information about NLP router capabilities"""
    return {
        "name": "CryptoSatX NLP Router",
        "version": "1.0.0",
        "description": "Universal natural language interface for crypto analysis",
        "supported_languages": ["Indonesian", "English"],
        "supported_layers": {
            "scalping": {
                "keywords": ["analisa", "analyze", "scalping", "entry"],
                "description": "Complete scalping analysis with all layers"
            },
            "news": {
                "keywords": ["berita", "news", "update"],
                "description": "Latest crypto news and updates"
            },
            "whale": {
                "keywords": ["whale", "paus", "institutional", "institusi"],
                "description": "Hyperliquid whale positions"
            },
            "sentiment": {
                "keywords": ["sentimen", "sentiment", "social", "hype"],
                "description": "Social sentiment analysis"
            },
            "funding": {
                "keywords": ["funding", "dana", "rate"],
                "description": "Funding rate history"
            },
            "liquidation": {
                "keywords": ["liquidation", "likuidasi", "liq", "panic"],
                "description": "Liquidation history"
            },
            "ls_ratio": {
                "keywords": ["ratio", "long", "short", "posisi"],
                "description": "Long/Short position ratio"
            },
            "rsi": {
                "keywords": ["rsi", "overbought", "oversold"],
                "description": "RSI indicator"
            },
            "smart_money": {
                "keywords": ["smart", "smartmoney", "institutional"],
                "description": "Smart money flow analysis"
            },
            "ohlcv": {
                "keywords": ["candle", "ohlcv", "chart", "trend"],
                "description": "OHLCV trend analysis"
            },
            "price": {
                "keywords": ["price", "harga", "spot"],
                "description": "Current spot price"
            },
            "volume": {
                "keywords": ["volume", "vol"],
                "description": "Volume delta analysis"
            }
        },
        "supported_symbols": [
            "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC", "DOT", "AVAX",
            "LINK", "UNI", "ATOM", "LTC", "ETC", "XLM", "ALGO", "VET", "ICP", "FIL",
            "TRX", "NEAR", "HBAR", "APT", "ARB", "OP", "PEPE", "SHIB", "WIF", "BONK"
        ],
        "examples": [
            {"query": "Analisa SOL", "layer": "scalping", "symbol": "SOL"},
            {"query": "Berita BTC", "layer": "news", "symbol": "BTC"},
            {"query": "Whale ETH", "layer": "whale", "symbol": "ETH"},
            {"query": "Sentimen PEPE", "layer": "sentiment", "symbol": "PEPE"},
            {"query": "Funding XRP", "layer": "funding", "symbol": "XRP"},
            {"query": "RSI DOGE", "layer": "rsi", "symbol": "DOGE"}
        ],
        "endpoints": {
            "POST /nlp/analyze": "Main endpoint for natural language queries",
            "GET /nlp/analyze?query=...": "GET version for quick testing",
            "GET /nlp/info": "This endpoint"
        }
    }
