#!/bin/bash
set -euo pipefail

echo "========================================="
echo "  End-to-End Pipeline Integration Test"
echo "========================================="
echo ""

BASE_URL="${BASE_URL:-http://localhost}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILURES=0

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
warn_fail() { echo -e "${YELLOW}⚠ $1${NC}"; FAILURES=$((FAILURES + 1)); }
info() { echo -e "  $1"; }

echo "Step 1: Service Health Checks"
echo "-----------------------------"

# App service
if curl -sf "${BASE_URL}:8000/api/health" > /dev/null 2>&1; then
    pass "App service (port 8000)"
else
    fail "App service not responding"
fi

# Distribution service
if curl -sf "${BASE_URL}:8200/health" > /dev/null 2>&1; then
    pass "Distribution service (port 8200)"
else
    fail "Distribution service not responding"
fi

# LLM service (optional - requires GPU)
if curl -sf "${BASE_URL}:11434/api/tags" > /dev/null 2>&1; then
    pass "LLM service (port 11434)"
    LLM_AVAILABLE=true
else
    warn "LLM service not available (GPU services may not be running)"
    LLM_AVAILABLE=false
fi

# TTS service (optional - requires GPU)
if curl -sf "${BASE_URL}:8100/health" > /dev/null 2>&1; then
    pass "TTS service (port 8100)"
    TTS_AVAILABLE=true
else
    warn "TTS service not available (GPU services may not be running)"
    TTS_AVAILABLE=false
fi

# Frontend
if curl -sf "${BASE_URL}:3000/" > /dev/null 2>&1; then
    pass "Frontend (port 3000)"
else
    warn "Frontend not available (dev profile may not be running)"
fi

echo ""
echo "Step 2: Distribution Service Tests"
echo "-----------------------------------"

# Test RSS feed generation
FEED_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}:8200/feeds/olivers_workshop.xml" 2>/dev/null)
HTTP_CODE=$(echo "$FEED_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    pass "RSS feed endpoint responds (HTTP $HTTP_CODE)"
else
    fail "RSS feed endpoint failed (HTTP $HTTP_CODE)"
fi

# Test feed regeneration
REGEN_RESPONSE=$(curl -s -X POST "${BASE_URL}:8200/feeds/olivers_workshop/regenerate" 2>/dev/null)
if echo "$REGEN_RESPONSE" | grep -q "regenerated"; then
    pass "Feed regeneration works"
else
    warn_fail "Feed regeneration returned unexpected response"
    info "$REGEN_RESPONSE"
fi

echo ""
echo "Step 3: Pipeline API Tests"
echo "--------------------------"

# Test pipeline status endpoint
STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}:8000/api/pipeline/status/olivers_workshop/test_episode" 2>/dev/null)
HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "404" ]; then
    pass "Pipeline status returns 404 for missing episode (correct)"
elif [ "$HTTP_CODE" = "200" ]; then
    pass "Pipeline status endpoint works"
else
    warn_fail "Pipeline status returned HTTP $HTTP_CODE"
fi

echo ""
if [ "$LLM_AVAILABLE" = true ] && [ "$TTS_AVAILABLE" = true ]; then
    echo "Step 4: Full Pipeline Test (GPU services available)"
    echo "---------------------------------------------------"

    # Run a full pipeline
    PIPELINE_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"show_id": "olivers_workshop", "topic": "How do magnets work?", "title": "The Magnet Mystery"}' \
        "${BASE_URL}:8000/api/pipeline/run" 2>/dev/null)

    if echo "$PIPELINE_RESPONSE" | grep -q "episode_id"; then
        pass "Full pipeline executed"
        EPISODE_ID=$(echo "$PIPELINE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['episode_id'])" 2>/dev/null || echo "unknown")
        info "Episode ID: $EPISODE_ID"
        info "Response: $PIPELINE_RESPONSE"
    else
        warn_fail "Full pipeline test failed (may need longer timeout)"
        info "Response: $PIPELINE_RESPONSE"
    fi
else
    echo "Step 4: Skipped (GPU services not available)"
    echo "---------------------------------------------"
    warn "Start GPU services with: make up-gpu"
fi

echo ""
echo "========================================="
echo "  E2E Test Summary"
echo "========================================="

if [ "$FAILURES" -gt 0 ]; then
    fail "$FAILURES test(s) failed"
else
    pass "All integration tests passed"
fi
