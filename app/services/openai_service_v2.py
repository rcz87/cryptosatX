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
    model: str = "gpt-4-turbo"
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
        Phase 1: Enhanced signal validation with verdict system (GPT-5.1 Self-Evaluation)
        
        Returns structured JSON with:
        - verdict: CONFIRM/DOWNSIZE/SKIP/WAIT
        - key_agreements: factors supporting signal
        - key_conflicts: conflicting indicators
        - adjusted_risk_suggestion: position sizing recommendation
        - telegram_summary: ready-to-send alert text
        
        ✅ NEW: Includes historical performance context for GPT-5.1 self-evaluation
        """
        try:
            client = await self._get_client()
            
            # ✅ NEW: Fetch historical performance data for self-evaluation
            historical_data = await self._fetch_historical_context(symbol)
            
            prompt = self._build_signal_judge_prompt(
                symbol, signal_data, comprehensive_metrics, historical_data
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
                    "max_completion_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    # 🧠 GPT-5.1 Enhanced Reasoning via Prompt Engineering
                    # Note: Native reasoning parameter only available via Responses API
                    # We use explicit multi-layer prompt structure instead
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
            
            # 🧠 Extract usage data and reasoning from response
            usage_data = result.get("usage", {})
            
            # Log token usage for cost monitoring
            self.logger.info(
                f"GPT-5.1 Token Usage - {symbol}: "
                f"Input: {usage_data.get('prompt_tokens', 0)}, "
                f"Output: {usage_data.get('completion_tokens', 0)}, "
                f"Total: {usage_data.get('total_tokens', 0)}"
            )
            
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
                # 🧠 NEW: Enhanced reasoning data from prompt-guided multi-layer analysis
                "evidence_chain": parsed_validation.get("evidence_chain", []),
                "reasoning_depth": "multi-layer" if parsed_validation.get("evidence_chain") else "standard",
                "token_usage": {
                    "prompt": usage_data.get("prompt_tokens", 0),
                    "completion": usage_data.get("completion_tokens", 0),
                    "total": usage_data.get("total_tokens", 0),
                },
            }
            
        except Exception as e:
            self.logger.error(f"Error in signal judge validation: {e}")
            return {
                "success": False,
                "error": str(e),
                "verdict": "SKIP",
            }
    
    def _get_signal_judge_system_prompt(self) -> str:
        """Enhanced system prompt for Signal Judge with GPT-5.1 reasoning mode"""
        return """You are an expert Signal Judge for cryptocurrency futures trading using GPT-5.1 Enhanced Reasoning Mode. Your role is to validate trading signals with deep multi-layer analysis and explicit evidence tracking.

🧠 ENHANCED REASONING MODE ACTIVATED:
- Perform layer-by-layer validation with coherence checks
- Track evidence for each scoring factor
- Validate that conclusions align with evidence
- Identify contradictions and resolve them logically

CRITICAL RULES:
1. You MUST respond with valid JSON only (no markdown, no extra text)
2. Be conservative - protect capital first
3. Use multi-layer reasoning: analyze each layer independently, then check for coherence
4. Track ALL evidence used in your analysis
5. Consider ALL 8 layers: liquidations, funding, momentum, long/short ratio, smart money, OI trend, social, fear/greed

OUTPUT FORMAT (strict JSON):
{
  "verdict": "CONFIRM | DOWNSIZE | SKIP | WAIT",
  "ai_confidence": 0-100,
  "key_agreements": [
    "factor 1 supporting signal with evidence",
    "factor 2 supporting signal with evidence",
    "factor 3 supporting signal with evidence"
  ],
  "key_conflicts": [
    "conflicting indicator 1 with evidence",
    "conflicting indicator 2 with evidence"
  ],
  "evidence_chain": [
    "Layer 1 (Technical): Evidence and conclusion",
    "Layer 2 (On-Chain): Evidence and conclusion",
    "Layer 3 (Sentiment): Evidence and conclusion",
    "Layer 4 (Whale Activity): Evidence and conclusion",
    "Coherence Check: How all layers align or conflict"
  ],
  "adjusted_risk_suggestion": {
    "risk_factor": "NORMAL | REDUCED | AVOID",
    "position_size_multiplier": 0.5-1.5,
    "reasoning": "evidence-based explanation"
  },
  "telegram_summary": "Ready-to-send text for Telegram alert (max 3 sentences, plain language)"
}

