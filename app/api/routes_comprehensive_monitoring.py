"""
CryptoSatX Comprehensive Monitoring API Routes
API endpoints for managing multi-coin, multi-timeframe intelligent monitoring
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.services.comprehensive_monitor import get_comprehensive_monitor, AlertSeverity
from app.storage.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/comprehensive-monitoring", tags=["comprehensive-monitoring"])


# Request/Response Models
class AddCoinRequest(BaseModel):
    """Request model for adding a coin to watchlist"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    exchange: str = Field(default="binance", description="Exchange name")
    priority: int = Field(default=1, ge=1, le=10, description="Monitoring priority (1-10)")
    check_interval_seconds: int = Field(default=300, ge=60, le=3600, description="Check interval in seconds")
    timeframes: List[str] = Field(default=["5m", "15m", "1h", "4h"], description="Timeframes to monitor")
    metrics_enabled: Dict[str, bool] = Field(
        default={"price": True, "volume": True, "funding": True, "open_interest": True, "liquidations": True},
        description="Metrics to track"
    )


class BulkAddCoinsRequest(BaseModel):
    """Request model for adding multiple coins"""
    symbols: List[str] = Field(..., min_items=1, max_items=50, description="List of symbols to monitor")
    exchange: str = Field(default="binance")
    priority: int = Field(default=1, ge=1, le=10)
    check_interval_seconds: int = Field(default=300, ge=60, le=3600)
    timeframes: List[str] = Field(default=["5m", "15m", "1h", "4h"])
    metrics_enabled: Dict[str, bool] = Field(
        default={"price": True, "volume": True, "funding": True, "open_interest": True, "liquidations": True}
    )


class AddRuleRequest(BaseModel):
    """Request model for adding a monitoring rule"""
    symbol: str = Field(..., description="Symbol to apply rule to")
    rule_type: str = Field(..., description="Type of rule (price_threshold, volume_threshold, funding_threshold, oi_change)")
    rule_name: str = Field(..., description="Name of the rule")
    condition: Dict[str, Any] = Field(..., description="Rule condition parameters")
    timeframe: Optional[str] = Field(default="1h", description="Timeframe for the rule")
    priority: int = Field(default=1, ge=1, le=10)
    enabled: bool = Field(default=True)
    cooldown_minutes: int = Field(default=60, ge=0, le=1440, description="Cooldown period in minutes")


