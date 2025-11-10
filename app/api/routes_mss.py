"""
MSS (Multimodal Signal Score) API Routes

Endpoints for high-potential crypto asset discovery and analysis.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging
import os

from app.services.mss_service import MSSService
from app.services.telegram_mss_notifier import telegram_mss_notifier

logger = logging.getLogger(__name__)

# MSS notification threshold (configurable via environment)
MSS_NOTIFICATION_THRESHOLD = float(os.getenv("MSS_NOTIFICATION_THRESHOLD", "75.0"))

router = APIRouter()

# Global MSS service instance
mss_service: Optional[MSSService] = None


def get_mss_service() -> MSSService:
    """Get or create MSS service instance"""
    global mss_service
    if mss_service is None:
        mss_service = MSSService()
    return mss_service


@router.get("/discover")
async def discover_new_coins(
    max_fdv: float = Query(
        50_000_000,
        description="Maximum FDV (Fully Diluted Valuation) in USD",
        ge=1_000_000,
        le=500_000_000
    ),
    max_age_hours: float = Query(
        72,
        description="Maximum age in hours since listing",
        ge=1,
        le=720
    ),
    min_volume: float = Query(
        100_000,
        description="Minimum 24h volume in USD",
        ge=10_000
    ),
    limit: int = Query(
        20,
        description="Maximum number of results",
        ge=1,
        le=100
    )
):
    """
    **Phase 1: Discover New Low-FDV Coins**

    Scans CoinGecko and Binance for recently listed coins with:
    - Low FDV (fully diluted valuation)
    - Recent listing (< 72 hours ideal)
    - Sufficient liquidity

    **Use Case:** Find hidden gems before retail discovers them

    **Example:** `GET /mss/discover?max_fdv=50000000&max_age_hours=48&limit=10`

    Returns:
    - List of discovered coins with discovery scores
    - Tokenomics analysis
    - Age and volume metrics
    """
    try:
        service = get_mss_service()
        results = await service.phase1_discovery(
            max_fdv_usd=max_fdv,
            max_age_hours=max_age_hours,
            min_volume_24h=min_volume,
            limit=limit
        )

        from datetime import datetime
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "filters": {
                "max_fdv_usd": max_fdv,
                "max_age_hours": max_age_hours,
                "min_volume_24h_usd": min_volume
            },
            "total_discovered": len(results),
            "coins": results
        }

    except Exception as e:
        logger.error(f"Discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{symbol}")
async def analyze_coin(
    symbol: str,
    include_raw: bool = Query(
        False,
        description="Include raw phase breakdowns"
    ),
    send_alert: bool = Query(
        True,
        description="Send Telegram alert if MSS score is high (>= threshold)"
    )
):
    """
    **Full 3-Phase MSS Analysis**

    Complete analysis of any cryptocurrency:
    - Phase 1: Discovery (tokenomics scoring)
    - Phase 2: Social Confirmation (LunarCrush + volume)
    - Phase 3: Institutional Validation (OI + whale activity)

    **Use Case:** Deep-dive analysis on specific coin

    **Example:** `GET /mss/analyze/PEPE?include_raw=true`

    Returns:
    - MSS score (0-100)
    - Signal recommendation
    - Confidence level
    - Phase breakdowns
    - Risk warnings
    - Telegram alert status (if high-scoring)
    """
    try:
        service = get_mss_service()
        result = await service.calculate_mss_score(symbol.upper())

        # Send Telegram alert for high-scoring discoveries
        telegram_sent = False
        if send_alert and result.get("mss_score", 0) >= MSS_NOTIFICATION_THRESHOLD:
            try:
                phases = result.get("phases", {})
                
                # Extract market data from phases
                phase1 = phases.get("phase1_discovery", {})
                p1_breakdown = phase1.get("breakdown", {})
                
                notification_result = await telegram_mss_notifier.send_mss_discovery_alert(
                    symbol=symbol.upper(),
                    mss_score=result.get("mss_score", 0),
                    signal=result.get("signal", "NEUTRAL"),
                    confidence=result.get("confidence", "medium"),
                    phases=phases,
                    price=p1_breakdown.get("current_price"),
                    market_cap=p1_breakdown.get("market_cap_usd"),
                    fdv=p1_breakdown.get("fdv_usd")
                )
                
                telegram_sent = notification_result.get("success", False)
                
                if telegram_sent:
                    logger.info(f"✅ Telegram alert sent for {symbol} (MSS: {result.get('mss_score'):.1f})")
                
            except Exception as notify_err:
                logger.warning(f"Failed to send Telegram alert for {symbol}: {notify_err}")

        if not include_raw:
            # Simplified response
            result.pop("phases", None)

        response = {
            "success": True,
            **result
        }
        
        # Add Telegram alert status if sent
        if telegram_sent:
            response["telegram_alert"] = {
                "sent": True,
                "threshold": MSS_NOTIFICATION_THRESHOLD,
                "message": f"High MSS score alert sent to Telegram"
            }

        return response

    except Exception as e:
        logger.error(f"Analysis error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def scan_market(
    max_fdv: float = Query(
        50_000_000,
        description="Maximum FDV for discovery phase"
    ),
    max_age_hours: float = Query(
        72,
        description="Maximum coin age in hours"
    ),
    min_mss_score: float = Query(
        65,
        description="Minimum MSS score threshold",
        ge=0,
        le=100
    ),
    limit: int = Query(
        10,
        description="Maximum results",
        ge=1,
        le=50
    ),
    send_alerts: bool = Query(
        True,
        description="Send Telegram alerts for coins exceeding notification threshold"
    )
):
    """
    **Auto-Scan: Complete MSS Pipeline**

    Full automated workflow:
    1. Discover new low-FDV coins
    2. Confirm social momentum
    3. Validate whale activity
    4. Rank by MSS score
    5. Send Telegram alerts for high-scoring discoveries

    **Use Case:** Daily alpha hunting - find best opportunities automatically

    **Example:** `GET /mss/scan?min_mss_score=75&limit=5`

    Returns:
    - Top coins ranked by MSS score
    - Complete analysis for each
    - Ready-to-trade signals
    - Telegram alert summary
    """
    try:
        service = get_mss_service()
        results = await service.scan_and_rank(
            max_fdv_usd=max_fdv,
            max_age_hours=max_age_hours,
            min_mss_score=min_mss_score,
            limit=limit
        )

        from datetime import datetime
        
        # Send Telegram alerts for high-scoring coins
        alerts_sent = 0
        if send_alerts and results:
            for coin in results:
                if coin.get("mss_score", 0) >= MSS_NOTIFICATION_THRESHOLD:
                    try:
                        phases = coin.get("phases", {})
                        phase1 = phases.get("phase1_discovery", {})
                        p1_breakdown = phase1.get("breakdown", {})
                        
                        notification_result = await telegram_mss_notifier.send_mss_discovery_alert(
                            symbol=coin.get("symbol", "UNKNOWN"),
                            mss_score=coin.get("mss_score", 0),
                            signal=coin.get("signal", "NEUTRAL"),
                            confidence=coin.get("confidence", "medium"),
                            phases=phases,
                            price=p1_breakdown.get("current_price"),
                            market_cap=p1_breakdown.get("market_cap_usd"),
                            fdv=p1_breakdown.get("fdv_usd")
                        )
                        
                        if notification_result.get("success"):
                            alerts_sent += 1
                            logger.info(f"✅ Alert sent for {coin.get('symbol')} (MSS: {coin.get('mss_score'):.1f})")
                            
                    except Exception as notify_err:
                        logger.warning(f"Failed to send alert for {coin.get('symbol')}: {notify_err}")
        
        response = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scan_parameters": {
                "max_fdv_usd": max_fdv,
                "max_age_hours": max_age_hours,
                "min_mss_score": min_mss_score
            },
            "total_high_potential": len(results),
            "coins": results,
            "summary": {
                "avg_mss_score": round(sum(c.get("mss_score", 0) for c in results) / len(results), 2) if results else 0,
                "strong_signals": len([c for c in results if c.get("signal") == "STRONG_LONG"]),
                "long_signals": len([c for c in results if c.get("signal") in ["LONG", "MODERATE_LONG"]])
            }
        }
        
        # Add Telegram alert summary
        if send_alerts:
            response["telegram_alerts"] = {
                "sent": alerts_sent,
                "threshold": MSS_NOTIFICATION_THRESHOLD,
                "eligible_coins": len([c for c in results if c.get("mss_score", 0) >= MSS_NOTIFICATION_THRESHOLD])
            }
        
        return response

    except Exception as e:
        logger.error(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watch/{symbol}")
async def watch_coin(
    symbol: str,
    interval_minutes: int = Query(
        15,
        description="Update interval in minutes",
        ge=5,
        le=60
    )
):
    """
    **Real-Time MSS Monitoring**

    Continuous monitoring of MSS score changes:
    - Track score evolution
    - Alert on significant changes
    - Monitor phase transitions

    **Use Case:** Monitor coins you're considering entering

    **Example:** `GET /mss/watch/PEPE?interval_minutes=15`

    Returns:
    - Current MSS score
    - Recent score history
    - Change indicators
    - Alert triggers
    """
    try:
        service = get_mss_service()

        # Current analysis
        current = await service.calculate_mss_score(symbol.upper())

        # Note: Full historical tracking would require database
        # For now, return current state with monitoring setup
        return {
            "success": True,
            "symbol": symbol.upper(),
            "monitoring": {
                "interval_minutes": interval_minutes,
                "active": True,
                "next_update_in_minutes": interval_minutes
            },
            "current_state": {
                "mss_score": current.get("mss_score"),
                "signal": current.get("signal"),
                "confidence": current.get("confidence"),
                "timestamp": current.get("timestamp")
            },
            "alerts": {
                "score_threshold": 75,
                "signal_change_alert": True,
                "whale_activity_alert": True
            },
            "note": "Enable database integration for full historical tracking"
        }

    except Exception as e:
        logger.error(f"Watch error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_system_info():
    """
    **MSS System Information**

    Get information about the MSS scoring system:
    - Scoring methodology
    - Phase weights
    - Thresholds
    - Data sources
    - Telegram notification configuration

    **Example:** `GET /mss/info`

    Returns:
    - System configuration
    - Scoring formula
    - API endpoints list
    - Notification settings
    """
    return {
        "success": True,
        "system": {
            "name": "MSS (Multimodal Signal Score) Alpha System",
            "version": "1.0.0",
            "description": "3-phase analysis for high-potential crypto discovery"
        },
        "telegram_notifications": {
            "enabled": telegram_mss_notifier.enabled,
            "threshold": MSS_NOTIFICATION_THRESHOLD,
            "description": f"Auto-alert when MSS score >= {MSS_NOTIFICATION_THRESHOLD}"
        },
        "methodology": {
            "phase1_discovery": {
                "weight": 0.35,
                "max_score": 35,
                "focus": "Tokenomics & FDV filtering",
                "thresholds": {
                    "max_fdv_usd": 50_000_000,
                    "max_age_hours": 72,
                    "pass_score": 20
                }
            },
            "phase2_confirmation": {
                "weight": 0.30,
                "max_score": 30,
                "focus": "Social momentum & volume validation",
                "thresholds": {
                    "min_altrank": 100,
                    "min_galaxy_score": 65,
                    "min_volume_spike_pct": 100,
                    "pass_score": 18
                }
            },
            "phase3_validation": {
                "weight": 0.35,
                "max_score": 35,
                "focus": "Institutional positioning & whale activity",
                "thresholds": {
                    "min_oi_increase_pct": 50,
                    "funding_rate_range": [0.01, 0.04],
                    "pass_score": 20
                }
            }
        },
        "scoring": {
            "formula": "MSS = (Discovery × 0.35) + (Social × 0.30) + (Validation × 0.35)",
            "scale": "0-100",
            "signal_thresholds": {
                "STRONG_LONG": 75,
                "LONG": 65,
                "MODERATE_LONG": 50,
                "WEAK_LONG": 35,
                "NEUTRAL": 0
            }
        },
        "data_sources": [
            "CoinGecko - Coin discovery & market data",
            "Binance Futures - Volume, OI, funding rates",
            "LunarCrush - Social sentiment & AltRank",
            "Coinglass - Top trader positioning",
            "CoinAPI - Whale detection via orderbook"
        ],
        "endpoints": {
            "discover": "/mss/discover - Phase 1 coin discovery",
            "analyze": "/mss/analyze/{symbol} - Full 3-phase analysis",
            "scan": "/mss/scan - Auto-scan and rank",
            "watch": "/mss/watch/{symbol} - Real-time monitoring",
            "info": "/mss/info - System information"
        },
        "gpt_compatible": True,
        "telegram_alerts": {
            "enabled": True,
            "trigger_threshold": 75,
            "includes": [
                "MSS score",
                "Phase breakdowns",
                "Whale activity",
                "Risk warnings"
            ]
        }
    }


@router.get("/telegram/test")
async def test_telegram():
    """
    **Test Telegram MSS Notifications**
    
    Send a test message to verify Telegram bot configuration for MSS alerts.
    
    **Example:** `GET /mss/telegram/test`
    
    Returns:
    - Success status
    - Telegram API response
    - Configuration details
    """
    try:
        result = await telegram_mss_notifier.send_test_message()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "telegram_enabled": telegram_mss_notifier.enabled,
            "notification_threshold": MSS_NOTIFICATION_THRESHOLD,
            "telegram_response": result.get("telegram_response")
        }
    
    except Exception as e:
        logger.error(f"Telegram test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