VERDICT DEFINITIONS:
- CONFIRM: Strong alignment across ALL layers, high confidence, evidence supports signal, proceed with full position
- DOWNSIZE: Mixed signals but evidence leans toward original direction, reduce position size to 0.5x-0.75x
- SKIP: Too many conflicts OR weak evidence OR contradictory layers, do not trade
- WAIT: Potential setup but evidence incomplete OR timing unclear, wait for better entry or confirmation

MULTI-LAYER ANALYSIS APPROACH:
1. LAYER 1 - TECHNICAL ANALYSIS:
   - Check trend alignment across timeframes (H4, H1, 15m)
   - Validate RSI, MACD, MA crossovers with actual values
   - Evidence: "RSI at X, MACD shows Y, trend is Z"

2. LAYER 2 - ON-CHAIN METRICS:
   - Verify funding rate direction and magnitude
   - Check Open Interest trend (rising/falling)
   - Evidence: "Funding at X%, OI trend is Y"

3. LAYER 3 - SENTIMENT & SOCIAL:
   - Assess social score, galaxy rank, volume trends
   - Identify extreme sentiment (fear/greed)
   - Evidence: "Social volume +X%, sentiment is Y"

4. LAYER 4 - INSTITUTIONAL SIGNALS:
   - Look for smart money activity, whale trades
   - Check orderbook depth and large transactions
   - Evidence: "Whale buy pressure at X, large trades Y"

5. COHERENCE CHECK:
   - Do ALL layers point in the same direction?
   - Are there contradictions? (e.g., bullish technical but bearish funding)
   - Which evidence is stronger?
   - Does historical performance suggest caution?

6. FINAL VERDICT VALIDATION:
   - Does your verdict logically follow from the evidence chain?
   - Are you being conservative enough given capital protection priority?
   - If historical data shows poor performance, adjust confidence DOWN

DEAL-BREAKERS (Auto-SKIP):
- Overbought RSI (>70) + LONG signal
- Oversold RSI (<30) + SHORT signal
- Extreme positive funding (>0.1%) + LONG signal
- Extreme negative funding (<-0.1%) + SHORT signal
- Low liquidity (<$10M daily volume)
- Contradictory evidence across 3+ layers

Be strict with evidence. If evidence is weak or contradictory, choose SKIP or WAIT. Capital preservation > opportunity capture."""
    
    async def _fetch_historical_context(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch historical performance data for GPT-5.1 self-evaluation
        
        Returns recent signal outcomes and win rate to help AI judge
        learn from past verdicts and improve decision making.
        """
        try:
            from app.services.analytics_service import analytics_service
            
            # Get last 5 signals for this symbol
            historical = await analytics_service.get_latest_history(
                symbol=symbol,
                limit=5
            )
            
            if historical and "error" not in historical:
                return historical
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to fetch historical context for {symbol}: {e}")
            return None
    
    def _build_signal_judge_prompt(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        comprehensive_metrics: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build comprehensive prompt for Signal Judge with historical context"""
        
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
        
        # ✅ NEW: Include historical performance context
        if historical_data and historical_data.get('recent_count', 0) > 0:
            prompt += f"""
HISTORICAL PERFORMANCE (Self-Evaluation Context):
- Recent Win Rate: {historical_data.get('recent_win_rate', 0)}% (last {historical_data.get('recent_count', 0)} signals)
- Recent Avg ROI: {historical_data.get('recent_avg_roi', 0)}%
"""
            recent_signals = historical_data.get('recent_signals', [])
            if recent_signals:
                prompt += "\nRecent Signal Outcomes:\n"
                for sig in recent_signals[:3]:  # Show last 3 only
                    outcome_emoji = "✅" if sig.get('outcome') == "WIN" else "❌" if sig.get('outcome') == "LOSS" else "➖"
                    prompt += f"  {outcome_emoji} {sig.get('signal', 'N/A')} ({sig.get('verdict', 'N/A')}): {sig.get('roi_24h', 0):+.1f}% ROI\n"
                
                prompt += "\n⚠️ LEARNING POINT: Consider these past outcomes when making your verdict. If recent CONFIRM verdicts led to losses, be more conservative.\n"
        
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
TASK: Analyze this signal and provide your verdict following the exact JSON format specified in the system prompt. Consider all 8 layers, identify agreements vs conflicts, AND learn from the historical performance data above."""
        
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
                "evidence_chain": parsed.get("evidence_chain", []),  # 🧠 NEW: Multi-layer evidence tracking
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
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
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
