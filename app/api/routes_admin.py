"""
Admin API Routes for CryptoSatX
Dynamic weight adjustment dan system management
"""
import os
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.services.dynamic_weight_service import dynamic_weight_service, WeightHistory
from app.services.metrics_service import metrics_service
from app.utils.logger import default_logger

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()
logger = default_logger


# Pydantic models untuk request/response
class WeightUpdateRequest(BaseModel):
    factor: str = Field(..., description="Factor name to update")
    new_weight: float = Field(..., ge=0, le=1, description="New weight value (0-1)")
    reason: str = Field("", description="Reason for weight change")


class WeightResetRequest(BaseModel):
    reason: str = Field("", description="Reason for reset")


class ABTestRequest(BaseModel):
    test_name: str = Field(..., description="Test identifier")
    variant_weights: Dict[str, Dict[str, float]] = Field(..., description="Variant weight configurations")
    traffic_split: Optional[Dict[str, float]] = Field(None, description="Traffic split percentage")


class AutoOptimizationRequest(BaseModel):
    enabled: bool = Field(True, description="Enable auto-optimization")
    interval: int = Field(3600, description="Optimization interval in seconds")
    min_sample_size: int = Field(100, description="Minimum sample size")
    accuracy_threshold: float = Field(0.6, description="Accuracy threshold")


