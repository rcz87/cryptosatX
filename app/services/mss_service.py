"""
MSS (Multimodal Signal Score) Service

Orchestrates 3-phase analysis for high-potential crypto asset discovery:
- Phase 1: Discovery via CoinGecko + Binance
- Phase 2: Social Confirmation via LunarCrush + Volume analysis
- Phase 3: Institutional Validation via OI + Whale detection

Reuses all existing services for data collection.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.core.mss_engine import MSSEngine
from app.services.coingecko_service import CoinGeckoService
from app.services.binance_futures_service import BinanceFuturesService
from app.services.lunarcrush_service import LunarCrushService
from app.services.coinglass_service import CoinglassService
from app.services.coinglass_premium_service import CoinglassPremiumService
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService

logger = logging.getLogger(__name__)


class MSSService:
    """
    MSS Service orchestrator that combines multiple data sources
    for alpha generation through multi-modal signal analysis.
    """

    def __init__(self):
        """Initialize MSS Service with all required components"""
        self.mss_engine = MSSEngine()
        self.coingecko = CoinGeckoService()
        self.binance = BinanceFuturesService()
        self.lunarcrush = LunarCrushService()
        self.coinglass = CoinglassService()
        self.coinglass_premium = CoinglassPremiumService()
        self.coinglass_comprehensive = CoinglassComprehensiveService()
        self.coinapi_comprehensive = CoinAPIComprehensiveService()

        logger.info("MSS Service initialized with all data providers (Premium + Comprehensive)")

    async def close(self):
        """Close all HTTP clients"""
        await self.coingecko.close()
        await self.binance.close()
        await self.coinglass_premium.close()
        await self.coinglass_comprehensive.close()
        await self.coinapi_comprehensive.close()

    async def phase1_discovery(
        self,
        max_fdv_usd: float = 50_000_000,
        max_age_hours: float = 72,
        min_volume_24h: float = 100_000,
        limit: int = 50
    ) -> List[Dict]:
        """
        Phase 1: Discover new low-FDV coins

        Uses CoinGecko + Binance to find recently listed coins
        with low market cap and strong tokenomics potential.

        Args:
            max_fdv_usd: Maximum FDV threshold
            max_age_hours: Maximum age in hours
            min_volume_24h: Minimum 24h volume
            limit: Max results to return

        Returns:
            List of discovered coins with discovery scores
        """
        logger.info(
            f"Phase 1 Discovery: FDV<${max_fdv_usd:,.0f}, "
            f"Age<{max_age_hours}h, Vol>${min_volume_24h:,.0f}"
        )

        discovered_coins = []

        try:
            # ✅ PRIMARY: Coinglass futures markets (PREMIUM API - complete data!)
            all_cg_coins = {}
            
            logger.info("Fetching from Coinglass futures markets (premium API)...")
            coinglass_markets = await self.coinglass_comprehensive.get_coins_markets()
            
            if coinglass_markets.get("success"):
                markets_data = coinglass_markets.get("data", [])
                logger.info(f"✅ Coinglass: {len(markets_data)} futures coins")
                
                # Convert Coinglass format to standard format
                for coin in markets_data:
                    symbol = coin.get("symbol", "").upper()
                    if symbol:
                        # Coinglass provides OI and MC - use OI as volume proxy!
                        # OI represents institutional commitment = better signal than volume
                        oi_usd = coin.get("open_interest_usd", 0)
                        mc_usd = coin.get("market_cap_usd", 0)
                        
                        all_cg_coins[symbol] = {
                            "symbol": symbol,
                            "name": symbol,  # Coinglass doesn't return name, use symbol
                            "market_cap": mc_usd,
                            "fully_diluted_valuation": mc_usd,  # Use MC as FDV for futures
                            "total_volume": oi_usd,  # ✅ USE OI AS VOLUME PROXY (institutional money!)
                            "price": coin.get("current_price", 0),
                            # Bonus: OI data already mapped for Phase 3!
                            "open_interest_usd": oi_usd,
                            "funding_rate": coin.get("avg_funding_rate_by_oi", 0),
                            "price_change_24h": coin.get("price_change_percent_24h", 0),
                            "source": "coinglass"
                        }
                logger.info(f"✅ Coinglass mapped: {len(all_cg_coins)} coins with OI data")
            else:
                logger.warning(f"Coinglass failed: {coinglass_markets.get('error')}")
            
            # SECONDARY: CoinGecko markets (fallback/enrichment)
            try:
                logger.info("Fetching from CoinGecko markets for enrichment...")
                cg_markets = await self.coingecko.get_coins_markets(
                    vs_currency="usd",
                    order="volume_desc",
                    per_page=min(limit * 2, 50),
                    category=None
                )
                
                if cg_markets.get("success"):
                    for coin in cg_markets.get("data", []):
                        symbol = coin.get("symbol", "").upper()
                        if symbol and symbol not in all_cg_coins:
                            all_cg_coins[symbol] = coin
                    logger.info(f"✅ CoinGecko enrichment: added {len([c for c in cg_markets.get('data', []) if c.get('symbol', '').upper() not in all_cg_coins])} new coins")
            except Exception as e:
                logger.warning(f"CoinGecko enrichment failed (non-critical): {e}")
            
            # TERTIARY: Binance (if not geo-blocked)
            try:
                binance_symbols = await self.binance.filter_coins_by_criteria(
                    min_volume_usdt=min_volume_24h,
                    limit=limit
                )
                if binance_symbols:
                    logger.info(f"✅ Binance: {len(binance_symbols)} symbols")
            except Exception as e:
                logger.warning(f"Binance unavailable (expected if geo-blocked): {str(e)[:80]}")

            # Merge data sources and apply filters (relaxed for Coinglass)
            for symbol, cg_data in all_cg_coins.items():
                source = cg_data.get("source", "unknown")
                market_cap = cg_data.get("market_cap", 0) or cg_data.get("market_data", {}).get("market_cap", {}).get("usd", 0)
                volume_24h = cg_data.get("total_volume", {}).get("usd", 0) if isinstance(cg_data.get("total_volume"), dict) else cg_data.get("total_volume", 0)
                
                # Get FDV (fully diluted valuation) if available
                fdv = cg_data.get("fully_diluted_valuation", {}).get("usd") if isinstance(cg_data.get("fully_diluted_valuation"), dict) else cg_data.get("fully_diluted_valuation")
                if not fdv:
                    fdv = market_cap  # Fallback to market cap only if FDV unavailable

                # ✅ FLEXIBLE FILTERING: Coinglass coins (established) vs CoinGecko (new)
                if source == "coinglass":
                    # Coinglass = established futures markets, skip FDV/age filters
                    # Only check OI (used as volume) is meaningful
                    if volume_24h < 100_000:  # OI at least $100K (very low bar)
                        continue
                    age_hours = None  # No age data for established coins
                else:
                    # CoinGecko = apply strict discovery filters for new/small-cap
                    if not fdv or fdv > max_fdv_usd:
                        continue
                    if not volume_24h or volume_24h < min_volume_24h:
                        continue
                    age_hours = self._estimate_age_hours(cg_data)
                    if age_hours and age_hours > max_age_hours:
                        continue

                # Get circulating supply %
                total_supply = cg_data.get("total_supply", 0)
                circ_supply = cg_data.get("circulating_supply", 0)
                circ_pct = (circ_supply / total_supply * 100) if total_supply > 0 else None

                discovery_score, breakdown = self.mss_engine.calculate_discovery_score(
                    fdv_usd=fdv,
                    age_hours=age_hours,
                    circulating_supply_pct=circ_pct,
                    market_cap_usd=market_cap
                )

                # Include all Coinglass coins (established) + CoinGecko coins that PASS
                if source == "coinglass" or breakdown["status"] == "PASS":
                    discovered_coins.append({
                        "symbol": symbol,
                        "name": cg_data.get("name", symbol),
                        "fdv_usd": fdv,
                        "market_cap_usd": market_cap,
                        "volume_24h_usd": volume_24h,
                        "age_hours": age_hours,
                        "discovery_score": discovery_score,
                        "discovery_breakdown": breakdown,
                        "source": source,
                        # Coinglass bonus data
                        "open_interest_usd": cg_data.get("open_interest_usd"),
                        "funding_rate": cg_data.get("funding_rate")
                    })

            # SKIP Binance-only coins without FDV data (can't properly filter)
            # This ensures quality - only analyze coins with complete tokenomics data

            # Sort by discovery score
            discovered_coins.sort(key=lambda x: x.get("discovery_score", 0), reverse=True)

            logger.info(f"Phase 1 complete: {len(discovered_coins)} coins discovered")
            return discovered_coins[:limit]

        except Exception as e:
            logger.error(f"Phase 1 discovery error: {e}")
            return []

    async def phase2_confirmation(
        self,
        symbol: str,
        binance_data: Optional[Dict] = None
    ) -> Tuple[float, Dict]:
        """
        Phase 2: Confirm social momentum and volume spike

        Uses LunarCrush + CoinAPI Comprehensive to validate market interest,
        social engagement, and detect volume spikes from actual trade data.

        Args:
            symbol: Coin symbol to analyze
            binance_data: Optional pre-fetched Binance data (not used for volume)

        Returns:
            Tuple of (social_score, breakdown_dict)
        """
        logger.info(f"Phase 2 Confirmation: {symbol}")

        try:
            # Fetch data concurrently
            # Use CoinAPI Comprehensive for real volume analysis instead of Binance ticker
            tasks = [
                self.lunarcrush.get_market_data(symbol),
                self.coinapi_comprehensive.get_recent_trades(symbol, "BINANCE", 100),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            lc_data = results[0] if not isinstance(results[0], Exception) else {}
            trades_data = results[1] if not isinstance(results[1], Exception) else {}

            # Extract metrics from LunarCrush
            if isinstance(lc_data, dict):
                altrank = lc_data.get("data", {}).get("alt_rank")
                galaxy_score = lc_data.get("data", {}).get("galaxy_score")
                sentiment = lc_data.get("data", {}).get("average_sentiment")
            else:
                altrank, galaxy_score, sentiment = None, None, None

            # Extract VOLUME change from CoinAPI trade data
            # Calculate volume spike by comparing buy/sell pressure
            volume_change = 0
            if isinstance(trades_data, dict) and trades_data.get("success"):
                volume_info = trades_data.get("volume", {})
                buy_pressure = volume_info.get("buyPressure", 50.0)
                sell_pressure = volume_info.get("sellPressure", 50.0)
                
                # Volume spike detected when buy pressure significantly exceeds sell pressure
                # or when total volume is unusually high (buy + sell imbalance)
                if buy_pressure > 60:
                    # Strong buy pressure = volume spike upward
                    volume_change = (buy_pressure - 50) * 2  # Scale: 60% buy = 20% volume spike
                elif sell_pressure > 60:
                    # Strong sell pressure = volume spike downward
                    volume_change = -(sell_pressure - 50) * 2
                else:
                    # Balanced pressure = no significant volume spike
                    volume_change = 0
                
                logger.info(f"Phase 2 volume analysis: Buy {buy_pressure:.1f}%, Sell {sell_pressure:.1f}%, Spike: {volume_change:.1f}%")
            else:
                logger.warning(f"CoinAPI trade data unavailable for {symbol}, volume spike = 0")
                volume_change = 0

            # Calculate social score
            social_score, breakdown = self.mss_engine.calculate_social_score(
                altrank=altrank,
                galaxy_score=galaxy_score,
                sentiment_score=sentiment,
                volume_24h_change_pct=volume_change
            )

            logger.info(f"Phase 2 complete: {symbol} - Social score: {social_score:.2f}/35")
            return social_score, breakdown

        except Exception as e:
            logger.error(f"Phase 2 confirmation error for {symbol}: {e}")
            return 0.0, {"status": "ERROR", "error": str(e)}

    async def phase3_validation(
        self,
        symbol: str,
        binance_data: Optional[Dict] = None
    ) -> Tuple[float, Dict]:
        """
        Phase 3: Validate institutional positioning (ENHANCED with new data sources)

        Uses Coinglass Premium + Comprehensive endpoints for maximum whale detection:
        - OI trends & top trader ratios
        - Options OI (smart money hedging)
        - ETF flows (institutional sentiment)
        - Exchange reserves (whale movements)
        - CoinAPI trade data

        Args:
            symbol: Coin symbol to analyze
            binance_data: Optional pre-fetched Binance data

        Returns:
            Tuple of (validation_score, breakdown_dict)
        """
        logger.info(f"Phase 3 Validation (Enhanced): {symbol}")

        try:
            # Fetch data concurrently - include NEW comprehensive endpoints
            tasks = [
                # Existing Premium endpoints
                self.coinglass_premium.get_oi_trend(symbol),
                self.coinglass_premium.get_top_trader_ratio(symbol),
                self.binance.get_funding_rate(f"{symbol}USDT"),
                self.coinapi_comprehensive.get_recent_trades(symbol, "BINANCE", 100),
                
                # NEW: Comprehensive institutional tracking
                self.coinglass_comprehensive.get_options_open_interest(),
                self.coinglass_comprehensive.get_etf_flows(asset=symbol),
                self.coinglass_comprehensive.get_exchange_reserves(symbol=symbol),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            oi_trend_data = results[0] if not isinstance(results[0], Exception) else {}
            trader_data = results[1] if not isinstance(results[1], Exception) else {}
            funding_data = results[2] if not isinstance(results[2], Exception) else {}
            trades_data = results[3] if not isinstance(results[3], Exception) else {}
            options_data = results[4] if not isinstance(results[4], Exception) else {}
            etf_data = results[5] if not isinstance(results[5], Exception) else {}
            reserves_data = results[6] if not isinstance(results[6], Exception) else {}

            # Extract OI change from Coinglass Premium OI trend
            oi_change = 0.0
            if isinstance(oi_trend_data, dict) and oi_trend_data.get("success"):
                # Coinglass Premium OI trend returns change percentage
                oi_change = oi_trend_data.get("oiChangePct", 0.0)
                logger.info(f"Phase 3 OI trend: {oi_change:.2f}%")
            else:
                logger.warning(f"Coinglass OI trend unavailable for {symbol}")
            
            # Extract funding rate
            funding_rate = 0.0
            if isinstance(funding_data, dict) and funding_data.get("success"):
                funding_rate = funding_data.get("fundingRate", 0.0)
            else:
                logger.warning(f"Funding rate unavailable for {symbol}")
            
            # Extract top trader ratio from Coinglass Premium
            # This is the KEY fix - use proper Premium endpoint
            long_ratio = 1.0
            if isinstance(trader_data, dict) and trader_data.get("success"):
                top_trader_long_pct = trader_data.get("topTraderLongPct", 50.0)
                top_trader_short_pct = trader_data.get("topTraderShortPct", 50.0)
                
                # Convert percentage to ratio (e.g., 60% long, 40% short = 1.5 ratio)
                if top_trader_short_pct > 0:
                    long_ratio = top_trader_long_pct / top_trader_short_pct
                else:
                    long_ratio = 2.0 if top_trader_long_pct > 50 else 0.5
                
                logger.info(f"Phase 3 top traders: {top_trader_long_pct:.1f}% long, ratio: {long_ratio:.2f}")
            else:
                logger.warning(f"Coinglass top trader data unavailable for {symbol}")

            # Extract volume change from CoinAPI trades (same as Phase 2)
            volume_change = 0.0
            if isinstance(trades_data, dict) and trades_data.get("success"):
                volume_info = trades_data.get("volume", {})
                buy_pressure = volume_info.get("buyPressure", 50.0)
                sell_pressure = volume_info.get("sellPressure", 50.0)
                
                # Convert pressure to volume change estimate
                if buy_pressure > 60:
                    volume_change = (buy_pressure - 50) * 2
                elif sell_pressure > 60:
                    volume_change = -(sell_pressure - 50) * 2
                
                logger.info(f"Phase 3 volume: Buy {buy_pressure:.1f}%, Sell {sell_pressure:.1f}%")
            else:
                logger.warning(f"CoinAPI trade data unavailable for {symbol}")

            # NEW: Extract institutional signals from comprehensive endpoints
            options_oi = options_data.get("totalOptionsOI", 0) if isinstance(options_data, dict) and options_data.get("success") else 0
            etf_sentiment = etf_data.get("sentiment", "neutral") if isinstance(etf_data, dict) and etf_data.get("success") else "neutral"
            reserves_interpretation = reserves_data.get("interpretation", "neutral") if isinstance(reserves_data, dict) and reserves_data.get("success") else "neutral"
            reserves_change_pct = reserves_data.get("changePct", 0) if isinstance(reserves_data, dict) and reserves_data.get("success") else 0
            
            # Log new data sources
            logger.info(f"Phase 3 NEW data - Options OI: ${options_oi:,.0f}, ETF: {etf_sentiment}, Reserves: {reserves_interpretation} ({reserves_change_pct:+.2f}%)")
            
            # Enhanced whale accumulation detection with NEW data sources
            whale_accumulation = self._detect_whale_accumulation_enhanced(
                oi_change=oi_change,
                long_ratio=long_ratio,
                volume_change=volume_change,
                options_oi=options_oi,
                etf_sentiment=etf_sentiment,
                reserves_interpretation=reserves_interpretation,
                reserves_change_pct=reserves_change_pct
            )

            # Calculate validation score (with enhanced whale signal)
            validation_score, breakdown = self.mss_engine.calculate_validation_score(
                oi_change_pct=oi_change,
                funding_rate=funding_rate,
                top_trader_long_ratio=long_ratio,
                whale_accumulation=whale_accumulation
            )
            
            # Add new data to breakdown
            breakdown["options_oi"] = options_oi
            breakdown["etf_sentiment"] = etf_sentiment
            breakdown["reserves_interpretation"] = reserves_interpretation
            breakdown["whale_accumulation_enhanced"] = whale_accumulation

            logger.info(f"Phase 3 complete (Enhanced): {symbol} - Score: {validation_score:.2f}/35, Whale: {whale_accumulation}")
            return validation_score, breakdown

        except Exception as e:
            logger.error(f"Phase 3 validation error for {symbol}: {e}")
            return 0.0, {"status": "ERROR", "error": str(e)}

    async def calculate_mss_score(self, symbol: str) -> Dict:
        """
        Calculate complete MSS score with all 3 phases

        Args:
            symbol: Coin symbol to analyze

        Returns:
            Complete MSS analysis dict
        """
        logger.info(f"=== MSS Analysis for {symbol} ===")

        try:
            # Fetch Binance data once (reuse across phases)
            binance_stats = await self.binance.get_24hr_ticker(f"{symbol}USDT")

            # Run all 3 phases
            discovery_score = 25.0  # Default for existing coins (skip discovery for known coins)
            discovery_breakdown = {"status": "SKIPPED", "note": "Existing coin - discovery phase bypassed"}

            # Phase 2 & 3
            social_score, social_breakdown = await self.phase2_confirmation(symbol, binance_stats)
            validation_score, validation_breakdown = await self.phase3_validation(symbol, binance_stats)

            # Calculate final MSS
            mss, signal, mss_breakdown = self.mss_engine.calculate_final_mss(
                discovery_score=discovery_score,
                social_score=social_score,
                validation_score=validation_score
            )

            # Generate risk warnings
            warnings = self.mss_engine.get_risk_warnings(
                age_hours=None,  # Not available for existing coins
                fdv_usd=None,
                funding_rate=validation_breakdown.get("funding_rate"),
                top_trader_long_ratio=validation_breakdown.get("top_trader_long_ratio"),
                circulating_supply_pct=None
            )

            result = {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "mss_score": mss,
                "signal": signal,
                "confidence": mss_breakdown["confidence"],
                "phases": {
                    "phase1_discovery": {
                        "score": discovery_score,
                        "breakdown": discovery_breakdown
                    },
                    "phase2_confirmation": {
                        "score": social_score,
                        "breakdown": social_breakdown
                    },
                    "phase3_validation": {
                        "score": validation_score,
                        "breakdown": validation_breakdown
                    }
                },
                "breakdown": mss_breakdown,
                "warnings": warnings
            }

            logger.info(f"MSS Analysis complete: {symbol} - Score: {mss:.2f}, Signal: {signal}")
            return result

        except Exception as e:
            logger.error(f"MSS calculation error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "mss_score": 0,
                "signal": "ERROR"
            }

    async def scan_and_rank(
        self,
        max_fdv_usd: float = 50_000_000,
        max_age_hours: float = 72,
        min_mss_score: float = 65,
        limit: int = 10
    ) -> List[Dict]:
        """
        Auto-scan: Discover → Confirm → Validate → Rank

        Complete pipeline from discovery to ranked signals.

        Args:
            max_fdv_usd: Max FDV for discovery
            max_age_hours: Max age for discovery
            min_mss_score: Minimum MSS score threshold
            limit: Max results to return

        Returns:
            List of coins ranked by MSS score
        """
        logger.info("=== MSS Auto-Scan Started ===")

        # Phase 1: Discover potential coins
        discovered = await self.phase1_discovery(
            max_fdv_usd=max_fdv_usd,
            max_age_hours=max_age_hours,
            limit=limit * 3  # Discover more, filter later
        )

        if not discovered:
            logger.warning("No coins discovered in Phase 1")
            return []

        logger.info(f"Phase 1: {len(discovered)} coins discovered")

        # Phase 2 & 3: Analyze each discovered coin
        # ✅ OPTIMIZED: Process in batches to avoid timeout (MSS analysis = 15-20s per coin)
        coins_to_analyze = discovered[:limit * 2]  # Analyze subset
        batch_size = 5  # Process 5 coins at a time (balance speed vs timeout)
        results = []
        
        for i in range(0, len(coins_to_analyze), batch_size):
            batch = coins_to_analyze[i:i + batch_size]
            logger.info(f"📊 MSS Batch {i//batch_size + 1}/{(len(coins_to_analyze)-1)//batch_size + 1}: Analyzing {[c['symbol'] for c in batch]}")
            
            tasks = [self.calculate_mss_score(coin["symbol"]) for coin in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches (avoid rate limits)
            if i + batch_size < len(coins_to_analyze):
                await asyncio.sleep(1)  # 1s delay between batches

        # Filter and rank
        high_potential = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if result.get("mss_score", 0) >= min_mss_score:
                high_potential.append(result)

        # Sort by MSS score
        high_potential.sort(key=lambda x: x.get("mss_score", 0), reverse=True)

        logger.info(f"=== MSS Auto-Scan Complete: {len(high_potential)} high-potential coins ===")
        return high_potential[:limit]

    def _estimate_age_hours(self, coin_data: Dict) -> Optional[float]:
        """
        Estimate coin age from available data

        Args:
            coin_data: CoinGecko coin data

        Returns:
            Estimated age in hours or None
        """
        # Try to get listing date
        listing_date = coin_data.get("listing_date") or coin_data.get("added_date")
        if listing_date:
            try:
                listed = datetime.fromisoformat(listing_date.replace("Z", "+00:00"))
                age = (datetime.utcnow() - listed).total_seconds() / 3600
                return age
            except:
                pass

        # Fallback: use 24 hours for trending coins without date
        return 24.0

    def _detect_whale_accumulation(
        self,
        oi_change: Optional[float],
        long_ratio: Optional[float],
        volume_change: Optional[float]
    ) -> bool:
        """
        Whale accumulation detection with proper bounds

        Whales accumulating when ALL conditions met:
        - OI increasing significantly (>50%)
        - Long ratio in sweet spot (1.5-2.5, not overcrowded)
        - Volume increasing (>30%)

        Args:
            oi_change: OI change % (None if unavailable)
            long_ratio: Long/Short ratio (None if unavailable)
            volume_change: Volume change % (None if unavailable)

        Returns:
            True if whale accumulation detected, False otherwise or if data incomplete
        """
        # Require ALL metrics to be available for confident detection
        if oi_change is None or long_ratio is None or volume_change is None:
            return False
        
        return (
            oi_change > 50 and
            1.5 <= long_ratio <= 2.5 and
            volume_change > 30
        )
    
    def _detect_whale_accumulation_enhanced(
        self,
        oi_change: Optional[float],
        long_ratio: Optional[float],
        volume_change: Optional[float],
        options_oi: float = 0,
        etf_sentiment: str = "neutral",
        reserves_interpretation: str = "neutral",
        reserves_change_pct: float = 0
    ) -> bool:
        """
        ENHANCED whale accumulation detection with institutional tracking
        
        Uses traditional signals PLUS new data sources:
        - Options OI (smart money hedging)
        - ETF flows (institutional sentiment)
        - Exchange reserves (whale movements)
        
        Whale accumulation when MULTIPLE conditions met:
        
        TRADITIONAL (high confidence if all 3):
        - OI increasing (>50%)
        - Long ratio sweet spot (1.5-2.5)
        - Volume increasing (>30%)
        
        INSTITUTIONAL (bonus signals):
        - Options OI > $1B (institutions hedging)
        - ETF accumulation sentiment
        - Exchange reserves decreasing (whales moving to cold storage)
        
        Args:
            oi_change: OI change %
            long_ratio: Long/Short ratio
            volume_change: Volume change %
            options_oi: Total options open interest
            etf_sentiment: ETF flow sentiment (accumulation/distribution/neutral)
            reserves_interpretation: Exchange reserves interpretation
            reserves_change_pct: Exchange reserves change %
            
        Returns:
            True if whale accumulation detected (either traditional OR institutional signals strong)
        """
        # Traditional detection (original logic)
        traditional_signal = False
        if oi_change is not None and long_ratio is not None and volume_change is not None:
            traditional_signal = (
                oi_change > 50 and
                1.5 <= long_ratio <= 2.5 and
                volume_change > 30
            )
        
        # Institutional signals (NEW!)
        institutional_signals = 0
        
        # 1. Options OI > $1B = smart money positioning
        if options_oi > 1_000_000_000:
            institutional_signals += 1
            logger.info(f"Whale signal: High options OI (${options_oi/1e9:.2f}B)")
        
        # 2. ETF accumulation = institutions buying
        if etf_sentiment in ["accumulation", "strong_accumulation"]:
            institutional_signals += 1
            logger.info(f"Whale signal: ETF {etf_sentiment}")
        
        # 3. Exchange reserves decreasing = whales moving to cold storage (bullish)
        if reserves_interpretation in ["whale_accumulation", "accumulation"]:
            institutional_signals += 1
            logger.info(f"Whale signal: Exchange reserves {reserves_interpretation} ({reserves_change_pct:+.2f}%)")
        
        # Enhanced logic: Whale accumulation if:
        # - Traditional signals all positive, OR
        # - 2+ institutional signals detected
        whale_detected = traditional_signal or institutional_signals >= 2
        
        if whale_detected:
            logger.info(f"🐋 WHALE ACCUMULATION DETECTED! Traditional: {traditional_signal}, Institutional signals: {institutional_signals}/3")
        
        return whale_detected
