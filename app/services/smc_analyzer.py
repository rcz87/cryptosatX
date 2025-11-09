# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Smart Money Concept (SMC) Analyzer
Detects BOS (Break of Structure), CHoCH (Change of Character), 
FVG (Fair Value Gaps), and Swing Points
"""
import httpx
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os


class SMCAnalyzer:
    """
    Analyzes price action using Smart Money Concept principles
    Identifies institutional trading patterns and liquidity zones
    """
    
    def __init__(self):
        self.coinapi_key = os.getenv("COINAPI_KEY")
        self.base_url = "https://rest.coinapi.io/v1"
    
    async def analyze_smc(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Perform complete SMC analysis
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            timeframe: Candle period (1MIN, 5MIN, 1HRS, 1DAY)
        
        Returns:
            Dict with SMC analysis results
        """
        try:
            # Get OHLCV data
            candles = await self._fetch_candles(symbol, timeframe, limit=50)
            
            if not candles:
                return {"error": "No candle data available"}
            
            # Perform SMC analysis
            swing_points = self._find_swing_points(candles)
            structure_breaks = self._detect_structure_breaks(candles, swing_points)
            fvgs = self._find_fair_value_gaps(candles)
            liquidity_zones = self._identify_liquidity_zones(swing_points)
            
            # Determine market structure
            market_structure = self._determine_market_structure(structure_breaks)
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
                "marketStructure": market_structure,
                "swingPoints": {
                    "highs": swing_points["highs"][-5:],  # Last 5 swing highs
                    "lows": swing_points["lows"][-5:],    # Last 5 swing lows
                },
                "structureBreaks": structure_breaks[-3:],  # Last 3 breaks
                "fairValueGaps": fvgs[-5:],  # Last 5 FVGs
                "liquidityZones": liquidity_zones,
                "analysis": {
                    "trend": market_structure["trend"],
                    "strength": market_structure["strength"],
                    "recommendation": self._get_smc_recommendation(market_structure, fvgs, structure_breaks)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"SMC analysis failed: {str(e)}"
            }
    
    async def _fetch_candles(self, symbol: str, period: str, limit: int = 50) -> List[Dict]:
        """Fetch OHLCV candles from CoinAPI"""
        try:
            symbol_id = f"BINANCE_SPOT_{symbol}_USDT"
            url = f"{self.base_url}/ohlcv/{symbol_id}/latest"
            
            # Fix header typing - ensure API key is string
            headers = {"X-CoinAPI-Key": self.coinapi_key or ""}
            params = {"period_id": period, "limit": limit}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return [{
                        "time": candle["time_period_start"],
                        "open": candle["price_open"],
                        "high": candle["price_high"],
                        "low": candle["price_low"],
                        "close": candle["price_close"],
                        "volume": candle["volume_traded"]
                    } for candle in data]
                
                return []
        
        except Exception:
            return []
    
    def _find_swing_points(self, candles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Identify swing highs and swing lows
        Swing High: High surrounded by 2 lower highs on each side
        Swing Low: Low surrounded by 2 higher lows on each side
        """
        highs = []
        lows = []
        lookback = 2
        
        for i in range(lookback, len(candles) - lookback):
            current = candles[i]
            
            # Check for swing high
            is_swing_high = True
            for j in range(1, lookback + 1):
                if candles[i - j]["high"] >= current["high"] or candles[i + j]["high"] >= current["high"]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                highs.append({
                    "price": current["high"],
                    "time": current["time"],
                    "index": i
                })
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, lookback + 1):
                if candles[i - j]["low"] <= current["low"] or candles[i + j]["low"] <= current["low"]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                lows.append({
                    "price": current["low"],
                    "time": current["time"],
                    "index": i
                })
        
        return {"highs": highs, "lows": lows}
    
    def _detect_structure_breaks(self, candles: List[Dict], swing_points: Dict) -> List[Dict]:
        """
        Detect BOS (Break of Structure) and CHoCH (Change of Character)
        BOS: Price breaks previous swing high/low in trend direction
        CHoCH: Price breaks counter-trend swing point (trend reversal signal)
        """
        breaks = []
        highs = swing_points["highs"]
        lows = swing_points["lows"]
        
        if len(highs) < 2 or len(lows) < 2:
            return breaks
        
        # Check for bullish breaks (BOS/CHoCH above swing highs)
        for i in range(len(candles) - 10, len(candles)):
            candle = candles[i]
            for swing_high in highs[-5:]:
                if candle["close"] > swing_high["price"] and i > swing_high["index"]:
                    breaks.append({
                        "type": "BOS" if candle["close"] > candle["open"] else "CHoCH",
                        "direction": "bullish",
                        "price": swing_high["price"],
                        "breakPrice": candle["close"],
                        "time": candle["time"]
                    })
        
        # Check for bearish breaks (BOS/CHoCH below swing lows)
        for i in range(len(candles) - 10, len(candles)):
            candle = candles[i]
            for swing_low in lows[-5:]:
                if candle["close"] < swing_low["price"] and i > swing_low["index"]:
                    breaks.append({
                        "type": "BOS" if candle["close"] < candle["open"] else "CHoCH",
                        "direction": "bearish",
                        "price": swing_low["price"],
                        "breakPrice": candle["close"],
                        "time": candle["time"]
                    })
        
        return breaks
    
    def _find_fair_value_gaps(self, candles: List[Dict]) -> List[Dict]:
        """
        Find Fair Value Gaps (FVG) - imbalances in price action
        Bullish FVG: Gap between candle[i-1].high and candle[i+1].low (with candle[i] being bullish)
        Bearish FVG: Gap between candle[i-1].low and candle[i+1].high (with candle[i] being bearish)
        """
        fvgs = []
        
        for i in range(1, len(candles) - 1):
            prev_candle = candles[i - 1]
            current_candle = candles[i]
            next_candle = candles[i + 1]
            
            # Bullish FVG
            if current_candle["close"] > current_candle["open"]:  # Bullish candle
                if prev_candle["high"] < next_candle["low"]:
                    gap_size = next_candle["low"] - prev_candle["high"]
                    fvgs.append({
                        "type": "bullish",
                        "top": next_candle["low"],
                        "bottom": prev_candle["high"],
                        "size": gap_size,
                        "time": current_candle["time"]
                    })
            
            # Bearish FVG
            elif current_candle["close"] < current_candle["open"]:  # Bearish candle
                if prev_candle["low"] > next_candle["high"]:
                    gap_size = prev_candle["low"] - next_candle["high"]
                    fvgs.append({
                        "type": "bearish",
                        "top": prev_candle["low"],
                        "bottom": next_candle["high"],
                        "size": gap_size,
                        "time": current_candle["time"]
                    })
        
        return fvgs
    
    def _identify_liquidity_zones(self, swing_points: Dict) -> Dict:
        """
        Identify key liquidity zones (areas where stops are likely)
        These are typically around swing highs/lows
        """
        highs = swing_points["highs"][-5:] if swing_points["highs"] else []
        lows = swing_points["lows"][-5:] if swing_points["lows"] else []
        
        return {
            "buyLiquidity": [{"price": h["price"], "strength": "high"} for h in highs],
            "sellLiquidity": [{"price": l["price"], "strength": "high"} for l in lows]
        }
    
    def _determine_market_structure(self, structure_breaks: List[Dict]) -> Dict:
        """Determine overall market structure from breaks"""
        if not structure_breaks:
            return {"trend": "neutral", "strength": "weak"}
        
        recent_breaks = structure_breaks[-3:]
        bullish_count = sum(1 for b in recent_breaks if b["direction"] == "bullish")
        bearish_count = sum(1 for b in recent_breaks if b["direction"] == "bearish")
        
        if bullish_count > bearish_count:
            strength = "strong" if bullish_count >= 2 else "moderate"
            return {"trend": "bullish", "strength": strength}
        elif bearish_count > bullish_count:
            strength = "strong" if bearish_count >= 2 else "moderate"
            return {"trend": "bearish", "strength": strength}
        else:
            return {"trend": "neutral", "strength": "weak"}
    
    def _get_smc_recommendation(self, market_structure: Dict, fvgs: List[Dict], 
                                structure_breaks: List[Dict]) -> str:
        """Generate trading recommendation based on SMC analysis"""
        trend = market_structure["trend"]
        strength = market_structure["strength"]
        
        if trend == "bullish" and strength == "strong":
            if fvgs and fvgs[-1]["type"] == "bullish":
                return "LONG - Strong bullish structure with FVG support"
            return "LONG - Strong bullish market structure"
        
        elif trend == "bearish" and strength == "strong":
            if fvgs and fvgs[-1]["type"] == "bearish":
                return "SHORT - Strong bearish structure with FVG resistance"
            return "SHORT - Strong bearish market structure"
        
        return "NEUTRAL - Wait for clear structure development"


# Singleton instance
smc_analyzer = SMCAnalyzer()
