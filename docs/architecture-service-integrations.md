# Integracje usługowe Mullm — co w Dockerze, co lokalnie

Mullm **nie osadza** logiki nlp2cmd/nlp2dsl/intract/propact w procesie BFF. BFF jest **orkiestratorem**; zewnętrzne możliwości przychodzą przez HTTP (runtime) lub narzędzia dev (CI).

## Rekomendacja (tak — warto rozdzielić)

| Komponent | Tryb integracji | Dlaczego |
|-----------|-----------------|----------|
| **nlp2cmd** | **Usługa Docker** (`profile: nlp2cmd`) | NL→shell, osobny cykl życia, Playwright/CIężkie zależności z dala od BFF |
| **nlp2dsl** | **Stack Docker** (`profile: nlp2dsl` lub `../nlp2dsl`) | Workflow DSL + worker; już tak działa |
| **shell-agent** | **Usługa Docker** (NATS) | Jedyny wykonawca poleceń na hoście |
| **intract** | **Lokalnie / CI** (`intract validate`) | Kontrakty kodu — nie runtime czatu |
| **propact** | **Lokalnie / CI** (`propact run …`) | Smoke HTTP / OpenAPI — nie runtime czatu |
| **cyberdsl** | **Opcjonalnie offline** | Model/analiza ingress (`docs/routing-model.cyberdsl`) |

```text
                    ┌─────────────┐
  User / UI ───────►│  mullm-web  │ orchestrator (ingress, routing, tickets)
                    └──────┬──────┘
           HTTP          │         NATS
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
 ┌─────────┐      ┌─────────────┐    ┌──────────────┐
 │ nlp2cmd │      │ nlp2dsl-    │    │ shell-agent  │
 │ :8000   │      │ backend     │    │ (executor)   │
 └─────────┘      └─────────────┘    └──────────────┘
```

**Nie** pakuj nlp2cmd/nlp2dsl jako biblioteki Python w `requirements.txt` web — utrzymuj **most HTTP** (`agent_plugins/*_plugin.py`) + manifesty w `integrations/`.

## Profile Compose

```bash
# Minimum czatu + pliki + shell
COMPOSE_PROFILES=core,rag docker compose up -d

# + NL→shell (nlp2cmd)
NLP2CMD=1 make up   # → profile nlp2cmd + docker/nlp2cmd-service.Dockerfile

# + workflow DSL
NLP2DSL=1 make up   # → sibling ../nlp2dsl compose
```

Zmienne: `MULLM_NLP2CMD_BACKEND_URL`, `MULLM_NLP2DSL_BACKEND_URL` (wewnątrz sieci `mullm_network`).

## Naprawy w bibliotekach (upstream / wrapper)

| Problem | Gdzie naprawione |
|---------|------------------|
| `python -m nlp2cmd service` → `click` NoneType | `nlp2cmd/cli/main.py` stub; Mullm: `docker/nlp2cmd-service.Dockerfile` |
| Brak `[service]` extra (FastAPI) | `nlp2cmd/pyproject.toml` → `pip install -e ".[service]"` |
| Propact: `propact plik.md` zamiast `propact run` | `scripts/run-propact-pact.sh`, docs |
| Intract `forbid:network` na pliku z `import httpx` | poluzowane kontrakty w `intract.yaml` |
| BFF mylił `localhost:8000` z nlp2cmd | usunięte z `nlp2cmd_plugin.backend_candidates` |

## Kiedy NIE dodawać usługi Docker

- **intract** — skan statyczny; wystarczy `make test-quality` / GitHub Actions.
- **propact** — test kontraktu HTTP; nie potrzebuje stałego kontenera.
- **cyberdsl** — symulacja dokumentacyjna, nie ścieżka produkcyjna czatu.

## Kolejne kroki (opcjonalnie)

1. `depends_on: nlp2cmd: condition: service_healthy` gdy zawsze używasz `NLP2CMD=1`.
2. Rejestr pluginów w orchestratorze (`PluginCatalog`) zsynchronizowany z `agent_plugins/` (jeden model manifestów).
3. `browser_agent` jako trzeci profil Compose, gdy nlp2cmd zwraca `multi_step` / browser DSL.
