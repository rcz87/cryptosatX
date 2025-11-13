"""
Admin API Routes for CryptoSatX
Dynamic weight adjustment dan system management
"""
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


# Import os untuk admin token validation
import os
