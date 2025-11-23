"""
Signal Versioning System
========================

Tracks which version of each component was used untuk generate signal.

Problem:
- GPT kadang dapat jawaban berbeda untuk coin yang sama
- Sulit debug kenapa: data stale? algorithm berubah? cache issue?

Solution:
- Track version untuk SETIAP signal:
  - Signal engine version
  - Canonical calculator version
  - Cache coherency version
  - Data timestamps
  - Services yang digunakan
- Store version metadata di signal
- Query by version untuk compare hasil

Author: CryptoSatX Intelligence Engine
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import platform
import sys


@dataclass
class SignalVersion:
    """
    Complete version metadata untuk signal generation.

    Tracks ALL components yang involved dalam signal generation
    untuk perfect reproducibility dan debugging.
    """

    # Core versions
    signal_engine_version: str  # e.g., "2.1.0"
    canonical_calculator_version: Optional[str]  # e.g., "1.0.0" or None if not used
    cache_coherency_version: Optional[str]  # e.g., "1.0.0" or None
    openai_service_version: str  # "v1" or "v2"

    # Data source versions
    data_sources: Dict[str, str]  # e.g., {"coinapi": "1.0", "coinglass": "2.3"}

    # Timestamp tracking
    signal_generated_at: str  # ISO timestamp
    data_fetched_at: Optional[str]  # Oldest data timestamp (staleness indicator)
    cache_age_seconds: Optional[float]  # How old was cached data

    # Cache coherency tracking
    cache_coherent: Optional[bool]  # Were all cache timestamps aligned?
    cache_staleness_warnings: List[str]  # Warnings about stale data

    # Service quality
    data_quality_score: Optional[int]  # 0-100 from ServiceCallMonitor
    services_successful: int
    services_failed: int
    critical_services_ok: bool  # Were all CRITICAL services successful?

    # Algorithm selection
    scoring_method: str  # "canonical" or "legacy"
    accumulation_method: Optional[str]  # Which accumulation detector used

    # Environment
    python_version: str
    platform: str

    # Metadata
    version_schema: str = "1.0.0"  # Schema version for this structure

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return asdict(self)

    @classmethod
    def create(
        cls,
        signal_engine_version: str,
        openai_service_version: str,
        scoring_method: str,
        data_sources: Dict[str, str],
        services_successful: int,
        services_failed: int,
        critical_services_ok: bool,
        canonical_calculator_version: Optional[str] = None,
        cache_coherency_version: Optional[str] = None,
        data_fetched_at: Optional[str] = None,
        cache_age_seconds: Optional[float] = None,
        cache_coherent: Optional[bool] = None,
        cache_staleness_warnings: Optional[List[str]] = None,
        data_quality_score: Optional[int] = None,
        accumulation_method: Optional[str] = None
    ) -> "SignalVersion":
        """
        Factory method to create SignalVersion with current environment.

        This captures Python version, platform, timestamp automatically.
        """
        return cls(
            signal_engine_version=signal_engine_version,
            canonical_calculator_version=canonical_calculator_version,
            cache_coherency_version=cache_coherency_version,
            openai_service_version=openai_service_version,
            data_sources=data_sources,
            signal_generated_at=datetime.utcnow().isoformat(),
            data_fetched_at=data_fetched_at,
            cache_age_seconds=cache_age_seconds,
            cache_coherent=cache_coherent,
            cache_staleness_warnings=cache_staleness_warnings or [],
            data_quality_score=data_quality_score,
            services_successful=services_successful,
            services_failed=services_failed,
            critical_services_ok=critical_services_ok,
            scoring_method=scoring_method,
            accumulation_method=accumulation_method,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform=platform.platform()
        )


class SignalVersionTracker:
    """
    Tracks signal versions dan provides querying capabilities.

    Features:
    - Store version history
    - Query signals by version
    - Compare hasil across versions
    - Detect version-related inconsistencies
    """

    VERSION = "1.0.0"

    def __init__(self):
        # In-memory storage (could be DB for production)
        self._version_history: List[Dict[str, Any]] = []

        # Version component registry
        self._component_versions = {
            "signal_engine": "2.1.0",  # Current signal engine version
            "canonical_calculator": "1.0.0",
            "cache_coherency": "1.0.0",
            "openai_service_v1": "1.0",
            "openai_service_v2": "2.0"
        }

    def get_component_version(self, component: str) -> str:
        """Get current version of a component"""
        return self._component_versions.get(component, "unknown")

    def track_signal(
        self,
        symbol: str,
        signal_type: str,
        signal_score: float,
        version: SignalVersion
    ) -> None:
        """
        Track a signal generation dengan full version metadata.

        Args:
            symbol: Crypto symbol
            signal_type: LONG/SHORT/NEUTRAL
            signal_score: Signal score
            version: SignalVersion metadata
        """
        record = {
            "symbol": symbol,
            "signal_type": signal_type,
            "signal_score": signal_score,
            "version": version.to_dict(),
            "tracked_at": datetime.utcnow().isoformat()
        }

        self._version_history.append(record)

        # Keep only last 1000 signals (memory limit)
        if len(self._version_history) > 1000:
            self._version_history = self._version_history[-1000:]

    def get_signal_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get signal history dengan version metadata.

        Args:
            symbol: Filter by symbol (optional)
            limit: Max records to return

        Returns:
            List of signal records with versions
        """
        filtered = self._version_history

        if symbol:
            filtered = [r for r in filtered if r["symbol"] == symbol]

        return filtered[-limit:]

    def compare_versions(
        self,
        symbol: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        Compare signal hasil across different versions.

        Useful untuk detect regressions or improvements.

        Args:
            symbol: Crypto symbol
            version1: First version to compare
            version2: Second version to compare

        Returns:
            Comparison report
        """
        v1_signals = [
            r for r in self._version_history
            if r["symbol"] == symbol
            and r["version"]["signal_engine_version"] == version1
        ]

        v2_signals = [
            r for r in self._version_history
            if r["symbol"] == symbol
            and r["version"]["signal_engine_version"] == version2
        ]

        if not v1_signals or not v2_signals:
            return {
                "error": "Not enough data for comparison",
                "v1_count": len(v1_signals),
                "v2_count": len(v2_signals)
            }

        # Calculate averages
        v1_avg_score = sum(r["signal_score"] for r in v1_signals) / len(v1_signals)
        v2_avg_score = sum(r["signal_score"] for r in v2_signals) / len(v2_signals)

        # Count signal types
        v1_types = {}
        v2_types = {}

        for r in v1_signals:
            sig = r["signal_type"]
            v1_types[sig] = v1_types.get(sig, 0) + 1

        for r in v2_signals:
            sig = r["signal_type"]
            v2_types[sig] = v2_types.get(sig, 0) + 1

        return {
            "symbol": symbol,
            "version1": {
                "version": version1,
                "count": len(v1_signals),
                "avg_score": round(v1_avg_score, 2),
                "signal_distribution": v1_types
            },
            "version2": {
                "version": version2,
                "count": len(v2_signals),
                "avg_score": round(v2_avg_score, 2),
                "signal_distribution": v2_types
            },
            "score_difference": round(v2_avg_score - v1_avg_score, 2)
        }

    def detect_inconsistencies(
        self,
        symbol: str,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Detect inconsistencies in signals untuk same symbol.

        Looks for:
        - Same symbol getting different signals in short time
        - Cache staleness causing different results
        - Version changes causing inconsistencies

        Args:
            symbol: Crypto symbol
            time_window_minutes: Time window to check

        Returns:
            Inconsistency report
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        recent_signals = [
            r for r in self._version_history
            if r["symbol"] == symbol
            and datetime.fromisoformat(r["tracked_at"]) > cutoff_time
        ]

        if len(recent_signals) < 2:
            return {
                "inconsistencies_found": False,
                "reason": "Not enough recent signals to compare"
            }

        # Check for different signal types
        signal_types = set(r["signal_type"] for r in recent_signals)

        if len(signal_types) > 1:
            # Found inconsistency!
            inconsistent_signals = []

            for sig in recent_signals:
                version_info = sig["version"]
                inconsistent_signals.append({
                    "signal_type": sig["signal_type"],
                    "score": sig["signal_score"],
                    "timestamp": sig["tracked_at"],
                    "engine_version": version_info["signal_engine_version"],
                    "scoring_method": version_info["scoring_method"],
                    "cache_age": version_info.get("cache_age_seconds"),
                    "cache_coherent": version_info.get("cache_coherent"),
                    "data_quality": version_info.get("data_quality_score")
                })

            return {
                "inconsistencies_found": True,
                "symbol": symbol,
                "time_window_minutes": time_window_minutes,
                "different_signals": list(signal_types),
                "signal_count": len(recent_signals),
                "signals": inconsistent_signals,
                "possible_causes": self._analyze_causes(inconsistent_signals)
            }

        return {
            "inconsistencies_found": False,
            "signals_checked": len(recent_signals)
        }

    def _analyze_causes(self, signals: List[Dict]) -> List[str]:
        """Analyze possible causes of inconsistencies"""
        causes = []

        # Check for stale cache
        cache_ages = [s.get("cache_age") for s in signals if s.get("cache_age") is not None]
        if cache_ages and max(cache_ages) > 300:  # >5 minutes
            causes.append("Stale cache data detected (>5 minutes old)")

        # Check for cache incoherency
        incoherent = [s for s in signals if s.get("cache_coherent") is False]
        if incoherent:
            causes.append(f"Cache incoherency in {len(incoherent)} signals")

        # Check for version changes
        versions = set(s["engine_version"] for s in signals)
        if len(versions) > 1:
            causes.append(f"Multiple engine versions: {', '.join(versions)}")

        # Check for scoring method changes
        methods = set(s["scoring_method"] for s in signals)
        if len(methods) > 1:
            causes.append(f"Different scoring methods: {', '.join(methods)}")

        # Check for data quality
        low_quality = [s for s in signals if s.get("data_quality", 100) < 70]
        if low_quality:
            causes.append(f"Low data quality in {len(low_quality)} signals")

        return causes if causes else ["No obvious cause detected"]

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            "total_signals_tracked": len(self._version_history),
            "component_versions": self._component_versions,
            "tracker_version": self.VERSION
        }


# Global singleton
signal_version_tracker = SignalVersionTracker()


# Utility functions
def create_signal_version(
    use_canonical: bool,
    use_cache_coherency: bool,
    openai_version: str,
    data_sources: Dict[str, str],
    services_stats: Dict[str, Any],
    cache_metadata: Optional[Dict[str, Any]] = None
) -> SignalVersion:
    """
    Convenience function to create SignalVersion from current state.

    Args:
        use_canonical: Whether canonical calculator was used
        use_cache_coherency: Whether cache coherency was used
        openai_version: "v1" or "v2"
        data_sources: Dict of data source versions
        services_stats: Service call statistics
        cache_metadata: Optional cache coherency metadata

    Returns:
        SignalVersion instance
    """
    return SignalVersion.create(
        signal_engine_version=signal_version_tracker.get_component_version("signal_engine"),
        canonical_calculator_version=(
            signal_version_tracker.get_component_version("canonical_calculator")
            if use_canonical else None
        ),
        cache_coherency_version=(
            signal_version_tracker.get_component_version("cache_coherency")
            if use_cache_coherency else None
        ),
        openai_service_version=openai_version,
        scoring_method="canonical" if use_canonical else "legacy",
        data_sources=data_sources,
        services_successful=services_stats.get("successful", 0),
        services_failed=services_stats.get("failed", 0),
        critical_services_ok=services_stats.get("critical_ok", True),
        data_quality_score=services_stats.get("quality_score"),
        cache_age_seconds=cache_metadata.get("max_age") if cache_metadata else None,
        cache_coherent=cache_metadata.get("coherent") if cache_metadata else None,
        cache_staleness_warnings=cache_metadata.get("warnings", []) if cache_metadata else []
    )
