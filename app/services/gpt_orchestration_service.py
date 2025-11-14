"""GPT endpoint orchestration service - moves business logic out of routes"""
from typing import Dict, Any, Optional
import copy

from app.core.signal_engine import signal_engine
from app.services.smc_analyzer import smc_analyzer
from app.services.openai_service import openai_service_legacy
from app.services.smart_money_service import smart_money_service
from app.utils.gpt_helpers import (
    calculate_risk_score,
    calculate_position_size,
    calculate_stop_loss,
    calculate_take_profit,
    detect_market_regime,
    assess_volatility,
    assess_liquidity,
    assess_sentiment,
    generate_final_recommendation,
)
from app.services.portfolio_optimizer_service import portfolio_optimizer_service
from app.utils.trading_strategies import TRADING_STRATEGIES, DEFAULT_TOP_COINS


class GPTOrchestrationService:
    """Service to orchestrate complex GPT endpoint logic"""
    
    async def build_ultimate_signal(
        self,
        symbol: str,
        include_ai_validation: bool,
        include_smc: bool,
        include_whale_data: bool,
        risk_level: str
    ) -> Dict[str, Any]:
        """Build ultimate signal with all enhancements"""
        signal = await signal_engine.build_signal(symbol, debug=False)
        
        response = {
            "symbol": symbol,
            "timestamp": signal.get("timestamp"),
            "ultimateSignal": {
                "primary": signal,
                "confidence": "MAXIMAL",
                "version": "3.0.0-MAXIMAL",
            },
        }
        
        if include_ai_validation:
            try:
                ai_analysis = await openai_service_legacy.analyze_signal_with_validation(signal)
                response["ultimateSignal"]["aiValidation"] = ai_analysis
            except Exception as e:
                response["ultimateSignal"]["aiValidation"] = {"success": False, "error": str(e)}
        
        if include_smc:
            try:
                smc_analysis = await smc_analyzer.analyze_smc(symbol, "1HRS")
                response["ultimateSignal"]["smcAnalysis"] = smc_analysis
            except Exception as e:
                response["ultimateSignal"]["smcAnalysis"] = {"success": False, "error": str(e)}
        
        if include_whale_data:
            try:
                from app.utils.trading_strategies import WHALE_SCAN_COINS
                whale_scan = await smart_money_service.scan_smart_money(
                    coins=WHALE_SCAN_COINS, min_accumulation_score=7, min_distribution_score=7
                )
                response["ultimateSignal"]["whaleActivity"] = whale_scan
            except Exception as e:
                response["ultimateSignal"]["whaleActivity"] = {"success": False, "error": str(e)}
        
        risk_score = calculate_risk_score(signal, risk_level)
        response["ultimateSignal"]["riskAssessment"] = {
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "positionSize": calculate_position_size(risk_score, risk_level),
            "stopLoss": calculate_stop_loss(signal, risk_level),
            "takeProfit": calculate_take_profit(signal, risk_level),
        }
        
        response["ultimateSignal"]["marketContext"] = {
            "marketRegime": detect_market_regime(signal),
            "volatility": assess_volatility(signal),
            "liquidity": assess_liquidity(signal),
            "sentiment": assess_sentiment(signal),
        }
        
        response["ultimateSignal"]["finalRecommendation"] = generate_final_recommendation(
            response["ultimateSignal"]
        )
        
        return response
    
    
    async def build_portfolio_optimization(
        self,
        risk_tolerance: int,
        investment_amount: float,
        time_horizon: str
    ) -> Dict[str, Any]:
        """Build optimized portfolio allocation"""
        portfolio_data = []
        for coin in DEFAULT_TOP_COINS:
            try:
                signal = await signal_engine.build_signal(coin, debug=False)
                
                expected_return = portfolio_optimizer_service.calculate_expected_return(
                    signal, risk_tolerance
                )
                risk = portfolio_optimizer_service.calculate_coin_risk(signal, risk_tolerance)
                
                portfolio_data.append({
                    "symbol": coin,
                    "allocation": 0,
                    "expectedReturn": expected_return,
                    "risk": risk,
                    "signal": signal.get("signal", "NEUTRAL"),
                    "confidence": signal.get("confidence", "low"),
                })
            except Exception:
                continue
        
        optimized_portfolio = portfolio_optimizer_service.optimize_portfolio_allocation(
            portfolio_data, risk_tolerance, investment_amount
        )
        
        return {
            "success": True,
            "portfolioOptimization": {
                "riskTolerance": risk_tolerance,
                "investmentAmount": investment_amount,
                "timeHorizon": time_horizon,
                **optimized_portfolio,
            },
        }
    
    
    async def find_whale_accumulation(
        self,
        min_score: int,
        exclude_overbought_coins: bool,
        whale_coins: str
    ) -> Dict[str, Any]:
        """Find whale accumulation opportunities"""
        scan_result = await smart_money_service.scan_smart_money(
            coins=whale_coins,
            min_accumulation_score=min_score,
            min_distribution_score=0,
        )
        
        if not scan_result.get("success"):
            return scan_result
        
        accumulating_coins = [
            coin for coin in scan_result.get("accumulation", [])
            if coin.get("accumulationScore", 0) >= min_score
        ]
        
        if exclude_overbought_coins:
            accumulating_coins = [
                coin for coin in accumulating_coins
                if coin.get("signal", {}).get("score", 50) < 75
            ]
        
        accumulating_coins.sort(
            key=lambda x: x.get("accumulationScore", 0), reverse=True
        )
        
        return {
            "success": True,
            "minScore": min_score,
            "excludeOverbought": exclude_overbought_coins,
            "totalFound": len(accumulating_coins),
            "opportunities": accumulating_coins[:10],
        }
    
    
    async def recommend_trading_strategies(
        self,
        symbol: Optional[str],
        strategy_type: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """Recommend trading strategies"""
        strategies = copy.deepcopy(TRADING_STRATEGIES)
        for strategy in strategies.values():
            strategy["parameters"]["timeframe"] = timeframe
        
        if strategy_type != "all" and strategy_type in strategies:
            selected_strategies = {strategy_type: strategies[strategy_type]}
        else:
            selected_strategies = strategies
        
        result = {
            "success": True,
            "strategyType": strategy_type,
            "timeframe": timeframe,
            "recommendedStrategies": selected_strategies,
        }
        
        if symbol:
            try:
                signal = await signal_engine.build_signal(symbol, debug=False)
                score = signal.get("score", 50)
                
                if score > 65:
                    result["primaryRecommendation"] = "momentum"
                    result["reasoning"] = "Strong bullish signal - use momentum strategy"
                elif score < 35:
                    result["primaryRecommendation"] = "momentum"
                    result["reasoning"] = "Strong bearish signal - use short momentum strategy"
                elif 45 <= score <= 55:
                    result["primaryRecommendation"] = "mean_reversion"
                    result["reasoning"] = "Neutral signal - use mean reversion"
                else:
                    result["primaryRecommendation"] = "breakout"
                    result["reasoning"] = "Moderate signal - wait for breakout"
                
                result["symbolAnalysis"] = {
                    "symbol": symbol,
                    "currentSignal": signal.get("signal"),
                    "score": score,
                    "confidence": signal.get("confidence"),
                }
            except Exception as e:
                result["symbolAnalysisError"] = str(e)
        
        return result


gpt_orchestration_service = GPTOrchestrationService()
