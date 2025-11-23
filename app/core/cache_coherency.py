"""
Cache Coherency Service
========================

Ensures related data expires together untuk konsistensi GPT analysis.

Problem:
- Price data expires every 5s
- Social data expires every 900s (15 minutes!)
- Signal data expires every 30s
→ GPT analyzes with MISMATCHED timestamps!

Solution:
- Cache coherency groups with aligned TTLs
- Timestamp tracking to detect staleness
- Batch invalidation untuk related data
- Warning system untuk stale data detection

Author: CryptoSatX Intelligence Engine
Version: 1.0.0
"""

import asyncio
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.core.cache_service import cache_service
from app.utils.logger import logger


@dataclass
class CacheGroupConfig:
    """Configuration untuk cache coherency group"""
    name: str
    ttl_seconds: int
    members: List[str]  # List of cache key prefixes dalam group ini
    max_staleness_seconds: int  # Maximum allowed age difference antar members


# ============================================================================
# CACHE COHERENCY GROUPS
# ============================================================================

# Group 1: SIGNAL_ANALYSIS - All data needed untuk GPT signal analysis
# Semua data dalam group ini HARUS expire bersamaan
SIGNAL_ANALYSIS_GROUP = CacheGroupConfig(
    name="signal_analysis",
    ttl_seconds=60,  # Unified 60 second TTL
    members=[
        "price",
        "funding_rate",
        "open_interest",
        "social_basic",
        "liquidations",
        "long_short_ratio"
    ],
    max_staleness_seconds=10  # Warn jika data age difference > 10s
)

# Group 2: MARKET_SENTIMENT - Fear/Greed + Social comprehensive
MARKET_SENTIMENT_GROUP = CacheGroupConfig(
    name="market_sentiment",
    ttl_seconds=300,  # 5 minutes (less frequent updates OK)
    members=[
        "fear_greed",
        "social_comprehensive",
        "lunarcrush_comprehensive"
    ],
    max_staleness_seconds=60  # Allow up to 60s difference
)

# Group 3: ORDERBOOK_DATA - Real-time market depth
ORDERBOOK_GROUP = CacheGroupConfig(
    name="orderbook",
    ttl_seconds=10,  # 10 seconds (fast-moving data)
    members=[
        "orderbook",
        "trades",
        "ticker"
    ],
    max_staleness_seconds=5
)

# Group 4: ACCUMULATION_ANALYSIS - Data for accumulation/distribution
ACCUMULATION_GROUP = CacheGroupConfig(
    name="accumulation",
    ttl_seconds=60,  # Aligned with signal analysis
    members=[
        "ohlcv",
        "volume_profile",
        "orderbook",
        "price"
    ],
    max_staleness_seconds=10
)


