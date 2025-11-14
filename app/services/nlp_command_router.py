"""
NLP Command Router
Universal natural language interface for all scalping layers
Supports Indonesian and English queries
"""

import re
from typing import Dict, Any, Optional
from app.services.coinapi_service import coinapi_service
from app.services.coinglass_comprehensive_service import coinglass_comprehensive
from app.services.lunarcrush_service import lunarcrush_service
from app.services.smart_money_service import smart_money_service
from app.utils.symbol_normalizer import normalize_symbol


class NLPCommandRouter:
    """Routes natural language commands to appropriate data layers"""
    
    def __init__(self):
        self.keyword_mapping = {
            # Signal generation (LONG/SHORT/NEUTRAL recommendations)
            "signal": "signal",
            "sinyal": "signal",
            "rekomendasi": "signal",
            "recommendation": "signal",
            
            # Scalping analysis
            "analisa": "scalping",
            "analyze": "scalping",
            "analisis": "scalping",
            "analysis": "scalping",
            "scalping": "scalping",
            "scalp": "scalping",
            "entry": "scalping",
            
            # News
            "berita": "news",
            "news": "news",
            "kabar": "news",
            "update": "news",
            
            # Whale positions
            "whale": "whale",
            "paus": "whale",
            "institusi": "whale",
            "dex": "whale",
            
            # Sentiment
            "sentimen": "sentiment",
            "sentiment": "sentiment",
            "social": "sentiment",
            "sosial": "sentiment",
            "hype": "sentiment",
            
            # Funding rate
            "funding": "funding",
            "dana": "funding",
            "rate": "funding",
            
            # Liquidations
            "liquidation": "liquidation",
            "likuidasi": "liquidation",
            "liq": "liquidation",
            "panic": "liquidation",
            
            # Long/Short ratio
            "ratio": "ls_ratio",
            "long": "ls_ratio",
            "short": "ls_ratio",
            "posisi": "ls_ratio",
            
            # RSI
            "rsi": "rsi",
            "overbought": "rsi",
            "oversold": "rsi",
            
            # Smart money
            "smart": "smart_money",
            "smartmoney": "smart_money",
            "institutional": "smart_money",
            "smc": "smart_money",
            
            # OHLCV
            "candle": "ohlcv",
            "ohlcv": "ohlcv",
            "chart": "ohlcv",
            "trend": "ohlcv",
            
            # Price
            "price": "price",
            "harga": "price",
            "spot": "price",
            
            # Volume
            "volume": "volume",
            "vol": "volume",
        }
    
    def extract_symbol(self, query: str) -> str:
        """Extract cryptocurrency symbol from query with safe fallback"""
        query_upper = query.upper()
        
        common_symbols = [
            "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC", "DOT", "AVAX",
            "LINK", "UNI", "ATOM", "LTC", "ETC", "XLM", "ALGO", "VET", "ICP", "FIL",
            "TRX", "NEAR", "HBAR", "APT", "ARB", "OP", "PEPE", "SHIB", "WIF", "BONK",
            "SUI", "SEI", "INJ", "RUNE", "AAVE", "MKR", "SNX", "CRV", "COMP"
        ]
        
        # Priority 1: Check against known symbols list
        for symbol in common_symbols:
            if f" {symbol} " in f" {query_upper} " or query_upper.startswith(symbol + " ") or query_upper.endswith(" " + symbol):
                return symbol
        
        # Priority 2: Extract potential symbol and validate
        symbol_pattern = r'\b([A-Z]{2,5})\b'
        matches = re.findall(symbol_pattern, query_upper)
        
        for match in matches:
            if match in common_symbols:
                return match
        
        # Fallback: Default to BTC
        return "BTC"
    
    def detect_layer(self, query: str) -> str:
        """Detect which layer to query based on keywords"""
        query_lower = query.lower()
        
        for keyword, layer in self.keyword_mapping.items():
            if keyword in query_lower:
                return layer
        
        return "scalping"
    
    def extract_mode(self, query: str) -> str:
        """
        Extract signal mode from natural language query
        Supports Indonesian and English mode keywords
        
        Examples:
            "scalping XRP mode 3" -> "3"
            "analisis BTC pakai mode agresif" -> "aggressive"
            "signal ETH konservatif" -> "conservative"
            "SOL ultra mode" -> "ultra"
        """
        query_lower = query.lower()
        
        # Mode keyword mappings (Indonesian + English)
        mode_patterns = {
            # Conservative mode (mode 1)
            r'\b(konservatif|conservative|safe|aman|mode\s*1|m1)\b': 'conservative',
            
            # Aggressive mode (mode 2) 
            r'\b(agresif|aggressive|balanced|seimbang|mode\s*2|m2)\b': 'aggressive',
            
            # Ultra mode (mode 3)
            r'\b(ultra|extreme|ekstrem|scalping\s+mode|mode\s+scalping|mode\s*3|m3)\b': 'ultra',
        }
        
        # Check each pattern
        for pattern, mode in mode_patterns.items():
            if re.search(pattern, query_lower):
                return mode
        
        # Default to aggressive if no mode specified
        return 'aggressive'
    
    async def route_command(self, query: str) -> Dict[str, Any]:
        """Route natural language command to appropriate layer"""
        symbol = self.extract_symbol(query)
        layer = self.detect_layer(query)
        mode = self.extract_mode(query)
        
        response = {
            "query": query,
            "detected_symbol": symbol,
            "detected_layer": layer,
            "detected_mode": mode,
            "data": None,
            "interpretation": ""
        }
        
        try:
            # Use base ticker for services that expect it
            if layer == "signal":
                response["data"] = await self._get_signal(symbol, mode)
                response["interpretation"] = f"Trading signal for {symbol} (mode: {mode})"
                
            elif layer == "scalping":
                response["data"] = await self._get_scalping_analysis(symbol, mode)
                response["interpretation"] = f"Complete scalping analysis for {symbol} (mode: {mode})"
                
            elif layer == "news":
                response["data"] = await self._get_news(symbol)
                response["interpretation"] = f"Latest news for {symbol}"
                
            elif layer == "whale":
                response["data"] = await self._get_whale_positions()
                response["interpretation"] = f"Hyperliquid whale positions (all symbols)"
                
            elif layer == "sentiment":
                response["data"] = await lunarcrush_service.get_coin_sentiment(symbol)
                response["interpretation"] = f"Social sentiment analysis for {symbol}"
                
            elif layer == "funding":
                pair = normalize_symbol(symbol, "coinglass") or f"{symbol}USDT"
                response["data"] = await coinglass_comprehensive.get_funding_rate_history(
                    exchange="BINANCE", symbol=pair, interval="h8", limit=10
                )
                response["interpretation"] = f"Funding rate history for {symbol}"
                
            elif layer == "liquidation":
                pair = normalize_symbol(symbol, "coinglass") or f"{symbol}USDT"
                response["data"] = await coinglass_comprehensive.get_liquidation_aggregated_history(
                    symbol=pair, exchange_list="BINANCE", interval="1h", limit=24
                )
                response["interpretation"] = f"Liquidation history for {symbol}"
                
            elif layer == "ls_ratio":
                pair = normalize_symbol(symbol, "coinglass") or f"{symbol}USDT"
                response["data"] = await coinglass_comprehensive.get_top_long_short_position_ratio_history(
                    exchange="BINANCE", symbol=pair, interval="h1", limit=10
                )
                response["interpretation"] = f"Long/Short ratio for {symbol}"
                
            elif layer == "rsi":
                pair = normalize_symbol(symbol, "coinglass") or f"{symbol}USDT"
                response["data"] = await coinglass_comprehensive.get_rsi_indicator(
                    exchange="BINANCE", symbol=pair, interval="1h"
                )
                response["interpretation"] = f"RSI indicator for {symbol}"
                
            elif layer == "smart_money":
                response["data"] = await smart_money_service.scan_smart_money(symbol)
                response["interpretation"] = f"Smart money analysis for {symbol}"
                
            elif layer == "ohlcv":
                response["data"] = await coinapi_service.get_ohlcv_latest(symbol, period="1HRS", limit=24)
                response["interpretation"] = f"OHLCV trend analysis for {symbol}"
                
            elif layer == "price":
                response["data"] = await coinapi_service.get_spot_price(symbol)
                response["interpretation"] = f"Current spot price for {symbol}"
                
            elif layer == "volume":
                pair = normalize_symbol(symbol, "coinglass") or f"{symbol}USDT"
                response["data"] = await coinglass_comprehensive.get_taker_buy_sell_volume_exchange_list(pair)
                response["interpretation"] = f"Volume delta for {symbol}"
            
            else:
                response["data"] = await self._get_scalping_analysis(symbol)
                response["interpretation"] = f"Complete analysis for {symbol} (default)"
            
            return response
            
        except Exception as e:
            response["error"] = str(e)
            response["interpretation"] = f"Error processing query: {str(e)}"
            return response
    
    async def _get_signal(self, symbol: str, mode: str = "aggressive") -> Dict[str, Any]:
        """
        Get trading signal (LONG/SHORT/NEUTRAL) with mode selection
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            mode: Signal mode - "conservative", "aggressive", or "ultra"
        """
        from app.core.signal_engine import signal_engine
        return await signal_engine.build_signal(symbol, debug=False, mode=mode)
    
    async def _get_scalping_analysis(self, symbol: str, mode: str = "aggressive") -> Dict[str, Any]:
        """
        Get complete scalping analysis with mode selection
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            mode: Signal mode - "conservative", "aggressive", or "ultra"
        """
        from app.api.routes_scalping import ScalpingAnalysisRequest, analyze_for_scalping
        
        request = ScalpingAnalysisRequest(
            symbol=symbol,
            mode=mode,
            include_smart_money=False,
            include_whale_positions=False,
            include_fear_greed=False,
            include_coinapi=True,
            include_sentiment=True
        )
        
        return await analyze_for_scalping(request)
    
    async def _get_news(self, symbol: str) -> Dict[str, Any]:
        """Get latest news"""
        try:
            news_data = await coinglass_comprehensive.get_news_feed(limit=10, include_content=False)
            
            if news_data.get("success") and news_data.get("news"):
                symbol_news = []
                for item in news_data["news"]:
                    title = item.get("title", "").upper()
                    if symbol.upper() in title:
                        symbol_news.append(item)
                
                if symbol_news:
                    return {
                        "success": True,
                        "symbol": symbol,
                        "news_count": len(symbol_news),
                        "news": symbol_news[:5]
                    }
                else:
                    return {
                        "success": True,
                        "symbol": symbol,
                        "news_count": len(news_data["news"]),
                        "news": news_data["news"][:10],
                        "note": f"No specific news for {symbol}, showing latest general news"
                    }
            
            return news_data
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_whale_positions(self) -> Dict[str, Any]:
        """Get Hyperliquid whale positions"""
        try:
            return await coinglass_comprehensive.get_hyperliquid_whale_positions()
        except Exception as e:
            return {"success": False, "error": str(e)}


nlp_router = NLPCommandRouter()


async def process_natural_command(query: str) -> Dict[str, Any]:
    """
    Process natural language command and route to appropriate layer
    
    Args:
        query: Natural language query (e.g., "Analisa SOL", "Berita BTC", "Whale posisi ETH")
    
    Returns:
        Dict with detected layer, symbol, and data
    """
    return await nlp_router.route_command(query)