# Admin authentication (simplified untuk production)
async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin credentials"""
    # In production, ini harus validasi dengan proper authentication
    # Untuk sekarang, kita gunakan simple token validation
    admin_token = credentials.credentials
    
    # Check against environment variable atau database
    valid_tokens = [
        os.getenv("ADMIN_TOKEN", "admin-token-123"),
        "dev-admin-token"  # Development token
    ]
    
    if admin_token not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    return {"admin_id": "admin", "token": admin_token}


@router.get("/weights/current")
async def get_current_weights(admin: Dict = Depends(verify_admin)):
    """Get current active weights"""
    try:
        weights = dynamic_weight_service.get_current_weights()
        return {
            "status": "success",
            "data": {
                "weights": weights,
                "total_weight": sum(weights.values()),
                "last_updated": dynamic_weight_service.get_weight_config_summary()["last_updated"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting current weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights/update")
async def update_weight(
    request: WeightUpdateRequest,
    admin: Dict = Depends(verify_admin)
):
    """Update weight untuk specific factor"""
    try:
        success = dynamic_weight_service.update_weight(
            factor=request.factor,
            new_weight=request.new_weight,
            updated_by=admin["admin_id"],
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update weight"
            )
        
        return {
            "status": "success",
            "message": f"Weight updated for {request.factor}",
            "data": {
                "factor": request.factor,
                "new_weight": request.new_weight,
                "updated_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating weight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights/reset")
async def reset_weights(
    request: WeightResetRequest,
    admin: Dict = Depends(verify_admin)
):
    """Reset all weights to default values"""
    try:
        success = dynamic_weight_service.reset_to_default(
            updated_by=admin["admin_id"],
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to reset weights"
            )
        
        return {
            "status": "success",
            "message": "Weights reset to default values",
            "data": {
                "reset_by": admin["admin_id"],
                "reason": request.reason,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights/history")
async def get_weight_history(
    factor: Optional[str] = Query(None, description="Filter by factor"),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    admin: Dict = Depends(verify_admin)
):
    """Get weight change history"""
    try:
        history = dynamic_weight_service.get_weight_history(
            factor=factor,
            days_back=days_back
        )
        
        return {
            "status": "success",
            "data": {
                "history": [entry.dict() for entry in history],
                "count": len(history),
                "filter": {
                    "factor": factor,
                    "days_back": days_back
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting weight history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights/performance")
async def get_performance_metrics(
    factor: Optional[str] = Query(None, description="Filter by factor"),
    admin: Dict = Depends(verify_admin)
):
    """Get performance metrics untuk factors"""
    try:
        metrics = dynamic_weight_service.get_performance_metrics(factor=factor)
        
        return {
            "status": "success",
            "data": {
                "metrics": {
                    factor: metric.dict() for factor, metric in metrics.items()
                },
                "count": len(metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights/importance")
async def get_factor_importance(admin: Dict = Depends(verify_admin)):
    """Get factor importance scores"""
    try:
        importance = dynamic_weight_service.calculate_factor_importance()
        
        return {
            "status": "success",
            "data": {
                "importance_scores": importance,
                "total_importance": sum(importance.values())
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating factor importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/create")
async def create_ab_test(
    request: ABTestRequest,
    admin: Dict = Depends(verify_admin)
):
    """Create A/B test untuk weight variations"""
    try:
        success = dynamic_weight_service.create_ab_test(
            test_name=request.test_name,
            variant_weights=request.variant_weights,
            traffic_split=request.traffic_split or {}
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to create A/B test"
            )
        
        return {
            "status": "success",
            "message": f"A/B test created: {request.test_name}",
            "data": {
                "test_name": request.test_name,
                "variants": request.variant_weights,
                "traffic_split": request.traffic_split,
                "created_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/list")
async def list_ab_tests(admin: Dict = Depends(verify_admin)):
    """List all active A/B tests"""
    try:
        tests = dynamic_weight_service.ab_test_configs
        
        return {
            "status": "success",
            "data": {
                "tests": tests,
                "count": len(tests)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing A/B tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-optimization/configure")
async def configure_auto_optimization(
    request: AutoOptimizationRequest,
    admin: Dict = Depends(verify_admin)
):
    """Configure auto-optimization settings"""
    try:
        dynamic_weight_service.enable_auto_optimization(
            enabled=request.enabled,
            interval=request.interval,
            min_sample_size=request.min_sample_size,
            accuracy_threshold=request.accuracy_threshold
        )
        
        return {
            "status": "success",
            "message": "Auto-optimization configured",
            "data": {
                "enabled": request.enabled,
                "interval": request.interval,
                "min_sample_size": request.min_sample_size,
                "accuracy_threshold": request.accuracy_threshold,
                "configured_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error configuring auto-optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-optimization/run")
async def run_auto_optimization(admin: Dict = Depends(verify_admin)):
    """Manually trigger auto-optimization"""
    try:
        success = await dynamic_weight_service.auto_optimize_weights()
        
        if not success:
            return {
                "status": "info",
                "message": "Auto-optimization skipped (insufficient data or minimal changes)"
            }
        
        return {
            "status": "success",
            "message": "Auto-optimization completed successfully",
            "data": {
                "triggered_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error running auto-optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_admin_dashboard(admin: Dict = Depends(verify_admin)):
    """Get comprehensive admin dashboard data"""
    try:
        # Get weight configuration summary
        weight_summary = dynamic_weight_service.get_weight_config_summary()
        
        # Get system metrics
        system_metrics = await metrics_service.get_metrics_summary()
        
        # Calculate additional dashboard metrics
        dashboard_data = {
            "weight_configuration": weight_summary,
            "system_metrics": system_metrics,
            "performance_summary": {
                "total_factors": len(weight_summary["current_weights"]),
                "factors_with_performance_data": len(weight_summary["performance_metrics"]),
                "auto_optimization_enabled": weight_summary["auto_optimization"]["enabled"],
                "active_ab_tests": weight_summary["active_ab_tests"],
                "recent_weight_changes": weight_summary["recent_changes"]
            },
            "alerts": [],
            "recommendations": []
        }
        
        # Generate alerts
        if weight_summary["auto_optimization"]["enabled"]:
            dashboard_data["alerts"].append({
                "type": "info",
                "message": "Auto-optimization is enabled",
                "timestamp": datetime.now().isoformat()
            })
        
        if weight_summary["recent_changes"] > 5:
            dashboard_data["alerts"].append({
                "type": "warning",
                "message": f"High number of recent weight changes: {weight_summary['recent_changes']}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate recommendations
        factors_without_data = set(weight_summary["current_weights"].keys()) - set(weight_summary["performance_metrics"].keys())
        if factors_without_data:
            dashboard_data["recommendations"].append({
                "type": "performance",
                "message": f"Factors without performance data: {', '.join(factors_without_data)}",
                "action": "Collect more signal data to enable performance tracking"
            })
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/health")
async def get_system_health(admin: Dict = Depends(verify_admin)):
    """Get detailed system health information"""
    try:
        # Get basic health from metrics service
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "weight_service": "healthy",
                "metrics_service": "healthy",
                "cache_service": "unknown",  # Will be updated with actual status
                "database": "unknown"
            },
            "performance": {
                "response_time": "unknown",
                "error_rate": "unknown",
                "uptime": "unknown"
            },
            "resources": {
                "memory_usage": "unknown",
                "cpu_usage": "unknown",
                "disk_usage": "unknown"
            }
        }
        
        # Try to get actual metrics
        try:
            metrics_summary = await metrics_service.get_metrics_summary()
            health_data["performance"] = {
                "total_requests": metrics_summary.get("api", {}).get("total_requests", 0),
                "active_connections": metrics_summary.get("api", {}).get("active_connections", 0),
                "avg_response_time": metrics_summary.get("api", {}).get("avg_response_time", 0)
            }
        except:
            pass
        
        return {
            "status": "success",
            "data": health_data
        }

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTO-SCANNER CONTROL ENDPOINTS
# ============================================================================

@router.get("/auto-scanner/status")
async def get_auto_scanner_status(admin: Dict = Depends(verify_admin)):
    """Get auto-scanner status and statistics"""
    try:
        from app.services.auto_scanner import auto_scanner

        stats = auto_scanner.get_stats()

        return {
            "status": "success",
            "data": {
                "enabled": stats["enabled"],
                "statistics": {
                    "total_scans": stats["total_scans"],
                    "smart_money_scans": stats["smart_money_scans"],
                    "mss_scans": stats["mss_scans"],
                    "rsi_scans": stats["rsi_scans"],
                    "alerts_sent": stats["alerts_sent"],
                    "last_scan_time": stats["last_scan_time"].isoformat() if stats["last_scan_time"] else None
                },
                "scheduled_jobs": stats.get("next_jobs", []),
                "configuration": {
                    "smart_money_interval_hours": auto_scanner.smart_money_interval,
                    "mss_interval_hours": auto_scanner.mss_interval,
                    "rsi_interval_hours": auto_scanner.rsi_interval,
                    "accumulation_threshold": auto_scanner.accumulation_threshold,
                    "distribution_threshold": auto_scanner.distribution_threshold,
                    "mss_threshold": auto_scanner.mss_threshold
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting auto-scanner status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-scanner/trigger/smart-money")
async def trigger_smart_money_scan(admin: Dict = Depends(verify_admin)):
    """Manually trigger Smart Money scan"""
    try:
        from app.services.auto_scanner import auto_scanner

        if not auto_scanner.enabled:
            raise HTTPException(
                status_code=400,
                detail="Auto-scanner is disabled. Enable it first."
            )

        # Trigger scan
        await auto_scanner.smart_money_auto_scan()

        return {
            "status": "success",
            "message": "Smart Money scan completed",
            "data": {
                "triggered_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering Smart Money scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-scanner/trigger/mss")
async def trigger_mss_discovery(admin: Dict = Depends(verify_admin)):
    """Manually trigger MSS Discovery scan"""
    try:
        from app.services.auto_scanner import auto_scanner

        if not auto_scanner.enabled:
            raise HTTPException(
                status_code=400,
                detail="Auto-scanner is disabled. Enable it first."
            )

        # Trigger scan
        await auto_scanner.mss_auto_discovery()

        return {
            "status": "success",
            "message": "MSS Discovery scan completed",
            "data": {
                "triggered_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering MSS Discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-scanner/trigger/rsi")
async def trigger_rsi_screener(admin: Dict = Depends(verify_admin)):
    """Manually trigger RSI screener"""
    try:
        from app.services.auto_scanner import auto_scanner

        if not auto_scanner.enabled:
            raise HTTPException(
                status_code=400,
                detail="Auto-scanner is disabled. Enable it first."
            )

        # Trigger scan
        await auto_scanner.rsi_auto_screener()

        return {
            "status": "success",
            "message": "RSI Screener completed",
            "data": {
                "triggered_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering RSI screener: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-scanner/trigger/daily-summary")
async def trigger_daily_summary(admin: Dict = Depends(verify_admin)):
    """Manually trigger daily summary report"""
    try:
        from app.services.auto_scanner import auto_scanner

        # Trigger summary
        await auto_scanner.send_daily_summary()

        return {
            "status": "success",
            "message": "Daily summary sent",
            "data": {
                "triggered_by": admin["admin_id"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error triggering daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
