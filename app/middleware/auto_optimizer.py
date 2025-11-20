"""
Auto-Optimizer Middleware
Automatically applies safe parameter presets to prevent timeouts
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AutoOptimizer:
    """Auto-apply parameter presets to prevent GPT Actions timeout"""
    
    def __init__(self, presets_file: str = "config/endpoint_presets.json"):
        self.presets_file = presets_file
        self.presets: Dict[str, Any] = {}
        self.load_presets()
    
    def load_presets(self) -> None:
        """Load presets from JSON file"""
        try:
            preset_path = Path(self.presets_file)
            if preset_path.exists():
                with open(preset_path, 'r') as f:
                    data = json.load(f)
                    self.presets = data.get('presets', {})
                logger.info(f"✅ Loaded {len(self.presets)} endpoint presets")
            else:
                logger.warning(f"⚠️  Preset file not found: {self.presets_file}")
        except Exception as e:
            logger.error(f"❌ Failed to load presets: {e}")
    
    def optimize_parameters(
        self, 
        operation: str, 
        params: Dict[str, Any],
        mode: str = "safe"
    ) -> tuple[Dict[str, Any], bool]:
        """
        Optimize parameters for operation
        
        Args:
            operation: Operation name (e.g., "smart_money.scan")
            params: User-provided parameters
            mode: "safe" (default) or "fast"
        
        Returns:
            (optimized_params, was_optimized)
        """
        # Check if operation has preset
        if operation not in self.presets:
            return params, False
        
        preset_config = self.presets[operation]
        preset_params = preset_config.get(mode, {})
        
        if not preset_params:
            return params, False
        
        # Apply preset only for missing parameters
        optimized = params.copy()
        applied_params = []
        
        for key, value in preset_params.items():
            if key not in optimized or optimized[key] is None:
                optimized[key] = value
                applied_params.append(f"{key}={value}")
        
        if applied_params:
            logger.info(
                f"🔧 Auto-optimized {operation} [{mode} mode]: "
                f"{', '.join(applied_params)}"
            )
            return optimized, True
        
        return params, False
    
    def get_timeout_risk(self, operation: str) -> Optional[str]:
        """Get timeout risk level for operation"""
        if operation in self.presets:
            return self.presets[operation].get('timeout_risk')
        return None
    
    def get_notes(self, operation: str) -> Optional[str]:
        """Get optimization notes for operation"""
        if operation in self.presets:
            return self.presets[operation].get('notes')
        return None
    
    def should_optimize(self, operation: str) -> bool:
        """Check if operation needs optimization"""
        return operation in self.presets
    
    def get_recommended_mode(self, timeout_budget_s: int = 60) -> str:
        """
        Get recommended mode based on timeout budget
        
        Args:
            timeout_budget_s: Available timeout budget in seconds
        
        Returns:
            "fast" if budget < 30s, "safe" otherwise
        """
        return "fast" if timeout_budget_s < 30 else "safe"

# Global optimizer instance
_optimizer = None

def get_optimizer() -> AutoOptimizer:
    """Get or create global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = AutoOptimizer()
    return _optimizer

def optimize_request(
    operation: str,
    params: Dict[str, Any],
    mode: str = "safe"
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Optimize request parameters
    
    Returns:
        (optimized_params, metadata)
        
    Example:
        >>> params = {"symbol": "BTC"}
        >>> optimized, meta = optimize_request("smart_money.scan", params)
        >>> # optimized will have limit=10, min_accumulation_score=7
        >>> # meta will have: {"optimized": True, "mode": "safe", "risk": "HIGH"}
    """
    optimizer = get_optimizer()
    optimized_params, was_optimized = optimizer.optimize_parameters(operation, params, mode)
    
    metadata = {
        "optimized": was_optimized,
        "mode": mode if was_optimized else None,
        "timeout_risk": optimizer.get_timeout_risk(operation),
        "notes": optimizer.get_notes(operation)
    }
    
    return optimized_params, metadata
