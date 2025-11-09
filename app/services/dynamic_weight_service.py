"""
Dynamic Weight Adjustment Service for CryptoSatX
Admin dashboard untuk mengatur scoring weights secara real-time
"""
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.utils.logger import default_logger


class WeightConfig(BaseModel):
    """Model untuk weight configuration"""
    factor: str = Field(..., description="Factor name")
    weight: float = Field(..., ge=0, le=1, description="Weight value (0-1)")
    enabled: bool = Field(True, description="Enable/disable factor")
    description: str = Field("", description="Factor description")
    last_updated: datetime = Field(default_factory=datetime.now)
    updated_by: str = Field("", description="Admin who updated")


class WeightHistory(BaseModel):
    """Model untuk weight change history"""
    factor: str
    old_weight: float
    new_weight: float
    changed_by: str
    timestamp: datetime
    reason: str = ""


class PerformanceMetrics(BaseModel):
    """Model untuk performance metrics per factor"""
    factor: str
    accuracy_score: float
    hit_rate: float
    avg_return: float
    volatility: float
    sample_size: int
    last_calculated: datetime


class DynamicWeightService:
    """
    Service untuk dynamic weight adjustment dengan:
    - Real-time weight updates
    - Performance tracking
    - A/B testing support
    - Historical analysis
    """
    
    def __init__(self):
        self.logger = default_logger
        
        # Default weights (8-factor system)
        self.default_weights = {
            "liquidations": 0.15,
            "funding_rate": 0.12,
            "price_momentum": 0.18,
            "long_short_ratio": 0.10,
            "smart_money": 0.15,
            "oi_trend": 0.12,
            "social_sentiment": 0.10,
            "fear_greed": 0.08
        }
        
        # Current active weights
        self.current_weights = self.default_weights.copy()
        
        # Weight change history
        self.weight_history: List[WeightHistory] = []
        
        # Performance metrics cache
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        # A/B testing configurations
        self.ab_test_configs: Dict[str, Dict] = {}
        
        # Auto-optimization settings
        self.auto_optimization = {
            "enabled": False,
            "optimization_interval": 3600,  # 1 hour
            "min_sample_size": 100,
            "accuracy_threshold": 0.6
        }
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current active weights"""
        return self.current_weights.copy()
    
    def update_weight(
        self, 
        factor: str, 
        new_weight: float, 
        updated_by: str = "admin",
        reason: str = ""
    ) -> bool:
        """
        Update weight untuk specific factor
        
        Args:
            factor: Factor name
            new_weight: New weight value (0-1)
            updated_by: Admin identifier
            reason: Update reason
            
        Returns:
            Success status
        """
        try:
            # Validate factor exists
            if factor not in self.default_weights:
                self.logger.error(f"Unknown factor: {factor}")
                return False
            
            # Validate weight range
            if not 0 <= new_weight <= 1:
                self.logger.error(f"Weight must be between 0 and 1: {new_weight}")
                return False
            
            # Record old weight
            old_weight = self.current_weights[factor]
            
            # Update weight
            self.current_weights[factor] = new_weight
            
            # Record in history
            history_entry = WeightHistory(
                factor=factor,
                old_weight=old_weight,
                new_weight=new_weight,
                changed_by=updated_by,
                timestamp=datetime.now(),
                reason=reason
            )
            self.weight_history.append(history_entry)
            
            # Log change
            self.logger.info(
                f"Weight updated: {factor} {old_weight:.3f} -> {new_weight:.3f} "
                f"by {updated_by} (reason: {reason})"
            )
            
            # Trigger weight normalization if needed
            self._normalize_weights()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating weight: {e}")
            return False
    
    def _normalize_weights(self):
        """Normalize weights to ensure they sum to 1.0"""
        total_weight = sum(self.current_weights.values())
        
        if abs(total_weight - 1.0) > 0.001:  # Allow small rounding errors
            # Normalize all weights
            for factor in self.current_weights:
                self.current_weights[factor] = self.current_weights[factor] / total_weight
            
            self.logger.info(f"Weights normalized to sum to 1.0 (was {total_weight:.3f})")
    
    def reset_to_default(self, updated_by: str = "admin", reason: str = "") -> bool:
        """Reset all weights to default values"""
        try:
            # Record changes for history
            for factor, default_weight in self.default_weights.items():
                old_weight = self.current_weights[factor]
                if abs(old_weight - default_weight) > 0.001:
                    history_entry = WeightHistory(
                        factor=factor,
                        old_weight=old_weight,
                        new_weight=default_weight,
                        changed_by=updated_by,
                        timestamp=datetime.now(),
                        reason=f"Reset to default - {reason}"
                    )
                    self.weight_history.append(history_entry)
            
            # Reset weights
            self.current_weights = self.default_weights.copy()
            
            self.logger.info(f"Weights reset to default by {updated_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting weights: {e}")
            return False
    
    def get_weight_history(
        self, 
        factor: Optional[str] = None,
        days_back: int = 30
    ) -> List[WeightHistory]:
        """Get weight change history"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered_history = [
            entry for entry in self.weight_history
            if entry.timestamp >= cutoff_date
        ]
        
        if factor:
            filtered_history = [
                entry for entry in filtered_history
                if entry.factor == factor
            ]
        
        return sorted(filtered_history, key=lambda x: x.timestamp, reverse=True)
    
    def update_performance_metrics(
        self, 
        factor: str, 
        metrics: Dict[str, float]
    ) -> bool:
        """Update performance metrics untuk factor"""
        try:
            performance_metric = PerformanceMetrics(
                factor=factor,
                accuracy_score=metrics.get("accuracy_score", 0.0),
                hit_rate=metrics.get("hit_rate", 0.0),
                avg_return=metrics.get("avg_return", 0.0),
                volatility=metrics.get("volatility", 0.0),
                sample_size=metrics.get("sample_size", 0),
                last_calculated=datetime.now()
            )
            
            self.performance_metrics[factor] = performance_metric
            
            self.logger.info(f"Performance metrics updated for {factor}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
            return False
    
    def get_performance_metrics(self, factor: Optional[str] = None) -> Dict[str, PerformanceMetrics]:
        """Get performance metrics"""
        if factor:
            return {factor: self.performance_metrics.get(factor)}
        return self.performance_metrics.copy()
    
    def calculate_factor_importance(self) -> Dict[str, float]:
        """
        Calculate factor importance based on:
        - Current weight
        - Performance metrics
        - Recent accuracy
        """
        importance_scores = {}
        
        for factor, weight in self.current_weights.items():
            base_score = weight * 100  # Convert to percentage
            
            # Adjust based on performance
            if factor in self.performance_metrics:
                perf = self.performance_metrics[factor]
                
                # Performance bonus/penalty
                performance_multiplier = (
                    perf.accuracy_score * 0.4 +  # 40% weight on accuracy
                    perf.hit_rate * 0.3 +        # 30% weight on hit rate
                    (perf.avg_return / 100) * 0.2 +  # 20% weight on returns
                    (1 - perf.volatility) * 0.1   # 10% weight on stability
                )
                
                adjusted_score = base_score * performance_multiplier
            else:
                adjusted_score = base_score * 0.5  # Penalty for no data
            
            importance_scores[factor] = adjusted_score
        
        # Normalize to 100%
        total_importance = sum(importance_scores.values())
        if total_importance > 0:
            for factor in importance_scores:
                importance_scores[factor] = (importance_scores[factor] / total_importance) * 100
        
        return importance_scores
    
    def create_ab_test(
        self, 
        test_name: str, 
        variant_weights: Dict[str, Dict[str, float]],
        traffic_split: Dict[str, float] = None
    ) -> bool:
        """
        Create A/B test untuk weight variations
        
        Args:
            test_name: Test identifier
            variant_weights: Dict of variant_name -> weights
            traffic_split: Traffic percentage per variant
        """
        try:
            if traffic_split is None:
                # Equal split
                variant_count = len(variant_weights)
                traffic_split = {variant: 1.0/variant_count for variant in variant_weights}
            
            # Validate traffic split sums to 1.0
            if abs(sum(traffic_split.values()) - 1.0) > 0.001:
                self.logger.error("Traffic split must sum to 1.0")
                return False
            
            self.ab_test_configs[test_name] = {
                "variants": variant_weights,
                "traffic_split": traffic_split,
                "created_at": datetime.now(),
                "status": "active",
                "results": {}
            }
            
            self.logger.info(f"A/B test created: {test_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating A/B test: {e}")
            return False
    
    def get_ab_test_weights(self, test_name: str, user_id: str) -> Optional[Dict[str, float]]:
        """Get weights for user in A/B test"""
        if test_name not in self.ab_test_configs:
            return None
        
        test_config = self.ab_test_configs[test_name]
        
        # Simple hash-based assignment (consistent for same user)
        import hashlib
        hash_value = int(hashlib.md5(f"{test_name}_{user_id}".encode()).hexdigest(), 16)
        user_percentage = (hash_value % 100) / 100.0
        
        # Assign variant based on traffic split
        cumulative_percentage = 0.0
        for variant, percentage in test_config["traffic_split"].items():
            cumulative_percentage += percentage
            if user_percentage <= cumulative_percentage:
                return test_config["variants"][variant]
        
        # Fallback to first variant
        return list(test_config["variants"].values())[0]
    
    def enable_auto_optimization(
        self, 
        enabled: bool = True,
        interval: int = 3600,
        min_sample_size: int = 100,
        accuracy_threshold: float = 0.6
    ):
        """Configure auto-optimization settings"""
        self.auto_optimization = {
            "enabled": enabled,
            "optimization_interval": interval,
            "min_sample_size": min_sample_size,
            "accuracy_threshold": accuracy_threshold
        }
        
        self.logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")
    
    async def auto_optimize_weights(self) -> bool:
        """Automatically optimize weights based on performance"""
        if not self.auto_optimization["enabled"]:
            return False
        
        try:
            # Check if we have enough data
            for factor, perf in self.performance_metrics.items():
                if perf.sample_size < self.auto_optimization["min_sample_size"]:
                    self.logger.info(f"Insufficient data for {factor}: {perf.sample_size}")
                    return False
            
            # Calculate optimal weights based on performance
            performance_scores = {}
            for factor, perf in self.performance_metrics.items():
                if perf.sample_size >= self.auto_optimization["min_sample_size"]:
                    # Calculate performance score
                    score = (
                        perf.accuracy_score * 0.4 +
                        perf.hit_rate * 0.3 +
                        max(0, perf.avg_return / 100) * 0.2 +
                        (1 - min(1, perf.volatility)) * 0.1
                    )
                    performance_scores[factor] = score
            
            if not performance_scores:
                self.logger.info("No factors with sufficient data for optimization")
                return False
            
            # Normalize scores to create new weights
            total_score = sum(performance_scores.values())
            optimized_weights = {}
            
            for factor in self.default_weights:
                if factor in performance_scores:
                    optimized_weights[factor] = performance_scores[factor] / total_score
                else:
                    # Keep current weight for factors without data
                    optimized_weights[factor] = self.current_weights[factor]
            
            # Check if optimization is significant enough
            max_change = max(
                abs(optimized_weights[factor] - self.current_weights[factor])
                for factor in self.current_weights
            )
            
            if max_change < 0.05:  # Less than 5% change
                self.logger.info("Optimization change too small, skipping")
                return False
            
            # Apply optimized weights
            for factor, new_weight in optimized_weights.items():
                self.update_weight(
                    factor=factor,
                    new_weight=new_weight,
                    updated_by="auto_optimizer",
                    reason=f"Auto-optimization based on performance (max change: {max_change:.3f})"
                )
            
            self.logger.info("Auto-optimization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in auto-optimization: {e}")
            return False
    
    def get_weight_config_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of weight configuration"""
        return {
            "current_weights": self.current_weights,
            "default_weights": self.default_weights,
            "factor_importance": self.calculate_factor_importance(),
            "performance_metrics": {
                factor: perf.dict() for factor, perf in self.performance_metrics.items()
            },
            "auto_optimization": self.auto_optimization,
            "active_ab_tests": len(self.ab_test_configs),
            "recent_changes": len([
                h for h in self.weight_history
                if h.timestamp > datetime.now() - timedelta(days=7)
            ]),
            "last_updated": max(
                [h.timestamp for h in self.weight_history] or [datetime.now()]
            )
        }


# Global instance
dynamic_weight_service = DynamicWeightService()
