"""
🚀 CRYPTO SCALPING ENGINE - GPT READY
Real-time multi-layer data aggregation untuk scalping execution

Endpoint Priority:
1. OHLCV (3s)         - Price momentum
2. Orderbook (3-5s)   - Bid/Ask pressure  
3. Liquidations (5s)  - Panic/Squeeze signals
4. RSI + Volume (5s)  - Entry timing confirmation
5. Funding (1-2m)     - Position bias
6. L/S Ratio (1m)     - Contrarian signals
7. Smart Money (10m)  - Whale activity
8. Fear & Greed (1h)  - Macro filter
"""

import requests
from datetime import datetime

BASE_URL = "https://guardiansofthetoken.org/invoke"

class ScalpingEngine:
    def __init__(self, symbol):
        self.symbol = symbol
        self.pair = f"{symbol}USDT"
        self.data = {}
        
    def _call(self, operation, **params):
        """Internal API caller with error handling"""
        payload = {"operation": operation, **params}
        try:
            timeout = 45 if "smart_money" in operation else 20
            r = requests.post(BASE_URL, json=payload, timeout=timeout)
            data = r.json()
            
            if data.get("ok"):
                return data.get("data")
            else:
                print(f"⚠️  {operation}: {data.get('error', '')[:60]}")
                return None
        except Exception as e:
            print(f"❌ {operation}: {str(e)[:50]}")
            return None
    
    def fetch_all(self):
        """
        🔄 FETCH ALL SCALPING DATA
        Ordered by priority untuk scalping decisions
        """
        print(f"\n{'='*70}")
        print(f"🎯 SCALPING ENGINE - {self.symbol}")
        print(f"{'='*70}\n")
        
        # Layer 1: CRITICAL - Price & Momentum (polling: 3s)
        print("📊 [1/8] Fetching Price & OHLCV...")
        self.data['ohlcv'] = self._call("coinapi.ohlcv.latest", symbol=self.symbol)
        
        # Layer 2: CRITICAL - Orderbook Pressure (polling: 3-5s)
        print("⚡ [2/8] Fetching Orderbook Pressure...")
        self.data['orderbook'] = self._call("coinapi.orderbook", symbol=self.symbol)
        
        # Layer 3: CRITICAL - Liquidation Stream (polling: 5s)
        print("💣 [3/8] Fetching Liquidation History...")
        self.data['liquidations'] = self._call(
            "coinglass.liquidation.aggregated_history",
            symbol=self.symbol,
            exchange_list="Binance",
            interval="1m",
            limit=20
        )
        
        # Layer 4: CRITICAL - RSI + Volume Delta (polling: 5s)
        print("📈 [4/8] Fetching RSI & Volume Delta...")
        self.data['rsi'] = self._call(
            "coinglass.indicators.rsi",
            symbol=self.symbol,
            period="14",
            interval="h1"
        )
        self.data['volume_delta'] = self._call(
            "coinglass.taker_buy_sell.exchange_list",
            symbol=self.pair
        )
        
        # Layer 5: RECOMMENDED - Funding Rate (polling: 1-2m)
        print("💰 [5/8] Fetching Funding Rate...")
        self.data['funding'] = self._call(
            "coinglass.funding_rate.history",
            exchange="Binance",
            symbol=self.pair,
            interval="h8",
            limit=10
        )
        
        # Layer 6: RECOMMENDED - Long/Short Ratio (polling: 1m)
        print("🧮 [6/8] Fetching Long/Short Ratio...")
        self.data['ls_ratio'] = self._call(
            "coinglass.long_short_ratio.position_history",
            exchange="Binance",
            symbol=self.pair,
            interval="h1",
            limit=10
        )
        
        # Layer 7: RECOMMENDED - Smart Money (polling: 10m)
        print("🐋 [7/8] Analyzing Smart Money Flow...")
        self.data['smart_money'] = self._call(
            "smart_money.scan",
            symbol=self.symbol
        )
        
        # Layer 8: OPTIONAL - Fear & Greed (polling: 1h)
        print("🧊 [8/8] Fetching Fear & Greed Index...")
        self.data['fear_greed'] = self._call("coinglass.indicators.fear_greed")
        
        return self.data
    
    def get_status(self):
        """📊 Check which data layers are available"""
        status = {
            "🔴 CRITICAL": {
                "Price & OHLCV": bool(self.data.get('ohlcv')),
                "Orderbook Pressure": bool(self.data.get('orderbook')),
                "Liquidations": bool(self.data.get('liquidations')),
                "RSI": bool(self.data.get('rsi')),
                "Volume Delta": bool(self.data.get('volume_delta')),
            },
            "🟡 RECOMMENDED": {
                "Funding Rate": bool(self.data.get('funding')),
                "Long/Short Ratio": bool(self.data.get('ls_ratio')),
                "Smart Money": bool(self.data.get('smart_money')),
            },
            "🟢 OPTIONAL": {
                "Fear & Greed": bool(self.data.get('fear_greed')),
            }
        }
        return status
    
    def print_summary(self):
        """Print data availability summary"""
        print(f"\n{'='*70}")
        print("📊 DATA LAYER STATUS")
        print(f"{'='*70}\n")
        
        status = self.get_status()
        
        for category, items in status.items():
            print(f"{category}")
            for name, available in items.items():
                icon = "✅" if available else "❌"
                print(f"  {icon} {name}")
            print()
        
        # Calculate readiness
        critical = list(status["🔴 CRITICAL"].values())
        recommended = list(status["🟡 RECOMMENDED"].values())
        
        critical_ok = sum(critical)
        recommended_ok = sum(recommended)
        total_critical = len(critical)
        total_recommended = len(recommended)
        
        print(f"{'='*70}")
        print(f"🎯 CRITICAL DATA: {critical_ok}/{total_critical} available")
        print(f"💡 RECOMMENDED DATA: {recommended_ok}/{total_recommended} available")
        
        # Readiness assessment
        if critical_ok == total_critical:
            print(f"\n✅ READY FOR SCALPING EXECUTION!")
            print(f"   All critical layers operational")
        elif critical_ok >= 4:
            print(f"\n⚠️  PARTIAL READINESS - {critical_ok}/{total_critical} critical")
            print(f"   Can proceed with reduced confidence")
        else:
            print(f"\n❌ NOT READY - Only {critical_ok}/{total_critical} critical")
            print(f"   Need minimum 4/5 critical layers")
        
        print(f"{'='*70}\n")
        
        return {
            "critical": critical_ok,
            "recommended": recommended_ok,
            "ready": critical_ok >= 4
        }


def main():
    """
    🚀 MAIN SCALPING WORKFLOW
    Usage: Change SYMBOL to any coin (BTC, ETH, SOL, XRP, etc)
    """
    
    # === CONFIGURATION ===
    SYMBOL = "XRP"  # Change this to any coin
    
    # === INITIALIZE ENGINE ===
    engine = ScalpingEngine(SYMBOL)
    
    # === FETCH ALL DATA ===
    print(f"⏱️  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    data = engine.fetch_all()
    
    # === SHOW SUMMARY ===
    result = engine.print_summary()
    
    # === READY FOR GPT ACTIONS ===
    if result['ready']:
        print("🧠 DATA READY FOR ANALYSIS!")
        print("   → Entry/Exit zones can be calculated")
        print("   → Risk/Reward ratios available")
        print("   → Whale activity monitored")
        print("   → Position bias determined\n")
        
        # Optional: Return data for further processing
        return {
            "symbol": SYMBOL,
            "data": data,
            "status": result,
            "timestamp": datetime.now().isoformat()
        }
    else:
        print("⚠️  Insufficient data for scalping execution")
        print("   Please check endpoint connectivity\n")
        return None


if __name__ == "__main__":
    result = main()
