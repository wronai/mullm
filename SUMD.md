# Mullm - Multi-Agent Learning and Labor Management

Mullm - Multi-Agent Learning and Labor Management

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `mullm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements-dev.txt, requirements-quality.txt, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: mullm;
  version: 0.1.0;
}

entity[name="ChatSessionStart"] {
  ticket_id: string!;
  project: string!;
}

entity[name="ChatMessage"] {
  session_id: str | None;
  message: string!;
  mode: string!;
  use_rag: bool!;
  form_values: dict[str, Any] | None;
  wait_for_confirmation: bool!;
}

entity[name="SessionRef"] {
  session_id: string!;
}

entity[name="WorkroomStart"] {
  user_session_id: str | None;
}

entity[name="WorkroomMessage"] {
  message: string!;
  wait_for_confirmation: bool!;
}

entity[name="ApprovalRequests"] {
  approval_id: string;
  action_type: string;
  target_id: string;
  risk_level: string;
  requested_by: string;
  status: string;
  approved_by: string;
  rejected_by: string;
  reject_reason: string;
  updated_at: datetime;
  created_at: datetime;
}

entity[name="PluginCatalog"] {
  plugin_id: string;
  version: string;
  status: string;
  capabilities: json;
  manifest: json;
  updated_at: datetime;
}

entity[name="ResourceRegistry"] {
  resource_id: string;
  uri: string;
  name: string;
  adapter: string;
  classification: string;
  status: string;
  metadata: json;
  last_transfer_id: string;
  updated_at: datetime;
  created_at: datetime;
}

entity[name="TransferLog"] {
  transfer_id: string;
  resource_id: string;
  source_uri: string;
  destination_uri: string;
  status: string;
  requested_by: string;
  outcome: json;
  error: string;
  started_at: datetime;
  completed_at: datetime;
}

entity[name="CapabilityRegistry"] {
  capability_id: string;
  kind: string;
  description: string;
  provided_by: json;
  risk_level: string;
  status: string;
  manifest: json;
  source: string;
  updated_at: datetime;
}

entity[name="EvolutionMetrics"] {
  id: bigserial;
  subject_type: string;
  subject_id: string;
  window_start: datetime;
  window_end: datetime;
  sample_count: int;
  success_count: int;
  failure_count: int;
  retry_count: int;
  human_takeover_count: int;
  rollback_count: int;
  total_duration_ms: int;
  success_rate: float;
  precision: not;
  human_takeover_rate: float;
  precision: not;
  median_duration_ms: float;
  precision: not;
  updated_at: datetime;
}

entity[name="Experiments"] {
  experiment_id: string;
  subject_type: string;
  subject_id: string;
  version: string;
  mode: string;
  traffic_percent: int;
  status: string;
  outcome: string;
  metrics: json;
  metadata: json;
  started_at: datetime;
  completed_at: datetime;
}

entity[name="ChangeProposals"] {
  change_id: string;
  change_type: string;
  target_id: string;
  status: string;
  hypothesis: string;
  proposed_by: string;
  payload: json;
  evaluation: json;
  created_at: datetime;
  updated_at: datetime;
}

entity[name="RagDocuments"] {
  resource_id: string;
  uri: string;
  name: string;
  classification: string;
  status: string;
  chunk_count: int;
  embedding_model: string;
  error: string;
  indexed_at: datetime;
  updated_at: datetime;
}

entity[name="RagChunks"] {
  chunk_id: string;
  resource_id: string;
}

entity[name="Events"] {
  id: bigserial;
  event_id: string;
  stream_id: string;
  aggregate_type: string;
  aggregate_id: string;
  event_type: string;
  revision: int;
  occurred_at: datetime;
  causation_id: string;
  correlation_id: string;
  payload: json;
  metadata: json;
}

entity[name="OperationalFeed"] {
  id: bigserial;
  event_id: string;
  stream_id: string;
  aggregate_type: string;
  aggregate_id: string;
  event_type: string;
  occurred_at: datetime;
  correlation_id: string;
  causation_id: string;
  actor_type: string;
  actor_id: string;
  title: string;
  summary: string;
  payload: json;
}

entity[name="TaskBoard"] {
  task_id: string;
  flow_id: string;
  title: string;
  status: string;
  priority: string;
  execution_mode: string;
  assigned_agent_id: string;
  assigned_human_id: string;
  required_capabilities: json;
  last_event_type: string;
  result: json;
  error: string;
  updated_at: datetime;
  created_at: datetime;
}

entity[name="AgentFleet"] {
  agent_id: string;
  machine_id: string;
  agent_type: string;
  status: string;
  capabilities: json;
  current_task_id: string;
  heartbeat_at: datetime;
  load_score: int;
  updated_at: datetime;
}

entity[name="WorkflowVersions"] {
  workflow_id: string;
  version: int;
  status: string;
  definition: json;
  proposed_at: datetime;
  activated_at: datetime;
}

entity[name="IncidentFeed"] {
  incident_id: string;
  incident_type: string;
  incident_class: string;
  severity: string;
  source: string;
  error_code: string;
  message: string;
  status: string;
  playbook_id: string;
  root_cause: string;
  correlation_id: string;
  context: json;
  diagnostics: json;
  created_at: datetime;
}

entity[name="ServiceHealth"] {
  service_id: string;
  component: string;
  status: string;
  error_code: string;
  details: json;
  last_check_at: datetime;
}

entity[name="RemediationHistory"] {
  id: bigserial;
  incident_id: string;
  playbook_id: string;
  status: string;
  result: json;
  error: string;
  started_at: datetime;
  finished_at: datetime;
  updated_at: datetime;
}

entity[name="RagQualityBoard"] {
  error_code: string;
  failure_count: int;
  last_query: string;
  last_message: string;
  last_failure_at: datetime;
  updated_at: datetime;
}

entity[name="Incidents"] {
  incident_id: string;
  correlation_id: string;
  retrieval_trace_id: string;
  chat_session_id: string;
  incident_code: string;
  severity: string;
  component: string;
  service: string;
  message: string;
  diagnostics: json;
  remediation: json;
  status: string;
  fallback_taken: string;
  created_at: datetime;
}

entity[name="RagHealthSnapshots"] {
  snapshot_id: string;
  retrieval_trace_id: string;
  correlation_id: string;
  status: string;
  checks: json;
  created_at: datetime;
}

database[name="postgres"] {
  type: postgresql;
  url: env.DATABASE_URL;
}

database[name="redis"] {
  type: redis;
  url: env.REDIS_URL;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
  auth-type: jwt;
}

workflow[name="up"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) up -d;
  step-2: run cmd=if [ "$(NLP2DSL)" = "1" ]; then \;
  step-3: run cmd=$(MAKE) --no-print-directory nlp2dsl-up; \;
  step-4: run cmd=fi;
}

workflow[name="down"] {
  trigger: manual;
  step-1: run cmd=if [ "$(NLP2DSL)" = "1" ]; then \;
  step-2: run cmd=$(MAKE) --no-print-directory nlp2dsl-down; \;
  step-3: run cmd=fi;
  step-4: run cmd=$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) down;
}

workflow[name="restart"] {
  trigger: manual;
  step-1: depend target=down;
  step-2: depend target=up;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) $(PROFILE_ARGS) build;
}

workflow[name="logs"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) $(PROFILE_ARGS) logs -f --tail=200;
}

workflow[name="ps"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) $(PROFILE_ARGS) ps;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
}

workflow[name="test-web"] {
  trigger: manual;
  step-1: run cmd=pip install -q -r requirements-dev.txt -r services/web/requirements.txt;
  step-2: run cmd=[ -f requirements-quality.txt ] && pip install -q -r requirements-quality.txt || true;
  step-3: run cmd=pytest -c services/web/pytest.ini services/web/tests -q;
}

workflow[name="test-e2e-live"] {
  trigger: manual;
  step-1: run cmd=pip install -q -r requirements-dev.txt -r services/web/requirements.txt;
  step-2: run cmd=chmod +x scripts/wait-for-web.sh;
  step-3: run cmd=./scripts/wait-for-web.sh;
  step-4: run cmd=MULLM_E2E=1 pytest -c services/web/pytest.ini services/web/tests/test_e2e_live_stack.py -v;
}

workflow[name="test-quality"] {
  trigger: manual;
  step-1: run cmd=chmod +x scripts/test-quality.sh;
  step-2: run cmd=./scripts/test-quality.sh;
}

workflow[name="test-quality-deps"] {
  trigger: manual;
  step-1: run cmd=pip install -q -r requirements-dev.txt -r services/web/requirements.txt -r requirements-quality.txt;
}

workflow[name="propact-pact"] {
  trigger: manual;
  step-1: run cmd=chmod +x scripts/run-propact-pact.sh;
  step-2: run cmd=./scripts/run-propact-pact.sh;
}

workflow[name="mullm-cli"] {
  trigger: manual;
  step-1: run cmd=printf "Dodaj do PATH:\n  export PATH=\"$(CURDIR)/scripts:$$PATH\"\n";
  step-2: run cmd=printf "Potem: mullm chat send \"lista plikow usera\"\n";
}

workflow[name="smoke"] {
  trigger: manual;
  step-1: run cmd=curl -fsS http://127.0.0.1:3003/health;
  step-2: run cmd=curl -fsS http://127.0.0.1:3003/api/agents/status;
  step-3: run cmd=curl -fsS http://127.0.0.1:8001/health;
  step-4: run cmd=curl -fsS http://127.0.0.1:8002/health;
  step-5: run cmd=if [ "$(NLP2DSL)" = "1" ] && [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \;
  step-6: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl backend: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_BACKEND_HOST_PORT)/docs && \;
  step-7: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl nlp: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_NLP_HOST_PORT)/docs && \;
  step-8: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl worker: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_WORKER_HOST_PORT)/health; \;
  step-9: run cmd=fi;
  step-10: run cmd=if [ "$(NLP2CMD)" = "1" ]; then \;
  step-11: run cmd=curl -fsS -o /dev/null -w 'nlp2cmd: %{http_code}\n' http://127.0.0.1:$${MULLM_NLP2CMD_HOST_PORT:-8020}/health; \;
  step-12: run cmd=fi;
}

workflow[name="ensure-env"] {
  trigger: manual;
  step-1: run cmd=if [ ! -f .env ] && [ -f .env.example ]; then \;
  step-2: run cmd=cp .env.example .env; \;
  step-3: run cmd=echo "Created .env from .env.example"; \;
  step-4: run cmd=fi;
}

workflow[name="ensure-nlp2dsl-env"] {
  trigger: manual;
  step-1: run cmd=if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \;
  step-2: run cmd=if [ ! -f "$(NLP2DSL_DIR)/.env" ] && [ -f "$(NLP2DSL_DIR)/.env.example" ]; then \;
  step-3: run cmd=cp "$(NLP2DSL_DIR)/.env.example" "$(NLP2DSL_DIR)/.env"; \;
  step-4: run cmd=echo "Created $(NLP2DSL_DIR)/.env from .env.example"; \;
  step-5: run cmd=fi; \;
  step-6: run cmd=fi;
}

workflow[name="nlp2dsl-up"] {
  trigger: manual;
  step-1: run cmd=if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \;
  step-2: run cmd=cd "$(NLP2DSL_DIR)" && $(COMPOSE) up -d; \;
  step-3: run cmd=else \;
  step-4: run cmd=echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"; \;
  step-5: run cmd=fi;
}

workflow[name="nlp2dsl-down"] {
  trigger: manual;
  step-1: run cmd=if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \;
  step-2: run cmd=cd "$(NLP2DSL_DIR)" && $(COMPOSE) down; \;
  step-3: run cmd=else \;
  step-4: run cmd=echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"; \;
  step-5: run cmd=fi;
}

workflow[name="nlp2cmd-up"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) --profile nlp2cmd up -d nlp2cmd;
}

workflow[name="nlp2cmd-down"] {
  trigger: manual;
  step-1: run cmd=$(COMPOSE) --profile nlp2cmd stop nlp2cmd;
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
}
```

## Interfaces

### testql Scenarios

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector, TestEndpointDetector, ConfigEndpointDetector

CONFIG[5]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  retry_backoff_ms, 1000
  detected_frameworks, FastAPIDetector, TestEndpointDetector, ConfigEndpointDetector

# Wait for service to be ready
WAIT 1000

# Health check
API GET /api/health 200
ASSERT_STATUS 200

# REST API Endpoints (1 unique)
API[1]{method, endpoint, expected_status}:
  GET, /, 200

# Capture useful values from responses for subsequent tests
# CAPTURE request_id FROM 'headers.x-request-id'
# CAPTURE session_token FROM 'body.token'

ASSERT[2]{field, operator, expected}:
  _status, <, 500
  _status, >=, 200

# Conditional flow for error handling
FLOW[2]{condition, action}:
  _status >= 500, LOG 'Server error detected'
  _status == 429, WAIT 2000  # Rate limit - wait and retry


# Summary by Framework:
#   fastapi: 1 endpoints
#   env: 5 endpoints
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 24 assertions from pytest
ASSERT[24]{field, operator, expected}:
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 403
  detail.error, ==, "approval_required"
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  code, ==, IncidentCode.RAG_BACKEND_UNAVAILABLE
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 403
  detail.error, ==, "approval_required"
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  _status, ==, 200
  code, ==, IncidentCode.RAG_BACKEND_UNAVAILABLE
```

## Workflows

## Configuration

```yaml
project:
  name: mullm
  version: 0.0.0
  env: local
```

## Deployment

```bash markpact:run
pip install mullm

# development install
pip install -e .[dev]
```

### Requirements Files

#### `requirements-dev.txt`

- `pytest==8.3.3`
- `pytest-asyncio==0.24.0`
- `httpx==0.27.2`
- `fastapi==0.104.1`
- `starlette==0.27.0`
- `anyio>=3.7.1,<4.0.0`

#### `requirements-quality.txt`

- `typer>=0.12.0,<1.0`
- `rich>=13.0`

### Docker Compose (`docker-compose.yml`)

- **postgres** image=`postgres:15` ports: `${MULLM_POSTGRES_HOST_PORT}:${MULLM_POSTGRES_PORT}`
- **nats** image=`nats:2.9` ports: `${MULLM_NATS_CLIENT_HOST_PORT}:${MULLM_NATS_CLIENT_PORT}`, `${MULLM_NATS_MONITOR_HOST_PORT}:${MULLM_NATS_MONITOR_PORT}`
- **redis** image=`redis:7-alpine` ports: `${MULLM_REDIS_HOST_PORT}:${MULLM_REDIS_PORT}`
- **eventstoredb** image=`eventstore/eventstore:24.10.0-bookworm-slim` ports: `${MULLM_EVENTSTORE_HOST_PORT}:${MULLM_EVENTSTORE_PORT}`
- **orchestrator** image=`{'context': './services/orchestrator', 'dockerfile': 'Dockerfile'}` ports: `${MULLM_ORCHESTRATOR_HOST_PORT}:${MULLM_ORCHESTRATOR_PORT}`
- **projector** image=`{'context': './services/projector', 'dockerfile': 'Dockerfile'}` ports: `${MULLM_PROJECTOR_HOST_PORT}:${MULLM_PROJECTOR_PORT}`
- **nlp2dsl-nlp** image=`{'context': '../nlp2dsl/nlp-service'}` ports: `${MULLM_NLP2DSL_NLP_HOST_PORT:-8012}:8002`
- **nlp2dsl-backend** image=`{'context': '../nlp2dsl/backend'}` ports: `${MULLM_NLP2DSL_BACKEND_HOST_PORT:-8010}:8000`
- **nlp2dsl-worker** image=`{'context': '../nlp2dsl/worker'}`
- **nlp2cmd** image=`{'context': '..', 'dockerfile': 'mullm/docker/nlp2cmd-service.Dockerfile'}` ports: `${MULLM_NLP2CMD_HOST_PORT:-8020}:8000`
- **web** image=`{'context': './services/web', 'dockerfile': 'Dockerfile'}` ports: `${MULLM_WEB_HOST_PORT}:${MULLM_WEB_PORT}`
- **shell-agent-a** image=`{'context': './agents/shell-agent', 'dockerfile': 'Dockerfile'}`
- **shell-agent-b** image=`{'context': './agents/shell-agent', 'dockerfile': 'Dockerfile'}`
- **access-data** image=`busybox:latest`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_PROFILES` | `core,web` | Docker Compose — bez tego: `docker compose up -d` → „no service selected” |
| `OPENROUTER_API_KEY` | `*(not set)*` | --- OpenRouter (RAG) --- |
| `LLM_MODEL` | `deepseek/deepseek-v4-pro` | Lokalnie możesz użyć prefiksu openrouter/ — API normalizuje do deepseek/... |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` |  |
| `RAG_AUTO_INGEST` | `true` |  |
| `POSTGRES_DB` | `mullm` | --- Postgres credentials --- |
| `POSTGRES_USER` | `mullm` |  |
| `POSTGRES_PASSWORD` | `mullm_password` |  |
| `MULLM_POSTGRES_HOST` | `postgres` | --- Docker: service hostnames (internal DNS) --- |
| `MULLM_NATS_HOST` | `nats` |  |
| `MULLM_REDIS_HOST` | `redis` |  |
| `MULLM_EVENTSTORE_HOST` | `eventstoredb` |  |
| `MULLM_ORCHESTRATOR_HOST` | `orchestrator` |  |
| `MULLM_PROJECTOR_HOST` | `projector` |  |
| `MULLM_POSTGRES_PORT` | `5432` | --- Docker: container (internal) ports --- |
| `MULLM_NATS_CLIENT_PORT` | `4222` |  |
| `MULLM_NATS_MONITOR_PORT` | `8222` |  |
| `MULLM_REDIS_PORT` | `6379` |  |
| `MULLM_EVENTSTORE_PORT` | `2113` |  |
| `MULLM_ORCHESTRATOR_PORT` | `8000` |  |
| `MULLM_PROJECTOR_PORT` | `8000` |  |
| `MULLM_WEB_PORT` | `3000` |  |
| `MULLM_POSTGRES_HOST_PORT` | `5433` | --- Host-published ports (localhost) --- |
| `MULLM_NATS_CLIENT_HOST_PORT` | `4222` |  |
| `MULLM_NATS_MONITOR_HOST_PORT` | `8222` |  |
| `MULLM_REDIS_HOST_PORT` | `6379` |  |
| `MULLM_EVENTSTORE_HOST_PORT` | `2113` |  |
| `MULLM_ORCHESTRATOR_HOST_PORT` | `8001` |  |
| `MULLM_PROJECTOR_HOST_PORT` | `8002` |  |
| `MULLM_WEB_HOST_PORT` | `3003` |  |
| `DATABASE_URL` | `postgresql://mullm:mullm_password@localhost:5433/mullm` | --- URLs: from host / local dev --- |
| `NATS_URL` | `nats://localhost:4222` |  |
| `REDIS_URL` | `redis://localhost:6379` |  |
| `EVENTSTORE_URL` | `esdb://localhost:2113?tls=false` |  |
| `ORCHESTRATOR_URL` | `http://localhost:8001` |  |
| `PROJECTOR_URL` | `http://localhost:8002` |  |
| `WEB_URL` | `http://localhost:3003` |  |
| `MULLM_DATABASE_URL` | `postgresql://mullm:mullm_password@postgres:5432/mullm` | --- URLs: inside Docker network (used by compose services) --- |
| `MULLM_NATS_URL` | `nats://nats:4222` |  |
| `MULLM_REDIS_URL` | `redis://redis:6379` |  |
| `MULLM_EVENTSTORE_URL` | `esdb://eventstoredb:2113?tls=false` |  |
| `MULLM_ORCHESTRATOR_URL` | `http://orchestrator:8000` |  |
| `MULLM_PROJECTOR_URL` | `http://projector:8000` |  |
| `MULLM_NLP2DSL_BACKEND_HOST_PORT` | `8010` | lub: docker compose --profile nlp2dsl up -d (z katalogu mullm) |
| `MULLM_NLP2DSL_NLP_HOST_PORT` | `8012` |  |
| `NLP2DSL_BACKEND_URL` | `http://localhost:8010` |  |
| `MULLM_NLP2DSL_BACKEND_URL` | `http://nlp2dsl-backend:8000` |  |
| `MULLM_NLP2CMD_HOST_PORT` | `8020` | Uruchom: NLP2CMD=1 make up  lub  make nlp2cmd-up |
| `NLP2CMD_BACKEND_URL` | `http://localhost:8020` |  |
| `MULLM_NLP2CMD_BACKEND_URL` | `http://nlp2cmd:8000` |  |
| `PROMPT_ROUTER_MODE` | `auto` | auto = hybrid gdy nlp2cmd/OpenRouter dostępne; rules = tylko regex; llm = reguły+LLM |
| `MULLM_ROUTING_NLP2CMD` | `1` |  |
| `MULLM_ROUTING_NLP2CMD_MIN_CONFIDENCE` | `0.65` |  |
| `MULLM_SHELL_WAIT_SECONDS` | `20` | Czekaj na stdout shell w tej samej odpowiedzi czatu (0 = tylko ticket, wynik w ◎) |
| `CATALOG_PATH` | `*(not set)*` | --- App --- |
| `ENVIRONMENT` | `development` |  |
| `EVENT_STORE_BACKEND` | `postgres` |  |
| `LOG_LEVEL` | `INFO` |  |
| `AGENT_ID` | `shell-agent-1` |  |
| `JWT_SECRET` | `your_jwt_secret_here` |  |
| `API_KEY` | `your_api_key_here` |  |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`mullm`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Makefile Targets

- `SHELL`
- `PROFILE_ARGS`
- `help`
- `NLP2CMD_PROFILE_ARGS`
- `up`
- `down`
- `restart`
- `build`
- `logs`
- `ps`
- `test`
- `test-web`
- `test-e2e-live`
- `test-quality`
- `test-quality-deps`
- `propact-pact`
- `mullm-cli`
- `smoke`
- `ensure-env`
- `ensure-nlp2dsl-env`
- `nlp2dsl-up`
- `nlp2dsl-down`
- `nlp2cmd-up`
- `nlp2cmd-down`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# mullm | 198f 28712L | python:181,shell:7,css:5,javascript:4,less:1 | 2026-06-05
# stats: 997 func | 168 cls | 198 mod | CC̄=3.1 | critical:15 | cycles:0
# alerts[5]: CC explain_pipeline=16; CC test_load_default_policy=15; CC test_incident_recorder_publishes_projectable_events=14; CC orient_query=13; CC _should_prefer_nlp2cmd_over_rules=13
# hotspots[5]: _rag_failure_result fan=27; lifespan fan=21; upload_resource fan=17; aggregate_learnings fan=16; search fan=15
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[198]:
  agents/shell-agent/app/__init__.py,2
  agents/shell-agent/app/executor.py,49
  agents/shell-agent/app/main.py,27
  agents/shell-agent/app/nats_consumer.py,48
  app.doql.less,474
  integrations/nlp2dsl/mullm_registry.py,33
  integrations/nlp2dsl/patch_startup.py,8
  project.sh,53
  scripts/e2e-chat-routing.sh,80
  scripts/run-propact-pact.sh,72
  scripts/test-quality.sh,63
  scripts/test.sh,14
  scripts/wait-for-web.sh,23
  services/orchestrator/app/__init__.py,2
  services/orchestrator/app/access/__init__.py,5
  services/orchestrator/app/access/adapters/__init__.py,18
  services/orchestrator/app/access/adapters/base.py,34
  services/orchestrator/app/access/adapters/http_adapter.py,50
  services/orchestrator/app/access/adapters/localfs.py,72
  services/orchestrator/app/access/transport.py,78
  services/orchestrator/app/access/uri.py,44
  services/orchestrator/app/api/__init__.py,2
  services/orchestrator/app/api/access.py,137
  services/orchestrator/app/api/catalog.py,42
  services/orchestrator/app/api/commands.py,380
  services/orchestrator/app/api/evolution.py,105
  services/orchestrator/app/api/observability.py,113
  services/orchestrator/app/api/queries.py,205
  services/orchestrator/app/api/rag.py,143
  services/orchestrator/app/application/__init__.py,2
  services/orchestrator/app/application/command_bus.py,990
  services/orchestrator/app/application/sagas/__init__.py,15
  services/orchestrator/app/application/sagas/approval_gate.py,147
  services/orchestrator/app/application/sagas/task_routing.py,67
  services/orchestrator/app/config.py,55
  services/orchestrator/app/domain/__init__.py,2
  services/orchestrator/app/domain/aggregates/__init__.py,2
  services/orchestrator/app/domain/aggregates/agent.py,84
  services/orchestrator/app/domain/aggregates/approval.py,98
  services/orchestrator/app/domain/aggregates/plugin.py,98
  services/orchestrator/app/domain/aggregates/resource.py,101
  services/orchestrator/app/domain/aggregates/task.py,245
  services/orchestrator/app/domain/aggregates/workflow.py,145
  services/orchestrator/app/domain/events/__init__.py,104
  services/orchestrator/app/domain/events/agents.py,96
  services/orchestrator/app/domain/events/approvals.py,127
  services/orchestrator/app/domain/events/base.py,82
  services/orchestrator/app/domain/events/incidents.py,255
  services/orchestrator/app/domain/events/plugins.py,119
  services/orchestrator/app/domain/events/resources.py,133
  services/orchestrator/app/domain/events/tasks.py,134
  services/orchestrator/app/domain/events/workflows.py,168
  services/orchestrator/app/domain/value_objects/__init__.py,86
  services/orchestrator/app/evolution/__init__.py,13
  services/orchestrator/app/evolution/catalog.py,93
  services/orchestrator/app/evolution/evaluation.py,203
  services/orchestrator/app/evolution/experiments.py,77
  services/orchestrator/app/evolution/policy_engine.py,132
  services/orchestrator/app/incidents/__init__.py,4
  services/orchestrator/app/incidents/pipeline.py,406
  services/orchestrator/app/infrastructure/__init__.py,2
  services/orchestrator/app/infrastructure/eventstore.py,183
  services/orchestrator/app/infrastructure/eventstore_dual.py,58
  services/orchestrator/app/infrastructure/eventstore_esdb.py,187
  services/orchestrator/app/infrastructure/eventstore_factory.py,67
  services/orchestrator/app/infrastructure/nats_bus.py,50
  services/orchestrator/app/infrastructure/postgres.py,93
  services/orchestrator/app/main.py,196
  services/orchestrator/app/observability/__init__.py,23
  services/orchestrator/app/observability/context.py,60
  services/orchestrator/app/observability/export.py,398
  services/orchestrator/app/observability/incidents.py,581
  services/orchestrator/app/observability/logging.py,60
  services/orchestrator/app/observability/middleware.py,20
  services/orchestrator/app/observability/rag_diagnostics.py,223
  services/orchestrator/app/observability/rag_pipeline.py,271
  services/orchestrator/app/rag/__init__.py,7
  services/orchestrator/app/rag/chunking.py,31
  services/orchestrator/app/rag/indexer.py,116
  services/orchestrator/app/rag/openrouter.py,129
  services/orchestrator/app/rag/retriever.py,104
  services/orchestrator/app/rag/store.py,284
  services/orchestrator/tests/__init__.py,2
  services/orchestrator/tests/conftest.py,10
  services/orchestrator/tests/fakes.py,64
  services/orchestrator/tests/test_api.py,90
  services/orchestrator/tests/test_command_bus.py,57
  services/orchestrator/tests/test_observability.py,151
  services/orchestrator/tests/test_task_aggregate.py,28
  services/projector/app/__init__.py,2
  services/projector/app/db.py,57
  services/projector/app/main.py,341
  services/projector/app/projections/__init__.py,4
  services/projector/app/projections/agent_fleet.py,98
  services/projector/app/projections/approval_requests.py,80
  services/projector/app/projections/dispatcher.py,48
  services/projector/app/projections/incidents.py,332
  services/projector/app/projections/operational_feed.py,71
  services/projector/app/projections/plugin_catalog.py,43
  services/projector/app/projections/resource_registry.py,131
  services/projector/app/projections/task_board.py,154
  services/projector/app/projections/workflow_versions.py,48
  services/web/app/__init__.py,1
  services/web/app/access_matrix.py,249
  services/web/app/agent_plugins/__init__.py,20
  services/web/app/agent_plugins/nlp2cmd_plugin.py,111
  services/web/app/agent_plugins/nlp2dsl_plugin.py,23
  services/web/app/agent_plugins/protocol.py,64
  services/web/app/agent_plugins/registry.py,96
  services/web/app/agent_workroom.py,643
  services/web/app/api/__init__.py,2
  services/web/app/api/access_routes.py,47
  services/web/app/api/agents_routes.py,14
  services/web/app/api/chat_routes.py,182
  services/web/app/api/config.py,17
  services/web/app/api/feedback_routes.py,52
  services/web/app/api/models.py,92
  services/web/app/api/router_routes.py,88
  services/web/app/api/task_routes.py,191
  services/web/app/api/workroom_routes.py,55
  services/web/app/api/workspace_routes.py,81
  services/web/app/api_routes.py,26
  services/web/app/chat.py,1072
  services/web/app/conductor.py,1486
  services/web/app/local_orient.py,208
  services/web/app/main.py,105
  services/web/app/nlp2dsl_bridge.py,175
  services/web/app/planfile_bridge.py,103
  services/web/app/prompt_router.py,927
  services/web/app/resource_areas.py,172
  services/web/app/routing/__init__.py,14
  services/web/app/routing/decision.py,101
  services/web/app/routing/execution_resolver.py,91
  services/web/app/routing/ingress_cache.py,44
  services/web/app/routing/orientation_provider.py,82
  services/web/app/routing_feedback.py,413
  services/web/app/routing_policy.py,183
  services/web/app/routing_schemas.py,172
  services/web/app/routing_trace.py,740
  services/web/app/static/access.css,84
  services/web/app/static/access.js,158
  services/web/app/static/app.css,200
  services/web/app/static/app.js,207
  services/web/app/static/workroom.css,87
  services/web/app/static/workroom.js,269
  services/web/app/static/workspace.css,856
  services/web/app/static/workspace.js,1402
  services/web/app/ticket_schemas.py,144
  services/web/app/tickets.py,46
  services/web/app/workspace.py,1439
  services/web/src/styles.css,287
  services/web/tests/conftest.py,84
  services/web/tests/test_access_matrix.py,38
  services/web/tests/test_agent_plugins.py,47
  services/web/tests/test_agent_workroom.py,73
  services/web/tests/test_api_routes.py,23
  services/web/tests/test_artifacts.py,191
  services/web/tests/test_chat_intent.py,127
  services/web/tests/test_conductor_ingress.py,102
  services/web/tests/test_context_tickets.py,40
  services/web/tests/test_continue_intent.py,38
  services/web/tests/test_e2e_chat_api.py,231
  services/web/tests/test_e2e_live_stack.py,204
  services/web/tests/test_intract_contracts.py,56
  services/web/tests/test_local_orient.py,14
  services/web/tests/test_nlp2dsl_bridge.py,44
  services/web/tests/test_nlp2dsl_orient.py,122
  services/web/tests/test_nlp2dsl_resume.py,74
  services/web/tests/test_prompt_router.py,76
  services/web/tests/test_prompt_router_hybrid.py,110
  services/web/tests/test_routing_contract.py,102
  services/web/tests/test_routing_explain.py,48
  services/web/tests/test_routing_feedback.py,76
  services/web/tests/test_routing_policy.py,42
  services/web/tests/test_routing_schemas.py,78
  services/web/tests/test_shell_nl_intent.py,15
  services/web/tests/test_ticket_schemas.py,40
  tests/conftest.py,354
  tests/test_access_fabric.py,62
  tests/test_agent_aggregate.py,33
  tests/test_api_orchestrator.py,152
  tests/test_approval_aggregate.py,26
  tests/test_approval_gate.py,121
  tests/test_command_bus.py,134
  tests/test_e2e_flow.py,46
  tests/test_eventstore_factory.py,26
  tests/test_evolution_layer.py,90
  tests/test_incident_observability.py,170
  tests/test_integration_postgres.py,43
  tests/test_plugin_aggregate.py,30
  tests/test_projections.py,88
  tests/test_projector_routes.py,37
  tests/test_rag.py,115
  tests/test_shell_executor.py,43
  tests/test_task_aggregate.py,38
  tests/test_task_routing.py,48
  tests/test_workflow_aggregate.py,25
  tree.sh,2
