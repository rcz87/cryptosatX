"""
Real-time Market Indicators for Smart Money Monitoring

Provides advanced real-time indicators for detecting whale activity:
- Volume spike detection (configurable threshold)
- Bid/Ask pressure monitoring
- Whale wall detection (large orderbook imbalances)
- OI correlation analysis (OI vs Price movement)
- Break of Structure (BOS) validation with volume

Author: CryptoSatX Engineering Team
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import statistics

from app.utils.logger import default_logger


class RealtimeIndicators:
    """
    Real-time market indicators for whale activity detection

    Monitors:
    - Volume spikes (e.g., 1.8x above average)
    - Bid/Ask pressure imbalances
    - Whale walls in orderbook
    - OI vs Price correlation
    """

    def __init__(self):
        self.logger = default_logger

        # Configuration from environment
        self.volume_spike_threshold = float(os.getenv("VOLUME_SPIKE_THRESHOLD", "1.8"))
        self.bid_ask_threshold = float(os.getenv("BID_ASK_THRESHOLD", "55.0"))
        self.whale_wall_threshold = float(os.getenv("WHALE_WALL_THRESHOLD", "100000"))  # $100K
        self.oi_correlation_window = int(os.getenv("OI_CORRELATION_WINDOW", "24"))  # hours

        # Volume history cache (symbol -> deque of volumes)
        self.volume_history: Dict[str, deque] = {}
        self.volume_window_size = 20  # Keep last 20 data points for average

        self.logger.info("RealtimeIndicators initialized")
        self.logger.info(f"Volume spike threshold: {self.volume_spike_threshold}x")
        self.logger.info(f"Bid/Ask threshold: {self.bid_ask_threshold}%")

    async def detect_volume_spike(
        self,
        symbol: str,
        current_volume: float,
        comparison_volumes: Optional[List[float]] = None
    ) -> Dict:
        """
        Detect if current volume is significantly above average

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            current_volume: Current period volume
            comparison_volumes: Optional list of recent volumes for comparison
                               If not provided, uses cached history

        Returns:
            Dict with spike detection results:
            {
                "isSpike": bool,
                "currentVolume": float,
                "averageVolume": float,
                "ratio": float,  # current/average
                "threshold": float,
                "significance": str  # "normal", "moderate", "high", "extreme"
            }
        """
        try:
            # Initialize volume history for this symbol if needed
            if symbol not in self.volume_history:
                self.volume_history[symbol] = deque(maxlen=self.volume_window_size)

            # Use provided volumes or cached history
            if comparison_volumes:
                volumes = comparison_volumes
            else:
                volumes = list(self.volume_history[symbol])

            # Need at least 5 data points for reliable average
            if len(volumes) < 5:
                # Add current volume to history
                self.volume_history[symbol].append(current_volume)

                return {
                    "isSpike": False,
                    "currentVolume": current_volume,
                    "averageVolume": None,
                    "ratio": None,
                    "threshold": self.volume_spike_threshold,
                    "significance": "insufficient_data",
                    "message": "Need at least 5 data points for spike detection"
                }

            # Calculate average volume
            avg_volume = statistics.mean(volumes)

            # Avoid division by zero
            if avg_volume == 0:
                ratio = 0
            else:
                ratio = current_volume / avg_volume

            # Determine significance
            if ratio >= self.volume_spike_threshold * 2:
                significance = "extreme"  # 3.6x+ above average
            elif ratio >= self.volume_spike_threshold * 1.5:
                significance = "high"  # 2.7x+ above average
            elif ratio >= self.volume_spike_threshold:
                significance = "moderate"  # 1.8x+ above average
            else:
                significance = "normal"

            is_spike = ratio >= self.volume_spike_threshold

            # Update volume history
            self.volume_history[symbol].append(current_volume)

            return {
                "isSpike": is_spike,
                "currentVolume": current_volume,
                "averageVolume": avg_volume,
                "ratio": ratio,
                "threshold": self.volume_spike_threshold,
                "significance": significance,
                "message": f"Volume is {ratio:.2f}x average" if avg_volume else "Normal volume"
            }

        except Exception as e:
            self.logger.error(f"Error detecting volume spike for {symbol}: {e}")
            return {
                "isSpike": False,
                "error": str(e)
            }

    async def analyze_bid_ask_pressure(
        self,
        symbol: str,
        orderbook_data: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze bid vs ask pressure from orderbook or trade data

        Args:
            symbol: Crypto symbol
            orderbook_data: Optional orderbook data with 'bids' and 'asks'
                           Format: {"bids": [[price, size], ...], "asks": [[price, size], ...]}

        Returns:
            Dict with pressure analysis:
            {
                "bidPressure": float,  # Percentage (0-100)
                "askPressure": float,  # Percentage (0-100)
                "dominantSide": str,   # "bid" or "ask"
                "isSignificant": bool, # True if above threshold
                "imbalanceRatio": float,  # bid/ask ratio
                "interpretation": str
            }
        """
        try:
            # If no orderbook data provided, fetch from CoinAPI or use trade data
            if not orderbook_data:
                # Placeholder - in real implementation, fetch from CoinAPI
                return {
                    "bidPressure": None,
                    "askPressure": None,
                    "dominantSide": None,
                    "isSignificant": False,
                    "message": "No orderbook data provided"
                }

            # Calculate bid and ask volumes
            bid_volume = sum(float(bid[1]) for bid in orderbook_data.get("bids", []))
            ask_volume = sum(float(ask[1]) for ask in orderbook_data.get("asks", []))

            total_volume = bid_volume + ask_volume

            if total_volume == 0:
                return {
                    "bidPressure": 0,
                    "askPressure": 0,
                    "dominantSide": None,
                    "isSignificant": False,
                    "message": "No volume in orderbook"
                }

            # Calculate percentages
            bid_pressure = (bid_volume / total_volume) * 100
            ask_pressure = (ask_volume / total_volume) * 100

            # Determine dominant side
            dominant_side = "bid" if bid_pressure > ask_pressure else "ask"

            # Check if significant
            is_significant = bid_pressure >= self.bid_ask_threshold or ask_pressure >= self.bid_ask_threshold

            # Calculate imbalance ratio
            imbalance_ratio = bid_volume / ask_volume if ask_volume > 0 else float('inf')

            # Interpretation
            if bid_pressure >= 65:
                interpretation = "Strong buying pressure - institutions accumulating"
            elif ask_pressure >= 65:
                interpretation = "Strong selling pressure - institutions distributing"
            elif bid_pressure >= 55:
                interpretation = "Moderate buying pressure"
            elif ask_pressure >= 55:
                interpretation = "Moderate selling pressure"
            else:
                interpretation = "Balanced orderbook - no clear pressure"

            return {
                "bidPressure": round(bid_pressure, 2),
                "askPressure": round(ask_pressure, 2),
                "dominantSide": dominant_side,
                "isSignificant": is_significant,
                "imbalanceRatio": round(imbalance_ratio, 2),
                "interpretation": interpretation,
                "threshold": self.bid_ask_threshold
            }

        except Exception as e:
            self.logger.error(f"Error analyzing bid/ask pressure for {symbol}: {e}")
            return {
                "error": str(e)
            }

    async def detect_whale_walls(
        self,
        symbol: str,
        orderbook_data: Optional[Dict] = None,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        Detect large buy/sell walls in orderbook (whale positions)

        Args:
            symbol: Crypto symbol
            orderbook_data: Orderbook with bids/asks
            current_price: Current market price

        Returns:
            Dict with whale wall detection:
            {
                "hasWhaleWalls": bool,
                "buyWalls": List[Dict],  # Large bid walls
                "sellWalls": List[Dict], # Large ask walls
                "nearestBuyWall": Dict,
                "nearestSellWall": Dict,
                "interpretation": str
            }
        """
        try:
            if not orderbook_data or not current_price:
                return {
                    "hasWhaleWalls": False,
                    "message": "Insufficient data for whale wall detection"
                }

            buy_walls = []
            sell_walls = []

            # Analyze bids for buy walls
            for bid in orderbook_data.get("bids", []):
                price = float(bid[0])
                size = float(bid[1])
                value_usd = price * size

                if value_usd >= self.whale_wall_threshold:
                    buy_walls.append({
                        "price": price,
                        "size": size,
                        "valueUsd": value_usd,
                        "distanceFromPrice": ((current_price - price) / current_price) * 100
                    })

            # Analyze asks for sell walls
            for ask in orderbook_data.get("asks", []):
                price = float(ask[0])
                size = float(ask[1])
                value_usd = price * size

                if value_usd >= self.whale_wall_threshold:
                    sell_walls.append({
                        "price": price,
                        "size": size,
                        "valueUsd": value_usd,
                        "distanceFromPrice": ((price - current_price) / current_price) * 100
                    })

            # Sort by distance from current price
            buy_walls.sort(key=lambda x: x["distanceFromPrice"])
            sell_walls.sort(key=lambda x: x["distanceFromPrice"])

            # Nearest walls
            nearest_buy_wall = buy_walls[0] if buy_walls else None
            nearest_sell_wall = sell_walls[0] if sell_walls else None

            # Interpretation
            has_whale_walls = len(buy_walls) > 0 or len(sell_walls) > 0

            if len(buy_walls) > len(sell_walls) * 2:
                interpretation = "Strong buy-side support - whales defending price"
            elif len(sell_walls) > len(buy_walls) * 2:
                interpretation = "Heavy sell-side resistance - whales capping price"
            elif has_whale_walls:
                interpretation = "Whale walls detected on both sides - consolidation"
            else:
                interpretation = "No significant whale walls detected"

            return {
                "hasWhaleWalls": has_whale_walls,
                "buyWalls": buy_walls[:5],  # Top 5 buy walls
                "sellWalls": sell_walls[:5],  # Top 5 sell walls
                "nearestBuyWall": nearest_buy_wall,
                "nearestSellWall": nearest_sell_wall,
                "totalBuyWalls": len(buy_walls),
                "totalSellWalls": len(sell_walls),
                "interpretation": interpretation,
                "threshold": self.whale_wall_threshold
            }

        except Exception as e:
            self.logger.error(f"Error detecting whale walls for {symbol}: {e}")
            return {
                "hasWhaleWalls": False,
                "error": str(e)
            }

    async def analyze_oi_price_correlation(
        self,
        symbol: str,
        oi_change: float,
        price_change: float
    ) -> Dict:
        """
        Analyze correlation between Open Interest and Price movement

        Key patterns:
        - OI ↑ + Price ↑ = Bullish continuation (new longs opening)
        - OI ↑ + Price ↓ = Bearish trap setup (longs getting trapped)
        - OI ↓ + Price ↑ = Short squeeze (shorts closing)
        - OI ↓ + Price ↓ = Long liquidation (longs closing)

        Args:
            symbol: Crypto symbol
            oi_change: Open Interest change percentage
            price_change: Price change percentage

        Returns:
            Dict with correlation analysis:
            {
                "pattern": str,
                "signal": str,  # "bullish", "bearish", "neutral"
                "strength": str,  # "weak", "moderate", "strong"
                "interpretation": str,
                "recommendation": str
            }
        """
        try:
            # Thresholds for significance
            oi_threshold = 2.0  # 2% OI change is significant
            price_threshold = 1.0  # 1% price change is significant

            # Determine OI direction
            oi_rising = oi_change > oi_threshold
            oi_falling = oi_change < -oi_threshold
            oi_neutral = not oi_rising and not oi_falling

            # Determine price direction
            price_rising = price_change > price_threshold
            price_falling = price_change < -price_threshold
            price_neutral = not price_rising and not price_falling

            # Pattern recognition
            if oi_rising and price_rising:
                pattern = "OI Rising + Price Rising"
                signal = "bullish"
                strength = "strong" if abs(oi_change) > 5 and abs(price_change) > 3 else "moderate"
                interpretation = "Bullish continuation - New long positions opening"
                recommendation = "Consider adding to longs - momentum confirmed"

            elif oi_rising and price_falling:
                pattern = "OI Rising + Price Falling"
                signal = "bearish"
                strength = "strong" if abs(oi_change) > 5 and abs(price_change) > 3 else "moderate"
                interpretation = "Bearish trap - Longs getting trapped, potential liquidation cascade"
                recommendation = "Avoid longs - consider shorts"

            elif oi_falling and price_rising:
                pattern = "OI Falling + Price Rising"
                signal = "bullish"
                strength = "moderate"
                interpretation = "Short squeeze - Shorts being forced to close"
                recommendation = "Cautious longs - may be short-covering rally"

            elif oi_falling and price_falling:
                pattern = "OI Falling + Price Falling"
                signal = "bearish"
                strength = "moderate"
                interpretation = "Long liquidation - Longs being closed/liquidated"
                recommendation = "Wait for capitulation bottom before entry"

            elif oi_neutral and price_rising:
                pattern = "OI Stable + Price Rising"
                signal = "neutral"
                strength = "weak"
                interpretation = "Spot-driven rally - No new leverage positions"
                recommendation = "Organic move but limited momentum"

            elif oi_neutral and price_falling:
                pattern = "OI Stable + Price Falling"
                signal = "neutral"
                strength = "weak"
                interpretation = "Spot-driven selloff - No forced liquidations"
                recommendation = "Organic correction, may find support"

            else:
                pattern = "OI Neutral + Price Neutral"
                signal = "neutral"
                strength = "weak"
                interpretation = "Consolidation - No clear directional bias"
                recommendation = "Wait for breakout with OI confirmation"

            return {
                "pattern": pattern,
                "signal": signal,
                "strength": strength,
                "interpretation": interpretation,
                "recommendation": recommendation,
                "oiChange": round(oi_change, 2),
                "priceChange": round(price_change, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing OI correlation for {symbol}: {e}")
            return {
                "error": str(e)
            }

    async def validate_bos_with_volume(
        self,
        symbol: str,
        bos_detected: bool,
        bos_price: float,
        volume_spike_data: Dict
    ) -> Dict:
        """
        Validate Break of Structure (BOS) with volume confirmation

        A valid BOS should be accompanied by volume spike for confirmation

        Args:
            symbol: Crypto symbol
            bos_detected: Whether BOS was detected
            bos_price: Price level where BOS occurred
            volume_spike_data: Result from detect_volume_spike()

        Returns:
            Dict with BOS validation:
            {
                "isValidBOS": bool,
                "bosDetected": bool,
                "volumeConfirmed": bool,
                "confidence": str,  # "high", "medium", "low"
                "recommendation": str
            }
        """
        try:
            if not bos_detected:
                return {
                    "isValidBOS": False,
                    "bosDetected": False,
                    "volumeConfirmed": False,
                    "confidence": "none",
                    "recommendation": "No BOS detected"
                }

            volume_confirmed = volume_spike_data.get("isSpike", False)
            volume_significance = volume_spike_data.get("significance", "normal")

            # Determine confidence level
            if volume_confirmed and volume_significance == "extreme":
                confidence = "very_high"
                recommendation = "Strong BOS confirmation - High probability move"
            elif volume_confirmed and volume_significance == "high":
                confidence = "high"
                recommendation = "BOS confirmed with strong volume - Valid breakout"
            elif volume_confirmed and volume_significance == "moderate":
                confidence = "medium"
                recommendation = "BOS with moderate volume - Monitor for follow-through"
            else:
                confidence = "low"
                recommendation = "BOS without volume confirmation - Possible fakeout"

            is_valid_bos = volume_confirmed

            return {
                "isValidBOS": is_valid_bos,
                "bosDetected": bos_detected,
                "volumeConfirmed": volume_confirmed,
                "confidence": confidence,
                "volumeSignificance": volume_significance,
                "volumeRatio": volume_spike_data.get("ratio"),
                "recommendation": recommendation,
                "bosPrice": bos_price,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error validating BOS for {symbol}: {e}")
            return {
                "isValidBOS": False,
                "error": str(e)
            }


# Singleton instance
realtime_indicators = RealtimeIndicators()
