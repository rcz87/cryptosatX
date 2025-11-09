# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Signal History Storage
Stores all generated signals for tracking, analysis, and backtesting
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class SignalHistory:
    """
    Store and retrieve signal history
    Uses JSON file storage for simplicity (can be upgraded to database later)
    """
    
    def __init__(self, storage_dir: str = "signal_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.history_file = self.storage_dir / "signal_history.json"
        
        # Create file if it doesn't exist
        if not self.history_file.exists():
            self._save_data([])
    
    async def save_signal(self, signal_data: Dict) -> Dict:
        """
        Save a signal to history
        
        Args:
            signal_data: Signal dict from /signals/{symbol} endpoint
        
        Returns:
            Dict with save status and signal ID
        """
        try:
            # Add metadata
            signal_entry = {
                "id": self._generate_id(),
                "saved_at": datetime.utcnow().isoformat(),
                "data": signal_data
            }
            
            # Load existing history
            history = self._load_data()
            
            # Add new signal
            history.append(signal_entry)
            
            # Keep only last 1000 signals (prevent file from growing too large)
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save back to file
            self._save_data(history)
            
            return {
                "success": True,
                "message": "Signal saved to history",
                "signal_id": signal_entry["id"],
                "total_signals": len(history)
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to save signal: {str(e)}"
            }
    
    async def get_history(self, symbol: Optional[str] = None, limit: int = 50, 
                         signal_type: Optional[str] = None) -> Dict:
        """
        Retrieve signal history
        
        Args:
            symbol: Filter by symbol (e.g., 'BTC')
            limit: Max number of signals to return
            signal_type: Filter by signal type ('LONG', 'SHORT', 'NEUTRAL')
        
        Returns:
            Dict with signals list and metadata
        """
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
                "signals": filtered
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to retrieve history: {str(e)}",
                "signals": []
            }
    
    async def get_statistics(self, symbol: Optional[str] = None) -> Dict:
        """
        Get signal statistics
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            Dict with statistics about signals
        """
        try:
            history = self._load_data()
            
            if symbol:
                history = [s for s in history if s["data"].get("symbol") == symbol.upper()]
            
            if not history:
                return {
                    "success": True,
                    "total": 0,
                    "message": "No signals in history"
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
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get statistics: {str(e)}"
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
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"sig_{timestamp}"


# Singleton instance
signal_history = SignalHistory()
