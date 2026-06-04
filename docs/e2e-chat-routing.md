# E2E — routing czatu Mullm

## Proponowane endpointy (bez nowego „magic” API)

| Metoda | Ścieżka | Rola w E2E |
|--------|---------|------------|
| `GET` | `/health` | Smoke — web żyje |
| `POST` | `/api/chat/session` | Nowa sesja → `session_id` |
| **`POST`** | **`/api/chat/message`** | **Pełna tura** (to samo co UI workspace) |
| `GET` | `/api/router/decide?message=…` | Suchy przebieg routera (bez wykonania) |
| `GET` | `/api/routing/policy` | Weryfikacja `ingress_order` |
| `GET` | `/api/workspace/logs/export?session_id=…` | Audyt: routing trace, zdarzenia |

Nie trzeba osobnego `/api/chat/turn` — `POST /api/chat/message` już woła `handle_turn` (ingress: rag_probe → rules → **agent_shell** → nlp2dsl → rag_answer).

| `GET` | `/api/agents/status` | Health pluginów (nlp2cmd, nlp2dsl) |

## Warstwy testów

### 1. Szybkie E2E (CI, bez Docker)

```bash
cd ~/github/wronai/mullm
pip install -r requirements-dev.txt -r services/web/requirements.txt
make test-web
# tylko E2E API (in-process):
pytest -c services/web/pytest.ini services/web/tests/test_e2e_chat_api.py -v
```

`TestClient` + mock `fetch_file_inventory` + wyłączony nlp2dsl (`health=false`).

### 2. E2E na żywym stacku

```bash
docker compose --profile core --profile rag up -d
# opcjonalnie: NLP2DSL=1 make nlp2dsl-up  oraz  NLP2CMD=1 make nlp2cmd-up

make test-e2e-live
# lub: MULLM_E2E=1 pytest -c services/web/pytest.ini services/web/tests/test_e2e_live_stack.py -v
```

Zmienne: `MULLM_E2E_BASE_URL` (domyślnie `http://127.0.0.1:3003`), `MULLM_E2E_TIMEOUT`.

### 3. Shell / ręcznie (jak „chat w terminalu”)

```bash
chmod +x scripts/e2e-chat-routing.sh
./scripts/e2e-chat-routing.sh
```

Pojedyncza wiadomość:

```bash
SID=$(curl -fsS -X POST http://127.0.0.1:3003/api/chat/session \
  -H 'Content-Type: application/json' -d '{}' | jq -r .session_id)

curl -fsS -X POST http://127.0.0.1:3003/api/chat/message \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"message\":\"lista plikow usera\",\"use_rag\":false}" \
  | jq '.routing, .reply'
```

To **nie** jest interaktywny REPL — każda wiadomość to osobny POST (jak programmatic chat). UI w przeglądarce używa tych samych endpointów.

## Scenariusze obowiązkowe

| Wiadomość | Oczekiwana trasa | `nlp2dsl` | Uwagi |
|-----------|------------------|-----------|--------|
| `lista plikow usera` | `mullm_file_list` | skipped | **Rejestr** plików usera (Access Fabric + RAG), **nie** `ls ~` w shell |
| `run ls -la ~` | `mullm_shell` | skipped | Jawny prefix — ticket shell_agent |
| `sprawdź miejsce na dysku` | `nlp2cmd_shell` | skipped | **nlp2cmd** `POST /query` → ticket → shell_agent (wymaga nlp2cmd up) |
| `kontynuuj` (bez `nlp2dsl_conversation_id`) | `workroom_hint` | — | Brak odpowiedzi „unknown” |
| `wyślij fakturę …` (z nlp2dsl up) | `nlp2dsl` | invoked | `routing.nlp2dsl` w odpowiedzi |

### Częste nieporozumienie

„lista plikow **usera**” ≠ „pokaż pliki w katalogu domowym `~`”.  
Pierwsze = zasoby zarejestrowane dla użytkownika (`mullm://localfs/…`).  
Drugie = `run ls ~` / `run ls -la ~` → ticket shell agenta.

## Czy da się testować przez chat w shell?

**Tak** — przez HTTP (`curl` / `httpx`), nie przez stdin do kontenera:

- Ten sam kontrakt co workspace.
- Można zautomatyzować w CI (`test_e2e_live_stack`, skrypt `e2e-chat-routing.sh`).
- Do debugu suchego routingu: tylko `GET /api/router/decide`.

## CLI (`scripts/mullm`)

```bash
# Jednorazowo — dodaj do PATH (z katalogu repo mullm):
export PATH="$(pwd)/scripts:$PATH"
# lub:
alias mullm='$HOME/github/wronai/mullm/scripts/mullm'

mullm health
mullm chat send "lista plikow usera"
mullm router decide "lista plikow usera"
export MULLM_SESSION_ID=$(mullm chat session)
mullm chat send "kontynuuj"
```

Zmienne: `MULLM_BASE_URL` (domyślnie `http://127.0.0.1:3003`), `MULLM_SESSION_ID`.
