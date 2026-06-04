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
pip install propact[semantic]   # opcjonalnie
propact tests/pacts/mullm-chat.md \
  --openapi tests/pacts/mullm-openapi.json \
  --base-url "$MULLM_BASE_URL"
```

## Wszystko naraz

```bash
make test-quality
# lub: ./scripts/test-quality.sh
```

Kolejność: pytest → intract → `e2e-chat-routing.sh` (jeśli web żyje) → propact (jeśli dostępny).
