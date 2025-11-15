#!/bin/bash
# Daily GPT Actions Monitoring Script
# Runs automated checks on GPT Actions endpoints health and compliance
# Schedule: Daily at 00:00 UTC via cron

set -e

# Configuration
API_BASE="https://guardiansofthetoken.org"
LOG_DIR="./logs/gpt_monitoring"
LOG_FILE="$LOG_DIR/daily_$(date +%Y%m%d).log"
ALERT_LOG="$LOG_DIR/alerts.log"

# Thresholds (from GPT_ACTIONS_ALERTING_CONFIG.md)
HEALTH_CRITICAL=70
HEALTH_WARNING=85
PROBLEM_COUNT_WARNING=3
ACTIVE_CLIENTS_WARNING=50
ACTIVE_CLIENTS_CRITICAL=100

# Create log directory if not exists
mkdir -p "$LOG_DIR"

# Start logging
echo "========================================" | tee -a "$LOG_FILE"
echo "GPT Actions Daily Monitoring Report" | tee -a "$LOG_FILE"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Function to send alert (placeholder for Telegram integration)
send_alert() {
    local severity=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $message" | tee -a "$ALERT_LOG"

    # TODO: Add Telegram bot integration here
    # curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    #   -d chat_id="${TELEGRAM_CHAT_ID}" \
    #   -d text="[$severity] $message"
}

# 1. Check health score
echo "1️⃣  Checking Health Score..." | tee -a "$LOG_FILE"
HEALTH_RESPONSE=$(curl -s "$API_BASE/gpt/monitoring/health-check" || echo "{}")
HEALTH_SCORE=$(echo "$HEALTH_RESPONSE" | jq -r '.data.health_score // "N/A"')

if [ "$HEALTH_SCORE" != "N/A" ]; then
    echo "   Health Score: $HEALTH_SCORE" | tee -a "$LOG_FILE"

    # Check if below critical threshold
    if (( $(echo "$HEALTH_SCORE < $HEALTH_CRITICAL" | bc -l) )); then
        echo "   🚨 CRITICAL: Health score below $HEALTH_CRITICAL!" | tee -a "$LOG_FILE"
        send_alert "CRITICAL" "GPT Actions health score is $HEALTH_SCORE (below critical threshold of $HEALTH_CRITICAL)"
    elif (( $(echo "$HEALTH_SCORE < $HEALTH_WARNING" | bc -l) )); then
        echo "   ⚠️  WARNING: Health score below $HEALTH_WARNING" | tee -a "$LOG_FILE"
        send_alert "WARNING" "GPT Actions health score is $HEALTH_SCORE (below warning threshold of $HEALTH_WARNING)"
    else
        echo "   ✅ Health score is good" | tee -a "$LOG_FILE"
    fi
else
    echo "   ❌ Failed to retrieve health score" | tee -a "$LOG_FILE"
    send_alert "ERROR" "Failed to retrieve GPT Actions health score"
fi

echo "" | tee -a "$LOG_FILE"

# 2. Check problematic endpoints
echo "2️⃣  Checking Problematic Endpoints..." | tee -a "$LOG_FILE"
PROBLEM_RESPONSE=$(curl -s "$API_BASE/gpt/monitoring/problematic-endpoints" || echo "{}")
PROBLEM_COUNT=$(echo "$PROBLEM_RESPONSE" | jq -r '.data.count // "N/A"')

if [ "$PROBLEM_COUNT" != "N/A" ]; then
    echo "   Problematic Endpoints: $PROBLEM_COUNT" | tee -a "$LOG_FILE"

    if [ "$PROBLEM_COUNT" -gt "$PROBLEM_COUNT_WARNING" ]; then
        echo "   ⚠️  WARNING: More than $PROBLEM_COUNT_WARNING problematic endpoints!" | tee -a "$LOG_FILE"

        # List problematic endpoints
        echo "   Problematic endpoints list:" | tee -a "$LOG_FILE"
        echo "$PROBLEM_RESPONSE" | jq -r '.data.endpoints[]? | "     - \(.endpoint): \(.size_kb) KB"' | tee -a "$LOG_FILE"

        send_alert "WARNING" "Found $PROBLEM_COUNT problematic endpoints (threshold: $PROBLEM_COUNT_WARNING)"
    elif [ "$PROBLEM_COUNT" -gt 0 ]; then
        echo "   ℹ️  Found $PROBLEM_COUNT problematic endpoint(s)" | tee -a "$LOG_FILE"
        echo "$PROBLEM_RESPONSE" | jq -r '.data.endpoints[]? | "     - \(.endpoint): \(.size_kb) KB"' | tee -a "$LOG_FILE"
    else
        echo "   ✅ No problematic endpoints" | tee -a "$LOG_FILE"
    fi
