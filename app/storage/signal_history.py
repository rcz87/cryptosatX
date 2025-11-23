# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Signal History Storage
Stores all generated signals for tracking, analysis, and backtesting
UPDATED: Now uses PostgreSQL as primary storage with JSON backup
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from app.utils.logger import logger, get_wib_datetime


class SignalHistory:
    """
    Store and retrieve signal history
    Uses PostgreSQL as primary storage with JSON file as backup
    """
    
    def __init__(self, storage_dir: str = "signal_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.history_file = self.storage_dir / "signal_history.json"
        
        # Import database service (lazy import to avoid circular dependencies)
        from app.storage.signal_db import signal_db
        self.db = signal_db
        
        # Create file if it doesn't exist
        if not self.history_file.exists():
            self._save_data([])
    
    async def save_signal(self, signal_data: Dict) -> Dict:
        """
        Save a signal to history (PostgreSQL + JSON backup)
        
        Args:
            signal_data: Signal dict from /signals/{symbol} endpoint
        
        Returns:
            Dict with save status and signal ID
        """
        try:
            # PRIMARY: Save to PostgreSQL
            signal_id = await self.db.save_signal(signal_data)
            
            # BACKUP: Also save to JSON file for redundancy
            try:
                signal_entry = {
                    "id": self._generate_id(),
                    "saved_at": get_wib_datetime().isoformat(),
                    "data": signal_data
                }
                
                history = self._load_data()
                history.append(signal_entry)
                
                # Keep only last 1000 signals in JSON (prevent file from growing too large)
                if len(history) > 1000:
                    history = history[-1000:]
                
                self._save_data(history)
            except Exception as backup_error:
                # Don't fail if backup fails
                logger.warning(f"JSON backup failed: {backup_error}")
            
            # Get total count from database
            total_count = await self.db.get_signal_count()
            
            return {
                "success": True,
                "message": "Signal saved to database",
                "signal_id": signal_id,
                "total_signals": total_count,
                "storage": "postgresql"
            }
        
        except Exception as e:
            # Fallback to JSON-only if database fails
            logger.warning(f"Database save failed, using JSON fallback: {e}")
            
            try:
                signal_entry = {
                    "id": self._generate_id(),
                    "saved_at": get_wib_datetime().isoformat(),
                    "data": signal_data
                }
                
                history = self._load_data()
                history.append(signal_entry)
                
                if len(history) > 1000:
                    history = history[-1000:]
                
                self._save_data(history)
                
                return {
                    "success": True,
                    "message": "Signal saved to JSON (database unavailable)",
                    "signal_id": signal_entry["id"],
                    "total_signals": len(history),
                    "storage": "json_fallback"
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "message": f"Failed to save signal: {str(fallback_error)}"
                }
    
    async def get_history(self, symbol: Optional[str] = None, limit: int = 50, 
                         signal_type: Optional[str] = None) -> Dict:
        """
        Retrieve signal history from PostgreSQL
        
        Args:
            symbol: Filter by symbol (e.g., 'BTC')
            limit: Max number of signals to return
            signal_type: Filter by signal type ('LONG', 'SHORT', 'NEUTRAL')
        
        Returns:
            Dict with signals list and metadata
        """
        try:
            # PRIMARY: Get from PostgreSQL
            if symbol:
                signals = await self.db.get_signals_by_symbol(symbol, limit=limit)
            else:
                signals = await self.db.get_latest_signals(limit=limit)
            
            # Apply signal type filter if specified
            if signal_type:
                signals = [s for s in signals if s.get("signal") == signal_type.upper()]
            
            total_count = await self.db.get_signal_count(symbol=symbol if symbol else None)
            
            return {
                "success": True,
                "total": total_count,
                "filtered": len(signals),
                "signals": signals,
                "storage": "postgresql"
            }
        
        except Exception as e:
            # Fallback to JSON if database fails
            logger.warning(f"Database query failed, using JSON fallback: {e}")
            
            try:
                history = self._load_data()
                
                # Apply filters
                filtered = history
                
                if symbol:
                    filtered = [s for s in filtered if s["data"].get("symbol") == symbol.upper()]
                
                if signal_type:
                    filtered = [s for s in filtered if s["data"].get("signal") == signal_type.upper()]
                
                # Sort by newest first
                filtered = sorted(filtered, key=lambda x: x["saved_at"], reverse=True)
                
                # Apply limit
                filtered = filtered[:limit]
                
                return {
                    "success": True,
                    "total": len(history),
                    "filtered": len(filtered),
                    "signals": filtered,
                    "storage": "json_fallback"
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "message": f"Failed to retrieve history: {str(fallback_error)}",
                    "signals": []
                }
    
    async def get_statistics(self, symbol: Optional[str] = None, days: int = 7) -> Dict:
        """
        Get signal statistics from PostgreSQL
        
        Args:
            symbol: Filter by symbol (optional)
            days: Number of days to analyze (default: 7)
        
        Returns:
            Dict with statistics about signals
        """
        try:
            # PRIMARY: Get analytics from PostgreSQL
            stats = await self.db.get_analytics_summary(symbol=symbol, days=days)
            
            return {
                "success": True,
                **stats,
                "storage": "postgresql"
            }
        
        except Exception as e:
            # Fallback to JSON statistics
            logger.warning(f"Database stats failed, using JSON fallback: {e}")
            
            try:
                history = self._load_data()
                
                if symbol:
                    history = [s for s in history if s["data"].get("symbol") == symbol.upper()]
                
                if not history:
                    return {
                        "success": True,
                        "total": 0,
                        "message": "No signals in history",
                        "storage": "json_fallback"
                    }
                
                # Calculate statistics
                total = len(history)
                long_count = sum(1 for s in history if s["data"].get("signal") == "LONG")
                short_count = sum(1 for s in history if s["data"].get("signal") == "SHORT")
                neutral_count = sum(1 for s in history if s["data"].get("signal") == "NEUTRAL")
                
                scores = [s["data"].get("score", 0) for s in history]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                # Symbol distribution
                symbols = {}
                for s in history:
                    sym = s["data"].get("symbol", "UNKNOWN")
                    symbols[sym] = symbols.get(sym, 0) + 1
                
                return {
                    "success": True,
                    "total": total,
                    "signals": {
                        "LONG": long_count,
                        "SHORT": short_count,
                        "NEUTRAL": neutral_count
                    },
                    "percentages": {
                        "LONG": round(long_count / total * 100, 1) if total > 0 else 0,
                        "SHORT": round(short_count / total * 100, 1) if total > 0 else 0,
                        "NEUTRAL": round(neutral_count / total * 100, 1) if total > 0 else 0
                    },
                    "averageScore": round(avg_score, 1),
                    "symbolDistribution": symbols,
                    "dateRange": {
                        "oldest": history[-1]["saved_at"] if history else None,
                        "newest": history[0]["saved_at"] if history else None
                    },
                    "storage": "json_fallback"
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "message": f"Failed to get statistics: {str(fallback_error)}"
                }
    
    async def clear_history(self, confirm: bool = False) -> Dict:
        """
        Clear all signal history (dangerous operation!)
        
        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            return {
                "success": False,
                "message": "Confirmation required. Set confirm=True to clear history."
            }
        
        try:
            self._save_data([])
            return {
                "success": True,
                "message": "Signal history cleared"
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clear history: {str(e)}"
            }
    
    def _load_data(self) -> List[Dict]:
        """Load signal history from JSON file"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict]):
        """Save signal history to JSON file"""
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_id(self) -> str:
        """Generate unique ID for signal"""
        timestamp = get_wib_datetime().strftime("%Y%m%d%H%M%S%f")
        return f"sig_{timestamp}"


# Singleton instance
signal_history = SignalHistory()
