"""
CryptoSatX Monitoring API Routes
Automated signal monitoring and alerting endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio

from ..services.monitoring_service import get_monitoring_service, start_monitoring, stop_monitoring
from ..services.telegram_notifier import TelegramNotifier
from ..services.social_spike_monitor import social_spike_monitor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.post("/start")
async def start_monitoring_service():
    """Start the automated monitoring service"""
    try:
        await start_monitoring()
        return {
            "success": True,
            "message": "Monitoring service started successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_monitoring_service():
    """Stop the automated monitoring service"""
    try:
        await stop_monitoring()
        return {
            "success": True,
            "message": "Monitoring service stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_monitoring_status():
    """Get current monitoring service status"""
    try:
        service = await get_monitoring_service()
        status = await service.get_monitoring_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_recent_alerts(limit: int = Query(50, ge=1, le=200)):
    """Get recent monitoring alerts"""
    try:
        service = await get_monitoring_service()
        alerts = await service.get_recent_alerts(limit)
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/symbols/add")
async def add_monitoring_symbol(symbol: str):
    """Add a symbol to monitoring"""
    try:
        service = await get_monitoring_service()
        await service.add_symbol(symbol.upper())
        return {
            "success": True,
            "message": f"Added {symbol.upper()} to monitoring",
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to add symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/symbols/{symbol}")
async def remove_monitoring_symbol(symbol: str):
    """Remove a symbol from monitoring"""
    try:
        service = await get_monitoring_service()
        await service.remove_symbol(symbol.upper())
        return {
            "success": True,
            "message": f"Removed {symbol.upper()} from monitoring",
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to remove symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_monitoring_config(
    check_interval_minutes: Optional[int] = None,
    strong_signal_threshold: Optional[float] = None,
    weak_signal_threshold: Optional[float] = None,
    max_alerts_per_hour: Optional[int] = None,
    enable_telegram: Optional[bool] = None
):
    """Update monitoring configuration"""
    try:
        service = await get_monitoring_service()
        
        # Build update dict
        updates = {}
        if check_interval_minutes is not None:
            updates['check_interval_minutes'] = check_interval_minutes
        if strong_signal_threshold is not None:
            updates['strong_signal_threshold'] = strong_signal_threshold
        if weak_signal_threshold is not None:
            updates['weak_signal_threshold'] = weak_signal_threshold
        if max_alerts_per_hour is not None:
            updates['max_alerts_per_hour'] = max_alerts_per_hour
        if enable_telegram is not None:
            updates['enable_telegram'] = enable_telegram
        
        if not updates:
            raise HTTPException(status_code=400, detail="No configuration parameters provided")
        
        await service.update_config(**updates)
        
        return {
            "success": True,
            "message": "Monitoring configuration updated",
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check/{symbol}")
async def check_symbol_now(symbol: str, background_tasks: BackgroundTasks):
    """Immediately check a specific symbol and send alerts if needed"""
    try:
        service = await get_monitoring_service()
        
        # Check symbol in background
        background_tasks.add_task(service._check_symbol, symbol.upper())
        
        return {
            "success": True,
            "message": f"Checking {symbol.upper()} now...",
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to check symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-alert/{symbol}")
async def test_alert(symbol: str):
    """Send a test alert for a symbol"""
    try:
        # Create test signal data
        test_signal = {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "signal": "TEST",
            "score": 99.9,
            "confidence": "very_high",
            "price": 0.0,
            "reasons": ["This is a test alert", "Monitoring system is working"],
            "metrics": {
                "fundingRate": 0.0,
                "openInterest": 0.0,
                "socialScore": 100.0,
                "priceTrend": "test"
            }
        }
        
        # Send test alert
        telegram = TelegramNotifier()
        message = f"""
🧪 CRYPTOSATX TEST ALERT 🧪

📊 Symbol: {symbol.upper()}
🧪 Signal: TEST
📈 Score: 99.9
🔒 Confidence: VERY HIGH