# Routes
@router.post("/start")
async def start_monitoring():
    """
    Start the comprehensive monitoring service

    Begins monitoring all coins in the watchlist across multiple timeframes and metrics.
    """
    try:
        monitor = get_comprehensive_monitor()
        await monitor.start()

        return {
            "success": True,
            "message": "Comprehensive monitoring started",
            "status": await monitor.get_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start comprehensive monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_monitoring():
    """Stop the comprehensive monitoring service"""
    try:
        monitor = get_comprehensive_monitor()
        await monitor.stop()

        return {
            "success": True,
            "message": "Comprehensive monitoring stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop comprehensive monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get comprehensive monitoring status

    Returns:
    - Running status
    - Number of coins monitored
    - Total rules
    - Watchlist details
    """
    try:
        monitor = get_comprehensive_monitor()
        status = await monitor.get_status()

        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/add")
async def add_coin(request: AddCoinRequest):
    """
    Add a single coin to watchlist

    Example:
    ```json
    {
      "symbol": "FILUSDT",
      "priority": 2,
      "check_interval_seconds": 300,
      "timeframes": ["5m", "15m", "1h", "4h"],
      "metrics_enabled": {
        "price": true,
        "volume": true,
        "funding": true,
        "open_interest": true,
        "liquidations": true
      }
    }
    ```
    """
    try:
        monitor = get_comprehensive_monitor()

        coin = await monitor.add_coin(
            symbol=request.symbol.upper(),
            exchange=request.exchange,
            priority=request.priority,
            check_interval_seconds=request.check_interval_seconds,
            timeframes=request.timeframes,
            metrics_enabled=request.metrics_enabled
        )

        return {
            "success": True,
            "message": f"Added {request.symbol} to watchlist",
            "data": {
                "id": coin.id,
                "symbol": coin.symbol,
                "exchange": coin.exchange,
                "priority": coin.priority,
                "check_interval_seconds": coin.check_interval_seconds,
                "timeframes": coin.timeframes,
                "metrics_enabled": coin.metrics_enabled
            },
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add coin: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/bulk-add")
async def bulk_add_coins(request: BulkAddCoinsRequest):
    """
    Add multiple coins to watchlist at once

    Useful for adding coins from scan results.

    Example:
    ```json
    {
      "symbols": ["FILUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT"],
      "priority": 2,
      "check_interval_seconds": 300,
      "timeframes": ["5m", "1h", "4h"]
    }
    ```
    """
    try:
        monitor = get_comprehensive_monitor()
        added_coins = []
        failed_coins = []

        for symbol in request.symbols:
            try:
                coin = await monitor.add_coin(
                    symbol=symbol.upper(),
                    exchange=request.exchange,
                    priority=request.priority,
                    check_interval_seconds=request.check_interval_seconds,
                    timeframes=request.timeframes,
                    metrics_enabled=request.metrics_enabled
                )
                added_coins.append(symbol.upper())
            except Exception as e:
                failed_coins.append({"symbol": symbol.upper(), "error": str(e)})
                logger.warning(f"Failed to add {symbol}: {e}")

        return {
            "success": True,
            "message": f"Added {len(added_coins)} coins to watchlist",
            "data": {
                "added": added_coins,
                "failed": failed_coins,
                "total_requested": len(request.symbols),
                "total_added": len(added_coins)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to bulk add coins: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
async def remove_coin(symbol: str):
    """Remove a coin from watchlist"""
    try:
        monitor = get_comprehensive_monitor()
        await monitor.remove_coin(symbol.upper())

        return {
            "success": True,
            "message": f"Removed {symbol} from watchlist",
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove coin: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(
    status: Optional[str] = Query(None, description="Filter by status (active, paused, stopped)"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get all coins in watchlist

    Returns detailed information about each monitored coin including:
    - Current status
    - Last check time
    - Alert statistics
    - Monitoring configuration
    """
    try:
        query = "SELECT * FROM coin_watchlist"
        params = []

        if status:
            query += " WHERE status = $1"
            params.append(status)

        query += " ORDER BY priority DESC, created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        async with db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        watchlist = [
            {
                "id": row['id'],
                "symbol": row['symbol'],
                "exchange": row['exchange'],
                "status": row['status'],
                "priority": row['priority'],
                "check_interval_seconds": row['check_interval_seconds'],
                "timeframes": row['timeframes'],
                "metrics_enabled": row['metrics_enabled'],
                "last_check_at": row['last_check_at'].isoformat() if row['last_check_at'] else None,
                "last_alert_at": row['last_alert_at'].isoformat() if row['last_alert_at'] else None,
                "alert_count": row['alert_count'],
                "created_at": row['created_at'].isoformat()
            }
            for row in rows
        ]

        return {
            "success": True,
            "data": {
                "watchlist": watchlist,
                "count": len(watchlist),
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/{symbol}")
async def get_coin_details(symbol: str):
    """Get detailed information about a specific coin"""
    try:
        query = "SELECT * FROM coin_watchlist WHERE symbol = $1"
        async with db.acquire() as conn:
            row = await conn.fetchrow(query, symbol.upper())

        if not row:
            raise HTTPException(status_code=404, detail=f"Coin {symbol} not in watchlist")

        # Get rules for this coin
        rules_query = "SELECT * FROM monitoring_rules WHERE watchlist_id = $1 ORDER BY priority DESC"
        async with db.acquire() as conn:
            rules_rows = await conn.fetch(rules_query, row['id'])

        rules = [
            {
                "id": r['id'],
                "rule_type": r['rule_type'],
                "rule_name": r['rule_name'],
                "condition": r['condition'],
                "timeframe": r['timeframe'],
                "enabled": r['enabled'],
                "trigger_count": r['trigger_count'],
                "last_triggered_at": r['last_triggered_at'].isoformat() if r['last_triggered_at'] else None
            }
            for r in rules_rows
        ]

        # Get recent alerts
        alerts_query = """
            SELECT * FROM monitoring_alerts
            WHERE watchlist_id = $1
            ORDER BY created_at DESC
            LIMIT 10
        """
        async with db.acquire() as conn:
            alerts_rows = await conn.fetch(alerts_query, row['id'])

        recent_alerts = [
            {
                "id": a['id'],
                "alert_type": a['alert_type'],
                "severity": a['severity'],
                "title": a['title'],
                "message": a['message'],
                "price": float(a['price']) if a['price'] else None,
                "telegram_sent": a['telegram_sent'],
                "created_at": a['created_at'].isoformat()
            }
            for a in alerts_rows
        ]

        return {
            "success": True,
            "data": {
                "coin": {
                    "id": row['id'],
                    "symbol": row['symbol'],
                    "exchange": row['exchange'],
                    "status": row['status'],
                    "priority": row['priority'],
                    "check_interval_seconds": row['check_interval_seconds'],
                    "timeframes": row['timeframes'],
                    "metrics_enabled": row['metrics_enabled'],
                    "last_check_at": row['last_check_at'].isoformat() if row['last_check_at'] else None,
                    "last_alert_at": row['last_alert_at'].isoformat() if row['last_alert_at'] else None,
                    "alert_count": row['alert_count'],
                    "created_at": row['created_at'].isoformat()
                },
                "rules": rules,
                "recent_alerts": recent_alerts
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get coin details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/add")
async def add_rule(request: AddRuleRequest):
    """
    Add a monitoring rule for a coin

    Example price threshold rule:
    ```json
    {
      "symbol": "FILUSDT",
      "rule_type": "price_threshold",
      "rule_name": "FIL Long Entry",
      "condition": {
        "price": 1.980,
        "operator": "above"
      },
      "timeframe": "1h",
      "priority": 2,
      "cooldown_minutes": 60
    }
    ```

    Example volume spike rule:
    ```json
    {
      "symbol": "FILUSDT",
      "rule_type": "volume_threshold",
      "rule_name": "FIL Volume Spike",
      "condition": {
        "threshold_pct": 200
      },
      "timeframe": "1h"
    }
    ```
    """
    try:
        # Get watchlist coin
        coin_query = "SELECT id FROM coin_watchlist WHERE symbol = $1"
        async with db.acquire() as conn:
            coin_row = await conn.fetchrow(coin_query, request.symbol.upper())

        if not coin_row:
            raise HTTPException(status_code=404, detail=f"Coin {request.symbol} not in watchlist. Add it first.")

        watchlist_id = coin_row['id']

        # Insert rule
        insert_query = """
            INSERT INTO monitoring_rules
            (watchlist_id, rule_type, rule_name, condition, timeframe, priority, enabled, cooldown_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """

        import json
        async with db.acquire() as conn:
            rule_row = await conn.fetchrow(
                insert_query,
                watchlist_id,
                request.rule_type,
                request.rule_name,
                json.dumps(request.condition),
                request.timeframe,
                request.priority,
                request.enabled,
                request.cooldown_minutes
            )

        # Reload rules in monitor
        monitor = get_comprehensive_monitor()
        await monitor._load_rules()

        return {
            "success": True,
            "message": f"Added rule '{request.rule_name}' for {request.symbol}",
            "data": {
                "id": rule_row['id'],
                "rule_type": rule_row['rule_type'],
                "rule_name": rule_row['rule_name'],
                "condition": rule_row['condition'],
                "timeframe": rule_row['timeframe'],
                "enabled": rule_row['enabled']
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete a monitoring rule"""
    try:
        # Check if rule exists
        async with db.acquire() as conn:
            rule = await conn.fetchrow("SELECT * FROM monitoring_rules WHERE id = $1", rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        # Delete rule
        async with db.acquire() as conn:
            await conn.execute("DELETE FROM monitoring_rules WHERE id = $1", rule_id)

        # Reload rules in monitor
        monitor = get_comprehensive_monitor()
        await monitor._load_rules()

        return {
            "success": True,
            "message": f"Deleted rule '{rule['rule_name']}'",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get monitoring alerts history

    Retrieve alerts with optional filters:
    - By symbol
    - By alert type
    - By severity
    - By time range
    """
    try:
        query = "SELECT * FROM monitoring_alerts WHERE created_at >= $1"
        params = [datetime.now() - timedelta(hours=hours)]
        param_count = 1

        if symbol:
            param_count += 1
            query += f" AND symbol = ${param_count}"
            params.append(symbol.upper())

        if alert_type:
            param_count += 1
            query += f" AND alert_type = ${param_count}"
            params.append(alert_type)

        if severity:
            param_count += 1
            query += f" AND severity = ${param_count}"
            params.append(severity)

        param_count += 1
        query += f" ORDER BY created_at DESC LIMIT ${param_count}"
        params.append(limit)

        async with db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        alerts = [
            {
                "id": row['id'],
                "symbol": row['symbol'],
                "alert_type": row['alert_type'],
                "severity": row['severity'],
                "title": row['title'],
                "message": row['message'],
                "price": float(row['price']) if row['price'] else None,
                "timeframe": row['timeframe'],
                "metrics": row['metrics'],
                "analysis": row['analysis'],
                "recommendations": row['recommendations'],
                "telegram_sent": row['telegram_sent'],
                "telegram_sent_at": row['telegram_sent_at'].isoformat() if row['telegram_sent_at'] else None,
                "created_at": row['created_at'].isoformat()
            }
            for row in rows
        ]

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "filters": {
                    "symbol": symbol,
                    "alert_type": alert_type,
                    "severity": severity,
                    "hours": hours
                },
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{alert_id}")
async def get_alert_details(alert_id: int):
    """Get detailed information about a specific alert"""
    try:
        query = "SELECT * FROM monitoring_alerts WHERE id = $1"
        async with db.acquire() as conn:
            row = await conn.fetchrow(query, alert_id)

        if not row:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        return {
            "success": True,
            "data": {
                "id": row['id'],
                "symbol": row['symbol'],
                "alert_type": row['alert_type'],
                "severity": row['severity'],
                "title": row['title'],
                "message": row['message'],
                "price": float(row['price']) if row['price'] else None,
                "timeframe": row['timeframe'],
                "metrics": row['metrics'],
                "analysis": row['analysis'],
                "recommendations": row['recommendations'],
                "telegram_sent": row['telegram_sent'],
                "telegram_sent_at": row['telegram_sent_at'].isoformat() if row['telegram_sent_at'] else None,
                "created_at": row['created_at'].isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_monitoring_stats():
    """
    Get comprehensive monitoring statistics

    Returns:
    - Total coins monitored
    - Total alerts sent
    - Alerts by type and severity
    - Most active coins
    - Rule effectiveness
    """
    try:
        # Get watchlist stats
        async with db.acquire() as conn:
            watchlist_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_coins,
                    COUNT(*) FILTER (WHERE status = 'active') as active_coins,
                    SUM(alert_count) as total_alerts
                FROM coin_watchlist
            """)

        # Get alert stats by type
        async with db.acquire() as conn:
            alert_type_stats = await conn.fetch("""
                SELECT alert_type, COUNT(*) as count
                FROM monitoring_alerts
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY alert_type
                ORDER BY count DESC
            """)

        # Get alert stats by severity
        async with db.acquire() as conn:
            severity_stats = await conn.fetch("""
                SELECT severity, COUNT(*) as count
                FROM monitoring_alerts
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY severity
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
            """)

        # Get most active coins
        async with db.acquire() as conn:
            most_active = await conn.fetch("""
                SELECT symbol, alert_count, last_alert_at
                FROM coin_watchlist
                WHERE status = 'active'
                ORDER BY alert_count DESC
                LIMIT 10
            """)

        # Get rule stats
        async with db.acquire() as conn:
            rule_stats = await conn.fetch("""
                SELECT rule_type, COUNT(*) as total_rules, SUM(trigger_count) as total_triggers
                FROM monitoring_rules
                WHERE enabled = true
                GROUP BY rule_type
                ORDER BY total_triggers DESC
            """)

        return {
            "success": True,
            "data": {
                "watchlist": {
                    "total_coins": watchlist_stats['total_coins'] if watchlist_stats else 0,
                    "active_coins": watchlist_stats['active_coins'] if watchlist_stats else 0,
                    "total_alerts": watchlist_stats['total_alerts'] if watchlist_stats else 0
                },
                "alerts_24h": {
                    "by_type": [{"type": row['alert_type'], "count": row['count']} for row in alert_type_stats],
                    "by_severity": [{"severity": row['severity'], "count": row['count']} for row in severity_stats]
                },
                "most_active_coins": [
                    {
                        "symbol": row['symbol'],
                        "alert_count": row['alert_count'],
                        "last_alert_at": row['last_alert_at'].isoformat() if row['last_alert_at'] else None
                    }
                    for row in most_active
                ],
                "rules": [
                    {
                        "rule_type": row['rule_type'],
                        "total_rules": row['total_rules'],
                        "total_triggers": row['total_triggers'] or 0
                    }
                    for row in rule_stats
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for comprehensive monitoring service"""
    try:
        monitor = get_comprehensive_monitor()
        status = await monitor.get_status()

        health_status = "healthy"
        issues = []

        if not status['running']:
            health_status = "stopped"
            issues.append("Monitoring service is not running")

        if status['coins_monitored'] == 0:
            health_status = "warning"
            issues.append("No coins in watchlist")

        if not status['telegram_enabled']:
            health_status = "warning"
            issues.append("Telegram notifications not configured")

        return {
            "success": True,
            "status": health_status,
            "issues": issues,
            "monitoring_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
