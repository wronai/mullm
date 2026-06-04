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
- **generated_from**: requirements-dev.txt, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(3 analysis files)

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
  step-1: run cmd=$(COMPOSE) $(PROFILE_ARGS) up -d;
  step-2: run cmd=if [ "$(NLP2DSL)" = "1" ]; then \;
  step-3: run cmd=$(MAKE) --no-print-directory nlp2dsl-up; \;
  step-4: run cmd=fi;
}

workflow[name="down"] {
  trigger: manual;
  step-1: run cmd=if [ "$(NLP2DSL)" = "1" ]; then \;
  step-2: run cmd=$(MAKE) --no-print-directory nlp2dsl-down; \;
  step-3: run cmd=fi;
  step-4: run cmd=$(COMPOSE) $(PROFILE_ARGS) down;
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

workflow[name="smoke"] {
  trigger: manual;
  step-1: run cmd=curl -fsS http://127.0.0.1:3003/health;
  step-2: run cmd=curl -fsS http://127.0.0.1:8001/health;
  step-3: run cmd=curl -fsS http://127.0.0.1:8002/health;
  step-4: run cmd=if [ "$(NLP2DSL)" = "1" ] && [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \;
  step-5: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl backend: %{http_code}\n' http://127.0.0.1:8010/docs && \;
  step-6: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl nlp: %{http_code}\n' http://127.0.0.1:8012/docs && \;
  step-7: run cmd=curl -fsS -o /dev/null -w 'nlp2dsl worker: %{http_code}\n' http://127.0.0.1:8004/health; \;
  step-8: run cmd=fi;
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
- `up`
- `down`
- `restart`
- `build`
- `logs`
- `ps`
- `test`
- `smoke`
- `ensure-env`
- `ensure-nlp2dsl-env`
- `nlp2dsl-up`
- `nlp2dsl-down`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# mullm | 136f 17856L | python:123,css:5,javascript:4,shell:3,less:1 | 2026-06-04
# stats: 408 func | 144 cls | 136 mod | CC̄=3.7 | critical:22 | cycles:0
# alerts[5]: CC _format_export_text=47; CC format_logs_text=29; CC filter_file_inventory=29; CC run_workroom=22; CC handle_chat_message=22
# hotspots[5]: lifespan fan=21; run_workroom fan=18; upload_resource fan=17; handle_chat_message fan=17; search fan=15
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[136]:
  agents/shell-agent/app/__init__.py,2
  agents/shell-agent/app/executor.py,49
  agents/shell-agent/app/main.py,27
  agents/shell-agent/app/nats_consumer.py,48
  app.doql.less,395
  integrations/nlp2dsl/mullm_registry.py,33
  integrations/nlp2dsl/patch_startup.py,8
  project.sh,53
  scripts/test.sh,14
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
  services/orchestrator/app/api/observability.py,109
  services/orchestrator/app/api/queries.py,181
  services/orchestrator/app/api/rag.py,143
  services/orchestrator/app/application/__init__.py,2
  services/orchestrator/app/application/command_bus.py,983
  services/orchestrator/app/application/sagas/__init__.py,15
  services/orchestrator/app/application/sagas/approval_gate.py,130
  services/orchestrator/app/application/sagas/task_routing.py,62
  services/orchestrator/app/config.py,55
  services/orchestrator/app/domain/__init__.py,2
  services/orchestrator/app/domain/aggregates/__init__.py,2
  services/orchestrator/app/domain/aggregates/agent.py,84
  services/orchestrator/app/domain/aggregates/approval.py,98
  services/orchestrator/app/domain/aggregates/plugin.py,98
  services/orchestrator/app/domain/aggregates/resource.py,101
  services/orchestrator/app/domain/aggregates/task.py,232
  services/orchestrator/app/domain/aggregates/workflow.py,145
  services/orchestrator/app/domain/events/__init__.py,812
  services/orchestrator/app/domain/events/incidents.py,255
  services/orchestrator/app/domain/value_objects/__init__.py,86
  services/orchestrator/app/evolution/__init__.py,13
  services/orchestrator/app/evolution/catalog.py,93
  services/orchestrator/app/evolution/evaluation.py,147
  services/orchestrator/app/evolution/experiments.py,77
  services/orchestrator/app/evolution/policy_engine.py,104
  services/orchestrator/app/incidents/__init__.py,4
  services/orchestrator/app/incidents/pipeline.py,322
  services/orchestrator/app/infrastructure/__init__.py,2
  services/orchestrator/app/infrastructure/eventstore.py,183
  services/orchestrator/app/infrastructure/eventstore_dual.py,58
  services/orchestrator/app/infrastructure/eventstore_esdb.py,187
  services/orchestrator/app/infrastructure/eventstore_factory.py,51
  services/orchestrator/app/infrastructure/nats_bus.py,50
  services/orchestrator/app/infrastructure/postgres.py,93
  services/orchestrator/app/main.py,196
  services/orchestrator/app/observability/__init__.py,23
  services/orchestrator/app/observability/context.py,60
  services/orchestrator/app/observability/export.py,191
  services/orchestrator/app/observability/incidents.py,338
  services/orchestrator/app/observability/logging.py,44
  services/orchestrator/app/observability/middleware.py,20
  services/orchestrator/app/observability/rag_diagnostics.py,205
  services/orchestrator/app/observability/rag_pipeline.py,143
  services/orchestrator/app/rag/__init__.py,7
  services/orchestrator/app/rag/chunking.py,28
  services/orchestrator/app/rag/indexer.py,86
  services/orchestrator/app/rag/openrouter.py,112
  services/orchestrator/app/rag/retriever.py,88
  services/orchestrator/app/rag/store.py,241
  services/orchestrator/tests/__init__.py,2
  services/orchestrator/tests/conftest.py,10
  services/orchestrator/tests/fakes.py,64
  services/orchestrator/tests/test_api.py,90
  services/orchestrator/tests/test_command_bus.py,57
  services/orchestrator/tests/test_observability.py,22
  services/orchestrator/tests/test_task_aggregate.py,28
  services/projector/app/__init__.py,2
  services/projector/app/db.py,57
  services/projector/app/main.py,341
  services/projector/app/projections/__init__.py,4
  services/projector/app/projections/agent_fleet.py,82
  services/projector/app/projections/approval_requests.py,80
  services/projector/app/projections/dispatcher.py,42
  services/projector/app/projections/incidents.py,321
  services/projector/app/projections/operational_feed.py,70
  services/projector/app/projections/plugin_catalog.py,43
  services/projector/app/projections/resource_registry.py,119
  services/projector/app/projections/task_board.py,116
  services/projector/app/projections/workflow_versions.py,48
  services/web/app/__init__.py,1
  services/web/app/access_matrix.py,206
  services/web/app/agent_workroom.py,355
  services/web/app/api_routes.py,529
  services/web/app/chat.py,665
  services/web/app/conductor.py,463
  services/web/app/main.py,105
  services/web/app/nlp2dsl_bridge.py,101
  services/web/app/resource_areas.py,158
  services/web/app/static/access.css,84
  services/web/app/static/access.js,158
  services/web/app/static/app.css,200
  services/web/app/static/app.js,194
  services/web/app/static/workroom.css,87
  services/web/app/static/workroom.js,187
  services/web/app/static/workspace.css,656
  services/web/app/static/workspace.js,843
  services/web/app/tickets.py,46
  services/web/app/workspace.py,681
  services/web/src/styles.css,287
  services/web/tests/test_access_matrix.py,38
  services/web/tests/test_agent_workroom.py,30
  services/web/tests/test_artifacts.py,31
  services/web/tests/test_chat_intent.py,111
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
    e: get_task,get_agent,get_workflow,list_tasks,list_agents,_event_to_dict,TaskQuery,AgentQuery,WorkflowQuery,TaskListQuery
    TaskQuery:
    AgentQuery:
    WorkflowQuery:
    TaskListQuery:
    get_task(task_id;request)
    get_agent(agent_id;request)
    get_workflow(workflow_id;request)
    list_tasks(request;status;agent_id;limit;offset)
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
    e: CommandBus
    CommandBus: __init__(2),handle(0),handle_envelope(1),_create_task(4),_assign_task(4),_start_task(4),_complete_task(4),_fail_task(4),_register_agent(4),_agent_heartbeat(4),_start_workflow(4),_propose_workflow_version(4),_validate_workflow_version(4),_approve_workflow_version(4),_activate_workflow_version(4),_rollback_workflow_version(4),_shadow_workflow_version(4),_propose_change(4),_propose_plugin(4),_validate_plugin(4),_install_plugin(4),_activate_plugin(4),_rollback_plugin(4),_create_approval(4),_approve_request(4),_reject_request(4),_expire_approval(4),_persist_workflow(4),_persist_plugin(4),_persist_approval(4),_load_workflow(1),_load_plugin(1),_load_approval(1),_load_task(1),_append_and_publish(3),_publish(2),_apply_policy(2),_register_resource(4),_request_transfer(4),_record_task_outcome(1),_result(2)
  services/orchestrator/app/application/sagas/__init__.py:
  services/orchestrator/app/application/sagas/approval_gate.py:
    e: _is_skipped,ensure_approval,follow_up_after_grant,ApprovalRequired
    ApprovalRequired: __init__(0)  # Komenda wymaga wcześniejszego ApprovalGranted.
    _is_skipped(data;metadata)
    ensure_approval(event_store;command_type;data)
    follow_up_after_grant(command_bus)
  services/orchestrator/app/application/sagas/task_routing.py:
    e: pick_idle_agent,maybe_auto_assign
    pick_idle_agent(event_store;required_capabilities)
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
    e: _event_type,_utc_now,_event_data,_event_timestamp,Task
    Task: __init__(8),create(8),from_events(2),assign_to_agent(1),start(0),complete(1),fail(1),apply(1),get_uncommitted_events(0),mark_events_committed(0),to_dict(0)
    _event_type(event)
    _utc_now()
    _event_data(event)
    _event_timestamp(event)
  services/orchestrator/app/domain/aggregates/workflow.py:
    e: Workflow
    Workflow: start(4),propose_version(4),validate_version(0),approve_version(1),shadow_version(1),activate_version(0),rollback_version(1),get_uncommitted_events(0),mark_events_committed(0)
  services/orchestrator/app/domain/events/__init__.py:
    e: _utc_now,_json_value,DomainEvent,TaskCreated,TaskAssigned,TaskStarted,TaskCompleted,TaskFailed,AgentRegistered,AgentHeartbeatReceived,TaskAssignedToAgent,AgentMarkedIdle,WorkflowStarted,WorkflowVersionProposed,WorkflowVersionValidated,WorkflowVersionApproved,WorkflowVersionShadowed,WorkflowVersionActivated,WorkflowVersionRolledBack,PluginProposed,PluginValidated,PluginInstalled,PluginActivated,PluginRolledBack,ApprovalRequested,ApprovalGranted,ApprovalRejected,ChangeProposed,CapabilityRegistered,ResourceRegistered,TransferRequested,TransferCompleted,TransferFailed,ApprovalExpired
    DomainEvent: aggregate_id(0),data(0),to_message(0)
    TaskCreated: aggregate_id(0),data(0)
    TaskAssigned: aggregate_id(0),data(0)
    TaskStarted: aggregate_id(0),data(0)
    TaskCompleted: aggregate_id(0),data(0)
    TaskFailed: aggregate_id(0),data(0)
    AgentRegistered: aggregate_id(0),data(0)
    AgentHeartbeatReceived: aggregate_id(0),data(0)
    TaskAssignedToAgent: aggregate_id(0),data(0)
    AgentMarkedIdle: aggregate_id(0),data(0)
    WorkflowStarted: aggregate_id(0),data(0)
    WorkflowVersionProposed: aggregate_id(0),data(0)
    WorkflowVersionValidated: aggregate_id(0),data(0)
    WorkflowVersionApproved: aggregate_id(0),data(0)
    WorkflowVersionShadowed: aggregate_id(0),data(0)
    WorkflowVersionActivated: aggregate_id(0),data(0)
    WorkflowVersionRolledBack: aggregate_id(0),data(0)
    PluginProposed: aggregate_id(0),data(0)
    PluginValidated: aggregate_id(0),data(0)
    PluginInstalled: aggregate_id(0),data(0)
    PluginActivated: aggregate_id(0),data(0)
    PluginRolledBack: aggregate_id(0),data(0)
    ApprovalRequested: aggregate_id(0),data(0)
    ApprovalGranted: aggregate_id(0),data(0)
    ApprovalRejected: aggregate_id(0),data(0)
    ChangeProposed: aggregate_id(0),data(0)
    CapabilityRegistered: aggregate_id(0),data(0)
    ResourceRegistered: aggregate_id(0),data(0)
    TransferRequested: aggregate_id(0),data(0)
    TransferCompleted: aggregate_id(0),data(0)
    TransferFailed: aggregate_id(0),data(0)
    ApprovalExpired: aggregate_id(0),data(0)
    _utc_now()
    _json_value(value)
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
    e: EvaluationEngine
    EvaluationEngine: __init__(1),record_task_outcome(0),_upsert_metrics(0),should_auto_rollback(2)  # Pętla oceny skutków — metryki jakości ewolucji i runtime.
  services/orchestrator/app/evolution/experiments.py:
    e: ExperimentManager
    ExperimentManager: __init__(1),start_experiment(0),complete_experiment(1),active_shadow(1)  # Shadow / canary — stan eksperymentu powiązany z wersją workf
  services/orchestrator/app/evolution/policy_engine.py:
    e: PolicyViolation,PolicyEngine
    PolicyViolation: __init__(2)
    PolicyEngine: __init__(1),rule_for(1),validate_command(2),validate_activation_metrics(3)  # Reguły first — AI proponuje tylko w granicach polityk z kata
  services/orchestrator/app/incidents/__init__.py:
  services/orchestrator/app/incidents/pipeline.py:
    e: classify_rag_error,IncidentPipeline
    IncidentPipeline: __init__(0),handle_rag_failure(0),_run_rag_diagnostics(1),_remediate_rag_incident(0),_verify_rag(1),_append_and_publish(2),_with_incident_id(2)
    classify_rag_error(error)
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
    e: build_event_store
    build_event_store()
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
    e: format_logs_text,build_orchestrator_bundle
    format_logs_text(bundle)
    build_orchestrator_bundle()
  services/orchestrator/app/observability/incidents.py:
    e: classify_rag_failure,_event_payload,_query_from_trace,_check_names,_checks_payload,_root_cause,_event_status,_incident_class,_default_playbook,IncidentCode,IncidentRecorder
    IncidentCode:
    IncidentRecorder: record(0),_persist(1),_publish_event(2)
    classify_rag_failure()
    _event_payload(event_type;row)
    _query_from_trace(trace_steps)
    _check_names(diagnostics)
    _checks_payload(diagnostics)
    _root_cause(diagnostics;code)
    _event_status(event_type;row)
    _incident_class(code)
    _default_playbook(code)
  services/orchestrator/app/observability/logging.py:
    e: log_event
    log_event()
  services/orchestrator/app/observability/middleware.py:
    e: CorrelationMiddleware
    CorrelationMiddleware: dispatch(2)
  services/orchestrator/app/observability/rag_diagnostics.py:
    e: RagDiagnostics
    RagDiagnostics: run(0),_check_postgres(0),_check_rag_tables(0),_check_openrouter_config(0),_check_embedding(0),_check_search(1),_recommendations(1),_snapshot(1)
  services/orchestrator/app/observability/rag_pipeline.py:
    e: RagPipeline
    RagPipeline: ask(0),_failure_payload(0)
  services/orchestrator/app/rag/__init__.py:
  services/orchestrator/app/rag/chunking.py:
    e: chunk_text
    chunk_text(text)
  services/orchestrator/app/rag/indexer.py:
    e: RagIndexer
    RagIndexer: __init__(3),ingest_resource(0)  # Ingest zasobu po rejestracji — fetch → chunk → embed → store
  services/orchestrator/app/rag/openrouter.py:
    e: normalize_openrouter_model,OpenRouterClient
    OpenRouterClient: __init__(1),configured(0),_headers(0),embed(1),chat(1),health(0)  # Klient OpenRouter — embeddings i chat (LLM_MODEL z .env).
    normalize_openrouter_model(model)
  services/orchestrator/app/rag/retriever.py:
    e: RagRetriever
    RagRetriever: __init__(2),search(1),ask(1)
  services/orchestrator/app/rag/store.py:
    e: _cosine,_parse_embedding,_row_dict,_chunk_hit,RagStore
    RagStore: __init__(1),upsert_document_pending(0),mark_indexed(0),mark_failed(0),replace_chunks(0),list_documents(0),search(1),_keyword_fallback(1)
    _cosine(a;b)
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
    e: test_classify_llm_unavailable,test_classify_empty_sources,test_classify_grounding,test_classify_backend_500
    test_classify_llm_unavailable()
    test_classify_empty_sources()
    test_classify_grounding()
    test_classify_backend_500()
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
    e: project_agent_fleet
    project_agent_fleet(db;event)
  services/projector/app/projections/approval_requests.py:
    e: project_approval_requests
    project_approval_requests(db;event)
  services/projector/app/projections/dispatcher.py:
    e: project_event,_normalize_event
    project_event(db;event)
    _normalize_event(event)
  services/projector/app/projections/incidents.py:
    e: project_incidents,_handle_rag_request_failed,_handle_incident_detected,_handle_incident_classified,_handle_diagnostics_started,_handle_diagnostics_completed,_handle_remediation_started,_handle_remediation_finished,_handle_post_remediation_verification,_upsert_rag_quality,_upsert_service_health,_update_incident_status,_error_code,_checks_payload,_root_cause,_diagnostics_ok
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
    e: project_resource_registry
    project_resource_registry(db;event)
  services/projector/app/projections/task_board.py:
    e: project_task_board,_update_status
    project_task_board(db;event)
    _update_status(db;task_id;status;event_type;occurred_at)
  services/projector/app/projections/workflow_versions.py:
    e: project_workflow_versions
    project_workflow_versions(db;event)
  services/web/app/__init__.py:
  services/web/app/access_matrix.py:
    e: _matrix_path,_default_resources,_default_agents,_empty_agent_resource,_empty_human_agent,default_state,load_state,_merge_bool_matrix,_reindex_state,save_state,agent_may_access_resource,human_may_use_agent,diagnose_file_list_command
    _matrix_path()
    _default_resources()
    _default_agents()
    _empty_agent_resource(resources;agents)
    _empty_human_agent(agents;humans)
    default_state()
    load_state()
    _merge_bool_matrix(base;patch)
    _reindex_state(state)
    save_state(state)
    agent_may_access_resource(agent_id;resource_id)
    human_may_use_agent(human_id;agent_id)
    diagnose_file_list_command()
  services/web/app/agent_workroom.py:
    e: create_workroom,get_workroom,_plan_steps,_extract_shell,run_workroom,workroom_catalog,LedgerEntry,WorkroomSession
    LedgerEntry: to_dict(0)
    WorkroomSession: add_ledger(3),agent_say(3),to_dict(0)
    create_workroom()
    get_workroom(workroom_id)
    _plan_steps(goal)
    _extract_shell(text)
    run_workroom(workroom_id;user_message)
    workroom_catalog()
  services/web/app/api_routes.py:
    e: start_chat_session,get_chat_session,workspace_state,chat_message,task_draft,create_task,create_task_from_draft,create_and_run_task,context_attach,upload_files,board_snapshot,list_tickets,get_ticket,confirm_ticket,archive_ticket,link_ticket,ticket_statuses,workspace_list_artifacts,workspace_get_artifact,workspace_file_list_export,workspace_chat_export,workspace_logs_export,workroom_start,workroom_get,workroom_run,api_resource_areas,api_role_scopes,access_matrix_get,access_matrix_put,access_matrix_reset,access_diagnose_file_list,ChatSessionStart,ChatMessage,TaskDraftRequest,CreateTaskBody,CreateFromDraftBody,ConfirmTicketBody,ContextAttachBody,SessionRef,WorkroomStart,WorkroomMessage,AccessMatrixBody
    ChatSessionStart:
    ChatMessage:
    TaskDraftRequest:
    CreateTaskBody:
    CreateFromDraftBody:
    ConfirmTicketBody:
    ContextAttachBody:
    SessionRef:
    WorkroomStart:
    WorkroomMessage:
    AccessMatrixBody:
    start_chat_session(body)
    get_chat_session(session_id)
    workspace_state(session_id)
    chat_message(body)
    task_draft(body)
    create_task(body)
    create_task_from_draft(body)
    create_and_run_task(body)
    context_attach(body)
    upload_files(session_id;files;classification)
    board_snapshot()
    list_tickets(session_id;view)
    get_ticket(task_id;session_id)
    confirm_ticket(task_id;body)
    archive_ticket(task_id;body)
    link_ticket(task_id;body)
    ticket_statuses()
    workspace_list_artifacts(session_id)
    workspace_get_artifact(session_id;artifact_id)
    workspace_file_list_export(session_id;message;scope)
    workspace_chat_export(session_id)
    workspace_logs_export(session_id;limit)
    workroom_start(body)
    workroom_get(workroom_id)
    workroom_run(workroom_id;body)
    api_resource_areas()
    api_role_scopes()
    access_matrix_get()
    access_matrix_put(body)
    access_matrix_reset()
    access_diagnose_file_list()
  services/web/app/chat.py:
    e: _orch,_projector,is_file_list_intent,file_list_scope,_uri_is_user_resource,_uri_is_system_resource,filter_file_inventory,_dedupe_rows_by_uri,fetch_file_inventory,format_file_list_reply,_append_session_files,_format_scope_uri,_append_resource_rows,_empty_resource_hint,_append_rag_rows,_append_file_list_errors,_append_file_list_tip,build_file_list_artifact,new_session_id,get_history,_append,_format_history,_format_incident,handle_message,_file_list_answer,_ask_rag,_rag_headers,_rag_query,_answer_from_rag_payload,_sources_fallback_answer,_source_preview,_rag_backend_fallback,_rag_search_fallback,_rag_unavailable_answer,_rag_diagnostics_hint,_default_chat_reply,_message_response,create_task
    _orch()
    _projector()
    is_file_list_intent(message)
    file_list_scope(message)
    _uri_is_user_resource(uri)
    _uri_is_system_resource(uri)
    filter_file_inventory(inventory;list_scope)
    _dedupe_rows_by_uri(rows)
    fetch_file_inventory()
    format_file_list_reply(inventory)
    _append_session_files(lines;list_scope;scope_files;scope_uris)
    _format_scope_uri(uri)
    _append_resource_rows(lines;list_scope;resources)
    _empty_resource_hint(list_scope)
    _append_rag_rows(lines;list_scope;rag_docs)
    _append_file_list_errors(lines;errors)
    _append_file_list_tip(lines;list_scope;resources;scope_files)
    build_file_list_artifact(reply_text;inventory)
    new_session_id()
    get_history(session_id)
    _append(session_id;role;content)
    _format_history(session_id)
    _format_incident(payload)
    handle_message()
    _file_list_answer(message)
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
    create_task()
  services/web/app/conductor.py:
    e: handle_turn,_nlp2dsl_turn,_call_nlp2dsl,_nlp_output_base,_in_progress_turn,_ready_turn,_ready_action_payload,_system_file_list_payload,_shell_task_payload,_shell_clarify_payload,_ticket_payload,_task_reply,_closed_turn,_append_turn,_mullm_file_list_turn,_fallback_turn,_local_clarify,_extract_shell
    handle_turn()
    _nlp2dsl_turn()
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
  services/web/app/main.py:
    e: health,workspace_home,agent_workroom_page,access_matrix_page,dashboard
    health()
    workspace_home(request;task_id)
    agent_workroom_page(request)
    access_matrix_page(request)
    dashboard(request)
  services/web/app/nlp2dsl_bridge.py:
    e: backend_url,backend_candidates,health,chat_start,chat_message,_post_json,form_to_prompt,primary_action,step_config
    backend_url()
    backend_candidates()
    health()
    chat_start(text)
    chat_message(conversation_id;text)
    _post_json(path;payload)
    form_to_prompt(form;values)
    primary_action(dsl)
    step_config(dsl)
  services/web/app/resource_areas.py:
    e: list_areas,list_groups,agent_may_access
    list_areas()
    list_groups()
    agent_may_access(role_id;area_id;action)
  services/web/app/tickets.py:
    e: ticket_uri,ticket_web_path,status_meta,enrich_task
    ticket_uri(task_id)
    ticket_web_path(task_id)
    status_meta(status)
    enrich_task(row)
  services/web/app/workspace.py:
    e: _orch,_projector,new_session,get_session,get_or_create,_artifact_title,register_artifact,artifact_summaries,get_artifact,workspace_state,attach_context,_extract_ticket,_extract_shell_command,build_task_payload,propose_task_draft,create_task_immediate,handle_chat_message,create_task_from_draft,create_and_run,export_debug_logs,_format_export_text,archive_task,link_ticket,fetch_live_board,WorkspaceContext,WorkspaceSession
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
    _extract_ticket(text)
    _extract_shell_command(text)
    build_task_payload(session_id;message)
    propose_task_draft(session_id;message)
    create_task_immediate(session_id)
    handle_chat_message()
    create_task_from_draft(session_id)
    create_and_run(session_id)
    export_debug_logs(session_id)
    _format_export_text(bundle)
    archive_task(session_id;task_id)
    link_ticket(session_id;task_id)
    fetch_live_board()
  services/web/tests/test_access_matrix.py:
    e: matrix_file,test_default_all_checked,test_save_and_deny,test_diagnose_file_list_no_shell
    matrix_file(monkeypatch)
    test_default_all_checked(matrix_file)
    test_save_and_deny(matrix_file)
    test_diagnose_file_list_no_shell()
  services/web/tests/test_agent_workroom.py:
    e: test_plan_includes_files_for_lista_plikow,test_files_agent_may_list_rag,test_mail_agent_denied_rag,test_groups_nonempty,test_workroom_session_dict
    test_plan_includes_files_for_lista_plikow()
    test_files_agent_may_list_rag()
    test_mail_agent_denied_rag()
    test_groups_nonempty()
    test_workroom_session_dict()
  services/web/tests/test_artifacts.py:
    e: test_register_and_get_artifact
    test_register_and_get_artifact()
  services/web/tests/test_chat_intent.py:
    e: test_file_list_intent_pl,test_format_file_list,test_file_list_scope_usera,test_filter_user_files,test_file_list_artifact,test_format_user_scope_title,test_dedupe_rag_documents_by_uri,test_handle_message_file_list_builds_artifact
    test_file_list_intent_pl()
    test_format_file_list()
    test_file_list_scope_usera()
    test_filter_user_files()
    test_file_list_artifact()
    test_format_user_scope_title()
    test_dedupe_rag_documents_by_uri()
    test_handle_message_file_list_builds_artifact(monkeypatch)
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
project_file('app.doql.less', 395, 'less').
project_file('integrations/nlp2dsl/mullm_registry.py', 33, 'python').
project_file('integrations/nlp2dsl/patch_startup.py', 8, 'python').
project_file('project.sh', 53, 'shell').
project_file('scripts/test.sh', 14, 'shell').
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
project_file('services/orchestrator/app/api/observability.py', 109, 'python').
project_file('services/orchestrator/app/api/queries.py', 181, 'python').
project_file('services/orchestrator/app/api/rag.py', 143, 'python').
project_file('services/orchestrator/app/application/__init__.py', 2, 'python').
project_file('services/orchestrator/app/application/command_bus.py', 983, 'python').
project_file('services/orchestrator/app/application/sagas/__init__.py', 15, 'python').
project_file('services/orchestrator/app/application/sagas/approval_gate.py', 130, 'python').
project_file('services/orchestrator/app/application/sagas/task_routing.py', 62, 'python').
project_file('services/orchestrator/app/config.py', 55, 'python').
project_file('services/orchestrator/app/domain/__init__.py', 2, 'python').
project_file('services/orchestrator/app/domain/aggregates/__init__.py', 2, 'python').
project_file('services/orchestrator/app/domain/aggregates/agent.py', 84, 'python').
project_file('services/orchestrator/app/domain/aggregates/approval.py', 98, 'python').
project_file('services/orchestrator/app/domain/aggregates/plugin.py', 98, 'python').
project_file('services/orchestrator/app/domain/aggregates/resource.py', 101, 'python').
project_file('services/orchestrator/app/domain/aggregates/task.py', 232, 'python').
project_file('services/orchestrator/app/domain/aggregates/workflow.py', 145, 'python').
project_file('services/orchestrator/app/domain/events/__init__.py', 812, 'python').
project_file('services/orchestrator/app/domain/events/incidents.py', 255, 'python').
project_file('services/orchestrator/app/domain/value_objects/__init__.py', 86, 'python').
project_file('services/orchestrator/app/evolution/__init__.py', 13, 'python').
project_file('services/orchestrator/app/evolution/catalog.py', 93, 'python').
project_file('services/orchestrator/app/evolution/evaluation.py', 147, 'python').
project_file('services/orchestrator/app/evolution/experiments.py', 77, 'python').
project_file('services/orchestrator/app/evolution/policy_engine.py', 104, 'python').
project_file('services/orchestrator/app/incidents/__init__.py', 4, 'python').
project_file('services/orchestrator/app/incidents/pipeline.py', 322, 'python').
project_file('services/orchestrator/app/infrastructure/__init__.py', 2, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore.py', 183, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_dual.py', 58, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_esdb.py', 187, 'python').
project_file('services/orchestrator/app/infrastructure/eventstore_factory.py', 51, 'python').
project_file('services/orchestrator/app/infrastructure/nats_bus.py', 50, 'python').
project_file('services/orchestrator/app/infrastructure/postgres.py', 93, 'python').
project_file('services/orchestrator/app/main.py', 196, 'python').
project_file('services/orchestrator/app/observability/__init__.py', 23, 'python').
project_file('services/orchestrator/app/observability/context.py', 60, 'python').
project_file('services/orchestrator/app/observability/export.py', 191, 'python').
project_file('services/orchestrator/app/observability/incidents.py', 338, 'python').
project_file('services/orchestrator/app/observability/logging.py', 44, 'python').
project_file('services/orchestrator/app/observability/middleware.py', 20, 'python').
project_file('services/orchestrator/app/observability/rag_diagnostics.py', 205, 'python').
project_file('services/orchestrator/app/observability/rag_pipeline.py', 143, 'python').
project_file('services/orchestrator/app/rag/__init__.py', 7, 'python').
project_file('services/orchestrator/app/rag/chunking.py', 28, 'python').
project_file('services/orchestrator/app/rag/indexer.py', 86, 'python').
project_file('services/orchestrator/app/rag/openrouter.py', 112, 'python').
project_file('services/orchestrator/app/rag/retriever.py', 88, 'python').
project_file('services/orchestrator/app/rag/store.py', 241, 'python').
project_file('services/orchestrator/tests/__init__.py', 2, 'python').
project_file('services/orchestrator/tests/conftest.py', 10, 'python').
project_file('services/orchestrator/tests/fakes.py', 64, 'python').
project_file('services/orchestrator/tests/test_api.py', 90, 'python').
project_file('services/orchestrator/tests/test_command_bus.py', 57, 'python').
project_file('services/orchestrator/tests/test_observability.py', 22, 'python').
project_file('services/orchestrator/tests/test_task_aggregate.py', 28, 'python').
project_file('services/projector/app/__init__.py', 2, 'python').
project_file('services/projector/app/db.py', 57, 'python').
project_file('services/projector/app/main.py', 341, 'python').
project_file('services/projector/app/projections/__init__.py', 4, 'python').
project_file('services/projector/app/projections/agent_fleet.py', 82, 'python').
project_file('services/projector/app/projections/approval_requests.py', 80, 'python').
project_file('services/projector/app/projections/dispatcher.py', 42, 'python').
project_file('services/projector/app/projections/incidents.py', 321, 'python').
project_file('services/projector/app/projections/operational_feed.py', 70, 'python').
project_file('services/projector/app/projections/plugin_catalog.py', 43, 'python').
project_file('services/projector/app/projections/resource_registry.py', 119, 'python').
project_file('services/projector/app/projections/task_board.py', 116, 'python').
project_file('services/projector/app/projections/workflow_versions.py', 48, 'python').
project_file('services/web/app/__init__.py', 1, 'python').
project_file('services/web/app/access_matrix.py', 206, 'python').
project_file('services/web/app/agent_workroom.py', 355, 'python').
project_file('services/web/app/api_routes.py', 529, 'python').
project_file('services/web/app/chat.py', 665, 'python').
project_file('services/web/app/conductor.py', 463, 'python').
project_file('services/web/app/main.py', 105, 'python').
project_file('services/web/app/nlp2dsl_bridge.py', 101, 'python').
project_file('services/web/app/resource_areas.py', 158, 'python').
project_file('services/web/app/static/access.css', 84, 'css').
project_file('services/web/app/static/access.js', 158, 'javascript').
project_file('services/web/app/static/app.css', 200, 'css').
project_file('services/web/app/static/app.js', 194, 'javascript').
project_file('services/web/app/static/workroom.css', 87, 'css').
project_file('services/web/app/static/workroom.js', 187, 'javascript').
project_file('services/web/app/static/workspace.css', 656, 'css').
project_file('services/web/app/static/workspace.js', 843, 'javascript').
project_file('services/web/app/tickets.py', 46, 'python').
project_file('services/web/app/workspace.py', 681, 'python').
project_file('services/web/src/styles.css', 287, 'css').
project_file('services/web/tests/test_access_matrix.py', 38, 'python').
project_file('services/web/tests/test_agent_workroom.py', 30, 'python').
project_file('services/web/tests/test_artifacts.py', 31, 'python').
project_file('services/web/tests/test_chat_intent.py', 111, 'python').
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
python_function('services/orchestrator/app/api/observability.py', 'export_logs', 3, 2, 6).
python_function('services/orchestrator/app/api/observability.py', 'list_incidents', 2, 3, 7).
python_function('services/orchestrator/app/api/queries.py', 'get_task', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'get_agent', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'get_workflow', 2, 6, 6).
python_function('services/orchestrator/app/api/queries.py', 'list_tasks', 5, 10, 8).
python_function('services/orchestrator/app/api/queries.py', 'list_agents', 3, 6, 8).
python_function('services/orchestrator/app/api/queries.py', '_event_to_dict', 1, 2, 3).
python_function('services/orchestrator/app/api/rag.py', 'rag_health', 1, 1, 2).
python_function('services/orchestrator/app/api/rag.py', 'list_documents', 2, 1, 2).
python_function('services/orchestrator/app/api/rag.py', 'search', 2, 3, 15).
python_function('services/orchestrator/app/api/rag.py', 'ask', 2, 1, 6).
python_function('services/orchestrator/app/api/rag.py', 'ingest_resource', 2, 2, 5).
python_function('services/orchestrator/app/api/rag.py', '_safe_rag_diagnostics', 1, 2, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', '_is_skipped', 2, 3, 2).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', 'ensure_approval', 3, 8, 6).
python_function('services/orchestrator/app/application/sagas/approval_gate.py', 'follow_up_after_grant', 1, 5, 3).
python_function('services/orchestrator/app/application/sagas/task_routing.py', 'pick_idle_agent', 2, 10, 4).
python_function('services/orchestrator/app/application/sagas/task_routing.py', 'maybe_auto_assign', 1, 5, 3).
python_function('services/orchestrator/app/domain/aggregates/agent.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_type', 1, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_data', 1, 2, 3).
python_function('services/orchestrator/app/domain/aggregates/task.py', '_event_timestamp', 1, 3, 3).
python_function('services/orchestrator/app/domain/events/__init__.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/domain/events/__init__.py', '_json_value', 1, 7, 5).
python_function('services/orchestrator/app/incidents/pipeline.py', 'classify_rag_error', 1, 11, 2).
python_function('services/orchestrator/app/infrastructure/eventstore.py', '_loads_json', 1, 3, 3).
python_function('services/orchestrator/app/infrastructure/eventstore.py', '_utc_now', 0, 1, 1).
python_function('services/orchestrator/app/infrastructure/eventstore_esdb.py', '_parse_esdb_uri', 1, 4, 3).
python_function('services/orchestrator/app/infrastructure/eventstore_factory.py', 'build_event_store', 0, 8, 7).
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
python_function('services/orchestrator/app/observability/export.py', 'format_logs_text', 1, 29, 5).
python_function('services/orchestrator/app/observability/export.py', 'build_orchestrator_bundle', 0, 11, 8).
python_function('services/orchestrator/app/observability/incidents.py', 'classify_rag_failure', 0, 15, 4).
python_function('services/orchestrator/app/observability/incidents.py', '_event_payload', 2, 19, 9).
python_function('services/orchestrator/app/observability/incidents.py', '_query_from_trace', 1, 4, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_check_names', 1, 6, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_checks_payload', 1, 8, 5).
python_function('services/orchestrator/app/observability/incidents.py', '_root_cause', 2, 4, 2).
python_function('services/orchestrator/app/observability/incidents.py', '_event_status', 2, 12, 1).
python_function('services/orchestrator/app/observability/incidents.py', '_incident_class', 1, 4, 0).
python_function('services/orchestrator/app/observability/incidents.py', '_default_playbook', 1, 1, 1).
python_function('services/orchestrator/app/observability/logging.py', 'log_event', 0, 3, 9).
python_function('services/orchestrator/app/rag/chunking.py', 'chunk_text', 1, 7, 5).
python_function('services/orchestrator/app/rag/openrouter.py', 'normalize_openrouter_model', 1, 3, 3).
python_function('services/orchestrator/app/rag/store.py', '_cosine', 2, 9, 4).
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
python_function('services/projector/app/projections/agent_fleet.py', 'project_agent_fleet', 2, 8, 4).
python_function('services/projector/app/projections/approval_requests.py', 'project_approval_requests', 2, 6, 2).
python_function('services/projector/app/projections/dispatcher.py', 'project_event', 2, 1, 9).
python_function('services/projector/app/projections/dispatcher.py', '_normalize_event', 1, 7, 5).
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
python_function('services/projector/app/projections/incidents.py', '_checks_payload', 1, 10, 5).
python_function('services/projector/app/projections/incidents.py', '_root_cause', 1, 4, 4).
python_function('services/projector/app/projections/incidents.py', '_diagnostics_ok', 1, 6, 3).
python_function('services/projector/app/projections/operational_feed.py', 'project_operational_feed', 2, 3, 5).
python_function('services/projector/app/projections/operational_feed.py', '_title_for', 2, 11, 1).
python_function('services/projector/app/projections/operational_feed.py', '_summary_for', 2, 6, 1).
python_function('services/projector/app/projections/plugin_catalog.py', 'project_plugin_catalog', 2, 5, 3).
python_function('services/projector/app/projections/resource_registry.py', 'project_resource_registry', 2, 8, 3).
python_function('services/projector/app/projections/task_board.py', 'project_task_board', 2, 9, 4).
python_function('services/projector/app/projections/task_board.py', '_update_status', 5, 1, 1).
python_function('services/projector/app/projections/workflow_versions.py', 'project_workflow_versions', 2, 5, 4).
python_function('services/web/app/access_matrix.py', '_matrix_path', 0, 2, 3).
python_function('services/web/app/access_matrix.py', '_default_resources', 0, 3, 2).
python_function('services/web/app/access_matrix.py', '_default_agents', 0, 5, 5).
python_function('services/web/app/access_matrix.py', '_empty_agent_resource', 2, 3, 0).
python_function('services/web/app/access_matrix.py', '_empty_human_agent', 2, 3, 0).
python_function('services/web/app/access_matrix.py', 'default_state', 0, 1, 5).
python_function('services/web/app/access_matrix.py', 'load_state', 0, 8, 9).
python_function('services/web/app/access_matrix.py', '_merge_bool_matrix', 2, 7, 3).
python_function('services/web/app/access_matrix.py', '_reindex_state', 1, 12, 7).
python_function('services/web/app/access_matrix.py', 'save_state', 1, 1, 6).
python_function('services/web/app/access_matrix.py', 'agent_may_access_resource', 2, 4, 3).
python_function('services/web/app/access_matrix.py', 'human_may_use_agent', 2, 4, 3).
python_function('services/web/app/access_matrix.py', 'diagnose_file_list_command', 0, 1, 0).
python_function('services/web/app/agent_workroom.py', 'create_workroom', 0, 1, 2).
python_function('services/web/app/agent_workroom.py', 'get_workroom', 1, 1, 1).
python_function('services/web/app/agent_workroom.py', '_plan_steps', 1, 4, 4).
python_function('services/web/app/agent_workroom.py', '_extract_shell', 1, 4, 5).
python_function('services/web/app/agent_workroom.py', 'run_workroom', 2, 22, 18).
python_function('services/web/app/agent_workroom.py', 'workroom_catalog', 0, 1, 2).
python_function('services/web/app/api_routes.py', 'start_chat_session', 1, 2, 4).
python_function('services/web/app/api_routes.py', 'get_chat_session', 1, 2, 3).
python_function('services/web/app/api_routes.py', 'workspace_state', 1, 1, 3).
python_function('services/web/app/api_routes.py', 'chat_message', 1, 6, 8).
python_function('services/web/app/api_routes.py', 'task_draft', 1, 1, 2).
python_function('services/web/app/api_routes.py', 'create_task', 1, 6, 7).
python_function('services/web/app/api_routes.py', 'create_task_from_draft', 1, 2, 4).
python_function('services/web/app/api_routes.py', 'create_and_run_task', 1, 2, 4).
python_function('services/web/app/api_routes.py', 'context_attach', 1, 1, 2).
python_function('services/web/app/api_routes.py', 'upload_files', 3, 6, 9).
python_function('services/web/app/api_routes.py', 'board_snapshot', 0, 1, 2).
python_function('services/web/app/api_routes.py', 'list_tickets', 2, 10, 5).
python_function('services/web/app/api_routes.py', 'get_ticket', 2, 5, 6).
python_function('services/web/app/api_routes.py', 'confirm_ticket', 2, 19, 11).
python_function('services/web/app/api_routes.py', 'archive_ticket', 2, 1, 2).
python_function('services/web/app/api_routes.py', 'link_ticket', 2, 1, 2).
python_function('services/web/app/api_routes.py', 'ticket_statuses', 0, 1, 1).
python_function('services/web/app/api_routes.py', 'workspace_list_artifacts', 1, 1, 3).
python_function('services/web/app/api_routes.py', 'workspace_get_artifact', 2, 2, 3).
python_function('services/web/app/api_routes.py', 'workspace_file_list_export', 3, 2, 9).
python_function('services/web/app/api_routes.py', 'workspace_chat_export', 1, 7, 7).
python_function('services/web/app/api_routes.py', 'workspace_logs_export', 2, 1, 5).
python_function('services/web/app/api_routes.py', 'workroom_start', 1, 2, 5).
python_function('services/web/app/api_routes.py', 'workroom_get', 1, 2, 4).
python_function('services/web/app/api_routes.py', 'workroom_run', 2, 2, 4).
python_function('services/web/app/api_routes.py', 'api_resource_areas', 0, 1, 3).
python_function('services/web/app/api_routes.py', 'api_role_scopes', 0, 1, 1).
python_function('services/web/app/api_routes.py', 'access_matrix_get', 0, 1, 2).
python_function('services/web/app/api_routes.py', 'access_matrix_put', 1, 1, 5).
python_function('services/web/app/api_routes.py', 'access_matrix_reset', 0, 1, 3).
python_function('services/web/app/api_routes.py', 'access_diagnose_file_list', 0, 1, 2).
python_function('services/web/app/chat.py', '_orch', 0, 2, 1).
python_function('services/web/app/chat.py', '_projector', 0, 1, 1).
python_function('services/web/app/chat.py', 'is_file_list_intent', 1, 7, 4).
python_function('services/web/app/chat.py', 'file_list_scope', 1, 7, 2).
python_function('services/web/app/chat.py', '_uri_is_user_resource', 1, 6, 2).
python_function('services/web/app/chat.py', '_uri_is_system_resource', 1, 5, 3).
python_function('services/web/app/chat.py', 'filter_file_inventory', 2, 29, 4).
python_function('services/web/app/chat.py', '_dedupe_rows_by_uri', 1, 8, 7).
python_function('services/web/app/chat.py', 'fetch_file_inventory', 0, 7, 7).
python_function('services/web/app/chat.py', 'format_file_list_reply', 1, 8, 7).
python_function('services/web/app/chat.py', '_append_session_files', 4, 7, 3).
python_function('services/web/app/chat.py', '_format_scope_uri', 1, 2, 1).
python_function('services/web/app/chat.py', '_append_resource_rows', 3, 7, 5).
python_function('services/web/app/chat.py', '_empty_resource_hint', 1, 2, 0).
python_function('services/web/app/chat.py', '_append_rag_rows', 3, 9, 4).
python_function('services/web/app/chat.py', '_append_file_list_errors', 2, 2, 2).
python_function('services/web/app/chat.py', '_append_file_list_tip', 4, 5, 1).
python_function('services/web/app/chat.py', 'build_file_list_artifact', 2, 1, 2).
python_function('services/web/app/chat.py', 'new_session_id', 0, 1, 2).
python_function('services/web/app/chat.py', 'get_history', 1, 1, 2).
python_function('services/web/app/chat.py', '_append', 3, 1, 2).
python_function('services/web/app/chat.py', '_format_history', 1, 3, 3).
python_function('services/web/app/chat.py', '_format_incident', 1, 15, 3).
python_function('services/web/app/chat.py', 'handle_message', 0, 5, 7).
python_function('services/web/app/chat.py', '_file_list_answer', 1, 2, 5).
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
python_function('services/web/app/chat.py', '_message_response', 0, 7, 3).
python_function('services/web/app/chat.py', 'create_task', 0, 7, 5).
python_function('services/web/app/conductor.py', 'handle_turn', 0, 7, 7).
python_function('services/web/app/conductor.py', '_nlp2dsl_turn', 0, 7, 6).
python_function('services/web/app/conductor.py', '_call_nlp2dsl', 2, 2, 2).
python_function('services/web/app/conductor.py', '_nlp_output_base', 2, 1, 0).
python_function('services/web/app/conductor.py', '_in_progress_turn', 6, 3, 3).
python_function('services/web/app/conductor.py', '_ready_turn', 0, 1, 7).
python_function('services/web/app/conductor.py', '_ready_action_payload', 1, 4, 3).
python_function('services/web/app/conductor.py', '_system_file_list_payload', 4, 1, 5).
python_function('services/web/app/conductor.py', '_shell_task_payload', 5, 4, 5).
python_function('services/web/app/conductor.py', '_shell_clarify_payload', 1, 1, 0).
python_function('services/web/app/conductor.py', '_ticket_payload', 4, 3, 3).
python_function('services/web/app/conductor.py', '_task_reply', 1, 3, 1).
python_function('services/web/app/conductor.py', '_closed_turn', 5, 2, 2).
python_function('services/web/app/conductor.py', '_append_turn', 3, 3, 2).
python_function('services/web/app/conductor.py', '_mullm_file_list_turn', 0, 1, 7).
python_function('services/web/app/conductor.py', '_fallback_turn', 0, 4, 5).
python_function('services/web/app/conductor.py', '_local_clarify', 1, 3, 3).
python_function('services/web/app/conductor.py', '_extract_shell', 1, 3, 4).
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
python_function('services/web/app/nlp2dsl_bridge.py', '_post_json', 2, 4, 6).
python_function('services/web/app/nlp2dsl_bridge.py', 'form_to_prompt', 2, 6, 4).
python_function('services/web/app/nlp2dsl_bridge.py', 'primary_action', 1, 4, 1).
python_function('services/web/app/nlp2dsl_bridge.py', 'step_config', 1, 5, 1).
python_function('services/web/app/resource_areas.py', 'list_areas', 0, 2, 1).
python_function('services/web/app/resource_areas.py', 'list_groups', 0, 1, 0).
python_function('services/web/app/resource_areas.py', 'agent_may_access', 3, 9, 2).
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
python_function('services/web/app/workspace.py', 'workspace_state', 1, 1, 4).
python_function('services/web/app/workspace.py', 'attach_context', 1, 12, 4).
python_function('services/web/app/workspace.py', '_extract_ticket', 1, 2, 2).
python_function('services/web/app/workspace.py', '_extract_shell_command', 1, 4, 4).
python_function('services/web/app/workspace.py', 'build_task_payload', 2, 4, 5).
python_function('services/web/app/workspace.py', 'propose_task_draft', 2, 1, 1).
python_function('services/web/app/workspace.py', 'create_task_immediate', 1, 3, 5).
python_function('services/web/app/workspace.py', 'handle_chat_message', 0, 22, 17).
python_function('services/web/app/workspace.py', 'create_task_from_draft', 1, 4, 3).
python_function('services/web/app/workspace.py', 'create_and_run', 1, 5, 4).
python_function('services/web/app/workspace.py', 'export_debug_logs', 1, 15, 13).
python_function('services/web/app/workspace.py', '_format_export_text', 1, 47, 8).
python_function('services/web/app/workspace.py', 'archive_task', 2, 2, 3).
python_function('services/web/app/workspace.py', 'link_ticket', 2, 3, 3).
python_function('services/web/app/workspace.py', 'fetch_live_board', 0, 1, 5).
python_function('services/web/tests/test_access_matrix.py', 'matrix_file', 1, 1, 4).
python_function('services/web/tests/test_access_matrix.py', 'test_default_all_checked', 1, 3, 1).
python_function('services/web/tests/test_access_matrix.py', 'test_save_and_deny', 1, 3, 3).
python_function('services/web/tests/test_access_matrix.py', 'test_diagnose_file_list_no_shell', 0, 3, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_plan_includes_files_for_lista_plikow', 0, 3, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_files_agent_may_list_rag', 0, 2, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_mail_agent_denied_rag', 0, 2, 1).
python_function('services/web/tests/test_agent_workroom.py', 'test_groups_nonempty', 0, 2, 2).
python_function('services/web/tests/test_agent_workroom.py', 'test_workroom_session_dict', 0, 3, 2).
python_function('services/web/tests/test_artifacts.py', 'test_register_and_get_artifact', 0, 7, 6).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_intent_pl', 0, 5, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_format_file_list', 0, 4, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_scope_usera', 0, 4, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_filter_user_files', 0, 3, 3).
python_function('services/web/tests/test_chat_intent.py', 'test_file_list_artifact', 0, 5, 2).
python_function('services/web/tests/test_chat_intent.py', 'test_format_user_scope_title', 0, 3, 1).
python_function('services/web/tests/test_chat_intent.py', 'test_dedupe_rag_documents_by_uri', 0, 2, 2).
python_function('services/web/tests/test_chat_intent.py', 'test_handle_message_file_list_builds_artifact', 1, 4, 2).
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
python_method('CommandBus', 'handle', 0, 29, 29).
python_method('CommandBus', 'handle_envelope', 1, 4, 2).
python_method('CommandBus', '_create_task', 4, 6, 11).
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
python_method('CommandBus', '_record_task_outcome', 1, 12, 5).
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
python_method('Task', 'apply', 1, 11, 7).
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
python_class('services/orchestrator/app/domain/events/__init__.py', 'DomainEvent').
python_method('DomainEvent', 'aggregate_id', 0, 1, 0).
python_method('DomainEvent', 'data', 0, 1, 0).
python_method('DomainEvent', 'to_message', 0, 3, 3).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskCreated').
python_method('TaskCreated', 'aggregate_id', 0, 1, 1).
python_method('TaskCreated', 'data', 0, 1, 2).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskAssigned').
python_method('TaskAssigned', 'aggregate_id', 0, 1, 1).
python_method('TaskAssigned', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskStarted').
python_method('TaskStarted', 'aggregate_id', 0, 1, 1).
python_method('TaskStarted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskCompleted').
python_method('TaskCompleted', 'aggregate_id', 0, 1, 1).
python_method('TaskCompleted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskFailed').
python_method('TaskFailed', 'aggregate_id', 0, 1, 1).
python_method('TaskFailed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'AgentRegistered').
python_method('AgentRegistered', 'aggregate_id', 0, 1, 1).
python_method('AgentRegistered', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'AgentHeartbeatReceived').
python_method('AgentHeartbeatReceived', 'aggregate_id', 0, 1, 1).
python_method('AgentHeartbeatReceived', 'data', 0, 1, 2).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TaskAssignedToAgent').
python_method('TaskAssignedToAgent', 'aggregate_id', 0, 1, 1).
python_method('TaskAssignedToAgent', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'AgentMarkedIdle').
python_method('AgentMarkedIdle', 'aggregate_id', 0, 1, 1).
python_method('AgentMarkedIdle', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowStarted').
python_method('WorkflowStarted', 'aggregate_id', 0, 1, 1).
python_method('WorkflowStarted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionProposed').
python_method('WorkflowVersionProposed', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionProposed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionValidated').
python_method('WorkflowVersionValidated', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionValidated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionApproved').
python_method('WorkflowVersionApproved', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionApproved', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionShadowed').
python_method('WorkflowVersionShadowed', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionShadowed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionActivated').
python_method('WorkflowVersionActivated', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionActivated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'WorkflowVersionRolledBack').
python_method('WorkflowVersionRolledBack', 'aggregate_id', 0, 1, 1).
python_method('WorkflowVersionRolledBack', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'PluginProposed').
python_method('PluginProposed', 'aggregate_id', 0, 1, 1).
python_method('PluginProposed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'PluginValidated').
python_method('PluginValidated', 'aggregate_id', 0, 1, 1).
python_method('PluginValidated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'PluginInstalled').
python_method('PluginInstalled', 'aggregate_id', 0, 1, 1).
python_method('PluginInstalled', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'PluginActivated').
python_method('PluginActivated', 'aggregate_id', 0, 1, 1).
python_method('PluginActivated', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'PluginRolledBack').
python_method('PluginRolledBack', 'aggregate_id', 0, 1, 1).
python_method('PluginRolledBack', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ApprovalRequested').
python_method('ApprovalRequested', 'aggregate_id', 0, 1, 1).
python_method('ApprovalRequested', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ApprovalGranted').
python_method('ApprovalGranted', 'aggregate_id', 0, 1, 1).
python_method('ApprovalGranted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ApprovalRejected').
python_method('ApprovalRejected', 'aggregate_id', 0, 1, 1).
python_method('ApprovalRejected', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ChangeProposed').
python_method('ChangeProposed', 'aggregate_id', 0, 1, 0).
python_method('ChangeProposed', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/__init__.py', 'CapabilityRegistered').
python_method('CapabilityRegistered', 'aggregate_id', 0, 1, 0).
python_method('CapabilityRegistered', 'data', 0, 1, 0).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ResourceRegistered').
python_method('ResourceRegistered', 'aggregate_id', 0, 1, 1).
python_method('ResourceRegistered', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TransferRequested').
python_method('TransferRequested', 'aggregate_id', 0, 1, 1).
python_method('TransferRequested', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TransferCompleted').
python_method('TransferCompleted', 'aggregate_id', 0, 1, 1).
python_method('TransferCompleted', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'TransferFailed').
python_method('TransferFailed', 'aggregate_id', 0, 1, 1).
python_method('TransferFailed', 'data', 0, 1, 1).
python_class('services/orchestrator/app/domain/events/__init__.py', 'ApprovalExpired').
python_method('ApprovalExpired', 'aggregate_id', 0, 1, 1).
python_method('ApprovalExpired', 'data', 0, 1, 1).
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
python_method('EvaluationEngine', '_upsert_metrics', 0, 13, 4).
python_method('EvaluationEngine', 'should_auto_rollback', 2, 7, 3).
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
python_method('PolicyEngine', 'validate_command', 2, 14, 5).
python_method('PolicyEngine', 'validate_activation_metrics', 3, 7, 7).
python_class('services/orchestrator/app/incidents/pipeline.py', 'IncidentPipeline').
python_method('IncidentPipeline', '__init__', 0, 1, 0).
python_method('IncidentPipeline', 'handle_rag_failure', 0, 7, 14).
python_method('IncidentPipeline', '_run_rag_diagnostics', 1, 14, 11).
python_method('IncidentPipeline', '_remediate_rag_incident', 0, 6, 12).
python_method('IncidentPipeline', '_verify_rag', 1, 4, 2).
python_method('IncidentPipeline', '_append_and_publish', 2, 5, 5).
python_method('IncidentPipeline', '_with_incident_id', 2, 2, 3).
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
python_method('IncidentRecorder', 'record', 0, 16, 10).
python_method('IncidentRecorder', '_persist', 1, 2, 3).
python_method('IncidentRecorder', '_publish_event', 2, 3, 6).
python_class('services/orchestrator/app/observability/middleware.py', 'CorrelationMiddleware').
python_method('CorrelationMiddleware', 'dispatch', 2, 3, 4).
python_class('services/orchestrator/app/observability/rag_diagnostics.py', 'RagDiagnostics').
python_method('RagDiagnostics', 'run', 0, 12, 16).
python_method('RagDiagnostics', '_check_postgres', 0, 4, 2).
python_method('RagDiagnostics', '_check_rag_tables', 0, 5, 2).
python_method('RagDiagnostics', '_check_openrouter_config', 0, 2, 0).
python_method('RagDiagnostics', '_check_embedding', 0, 3, 3).
python_method('RagDiagnostics', '_check_search', 1, 3, 3).
python_method('RagDiagnostics', '_recommendations', 1, 6, 2).
python_method('RagDiagnostics', '_snapshot', 1, 2, 5).
python_class('services/orchestrator/app/observability/rag_pipeline.py', 'RagPipeline').
python_method('RagPipeline', 'ask', 0, 10, 17).
python_method('RagPipeline', '_failure_payload', 0, 1, 1).
python_class('services/orchestrator/app/rag/indexer.py', 'RagIndexer').
python_method('RagIndexer', '__init__', 3, 1, 0).
python_method('RagIndexer', 'ingest_resource', 0, 13, 14).
python_class('services/orchestrator/app/rag/openrouter.py', 'OpenRouterClient').
python_method('OpenRouterClient', '__init__', 1, 2, 2).
python_method('OpenRouterClient', 'configured', 0, 1, 1).
python_method('OpenRouterClient', '_headers', 0, 1, 0).
python_method('OpenRouterClient', 'embed', 1, 5, 9).
python_method('OpenRouterClient', 'chat', 1, 9, 8).
python_method('OpenRouterClient', 'health', 0, 1, 0).
python_class('services/orchestrator/app/rag/retriever.py', 'RagRetriever').
python_method('RagRetriever', '__init__', 2, 1, 0).
python_method('RagRetriever', 'search', 1, 4, 2).
python_method('RagRetriever', 'ask', 1, 8, 4).
python_class('services/orchestrator/app/rag/store.py', 'RagStore').
python_method('RagStore', '__init__', 1, 1, 0).
python_method('RagStore', 'upsert_document_pending', 0, 1, 1).
python_method('RagStore', 'mark_indexed', 0, 1, 1).
python_method('RagStore', 'mark_failed', 0, 1, 1).
python_method('RagStore', 'replace_chunks', 0, 3, 4).
python_method('RagStore', 'list_documents', 0, 2, 2).
python_method('RagStore', 'search', 1, 10, 11).
python_method('RagStore', '_keyword_fallback', 1, 10, 11).
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
python_class('services/web/app/agent_workroom.py', 'LedgerEntry').
python_method('LedgerEntry', 'to_dict', 0, 2, 0).
python_class('services/web/app/agent_workroom.py', 'WorkroomSession').
python_method('WorkroomSession', 'add_ledger', 3, 1, 2).
python_method('WorkroomSession', 'agent_say', 3, 1, 2).
python_method('WorkroomSession', 'to_dict', 0, 2, 1).
python_class('services/web/app/api_routes.py', 'ChatSessionStart').
python_class('services/web/app/api_routes.py', 'ChatMessage').
python_class('services/web/app/api_routes.py', 'TaskDraftRequest').
python_class('services/web/app/api_routes.py', 'CreateTaskBody').
python_class('services/web/app/api_routes.py', 'CreateFromDraftBody').
python_class('services/web/app/api_routes.py', 'ConfirmTicketBody').
python_class('services/web/app/api_routes.py', 'ContextAttachBody').
python_class('services/web/app/api_routes.py', 'SessionRef').
python_class('services/web/app/api_routes.py', 'WorkroomStart').
python_class('services/web/app/api_routes.py', 'WorkroomMessage').
python_class('services/web/app/api_routes.py', 'AccessMatrixBody').
python_class('services/web/app/workspace.py', 'WorkspaceContext').
python_method('WorkspaceContext', 'to_dict', 0, 1, 0).
python_class('services/web/app/workspace.py', 'WorkspaceSession').
python_method('WorkspaceSession', 'add_event', 2, 2, 2).
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

% ── Makefile Targets ─────────────────────────────────────
makefile_target('SHELL', '').
makefile_target('PROFILE_ARGS', '').
makefile_target('help', '').
makefile_target('up', '').
makefile_target('down', '').
makefile_target('restart', '').
makefile_target('build', '').
makefile_target('logs', '').
makefile_target('ps', '').
makefile_target('test', '').
makefile_target('smoke', '').
makefile_target('ensure-env', '').
makefile_target('ensure-nlp2dsl-env', '').
makefile_target('nlp2dsl-up', '').
makefile_target('nlp2dsl-down', '').

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
sumd_workflow_step('up', 1, '$(COMPOSE) $(PROFILE_ARGS) up -d').
sumd_workflow_step('up', 2, 'if [ "$(NLP2DSL)" = "1" ]').
sumd_workflow_step('up', 3, '$(MAKE) --no-print-directory nlp2dsl-up').
sumd_workflow_step('up', 4, 'fi').
sumd_workflow('down', 'manual').
sumd_workflow_step('down', 1, 'if [ "$(NLP2DSL)" = "1" ]').
sumd_workflow_step('down', 2, '$(MAKE) --no-print-directory nlp2dsl-down').
sumd_workflow_step('down', 3, 'fi').
sumd_workflow_step('down', 4, '$(COMPOSE) $(PROFILE_ARGS) down').
sumd_workflow('restart', 'manual').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, '$(COMPOSE) $(PROFILE_ARGS) build').
sumd_workflow('logs', 'manual').
sumd_workflow_step('logs', 1, '$(COMPOSE) $(PROFILE_ARGS) logs -f --tail=200').
sumd_workflow('ps', 'manual').
sumd_workflow_step('ps', 1, '$(COMPOSE) $(PROFILE_ARGS) ps').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'pytest -q').
sumd_workflow('smoke', 'manual').
sumd_workflow_step('smoke', 1, 'curl -fsS http://127.0.0.1:3003/health').
sumd_workflow_step('smoke', 2, 'curl -fsS http://127.0.0.1:8001/health').
sumd_workflow_step('smoke', 3, 'curl -fsS http://127.0.0.1:8002/health').
sumd_workflow_step('smoke', 4, 'if [ "$(NLP2DSL)" = "1" ] && [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]').
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
sumd_deploy_target('docker_compose').
sumd_deploy_compose_file('docker-compose.yml').
```

## Call Graph

*340 nodes · 423 edges · 54 modules · CC̄=3.6*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_format_export_text` *(in services.web.app.workspace)* | 47 ⚠ | 1 | 97 | **98** |
| `format_logs_text` *(in services.orchestrator.app.observability.export)* | 29 ⚠ | 1 | 66 | **67** |
| `run_workroom` *(in services.web.app.agent_workroom)* | 22 ⚠ | 0 | 45 | **45** |
| `handle_chat_message` *(in services.web.app.workspace)* | 22 ⚠ | 0 | 43 | **43** |
| `ask` *(in services.orchestrator.app.observability.rag_pipeline.RagPipeline)* | 10 ⚠ | 0 | 36 | **36** |
| `_event_payload` *(in services.orchestrator.app.observability.incidents)* | 19 ⚠ | 1 | 28 | **29** |
| `export_debug_logs` *(in services.web.app.workspace)* | 15 ⚠ | 0 | 26 | **26** |
| `api` *(in services.web.app.static.workspace)* | 6 | 21 | 4 | **25** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/mullm
# generated in 0.18s
# nodes: 340 | edges: 423 | modules: 54
# CC̄=3.6

HUBS[20]:
  services.web.app.workspace._format_export_text
    CC=47  in:1  out:97  total:98
  services.orchestrator.app.observability.export.format_logs_text
    CC=29  in:1  out:66  total:67
  services.web.app.agent_workroom.run_workroom
    CC=22  in:0  out:45  total:45
  services.web.app.workspace.handle_chat_message
    CC=22  in:0  out:43  total:43
  services.orchestrator.app.observability.rag_pipeline.RagPipeline.ask
    CC=10  in:0  out:36  total:36
  services.orchestrator.app.observability.incidents._event_payload
    CC=19  in:1  out:28  total:29
  services.web.app.workspace.export_debug_logs
    CC=15  in:0  out:26  total:26
  services.web.app.static.workspace.api
    CC=6  in:21  out:4  total:25
  services.orchestrator.app.observability.incidents.IncidentRecorder.record
    CC=16  in:0  out:23  total:23
  services.orchestrator.app.observability.rag_diagnostics.RagDiagnostics.run
    CC=12  in:0  out:23  total:23
  services.orchestrator.app.api.commands._dispatch
    CC=4  in:14  out:9  total:23
  services.web.app.static.workspace.refreshWorkspace
    CC=8  in:8  out:14  total:22
  services.orchestrator.app.api.rag.search
    CC=3  in:0  out:22  total:22
  services.orchestrator.app.rag.indexer.RagIndexer.ingest_resource
    CC=13  in:0  out:22  total:22
  services.web.app.static.workspace.sendChat
    CC=26  in:0  out:21  total:21
  services.orchestrator.app.application.command_bus.CommandBus._create_task
    CC=6  in:0  out:20  total:20
  services.orchestrator.app.api.access.upload_resource
    CC=4  in:0  out:19  total:19
  services.web.app.static.workspace.formValues
    CC=21  in:0  out:19  total:19
  services.web.app.static.workspace.selectTicket
    CC=5  in:7  out:11  total:18
  services.orchestrator.app.observability.export.build_orchestrator_bundle
    CC=11  in:1  out:17  total:18

MODULES:
  agents.shell-agent.app.executor  [1 funcs]
    run_shell_command  CC=4  out:3
  agents.shell-agent.app.nats_consumer  [1 funcs]
    handle_message  CC=4  out:8
  services.orchestrator.app.access.adapters  [1 funcs]
    get_adapter  CC=2  out:5
  services.orchestrator.app.access.transport  [3 funcs]
    copy  CC=4  out:10
    fetch  CC=1  out:4
    probe  CC=1  out:4
  services.orchestrator.app.access.uri  [2 funcs]
    build_uri  CC=2  out:1
    parse_uri  CC=6  out:9
  services.orchestrator.app.api.access  [3 funcs]
    build_resource_uri  CC=1  out:2
    register_resource  CC=2  out:6
    upload_resource  CC=4  out:19
  services.orchestrator.app.api.commands  [15 funcs]
    _dispatch  CC=4  out:9
    activate_plugin  CC=1  out:3
    activate_workflow_version  CC=1  out:3
    approve_request  CC=2  out:2
    approve_workflow_version  CC=1  out:3
    create_approval  CC=1  out:3
    expire_approval  CC=1  out:2
    install_plugin  CC=1  out:3
    propose_plugin  CC=1  out:3
    propose_workflow_version  CC=1  out:3
  services.orchestrator.app.api.observability  [4 funcs]
    export_logs  CC=2  out:6
    list_incidents  CC=3  out:7
    rag_diagnose  CC=1  out:4
    rag_health  CC=1  out:4
  services.orchestrator.app.api.queries  [4 funcs]
    _event_to_dict  CC=2  out:10
    get_agent  CC=6  out:7
    get_task  CC=6  out:7
    get_workflow  CC=6  out:7
  services.orchestrator.app.api.rag  [2 funcs]
    ask  CC=1  out:6
    search  CC=3  out:22
  services.orchestrator.app.application.command_bus  [7 funcs]
    _activate_plugin  CC=1  out:4
    _activate_workflow_version  CC=3  out:6
    _approve_request  CC=3  out:6
    _create_task  CC=6  out:20
    _register_resource  CC=5  out:16
    _rollback_plugin  CC=1  out:5
    _rollback_workflow_version  CC=1  out:5
  services.orchestrator.app.application.sagas.approval_gate  [3 funcs]
    _is_skipped  CC=3  out:3
    ensure_approval  CC=8  out:13
    follow_up_after_grant  CC=5  out:3
  services.orchestrator.app.application.sagas.task_routing  [2 funcs]
    maybe_auto_assign  CC=5  out:6
    pick_idle_agent  CC=10  out:5
  services.orchestrator.app.config  [1 funcs]
    model_post_init  CC=1  out:2
  services.orchestrator.app.domain.aggregates.agent  [1 funcs]
    heartbeat  CC=1  out:3
  services.orchestrator.app.domain.aggregates.task  [10 funcs]
    __init__  CC=4  out:5
    apply  CC=11  out:18
    assign_to_agent  CC=2  out:4
    complete  CC=2  out:4
    fail  CC=2  out:4
    start  CC=3  out:5
    _event_data  CC=2  out:3
    _event_timestamp  CC=3  out:5
    _event_type  CC=1  out:1
    _utc_now  CC=1  out:1
  services.orchestrator.app.incidents.pipeline  [2 funcs]
    handle_rag_failure  CC=7  out:16
    classify_rag_error  CC=11  out:2
  services.orchestrator.app.infrastructure.eventstore  [4 funcs]
    _record_from_row  CC=1  out:3
    append  CC=6  out:15
    _loads_json  CC=3  out:3
    _utc_now  CC=1  out:1
  services.orchestrator.app.infrastructure.eventstore_esdb  [2 funcs]
    __init__  CC=1  out:1
    _parse_esdb_uri  CC=4  out:6
  services.orchestrator.app.observability.context  [6 funcs]
    get_chat_session_id  CC=1  out:1
    get_correlation_id  CC=1  out:1
    get_retrieval_trace_id  CC=1  out:1
    new_correlation_id  CC=1  out:2
    new_retrieval_trace_id  CC=1  out:1
    observability_context  CC=5  out:8
  services.orchestrator.app.observability.export  [2 funcs]
    build_orchestrator_bundle  CC=11  out:17
    format_logs_text  CC=29  out:66
  services.orchestrator.app.observability.incidents  [6 funcs]
    _persist  CC=2  out:4
    _publish_event  CC=3  out:6
    record  CC=16  out:23
    _default_playbook  CC=1  out:1
    _event_payload  CC=19  out:28
    _incident_class  CC=4  out:0
  services.orchestrator.app.observability.logging  [1 funcs]
    log_event  CC=3  out:9
  services.orchestrator.app.observability.middleware  [1 funcs]
    dispatch  CC=3  out:5
  services.orchestrator.app.observability.rag_diagnostics  [1 funcs]
    run  CC=12  out:23
  services.orchestrator.app.observability.rag_pipeline  [1 funcs]
    ask  CC=10  out:36
  services.orchestrator.app.rag.chunking  [1 funcs]
    chunk_text  CC=7  out:9
  services.orchestrator.app.rag.indexer  [1 funcs]
    ingest_resource  CC=13  out:22
  services.orchestrator.app.rag.openrouter  [2 funcs]
    __init__  CC=2  out:3
    normalize_openrouter_model  CC=3  out:3
  services.orchestrator.app.rag.store  [7 funcs]
    _keyword_fallback  CC=10  out:12
    list_documents  CC=2  out:2
    search  CC=10  out:13
    _chunk_hit  CC=2  out:5
    _cosine  CC=9  out:8
    _parse_embedding  CC=5  out:6
    _row_dict  CC=4  out:5
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
    project_agent_fleet  CC=8  out:11
  services.projector.app.projections.approval_requests  [1 funcs]
    project_approval_requests  CC=6  out:9
  services.projector.app.projections.dispatcher  [2 funcs]
    _normalize_event  CC=7  out:9
    project_event  CC=1  out:9
  services.projector.app.projections.incidents  [16 funcs]
    _checks_payload  CC=10  out:11
    _diagnostics_ok  CC=6  out:4
    _error_code  CC=4  out:3
    _handle_diagnostics_completed  CC=4  out:9
    _handle_diagnostics_started  CC=1  out:2
    _handle_incident_classified  CC=1  out:5
    _handle_incident_detected  CC=6  out:12
    _handle_post_remediation_verification  CC=4  out:4
    _handle_rag_request_failed  CC=2  out:6
    _handle_remediation_finished  CC=2  out:7
  services.projector.app.projections.operational_feed  [3 funcs]
    _summary_for  CC=6  out:6
    _title_for  CC=11  out:8
    project_operational_feed  CC=3  out:10
  services.projector.app.projections.plugin_catalog  [1 funcs]
    project_plugin_catalog  CC=5  out:6
  services.projector.app.projections.resource_registry  [1 funcs]
    project_resource_registry  CC=8  out:15
  services.projector.app.projections.task_board  [2 funcs]
    _update_status  CC=1  out:1
    project_task_board  CC=9  out:15
  services.projector.app.projections.workflow_versions  [1 funcs]
    project_workflow_versions  CC=5  out:6
  services.web.app.access_matrix  [12 funcs]
    _default_agents  CC=5  out:7
    _default_resources  CC=3  out:2
    _empty_agent_resource  CC=3  out:0
    _empty_human_agent  CC=3  out:0
    _matrix_path  CC=2  out:4
    _merge_bool_matrix  CC=7  out:5
    _reindex_state  CC=12  out:16
    agent_may_access_resource  CC=4  out:6
    default_state  CC=1  out:5
    human_may_use_agent  CC=4  out:6
  services.web.app.agent_workroom  [5 funcs]
    _extract_shell  CC=4  out:8
    _plan_steps  CC=4  out:7
    get_workroom  CC=1  out:1
    run_workroom  CC=22  out:45
    workroom_catalog  CC=1  out:2
  services.web.app.api_routes  [3 funcs]
    chat_message  CC=6  out:10
    get_ticket  CC=5  out:9
    list_tickets  CC=10  out:7
  services.web.app.chat  [36 funcs]
    _answer_from_rag_payload  CC=6  out:3
    _append  CC=1  out:2
    _append_file_list_errors  CC=2  out:3
    _append_file_list_tip  CC=5  out:5
    _append_rag_rows  CC=9  out:11
    _append_resource_rows  CC=7  out:12
    _append_session_files  CC=7  out:9
    _ask_rag  CC=5  out:9
    _dedupe_rows_by_uri  CC=8  out:10
    _default_chat_reply  CC=1  out:0
  services.web.app.conductor  [18 funcs]
    _append_turn  CC=3  out:4
    _call_nlp2dsl  CC=2  out:2
    _closed_turn  CC=2  out:2
    _extract_shell  CC=3  out:5
    _fallback_turn  CC=4  out:7
    _in_progress_turn  CC=3  out:4
    _local_clarify  CC=3  out:3
    _mullm_file_list_turn  CC=1  out:8
    _nlp2dsl_turn  CC=7  out:8
    _nlp_output_base  CC=1  out:0
  services.web.app.nlp2dsl_bridge  [6 funcs]
    _post_json  CC=4  out:6
    backend_candidates  CC=4  out:6
    backend_url  CC=1  out:1
    chat_message  CC=1  out:1
    chat_start  CC=1  out:1
    health  CC=4  out:3
  services.web.app.resource_areas  [3 funcs]
    agent_may_access  CC=9  out:4
    list_areas  CC=2  out:1
    list_groups  CC=1  out:0
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
  services.web.app.static.app  [7 funcs]
    appendMessage  CC=2  out:2
    ensureSession  CC=3  out:4
    escapeHtml  CC=1  out:2
    renderHistory  CC=7  out:2
    rowTask  CC=6  out:2
    text  CC=16  out:15
    uploadFiles  CC=8  out:5
  services.web.app.static.workroom  [14 funcs]
    api  CC=5  out:3
    data  CC=1  out:1
    ensureWorkroom  CC=4  out:4
    escapeHtml  CC=1  out:2
    loadAreas  CC=2  out:2
    refresh  CC=6  out:5
    renderCatalog  CC=11  out:4
    renderLedger  CC=7  out:3
    renderState  CC=3  out:2
    renderThread  CC=7  out:3
  services.web.app.static.workspace  [57 funcs]
    api  CC=6  out:4
    appendMsg  CC=1  out:1
    appendMsgTo  CC=6  out:2
    archiveTicket  CC=2  out:5
    cacheArtifactFull  CC=3  out:1
    clearArtifactPreview  CC=8  out:3
    collectClarifyValues  CC=4  out:4
    color  CC=1  out:1
    confirmTicket  CC=1  out:6
    copyChatToClipboard  CC=10  out:11
  services.web.app.tickets  [4 funcs]
    enrich_task  CC=4  out:6
    status_meta  CC=3  out:2
    ticket_uri  CC=1  out:0
    ticket_web_path  CC=1  out:0
  services.web.app.workspace  [22 funcs]
    _artifact_title  CC=6  out:4
    _extract_shell_command  CC=4  out:8
    _extract_ticket  CC=2  out:2
    _format_export_text  CC=47  out:97
    archive_task  CC=2  out:3
    artifact_summaries  CC=2  out:11
    attach_context  CC=12  out:7
    build_task_payload  CC=4  out:7
    create_and_run  CC=5  out:9
    create_task_from_draft  CC=4  out:5
  services.web.src.main  [2 funcs]
    createTask  CC=4  out:9
    refresh  CC=7  out:8

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
  services.projector.app.projections.task_board.project_task_board → services.projector.app.projections.task_board._update_status
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
  services.projector.app.projections.incidents._root_cause → services.projector.app.projections.incidents._error_code
  services.web.app.agent_workroom._plan_steps → services.web.app.agent_workroom._extract_shell
  services.web.app.agent_workroom.run_workroom → services.web.app.agent_workroom.get_workroom
  services.web.app.agent_workroom.run_workroom → services.web.app.agent_workroom._plan_steps
  services.web.app.agent_workroom.workroom_catalog → services.web.app.resource_areas.list_areas
  services.web.app.agent_workroom.workroom_catalog → services.web.app.resource_areas.list_groups
  services.web.app.tickets.enrich_task → services.web.app.tickets.status_meta
  services.web.app.tickets.enrich_task → services.web.app.tickets.ticket_uri
  services.web.app.tickets.enrich_task → services.web.app.tickets.ticket_web_path
  services.web.app.nlp2dsl_bridge.backend_url → services.web.app.nlp2dsl_bridge.backend_candidates
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
