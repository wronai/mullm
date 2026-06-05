#!/usr/bin/env bash
# Propact smoke Mullm — wymaga: propact run (nie: propact plik.md)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

BASE="${MULLM_BASE_URL:-http://127.0.0.1:3003}"
BASE="${BASE%/}"
OPENAPI="${ROOT}/tests/pacts/mullm-openapi.json"
PACT_MD="${ROOT}/tests/pacts/mullm-health.md"

PROPACT_DIR="${PROPACT_ROOT:-/home/tom/github/pactown-com/propact}"
propact_cmd() {
  if command -v propact >/dev/null 2>&1; then
    propact "$@"
    return
  fi
  if [ -f "${PROPACT_DIR}/src/propact/cli.py" ]; then
    PYTHONPATH="${PROPACT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
      python -m propact.cli "$@"
    return
  fi
  echo "Brak propact w PATH ani ${PROPACT_DIR}/src/propact/cli.py" >&2
  echo "  pip install 'propact[semantic]' && pip install 'rich>=14.3.4'" >&2
  echo "(propact 0.0.9 pinuje starsze rich — po instalacji podnieś rich dla koru)" >&2
  exit 1
}

if ! curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
  echo "BFF niedostępny: ${BASE}/health — uruchom: make up" >&2
  exit 1
fi

echo "== propact: health =="
propact_cmd run "${PACT_MD}" \
  --openapi "${OPENAPI}" \
  --base-url "${BASE}" \
  --method GET \
  --error-mode strict

echo "== propact: router decide (file list) =="
propact_cmd run "${PACT_MD}" \
  --endpoint "${BASE}/api/router/decide?message=lista%20plikow%20usera&use_rag=false" \
  --method GET \
  --error-mode strict

SID=$(curl -fsS -X POST "${BASE}/api/chat/session" -H 'Content-Type: application/json' -d '{}' | jq -r .session_id)
echo "session_id=${SID}"

echo "== propact: chat file list =="
# Tymczasowy plik z jednym blokiem POST (propact nie podstawia zmiennych w MD)
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
cat > "${TMP}" <<EOF
# Chat file list

\`\`\`propact:rest
POST /api/chat/message
{"session_id":"${SID}","message":"lista plikow usera","mode":"discuss","use_rag":false}
\`\`\`
EOF

propact_cmd run "${TMP}" \
  --base-url "${BASE}" \
  --endpoint "${BASE}/api/chat/message" \
  --openapi "${OPENAPI}" \
  --method POST \
  --error-mode strict

echo "OK — propact pact (sprawdź *.response.md obok plików wejściowych)"
