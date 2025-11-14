"""Portfolio optimization service"""
from typing import List, Dict, Any

class PortfolioOptimizerService:
    """Service for portfolio optimization and allocation"""
    
    def calculate_expected_return(self, signal: dict, risk_tolerance: int) -> float:
        """Calculate expected return for portfolio optimization"""
        base_return = (signal.get("score", 50) - 50) / 100
        risk_adjustment = (risk_tolerance - 5) / 20
        return (base_return + risk_adjustment) * 100
    
    
    def calculate_coin_risk(self, signal: dict, risk_tolerance: int) -> float:
        """Calculate risk for portfolio optimization"""
        confidence = signal.get("confidence", "low")
        confidence_risk = {"low": 0.3, "medium": 0.2, "high": 0.15, "maximum": 0.1}
        base_risk = confidence_risk.get(confidence, 0.25)
        risk_adjustment = (11 - risk_tolerance) / 20
        return base_risk * (1 + risk_adjustment)
    
    
    def optimize_portfolio_allocation(
        self, 
        portfolio_data: list, 
        risk_tolerance: int, 
        investment_amount: float
    ) -> dict:
        """Optimize portfolio allocation using simplified approach"""
        if not portfolio_data:
            return {"allocations": [], "metrics": {}}
        
        portfolio_data.sort(key=lambda x: x["expectedReturn"], reverse=True)
        
        num_coins = len(portfolio_data)
        base_allocation = 1.0 / num_coins
        
        allocations = []
        total_expected_return = 0
        total_risk = 0
        
        for coin_data in portfolio_data:
            return_adjustment = coin_data["expectedReturn"] / 100
            risk_penalty = coin_data["risk"]
            
            adjusted_allocation = base_allocation * (1 + return_adjustment - risk_penalty)
            adjusted_allocation = max(0.05, min(0.4, adjusted_allocation))
            
            allocation_amount = investment_amount * adjusted_allocation
            
            allocations.append({
                "symbol": coin_data["symbol"],
                "percentage": round(adjusted_allocation * 100, 2),
                "amount": round(allocation_amount, 2),
                "expectedReturn": coin_data["expectedReturn"],
                "risk": coin_data["risk"],
                "signal": coin_data["signal"],
            })
            
            total_expected_return += adjusted_allocation * coin_data["expectedReturn"]
            total_risk += adjusted_allocation * coin_data["risk"]
        
        total_percentage = sum(a["percentage"] for a in allocations)
        if total_percentage != 100:
            for allocation in allocations:
                allocation["percentage"] = round(
                    allocation["percentage"] / total_percentage * 100, 2
                )
                allocation["amount"] = round(
                    investment_amount * allocation["percentage"] / 100, 2
                )
        
        risk_free_rate = 2.0
        sharpe_ratio = (
            (total_expected_return - risk_free_rate) / total_risk 
            if total_risk > 0 else 0
        )
        
        return {
            "allocations": allocations,
            "metrics": {
                "diversificationScore": min(100, num_coins * 10),
                "riskScore": round(total_risk * 100, 2),
                "expectedAnnualReturn": round(total_expected_return * 365 / 7, 2),
                "maxDrawdown": round(total_risk * 50, 2),
            },
            "rebalancing": {
                "frequency": "weekly",
                "threshold": 5.0,
                "nextRebalance": "7 days",
            },
            "expectedReturn": round(total_expected_return, 2),
            "expectedRisk": round(total_risk * 100, 2),
            "sharpeRatio": round(sharpe_ratio, 2),
        }


portfolio_optimizer_service = PortfolioOptimizerService()