class CacheCoherencyService:
    """
    Service untuk ensure cache coherency across related data.

    Features:
    - Aligned TTL untuk related data groups
    - Staleness detection and warnings
    - Batch invalidation for groups
    - Timestamp tracking for each cache entry
    - Coherency validation before GPT analysis
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.groups = {
            "signal_analysis": SIGNAL_ANALYSIS_GROUP,
            "market_sentiment": MARKET_SENTIMENT_GROUP,
            "orderbook": ORDERBOOK_GROUP,
            "accumulation": ACCUMULATION_GROUP
        }

        # Track timestamps untuk each cache entry
        self._timestamps: Dict[str, datetime] = {}

        logger.info(f"✅ CacheCoherencyService initialized (v{self.VERSION})")
        logger.info(f"   Registered {len(self.groups)} coherency groups")

    async def get_with_coherency_check(
        self,
        group_name: str,
        symbol: str,
        fetch_callbacks: Dict[str, callable]
    ) -> Dict[str, Any]:
        """
        Get all data dalam coherency group dengan staleness checking.

        Args:
            group_name: Name of coherency group
            symbol: Crypto symbol
            fetch_callbacks: Dict[member_name] = async fetch function

        Returns:
            Dict dengan all group data + metadata

        Example:
            >>> data = await coherency.get_with_coherency_check(
            ...     group_name="signal_analysis",
            ...     symbol="BTC",
            ...     fetch_callbacks={
            ...         "price": lambda: fetch_price("BTC"),
            ...         "funding_rate": lambda: fetch_funding("BTC"),
            ...         "social_basic": lambda: fetch_social("BTC")
            ...     }
            ... )
            >>> print(data["coherent"])  # True if all timestamps aligned
        """
        if group_name not in self.groups:
            raise ValueError(f"Unknown coherency group: {group_name}")

        group = self.groups[group_name]

        # Fetch all members
        data = {}
        timestamps = {}
        cache_statuses = {}

        for member in group.members:
            if member not in fetch_callbacks:
                logger.warning(f"No fetch callback for {member} in {group_name}")
                continue

            cache_key = f"{member}:{symbol}"

            # Try cache first
            cached_value = await cache_service.get(cache_key)

            if cached_value is not None:
                data[member] = cached_value
                timestamps[member] = self._timestamps.get(cache_key, datetime.utcnow())
                cache_statuses[member] = "hit"
            else:
                # Cache miss - fetch fresh
                try:
                    fresh_value = await fetch_callbacks[member]()
                    data[member] = fresh_value

                    # Store in cache with group TTL
                    await cache_service.set(cache_key, fresh_value, group.ttl_seconds)

                    # Track timestamp
                    now = datetime.utcnow()
                    timestamps[member] = now
                    self._timestamps[cache_key] = now

                    cache_statuses[member] = "miss"

                except Exception as e:
                    logger.error(f"Failed to fetch {member} for {symbol}: {e}")
                    data[member] = None
                    timestamps[member] = None
                    cache_statuses[member] = "error"

        # Check coherency
        coherency_check = self._check_coherency(
            timestamps,
            group.max_staleness_seconds
        )

        return {
            "group": group_name,
            "symbol": symbol,
            "data": data,
            "metadata": {
                "timestamps": {k: v.isoformat() if v else None for k, v in timestamps.items()},
                "cache_statuses": cache_statuses,
                "coherent": coherency_check["coherent"],
                "staleness_detected": coherency_check["staleness_detected"],
                "max_age_difference": coherency_check["max_age_difference"],
                "warnings": coherency_check["warnings"]
            },
            "version": self.VERSION
        }

    def _check_coherency(
        self,
        timestamps: Dict[str, Optional[datetime]],
        max_staleness: int
    ) -> Dict[str, Any]:
        """
        Check if timestamps are coherent (within max_staleness threshold).

        Args:
            timestamps: Dict of member timestamps
            max_staleness: Maximum allowed age difference in seconds

        Returns:
            Coherency check result
        """
        # Filter out None timestamps
        valid_timestamps = {k: v for k, v in timestamps.items() if v is not None}

        if len(valid_timestamps) < 2:
            return {
                "coherent": True,
                "staleness_detected": False,
                "max_age_difference": 0,
                "warnings": []
            }

        # Find oldest and newest
        oldest_time = min(valid_timestamps.values())
        newest_time = max(valid_timestamps.values())

        age_difference = (newest_time - oldest_time).total_seconds()

        staleness_detected = age_difference > max_staleness

        warnings = []
        if staleness_detected:
            oldest_member = [k for k, v in valid_timestamps.items() if v == oldest_time][0]
            newest_member = [k for k, v in valid_timestamps.items() if v == newest_time][0]

            warnings.append(
                f"⚠️  Staleness detected: {oldest_member} is {age_difference:.1f}s older than {newest_member} "
                f"(max allowed: {max_staleness}s)"
            )

            logger.warning(
                f"Cache coherency violation: age difference {age_difference:.1f}s > {max_staleness}s"
            )

        return {
            "coherent": not staleness_detected,
            "staleness_detected": staleness_detected,
            "max_age_difference": round(age_difference, 2),
            "warnings": warnings,
            "oldest_member": oldest_member if staleness_detected else None,
            "newest_member": newest_member if staleness_detected else None
        }

    async def invalidate_group(self, group_name: str, symbol: str) -> int:
        """
        Invalidate (delete) all cache entries dalam group.

        Useful untuk force refresh all related data together.

        Args:
            group_name: Name of coherency group
            symbol: Crypto symbol

        Returns:
            Number of cache entries deleted
        """
        if group_name not in self.groups:
            raise ValueError(f"Unknown coherency group: {group_name}")

        group = self.groups[group_name]
        deleted_count = 0

        for member in group.members:
            cache_key = f"{member}:{symbol}"
            await cache_service.delete(cache_key)

            if cache_key in self._timestamps:
                del self._timestamps[cache_key]

            deleted_count += 1

        logger.info(f"🗑️  Invalidated {deleted_count} cache entries for {group_name}:{symbol}")
        return deleted_count

    async def warm_group_cache(
        self,
        group_name: str,
        symbol: str,
        fetch_callbacks: Dict[str, callable]
    ) -> Dict[str, Any]:
        """
        Pre-warm all cache entries dalam group dengan fresh data.

        All members akan di-fetch secara parallel dan cached dengan
        SAME timestamp untuk perfect coherency.

        Args:
            group_name: Name of coherency group
            symbol: Crypto symbol
            fetch_callbacks: Dict[member_name] = async fetch function

        Returns:
            Warming result with status
        """
        if group_name not in self.groups:
            raise ValueError(f"Unknown coherency group: {group_name}")

        group = self.groups[group_name]

        logger.info(f"🔥 Warming cache for {group_name}:{symbol} ({len(group.members)} members)")

        # Fetch all members in parallel
        tasks = {}
        for member in group.members:
            if member in fetch_callbacks:
                tasks[member] = fetch_callbacks[member]()

        # Wait for all fetches
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Store all with SAME timestamp
        now = datetime.utcnow()
        success_count = 0
        error_count = 0

        for member, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to warm {member}: {result}")
                error_count += 1
                continue

            cache_key = f"{member}:{symbol}"

            # Store in cache
            await cache_service.set(cache_key, result, group.ttl_seconds)

            # Store timestamp
            self._timestamps[cache_key] = now

            success_count += 1

        logger.info(
            f"✅ Cache warming complete for {group_name}:{symbol}: "
            f"{success_count} success, {error_count} errors"
        )

        return {
            "group": group_name,
            "symbol": symbol,
            "warmed_members": success_count,
            "failed_members": error_count,
            "timestamp": now.isoformat(),
            "ttl_seconds": group.ttl_seconds
        }

    def get_group_info(self, group_name: str) -> Dict[str, Any]:
        """Get information about a coherency group"""
        if group_name not in self.groups:
            raise ValueError(f"Unknown coherency group: {group_name}")

        group = self.groups[group_name]

        return {
            "name": group.name,
            "ttl_seconds": group.ttl_seconds,
            "members": group.members,
            "max_staleness_seconds": group.max_staleness_seconds,
            "member_count": len(group.members)
        }

    def get_all_groups(self) -> Dict[str, Any]:
        """Get info about all coherency groups"""
        return {
            name: self.get_group_info(name)
            for name in self.groups.keys()
        }


# Global singleton
cache_coherency = CacheCoherencyService()
