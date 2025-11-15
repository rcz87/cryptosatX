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
from app.utils.logger import logger


class SmartMoneyService:
    """Service for detecting whale accumulation/distribution patterns"""

    # Comprehensive list of coins to scan (30+ coins)
    SCAN_LIST = [
        # Major Caps
        "BTC",
        "ETH",
        "BNB",
        "SOL",
        "XRP",
        "ADA",
        "AVAX",
        "DOT",
        "MATIC",
        "LINK",
        # DeFi Tokens
        "UNI",
        "AAVE",
        "CRV",
        "SUSHI",
        "MKR",
        "COMP",
        "SNX",
        # Layer 1/2
        "ATOM",
        "NEAR",
        "FTM",
        "ARB",
        "OP",
        "APT",
        "SUI",
        # Popular Alts
        "DOGE",
        "SHIB",
        "PEPE",
        "LTC",
        "BCH",
        "ETC",
        # Gaming/Metaverse
        "SAND",
        "MANA",
        "AXS",
        "GALA",
        # Others
        "XLM",
        "ALGO",
        "VET",
        "HBAR",
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
            logger.error(f"Error fetching {symbol}: {str(e)}")
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
        buy_pressure = (
            data.get("coinAPIMetrics", {}).get("trades", {}).get("buyPressure", 0)
        )
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
                reasons.append(
                    f"Very low social activity ({social_score:.1f}) - retail unaware"
                )
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
        sell_pressure = (
            data.get("coinAPIMetrics", {}).get("trades", {}).get("sellPressure", 0)
        )
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
            reasons.append(
                f"Very high funding ({funding_rate:.3f}%) - longs overcrowded"
            )
        elif funding_rate > 0.3:
            score += 1
            reasons.append(f"High funding ({funding_rate:.3f}%) - retail longing")

        # Social Activity (0-2 points) - Higher is worse (retail FOMO)
        # Only score if data is available (not None)
        if social_score is not None:
            if social_score > 70:
                score += 2
                reasons.append(
                    f"Very high social activity ({social_score:.1f}) - retail FOMO"
                )
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
        coins: Optional[List[str]] = None,
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
                "dominantPattern": (
                    "accumulation" if accum_score > dist_score else "distribution"
                ),
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
                "neutralCoins": len(neutral_coins),
            },
            "accumulation": accumulation_signals,
            "distribution": distribution_signals,
            "neutral": (
                neutral_coins[:5] if neutral_coins else []
            ),  # Only return top 5 neutral
            "failed": failed_coins,
        }

    async def scan_smart_money(
        self,
        coins: Optional[str] = None,
        min_accumulation_score: int = 5,
        min_distribution_score: int = 5,
    ) -> Dict:
        """
        Scan smart money patterns (alias for scan_markets for compatibility)

        Args:
            coins: Comma-separated string of coins to scan
            min_accumulation_score: Minimum accumulation score
            min_distribution_score: Minimum distribution score

        Returns:
            Dict with scan results
        """
        # Parse coins string to list if provided
        coin_list = None
        if coins:
            coin_list = [coin.strip().upper() for coin in coins.split(",")]

        return await self.scan_markets(
            min_accumulation_score=min_accumulation_score,
            min_distribution_score=min_distribution_score,
            coins=coin_list,
        )

    async def find_accumulation_coins(
        self, min_score: int = 6, exclude_overbought: bool = True
    ) -> Dict:
        """
        Find coins with strong accumulation patterns

        Args:
            min_score: Minimum accumulation score (default 6)
            exclude_overbought: Exclude coins that are overbought

        Returns:
            Dict with accumulation opportunities
        """
        # Scan all coins
        scan_result = await self.scan_markets(min_accumulation_score=min_score)

        if not scan_result.get("success"):
            return scan_result

        accumulation_coins = scan_result.get("accumulation", [])

        # Filter out overbought coins if requested
        if exclude_overbought:
            accumulation_coins = [
                coin
                for coin in accumulation_coins
                if coin.get("compositeScore", 0) < 75  # Not overbought
            ]

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "totalCoins": len(accumulation_coins),
            "minScore": min_score,
            "excludeOverbought": exclude_overbought,
            "accumulation_coins": accumulation_coins,
            "summary": {
                "high_confidence": len(
                    [
                        c
                        for c in accumulation_coins
                        if c.get("accumulationScore", 0) >= 8
                    ]
                ),
                "medium_confidence": len(
                    [
                        c
                        for c in accumulation_coins
                        if 6 <= c.get("accumulationScore", 0) < 8
                    ]
                ),
                "total_opportunities": len(accumulation_coins),
            },
        }

    # ==================== NEW METHODS - EXTENDED FUNCTIONALITY ====================
    
    async def analyze_any_coin(self, symbol: str) -> Dict:
        """
        Analyze ANY coin dynamically (not limited to SCAN_LIST)
        
        Args:
            symbol: Coin symbol to analyze (e.g., 'PEPE', 'WIF', 'BONK')
            
        Returns:
            Complete smart money analysis for the coin
        """
        try:
            # Fetch signal data
            data = await self._fetch_signal_data(symbol)
            
            if not data:
                return {
                    "success": False,
                    "symbol": symbol.upper(),
                    "error": "Could not fetch data for this coin. It may not be supported or data is unavailable."
                }
            
            # Calculate scores
            accum_score, accum_reasons = self._calculate_accumulation_score(data)
            dist_score, dist_reasons = self._calculate_distribution_score(data)
            
            # Determine dominant pattern
            if accum_score > dist_score:
                pattern = "accumulation"
                score = accum_score
                reasons = accum_reasons
            elif dist_score > accum_score:
                pattern = "distribution"
                score = dist_score
                reasons = dist_reasons
            else:
                pattern = "neutral"
                score = max(accum_score, dist_score)
                reasons = []
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "analysis": {
                    "price": data.get("price", 0),
                    "signal": data.get("signal", "NEUTRAL"),
                    "compositeScore": data.get("score", 0),
                    "accumulationScore": accum_score,
                    "distributionScore": dist_score,
                    "dominantPattern": pattern,
                    "patternScore": score,
                    "reasons": reasons,
                    "interpretation": self._get_interpretation(pattern, score)
                },
                "metrics": {
                    "fundingRate": data.get("metrics", {}).get("fundingRate", 0),
                    "openInterest": data.get("metrics", {}).get("openInterest", 0),
                    "volume24h": data.get("metrics", {}).get("volume24h", 0),
                    "priceChange24h": data.get("metrics", {}).get("priceChange24h", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "symbol": symbol.upper(),
                "error": str(e)
            }
    
    def _get_interpretation(self, pattern: str, score: int) -> str:
        """Get human-readable interpretation of pattern and score"""
        if pattern == "accumulation":
            if score >= 8:
                return "⭐⭐⭐ VERY STRONG ACCUMULATION - Whales buying aggressively before retail"
            elif score >= 6:
                return "⭐ STRONG ACCUMULATION - Good opportunity before potential pump"
            elif score >= 4:
                return "MODERATE ACCUMULATION - Early signs of whale interest"
            else:
                return "WEAK ACCUMULATION - Monitor for confirmation"
        elif pattern == "distribution":
            if score >= 8:
                return "🚨 VERY STRONG DISTRIBUTION - Whales dumping, avoid/short"
            elif score >= 6:
                return "⚠️ STRONG DISTRIBUTION - Risk of dump, consider exit"
            elif score >= 4:
                return "MODERATE DISTRIBUTION - Whales taking profits"
            else:
                return "WEAK DISTRIBUTION - Monitor trend"
        else:
            return "NEUTRAL - No clear pattern detected"
    
    async def discover_new_coins(
        self,
        max_market_cap: float = 100000000,  # $100M
        min_volume: float = 500000,  # $500K
        source: str = "all",  # 'binance', 'coingecko', 'all'
        limit: int = 30
    ) -> Dict:
        """
        Discover new/small cap coins from multiple sources
        
        Args:
            max_market_cap: Maximum market cap in USD (default $100M)
            min_volume: Minimum 24h volume in USD (default $500K)
            source: Data source ('binance', 'coingecko', 'all')
            limit: Maximum number of results
            
        Returns:
            List of discovered coins with basic analysis
        """
        try:
            from app.services.binance_futures_service import binance_futures_service
            from app.services.coingecko_service import coingecko_service
            
            discovered_coins = []
            
            # Fetch from CoinGecko if requested
            if source in ["coingecko", "all"]:
                cg_coins = await coingecko_service.discover_small_cap_coins(
                    max_market_cap=max_market_cap,
                    min_volume=min_volume,
                    limit=limit
                )
                
                for coin in cg_coins:
                    discovered_coins.append({
                        "symbol": coin["symbol"],
                        "name": coin["name"],
                        "price": coin["price"],
                        "marketCap": coin["marketCap"],
                        "volume24h": coin["volume24h"],
                        "priceChange24h": coin["priceChange24h"],
                        "source": "coingecko",
                        "hasFutures": False  # Will check later
                    })
            
            # Fetch from Binance Futures if requested
            if source in ["binance", "all"]:
                bf_coins = await binance_futures_service.filter_coins_by_criteria(
                    min_volume_usdt=min_volume,
                    limit=limit
                )
                
                for coin in bf_coins:
                    # Check if already in list from CoinGecko
                    existing = next((c for c in discovered_coins if c["symbol"] == coin["symbol"]), None)
                    
                    if existing:
                        existing["hasFutures"] = True
                        existing["source"] = "both"
                    else:
                        discovered_coins.append({
                            "symbol": coin["symbol"],
                            "name": coin["symbol"],
                            "price": coin["price"],
                            "marketCap": 0,  # Not available from Binance
                            "volume24h": coin["volume24h"],
                            "priceChange24h": coin["priceChange24h"],
                            "source": "binance_futures",
                            "hasFutures": True
                        })
            
            # Sort by volume
            discovered_coins.sort(key=lambda x: x["volume24h"], reverse=True)
            
            return {
                "success": True,
                "totalFound": len(discovered_coins),
                "filters": {
                    "maxMarketCap": max_market_cap,
                    "minVolume": min_volume,
                    "source": source
                },
                "coins": discovered_coins[:limit],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_futures_coins_list(self, min_volume: float = 1000000) -> Dict:
        """
        Get list of all coins available on Binance Futures
        
        Args:
            min_volume: Minimum 24h volume filter (default $1M)
            
        Returns:
            List of futures symbols with volume data
        """
        try:
            from app.services.binance_futures_service import binance_futures_service
            
            # Get all perpetual symbols
            symbols = await binance_futures_service.get_all_perpetual_symbols()
            
            if not symbols:
                return {
                    "success": False,
                    "error": "Could not fetch futures symbols"
                }
            
            # Get 24hr stats for all symbols
            tickers = await binance_futures_service.get_24hr_ticker()
            
            if not tickers.get("success"):
                return {
                    "success": False,
                    "error": "Could not fetch ticker data"
                }
            
            # Filter and format
            coins = []
            for ticker in tickers.get("data", []):
                symbol = ticker.get("symbol", "")
                volume = float(ticker.get("quoteVolume", 0))
                
                if volume < min_volume:
                    continue
                
                coins.append({
                    "symbol": symbol,
                    "price": float(ticker.get("lastPrice", 0)),
                    "volume24h": volume,
                    "priceChange24h": float(ticker.get("priceChangePercent", 0)),
                    "high24h": float(ticker.get("highPrice", 0)),
                    "low24h": float(ticker.get("lowPrice", 0))
                })
            
            # Sort by volume
            coins.sort(key=lambda x: x["volume24h"], reverse=True)
            
            return {
                "success": True,
                "totalSymbols": len(symbols),
                "filteredCount": len(coins),
                "minVolume": min_volume,
                "coins": coins,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def auto_select_coins(
        self,
        criteria: str = "volume",  # 'volume', 'gainers', 'losers', 'small_cap'
        limit: int = 20
    ) -> Dict:
        """
        Auto-select coins based on criteria
        
        Args:
            criteria: Selection criteria
                - 'volume': Highest volume coins
                - 'gainers': Top gainers 24h
                - 'losers': Top losers 24h (for short opportunities)
                - 'small_cap': Small cap with decent volume
            limit: Number of coins to return
            
        Returns:
            Selected coins for scanning
        """
        try:
            from app.services.binance_futures_service import binance_futures_service
            
            if criteria == "small_cap":
                # Use CoinGecko for small caps
                from app.services.coingecko_service import coingecko_service
                
                small_caps = await coingecko_service.discover_small_cap_coins(
                    max_market_cap=100000000,  # $100M
                    min_volume=100000,  # $100K
                    limit=limit
                )
                
                coins = [c["symbol"] for c in small_caps]
                
            else:
                # Use Binance Futures for other criteria
                if criteria == "volume":
                    min_price_change = None
                    sort_key = "volume24h"
                elif criteria == "gainers":
                    min_price_change = 5.0  # +5% minimum
                    sort_key = "priceChange24h"
                elif criteria == "losers":
                    min_price_change = -5.0  # -5% minimum
                    sort_key = "priceChange24h"
                else:
                    min_price_change = None
                    sort_key = "volume24h"
                
                bf_coins = await binance_futures_service.filter_coins_by_criteria(
                    min_volume_usdt=1000000,  # $1M volume
                    min_price_change_percent=min_price_change,
                    limit=limit
                )
                
                # Extract symbols
                coins = [c["symbol"].replace("USDT", "") for c in bf_coins]
            
            return {
                "success": True,
                "criteria": criteria,
                "selectedCoins": coins,
                "count": len(coins),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
smart_money_service = SmartMoneyService()