📊 Analysis:
• This is a test alert
• Monitoring system is working
• All systems operational

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 Powered by CryptoSatX AI
        """.strip()
        
        result = await telegram.send_signal_alert(test_signal)
        
        return {
            "success": True,
            "message": f"Test alert sent for {symbol.upper()}",
            "symbol": symbol.upper(),
            "telegram_result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send test alert for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def monitoring_health_check():
    """Health check for monitoring service"""
    try:
        service = await get_monitoring_service()
        status = await service.get_monitoring_status()
        
        # Check if monitoring is healthy
        health_status = "healthy"
        issues = []
        
        if not status['running']:
            health_status = "stopped"
            issues.append("Monitoring service is not running")
        
        if not status['symbols']:
            health_status = "warning"
            issues.append("No symbols configured for monitoring")
        
        # Check Telegram configuration
        telegram = TelegramNotifier()
        if not telegram.enabled:
            health_status = "warning"
            issues.append("Telegram not configured")
        
        return {
            "success": True,
            "status": health_status,
            "issues": issues,
            "monitoring_status": status,
            "telegram_configured": telegram.enabled,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/stats")
async def get_monitoring_stats():
    """Get monitoring statistics"""
    try:
        service = await get_monitoring_service()
        status = await service.get_monitoring_status()
        alerts = await service.get_recent_alerts(100)  # Get last 100 alerts
        
        # Calculate statistics
        total_alerts = len(alerts)
        total_symbols = len(status['symbols'])
        
        # Alert type distribution
        alert_types = {}
        for alert in alerts:
            for alert_type in alert.get('alert_types', []):
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        # Symbol alert distribution
        symbol_alerts = {}
        for alert in alerts:
            symbol = alert.get('symbol', 'UNKNOWN')
            symbol_alerts[symbol] = symbol_alerts.get(symbol, 0) + 1
        
        # Recent activity (last 24 hours)
        now = datetime.now()
        recent_alerts = [
            alert for alert in alerts 
            if datetime.fromisoformat(alert.get('timestamp', '').replace('Z', '+00:00')) > now - timedelta(hours=24)
        ]
        
        return {
            "success": True,
            "data": {
                "monitoring_running": status['running'],
                "total_symbols": total_symbols,
                "total_alerts": total_alerts,
                "recent_alerts_24h": len(recent_alerts),
                "alert_types": alert_types,
                "symbol_alerts": symbol_alerts,
                "check_interval_minutes": status['check_interval_minutes'],
                "strong_signal_threshold": status['strong_signal_threshold'],
                "weak_signal_threshold": status['weak_signal_threshold']
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spike-monitor/status")
async def get_spike_monitor_status():
    """
    Get social spike monitor status
    
    Returns monitoring configuration, last check time, and recent spike detections
    for viral moment detection system.
    """
    try:
        status = await social_spike_monitor.get_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get spike monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spike-monitor/start")
async def start_spike_monitor():
    """
    Start social spike monitor for viral moments
    
    Monitors top 50 coins every 5 minutes for social volume spikes >100%.
    Sends automated Telegram alerts when viral moments are detected.
    """
    try:
        if social_spike_monitor.is_running:
            return {
                "success": False,
                "message": "Spike monitor already running",
                "timestamp": datetime.now().isoformat()
            }
        
        asyncio.create_task(social_spike_monitor.start())
        await asyncio.sleep(1)
        
        logger.info("Social spike monitor started")
        
        return {
            "success": True,
            "message": "Social spike monitor started - monitoring viral moments",
            "config": {
                "check_interval": f"{social_spike_monitor.check_interval}s",
                "min_spike_threshold": f"{social_spike_monitor.min_spike_threshold}%",
                "top_coins_count": social_spike_monitor.top_coins_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start spike monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spike-monitor/stop")
async def stop_spike_monitor():
    """Stop social spike monitor"""
    try:
        if not social_spike_monitor.is_running:
            return {
                "success": False,
                "message": "Spike monitor not running",
                "timestamp": datetime.now().isoformat()
            }
        
        social_spike_monitor.stop()
        logger.info("Social spike monitor stopped")
        
        return {
            "success": True,
            "message": "Social spike monitor stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop spike monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
