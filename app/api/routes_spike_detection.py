"""
Spike Detection System API Routes
Provides status and control endpoints for real-time spike detection
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.realtime_spike_detector import realtime_spike_detector
from app.services.liquidation_spike_detector import liquidation_spike_detector
from app.services.social_spike_monitor import social_spike_monitor
from app.services.spike_coordinator import spike_coordinator
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/spike-detection", tags=["Spike Detection System"])


@router.get("/status", summary="Get overall spike detection system status")
async def get_spike_detection_status() -> Dict[str, Any]:
    """
    Get comprehensive status of all spike detection components

    Returns:
    - Status of each detector (price, liquidation, social)
    - Spike coordinator status
    - System health metrics
    """
    try:
        # Get status from all detectors
        price_status = await realtime_spike_detector.get_status()
        liquidation_status = await liquidation_spike_detector.get_status()
        social_status = await social_spike_monitor.get_status()
        coordinator_status = await spike_coordinator.get_status()

        return {
            "success": True,
            "system_status": "ACTIVE",
            "detectors": {
                "price_spike_detector": {
                    "is_running": price_status["is_running"],
                    "check_interval": price_status["check_interval"],
                    "spike_threshold": f"{price_status['spike_threshold']}%",
                    "coins_tracked": price_status["coins_tracked"],
                    "total_alerts_sent": price_status["total_alerts_sent"],
                    "last_check": price_status["last_check_time"]
                },
                "liquidation_spike_detector": {
                    "is_running": liquidation_status["is_running"],
                    "check_interval": liquidation_status["check_interval"],
                    "extreme_threshold": f"${liquidation_status['extreme_threshold']:,.0f}",
                    "high_threshold": f"${liquidation_status['high_threshold']:,.0f}",
                    "coins_tracked": liquidation_status["coins_tracked"],
                    "total_alerts_sent": liquidation_status["total_alerts_sent"],
                    "last_check": liquidation_status["last_check_time"]
                },
                "social_spike_monitor": {
                    "is_running": social_status["is_running"],
                    "check_interval": social_status["check_interval"],
                    "min_spike_threshold": f"{social_status['min_spike_threshold']}%",
                    "top_coins_count": social_status["top_coins_count"],
                    "total_spikes_detected": social_status["total_spikes_detected"],
                    "last_check": social_status["last_check_time"]
                }
            },
            "spike_coordinator": {
                "correlation_window": f"{coordinator_status['correlation_window_seconds']}s",
                "active_symbols": coordinator_status["active_symbols"],
                "total_recent_signals": coordinator_status["total_recent_signals"],
                "correlated_spikes_detected": coordinator_status["correlated_spikes_detected"],
                "alerts_sent": coordinator_status["alerts_sent"],
                "monitored_symbols": coordinator_status["monitored_symbols"][:20]  # Show first 20
            },
            "configuration": {
                "price_spike_threshold": "8% in 5 minutes",
                "liquidation_thresholds": {
                    "market_wide": "$50M in 1 hour",
                    "per_coin": "$20M in 1 hour"
                },
                "social_spike_threshold": "100% volume increase",
                "alert_channel": "Telegram (instant, no cooldown)",
                "monitoring_scope": "Top 100 coins by market cap"
            }
        }

    except Exception as e:
        logger.error(f"Error getting spike detection status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/price-detector/status", summary="Get price spike detector status")
async def get_price_detector_status() -> Dict[str, Any]:
    """Get detailed status of real-time price spike detector"""
    try:
        status = await realtime_spike_detector.get_status()

        return {
            "success": True,
            "detector": "Real-Time Price Spike Detector",
            **status
        }

    except Exception as e:
        logger.error(f"Error getting price detector status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/liquidation-detector/status", summary="Get liquidation spike detector status")
async def get_liquidation_detector_status() -> Dict[str, Any]:
    """Get detailed status of liquidation spike detector"""
    try:
        status = await liquidation_spike_detector.get_status()

        return {
            "success": True,
            "detector": "Liquidation Spike Detector",
            **status
        }

    except Exception as e:
        logger.error(f"Error getting liquidation detector status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-monitor/status", summary="Get social spike monitor status")
async def get_social_monitor_status() -> Dict[str, Any]:
    """Get detailed status of social spike monitor"""
    try:
        status = await social_spike_monitor.get_status()

        return {
            "success": True,
            "monitor": "Social Spike Monitor",
            **status
        }

    except Exception as e:
        logger.error(f"Error getting social monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coordinator/status", summary="Get spike coordinator status")
async def get_coordinator_status() -> Dict[str, Any]:
    """Get detailed status of multi-signal correlation coordinator"""
    try:
        status = await spike_coordinator.get_status()

        return {
            "success": True,
            "coordinator": "Spike Correlation Engine",
            **status
        }

    except Exception as e:
        logger.error(f"Error getting coordinator status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Quick health check for spike detection system")
async def health_check() -> Dict[str, Any]:
    """
    Quick health check - are all detectors running?

    Returns:
    - Overall system health
    - Status of each component
    """
    try:
        price_running = realtime_spike_detector.is_running
        liquidation_running = liquidation_spike_detector.is_running
        social_running = social_spike_monitor.is_running

        all_running = price_running and liquidation_running and social_running

        return {
            "success": True,
            "system_health": "HEALTHY" if all_running else "DEGRADED",
            "components": {
                "price_spike_detector": "RUNNING" if price_running else "STOPPED",
                "liquidation_spike_detector": "RUNNING" if liquidation_running else "STOPPED",
                "social_spike_monitor": "RUNNING" if social_running else "STOPPED",
                "spike_coordinator": "ACTIVE"
            },
            "all_systems_operational": all_running
        }

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "success": False,
            "system_health": "ERROR",
            "error": str(e)
        }
