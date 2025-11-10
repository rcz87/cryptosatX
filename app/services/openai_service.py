"""
OpenAI Integration Service
Enhances trading signals with GPT-4 analysis and insights
"""

import os
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from app.utils.logger import default_logger


@dataclass
class OpenAIConfig:
    """OpenAI service configuration"""

    api_key: str
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 1000
    temperature: float = 0.1  # Low temperature for consistent analysis
    timeout: int = 30


class OpenAIService:
    """
    OpenAI GPT-4 integration for enhanced trading analysis

    Features:
    - Signal validation and confirmation
    - Market sentiment analysis
    - Risk assessment
    - Trading strategy recommendations
    - News and social media analysis
    """

    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.logger = default_logger
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if not self._client or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def analyze_signal_with_gpt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        market_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Analyze trading signal using GPT-4 for enhanced insights

        Args:
            symbol: Cryptocurrency symbol
            signal_data: Current signal data from signal engine
            market_context: Additional market data for context

        Returns:
            Enhanced analysis with GPT insights
        """
        try:
            client = await self._get_client()

            # Build comprehensive prompt
            prompt = self._build_signal_analysis_prompt(
                symbol, signal_data, market_context
            )

            # Call OpenAI API
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )

            if response.status_code != 200:
                self.logger.error(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"OpenAI API error: {response.status_code}",
                    "analysis": None,
                }

            result = response.json()
            gpt_analysis = result["choices"][0]["message"]["content"]

            # Parse GPT response
            parsed_analysis = self._parse_gpt_analysis(gpt_analysis)

            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "original_signal": signal_data.get("signal"),
                "original_score": signal_data.get("score"),
                "gpt_analysis": parsed_analysis,
                "raw_response": gpt_analysis,
                "model_used": self.config.model,
            }

        except Exception as e:
            self.logger.error(f"Error in GPT signal analysis: {e}")
            return {"success": False, "error": str(e), "analysis": None}

    async def generate_market_sentiment_analysis(
        self, symbols: List[str], market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive market sentiment analysis using GPT-4

        Args:
            symbols: List of cryptocurrency symbols
            market_data: Market data for context

        Returns:
            Market sentiment analysis
        """
        try:
            client = await self._get_client()

            prompt = self._build_sentiment_analysis_prompt(symbols, market_data)

            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert cryptocurrency market analyst specializing in sentiment analysis and market psychology.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"OpenAI API error: {response.status_code}",
                }

            result = response.json()
            sentiment_analysis = result["choices"][0]["message"]["content"]

            return {
                "success": True,
                "symbols": symbols,
                "timestamp": datetime.utcnow().isoformat(),
                "sentiment_analysis": sentiment_analysis,
                "model_used": self.config.model,
            }

        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {"success": False, "error": str(e)}

    async def validate_signal_with_gpt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        conflicting_indicators: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Use GPT-4 to validate and potentially override trading signals

        Args:
            symbol: Cryptocurrency symbol
            signal_data: Current signal data
            conflicting_indicators: List of conflicting signals

        Returns:
            Validated signal with GPT recommendation
        """
        try:
            client = await self._get_client()

            prompt = self._build_signal_validation_prompt(
                symbol, signal_data, conflicting_indicators
            )

            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_validation_system_prompt(),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1,  # Very low for consistent validation
                },
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"OpenAI API error: {response.status_code}",
                    "validated_signal": signal_data.get("signal"),
                }

            result = response.json()
            validation_response = result["choices"][0]["message"]["content"]

            # Parse validation response
            validation = self._parse_validation_response(validation_response)

            return {
                "success": True,
                "symbol": symbol,
                "original_signal": signal_data.get("signal"),
                "validated_signal": validation.get("signal", signal_data.get("signal")),
                "confidence": validation.get("confidence", "medium"),
                "reasoning": validation.get("reasoning"),
                "gpt_recommendation": validation_response,
                "model_used": self.config.model,
            }

        except Exception as e:
            self.logger.error(f"Error in signal validation: {e}")
            return {
                "success": False,
                "error": str(e),
                "validated_signal": signal_data.get("signal"),
            }

    def _get_system_prompt(self) -> str:
        """Get system prompt for signal analysis"""
        return """You are an expert cryptocurrency trading analyst with deep knowledge of technical analysis, market psychology, and institutional trading patterns.

Your task is to analyze trading signals and provide comprehensive insights. Consider:
1. Technical indicators and their reliability
2. Market sentiment and psychology
3. Risk factors and potential catalysts
4. Institutional money flow patterns
5. Macro-economic factors affecting crypto

Provide analysis in JSON format with:
- overall_sentiment: "bullish", "bearish", or "neutral"
- confidence_level: "high", "medium", or "low"
- key_factors: list of important factors
- risks: list of potential risks
- opportunities: list of opportunities
- recommendation: "STRONG_BUY", "BUY", "HOLD", "SELL", or "STRONG_SELL"
- time_horizon: "short_term" (hours-days), "medium_term" (weeks), or "long_term" (months)"""

    def _get_validation_system_prompt(self) -> str:
        """Get system prompt for signal validation"""
        return """You are a conservative trading signal validator. Your job is to validate trading signals and ensure they are sound.

Analyze the provided signal data and conflicting indicators. Provide:
- validated_signal: "LONG", "SHORT", or "NEUTRAL"
- confidence: "high", "medium", or "low"
- reasoning: brief explanation of your decision

