"""
Advanced Analytics Routes for CryptoSatX
AI/ML-powered pattern recognition and predictive analytics endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
import asyncio
import logging

from app.services.advanced_analytics_service import advanced_analytics_service
from app.services.performance_optimization_service import (
    performance_optimization_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["advanced-analytics"])


@router.get("/patterns/{symbol}")
async def detect_chart_patterns(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe for analysis"),
    use_cache: bool = Query(default=True, description="Use cached results"),
):
    """Detect technical chart patterns using ML algorithms"""
    try:
        if use_cache:
            # Try to get from cache first
            cache_key = f"patterns:{symbol}:{timeframe}"
            cached_result = await performance_optimization_service.get_cached_result(
                cache_key
            )
            if cached_result:
                return cached_result

        # Perform pattern detection
        result = await advanced_analytics_service.detect_chart_patterns(
            symbol, timeframe
        )

        if use_cache and "error" not in result:
            # Cache the result for 5 minutes
            await performance_optimization_service.cache_result(
                cache_key, result, ttl=300
            )

        return result

    except Exception as e:
        logger.error(f"Error detecting patterns for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction/{symbol}")
async def predict_price_movement(
    symbol: str,
    horizon: str = Query(default="24h", description="Prediction time horizon"),
    use_cache: bool = Query(default=True, description="Use cached results"),
):
    """Predict price movement using ML models"""
    try:
        if use_cache:
            # Try to get from cache first
            cache_key = f"prediction:{symbol}:{horizon}"
            cached_result = await performance_optimization_service.get_cached_result(
                cache_key
            )
            if cached_result:
                return cached_result

        # Perform price prediction
        result = await advanced_analytics_service.predict_price_movement(
            symbol, horizon
        )

        if use_cache and "error" not in result:
            # Cache the result for 15 minutes
            await performance_optimization_service.cache_result(
                cache_key, result, ttl=900
            )

        return result

    except Exception as e:
        logger.error(f"Error predicting price movement for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{symbol}")
async def analyze_market_sentiment(
    symbol: str, use_cache: bool = Query(default=True, description="Use cached results")
):
    """Analyze market sentiment from multiple sources"""
    try:
        if use_cache:
            # Try to get from cache first
            cache_key = f"sentiment:{symbol}"
            cached_result = await performance_optimization_service.get_cached_result(
                cache_key
            )
            if cached_result:
                return cached_result

        # Perform sentiment analysis
        result = await advanced_analytics_service.analyze_market_sentiment(symbol)

        if use_cache and "error" not in result:
            # Cache the result for 10 minutes
            await performance_optimization_service.cache_result(
                cache_key, result, ttl=600
            )

        return result

    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/{symbol}")
async def detect_anomalies(
    symbol: str,
    use_cache: bool = Query(default=False, description="Use cached results"),
):
    """Detect unusual market behavior and anomalies"""
    try:
        if use_cache:
            # Try to get from cache first (shorter cache for anomalies)
            cache_key = f"anomalies:{symbol}"
            cached_result = await performance_optimization_service.get_cached_result(
                cache_key
            )
            if cached_result:
                return cached_result

        # Perform anomaly detection
        result = await advanced_analytics_service.detect_anomalies(symbol)

        if use_cache and "error" not in result:
            # Cache the result for 2 minutes (anomalies need fresh data)
            await performance_optimization_service.cache_result(
                cache_key, result, ttl=120
            )

        return result

    except Exception as e:
        logger.error(f"Error detecting anomalies for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive/{symbol}")
async def get_comprehensive_analysis(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe for analysis"),
    horizon: str = Query(default="24h", description="Prediction time horizon"),
    use_cache: bool = Query(default=True, description="Use cached results"),
):
    """Get comprehensive analysis including patterns, predictions, sentiment, and anomalies"""
    try:
        if use_cache:
            # Try to get from cache first
            cache_key = f"comprehensive:{symbol}:{timeframe}:{horizon}"
            cached_result = await performance_optimization_service.get_cached_result(
                cache_key
            )
            if cached_result:
                return cached_result

        # Perform all analyses in parallel
        patterns_task = advanced_analytics_service.detect_chart_patterns(
            symbol, timeframe
        )
        prediction_task = advanced_analytics_service.predict_price_movement(
            symbol, horizon
        )
        sentiment_task = advanced_analytics_service.analyze_market_sentiment(symbol)
        anomalies_task = advanced_analytics_service.detect_anomalies(symbol)

        # Wait for all tasks to complete
        patterns, prediction, sentiment, anomalies = await asyncio.gather(
            patterns_task,
            prediction_task,
            sentiment_task,
            anomalies_task,
            return_exceptions=True,
        )

        # Compile comprehensive result
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "prediction_horizon": horizon,
            "analysis_time": (
                patterns.get("analysis_time") if isinstance(patterns, dict) else None
            ),
            "patterns": (
                patterns if isinstance(patterns, dict) else {"error": str(patterns)}
            ),
            "prediction": (
                prediction
                if isinstance(prediction, dict)
                else {"error": str(prediction)}
            ),
            "sentiment": (
                sentiment if isinstance(sentiment, dict) else {"error": str(sentiment)}
            ),
            "anomalies": (
                anomalies if isinstance(anomalies, dict) else {"error": str(anomalies)}
            ),
            "summary": {
                "patterns_detected": (
                    len(patterns.get("patterns", []))
                    if isinstance(patterns, dict)
                    else 0
                ),
                "prediction_confidence": (
                    prediction.get("confidence_score", 0)
                    if isinstance(prediction, dict)
                    else 0
                ),
                "sentiment_score": (
                    sentiment.get("sentiment_score", 0)
                    if isinstance(sentiment, dict)
                    else 0
                ),
                "anomalies_count": (
                    len(anomalies.get("anomalies", []))
                    if isinstance(anomalies, dict)
                    else 0
                ),
                "overall_risk": (
                    anomalies.get("risk_level", "low")
                    if isinstance(anomalies, dict)
                    else "unknown"
                ),
            },
        }

        if use_cache:
            # Cache the comprehensive result for 10 minutes
            await performance_optimization_service.cache_result(
                cache_key, result, ttl=600
            )

        return result

    except Exception as e:
        logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/batch")
async def batch_detect_patterns(
    symbols: List[str] = Query(..., description="List of symbols to analyze"),
    timeframe: str = Query(default="1h", description="Timeframe for analysis"),
    use_cache: bool = Query(default=True, description="Use cached results"),
):
    """Detect patterns for multiple symbols"""
    try:
        results = {}

        # Process symbols in parallel with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests

        async def analyze_symbol(symbol):
            async with semaphore:
                if use_cache:
                    cache_key = f"patterns:{symbol}:{timeframe}"
                    cached_result = (
                        await performance_optimization_service.get_cached_result(
                            cache_key
                        )
                    )
                    if cached_result:
                        return symbol, cached_result

                result = await advanced_analytics_service.detect_chart_patterns(
                    symbol, timeframe
                )

                if use_cache and "error" not in result:
                    cache_key = f"patterns:{symbol}:{timeframe}"
                    await performance_optimization_service.cache_result(
                        cache_key, result, ttl=300
                    )

                return symbol, result

        # Execute all analyses
        tasks = [analyze_symbol(symbol) for symbol in symbols]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        for task in completed_tasks:
            if isinstance(task, Exception):
                logger.error(f"Error in batch pattern detection: {task}")
                continue
            symbol, result = task
            results[symbol] = result

        return {
            "symbols_analyzed": len(results),
            "timeframe": timeframe,
            "results": results,
            "analysis_time": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        logger.error(f"Error in batch pattern detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        metrics = await performance_optimization_service.get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/cache")
async def get_cache_metrics():
    """Get cache performance metrics"""
    try:
        metrics = await performance_optimization_service.get_cache_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/recommendations")
async def get_auto_scale_recommendations():
    """Get auto-scaling recommendations"""
    try:
        recommendations = (
            await performance_optimization_service.auto_scale_recommendations()
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error getting auto-scale recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(default="*", description="Cache pattern to invalidate")
):
    """Invalidate cache by pattern"""
    try:
        await performance_optimization_service.invalidate_cache(pattern)
        return {"message": f"Cache invalidated for pattern: {pattern}"}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/load-balance")
async def test_load_balancing(
    servers: List[str] = Query(..., description="List of servers to balance")
):
    """Test load balancing across servers"""
    try:
        result = await performance_optimization_service.implement_load_balancing(
            servers
        )
        return result
    except Exception as e:
        logger.error(f"Error testing load balancing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/rate-limit/{client_id}")
async def test_rate_limiting(
    client_id: str,
    limit: int = Query(default=100, description="Rate limit"),
    window: int = Query(default=60, description="Time window in seconds"),
):
    """Test rate limiting for a client"""
    try:
        result = await performance_optimization_service.implement_rate_limiting(
            client_id, limit, window
        )
        return result
    except Exception as e:
        logger.error(f"Error testing rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-response")
async def optimize_api_response(endpoint: str, data: Dict):
    """Optimize API response for better performance"""
    try:
        result = await performance_optimization_service.optimize_api_response(
            endpoint, data
        )
        return result
    except Exception as e:
        logger.error(f"Error optimizing API response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/analytics")
async def analytics_health_check():
    """Health check for analytics services"""
    try:
        # Test advanced analytics service
        test_symbol = "BTC"
        patterns_test = await advanced_analytics_service.detect_chart_patterns(
            test_symbol, "1h"
        )

        # Test performance optimization service
        metrics_test = await performance_optimization_service.get_system_metrics()

        return {
            "status": "healthy",
            "services": {
                "advanced_analytics": (
                    "operational" if "error" not in patterns_test else "degraded"
                ),
                "performance_optimization": (
                    "operational" if metrics_test else "degraded"
                ),
            },
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"Error in analytics health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time(),
        }
