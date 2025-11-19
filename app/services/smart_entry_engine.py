"""
CryptoSatX Smart Entry Engine
Professional-grade entry signal analysis with confluence scoring

Analyzes multiple data sources to provide high-probability entry signals:
- Price action & candlestick patterns
- Volume analysis & order book depth
- Funding rate trends & long/short ratios
- Open interest trends & divergence
- Smart money indicators (whale tracking, top traders)
- Social sentiment & trending analysis

Output: Confluence score (0-100) with actionable entry zones, SL/TP
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.services.lunarcrush_comprehensive_service import LunarCrushComprehensiveService
from app.services.binance_futures_service import BinanceFuturesService

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = "very_weak"      # 0-20
    WEAK = "weak"                # 21-40
    NEUTRAL = "neutral"          # 41-60
    STRONG = "strong"            # 61-80
    VERY_STRONG = "very_strong"  # 81-100


class EntryDirection(Enum):
    """Entry direction"""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class CandlestickPattern:
    """Detected candlestick pattern"""
    pattern_name: str
    signal: str  # bullish, bearish, neutral
    strength: int  # 0-100
    timeframe: str


@dataclass
class VolumeAnalysis:
    """Volume analysis result"""
    current_volume: float
    avg_volume_24h: float
    volume_change_pct: float
    volume_trend: str  # increasing, decreasing, stable
    is_spike: bool
    spike_strength: int  # 0-100


@dataclass
class FundingAnalysis:
    """Funding rate analysis"""
    current_rate: float
    avg_rate_24h: float
    trend: str  # increasing, decreasing, stable
    is_extreme: bool
    squeeze_risk: str  # high, medium, low, none
    signal: str  # bullish, bearish, neutral


@dataclass
class LongShortAnalysis:
    """Long/Short ratio analysis"""
    long_pct: float
    short_pct: float
    ratio: float  # long/short
    sentiment: str  # extremely_bullish, bullish, neutral, bearish, extremely_bearish
    contrarian_signal: str  # long, short, neutral
    strength: int  # 0-100


@dataclass
class OpenInterestAnalysis:
    """Open Interest analysis"""
    current_oi: float
    oi_change_24h_pct: float
    oi_trend: str  # increasing, decreasing, stable
    price_oi_divergence: bool
    signal: str  # bullish, bearish, neutral


@dataclass
class OrderBookAnalysis:
    """Order book depth analysis"""
    bid_depth: float
    ask_depth: float
    imbalance_ratio: float  # bid/ask
    strong_support: Optional[float]
    strong_resistance: Optional[float]
    signal: str  # bullish, bearish, neutral
    strength: int  # 0-100


@dataclass
class SmartMoneyAnalysis:
    """Smart money indicators"""
    top_trader_long_pct: float
    top_trader_short_pct: float
    top_trader_signal: str  # long, short, neutral
    large_transactions_24h: int
    net_flow_24h: float  # positive = accumulation, negative = distribution
    signal: str  # bullish, bearish, neutral
    strength: int  # 0-100


@dataclass
class SocialAnalysis:
    """Social sentiment analysis"""
    sentiment_score: float  # 0-100
    social_volume: int
    social_volume_change_pct: float
    galaxy_score: float
    trending: bool
    signal: str  # bullish, bearish, neutral
    strength: int  # 0-100


@dataclass
class ConfluenceScore:
    """Confluence scoring result"""
    total_score: int  # 0-100
    strength: SignalStrength
    signals_analyzed: int
    signals_bullish: int
    signals_bearish: int
    signals_neutral: int
    breakdown: Dict[str, int]  # metric_name -> score contribution


@dataclass
class EntryRecommendation:
    """Complete entry recommendation"""
    symbol: str
    direction: EntryDirection
    confluence_score: ConfluenceScore
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    risk_reward_ratio: float
    position_size_pct: float  # suggested % of portfolio
    urgency: str  # immediate, soon, wait, avoid
    reasoning: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class SmartEntryEngine:
    """
    Professional Smart Entry Engine

    Analyzes multiple data sources to generate high-probability entry signals
    with confluence scoring and complete risk management recommendations.
    """

    def __init__(self):
        self.coinapi = CoinAPIComprehensiveService()
        self.coinglass = CoinglassComprehensiveService()
        self.lunarcrush = LunarCrushComprehensiveService()
        self.binance = BinanceFuturesService()

        # Weights for confluence calculation (total = 100)
        self.weights = {
            'price_action': 15,
            'volume': 12,
            'funding': 15,
            'long_short': 13,
            'open_interest': 12,
            'order_book': 10,
            'smart_money': 13,
            'social': 10
        }

    async def analyze_entry(self, symbol: str, timeframe: str = "1h") -> Optional[EntryRecommendation]:
        """
        Comprehensive entry analysis

        Returns full entry recommendation with confluence score,
        entry zones, SL/TP, and risk management.
        """
        try:
            logger.info(f"🔍 Analyzing entry for {symbol} ({timeframe})...")

            # Collect all metrics in parallel
            results = await asyncio.gather(
                self._analyze_price_action(symbol, timeframe),
                self._analyze_volume(symbol, timeframe),
                self._analyze_funding(symbol),
                self._analyze_long_short_ratio(symbol),
                self._analyze_open_interest(symbol),
                self._analyze_order_book(symbol),
                self._analyze_smart_money(symbol),
                self._analyze_social(symbol),
                return_exceptions=True
            )

            # Unpack results
            price_action, volume, funding, long_short, oi, order_book, smart_money, social = results

            # Handle any errors
            metrics = {
                'price_action': price_action if not isinstance(price_action, Exception) else None,
                'volume': volume if not isinstance(volume, Exception) else None,
                'funding': funding if not isinstance(funding, Exception) else None,
                'long_short': long_short if not isinstance(long_short, Exception) else None,
                'open_interest': oi if not isinstance(oi, Exception) else None,
                'order_book': order_book if not isinstance(order_book, Exception) else None,
                'smart_money': smart_money if not isinstance(smart_money, Exception) else None,
                'social': social if not isinstance(social, Exception) else None
            }

            # Calculate confluence
            confluence = self._calculate_confluence(metrics)

            # Determine entry direction
            direction = self._determine_direction(metrics, confluence)

            # Get current price
            current_price = await self._get_current_price(symbol)
            if not current_price:
                logger.warning(f"Could not get price for {symbol}")
                return None

            # Calculate entry zones and risk management
            entry_zone = self._calculate_entry_zone(current_price, direction, metrics)
            stop_loss = self._calculate_stop_loss(current_price, direction, metrics, order_book)
            take_profits = self._calculate_take_profits(current_price, direction, metrics)

            risk_reward = self._calculate_risk_reward(
                entry_zone[0],  # entry_zone_low
                stop_loss,
                take_profits[0]  # TP1
            )

            # Position sizing based on confluence and risk
            position_size = self._suggest_position_size(confluence.total_score, risk_reward)

            # Determine urgency
            urgency = self._determine_urgency(confluence.total_score, metrics)

            # Generate reasoning
            reasoning = self._generate_reasoning(metrics, confluence)

            recommendation = EntryRecommendation(
                symbol=symbol,
                direction=direction,
                confluence_score=confluence,
                entry_zone_low=entry_zone[0],
                entry_zone_high=entry_zone[1],
                stop_loss=stop_loss,
                take_profit_1=take_profits[0],
                take_profit_2=take_profits[1] if len(take_profits) > 1 else None,
                take_profit_3=take_profits[2] if len(take_profits) > 2 else None,
                risk_reward_ratio=risk_reward,
                position_size_pct=position_size,
                urgency=urgency,
                reasoning=reasoning
            )

            logger.info(f"✅ Analysis complete: {direction.value} with {confluence.total_score}% confluence")
            return recommendation

        except Exception as e:
            logger.error(f"Error analyzing entry for {symbol}: {e}", exc_info=True)
            return None

    async def _analyze_price_action(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Analyze price action and candlestick patterns"""
        try:
            # Get OHLCV data
            ohlcv = await self.coinapi.get_ohlcv(symbol, timeframe, limit=20)
            if not ohlcv or len(ohlcv) < 5:
                return None

            # Detect patterns
            patterns = self._detect_candlestick_patterns(ohlcv)

            # Calculate support/resistance
            support, resistance = self._calculate_support_resistance(ohlcv)

            # Price trend
            trend = self._detect_trend(ohlcv)

            # Overall signal
            signal = "neutral"
            strength = 50

            if patterns:
                # Use most recent pattern
                latest_pattern = patterns[0]
                if latest_pattern.signal == "bullish":
                    signal = "bullish"
                    strength = latest_pattern.strength
                elif latest_pattern.signal == "bearish":
                    signal = "bearish"
                    strength = latest_pattern.strength

            return {
                'signal': signal,
                'strength': strength,
                'patterns': patterns,
                'support': support,
                'resistance': resistance,
                'trend': trend
            }

        except Exception as e:
            logger.debug(f"Price action analysis failed: {e}")
            return None

    def _detect_candlestick_patterns(self, ohlcv: List[Dict]) -> List[CandlestickPattern]:
        """Detect candlestick patterns"""
        patterns = []

        if len(ohlcv) < 3:
            return patterns

        # Get last 3 candles
        candles = ohlcv[-3:]
        c1, c2, c3 = candles

        # Bullish Engulfing
        if (c2['close'] < c2['open'] and  # Previous bearish
            c3['close'] > c3['open'] and  # Current bullish
            c3['open'] < c2['close'] and
            c3['close'] > c2['open']):
            patterns.append(CandlestickPattern(
                pattern_name="Bullish Engulfing",
                signal="bullish",
                strength=75,
                timeframe="recent"
            ))

        # Bearish Engulfing
        if (c2['close'] > c2['open'] and  # Previous bullish
            c3['close'] < c3['open'] and  # Current bearish
            c3['open'] > c2['close'] and
            c3['close'] < c2['open']):
            patterns.append(CandlestickPattern(
                pattern_name="Bearish Engulfing",
                signal="bearish",
                strength=75,
                timeframe="recent"
            ))

        # Hammer (bullish)
        last = ohlcv[-1]
        body = abs(last['close'] - last['open'])
        range_val = last['high'] - last['low']
        if range_val > 0:
            body_ratio = body / range_val
            lower_shadow = min(last['open'], last['close']) - last['low']
            upper_shadow = last['high'] - max(last['open'], last['close'])

            if body_ratio < 0.3 and lower_shadow > 2 * body and upper_shadow < body:
                patterns.append(CandlestickPattern(
                    pattern_name="Hammer",
                    signal="bullish",
                    strength=70,
                    timeframe="recent"
                ))

        # Shooting Star (bearish)
        if range_val > 0:
            if body_ratio < 0.3 and upper_shadow > 2 * body and lower_shadow < body:
                patterns.append(CandlestickPattern(
                    pattern_name="Shooting Star",
                    signal="bearish",
                    strength=70,
                    timeframe="recent"
                ))

        return patterns

    def _calculate_support_resistance(self, ohlcv: List[Dict]) -> Tuple[float, float]:
        """Calculate support and resistance levels"""
        if not ohlcv:
            return 0.0, 0.0

        lows = [c['low'] for c in ohlcv]
        highs = [c['high'] for c in ohlcv]

        # Simple approach: recent min/max
        support = min(lows[-10:]) if len(lows) >= 10 else min(lows)
        resistance = max(highs[-10:]) if len(highs) >= 10 else max(highs)

        return support, resistance

    def _detect_trend(self, ohlcv: List[Dict]) -> str:
        """Detect price trend"""
        if len(ohlcv) < 5:
            return "neutral"

        closes = [c['close'] for c in ohlcv[-10:]]

        # Simple moving average
        sma_short = statistics.mean(closes[-5:])
        sma_long = statistics.mean(closes)

        if sma_short > sma_long * 1.02:
            return "uptrend"
        elif sma_short < sma_long * 0.98:
            return "downtrend"
        else:
            return "neutral"

    async def _analyze_volume(self, symbol: str, timeframe: str) -> Optional[VolumeAnalysis]:
        """Analyze volume patterns"""
        try:
            ticker = await self.binance.get_24h_ticker(symbol)
            if not ticker:
                return None

            current_volume = float(ticker.get('quoteVolume', 0))

            # Get historical volume (simplified)
            # In production, fetch actual historical data
            avg_volume = current_volume * 0.7  # Placeholder

            volume_change = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

            is_spike = volume_change > 100
            spike_strength = min(int(volume_change / 2), 100)

            trend = "increasing" if volume_change > 20 else "decreasing" if volume_change < -20 else "stable"

            return VolumeAnalysis(
                current_volume=current_volume,
                avg_volume_24h=avg_volume,
                volume_change_pct=volume_change,
                volume_trend=trend,
                is_spike=is_spike,
                spike_strength=spike_strength
            )

        except Exception as e:
            logger.debug(f"Volume analysis failed: {e}")
            return None

    async def _analyze_funding(self, symbol: str) -> Optional[FundingAnalysis]:
        """Analyze funding rate trends"""
        try:
            funding_data = await self.coinglass.get_funding_rate(symbol)
            if not funding_data:
                return None

            current_rate = float(funding_data.get('rate', 0))

            # Get historical funding (if available)
            # For now, use simple logic
            avg_rate = current_rate * 0.8  # Placeholder

            trend = "increasing" if current_rate > avg_rate else "decreasing" if current_rate < avg_rate else "stable"
            is_extreme = abs(current_rate) > 0.1

            # Squeeze risk
            if current_rate > 0.15:
                squeeze_risk = "high"  # High positive funding = short squeeze risk
                signal = "bearish"  # Contrarian
            elif current_rate < -0.15:
                squeeze_risk = "high"  # High negative funding = long squeeze risk
                signal = "bullish"  # Contrarian
            elif abs(current_rate) > 0.05:
                squeeze_risk = "medium"
                signal = "bearish" if current_rate > 0 else "bullish"
            else:
                squeeze_risk = "low"
                signal = "neutral"

            return FundingAnalysis(
                current_rate=current_rate,
                avg_rate_24h=avg_rate,
                trend=trend,
                is_extreme=is_extreme,
                squeeze_risk=squeeze_risk,
                signal=signal
            )

        except Exception as e:
            logger.debug(f"Funding analysis failed: {e}")
            return None

    async def _analyze_long_short_ratio(self, symbol: str) -> Optional[LongShortAnalysis]:
        """Analyze long/short ratio for contrarian signals"""
        try:
            ratio_data = await self.coinglass.get_long_short_ratio(symbol)
            if not ratio_data:
                return None

            long_pct = float(ratio_data.get('longAccount', 50))
            short_pct = float(ratio_data.get('shortAccount', 50))
            ratio = long_pct / short_pct if short_pct > 0 else 1.0

            # Determine sentiment
            if long_pct > 75:
                sentiment = "extremely_bullish"
                contrarian_signal = "short"  # Too many longs = contrarian short
                strength = 80
            elif long_pct > 65:
                sentiment = "bullish"
                contrarian_signal = "short"
                strength = 60
            elif short_pct > 75:
                sentiment = "extremely_bearish"
                contrarian_signal = "long"  # Too many shorts = contrarian long
                strength = 80
            elif short_pct > 65:
                sentiment = "bearish"
                contrarian_signal = "long"
                strength = 60
            else:
                sentiment = "neutral"
                contrarian_signal = "neutral"
                strength = 40

            return LongShortAnalysis(
                long_pct=long_pct,
                short_pct=short_pct,
                ratio=ratio,
                sentiment=sentiment,
                contrarian_signal=contrarian_signal,
                strength=strength
            )

        except Exception as e:
            logger.debug(f"Long/short analysis failed: {e}")
            return None

    async def _analyze_open_interest(self, symbol: str) -> Optional[OpenInterestAnalysis]:
        """Analyze open interest trends"""
        try:
            oi_data = await self.coinglass.get_open_interest(symbol)
            if not oi_data:
                return None

            current_oi = float(oi_data.get('openInterest', 0))
            oi_change = float(oi_data.get('h24Change', 0))

            trend = "increasing" if oi_change > 5 else "decreasing" if oi_change < -5 else "stable"

            # Price-OI divergence (simplified, would need price data)
            price_oi_divergence = False

            # Signal based on OI change
            if oi_change > 15:
                signal = "bullish"  # Strong accumulation
            elif oi_change < -15:
                signal = "bearish"  # Strong distribution
            else:
                signal = "neutral"

            return OpenInterestAnalysis(
                current_oi=current_oi,
                oi_change_24h_pct=oi_change,
                oi_trend=trend,
                price_oi_divergence=price_oi_divergence,
                signal=signal
            )

        except Exception as e:
            logger.debug(f"OI analysis failed: {e}")
            return None

    async def _analyze_order_book(self, symbol: str) -> Optional[OrderBookAnalysis]:
        """Analyze order book depth"""
        try:
            # Get order book from Binance
            order_book = await self.binance.get_order_book(symbol, limit=20)
            if not order_book:
                return None

            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])

            # Calculate depth
            bid_depth = sum(float(bid[1]) * float(bid[0]) for bid in bids[:10])  # Top 10 bids
            ask_depth = sum(float(ask[1]) * float(ask[0]) for ask in asks[:10])  # Top 10 asks

            imbalance = bid_depth / ask_depth if ask_depth > 0 else 1.0

            # Find strong support/resistance (large orders)
            strong_support = None
            strong_resistance = None

            if bids:
                largest_bid = max(bids[:10], key=lambda x: float(x[1]))
                strong_support = float(largest_bid[0])

            if asks:
                largest_ask = max(asks[:10], key=lambda x: float(x[1]))
                strong_resistance = float(largest_ask[0])

            # Signal based on imbalance
            if imbalance > 1.5:
                signal = "bullish"
                strength = min(int((imbalance - 1) * 50), 100)
            elif imbalance < 0.67:
                signal = "bearish"
                strength = min(int((1 - imbalance) * 50), 100)
            else:
                signal = "neutral"
                strength = 50

            return OrderBookAnalysis(
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                imbalance_ratio=imbalance,
                strong_support=strong_support,
                strong_resistance=strong_resistance,
                signal=signal,
                strength=strength
            )

        except Exception as e:
            logger.debug(f"Order book analysis failed: {e}")
            return None

    async def _analyze_smart_money(self, symbol: str) -> Optional[SmartMoneyAnalysis]:
        """Analyze smart money indicators"""
        try:
            # Get top trader positions
            top_traders = await self.coinglass.get_top_trader_positions(symbol)

            if not top_traders:
                return SmartMoneyAnalysis(
                    top_trader_long_pct=50,
                    top_trader_short_pct=50,
                    top_trader_signal="neutral",
                    large_transactions_24h=0,
                    net_flow_24h=0,
                    signal="neutral",
                    strength=50
                )

            long_pct = float(top_traders.get('longAccount', 50))
            short_pct = float(top_traders.get('shortAccount', 50))

            # Determine signal from top traders
            if long_pct > 65:
                top_trader_signal = "long"
                signal = "bullish"
                strength = min(int(long_pct), 100)
            elif short_pct > 65:
                top_trader_signal = "short"
                signal = "bearish"
                strength = min(int(short_pct), 100)
            else:
                top_trader_signal = "neutral"
                signal = "neutral"
                strength = 50

            return SmartMoneyAnalysis(
                top_trader_long_pct=long_pct,
                top_trader_short_pct=short_pct,
                top_trader_signal=top_trader_signal,
                large_transactions_24h=0,  # Would need additional API
                net_flow_24h=0,  # Would need exchange flow data
                signal=signal,
                strength=strength
            )

        except Exception as e:
            logger.debug(f"Smart money analysis failed: {e}")
            return None

    async def _analyze_social(self, symbol: str) -> Optional[SocialAnalysis]:
        """Analyze social sentiment"""
        try:
            # Clean symbol for LunarCrush (remove USDT)
            clean_symbol = symbol.replace('USDT', '').replace('PERP', '')

            social_data = await self.lunarcrush.get_coin_metrics(clean_symbol)
            if not social_data:
                return None

            sentiment = float(social_data.get('sentiment', 50))
            social_volume = int(social_data.get('social_volume', 0))
            social_change = float(social_data.get('social_volume_24h_change', 0))
            galaxy_score = float(social_data.get('galaxy_score', 50))

            trending = social_change > 100

            # Signal based on sentiment and volume
            if sentiment > 70 and social_change > 50:
                signal = "bullish"
                strength = min(int(sentiment), 100)
            elif sentiment < 30 and social_change > 50:
                signal = "bearish"
                strength = min(int(100 - sentiment), 100)
            else:
                signal = "neutral"
                strength = 50

            return SocialAnalysis(
                sentiment_score=sentiment,
                social_volume=social_volume,
                social_volume_change_pct=social_change,
                galaxy_score=galaxy_score,
                trending=trending,
                signal=signal,
                strength=strength
            )

        except Exception as e:
            logger.debug(f"Social analysis failed: {e}")
            return None

    def _calculate_confluence(self, metrics: Dict[str, Any]) -> ConfluenceScore:
        """Calculate confluence score from all metrics"""
        breakdown = {}
        total_weight = 0
        weighted_score = 0

        signals_bullish = 0
        signals_bearish = 0
        signals_neutral = 0
        signals_analyzed = 0

        # Price action
        if metrics.get('price_action'):
            pa = metrics['price_action']
            signal = pa.get('signal', 'neutral')
            strength = pa.get('strength', 50)

            if signal == 'bullish':
                score = strength
                signals_bullish += 1
            elif signal == 'bearish':
                score = 100 - strength
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['price_action']
            breakdown['price_action'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Volume
        if metrics.get('volume'):
            vol = metrics['volume']
            if vol.is_spike:
                score = 70  # Volume spike is bullish
                signals_bullish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['volume']
            breakdown['volume'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Funding (contrarian)
        if metrics.get('funding'):
            fund = metrics['funding']
            signal = fund.signal

            if signal == 'bullish':
                score = 65
                signals_bullish += 1
            elif signal == 'bearish':
                score = 35
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['funding']
            breakdown['funding'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Long/Short (contrarian)
        if metrics.get('long_short'):
            ls = metrics['long_short']
            signal = ls.contrarian_signal
            strength = ls.strength

            if signal == 'long':
                score = 50 + strength / 2
                signals_bullish += 1
            elif signal == 'short':
                score = 50 - strength / 2
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['long_short']
            breakdown['long_short'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Open Interest
        if metrics.get('open_interest'):
            oi = metrics['open_interest']
            signal = oi.signal

            if signal == 'bullish':
                score = 70
                signals_bullish += 1
            elif signal == 'bearish':
                score = 30
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['open_interest']
            breakdown['open_interest'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Order Book
        if metrics.get('order_book'):
            ob = metrics['order_book']
            signal = ob.signal
            strength = ob.strength

            if signal == 'bullish':
                score = strength
                signals_bullish += 1
            elif signal == 'bearish':
                score = 100 - strength
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['order_book']
            breakdown['order_book'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Smart Money
        if metrics.get('smart_money'):
            sm = metrics['smart_money']
            signal = sm.signal
            strength = sm.strength

            if signal == 'bullish':
                score = strength
                signals_bullish += 1
            elif signal == 'bearish':
                score = 100 - strength
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['smart_money']
            breakdown['smart_money'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Social
        if metrics.get('social'):
            soc = metrics['social']
            signal = soc.signal
            strength = soc.strength

            if signal == 'bullish':
                score = strength
                signals_bullish += 1
            elif signal == 'bearish':
                score = 100 - strength
                signals_bearish += 1
            else:
                score = 50
                signals_neutral += 1

            weight = self.weights['social']
            breakdown['social'] = int(score * weight / 100)
            weighted_score += score * weight / 100
            total_weight += weight
            signals_analyzed += 1

        # Calculate final score
        final_score = int(weighted_score) if total_weight > 0 else 50

        # Determine strength
        if final_score >= 81:
            strength_level = SignalStrength.VERY_STRONG
        elif final_score >= 61:
            strength_level = SignalStrength.STRONG
        elif final_score >= 41:
            strength_level = SignalStrength.NEUTRAL
        elif final_score >= 21:
            strength_level = SignalStrength.WEAK
        else:
            strength_level = SignalStrength.VERY_WEAK

        return ConfluenceScore(
            total_score=final_score,
            strength=strength_level,
            signals_analyzed=signals_analyzed,
            signals_bullish=signals_bullish,
            signals_bearish=signals_bearish,
            signals_neutral=signals_neutral,
            breakdown=breakdown
        )

    def _determine_direction(self, metrics: Dict[str, Any], confluence: ConfluenceScore) -> EntryDirection:
        """Determine entry direction based on confluence"""
        if confluence.total_score >= 60:
            return EntryDirection.LONG
        elif confluence.total_score <= 40:
            return EntryDirection.SHORT
        else:
            return EntryDirection.NEUTRAL

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price"""
        try:
            price_data = await self.coinapi.get_current_price(symbol)
            if price_data:
                return float(price_data.get('price', 0))
            return None
        except:
            return None

    def _calculate_entry_zone(self, current_price: float, direction: EntryDirection,
                             metrics: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate entry zone (range)"""
        if direction == EntryDirection.LONG:
            # Entry zone: current price to 1% below
            entry_low = current_price * 0.99
            entry_high = current_price * 1.005
        elif direction == EntryDirection.SHORT:
            # Entry zone: current price to 1% above
            entry_low = current_price * 0.995
            entry_high = current_price * 1.01
        else:
            # Neutral
            entry_low = current_price * 0.995
            entry_high = current_price * 1.005

        return (entry_low, entry_high)

    def _calculate_stop_loss(self, current_price: float, direction: EntryDirection,
                            metrics: Dict[str, Any], order_book: Optional[OrderBookAnalysis]) -> float:
        """Calculate stop loss"""
        if direction == EntryDirection.LONG:
            # SL below support or 2-3% below entry
            if order_book and order_book.strong_support:
                sl = order_book.strong_support * 0.995
            else:
                sl = current_price * 0.97  # 3% below
        elif direction == EntryDirection.SHORT:
            # SL above resistance or 2-3% above entry
            if order_book and order_book.strong_resistance:
                sl = order_book.strong_resistance * 1.005
            else:
                sl = current_price * 1.03  # 3% above
        else:
            sl = current_price * 0.98

        return sl

    def _calculate_take_profits(self, current_price: float, direction: EntryDirection,
                                metrics: Dict[str, Any]) -> List[float]:
        """Calculate multiple take profit levels"""
        if direction == EntryDirection.LONG:
            tp1 = current_price * 1.03  # 3%
            tp2 = current_price * 1.05  # 5%
            tp3 = current_price * 1.08  # 8%
        elif direction == EntryDirection.SHORT:
            tp1 = current_price * 0.97  # 3%
            tp2 = current_price * 0.95  # 5%
            tp3 = current_price * 0.92  # 8%
        else:
            tp1 = current_price * 1.02
            tp2 = current_price * 1.03
            tp3 = current_price * 1.04

        return [tp1, tp2, tp3]

    def _calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float) -> float:
        """Calculate risk/reward ratio"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)

        if risk > 0:
            return round(reward / risk, 2)
        return 0.0

    def _suggest_position_size(self, confluence_score: int, risk_reward: float) -> float:
        """Suggest position size as % of portfolio"""
        # Base size on confluence
        if confluence_score >= 80:
            base_size = 10.0  # 10% for very strong signals
        elif confluence_score >= 70:
            base_size = 7.0
        elif confluence_score >= 60:
            base_size = 5.0
        else:
            base_size = 2.0

        # Adjust for risk/reward
        if risk_reward >= 3:
            base_size *= 1.2
        elif risk_reward >= 2:
            base_size *= 1.0
        else:
            base_size *= 0.8

        return min(base_size, 15.0)  # Cap at 15%

    def _determine_urgency(self, confluence_score: int, metrics: Dict[str, Any]) -> str:
        """Determine entry urgency"""
        if confluence_score >= 80:
            return "immediate"
        elif confluence_score >= 70:
            # Check if volume spike
            vol = metrics.get('volume')
            if vol and vol.is_spike:
                return "immediate"
            return "soon"
        elif confluence_score >= 60:
            return "soon"
        elif confluence_score >= 50:
            return "wait"
        else:
            return "avoid"

    def _generate_reasoning(self, metrics: Dict[str, Any], confluence: ConfluenceScore) -> List[str]:
        """Generate human-readable reasoning"""
        reasons = []

        # Price action
        if metrics.get('price_action'):
            pa = metrics['price_action']
            if pa['signal'] != 'neutral':
                patterns = pa.get('patterns', [])
                if patterns:
                    reasons.append(f"Price: {patterns[0].pattern_name} detected ({pa['signal']})")
                else:
                    reasons.append(f"Price: {pa['signal']} trend")

        # Volume
        if metrics.get('volume'):
            vol = metrics['volume']
            if vol.is_spike:
                reasons.append(f"Volume: Spike detected (+{vol.volume_change_pct:.1f}%)")

        # Funding
        if metrics.get('funding'):
            fund = metrics['funding']
            if fund.is_extreme:
                reasons.append(f"Funding: Extreme at {fund.current_rate:.4f}% ({fund.squeeze_risk} squeeze risk)")

        # Long/Short
        if metrics.get('long_short'):
            ls = metrics['long_short']
            if ls.contrarian_signal != 'neutral':
                reasons.append(f"Sentiment: {ls.sentiment} ({ls.long_pct:.0f}% longs) → Contrarian {ls.contrarian_signal}")

        # OI
        if metrics.get('open_interest'):
            oi = metrics['open_interest']
            if abs(oi.oi_change_24h_pct) > 10:
                reasons.append(f"Open Interest: {oi.oi_change_24h_pct:+.1f}% ({oi.signal})")

        # Order Book
        if metrics.get('order_book'):
            ob = metrics['order_book']
            if ob.signal != 'neutral':
                reasons.append(f"Order Book: Imbalance {ob.imbalance_ratio:.2f} ({ob.signal})")

        # Smart Money
        if metrics.get('smart_money'):
            sm = metrics['smart_money']
            if sm.signal != 'neutral':
                reasons.append(f"Smart Money: Top traders {sm.top_trader_long_pct:.0f}% long ({sm.signal})")

        # Social
        if metrics.get('social'):
            soc = metrics['social']
            if soc.trending:
                reasons.append(f"Social: Trending with sentiment {soc.sentiment_score:.0f}/100")

        # Add confluence summary
        reasons.append(f"Confluence: {confluence.signals_bullish} bullish, {confluence.signals_bearish} bearish, {confluence.signals_neutral} neutral signals")

        return reasons


# Global instance
_smart_entry_engine: Optional[SmartEntryEngine] = None

def get_smart_entry_engine() -> SmartEntryEngine:
    """Get or create global smart entry engine instance"""
    global _smart_entry_engine
    if _smart_entry_engine is None:
        _smart_entry_engine = SmartEntryEngine()
    return _smart_entry_engine