D:
  agents/shell-agent/app/__init__.py:
  agents/shell-agent/app/executor.py:
    e: run_shell_command,ShellResult
    ShellResult: ok(0),to_dict(0)
    run_shell_command(command;timeout_seconds)
  agents/shell-agent/app/main.py:
    e: main
    main()
  agents/shell-agent/app/nats_consumer.py:
    e: ShellAgent
    ShellAgent: __init__(0),run(0),handle_message(1)
  integrations/nlp2dsl/mullm_registry.py:
  integrations/nlp2dsl/patch_startup.py:
  services/orchestrator/app/__init__.py:
  services/orchestrator/app/access/__init__.py:
  services/orchestrator/app/access/adapters/__init__.py:
    e: get_adapter
    get_adapter(name)
  services/orchestrator/app/access/adapters/base.py:
    e: AdapterResult,ResourceAdapter
    AdapterResult:
    ResourceAdapter: probe(1),fetch(1),copy_to_local(2)
  services/orchestrator/app/access/adapters/http_adapter.py:
    e: HttpAdapter
    HttpAdapter: probe(1),fetch(1),copy_to_local(2),_to_url(1)
  services/orchestrator/app/access/adapters/localfs.py:
    e: LocalFsAdapter
    LocalFsAdapter: __init__(1),_resolve(1),probe(1),fetch(1),copy_to_local(2)
  services/orchestrator/app/access/transport.py:
    e: TransportService
    TransportService: __init__(0),_sandbox_dir(0),probe(1),fetch(1),copy(2),package_to_sandbox(1),_result_dict(2)  # Access Fabric — probe, fetch, copy między adapterami.
  services/orchestrator/app/access/uri.py:
    e: parse_uri,build_uri,MullmUri
    MullmUri: canonical(0)
    parse_uri(uri)
    build_uri(adapter;path)
  services/orchestrator/app/api/__init__.py:
  services/orchestrator/app/api/access.py:
    e: register_resource,transfer_resource,probe_uri,fetch_uri,list_resources,build_resource_uri,_safe_filename,upload_resource,RegisterResourceCommand,TransferResourceCommand,ProbeUriCommand
    RegisterResourceCommand:
    TransferResourceCommand:
    ProbeUriCommand:
    register_resource(command;request)
    transfer_resource(command;request)
    probe_uri(command;request)
    fetch_uri(command;request)
    list_resources(request;limit)
    build_resource_uri(adapter;path)
    _safe_filename(name)
    upload_resource(request;file;classification)
  services/orchestrator/app/api/catalog.py:
    e: catalog_index,catalog_graph,catalog_domains,catalog_events,catalog_capabilities,catalog_services,catalog_policies
    catalog_index(request)
    catalog_graph(request)
    catalog_domains(request)
    catalog_events(request)
    catalog_capabilities(request)
    catalog_services(request)
    catalog_policies(request)
  services/orchestrator/app/api/commands.py:
    e: post_command,create_task,assign_task,start_task,complete_task,fail_task,register_agent,start_workflow,propose_workflow_version,validate_workflow_version,approve_workflow_version,activate_workflow_version,rollback_workflow_version,propose_plugin,validate_plugin,install_plugin,activate_plugin,rollback_plugin,create_approval,approve_request,reject_request,expire_approval,_dispatch,CommandEnvelope,CreateTaskCommand,AssignTaskCommand,StartTaskCommand,CompleteTaskCommand,FailTaskCommand,RegisterAgentCommand,StartWorkflowCommand,ProposeWorkflowVersionCommand,WorkflowVersionCommand,ProposePluginCommand,PluginIdCommand,CreateApprovalCommand,ApprovalActionCommand
    CommandEnvelope:
    CreateTaskCommand:
    AssignTaskCommand:
    StartTaskCommand:
    CompleteTaskCommand:
    FailTaskCommand:
    RegisterAgentCommand:
    StartWorkflowCommand:
    ProposeWorkflowVersionCommand:
    WorkflowVersionCommand:
    ProposePluginCommand:
    PluginIdCommand:
    CreateApprovalCommand:
    ApprovalActionCommand:
    post_command(command;request)
    create_task(command;request)
    assign_task(command;request)
    start_task(command;request)
    complete_task(command;request)
    fail_task(command;request)
    register_agent(command;request)
    start_workflow(command;request)
    propose_workflow_version(command;request)
    validate_workflow_version(command;request)
    approve_workflow_version(command;request)
    activate_workflow_version(command;request)
    rollback_workflow_version(command;request)
    propose_plugin(command;request)
    validate_plugin(command;request)
    install_plugin(command;request)
    activate_plugin(command;request)
    rollback_plugin(command;request)
    create_approval(command;request)
    approve_request(command;request)
    reject_request(command;request)
    expire_approval(command;request)
    _dispatch(request;command_type;data)
  services/orchestrator/app/api/evolution.py:
    e: evolution_metrics,list_experiments,capability_registry,propose_change,shadow_workflow,ProposeChangeCommand,ShadowWorkflowCommand
    ProposeChangeCommand:
    ShadowWorkflowCommand:
    evolution_metrics(request;subject_type;subject_id;limit)
    list_experiments(request;status;limit)
    capability_registry(request;limit)
    propose_change(command;request)
    shadow_workflow(command;request)
  services/orchestrator/app/api/observability.py:
    e: rag_health,rag_diagnose,list_playbooks,export_logs,list_incidents,DiagnoseBody
    DiagnoseBody:
    rag_health(request)
    rag_diagnose(body;request)
    list_playbooks()
    export_logs(request;correlation_id;limit)
    list_incidents(request;limit)
  services/orchestrator/app/api/queries.py:
    e: get_task,get_agent,get_workflow,list_tasks,_task_list_item,_aggregate_state,_matches_task_filters,list_agents,_event_to_dict,TaskQuery,AgentQuery,WorkflowQuery,TaskListQuery
    TaskQuery:
    AgentQuery:
    WorkflowQuery:
    TaskListQuery:
    get_task(task_id;request)
    get_agent(agent_id;request)
    get_workflow(workflow_id;request)
    list_tasks(request;status;agent_id;limit;offset)
    _task_list_item(task_id;events)
    _aggregate_state(events)
    _matches_task_filters(task_state)
    list_agents(request;limit;offset)
    _event_to_dict(event)
  services/orchestrator/app/api/rag.py:
    e: rag_health,list_documents,search,ask,ingest_resource,_safe_rag_diagnostics,SearchQuery,AskQuery
    SearchQuery:
    AskQuery:
    rag_health(request)
    list_documents(request;limit)
    search(body;request)
    ask(body;request)
    ingest_resource(resource_id;request)
    _safe_rag_diagnostics(request)
  services/orchestrator/app/application/__init__.py:
  services/orchestrator/app/application/command_bus.py:
    e: _task_outcome_payload,CommandBus
    CommandBus: __init__(2),handle(0),handle_envelope(1),_create_task(4),_assign_task(4),_start_task(4),_complete_task(4),_fail_task(4),_register_agent(4),_agent_heartbeat(4),_start_workflow(4),_propose_workflow_version(4),_validate_workflow_version(4),_approve_workflow_version(4),_activate_workflow_version(4),_rollback_workflow_version(4),_shadow_workflow_version(4),_propose_change(4),_propose_plugin(4),_validate_plugin(4),_install_plugin(4),_activate_plugin(4),_rollback_plugin(4),_create_approval(4),_approve_request(4),_reject_request(4),_expire_approval(4),_persist_workflow(4),_persist_plugin(4),_persist_approval(4),_load_workflow(1),_load_plugin(1),_load_approval(1),_load_task(1),_append_and_publish(3),_publish(2),_apply_policy(2),_register_resource(4),_request_transfer(4),_record_task_outcome(1),_should_auto_rollback(2),_rollback_workflow(1),_result(2)
    _task_outcome_payload(task)
  services/orchestrator/app/application/sagas/__init__.py:
  services/orchestrator/app/application/sagas/approval_gate.py:
    e: _is_skipped,ensure_approval,_required_approval_id,_validate_approval_events,follow_up_after_grant,ApprovalRequired
    ApprovalRequired: __init__(0)  # Komenda wymaga wcześniejszego ApprovalGranted.
    _is_skipped(data;metadata)
    ensure_approval(event_store;command_type;data)
    _required_approval_id(command_type;data;action_type;target_id)
    _validate_approval_events(events;approval_id;action_type;target_id)
    follow_up_after_grant(command_bus)
  services/orchestrator/app/application/sagas/task_routing.py:
    e: pick_idle_agent,_agent_route_state,_agent_matches,maybe_auto_assign
    pick_idle_agent(event_store;required_capabilities)
    _agent_route_state(events)
    _agent_matches(state;required)
    maybe_auto_assign(command_bus)
  services/orchestrator/app/config.py:
    e: Settings
    Settings: model_post_init(1)
  services/orchestrator/app/domain/__init__.py:
  services/orchestrator/app/domain/aggregates/__init__.py:
  services/orchestrator/app/domain/aggregates/agent.py:
    e: _utc_now,Agent
    Agent: register(5),heartbeat(1),assign_task(1),mark_idle(0),get_uncommitted_events(0),mark_events_committed(0)
    _utc_now()
  services/orchestrator/app/domain/aggregates/approval.py:
    e: ApprovalStatus,Approval
    ApprovalStatus:
    Approval: create_request(1),approve(1),reject(2),expire(0),get_uncommitted_events(0),mark_events_committed(0)
  services/orchestrator/app/domain/aggregates/plugin.py:
    e: PluginStatus,Plugin
    PluginStatus:
    Plugin: propose(5),validate(0),install(0),activate(0),rollback(1),get_uncommitted_events(0),mark_events_committed(0)
  services/orchestrator/app/domain/aggregates/resource.py:
    e: Resource
    Resource: register(1),request_transfer(0),complete_transfer(2),fail_transfer(2),get_uncommitted_events(0),mark_events_committed(0)
  services/orchestrator/app/domain/aggregates/task.py:
    e: _event_type,_utc_now,_event_data,_event_timestamp,_apply_task_created,_apply_task_assigned,_apply_task_started,_apply_task_completed,_apply_task_failed,Task
    Task: __init__(8),create(8),from_events(2),assign_to_agent(1),start(0),complete(1),fail(1),apply(1),get_uncommitted_events(0),mark_events_committed(0),to_dict(0)
    _event_type(event)
    _utc_now()
    _event_data(event)
    _event_timestamp(event)
    _apply_task_created(task;data;timestamp)
    _apply_task_assigned(task;data;timestamp)
    _apply_task_started(task;data;timestamp)
    _apply_task_completed(task;data;timestamp)
    _apply_task_failed(task;data;timestamp)
  services/orchestrator/app/domain/aggregates/workflow.py:
    e: Workflow
    Workflow: start(4),propose_version(4),validate_version(0),approve_version(1),shadow_version(1),activate_version(0),rollback_version(1),get_uncommitted_events(0),mark_events_committed(0)
  services/orchestrator/app/domain/events/__init__.py:
  services/orchestrator/app/domain/events/agents.py:
    e: AgentRegistered,AgentHeartbeatReceived,TaskAssignedToAgent,AgentMarkedIdle
    AgentRegistered: aggregate_id(0),data(0)
    AgentHeartbeatReceived: aggregate_id(0),data(0)
    TaskAssignedToAgent: aggregate_id(0),data(0)
    AgentMarkedIdle: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/approvals.py:
    e: ApprovalRequested,ApprovalGranted,ApprovalRejected,ApprovalExpired,ChangeProposed
    ApprovalRequested: aggregate_id(0),data(0)
    ApprovalGranted: aggregate_id(0),data(0)
    ApprovalRejected: aggregate_id(0),data(0)
    ApprovalExpired: aggregate_id(0),data(0)
    ChangeProposed: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/base.py:
    e: _utc_now,_json_value,_json_datetime,_json_list,_json_dict,_json_none,DomainEvent
    DomainEvent: aggregate_id(0),data(0),to_message(0)
    _utc_now()
    _json_value(value)
    _json_datetime(value)
    _json_list(value)
    _json_dict(value)
    _json_none(value)
  services/orchestrator/app/domain/events/incidents.py:
    e: RagRequestFailed,IncidentDetected,IncidentClassified,DiagnosticsStarted,DiagnosticsCompleted,RemediationStarted,RemediationSucceeded,RemediationFailed,PostRemediationVerificationPassed,PostRemediationVerificationFailed
    RagRequestFailed: aggregate_id(0),data(0)
    IncidentDetected: aggregate_id(0),data(0)
    IncidentClassified: aggregate_id(0),data(0)
    DiagnosticsStarted: aggregate_id(0),data(0)
    DiagnosticsCompleted: aggregate_id(0),data(0)
    RemediationStarted: aggregate_id(0),data(0)
    RemediationSucceeded: aggregate_id(0),data(0)
    RemediationFailed: aggregate_id(0),data(0)
    PostRemediationVerificationPassed: aggregate_id(0),data(0)
    PostRemediationVerificationFailed: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/plugins.py:
    e: PluginProposed,PluginValidated,PluginInstalled,PluginActivated,PluginRolledBack
    PluginProposed: aggregate_id(0),data(0)
    PluginValidated: aggregate_id(0),data(0)
    PluginInstalled: aggregate_id(0),data(0)
    PluginActivated: aggregate_id(0),data(0)
    PluginRolledBack: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/resources.py:
    e: CapabilityRegistered,ResourceRegistered,TransferRequested,TransferCompleted,TransferFailed
    CapabilityRegistered: aggregate_id(0),data(0)
    ResourceRegistered: aggregate_id(0),data(0)
    TransferRequested: aggregate_id(0),data(0)
    TransferCompleted: aggregate_id(0),data(0)
    TransferFailed: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/tasks.py:
    e: TaskCreated,TaskAssigned,TaskStarted,TaskCompleted,TaskFailed
    TaskCreated: aggregate_id(0),data(0)
    TaskAssigned: aggregate_id(0),data(0)
    TaskStarted: aggregate_id(0),data(0)
    TaskCompleted: aggregate_id(0),data(0)
    TaskFailed: aggregate_id(0),data(0)
  services/orchestrator/app/domain/events/workflows.py:
    e: WorkflowStarted,WorkflowVersionProposed,WorkflowVersionValidated,WorkflowVersionApproved,WorkflowVersionShadowed,WorkflowVersionActivated,WorkflowVersionRolledBack
    WorkflowStarted: aggregate_id(0),data(0)
    WorkflowVersionProposed: aggregate_id(0),data(0)
    WorkflowVersionValidated: aggregate_id(0),data(0)
    WorkflowVersionApproved: aggregate_id(0),data(0)
    WorkflowVersionShadowed: aggregate_id(0),data(0)
    WorkflowVersionActivated: aggregate_id(0),data(0)
    WorkflowVersionRolledBack: aggregate_id(0),data(0)
  services/orchestrator/app/domain/value_objects/__init__.py:
    e: TaskId,AgentId,WorkflowId,PluginId,ApprovalId,ResourceId,Priority,TaskStatus,ExecutionMode,AgentStatus,WorkflowStatus
    TaskId:
    AgentId:
    WorkflowId:
    PluginId:
    ApprovalId:
    ResourceId:
    Priority: from_value(2)
    TaskStatus:
    ExecutionMode: from_value(2)
    AgentStatus:
    WorkflowStatus:
  services/orchestrator/app/evolution/__init__.py:
  services/orchestrator/app/evolution/catalog.py:
    e: ArchitectureCatalog
    ArchitectureCatalog: __init__(1),_load_json(1),index(0),domains(0),capabilities(0),services(0),policies(0),list_events(0),get_event_schema(1),get_capability(1),as_graph(0)  # Samopiszący katalog architektury mullm (domains, events, cap
  services/orchestrator/app/evolution/evaluation.py:
    e: _count_if,_rate_if,_should_rollback_metrics,EvaluationEngine
    EvaluationEngine: __init__(1),record_task_outcome(0),_upsert_metrics(0),_current_metrics_row(3),_update_metrics(1),_insert_metrics(0),should_auto_rollback(2)  # Pętla oceny skutków — metryki jakości ewolucji i runtime.
    _count_if(value)
    _rate_if(value)
    _should_rollback_metrics(row)
  services/orchestrator/app/evolution/experiments.py:
    e: ExperimentManager
    ExperimentManager: __init__(1),start_experiment(0),complete_experiment(1),active_shadow(1)  # Shadow / canary — stan eksperymentu powiązany z wersją workf
  services/orchestrator/app/evolution/policy_engine.py:
    e: _activation_metrics_row,_has_enough_activation_samples,PolicyViolation,PolicyEngine
    PolicyViolation: __init__(2)
    PolicyEngine: __init__(1),rule_for(1),validate_command(2),_validate_environment(3),_validate_manifest(3),_validate_auto_risk(3),validate_activation_metrics(3)  # Reguły first — AI proponuje tylko w granicach polityk z kata
    _activation_metrics_row(postgres;target_id)
    _has_enough_activation_samples(row;policies)
  services/orchestrator/app/incidents/__init__.py:
  services/orchestrator/app/incidents/pipeline.py:
    e: classify_rag_error,_rag_root_cause,_rag_schema_missing,_rag_index_empty,_retriever_empty_result,_openrouter_unconfigured,_rag_failure_events,_rag_failure_result,IncidentPipeline
    IncidentPipeline: __init__(0),handle_rag_failure(0)
    classify_rag_error(error)
    _rag_root_cause(checks)
    _rag_schema_missing(checks;combined_errors)
    _rag_index_empty(checks;combined_errors)
    _retriever_empty_result(checks;combined_errors)
    _openrouter_unconfigured(checks;combined_errors)
    _rag_failure_events(incident_id)
    _rag_failure_result(incident_id)
  services/orchestrator/app/infrastructure/__init__.py:
  services/orchestrator/app/infrastructure/eventstore.py:
    e: _loads_json,_utc_now,EventRecord,EventStore
    EventRecord: to_message(0)
    EventStore: __init__(1),append(3),get_events_for_aggregate(2),get_aggregate_ids(1),all_events(0),_record_from_row(1)
    _loads_json(value)
    _utc_now()
  services/orchestrator/app/infrastructure/eventstore_dual.py:
    e: DualEventStore
    DualEventStore: __init__(2),append(3),get_events_for_aggregate(2),get_aggregate_ids(1),all_events(0)  # Zapis do Postgres (odczyt) + mirror do EventStoreDB.
  services/orchestrator/app/infrastructure/eventstore_esdb.py:
    e: _parse_esdb_uri,EsdbEventStore
    EsdbEventStore: __init__(1),connect(0),disconnect(0),append(3),get_events_for_aggregate(2),get_aggregate_ids(1),all_events(0)  # Adapter EventStoreDB przez pakiet `esdbclient`.
    _parse_esdb_uri(uri)
  services/orchestrator/app/infrastructure/eventstore_factory.py:
    e: build_event_store,_require_eventstore_url,_eventstoredb_backend,_dual_backend
    build_event_store()
    _require_eventstore_url(eventstore_url;backend)
    _eventstoredb_backend(eventstore_url;info)
    _dual_backend(primary;eventstore_url;info)
  services/orchestrator/app/infrastructure/nats_bus.py:
    e: NATSBus
    NATSBus: __init__(1),connect(0),disconnect(0),publish(2),subscribe(2)
  services/orchestrator/app/infrastructure/postgres.py:
    e: PostgresConnection
    PostgresConnection: __init__(1),connect(0),disconnect(0),execute(1),fetch(1),fetchrow(1),_run_schema_migrations(0)
  services/orchestrator/app/main.py:
    e: lifespan,health_check,root,_seed_capability_registry,_subscribe_shell_results
    lifespan(app)
    health_check()
    root()
    _seed_capability_registry(app)
    _subscribe_shell_results(app)
  services/orchestrator/app/observability/__init__.py:
  services/orchestrator/app/observability/context.py:
    e: new_correlation_id,new_retrieval_trace_id,get_correlation_id,get_retrieval_trace_id,get_chat_session_id,observability_context
    new_correlation_id()
    new_retrieval_trace_id()
    get_correlation_id()
    get_retrieval_trace_id()
    get_chat_session_id()
    observability_context()
  services/orchestrator/app/observability/export.py:
    e: format_logs_text,clamp_log_export_limit,_nfo_package_version,_build_nfo_package,_nfo_counts,_nfo_errors,_append_nfo,_append_rag_health,_append_incidents,_append_incident_feed,_append_rag_snapshots,_append_workspace_session,_append_workspace_context,_append_workspace_events,_append_workspace_chat,build_orchestrator_bundle,_safe_rag_health,_safe_fetch_incidents,_fetch_incidents,_safe_fetch_incident_feed,_fetch_incident_feed,_safe_fetch_rag_snapshots,_fetch_rag_snapshots
    format_logs_text(bundle)
    clamp_log_export_limit(limit)
    _nfo_package_version()
    _build_nfo_package(bundle)
    _nfo_counts(bundle)
    _nfo_errors(bundle)
    _append_nfo(lines;package)
    _append_rag_health(lines;rag)
    _append_incidents(lines;incidents)
    _append_incident_feed(lines;feed)
    _append_rag_snapshots(lines;snapshots)
    _append_workspace_session(lines;session)
    _append_workspace_context(lines;ctx)
    _append_workspace_events(lines;events)
    _append_workspace_chat(lines;history)
    build_orchestrator_bundle()
    _safe_rag_health(rag_diagnostics)
    _safe_fetch_incidents(postgres)
    _fetch_incidents(postgres)
    _safe_fetch_incident_feed(postgres)
    _fetch_incident_feed(postgres)
    _safe_fetch_rag_snapshots(postgres)
    _fetch_rag_snapshots(postgres)
  services/orchestrator/app/observability/incidents.py:
    e: classify_rag_failure,_backend_unavailable,_rag_timeout,_vector_db_unavailable,_embedding_pipeline_failed,_llm_unavailable,_retriever_empty_result,_grounding_failed,_incident_row,_incident_correlation_id,_incident_trace_id,_incident_dict,_log_incident_row,_incident_event_plan,_diagnostics_event_plan,_remediation_event_plan,_remediation_done_event,_verification_event,_event_payload,_base_event_payload,_event_context,_apply_event_payload_details,_payload_rag_request_failed,_payload_incident_classified,_payload_diagnostics_started,_payload_diagnostics_completed,_payload_remediation_started,_payload_remediation_result,_query_from_trace,_check_names,_checks_payload,_checks_list_payload,_check_payload,_root_cause,_event_status,_incident_class,_default_playbook,IncidentCode,IncidentRecorder
    IncidentCode:
    IncidentRecorder: record(0),_persist(1),_publish_event(2)
    classify_rag_failure()
    _backend_unavailable(http_status;text;llm_error;source_count)
    _rag_timeout(http_status;text;llm_error;source_count)
    _vector_db_unavailable(http_status;text;llm_error;source_count)
    _embedding_pipeline_failed(http_status;text;llm_error;source_count)
    _llm_unavailable(http_status;text;llm_error;source_count)
    _retriever_empty_result(http_status;text;llm_error;source_count)
    _grounding_failed(http_status;text;llm_error;source_count)
    _incident_row()
    _incident_correlation_id(correlation_id)
    _incident_trace_id(retrieval_trace_id)
    _incident_dict(value)
    _log_incident_row(row)
    _incident_event_plan(row)
    _diagnostics_event_plan(row)
    _remediation_event_plan(row)
    _remediation_done_event(status)
    _verification_event(remediation)
    _event_payload(event_type;row)
    _base_event_payload(event_type;row)
    _event_context(row)
    _apply_event_payload_details(payload;event_type)
    _payload_rag_request_failed(payload)
    _payload_incident_classified(payload)
    _payload_diagnostics_started(payload)
    _payload_diagnostics_completed(payload)
    _payload_remediation_started(payload)
    _payload_remediation_result(payload)
    _query_from_trace(trace_steps)
    _check_names(diagnostics)
    _checks_payload(diagnostics)
    _checks_list_payload(checks)
    _check_payload(item)
    _root_cause(diagnostics;code)
    _event_status(event_type;row)
    _incident_class(code)
    _default_playbook(code)
  services/orchestrator/app/observability/logging.py:
    e: log_event,_emit_nfo_event
    log_event()
    _emit_nfo_event(payload)
  services/orchestrator/app/observability/middleware.py:
    e: CorrelationMiddleware
    CorrelationMiddleware: dispatch(2)
  services/orchestrator/app/observability/rag_diagnostics.py:
    e: _checks_with_status,_overall_status,_primary_incident_code,_log_diagnostics_result,RagDiagnostics
    RagDiagnostics: run(0),_check_postgres(0),_check_rag_tables(0),_check_openrouter_config(0),_check_embedding(0),_check_search(1),_recommendations(1),_snapshot(1)
    _checks_with_status(checks;status)
    _overall_status(checks)
    _primary_incident_code(checks)
    _log_diagnostics_result(overall;primary_code;checks)
  services/orchestrator/app/observability/rag_pipeline.py:
    e: _result_with_trace,RagPipeline
    RagPipeline: ask(0),_step_recorder(1),_diagnostics_if_enabled(3),_retriever_result(3),_exception_payload(1),_fallback_payload_if_needed(1),_llm_error_payload(1),_empty_result_payload(1),_failure_payload(0)
    _result_with_trace(result)
  services/orchestrator/app/rag/__init__.py:
  services/orchestrator/app/rag/chunking.py:
    e: chunk_text,_overlapping_chunks
    chunk_text(text)
    _overlapping_chunks(text)
  services/orchestrator/app/rag/indexer.py:
    e: _chunks_for_body,_packed_chunks,_indexed_result,_failed_result,RagIndexer
    RagIndexer: __init__(3),ingest_resource(0),_fetch_body(1),_embed_chunks(1)  # Ingest zasobu po rejestracji — fetch → chunk → embed → store
    _chunks_for_body(body)
    _packed_chunks(chunks;embeddings)
    _indexed_result(resource_id;chunks;embedding_model)
    _failed_result(resource_id;exc)
  services/orchestrator/app/rag/openrouter.py:
    e: normalize_openrouter_model,_chat_response_error,_chat_result,OpenRouterClient
    OpenRouterClient: __init__(1),configured(0),_headers(0),embed(1),chat(1),_post_chat(3),health(0)  # Klient OpenRouter — embeddings i chat (LLM_MODEL z .env).
    normalize_openrouter_model(model)
    _chat_response_error(response)
    _chat_result(payload)
  services/orchestrator/app/rag/retriever.py:
    e: _no_hits_answer,_unconfigured_answer,_context_from_hits,_rag_messages,_fragment_fallback_answer,RagRetriever
    RagRetriever: __init__(2),search(1),ask(1)
    _no_hits_answer(query;llm_model)
    _unconfigured_answer(query;hits)
    _context_from_hits(hits)
    _rag_messages(context;query)
    _fragment_fallback_answer(hits;llm_error)
  services/orchestrator/app/rag/store.py:
    e: _cosine,_same_dimension_vectors,_vector_norm,_vector_hits,_ranked_hits,_query_tokens,_keyword_hits,_keyword_score,_parse_embedding,_row_dict,_chunk_hit,RagStore
    RagStore: __init__(1),upsert_document_pending(0),mark_indexed(0),mark_failed(0),replace_chunks(0),list_documents(0),search(1),_vector_search(1),_fts_search(1),_keyword_fallback(1)
    _cosine(a;b)
    _same_dimension_vectors(a;b)
    _vector_norm(values)
    _vector_hits(rows;query_embedding)
    _ranked_hits(rows)
    _query_tokens(query)
    _keyword_hits(rows;tokens)
    _keyword_score(row;tokens)
    _parse_embedding(row)
    _row_dict(row)
    _chunk_hit(row;score)
  services/orchestrator/tests/__init__.py:
  services/orchestrator/tests/conftest.py:
  services/orchestrator/tests/fakes.py:
    e: FakeEventStore,FakeMessageBus
    FakeEventStore: __init__(0),append(3),get_events_for_aggregate(2),get_aggregate_ids(1)
    FakeMessageBus: __init__(0),publish(2)
  services/orchestrator/tests/test_api.py:
    e: client,test_create_task_endpoint_dispatches_command,test_generic_command_envelope_endpoint,test_get_task_query_returns_reconstructed_state,test_get_task_query_returns_404,StubCommandBus,StubEventStore
    StubCommandBus: __init__(0),handle(0),handle_envelope(1)
    StubEventStore: get_events_for_aggregate(2),get_aggregate_ids(1)
    client()
    test_create_task_endpoint_dispatches_command(client)
    test_generic_command_envelope_endpoint(client)
    test_get_task_query_returns_reconstructed_state(client)
    test_get_task_query_returns_404(client)
  services/orchestrator/tests/test_command_bus.py:
    e: test_command_bus_creates_assigns_and_completes_task,test_command_bus_registers_agent
    test_command_bus_creates_assigns_and_completes_task()
    test_command_bus_registers_agent()
  services/orchestrator/tests/test_observability.py:
    e: test_classify_llm_unavailable,test_classify_empty_sources,test_classify_grounding,test_classify_backend_500,test_format_logs_text_keeps_observability_sections,test_build_bundle_uses_expanded_log_limit,test_incident_event_plan_includes_diagnostics_and_remediation,test_event_payload_adds_diagnostics_details
    test_classify_llm_unavailable()
    test_classify_empty_sources()
    test_classify_grounding()
    test_classify_backend_500()
    test_format_logs_text_keeps_observability_sections()
    test_build_bundle_uses_expanded_log_limit()
    test_incident_event_plan_includes_diagnostics_and_remediation()
    test_event_payload_adds_diagnostics_details()
  services/orchestrator/tests/test_task_aggregate.py:
    e: test_task_rehydrates_from_domain_events,test_task_cannot_complete_before_assignment
    test_task_rehydrates_from_domain_events()
    test_task_cannot_complete_before_assignment()
  services/projector/app/__init__.py:
  services/projector/app/db.py:
    e: Database
    Database: __init__(1),connect(0),disconnect(0),execute(1),fetch(1),_run_schema_migrations(0)
  services/projector/app/main.py:
    e: lifespan,health_check,operational_feed,task_board,agent_fleet,approval_requests,plugin_catalog,rag_documents,incident_feed,service_health,remediation_history,rag_quality_board,resource_registry,workflow_versions,_row_to_dict
    lifespan(app)
    health_check()
    operational_feed(limit;offset)
    task_board(status;limit;offset)
    agent_fleet(status;limit;offset)
    approval_requests(status;limit;offset)
    plugin_catalog(status;limit;offset)
    rag_documents(limit;offset)
    incident_feed(status;limit;offset)
    service_health(limit;offset)
    remediation_history(limit;offset)
    rag_quality_board(limit;offset)
    resource_registry(limit;offset)
    workflow_versions(limit;offset)
    _row_to_dict(row)
  services/projector/app/projections/__init__.py:
  services/projector/app/projections/agent_fleet.py:
    e: project_agent_fleet,_handle_agent_registered,_handle_agent_heartbeat,_handle_task_assigned_to_agent,_handle_agent_marked_idle
    project_agent_fleet(db;event)
    _handle_agent_registered(db;payload;occurred_at)
    _handle_agent_heartbeat(db;payload;occurred_at)
    _handle_task_assigned_to_agent(db;payload;occurred_at)
    _handle_agent_marked_idle(db;payload;occurred_at)
  services/projector/app/projections/approval_requests.py:
    e: project_approval_requests
    project_approval_requests(db;event)
  services/projector/app/projections/dispatcher.py:
    e: project_event,_normalize_event,_event_payload,_event_occurred_at
    project_event(db;event)
    _normalize_event(event)
    _event_payload(event)
    _event_occurred_at(event)
  services/projector/app/projections/incidents.py:
    e: project_incidents,_handle_rag_request_failed,_handle_incident_detected,_handle_incident_classified,_handle_diagnostics_started,_handle_diagnostics_completed,_handle_remediation_started,_handle_remediation_finished,_handle_post_remediation_verification,_upsert_rag_quality,_upsert_service_health,_update_incident_status,_error_code,_checks_payload,_raw_checks,_checks_list_payload,_check_payload,_root_cause,_diagnostics_ok
    project_incidents(db;event)
    _handle_rag_request_failed(db;event)
    _handle_incident_detected(db;event)
    _handle_incident_classified(db;event)
    _handle_diagnostics_started(db;event)
    _handle_diagnostics_completed(db;event)
    _handle_remediation_started(db;event)
    _handle_remediation_finished(db;event)
    _handle_post_remediation_verification(db;event)
    _upsert_rag_quality(db;payload;occurred_at)
    _upsert_service_health(db)
    _update_incident_status(db;incident_id;status;occurred_at)
    _error_code(payload)
    _checks_payload(payload)
    _raw_checks(payload)
    _checks_list_payload(checks)
    _check_payload(item)
    _root_cause(payload)
    _diagnostics_ok(checks)
  services/projector/app/projections/operational_feed.py:
    e: project_operational_feed,_title_for,_summary_for
    project_operational_feed(db;event)
    _title_for(event_type;payload)
    _summary_for(event_type;payload)
  services/projector/app/projections/plugin_catalog.py:
    e: project_plugin_catalog
    project_plugin_catalog(db;event)
  services/projector/app/projections/resource_registry.py:
    e: project_resource_registry,_handle_resource_registered,_handle_transfer_requested,_handle_transfer_completed,_handle_transfer_failed
    project_resource_registry(db;event)
    _handle_resource_registered(db;payload;occurred_at)
    _handle_transfer_requested(db;payload;occurred_at)
    _handle_transfer_completed(db;payload;occurred_at)
    _handle_transfer_failed(db;payload;occurred_at)
  services/projector/app/projections/task_board.py:
    e: project_task_board,_handle_task_created,_handle_task_assigned,_handle_task_started,_handle_task_completed,_handle_task_failed,_update_status
    project_task_board(db;event)
    _handle_task_created(db;payload;event_type;occurred_at)
    _handle_task_assigned(db;payload;event_type;occurred_at)
    _handle_task_started(db;payload;event_type;occurred_at)
    _handle_task_completed(db;payload;event_type;occurred_at)
    _handle_task_failed(db;payload;event_type;occurred_at)
    _update_status(db;task_id;status;event_type;occurred_at)
  services/projector/app/projections/workflow_versions.py:
    e: project_workflow_versions
    project_workflow_versions(db;event)
  services/web/app/__init__.py:
  services/web/app/access_matrix.py:
    e: _matrix_path,_default_resources,_default_agents,_empty_agent_resource,_empty_human_agent,default_state,load_state,_load_raw_state,_apply_state_lists,_apply_state_matrices,_merge_bool_matrix,_merged_bool_row,_reindex_state,_reindex_matrix,_reindex_matrix_row,save_state,agent_may_access_resource,human_may_use_agent,diagnose_file_list_command
    _matrix_path()
    _default_resources()
    _default_agents()
    _empty_agent_resource(resources;agents)
    _empty_human_agent(agents;humans)
    default_state()
    load_state()
    _load_raw_state(path)
    _apply_state_lists(base;raw)
    _apply_state_matrices(base;raw)
    _merge_bool_matrix(base;patch)
    _merged_bool_row(base_row;patch_row)
    _reindex_state(state)
    _reindex_matrix(matrix)
    _reindex_matrix_row(row)
    save_state(state)
    agent_may_access_resource(agent_id;resource_id)
    human_may_use_agent(human_id;agent_id)
    diagnose_file_list_command()
  services/web/app/agent_plugins/__init__.py:
  services/web/app/agent_plugins/nlp2cmd_plugin.py:
    e: backend_candidates,_translation_from_response,Nlp2CmdPlugin
    Nlp2CmdPlugin: health(0),translate_shell(1),analyze_shell_nl(1)
    backend_candidates()
    _translation_from_response(data)
  services/web/app/agent_plugins/nlp2dsl_plugin.py:
    e: Nlp2DslPlugin
    Nlp2DslPlugin: health(0),translate_shell(1)
  services/web/app/agent_plugins/protocol.py:
    e: ShellTranslation,AgentPlugin
    ShellTranslation: from_validated_analysis(2)  # Wynik tłumaczenia NL → polecenie shell (bez wykonania).
    AgentPlugin: plugin_id(0),title(0),executor_agent_id(0),ingress_steps(0),route_kinds(0),health(0),translate_shell(1)  # Plugin łączący Mullm z usługą agenta (HTTP/CLI w sibling rep
  services/web/app/agent_plugins/registry.py:
    e: bootstrap,list_plugins,get_plugin,plugins_for_ingress_step,agents_status,analyze_shell_nl,translate_shell_nl
    bootstrap()
    list_plugins()
    get_plugin(plugin_id)
    plugins_for_ingress_step(step)
    agents_status()
    analyze_shell_nl(message)
    translate_shell_nl(message)
  services/web/app/agent_workroom.py:
    e: create_workroom,get_workroom,_plan_steps,_build_file_list_for_goal,format_workroom_export,_workroom_export_header,_append_workroom_thread,_append_workroom_ledger,_append_workroom_result,_extract_shell,run_workroom,_reset_workroom,_start_plan,_workspace_scope,_run_workroom_step,_run_analyze_workroom_step,_run_files_workroom_step,_run_shell_workroom_step,_run_summarize_workroom_step,_run_analyze_step,_run_files_step,_add_permission,_record_file_list_result,_register_file_list_artifact,_run_shell_step,_record_shell_result,_run_summarize_step,_finish_workroom,workroom_catalog,LedgerEntry,WorkroomSession
    LedgerEntry: to_dict(0)
    WorkroomSession: add_ledger(3),agent_say(3),to_dict(0)
    create_workroom()
    get_workroom(workroom_id)
    _plan_steps(goal)
    _build_file_list_for_goal(goal)
    format_workroom_export(session)
    _workroom_export_header(session)
    _append_workroom_thread(lines;agent_thread)
    _append_workroom_ledger(lines;ledger)
    _append_workroom_result(lines;result_summary)
    _extract_shell(text)
    run_workroom(workroom_id;user_message)
    _reset_workroom(session;user_message)
    _start_plan(session;user_message)
    _workspace_scope(session)
    _run_workroom_step(session;step;user_message)
    _run_analyze_workroom_step(session;step;user_message)
    _run_files_workroom_step(session;step;user_message)
    _run_shell_workroom_step(session;step;user_message)
    _run_summarize_workroom_step(session;step;user_message)
    _run_analyze_step(session)
    _run_files_step(session;step;user_message)
    _add_permission(session;agent_id;summary;status;perm)
    _record_file_list_result(session;reply;scope_kind)
    _register_file_list_artifact(session;reply;inventory;scope_kind;user_message)
    _run_shell_step(session;user_message)
    _record_shell_result(session;result;wait_for_confirmation)
    _run_summarize_step(session)
    _finish_workroom(session;final_parts)
    workroom_catalog()
  services/web/app/api/__init__.py:
  services/web/app/api/access_routes.py:
    e: api_resource_areas,api_role_scopes,access_matrix_get,access_matrix_put,access_matrix_reset,access_diagnose_file_list
    api_resource_areas()
    api_role_scopes()
    access_matrix_get()
    access_matrix_put(body)
    access_matrix_reset()
    access_diagnose_file_list()
  services/web/app/api/agents_routes.py:
    e: agents_status_get
    agents_status_get()
  services/web/app/api/chat_routes.py:
    e: start_chat_session,get_chat_session,workspace_state,chat_message,_form_only_message,_form_only_chat_message,_update_nlp_conversation,task_draft,context_attach,context_clear_tickets,upload_files,_upload_one_file,board_snapshot
    start_chat_session(body)
    get_chat_session(session_id)
    workspace_state(session_id)
    chat_message(body)
    _form_only_message(body)
    _form_only_chat_message(session;body)
    _update_nlp_conversation(session;outcome)
    task_draft(body)
    context_attach(body)
    context_clear_tickets(body)
    upload_files(session_id;files;classification)
    _upload_one_file(client;upload)
    board_snapshot()
  services/web/app/api/config.py:
  services/web/app/api/feedback_routes.py:
    e: routing_feedback_post,routing_feedback_list,routing_learnings,routing_improvements
    routing_feedback_post(body)
    routing_feedback_list(session_id;limit)
    routing_learnings(limit)
    routing_improvements(status;limit)
  services/web/app/api/models.py:
    e: ChatSessionStart,ChatMessage,TaskDraftRequest,CreateTaskBody,CreateFromDraftBody,ConfirmTicketBody,SessionRef,ContextAttachBody,WorkroomStart,WorkroomMessage,RoutingFeedbackBody,AccessMatrixBody
    ChatSessionStart:
    ChatMessage:
    TaskDraftRequest:
    CreateTaskBody:
    CreateFromDraftBody:
    ConfirmTicketBody:
    SessionRef:
    ContextAttachBody:
    WorkroomStart:
    WorkroomMessage:
    RoutingFeedbackBody:
    AccessMatrixBody:
  services/web/app/api/router_routes.py:
    e: router_decide,routing_schemas_get,ticket_schemas_get,routing_policy_get,routing_explain,routing_trace_last
    router_decide(message;mode;use_rag)
    routing_schemas_get()
    ticket_schemas_get()
    routing_policy_get(reload)
    routing_explain(message;mode;use_rag;session_id)
    routing_trace_last(session_id)
  services/web/app/api/task_routes.py:
    e: create_task,create_task_from_draft,create_and_run_task,list_tickets,ticket_statuses,get_ticket,confirm_ticket,archive_ticket,link_ticket,unlink_ticket,_archived_ids,_filter_tickets_view,_is_archived_ticket,_is_active_ticket,_confirmable_task_and_agent,_task_from_board,_assert_confirmable_task,_first_idle_agent_id,_assign_ticket
    create_task(body)
    create_task_from_draft(body)
    create_and_run_task(body)
    list_tickets(session_id;view)
    ticket_statuses()
    get_ticket(task_id;session_id)
    confirm_ticket(task_id;body)
    archive_ticket(task_id;body)
    link_ticket(task_id;body)
    unlink_ticket(task_id;body)
    _archived_ids(session_id)
    _filter_tickets_view(items;view)
    _is_archived_ticket(item)
    _is_active_ticket(item)
    _confirmable_task_and_agent(task_id)
    _task_from_board(board;task_id)
    _assert_confirmable_task(task)
    _first_idle_agent_id(board)
    _assign_ticket(task_id;agent_id;shell)
  services/web/app/api/workroom_routes.py:
    e: workroom_start,workroom_get,workroom_export,workroom_run,_workroom_or_404
    workroom_start(body)
    workroom_get(workroom_id)
    workroom_export(workroom_id)
    workroom_run(workroom_id;body)
    _workroom_or_404(workroom_id)
  services/web/app/api/workspace_routes.py:
    e: workspace_list_artifacts,workspace_get_artifact,workspace_file_list_export,workspace_chat_export,workspace_logs_export
    workspace_list_artifacts(session_id)
    workspace_get_artifact(session_id;artifact_id)
    workspace_file_list_export(session_id;message;scope)
    workspace_chat_export(session_id)
    workspace_logs_export(session_id;limit)
  services/web/app/api_routes.py:
  services/web/app/chat.py:
    e: _orch,_projector,is_continue_intent,is_file_list_intent,is_shell_nl_intent,_has_list_word,_looks_like_misspelled_file_list,_has_polish_file_list_words,_has_english_file_list_words,_has_user_files_phrase,file_list_scope,_system_scope_requested,_user_scope_requested,_rag_scope_requested,_session_scope_requested,_uri_is_user_resource,_uri_is_system_resource,filter_file_inventory,_filtered_resources,_filter_rows_by_scope,_rows_matching_uri,_rows_in_session_scope,_dedupe_rows_by_uri,_row_dedupe_key,fetch_file_inventory,_fetch_inventory_rows,format_file_list_reply,_safe_list,_list_scope_value,_append_session_files,_append_uploaded_session_files,_get_user_context_parts,_append_tickets_context,_append_other_context,_append_user_context_only,_append_scope_uris,_format_scope_uri,_append_resource_rows,_format_resource_row,_empty_resource_hint,_append_rag_rows,_rag_rows_label,_format_rag_doc_row,_append_file_list_errors,_append_file_list_tip,build_file_list_artifact,new_session_id,get_history,_append,stamp_last_assistant_routing,_format_history,_format_incident,_incident_detail_parts,_incident_message_part,_incident_trace_part,_incident_correlation_part,_incident_fallback_part,handle_message,_file_list_answer,probe_rag,_ask_rag,_rag_headers,_rag_query,_answer_from_rag_payload,_sources_fallback_answer,_source_preview,_rag_backend_fallback,_rag_search_fallback,_rag_unavailable_answer,_rag_diagnostics_hint,_default_chat_reply,_message_response,_response_intent,_attach_inventory_response,_attach_trace_response,fetch_task_state,_fetch_task_from_projector,wait_for_task_terminal,create_task,_task_create_payload,_apply_task_agent,_apply_task_shell
    _orch()
    _projector()
    is_continue_intent(message)
    is_file_list_intent(message)
    is_shell_nl_intent(message)
    _has_list_word(text)
    _looks_like_misspelled_file_list(text)
    _has_polish_file_list_words(text)
    _has_english_file_list_words(text)
    _has_user_files_phrase(text)
    file_list_scope(message)
    _system_scope_requested(text)
    _user_scope_requested(text)
    _rag_scope_requested(text)
    _session_scope_requested(text)
    _uri_is_user_resource(uri)
    _uri_is_system_resource(uri)
    filter_file_inventory(inventory;list_scope)
    _filtered_resources(resources;list_scope;scope_uris)
    _filter_rows_by_scope(rows;list_scope;scope_uris)
    _rows_matching_uri(rows;predicate)
    _rows_in_session_scope(rows;scope_uris)
    _dedupe_rows_by_uri(rows)
    _row_dedupe_key(row)
    fetch_file_inventory()
    _fetch_inventory_rows(client;url;label;errors)
    format_file_list_reply(inventory)
    _safe_list(value)
    _list_scope_value(inventory;list_scope)
    _append_session_files(lines;list_scope;scope_files;scope_uris)
    _append_uploaded_session_files(lines;scope_files)
    _get_user_context_parts(scope_uris)
    _append_tickets_context(lines;tickets)
    _append_other_context(lines;other)
    _append_user_context_only(lines;list_scope;scope_uris)
    _append_scope_uris(lines;list_scope;scope_uris)
    _format_scope_uri(uri)
    _append_resource_rows(lines;list_scope;resources)
    _format_resource_row(index;row)
    _empty_resource_hint(list_scope)
    _append_rag_rows(lines;list_scope;rag_docs)
    _rag_rows_label(list_scope)
    _format_rag_doc_row(index;doc)
    _append_file_list_errors(lines;errors)
    _append_file_list_tip(lines;list_scope;resources;scope_files)
    build_file_list_artifact(reply_text;inventory)
    new_session_id()
    get_history(session_id)
    _append(session_id;role;content)
    stamp_last_assistant_routing(session_id;routing)
    _format_history(session_id)
    _format_incident(payload)
    _incident_detail_parts(payload;incident)
    _incident_message_part(payload;incident)
    _incident_trace_part(payload;incident)
    _incident_correlation_part(payload;incident)
    _incident_fallback_part(payload;incident)
    handle_message()
    _file_list_answer(message)
    probe_rag()
    _ask_rag()
    _rag_headers(session_id)
    _rag_query(session_id;message)
    _answer_from_rag_payload(payload;sources)
    _sources_fallback_answer(payload;sources)
    _source_preview(source)
    _rag_backend_fallback(client)
    _rag_search_fallback(client;message)
    _rag_unavailable_answer(client;headers;status_code)
    _rag_diagnostics_hint(client;headers)
    _default_chat_reply()
    _message_response()
    _response_intent(inventory;use_rag)
    _attach_inventory_response(out;answer;inventory;session_id)
    _attach_trace_response(out;last_payload)
    fetch_task_state(task_id)
    _fetch_task_from_projector(task_id)
    wait_for_task_terminal(task_id)
    create_task()
    _task_create_payload()
    _apply_task_agent(payload;agent_id)
    _apply_task_shell(payload;shell_command;wait_for_confirmation;agent_id)
  services/web/app/conductor.py:
    e: _merge_nlp2dsl_routing,_attach_routing,_enrich_decision,_rag_answer_turn,_execute_rules_route,_execute_file_list_route,_execute_shell_route,_missing_shell_response,_shell_wait_seconds,_create_shell_task,_translation_from_policy_flags,_apply_nlp2cmd_decision,_shell_route_response,_shell_task_reply,_format_shell_terminal,_execute_rag_route,handle_turn,_message_with_form_values,_attach_decision_tree,_should_interrupt_nlp2dsl_resume,_nlp2dsl_orient_step,_nlp2dsl_resume_step,_run_ingress_pipeline,_rag_probe_step,_rag_probe_enabled,_rag_probe_should_answer,_rag_probe_answer,_should_skip_rag_probe,_nlp2dsl_continue_decision,_mullm_continue_clarify_decision,_continue_clarify_reply,_try_continue_turn,_rag_probe_decision,_rules_step,_should_skip_nlp2dsl_step,_nlp2cmd_ingress_decision,_agent_shell_step,_nlp2dsl_step,_rag_answer_step,_rag_pipeline_decision,_fallback_routed_turn,_decide_default_route,_nlp2dsl_turn,_nlp2dsl_status_turn,_call_nlp2dsl,_nlp_output_base,_in_progress_turn,_ready_turn,_ready_action_payload,_system_file_list_payload,_shell_task_payload,_shell_clarify_payload,_ticket_payload,_task_reply,_closed_turn,_append_turn,_mullm_file_list_turn,_fallback_turn,_local_clarify,_extract_shell,TurnState
    TurnState:
    _merge_nlp2dsl_routing(out;nlp_routing;decision)
    _attach_routing(session_id;out;decision)
    _enrich_decision(decision;session_id)
    _rag_answer_turn()
    _execute_rules_route()
    _execute_file_list_route()
    _execute_shell_route()
    _missing_shell_response(session_id;decision)
    _shell_wait_seconds()
    _create_shell_task(session_id)
    _translation_from_policy_flags(decision)
    _apply_nlp2cmd_decision(decision;translation)
    _shell_route_response(session_id;message;decision;result)
    _shell_task_reply(result;agent)
    _format_shell_terminal(state)
    _execute_rag_route()
    handle_turn()
    _message_with_form_values(message;form_values)
    _attach_decision_tree(out)
    _should_interrupt_nlp2dsl_resume(state)
    _nlp2dsl_orient_step(state)
    _nlp2dsl_resume_step(state)
    _run_ingress_pipeline(state)
    _rag_probe_step(state)
    _rag_probe_enabled(state)
    _rag_probe_should_answer(state;hits)
    _rag_probe_answer(state)
    _should_skip_rag_probe(state)
    _nlp2dsl_continue_decision()
    _mullm_continue_clarify_decision()
    _continue_clarify_reply(state)
    _try_continue_turn(state)
    _rag_probe_decision()
    _rules_step(state)
    _should_skip_nlp2dsl_step(state)
    _nlp2cmd_ingress_decision(translation)
    _agent_shell_step(state)
    _nlp2dsl_step(state)
    _rag_answer_step(state)
    _rag_pipeline_decision()
    _fallback_routed_turn(state)
    _decide_default_route(state)
    _nlp2dsl_turn()
    _nlp2dsl_status_turn()
    _call_nlp2dsl(nlp_conversation_id;message)
    _nlp_output_base(cid;status)
    _in_progress_turn(session_id;message;resp;cid;status;assistant)
    _ready_turn()
    _ready_action_payload(action)
    _system_file_list_payload(session_id;message;scope_files;scope_uris)
    _shell_task_payload(session_id;message;cfg;cid;wait_for_confirmation)
    _shell_clarify_payload(cid)
    _ticket_payload(session_id;message;cfg;wait_for_confirmation)
    _task_reply(result)
    _closed_turn(session_id;message;cid;status;assistant)
    _append_turn(session_id;message;out)
    _mullm_file_list_turn()
    _fallback_turn()
    _local_clarify(message)
    _extract_shell(text)
  services/web/app/local_orient.py:
    e: _has_registry_hint,_has_host_hint,_is_file_list_query,_file_list_scope,orient_query,OrientationResult
    OrientationResult: to_dict(0)
    _has_registry_hint(text)
    _has_host_hint(text)
    _is_file_list_query(text)
    _file_list_scope(text)
    orient_query(text)
  services/web/app/main.py:
    e: health,workspace_home,agent_workroom_page,access_matrix_page,dashboard
    health()
    workspace_home(request;task_id)
    agent_workroom_page(request)
    access_matrix_page(request)
    dashboard(request)
  services/web/app/nlp2dsl_bridge.py:
    e: backend_url,backend_candidates,health,chat_start,chat_message,orient,nlp_service_candidates,orient_direct,_post_json,form_to_prompt,primary_action,step_config,routing_from_response,intent_routing_policy_flags,merge_intent_into_policy_flags
    backend_url()
    backend_candidates()
    health()
    chat_start(text)
    chat_message(conversation_id;text)
    orient(text)
    nlp_service_candidates()
    orient_direct(text)
    _post_json(path;payload)
    form_to_prompt(form;values)
    primary_action(dsl)
    step_config(dsl)
    routing_from_response(resp)
    intent_routing_policy_flags(routing)
    merge_intent_into_policy_flags(policy_flags;routing)
  services/web/app/planfile_bridge.py:
    e: planfile_sync_enabled,planfile_project_path,sync_improvement_ticket,_build_create_cmd,_improvement_files,_parse_created_id
    planfile_sync_enabled()
    planfile_project_path()
    sync_improvement_ticket(ticket)
    _build_create_cmd(ticket)
    _improvement_files(ticket)
    _parse_created_id(stdout)
  services/web/app/prompt_router.py:
    e: _candidate,_build_decision,_shell_prefix,decide_route_rules,_router_flags,_empty_route_decision,_direct_route_decision,_default_route_decision,_mode_route_decision,_file_list_route_decision,_shell_route_decision,_shell_nl_route_decision,_default_discuss_decision,_fallback_mode_decision,decide_route_llm,_llm_classifier_data,_llm_classifier_payload,_normalize_router_model,_extract_llm_json,_llm_decision_from_data,_llm_route,_explicit_registry_list,_registry_scope_requested,_host_filesystem_list_requested,_command_looks_like_host_list,_nlp2cmd_min_confidence,_routing_use_nlp2cmd,_local_min_confidence,_local_confidence_sufficient,_match_expectations_local,_decision_from_expectations,_safe_analyze_shell_nl,_gather_local_analyses,_pick_local_winner,_resolve_local_decision,_decision_from_nlp2cmd,_should_prefer_nlp2cmd_over_rules,_resolve_router_mode,decide_route_local_first,decide_route_hybrid,decide_route,_merged_llm_decision,record_route_event,RouteDecision
    RouteDecision: to_dict(0)  # Audytowalna decyzja routingu (ingress Mullm BFF).
    _candidate(route;handler;intent;confidence;reason_codes)
    _build_decision(chosen)
    _shell_prefix(message)
    decide_route_rules(message)
    _router_flags(chat_mode;use_rag;policy_flags)
    _empty_route_decision(flags)
    _direct_route_decision(chat_mode;text;flags)
    _default_route_decision(chat_mode;flags)
    _mode_route_decision(chat_mode;flags)
    _file_list_route_decision(text;flags)
    _shell_route_decision(text;flags)
    _shell_nl_route_decision(text;flags)
    _default_discuss_decision(flags)
    _fallback_mode_decision(chat_mode;flags)
    decide_route_llm(message)
    _llm_classifier_data(api_key;model;message)
    _llm_classifier_payload(model;message)
    _normalize_router_model(model)
    _extract_llm_json(content)
    _llm_decision_from_data(data)
    _llm_route(route)
    _explicit_registry_list(message)
    _registry_scope_requested(message)
    _host_filesystem_list_requested(message)
    _command_looks_like_host_list(command)
    _nlp2cmd_min_confidence()
    _routing_use_nlp2cmd()
    _local_min_confidence()
    _local_confidence_sufficient(decision)
    _match_expectations_local(message)
    _decision_from_expectations(message;expectations;rules)
    _safe_analyze_shell_nl(message)
    _gather_local_analyses(message)
    _pick_local_winner(pool)
    _resolve_local_decision(message)
    _decision_from_nlp2cmd(message;translation)
    _should_prefer_nlp2cmd_over_rules(message;translation;rules)
    _resolve_router_mode()
    decide_route_local_first(message)
    decide_route_hybrid(message)
    decide_route(message)
    _merged_llm_decision(rules;llm)
    record_route_event(session_id;decision)
  services/web/app/resource_areas.py:
    e: list_areas,list_groups,agent_may_access,_area_policy_decision,_matrix_access_decision
    list_areas()
    list_groups()
    agent_may_access(role_id;area_id;action)
    _area_policy_decision(policy;area_id;action)
    _matrix_access_decision(role_id;area_id;action)
  services/web/app/routing/__init__.py:
  services/web/app/routing/decision.py:
    e: OrientationDecision
    OrientationDecision: from_dict(2),to_dict(0),is_actionable(0),shell_translation_source(0)
  services/web/app/routing/execution_resolver.py:
    e: route_from_orientation
    route_from_orientation(orient)
  services/web/app/routing/ingress_cache.py:
    e: _normalize_text,cache_key,get_cached_orient,set_cached_orient,clear_cache
    _normalize_text(text)
    cache_key(session_id;message)
    get_cached_orient(session_id;message)
    set_cached_orient(session_id;message;orient)
    clear_cache()
  services/web/app/routing/orientation_provider.py:
    e: _orient_remote,_orient_timeout,orient_message
    _orient_remote(text)
    _orient_timeout()
    orient_message(text)
  services/web/app/routing_feedback.py:
    e: feedback_dir,_feedback_path,_improvements_path,_now_iso,_find_turn_context,_resolve_feedback_inputs,_build_feedback_tags,record_feedback,_create_improvement_ticket,_maybe_sync_planfile,_suggest_actions,list_feedback,list_improvement_tickets,aggregate_learnings,_append_jsonl,_read_jsonl_tail,new_turn_id,RoutingFeedbackRecord
    RoutingFeedbackRecord: to_dict(0)
    feedback_dir()
    _feedback_path()
    _improvements_path()
    _now_iso()
    _find_turn_context(session_id;turn_id)
    _resolve_feedback_inputs(session_id;turn_id;user_message;routing;decision_tree)
    _build_feedback_tags(rating;actual_route;expected_route;improvement_notes;tags)
    record_feedback()
    _create_improvement_ticket()
    _maybe_sync_planfile(ticket)
    _suggest_actions()
    list_feedback()
    list_improvement_tickets()
    aggregate_learnings()
    _append_jsonl(path;obj)
    _read_jsonl_tail(path)
    new_turn_id()
  services/web/app/routing_policy.py:
    e: _policy_path,_parse_policy,_parse_user_expectations,_parse_agents,_valid_ingress_order,_parse_mode_overrides,_valid_override_steps,_parse_rag_probe,load_policy,RagProbeSettings,RoutingPolicy
    RagProbeSettings:
    RoutingPolicy: ingress_for_mode(1),agent_for_route(1),to_dict(0)
    _policy_path()
    _parse_policy(data;path)
    _parse_user_expectations(raw)
    _parse_agents(raw_agents)
    _valid_ingress_order(raw_order)
    _parse_mode_overrides(overrides)
    _valid_override_steps(spec)
    _parse_rag_probe(raw)
    load_policy()
  services/web/app/routing_schemas.py:
    e: routing_analysis_use_explain,build_nlp2cmd_request,parse_nlp2cmd_response,parse_llm_classifier,llm_classifier_json_schema,llm_system_prompt_with_schema,schemas_bundle,Nlp2CmdQueryRequest,Nlp2CmdQueryResponse,LlmRouteClassifierOutput,NlpCommandAnalysis
    Nlp2CmdQueryRequest:  # Zgodne z nlp2cmd.service.QueryRequest.
    Nlp2CmdQueryResponse: command_text(0)  # Zgodne z nlp2cmd.service.QueryResponse.
    LlmRouteClassifierOutput:  # JSON z OpenRouter (PROMPT_ROUTER_MODE llm/hybrid).
    NlpCommandAnalysis: to_shell_translation(0),to_policy_flags(0)  # Walidowany wynik analizy NL (nlp2cmd) używany przez router M
    routing_analysis_use_explain()
    build_nlp2cmd_request(message)
    parse_nlp2cmd_response(data)
    parse_llm_classifier(data)
    llm_classifier_json_schema()
    llm_system_prompt_with_schema()
    schemas_bundle()
  services/web/app/routing_trace.py:
    e: new_trace,append_step,_is_expectation_hit,match_user_expectations,_node_empty,_node_mode_override,_node_continue,_node_file_list,_node_shell_prefix,_node_shell_nl,_node_default_discuss,build_rules_rule_nodes,_file_list_checks,_default_principles,explain_pipeline,_build_rag_probe_checks,_check_rag_probe_skipped,_evaluate_rag_probe_hits,_explain_rag_probe,_explain_rules_step,_explain_agent_shell,_explain_nlp2dsl,_explain_rag_answer,_orient_category_to_route,align_tree_to_route,record_live_step,TraceCheck,TraceStep,DecisionTree
    TraceCheck: to_dict(0)
    TraceStep: to_dict(0)
    DecisionTree: to_dict(0)
    new_trace()
    append_step(trace;step)
    _is_expectation_hit(text;spec)
    match_user_expectations(message;policy)
    _node_empty(passed)
    _node_mode_override(chat_mode;passed)
    _node_continue()
    _node_file_list(text;file_list)
    _node_shell_prefix(shell_prefix)
    _node_shell_nl(shell_nl)
    _node_default_discuss()
    build_rules_rule_nodes(message)
    _file_list_checks(text)
    _default_principles()
    explain_pipeline(message)
    _build_rag_probe_checks(use_rag;rp;skip_file;skip_shell;skip_nl)
    _check_rag_probe_skipped(use_rag;rp;skip_file;skip_shell;skip_nl;checks)
    _evaluate_rag_probe_hits(rp;hits;checks)
    _explain_rag_probe(text)
    _explain_rules_step(text)
    _explain_agent_shell(text)
    _explain_nlp2dsl(text)
    _explain_rag_answer()
    _orient_category_to_route(category)
    align_tree_to_route(tree;actual_route)
    record_live_step(trace)
  services/web/app/ticket_schemas.py:
    e: schemas_bundle,MullmTicketRef,ExecutionTicketCreate,ImprovementTicket,WorkflowTicketRef
    MullmTicketRef:  # Wspólny nagłówek odniesienia (URI + źródło).
    ExecutionTicketCreate:  # POST orchestrator /api/commands/tasks (CreateTask).
    ImprovementTicket: planfile_title(0),planfile_description(0),planfile_labels(0)  # mullm.routing.improvement_ticket.v1 (routing feedback).
    WorkflowTicketRef:  # nlp2dsl — rozmowa workflow (nie UUID orchestratora).
    schemas_bundle()
  services/web/app/tickets.py:
    e: ticket_uri,ticket_web_path,status_meta,enrich_task
    ticket_uri(task_id)
    ticket_web_path(task_id)
    status_meta(status)
    enrich_task(row)
  services/web/app/workspace.py:
    e: _orch,_projector,new_session,get_session,get_or_create,_artifact_title,register_artifact,artifact_summaries,get_artifact,workspace_state,attach_context,_apply_context_scalars,_append_unique,_extract_ticket,_extract_shell_command,build_task_payload,propose_task_draft,create_task_immediate,_resolved_task_agent,handle_chat_message,_attach_ticket_context,_dispatch_chat_mode,_create_task_from_message,_task_chat_outcome,_task_result_reply,_search_context_outcome,_conductor_outcome,_record_chat_outcome,_register_outcome_artifact,_record_file_list_event,_record_rag_trace_event,_record_rag_incident_event,_record_task_outcome,_chat_response,create_task_from_draft,create_and_run,format_chat_export_text,_append_chat_export_message,_append_chat_export_trace,_append_chat_export_draft,clamp_log_export_limit,export_debug_logs,_debug_export_base,_attach_orchestrator_debug_export,_merge_orchestrator_debug_payload,_attach_operational_feed,_filter_operational_feed,_format_export_text,_export_header,_append_export_sections,_list_section,_dict_section,_visible_log_limit,_nfo_package_version,_emit_nfo_event,_build_nfo_package,_nfo_counts,_nfo_errors,_append_nfo_section,_append_orchestrator_error,_trace_event_row,_trace_message_row,_routing_fingerprint,_append_context_section,_append_context_scalars,_append_context_collections,_append_inventory_section,_append_resource_inventory,_append_rag_inventory,_append_history_section,_append_history_message,_format_routing_line,_routing_base_parts,_routing_optional_parts,_routing_fallback_parts,_routing_shell_plugin_parts,_routing_nlp2dsl_parts,_append_routing_trace_section,_append_routing_trace_decision,_append_candidate_routes,_format_candidate_route,_collect_routing_trace,_append_unique_trace_row,_append_draft_section,_append_session_events_section,_event_extra,_event_extra_parts,_routing_event_extra,_append_rag_health_section,_append_incidents_section,_append_rag_snapshots_section,_session_rag_snapshots,_append_operational_feed_section,archive_task,link_ticket,unlink_ticket,clear_ticket_uris,fetch_live_board,WorkspaceContext,WorkspaceSession
    WorkspaceContext: to_dict(0)
    WorkspaceSession: add_event(2)
    _orch()
    _projector()
    new_session()
    get_session(session_id)
    get_or_create(session_id)
    _artifact_title(artifact)
    register_artifact(session;artifact)
    artifact_summaries(session)
    get_artifact(session_id;artifact_id)
    workspace_state(session_id)
    attach_context(session_id)
    _apply_context_scalars(ctx)
    _append_unique(items;value)
    _extract_ticket(text)
    _extract_shell_command(text)
    build_task_payload(session_id;message)
    propose_task_draft(session_id;message)
    create_task_immediate(session_id)
    _resolved_task_agent(session;agent_id;shell_command)
    handle_chat_message()
    _attach_ticket_context(session;message)
    _dispatch_chat_mode(session)
    _create_task_from_message(session;message)
    _task_chat_outcome(session;task_result;message;wait_for_confirmation)
    _task_result_reply(task_result;shell;wait_for_confirmation)
    _search_context_outcome(session;message;scope_files;scope_uris)
    _conductor_outcome(session)
    _record_chat_outcome(session;message)
    _register_outcome_artifact(session;message;outcome)
    _record_file_list_event(session;outcome)
    _record_rag_trace_event(session;outcome)
    _record_rag_incident_event(session;outcome)
    _record_task_outcome(session;task_result)
    _chat_response(session;outcome;task_result)
    create_task_from_draft(session_id)
    create_and_run(session_id)
    format_chat_export_text(session)
    _append_chat_export_message(lines;msg)
    _append_chat_export_trace(lines;trace)
    _append_chat_export_draft(lines;draft)
    clamp_log_export_limit(limit)
    export_debug_logs(session_id)
    _debug_export_base(session)
    _attach_orchestrator_debug_export(client;bundle)
    _merge_orchestrator_debug_payload(bundle;orch)
    _attach_operational_feed(client;bundle)
    _filter_operational_feed(items)
    _format_export_text(bundle)
    _export_header(bundle)
    _append_export_sections(lines;bundle;sess)
    _list_section(payload;key)
    _dict_section(payload;key)
    _visible_log_limit(bundle)
    _nfo_package_version()
    _emit_nfo_event(name)
    _build_nfo_package(bundle)
    _nfo_counts(bundle)
    _nfo_errors(bundle)
    _append_nfo_section(lines;nfo_package)
    _append_orchestrator_error(lines;bundle)
    _trace_event_row(ev;index)
    _trace_message_row(msg;assistant_index)
    _routing_fingerprint(routing)
    _append_context_section(lines;ctx)
    _append_context_scalars(lines;ctx)
    _append_context_collections(lines;ctx)
    _append_inventory_section(lines;inv)
    _append_resource_inventory(lines;resources)
    _append_rag_inventory(lines;rag_docs)
    _append_history_section(lines;history)
    _append_history_message(lines;msg)
    _format_routing_line(routing)
    _routing_base_parts(routing;route)
    _routing_optional_parts(routing;route)
    _routing_fallback_parts(routing;route)
    _routing_shell_plugin_parts(routing)
    _routing_nlp2dsl_parts(routing)
    _append_routing_trace_section(lines;history;events)
    _append_routing_trace_decision(lines;index;row)
    _append_candidate_routes(lines;candidates)
    _format_candidate_route(candidate)
    _collect_routing_trace(history;events)
    _append_unique_trace_row(trace;seen;item)
    _append_draft_section(lines;sess)
    _append_session_events_section(lines;events)
    _event_extra(ev)
    _event_extra_parts(ev)
    _routing_event_extra(ev)
    _append_rag_health_section(lines;rag)
    _append_incidents_section(lines;incidents)
    _append_rag_snapshots_section(lines;bundle)
    _session_rag_snapshots(bundle)
    _append_operational_feed_section(lines;feed)
    archive_task(session_id;task_id)
    link_ticket(session_id;task_id)
    unlink_ticket(session_id;task_id)
    clear_ticket_uris(session_id)
    fetch_live_board()
  services/web/tests/conftest.py:
    e: _deterministic_routing_env,fake_file_inventory,patch_file_inventory,patch_nlp2dsl_down,patch_nlp2cmd_translate,patch_shell_task
    _deterministic_routing_env(monkeypatch)
    fake_file_inventory()
    patch_file_inventory(monkeypatch;fake_file_inventory)
    patch_nlp2dsl_down(monkeypatch)
    patch_nlp2cmd_translate(monkeypatch)
    patch_shell_task(monkeypatch)
  services/web/tests/test_access_matrix.py:
    e: matrix_file,test_default_all_checked,test_save_and_deny,test_diagnose_file_list_no_shell
    matrix_file(monkeypatch)
    test_default_all_checked(matrix_file)
    test_save_and_deny(matrix_file)
    test_diagnose_file_list_no_shell()
  services/web/tests/test_agent_plugins.py:
    e: test_registry_lists_builtin_plugins,test_translation_from_response,test_translate_shell_nl_mocked,test_nlp2cmd_plugin_metadata
    test_registry_lists_builtin_plugins()
    test_translation_from_response()
    test_translate_shell_nl_mocked(monkeypatch)
    test_nlp2cmd_plugin_metadata()
  services/web/tests/test_agent_workroom.py:
    e: test_plan_includes_files_for_lista_plikow,test_list_aplikow_usera_intent_and_scope,_assert_user_file_step,test_workroom_export_contains_goal,test_files_agent_may_list_rag,test_mail_agent_denied_rag,test_groups_nonempty,test_workroom_session_dict,test_run_workroom_file_list_step
    test_plan_includes_files_for_lista_plikow()
    test_list_aplikow_usera_intent_and_scope()
    _assert_user_file_step(msg)
    test_workroom_export_contains_goal()
    test_files_agent_may_list_rag()
    test_mail_agent_denied_rag()
    test_groups_nonempty()
    test_workroom_session_dict()
    test_run_workroom_file_list_step(monkeypatch)
  services/web/tests/test_api_routes.py:
    e: test_api_router_keeps_public_workspace_paths
    test_api_router_keeps_public_workspace_paths(path)
  services/web/tests/test_artifacts.py:
    e: test_register_and_get_artifact,_register_user_file_list_artifact,_assert_single_artifact_summary,_assert_artifact_text,test_format_export_text_keeps_core_sections,test_format_export_text_uses_log_limit_for_verbose_sections,test_format_chat_export_includes_routing,test_format_export_includes_routing_trace,test_format_routing_line_nlp2dsl_skipped
    test_register_and_get_artifact()
    _register_user_file_list_artifact(session)
    _assert_single_artifact_summary(session)
    _assert_artifact_text(session;artifact_id;expected)
    test_format_export_text_keeps_core_sections()
    test_format_export_text_uses_log_limit_for_verbose_sections()
    test_format_chat_export_includes_routing()
    test_format_export_includes_routing_trace()
    test_format_routing_line_nlp2dsl_skipped()
  services/web/tests/test_chat_intent.py:
    e: test_file_list_intent_pl,test_format_file_list,test_file_list_intent_aplikow_typo,test_file_list_intent_en_and_pikow,test_file_list_scope_usera,test_filter_user_files,test_file_list_artifact,test_format_user_scope_title,test_dedupe_rag_documents_by_uri,test_handle_message_file_list_builds_artifact
    test_file_list_intent_pl()
    test_format_file_list()
    test_file_list_intent_aplikow_typo()
    test_file_list_intent_en_and_pikow()
    test_file_list_scope_usera()
    test_filter_user_files()
    test_file_list_artifact()
    test_format_user_scope_title()
    test_dedupe_rag_documents_by_uri()
    test_handle_message_file_list_builds_artifact(monkeypatch)
  services/web/tests/test_conductor_ingress.py:
    e: test_orient_host_file_list_skips_nlp2dsl_chat,test_registry_file_list_via_orient,test_agent_shell_uses_nlp2cmd_not_nlp2dsl
    test_orient_host_file_list_skips_nlp2dsl_chat(monkeypatch)
    test_registry_file_list_via_orient(monkeypatch;patch_file_inventory)
    test_agent_shell_uses_nlp2cmd_not_nlp2dsl(monkeypatch;patch_nlp2cmd_translate;patch_nlp2dsl_down)
  services/web/tests/test_context_tickets.py:
    e: test_unlink_ticket_removes_uri_and_linked_id,test_unlink_ticket_keeps_other_uris,test_clear_ticket_uris_removes_all_ticket_uris
    test_unlink_ticket_removes_uri_and_linked_id()
    test_unlink_ticket_keeps_other_uris()
    test_clear_ticket_uris_removes_all_ticket_uris()
  services/web/tests/test_continue_intent.py:
    e: test_is_continue_intent,test_continue_without_nlp_session_clarifies
    test_is_continue_intent()
    test_continue_without_nlp_session_clarifies(monkeypatch)
  services/web/tests/test_e2e_chat_api.py:
    e: api_client,_start_session,_chat,TestE2EChatRoutingApi
    TestE2EChatRoutingApi: test_host_file_list_via_orient(2),test_registry_file_list_full_api_path(3),test_file_list_registry_scope_stays_mullm_file_list(3),test_router_file_list_rules_mode(1),test_router_run_ls_home_is_shell(1),test_continue_clarify_not_unknown(3),test_router_decide_dry_run_file_list(1),test_routing_feedback_on_turn(3),test_routing_explain_file_list_tree(2),test_routing_schemas_endpoint(1),test_routing_policy_endpoint(1),test_agents_status_endpoint(1),test_shell_nl_uses_nlp2cmd_plugin(4)  # Scenariusze z exportu workspace (file list, kontynuuj).
    api_client()
    _start_session(client)
    _chat(client;session_id;message)
  services/web/tests/test_e2e_live_stack.py:
    e: _wait_for_web_ready,_live_stack_ready,http,test_live_health,test_live_file_list_chat,test_live_file_list_host_or_registry,test_live_shell_route_for_run_ls_home,test_live_router_decide,test_live_routing_explain_file_list,test_live_chat_includes_decision_tree,test_live_routing_policy_has_routes,test_live_agents_status_lists_plugins,test_live_nlp2cmd_shell_nl
    _wait_for_web_ready()
    _live_stack_ready()
    http()
    test_live_health(http)
    test_live_file_list_chat(http)
    test_live_file_list_host_or_registry(http)
    test_live_shell_route_for_run_ls_home(http)
    test_live_router_decide(http)
    test_live_routing_explain_file_list(http)
    test_live_chat_includes_decision_tree(http)
    test_live_routing_policy_has_routes(http)
    test_live_agents_status_lists_plugins(http)
    test_live_nlp2cmd_shell_nl(http)
  services/web/tests/test_intract_contracts.py:
    e: _intract_cli_ready,test_intract_validate_routing_contracts
    _intract_cli_ready()
    test_intract_validate_routing_contracts()
  services/web/tests/test_local_orient.py:
    e: test_lista_plikow_usera_host,test_registry_hint
    test_lista_plikow_usera_host()
    test_registry_hint()
  services/web/tests/test_nlp2dsl_bridge.py:
    e: test_routing_from_response,test_intent_routing_policy_flags,test_merge_intent_into_policy_flags
    test_routing_from_response()
    test_intent_routing_policy_flags()
    test_merge_intent_into_policy_flags()
  services/web/tests/test_nlp2dsl_orient.py:
    e: test_orient_step_host_file_list,test_orient_step_registry_file_list,test_orient_local_fallback_host_list,test_orient_registry_falls_through_rules_when_unknown_category
    test_orient_step_host_file_list(monkeypatch)
    test_orient_step_registry_file_list(monkeypatch;patch_file_inventory)
    test_orient_local_fallback_host_list(monkeypatch;patch_file_inventory)
    test_orient_registry_falls_through_rules_when_unknown_category(monkeypatch;patch_file_inventory)
  services/web/tests/test_nlp2dsl_resume.py:
    e: test_nlp2dsl_resume_step_continues_conversation,test_nlp2dsl_resume_skipped_for_file_list
    test_nlp2dsl_resume_step_continues_conversation(monkeypatch)
    test_nlp2dsl_resume_skipped_for_file_list(monkeypatch)
  services/web/tests/test_prompt_router.py:
    e: test_file_list_routes,test_file_list_registry_scope_higher_confidence,test_shell_route,test_discuss_defaults_nlp2dsl,test_search_context_rag,test_route_decision_to_dict,test_extract_llm_json_handles_none_and_empty,test_decide_route_sets_timing
    test_file_list_routes(msg;scope)
    test_file_list_registry_scope_higher_confidence()
    test_shell_route()
    test_discuss_defaults_nlp2dsl()
    test_search_context_rag()
    test_route_decision_to_dict()
    test_extract_llm_json_handles_none_and_empty()
    test_decide_route_sets_timing()
  services/web/tests/test_prompt_router_hybrid.py:
    e: _analysis,test_hybrid_nlp2cmd_prefers_shell_over_file_list,test_hybrid_prefers_host_shell_for_lista_plikow_usera,test_hybrid_keeps_file_list_when_registry_hint,test_hybrid_without_nlp2cmd_falls_back_expectations,test_local_sufficient_skips_openrouter,test_shell_nl_rules_local_route
    _analysis(command;confidence)
    test_hybrid_nlp2cmd_prefers_shell_over_file_list(monkeypatch)
    test_hybrid_prefers_host_shell_for_lista_plikow_usera(monkeypatch)
    test_hybrid_keeps_file_list_when_registry_hint(monkeypatch)
    test_hybrid_without_nlp2cmd_falls_back_expectations(monkeypatch)
    test_local_sufficient_skips_openrouter(monkeypatch)
    test_shell_nl_rules_local_route(monkeypatch)
  services/web/tests/test_routing_contract.py:
    e: test_orientation_decision_from_dict,test_route_from_orientation_registry,test_route_from_orientation_shell_builtin,test_route_from_orientation_shell_nl_pending,test_orient_message_uses_cache
    test_orientation_decision_from_dict()
    test_route_from_orientation_registry()
    test_route_from_orientation_shell_builtin()
    test_route_from_orientation_shell_nl_pending()
    test_orient_message_uses_cache()
  services/web/tests/test_routing_explain.py:
    e: test_explain_file_list_usera_selects_rules,test_explain_disk_space_agent_shell,test_align_file_list_route
    test_explain_file_list_usera_selects_rules(monkeypatch)
    test_explain_disk_space_agent_shell()
    test_align_file_list_route()
  services/web/tests/test_routing_feedback.py:
    e: feedback_store,test_record_good_feedback,test_record_bad_creates_improvement_ticket,test_aggregate_learnings_proposes_expectation
    feedback_store(tmp_path;monkeypatch)
    test_record_good_feedback(feedback_store)
    test_record_bad_creates_improvement_ticket(feedback_store)
    test_aggregate_learnings_proposes_expectation(feedback_store)
  services/web/tests/test_routing_policy.py:
    e: test_load_default_policy,test_session_agent_overrides_route,test_mode_override_rag_only,test_policy_to_dict
    test_load_default_policy()
    test_session_agent_overrides_route()
    test_mode_override_rag_only()
    test_policy_to_dict()
  services/web/tests/test_routing_schemas.py:
    e: test_schemas_bundle_has_all_libraries,test_parse_nlp2cmd_response_rejects_invalid,test_parse_llm_classifier_valid_and_invalid,test_llm_prompt_embeds_json_schema,test_nlp_analysis_to_policy_flags
    test_schemas_bundle_has_all_libraries()
    test_parse_nlp2cmd_response_rejects_invalid()
    test_parse_llm_classifier_valid_and_invalid()
    test_llm_prompt_embeds_json_schema()
    test_nlp_analysis_to_policy_flags()
  services/web/tests/test_shell_nl_intent.py:
    e: test_file_list_not_shell_nl,test_shell_nl_disk_intent,test_run_prefix_not_shell_nl
    test_file_list_not_shell_nl()
    test_shell_nl_disk_intent()
    test_run_prefix_not_shell_nl()
  services/web/tests/test_ticket_schemas.py:
    e: test_ticket_schemas_bundle,test_improvement_planfile_cmd,test_sync_disabled_without_env
    test_ticket_schemas_bundle()
    test_improvement_planfile_cmd()
    test_sync_disabled_without_env()
  tests/conftest.py:
    e: fake_postgres,fake_bus,event_store,catalog,command_bus,sample_command_id,orchestrator_app,api_client,FakeRow,InMemoryPostgres,FakeMessageBus
    FakeRow: __getitem__(1),get(2),keys(0)
    InMemoryPostgres: __init__(0),connect(0),disconnect(0),execute(1),fetchrow(1),fetch(1),_event_row(1)
    FakeMessageBus: __init__(0),publish(2)
    fake_postgres()
    fake_bus()
    event_store(fake_postgres)
    catalog()
    command_bus(event_store;fake_bus;fake_postgres;catalog)
    sample_command_id()
    orchestrator_app(command_bus;event_store;fake_postgres;catalog)
    api_client(orchestrator_app)
  tests/test_access_fabric.py:
    e: test_parse_and_build_uri,test_localfs_probe_and_fetch,test_register_and_transfer_resource
    test_parse_and_build_uri()
    test_localfs_probe_and_fetch(tmp_path)
    test_register_and_transfer_resource(command_bus;tmp_path)
  tests/test_agent_aggregate.py:
    e: test_register_agent,test_assign_task_marks_busy,test_disabled_agent_cannot_take_task
    test_register_agent()
    test_assign_task_marks_busy()
    test_disabled_agent_cannot_take_task()
  tests/test_api_orchestrator.py:
    e: test_health_not_on_minimal_app,test_register_agent_api,test_approval_api_flow,test_plugin_api_flow,test_workflow_version_api,test_command_envelope
    test_health_not_on_minimal_app(api_client)
    test_register_agent_api(api_client)
    test_approval_api_flow(api_client)
    test_plugin_api_flow(api_client)
    test_workflow_version_api(api_client)
    test_command_envelope(api_client)
  tests/test_approval_aggregate.py:
    e: test_approval_request_and_grant,test_cannot_approve_twice
    test_approval_request_and_grant()
    test_cannot_approve_twice()
  tests/test_approval_gate.py:
    e: test_activate_plugin_requires_approval,test_activate_plugin_with_granted_approval,test_skip_approval_for_dev,test_ensure_approval_rejects_wrong_target
    test_activate_plugin_requires_approval(command_bus)
    test_activate_plugin_with_granted_approval(command_bus)
    test_skip_approval_for_dev(command_bus)
    test_ensure_approval_rejects_wrong_target(command_bus)
  tests/test_command_bus.py:
    e: test_create_and_assign_task,test_register_agent_and_heartbeat,test_approval_flow,test_plugin_and_workflow_version_flow
    test_create_and_assign_task(command_bus;fake_bus)
    test_register_agent_and_heartbeat(command_bus)
    test_approval_flow(command_bus)
    test_plugin_and_workflow_version_flow(command_bus)
  tests/test_e2e_flow.py:
    e: test_full_task_lifecycle
    test_full_task_lifecycle(command_bus;fake_bus)
  tests/test_eventstore_factory.py:
    e: test_build_postgres_backend,test_build_dual_without_esdb_falls_back
    test_build_postgres_backend(fake_postgres)
    test_build_dual_without_esdb_falls_back(fake_postgres)
  tests/test_evolution_layer.py:
    e: catalog,test_catalog_loads_events,test_catalog_graph,test_policy_requires_plugin_manifest,test_policy_accepts_full_manifest,test_shadow_workflow,test_propose_change
    catalog()
    test_catalog_loads_events(catalog)
    test_catalog_graph(catalog)
    test_policy_requires_plugin_manifest(catalog)
    test_policy_accepts_full_manifest(catalog)
    test_shadow_workflow(command_bus)
    test_propose_change(command_bus)
  tests/test_incident_observability.py:
    e: test_observability_playbooks_are_exposed,test_incident_recorder_publishes_projectable_events,test_rag_search_failure_returns_incident_payload,test_project_incidents_accepts_legacy_incident_code_payload,_load_project_incidents,RecordingDb
    RecordingDb: __init__(0),execute(1)
    test_observability_playbooks_are_exposed()
    test_incident_recorder_publishes_projectable_events(fake_postgres;fake_bus)
    test_rag_search_failure_returns_incident_payload(fake_postgres;fake_bus)
    test_project_incidents_accepts_legacy_incident_code_payload()
    _load_project_incidents()
  tests/test_integration_postgres.py:
    e: live_command_bus,test_create_task_persisted
    live_command_bus()
    test_create_task_persisted(live_command_bus)
  tests/test_plugin_aggregate.py:
    e: test_plugin_lifecycle,test_cannot_install_before_validate
    test_plugin_lifecycle()
    test_cannot_install_before_validate()
  tests/test_projections.py:
    e: _project_event,_event,test_task_created_updates_task_board_and_feed,test_approval_requested_projection,RecordingDB
    RecordingDB: __init__(0),execute(1)
    _project_event()
    _event(event_type;aggregate_type;aggregate_id;payload)
    test_task_created_updates_task_board_and_feed()
    test_approval_requested_projection()
  tests/test_projector_routes.py:
    e: _projector_app,test_projector_get_routes_are_unique
    _projector_app()
    test_projector_get_routes_are_unique()
  tests/test_rag.py:
    e: test_chunk_text_overlap,test_auto_ingest_on_register,test_rag_search_keyword,test_rag_ask_without_api_key,test_openrouter_embed_mock
    test_chunk_text_overlap()
    test_auto_ingest_on_register(command_bus;fake_postgres;tmp_path)
    test_rag_search_keyword(fake_postgres)
    test_rag_ask_without_api_key(fake_postgres)
    test_openrouter_embed_mock()
  tests/test_shell_executor.py:
    e: _run_shell_command,test_run_shell_command_success,test_run_shell_command_failure,test_run_shell_command_timeout
    _run_shell_command(command;timeout_seconds)
    test_run_shell_command_success()
    test_run_shell_command_failure()
    test_run_shell_command_timeout()
  tests/test_task_aggregate.py:
    e: test_create_task_emits_task_created,test_assign_and_complete_lifecycle,test_cannot_complete_without_assignment,test_replay_from_events
    test_create_task_emits_task_created()
    test_assign_and_complete_lifecycle()
    test_cannot_complete_without_assignment()
    test_replay_from_events()
  tests/test_task_routing.py:
    e: test_pick_idle_agent,test_auto_assign_after_create
    test_pick_idle_agent(command_bus)
    test_auto_assign_after_create(command_bus)
  tests/test_workflow_aggregate.py:
    e: test_start_workflow,test_version_lifecycle
    test_start_workflow()
    test_version_lifecycle()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('mullm', '0.0.0', 'python').

