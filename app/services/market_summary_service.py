"""
Market Summary Service
Aggregates market data across major cryptocurrencies to provide overall market condition
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime


class MarketSummaryService:
    """
    Service untuk mendapatkan ringkasan kondisi pasar secara keseluruhan
    Menganalisis beberapa koin utama dan memberikan insight market-wide
    """
    
    # Major coins untuk analisis pasar
    MAJOR_COINS = ["BTC", "ETH", "SOL", "XRP", "BNB"]
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive market summary across major cryptocurrencies
        
        Returns:
            Dict with:
            - market_sentiment: Overall bullish/bearish/neutral
            - major_coins_signals: Signals for BTC, ETH, SOL, XRP, BNB
            - aggregate_metrics: Average funding, liquidations, etc.
            - explanation: AI-generated market condition explanation
            - recommendations: Trading recommendations based on market state
        """
        from app.core.signal_engine import signal_engine
        
        # Fetch signals for all major coins in parallel
        tasks = [
            signal_engine.build_signal(coin, debug=False, mode="aggressive")
            for coin in self.MAJOR_COINS
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch market data: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Process results
        coin_signals = {}
        valid_results = []
        
        for i, result in enumerate(results):
            coin = self.MAJOR_COINS[i]
            
            if isinstance(result, Exception):
                coin_signals[coin] = {
                    "error": str(result),
                    "signal": "UNAVAILABLE"
                }
            elif isinstance(result, dict):
                coin_signals[coin] = {
                    "signal": result.get("signal", "UNKNOWN"),
                    "score": result.get("score", 0),
                    "price": result.get("price", 0),
                    "confidence": result.get("confidence", "unknown")
                }
                
                # Only include successful results for aggregation
                if "metrics" in result:
                    valid_results.append({
                        "coin": coin,
                        "data": result
                    })
            else:
                coin_signals[coin] = {
                    "error": "Invalid response type",
                    "signal": "UNAVAILABLE"
                }
        
        # Calculate aggregate metrics
        aggregate = self._calculate_aggregates(valid_results)
        
        # Determine market sentiment
        market_sentiment = self._determine_market_sentiment(coin_signals, aggregate)
        
        # Generate explanation
        explanation = self._generate_explanation(coin_signals, aggregate, market_sentiment)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(market_sentiment, aggregate)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "market_sentiment": market_sentiment,
            "major_coins": coin_signals,
            "aggregate_metrics": aggregate,
            "explanation": explanation,
            "recommendations": recommendations,
            "data_quality": {
                "coins_analyzed": len(self.MAJOR_COINS),
                "successful_fetches": len(valid_results),
                "coverage_percent": round((len(valid_results) / len(self.MAJOR_COINS)) * 100, 1)
            }
        }
    
    def _calculate_aggregates(self, valid_results: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all coins"""
        if not valid_results:
            return {
                "avg_score": 0,
                "avg_funding_rate": 0,
                "total_signals": {"LONG": 0, "SHORT": 0, "NEUTRAL": 0},
                "market_bias": "UNKNOWN"
            }
        
        scores = []
        funding_rates = []
        signals_count = {"LONG": 0, "SHORT": 0, "NEUTRAL": 0}
        
        for item in valid_results:
            data = item["data"]
            
            # Collect scores
            if "score" in data:
                scores.append(data["score"])
            
            # Collect funding rates
            if "metrics" in data and "fundingRate" in data["metrics"]:
                funding_rates.append(data["metrics"]["fundingRate"])
            
            # Count signals
            signal = data.get("signal", "NEUTRAL")
            if signal in signals_count:
                signals_count[signal] += 1
        
        # Calculate averages
        avg_score = sum(scores) / len(scores) if scores else 50
        avg_funding = sum(funding_rates) / len(funding_rates) if funding_rates else 0
        
        # Determine market bias
        if signals_count["LONG"] > signals_count["SHORT"]:
            market_bias = "BULLISH"
        elif signals_count["SHORT"] > signals_count["LONG"]:
            market_bias = "BEARISH"
        else:
            market_bias = "NEUTRAL"
        
        return {
            "avg_score": round(avg_score, 1),
            "avg_funding_rate": round(avg_funding * 100, 3),  # Convert to percentage
            "total_signals": signals_count,
            "market_bias": market_bias,
            "coins_with_data": len(valid_results)
        }
    
    def _determine_market_sentiment(self, coin_signals: Dict, aggregate: Dict) -> str:
        """
        Determine overall market sentiment based on signals and metrics
        
        Returns: BULLISH, BEARISH, NEUTRAL, or MIXED
        """
        signals = aggregate.get("total_signals", {})
        longs = signals.get("LONG", 0)
        shorts = signals.get("SHORT", 0)
        neutrals = signals.get("NEUTRAL", 0)
        
        total = longs + shorts + neutrals
        if total == 0:
            return "UNKNOWN"
        
        # Strong bearish: >60% shorts
        if shorts / total > 0.6:
            return "BEARISH"
        
        # Strong bullish: >60% longs
        if longs / total > 0.6:
            return "BULLISH"
        
        # Mixed: relatively balanced
        if abs(longs - shorts) <= 1:
            return "MIXED"
        
        # Default to market bias
        return aggregate.get("market_bias", "NEUTRAL")
    
    def _generate_explanation(self, coin_signals: Dict, aggregate: Dict, sentiment: str) -> str:
        """
        Generate human-readable explanation of market condition (Indonesian)
        """
        avg_score = aggregate.get("avg_score", 50)
        avg_funding = aggregate.get("avg_funding_rate", 0)
        signals = aggregate.get("total_signals", {})
        
        # Base explanation
        if sentiment == "BEARISH":
            base = f"📉 Market sedang BEARISH - {signals.get('SHORT', 0)} dari {len(self.MAJOR_COINS)} koin utama menunjukkan sinyal SHORT."
        elif sentiment == "BULLISH":
            base = f"📈 Market sedang BULLISH - {signals.get('LONG', 0)} dari {len(self.MAJOR_COINS)} koin utama menunjukkan sinyal LONG."
        elif sentiment == "MIXED":
            base = f"⚖️ Market kondisi MIXED - sinyal terbagi antara LONG ({signals.get('LONG', 0)}) dan SHORT ({signals.get('SHORT', 0)})."
        else:
            base = f"➖ Market sedang NEUTRAL - mayoritas koin ({signals.get('NEUTRAL', 0)}) tidak menunjukkan arah jelas."
        
        # Add funding rate context
        if avg_funding > 0.5:
            funding_context = f" Funding rate tinggi ({avg_funding:.2f}%) menunjukkan posisi LONG terlalu ramai (overleveraged), risiko long squeeze."
        elif avg_funding < -0.2:
            funding_context = f" Funding rate negatif ({avg_funding:.2f}%) menunjukkan posisi SHORT dominan, potensi short squeeze."
        else:
            funding_context = f" Funding rate normal ({avg_funding:.2f}%), tidak ada tekanan leverage ekstrem."
        
        # Add score context
        if avg_score < 40:
            score_context = " Skor rata-rata rendah menunjukkan momentum bearish kuat."
        elif avg_score > 60:
            score_context = " Skor rata-rata tinggi menunjukkan momentum bullish kuat."
        else:
            score_context = " Skor rata-rata netral, market masih mencari arah."
        
        return base + funding_context + score_context
    
    def _generate_recommendations(self, sentiment: str, aggregate: Dict) -> List[str]:
        """
        Generate actionable trading recommendations based on market state
        """
        recommendations = []
        avg_funding = aggregate.get("avg_funding_rate", 0)
        
        if sentiment == "BEARISH":
            recommendations.append("🔻 Pertimbangkan posisi SHORT pada breakdown support level")
            recommendations.append("⏸️ Hindari buy dip langsung, tunggu konfirmasi bottom")
            if avg_funding > 0.5:
                recommendations.append("⚠️ Longs overleveraged - risiko long squeeze tinggi")
            recommendations.append("💰 Gunakan mode conservative untuk entry yang lebih aman")
            
        elif sentiment == "BULLISH":
            recommendations.append("🔺 Cari entry LONG pada pullback ke support")
            recommendations.append("📈 Follow trend dengan proper stop loss")
            if avg_funding < 0:
                recommendations.append("✅ Shorts mulai cover - potensi short squeeze")
            recommendations.append("⚡ Gunakan mode aggressive untuk catch momentum")
            
        elif sentiment == "MIXED":
            recommendations.append("⚖️ Market indecisive - tunggu breakout jelas")
            recommendations.append("🎯 Fokus scalping di range dengan R:R ketat")
            recommendations.append("📊 Monitor volume untuk konfirmasi arah")
            recommendations.append("🔄 Gunakan mode ultra untuk scalping reaktif")
            
        else:  # NEUTRAL
            recommendations.append("➖ Market flat - scalping range lebih aman dari trend following")
            recommendations.append("⏳ Tunggu catalyst fundamental atau technical breakout")
            recommendations.append("💤 Kurangi posisi size, hindari overtrading")
        
        # Universal recommendations
        if avg_funding > 0.6:
            recommendations.append("🚨 PENTING: Funding rate sangat tinggi - kurangi leverage!")
        
        return recommendations


# Singleton instance
market_summary_service = MarketSummaryService()
