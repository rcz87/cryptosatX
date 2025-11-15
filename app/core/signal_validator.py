"""
Signal Validator for CryptoSatX

Cross-validates signals from multiple scanner sources to increase
confidence and reduce false positives.

Validation Logic:
- 1 scanner agrees: 60% confidence (single source)
- 2 scanners agree: 75% confidence (confirmed)
- 3+ scanners agree: 85-95% confidence (strong consensus)

Scanners checked:
- Smart Money (accumulation/distribution)
- MSS (multi-modal signal score)
- Technical (RSI, trends)
- Social (LunarCrush momentum)
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from app.utils.logger import default_logger


class SignalValidator:
    """
    Cross-validate signals from multiple sources

    Increases confidence by checking agreement across different scanners.
    """

    # Confidence thresholds
    CONFIDENCE_LEVELS = {
        1: 60,  # Single scanner
        2: 75,  # Two scanners agree
        3: 85,  # Three scanners agree
        4: 95   # All scanners agree
    }

    # Signal interpretation thresholds
    THRESHOLDS = {
        "smart_money_accumulation": 70,  # Accumulation score >70 = BUY
        "smart_money_distribution": 70,  # Distribution score >70 = SELL
        "mss_score": 75,                  # MSS >75 = BUY
        "technical_rsi_oversold": 30,     # RSI <30 = BUY
        "technical_rsi_overbought": 70,   # RSI >70 = SELL
        "social_momentum": 70             # Social score >70 = BUY
    }

    def __init__(self):
        self.logger = default_logger

    async def _check_smart_money(self, symbol: str) -> str:
        """
        Check Smart Money signal

        Returns: "BUY", "SELL", "NEUTRAL"
        """
        try:
            from app.services.smart_money_service import SmartMoneyService

            service = SmartMoneyService()
            result = await service.scan_markets(coins=[symbol])
            await service.close()

            # Check accumulation
            accumulation = result.get("accumulation", [])
            for signal in accumulation:
                if signal.get("symbol") == symbol:
                    score = signal.get("score", 0)
                    if score >= 7:  # Strong accumulation
                        return "BUY"

            # Check distribution
            distribution = result.get("distribution", [])
            for signal in distribution:
                if signal.get("symbol") == symbol:
                    score = signal.get("score", 0)
                    if score >= 7:  # Strong distribution
                        return "SELL"

            return "NEUTRAL"

        except Exception as e:
            self.logger.error(f"Error checking smart money for {symbol}: {e}")
            return "NEUTRAL"

    async def _check_mss(self, symbol: str) -> str:
        """
        Check MSS signal

        Returns: "BUY", "SELL", "NEUTRAL"
        """
        try:
            from app.services.mss_service import MSSService

            service = MSSService()
            result = await service.phase1_discovery(limit=100)
            await service.close()

            # Find symbol in results
            for coin in result:
                if coin.get("symbol") == symbol:
                    mss_score = coin.get("mss_score", 0)
                    if mss_score >= self.THRESHOLDS["mss_score"]:
                        return "BUY"
                    elif mss_score < 30:
                        return "SELL"

            return "NEUTRAL"

        except Exception as e:
            self.logger.error(f"Error checking MSS for {symbol}: {e}")
            return "NEUTRAL"

    async def _check_technical(self, symbol: str) -> str:
        """
        Check technical indicators (RSI)

        Returns: "BUY", "SELL", "NEUTRAL"
        """
        try:
            from app.services.coinglass_service import CoinglassService

            service = CoinglassService()
            rsi_data = await service.get_rsi(symbol)

            if rsi_data.get("success"):
                rsi = rsi_data.get("rsi", 50)

                if rsi < self.THRESHOLDS["technical_rsi_oversold"]:
                    return "BUY"  # Oversold
                elif rsi > self.THRESHOLDS["technical_rsi_overbought"]:
                    return "SELL"  # Overbought

            return "NEUTRAL"

        except Exception as e:
            self.logger.error(f"Error checking technical for {symbol}: {e}")
            return "NEUTRAL"

    async def _check_social(self, symbol: str) -> str:
        """
        Check social momentum

        Returns: "BUY", "SELL", "NEUTRAL"
        """
        try:
            from app.services.lunarcrush_service import LunarCrushService

            service = LunarCrushService()
            metrics = await service.get_coin_metrics(symbol)

            if metrics:
                galaxy_score = metrics.get("galaxy_score")

                if galaxy_score and galaxy_score >= self.THRESHOLDS["social_momentum"]:
                    return "BUY"  # Strong social momentum
                elif galaxy_score and galaxy_score < 30:
                    return "SELL"  # Weak social momentum

            return "NEUTRAL"

        except Exception as e:
            self.logger.error(f"Error checking social for {symbol}: {e}")
            return "NEUTRAL"

    async def validate_buy_signal(self, symbol: str) -> Dict:
        """
        Validate BUY signal by checking multiple scanners

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            {
                "action": "STRONG_BUY" | "BUY" | "WATCH" | "NEUTRAL",
                "confidence": 60-95,
                "confirmations": 0-4,
                "agreeing_scanners": [...],
                "disagreeing_scanners": [...],
                "scanner_signals": {
                    "smart_money": "BUY" | "SELL" | "NEUTRAL",
                    "mss": "BUY" | "SELL" | "NEUTRAL",
                    "technical": "BUY" | "SELL" | "NEUTRAL",
                    "social": "BUY" | "SELL" | "NEUTRAL"
                },
                "timestamp": "2025-11-15T14:30:00Z"
            }
        """
        self.logger.info(f"Validating BUY signal for {symbol}")

        # Check all scanners in parallel
        tasks = {
            "smart_money": self._check_smart_money(symbol),
            "mss": self._check_mss(symbol),
            "technical": self._check_technical(symbol),
            "social": self._check_social(symbol)
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Process results
        signals = {}
        for idx, (scanner, result) in enumerate(zip(tasks.keys(), results)):
            if isinstance(result, Exception):
                self.logger.error(f"Error from {scanner}: {result}")
                signals[scanner] = "NEUTRAL"
            else:
                signals[scanner] = result

        # Count BUY signals
        buy_signals = sum(1 for s in signals.values() if s == "BUY")
        sell_signals = sum(1 for s in signals.values() if s == "SELL")

        # Identify agreeing/disagreeing scanners
        agreeing_scanners = [k for k, v in signals.items() if v == "BUY"]
        disagreeing_scanners = [k for k, v in signals.items() if v != "BUY"]

        # Determine action and confidence
        if buy_signals >= 3:
            action = "STRONG_BUY"
            confidence = self.CONFIDENCE_LEVELS.get(buy_signals, 95)
        elif buy_signals >= 2:
            action = "BUY"
            confidence = self.CONFIDENCE_LEVELS[2]
        elif buy_signals >= 1:
            action = "WATCH"
            confidence = self.CONFIDENCE_LEVELS[1]
        else:
            # Check if majority is SELL
            if sell_signals >= 2:
                action = "AVOID"
                confidence = 70
            else:
                action = "NEUTRAL"
                confidence = 50

        result = {
            "action": action,
            "confidence": confidence,
            "confirmations": buy_signals,
            "agreeing_scanners": agreeing_scanners,
            "disagreeing_scanners": disagreeing_scanners,
            "scanner_signals": signals,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(
            f"Validation for {symbol}: {action} "
            f"({buy_signals}/4 confirmations, {confidence}% confidence)"
        )

        return result

    async def validate_sell_signal(self, symbol: str) -> Dict:
        """
        Validate SELL signal by checking multiple scanners

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Similar to validate_buy_signal but for SELL signals
        """
        self.logger.info(f"Validating SELL signal for {symbol}")

        # Check all scanners
        tasks = {
            "smart_money": self._check_smart_money(symbol),
            "mss": self._check_mss(symbol),
            "technical": self._check_technical(symbol),
            "social": self._check_social(symbol)
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Process results
        signals = {}
        for idx, (scanner, result) in enumerate(zip(tasks.keys(), results)):
            if isinstance(result, Exception):
                signals[scanner] = "NEUTRAL"
            else:
                signals[scanner] = result

        # Count SELL signals
        sell_signals = sum(1 for s in signals.values() if s == "SELL")
        buy_signals = sum(1 for s in signals.values() if s == "BUY")

        # Identify agreeing/disagreeing scanners
        agreeing_scanners = [k for k, v in signals.items() if v == "SELL"]
        disagreeing_scanners = [k for k, v in signals.items() if v != "SELL"]

        # Determine action and confidence
        if sell_signals >= 3:
            action = "STRONG_SELL"
            confidence = self.CONFIDENCE_LEVELS.get(sell_signals, 95)
        elif sell_signals >= 2:
            action = "SELL"
            confidence = self.CONFIDENCE_LEVELS[2]
        elif sell_signals >= 1:
            action = "CONSIDER_SELL"
            confidence = self.CONFIDENCE_LEVELS[1]
        else:
            # Check if majority is BUY
            if buy_signals >= 2:
                action = "HOLD"
                confidence = 70
            else:
                action = "NEUTRAL"
                confidence = 50

        result = {
            "action": action,
            "confidence": confidence,
            "confirmations": sell_signals,
            "agreeing_scanners": agreeing_scanners,
            "disagreeing_scanners": disagreeing_scanners,
            "scanner_signals": signals,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(
            f"Validation for {symbol}: {action} "
            f"({sell_signals}/4 confirmations, {confidence}% confidence)"
        )

        return result

    async def validate_signal(self, symbol: str, signal_type: str = "BUY") -> Dict:
        """
        Validate signal (convenience method)

        Args:
            symbol: Cryptocurrency symbol
            signal_type: "BUY" or "SELL"

        Returns:
            Validation result
        """
        if signal_type.upper() == "BUY":
            return await self.validate_buy_signal(symbol)
        elif signal_type.upper() == "SELL":
            return await self.validate_sell_signal(symbol)
        else:
            raise ValueError(f"Invalid signal_type: {signal_type}. Must be 'BUY' or 'SELL'")


# Global instance
signal_validator = SignalValidator()


# Convenience functions
async def validate_buy(symbol: str) -> Dict:
    """Validate BUY signal for a symbol"""
    return await signal_validator.validate_buy_signal(symbol)


async def validate_sell(symbol: str) -> Dict:
    """Validate SELL signal for a symbol"""
    return await signal_validator.validate_sell_signal(symbol)
