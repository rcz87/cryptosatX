"""
CRITICAL FIX: Signal Engine Weight Distribution
Bug: Weights sum to 110% instead of 100%
Fix: Rebalance to exactly 100%
"""

# CURRENT WEIGHTS (INVALID - SUMS TO 110%)
WEIGHTS_OLD = {
    "funding_rate": 18,       # +3 from before
    "social_sentiment": 8,    # -2 from before
    "price_momentum": 20,     # +5 from before
    "liquidations": 25,       # +5 from before
    "long_short_ratio": 12,   # -3 from before
    "oi_trend": 8,            # -2 from before
    "smart_money": 12,        # +2 from before
    "fear_greed": 7,          # +2 from before
}
# Total: 110% ❌

print("="*70)
print("SIGNAL ENGINE WEIGHT FIX")
print("="*70)
print(f"\n❌ OLD WEIGHTS (Sum = {sum(WEIGHTS_OLD.values())}%):")
for k, v in sorted(WEIGHTS_OLD.items(), key=lambda x: x[1], reverse=True):
    print(f"   {k:20s}: {v:3d}%")

# OPTION 1: PROPORTIONAL REDUCTION (Maintain relative priorities)
# Scale all weights by 100/110 = 0.909
WEIGHTS_PROPORTIONAL = {
    "funding_rate": 16,       # 18 * 0.909 ≈ 16
    "social_sentiment": 7,    # 8 * 0.909 ≈ 7
    "price_momentum": 18,     # 20 * 0.909 ≈ 18
    "liquidations": 23,       # 25 * 0.909 ≈ 23
    "long_short_ratio": 11,   # 12 * 0.909 ≈ 11
    "oi_trend": 7,            # 8 * 0.909 ≈ 7
    "smart_money": 11,        # 12 * 0.909 ≈ 11
    "fear_greed": 7,          # 7 * 0.909 ≈ 6.4 → round to 7
}
# Adjust to sum exactly 100
WEIGHTS_PROPORTIONAL["funding_rate"] = 16  # 100 - 93 = 7, distribute

print(f"\n✅ OPTION 1: PROPORTIONAL REDUCTION (Sum = {sum(WEIGHTS_PROPORTIONAL.values())}%):")
for k, v in sorted(WEIGHTS_PROPORTIONAL.items(), key=lambda x: x[1], reverse=True):
    print(f"   {k:20s}: {v:3d}% {'█' * (v // 2)}")

# OPTION 2: STRATEGIC REDUCTION (Cut less important factors)
# Reduce social_sentiment and oi_trend more aggressively
WEIGHTS_STRATEGIC = {
    "funding_rate": 18,       # Keep high priority
    "social_sentiment": 6,    # -2 (less reliable)
    "price_momentum": 20,     # Keep high priority
    "liquidations": 24,       # -1 (still very important)
    "long_short_ratio": 11,   # -1 (slight reduction)
    "oi_trend": 6,            # -2 (less reliable)
    "smart_money": 11,        # -1 (slight reduction)
    "fear_greed": 4,          # -3 (reduce sentiment weight)
}

print(f"\n✅ OPTION 2: STRATEGIC REDUCTION (Sum = {sum(WEIGHTS_STRATEGIC.values())}%):")
for k, v in sorted(WEIGHTS_STRATEGIC.items(), key=lambda x: x[1], reverse=True):
    print(f"   {k:20s}: {v:3d}% {'█' * (v // 2)}")

# OPTION 3: BALANCED APPROACH (Round down top weights)
WEIGHTS_BALANCED = {
    "funding_rate": 17,       # -1
    "social_sentiment": 7,    # -1
    "price_momentum": 19,     # -1
    "liquidations": 23,       # -2
    "long_short_ratio": 11,   # -1
    "oi_trend": 7,            # -1
    "smart_money": 11,        # -1
    "fear_greed": 5,          # -2
}

print(f"\n✅ OPTION 3: BALANCED APPROACH (Sum = {sum(WEIGHTS_BALANCED.values())}%):")
for k, v in sorted(WEIGHTS_BALANCED.items(), key=lambda x: x[1], reverse=True):
    print(f"   {k:20s}: {v:3d}% {'█' * (v // 2)}")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)
print("""
I recommend OPTION 2: STRATEGIC REDUCTION

Reasoning:
1. Maintains high priority on reliable indicators (price momentum, liquidations)
2. Reduces weight on less reliable factors (social sentiment, fear/greed)
3. Keeps funding rate high (smart money positioning)
4. Preserves the "more aggressive" philosophy from your original adjustments

Replace in signal_engine.py line 58-65:

    WEIGHTS = {
        "funding_rate": 18,
        "social_sentiment": 6,     # REDUCED from 8
        "price_momentum": 20,
        "liquidations": 24,        # REDUCED from 25
        "long_short_ratio": 11,    # REDUCED from 12
        "oi_trend": 6,             # REDUCED from 8
        "smart_money": 11,         # REDUCED from 12
        "fear_greed": 4,           # REDUCED from 7
    }
    # Total: 100% ✅
""")

print("\n" + "="*70)
print("IMPACT ANALYSIS")
print("="*70)

# Test impact on scenarios
test_scenarios = [
    {
        "name": "Strong Bullish",
        "scores": {
            "funding_rate": 85,
            "social_sentiment": 75,
            "price_momentum": 80,
            "liquidations": 70,
            "long_short_ratio": 60,
            "oi_trend": 70,
            "smart_money": 70,
            "fear_greed": 25
        }
    }
]

for scenario in test_scenarios:
    print(f"\n{scenario['name']} Scenario:")
    
    old_score = sum(scenario["scores"][k] * WEIGHTS_OLD[k] / 110 for k in scenario["scores"])
    new_score = sum(scenario["scores"][k] * WEIGHTS_STRATEGIC[k] / 100 for k in scenario["scores"])
    
    print(f"   Old (110% basis): {old_score:.1f}/100")
    print(f"   New (100% basis): {new_score:.1f}/100")
    print(f"   Difference: {new_score - old_score:+.1f} points")
    
    if old_score >= 52:
        old_signal = "LONG"
    elif old_score <= 48:
        old_signal = "SHORT"
    else:
        old_signal = "NEUTRAL"
    
    if new_score >= 52:
        new_signal = "LONG"
    elif new_score <= 48:
        new_signal = "SHORT"
    else:
        new_signal = "NEUTRAL"
    
    if old_signal == new_signal:
        print(f"   Signal: {new_signal} (UNCHANGED)")
    else:
        print(f"   Signal: {old_signal} → {new_signal} (CHANGED!)")
