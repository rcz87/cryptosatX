"""
Theme Analyzer Utility

Smart theme detection using LunarCrush metrics (Builder tier)
Alternative to Enterprise-only AI Whatsup endpoint

Detects themes like:
- Viral momentum
- Strong community
- Institutional interest
- Scam risk
- Sentiment trends
"""

from typing import Dict, List
from datetime import datetime


class ThemeAnalyzer:
    """
    Analyzes social metrics to detect market themes
    
    Uses existing Builder tier metrics:
    - Social sentiment
    - Social volume changes
    - Galaxy Score
    - Spam detection
    - Social dominance
    """
    
    # Theme detection thresholds
    THRESHOLDS = {
        "sentiment": {
            "very_positive": 80,
            "positive": 70,
            "neutral": 50,
            "negative": 40,
            "very_negative": 30,
        },
        "social_spike": {
            "extreme": 300,  # 300%+ = viral explosion
            "high": 150,     # 150%+ = strong momentum
            "moderate": 50,  # 50%+ = growing interest
        },
        "galaxy_score": {
            "excellent": 80,
            "strong": 70,
            "good": 60,
            "average": 50,
        },
        "spam_risk": {
            "high": 50,      # 50+ spam count
            "moderate": 20,
        },
        "dominance": {
            "leader": 2.0,   # 2%+ of total crypto buzz
            "significant": 1.0,
            "notable": 0.5,
        },
    }
    
    @staticmethod
    def analyze(metrics: Dict) -> Dict:
        """
        Main theme analysis function
        
        Args:
            metrics: Dict with social metrics from LunarCrush
                - sentiment: float (0-100 or 1-5 scale)
                - social_volume_change: float (% change)
                - galaxy_score: float (0-100)
                - spam_detected: int (spam count)
                - social_dominance: float (% of total)
                - social_volume: int (optional)
                - social_contributors: int (optional)
        
        Returns:
            Dict with detected themes, confidence, and summary
        """
        
        # Normalize sentiment to 0-100 scale
        sentiment = ThemeAnalyzer._normalize_sentiment(metrics.get("sentiment", 50))
        social_change = metrics.get("social_volume_change", 0)
        galaxy_score = metrics.get("galaxy_score", 50)
        spam = metrics.get("spam_detected", 0)
        dominance = metrics.get("social_dominance", 0)
        
        themes = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "confidence": 0,
            "sentiment_label": "",
            "summary": "",
            "risk_level": "low",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # POSITIVE THEMES DETECTION
        themes["positive"] = ThemeAnalyzer._detect_positive_themes(
            sentiment, social_change, galaxy_score, dominance
        )
        
        # NEGATIVE THEMES DETECTION
        themes["negative"] = ThemeAnalyzer._detect_negative_themes(
            sentiment, social_change, spam
        )
        
        # NEUTRAL THEMES
        if not themes["positive"] and not themes["negative"]:
            themes["neutral"].append("stable_sentiment")
        
        # Calculate confidence score
        themes["confidence"] = ThemeAnalyzer._calculate_confidence(
            themes["positive"], themes["negative"]
        )
        
        # Sentiment label
        themes["sentiment_label"] = ThemeAnalyzer._get_sentiment_label(sentiment)
        
        # Risk assessment
        themes["risk_level"] = ThemeAnalyzer._assess_risk(spam, social_change, sentiment)
        
        # Generate human-readable summary
        themes["summary"] = ThemeAnalyzer._generate_summary(
            themes["positive"], themes["negative"], themes["sentiment_label"]
        )
        
        return themes
    
    @staticmethod
    def _normalize_sentiment(value: float) -> float:
        """Normalize sentiment to 0-100 scale"""
        if value <= 5.0:  # Assume 1-5 scale
            return ((value - 1) / 4) * 100
        return value  # Already 0-100
    
    @staticmethod
    def _detect_positive_themes(
        sentiment: float,
        social_change: float,
        galaxy_score: float,
        dominance: float
    ) -> List[str]:
        """Detect positive market themes"""
        themes = []
        t = ThemeAnalyzer.THRESHOLDS
        
        # Sentiment-based
        if sentiment >= t["sentiment"]["very_positive"]:
            themes.append("very_positive_sentiment")
        elif sentiment >= t["sentiment"]["positive"]:
            themes.append("positive_sentiment")
        
        # Social momentum
        if social_change >= t["social_spike"]["extreme"]:
            themes.append("viral_explosion")
        elif social_change >= t["social_spike"]["high"]:
            themes.append("strong_momentum")
        elif social_change >= t["social_spike"]["moderate"]:
            themes.append("growing_interest")
        
        # Community strength
        if galaxy_score >= t["galaxy_score"]["excellent"]:
            themes.append("excellent_community")
        elif galaxy_score >= t["galaxy_score"]["strong"]:
            themes.append("strong_community")
        elif galaxy_score >= t["galaxy_score"]["good"]:
            themes.append("healthy_community")
        
        # Market dominance
        if dominance >= t["dominance"]["leader"]:
            themes.append("market_leader")
        elif dominance >= t["dominance"]["significant"]:
            themes.append("significant_presence")
        elif dominance >= t["dominance"]["notable"]:
            themes.append("notable_buzz")
        
        return themes
    
    @staticmethod
    def _detect_negative_themes(
        sentiment: float,
        social_change: float,
        spam: int
    ) -> List[str]:
        """Detect negative market themes"""
        themes = []
        t = ThemeAnalyzer.THRESHOLDS
        
        # Negative sentiment
        if sentiment <= t["sentiment"]["very_negative"]:
            themes.append("very_negative_sentiment")
        elif sentiment <= t["sentiment"]["negative"]:
            themes.append("negative_sentiment")
        
        # Losing interest
        if social_change <= -50:
            themes.append("declining_interest")
        elif social_change <= -20:
            themes.append("weakening_momentum")
        
        # Spam risk
        if spam >= t["spam_risk"]["high"]:
            themes.append("high_spam_risk")
        elif spam >= t["spam_risk"]["moderate"]:
            themes.append("moderate_spam_risk")
        
        return themes
    
    @staticmethod
    def _calculate_confidence(positive: List[str], negative: List[str]) -> int:
        """
        Calculate theme confidence score (0-100)
        
        More signals = higher confidence
        More positive vs negative = higher confidence
        """
        total_signals = len(positive) + len(negative)
        
        if total_signals == 0:
            return 50  # Neutral
        
        # Base confidence on signal count
        base_confidence = min(40 + (total_signals * 10), 70)
        
        # Adjust based on positive/negative ratio
        if len(positive) > len(negative):
            adjustment = (len(positive) - len(negative)) * 10
            return min(base_confidence + adjustment, 95)
        elif len(negative) > len(positive):
            adjustment = (len(negative) - len(positive)) * 10
            return max(base_confidence - adjustment, 20)
        
        return base_confidence
    
    @staticmethod
    def _get_sentiment_label(sentiment: float) -> str:
        """Get human-readable sentiment label"""
        t = ThemeAnalyzer.THRESHOLDS["sentiment"]
        
        if sentiment >= t["very_positive"]:
            return "Very Positive"
        elif sentiment >= t["positive"]:
            return "Positive"
        elif sentiment >= t["neutral"]:
            return "Neutral"
        elif sentiment >= t["negative"]:
            return "Negative"
        else:
            return "Very Negative"
    
    @staticmethod
    def _assess_risk(spam: int, social_change: float, sentiment: float) -> str:
        """Assess overall risk level"""
        t = ThemeAnalyzer.THRESHOLDS
        
        # High risk conditions
        if spam >= t["spam_risk"]["high"]:
            return "high"
        if sentiment <= t["sentiment"]["very_negative"]:
            return "high"
        
        # Moderate risk
        if spam >= t["spam_risk"]["moderate"]:
            return "moderate"
        if social_change >= t["social_spike"]["extreme"] and sentiment < t["sentiment"]["positive"]:
            return "moderate"  # Viral but not positive = pump risk
        
        return "low"
    
    @staticmethod
    def _generate_summary(positive: List[str], negative: List[str], sentiment_label: str) -> str:
        """Generate human-readable summary"""
        
        if not positive and not negative:
            return f"{sentiment_label} market sentiment with stable activity"
        
        if len(positive) > len(negative):
            main_themes = ", ".join(positive[:3])  # Top 3
            return f"Bullish: {main_themes.replace('_', ' ').title()}"
        elif len(negative) > len(positive):
            main_themes = ", ".join(negative[:3])
            return f"Bearish: {main_themes.replace('_', ' ').title()}"
        else:
            return f"{sentiment_label} with mixed signals"


# Convenience function
def analyze_themes(metrics: Dict) -> Dict:
    """
    Analyze social metrics for market themes
    
    Quick wrapper for ThemeAnalyzer.analyze()
    """
    return ThemeAnalyzer.analyze(metrics)
