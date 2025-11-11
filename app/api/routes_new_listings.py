"""
New Listings API Routes
Early detection for Binance perpetual futures listings
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

from app.services.binance_listings_monitor import BinanceListingsMonitor
from app.services.mss_service import MSSService
from app.services.telegram_mss_notifier import TelegramMSSNotifier

router = APIRouter()


@router.get("/new-listings/binance")
async def get_binance_new_listings(
    hours: int = Query(
        default=72,
        ge=1,
        le=168,
        description="Look back period in hours (1-168). Default 72h (3 days)"
    ),
    include_stats: bool = Query(
        default=True,
        description="Include 24h trading stats (volume, price change)"
    )
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
        
        return result
        
    finally:
        await monitor.close()


@router.get("/new-listings/analyze")
async def analyze_new_listings_with_mss(
    hours: int = Query(
        default=48,
        ge=1,
        le=168,
        description="Look back period in hours"
    ),
    min_volume_usd: float = Query(
        default=1000000,
        ge=0,
        description="Minimum 24h volume in USD (default $1M)"
    ),
    auto_alert: bool = Query(
        default=False,
        description="Send Telegram alert for high MSS scores (≥65)"
    )
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
            return listings_result
        
        new_listings = listings_result.get("new_listings", [])
        
        # Filter by volume
        filtered_listings = [
            listing for listing in new_listings
            if listing.get("stats", {}).get("quote_volume_usd", 0) >= min_volume_usd
        ]
        
        if not filtered_listings:
            return {
                "success": True,
                "analyzed": [],
                "count": 0,
                "message": f"No new listings with volume ≥ ${min_volume_usd:,.0f} in last {hours}h",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Analyze each with MSS
        analyzed_coins = []
        alerts_sent = 0
        
        for listing in filtered_listings:
            symbol = listing.get("symbol")
            
            # Run MSS analysis
            mss_result = await mss_service.calculate_mss_score(symbol)
            
            if mss_result.get("success"):
                analysis = {
                    "symbol": symbol,
                    "baseAsset": listing.get("baseAsset"),
                    "age_hours": listing.get("age_hours"),
                    "listed_at": listing.get("listed_at"),
                    "mss_score": mss_result.get("mss_score"),
                    "tier": mss_result.get("tier"),
                    "signal": mss_result.get("signal"),
                    "confidence": mss_result.get("confidence"),
                    "phase_scores": mss_result.get("phase_scores"),
                    "volume_24h_usd": listing.get("stats", {}).get("quote_volume_usd"),
                    "price_change_24h": listing.get("stats", {}).get("price_change_24h"),
                    "trades_24h": listing.get("stats", {}).get("trades_24h")
                }
                
                analyzed_coins.append(analysis)
                
                # Send Telegram alert if enabled and score is high
                if auto_alert and mss_result.get("mss_score", 0) >= 65:
                    phases = mss_result.get("phases", {})
                    phase1 = phases.get("phase1_discovery", {})
                    p1_breakdown = phase1.get("breakdown", {})
                    
                    alert_sent = await notifier.send_mss_discovery_alert(
                        symbol=symbol,
                        mss_score=mss_result.get("mss_score"),
                        signal=mss_result.get("signal"),
                        confidence=mss_result.get("confidence"),
                        phases=phases,
                        price=listing.get("stats", {}).get("current_price") or p1_breakdown.get("current_price"),
                        market_cap=p1_breakdown.get("market_cap_usd"),
                        fdv=p1_breakdown.get("fdv_usd"),
                        custom_note=f"🆕 NEW BINANCE LISTING ({listing.get('age_hours')}h old)"
                    )
                    
                    if alert_sent:
                        alerts_sent += 1
        
        # Sort by MSS score (highest first)
        analyzed_coins.sort(
            key=lambda x: x.get("mss_score", 0),
            reverse=True
        )
        
        return {
            "success": True,
            "analyzed": analyzed_coins,
            "count": len(analyzed_coins),
            "lookback_hours": hours,
            "min_volume_filter_usd": min_volume_usd,
            "alerts_sent": alerts_sent if auto_alert else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        await monitor.close()


@router.get("/new-listings/watch")
async def watch_new_listings(
    min_mss_score: float = Query(
        default=60,
        ge=0,
        le=100,
        description="Minimum MSS score to include (default 60)"
    ),
    max_age_hours: int = Query(
        default=24,
        ge=1,
        le=72,
        description="Maximum age in hours (default 24h)"
    )
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
        listings_result = await monitor.detect_new_listings_with_stats(hours=max_age_hours)
        
        if not listings_result.get("success"):
            return listings_result
        
        new_listings = listings_result.get("new_listings", [])
        
        # Analyze and filter
        watch_list = []
        
        for listing in new_listings:
            symbol = listing.get("symbol")
            
            # Quick MSS analysis
            mss_result = await mss_service.calculate_mss_score(symbol)
            
            if mss_result.get("success"):
                mss_score = mss_result.get("mss_score", 0)
                
                # Only include if meets minimum score
                if mss_score >= min_mss_score:
                    watch_list.append({
                        "symbol": symbol,
                        "baseAsset": listing.get("baseAsset"),
                        "age_hours": listing.get("age_hours"),
                        "mss_score": mss_score,
                        "tier": mss_result.get("tier"),
                        "signal": mss_result.get("signal"),
                        "volume_24h_usd": listing.get("stats", {}).get("quote_volume_usd"),
                        "price_change_24h": listing.get("stats", {}).get("price_change_24h")
                    })
        
        # Sort by MSS score
        watch_list.sort(
            key=lambda x: x.get("mss_score", 0),
            reverse=True
        )
        
        return {
            "success": True,
            "watch_list": watch_list,
            "count": len(watch_list),
            "filters": {
                "min_mss_score": min_mss_score,
                "max_age_hours": max_age_hours
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        await monitor.close()
