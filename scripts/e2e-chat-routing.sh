#!/usr/bin/env bash
# E2E routingu czatu Mullm — ten sam kontrakt co UI (POST /api/chat/message).
# Wymaga: curl, jq, działający web (domyślnie http://127.0.0.1:3003).
set -euo pipefail

BASE="${MULLM_E2E_BASE_URL:-http://127.0.0.1:3003}"
BASE="${BASE%/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "${SCRIPT_DIR}/wait-for-web.sh"
MULLM_E2E_BASE_URL="${BASE}" "${SCRIPT_DIR}/wait-for-web.sh"

echo "== health =="
curl -fsS "${BASE}/health" | jq .

echo "== agents/status =="
AGENTS_JSON=$(curl -fsS "${BASE}/api/agents/status")
echo "${AGENTS_JSON}" | jq '.agents[] | {id, healthy, executor_agent_id}'

echo "== routing/policy (ingress) =="
curl -fsS "${BASE}/api/routing/policy?reload=true" | jq '{ingress_order, by_route: .agents.by_route, agent_plugins}'

echo "== routing/schemas (Pydantic bundle) =="
curl -fsS "${BASE}/api/routing/schemas" | jq '{bundle_id, nlp2cmd: (.nlp2cmd | keys), openrouter: (.openrouter_classifier | keys)}'

echo "== session =="
SID=$(curl -fsS -X POST "${BASE}/api/chat/session" -H 'Content-Type: application/json' -d '{}' | jq -r .session_id)
echo "session_id=${SID}"

echo "== router/decide (dry-run) =="
curl -fsS "${BASE}/api/router/decide?message=lista%20plikow%20usera&use_rag=false" | jq '{route, confidence, reason_codes}'

echo "== chat: lista plikow usera (musi być mullm_file_list, NIE shell ls ~) =="
FILE_LIST_JSON=$(curl -fsS -X POST "${BASE}/api/chat/message" \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"${SID}\",\"message\":\"lista plikow usera\",\"mode\":\"discuss\",\"use_rag\":false}")
echo "${FILE_LIST_JSON}" | jq '{intent, route: .routing.route, executed, nlp2dsl_skipped: .routing.nlp2dsl_skipped, reply: .reply[0:200]}'
ROUTE=$(echo "${FILE_LIST_JSON}" | jq -r '.routing.route')
if [ "${ROUTE}" != "mullm_file_list" ]; then
  echo "FAIL: oczekiwano mullm_file_list, jest: ${ROUTE}" >&2
  exit 1
fi
if echo "${FILE_LIST_JSON}" | jq -r '.routing.route' | grep -q shell; then
  echo "FAIL: lista plikow usera nie powinna używać mullm_shell" >&2
  exit 1
fi

echo "== router/decide: run ls -la ~ (shell — osobna komenda) =="
curl -fsS "${BASE}/api/router/decide?message=run%20ls%20-la%20~&use_rag=false" \
  | jq '{route, confidence, reason_codes}'

NLP2CMD_OK=$(echo "${AGENTS_JSON}" | jq -r '[.agents[] | select(.id=="nlp2cmd" and .healthy==true)] | length')
# Potwierdź że API odpowiada (health pluginu może być mylące przy restarcie kontenera).
if [ "${NLP2CMD_OK}" = "1" ] && curl -fsS --max-time 5 "http://127.0.0.1:${MULLM_NLP2CMD_HOST_PORT:-8020}/health" >/dev/null 2>&1; then
  echo "== chat: sprawdz miejsce na dysku (nlp2cmd → shell_agent) =="
  SHELL_NL_JSON=$(curl -fsS -X POST "${BASE}/api/chat/message" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\":\"${SID}\",\"message\":\"sprawdz miejsce na dysku\",\"mode\":\"discuss\",\"use_rag\":false}")
  echo "${SHELL_NL_JSON}" | jq '{route: .routing.route, shell_plugin: .routing.shell_plugin, executed, task_id: .task.task_id}'
  SNL_ROUTE=$(echo "${SHELL_NL_JSON}" | jq -r '.routing.route')
  if [ "${SNL_ROUTE}" != "nlp2cmd_shell" ]; then
    echo "FAIL: oczekiwano nlp2cmd_shell, jest: ${SNL_ROUTE}" >&2
    exit 1
  fi
else
  echo "SKIP: nlp2cmd niedostępny (make nlp2cmd-up lub NLP2CMD=1 make up)"
fi

echo "== chat: kontynuuj =="
curl -fsS -X POST "${BASE}/api/chat/message" \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"${SID}\",\"message\":\"kontynuuj\",\"mode\":\"discuss\",\"use_rag\":false}" \
  | jq '{route: .routing.route, reply: .reply[0:240]}'

echo "== logs export (fragment) =="
curl -fsS "${BASE}/api/workspace/logs/export?session_id=${SID}&limit=10" \
  | jq -r '.text' | head -n 40

echo "OK — E2E shell zakończone"
