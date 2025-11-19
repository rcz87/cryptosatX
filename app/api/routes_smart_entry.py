"""
CryptoSatX Smart Entry API Routes
Professional entry signal analysis with confluence scoring
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import logging

from app.services.smart_entry_engine import get_smart_entry_engine, EntryDirection
from app.services.pro_alert_formatter import get_pro_alert_formatter
from app.services.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/smart-entry", tags=["smart-entry"])


@router.get("/analyze/{symbol}")
async def analyze_entry(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe for analysis (5m, 15m, 1h, 4h)"),
    send_telegram: bool = Query(default=False, description="Send alert to Telegram")
):
    """
    Analyze entry opportunity for a symbol using Smart Entry Engine

    Performs comprehensive multi-metric analysis and returns:
    - Confluence score (0-100)
    - Entry direction (LONG/SHORT/NEUTRAL)
    - Entry zone, SL, TP levels
    - Risk/Reward ratio
    - Position sizing recommendation
    - Complete reasoning

    Example:
    ```
    GET /smart-entry/analyze/FILUSDT?timeframe=1h&send_telegram=true
    ```
    """
    try:
        logger.info(f"Analyzing {symbol} for smart entry...")

        # Get smart entry engine
        engine = get_smart_entry_engine()

        # Analyze entry
        recommendation = await engine.analyze_entry(symbol.upper(), timeframe)

        if not recommendation:
            raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}. Check if symbol is valid.")

        # Format for Telegram if requested
        if send_telegram:
            try:
                telegram = TelegramNotifier()
                formatter = get_pro_alert_formatter()

                # Format professional alert
                alert_message = formatter.format_entry_alert(recommendation)

                # Send to Telegram
                await telegram.send_custom_alert(
                    title=f"{symbol} Smart Entry Analysis",
                    message=alert_message,
                    emoji="🎯"
                )

                logger.info(f"Telegram alert sent for {symbol}")
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

        # Return JSON response
        return {
            "success": True,
            "data": {
                "symbol": recommendation.symbol,
                "direction": recommendation.direction.value,
                "confluence": {
                    "score": recommendation.confluence_score.total_score,
                    "strength": recommendation.confluence_score.strength.value,
                    "signals_analyzed": recommendation.confluence_score.signals_analyzed,
                    "signals_bullish": recommendation.confluence_score.signals_bullish,
                    "signals_bearish": recommendation.confluence_score.signals_bearish,
                    "signals_neutral": recommendation.confluence_score.signals_neutral,
                    "breakdown": recommendation.confluence_score.breakdown
                },
                "entry": {
                    "entry_zone_low": recommendation.entry_zone_low,
                    "entry_zone_high": recommendation.entry_zone_high,
                    "stop_loss": recommendation.stop_loss,
                    "take_profit_1": recommendation.take_profit_1,
                    "take_profit_2": recommendation.take_profit_2,
                    "take_profit_3": recommendation.take_profit_3
                },
                "risk_management": {
                    "risk_reward_ratio": recommendation.risk_reward_ratio,
                    "position_size_pct": recommendation.position_size_pct,
                    "urgency": recommendation.urgency
                },
                "reasoning": recommendation.reasoning,
                "timestamp": recommendation.timestamp.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-batch")
async def analyze_batch(
    symbols: list[str],
    timeframe: str = Query(default="1h"),
    min_confluence: int = Query(default=60, ge=0, le=100, description="Minimum confluence score to include"),
    send_telegram: bool = Query(default=False)
):
    """
    Analyze multiple symbols and return best entry opportunities

    Analyzes all symbols in parallel and returns those with
    confluence score >= min_confluence, sorted by score.

    Example:
    ```json
    POST /smart-entry/analyze-batch
    {
      "symbols": ["FILUSDT", "ARBUSDT", "OPUSDT", "BTCUSDT"],
      "timeframe": "1h",
      "min_confluence": 70,
      "send_telegram": true
    }
    ```
    """
    try:
        if len(symbols) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols allowed per batch")

        logger.info(f"Batch analyzing {len(symbols)} symbols...")

        engine = get_smart_entry_engine()
        results = []

        # Analyze all symbols
        import asyncio
        tasks = [engine.analyze_entry(symbol.upper(), timeframe) for symbol in symbols]
        recommendations = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter and sort results
        for symbol, rec in zip(symbols, recommendations):
            if isinstance(rec, Exception):
                logger.warning(f"Failed to analyze {symbol}: {rec}")
                continue

            if not rec:
                continue

            # Filter by min confluence
            if rec.confluence_score.total_score >= min_confluence:
                results.append({
                    "symbol": rec.symbol,
                    "direction": rec.direction.value,
                    "confluence_score": rec.confluence_score.total_score,
                    "entry_zone_low": rec.entry_zone_low,
                    "entry_zone_high": rec.entry_zone_high,
                    "stop_loss": rec.stop_loss,
                    "take_profit_1": rec.take_profit_1,
                    "risk_reward_ratio": rec.risk_reward_ratio,
                    "position_size_pct": rec.position_size_pct,
                    "urgency": rec.urgency,
                    "top_reasons": rec.reasoning[:3]  # Top 3 reasons
                })

        # Sort by confluence score (highest first)
        results.sort(key=lambda x: x['confluence_score'], reverse=True)

        # Send best opportunity to Telegram if requested
        if send_telegram and results:
            best = results[0]
            try:
                # Re-analyze best symbol for full recommendation
                best_rec = await engine.analyze_entry(best['symbol'], timeframe)

                if best_rec:
                    telegram = TelegramNotifier()
                    formatter = get_pro_alert_formatter()

                    alert_message = formatter.format_entry_alert(best_rec)

                    await telegram.send_custom_alert(
                        title=f"🏆 Best Entry: {best['symbol']}",
                        message=alert_message,
                        emoji="🎯"
                    )

                    logger.info(f"Sent best entry alert for {best['symbol']}")
            except Exception as e:
                logger.error(f"Failed to send batch alert: {e}")

        return {
            "success": True,
            "data": {
                "analyzed": len(symbols),
                "opportunities": len(results),
                "min_confluence": min_confluence,
                "results": results
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/{symbol}")
async def test_smart_entry(symbol: str):
    """
    Test Smart Entry Engine with a symbol

    Quick test endpoint to verify engine is working.
    Returns formatted Telegram message (preview only, not sent).
    """
    try:
        engine = get_smart_entry_engine()
        recommendation = await engine.analyze_entry(symbol.upper(), "1h")

        if not recommendation:
            raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")

        formatter = get_pro_alert_formatter()

        # Format both long and short versions
        long_alert = formatter.format_entry_alert(recommendation)
        short_alert = formatter.format_short_alert(recommendation)

        return {
            "success": True,
            "data": {
                "symbol": recommendation.symbol,
                "direction": recommendation.direction.value,
                "confluence_score": recommendation.confluence_score.total_score,
                "telegram_preview": {
                    "full": long_alert,
                    "compact": short_alert
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for Smart Entry Engine"""
    try:
        # Test with BTC
        engine = get_smart_entry_engine()
        test_rec = await engine.analyze_entry("BTCUSDT", "1h")

        if test_rec:
            status = "healthy"
            message = f"Smart Entry Engine operational (test: BTC confluence {test_rec.confluence_score.total_score}%)"
        else:
            status = "degraded"
            message = "Engine running but test analysis failed"

        return {
            "success": True,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
