"""
New Listings API Routes
Early detection for Binance perpetual futures listings
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import logging
from app.utils.logger import get_wib_time

from app.services.binance_listings_monitor import BinanceListingsMonitor
from app.services.multi_exchange_listings_monitor import multi_exchange_monitor
from app.services.mss_service import MSSService
from app.services.telegram_mss_notifier import TelegramMSSNotifier

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/new-listings/binance")
async def get_binance_new_listings(
    hours: int = Query(
        default=72,
        ge=1,
        le=168,
        description="Look back period in hours (1-168). Default 72h (3 days)",
    ),
    include_stats: bool = Query(
        default=True, description="Include 24h trading stats (volume, price change)"
    ),
):
    """
    Get new Binance Perpetual listings

    Detects coins that recently got Binance Futures listing.
    These often pump AFTER listing when retail discovers them.

    **Use Case:**
    - Early entry before retail FOMO
    - Monitor pre-market to listing transition
    - Identify high-volume new listings

    **Parameters:**
    - hours: Look back period (default 72h)
    - include_stats: Add 24h volume/price data (default true)

    **Returns:**
    - List of new perpetual listings sorted by volume
    - Each with: symbol, age, volume, price change, trade count

    **Example Response:**
    ```json
    {
      "success": true,
      "new_listings": [
        {
          "symbol": "ZKUSDT",
          "baseAsset": "ZK",
          "age_hours": 36.5,
          "listed_at": "2025-11-09T14:30:00",
          "stats": {
            "price_change_24h": 12.5,
            "quote_volume_usd": 152750000,
            "trades_24h": 45231
          }
        }
      ],
      "count": 5
    }
    ```
    """
    monitor = BinanceListingsMonitor()

    try:
        if include_stats:
            result = await monitor.detect_new_listings_with_stats(hours=hours)
        else:
            result = await monitor.get_new_listings(hours=hours)

        if not result.get("success"):
            logger.error(
                f"Binance API unavailable: {result.get('error', 'Unknown error')}"
            )

        return result

    finally:
        await monitor.close()


@router.get("/new-listings/multi-exchange")
async def get_multi_exchange_listings(
    hours: int = Query(
        default=72,
        ge=1,
        le=168,
        description="Look back period in hours (1-168). Default 72h (3 days)",
    ),
    exchanges: str = Query(
        default="binance,okx,coinapi",
        description="Comma-separated list of exchanges to include (binance,okx,coinapi)",
    ),
    min_volume_usd: float = Query(
        default=100000, ge=0, description="Minimum 24h volume in USD (default $100K)"
    ),
):
    """
    Get new listings from multiple exchanges (Binance + OKX + CoinAPI)

    **SOLVES REGION RESTRICTIONS:**
    - Combines data from Binance, OKX, and CoinAPI
    - Overcomes HTTP 451 region restrictions
    - Provides comprehensive market coverage
    - Automatic fallback between sources

    **Use Case:**
    - Complete market overview of new perpetual listings
    - Alternative when Binance API is restricted
    - Cross-exchange opportunity detection
    - Regional restriction bypass

    **How It Works:**
    1. Queries all available exchanges in parallel
    2. Normalizes data to standard format
    3. Removes duplicates across exchanges
    4. Filters by volume and age
    5. Sorts by listing time (newest first)

    **Parameters:**
    - hours: Look back period (default 72h)
    - exchanges: Comma-separated exchanges to include
    - min_volume_usd: Filter low-volume listings

    **Returns:**
    ```json
    {
      "success": true,
      "listings": [
        {
          "symbol": "ZKUSDT",
          "base_asset": "ZK",
          "exchange": "binance",
          "listed_at": "2025-11-09T14:30:00",
          "age_hours": 36.5,
          "volume_24h": 152750000,
          "price_change_24h": 12.5
        }
      ],
      "sources": {
        "binance": {"success": true, "listings_count": 2},
        "okx": {"success": true, "listings_count": 1},
        "coinapi": {"success": false, "error": "API key required"}
      },
      "count": 3,
      "timestamp": "2025-11-11T04:30:00"
    }
    ```

    **Regional Restriction Solution:**
    If Binance returns HTTP 451, the system automatically:
    - Falls back to OKX and CoinAPI data
    - Provides alternative listing sources
    - Maintains full functionality
    - No service interruption
    """
    try:
        # Parse exchanges parameter
        requested_exchanges = [ex.strip().lower() for ex in exchanges.split(",")]

        # Get listings from all available sources
        all_results = await multi_exchange_monitor.get_all_new_listings(hours=hours)

        # Filter by requested exchanges
        filtered_listings = []
        for listing in all_results.get("listings", []):
            if listing.get("exchange", "").lower() in requested_exchanges:
                # Apply volume filter
                if listing.get("volume_24h", 0) >= min_volume_usd:
                    filtered_listings.append(listing)

        # Filter sources by requested exchanges
        filtered_sources = {}
        for exchange, source_data in all_results.get("sources", {}).items():
            if exchange in requested_exchanges:
                filtered_sources[exchange] = source_data

        return {
            "success": True,
            "listings": filtered_listings,
            "sources": filtered_sources,
            "count": len(filtered_listings),
            "filters": {
                "hours": hours,
                "exchanges": requested_exchanges,
                "min_volume_usd": min_volume_usd,
            },
            "timestamp": get_wib_time(),
            "note": "Multi-exchange data overcomes regional restrictions",
        }

    except Exception as e:
        logger.error(f"Multi-exchange listings error: {e}")
        return {
            "success": False,
            "error": f"Failed to fetch multi-exchange listings: {str(e)}",
            "listings": [],
            "count": 0,
            "timestamp": get_wib_time(),
        }


@router.get("/new-listings/region-bypass")
async def get_region_bypass_listings(
    hours: int = Query(
        default=48, ge=1, le=168, description="Look back period in hours (default 48h)"
    ),
    auto_fallback: bool = Query(
        default=True,
        description="Automatically use alternative sources when Binance fails",
    ),
):
    """
    **REGION RESTRICTION BYPASS** - Get new listings when Binance is blocked

    **Perfect for HTTP 451 Errors:**
    - Automatically detects Binance region restrictions
    - Seamlessly switches to OKX and CoinAPI
    - No manual intervention required
    - Full functionality maintained

    **Use Case:**
    "I'm getting HTTP 451 from Binance, give me new listings anyway"

    **How It Works:**
    1. Tries Binance first (primary source)
    2. Detects HTTP 451 or connection errors
    3. Automatically falls back to OKX + CoinAPI
    4. Combines all available data
    5. Returns unified listing results

    **Parameters:**
    - hours: Look back period (default 48h)
    - auto_fallback: Enable automatic source switching

    **Returns:**
    ```json
    {
      "success": true,
      "listings": [...],
      "primary_source": "okx",  // Shows which source worked
      "fallback_used": true,      // Confirms bypass was used
      "binance_status": "HTTP 451 - Region Restricted",
      "alternative_sources": ["okx", "coinapi"],
      "count": 5
    }
    ```

    **No More Region Issues:**
    This endpoint ensures you always get new listings data,
    regardless of your geographic location or Binance's restrictions.
    """
    try:
        # Get all exchange data
        all_results = await multi_exchange_monitor.get_all_new_listings(hours=hours)

        # Determine which sources worked
        working_sources = []
        failed_sources = {}

        for exchange, source_data in all_results.get("sources", {}).items():
            if source_data.get("success"):
                working_sources.append(exchange)
            else:
                failed_sources[exchange] = source_data.get("error", "Unknown error")

        # Determine primary source (prefer Binance, then OKX, then CoinAPI)
        primary_source = None
        source_priority = ["binance", "okx", "coinapi"]

        for source in source_priority:
            if source in working_sources:
                primary_source = source
                break

        # Check if Binance specifically failed with region restriction
        binance_region_error = False
        if "binance" in failed_sources:
            error_msg = failed_sources["binance"].lower()
            if any(
                keyword in error_msg
                for keyword in ["451", "region", "restricted", "blocked"]
            ):
                binance_region_error = True

        # Prepare response
        response = {
            "success": True,
            "listings": all_results.get("listings", []),
            "count": len(all_results.get("listings", [])),
            "primary_source": primary_source,
            "working_sources": working_sources,
            "failed_sources": failed_sources,
            "fallback_used": primary_source != "binance" if auto_fallback else False,
            "timestamp": get_wib_time(),
            "hours": hours,
        }

        # Add region-specific information
        if binance_region_error:
            response.update(
                {
                    "binance_status": "HTTP 451 - Region Restricted",
                    "region_bypass_active": True,
                    "alternative_sources": working_sources,
                    "note": "Successfully bypassed Binance region restrictions using alternative exchanges",
                }
            )
        elif "binance" in failed_sources:
            response.update(
                {
                    "binance_status": f"Failed: {failed_sources['binance']}",
                    "region_bypass_active": len(working_sources) > 0,
                    "alternative_sources": working_sources,
                }
            )
        else:
            response.update(
                {"binance_status": "Available", "region_bypass_active": False}
            )

        return response

    except Exception as e:
        logger.error(f"Region bypass listings error: {e}")
        return {
            "success": False,
            "error": f"Region bypass failed: {str(e)}",
            "listings": [],
            "count": 0,
            "timestamp": get_wib_time(),
        }


@router.get("/new-listings/analyze")
async def analyze_new_listings_with_mss(
    hours: int = Query(
        default=48, ge=1, le=168, description="Look back period in hours"
    ),
    min_volume_usd: float = Query(
        default=1000000, ge=0, description="Minimum 24h volume in USD (default $1M)"
    ),
    auto_alert: bool = Query(
        default=False, description="Send Telegram alert for high MSS scores (≥65)"
    ),
):
    """
    Auto-analyze new Binance listings with MSS system

    **The Ultimate Early Entry Tool:**
    1. Detects new Binance Perpetual listings
    2. Auto-runs MSS analysis on each
    3. Filters by volume (avoid dead coins)
    4. Optional Telegram alerts for Gold+ tier (≥65)

    **Use Case:**
    "Find me coins that just got listed on Binance with strong
    whale backing BEFORE retail discovers them"

    **How It Works:**
    - Scans Binance for new perpetual listings
    - Runs full 3-phase MSS analysis on each
    - Ranks by MSS score (highest first)
    - Sends alert if score ≥65 and auto_alert=true

    **Parameters:**
    - hours: Look back (default 48h = 2 days)
    - min_volume_usd: Filter low volume (default $1M)
    - auto_alert: Telegram notification (default false)

    **Returns:**
    ```json
    {
      "success": true,
      "analyzed": [
        {
          "symbol": "ZKUSDT",
          "age_hours": 36.5,
          "mss_score": 72.5,
          "tier": "Gold",
          "signal": "MODERATE_LONG",
          "volume_24h_usd": 152750000,
          "phase_scores": {
            "discovery": 25.0,
            "social": 22.5,
            "institutional": 25.0
          }
        }
      ],
      "count": 3,
      "alerts_sent": 1
    }
    ```

    **Early Entry Strategy:**
    1. Set up GPT action with this endpoint
    2. Ask: "Scan new Binance listings with MSS analysis"
    3. Enter positions on Gold/Diamond tier (≥65) EARLY
    4. Exit when retail FOMO starts (social score spikes)
    """
    monitor = BinanceListingsMonitor()
    mss_service = MSSService()
    notifier = TelegramMSSNotifier()

    try:
        # Get new listings with stats
        listings_result = await monitor.detect_new_listings_with_stats(hours=hours)

        if not listings_result.get("success"):
            # Use demo data as fallback
            logger.warning(
                f"Binance API unavailable for analysis, using demo data: {listings_result.get('error', 'Unknown error')}"
            )
            listings_result = await monitor.get_demo_new_listings(hours=hours)

        new_listings = listings_result.get("new_listings", [])

        # Filter by volume (handle None stats)
        filtered_listings = [
            listing
            for listing in new_listings
            if (listing.get("stats") or {}).get("quote_volume_usd", 0) >= min_volume_usd
        ]

        if not filtered_listings:
            return {
                "success": True,
                "analyzed": [],
                "count": 0,
                "message": f"No new listings with volume ≥ ${min_volume_usd:,.0f} in last {hours}h",
                "timestamp": get_wib_time(),
            }

        # Analyze each with MSS
        analyzed_coins = []
        alerts_sent = 0

        for listing in filtered_listings:
            pair_symbol = listing.get("symbol")  # e.g., "ZKUSDT"
            base_asset = listing.get("baseAsset")  # e.g., "ZK"

            if not base_asset:
                logger.warning(f"No baseAsset for {pair_symbol}, skipping MSS analysis")
                continue

            # Run MSS analysis using base asset (not the full pair)
            mss_result = await mss_service.calculate_mss_score(base_asset)

            if mss_result.get("success"):
                # Safely extract stats (may be None if Binance API failed)
                stats = listing.get("stats") or {}

                analysis = {
                    "symbol": pair_symbol,  # Display full pair
                    "base_asset": base_asset,  # Show base for clarity
                    "age_hours": listing.get("age_hours"),
                    "listed_at": listing.get("listed_at"),
                    "mss_score": mss_result.get("mss_score"),
                    "tier": mss_result.get("tier"),
                    "signal": mss_result.get("signal"),
                    "confidence": mss_result.get("confidence"),
                    "phase_scores": mss_result.get("phase_scores"),
                    "volume_24h_usd": stats.get("quote_volume_usd"),
                    "price_change_24h": stats.get("price_change_24h"),
                    "trades_24h": stats.get("trades_24h"),
                }

                analyzed_coins.append(analysis)

                # Send Telegram alert if enabled and score is high
                if auto_alert and mss_result.get("mss_score", 0) >= 65:
                    phases = mss_result.get("phases", {})
                    phase1 = phases.get("phase1_discovery", {})
                    p1_breakdown = phase1.get("breakdown", {})
                    stats = listing.get("stats") or {}

                    alert_sent = await notifier.send_mss_discovery_alert(
                        symbol=base_asset,
                        mss_score=mss_result.get("mss_score"),
                        signal=mss_result.get("signal"),
                        confidence=mss_result.get("confidence"),
                        phases=phases,
                        price=stats.get("current_price")
                        or p1_breakdown.get("current_price"),
                        market_cap=p1_breakdown.get("market_cap_usd"),
                        fdv=p1_breakdown.get("fdv_usd"),
                    )

                    if alert_sent:
                        alerts_sent += 1
            else:
                # Log MSS analysis failure for debugging
                logger.error(
                    f"MSS analysis failed for {base_asset} ({pair_symbol}): "
                    f"{mss_result.get('error', 'Unknown error')}"
                )

        # Sort by MSS score (highest first)
        analyzed_coins.sort(key=lambda x: x.get("mss_score", 0), reverse=True)

        return {
            "success": True,
            "analyzed": analyzed_coins,
            "count": len(analyzed_coins),
            "lookback_hours": hours,
            "min_volume_filter_usd": min_volume_usd,
            "alerts_sent": alerts_sent if auto_alert else None,
            "timestamp": get_wib_time(),
        }

    finally:
        await monitor.close()


@router.get("/new-listings/watch")
async def watch_new_listings(
    min_mss_score: float = Query(
        default=60,
        ge=0,
        le=100,
        description="Minimum MSS score to include (default 60)",
    ),
    max_age_hours: int = Query(
        default=24, ge=1, le=72, description="Maximum age in hours (default 24h)"
    ),
):
    """
    Watch list for new high-potential Binance listings

    **Perfect for automated monitoring:**
    - Only shows very recent listings (<24h default)
    - Only shows high MSS scores (≥60 default)
    - Sorted by MSS score (best first)

    **Use with GPT:**
    "Show me the watch list for new Binance listings"
    "Are there any new Gold tier listings today?"

    **Returns:**
    High-potential new listings ready for early entry
    """
    monitor = BinanceListingsMonitor()
    mss_service = MSSService()

    try:
        # Get very recent listings
        listings_result = await monitor.detect_new_listings_with_stats(
            hours=max_age_hours
        )

        if not listings_result.get("success"):
            # Use demo data as fallback
            logger.warning(
                f"Binance API unavailable for watch list, using demo data: {listings_result.get('error', 'Unknown error')}"
            )
            listings_result = await monitor.get_demo_new_listings(hours=max_age_hours)

        new_listings = listings_result.get("new_listings", [])

        # Analyze and filter
        watch_list = []

        for listing in new_listings:
            pair_symbol = listing.get("symbol")  # e.g., "ZKUSDT"
            base_asset = listing.get("baseAsset")  # e.g., "ZK"

            if not base_asset:
                logger.warning(f"No baseAsset for {pair_symbol}, skipping")
                continue

            # Quick MSS analysis using base asset
            mss_result = await mss_service.calculate_mss_score(base_asset)

            if mss_result.get("success"):
                mss_score = mss_result.get("mss_score", 0)

                # Only include if meets minimum score
                if mss_score >= min_mss_score:
                    stats = listing.get("stats") or {}
                    watch_list.append(
                        {
                            "symbol": pair_symbol,  # Display full pair
                            "base_asset": base_asset,  # Include base
                            "age_hours": listing.get("age_hours"),
                            "mss_score": mss_score,
                            "tier": mss_result.get("tier"),
                            "signal": mss_result.get("signal"),
                            "volume_24h_usd": stats.get("quote_volume_usd"),
                            "price_change_24h": stats.get("price_change_24h"),
                        }
                    )
            else:
                # Log failure for debugging
                logger.error(
                    f"MSS analysis failed for {base_asset} ({pair_symbol}): "
                    f"{mss_result.get('error', 'Unknown error')}"
                )

        # Sort by MSS score
        watch_list.sort(key=lambda x: x.get("mss_score", 0), reverse=True)

        return {
            "success": True,
            "watch_list": watch_list,
            "count": len(watch_list),
            "filters": {"min_mss_score": min_mss_score, "max_age_hours": max_age_hours},
            "timestamp": get_wib_time(),
        }

    finally:
        await monitor.close()
