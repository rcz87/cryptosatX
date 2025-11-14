"""Risk assessment service"""
from typing import Dict, Any, Optional

class RiskAssessmentService:
    """Service for comprehensive risk assessment"""
    
    def assess_coin_risk(
        self,
        symbol: str,
        signal: dict,
        position_size: Optional[float] = None
    ) -> dict:
        """Comprehensive risk assessment for a cryptocurrency position"""
        from app.utils.gpt_helpers import (
            calculate_stop_loss,
            calculate_take_profit,
            detect_market_regime,
            get_risk_warnings
        )
        
        volatility_7d = signal.get("coinAPIMetrics", {}).get("volatility7d", 10.0)
        
        score = signal.get("score", 50)
        confidence = signal.get("confidence", "medium")
        
        if score > 65 or score < 35:
            risk_level = "high"
            risk_score = 75
        elif score > 55 or score < 45:
            risk_level = "medium"
            risk_score = 50
        else:
            risk_level = "low"
            risk_score = 25
        
        if volatility_7d > 15:
            risk_score += 15
            risk_level = "high"
        elif volatility_7d > 10:
            risk_score += 10
        
        risk_score = min(100, risk_score)
        
        recommended_size = None
        if position_size:
            max_loss_percent = 2.0
            stop_loss_percent = calculate_stop_loss(signal, "moderate")
            recommended_size = (position_size * max_loss_percent) / stop_loss_percent
        
        return {
            "success": True,
            "symbol": symbol,
            "riskAssessment": {
                "riskLevel": risk_level,
                "riskScore": round(risk_score, 2),
                "volatility": {
                    "7day": round(volatility_7d, 2),
                    "level": (
                        "high" if volatility_7d > 15
                        else "medium" if volatility_7d > 10
                        else "low"
                    ),
                },
                "liquidity": {
                    "level": "high",
                    "openInterest": signal.get("metrics", {}).get("openInterest", 0),
                },
                "marketRegime": detect_market_regime(signal),
                "signalConfidence": confidence,
            },
            "positionSizing": {
                "requestedSize": position_size,
                "recommendedSize": (
                    round(recommended_size, 2) if recommended_size else None
                ),
                "maxLossPercent": 2.0,
                "stopLossPercent": calculate_stop_loss(signal, "moderate"),
                "takeProfitPercent": calculate_take_profit(signal, "moderate"),
            },
            "riskMitigation": {
                "stopLoss": f"{calculate_stop_loss(signal, 'moderate')}% below entry",
                "takeProfit": f"{calculate_take_profit(signal, 'moderate')}% above entry",
                "positionLimit": "2-5% of portfolio",
                "diversification": "Maintain 8-12 positions across different sectors",
            },
            "warnings": get_risk_warnings(signal, risk_score),
        }


risk_assessment_service = RiskAssessmentService()
