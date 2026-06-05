# Jakość: Intract + Propact

## Intract (kontrakty routingu)

Plik: `intract.yaml` + adnotacje `@intract.v1` w:

- `services/web/app/chat.py` — `is_file_list_intent`, `is_shell_nl_intent`
- `services/web/app/prompt_router.py` — trasy file_list / shell prefix
- `services/web/app/conductor.py` — krok `agent_shell` (nlp2cmd)

```bash
cd ~/github/wronai/mullm
PYTHONPATH=~/github/semcod/intract/src python -m intract validate . --manifest intract.yaml
```

## Propact (smoke HTTP BFF)

Pliki: `tests/pacts/mullm-chat.md`, `tests/pacts/mullm-openapi.json`

```bash
export MULLM_BASE_URL=http://127.0.0.1:3003
# Propact to grupa komend Click — pierwszy argument to subkomenda `run`, nie ścieżka pliku.
pip install 'propact[semantic]'
pip install 'rich>=14.3.4'   # po propact: unikaj konfliktu z koru (propact pinuje rich 13.x)

propact run tests/pacts/mullm-health.md \
  --openapi tests/pacts/mullm-openapi.json \
  --base-url "$MULLM_BASE_URL" \
  --method GET

# Pełniejszy smoke (health + router + chat):
./scripts/run-propact-pact.sh
```

Błąd `No such command 'tests/pacts/mullm-chat.md'` = brakuje słowa **`run`** przed plikiem.

## Wszystko naraz

```bash
make test-quality
# lub: ./scripts/test-quality.sh
```

Kolejność: pytest → intract → `e2e-chat-routing.sh` (jeśli web żyje) → propact (jeśli dostępny).

## nlp2cmd w Docker

Profil `nlp2cmd` używa `docker/nlp2cmd-service.Dockerfile` (obejście błędu CLI `click` w upstream).

```bash
NLP2CMD=1 docker compose --profile core --profile nlp2cmd up -d
curl -s http://127.0.0.1:8020/query -d '{"query":"sprawdz miejsce na dysku","dsl":"shell"}' | jq .command
# → "df -h"
```

## CyberDSL (analiza)

Model dokumentacyjny: `docs/routing-model.cyberdsl` (nie wpływa na runtime).
