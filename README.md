# Mullm - Multi-Agent Learning and Labor Management

A distributed system for orchestrating multiple AI agents with event-driven architecture, CQRS patterns, and real-time projections.

## Architecture Overview

Mullm is built using Domain-Driven Design (DDD) principles with:
- **Event Sourcing** for state management
- **CQRS** for command/query separation
- **Saga Pattern** for distributed transactions
- **Event-Driven Architecture** with NATS messaging
- **Read Model Projections** for real-time dashboards

## Services

### Core Services
- **Orchestrator**: Command handling, domain logic, and event publishing
- **Projector**: Read model projections and query handling
- **Web**: FastAPI/Jinja dashboard for monitoring and control

### Agents
- **Shell Agent**: Command execution and system operations
- **Browser Host Agent**: Web automation and browser control

## Quick Start

```bash
# Start the core control-plane profile
docker compose --profile core up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- NATS Server

### Local Development

```bash
# Setup environment
cp .env.example .env

# Start infrastructure
docker compose --profile core up postgres nats -d

# Install dependencies
pip install -r services/orchestrator/requirements.txt
pip install -r services/projector/requirements.txt
pip install -r services/web/requirements.txt

# Run services locally
# Ports from .env: MULLM_ORCHESTRATOR_HOST_PORT, MULLM_PROJECTOR_HOST_PORT, MULLM_WEB_HOST_PORT
uvicorn app.main:app --app-dir services/orchestrator --host 0.0.0.0 --port ${MULLM_ORCHESTRATOR_HOST_PORT:-8001}
uvicorn app.main:app --app-dir services/projector --host 0.0.0.0 --port ${MULLM_PROJECTOR_HOST_PORT:-8002}
ORCHESTRATOR_URL=${ORCHESTRATOR_URL} PROJECTOR_URL=${PROJECTOR_URL} \
  uvicorn app.main:app --app-dir services/web --host 0.0.0.0 --port ${MULLM_WEB_PORT:-3000}
```

## API Documentation

Host ports are configured in `.env` (see `.env.example`). Defaults:

| Service | URL |
|---------|-----|
| Web UI | `${WEB_URL}` → http://localhost:3003 |
| Orchestrator | `${ORCHESTRATOR_URL}` → http://localhost:8001 |
| Projector | `${PROJECTOR_URL}` → http://localhost:8002 |
| Postgres | localhost:`${MULLM_POSTGRES_HOST_PORT}` (5433) |
| NATS monitor | http://localhost:`${MULLM_NATS_MONITOR_HOST_PORT}` |

### Orchestrator API
- `POST /api/commands` - Submit commands
- `GET /api/queries` - Execute queries
- `GET /health` - Health check

### Projector API
- `GET /projections/tasks` - Task board view
- `GET /projections/agents` - Agent fleet status
- `GET /projections/workflows` - Workflow versions

## Domain Model

### Aggregates
- **Task**: Represents work units with state transitions
- **Agent**: AI agents with capabilities and status
- **Workflow**: Multi-step processes with orchestration logic

### Events
- `TaskCreated`, `TaskAssigned`, `TaskCompleted`
- `AgentRegistered`, `AgentStatusChanged`
- `WorkflowStarted`, `WorkflowStepCompleted`

## Monitoring

Ports from `.env`: `MULLM_NATS_MONITOR_HOST_PORT`, `MULLM_POSTGRES_HOST_PORT`, `MULLM_REDIS_HOST_PORT`.

## RAG Fabric (Sprint 6 MVP)

Wymaga w `.env` (patrz `.env.example`):

- `OPENROUTER_API_KEY` — embeddings + opcjonalne odpowiedzi `/ask`
- `LLM_MODEL` — model chat (np. `openrouter/deepseek/deepseek-v4-pro`)
- `EMBEDDING_MODEL` — opcjonalnie (domyślnie `openai/text-embedding-3-small`)

Po `RegisterResource` orchestrator automatycznie indeksuje treść (`RAG_AUTO_INGEST=true`).

- `POST /api/rag/search` — wyszukiwanie (embedding + FTS fallback)
- `POST /api/rag/ask` — odpowiedź LLM na podstawie chunków
- `POST /api/rag/ingest/{resource_id}` — ręczny re-ingest
- `GET /projections/rag/documents` — stan indeksu

```bash
docker compose --profile rag up -d
```

## Access Fabric (Sprint 4–5 MVP)

- URI: `mullm://localfs/...`, `mullm://http/...`
- Rejestr zasobów: `POST /api/access/resources/register`
- Transport: `POST /api/access/resources/transfer`
- Probe/fetch: `POST /api/access/probe`, `/fetch`

```bash
docker compose --profile access up -d
```

## Evolution control plane (Sprint 7–9 MVP)

System opisuje sam siebie i kontroluje zmiany:

- **`catalog/`** — domeny, event schemas, capabilities, services, policies
- **Policy engine** — reguły przed `ProposePlugin`, aktywacją workflow (manifest, approval, metryki)
- **Evaluation engine** — `evolution_metrics` po `CompleteTask` / `FailTask`
- **Experiment manager** — shadow workflow (`ShadowWorkflowVersion`)
- **API:** `GET /api/catalog/graph`, `GET /api/evolution/metrics`

Szczegóły: [docs/roadmap-90d.md](docs/roadmap-90d.md)

```bash
docker compose --profile core up -d      # orchestrator + projector + agents
docker compose --profile evolution up -d # + eventstoredb (dual write)
docker compose --profile full up -d        # cały stack (+ placeholdery access/rag)
```

## Event store

| `EVENT_STORE_BACKEND` | Opis |
|-----------------------|------|
| `postgres` (default) | Tabela `events` w Postgres |
| `eventstoredb` | Tylko EventStoreDB (`EVENTSTORE_URL`) |
| `dual` | Zapis do Postgres + mirror do EventStoreDB |

```bash
pip install -r services/orchestrator/requirements-esdb.txt
```

## Tests

```bash
./scripts/test.sh
# lub
PYTHONPATH=services/orchestrator pytest tests/ -q
```

Testy integracyjne z Postgres (wymaga `docker compose up postgres -d`):

```bash
MULLM_INTEGRATION=1 pytest tests/test_integration_postgres.py -v
```

## API (orchestrator)

| Endpoint | Opis |
|----------|------|
| `POST /api/commands` | Ogólny envelope CQRS |
| `POST /api/commands/tasks` | `CreateTask` (`auto_assign`, `shell_command`) |
| `POST /api/commands/approvals/*` | Approval gate |
| `POST /api/commands/plugins/*` | Plugin lifecycle |
| `POST /api/commands/workflows/versions/*` | Wersjonowanie workflow |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## License

Licensed under Apache-2.0.
