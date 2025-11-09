"""
Backtesting Framework for CryptoSatX
Historical validation system untuk trading signals
"""
import asyncio
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from dataclasses import dataclass
from app.utils.logger import default_logger


@dataclass
class BacktestConfig:
    """Configuration untuk backtesting"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    symbols: List[str] = None
    timeframes: List[str] = None
    commission_rate: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    max_position_size: float = 1.0  # 100% of capital
    stop_loss: float = 0.02  # 2%
    take_profit: float = 0.05  # 5%
    min_signal_score: float = 60.0


class BacktestResult(BaseModel):
    """Model untuk backtest results"""
    config: Dict[str, Any]
    performance: Dict[str, float]
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    generated_at: datetime = Field(default_factory=datetime.now)


class Trade(BaseModel):
    """Model untuk individual trade"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    signal_type: str  # LONG/SHORT
    signal_score: float
    pnl: Optional[float] = 0.0
    pnl_percentage: Optional[float] = 0.0
    exit_reason: str = ""
    commission: float = 0.0
    slippage: float = 0.0


class BacktestingService:
    """
    Comprehensive backtesting framework dengan:
    - Historical data simulation
    - Performance analytics
    - Risk metrics calculation
    - Strategy comparison
    """
    
    def __init__(self):
        self.logger = default_logger
        self.historical_data = {}  # Cache untuk historical data
        self.backtest_results = []  # Store backtest results
        
        # Default timeframes
        self.default_timeframes = ["1h", "4h", "1d"]
        
        # Performance metrics calculation
        self.performance_metrics = [
            "total_return", "annualized_return", "sharpe_ratio", "sortino_ratio",
            "max_drawdown", "win_rate", "profit_factor", "avg_trade_return",
            "volatility", "calmar_ratio", "expectancy", "kelly_criterion"
        ]
    
    async def run_backtest(
        self, 
        config: BacktestConfig,
        weight_config: Optional[Dict[str, float]] = None
    ) -> BacktestResult:
        """
        Run comprehensive backtest dengan given configuration
        
        Args:
            config: Backtest configuration
            weight_config: Custom weight configuration untuk testing
            
        Returns:
            BacktestResult dengan comprehensive analysis
        """
        try:
            self.logger.info(f"Starting backtest: {config.start_date} to {config.end_date}")
            
            # Initialize results
            trades = []
            equity_curve = []
            current_capital = config.initial_capital
            current_positions = {}
            
            # Generate historical signals
            historical_signals = await self._generate_historical_signals(
                config, weight_config
            )
            
            # Process each time period
            current_date = config.start_date
            while current_date <= config.end_date:
                # Get signals for current period
                period_signals = [
                    signal for signal in historical_signals
                    if signal["timestamp"].date() == current_date.date()
                ]
                
                # Process existing positions
                current_capital, current_positions = await self._process_positions(
                    current_positions, current_date, current_capital, config
                )
                
                # Process new signals
                new_trades, updated_positions = await self._process_signals(
                    period_signals, current_positions, current_capital, config
                )
                
                trades.extend(new_trades)
                current_positions.update(updated_positions)
                
                # Record equity curve
                portfolio_value = await self._calculate_portfolio_value(
                    current_positions, current_capital, current_date
                )
                
                equity_curve.append({
                    "date": current_date.isoformat(),
                    "portfolio_value": portfolio_value,
                    "cash": current_capital,
                    "positions_value": portfolio_value - current_capital,
                    "num_positions": len(current_positions)
                })
                
                current_date += timedelta(days=1)
            
            # Close remaining positions at end
            final_trades, final_capital = await self._close_all_positions(
                current_positions, current_date, current_capital, config
            )
            trades.extend(final_trades)
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                equity_curve, trades, config
            )
            
            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(
                equity_curve, trades, config
            )
            
            # Create result
            result = BacktestResult(
                config=config.__dict__,
                performance={
                    "total_return": (final_capital - config.initial_capital) / config.initial_capital,
                    "final_capital": final_capital,
                    "total_trades": len(trades),
                    "winning_trades": len([t for t in trades if t.get("pnl", 0) > 0]),
                    "losing_trades": len([t for t in trades if t.get("pnl", 0) < 0])
                },
                trades=trades,
                equity_curve=equity_curve,
                metrics=performance_metrics,
                risk_metrics=risk_metrics
            )
            
            # Store result
            self.backtest_results.append(result)
            
            self.logger.info(f"Backtest completed: {len(trades)} trades, {result.performance['total_return']:.2%} return")
            return result
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {e}")
            raise
    
    async def _generate_historical_signals(
        self, 
        config: BacktestConfig,
        weight_config: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Generate historical signals untuk backtesting"""
        try:
            # Simulate historical signal generation
            signals = []
            
            # For each symbol and timeframe
            for symbol in config.symbols or ["BTCUSDT", "ETHUSDT"]:
                for timeframe in config.timeframes or self.default_timeframes:
                    # Generate daily signals
                    current_date = config.start_date
                    while current_date <= config.end_date:
                        # Simulate signal generation based on historical patterns
                        signal = await self._simulate_historical_signal(
                            symbol, timeframe, current_date, weight_config
                        )
                        
                        if signal and signal["score"] >= config.min_signal_score:
                            signals.append(signal)
                        
                        current_date += timedelta(days=1)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating historical signals: {e}")
            return []
    
    async def _simulate_historical_signal(
        self,
        symbol: str,
        timeframe: str,
        date: datetime,
        weight_config: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        """Simulate historical signal generation"""
        try:
            # This would normally fetch real historical data
            # For now, we'll simulate based on patterns
            
            # Simulate market conditions
            np.random.seed(hash(f"{symbol}_{timeframe}_{date}") % 2**32)
            
            # Generate random market factors
            liquidations = np.random.exponential(0.1)
            funding_rate = np.random.normal(0, 0.01)
            price_momentum = np.random.normal(0, 0.02)
            long_short_ratio = np.random.uniform(0.3, 0.7)
            smart_money = np.random.exponential(0.05)
            oi_trend = np.random.normal(0, 0.01)
            social_sentiment = np.random.uniform(-1, 1)
            fear_greed = np.random.uniform(0, 100)
            
            # Use provided weights or defaults
            if weight_config is None:
                weight_config = {
                    "liquidations": 0.15,
                    "funding_rate": 0.12,
                    "price_momentum": 0.18,
                    "long_short_ratio": 0.10,
                    "smart_money": 0.15,
                    "oi_trend": 0.12,
                    "social_sentiment": 0.10,
                    "fear_greed": 0.08
                }
            
            # Calculate score
            score = (
                liquidations * weight_config["liquidations"] * 100 +
                abs(funding_rate) * weight_config["funding_rate"] * 100 +
                abs(price_momentum) * weight_config["price_momentum"] * 100 +
                abs(0.5 - long_short_ratio) * weight_config["long_short_ratio"] * 100 +
                smart_money * weight_config["smart_money"] * 100 +
                abs(oi_trend) * weight_config["oi_trend"] * 100 +
                abs(social_sentiment) * weight_config["social_sentiment"] * 50 +
                (50 - abs(50 - fear_greed)) * weight_config["fear_greed"]
            )
            
            # Determine signal type
            if score > 70:
                signal_type = "LONG" if price_momentum > 0 else "SHORT"
            elif score > 60:
                signal_type = "LONG" if long_short_ratio < 0.4 else "SHORT"
            else:
                signal_type = "NEUTRAL"
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": date,
                "signal_type": signal_type,
                "score": score,
                "confidence": "HIGH" if score > 80 else "MEDIUM" if score > 70 else "LOW",
                "factors": {
                    "liquidations": liquidations,
                    "funding_rate": funding_rate,
                    "price_momentum": price_momentum,
                    "long_short_ratio": long_short_ratio,
                    "smart_money": smart_money,
                    "oi_trend": oi_trend,
                    "social_sentiment": social_sentiment,
                    "fear_greed": fear_greed
                },
                "price": np.random.uniform(20000, 70000) if "BTC" in symbol else np.random.uniform(1000, 4000)
            }
            
        except Exception as e:
            self.logger.error(f"Error simulating historical signal: {e}")
            return None
    
    async def _process_positions(
        self,
        positions: Dict[str, Trade],
        current_date: datetime,
        current_capital: float,
        config: BacktestConfig
    ) -> Tuple[float, Dict[str, Trade]]:
        """Process existing positions untuk exit conditions"""
        try:
            updated_positions = {}
            
            for symbol, trade in positions.items():
                # Simulate price movement
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                current_price = trade.entry_price * (1 + price_change)
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                # Stop loss
                if trade.signal_type == "LONG":
                    if current_price <= trade.entry_price * (1 - config.stop_loss):
                        should_exit = True
                        exit_reason = "STOP_LOSS"
                else:  # SHORT
                    if current_price >= trade.entry_price * (1 + config.stop_loss):
                        should_exit = True
                        exit_reason = "STOP_LOSS"
                
                # Take profit
                if trade.signal_type == "LONG":
                    if current_price >= trade.entry_price * (1 + config.take_profit):
                        should_exit = True
                        exit_reason = "TAKE_PROFIT"
                else:  # SHORT
                    if current_price <= trade.entry_price * (1 - config.take_profit):
                        should_exit = True
                        exit_reason = "TAKE_PROFIT"
                
                # Time-based exit (hold max 7 days)
                if (current_date - trade.entry_time).days >= 7:
                    should_exit = True
                    exit_reason = "TIME_EXIT"
                
                if should_exit:
                    # Close position
                    trade.exit_time = current_date
                    trade.exit_price = current_price
                    trade.exit_reason = exit_reason
                    
                    # Calculate PnL
                    if trade.signal_type == "LONG":
                        price_return = (current_price - trade.entry_price) / trade.entry_price
                    else:  # SHORT
                        price_return = (trade.entry_price - current_price) / trade.entry_price
                    
                    # Apply commission and slippage
                    gross_pnl = trade.position_size * current_capital * price_return
                    commission = trade.position_size * current_capital * config.commission_rate * 2  # Entry + exit
                    slippage = trade.position_size * current_capital * config.slippage * 2
                    
                    trade.pnl = gross_pnl - commission - slippage
                    trade.pnl_percentage = price_return - (config.commission_rate * 2) - (config.slippage * 2)
                    trade.commission = commission
                    trade.slippage = slippage
                    
                    current_capital += trade.pnl
                else:
                    # Keep position open
                    updated_positions[symbol] = trade
            
            return current_capital, updated_positions
            
        except Exception as e:
            self.logger.error(f"Error processing positions: {e}")
            return current_capital, positions
    
    async def _process_signals(
        self,
        signals: List[Dict[str, Any]],
        positions: Dict[str, Trade],
        current_capital: float,
        config: BacktestConfig
    ) -> Tuple[List[Trade], Dict[str, Trade]]:
        """Process new signals untuk entry"""
        try:
            new_trades = []
            updated_positions = positions.copy()
            
            for signal in signals:
                # Skip if we already have position in this symbol
                if signal["symbol"] in positions:
                    continue
                
                # Skip neutral signals
                if signal["signal_type"] == "NEUTRAL":
                    continue
                
                # Calculate position size
                position_size = min(config.max_position_size, 0.25)  # Max 25% per trade
                
                # Create new trade
                trade = Trade(
                    symbol=signal["symbol"],
                    entry_time=signal["timestamp"],
                    exit_time=None,
                    entry_price=signal["price"],
                    exit_price=None,
                    position_size=position_size,
                    signal_type=signal["signal_type"],
                    signal_score=signal["score"],
                    pnl=0.0,
                    pnl_percentage=0.0,
                    exit_reason="",
                    commission=position_size * current_capital * config.commission_rate,
                    slippage=position_size * current_capital * config.slippage
                )
                
                new_trades.append(trade)
                updated_positions[signal["symbol"]] = trade
            
            return new_trades, updated_positions
            
        except Exception as e:
            self.logger.error(f"Error processing signals: {e}")
            return [], positions
    
    async def _close_all_positions(
        self,
        positions: Dict[str, Trade],
        current_date: datetime,
        current_capital: float,
        config: BacktestConfig
    ) -> Tuple[List[Trade], float]:
        """Close all positions at end of backtest"""
        try:
            closing_trades = []
            
            for symbol, trade in positions.items():
                # Simulate final price
                price_change = np.random.normal(0, 0.01)
                final_price = trade.entry_price * (1 + price_change)
                
                trade.exit_time = current_date
                trade.exit_price = final_price
                trade.exit_reason = "BACKTEST_END"
                
                # Calculate final PnL
                if trade.signal_type == "LONG":
                    price_return = (final_price - trade.entry_price) / trade.entry_price
                else:  # SHORT
                    price_return = (trade.entry_price - final_price) / trade.entry_price
                
                gross_pnl = trade.position_size * current_capital * price_return
                commission = trade.position_size * current_capital * config.commission_rate * 2
                slippage = trade.position_size * current_capital * config.slippage * 2
                
                trade.pnl = gross_pnl - commission - slippage
                trade.pnl_percentage = price_return - (config.commission_rate * 2) - (config.slippage * 2)
                trade.commission = commission
                trade.slippage = slippage
                
                current_capital += trade.pnl
                closing_trades.append(trade)
            
            return closing_trades, current_capital
            
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")
            return [], current_capital
    
    async def _calculate_portfolio_value(
        self,
        positions: Dict[str, Trade],
        current_capital: float,
        current_date: datetime
    ) -> float:
        """Calculate total portfolio value"""
        try:
            positions_value = 0.0
            
            for trade in positions.values():
                # Simulate current price
                price_change = np.random.normal(0, 0.01)
                current_price = trade.entry_price * (1 + price_change)
                
                if trade.signal_type == "LONG":
                    position_value = trade.position_size * current_capital * (current_price / trade.entry_price)
                else:  # SHORT
                    position_value = trade.position_size * current_capital * (2 - current_price / trade.entry_price)
                
                positions_value += position_value
            
            return current_capital + positions_value
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {e}")
            return current_capital
    
    async def _calculate_performance_metrics(
        self,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        config: BacktestConfig
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        try:
            if not equity_curve or not trades:
                return {}
            
            # Extract portfolio values
            portfolio_values = [point["portfolio_value"] for point in equity_curve]
            initial_value = config.initial_capital
            final_value = portfolio_values[-1]
            
            # Basic returns
            total_return = (final_value - initial_value) / initial_value
            days = (config.end_date - config.start_date).days
            annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # Daily returns
            daily_returns = []
            for i in range(1, len(portfolio_values)):
                daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                daily_returns.append(daily_return)
            
            # Risk metrics
            volatility = np.std(daily_returns) * np.sqrt(365) if daily_returns else 0
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # Downside deviation for Sortino ratio
            negative_returns = [r for r in daily_returns if r < 0]
            downside_deviation = np.std(negative_returns) * np.sqrt(365) if negative_returns else 0
            sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0
            
            # Drawdown
            peak = portfolio_values[0]
            max_drawdown = 0
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Trade metrics
            winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
            losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
            
            win_rate = len(winning_trades) / len(trades) if trades else 0
            
            avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
            
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            avg_trade_return = np.mean([t.get("pnl_percentage", 0) for t in trades]) if trades else 0
            
            # Calmar ratio
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
            
            # Expectancy
            expectancy = (win_rate * avg_win - (1 - win_rate) * abs(avg_loss)) if avg_loss != 0 else 0
            
            # Kelly Criterion (simplified)
            kelly_criterion = win_rate - ((1 - win_rate) / abs(avg_loss / avg_win)) if avg_loss != 0 and avg_win != 0 else 0
            
            return {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_trade_return": avg_trade_return,
                "volatility": volatility,
                "calmar_ratio": calmar_ratio,
                "expectancy": expectancy,
                "kelly_criterion": kelly_criterion,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    async def _calculate_risk_metrics(
        self,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        config: BacktestConfig
    ) -> Dict[str, float]:
        """Calculate risk metrics"""
        try:
            if not equity_curve:
                return {}
            
            portfolio_values = [point["portfolio_value"] for point in equity_curve]
            daily_returns = []
            
            for i in range(1, len(portfolio_values)):
                daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                daily_returns.append(daily_return)
            
            # VaR (Value at Risk) at 95% confidence
            var_95 = np.percentile(daily_returns, 5) if daily_returns else 0
            
            # CVaR (Conditional VaR) - Expected shortfall
            var_95_returns = [r for r in daily_returns if r <= var_95]
            cvar_95 = np.mean(var_95_returns) if var_95_returns else 0
            
            # Maximum consecutive losses
            consecutive_losses = 0
            max_consecutive_losses = 0
            for trade in trades:
                if trade.get("pnl", 0) < 0:
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0
            
            # Average holding period
            holding_periods = []
            for trade in trades:
                if trade.get("entry_time") and trade.get("exit_time"):
                    holding_period = (trade["exit_time"] - trade["entry_time"]).days
                    holding_periods.append(holding_period)
            
            avg_holding_period = np.mean(holding_periods) if holding_periods else 0
            
            # Position size consistency
            position_sizes = [t.get("position_size", 0) for t in trades]
            position_size_std = np.std(position_sizes) if position_sizes else 0
            
            return {
                "var_95": var_95,
                "cvar_95": cvar_95,
                "max_consecutive_losses": max_consecutive_losses,
                "avg_holding_period": avg_holding_period,
                "position_size_std": position_size_std,
                "volatility": np.std(daily_returns) if daily_returns else 0,
                "skewness": float(pd.Series(daily_returns).skew()) if daily_returns else 0,
                "kurtosis": float(pd.Series(daily_returns).kurtosis()) if daily_returns else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    async def compare_strategies(
        self,
        backtest_results: List[BacktestResult]
    ) -> Dict[str, Any]:
        """Compare multiple backtest results"""
        try:
            if not backtest_results:
                return {}
            
            comparison = {
                "strategies": [],
                "ranking": {},
                "summary": {}
            }
            
            # Extract metrics for each strategy
            for i, result in enumerate(backtest_results):
                strategy_name = f"Strategy_{i+1}"
                metrics = result.metrics
                
                comparison["strategies"].append({
                    "name": strategy_name,
                    "total_return": metrics.get("total_return", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "profit_factor": metrics.get("profit_factor", 0)
                })
            
            # Rank by different metrics
            metrics_to_rank = ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]
            
            for metric in metrics_to_rank:
                sorted_strategies = sorted(
                    comparison["strategies"],
                    key=lambda x: x[metric],
                    reverse=True
                )
                comparison["ranking"][metric] = [s["name"] for s in sorted_strategies]
            
            # Overall ranking (simple average)
            strategy_scores = {}
            for strategy in comparison["strategies"]:
                score = 0
                count = 0
                for metric in metrics_to_rank:
                    if metric in strategy and strategy[metric] is not None:
                        score += strategy[metric]
                        count += 1
                
                strategy_scores[strategy["name"]] = score / count if count > 0 else 0
            
            comparison["ranking"]["overall"] = sorted(
                strategy_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {e}")
            return {}
    
    def get_backtest_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of backtest results"""
        try:
            history = []
            
            for result in self.backtest_results[-limit:]:
                history.append({
                    "id": str(result.generated_at),
                    "generated_at": result.generated_at.isoformat(),
                    "total_return": result.performance.get("total_return", 0),
                    "sharpe_ratio": result.metrics.get("sharpe_ratio", 0),
                    "max_drawdown": result.metrics.get("max_drawdown", 0),
                    "total_trades": result.performance.get("total_trades", 0),
                    "win_rate": result.metrics.get("win_rate", 0)
                })
            
            return sorted(history, key=lambda x: x["generated_at"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting backtest history: {e}")
            return []


# Global instance
backtesting_service = BacktestingService()