% ── Project Files ────────────────────────────────────────
project_file('agents/shell-agent/app/__init__.py', 2, 'python').
project_file('agents/shell-agent/app/executor.py', 49, 'python').
project_file('agents/shell-agent/app/main.py', 27, 'python').
project_file('agents/shell-agent/app/nats_consumer.py', 48, 'python').
project_file('app.doql.less', 474, 'less').
project_file('integrations/nlp2dsl/mullm_registry.py', 33, 'python').
project_file('integrations/nlp2dsl/patch_startup.py', 8, 'python').
project_file('project.sh', 53, 'shell').
project_file('scripts/e2e-chat-routing.sh', 80, 'shell').
project_file('scripts/run-propact-pact.sh', 72, 'shell').
project_file('scripts/test-quality.sh', 63, 'shell').
project_file('scripts/test.sh', 14, 'shell').
project_file('scripts/wait-for-web.sh', 23, 'shell').
project_file('services/orchestrator/app/__init__.py', 2, 'python').
project_file('services/orchestrator/app/access/__init__.py', 5, 'python').
project_file('services/orchestrator/app/access/adapters/__init__.py', 18, 'python').
project_file('services/orchestrator/app/access/adapters/base.py', 34, 'python').
project_file('services/orchestrator/app/access/adapters/http_adapter.py', 50, 'python').
project_file('services/orchestrator/app/access/adapters/localfs.py', 72, 'python').
project_file('services/orchestrator/app/access/transport.py', 78, 'python').
project_file('services/orchestrator/app/access/uri.py', 44, 'python').
project_file('services/orchestrator/app/api/__init__.py', 2, 'python').
project_file('services/orchestrator/app/api/access.py', 137, 'python').
project_file('services/orchestrator/app/api/catalog.py', 42, 'python').
project_file('services/orchestrator/app/api/commands.py', 380, 'python').
project_file('services/orchestrator/app/api/evolution.py', 105, 'python').
project_file('services/orchestrator/app/api/observability.py', 113, 'python').
project_file('services/orchestrator/app/api/queries.py', 205, 'python').
project_file('services/orchestrator/app/api/rag.py', 143, 'python').
project_file('services/orchestrator/app/application/__init__.py', 2, 'python').
project_file('services/orchestrator/app/application/command_bus.py', 990, 'python').
project_file('services/orchestrator/app/application/sagas/__init__.py', 15, 'python').
project_file('services/orchestrator/app/application/sagas/approval_gate.py', 147, 'python').
project_file('services/orchestrator/app/application/sagas/task_routing.py', 67, 'python').
project_file('services/orchestrator/app/config.py', 55, 'python').
project_file('services/orchestrator/app/domain/__init__.py', 2, 'python').
project_file('services/orchestrator/app/domain/aggregates/__init__.py', 2, 'python').
project_file('services/orchestrator/app/domain/aggregates/agent.py', 84, 'python').
project_file('services/orchestrator/app/domain/aggregates/approval.py', 98, 'python').
project_file('services/orchestrator/app/domain/aggregates/plugin.py', 98, 'python').
project_file('services/orchestrator/app/domain/aggregates/resource.py', 101, 'python').
project_file('services/orchestrator/app/domain/aggregates/task.py', 245, 'python').
project_file('services/orchestrator/app/domain/aggregates/workflow.py', 145, 'python').
project_file('services/orchestrator/app/domain/events/__init__.py', 104, 'python').
project_file('services/orchestrator/app/domain/events/agents.py', 96, 'python').
project_file('services/orchestrator/app/domain/events/approvals.py', 127, 'python').
project_file('services/orchestrator/app/domain/events/base.py', 82, 'python').
project_file('services/orchestrator/app/domain/events/incidents.py', 255, 'python').
project_file('services/orchestrator/app/domain/events/plugins.py', 119, 'python').
project_file('services/orchestrator/app/domain/events/resources.py', 133, 'python').
project_file('services/orchestrator/app/domain/events/tasks.py', 134, 'python').
project_file('services/orchestrator/app/domain/events/workflows.py', 168, 'python').
project_file('services/orchestrator/app/domain/value_objects/__init__.py', 86, 'python').
project_file('services/orchestrator/app/evolution/__init__.py', 13, 'python').
project_file('services/orchestrator/app/evolution/catalog.py', 93, 'python').
project_file('services/orchestrator/app/evolution/evaluation.py', 203, 'python').
project_file('services/orchestrator/app/evolution/experiments.py', 77, 'python').
project_file('services/orchestrator/app/evolution/policy_engine.py', 132, 'python').
project_file('services/orchestrator/app/incidents/__init__.py', 4, 'python').
project_file('services/orchestrator/app/incidents/pipeline.py', 406, 'python').
project_file('services/orchestrator/app/infrastructure/__init__.py', 2, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore.py', 183, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_dual.py', 58, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_esdb.py', 187, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_factory.py', 67, 'python').
project_file('services/orchestrator/app/infrastructure/nats_bus.py', 50, 'python').
project_file('services/orchestrator/app/infrastructure/postgres.py', 93, 'python').
project_file('services/orchestrator/app/main.py', 196, 'python').
project_file('services/orchestrator/app/observability/__init__.py', 23, 'python').
project_file('services/orchestrator/app/observability/context.py', 60, 'python').
project_file('services/orchestrator/app/observability/export.py', 398, 'python').
project_file('services/orchestrator/app/observability/incidents.py', 581, 'python').
project_file('services/orchestrator/app/observability/logging.py', 60, 'python').
project_file('services/orchestrator/app/observability/middleware.py', 20, 'python').
project_file('services/orchestrator/app/observability/rag_diagnostics.py', 223, 'python').
project_file('services/orchestrator/app/observability/rag_pipeline.py', 271, 'python').
project_file('services/orchestrator/app/rag/__init__.py', 7, 'python').
project_file('services/orchestrator/app/rag/chunking.py', 31, 'python').
project_file('services/orchestrator/app/rag/indexer.py', 116, 'python').
project_file('services/orchestrator/app/rag/openrouter.py', 129, 'python').
project_file('services/orchestrator/app/rag/retriever.py', 104, 'python').
project_file('services/orchestrator/app/rag/store.py', 284, 'python').
project_file('services/orchestrator/tests/__init__.py', 2, 'python').
project_file('services/orchestrator/tests/conftest.py', 10, 'python').
project_file('services/orchestrator/tests/fakes.py', 64, 'python').
project_file('services/orchestrator/tests/test_api.py', 90, 'python').
project_file('services/orchestrator/tests/test_command_bus.py', 57, 'python').
project_file('services/orchestrator/tests/test_observability.py', 151, 'python').
project_file('services/orchestrator/tests/test_task_aggregate.py', 28, 'python').
project_file('services/projector/app/__init__.py', 2, 'python').
project_file('services/projector/app/db.py', 57, 'python').
project_file('services/projector/app/main.py', 341, 'python').
project_file('services/projector/app/projections/__init__.py', 4, 'python').
project_file('services/projector/app/projections/agent_fleet.py', 98, 'python').
project_file('services/projector/app/projections/approval_requests.py', 80, 'python').
project_file('services/projector/app/projections/dispatcher.py', 48, 'python').
project_file('services/projector/app/projections/incidents.py', 332, 'python').
project_file('services/projector/app/projections/operational_feed.py', 71, 'python').
project_file('services/projector/app/projections/plugin_catalog.py', 43, 'python').
project_file('services/projector/app/projections/resource_registry.py', 131, 'python').
project_file('services/projector/app/projections/task_board.py', 154, 'python').
project_file('services/projector/app/projections/workflow_versions.py', 48, 'python').
project_file('services/web/app/__init__.py', 1, 'python').
project_file('services/web/app/access_matrix.py', 249, 'python').
project_file('services/web/app/agent_plugins/__init__.py', 20, 'python').
project_file('services/web/app/agent_plugins/nlp2cmd_plugin.py', 111, 'python').
project_file('services/web/app/agent_plugins/nlp2dsl_plugin.py', 23, 'python').
project_file('services/web/app/agent_plugins/protocol.py', 64, 'python').
project_file('services/web/app/agent_plugins/registry.py', 96, 'python').
project_file('services/web/app/agent_workroom.py', 643, 'python').
project_file('services/web/app/api/__init__.py', 2, 'python').
project_file('services/web/app/api/access_routes.py', 47, 'python').
project_file('services/web/app/api/agents_routes.py', 14, 'python').
project_file('services/web/app/api/chat_routes.py', 182, 'python').
project_file('services/web/app/api/config.py', 17, 'python').
project_file('services/web/app/api/feedback_routes.py', 52, 'python').
project_file('services/web/app/api/models.py', 92, 'python').
project_file('services/web/app/api/router_routes.py', 88, 'python').
project_file('services/web/app/api/task_routes.py', 191, 'python').
project_file('services/web/app/api/workroom_routes.py', 55, 'python').
project_file('services/web/app/api/workspace_routes.py', 81, 'python').
project_file('services/web/app/api_routes.py', 26, 'python').
project_file('services/web/app/chat.py', 1072, 'python').
project_file('services/web/app/conductor.py', 1486, 'python').
project_file('services/web/app/local_orient.py', 208, 'python').
project_file('services/web/app/main.py', 105, 'python').
project_file('services/web/app/nlp2dsl_bridge.py', 175, 'python').
project_file('services/web/app/planfile_bridge.py', 103, 'python').
project_file('services/web/app/prompt_router.py', 927, 'python').
project_file('services/web/app/resource_areas.py', 172, 'python').
project_file('services/web/app/routing/__init__.py', 14, 'python').
project_file('services/web/app/routing/decision.py', 101, 'python').
project_file('services/web/app/routing/execution_resolver.py', 91, 'python').
project_file('services/web/app/routing/ingress_cache.py', 44, 'python').
project_file('services/web/app/routing/orientation_provider.py', 82, 'python').
project_file('services/web/app/routing_feedback.py', 413, 'python').
project_file('services/web/app/routing_policy.py', 183, 'python').
project_file('services/web/app/routing_schemas.py', 172, 'python').
project_file('services/web/app/routing_trace.py', 740, 'python').
project_file('services/web/app/static/access.css', 84, 'css').
project_file('services/web/app/static/access.js', 158, 'javascript').
project_file('services/web/app/static/app.css', 200, 'css').
project_file('services/web/app/static/app.js', 207, 'javascript').
project_file('services/web/app/static/workroom.css', 87, 'css').
project_file('services/web/app/static/workroom.js', 269, 'javascript').
project_file('services/web/app/static/workspace.css', 856, 'css').
project_file('services/web/app/static/workspace.js', 1402, 'javascript').
project_file('services/web/app/ticket_schemas.py', 144, 'python').
project_file('services/web/app/tickets.py', 46, 'python').
project_file('services/web/app/workspace.py', 1439, 'python').
project_file('services/web/src/styles.css', 287, 'css').
project_file('services/web/tests/conftest.py', 84, 'python').
project_file('services/web/tests/test_access_matrix.py', 38, 'python').
project_file('services/web/tests/test_agent_plugins.py', 47, 'python').
project_file('services/web/tests/test_agent_workroom.py', 73, 'python').
project_file('services/web/tests/test_api_routes.py', 23, 'python').
project_file('services/web/tests/test_artifacts.py', 191, 'python').
project_file('services/web/tests/test_chat_intent.py', 127, 'python').
project_file('services/web/tests/test_conductor_ingress.py', 102, 'python').
project_file('services/web/tests/test_context_tickets.py', 40, 'python').
project_file('services/web/tests/test_continue_intent.py', 38, 'python').
project_file('services/web/tests/test_e2e_chat_api.py', 231, 'python').
project_file('services/web/tests/test_e2e_live_stack.py', 204, 'python').
project_file('services/web/tests/test_intract_contracts.py', 56, 'python').
project_file('services/web/tests/test_local_orient.py', 14, 'python').
project_file('services/web/tests/test_nlp2dsl_bridge.py', 44, 'python').
project_file('services/web/tests/test_nlp2dsl_orient.py', 122, 'python').
project_file('services/web/tests/test_nlp2dsl_resume.py', 74, 'python').
project_file('services/web/tests/test_prompt_router.py', 76, 'python').
project_file('services/web/tests/test_prompt_router_hybrid.py', 110, 'python').
project_file('services/web/tests/test_routing_contract.py', 102, 'python').
project_file('services/web/tests/test_routing_explain.py', 48, 'python').
project_file('services/web/tests/test_routing_feedback.py', 76, 'python').
project_file('services/web/tests/test_routing_policy.py', 42, 'python').
project_file('services/web/tests/test_routing_schemas.py', 78, 'python').
project_file('services/web/tests/test_shell_nl_intent.py', 15, 'python').
project_file('services/web/tests/test_ticket_schemas.py', 40, 'python').
project_file('tests/conftest.py', 354, 'python').
project_file('tests/test_access_fabric.py', 62, 'python').
project_file('tests/test_agent_aggregate.py', 33, 'python').
project_file('tests/test_api_orchestrator.py', 152, 'python').
project_file('tests/test_approval_aggregate.py', 26, 'python').
project_file('tests/test_approval_gate.py', 121, 'python').
project_file('tests/test_command_bus.py', 134, 'python').
project_file('tests/test_e2e_flow.py', 46, 'python').
project_file('tests/test_eventstore_factory.py', 26, 'python').
project_file('tests/test_evolution_layer.py', 90, 'python').
project_file('tests/test_incident_observability.py', 170, 'python').
project_file('tests/test_integration_postgres.py', 43, 'python').
project_file('tests/test_plugin_aggregate.py', 30, 'python').
project_file('tests/test_projections.py', 88, 'python').
project_file('tests/test_projector_routes.py', 37, 'python').
project_file('tests/test_rag.py', 115, 'python').
project_file('tests/test_shell_executor.py', 43, 'python').
project_file('tests/test_task_aggregate.py', 38, 'python').
project_file('tests/test_task_routing.py', 48, 'python').
project_file('tests/test_workflow_aggregate.py', 25, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('agents/shell-agent/app/executor.py', 'run_shell_command', 2, 4, 2).
python_function('agents/shell-agent/app/main.py', 'main', 0, 2, 3).
python_function('services/orchestrator/app/access/adapters/__init__.py', 'get_adapter', 1, 2, 4).
python_function('services/orchestrator/app/access/uri.py', 'parse_uri', 1, 6, 7).
python_function('services/orchestrator/app/access/uri.py', 'build_uri', 2, 2, 1).
python_function('services/orchestrator/app/api/access.py', 'register_resource', 2, 2, 6).
python_function('services/orchestrator/app/api/access.py', 'transfer_resource', 2, 2, 5).
python_function('services/orchestrator/app/api/access.py', 'probe_uri', 2, 2, 4).
python_function('services/orchestrator/app/api/access.py', 'fetch_uri', 2, 2, 4).
python_function('services/orchestrator/app/api/access.py', 'list_resources', 2, 2, 3).
python_function('services/orchestrator/app/api/access.py', 'build_resource_uri', 2, 1, 2).
python_function('services/orchestrator/app/api/access.py', '_safe_filename', 1, 3, 2).
python_function('services/orchestrator/app/api/access.py', 'upload_resource', 3, 4, 17).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_index', 1, 1, 1).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_graph', 1, 1, 2).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_domains', 1, 1, 1).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_events', 1, 1, 2).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_capabilities', 1, 1, 1).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_services', 1, 1, 1).
python_function('services/orchestrator/app/api/catalog.py', 'catalog_policies', 1, 1, 1).
python_function('services/orchestrator/app/api/commands.py', 'post_command', 2, 4, 5).
python_function('services/orchestrator/app/api/commands.py', 'create_task', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'assign_task', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'start_task', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'complete_task', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'fail_task', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'register_agent', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'start_workflow', 2, 2, 6).
python_function('services/orchestrator/app/api/commands.py', 'propose_workflow_version', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'validate_workflow_version', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'approve_workflow_version', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'activate_workflow_version', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'rollback_workflow_version', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'propose_plugin', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'validate_plugin', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'install_plugin', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'activate_plugin', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'rollback_plugin', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'create_approval', 2, 1, 3).
python_function('services/orchestrator/app/api/commands.py', 'approve_request', 2, 2, 2).
python_function('services/orchestrator/app/api/commands.py', 'reject_request', 2, 3, 2).
python_function('services/orchestrator/app/api/commands.py', 'expire_approval', 2, 1, 2).
python_function('services/orchestrator/app/api/commands.py', '_dispatch', 3, 4, 4).
python_function('services/orchestrator/app/api/evolution.py', 'evolution_metrics', 4, 4, 3).
python_function('services/orchestrator/app/api/evolution.py', 'list_experiments', 3, 3, 3).
python_function('services/orchestrator/app/api/evolution.py', 'capability_registry', 2, 2, 3).
python_function('services/orchestrator/app/api/evolution.py', 'propose_change', 2, 2, 5).
python_function('services/orchestrator/app/api/evolution.py', 'shadow_workflow', 2, 2, 5).
python_function('services/orchestrator/app/api/observability.py', 'rag_health', 1, 1, 4).
python_function('services/orchestrator/app/api/observability.py', 'rag_diagnose', 2, 1, 4).
python_function('services/orchestrator/app/api/observability.py', 'list_playbooks', 0, 1, 1).
python_function('services/orchestrator/app/api/observability.py', 'export_logs', 3, 2, 5).
python_function('services/orchestrator/app/api/observability.py', 'list_incidents', 2, 3, 6).
python_function('services/orchestrator/app/api/queries.py', 'get_task', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'get_agent', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'get_workflow', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'list_tasks', 5, 4, 8).
python_function('services/orchestrator/app/api/queries.py', '_task_list_item', 2, 3, 2).
python_function('services/orchestrator/app/api/queries.py', '_aggregate_state', 1, 2, 1).
python_function('services/orchestrator/app/api/queries.py', '_matches_task_filters', 1, 5, 1).
python_function('services/orchestrator/app/api/queries.py', 'list_agents', 3, 6, 8).
python_function('services/orchestrator/app/api/queries.py', '_event_to_dict', 1, 2, 3).
python_function('services/orchestrator/app/api/rag.py', 'rag_health', 1, 1, 2).
python_function('services/orchestrator/app/api/rag.py', 'list_documents', 2, 1, 2).
python_function('services/orchestrator/app/api/rag.py', 'search', 2, 3, 15).
python_function('services/orchestrator/app/api/rag.py', 'ask', 2, 1, 6).
python_function('services/orchestrator/app/api/rag.py', 'ingest_resource', 2, 2, 5).
python_function('services/orchestrator/app/api/rag.py', '_safe_rag_diagnostics', 1, 2, 2).
python_function('services/orchestrator/app/application/command_bus.py', '_task_outcome_payload', 1, 5, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', '_is_skipped', 2, 3, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', 'ensure_approval', 3, 3, 6).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', '_required_approval_id', 4, 2, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', '_validate_approval_events', 4, 5, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', 'follow_up_after_grant', 1, 5, 3).
python_function('services/orchestrator/app/application/sagas/task_routing.py', 'pick_idle_agent', 2, 4, 4).
python_function('services/orchestrator/app/application/sagas/task_routing.py', '_agent_route_state', 1, 4, 1).
python_function('services/orchestrator/app/application/sagas/task_routing.py', '_agent_matches', 2, 4, 2).
python_function('services/orchestrator/app/application/sagas/task_routing.py', 'maybe_auto_assign', 1, 5, 3).
python_function('services/orchestrator/app/domain/aggregates/agent.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_type', 1, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_data', 1, 2, 3).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_timestamp', 1, 3, 3).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_apply_task_created', 3, 4, 4).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_apply_task_assigned', 3, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_apply_task_started', 3, 2, 2).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_apply_task_completed', 3, 2, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_apply_task_failed', 3, 1, 1).
python_function('services/orchestrator/app/domain/events/base.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/events/base.py', '_json_value', 1, 3, 3).
python_function('services/orchestrator/app/domain/events/base.py', '_json_datetime', 1, 1, 1).
python_function('services/orchestrator/app/domain/events/base.py', '_json_list', 1, 2, 1).
python_function('services/orchestrator/app/domain/events/base.py', '_json_dict', 1, 2, 2).
python_function('services/orchestrator/app/domain/events/base.py', '_json_none', 1, 1, 0).
python_function('services/orchestrator/app/evolution/evaluation.py', '_count_if', 1, 2, 0).
python_function('services/orchestrator/app/evolution/evaluation.py', '_rate_if', 1, 2, 0).
python_function('services/orchestrator/app/evolution/evaluation.py', '_should_rollback_metrics', 1, 5, 2).
python_function('services/orchestrator/app/evolution/policy_engine.py', '_activation_metrics_row', 2, 1, 1).
python_function('services/orchestrator/app/evolution/policy_engine.py', '_has_enough_activation_samples', 2, 3, 2).
python_function('services/orchestrator/app/incidents/pipeline.py', 'classify_rag_error', 1, 3, 4).
python_function('services/orchestrator/app/incidents/pipeline.py', '_rag_root_cause', 1, 5, 7).
python_function('services/orchestrator/app/incidents/pipeline.py', '_rag_schema_missing', 2, 1, 0).
python_function('services/orchestrator/app/incidents/pipeline.py', '_rag_index_empty', 2, 1, 1).
python_function('services/orchestrator/app/incidents/pipeline.py', '_retriever_empty_result', 2, 1, 1).
python_function('services/orchestrator/app/incidents/pipeline.py', '_openrouter_unconfigured', 2, 1, 1).
python_function('services/orchestrator/app/incidents/pipeline.py', '_rag_failure_events', 1, 3, 6).
python_function('services/orchestrator/app/incidents/pipeline.py', '_rag_failure_result', 1, 4, 27).
python_function('services/orchestrator/app/infrastructure/eventstore.py', '_loads_json', 1, 3, 3).
python_function('services/orchestrator/app/infrastructure/eventstore.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/infrastructure/eventstore_esdb.py', '_parse_esdb_uri', 1, 4, 3).
python_function('services/orchestrator/app/infrastructure/eventstore_factory.py', 'build_event_store', 0, 5, 5).
python_function('services/orchestrator/app/infrastructure/eventstore_factory.py', '_require_eventstore_url', 2, 2, 1).
python_function('services/orchestrator/app/infrastructure/eventstore_factory.py', '_eventstoredb_backend', 2, 1, 3).
python_function('services/orchestrator/app/infrastructure/eventstore_factory.py', '_dual_backend', 3, 2, 5).
python_function('services/orchestrator/app/main.py', 'lifespan', 1, 6, 21).
python_function('services/orchestrator/app/main.py', 'health_check', 0, 1, 2).
python_function('services/orchestrator/app/main.py', 'root', 0, 1, 1).
python_function('services/orchestrator/app/main.py', '_seed_capability_registry', 1, 3, 3).
python_function('services/orchestrator/app/main.py', '_subscribe_shell_results', 1, 1, 5).
python_function('services/orchestrator/app/observability/context.py', 'new_correlation_id', 0, 1, 2).
python_function('services/orchestrator/app/observability/context.py', 'new_retrieval_trace_id', 0, 1, 1).
python_function('services/orchestrator/app/observability/context.py', 'get_correlation_id', 0, 1, 1).
python_function('services/orchestrator/app/observability/context.py', 'get_retrieval_trace_id', 0, 1, 1).
python_function('services/orchestrator/app/observability/context.py', 'get_chat_session_id', 0, 1, 1).
python_function('services/orchestrator/app/observability/context.py', 'observability_context', 0, 5, 4).
python_function('services/orchestrator/app/observability/export.py', 'format_logs_text', 1, 7, 11).
python_function('services/orchestrator/app/observability/export.py', 'clamp_log_export_limit', 1, 3, 3).
python_function('services/orchestrator/app/observability/export.py', '_nfo_package_version', 0, 1, 2).
python_function('services/orchestrator/app/observability/export.py', '_build_nfo_package', 1, 2, 5).
python_function('services/orchestrator/app/observability/export.py', '_nfo_counts', 1, 9, 3).
python_function('services/orchestrator/app/observability/export.py', '_nfo_errors', 1, 5, 3).
python_function('services/orchestrator/app/observability/export.py', '_append_nfo', 2, 7, 4).
python_function('services/orchestrator/app/observability/export.py', '_append_rag_health', 2, 6, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_incidents', 2, 5, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_incident_feed', 2, 4, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_rag_snapshots', 2, 3, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_workspace_session', 2, 5, 5).
python_function('services/orchestrator/app/observability/export.py', '_append_workspace_context', 2, 3, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_workspace_events', 2, 2, 2).
python_function('services/orchestrator/app/observability/export.py', '_append_workspace_chat', 2, 3, 3).
python_function('services/orchestrator/app/observability/export.py', 'build_orchestrator_bundle', 0, 1, 11).
python_function('services/orchestrator/app/observability/export.py', '_safe_rag_health', 1, 2, 2).
python_function('services/orchestrator/app/observability/export.py', '_safe_fetch_incidents', 1, 3, 3).
python_function('services/orchestrator/app/observability/export.py', '_fetch_incidents', 1, 2, 1).
python_function('services/orchestrator/app/observability/export.py', '_safe_fetch_incident_feed', 1, 3, 3).
python_function('services/orchestrator/app/observability/export.py', '_fetch_incident_feed', 1, 2, 1).
python_function('services/orchestrator/app/observability/export.py', '_safe_fetch_rag_snapshots', 1, 3, 3).
python_function('services/orchestrator/app/observability/export.py', '_fetch_rag_snapshots', 1, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', 'classify_rag_failure', 0, 3, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_backend_unavailable', 4, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_rag_timeout', 4, 2, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_vector_db_unavailable', 4, 3, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_embedding_pipeline_failed', 4, 1, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_llm_unavailable', 4, 3, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_retriever_empty_result', 4, 1, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_grounding_failed', 4, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_row', 0, 2, 8).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_correlation_id', 1, 3, 3).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_trace_id', 1, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_dict', 1, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_log_incident_row', 1, 1, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_event_plan', 1, 2, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_diagnostics_event_plan', 1, 3, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_remediation_event_plan', 1, 6, 4).
python_function('services/orchestrator/app/observability/incidents.py', '_remediation_done_event', 1, 2, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_verification_event', 1, 3, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_event_payload', 2, 4, 4).
python_function('services/orchestrator/app/observability/incidents.py', '_base_event_payload', 2, 4, 4).
python_function('services/orchestrator/app/observability/incidents.py', '_event_context', 1, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_apply_event_payload_details', 2, 4, 3).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_rag_request_failed', 1, 2, 2).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_incident_classified', 1, 1, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_diagnostics_started', 1, 1, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_diagnostics_completed', 1, 1, 2).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_remediation_started', 1, 1, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_payload_remediation_result', 1, 2, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_query_from_trace', 1, 4, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_check_names', 1, 6, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_checks_payload', 1, 4, 3).
python_function('services/orchestrator/app/observability/incidents.py', '_checks_list_payload', 1, 3, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_check_payload', 1, 3, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_root_cause', 2, 4, 2).
python_function('services/orchestrator/app/observability/incidents.py', '_event_status', 2, 5, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_class', 1, 4, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_default_playbook', 1, 1, 1).
python_function('services/orchestrator/app/observability/logging.py', 'log_event', 0, 3, 10).
python_function('services/orchestrator/app/observability/logging.py', '_emit_nfo_event', 1, 3, 2).
python_function('services/orchestrator/app/observability/rag_diagnostics.py', '_checks_with_status', 2, 3, 1).
python_function('services/orchestrator/app/observability/rag_diagnostics.py', '_overall_status', 1, 3, 1).
python_function('services/orchestrator/app/observability/rag_diagnostics.py', '_primary_incident_code', 1, 3, 2).
python_function('services/orchestrator/app/observability/rag_diagnostics.py', '_log_diagnostics_result', 3, 2, 2).
python_function('services/orchestrator/app/observability/rag_pipeline.py', '_result_with_trace', 1, 1, 0).
python_function('services/orchestrator/app/rag/chunking.py', 'chunk_text', 1, 4, 3).
python_function('services/orchestrator/app/rag/chunking.py', '_overlapping_chunks', 1, 4, 5).
python_function('services/orchestrator/app/rag/indexer.py', '_chunks_for_body', 1, 2, 2).
python_function('services/orchestrator/app/rag/indexer.py', '_packed_chunks', 2, 3, 1).
python_function('services/orchestrator/app/rag/indexer.py', '_indexed_result', 3, 1, 1).
python_function('services/orchestrator/app/rag/indexer.py', '_failed_result', 2, 1, 1).
python_function('services/orchestrator/app/rag/openrouter.py', 'normalize_openrouter_model', 1, 3, 3).
python_function('services/orchestrator/app/rag/openrouter.py', '_chat_response_error', 1, 2, 1).
python_function('services/orchestrator/app/rag/openrouter.py', '_chat_result', 1, 6, 2).
python_function('services/orchestrator/app/rag/retriever.py', '_no_hits_answer', 2, 1, 0).
python_function('services/orchestrator/app/rag/retriever.py', '_unconfigured_answer', 2, 1, 0).
python_function('services/orchestrator/app/rag/retriever.py', '_context_from_hits', 1, 2, 1).
python_function('services/orchestrator/app/rag/retriever.py', '_rag_messages', 2, 1, 0).
python_function('services/orchestrator/app/rag/retriever.py', '_fragment_fallback_answer', 2, 3, 2).
python_function('services/orchestrator/app/rag/store.py', '_cosine', 2, 5, 4).
python_function('services/orchestrator/app/rag/store.py', '_same_dimension_vectors', 2, 3, 2).
python_function('services/orchestrator/app/rag/store.py', '_vector_norm', 1, 2, 2).
python_function('services/orchestrator/app/rag/store.py', '_vector_hits', 2, 3, 5).
python_function('services/orchestrator/app/rag/store.py', '_ranked_hits', 1, 2, 4).
python_function('services/orchestrator/app/rag/store.py', '_query_tokens', 1, 3, 3).
python_function('services/orchestrator/app/rag/store.py', '_keyword_hits', 2, 3, 5).
python_function('services/orchestrator/app/rag/store.py', '_keyword_score', 2, 4, 4).
python_function('services/orchestrator/app/rag/store.py', '_parse_embedding', 1, 5, 5).
python_function('services/orchestrator/app/rag/store.py', '_row_dict', 1, 4, 3).
python_function('services/orchestrator/app/rag/store.py', '_chunk_hit', 2, 2, 4).
python_function('services/orchestrator/tests/test_api.py', 'client', 0, 1, 5).
python_function('services/orchestrator/tests/test_api.py', 'test_create_task_endpoint_dispatches_command', 1, 3, 2).
python_function('services/orchestrator/tests/test_api.py', 'test_generic_command_envelope_endpoint', 1, 3, 2).
python_function('services/orchestrator/tests/test_api.py', 'test_get_task_query_returns_reconstructed_state', 1, 3, 2).
python_function('services/orchestrator/tests/test_api.py', 'test_get_task_query_returns_404', 1, 2, 1).
python_function('services/orchestrator/tests/test_command_bus.py', 'test_command_bus_creates_assigns_and_completes_task', 0, 6, 6).
python_function('services/orchestrator/tests/test_command_bus.py', 'test_command_bus_registers_agent', 0, 3, 3).
python_function('services/orchestrator/tests/test_observability.py', 'test_classify_llm_unavailable', 0, 2, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_classify_empty_sources', 0, 2, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_classify_grounding', 0, 2, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_classify_backend_500', 0, 2, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_format_logs_text_keeps_observability_sections', 0, 7, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_build_bundle_uses_expanded_log_limit', 0, 4, 4).
python_function('services/orchestrator/tests/test_observability.py', 'test_incident_event_plan_includes_diagnostics_and_remediation', 0, 3, 1).
python_function('services/orchestrator/tests/test_observability.py', 'test_event_payload_adds_diagnostics_details', 0, 4, 1).
python_function('services/orchestrator/tests/test_task_aggregate.py', 'test_task_rehydrates_from_domain_events', 0, 5, 7).
python_function('services/orchestrator/tests/test_task_aggregate.py', 'test_task_cannot_complete_before_assignment', 0, 4, 4).
python_function('services/projector/app/main.py', 'lifespan', 1, 4, 10).
python_function('services/projector/app/main.py', 'health_check', 0, 1, 1).
python_function('services/projector/app/main.py', 'operational_feed', 2, 2, 3).
python_function('services/projector/app/main.py', 'task_board', 3, 3, 3).
python_function('services/projector/app/main.py', 'agent_fleet', 3, 3, 3).
python_function('services/projector/app/main.py', 'approval_requests', 3, 3, 3).
python_function('services/projector/app/main.py', 'plugin_catalog', 3, 3, 3).
python_function('services/projector/app/main.py', 'rag_documents', 2, 2, 3).
python_function('services/projector/app/main.py', 'incident_feed', 3, 3, 3).
python_function('services/projector/app/main.py', 'service_health', 2, 2, 3).
python_function('services/projector/app/main.py', 'remediation_history', 2, 2, 3).
python_function('services/projector/app/main.py', 'rag_quality_board', 2, 2, 3).
python_function('services/projector/app/main.py', 'resource_registry', 2, 2, 3).
python_function('services/projector/app/main.py', 'workflow_versions', 2, 2, 3).
python_function('services/projector/app/main.py', '_row_to_dict', 1, 3, 5).
python_function('services/projector/app/projections/agent_fleet.py', 'project_agent_fleet', 2, 3, 2).
python_function('services/projector/app/projections/agent_fleet.py', '_handle_agent_registered', 3, 2, 3).
python_function('services/projector/app/projections/agent_fleet.py', '_handle_agent_heartbeat', 3, 2, 3).
python_function('services/projector/app/projections/agent_fleet.py', '_handle_task_assigned_to_agent', 3, 1, 1).
python_function('services/projector/app/projections/agent_fleet.py', '_handle_agent_marked_idle', 3, 1, 1).
python_function('services/projector/app/projections/approval_requests.py', 'project_approval_requests', 2, 6, 2).
python_function('services/projector/app/projections/dispatcher.py', 'project_event', 2, 1, 9).
python_function('services/projector/app/projections/dispatcher.py', '_normalize_event', 1, 2, 3).
python_function('services/projector/app/projections/dispatcher.py', '_event_payload', 1, 3, 1).
python_function('services/projector/app/projections/dispatcher.py', '_event_occurred_at', 1, 4, 5).
python_function('services/projector/app/projections/incidents.py', 'project_incidents', 2, 3, 2).
python_function('services/projector/app/projections/incidents.py', '_handle_rag_request_failed', 2, 2, 4).
python_function('services/projector/app/projections/incidents.py', '_handle_incident_detected', 2, 6, 4).
python_function('services/projector/app/projections/incidents.py', '_handle_incident_classified', 2, 1, 3).
python_function('services/projector/app/projections/incidents.py', '_handle_diagnostics_started', 2, 1, 2).
python_function('services/projector/app/projections/incidents.py', '_handle_diagnostics_completed', 2, 4, 8).
python_function('services/projector/app/projections/incidents.py', '_handle_remediation_started', 2, 1, 3).
python_function('services/projector/app/projections/incidents.py', '_handle_remediation_finished', 2, 2, 4).
python_function('services/projector/app/projections/incidents.py', '_handle_post_remediation_verification', 2, 4, 3).
python_function('services/projector/app/projections/incidents.py', '_upsert_rag_quality', 3, 1, 3).
python_function('services/projector/app/projections/incidents.py', '_upsert_service_health', 1, 1, 2).
python_function('services/projector/app/projections/incidents.py', '_update_incident_status', 4, 1, 1).
python_function('services/projector/app/projections/incidents.py', '_error_code', 1, 4, 1).
python_function('services/projector/app/projections/incidents.py', '_checks_payload', 1, 3, 3).
python_function('services/projector/app/projections/incidents.py', '_raw_checks', 1, 4, 2).
python_function('services/projector/app/projections/incidents.py', '_checks_list_payload', 1, 3, 5).
python_function('services/projector/app/projections/incidents.py', '_check_payload', 1, 3, 1).
python_function('services/projector/app/projections/incidents.py', '_root_cause', 1, 4, 4).
python_function('services/projector/app/projections/incidents.py', '_diagnostics_ok', 1, 6, 3).
python_function('services/projector/app/projections/operational_feed.py', 'project_operational_feed', 2, 3, 5).
python_function('services/projector/app/projections/operational_feed.py', '_title_for', 2, 2, 2).
python_function('services/projector/app/projections/operational_feed.py', '_summary_for', 2, 6, 1).
python_function('services/projector/app/projections/plugin_catalog.py', 'project_plugin_catalog', 2, 5, 3).
python_function('services/projector/app/projections/resource_registry.py', 'project_resource_registry', 2, 3, 2).
python_function('services/projector/app/projections/resource_registry.py', '_handle_resource_registered', 3, 2, 3).
python_function('services/projector/app/projections/resource_registry.py', '_handle_transfer_requested', 3, 1, 2).
python_function('services/projector/app/projections/resource_registry.py', '_handle_transfer_completed', 3, 2, 3).
python_function('services/projector/app/projections/resource_registry.py', '_handle_transfer_failed', 3, 1, 2).
python_function('services/projector/app/projections/task_board.py', 'project_task_board', 2, 3, 2).
python_function('services/projector/app/projections/task_board.py', '_handle_task_created', 4, 2, 3).
python_function('services/projector/app/projections/task_board.py', '_handle_task_assigned', 4, 1, 2).
python_function('services/projector/app/projections/task_board.py', '_handle_task_started', 4, 1, 1).
python_function('services/projector/app/projections/task_board.py', '_handle_task_completed', 4, 2, 3).
python_function('services/projector/app/projections/task_board.py', '_handle_task_failed', 4, 1, 2).
python_function('services/projector/app/projections/task_board.py', '_update_status', 5, 1, 1).
python_function('services/projector/app/projections/workflow_versions.py', 'project_workflow_versions', 2, 5, 4).
python_function('services/web/app/access_matrix.py', '_matrix_path', 0, 2, 3).
python_function('services/web/app/access_matrix.py', '_default_resources', 0, 3, 2).
python_function('services/web/app/access_matrix.py', '_default_agents', 0, 5, 5).
python_function('services/web/app/access_matrix.py', '_empty_agent_resource', 2, 3, 0).
python_function('services/web/app/access_matrix.py', '_empty_human_agent', 2, 3, 0).
python_function('services/web/app/access_matrix.py', 'default_state', 0, 1, 5).
python_function('services/web/app/access_matrix.py', 'load_state', 0, 3, 9).
python_function('services/web/app/access_matrix.py', '_load_raw_state', 1, 3, 2).
python_function('services/web/app/access_matrix.py', '_apply_state_lists', 2, 3, 1).
python_function('services/web/app/access_matrix.py', '_apply_state_matrices', 2, 3, 2).
python_function('services/web/app/access_matrix.py', '_merge_bool_matrix', 2, 5, 4).
python_function('services/web/app/access_matrix.py', '_merged_bool_row', 2, 3, 3).
python_function('services/web/app/access_matrix.py', '_reindex_state', 1, 6, 6).
python_function('services/web/app/access_matrix.py', '_reindex_matrix', 1, 3, 2).
python_function('services/web/app/access_matrix.py', '_reindex_matrix_row', 1, 2, 2).
python_function('services/web/app/access_matrix.py', 'save_state', 1, 1, 6).
python_function('services/web/app/access_matrix.py', 'agent_may_access_resource', 2, 4, 3).
python_function('services/web/app/access_matrix.py', 'human_may_use_agent', 2, 4, 3).
python_function('services/web/app/access_matrix.py', 'diagnose_file_list_command', 0, 1, 0).
python_function('services/web/app/agent_plugins/nlp2cmd_plugin.py', 'backend_candidates', 0, 4, 5).
python_function('services/web/app/agent_plugins/nlp2cmd_plugin.py', '_translation_from_response', 1, 7, 5).
python_function('services/web/app/agent_plugins/registry.py', 'bootstrap', 0, 1, 0).
python_function('services/web/app/agent_plugins/registry.py', 'list_plugins', 0, 1, 3).
python_function('services/web/app/agent_plugins/registry.py', 'get_plugin', 1, 1, 2).
python_function('services/web/app/agent_plugins/registry.py', 'plugins_for_ingress_step', 1, 3, 2).
python_function('services/web/app/agent_plugins/registry.py', 'agents_status', 0, 2, 4).
python_function('services/web/app/agent_plugins/registry.py', 'analyze_shell_nl', 1, 4, 5).
python_function('services/web/app/agent_plugins/registry.py', 'translate_shell_nl', 1, 4, 5).
python_function('services/web/app/agent_workroom.py', 'create_workroom', 0, 1, 2).
python_function('services/web/app/agent_workroom.py', 'get_workroom', 1, 1, 1).
python_function('services/web/app/agent_workroom.py', '_plan_steps', 1, 5, 7).
python_function('services/web/app/agent_workroom.py', '_build_file_list_for_goal', 1, 1, 4).
python_function('services/web/app/agent_workroom.py', 'format_workroom_export', 1, 1, 6).
python_function('services/web/app/agent_workroom.py', '_workroom_export_header', 1, 3, 2).
python_function('services/web/app/agent_workroom.py', '_append_workroom_thread', 2, 6, 3).
python_function('services/web/app/agent_workroom.py', '_append_workroom_ledger', 2, 5, 1).
python_function('services/web/app/agent_workroom.py', '_append_workroom_result', 2, 2, 1).
python_function('services/web/app/agent_workroom.py', '_extract_shell', 1, 4, 5).
python_function('services/web/app/agent_workroom.py', 'run_workroom', 2, 6, 9).
python_function('services/web/app/agent_workroom.py', '_reset_workroom', 2, 1, 2).
python_function('services/web/app/agent_workroom.py', '_start_plan', 2, 2, 5).
python_function('services/web/app/agent_workroom.py', '_workspace_scope', 1, 3, 2).
python_function('services/web/app/agent_workroom.py', '_run_workroom_step', 3, 2, 3).
python_function('services/web/app/agent_workroom.py', '_run_analyze_workroom_step', 3, 1, 1).
python_function('services/web/app/agent_workroom.py', '_run_files_workroom_step', 3, 1, 1).
python_function('services/web/app/agent_workroom.py', '_run_shell_workroom_step', 3, 1, 1).
python_function('services/web/app/agent_workroom.py', '_run_summarize_workroom_step', 3, 1, 1).
python_function('services/web/app/agent_workroom.py', '_run_analyze_step', 1, 1, 1).
python_function('services/web/app/agent_workroom.py', '_run_files_step', 3, 6, 8).
python_function('services/web/app/agent_workroom.py', '_add_permission', 5, 1, 1).
python_function('services/web/app/agent_workroom.py', '_record_file_list_result', 3, 1, 2).
python_function('services/web/app/agent_workroom.py', '_register_file_list_artifact', 5, 2, 3).
python_function('services/web/app/agent_workroom.py', '_run_shell_step', 2, 4, 6).
python_function('services/web/app/agent_workroom.py', '_record_shell_result', 3, 2, 3).
python_function('services/web/app/agent_workroom.py', '_run_summarize_step', 1, 1, 1).
python_function('services/web/app/agent_workroom.py', '_finish_workroom', 2, 2, 2).
python_function('services/web/app/agent_workroom.py', 'workroom_catalog', 0, 1, 2).
python_function('services/web/app/api/access_routes.py', 'api_resource_areas', 0, 1, 3).
python_function('services/web/app/api/access_routes.py', 'api_role_scopes', 0, 1, 1).
python_function('services/web/app/api/access_routes.py', 'access_matrix_get', 0, 1, 2).
python_function('services/web/app/api/access_routes.py', 'access_matrix_put', 1, 1, 5).
python_function('services/web/app/api/access_routes.py', 'access_matrix_reset', 0, 1, 3).
python_function('services/web/app/api/access_routes.py', 'access_diagnose_file_list', 0, 1, 2).
python_function('services/web/app/api/agents_routes.py', 'agents_status_get', 0, 1, 2).
python_function('services/web/app/api/chat_routes.py', 'start_chat_session', 1, 2, 4).
python_function('services/web/app/api/chat_routes.py', 'get_chat_session', 1, 2, 3).
python_function('services/web/app/api/chat_routes.py', 'workspace_state', 1, 1, 3).
python_function('services/web/app/api/chat_routes.py', 'chat_message', 1, 3, 7).
python_function('services/web/app/api/chat_routes.py', '_form_only_message', 1, 3, 2).
python_function('services/web/app/api/chat_routes.py', '_form_only_chat_message', 2, 2, 3).
python_function('services/web/app/api/chat_routes.py', '_update_nlp_conversation', 2, 3, 2).
python_function('services/web/app/api/chat_routes.py', 'task_draft', 1, 1, 2).
python_function('services/web/app/api/chat_routes.py', 'context_attach', 1, 1, 2).
python_function('services/web/app/api/chat_routes.py', 'context_clear_tickets', 1, 1, 2).
python_function('services/web/app/api/chat_routes.py', 'upload_files', 3, 3, 6).
python_function('services/web/app/api/chat_routes.py', '_upload_one_file', 2, 5, 5).
python_function('services/web/app/api/chat_routes.py', 'board_snapshot', 0, 1, 2).
python_function('services/web/app/api/feedback_routes.py', 'routing_feedback_post', 1, 2, 5).
python_function('services/web/app/api/feedback_routes.py', 'routing_feedback_list', 2, 1, 2).
python_function('services/web/app/api/feedback_routes.py', 'routing_learnings', 1, 1, 2).
python_function('services/web/app/api/feedback_routes.py', 'routing_improvements', 2, 1, 2).
python_function('services/web/app/api/router_routes.py', 'router_decide', 3, 1, 3).
python_function('services/web/app/api/router_routes.py', 'routing_schemas_get', 0, 1, 2).
python_function('services/web/app/api/router_routes.py', 'ticket_schemas_get', 0, 1, 2).
python_function('services/web/app/api/router_routes.py', 'routing_policy_get', 1, 1, 3).
python_function('services/web/app/api/router_routes.py', 'routing_explain', 4, 1, 2).
python_function('services/web/app/api/router_routes.py', 'routing_trace_last', 1, 9, 4).
python_function('services/web/app/api/task_routes.py', 'create_task', 1, 6, 7).
python_function('services/web/app/api/task_routes.py', 'create_task_from_draft', 1, 2, 4).
python_function('services/web/app/api/task_routes.py', 'create_and_run_task', 1, 2, 4).
python_function('services/web/app/api/task_routes.py', 'list_tickets', 2, 3, 5).
python_function('services/web/app/api/task_routes.py', 'ticket_statuses', 0, 1, 1).
python_function('services/web/app/api/task_routes.py', 'get_ticket', 2, 4, 5).
python_function('services/web/app/api/task_routes.py', 'confirm_ticket', 2, 5, 8).
python_function('services/web/app/api/task_routes.py', 'archive_ticket', 2, 1, 2).
python_function('services/web/app/api/task_routes.py', 'link_ticket', 2, 1, 2).
python_function('services/web/app/api/task_routes.py', 'unlink_ticket', 2, 1, 2).
python_function('services/web/app/api/task_routes.py', '_archived_ids', 1, 2, 2).
python_function('services/web/app/api/task_routes.py', '_filter_tickets_view', 2, 4, 2).
python_function('services/web/app/api/task_routes.py', '_is_archived_ticket', 1, 1, 0).
python_function('services/web/app/api/task_routes.py', '_is_active_ticket', 1, 1, 0).
python_function('services/web/app/api/task_routes.py', '_confirmable_task_and_agent', 1, 2, 5).
python_function('services/web/app/api/task_routes.py', '_task_from_board', 2, 5, 3).
python_function('services/web/app/api/task_routes.py', '_assert_confirmable_task', 1, 3, 3).
python_function('services/web/app/api/task_routes.py', '_first_idle_agent_id', 1, 5, 2).
python_function('services/web/app/api/task_routes.py', '_assign_ticket', 3, 3, 3).
python_function('services/web/app/api/workroom_routes.py', 'workroom_start', 1, 2, 5).
python_function('services/web/app/api/workroom_routes.py', 'workroom_get', 1, 1, 3).
python_function('services/web/app/api/workroom_routes.py', 'workroom_export', 1, 1, 4).
python_function('services/web/app/api/workroom_routes.py', 'workroom_run', 2, 2, 4).
python_function('services/web/app/api/workroom_routes.py', '_workroom_or_404', 1, 2, 2).
python_function('services/web/app/api/workspace_routes.py', 'workspace_list_artifacts', 1, 1, 3).
python_function('services/web/app/api/workspace_routes.py', 'workspace_get_artifact', 2, 2, 3).
python_function('services/web/app/api/workspace_routes.py', 'workspace_file_list_export', 3, 2, 9).
python_function('services/web/app/api/workspace_routes.py', 'workspace_chat_export', 1, 1, 5).
python_function('services/web/app/api/workspace_routes.py', 'workspace_logs_export', 2, 1, 4).
python_function('services/web/app/chat.py', '_orch', 0, 2, 1).
python_function('services/web/app/chat.py', '_projector', 0, 1, 1).
python_function('services/web/app/chat.py', 'is_continue_intent', 1, 2, 3).
python_function('services/web/app/chat.py', 'is_file_list_intent', 1, 4, 5).
python_function('services/web/app/chat.py', 'is_shell_nl_intent', 1, 5, 5).
python_function('services/web/app/chat.py', '_has_list_word', 1, 3, 1).
python_function('services/web/app/chat.py', '_looks_like_misspelled_file_list', 1, 5, 3).
python_function('services/web/app/chat.py', '_has_polish_file_list_words', 1, 2, 1).
python_function('services/web/app/chat.py', '_has_english_file_list_words', 1, 2, 3).
python_function('services/web/app/chat.py', '_has_user_files_phrase', 1, 2, 2).
python_function('services/web/app/chat.py', 'file_list_scope', 1, 6, 5).
python_function('services/web/app/chat.py', '_system_scope_requested', 1, 1, 2).
python_function('services/web/app/chat.py', '_user_scope_requested', 1, 1, 2).
python_function('services/web/app/chat.py', '_rag_scope_requested', 1, 2, 2).
python_function('services/web/app/chat.py', '_session_scope_requested', 1, 1, 2).
python_function('services/web/app/chat.py', '_uri_is_user_resource', 1, 6, 2).
python_function('services/web/app/chat.py', '_uri_is_system_resource', 1, 5, 3).
python_function('services/web/app/chat.py', 'filter_file_inventory', 2, 5, 4).
python_function('services/web/app/chat.py', '_filtered_resources', 3, 2, 1).
python_function('services/web/app/chat.py', '_filter_rows_by_scope', 3, 4, 2).
python_function('services/web/app/chat.py', '_rows_matching_uri', 2, 4, 2).
python_function('services/web/app/chat.py', '_rows_in_session_scope', 2, 6, 2).
python_function('services/web/app/chat.py', '_dedupe_rows_by_uri', 1, 3, 4).
python_function('services/web/app/chat.py', '_row_dedupe_key', 1, 6, 4).
python_function('services/web/app/chat.py', 'fetch_file_inventory', 0, 1, 4).
python_function('services/web/app/chat.py', '_fetch_inventory_rows', 4, 4, 4).
python_function('services/web/app/chat.py', 'format_file_list_reply', 1, 1, 9).
python_function('services/web/app/chat.py', '_safe_list', 1, 2, 1).
python_function('services/web/app/chat.py', '_list_scope_value', 2, 3, 1).
python_function('services/web/app/chat.py', '_append_session_files', 4, 2, 4).
python_function('services/web/app/chat.py', '_append_uploaded_session_files', 2, 3, 2).
python_function('services/web/app/chat.py', '_get_user_context_parts', 1, 8, 2).
python_function('services/web/app/chat.py', '_append_tickets_context', 2, 3, 3).
python_function('services/web/app/chat.py', '_append_other_context', 2, 3, 1).
python_function('services/web/app/chat.py', '_append_user_context_only', 3, 4, 4).
python_function('services/web/app/chat.py', '_append_scope_uris', 3, 4, 3).
python_function('services/web/app/chat.py', '_format_scope_uri', 1, 2, 1).
python_function('services/web/app/chat.py', '_append_resource_rows', 3, 3, 6).
python_function('services/web/app/chat.py', '_format_resource_row', 2, 5, 1).
python_function('services/web/app/chat.py', '_empty_resource_hint', 1, 2, 0).
python_function('services/web/app/chat.py', '_append_rag_rows', 3, 5, 5).
python_function('services/web/app/chat.py', '_rag_rows_label', 1, 2, 0).
python_function('services/web/app/chat.py', '_format_rag_doc_row', 2, 4, 1).
python_function('services/web/app/chat.py', '_append_file_list_errors', 2, 2, 2).
python_function('services/web/app/chat.py', '_append_file_list_tip', 4, 5, 1).
python_function('services/web/app/chat.py', 'build_file_list_artifact', 2, 1, 2).
python_function('services/web/app/chat.py', 'new_session_id', 0, 1, 2).
python_function('services/web/app/chat.py', 'get_history', 1, 1, 2).
python_function('services/web/app/chat.py', '_append', 3, 1, 2).
python_function('services/web/app/chat.py', 'stamp_last_assistant_routing', 2, 4, 3).
python_function('services/web/app/chat.py', '_format_history', 1, 3, 3).
python_function('services/web/app/chat.py', '_format_incident', 1, 6, 4).
python_function('services/web/app/chat.py', '_incident_detail_parts', 2, 3, 4).
python_function('services/web/app/chat.py', '_incident_message_part', 2, 4, 1).
python_function('services/web/app/chat.py', '_incident_trace_part', 2, 3, 1).
python_function('services/web/app/chat.py', '_incident_correlation_part', 2, 3, 1).
python_function('services/web/app/chat.py', '_incident_fallback_part', 2, 3, 1).
python_function('services/web/app/chat.py', 'handle_message', 0, 5, 7).
python_function('services/web/app/chat.py', '_file_list_answer', 1, 2, 5).
python_function('services/web/app/chat.py', 'probe_rag', 0, 4, 7).
python_function('services/web/app/chat.py', '_ask_rag', 0, 5, 9).
python_function('services/web/app/chat.py', '_rag_headers', 1, 1, 0).
python_function('services/web/app/chat.py', '_rag_query', 2, 1, 1).
python_function('services/web/app/chat.py', '_answer_from_rag_payload', 2, 6, 3).
python_function('services/web/app/chat.py', '_sources_fallback_answer', 2, 4, 3).
python_function('services/web/app/chat.py', '_source_preview', 1, 2, 1).
python_function('services/web/app/chat.py', '_rag_backend_fallback', 1, 2, 2).
python_function('services/web/app/chat.py', '_rag_search_fallback', 2, 5, 5).
python_function('services/web/app/chat.py', '_rag_unavailable_answer', 3, 1, 1).
python_function('services/web/app/chat.py', '_rag_diagnostics_hint', 2, 5, 3).
python_function('services/web/app/chat.py', '_default_chat_reply', 0, 1, 0).
python_function('services/web/app/chat.py', '_message_response', 0, 1, 4).
python_function('services/web/app/chat.py', '_response_intent', 2, 3, 0).
python_function('services/web/app/chat.py', '_attach_inventory_response', 4, 4, 2).
python_function('services/web/app/chat.py', '_attach_trace_response', 2, 2, 1).
python_function('services/web/app/chat.py', 'fetch_task_state', 1, 5, 5).
python_function('services/web/app/chat.py', '_fetch_task_from_projector', 1, 9, 7).
python_function('services/web/app/chat.py', 'wait_for_task_terminal', 1, 6, 8).
python_function('services/web/app/chat.py', 'create_task', 0, 3, 6).
python_function('services/web/app/chat.py', '_task_create_payload', 0, 3, 2).
python_function('services/web/app/chat.py', '_apply_task_agent', 2, 2, 0).
python_function('services/web/app/chat.py', '_apply_task_shell', 4, 4, 0).
python_function('services/web/app/conductor.py', '_merge_nlp2dsl_routing', 3, 3, 1).
python_function('services/web/app/conductor.py', '_attach_routing', 3, 12, 5).
python_function('services/web/app/conductor.py', '_enrich_decision', 2, 3, 6).
python_function('services/web/app/conductor.py', '_rag_answer_turn', 0, 1, 1).
python_function('services/web/app/conductor.py', '_execute_rules_route', 0, 2, 2).
python_function('services/web/app/conductor.py', '_execute_file_list_route', 0, 1, 3).
python_function('services/web/app/conductor.py', '_execute_shell_route', 0, 8, 9).
python_function('services/web/app/conductor.py', '_missing_shell_response', 2, 4, 8).
python_function('services/web/app/conductor.py', '_shell_wait_seconds', 0, 3, 4).
python_function('services/web/app/conductor.py', '_create_shell_task', 1, 6, 5).
python_function('services/web/app/conductor.py', '_translation_from_policy_flags', 1, 7, 5).
python_function('services/web/app/conductor.py', '_apply_nlp2cmd_decision', 2, 2, 4).
python_function('services/web/app/conductor.py', '_shell_route_response', 4, 3, 6).
python_function('services/web/app/conductor.py', '_shell_task_reply', 2, 8, 4).
python_function('services/web/app/conductor.py', '_format_shell_terminal', 1, 11, 7).
python_function('services/web/app/conductor.py', '_execute_rag_route', 0, 1, 3).
python_function('services/web/app/conductor.py', 'handle_turn', 0, 2, 6).
python_function('services/web/app/conductor.py', '_message_with_form_values', 2, 5, 2).
python_function('services/web/app/conductor.py', '_attach_decision_tree', 1, 4, 7).
python_function('services/web/app/conductor.py', '_should_interrupt_nlp2dsl_resume', 1, 4, 2).
python_function('services/web/app/conductor.py', '_nlp2dsl_orient_step', 1, 5, 6).
python_function('services/web/app/conductor.py', '_nlp2dsl_resume_step', 1, 6, 11).
python_function('services/web/app/conductor.py', '_run_ingress_pipeline', 1, 4, 3).
python_function('services/web/app/conductor.py', '_rag_probe_step', 1, 4, 6).
python_function('services/web/app/conductor.py', '_rag_probe_enabled', 1, 3, 2).
python_function('services/web/app/conductor.py', '_rag_probe_should_answer', 2, 2, 1).
python_function('services/web/app/conductor.py', '_rag_probe_answer', 1, 1, 5).
python_function('services/web/app/conductor.py', '_should_skip_rag_probe', 1, 5, 4).
python_function('services/web/app/conductor.py', '_nlp2dsl_continue_decision', 0, 1, 1).
python_function('services/web/app/conductor.py', '_mullm_continue_clarify_decision', 0, 1, 1).
python_function('services/web/app/conductor.py', '_continue_clarify_reply', 1, 3, 3).
python_function('services/web/app/conductor.py', '_try_continue_turn', 1, 4, 13).
python_function('services/web/app/conductor.py', '_rag_probe_decision', 0, 1, 1).
python_function('services/web/app/conductor.py', '_rules_step', 1, 3, 5).
python_function('services/web/app/conductor.py', '_should_skip_nlp2dsl_step', 1, 7, 3).
python_function('services/web/app/conductor.py', '_nlp2cmd_ingress_decision', 1, 2, 2).
python_function('services/web/app/conductor.py', '_agent_shell_step', 1, 3, 7).
python_function('services/web/app/conductor.py', '_nlp2dsl_step', 1, 4, 8).
python_function('services/web/app/conductor.py', '_rag_answer_step', 1, 3, 5).
python_function('services/web/app/conductor.py', '_rag_pipeline_decision', 0, 1, 1).
python_function('services/web/app/conductor.py', '_fallback_routed_turn', 1, 2, 3).
python_function('services/web/app/conductor.py', '_decide_default_route', 1, 1, 2).
python_function('services/web/app/conductor.py', '_nlp2dsl_turn', 0, 6, 4).
python_function('services/web/app/conductor.py', '_nlp2dsl_status_turn', 0, 3, 3).
python_function('services/web/app/conductor.py', '_call_nlp2dsl', 2, 2, 2).
python_function('services/web/app/conductor.py', '_nlp_output_base', 2, 1, 0).
python_function('services/web/app/conductor.py', '_in_progress_turn', 6, 3, 3).
python_function('services/web/app/conductor.py', '_ready_turn', 0, 1, 7).
python_function('services/web/app/conductor.py', '_ready_action_payload', 1, 4, 3).
python_function('services/web/app/conductor.py', '_system_file_list_payload', 4, 1, 5).
python_function('services/web/app/conductor.py', '_shell_task_payload', 5, 5, 8).
python_function('services/web/app/conductor.py', '_shell_clarify_payload', 1, 1, 0).
python_function('services/web/app/conductor.py', '_ticket_payload', 4, 4, 6).
python_function('services/web/app/conductor.py', '_task_reply', 1, 3, 1).
python_function('services/web/app/conductor.py', '_closed_turn', 5, 2, 2).
python_function('services/web/app/conductor.py', '_append_turn', 3, 3, 2).
python_function('services/web/app/conductor.py', '_mullm_file_list_turn', 0, 1, 7).
python_function('services/web/app/conductor.py', '_fallback_turn', 0, 4, 5).
python_function('services/web/app/conductor.py', '_local_clarify', 1, 3, 3).
python_function('services/web/app/conductor.py', '_extract_shell', 1, 3, 4).
python_function('services/web/app/local_orient.py', '_has_registry_hint', 1, 2, 2).
python_function('services/web/app/local_orient.py', '_has_host_hint', 1, 3, 2).
python_function('services/web/app/local_orient.py', '_is_file_list_query', 1, 5, 4).
python_function('services/web/app/local_orient.py', '_file_list_scope', 1, 5, 2).
python_function('services/web/app/local_orient.py', 'orient_query', 1, 13, 10).
python_function('services/web/app/main.py', 'health', 0, 1, 1).
python_function('services/web/app/main.py', 'workspace_home', 2, 1, 2).
python_function('services/web/app/main.py', 'agent_workroom_page', 1, 1, 2).
python_function('services/web/app/main.py', 'access_matrix_page', 1, 1, 2).
python_function('services/web/app/main.py', 'dashboard', 1, 1, 5).
python_function('services/web/app/nlp2dsl_bridge.py', 'backend_url', 0, 1, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'backend_candidates', 0, 4, 5).
python_function('services/web/app/nlp2dsl_bridge.py', 'health', 0, 4, 3).
python_function('services/web/app/nlp2dsl_bridge.py', 'chat_start', 1, 1, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'chat_message', 2, 1, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'orient', 1, 2, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'nlp_service_candidates', 0, 4, 5).
python_function('services/web/app/nlp2dsl_bridge.py', 'orient_direct', 1, 1, 2).
python_function('services/web/app/nlp2dsl_bridge.py', '_post_json', 2, 4, 6).
python_function('services/web/app/nlp2dsl_bridge.py', 'form_to_prompt', 2, 6, 4).
python_function('services/web/app/nlp2dsl_bridge.py', 'primary_action', 1, 4, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'step_config', 1, 5, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'routing_from_response', 1, 2, 2).
python_function('services/web/app/nlp2dsl_bridge.py', 'intent_routing_policy_flags', 1, 7, 2).
python_function('services/web/app/nlp2dsl_bridge.py', 'merge_intent_into_policy_flags', 2, 2, 2).
python_function('services/web/app/planfile_bridge.py', 'planfile_sync_enabled', 0, 2, 3).
python_function('services/web/app/planfile_bridge.py', 'planfile_project_path', 0, 5, 7).
python_function('services/web/app/planfile_bridge.py', 'sync_improvement_ticket', 1, 9, 7).
python_function('services/web/app/planfile_bridge.py', '_build_create_cmd', 1, 3, 5).
python_function('services/web/app/planfile_bridge.py', '_improvement_files', 1, 3, 1).
python_function('services/web/app/planfile_bridge.py', '_parse_created_id', 1, 7, 6).
python_function('services/web/app/prompt_router.py', '_candidate', 5, 1, 0).
python_function('services/web/app/prompt_router.py', '_build_decision', 1, 3, 5).
python_function('services/web/app/prompt_router.py', '_shell_prefix', 1, 3, 5).
python_function('services/web/app/prompt_router.py', 'decide_route_rules', 1, 4, 5).
python_function('services/web/app/prompt_router.py', '_router_flags', 3, 2, 2).
python_function('services/web/app/prompt_router.py', '_empty_route_decision', 1, 1, 2).
python_function('services/web/app/prompt_router.py', '_direct_route_decision', 3, 3, 5).
python_function('services/web/app/prompt_router.py', '_default_route_decision', 2, 2, 2).
python_function('services/web/app/prompt_router.py', '_mode_route_decision', 2, 3, 2).
python_function('services/web/app/prompt_router.py', '_file_list_route_decision', 2, 5, 6).
python_function('services/web/app/prompt_router.py', '_shell_route_decision', 2, 2, 3).
python_function('services/web/app/prompt_router.py', '_shell_nl_route_decision', 2, 2, 3).
python_function('services/web/app/prompt_router.py', '_default_discuss_decision', 1, 1, 2).
python_function('services/web/app/prompt_router.py', '_fallback_mode_decision', 2, 1, 2).
python_function('services/web/app/prompt_router.py', 'decide_route_llm', 1, 4, 4).
python_function('services/web/app/prompt_router.py', '_llm_classifier_data', 3, 6, 7).
python_function('services/web/app/prompt_router.py', '_llm_classifier_payload', 2, 1, 2).
python_function('services/web/app/prompt_router.py', '_normalize_router_model', 1, 2, 2).
python_function('services/web/app/prompt_router.py', '_extract_llm_json', 1, 4, 3).
python_function('services/web/app/prompt_router.py', '_llm_decision_from_data', 1, 3, 6).
python_function('services/web/app/prompt_router.py', '_llm_route', 1, 2, 0).
python_function('services/web/app/prompt_router.py', '_explicit_registry_list', 1, 3, 2).
python_function('services/web/app/prompt_router.py', '_registry_scope_requested', 1, 3, 2).
python_function('services/web/app/prompt_router.py', '_host_filesystem_list_requested', 1, 4, 2).
python_function('services/web/app/prompt_router.py', '_command_looks_like_host_list', 1, 3, 3).
python_function('services/web/app/prompt_router.py', '_nlp2cmd_min_confidence', 0, 2, 2).
python_function('services/web/app/prompt_router.py', '_routing_use_nlp2cmd', 0, 1, 3).
python_function('services/web/app/prompt_router.py', '_local_min_confidence', 0, 2, 2).
python_function('services/web/app/prompt_router.py', '_local_confidence_sufficient', 1, 4, 1).
python_function('services/web/app/prompt_router.py', '_match_expectations_local', 1, 1, 2).
python_function('services/web/app/prompt_router.py', '_decision_from_expectations', 3, 5, 5).
python_function('services/web/app/prompt_router.py', '_safe_analyze_shell_nl', 1, 3, 2).
python_function('services/web/app/prompt_router.py', '_gather_local_analyses', 1, 1, 4).
python_function('services/web/app/prompt_router.py', '_pick_local_winner', 1, 1, 2).
python_function('services/web/app/prompt_router.py', '_resolve_local_decision', 1, 7, 6).
python_function('services/web/app/prompt_router.py', '_decision_from_nlp2cmd', 2, 5, 8).
python_function('services/web/app/prompt_router.py', '_should_prefer_nlp2cmd_over_rules', 3, 13, 8).
python_function('services/web/app/prompt_router.py', '_resolve_router_mode', 0, 5, 4).
python_function('services/web/app/prompt_router.py', 'decide_route_local_first', 1, 8, 7).
python_function('services/web/app/prompt_router.py', 'decide_route_hybrid', 1, 1, 1).
python_function('services/web/app/prompt_router.py', 'decide_route', 1, 6, 5).
python_function('services/web/app/prompt_router.py', '_merged_llm_decision', 2, 6, 1).
python_function('services/web/app/prompt_router.py', 'record_route_event', 2, 1, 3).
python_function('services/web/app/resource_areas.py', 'list_areas', 0, 2, 1).
python_function('services/web/app/resource_areas.py', 'list_groups', 0, 1, 0).
python_function('services/web/app/resource_areas.py', 'agent_may_access', 3, 4, 3).
python_function('services/web/app/resource_areas.py', '_area_policy_decision', 3, 5, 0).
python_function('services/web/app/resource_areas.py', '_matrix_access_decision', 3, 3, 1).
python_function('services/web/app/routing/execution_resolver.py', 'route_from_orientation', 1, 11, 6).
python_function('services/web/app/routing/ingress_cache.py', '_normalize_text', 1, 2, 3).
python_function('services/web/app/routing/ingress_cache.py', 'cache_key', 2, 1, 1).
python_function('services/web/app/routing/ingress_cache.py', 'get_cached_orient', 2, 1, 2).
python_function('services/web/app/routing/ingress_cache.py', 'set_cached_orient', 3, 1, 1).
python_function('services/web/app/routing/ingress_cache.py', 'clear_cache', 0, 1, 1).
python_function('services/web/app/routing/orientation_provider.py', '_orient_remote', 1, 6, 7).
python_function('services/web/app/routing/orientation_provider.py', '_orient_timeout', 0, 2, 4).
python_function('services/web/app/routing/orientation_provider.py', 'orient_message', 1, 8, 8).
python_function('services/web/app/routing_feedback.py', 'feedback_dir', 0, 2, 4).
python_function('services/web/app/routing_feedback.py', '_feedback_path', 0, 1, 2).
python_function('services/web/app/routing_feedback.py', '_improvements_path', 0, 1, 2).
python_function('services/web/app/routing_feedback.py', '_now_iso', 0, 1, 2).
python_function('services/web/app/routing_feedback.py', '_find_turn_context', 2, 9, 4).
python_function('services/web/app/routing_feedback.py', '_resolve_feedback_inputs', 5, 6, 3).
python_function('services/web/app/routing_feedback.py', '_build_feedback_tags', 5, 8, 2).
python_function('services/web/app/routing_feedback.py', 'record_feedback', 0, 7, 15).
python_function('services/web/app/routing_feedback.py', '_create_improvement_ticket', 0, 2, 9).
python_function('services/web/app/routing_feedback.py', '_maybe_sync_planfile', 1, 6, 4).
python_function('services/web/app/routing_feedback.py', '_suggest_actions', 0, 7, 2).
python_function('services/web/app/routing_feedback.py', 'list_feedback', 0, 4, 3).
python_function('services/web/app/routing_feedback.py', 'list_improvement_tickets', 0, 4, 3).
python_function('services/web/app/routing_feedback.py', 'aggregate_learnings', 0, 11, 16).
python_function('services/web/app/routing_feedback.py', '_append_jsonl', 2, 1, 3).
python_function('services/web/app/routing_feedback.py', '_read_jsonl_tail', 1, 5, 6).
python_function('services/web/app/routing_feedback.py', 'new_turn_id', 0, 1, 2).
python_function('services/web/app/routing_policy.py', '_policy_path', 0, 2, 4).
python_function('services/web/app/routing_policy.py', '_parse_policy', 2, 10, 11).
python_function('services/web/app/routing_policy.py', '_parse_user_expectations', 1, 5, 4).
python_function('services/web/app/routing_policy.py', '_parse_agents', 1, 4, 5).
python_function('services/web/app/routing_policy.py', '_valid_ingress_order', 1, 5, 1).
python_function('services/web/app/routing_policy.py', '_parse_mode_overrides', 1, 2, 3).
python_function('services/web/app/routing_policy.py', '_valid_override_steps', 1, 6, 3).
python_function('services/web/app/routing_policy.py', '_parse_rag_probe', 1, 1, 4).
python_function('services/web/app/routing_policy.py', 'load_policy', 0, 5, 6).
python_function('services/web/app/routing_schemas.py', 'routing_analysis_use_explain', 0, 1, 3).
python_function('services/web/app/routing_schemas.py', 'build_nlp2cmd_request', 1, 1, 3).
python_function('services/web/app/routing_schemas.py', 'parse_nlp2cmd_response', 1, 3, 2).
python_function('services/web/app/routing_schemas.py', 'parse_llm_classifier', 1, 3, 2).
python_function('services/web/app/routing_schemas.py', 'llm_classifier_json_schema', 0, 1, 1).
python_function('services/web/app/routing_schemas.py', 'llm_system_prompt_with_schema', 0, 1, 2).
python_function('services/web/app/routing_schemas.py', 'schemas_bundle', 0, 1, 2).
python_function('services/web/app/routing_trace.py', 'new_trace', 0, 3, 5).
python_function('services/web/app/routing_trace.py', 'append_step', 2, 3, 2).
python_function('services/web/app/routing_trace.py', '_is_expectation_hit', 2, 13, 6).
python_function('services/web/app/routing_trace.py', 'match_user_expectations', 2, 8, 9).
python_function('services/web/app/routing_trace.py', '_node_empty', 1, 1, 0).
python_function('services/web/app/routing_trace.py', '_node_mode_override', 2, 2, 0).
python_function('services/web/app/routing_trace.py', '_node_continue', 0, 1, 0).
python_function('services/web/app/routing_trace.py', '_node_file_list', 2, 5, 2).
python_function('services/web/app/routing_trace.py', '_node_shell_prefix', 1, 3, 0).
python_function('services/web/app/routing_trace.py', '_node_shell_nl', 1, 2, 0).
python_function('services/web/app/routing_trace.py', '_node_default_discuss', 0, 1, 0).
python_function('services/web/app/routing_trace.py', 'build_rules_rule_nodes', 1, 7, 14).
python_function('services/web/app/routing_trace.py', '_file_list_checks', 1, 2, 7).
python_function('services/web/app/routing_trace.py', '_default_principles', 0, 1, 0).
python_function('services/web/app/routing_trace.py', 'explain_pipeline', 1, 16, 13).
python_function('services/web/app/routing_trace.py', '_build_rag_probe_checks', 5, 2, 1).
python_function('services/web/app/routing_trace.py', '_check_rag_probe_skipped', 6, 8, 1).
python_function('services/web/app/routing_trace.py', '_evaluate_rag_probe_hits', 3, 3, 3).
python_function('services/web/app/routing_trace.py', '_explain_rag_probe', 1, 6, 11).
python_function('services/web/app/routing_trace.py', '_explain_rules_step', 1, 3, 6).
python_function('services/web/app/routing_trace.py', '_explain_agent_shell', 1, 4, 6).
python_function('services/web/app/routing_trace.py', '_explain_nlp2dsl', 1, 10, 9).
python_function('services/web/app/routing_trace.py', '_explain_rag_answer', 0, 2, 3).
python_function('services/web/app/routing_trace.py', '_orient_category_to_route', 1, 1, 1).
python_function('services/web/app/routing_trace.py', 'align_tree_to_route', 2, 13, 2).
python_function('services/web/app/routing_trace.py', 'record_live_step', 1, 3, 2).
python_function('services/web/app/ticket_schemas.py', 'schemas_bundle', 0, 1, 1).
python_function('services/web/app/tickets.py', 'ticket_uri', 1, 1, 0).
python_function('services/web/app/tickets.py', 'ticket_web_path', 1, 1, 0).
python_function('services/web/app/tickets.py', 'status_meta', 1, 3, 2).
python_function('services/web/app/tickets.py', 'enrich_task', 1, 4, 5).
python_function('services/web/app/workspace.py', '_orch', 0, 1, 1).
python_function('services/web/app/workspace.py', '_projector', 0, 1, 1).
python_function('services/web/app/workspace.py', 'new_session', 0, 1, 5).
python_function('services/web/app/workspace.py', 'get_session', 1, 1, 1).
python_function('services/web/app/workspace.py', 'get_or_create', 1, 3, 5).
python_function('services/web/app/workspace.py', '_artifact_title', 1, 6, 1).
python_function('services/web/app/workspace.py', 'register_artifact', 2, 5, 9).
python_function('services/web/app/workspace.py', 'artifact_summaries', 1, 2, 3).
python_function('services/web/app/workspace.py', 'get_artifact', 2, 4, 2).
python_function('services/web/app/workspace.py', 'workspace_state', 1, 1, 5).
python_function('services/web/app/workspace.py', 'attach_context', 1, 2, 6).
python_function('services/web/app/workspace.py', '_apply_context_scalars', 1, 6, 1).
python_function('services/web/app/workspace.py', '_append_unique', 2, 3, 1).
python_function('services/web/app/workspace.py', '_extract_ticket', 1, 2, 2).
python_function('services/web/app/workspace.py', '_extract_shell_command', 1, 4, 4).
python_function('services/web/app/workspace.py', 'build_task_payload', 2, 4, 5).
python_function('services/web/app/workspace.py', 'propose_task_draft', 2, 1, 1).
python_function('services/web/app/workspace.py', 'create_task_immediate', 1, 4, 6).
python_function('services/web/app/workspace.py', '_resolved_task_agent', 3, 5, 2).
python_function('services/web/app/workspace.py', 'handle_chat_message', 0, 6, 10).
python_function('services/web/app/workspace.py', '_attach_ticket_context', 2, 2, 2).
python_function('services/web/app/workspace.py', '_dispatch_chat_mode', 1, 3, 4).
python_function('services/web/app/workspace.py', '_create_task_from_message', 2, 1, 4).
python_function('services/web/app/workspace.py', '_task_chat_outcome', 4, 1, 3).
python_function('services/web/app/workspace.py', '_task_result_reply', 3, 4, 1).
python_function('services/web/app/workspace.py', '_search_context_outcome', 4, 1, 1).
python_function('services/web/app/workspace.py', '_conductor_outcome', 1, 3, 3).
python_function('services/web/app/workspace.py', '_record_chat_outcome', 2, 2, 5).
python_function('services/web/app/workspace.py', '_register_outcome_artifact', 3, 2, 2).
python_function('services/web/app/workspace.py', '_record_file_list_event', 2, 2, 2).
python_function('services/web/app/workspace.py', '_record_rag_trace_event', 2, 2, 2).
python_function('services/web/app/workspace.py', '_record_rag_incident_event', 2, 3, 2).
python_function('services/web/app/workspace.py', '_record_task_outcome', 2, 4, 3).
python_function('services/web/app/workspace.py', '_chat_response', 3, 2, 3).
python_function('services/web/app/workspace.py', 'create_task_from_draft', 1, 4, 3).
python_function('services/web/app/workspace.py', 'create_and_run', 1, 5, 4).
python_function('services/web/app/workspace.py', 'format_chat_export_text', 1, 2, 7).
python_function('services/web/app/workspace.py', '_append_chat_export_message', 2, 6, 5).
python_function('services/web/app/workspace.py', '_append_chat_export_trace', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_chat_export_draft', 2, 3, 2).
python_function('services/web/app/workspace.py', 'clamp_log_export_limit', 1, 3, 3).
python_function('services/web/app/workspace.py', 'export_debug_logs', 1, 2, 14).
python_function('services/web/app/workspace.py', '_debug_export_base', 1, 1, 5).
python_function('services/web/app/workspace.py', '_attach_orchestrator_debug_export', 2, 3, 6).
python_function('services/web/app/workspace.py', '_merge_orchestrator_debug_payload', 2, 6, 2).
python_function('services/web/app/workspace.py', '_attach_operational_feed', 2, 5, 5).
python_function('services/web/app/workspace.py', '_filter_operational_feed', 1, 5, 1).
python_function('services/web/app/workspace.py', '_format_export_text', 1, 2, 6).
python_function('services/web/app/workspace.py', '_export_header', 1, 2, 3).
python_function('services/web/app/workspace.py', '_append_export_sections', 3, 2, 15).
python_function('services/web/app/workspace.py', '_list_section', 2, 2, 2).
python_function('services/web/app/workspace.py', '_dict_section', 2, 2, 2).
python_function('services/web/app/workspace.py', '_visible_log_limit', 1, 1, 2).
python_function('services/web/app/workspace.py', '_nfo_package_version', 0, 1, 2).
python_function('services/web/app/workspace.py', '_emit_nfo_event', 1, 3, 2).
python_function('services/web/app/workspace.py', '_build_nfo_package', 1, 2, 5).
python_function('services/web/app/workspace.py', '_nfo_counts', 1, 1, 3).
python_function('services/web/app/workspace.py', '_nfo_errors', 1, 5, 3).
python_function('services/web/app/workspace.py', '_append_nfo_section', 2, 7, 4).
python_function('services/web/app/workspace.py', '_append_orchestrator_error', 2, 2, 2).
python_function('services/web/app/workspace.py', '_trace_event_row', 2, 6, 2).
python_function('services/web/app/workspace.py', '_trace_message_row', 2, 2, 2).
python_function('services/web/app/workspace.py', '_routing_fingerprint', 1, 2, 2).
python_function('services/web/app/workspace.py', '_append_context_section', 2, 4, 3).
python_function('services/web/app/workspace.py', '_append_context_scalars', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_context_collections', 2, 4, 4).
python_function('services/web/app/workspace.py', '_append_inventory_section', 2, 5, 4).
python_function('services/web/app/workspace.py', '_append_resource_inventory', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_rag_inventory', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_history_section', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_history_message', 2, 6, 5).
python_function('services/web/app/workspace.py', '_format_routing_line', 1, 1, 5).
python_function('services/web/app/workspace.py', '_routing_base_parts', 2, 2, 2).
python_function('services/web/app/workspace.py', '_routing_optional_parts', 2, 4, 7).
python_function('services/web/app/workspace.py', '_routing_fallback_parts', 2, 3, 1).
python_function('services/web/app/workspace.py', '_routing_shell_plugin_parts', 1, 4, 3).
python_function('services/web/app/workspace.py', '_routing_nlp2dsl_parts', 1, 6, 2).
python_function('services/web/app/workspace.py', '_append_routing_trace_section', 3, 3, 4).
python_function('services/web/app/workspace.py', '_append_routing_trace_decision', 3, 4, 4).
python_function('services/web/app/workspace.py', '_append_candidate_routes', 2, 3, 2).
python_function('services/web/app/workspace.py', '_format_candidate_route', 1, 3, 3).
python_function('services/web/app/workspace.py', '_collect_routing_trace', 2, 4, 6).
python_function('services/web/app/workspace.py', '_append_unique_trace_row', 3, 6, 4).
python_function('services/web/app/workspace.py', '_append_draft_section', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_session_events_section', 2, 3, 3).
python_function('services/web/app/workspace.py', '_event_extra', 1, 1, 3).
python_function('services/web/app/workspace.py', '_event_extra_parts', 1, 4, 2).
python_function('services/web/app/workspace.py', '_routing_event_extra', 1, 6, 3).
python_function('services/web/app/workspace.py', '_append_rag_health_section', 2, 4, 2).
python_function('services/web/app/workspace.py', '_append_incidents_section', 2, 3, 2).
python_function('services/web/app/workspace.py', '_append_rag_snapshots_section', 2, 3, 3).
python_function('services/web/app/workspace.py', '_session_rag_snapshots', 1, 4, 1).
python_function('services/web/app/workspace.py', '_append_operational_feed_section', 2, 4, 3).
python_function('services/web/app/workspace.py', 'archive_task', 2, 2, 3).
python_function('services/web/app/workspace.py', 'link_ticket', 2, 3, 3).
python_function('services/web/app/workspace.py', 'unlink_ticket', 2, 3, 4).
python_function('services/web/app/workspace.py', 'clear_ticket_uris', 1, 4, 5).
python_function('services/web/app/workspace.py', 'fetch_live_board', 0, 1, 5).
python_function('services/web/tests/conftest.py', '_deterministic_routing_env', 1, 1, 3).
python_function('services/web/tests/conftest.py', 'fake_file_inventory', 0, 1, 0).
python_function('services/web/tests/conftest.py', 'patch_file_inventory', 2, 1, 1).
python_function('services/web/tests/conftest.py', 'patch_nlp2dsl_down', 1, 1, 1).
python_function('services/web/tests/conftest.py', 'patch_nlp2cmd_translate', 1, 1, 3).
python_function('services/web/tests/conftest.py', 'patch_shell_task', 1, 1, 1).
python_function('services/web/tests/test_access_matrix.py', 'matrix_file', 1, 1, 4).
python_function('services/web/tests/test_access_matrix.py', 'test_default_all_checked', 1, 3, 1).
python_function('services/web/tests/test_access_matrix.py', 'test_save_and_deny', 1, 3, 3).
python_function('services/web/tests/test_access_matrix.py', 'test_diagnose_file_list_no_shell', 0, 3, 1).
python_function('services/web/tests/test_agent_plugins.py', 'test_registry_lists_builtin_plugins', 0, 3, 1).
python_function('services/web/tests/test_agent_plugins.py', 'test_translation_from_response', 0, 3, 1).
python_function('services/web/tests/test_agent_plugins.py', 'test_translate_shell_nl_mocked', 1, 4, 4).
python_function('services/web/tests/test_agent_plugins.py', 'test_nlp2cmd_plugin_metadata', 0, 3, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_plan_includes_files_for_lista_plikow', 0, 3, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_list_aplikow_usera_intent_and_scope', 0, 3, 3).
python_function('services/web/tests/test_agent_workroom.py', '_assert_user_file_step', 1, 5, 3).
python_function('services/web/tests/test_agent_workroom.py', 'test_workroom_export_contains_goal', 0, 3, 3).
python_function('services/web/tests/test_agent_workroom.py', 'test_files_agent_may_list_rag', 0, 2, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_mail_agent_denied_rag', 0, 2, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_groups_nonempty', 0, 2, 2).
python_function('services/web/tests/test_agent_workroom.py', 'test_workroom_session_dict', 0, 3, 2).
python_function('services/web/tests/test_agent_workroom.py', 'test_run_workroom_file_list_step', 1, 5, 4).
python_function('services/web/tests/test_api_routes.py', 'test_api_router_keeps_public_workspace_paths', 1, 3, 1).
python_function('services/web/tests/test_artifacts.py', 'test_register_and_get_artifact', 0, 3, 5).
python_function('services/web/tests/test_artifacts.py', '_register_user_file_list_artifact', 1, 1, 1).
python_function('services/web/tests/test_artifacts.py', '_assert_single_artifact_summary', 1, 3, 2).
python_function('services/web/tests/test_artifacts.py', '_assert_artifact_text', 3, 3, 1).
python_function('services/web/tests/test_artifacts.py', 'test_format_export_text_keeps_core_sections', 0, 6, 1).
python_function('services/web/tests/test_artifacts.py', 'test_format_export_text_uses_log_limit_for_verbose_sections', 0, 10, 1).
python_function('services/web/tests/test_artifacts.py', 'test_format_chat_export_includes_routing', 0, 6, 3).
python_function('services/web/tests/test_artifacts.py', 'test_format_export_includes_routing_trace', 0, 6, 1).
python_function('services/web/tests/test_artifacts.py', 'test_format_routing_line_nlp2dsl_skipped', 0, 4, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_intent_pl', 0, 5, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_format_file_list', 0, 4, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_intent_aplikow_typo', 0, 2, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_intent_en_and_pikow', 0, 5, 2).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_scope_usera', 0, 5, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_filter_user_files', 0, 3, 3).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_artifact', 0, 5, 2).
python_function('services/web/tests/test_chat_intent.py', 'test_format_user_scope_title', 0, 6, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_dedupe_rag_documents_by_uri', 0, 2, 2).
python_function('services/web/tests/test_chat_intent.py', 'test_handle_message_file_list_builds_artifact', 1, 4, 2).
python_function('services/web/tests/test_conductor_ingress.py', 'test_orient_host_file_list_skips_nlp2dsl_chat', 1, 4, 5).
python_function('services/web/tests/test_conductor_ingress.py', 'test_registry_file_list_via_orient', 2, 4, 4).
python_function('services/web/tests/test_conductor_ingress.py', 'test_agent_shell_uses_nlp2cmd_not_nlp2dsl', 3, 9, 4).
python_function('services/web/tests/test_context_tickets.py', 'test_unlink_ticket_removes_uri_and_linked_id', 0, 5, 3).
python_function('services/web/tests/test_context_tickets.py', 'test_unlink_ticket_keeps_other_uris', 0, 3, 4).
python_function('services/web/tests/test_context_tickets.py', 'test_clear_ticket_uris_removes_all_ticket_uris', 0, 3, 4).
python_function('services/web/tests/test_continue_intent.py', 'test_is_continue_intent', 0, 6, 1).
python_function('services/web/tests/test_continue_intent.py', 'test_continue_without_nlp_session_clarifies', 1, 4, 4).
python_function('services/web/tests/test_e2e_chat_api.py', 'api_client', 0, 3, 4).
python_function('services/web/tests/test_e2e_chat_api.py', '_start_session', 1, 2, 2).
python_function('services/web/tests/test_e2e_chat_api.py', '_chat', 3, 2, 2).
python_function('services/web/tests/test_e2e_live_stack.py', '_wait_for_web_ready', 0, 7, 8).
python_function('services/web/tests/test_e2e_live_stack.py', '_live_stack_ready', 0, 2, 3).
python_function('services/web/tests/test_e2e_live_stack.py', 'http', 0, 1, 1).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_health', 1, 3, 2).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_file_list_chat', 1, 8, 4).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_file_list_host_or_registry', 1, 4, 3).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_shell_route_for_run_ls_home', 1, 2, 2).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_router_decide', 1, 3, 2).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_routing_explain_file_list', 1, 4, 3).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_chat_includes_decision_tree', 1, 4, 3).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_routing_policy_has_routes', 1, 9, 3).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_agents_status_lists_plugins', 1, 6, 2).
python_function('services/web/tests/test_e2e_live_stack.py', 'test_live_nlp2cmd_shell_nl', 1, 9, 5).
python_function('services/web/tests/test_intract_contracts.py', '_intract_cli_ready', 0, 3, 1).
python_function('services/web/tests/test_intract_contracts.py', 'test_intract_validate_routing_contracts', 0, 4, 7).
python_function('services/web/tests/test_local_orient.py', 'test_lista_plikow_usera_host', 0, 3, 1).
python_function('services/web/tests/test_local_orient.py', 'test_registry_hint', 0, 3, 1).
python_function('services/web/tests/test_nlp2dsl_bridge.py', 'test_routing_from_response', 0, 3, 1).
python_function('services/web/tests/test_nlp2dsl_bridge.py', 'test_intent_routing_policy_flags', 0, 4, 1).
python_function('services/web/tests/test_nlp2dsl_bridge.py', 'test_merge_intent_into_policy_flags', 0, 3, 1).
python_function('services/web/tests/test_nlp2dsl_orient.py', 'test_orient_step_host_file_list', 1, 5, 3).
python_function('services/web/tests/test_nlp2dsl_orient.py', 'test_orient_step_registry_file_list', 2, 3, 3).
python_function('services/web/tests/test_nlp2dsl_orient.py', 'test_orient_local_fallback_host_list', 2, 5, 5).
python_function('services/web/tests/test_nlp2dsl_orient.py', 'test_orient_registry_falls_through_rules_when_unknown_category', 2, 2, 3).
python_function('services/web/tests/test_nlp2dsl_resume.py', 'test_nlp2dsl_resume_step_continues_conversation', 1, 4, 7).
python_function('services/web/tests/test_nlp2dsl_resume.py', 'test_nlp2dsl_resume_skipped_for_file_list', 1, 2, 6).
python_function('services/web/tests/test_prompt_router.py', 'test_file_list_routes', 2, 7, 2).
python_function('services/web/tests/test_prompt_router.py', 'test_file_list_registry_scope_higher_confidence', 0, 3, 1).
python_function('services/web/tests/test_prompt_router.py', 'test_shell_route', 0, 3, 1).
python_function('services/web/tests/test_prompt_router.py', 'test_discuss_defaults_nlp2dsl', 0, 4, 2).
python_function('services/web/tests/test_prompt_router.py', 'test_search_context_rag', 0, 3, 2).
python_function('services/web/tests/test_prompt_router.py', 'test_route_decision_to_dict', 0, 3, 2).
python_function('services/web/tests/test_prompt_router.py', 'test_extract_llm_json_handles_none_and_empty', 0, 4, 1).
python_function('services/web/tests/test_prompt_router.py', 'test_decide_route_sets_timing', 0, 3, 1).
python_function('services/web/tests/test_prompt_router_hybrid.py', '_analysis', 2, 1, 3).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_hybrid_nlp2cmd_prefers_shell_over_file_list', 1, 5, 5).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_hybrid_prefers_host_shell_for_lista_plikow_usera', 1, 4, 5).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_hybrid_keeps_file_list_when_registry_hint', 1, 2, 4).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_hybrid_without_nlp2cmd_falls_back_expectations', 1, 3, 4).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_local_sufficient_skips_openrouter', 1, 2, 6).
python_function('services/web/tests/test_prompt_router_hybrid.py', 'test_shell_nl_rules_local_route', 1, 3, 2).
python_function('services/web/tests/test_routing_contract.py', 'test_orientation_decision_from_dict', 0, 5, 1).
python_function('services/web/tests/test_routing_contract.py', 'test_route_from_orientation_registry', 0, 4, 2).
python_function('services/web/tests/test_routing_contract.py', 'test_route_from_orientation_shell_builtin', 0, 4, 2).
python_function('services/web/tests/test_routing_contract.py', 'test_route_from_orientation_shell_nl_pending', 0, 4, 2).
python_function('services/web/tests/test_routing_contract.py', 'test_orient_message_uses_cache', 0, 5, 4).
python_function('services/web/tests/test_routing_explain.py', 'test_explain_file_list_usera_selects_rules', 1, 8, 5).
python_function('services/web/tests/test_routing_explain.py', 'test_explain_disk_space_agent_shell', 0, 5, 3).
python_function('services/web/tests/test_routing_explain.py', 'test_align_file_list_route', 0, 5, 3).
python_function('services/web/tests/test_routing_feedback.py', 'feedback_store', 2, 1, 2).
python_function('services/web/tests/test_routing_feedback.py', 'test_record_good_feedback', 1, 4, 5).
python_function('services/web/tests/test_routing_feedback.py', 'test_record_bad_creates_improvement_ticket', 1, 4, 5).
python_function('services/web/tests/test_routing_feedback.py', 'test_aggregate_learnings_proposes_expectation', 1, 4, 6).
python_function('services/web/tests/test_routing_policy.py', 'test_load_default_policy', 0, 15, 6).
python_function('services/web/tests/test_routing_policy.py', 'test_session_agent_overrides_route', 0, 2, 2).
python_function('services/web/tests/test_routing_policy.py', 'test_mode_override_rag_only', 0, 2, 2).
python_function('services/web/tests/test_routing_policy.py', 'test_policy_to_dict', 0, 3, 2).
python_function('services/web/tests/test_routing_schemas.py', 'test_schemas_bundle_has_all_libraries', 0, 6, 1).
python_function('services/web/tests/test_routing_schemas.py', 'test_parse_nlp2cmd_response_rejects_invalid', 0, 7, 1).
python_function('services/web/tests/test_routing_schemas.py', 'test_parse_llm_classifier_valid_and_invalid', 0, 5, 1).
python_function('services/web/tests/test_routing_schemas.py', 'test_llm_prompt_embeds_json_schema', 0, 3, 1).
python_function('services/web/tests/test_routing_schemas.py', 'test_nlp_analysis_to_policy_flags', 0, 6, 5).
python_function('services/web/tests/test_shell_nl_intent.py', 'test_file_list_not_shell_nl', 0, 3, 2).
python_function('services/web/tests/test_shell_nl_intent.py', 'test_shell_nl_disk_intent', 0, 2, 1).
python_function('services/web/tests/test_shell_nl_intent.py', 'test_run_prefix_not_shell_nl', 0, 2, 1).
python_function('services/web/tests/test_ticket_schemas.py', 'test_ticket_schemas_bundle', 0, 4, 1).
python_function('services/web/tests/test_ticket_schemas.py', 'test_improvement_planfile_cmd', 0, 4, 2).
python_function('services/web/tests/test_ticket_schemas.py', 'test_sync_disabled_without_env', 0, 2, 2).
python_function('tests/conftest.py', 'fake_postgres', 0, 1, 1).
python_function('tests/conftest.py', 'fake_bus', 0, 1, 1).
python_function('tests/conftest.py', 'event_store', 1, 1, 1).
python_function('tests/conftest.py', 'catalog', 0, 1, 3).
python_function('tests/conftest.py', 'command_bus', 4, 1, 7).
python_function('tests/conftest.py', 'sample_command_id', 0, 1, 2).
python_function('tests/conftest.py', 'orchestrator_app', 4, 1, 2).
python_function('tests/conftest.py', 'api_client', 1, 1, 1).
python_function('tests/test_access_fabric.py', 'test_parse_and_build_uri', 0, 4, 2).
python_function('tests/test_access_fabric.py', 'test_localfs_probe_and_fetch', 1, 3, 7).
python_function('tests/test_access_fabric.py', 'test_register_and_transfer_resource', 2, 4, 5).
python_function('tests/test_agent_aggregate.py', 'test_register_agent', 0, 3, 2).
python_function('tests/test_agent_aggregate.py', 'test_assign_task_marks_busy', 0, 3, 3).
python_function('tests/test_agent_aggregate.py', 'test_disabled_agent_cannot_take_task', 0, 1, 5).
python_function('tests/test_api_orchestrator.py', 'test_health_not_on_minimal_app', 1, 4, 2).
python_function('tests/test_api_orchestrator.py', 'test_register_agent_api', 1, 2, 1).
python_function('tests/test_api_orchestrator.py', 'test_approval_api_flow', 1, 3, 2).
python_function('tests/test_api_orchestrator.py', 'test_plugin_api_flow', 1, 8, 2).
python_function('tests/test_api_orchestrator.py', 'test_workflow_version_api', 1, 5, 2).
python_function('tests/test_api_orchestrator.py', 'test_command_envelope', 1, 3, 2).
python_function('tests/test_approval_aggregate.py', 'test_approval_request_and_grant', 0, 3, 4).
python_function('tests/test_approval_aggregate.py', 'test_cannot_approve_twice', 0, 1, 3).
python_function('tests/test_approval_gate.py', 'test_activate_plugin_requires_approval', 1, 1, 2).
python_function('tests/test_approval_gate.py', 'test_activate_plugin_with_granted_approval', 1, 3, 1).
python_function('tests/test_approval_gate.py', 'test_skip_approval_for_dev', 1, 2, 2).
python_function('tests/test_approval_gate.py', 'test_ensure_approval_rejects_wrong_target', 1, 1, 3).
python_function('tests/test_command_bus.py', 'test_create_and_assign_task', 2, 4, 1).
python_function('tests/test_command_bus.py', 'test_register_agent_and_heartbeat', 1, 2, 1).
python_function('tests/test_command_bus.py', 'test_approval_flow', 1, 2, 1).
python_function('tests/test_command_bus.py', 'test_plugin_and_workflow_version_flow', 1, 1, 1).
python_function('tests/test_e2e_flow.py', 'test_full_task_lifecycle', 2, 8, 2).
python_function('tests/test_eventstore_factory.py', 'test_build_postgres_backend', 1, 3, 2).
python_function('tests/test_eventstore_factory.py', 'test_build_dual_without_esdb_falls_back', 1, 3, 2).
python_function('tests/test_evolution_layer.py', 'catalog', 0, 1, 3).
python_function('tests/test_evolution_layer.py', 'test_catalog_loads_events', 1, 5, 1).
python_function('tests/test_evolution_layer.py', 'test_catalog_graph', 1, 3, 1).
python_function('tests/test_evolution_layer.py', 'test_policy_requires_plugin_manifest', 1, 1, 3).
python_function('tests/test_evolution_layer.py', 'test_policy_accepts_full_manifest', 1, 1, 2).
python_function('tests/test_evolution_layer.py', 'test_shadow_workflow', 1, 3, 1).
python_function('tests/test_evolution_layer.py', 'test_propose_change', 1, 2, 1).
python_function('tests/test_incident_observability.py', 'test_observability_playbooks_are_exposed', 0, 3, 1).
python_function('tests/test_incident_observability.py', 'test_incident_recorder_publishes_projectable_events', 2, 14, 3).
python_function('tests/test_incident_observability.py', 'test_rag_search_failure_returns_incident_payload', 2, 7, 9).
python_function('tests/test_incident_observability.py', 'test_project_incidents_accepts_legacy_incident_code_payload', 0, 5, 3).
python_function('tests/test_incident_observability.py', '_load_project_incidents', 0, 2, 5).
python_function('tests/test_integration_postgres.py', 'live_command_bus', 0, 1, 5).
python_function('tests/test_integration_postgres.py', 'test_create_task_persisted', 1, 3, 3).
python_function('tests/test_plugin_aggregate.py', 'test_plugin_lifecycle', 0, 3, 6).
python_function('tests/test_plugin_aggregate.py', 'test_cannot_install_before_validate', 0, 1, 3).
python_function('tests/test_projections.py', '_project_event', 0, 8, 7).
python_function('tests/test_projections.py', '_event', 4, 1, 1).
python_function('tests/test_projections.py', 'test_task_created_updates_task_board_and_feed', 0, 4, 4).
python_function('tests/test_projections.py', 'test_approval_requested_projection', 0, 2, 4).
python_function('tests/test_projector_routes.py', '_projector_app', 0, 8, 7).
python_function('tests/test_projector_routes.py', 'test_projector_get_routes_are_unique', 0, 11, 6).
python_function('tests/test_rag.py', 'test_chunk_text_overlap', 0, 3, 3).
python_function('tests/test_rag.py', 'test_auto_ingest_on_register', 3, 5, 6).
python_function('tests/test_rag.py', 'test_rag_search_keyword', 1, 3, 7).
python_function('tests/test_rag.py', 'test_rag_ask_without_api_key', 1, 4, 7).
python_function('tests/test_rag.py', 'test_openrouter_embed_mock', 0, 2, 3).
python_function('tests/test_shell_executor.py', '_run_shell_command', 2, 8, 8).
python_function('tests/test_shell_executor.py', 'test_run_shell_command_success', 0, 3, 1).
python_function('tests/test_shell_executor.py', 'test_run_shell_command_failure', 0, 3, 1).
python_function('tests/test_shell_executor.py', 'test_run_shell_command_timeout', 0, 3, 3).
python_function('tests/test_task_aggregate.py', 'test_create_task_emits_task_created', 0, 4, 3).
python_function('tests/test_task_aggregate.py', 'test_assign_and_complete_lifecycle', 0, 3, 7).
python_function('tests/test_task_aggregate.py', 'test_cannot_complete_without_assignment', 0, 1, 3).
python_function('tests/test_task_aggregate.py', 'test_replay_from_events', 0, 3, 5).
python_function('tests/test_task_routing.py', 'test_pick_idle_agent', 1, 2, 2).
python_function('tests/test_task_routing.py', 'test_auto_assign_after_create', 1, 3, 1).
python_function('tests/test_workflow_aggregate.py', 'test_start_workflow', 0, 3, 2).
python_function('tests/test_workflow_aggregate.py', 'test_version_lifecycle', 0, 2, 4).