else
    echo "   ❌ Failed to retrieve problematic endpoints" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# 3. Check active clients (rate limit monitoring)
echo "3️⃣  Checking Rate Limits & Active Clients..." | tee -a "$LOG_FILE"
RATE_RESPONSE=$(curl -s "$API_BASE/gpt/monitoring/rate-limits" || echo "{}")
ACTIVE_CLIENTS=$(echo "$RATE_RESPONSE" | jq -r '.data.active_clients_last_minute // "N/A"')

if [ "$ACTIVE_CLIENTS" != "N/A" ]; then
    echo "   Active Clients (last minute): $ACTIVE_CLIENTS" | tee -a "$LOG_FILE"

    if [ "$ACTIVE_CLIENTS" -ge "$ACTIVE_CLIENTS_CRITICAL" ]; then
        echo "   🚨 CRITICAL: Active clients exceed critical threshold ($ACTIVE_CLIENTS_CRITICAL)!" | tee -a "$LOG_FILE"
        send_alert "CRITICAL" "Active clients: $ACTIVE_CLIENTS (critical threshold: $ACTIVE_CLIENTS_CRITICAL)"
    elif [ "$ACTIVE_CLIENTS" -ge "$ACTIVE_CLIENTS_WARNING" ]; then
        echo "   ⚠️  WARNING: Active clients approaching limit" | tee -a "$LOG_FILE"
        send_alert "WARNING" "Active clients: $ACTIVE_CLIENTS (warning threshold: $ACTIVE_CLIENTS_WARNING)"
    else
        echo "   ✅ Active client count is normal" | tee -a "$LOG_FILE"
    fi
else
    echo "   ❌ Failed to retrieve active clients count" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# 4. Response size statistics
echo "4️⃣  Checking Response Size Statistics..." | tee -a "$LOG_FILE"
SIZE_RESPONSE=$(curl -s "$API_BASE/gpt/monitoring/response-sizes" || echo "{}")
AVG_SIZE=$(echo "$SIZE_RESPONSE" | jq -r '.data.average_size_kb // "N/A"')

if [ "$AVG_SIZE" != "N/A" ]; then
    echo "   Average Response Size: $AVG_SIZE KB" | tee -a "$LOG_FILE"
    echo "   Target: < 25 KB" | tee -a "$LOG_FILE"
else
    echo "   ❌ Failed to retrieve response size statistics" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# 5. Summary
echo "========================================" | tee -a "$LOG_FILE"
echo "📊 Monitoring Summary" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Health Score: $HEALTH_SCORE (Target: > 90)" | tee -a "$LOG_FILE"
echo "Problematic Endpoints: $PROBLEM_COUNT (Target: 0)" | tee -a "$LOG_FILE"
echo "Active Clients: $ACTIVE_CLIENTS (Warning: > $ACTIVE_CLIENTS_WARNING)" | tee -a "$LOG_FILE"
echo "Avg Response Size: $AVG_SIZE KB (Target: < 25 KB)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 6. Determine overall status
OVERALL_STATUS="✅ HEALTHY"

if [ "$HEALTH_SCORE" != "N/A" ] && (( $(echo "$HEALTH_SCORE < $HEALTH_CRITICAL" | bc -l) )); then
    OVERALL_STATUS="🚨 CRITICAL"
elif [ "$PROBLEM_COUNT" != "N/A" ] && [ "$PROBLEM_COUNT" -gt "$PROBLEM_COUNT_WARNING" ]; then
    OVERALL_STATUS="⚠️  WARNING"
elif [ "$ACTIVE_CLIENTS" != "N/A" ] && [ "$ACTIVE_CLIENTS" -ge "$ACTIVE_CLIENTS_CRITICAL" ]; then
    OVERALL_STATUS="🚨 CRITICAL"
elif [ "$HEALTH_SCORE" != "N/A" ] && (( $(echo "$HEALTH_SCORE < $HEALTH_WARNING" | bc -l) )); then
    OVERALL_STATUS="⚠️  WARNING"
fi

echo "Overall Status: $OVERALL_STATUS" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"

# Exit with appropriate code
if [[ "$OVERALL_STATUS" == *"CRITICAL"* ]]; then
    exit 2
elif [[ "$OVERALL_STATUS" == *"WARNING"* ]]; then
    exit 1
else
    exit 0
fi
