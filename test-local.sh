#!/bin/bash
# ============================================================
# LOCAL TESTING — No AWS required
# Usage: bash test-local.sh
# Runs: unit tests + integration tests + API smoke tests
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()    { echo -e "${GREEN}[$(date +%H:%M:%S)] $1${NC}"; }
warn()   { echo -e "${YELLOW}[$(date +%H:%M:%S)] $1${NC}"; }
error()  { echo -e "${RED}[$(date +%H:%M:%S)] FAILED: $1${NC}"; FAILED=1; }

FAILED=0
cd agentic-platform

# ── Step 1: Unit tests ───────────────────────────────────────
log "Step 1/4: Running unit tests..."
pip install pytest pytest-cov pytest-asyncio httpx -q

ENVIRONMENT=test \
ENABLE_RAG=false \
ENABLE_MEMORY=false \
GROQ_API_KEY=test-key \
DB_TYPE=snowflake \
SNOWFLAKE_USER=test \
SNOWFLAKE_PASSWORD=test \
SNOWFLAKE_ACCOUNT=test \
SNOWFLAKE_WAREHOUSE=test \
SNOWFLAKE_DATABASE=test \
SNOWFLAKE_SCHEMA=test \
SNOWFLAKE_ROLE=test \
REDIS_URL=redis://localhost:6379/0 \
JWT_SECRET_KEY=test-secret-min-32-chars-long-here \
API_KEY=test-api-key \
pytest tests/ -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-fail-under=60 \
  --tb=short \
  2>&1 | tee /tmp/test-results.txt

if grep -q "FAILED\|ERROR" /tmp/test-results.txt; then
  error "Unit tests failed"
else
  log "Unit tests passed ✅"
fi

# ── Step 2: Start local stack ────────────────────────────────
log "Step 2/4: Starting local Docker stack..."
cd ..

# Load .env for local testing
if [ -f agentic-platform/.env ]; then
  export $(cat agentic-platform/.env | grep -v "^#" | xargs)
else
  warn ".env not found — using environment variables"
fi

docker-compose up -d --build

log "Waiting for app to be ready..."
for i in {1..20}; do
  if curl -s http://localhost:8000/health | grep -q "ok"; then
    log "App is ready ✅"
    break
  fi
  sleep 5
  echo "  Waiting... ($i/20)"
done

# ── Step 3: API smoke tests ──────────────────────────────────
log "Step 3/4: Running API smoke tests..."

# Health check
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "ok"; then
  log "Health check ✅"
else
  error "Health check failed: $HEALTH"
fi

# Auth check (no key = 401)
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}')
if [ "$AUTH_STATUS" = "401" ]; then
  log "Auth check ✅ (correctly blocked unauthenticated request)"
else
  warn "Auth check: expected 401, got $AUTH_STATUS"
fi

# Execute endpoint
API_KEY_LOCAL="${API_KEY:-test-api-key}"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY_LOCAL" \
  -d '{"question": "how many orders were placed in 1995?", "environment": "dev"}')

if echo "$RESPONSE" | grep -q "execution_id"; then
  log "Execute endpoint ✅"
  echo "  Response: $(echo $RESPONSE | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("answer","no answer"))' 2>/dev/null || echo $RESPONSE)"
else
  error "Execute endpoint failed: $RESPONSE"
fi

# Cache stats
CACHE=$(curl -s http://localhost:8000/api/v1/cache/stats \
  -H "X-API-Key: $API_KEY_LOCAL")
log "Cache stats: $CACHE"

# ── Step 4: Lint check ───────────────────────────────────────
log "Step 4/4: Running lint check..."
cd agentic-platform
pip install flake8 -q
flake8 app/ \
  --ignore=E302,E303,W292,E501,E241,F401,F841,W503 \
  --max-line-length=120 \
  --exclude=__pycache__ && log "Lint passed ✅" || error "Lint failed"
cd ..

# ── Teardown local stack ─────────────────────────────────────
log "Stopping local Docker stack..."
docker-compose down

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "============================================================"
if [ $FAILED -eq 0 ]; then
  log "  ALL TESTS PASSED ✅"
  echo "  Ready to push to GitHub and deploy to AWS"
else
  echo -e "${RED}  SOME TESTS FAILED ❌${NC}"
  echo "  Check /tmp/test-results.txt for details"
fi
echo "============================================================"

exit $FAILED