% ── Python Classes ───────────────────────────────────────
python_class('agents/shell-agent/app/executor.py', 'ShellResult').
python_method('ShellResult', 'ok', 0, 2, 0).
python_method('ShellResult', 'to_dict', 0, 1, 0).
python_class('agents/shell-agent/app/nats_consumer.py', 'ShellAgent').
python_method('ShellAgent', '__init__', 0, 1, 0).
python_method('ShellAgent', 'run', 0, 2, 5).
python_method('ShellAgent', 'handle_message', 1, 4, 8).
python_class('services/orchestrator/app/access/adapters/base.py', 'AdapterResult').
python_class('services/orchestrator/app/access/adapters/base.py', 'ResourceAdapter').
python_method('ResourceAdapter', 'probe', 1, 1, 0).
python_method('ResourceAdapter', 'fetch', 1, 1, 0).
python_method('ResourceAdapter', 'copy_to_local', 2, 1, 0).
python_class('services/orchestrator/app/access/adapters/http_adapter.py', 'HttpAdapter').
python_method('HttpAdapter', 'probe', 1, 3, 7).
python_method('HttpAdapter', 'fetch', 1, 2, 8).
python_method('HttpAdapter', 'copy_to_local', 2, 3, 4).
python_method('HttpAdapter', '_to_url', 1, 3, 0).
python_class('services/orchestrator/app/access/adapters/localfs.py', 'LocalFsAdapter').
python_method('LocalFsAdapter', '__init__', 1, 2, 2).
python_method('LocalFsAdapter', '_resolve', 1, 2, 4).
python_method('LocalFsAdapter', 'probe', 1, 4, 6).
python_method('LocalFsAdapter', 'fetch', 1, 4, 10).
python_method('LocalFsAdapter', 'copy_to_local', 2, 3, 8).
python_class('services/orchestrator/app/access/transport.py', 'TransportService').
python_method('TransportService', '__init__', 0, 1, 0).
python_method('TransportService', '_sandbox_dir', 0, 2, 2).
python_method('TransportService', 'probe', 1, 1, 4).
python_method('TransportService', 'fetch', 1, 1, 4).
python_method('TransportService', 'copy', 2, 4, 9).
python_method('TransportService', 'package_to_sandbox', 1, 1, 5).
python_method('TransportService', '_result_dict', 2, 2, 0).
python_class('services/orchestrator/app/access/uri.py', 'MullmUri').
python_method('MullmUri', 'canonical', 0, 2, 0).
python_class('services/orchestrator/app/api/access.py', 'RegisterResourceCommand').
python_class('services/orchestrator/app/api/access.py', 'TransferResourceCommand').
python_class('services/orchestrator/app/api/access.py', 'ProbeUriCommand').
python_class('services/orchestrator/app/api/commands.py', 'CommandEnvelope').
python_class('services/orchestrator/app/api/commands.py', 'CreateTaskCommand').
python_class('services/orchestrator/app/api/commands.py', 'AssignTaskCommand').
python_class('services/orchestrator/app/api/commands.py', 'StartTaskCommand').
python_class('services/orchestrator/app/api/commands.py', 'CompleteTaskCommand').
python_class('services/orchestrator/app/api/commands.py', 'FailTaskCommand').
python_class('services/orchestrator/app/api/commands.py', 'RegisterAgentCommand').
python_class('services/orchestrator/app/api/commands.py', 'StartWorkflowCommand').
python_class('services/orchestrator/app/api/commands.py', 'ProposeWorkflowVersionCommand').
python_class('services/orchestrator/app/api/commands.py', 'WorkflowVersionCommand').
python_class('services/orchestrator/app/api/commands.py', 'ProposePluginCommand').
python_class('services/orchestrator/app/api/commands.py', 'PluginIdCommand').
python_class('services/orchestrator/app/api/commands.py', 'CreateApprovalCommand').
python_class('services/orchestrator/app/api/commands.py', 'ApprovalActionCommand').
python_class('services/orchestrator/app/api/evolution.py', 'ProposeChangeCommand').
python_class('services/orchestrator/app/api/evolution.py', 'ShadowWorkflowCommand').
python_class('services/orchestrator/app/api/observability.py', 'DiagnoseBody').
python_class('services/orchestrator/app/api/queries.py', 'TaskQuery').
python_class('services/orchestrator/app/api/queries.py', 'AgentQuery').
python_class('services/orchestrator/app/api/queries.py', 'WorkflowQuery').
python_class('services/orchestrator/app/api/queries.py', 'TaskListQuery').
python_class('services/orchestrator/app/api/rag.py', 'SearchQuery').
python_class('services/orchestrator/app/api/rag.py', 'AskQuery').
python_class('services/orchestrator/app/application/command_bus.py', 'CommandBus').
python_method('CommandBus', '__init__', 2, 1, 0).
python_method('CommandBus', 'handle', 0, 4, 6).
python_method('CommandBus', 'handle_envelope', 1, 4, 2).
python_method('CommandBus', '_create_task', 4, 8, 12).
python_method('CommandBus', '_assign_task', 4, 3, 11).
python_method('CommandBus', '_start_task', 4, 1, 6).
python_method('CommandBus', '_complete_task', 4, 3, 11).
python_method('CommandBus', '_fail_task', 4, 2, 12).
python_method('CommandBus', '_register_agent', 4, 3, 7).
python_method('CommandBus', '_agent_heartbeat', 4, 2, 10).
python_method('CommandBus', '_start_workflow', 4, 3, 7).
python_method('CommandBus', '_propose_workflow_version', 4, 2, 4).
python_method('CommandBus', '_validate_workflow_version', 4, 1, 3).
python_method('CommandBus', '_approve_workflow_version', 4, 1, 4).
python_method('CommandBus', '_activate_workflow_version', 4, 3, 6).
python_method('CommandBus', '_rollback_workflow_version', 4, 1, 5).
python_method('CommandBus', '_shadow_workflow_version', 4, 2, 7).
python_method('CommandBus', '_propose_change', 4, 6, 9).
python_method('CommandBus', '_propose_plugin', 4, 3, 4).
python_method('CommandBus', '_validate_plugin', 4, 1, 3).
python_method('CommandBus', '_install_plugin', 4, 1, 3).
python_method('CommandBus', '_activate_plugin', 4, 1, 4).
python_method('CommandBus', '_rollback_plugin', 4, 1, 5).
python_method('CommandBus', '_create_approval', 4, 1, 3).
python_method('CommandBus', '_approve_request', 4, 3, 6).
python_method('CommandBus', '_reject_request', 4, 1, 4).
python_method('CommandBus', '_expire_approval', 4, 1, 3).
python_method('CommandBus', '_persist_workflow', 4, 1, 5).
python_method('CommandBus', '_persist_plugin', 4, 1, 5).
python_method('CommandBus', '_persist_approval', 4, 1, 5).
python_method('CommandBus', '_load_workflow', 1, 5, 6).
python_method('CommandBus', '_load_plugin', 1, 4, 5).
python_method('CommandBus', '_load_approval', 1, 2, 5).
python_method('CommandBus', '_load_task', 1, 2, 3).
python_method('CommandBus', '_append_and_publish', 3, 4, 4).
python_method('CommandBus', '_publish', 2, 2, 1).
python_method('CommandBus', '_apply_policy', 2, 2, 1).
python_method('CommandBus', '_register_resource', 4, 5, 10).
python_method('CommandBus', '_request_transfer', 4, 5, 15).
python_method('CommandBus', '_record_task_outcome', 1, 5, 5).
python_method('CommandBus', '_should_auto_rollback', 2, 4, 2).
python_method('CommandBus', '_rollback_workflow', 1, 1, 1).
python_method('CommandBus', '_result', 2, 3, 2).
python_class('services/orchestrator/app/application/sagas/approval_gate.py', 'ApprovalRequired').
python_method('ApprovalRequired', '__init__', 0, 1, 2).
python_class('services/orchestrator/app/config.py', 'Settings').
python_method('Settings', 'model_post_init', 1, 1, 1).
python_class('services/orchestrator/app/domain/aggregates/agent.py', 'Agent').
python_method('Agent', 'register', 5, 2, 4).
python_method('Agent', 'heartbeat', 1, 1, 3).
python_method('Agent', 'assign_task', 1, 2, 3).
python_method('Agent', 'mark_idle', 0, 1, 2).
python_method('Agent', 'get_uncommitted_events', 0, 1, 1).
python_method('Agent', 'mark_events_committed', 0, 1, 1).
python_class('services/orchestrator/app/domain/aggregates/approval.py', 'ApprovalStatus').
python_class('services/orchestrator/app/domain/aggregates/approval.py', 'Approval').
python_method('Approval', 'create_request', 1, 2, 6).
python_method('Approval', 'approve', 1, 2, 3).
python_method('Approval', 'reject', 2, 2, 3).
python_method('Approval', 'expire', 0, 2, 3).
python_method('Approval', 'get_uncommitted_events', 0, 1, 1).
python_method('Approval', 'mark_events_committed', 0, 1, 1).
python_class('services/orchestrator/app/domain/aggregates/plugin.py', 'PluginStatus').
python_class('services/orchestrator/app/domain/aggregates/plugin.py', 'Plugin').
python_method('Plugin', 'propose', 5, 2, 4).
python_method('Plugin', 'validate', 0, 2, 3).
python_method('Plugin', 'install', 0, 2, 3).
python_method('Plugin', 'activate', 0, 2, 3).
python_method('Plugin', 'rollback', 1, 2, 3).
python_method('Plugin', 'get_uncommitted_events', 0, 1, 1).
python_method('Plugin', 'mark_events_committed', 0, 1, 1).
python_class('services/orchestrator/app/domain/aggregates/resource.py', 'Resource').
python_method('Resource', 'register', 1, 3, 6).
python_method('Resource', 'request_transfer', 0, 1, 2).
python_method('Resource', 'complete_transfer', 2, 1, 2).
python_method('Resource', 'fail_transfer', 2, 1, 2).
python_method('Resource', 'get_uncommitted_events', 0, 1, 1).
python_method('Resource', 'mark_events_committed', 0, 1, 1).
python_class('services/orchestrator/app/domain/aggregates/task.py', 'Task').
python_method('Task', '__init__', 8, 4, 4).
python_method('Task', 'create', 8, 2, 3).
python_method('Task', 'from_events', 2, 2, 3).
python_method('Task', 'assign_to_agent', 1, 2, 4).
python_method('Task', 'start', 0, 3, 4).
python_method('Task', 'complete', 1, 2, 4).
python_method('Task', 'fail', 1, 2, 4).
python_method('Task', 'apply', 1, 2, 5).
python_method('Task', 'get_uncommitted_events', 0, 1, 1).
python_method('Task', 'mark_events_committed', 0, 1, 1).
python_method('Task', 'to_dict', 0, 3, 2).
python_class('services/orchestrator/app/domain/aggregates/workflow.py', 'Workflow').
python_method('Workflow', 'start', 4, 3, 4).
python_method('Workflow', 'propose_version', 4, 1, 4).
python_method('Workflow', 'validate_version', 0, 2, 3).
python_method('Workflow', 'approve_version', 1, 2, 3).
python_method('Workflow', 'shadow_version', 1, 2, 3).
python_method('Workflow', 'activate_version', 0, 2, 3).
python_method('Workflow', 'rollback_version', 1, 1, 2).
python_method('Workflow', 'get_uncommitted_events', 0, 1, 1).
python_method('Workflow', 'mark_events_committed', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/agents.py', 'AgentRegistered').
python_method('AgentRegistered', 'aggregate_id', 0, 1, 1).
python_method('AgentRegistered', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/agents.py', 'AgentHeartbeatReceived').
python_method('AgentHeartbeatReceived', 'aggregate_id', 0, 1, 1).
python_method('AgentHeartbeatReceived', 'data', 0, 1, 2).
python_class('services/orchestrator/app/domain/events/agents.py', 'TaskAssignedToAgent').
python_method('TaskAssignedToAgent', 'aggregate_id', 0, 1, 1).
python_method('TaskAssignedToAgent', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/agents.py', 'AgentMarkedIdle').
python_method('AgentMarkedIdle', 'aggregate_id', 0, 1, 1).
python_method('AgentMarkedIdle', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/approvals.py', 'ApprovalRequested').
python_method('ApprovalRequested', 'aggregate_id', 0, 1, 1).
python_method('ApprovalRequested', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/approvals.py', 'ApprovalGranted').
python_method('ApprovalGranted', 'aggregate_id', 0, 1, 1).
python_method('ApprovalGranted', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/approvals.py', 'ApprovalRejected').
python_method('ApprovalRejected', 'aggregate_id', 0, 1, 1).
python_method('ApprovalRejected', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/approvals.py', 'ApprovalExpired').
python_method('ApprovalExpired', 'aggregate_id', 0, 1, 1).
python_method('ApprovalExpired', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/approvals.py', 'ChangeProposed').
python_method('ChangeProposed', 'aggregate_id', 0, 1, 0).
python_method('ChangeProposed', 'data', 0, 2, 0).
python_class('services/orchestrator/app/domain/events/base.py', 'DomainEvent').
python_method('DomainEvent', 'aggregate_id', 0, 1, 0).
python_method('DomainEvent', 'data', 0, 1, 0).
python_method('DomainEvent', 'to_message', 0, 3, 3).
python_class('services/orchestrator/app/domain/events/incidents.py', 'RagRequestFailed').
python_method('RagRequestFailed', 'aggregate_id', 0, 1, 0).
python_method('RagRequestFailed', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'IncidentDetected').
python_method('IncidentDetected', 'aggregate_id', 0, 1, 0).
python_method('IncidentDetected', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'IncidentClassified').
python_method('IncidentClassified', 'aggregate_id', 0, 1, 0).
python_method('IncidentClassified', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'DiagnosticsStarted').
python_method('DiagnosticsStarted', 'aggregate_id', 0, 1, 0).
python_method('DiagnosticsStarted', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'DiagnosticsCompleted').
python_method('DiagnosticsCompleted', 'aggregate_id', 0, 1, 0).
python_method('DiagnosticsCompleted', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'RemediationStarted').
python_method('RemediationStarted', 'aggregate_id', 0, 1, 0).
python_method('RemediationStarted', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'RemediationSucceeded').
python_method('RemediationSucceeded', 'aggregate_id', 0, 1, 0).
python_method('RemediationSucceeded', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'RemediationFailed').
python_method('RemediationFailed', 'aggregate_id', 0, 1, 0).
python_method('RemediationFailed', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'PostRemediationVerificationPassed').
python_method('PostRemediationVerificationPassed', 'aggregate_id', 0, 1, 0).
python_method('PostRemediationVerificationPassed', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/incidents.py', 'PostRemediationVerificationFailed').
python_method('PostRemediationVerificationFailed', 'aggregate_id', 0, 1, 0).
python_method('PostRemediationVerificationFailed', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/plugins.py', 'PluginProposed').
python_method('PluginProposed', 'aggregate_id', 0, 1, 1).
python_method('PluginProposed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/plugins.py', 'PluginValidated').
python_method('PluginValidated', 'aggregate_id', 0, 1, 1).
python_method('PluginValidated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/plugins.py', 'PluginInstalled').
python_method('PluginInstalled', 'aggregate_id', 0, 1, 1).
python_method('PluginInstalled', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/plugins.py', 'PluginActivated').
python_method('PluginActivated', 'aggregate_id', 0, 1, 1).
python_method('PluginActivated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/plugins.py', 'PluginRolledBack').
python_method('PluginRolledBack', 'aggregate_id', 0, 1, 1).
python_method('PluginRolledBack', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/resources.py', 'CapabilityRegistered').
python_method('CapabilityRegistered', 'aggregate_id', 0, 1, 0).
python_method('CapabilityRegistered', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/resources.py', 'ResourceRegistered').
python_method('ResourceRegistered', 'aggregate_id', 0, 1, 1).
python_method('ResourceRegistered', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/resources.py', 'TransferRequested').
python_method('TransferRequested', 'aggregate_id', 0, 1, 1).
python_method('TransferRequested', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/resources.py', 'TransferCompleted').
python_method('TransferCompleted', 'aggregate_id', 0, 1, 1).
python_method('TransferCompleted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/resources.py', 'TransferFailed').
python_method('TransferFailed', 'aggregate_id', 0, 1, 1).
python_method('TransferFailed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/tasks.py', 'TaskCreated').
python_method('TaskCreated', 'aggregate_id', 0, 1, 1).
python_method('TaskCreated', 'data', 0, 2, 2).
python_class('services/orchestrator/app/domain/events/tasks.py', 'TaskAssigned').
python_method('TaskAssigned', 'aggregate_id', 0, 1, 1).
python_method('TaskAssigned', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/tasks.py', 'TaskStarted').
python_method('TaskStarted', 'aggregate_id', 0, 1, 1).
python_method('TaskStarted', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/tasks.py', 'TaskCompleted').
python_method('TaskCompleted', 'aggregate_id', 0, 1, 1).
python_method('TaskCompleted', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/tasks.py', 'TaskFailed').
python_method('TaskFailed', 'aggregate_id', 0, 1, 1).
python_method('TaskFailed', 'data', 0, 2, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowStarted').
python_method('WorkflowStarted', 'aggregate_id', 0, 1, 1).
python_method('WorkflowStarted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionProposed').
python_method('WorkflowVersionProposed', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionProposed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionValidated').
python_method('WorkflowVersionValidated', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionValidated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionApproved').
python_method('WorkflowVersionApproved', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionApproved', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionShadowed').
python_method('WorkflowVersionShadowed', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionShadowed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionActivated').
python_method('WorkflowVersionActivated', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionActivated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/workflows.py', 'WorkflowVersionRolledBack').
python_method('WorkflowVersionRolledBack', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionRolledBack', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'TaskId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'AgentId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'WorkflowId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'PluginId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'ApprovalId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'ResourceId').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'Priority').
python_method('Priority', 'from_value', 2, 4, 5).
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'TaskStatus').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'ExecutionMode').
python_method('ExecutionMode', 'from_value', 2, 4, 5).
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'AgentStatus').
python_class('services/orchestrator/app/domain/value_objects/__init__.py', 'WorkflowStatus').
python_class('services/orchestrator/app/evolution/catalog.py', 'ArchitectureCatalog').
python_method('ArchitectureCatalog', '__init__', 1, 4, 5).
python_method('ArchitectureCatalog', '_load_json', 1, 3, 3).
python_method('ArchitectureCatalog', 'index', 0, 1, 1).
python_method('ArchitectureCatalog', 'domains', 0, 1, 1).
python_method('ArchitectureCatalog', 'capabilities', 0, 1, 1).
python_method('ArchitectureCatalog', 'services', 0, 1, 1).
python_method('ArchitectureCatalog', 'policies', 0, 1, 1).
python_method('ArchitectureCatalog', 'list_events', 0, 4, 7).
python_method('ArchitectureCatalog', 'get_event_schema', 1, 3, 2).
python_method('ArchitectureCatalog', 'get_capability', 1, 3, 1).
python_method('ArchitectureCatalog', 'as_graph', 0, 1, 4).
python_class('services/orchestrator/app/evolution/evaluation.py', 'EvaluationEngine').
python_method('EvaluationEngine', '__init__', 1, 1, 0).
python_method('EvaluationEngine', 'record_task_outcome', 0, 4, 1).
python_method('EvaluationEngine', '_upsert_metrics', 0, 2, 4).
python_method('EvaluationEngine', '_current_metrics_row', 3, 1, 1).
python_method('EvaluationEngine', '_update_metrics', 1, 6, 2).
python_method('EvaluationEngine', '_insert_metrics', 0, 2, 3).
python_method('EvaluationEngine', 'should_auto_rollback', 2, 2, 2).
python_class('services/orchestrator/app/evolution/experiments.py', 'ExperimentManager').
python_method('ExperimentManager', '__init__', 1, 1, 0).
python_method('ExperimentManager', 'start_experiment', 0, 2, 5).
python_method('ExperimentManager', 'complete_experiment', 1, 2, 3).
python_method('ExperimentManager', 'active_shadow', 1, 2, 2).
python_class('services/orchestrator/app/evolution/policy_engine.py', 'PolicyViolation').
python_method('PolicyViolation', '__init__', 2, 2, 2).
python_class('services/orchestrator/app/evolution/policy_engine.py', 'PolicyEngine').
python_method('PolicyEngine', '__init__', 1, 2, 1).
python_method('PolicyEngine', 'rule_for', 1, 1, 1).
python_method('PolicyEngine', 'validate_command', 2, 2, 4).
python_method('PolicyEngine', '_validate_environment', 3, 3, 2).
python_method('PolicyEngine', '_validate_manifest', 3, 6, 3).
python_method('PolicyEngine', '_validate_auto_risk', 3, 6, 3).
python_method('PolicyEngine', 'validate_activation_metrics', 3, 5, 7).
python_class('services/orchestrator/app/incidents/pipeline.py', 'IncidentPipeline').
python_method('IncidentPipeline', '__init__', 0, 1, 0).
python_method('IncidentPipeline', 'handle_rag_failure', 0, 2, 9).
python_class('services/orchestrator/app/infrastructure/eventstore.py', 'EventRecord').
python_method('EventRecord', 'to_message', 0, 1, 1).
python_class('services/orchestrator/app/infrastructure/eventstore.py', 'EventStore').
python_method('EventStore', '__init__', 1, 1, 0).
python_method('EventStore', 'append', 3, 6, 12).
python_method('EventStore', 'get_events_for_aggregate', 2, 2, 2).
python_method('EventStore', 'get_aggregate_ids', 1, 2, 1).
python_method('EventStore', 'all_events', 0, 2, 2).
python_method('EventStore', '_record_from_row', 1, 1, 2).
python_class('services/orchestrator/app/infrastructure/eventstore_dual.py', 'DualEventStore').
python_method('DualEventStore', '__init__', 2, 1, 0).
python_method('DualEventStore', 'append', 3, 2, 1).
python_method('DualEventStore', 'get_events_for_aggregate', 2, 1, 1).
python_method('DualEventStore', 'get_aggregate_ids', 1, 1, 1).
python_method('DualEventStore', 'all_events', 0, 1, 1).
python_class('services/orchestrator/app/infrastructure/eventstore_esdb.py', 'EsdbEventStore').
python_method('EsdbEventStore', '__init__', 1, 1, 1).
python_method('EsdbEventStore', 'connect', 0, 2, 3).
python_method('EsdbEventStore', 'disconnect', 0, 3, 2).
python_method('EsdbEventStore', 'append', 3, 3, 20).
python_method('EsdbEventStore', 'get_events_for_aggregate', 2, 2, 11).
python_method('EsdbEventStore', 'get_aggregate_ids', 1, 2, 9).
python_method('EsdbEventStore', 'all_events', 0, 1, 0).
python_class('services/orchestrator/app/infrastructure/nats_bus.py', 'NATSBus').
python_method('NATSBus', '__init__', 1, 1, 0).
python_method('NATSBus', 'connect', 0, 3, 3).
python_method('NATSBus', 'disconnect', 0, 3, 1).
python_method('NATSBus', 'publish', 2, 4, 4).
python_method('NATSBus', 'subscribe', 2, 3, 1).
python_class('services/orchestrator/app/infrastructure/postgres.py', 'PostgresConnection').
python_method('PostgresConnection', '__init__', 1, 1, 0).
python_method('PostgresConnection', 'connect', 0, 2, 3).
python_method('PostgresConnection', 'disconnect', 0, 2, 1).
python_method('PostgresConnection', 'execute', 1, 2, 3).
python_method('PostgresConnection', 'fetch', 1, 2, 3).
python_method('PostgresConnection', 'fetchrow', 1, 2, 3).
python_method('PostgresConnection', '_run_schema_migrations', 0, 5, 10).
python_class('services/orchestrator/app/observability/incidents.py', 'IncidentCode').
python_class('services/orchestrator/app/observability/incidents.py', 'IncidentRecorder').
python_method('IncidentRecorder', 'record', 0, 2, 5).
python_method('IncidentRecorder', '_persist', 1, 2, 3).
python_method('IncidentRecorder', '_publish_event', 2, 3, 6).
python_class('services/orchestrator/app/observability/middleware.py', 'CorrelationMiddleware').
python_method('CorrelationMiddleware', 'dispatch', 2, 3, 4).
python_class('services/orchestrator/app/observability/rag_diagnostics.py', 'RagDiagnostics').
python_method('RagDiagnostics', 'run', 0, 3, 16).
python_method('RagDiagnostics', '_check_postgres', 0, 4, 2).
python_method('RagDiagnostics', '_check_rag_tables', 0, 5, 2).
python_method('RagDiagnostics', '_check_openrouter_config', 0, 2, 0).
python_method('RagDiagnostics', '_check_embedding', 0, 3, 3).
python_method('RagDiagnostics', '_check_search', 1, 3, 3).
python_method('RagDiagnostics', '_recommendations', 1, 6, 2).
python_method('RagDiagnostics', '_snapshot', 1, 2, 5).
python_class('services/orchestrator/app/observability/rag_pipeline.py', 'RagPipeline').
python_method('RagPipeline', 'ask', 0, 5, 12).
python_method('RagPipeline', '_step_recorder', 1, 1, 4).
python_method('RagPipeline', '_diagnostics_if_enabled', 3, 2, 2).
python_method('RagPipeline', '_retriever_result', 3, 3, 4).
python_method('RagPipeline', '_exception_payload', 1, 1, 5).
python_method('RagPipeline', '_fallback_payload_if_needed', 1, 5, 4).
python_method('RagPipeline', '_llm_error_payload', 1, 2, 6).
python_method('RagPipeline', '_empty_result_payload', 1, 1, 3).
python_method('RagPipeline', '_failure_payload', 0, 1, 1).
python_class('services/orchestrator/app/rag/indexer.py', 'RagIndexer').
python_method('RagIndexer', '__init__', 3, 1, 0).
python_method('RagIndexer', 'ingest_resource', 0, 2, 12).
python_method('RagIndexer', '_fetch_body', 1, 5, 4).
python_method('RagIndexer', '_embed_chunks', 1, 5, 3).
python_class('services/orchestrator/app/rag/openrouter.py', 'OpenRouterClient').
python_method('OpenRouterClient', '__init__', 1, 2, 2).
python_method('OpenRouterClient', 'configured', 0, 1, 1).
python_method('OpenRouterClient', '_headers', 0, 1, 0).
python_method('OpenRouterClient', 'embed', 1, 5, 9).
python_method('OpenRouterClient', 'chat', 1, 4, 6).
python_method('OpenRouterClient', '_post_chat', 3, 1, 3).
python_method('OpenRouterClient', 'health', 0, 1, 0).
python_class('services/orchestrator/app/rag/retriever.py', 'RagRetriever').
python_method('RagRetriever', '__init__', 2, 1, 0).
python_method('RagRetriever', 'search', 1, 4, 2).
python_method('RagRetriever', 'ask', 1, 5, 7).
python_class('services/orchestrator/app/rag/store.py', 'RagStore').
python_method('RagStore', '__init__', 1, 1, 0).
python_method('RagStore', 'upsert_document_pending', 0, 1, 1).
python_method('RagStore', 'mark_indexed', 0, 1, 1).
python_method('RagStore', 'mark_failed', 0, 1, 1).
python_method('RagStore', 'replace_chunks', 0, 3, 4).
python_method('RagStore', 'list_documents', 0, 2, 2).
python_method('RagStore', 'search', 1, 5, 5).
python_method('RagStore', '_vector_search', 1, 3, 2).
python_method('RagStore', '_fts_search', 1, 1, 1).
python_method('RagStore', '_keyword_fallback', 1, 3, 3).
python_class('services/orchestrator/tests/fakes.py', 'FakeEventStore').
python_method('FakeEventStore', '__init__', 0, 1, 1).
python_method('FakeEventStore', 'append', 3, 4, 9).
python_method('FakeEventStore', 'get_events_for_aggregate', 2, 1, 0).
python_method('FakeEventStore', 'get_aggregate_ids', 1, 3, 1).
python_class('services/orchestrator/tests/fakes.py', 'FakeMessageBus').
python_method('FakeMessageBus', '__init__', 0, 1, 0).
python_method('FakeMessageBus', 'publish', 2, 1, 1).
python_class('services/orchestrator/tests/test_api.py', 'StubCommandBus').
python_method('StubCommandBus', '__init__', 0, 1, 0).
python_method('StubCommandBus', 'handle', 0, 1, 1).
python_method('StubCommandBus', 'handle_envelope', 1, 2, 2).
python_class('services/orchestrator/tests/test_api.py', 'StubEventStore').
python_method('StubEventStore', 'get_events_for_aggregate', 2, 2, 2).
python_method('StubEventStore', 'get_aggregate_ids', 1, 1, 0).
python_class('services/projector/app/db.py', 'Database').
python_method('Database', '__init__', 1, 1, 0).
python_method('Database', 'connect', 0, 2, 3).
python_method('Database', 'disconnect', 0, 2, 1).
python_method('Database', 'execute', 1, 2, 3).
python_method('Database', 'fetch', 1, 2, 3).
python_method('Database', '_run_schema_migrations', 0, 4, 10).
python_class('services/web/app/agent_plugins/nlp2cmd_plugin.py', 'Nlp2CmdPlugin').
python_method('Nlp2CmdPlugin', 'health', 0, 4, 3).
python_method('Nlp2CmdPlugin', 'translate_shell', 1, 2, 2).
python_method('Nlp2CmdPlugin', 'analyze_shell_nl', 1, 9, 11).
python_class('services/web/app/agent_plugins/nlp2dsl_plugin.py', 'Nlp2DslPlugin').
python_method('Nlp2DslPlugin', 'health', 0, 1, 1).
python_method('Nlp2DslPlugin', 'translate_shell', 1, 1, 0).
python_class('services/web/app/agent_plugins/protocol.py', 'ShellTranslation').
python_method('ShellTranslation', 'from_validated_analysis', 2, 4, 6).
python_class('services/web/app/agent_plugins/protocol.py', 'AgentPlugin').
python_method('AgentPlugin', 'plugin_id', 0, 1, 0).
python_method('AgentPlugin', 'title', 0, 1, 0).
python_method('AgentPlugin', 'executor_agent_id', 0, 1, 0).
python_method('AgentPlugin', 'ingress_steps', 0, 1, 0).
python_method('AgentPlugin', 'route_kinds', 0, 1, 0).
python_method('AgentPlugin', 'health', 0, 1, 0).
python_method('AgentPlugin', 'translate_shell', 1, 1, 0).
python_class('services/web/app/agent_workroom.py', 'LedgerEntry').
python_method('LedgerEntry', 'to_dict', 0, 2, 0).
python_class('services/web/app/agent_workroom.py', 'WorkroomSession').
python_method('WorkroomSession', 'add_ledger', 3, 1, 2).
python_method('WorkroomSession', 'agent_say', 3, 1, 2).
python_method('WorkroomSession', 'to_dict', 0, 2, 1).
python_class('services/web/app/api/models.py', 'ChatSessionStart').
python_class('services/web/app/api/models.py', 'ChatMessage').
python_class('services/web/app/api/models.py', 'TaskDraftRequest').
python_class('services/web/app/api/models.py', 'CreateTaskBody').
python_class('services/web/app/api/models.py', 'CreateFromDraftBody').
python_class('services/web/app/api/models.py', 'ConfirmTicketBody').
python_class('services/web/app/api/models.py', 'SessionRef').
python_class('services/web/app/api/models.py', 'ContextAttachBody').
python_class('services/web/app/api/models.py', 'WorkroomStart').
python_class('services/web/app/api/models.py', 'WorkroomMessage').
python_class('services/web/app/api/models.py', 'RoutingFeedbackBody').
python_class('services/web/app/api/models.py', 'AccessMatrixBody').
python_class('services/web/app/conductor.py', 'TurnState').
python_class('services/web/app/local_orient.py', 'OrientationResult').
python_method('OrientationResult', 'to_dict', 0, 1, 0).
python_class('services/web/app/prompt_router.py', 'RouteDecision').
python_method('RouteDecision', 'to_dict', 0, 1, 1).
python_class('services/web/app/routing/decision.py', 'OrientationDecision').
python_method('OrientationDecision', 'from_dict', 2, 11, 5).
python_method('OrientationDecision', 'to_dict', 0, 1, 1).
python_method('OrientationDecision', 'is_actionable', 0, 1, 0).
python_method('OrientationDecision', 'shell_translation_source', 0, 3, 0).
python_class('services/web/app/routing_feedback.py', 'RoutingFeedbackRecord').
python_method('RoutingFeedbackRecord', 'to_dict', 0, 1, 0).
python_class('services/web/app/routing_policy.py', 'RagProbeSettings').
python_class('services/web/app/routing_policy.py', 'RoutingPolicy').
python_method('RoutingPolicy', 'ingress_for_mode', 1, 4, 2).
python_method('RoutingPolicy', 'agent_for_route', 1, 4, 1).
python_method('RoutingPolicy', 'to_dict', 0, 1, 0).
python_class('services/web/app/routing_schemas.py', 'Nlp2CmdQueryRequest').
python_class('services/web/app/routing_schemas.py', 'Nlp2CmdQueryResponse').
python_method('Nlp2CmdQueryResponse', 'command_text', 0, 2, 1).
python_class('services/web/app/routing_schemas.py', 'LlmRouteClassifierOutput').
python_class('services/web/app/routing_schemas.py', 'NlpCommandAnalysis').
python_method('NlpCommandAnalysis', 'to_shell_translation', 0, 1, 1).
python_method('NlpCommandAnalysis', 'to_policy_flags', 0, 4, 2).
python_class('services/web/app/routing_trace.py', 'TraceCheck').
python_method('TraceCheck', 'to_dict', 0, 2, 0).
python_class('services/web/app/routing_trace.py', 'TraceStep').
python_method('TraceStep', 'to_dict', 0, 2, 1).
python_class('services/web/app/routing_trace.py', 'DecisionTree').
python_method('DecisionTree', 'to_dict', 0, 2, 1).
python_class('services/web/app/ticket_schemas.py', 'MullmTicketRef').
python_class('services/web/app/ticket_schemas.py', 'ExecutionTicketCreate').
python_class('services/web/app/ticket_schemas.py', 'ImprovementTicket').
python_method('ImprovementTicket', 'planfile_title', 0, 3, 0).
python_method('ImprovementTicket', 'planfile_description', 0, 5, 3).
python_method('ImprovementTicket', 'planfile_labels', 0, 3, 1).
python_class('services/web/app/ticket_schemas.py', 'WorkflowTicketRef').
python_class('services/web/app/workspace.py', 'WorkspaceContext').
python_method('WorkspaceContext', 'to_dict', 0, 1, 0).
python_class('services/web/app/workspace.py', 'WorkspaceSession').
python_method('WorkspaceSession', 'add_event', 2, 2, 2).
python_class('services/web/tests/test_e2e_chat_api.py', 'TestE2EChatRoutingApi').
python_method('TestE2EChatRoutingApi', 'test_host_file_list_via_orient', 2, 5, 4).
python_method('TestE2EChatRoutingApi', 'test_registry_file_list_full_api_path', 3, 9, 4).
python_method('TestE2EChatRoutingApi', 'test_file_list_registry_scope_stays_mullm_file_list', 3, 4, 3).
python_method('TestE2EChatRoutingApi', 'test_router_file_list_rules_mode', 1, 3, 2).
python_method('TestE2EChatRoutingApi', 'test_router_run_ls_home_is_shell', 1, 3, 2).
python_method('TestE2EChatRoutingApi', 'test_continue_clarify_not_unknown', 3, 5, 3).
python_method('TestE2EChatRoutingApi', 'test_router_decide_dry_run_file_list', 1, 4, 2).
python_method('TestE2EChatRoutingApi', 'test_routing_feedback_on_turn', 3, 5, 5).
python_method('TestE2EChatRoutingApi', 'test_routing_explain_file_list_tree', 2, 7, 5).
python_method('TestE2EChatRoutingApi', 'test_routing_schemas_endpoint', 1, 5, 2).
python_method('TestE2EChatRoutingApi', 'test_routing_policy_endpoint', 1, 7, 3).
python_method('TestE2EChatRoutingApi', 'test_agents_status_endpoint', 1, 5, 2).
python_method('TestE2EChatRoutingApi', 'test_shell_nl_uses_nlp2cmd_plugin', 4, 8, 3).
python_class('tests/conftest.py', 'FakeRow').
python_method('FakeRow', '__getitem__', 1, 1, 0).
python_method('FakeRow', 'get', 2, 1, 1).
python_method('FakeRow', 'keys', 0, 1, 1).
python_class('tests/conftest.py', 'InMemoryPostgres').
python_method('InMemoryPostgres', '__init__', 0, 1, 0).
python_method('InMemoryPostgres', 'connect', 0, 1, 0).
python_method('InMemoryPostgres', 'disconnect', 0, 1, 0).
python_method('InMemoryPostgres', 'execute', 1, 22, 4).
python_method('InMemoryPostgres', 'fetchrow', 1, 6, 3).
python_method('InMemoryPostgres', 'fetch', 1, 38, 13).
python_method('InMemoryPostgres', '_event_row', 1, 1, 1).
python_class('tests/conftest.py', 'FakeMessageBus').
python_method('FakeMessageBus', '__init__', 0, 1, 0).
python_method('FakeMessageBus', 'publish', 2, 1, 1).
python_class('tests/test_incident_observability.py', 'RecordingDb').
python_method('RecordingDb', '__init__', 0, 1, 0).
python_method('RecordingDb', 'execute', 1, 1, 1).
python_class('tests/test_projections.py', 'RecordingDB').
python_method('RecordingDB', '__init__', 0, 1, 0).
python_method('RecordingDB', 'execute', 1, 1, 2).

% ── Dependencies ─────────────────────────────────────────
project_dependency('pytest==8.3.3', 'requirements-dev.txt').
project_dependency('pytest-asyncio==0.24.0', 'requirements-dev.txt').
project_dependency('httpx==0.27.2', 'requirements-dev.txt').
project_dependency('fastapi==0.104.1', 'requirements-dev.txt').
project_dependency('starlette==0.27.0', 'requirements-dev.txt').
project_dependency('anyio>=3.7.1,<4.0.0', 'requirements-dev.txt').
project_dependency('typer>=0.12.0,<1.0', 'requirements-quality.txt').
project_dependency('rich>=13.0', 'requirements-quality.txt').

% ── Makefile Targets ─────────────────────────────────────
makefile_target('SHELL', '').
makefile_target('PROFILE_ARGS', '').
makefile_target('help', '').
makefile_target('NLP2CMD_PROFILE_ARGS', '').
makefile_target('up', '').
makefile_target('down', '').
makefile_target('restart', '').
makefile_target('build', '').
makefile_target('logs', '').
makefile_target('ps', '').
makefile_target('test', '').
makefile_target('test-web', '').
makefile_target('test-e2e-live', '').
makefile_target('test-quality', '').
makefile_target('test-quality-deps', '').
makefile_target('propact-pact', '').
makefile_target('mullm-cli', '').
makefile_target('smoke', '').
makefile_target('ensure-env', '').
makefile_target('ensure-nlp2dsl-env', '').
makefile_target('nlp2dsl-up', '').
makefile_target('nlp2dsl-down', '').
makefile_target('nlp2cmd-up', '').
makefile_target('nlp2cmd-down', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('COMPOSE_PROFILES', 'core,web', 'Docker Compose — bez tego: `docker compose up -d` → „no service selected”').
env_variable('OPENROUTER_API_KEY', '*(not set)*', '--- OpenRouter (RAG) ---').
env_variable('LLM_MODEL', 'deepseek/deepseek-v4-pro', 'Lokalnie możesz użyć prefiksu openrouter/ — API normalizuje do deepseek/...').
env_variable('EMBEDDING_MODEL', 'openai/text-embedding-3-small', '').
env_variable('RAG_AUTO_INGEST', 'true', '').
env_variable('POSTGRES_DB', 'mullm', '--- Postgres credentials ---').
env_variable('POSTGRES_USER', 'mullm', '').
env_variable('POSTGRES_PASSWORD', 'mullm_password', '').
env_variable('MULLM_POSTGRES_HOST', 'postgres', '--- Docker: service hostnames (internal DNS) ---').
env_variable('MULLM_NATS_HOST', 'nats', '').
env_variable('MULLM_REDIS_HOST', 'redis', '').
env_variable('MULLM_EVENTSTORE_HOST', 'eventstoredb', '').
env_variable('MULLM_ORCHESTRATOR_HOST', 'orchestrator', '').
env_variable('MULLM_PROJECTOR_HOST', 'projector', '').
env_variable('MULLM_POSTGRES_PORT', '5432', '--- Docker: container (internal) ports ---').
env_variable('MULLM_NATS_CLIENT_PORT', '4222', '').
env_variable('MULLM_NATS_MONITOR_PORT', '8222', '').
env_variable('MULLM_REDIS_PORT', '6379', '').
env_variable('MULLM_EVENTSTORE_PORT', '2113', '').
env_variable('MULLM_ORCHESTRATOR_PORT', '8000', '').
env_variable('MULLM_PROJECTOR_PORT', '8000', '').
env_variable('MULLM_WEB_PORT', '3000', '').
env_variable('MULLM_POSTGRES_HOST_PORT', '5433', '--- Host-published ports (localhost) ---').
env_variable('MULLM_NATS_CLIENT_HOST_PORT', '4222', '').
env_variable('MULLM_NATS_MONITOR_HOST_PORT', '8222', '').
env_variable('MULLM_REDIS_HOST_PORT', '6379', '').
env_variable('MULLM_EVENTSTORE_HOST_PORT', '2113', '').
env_variable('MULLM_ORCHESTRATOR_HOST_PORT', '8001', '').
env_variable('MULLM_PROJECTOR_HOST_PORT', '8002', '').
env_variable('MULLM_WEB_HOST_PORT', '3003', '').
env_variable('DATABASE_URL', 'postgresql://mullm:mullm_password@localhost:5433/mullm', '--- URLs: from host / local dev ---').
env_variable('NATS_URL', 'nats://localhost:4222', '').
env_variable('REDIS_URL', 'redis://localhost:6379', '').
env_variable('EVENTSTORE_URL', 'esdb://localhost:2113?tls=false', '').
env_variable('ORCHESTRATOR_URL', 'http://localhost:8001', '').
env_variable('PROJECTOR_URL', 'http://localhost:8002', '').
env_variable('WEB_URL', 'http://localhost:3003', '').
env_variable('MULLM_DATABASE_URL', 'postgresql://mullm:mullm_password@postgres:5432/mullm', '--- URLs: inside Docker network (used by compose services) ---').
env_variable('MULLM_NATS_URL', 'nats://nats:4222', '').
env_variable('MULLM_REDIS_URL', 'redis://redis:6379', '').
env_variable('MULLM_EVENTSTORE_URL', 'esdb://eventstoredb:2113?tls=false', '').
env_variable('MULLM_ORCHESTRATOR_URL', 'http://orchestrator:8000', '').
env_variable('MULLM_PROJECTOR_URL', 'http://projector:8000', '').
env_variable('MULLM_NLP2DSL_BACKEND_HOST_PORT', '8010', 'lub: docker compose --profile nlp2dsl up -d (z katalogu mullm)').
env_variable('MULLM_NLP2DSL_NLP_HOST_PORT', '8012', '').
env_variable('NLP2DSL_BACKEND_URL', 'http://localhost:8010', '').
env_variable('MULLM_NLP2DSL_BACKEND_URL', 'http://nlp2dsl-backend:8000', '').
env_variable('MULLM_NLP2CMD_HOST_PORT', '8020', 'Uruchom: NLP2CMD=1 make up  lub  make nlp2cmd-up').
env_variable('NLP2CMD_BACKEND_URL', 'http://localhost:8020', '').
env_variable('MULLM_NLP2CMD_BACKEND_URL', 'http://nlp2cmd:8000', '').
env_variable('PROMPT_ROUTER_MODE', 'auto', 'auto = hybrid gdy nlp2cmd/OpenRouter dostępne; rules = tylko regex; llm = reguły+LLM').
env_variable('MULLM_ROUTING_NLP2CMD', '1', '').
env_variable('MULLM_ROUTING_NLP2CMD_MIN_CONFIDENCE', '0.65', '').
env_variable('MULLM_SHELL_WAIT_SECONDS', '20', 'Czekaj na stdout shell w tej samej odpowiedzi czatu (0 = tylko ticket, wynik w ◎)').
env_variable('CATALOG_PATH', '*(not set)*', '--- App ---').
env_variable('ENVIRONMENT', 'development', '').
env_variable('EVENT_STORE_BACKEND', 'postgres', '').
env_variable('LOG_LEVEL', 'INFO', '').
env_variable('AGENT_ID', 'shell-agent-1', '').
env_variable('JWT_SECRET', 'your_jwt_secret_here', '').
env_variable('API_KEY', 'your_api_key_here', '').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-api-smoke.testql.toon.yaml', 'api').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-api-smoke.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('api', '').
sumd_workflow('up', 'manual').
sumd_workflow_step('up', 1, '$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) up -d').
sumd_workflow_step('up', 2, 'if [ "$(NLP2DSL)" = "1" ]').
sumd_workflow_step('up', 3, '$(MAKE) --no-print-directory nlp2dsl-up').
sumd_workflow_step('up', 4, 'fi').
sumd_workflow('down', 'manual').
sumd_workflow_step('down', 1, 'if [ "$(NLP2DSL)" = "1" ]').
sumd_workflow_step('down', 2, '$(MAKE) --no-print-directory nlp2dsl-down').
sumd_workflow_step('down', 3, 'fi').
sumd_workflow_step('down', 4, '$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) down').
sumd_workflow('restart', 'manual').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, '$(COMPOSE) $(PROFILE_ARGS) build').
sumd_workflow('logs', 'manual').
sumd_workflow_step('logs', 1, '$(COMPOSE) $(PROFILE_ARGS) logs -f --tail=200').
sumd_workflow('ps', 'manual').
sumd_workflow_step('ps', 1, '$(COMPOSE) $(PROFILE_ARGS) ps').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'pytest -q').
sumd_workflow('test-web', 'manual').
sumd_workflow_step('test-web', 1, 'pip install -q -r requirements-dev.txt -r services/web/requirements.txt').
sumd_workflow_step('test-web', 2, '[ -f requirements-quality.txt ] && pip install -q -r requirements-quality.txt || true').
sumd_workflow_step('test-web', 3, 'pytest -c services/web/pytest.ini services/web/tests -q').
sumd_workflow('test-e2e-live', 'manual').
sumd_workflow_step('test-e2e-live', 1, 'pip install -q -r requirements-dev.txt -r services/web/requirements.txt').
sumd_workflow_step('test-e2e-live', 2, 'chmod +x scripts/wait-for-web.sh').
sumd_workflow_step('test-e2e-live', 3, './scripts/wait-for-web.sh').
sumd_workflow_step('test-e2e-live', 4, 'MULLM_E2E=1 pytest -c services/web/pytest.ini services/web/tests/test_e2e_live_stack.py -v').
sumd_workflow('test-quality', 'manual').
sumd_workflow_step('test-quality', 1, 'chmod +x scripts/test-quality.sh').
sumd_workflow_step('test-quality', 2, './scripts/test-quality.sh').
sumd_workflow('test-quality-deps', 'manual').
sumd_workflow_step('test-quality-deps', 1, 'pip install -q -r requirements-dev.txt -r services/web/requirements.txt -r requirements-quality.txt').
sumd_workflow('propact-pact', 'manual').
sumd_workflow_step('propact-pact', 1, 'chmod +x scripts/run-propact-pact.sh').
sumd_workflow_step('propact-pact', 2, './scripts/run-propact-pact.sh').
sumd_workflow('mullm-cli', 'manual').
sumd_workflow_step('mullm-cli', 1, 'printf "Dodaj do PATH:\n  export PATH=\"$(CURDIR)/scripts:$$PATH\"\n"').
sumd_workflow_step('mullm-cli', 2, 'printf "Potem: mullm chat send \"lista plikow usera\"\n"').
sumd_workflow('smoke', 'manual').
sumd_workflow_step('smoke', 1, 'curl -fsS http://127.0.0.1:3003/health').
sumd_workflow_step('smoke', 2, 'curl -fsS http://127.0.0.1:3003/api/agents/status').
sumd_workflow_step('smoke', 3, 'curl -fsS http://127.0.0.1:8001/health').
sumd_workflow_step('smoke', 4, 'curl -fsS http://127.0.0.1:8002/health').
sumd_workflow_step('smoke', 5, 'if [ "$(NLP2DSL)" = "1" ] && [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]').
sumd_workflow('ensure-env', 'manual').
sumd_workflow_step('ensure-env', 1, 'if [ ! -f .env ] && [ -f .env.example ]').
sumd_workflow_step('ensure-env', 2, 'cp .env.example .env').
sumd_workflow_step('ensure-env', 3, 'echo "Created .env from .env.example"').
sumd_workflow_step('ensure-env', 4, 'fi').
sumd_workflow('ensure-nlp2dsl-env', 'manual').
sumd_workflow_step('ensure-nlp2dsl-env', 1, 'if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]').
sumd_workflow_step('ensure-nlp2dsl-env', 2, 'if [ ! -f "$(NLP2DSL_DIR)/.env" ] && [ -f "$(NLP2DSL_DIR)/.env.example" ]').
sumd_workflow_step('ensure-nlp2dsl-env', 3, 'cp "$(NLP2DSL_DIR)/.env.example" "$(NLP2DSL_DIR)/.env"').
sumd_workflow_step('ensure-nlp2dsl-env', 4, 'echo "Created $(NLP2DSL_DIR)/.env from .env.example"').
sumd_workflow_step('ensure-nlp2dsl-env', 5, 'fi').
sumd_workflow_step('ensure-nlp2dsl-env', 6, 'fi').
sumd_workflow('nlp2dsl-up', 'manual').
sumd_workflow_step('nlp2dsl-up', 1, 'if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]').
sumd_workflow_step('nlp2dsl-up', 2, 'cd "$(NLP2DSL_DIR)" && $(COMPOSE) up -d').
sumd_workflow_step('nlp2dsl-up', 3, 'else \').
sumd_workflow_step('nlp2dsl-up', 4, 'echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"').
sumd_workflow_step('nlp2dsl-up', 5, 'fi').
sumd_workflow('nlp2dsl-down', 'manual').
sumd_workflow_step('nlp2dsl-down', 1, 'if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]').
sumd_workflow_step('nlp2dsl-down', 2, 'cd "$(NLP2DSL_DIR)" && $(COMPOSE) down').
sumd_workflow_step('nlp2dsl-down', 3, 'else \').
sumd_workflow_step('nlp2dsl-down', 4, 'echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"').
sumd_workflow_step('nlp2dsl-down', 5, 'fi').
sumd_workflow('nlp2cmd-up', 'manual').
sumd_workflow_step('nlp2cmd-up', 1, '$(COMPOSE) --profile nlp2cmd up -d nlp2cmd').
sumd_workflow('nlp2cmd-down', 'manual').
sumd_workflow_step('nlp2cmd-down', 1, '$(COMPOSE) --profile nlp2cmd stop nlp2cmd').
sumd_deploy_target('docker_compose').
sumd_deploy_compose_file('docker-compose.yml').
```

## Call Graph

*381 nodes · 500 edges · 25 modules · CC̄=2.9*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `toast` *(in services.web.app.static.workspace)* | 3 | 35 | 2 | **37** |
| `get_or_create` *(in services.web.app.workspace)* | 3 | 26 | 5 | **31** |
| `api` *(in services.web.app.static.workspace)* | 6 | 26 | 4 | **30** |
| `aggregate_learnings` *(in services.web.app.routing_feedback)* | 11 ⚠ | 0 | 28 | **28** |
| `refreshWorkspace` *(in services.web.app.static.workspace)* | 8 | 10 | 17 | **27** |
| `_nfo_counts` *(in services.web.app.workspace)* | 1 | 2 | 20 | **22** |
| `_append_export_sections` *(in services.web.app.workspace)* | 2 | 1 | 21 | **22** |
| `escapeHtml` *(in services.web.app.static.workspace)* | 1 | 19 | 2 | **21** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/mullm
# generated in 0.20s
# nodes: 381 | edges: 500 | modules: 25
# CC̄=2.9

HUBS[20]:
  services.web.app.static.workspace.toast
    CC=3  in:35  out:2  total:37
  services.web.app.workspace.get_or_create
    CC=3  in:26  out:5  total:31
  services.web.app.static.workspace.api
    CC=6  in:26  out:4  total:30
  services.web.app.routing_feedback.aggregate_learnings
    CC=11  in:0  out:28  total:28
  services.web.app.static.workspace.refreshWorkspace
    CC=8  in:10  out:17  total:27
  services.web.app.workspace._nfo_counts
    CC=1  in:2  out:20  total:22
  services.web.app.workspace._append_export_sections
    CC=2  in:1  out:21  total:22
  services.web.app.static.workspace.escapeHtml
    CC=1  in:19  out:2  total:21
  services.web.app.workspace._append_nfo_section
    CC=7  in:1  out:17  total:18
  services.web.app.prompt_router._build_decision
    CC=3  in:11  out:7  total:18
  services.web.app.workspace.export_debug_logs
    CC=2  in:0  out:18  total:18
  services.web.app.routing_feedback.record_feedback
    CC=7  in:0  out:17  total:17
  services.web.app.static.workspace.selectTicket
    CC=5  in:6  out:11  total:17
  services.projector.app.main._row_to_dict
    CC=3  in:12  out:5  total:17
  services.web.app.static.workspace.ensureSession
    CC=2  in:14  out:3  total:17
  services.web.app.routing_trace.match_user_expectations
    CC=8  in:2  out:13  total:15
  services.web.app.workspace._list_section
    CC=2  in:13  out:2  total:15
  services.web.app.static.workspace.renderTasks
    CC=12  in:6  out:8  total:14
  services.web.app.static.workspace.appendMsgTo
    CC=14  in:2  out:12  total:14
  services.web.app.workspace._routing_optional_parts
    CC=4  in:1  out:13  total:14

MODULES:
  services.projector.app.main  [13 funcs]
    _row_to_dict  CC=3  out:5
    agent_fleet  CC=3  out:4
    approval_requests  CC=3  out:4
    incident_feed  CC=3  out:4
    operational_feed  CC=2  out:3
    plugin_catalog  CC=3  out:4
    rag_documents  CC=2  out:3
    rag_quality_board  CC=2  out:3
    remediation_history  CC=2  out:3
    resource_registry  CC=2  out:3
  services.projector.app.projections.agent_fleet  [1 funcs]
    project_agent_fleet  CC=3  out:2
  services.projector.app.projections.approval_requests  [1 funcs]
    project_approval_requests  CC=6  out:9
  services.projector.app.projections.dispatcher  [4 funcs]
    _event_occurred_at  CC=4  out:6
    _event_payload  CC=3  out:2
    _normalize_event  CC=2  out:3
    project_event  CC=1  out:9
  services.projector.app.projections.incidents  [19 funcs]
    _check_payload  CC=3  out:1
    _checks_list_payload  CC=3  out:5
    _checks_payload  CC=3  out:4
    _diagnostics_ok  CC=6  out:4
    _error_code  CC=4  out:3
    _handle_diagnostics_completed  CC=4  out:9
    _handle_diagnostics_started  CC=1  out:2
    _handle_incident_classified  CC=1  out:5
    _handle_incident_detected  CC=6  out:12
    _handle_post_remediation_verification  CC=4  out:4
  services.projector.app.projections.operational_feed  [3 funcs]
    _summary_for  CC=6  out:6
    _title_for  CC=2  out:2
    project_operational_feed  CC=3  out:10
  services.projector.app.projections.plugin_catalog  [1 funcs]
    project_plugin_catalog  CC=5  out:6
  services.projector.app.projections.resource_registry  [1 funcs]
    project_resource_registry  CC=3  out:2
  services.projector.app.projections.task_board  [3 funcs]
    _handle_task_started  CC=1  out:1
    _update_status  CC=1  out:1
    project_task_board  CC=3  out:2
  services.projector.app.projections.workflow_versions  [1 funcs]
    project_workflow_versions  CC=5  out:6
  services.web.app.access_matrix  [18 funcs]
    _apply_state_lists  CC=3  out:1
    _apply_state_matrices  CC=3  out:4
    _default_agents  CC=5  out:7
    _default_resources  CC=3  out:2
    _empty_agent_resource  CC=3  out:0
    _empty_human_agent  CC=3  out:0
    _load_raw_state  CC=3  out:2
    _matrix_path  CC=2  out:4
    _merge_bool_matrix  CC=5  out:5
    _merged_bool_row  CC=3  out:3
  services.web.app.agent_plugins.registry  [1 funcs]
    analyze_shell_nl  CC=4  out:5
  services.web.app.agent_workroom  [27 funcs]
    _add_permission  CC=1  out:1
    _append_workroom_ledger  CC=5  out:6
    _append_workroom_result  CC=2  out:2
    _append_workroom_thread  CC=6  out:9
    _extract_shell  CC=4  out:8
    _finish_workroom  CC=2  out:2
    _plan_steps  CC=5  out:10
    _record_file_list_result  CC=1  out:2
    _record_shell_result  CC=2  out:3
    _register_file_list_artifact  CC=2  out:3
  services.web.app.conductor  [1 funcs]
    handle_turn  CC=2  out:7
  services.web.app.planfile_bridge  [5 funcs]
    _build_create_cmd  CC=3  out:6
    _improvement_files  CC=3  out:3
    _parse_created_id  CC=7  out:7
    planfile_project_path  CC=5  out:7
    sync_improvement_ticket  CC=9  out:9
  services.web.app.prompt_router  [41 funcs]
    _build_decision  CC=3  out:7
    _candidate  CC=1  out:0
    _command_looks_like_host_list  CC=3  out:3
    _decision_from_expectations  CC=5  out:10
    _decision_from_nlp2cmd  CC=5  out:8
    _default_discuss_decision  CC=1  out:3
    _default_route_decision  CC=2  out:2
    _direct_route_decision  CC=3  out:5
    _empty_route_decision  CC=1  out:2
    _explicit_registry_list  CC=3  out:2
  services.web.app.resource_areas  [5 funcs]
    _area_policy_decision  CC=5  out:0
    _matrix_access_decision  CC=3  out:1
    agent_may_access  CC=4  out:5
    list_areas  CC=2  out:1
    list_groups  CC=1  out:0
  services.web.app.routing_feedback  [16 funcs]
    _append_jsonl  CC=1  out:3
    _build_feedback_tags  CC=8  out:3
    _create_improvement_ticket  CC=2  out:9
    _feedback_path  CC=1  out:2
    _find_turn_context  CC=9  out:9
    _improvements_path  CC=1  out:2
    _maybe_sync_planfile  CC=6  out:10
    _now_iso  CC=1  out:2
    _read_jsonl_tail  CC=5  out:6
    _resolve_feedback_inputs  CC=6  out:4
  services.web.app.routing_policy  [1 funcs]
    load_policy  CC=5  out:6
  services.web.app.routing_schemas  [6 funcs]
    build_nlp2cmd_request  CC=1  out:3
    llm_classifier_json_schema  CC=1  out:1
    llm_system_prompt_with_schema  CC=1  out:2
    parse_llm_classifier  CC=3  out:2
    routing_analysis_use_explain  CC=1  out:3
    schemas_bundle  CC=1  out:4
  services.web.app.routing_trace  [1 funcs]
    match_user_expectations  CC=8  out:13
  services.web.app.static.access  [13 funcs]
    api  CC=5  out:3
    checked  CC=2  out:1
    escapeHtml  CC=1  out:2
    id  CC=2  out:2
    load  CC=3  out:4
    renderAgentResourceMatrix  CC=11  out:4
    renderAll  CC=1  out:2
    renderHumanAgentMatrix  CC=11  out:4
    res  CC=1  out:1
    resetAll  CC=1  out:3
  services.web.app.static.workspace  [100 funcs]
    agentId  CC=2  out:2
    api  CC=6  out:4
    appendFeedbackBar  CC=9  out:13
    appendMsg  CC=2  out:1
    appendMsgTo  CC=14  out:12
    appendPendingChatInput  CC=2  out:2
    appendRouteBadge  CC=3  out:4
    archiveTicket  CC=2  out:5
    b  CC=3  out:5
    bar  CC=3  out:6
  services.web.app.tickets  [4 funcs]
    enrich_task  CC=4  out:6
    status_meta  CC=3  out:2
    ticket_uri  CC=1  out:0
    ticket_web_path  CC=1  out:0
  services.web.app.workspace  [95 funcs]
    _append_candidate_routes  CC=3  out:3
    _append_chat_export_draft  CC=3  out:6
    _append_chat_export_message  CC=6  out:13
    _append_chat_export_trace  CC=3  out:4
    _append_context_collections  CC=4  out:9
    _append_context_scalars  CC=3  out:2
    _append_context_section  CC=4  out:7
    _append_draft_section  CC=3  out:7
    _append_export_sections  CC=2  out:21
    _append_history_message  CC=6  out:11

EDGES:
  services.projector.app.main.operational_feed → services.projector.app.main._row_to_dict
  services.projector.app.main.task_board → services.projector.app.main._row_to_dict
  services.projector.app.main.agent_fleet → services.projector.app.main._row_to_dict
  services.projector.app.main.approval_requests → services.projector.app.main._row_to_dict
  services.projector.app.main.plugin_catalog → services.projector.app.main._row_to_dict
  services.projector.app.main.rag_documents → services.projector.app.main._row_to_dict
  services.projector.app.main.incident_feed → services.projector.app.main._row_to_dict
  services.projector.app.main.service_health → services.projector.app.main._row_to_dict
  services.projector.app.main.remediation_history → services.projector.app.main._row_to_dict
  services.projector.app.main.rag_quality_board → services.projector.app.main._row_to_dict
  services.projector.app.main.resource_registry → services.projector.app.main._row_to_dict
  services.projector.app.main.workflow_versions → services.projector.app.main._row_to_dict
  services.projector.app.projections.task_board._handle_task_started → services.projector.app.projections.task_board._update_status
  services.projector.app.projections.operational_feed.project_operational_feed → services.projector.app.projections.operational_feed._title_for
  services.projector.app.projections.operational_feed.project_operational_feed → services.projector.app.projections.operational_feed._summary_for
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.dispatcher._normalize_event
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.operational_feed.project_operational_feed
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.task_board.project_task_board
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.agent_fleet.project_agent_fleet
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.workflow_versions.project_workflow_versions
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.approval_requests.project_approval_requests
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.plugin_catalog.project_plugin_catalog
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.resource_registry.project_resource_registry
  services.projector.app.projections.dispatcher.project_event → services.projector.app.projections.incidents.project_incidents
  services.projector.app.projections.dispatcher._normalize_event → services.projector.app.projections.dispatcher._event_payload
  services.projector.app.projections.dispatcher._normalize_event → services.projector.app.projections.dispatcher._event_occurred_at
  services.projector.app.projections.incidents._handle_rag_request_failed → services.projector.app.projections.incidents._upsert_rag_quality
  services.projector.app.projections.incidents._handle_rag_request_failed → services.projector.app.projections.incidents._upsert_service_health
  services.projector.app.projections.incidents._handle_rag_request_failed → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._handle_incident_detected → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._handle_incident_classified → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._handle_diagnostics_started → services.projector.app.projections.incidents._update_incident_status
  services.projector.app.projections.incidents._handle_diagnostics_completed → services.projector.app.projections.incidents._checks_payload
  services.projector.app.projections.incidents._handle_diagnostics_completed → services.projector.app.projections.incidents._diagnostics_ok
  services.projector.app.projections.incidents._handle_diagnostics_completed → services.projector.app.projections.incidents._upsert_service_health
  services.projector.app.projections.incidents._handle_diagnostics_completed → services.projector.app.projections.incidents._root_cause
  services.projector.app.projections.incidents._handle_diagnostics_completed → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._handle_remediation_started → services.projector.app.projections.incidents._update_incident_status
  services.projector.app.projections.incidents._handle_remediation_finished → services.projector.app.projections.incidents._update_incident_status
  services.projector.app.projections.incidents._handle_post_remediation_verification → services.projector.app.projections.incidents._update_incident_status
  services.projector.app.projections.incidents._handle_post_remediation_verification → services.projector.app.projections.incidents._upsert_service_health
  services.projector.app.projections.incidents._upsert_rag_quality → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._checks_payload → services.projector.app.projections.incidents._raw_checks
  services.projector.app.projections.incidents._checks_payload → services.projector.app.projections.incidents._checks_list_payload
  services.projector.app.projections.incidents._checks_list_payload → services.projector.app.projections.incidents._check_payload
  services.projector.app.projections.incidents._root_cause → services.projector.app.projections.incidents._error_code
  services.web.app.routing_feedback._feedback_path → services.web.app.routing_feedback.feedback_dir
  services.web.app.routing_feedback._improvements_path → services.web.app.routing_feedback.feedback_dir
  services.web.app.routing_feedback._resolve_feedback_inputs → services.web.app.routing_feedback._find_turn_context
  services.web.app.routing_feedback.record_feedback → services.web.app.routing_feedback._resolve_feedback_inputs
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (1)

**`Auto-generated API Smoke Tests`**
- assert `_status < 500`
- assert `_status >= 200`
- detectors: FastAPIDetector, TestEndpointDetector, ConfigEndpointDetector

### Integration (1)

**`Auto-generated from Python Tests`**
- assert `_status == 200`
- assert `_status == 200`
- assert `_status == 200`

## Intent

Mullm - Multi-Agent Learning and Labor Management
