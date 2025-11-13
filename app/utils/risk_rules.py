"""
Rule-Based Risk Assessment System
Fallback logic for when OpenAI V2 Signal Judge is unavailable
"""
from typing import Dict, Any, Tuple


def rule_based_risk_mode(signal_data: Dict[str, Any]) -> str:
    """
    Determine risk mode based on signal metrics
    
    Returns:
        str: "AVOID" | "REDUCED" | "NORMAL" | "AGGRESSIVE"
    """
    score = signal_data.get("score", 50)
    signal = signal_data.get("signal", "NEUTRAL").upper()
    
    metrics = signal_data.get("metrics", {})
    funding_rate = abs(metrics.get("fundingRate", 0)) * 100
    
    premium = signal_data.get("premiumMetrics", {})
    ls_ratio = premium.get("longShortRatio", {})
    long_pct = ls_ratio.get("longAccountPct", 50)
    
    liquidations = premium.get("liquidations", {})
    long_liq_pct = liquidations.get("longLiqPct", 50)
    
    if score < 50:
        return "AVOID"
    
    if score < 55:
        if funding_rate > 0.25 or long_pct > 70:
            return "AVOID"
        return "REDUCED"
    
    if score < 60:
        if funding_rate > 0.3 and long_pct > 65:
            return "AVOID"
        elif funding_rate > 0.2 or long_pct > 68:
            return "REDUCED"
        return "REDUCED"
    
    if score < 65:
        if funding_rate > 0.4 and long_pct > 70:
            return "REDUCED"
        return "NORMAL"
    
    if score >= 75:
        if funding_rate < 0.15 and 45 < long_pct < 55:
            return "AGGRESSIVE"
        return "NORMAL"
    
    return "NORMAL"


def rule_based_multiplier(signal_data: Dict[str, Any]) -> float:
    """
    Calculate position size multiplier based on risk mode
    
    Returns:
        float: 0.0 (skip), 0.5 (half size), 1.0 (full size), 1.5 (aggressive)
    """
    risk_mode = rule_based_risk_mode(signal_data)
    
    multipliers = {
        "AVOID": 0.0,
        "REDUCED": 0.5,
        "NORMAL": 1.0,
        "AGGRESSIVE": 1.5,
    }
    
    return multipliers.get(risk_mode, 1.0)


def rule_based_verdict(signal_data: Dict[str, Any]) -> str:
    """
    Generate trading verdict based on rules
    
    Returns:
        str: "CONFIRM" | "DOWNSIZE" | "SKIP" | "WAIT"
    """
    score = signal_data.get("score", 50)
    signal = signal_data.get("signal", "NEUTRAL").upper()
    risk_mode = rule_based_risk_mode(signal_data)
    
    if signal == "NEUTRAL":
        return "SKIP"
    
    if risk_mode == "AVOID":
        return "SKIP"
    
    if risk_mode == "REDUCED":
        if score < 58:
            return "WAIT"
        return "DOWNSIZE"
    
    if risk_mode == "NORMAL":
        if score >= 65:
            return "CONFIRM"
        return "DOWNSIZE"
    
    if risk_mode == "AGGRESSIVE":
        return "CONFIRM"
    
    return "DOWNSIZE"