Be conservative and prioritize risk management. If signals are conflicting, default to NEUTRAL unless there's strong evidence for a directional bias."""

    def _build_signal_analysis_prompt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        market_context: Dict[str, Any] = None,
    ) -> str:
        """Build comprehensive prompt for signal analysis"""
        prompt = f"""Analyze the following trading signal for {symbol}:

SIGNAL DATA:
- Signal: {signal_data.get('signal', 'N/A')}
- Score: {signal_data.get('score', 'N/A')}/100
- Confidence: {signal_data.get('confidence', 'N/A')}
- Price: ${signal_data.get('price', 'N/A')}
- Funding Rate: {signal_data.get('metrics', {}).get('fundingRate', 'N/A')}
- Open Interest: {signal_data.get('metrics', {}).get('openInterest', 'N/A')}
- Social Score: {signal_data.get('metrics', {}).get('socialScore', 'N/A')}
- Price Trend: {signal_data.get('metrics', {}).get('priceTrend', 'N/A')}

REASONS:
{chr(10).join(f"- {reason}" for reason in signal_data.get('reasons', []))}

"""

        if market_context:
            prompt += f"ADDITIONAL CONTEXT:\n{json.dumps(market_context, indent=2)}\n\n"

        prompt += "Provide comprehensive analysis following the JSON format specified in the system prompt."

        return prompt

    def _build_sentiment_analysis_prompt(
        self, symbols: List[str], market_data: Dict[str, Any]
    ) -> str:
        """Build prompt for market sentiment analysis"""
        return f"""Analyze the overall market sentiment for these cryptocurrencies: {', '.join(symbols)}

MARKET DATA:
{json.dumps(market_data, indent=2)}

Provide insights on:
1. Overall market sentiment (bullish/bearish/neutral)
2. Key market drivers
3. Risk factors
4. Opportunities
5. Recommended positioning strategy

Focus on psychological factors and market dynamics that might not be captured by technical indicators alone."""

    def _build_signal_validation_prompt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        conflicting_indicators: List[str] = None,
    ) -> str:
        """Build prompt for signal validation"""
        prompt = f"""Validate this trading signal for {symbol}:

SIGNAL: {signal_data.get('signal', 'N/A')}
SCORE: {signal_data.get('score', 'N/A')}/100
CONFIDENCE: {signal_data.get('confidence', 'N/A')}

REASONS:
{chr(10).join(f"- {reason}" for reason in signal_data.get('reasons', []))}

"""

        if conflicting_indicators:
            prompt += f"CONFLICTING INDICATORS:\n{chr(10).join(f'- {indicator}' for indicator in conflicting_indicators)}\n\n"

        prompt += "Should this signal be validated? Provide your recommendation following the JSON format in the system prompt."

        return prompt

    def _parse_gpt_analysis(self, gpt_response: str) -> Dict[str, Any]:
        """Parse GPT analysis response"""
        try:
            # Try to parse as JSON first
            if gpt_response.strip().startswith("{"):
                return json.loads(gpt_response)

            # If not JSON, extract key information
            analysis = {
                "overall_sentiment": "neutral",
                "confidence_level": "medium",
                "key_factors": [],
                "risks": [],
                "opportunities": [],
                "recommendation": "HOLD",
                "time_horizon": "medium_term",
                "raw_analysis": gpt_response,
            }

            # Simple text parsing for key indicators
            response_lower = gpt_response.lower()

            if "bullish" in response_lower:
                analysis["overall_sentiment"] = "bullish"
            elif "bearish" in response_lower:
                analysis["overall_sentiment"] = "bearish"

            if "high confidence" in response_lower:
                analysis["confidence_level"] = "high"
            elif "low confidence" in response_lower:
                analysis["confidence_level"] = "low"

            return analysis

        except Exception as e:
            self.logger.error(f"Error parsing GPT analysis: {e}")
            return {
                "overall_sentiment": "neutral",
                "confidence_level": "low",
                "key_factors": ["Error parsing analysis"],
                "risks": ["Analysis parsing failed"],
                "opportunities": [],
                "recommendation": "HOLD",
                "time_horizon": "medium_term",
                "raw_analysis": gpt_response,
                "parse_error": str(e),
            }

    def _parse_validation_response(self, validation_response: str) -> Dict[str, Any]:
        """Parse validation response from GPT"""
        try:
            # Try to parse as JSON first
            if validation_response.strip().startswith("{"):
                return json.loads(validation_response)

            # Simple text parsing
            response_lower = validation_response.lower()

            validation = {
                "signal": "NEUTRAL",
                "confidence": "medium",
                "reasoning": validation_response,
            }

            if "long" in response_lower and "short" not in response_lower:
                validation["signal"] = "LONG"
            elif "short" in response_lower:
                validation["signal"] = "SHORT"

            if "high confidence" in response_lower:
                validation["confidence"] = "high"
            elif "low confidence" in response_lower:
                validation["confidence"] = "low"

            return validation

        except Exception as e:
            self.logger.error(f"Error parsing validation response: {e}")
            return {
                "signal": "NEUTRAL",
                "confidence": "low",
                "reasoning": f"Error parsing validation: {str(e)}",
            }


# Global instance
openai_service: Optional[OpenAIService] = None


async def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service instance"""
    global openai_service

    if openai_service is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        config = OpenAIConfig(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
        )

        openai_service = OpenAIService(config)

    return openai_service


async def close_openai_service():
    """Close OpenAI service"""
    global openai_service
    if openai_service:
        await openai_service.close()
