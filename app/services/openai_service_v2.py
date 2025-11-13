"""
OpenAI Integration Service V2 - Enhanced Signal Judge
Phase 1: Signal validation with verdict system (CONFIRM/DOWNSIZE/SKIP/WAIT)

Development version - does not affect production endpoints
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
class OpenAIConfigV2:
    """OpenAI service configuration V2"""
    api_key: str
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 1500
    temperature: float = 0.1
    timeout: int = 30


class OpenAIServiceV2:
    """
    OpenAI GPT-4 V2 - Enhanced Signal Judge
    
    Phase 1 Features:
    - Signal validation with verdict system
    - Structured JSON output
    - Risk adjustment suggestions
    - Telegram-ready summaries
    - Conflict detection
    """
    
    def __init__(self, config: OpenAIConfigV2):
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
    
    async def validate_signal_with_verdict(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        comprehensive_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 1: Enhanced signal validation with verdict system
        
        Returns structured JSON with:
        - verdict: CONFIRM/DOWNSIZE/SKIP/WAIT
        - key_agreements: factors supporting signal
        - key_conflicts: conflicting indicators
        - adjusted_risk_suggestion: position sizing recommendation
        - telegram_summary: ready-to-send alert text
        """
        try:
            client = await self._get_client()
            
            prompt = self._build_signal_judge_prompt(
                symbol, signal_data, comprehensive_metrics
            )
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_signal_judge_system_prompt(),
                        },
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
                    "verdict": "SKIP",
                }
            
            result = response.json()
            gpt_response = result["choices"][0]["message"]["content"]
            
            parsed_validation = self._parse_signal_judge_response(gpt_response)
            
            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "original_signal": signal_data.get("signal"),
                "original_score": signal_data.get("score"),
                "verdict": parsed_validation.get("verdict", "SKIP"),
                "ai_confidence": parsed_validation.get("ai_confidence", 50),
                "key_agreements": parsed_validation.get("key_agreements", []),
                "key_conflicts": parsed_validation.get("key_conflicts", []),
                "adjusted_risk_suggestion": parsed_validation.get("adjusted_risk_suggestion", {}),
                "telegram_summary": parsed_validation.get("telegram_summary", "Signal validation pending"),
                "raw_response": gpt_response,
                "model_used": self.config.model,
            }
            
        except Exception as e:
            self.logger.error(f"Error in signal judge validation: {e}")
            return {
                "success": False,
                "error": str(e),
                "verdict": "SKIP",
            }
    
    def _get_signal_judge_system_prompt(self) -> str:
        """Enhanced system prompt for Signal Judge"""
        return """You are an expert Signal Judge for cryptocurrency futures trading. Your role is to validate trading signals and provide actionable verdicts.

CRITICAL RULES:
1. You MUST respond with valid JSON only (no markdown, no extra text)
2. Be conservative - protect capital first
3. Detect conflicting indicators carefully
4. Consider ALL 8 layers: liquidations, funding, momentum, long/short ratio, smart money, OI trend, social, fear/greed

OUTPUT FORMAT (strict JSON):
{
  "verdict": "CONFIRM | DOWNSIZE | SKIP | WAIT",
  "ai_confidence": 0-100,
  "key_agreements": [
    "factor 1 supporting signal",
    "factor 2 supporting signal",
    "factor 3 supporting signal"
  ],
  "key_conflicts": [
    "conflicting indicator 1",
    "conflicting indicator 2"
  ],
  "adjusted_risk_suggestion": {
    "risk_factor": "NORMAL | REDUCED | AVOID",
    "position_size_multiplier": 0.5-1.5,
    "reasoning": "brief explanation"
  },
  "telegram_summary": "Ready-to-send text for Telegram alert (max 3 sentences, plain language)"
}

VERDICT DEFINITIONS:
- CONFIRM: Strong alignment across layers, high confidence, proceed with full position
- DOWNSIZE: Mixed signals but lean toward original direction, reduce position size to 0.5x
- SKIP: Too many conflicts or weak conviction, do not trade
- WAIT: Potential setup but timing unclear, wait for better entry or confirmation

ANALYSIS APPROACH:
1. Check trend alignment across timeframes (H4, H1, 15m if available)
2. Verify funding rate and OI support the directional bias
3. Look for institutional footprints (smart money, orderbook depth)
4. Assess sentiment extremes (social, fear/greed)
5. Identify deal-breakers: overbought RSI + bullish signal, extreme funding, low liquidity

Be strict. If in doubt, choose SKIP or WAIT."""
    
    def _build_signal_judge_prompt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        comprehensive_metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build comprehensive prompt for Signal Judge"""
        
        prompt = f"""Validate this trading signal for {symbol}:

ORIGINAL SIGNAL: {signal_data.get('signal', 'UNKNOWN')}
SCORE: {signal_data.get('score', 0)}/100
CONFIDENCE: {signal_data.get('confidence', 'unknown')}
CURRENT PRICE: ${signal_data.get('price', 'N/A')}

