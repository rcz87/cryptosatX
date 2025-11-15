"""
GPT Actions Monitoring Endpoints
Provides statistics and monitoring for GPT Actions integration
"""

from fastapi import APIRouter
from typing import Dict, Any
from app.middleware.response_size_monitor import response_size_stats
from app.middleware.gpt_rate_limiter import gpt_rate_limiter

router = APIRouter(prefix="/gpt/monitoring", tags=["GPT Monitoring"])

@router.get("/response-sizes", summary="Response Size Statistics")
async def get_response_size_stats() -> Dict[str, Any]:
    """
    Get statistics about response sizes across all endpoints

    Returns:
    - Total requests processed
    - Count of large responses (>40KB)
    - Count of responses exceeding 50KB limit
    - Per-endpoint statistics
    - Compliance rate
    """
    stats = response_size_stats.get_stats()

    return {
        "ok": True,
        "data": stats,
        "limits": {
            "gpt_actions_limit_kb": 50,
            "warning_threshold_kb": 40
        }
    }

@router.get("/problematic-endpoints", summary="Endpoints Exceeding Size Limits")
async def get_problematic_endpoints() -> Dict[str, Any]:
    """
    Get list of endpoints that frequently exceed the 50KB GPT Actions limit

    Useful for identifying which endpoints need optimization
    """
    problematic = response_size_stats.get_problematic_endpoints()

    return {
        "ok": True,
        "data": {
            "count": len(problematic),
            "endpoints": problematic
        },
        "recommendation": "Consider pagination or response trimming for these endpoints"
    }

@router.get("/rate-limits", summary="Rate Limit Statistics")
async def get_rate_limit_stats() -> Dict[str, Any]:
    """
    Get current rate limiting statistics

    Returns:
    - Active clients in last minute
    - Endpoint usage counts
    - Configured limits
    """
    stats = gpt_rate_limiter.get_stats()

    return {
        "ok": True,
        "data": stats
    }

@router.get("/health-check", summary="GPT Actions Integration Health")
async def gpt_integration_health() -> Dict[str, Any]:
    """
    Comprehensive health check for GPT Actions integration

    Checks:
    - Response size compliance
    - Rate limiting status
    - System performance
    """
    response_stats = response_size_stats.get_stats()
    rate_stats = gpt_rate_limiter.get_stats()

    health_score = 100

    if response_stats.get("total_requests", 0) > 0:
        compliance_rate = response_stats.get("compliance_rate", 100)
        if compliance_rate < 100:
            health_score -= (100 - compliance_rate) * 0.5

    active_clients = rate_stats.get("active_clients_last_minute", 0)
    if active_clients > 50:
        health_score -= min(20, (active_clients - 50) * 0.5)

    if health_score >= 95:
        status = "excellent"
    elif health_score >= 80:
        status = "good"
    elif health_score >= 60:
        status = "fair"
    else:
        status = "poor"

    return {
        "ok": True,
        "data": {
            "status": status,
            "health_score": round(health_score, 2),
            "checks": {
                "response_size_compliance": {
                    "status": "pass" if response_stats.get("compliance_rate", 100) >= 95 else "warning",
                    "compliance_rate": response_stats.get("compliance_rate", 100),
                    "exceeded_count": response_stats.get("exceeded_limit", 0)
                },
                "rate_limiting": {
                    "status": "active",
                    "active_clients": active_clients,
                    "endpoint_count": len(rate_stats.get("endpoint_usage_last_minute", {}))
                }
            },
            "recommendations": _generate_recommendations(response_stats, rate_stats)
        }
    }

def _generate_recommendations(response_stats: dict, rate_stats: dict) -> list:
    """Generate recommendations based on stats"""
    recommendations = []

    compliance_rate = response_stats.get("compliance_rate", 100)
    if compliance_rate < 95:
        recommendations.append({
            "type": "warning",
            "category": "response_size",
            "message": f"Response size compliance is {compliance_rate}%. Consider implementing pagination or response trimming.",
            "priority": "high"
        })

    problematic = response_size_stats.get_problematic_endpoints()
    if len(problematic) > 0:
        recommendations.append({
            "type": "action",
            "category": "optimization",
            "message": f"{len(problematic)} endpoint(s) frequently exceed size limits. Review /gpt/monitoring/problematic-endpoints for details.",
            "priority": "medium"
        })

    active_clients = rate_stats.get("active_clients_last_minute", 0)
    if active_clients > 50:
        recommendations.append({
            "type": "info",
            "category": "traffic",
            "message": f"High traffic detected ({active_clients} active clients). Consider implementing caching.",
            "priority": "low"
        })

    endpoint_usage = rate_stats.get("endpoint_usage_last_minute", {})
    if endpoint_usage:
        most_used = max(endpoint_usage.items(), key=lambda x: x[1])
        if most_used[1] > 20:
            recommendations.append({
                "type": "info",
                "category": "usage",
                "message": f"High usage on {most_used[0]} ({most_used[1]} requests/min). Ensure caching is effective.",
                "priority": "low"
            })

    if not recommendations:
        recommendations.append({
            "type": "success",
            "category": "health",
            "message": "All systems operating normally. GPT Actions integration is healthy.",
            "priority": "info"
        })

    return recommendations

@router.get("/summary", summary="Quick Monitoring Summary")
async def get_monitoring_summary() -> Dict[str, Any]:
    """
    Get a quick summary of GPT Actions integration status

    Perfect for dashboard displays or quick checks
    """
    response_stats = response_size_stats.get_stats()
    rate_stats = gpt_rate_limiter.get_stats()
    problematic = response_size_stats.get_problematic_endpoints()

    return {
        "ok": True,
        "data": {
            "response_sizes": {
                "total_requests": response_stats.get("total_requests", 0),
                "compliance_rate": response_stats.get("compliance_rate", 100),
                "exceeded_limit": response_stats.get("exceeded_limit", 0),
                "problematic_endpoints": len(problematic)
            },
            "rate_limiting": {
                "active_clients": rate_stats.get("active_clients_last_minute", 0),
                "endpoints_in_use": len(rate_stats.get("endpoint_usage_last_minute", {}))
            }
        }
    }

@router.get("/limits", summary="Get GPT Actions Limits Configuration")
async def get_limits_config() -> Dict[str, Any]:
    """
    Get the configured limits for GPT Actions

    Returns:
    - Response size limits
    - Rate limits per endpoint
    - Global limits
    """
    return {
        "ok": True,
        "data": {
            "response_size": {
                "max_size_kb": 50,
                "max_size_bytes": 50 * 1024,
                "warning_threshold_kb": 40,
                "warning_threshold_bytes": 40 * 1024,
                "description": "GPT Actions has a 50KB response size limit"
            },
            "rate_limits": {
                "endpoint_limits": gpt_rate_limiter.endpoint_limits,
                "global_limit": {
                    "max_requests": gpt_rate_limiter.global_limit[0],
                    "window_seconds": gpt_rate_limiter.global_limit[1],
                    "description": "Maximum requests per IP across all endpoints"
                },
                "description": "Rate limits are applied per IP address and per endpoint"
            }
        }
    }
