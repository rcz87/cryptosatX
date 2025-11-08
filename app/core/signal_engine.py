"""
Signal Engine
Combines data from multiple sources to generate trading signals
"""
from datetime import datetime
from typing import Dict
from app.services.coinapi_service import coinapi_service
from app.services.coinglass_service import coinglass_service
from app.services.lunarcrush_service import lunarcrush_service
from app.services.okx_service import okx_service


class SignalEngine:
    """
    Core engine that merges price, funding rate, open interest,
    and social sentiment to generate trading signals
    """
    
    async def build_signal(self, symbol: str) -> Dict:
        """
        Build a comprehensive trading signal for a given symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict containing all metrics and signal recommendation
        """
        # Normalize symbol
        symbol = symbol.upper()
        
        # Fetch data from all sources concurrently would be ideal,
        # but for simplicity we'll do sequential calls
        price_data = await coinapi_service.get_spot_price(symbol)
        cg_data = await coinglass_service.get_funding_and_oi(symbol)
        social_data = await lunarcrush_service.get_social_score(symbol)
        candles_data = await okx_service.get_candles(symbol, "15m", 20)
        
        # Extract metrics
        price = price_data.get("price", 0.0)
        funding_rate = cg_data.get("fundingRate", 0.0)
        open_interest = cg_data.get("openInterest", 0.0)
        social_score = social_data.get("socialScore", 50.0)
        
        # Calculate price trend from candles
        price_trend = self._calculate_price_trend(candles_data.get("candles", []))
        
        # Generate signal based on simple logic
        signal, reason = self._generate_signal(
            funding_rate=funding_rate,
            open_interest=open_interest,
            social_score=social_score,
            price_trend=price_trend
        )
        
        # Build comprehensive signal object
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "price": price,
            "fundingRate": funding_rate,
            "openInterest": open_interest,
            "socialScore": social_score,
            "priceTrend": price_trend,
            "signal": signal,
            "reason": reason,
            "dataQuality": {
                "priceAvailable": price_data.get("success", False),
                "fundingAvailable": cg_data.get("success", False),
                "socialAvailable": social_data.get("success", False),
                "candlesAvailable": candles_data.get("success", False)
            }
        }
    
    def _calculate_price_trend(self, candles: list) -> str:
        """
        Calculate simple price trend from candle data
        
        Args:
            candles: List of OHLCV candle data
            
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if not candles or len(candles) < 5:
            return "neutral"
        
        try:
            # Get recent candles (most recent first in OKX)
            recent = candles[:5]
            
            # Compare current price with average of last 5 candles
            current_close = recent[0]["close"]
            avg_close = sum(c["close"] for c in recent) / len(recent)
            
            # Calculate percentage difference
            diff_pct = ((current_close - avg_close) / avg_close) * 100
            
            if diff_pct > 0.5:
                return "bullish"
            elif diff_pct < -0.5:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            print(f"Error calculating price trend: {e}")
            return "neutral"
    
    def _generate_signal(
        self, 
        funding_rate: float,
        open_interest: float,
        social_score: float,
        price_trend: str
    ) -> tuple:
        """
        Generate trading signal based on multiple factors
        
        Simple logic (can be extended with SMC later):
        - LONG: Positive funding + high social score + bullish trend
        - SHORT: Negative funding + falling OI + bearish trend
        - NEUTRAL: Otherwise
        
        Args:
            funding_rate: Current funding rate (positive = longs paying shorts)
            open_interest: Current open interest value
            social_score: Social sentiment score (0-100)
            price_trend: Price trend direction
            
        Returns:
            Tuple of (signal, reason)
        """
        reasons = []
        score = 0
        
        # Funding rate analysis
        if funding_rate > 0.01:  # > 1% funding (extremely high)
            score -= 2
            reasons.append("Very high funding rate (overleveraged longs)")
        elif funding_rate > 0:
            score -= 1
            reasons.append("Positive funding rate")
        elif funding_rate < -0.01:  # < -1% funding
            score += 2
            reasons.append("Very negative funding rate (overleveraged shorts)")
        elif funding_rate < 0:
            score += 1
            reasons.append("Negative funding rate")
        
        # Social sentiment analysis
        if social_score > 70:
            score += 1
            reasons.append(f"High social sentiment ({social_score:.0f}/100)")
        elif social_score < 30:
            score -= 1
            reasons.append(f"Low social sentiment ({social_score:.0f}/100)")
        else:
            reasons.append(f"Neutral social sentiment ({social_score:.0f}/100)")
        
        # Price trend analysis
        if price_trend == "bullish":
            score += 1
            reasons.append("Bullish price action")
        elif price_trend == "bearish":
            score -= 1
            reasons.append("Bearish price action")
        else:
            reasons.append("Neutral price action")
        
        # Open interest note (for context, not directly influencing signal yet)
        if open_interest > 0:
            reasons.append(f"OI: ${open_interest:,.0f}")
        
        # Determine final signal
        if score >= 2:
            signal = "LONG"
        elif score <= -2:
            signal = "SHORT"
        else:
            signal = "NEUTRAL"
        
        reason = " | ".join(reasons)
        
        return signal, reason


# Singleton instance
signal_engine = SignalEngine()