def get_risk_warnings(signal_data: Dict[str, Any]) -> Tuple[list, list]:
    """
    Analyze signal and extract risk warnings and agreements
    
    Returns:
        Tuple[list, list]: (warnings, agreements)
    """
    warnings = []
    agreements = []
    
    metrics = signal_data.get("metrics", {})
    premium = signal_data.get("premiumMetrics", {})
    signal = signal_data.get("signal", "NEUTRAL").upper()
    score = signal_data.get("score", 50)
    
    funding_rate = abs(metrics.get("fundingRate", 0)) * 100
    
    ls_ratio = premium.get("longShortRatio", {})
    long_pct = ls_ratio.get("longAccountPct", 50)
    ls_sentiment = ls_ratio.get("sentiment", "neutral")
    
    liquidations = premium.get("liquidations", {})
    liq_imbalance = liquidations.get("imbalance", "balanced")
    
    oi_trend_data = premium.get("oiTrend", {})
    oi_change = oi_trend_data.get("oiChangePct", 0)
    
    top_trader = premium.get("topTraderRatio", {})
    smart_money_bias = top_trader.get("smartMoneyBias", "neutral")
    
    fear_greed = signal_data.get("fearGreedIndex", {})
    fg_value = fear_greed.get("value", 50)
    fg_sentiment = fear_greed.get("sentiment", "neutral")
    
    if signal == "LONG":
        if funding_rate > 0.3:
            warnings.append(f"High funding rate ({funding_rate:.3f}%) - longs overleveraged")
        elif funding_rate > 0.2:
            agreements.append(f"Moderate funding rate ({funding_rate:.3f}%)")
        else:
            agreements.append(f"Low funding rate ({funding_rate:.3f}%) - favorable for longs")
        
        if long_pct > 70:
            warnings.append(f"Overcrowded longs ({long_pct:.1f}%) - contrarian bearish")
        elif long_pct > 60:
            warnings.append(f"High long concentration ({long_pct:.1f}%)")
        elif 50 < long_pct < 60:
            agreements.append(f"Balanced long bias ({long_pct:.1f}%)")
        
        if smart_money_bias == "long":
            agreements.append("Smart money positioning: LONG")
        elif smart_money_bias == "short":
            warnings.append("Smart money positioning: SHORT (contrarian)")
        
        if oi_change > 5:
            agreements.append(f"Strong OI increase ({oi_change:+.1f}%) - conviction rising")
        elif oi_change < -5:
            warnings.append(f"OI declining ({oi_change:+.1f}%) - losing interest")
        
        if fg_value < 30:
            agreements.append(f"Fear & Greed: {fg_sentiment} ({fg_value}) - contrarian buy zone")
        elif fg_value > 75:
            warnings.append(f"Fear & Greed: {fg_sentiment} ({fg_value}) - euphoria risk")
    
    elif signal == "SHORT":
        if funding_rate > 0.3:
            agreements.append(f"High funding rate ({funding_rate:.3f}%) - longs overleveraged, favorable for shorts")
        
        if long_pct > 70:
            agreements.append(f"Overcrowded longs ({long_pct:.1f}%) - good short setup")
        elif long_pct < 40:
            warnings.append(f"Longs already squeezed ({long_pct:.1f}%)")
        
        if smart_money_bias == "short":
            agreements.append("Smart money positioning: SHORT")
        elif smart_money_bias == "long":
            warnings.append("Smart money positioning: LONG (contrarian)")
        
        if fg_value > 75:
            agreements.append(f"Fear & Greed: {fg_sentiment} ({fg_value}) - contrarian sell zone")
        elif fg_value < 25:
            warnings.append(f"Fear & Greed: {fg_sentiment} ({fg_value}) - already fearful")
    
    if score < 55:
        warnings.append(f"Low conviction score ({score:.1f}/100)")
    elif score > 70:
        agreements.append(f"High conviction score ({score:.1f}/100)")
    
    price_trend = metrics.get("priceTrend", "neutral")
    if price_trend == "neutral":
        warnings.append("Price trend: neutral (unclear direction)")
    else:
        trend_aligned = (signal == "LONG" and "bull" in price_trend.lower()) or \
                       (signal == "SHORT" and "bear" in price_trend.lower())
        if trend_aligned:
            agreements.append(f"Price trend: {price_trend} (aligned)")
        else:
            warnings.append(f"Price trend: {price_trend} (misaligned)")
    
    return warnings, agreements


def generate_rule_based_summary(
    signal_data: Dict[str, Any],
    verdict: str,
    risk_mode: str,
    warnings: list,
    agreements: list
) -> str:
    """
    Generate human-readable summary for rule-based assessment
    
    Returns:
        str: Telegram-ready summary text
    """
    symbol = signal_data.get("symbol", "UNKNOWN")
    signal = signal_data.get("signal", "NEUTRAL").upper()
    score = signal_data.get("score", 50)
    
    if verdict == "SKIP":
        if score < 50:
            return f"{symbol} {signal} SIGNAL: Skipping - low conviction score ({score:.1f}/100). " + \
                   (f"Key concerns: {', '.join(warnings[:2])}." if warnings else "Insufficient edge to trade.")
        else:
            primary_warning = warnings[0] if warnings else "mixed signals"
            return f"{symbol} {signal} SIGNAL: Skipping this setup. {primary_warning.capitalize()}. " + \
                   "Risk-reward not favorable - waiting for better opportunity."
    
    elif verdict == "WAIT":
        return f"{symbol} {signal} SIGNAL: Watchlist only. Setup developing but timing unclear. " + \
               (f"Monitor: {warnings[0] if warnings else 'market conditions'}." if warnings else "Wait for confirmation.")
    
    elif verdict == "DOWNSIZE":
        if risk_mode == "REDUCED":
            concern = warnings[0] if warnings else "elevated risk metrics"
            return f"{symbol} {signal} SIGNAL: Partial position recommended (50% size). {concern.capitalize()}. " + \
                   (f"Supporting factors: {agreements[0]}" if agreements else "Trade with caution.")
        else:
            return f"{symbol} {signal} SIGNAL: Conservative entry suggested. Score acceptable ({score:.1f}/100) " + \
                   f"but monitor {warnings[0] if warnings else 'market conditions closely'}."
    
    elif verdict == "CONFIRM":
        if risk_mode == "AGGRESSIVE":
            strength = agreements[0] if agreements else f"strong conviction ({score:.1f}/100)"
            return f"{symbol} {signal} SIGNAL: High-conviction setup - full size recommended. {strength.capitalize()}. " + \
                   (f"Additional support: {agreements[1]}" if len(agreements) > 1 else "Favorable risk-reward.")
        else:
            return f"{symbol} {signal} SIGNAL: Good setup confirmed. " + \
                   (f"{agreements[0].capitalize()}." if agreements else f"Score: {score:.1f}/100.") + \
                   " Normal position size appropriate."
    
    return f"{symbol} {signal} SIGNAL: Assessment complete. Exercise standard risk management."
