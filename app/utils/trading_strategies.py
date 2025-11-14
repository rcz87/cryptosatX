"""Trading strategy definitions and configurations"""

TRADING_STRATEGIES = {
    "momentum": {
        "name": "Momentum Trading",
        "description": "Ride strong trends with trailing stops",
        "suitability": "High volatility, clear trends",
        "parameters": {
            "entrySignal": "Price breaks above resistance with volume",
            "exitSignal": "Momentum reversal or trailing stop hit",
            "stopLoss": "2-3% below entry",
            "takeProfit": "5-8% above entry",
        },
    },
    "mean_reversion": {
        "name": "Mean Reversion",
        "description": "Trade oversold/overbought bounces",
        "suitability": "Range-bound markets, low volatility",
        "parameters": {
            "entrySignal": "RSI < 30 or RSI > 70",
            "exitSignal": "Return to mean (RSI 50)",
            "stopLoss": "Beyond support/resistance",
            "takeProfit": "At mean level",
        },
    },
    "breakout": {
        "name": "Breakout Trading",
        "description": "Trade confirmed breakouts from consolidation",
        "suitability": "Consolidation periods before major moves",
        "parameters": {
            "entrySignal": "Clean breakout with volume confirmation",
            "exitSignal": "Failed breakout or target reached",
            "stopLoss": "Below breakout level",
            "takeProfit": "Measured move from consolidation",
        },
    },
    "trend_following": {
        "name": "Trend Following",
        "description": "Follow established trends",
        "suitability": "Strong directional markets",
        "parameters": {
            "entrySignal": "Pullback to moving average in uptrend",
            "exitSignal": "Trend reversal signal",
            "stopLoss": "Below recent swing low",
            "takeProfit": "Trailing stop at 50% of ATR",
        },
    },
}


DEFAULT_TOP_COINS = ["BTC", "ETH", "SOL", "AVAX", "DOGE", "SHIB", "MATIC", "DOT", "LINK", "UNI"]

WHALE_SCAN_COINS = "BTC,ETH,SOL,AVAX,DOGE,SHIB,MATIC,DOT,LINK,UNI,ADA,XRP,ATOM,NEAR,FTM"