TOP REASONS (from signal engine):
"""
        
        for idx, reason in enumerate(signal_data.get('reasons', []), 1):
            prompt += f"{idx}. {reason}\n"
        
        metrics = signal_data.get('metrics', {})
        prompt += f"""
CORE METRICS:
- Funding Rate: {metrics.get('fundingRate', 'N/A')}
- Open Interest: {metrics.get('openInterest', 'N/A')}
- Social Score: {metrics.get('socialScore', 'N/A')}
- Price Trend: {metrics.get('priceTrend', 'N/A')}
"""
        
        if comprehensive_metrics:
            prompt += f"""
COMPREHENSIVE DATA (Coinglass):
{json.dumps(comprehensive_metrics, indent=2)}
"""
        
        lunarcrush = signal_data.get('lunarCrushMetrics')
        if lunarcrush:
            prompt += f"""
LUNARCRUSH SOCIAL DATA:
- Galaxy Score: {lunarcrush.get('galaxy_score', 'N/A')}
- Alt Rank: {lunarcrush.get('alt_rank', 'N/A')}
- Social Volume 24h: {lunarcrush.get('social_volume_24h', 'N/A')}
"""
        
        coinapi = signal_data.get('coinAPIMetrics')
        if coinapi:
            prompt += f"""
COINAPI WHALE DATA:
- Whale Buy Pressure: {coinapi.get('whale_buy_pressure', 'N/A')}
- Large Trades 24h: {coinapi.get('large_trades_24h', 'N/A')}
"""
        
        prompt += """
TASK: Analyze this signal and provide your verdict following the exact JSON format specified in the system prompt. Consider all 8 layers and identify agreements vs conflicts."""
        
        return prompt
    
    def _parse_signal_judge_response(self, gpt_response: str) -> Dict[str, Any]:
        """Parse Signal Judge JSON response"""
        try:
            response_clean = gpt_response.strip()
            
            if response_clean.startswith("```json"):
                response_clean = response_clean.replace("```json", "").replace("```", "").strip()
            elif response_clean.startswith("```"):
                response_clean = response_clean.replace("```", "").strip()
            
            parsed = json.loads(response_clean)
            
            verdict = parsed.get("verdict", "SKIP").upper()
            if verdict not in ["CONFIRM", "DOWNSIZE", "SKIP", "WAIT"]:
                verdict = "SKIP"
            
            return {
                "verdict": verdict,
                "ai_confidence": min(100, max(0, int(parsed.get("ai_confidence", 50)))),
                "key_agreements": parsed.get("key_agreements", []),
                "key_conflicts": parsed.get("key_conflicts", []),
                "adjusted_risk_suggestion": parsed.get("adjusted_risk_suggestion", {
                    "risk_factor": "NORMAL",
                    "position_size_multiplier": 1.0,
                    "reasoning": "Default risk settings"
                }),
                "telegram_summary": parsed.get("telegram_summary", "Signal validation complete"),
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error in Signal Judge response: {e}")
            self.logger.error(f"Raw response: {gpt_response}")
            
            fallback_verdict = "SKIP"
            if "confirm" in gpt_response.lower():
                fallback_verdict = "CONFIRM"
            elif "downsize" in gpt_response.lower():
                fallback_verdict = "DOWNSIZE"
            elif "wait" in gpt_response.lower():
                fallback_verdict = "WAIT"
            
            return {
                "verdict": fallback_verdict,
                "ai_confidence": 30,
                "key_agreements": ["Unable to parse detailed analysis"],
                "key_conflicts": ["JSON parsing failed"],
                "adjusted_risk_suggestion": {
                    "risk_factor": "REDUCED",
                    "position_size_multiplier": 0.5,
                    "reasoning": "Fallback due to parsing error"
                },
                "telegram_summary": f"Signal validation uncertain - defaulting to {fallback_verdict}",
                "parse_error": str(e),
            }
        
        except Exception as e:
            self.logger.error(f"Unexpected error parsing Signal Judge response: {e}")
            return {
                "verdict": "SKIP",
                "ai_confidence": 20,
                "key_agreements": [],
                "key_conflicts": ["Parse error occurred"],
                "adjusted_risk_suggestion": {
                    "risk_factor": "AVOID",
                    "position_size_multiplier": 0.0,
                    "reasoning": "Critical error in validation"
                },
                "telegram_summary": "Signal validation failed - skipping trade",
            }


openai_service_v2: Optional[OpenAIServiceV2] = None


async def get_openai_service_v2() -> OpenAIServiceV2:
    """Get or create OpenAI Service V2 instance"""
    global openai_service_v2
    
    if openai_service_v2 is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        config = OpenAIConfigV2(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS_V2", "1500")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
        )
        
        openai_service_v2 = OpenAIServiceV2(config)
    
    return openai_service_v2


async def close_openai_service_v2():
    """Close OpenAI Service V2"""
    global openai_service_v2
    if openai_service_v2:
        await openai_service_v2.close()
