"""
Parallel Scanner Service for CryptoSatX

High-performance parallel scanning engine that processes 100-1000 coins
in minutes instead of hours using asyncio.gather and connection pooling.

Performance Targets:
- 100 coins: 30-45 seconds (from 5 minutes)
- 500 coins: 2-3 minutes (from 20+ minutes)
- 1000 coins: 4-6 minutes (from 40+ minutes)
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from collections import defaultdict

from app.utils.logger import default_logger


class SmartRateLimiter:
    """Dynamic rate limiting based on API response patterns"""

    def __init__(self, initial_limit: int = 10, max_limit: int = 50):
        self.current_limit = initial_limit  # Start conservative
        self.max_limit = max_limit
        self.min_limit = 5
        self.error_threshold = 0.05  # 5% error rate
        self.success_threshold = 0.02  # 2% error rate

        self.logger = default_logger

    def _calculate_error_rate(self, results: List[Dict]) -> float:
        """Calculate error rate from batch results"""
        if not results:
            return 0.0

        errors = sum(1 for r in results if r.get("error") or r.get("success") is False)
        return errors / len(results)

    async def adjust_rate_limit(self, results: List[Dict]):
        """Dynamically adjust rate limit based on success rate"""
        error_rate = self._calculate_error_rate(results)

        if error_rate < self.success_threshold:  # < 2% errors - increase
            old_limit = self.current_limit
            self.current_limit = min(self.current_limit + 5, self.max_limit)
            if old_limit != self.current_limit:
                self.logger.info(
                    f"📈 Rate limit increased: {old_limit} → {self.current_limit} "
                    f"(error rate: {error_rate:.1%})"
                )

        elif error_rate > self.error_threshold:  # > 5% errors - decrease
            old_limit = self.current_limit
            self.current_limit = max(self.current_limit - 10, self.min_limit)
            if old_limit != self.current_limit:
                self.logger.warning(
                    f"📉 Rate limit decreased: {old_limit} → {self.current_limit} "
                    f"(error rate: {error_rate:.1%})"
                )

    def get_current_limit(self) -> int:
        """Get current rate limit"""
        return self.current_limit


class RequestPool:
    """Connection pooling for HTTP requests to reuse connections"""

    def __init__(self, max_connections: int = 100, max_per_host: int = 20):
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_per_host,
            ttl_dns_cache=300,  # 5 min DNS cache
            enable_cleanup_closed=True
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = default_logger

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout
            )
            self.logger.info("🔌 HTTP connection pool initialized")

        return self.session

    async def make_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request with connection reuse"""
        session = await self.get_session()

        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"HTTP {response.status}",
                        "status_code": response.status
                    }

        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except aiohttp.ClientError as e:
            return {"error": f"Client error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("🔌 HTTP connection pool closed")


class ParallelScanner:
    """
    High-performance parallel scanning engine

    Scans 100-1000 coins in parallel with intelligent batching,
    rate limiting, retry logic, and connection pooling.
    """

    def __init__(
        self,
        max_concurrent: int = 50,
        batch_size: int = 50,
        base_url: str = "http://localhost:8000"
    ):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.base_url = base_url

        # Components
        self.rate_limiter = SmartRateLimiter(initial_limit=10, max_limit=max_concurrent)
        self.request_pool = RequestPool(max_connections=100, max_per_host=20)

        # Statistics
        self.stats = {
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "total_time": 0.0,
            "avg_scan_time": 0.0,
            "scans_per_second": 0.0
        }

        self.logger = default_logger

    def _create_batches(self, coins: List[str], size: int) -> List[List[str]]:
        """Split coins list into batches"""
        batches = []
        for i in range(0, len(coins), size):
            batches.append(coins[i:i + size])
        return batches

    async def _scan_single(
        self,
        coin: str,
        scanner_type: str,
        retries: int = 3
    ) -> Dict:
        """
        Scan single coin with retry logic and exponential backoff

        Args:
            coin: Symbol to scan
            scanner_type: Type of scanner ('smart_money', 'mss', 'signals', 'price')
            retries: Number of retry attempts

        Returns:
            Scan result dict
        """
        for attempt in range(retries):
            try:
                # Select endpoint based on scanner type
                if scanner_type == 'smart_money':
                    url = f"{self.base_url}/smart-money/analyze/{coin}"
                elif scanner_type == 'mss':
                    url = f"{self.base_url}/mss/analyze/{coin}"
                elif scanner_type == 'signals':
                    url = f"{self.base_url}/signals/{coin}"
                elif scanner_type == 'price':
                    url = f"{self.base_url}/coinapi/price/{coin}"
                else:
                    return {"symbol": coin, "error": f"Unknown scanner type: {scanner_type}"}

                # Make request
                result = await self.request_pool.make_request(url)

                # Check for errors
                if "error" in result:
                    if attempt < retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed
                        return {"symbol": coin, "error": result["error"], "success": False}

                # Success
                return {"symbol": coin, "data": result, "success": True}

            except Exception as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    return {"symbol": coin, "error": str(e), "success": False}

        return {"symbol": coin, "error": "Max retries exceeded", "success": False}

    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate scan results with statistics"""
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        # Group by error type
        error_types = defaultdict(int)
        for r in failed:
            error = r.get("error", "unknown")
            error_types[error] += 1

        return {
            "total_scanned": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "results": successful,
            "errors": dict(error_types),
            "failed_symbols": [r.get("symbol") for r in failed]
        }

    async def scan_bulk(
        self,
        coins: List[str],
        scanner_type: str = 'signals',
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Scan multiple coins in parallel with intelligent batching

        Args:
            coins: List of symbols to scan
            scanner_type: Scanner to use ('smart_money', 'mss', 'signals', 'price')
            progress_callback: Optional callback for progress updates

        Returns:
            Aggregated results dict with statistics

        Example:
            >>> scanner = ParallelScanner()
            >>> results = await scanner.scan_bulk(
            ...     coins=['BTC', 'ETH', 'SOL', ...],
            ...     scanner_type='smart_money'
            ... )
            >>> print(f"Scanned {results['successful']}/{results['total_scanned']}")
        """
        start_time = time.time()

        self.logger.info(
            f"🚀 Starting parallel scan: {len(coins)} coins, "
            f"scanner: {scanner_type}, batch size: {self.batch_size}"
        )

        # Create batches
        batches = self._create_batches(coins, self.batch_size)
        all_results = []
        total_processed = 0

        # Process batches
        for batch_idx, batch in enumerate(batches):
            batch_start = time.time()

            # Get current rate limit
            current_limit = self.rate_limiter.get_current_limit()

            # Process batch in parallel (limited by rate limiter)
            tasks = [
                self._scan_single(coin, scanner_type)
                for coin in batch
            ]

            # Use semaphore to limit concurrency
            semaphore = asyncio.Semaphore(current_limit)

            async def limited_scan(task):
                async with semaphore:
                    return await task

            batch_results = await asyncio.gather(*[limited_scan(task) for task in tasks])
            all_results.extend(batch_results)

            # Update rate limiter based on results
            await self.rate_limiter.adjust_rate_limit(batch_results)

            # Update progress
            total_processed += len(batch)
            batch_time = time.time() - batch_start

            self.logger.info(
                f"📊 Batch {batch_idx + 1}/{len(batches)} complete: "
                f"{len(batch)} coins in {batch_time:.2f}s "
                f"({len(batch)/batch_time:.1f} coins/s) - "
                f"Progress: {total_processed}/{len(coins)}"
            )

            # Call progress callback if provided
            if progress_callback:
                await progress_callback(
                    total=len(coins),
                    processed=total_processed,
                    current_batch=batch_idx + 1,
                    total_batches=len(batches)
                )

            # Small delay between batches to avoid overwhelming APIs
            if batch_idx < len(batches) - 1:  # Not last batch
                await asyncio.sleep(0.1)

        # Calculate final statistics
        total_time = time.time() - start_time
        aggregated = self._aggregate_results(all_results)

        # Update global stats
        self.stats["total_scans"] += len(coins)
        self.stats["successful_scans"] += aggregated["successful"]
        self.stats["failed_scans"] += aggregated["failed"]
        self.stats["total_time"] += total_time
        self.stats["avg_scan_time"] = self.stats["total_time"] / self.stats["total_scans"]
        self.stats["scans_per_second"] = len(coins) / total_time

        # Add performance metrics to result
        aggregated["performance"] = {
            "total_time_seconds": round(total_time, 2),
            "scans_per_second": round(len(coins) / total_time, 2),
            "avg_time_per_coin": round(total_time / len(coins), 3),
            "batches_processed": len(batches),
            "final_rate_limit": self.rate_limiter.get_current_limit()
        }

        self.logger.info(
            f"✅ Parallel scan complete: {aggregated['successful']}/{len(coins)} successful "
            f"in {total_time:.2f}s ({aggregated['performance']['scans_per_second']:.1f} coins/s)"
        )

        return aggregated

    async def scan_smart_money_bulk(self, coins: List[str]) -> Dict:
        """Convenience method for bulk Smart Money scanning"""
        return await self.scan_bulk(coins, scanner_type='smart_money')

    async def scan_mss_bulk(self, coins: List[str]) -> Dict:
        """Convenience method for bulk MSS scanning"""
        return await self.scan_bulk(coins, scanner_type='mss')

    async def scan_signals_bulk(self, coins: List[str]) -> Dict:
        """Convenience method for bulk signal scanning"""
        return await self.scan_bulk(coins, scanner_type='signals')

    async def scan_prices_bulk(self, coins: List[str]) -> Dict:
        """Convenience method for bulk price scanning"""
        return await self.scan_bulk(coins, scanner_type='price')

    def get_stats(self) -> Dict:
        """Get scanner statistics"""
        return {
            **self.stats,
            "current_rate_limit": self.rate_limiter.get_current_limit(),
            "max_concurrent": self.max_concurrent,
            "batch_size": self.batch_size
        }

    async def close(self):
        """Close HTTP connection pool"""
        await self.request_pool.close()


# Global instance
parallel_scanner = ParallelScanner(
    max_concurrent=50,
    batch_size=50,
    base_url="http://localhost:8000"
)


async def scan_bulk_parallel(
    coins: List[str],
    scanner_type: str = 'signals'
) -> Dict:
    """
    Convenience function for bulk parallel scanning

    Args:
        coins: List of symbols
        scanner_type: Scanner type

    Returns:
        Aggregated results
    """
    return await parallel_scanner.scan_bulk(coins, scanner_type)
