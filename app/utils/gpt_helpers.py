"""Helper functions for GPT-powered routes"""
from typing import Dict, Any

def calculate_risk_score(signal: dict, risk_level: str) -> float:
    """Calculate comprehensive risk score"""
    base_score = signal.get("score", 50)
    risk_multipliers = {"conservative": 1.5, "moderate": 1.0, "aggressive": 0.7}
    return min(100, base_score * risk_multipliers.get(risk_level, 1.0))


def calculate_position_size(risk_score: float, risk_level: str) -> float:
    """Calculate recommended position size"""
    base_sizes = {
        "conservative": 0.02,
        "moderate": 0.05,
        "aggressive": 0.10,
    }
    base_size = base_sizes.get(risk_level, 0.05)
    risk_adjustment = (risk_score / 100) * 0.5
    return base_size * (1 + risk_adjustment)


def calculate_stop_loss(signal: dict, risk_level: str) -> float:
    """Calculate stop loss percentage"""
    base_stop_losses = {"conservative": 1.5, "moderate": 2.5, "aggressive": 4.0}
    return base_stop_losses.get(risk_level, 2.5)


def calculate_take_profit(signal: dict, risk_level: str) -> float:
    """Calculate take profit percentage"""
    base_take_profits = {"conservative": 3.0, "moderate": 5.0, "aggressive": 8.0}
    score_multiplier = signal.get("score", 50) / 100
    return base_take_profits.get(risk_level, 5.0) * (1 + score_multiplier)


def detect_market_regime(signal: dict) -> str:
    """Detect current market regime"""
    score = signal.get("score", 50)
    if score > 70:
        return "bullish"
    elif score < 30:
        return "bearish"
    else:
        return "neutral"


def assess_volatility(signal: dict) -> str:
    """Assess market volatility"""
    return "moderate"


def assess_liquidity(signal: dict) -> str:
    """Assess market liquidity"""
    return "high"


def assess_sentiment(signal: dict) -> str:
    """Assess market sentiment"""
    score = signal.get("score", 50)
    if score > 60:
        return "positive"
    elif score < 40:
        return "negative"
    else:
        return "neutral"


def generate_final_recommendation(ultimate_signal: dict) -> dict:
    """Generate final trading recommendation"""
    primary_signal = ultimate_signal.get("primary", {})
    signal = primary_signal.get("signal", "NEUTRAL")
    confidence = primary_signal.get("confidence", "low")
    
    return {
        "action": signal,
        "confidence": confidence,
        "reasoning": f"MAXIMAL analysis indicates {signal} position with {confidence} confidence",
        "entryStrategy": get_entry_strategy(signal, confidence),
        "exitStrategy": get_exit_strategy(signal, confidence),
        "timeHorizon": "1-7 days",
        "conviction": "HIGH" if confidence in ["high", "maximum"] else "MEDIUM",
    }


def get_entry_strategy(signal: str, confidence: str) -> str:
    """Get entry strategy based on signal and confidence"""
    if signal == "LONG":
        if confidence == "maximum":
            return "Enter immediately with full position"
        elif confidence == "high":
            return "Enter in 2-3 tranches over 2 hours"
        else:
            return "Wait for confirmation, enter with 50% position"
    elif signal == "SHORT":
        if confidence == "maximum":
            return "Short immediately with full position"
        elif confidence == "high":
            return "Short in 2-3 tranches over 2 hours"
        else:
            return "Wait for confirmation, short with 50% position"
    else:
        return "Stay flat, wait for better setup"


def get_exit_strategy(signal: str, confidence: str) -> str:
    """Get exit strategy based on signal and confidence"""
    if confidence == "maximum":
        return "Take profit at 8%, stop loss at 2%"
    elif confidence == "high":
        return "Take profit at 5%, stop loss at 2.5%"
    else:
        return "Take profit at 3%, stop loss at 2%"


def get_risk_warnings(signal: dict, risk_score: float) -> list:
    """Generate risk warnings based on signal data"""
    warnings = []
    
    if risk_score > 70:
        warnings.append("⚠️ HIGH RISK: Consider reducing position size")
    
    funding_rate = signal.get("metrics", {}).get("fundingRate", 0)
    if abs(funding_rate) > 0.01:
        warnings.append(
            f"⚠️ High funding rate ({funding_rate*100:.2f}%): Overcrowded trade"
        )
    
    score = signal.get("score", 50)
    if 48 <= score <= 52:
        warnings.append("⚠️ NEUTRAL signal: Low conviction trade, consider waiting")
    
    if not warnings:
        warnings.append("✅ Risk levels acceptable for moderate trading")
    
    return warnings
