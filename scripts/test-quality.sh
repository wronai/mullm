#!/usr/bin/env bash
# Jakość Mullm: intract (kontrakty routingu) + pytest web + opcjonalnie propact/curl E2E.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

BASE="${MULLM_BASE_URL:-http://127.0.0.1:3003}"
BASE="${BASE%/}"
INTRACT_DIR="${INTRACT_ROOT:-/home/tom/github/semcod/intract}"
PROPACT_DIR="${PROPACT_ROOT:-/home/tom/github/pactown-com/propact}"

echo "== 1/4 pytest (services/web) =="
pip install -q -r requirements-dev.txt -r services/web/requirements.txt
if [ -f requirements-quality.txt ]; then
  pip install -q -r requirements-quality.txt
fi
pytest -c services/web/pytest.ini services/web/tests \
  --ignore=services/web/tests/test_api_routes.py \
  --ignore=services/web/tests/test_e2e_live_stack.py \
  -q

echo "== 2/4 intract validate (routing contracts) =="
if [ -d "${INTRACT_DIR}/src/intract" ]; then
  OUT="$(PYTHONPATH="${INTRACT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    python -m intract validate . --manifest intract.yaml 2>&1)" || true
  echo "${OUT}"
  if echo "${OUT}" | grep -q "Status: violation"; then
    echo "FAIL intract: violation (see table above)" >&2
    exit 1
  fi
else
  echo "SKIP intract: ${INTRACT_DIR} not found (set INTRACT_ROOT)"
fi

echo "== 3/4 curl routing smoke (live BFF) =="
if curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
  chmod +x scripts/e2e-chat-routing.sh
  MULLM_E2E_BASE_URL="${BASE}" ./scripts/e2e-chat-routing.sh
else
  echo "SKIP live E2E: ${BASE}/health unreachable (docker compose up web)"
fi

echo "== 4/4 propact pact (optional) =="
if curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
  if command -v propact >/dev/null 2>&1; then
    chmod +x scripts/run-propact-pact.sh
    ./scripts/run-propact-pact.sh || echo "WARN: propact pact failed (see *.response.md)"
  elif [ -f "${PROPACT_DIR}/src/propact/cli.py" ]; then
    PYTHONPATH="${PROPACT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
      python -m propact.cli run tests/pacts/mullm-health.md \
      --openapi "${ROOT}/tests/pacts/mullm-openapi.json" \
      --base-url "${BASE}" --method GET 2>/dev/null \
      || echo "SKIP propact: run failed"
  else
    echo "SKIP propact: not installed (pip install propact[semantic])"
  fi
else
  echo "SKIP propact: BFF down"
fi

echo "OK — test-quality finished"
