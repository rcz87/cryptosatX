"""
Volatility-Adjusted Position Sizing
Dynamic position sizing and stop loss based on ATR
Phase 2: Risk Model V2
"""

from typing import Dict, Optional
from app.services.atr_calculator import atr_calculator


class PositionSizer:
    """
    Calculate optimal position sizes and stop losses based on volatility
    
    Key Concepts:
    - Higher volatility → Smaller position (reduce risk)
    - Lower volatility → Larger position (capitalize on opportunity)
    - ATR-based stop loss (not too tight, not too wide)
    - Risk-adjusted targets
    """

    def __init__(self):
        # Base configuration
        self.base_position_multiplier = 1.0  # 100% = normal position
        self.min_position_multiplier = 0.25  # 25% = minimum position
        self.max_position_multiplier = 2.0   # 200% = maximum position
        
        # Volatility targets (ATR percentage thresholds)
        self.normal_volatility = 3.0  # 3% ATR is considered "normal"
        
        # Stop loss configuration (ATR multiples)
        self.stop_loss_multipliers = {
            "AGGRESSIVE": 1.5,  # Tighter SL for aggressive trades
            "NORMAL": 2.0,      # Standard SL distance
            "REDUCED": 2.5,     # Wider SL for reduced risk
            "AVOID": 3.0        # Very wide SL (shouldn't trade)
        }
        
        # Take profit configuration (risk-reward ratios)
        self.take_profit_ratios = {
            "AGGRESSIVE": 2.0,  # 2:1 R:R
            "NORMAL": 2.5,      # 2.5:1 R:R
            "REDUCED": 3.0,     # 3:1 R:R (conservative)
            "AVOID": 1.5        # Lower target for risky conditions
        }

    async def calculate_volatility_adjusted_size(
        self,
        symbol: str,
        base_size: float = 1.0,
        timeframe: str = "4h"
    ) -> Optional[Dict]:
        """
        Calculate volatility-adjusted position size
        
        Formula: adjusted_size = base_size * (normal_volatility / current_volatility)
        
        Args:
            symbol: Trading pair
            base_size: Base position size (e.g., 1.0 = 100%)
            timeframe: Timeframe for volatility measurement
        
        Returns:
            Dict with recommended_size, multiplier, volatility_info
        """
        try:
            # Get ATR data
            atr_data = await atr_calculator.get_atr(symbol=symbol, timeframe=timeframe)
            
            if not atr_data or "atr_percentage" not in atr_data:
                print(f"[WARN] No ATR data for {symbol}, using base size")
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "base_size": base_size,
                    "recommended_size": base_size,
                    "multiplier": 1.0,
                    "volatility_info": None,
                    "warning": "ATR data unavailable, using default sizing (1.0x)"
                }
            
            current_volatility = atr_data.get("atr_percentage", 0)
            
            # Calculate multiplier
            if current_volatility > 0:
                multiplier = self.normal_volatility / current_volatility
                
                # Clamp to min/max bounds
                multiplier = max(self.min_position_multiplier, 
                               min(self.max_position_multiplier, multiplier))
            else:
                multiplier = 1.0
            
            # Calculate adjusted size
            recommended_size = base_size * multiplier
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "base_size": base_size,
                "recommended_size": round(recommended_size, 4),
                "multiplier": round(multiplier, 4),
                "volatility_info": {
                    "current_atr_pct": atr_data["atr_percentage"],
                    "normal_atr_pct": self.normal_volatility,
                    "classification": atr_data.get("volatility_classification", "UNKNOWN"),
                    "atr_value": atr_data["atr"]
                },
                "interpretation": self._interpret_sizing(multiplier, current_volatility)
            }
        
        except Exception as e:
            print(f"[ERROR] Failed to calculate position size: {e}")
            return None

    def _interpret_sizing(self, multiplier: float, volatility: float) -> str:
        """Generate human-readable interpretation of sizing recommendation"""
        if multiplier >= 1.5:
            return f"Low volatility ({volatility:.2f}%) - Increase position size to {multiplier:.1f}x"
        elif multiplier >= 1.0:
            return f"Normal volatility ({volatility:.2f}%) - Use standard position size"
        elif multiplier >= 0.5:
            return f"High volatility ({volatility:.2f}%) - Reduce position to {multiplier:.1f}x"
        else:
            return f"Very high volatility ({volatility:.2f}%) - Significantly reduce position to {multiplier:.1f}x"

    async def calculate_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        signal_type: str,
        risk_mode: str = "NORMAL",
        timeframe: str = "4h"
    ) -> Optional[Dict]:
        """
        Calculate ATR-based stop loss
        
        Args:
            symbol: Trading pair
            entry_price: Entry price for the trade
            signal_type: LONG or SHORT
            risk_mode: NORMAL/REDUCED/AGGRESSIVE/AVOID
            timeframe: Timeframe for ATR calculation
        
        Returns:
            Dict with stop_loss_price, distance, atr_multiple
        """
        try:
            # Get ATR data
            atr_data = await atr_calculator.get_atr(symbol=symbol, timeframe=timeframe)
            
            if not atr_data:
                print(f"[WARN] No ATR data for {symbol}, using default SL")
                default_sl_pct = 2.0  # 2% default
                sl_distance = entry_price * (default_sl_pct / 100)
                
                if signal_type == "LONG":
                    sl_price = entry_price - sl_distance
                else:  # SHORT
                    sl_price = entry_price + sl_distance
                
                return {
                    "stop_loss_price": round(sl_price, 8),
                    "distance_pct": default_sl_pct,
                    "warning": "ATR unavailable, using default 2% SL"
                }
            
            # Get ATR multiple based on risk mode
            atr_multiple = self.stop_loss_multipliers.get(risk_mode, 2.0)
            
            # Calculate SL distance (ATR * multiple)
            sl_distance = atr_data["atr"] * atr_multiple
            
            # Calculate SL price based on signal type
            if signal_type == "LONG":
                sl_price = entry_price - sl_distance
            else:  # SHORT
                sl_price = entry_price + sl_distance
            
            # Calculate distance as percentage
            distance_pct = (sl_distance / entry_price) * 100
            
            return {
                "stop_loss_price": round(sl_price, 8),
                "distance": round(sl_distance, 8),
                "distance_pct": round(distance_pct, 4),
                "atr_multiple": atr_multiple,
                "atr_value": atr_data["atr"],
                "risk_mode": risk_mode,
                "interpretation": f"SL {distance_pct:.2f}% away ({atr_multiple}x ATR)"
            }
        
        except Exception as e:
            print(f"[ERROR] Failed to calculate stop loss: {e}")
            return None

    async def calculate_take_profit(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        signal_type: str,
        risk_mode: str = "NORMAL"
    ) -> Optional[Dict]:
        """
        Calculate take profit based on risk-reward ratio
        
        Args:
            symbol: Trading pair
            entry_price: Entry price
            stop_loss_price: Stop loss price
            signal_type: LONG or SHORT
            risk_mode: Determines R:R ratio
        
        Returns:
            Dict with take_profit_price, risk_reward_ratio
        """
        try:
            # Calculate risk (distance from entry to SL)
            risk = abs(entry_price - stop_loss_price)
            
            # Get R:R ratio based on risk mode
            rr_ratio = self.take_profit_ratios.get(risk_mode, 2.5)
            
            # Calculate reward distance
            reward = risk * rr_ratio
            
            # Calculate TP price based on signal type
            if signal_type == "LONG":
                tp_price = entry_price + reward
            else:  # SHORT
                tp_price = entry_price - reward
            
            # Calculate TP distance as percentage
            tp_distance_pct = (reward / entry_price) * 100
            risk_pct = (risk / entry_price) * 100
            
            return {
                "take_profit_price": round(tp_price, 8),
                "reward_distance": round(reward, 8),
                "reward_distance_pct": round(tp_distance_pct, 4),
                "risk_distance_pct": round(risk_pct, 4),
                "risk_reward_ratio": rr_ratio,
                "interpretation": f"TP {tp_distance_pct:.2f}% away ({rr_ratio}:1 R:R)"
            }
        
        except Exception as e:
            print(f"[ERROR] Failed to calculate take profit: {e}")
            return None

    async def get_complete_trade_plan(
        self,
        symbol: str,
        entry_price: float,
        signal_type: str,
        risk_mode: str = "NORMAL",
        base_size: float = 1.0,
        timeframe: str = "4h"
    ) -> Dict:
        """
        Generate complete trade plan with position size, SL, and TP
        
        Returns all-in-one trading recommendation
        """
        try:
            # Calculate position size
            position_data = await self.calculate_volatility_adjusted_size(
                symbol=symbol,
                base_size=base_size,
                timeframe=timeframe
            )
            
            # Calculate stop loss
            sl_data = await self.calculate_stop_loss(
                symbol=symbol,
                entry_price=entry_price,
                signal_type=signal_type,
                risk_mode=risk_mode,
                timeframe=timeframe
            )
            
            # Calculate take profit
            tp_data = None
            if sl_data:
                tp_data = await self.calculate_take_profit(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss_price=sl_data["stop_loss_price"],
                    signal_type=signal_type,
                    risk_mode=risk_mode
                )
            
            return {
                "symbol": symbol,
                "signal_type": signal_type,
                "risk_mode": risk_mode,
                "entry_price": entry_price,
                "position_sizing": position_data,
                "stop_loss": sl_data,
                "take_profit": tp_data,
                "trade_plan_summary": self._generate_trade_summary(
                    position_data, sl_data, tp_data, risk_mode
                )
            }
        
        except Exception as e:
            print(f"[ERROR] Failed to generate trade plan: {e}")
            return {
                "error": str(e),
                "symbol": symbol
            }

    def _generate_trade_summary(
        self,
        position_data: Optional[Dict],
        sl_data: Optional[Dict],
        tp_data: Optional[Dict],
        risk_mode: str
    ) -> str:
        """Generate human-readable trade plan summary"""
        summary_parts = []
        
        if position_data:
            size_pct = position_data["recommended_size"] * 100
            summary_parts.append(f"Position: {size_pct:.0f}% of base")
        
        if sl_data:
            summary_parts.append(f"SL: {sl_data.get('distance_pct', 0):.2f}% away")
        
        if tp_data:
            summary_parts.append(f"TP: {tp_data.get('risk_reward_ratio', 0):.1f}:1 R:R")
        
        summary_parts.append(f"Risk Mode: {risk_mode}")
        
        return " | ".join(summary_parts)


# Global instance
position_sizer = PositionSizer()
