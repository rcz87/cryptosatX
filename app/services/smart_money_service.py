"""
Smart Money Scanner Service

Detects whale accumulation and distribution patterns across multiple cryptocurrencies.
Scans 30+ coins to identify opportunities before retail traders enter/exit.

Key Metrics for Detection:
- Accumulation: High buy pressure + low funding + low social + sideways price
- Distribution: High sell pressure + high funding + high social + recent pump
"""

import asyncio
from typing import Dict, List, Optional
import httpx
from datetime import datetime


class SmartMoneyService:
    """Service for detecting whale accumulation/distribution patterns"""
    
    # Comprehensive list of coins to scan (30+ coins)
    SCAN_LIST = [
        # Major Caps
        "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOT", "MATIC", "LINK",
        # DeFi Tokens
        "UNI", "AAVE", "CRV", "SUSHI", "MKR", "COMP", "SNX",
        # Layer 1/2
        "ATOM", "NEAR", "FTM", "ARB", "OP", "APT", "SUI",
        # Popular Alts
        "DOGE", "SHIB", "PEPE", "LTC", "BCH", "ETC",
        # Gaming/Metaverse
        "SAND", "MANA", "AXS", "GALA",
        # Others
        "XLM", "ALGO", "VET", "HBAR"
    ]
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def _fetch_signal_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch signal data for a single coin
        
        Args:
            symbol: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal data dict or None if failed
        """
        try:
            response = await self.client.get(f"{self.base_url}/signals/{symbol}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None
    
    def _calculate_accumulation_score(self, data: Dict) -> tuple[int, List[str]]:
        """
        Calculate accumulation score (0-10)
        Higher score = stronger accumulation signal
        
        Accumulation indicators:
        - High buy pressure (whale buying)
        - Low funding rate (not crowded)
        - Low social activity (retail not aware)
        - Sideways price action (no pump yet)
        - Rising open interest (new positions)
        
        Returns:
            (score, reasons list)
        """
        score = 0
        reasons = []
        
        # Extract metrics
        buy_pressure = data.get("coinAPIMetrics", {}).get("trades", {}).get("buyPressure", 0)
        funding_rate = data.get("metrics", {}).get("fundingRate", 0) * 100
        
        # Handle missing social data (None = unavailable, treat as neutral, don't score)
        lc_metrics = data.get("lunarCrushMetrics", {}).get("momentum", {})
        social_score = lc_metrics.get("momentumScore")
        if social_score is None or social_score == 0:
            social_score = None  # Explicitly mark as unavailable
        
        price_changes = data.get("comprehensiveMetrics", {}).get("priceChanges", {})
        price_4h = price_changes.get("4h", 0)
        price_24h = price_changes.get("24h", 0)
        
        # Buy Pressure (0-3 points)
        if buy_pressure > 80:
            score += 3
            reasons.append(f"Very high buy pressure ({buy_pressure:.1f}%)")
        elif buy_pressure > 65:
            score += 2
            reasons.append(f"High buy pressure ({buy_pressure:.1f}%)")
        elif buy_pressure > 55:
            score += 1
            reasons.append(f"Moderate buy pressure ({buy_pressure:.1f}%)")
        
        # Funding Rate (0-2 points) - Lower is better for accumulation
        if funding_rate < 0:
            score += 2
            reasons.append(f"Negative funding ({funding_rate:.3f}%) - very quiet")
        elif funding_rate < 0.1:
            score += 1
            reasons.append(f"Low funding ({funding_rate:.3f}%) - not crowded")
        
        # Social Activity (0-2 points) - Lower is better (retail not aware yet)
        # Only score if data is available (not None)
        if social_score is not None:
            if social_score < 30:
                score += 2
                reasons.append(f"Very low social activity ({social_score:.1f}) - retail unaware")
            elif social_score < 45:
                score += 1
                reasons.append(f"Low social activity ({social_score:.1f})")
        else:
            # Social data unavailable - neutral, no points awarded
            pass
        
        # Price Action (0-2 points) - Sideways is ideal
        if abs(price_4h) < 1.5 and abs(price_24h) < 3:
            score += 2
            reasons.append("Sideways price action - no pump yet")
        elif abs(price_4h) < 3:
            score += 1
            reasons.append("Relatively stable price")
        
        # Trend confirmation (0-1 point)
        if price_24h > 0 and price_24h < 5:
            score += 1
            reasons.append("Mild uptrend - healthy accumulation")
        
        return score, reasons
    
    def _calculate_distribution_score(self, data: Dict) -> tuple[int, List[str]]:
        """
        Calculate distribution score (0-10)
        Higher score = stronger distribution signal
        
        Distribution indicators:
        - High sell pressure (whale selling)
        - High funding rate (longs crowded)
        - High social activity (retail FOMO)
        - Recent price pump (top formation)
        - Declining open interest (positions closing)
        
        Returns:
            (score, reasons list)
        """
        score = 0
        reasons = []
        
        # Extract metrics
        sell_pressure = data.get("coinAPIMetrics", {}).get("trades", {}).get("sellPressure", 0)
        funding_rate = data.get("metrics", {}).get("fundingRate", 0) * 100
        
        # Handle missing social data (None = unavailable, treat as neutral, don't score)
        lc_metrics = data.get("lunarCrushMetrics", {}).get("momentum", {})
        social_score = lc_metrics.get("momentumScore")
        if social_score is None or social_score == 0:
            social_score = None  # Explicitly mark as unavailable
        
        price_changes = data.get("comprehensiveMetrics", {}).get("priceChanges", {})
        price_4h = price_changes.get("4h", 0)
        price_24h = price_changes.get("24h", 0)
        
        # Sell Pressure (0-3 points)
        if sell_pressure > 80:
            score += 3
            reasons.append(f"Very high sell pressure ({sell_pressure:.1f}%)")
        elif sell_pressure > 65:
            score += 2
            reasons.append(f"High sell pressure ({sell_pressure:.1f}%)")
        elif sell_pressure > 55:
            score += 1
            reasons.append(f"Moderate sell pressure ({sell_pressure:.1f}%)")
        
        # Funding Rate (0-2 points) - Higher is worse (longs overcrowded)
        if funding_rate > 0.5:
            score += 2
            reasons.append(f"Very high funding ({funding_rate:.3f}%) - longs overcrowded")
        elif funding_rate > 0.3:
            score += 1
            reasons.append(f"High funding ({funding_rate:.3f}%) - retail longing")
        
        # Social Activity (0-2 points) - Higher is worse (retail FOMO)
        # Only score if data is available (not None)
        if social_score is not None:
            if social_score > 70:
                score += 2
                reasons.append(f"Very high social activity ({social_score:.1f}) - retail FOMO")
            elif social_score > 55:
                score += 1
                reasons.append(f"High social activity ({social_score:.1f})")
        else:
            # Social data unavailable - neutral, no points awarded
            pass
        
        # Recent Pump (0-2 points) - Distribution after pump
        if price_24h > 15:
            score += 2
            reasons.append(f"Large pump ({price_24h:+.1f}% 24h) - potential top")
        elif price_24h > 8:
            score += 1
            reasons.append(f"Recent pump ({price_24h:+.1f}% 24h)")
        
        # Momentum shift (0-1 point) - Price declining after pump
        if price_24h > 5 and price_4h < 0:
            score += 1
            reasons.append("Momentum shifting - pump losing steam")
        
        return score, reasons
    
    async def scan_markets(
        self,
        min_accumulation_score: int = 5,
        min_distribution_score: int = 5,
        coins: Optional[List[str]] = None
    ) -> Dict:
        """
        Scan multiple markets for smart money patterns
        
        Args:
            min_accumulation_score: Minimum score to flag accumulation (default 5)
            min_distribution_score: Minimum score to flag distribution (default 5)
            coins: Optional list of coins to scan (uses SCAN_LIST if None)
            
        Returns:
            Dict with accumulation and distribution signals
        """
        target_coins = coins if coins else self.SCAN_LIST
        
        # Fetch all signal data concurrently
        tasks = [self._fetch_signal_data(symbol) for symbol in target_coins]
        results = await asyncio.gather(*tasks)
        
        accumulation_signals = []
        distribution_signals = []
        neutral_coins = []
        failed_coins = []
        
        for i, symbol in enumerate(target_coins):
            data = results[i]
            
            if not data:
                failed_coins.append(symbol)
                continue
            
            # Calculate scores
            accum_score, accum_reasons = self._calculate_accumulation_score(data)
            dist_score, dist_reasons = self._calculate_distribution_score(data)
            
            # Get basic info
            price = data.get("price", 0)
            signal_type = data.get("signal", "NEUTRAL")
            composite_score = data.get("score", 0)
            
            coin_info = {
                "symbol": symbol,
                "price": price,
                "signalType": signal_type,
                "compositeScore": composite_score,
                "accumulationScore": accum_score,
                "distributionScore": dist_score,
                "dominantPattern": "accumulation" if accum_score > dist_score else "distribution"
            }
            
            # Categorize based on scores
            if accum_score >= min_accumulation_score and accum_score > dist_score:
                coin_info["reasons"] = accum_reasons
                accumulation_signals.append(coin_info)
            elif dist_score >= min_distribution_score and dist_score > accum_score:
                coin_info["reasons"] = dist_reasons
                distribution_signals.append(coin_info)
            else:
                coin_info["reasons"] = []
                neutral_coins.append(coin_info)
        
        # Sort by score (highest first)
        accumulation_signals.sort(key=lambda x: x["accumulationScore"], reverse=True)
        distribution_signals.sort(key=lambda x: x["distributionScore"], reverse=True)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "coinsScanned": len(target_coins),
            "coinsSuccessful": len(target_coins) - len(failed_coins),
            "coinsFailed": len(failed_coins),
            "summary": {
                "accumulationSignals": len(accumulation_signals),
                "distributionSignals": len(distribution_signals),
                "neutralCoins": len(neutral_coins)
            },
            "accumulation": accumulation_signals,
            "distribution": distribution_signals,
            "neutral": neutral_coins[:5] if neutral_coins else [],  # Only return top 5 neutral
            "failed": failed_coins
        }


# Singleton instance
smart_money_service = SmartMoneyService()
