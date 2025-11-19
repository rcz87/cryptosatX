"""
Technical Indicators Module
Provides professional-grade technical analysis indicators for trend detection

Indicators:
- MA (Moving Average): Simple moving average for trend identification
- EMA (Exponential Moving Average): Weighted moving average giving more importance to recent prices
- RSI (Relative Strength Index): Momentum oscillator measuring overbought/oversold conditions
- MACD (Moving Average Convergence Divergence): Trend-following momentum indicator
- Volume Analysis: Volume confirmation for trend validation

Author: CryptoSatX Signal Engine
Last Updated: November 19, 2025
"""
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Professional Technical Analysis Indicators Calculator
    
    All methods handle edge cases gracefully and return safe defaults
    when insufficient data is available.
    """
    
    @staticmethod
    def calculate_ma(prices: List[float], period: int = 20) -> Optional[float]:
        """
        Calculate Simple Moving Average (MA)
        
        Args:
            prices: List of closing prices (most recent last)
            period: Number of periods for MA calculation (default: 20)
            
        Returns:
            MA value or None if insufficient data
            
        Example:
            prices = [100, 102, 101, 103, 105]
            ma = calculate_ma(prices, period=5)  # Returns 102.2
        """
        if not prices or len(prices) < period:
            return None
            
        try:
            recent_prices = prices[-period:]
            ma = sum(recent_prices) / period
            return round(ma, 8)
        except Exception as e:
            logger.error(f"MA calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int = 12) -> Optional[float]:
        """
        Calculate Exponential Moving Average (EMA)
        
        EMA gives more weight to recent prices, making it more responsive
        to new information than simple MA.
        
        Formula:
            EMA = Price(today) * k + EMA(yesterday) * (1 - k)
            where k = 2 / (period + 1)
        
        Args:
            prices: List of closing prices (most recent last)
            period: Number of periods for EMA calculation (default: 12)
            
        Returns:
            EMA value or None if insufficient data
        """
        if not prices or len(prices) < period:
            return None
            
        try:
            # Calculate multiplier
            k = 2 / (period + 1)
            
            # Start with SMA as initial EMA
            sma = sum(prices[:period]) / period
            ema = sma
            
            # Calculate EMA for remaining prices
            for price in prices[period:]:
                ema = (price * k) + (ema * (1 - k))
            
            return round(ema, 8)
        except Exception as e:
            logger.error(f"EMA calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI measures momentum on a scale of 0-100:
        - RSI > 70: Overbought (potential reversal down)
        - RSI < 30: Oversold (potential reversal up)
        - RSI 50: Neutral
        
        Formula:
            RSI = 100 - (100 / (1 + RS))
            where RS = Average Gain / Average Loss
        
        Args:
            prices: List of closing prices (most recent last)
            period: Number of periods for RSI calculation (default: 14)
            
        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if not prices or len(prices) < period + 1:
            return None
            
        try:
            # Calculate price changes
            changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            # Separate gains and losses
            gains = [change if change > 0 else 0 for change in changes]
            losses = [-change if change < 0 else 0 for change in changes]
            
            # Calculate average gain and loss
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            # Handle division by zero
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        MACD is a trend-following momentum indicator showing the relationship
        between two moving averages of a security's price.
        
        Components:
        - MACD Line: 12-period EMA - 26-period EMA
        - Signal Line: 9-period EMA of MACD Line
        - Histogram: MACD Line - Signal Line
        
        Trading Signals:
        - MACD crosses above Signal: Bullish (buy signal)
        - MACD crosses below Signal: Bearish (sell signal)
        - Histogram > 0: Bullish momentum
        - Histogram < 0: Bearish momentum
        
        Args:
            prices: List of closing prices (most recent last)
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            
        Returns:
            Dict with 'macd', 'signal', 'histogram', and 'trend' or None
        """
        if not prices or len(prices) < slow_period + signal_period:
            return None
            
        try:
            # Calculate fast and slow EMAs
            fast_ema = TechnicalIndicators._calculate_ema_series(prices, fast_period)
            slow_ema = TechnicalIndicators._calculate_ema_series(prices, slow_period)
            
            if not fast_ema or not slow_ema:
                return None
            
            # FIXED: Align fast EMA to slow EMA length before subtraction
            # Slow EMA starts later due to longer period, so trim fast EMA to match
            fast_ema_aligned = fast_ema[-len(slow_ema):]
            
            # Calculate MACD line (now properly aligned)
            macd_line = [fast - slow for fast, slow in zip(fast_ema_aligned, slow_ema)]
            
            # Calculate signal line (EMA of MACD)
            signal_line = TechnicalIndicators._calculate_ema_series(macd_line, signal_period)
            
            if not signal_line:
                return None
            
            # Get current values (most recent)
            macd_current = macd_line[-1]
            signal_current = signal_line[-1]
            histogram = macd_current - signal_current
            
            # Determine trend
            if histogram > 0 and macd_current > 0:
                trend = "bullish"
            elif histogram < 0 and macd_current < 0:
                trend = "bearish"
            else:
                trend = "neutral"
            
            return {
                "macd": round(macd_current, 8),
                "signal": round(signal_current, 8),
                "histogram": round(histogram, 8),
                "trend": trend
            }
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return None
    
    @staticmethod
    def _calculate_ema_series(prices: List[float], period: int) -> Optional[List[float]]:
        """
        Calculate EMA for entire price series (helper for MACD)
        
        Args:
            prices: List of closing prices
            period: EMA period
            
        Returns:
            List of EMA values or None
        """
        if not prices or len(prices) < period:
            return None
            
        try:
            k = 2 / (period + 1)
            ema_series = []
            
            # Start with SMA as initial EMA
            sma = sum(prices[:period]) / period
            ema_series.append(sma)
            
            # Calculate EMA for each subsequent price
            for price in prices[period:]:
                ema = (price * k) + (ema_series[-1] * (1 - k))
                ema_series.append(ema)
            
            return ema_series
        except Exception as e:
            logger.error(f"EMA series calculation error: {e}")
            return None
    
    @staticmethod
    def detect_ma_crossover(
        prices: List[float],
        fast_period: int = 10,
        slow_period: int = 20
    ) -> Optional[str]:
        """
        Detect Moving Average Crossover Signal
        
        A crossover occurs when a faster MA crosses a slower MA:
        - Golden Cross: Fast MA crosses above Slow MA → Bullish
        - Death Cross: Fast MA crosses below Slow MA → Bearish
        
        Args:
            prices: List of closing prices (most recent last)
            fast_period: Fast MA period (default: 10)
            slow_period: Slow MA period (default: 20)
            
        Returns:
            'bullish_crossover', 'bearish_crossover', or 'no_crossover'
        """
        if not prices or len(prices) < slow_period + 2:
            return None
            
        try:
            # Calculate current MAs
            fast_ma_current = TechnicalIndicators.calculate_ma(prices, fast_period)
            slow_ma_current = TechnicalIndicators.calculate_ma(prices, slow_period)
            
            # Calculate previous MAs
            fast_ma_prev = TechnicalIndicators.calculate_ma(prices[:-1], fast_period)
            slow_ma_prev = TechnicalIndicators.calculate_ma(prices[:-1], slow_period)
            
            # None check
            if fast_ma_current is None or slow_ma_current is None or fast_ma_prev is None or slow_ma_prev is None:
                return "no_crossover"
            
            # Detect crossover
            # Golden Cross: Fast was below, now above
            if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
                return "bullish_crossover"
            
            # Death Cross: Fast was above, now below
            elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
                return "bearish_crossover"
            
            else:
                return "no_crossover"
                
        except Exception as e:
            logger.error(f"MA crossover detection error: {e}")
            return "no_crossover"
    
    @staticmethod
    def analyze_volume_trend(
        volumes: List[float],
        prices: List[float],
        period: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze Volume Trend for Confirmation
        
        Volume analysis helps confirm price trends:
        - Rising price + Rising volume = Strong uptrend (confirmed)
        - Rising price + Falling volume = Weak uptrend (divergence)
        - Falling price + Rising volume = Strong downtrend (confirmed)
        - Falling price + Falling volume = Weak downtrend (divergence)
        
        Args:
            volumes: List of volume data (most recent last)
            prices: List of closing prices (most recent last)
            period: Lookback period for analysis (default: 10)
            
        Returns:
            Dict with 'confirmation', 'divergence', 'strength' or None
        """
        if not volumes or not prices or len(volumes) < period or len(prices) < period:
            return None
            
        try:
            # Calculate average volume
            avg_volume = sum(volumes[-period:]) / period
            current_volume = volumes[-1]
            
            # Volume trend
            volume_increasing = current_volume > avg_volume
            
            # Price trend
            price_change = prices[-1] - prices[-period]
            price_increasing = price_change > 0
            
            # Volume strength (vs average)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Determine confirmation
            if price_increasing and volume_increasing:
                confirmation = "bullish_confirmed"
                divergence = False
                strength = min(volume_ratio, 3.0)  # Cap at 3x for scoring
            elif not price_increasing and volume_increasing:
                confirmation = "bearish_confirmed"
                divergence = False
                strength = min(volume_ratio, 3.0)
            elif price_increasing and not volume_increasing:
                confirmation = "bullish_weak"
                divergence = True
                strength = volume_ratio
            else:  # Falling price + falling volume
                confirmation = "bearish_weak"
                divergence = True
                strength = volume_ratio
            
            return {
                "confirmation": confirmation,
                "divergence": divergence,
                "strength": round(strength, 2),
                "volume_ratio": round(volume_ratio, 2)
            }
        except Exception as e:
            logger.error(f"Volume analysis error: {e}")
            return None
    
    @staticmethod
    def calculate_trend_score(
        prices: List[float],
        volumes: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate Comprehensive Trend Score using all indicators
        
        Combines multiple technical indicators for robust trend detection:
        - MA Crossover (weight: 25%)
        - RSI Momentum (weight: 20%)
        - MACD Trend (weight: 30%)
        - Volume Confirmation (weight: 25%)
        
        Args:
            prices: List of closing prices (most recent last)
            volumes: Optional list of volume data
            
        Returns:
            Dict with 'trend', 'score', 'confidence', 'signals'
        """
        if not prices or len(prices) < 30:
            return {
                "trend": "neutral",
                "score": 50,
                "confidence": "low",
                "signals": {}
            }
        
        try:
            signals = {}
            score = 50  # Start neutral
            
            # 1. MA Crossover (25% weight)
            ma_cross = TechnicalIndicators.detect_ma_crossover(prices, 10, 20)
            if ma_cross == "bullish_crossover":
                score += 25
                signals["ma_crossover"] = "bullish"
            elif ma_cross == "bearish_crossover":
                score -= 25
                signals["ma_crossover"] = "bearish"
            else:
                signals["ma_crossover"] = "neutral"
            
            # 2. RSI Momentum (20% weight)
            rsi = TechnicalIndicators.calculate_rsi(prices, 14)
            if rsi:
                if rsi > 70:
                    score -= 15  # Overbought - bearish
                    signals["rsi"] = f"overbought ({rsi:.1f})"
                elif rsi < 30:
                    score += 15  # Oversold - bullish
                    signals["rsi"] = f"oversold ({rsi:.1f})"
                elif rsi > 55:
                    score += 10  # Bullish momentum
                    signals["rsi"] = f"bullish ({rsi:.1f})"
                elif rsi < 45:
                    score -= 10  # Bearish momentum
                    signals["rsi"] = f"bearish ({rsi:.1f})"
                else:
                    signals["rsi"] = f"neutral ({rsi:.1f})"
            
            # 3. MACD Trend (30% weight)
            macd = TechnicalIndicators.calculate_macd(prices)
            if macd:
                if macd["trend"] == "bullish":
                    score += 30
                    signals["macd"] = f"bullish (hist: {macd['histogram']:.4f})"
                elif macd["trend"] == "bearish":
                    score -= 30
                    signals["macd"] = f"bearish (hist: {macd['histogram']:.4f})"
                else:
                    signals["macd"] = "neutral"
            
            # 4. Volume Confirmation (25% weight)
            if volumes:
                vol_analysis = TechnicalIndicators.analyze_volume_trend(volumes, prices, 10)
                if vol_analysis:
                    conf = vol_analysis["confirmation"]
                    if "bullish_confirmed" in conf:
                        score += 25
                        signals["volume"] = f"confirmed (ratio: {vol_analysis['volume_ratio']}x)"
                    elif "bearish_confirmed" in conf:
                        score -= 25
                        signals["volume"] = f"confirmed (ratio: {vol_analysis['volume_ratio']}x)"
                    elif vol_analysis["divergence"]:
                        score += 5 if "bullish" in conf else -5
                        signals["volume"] = "divergence (weak)"
                    else:
                        signals["volume"] = "neutral"
            
            # Clamp score to 0-100
            score = max(0, min(100, score))
            
            # Determine trend and confidence
            if score >= 70:
                trend = "strongly_bullish"
                confidence = "high"
            elif score >= 60:
                trend = "bullish"
                confidence = "medium"
            elif score > 40:
                trend = "neutral"
                confidence = "low"
            elif score > 30:
                trend = "bearish"
                confidence = "medium"
            else:
                trend = "strongly_bearish"
                confidence = "high"
            
            return {
                "trend": trend,
                "score": round(score, 1),
                "confidence": confidence,
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Trend score calculation error: {e}")
            return {
                "trend": "neutral",
                "score": 50,
                "confidence": "low",
                "signals": {"error": str(e)}
            }
