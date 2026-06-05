#!/usr/bin/env bash
# Czeka aż Mullm web odpowie na /health (po docker compose up / recreate).
set -euo pipefail

BASE="${MULLM_E2E_BASE_URL:-http://127.0.0.1:3003}"
BASE="${BASE%/}"
MAX_WAIT="${MULLM_E2E_WAIT_SECONDS:-90}"
INTERVAL="${MULLM_E2E_WAIT_INTERVAL:-1}"

deadline=$((SECONDS + MAX_WAIT))
echo "Czekam na ${BASE}/health (max ${MAX_WAIT}s)…"
while (( SECONDS < deadline )); do
  if curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
    echo "OK — web gotowy"
    exit 0
  fi
  sleep "${INTERVAL}"
done

echo "FAIL — web nie odpowiada na ${BASE}/health w ${MAX_WAIT}s" >&2
echo "Sprawdź: docker compose ps web && docker compose logs web --tail 30" >&2
exit 1
