# Mullm — orchestracja agentów (pluginy)

Mullm **nie wykonuje** poleceń użytkownika w czacie — routuje do pluginów i przypisuje **agentów wykonawczych** (NATS / Access Fabric).

**Integracja usługowa (Docker vs CI):** [architecture-service-integrations.md](architecture-service-integrations.md)

## Pipeline ingress (discuss)

```
rag_probe → rules → agent_shell → nlp2dsl → rag_answer
```

| Krok | Plugin / logika | Agent wykonawczy |
|------|-----------------|------------------|
| rules | `prompt_router` (file list, `run …`) | files_agent / shell_agent |
| agent_shell | **nlp2cmd** `POST /query` | shell_agent (ticket) |
| nlp2dsl | **nlp2dsl** workflow | coordinator |

## nlp2cmd (shell NL)

- Repo: `/home/tom/github/wronai/nlp2cmd`
- Usługa: `nlp2cmd service` → `POST /query` (`execute: false`)
- Mullm tworzy ticket → `shell-agent-a/b` na NATS

Przykłady:

| Prompt | Trasa |
|--------|--------|
| `lista plikow usera` | `mullm_file_list` (rejestr, **nie** nlp2cmd) |
| `run ls -la ~` | `mullm_shell` (bez nlp2cmd) |
| `sprawdź miejsce na dysku` | `nlp2cmd_shell` → ticket |
| `wyślij fakturę …` | `nlp2dsl` |

## API

- `GET /api/agents/status` — health pluginów
- `GET /api/routing/policy` — kolejność ingress z YAML

## Uruchomienie

```bash
cd ~/github/wronai/mullm
cp -n .env.example .env   # jeśli brak .env
export NLP2CMD=1 NLP2DSL=1
make up
# nlp2cmd: docker/nlp2cmd-service.Dockerfile (port ${MULLM_NLP2CMD_HOST_PORT:-8020})
export PATH="$(pwd)/scripts:$PATH"
mullm agents status
mullm chat send "sprawdz miejsce na dysku"
./scripts/e2e-chat-routing.sh
```

E2E z wymaganym nlp2cmd na żywym stacku:

```bash
MULLM_E2E=1 MULLM_E2E_REQUIRE_NLP2CMD=1 make test-e2e-live
```

Env:

- `MULLM_NLP2CMD_BACKEND_URL` / `NLP2CMD_BACKEND_URL` (domyślnie `http://nlp2cmd:8000` w Docker)
- `MULLM_NLP2DSL_BACKEND_URL` — jak wcześniej

## Rozszerzanie

1. Dodać `app/agent_plugins/<name>_plugin.py` implementujący `AgentPlugin`
2. Zarejestrować w `registry.py`
3. Dodać manifest `integrations/<name>/agent_manifest.yaml`
4. Opcjonalnie: krok w `services/web/data/routing_policy.yaml` + mapowanie `agents.by_route`
