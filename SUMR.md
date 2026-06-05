# Mullm - Multi-Agent Learning and Labor Management

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `mullm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements-dev.txt, requirements-quality.txt, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(5 analysis files)

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

## Workflows

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 189f 29599L | python:116,md:25,json:12,yaml:9,txt:7,shell:7,javascript:5,ini:2,yml:1 | 2026-06-05
# generated in 0.06s
# CC̅=2.9 | critical:1/1305 | dups:0 | cycles:0

HEALTH[1]:
  🟡 CC    explain_pipeline CC=16 (limit:15)

REFACTOR[1]:
  1. split 1 high-CC methods  (CC>15)

PIPELINES[562]:
  [1] Src [lifespan]: lifespan → project_event → _normalize_event → _event_payload
      PURITY: 100% pure
  [2] Src [health_check]: health_check
      PURITY: 100% pure
  [3] Src [operational_feed]: operational_feed → _row_to_dict
      PURITY: 100% pure
  [4] Src [task_board]: task_board → _row_to_dict
      PURITY: 100% pure
  [5] Src [agent_fleet]: agent_fleet → _row_to_dict
      PURITY: 100% pure
  [6] Src [approval_requests]: approval_requests → _row_to_dict
      PURITY: 100% pure
  [7] Src [plugin_catalog]: plugin_catalog → _row_to_dict
      PURITY: 100% pure
  [8] Src [rag_documents]: rag_documents → _row_to_dict
      PURITY: 100% pure
  [9] Src [incident_feed]: incident_feed → _row_to_dict
      PURITY: 100% pure
  [10] Src [service_health]: service_health → _row_to_dict
      PURITY: 100% pure
  [11] Src [remediation_history]: remediation_history → _row_to_dict
      PURITY: 100% pure
  [12] Src [rag_quality_board]: rag_quality_board → _row_to_dict
      PURITY: 100% pure
  [13] Src [resource_registry]: resource_registry → _row_to_dict
      PURITY: 100% pure
  [14] Src [workflow_versions]: workflow_versions → _row_to_dict
      PURITY: 100% pure
  [15] Src [connect]: connect
      PURITY: 100% pure
  [16] Src [disconnect]: disconnect
      PURITY: 100% pure
  [17] Src [execute]: execute
      PURITY: 100% pure
  [18] Src [fetch]: fetch
      PURITY: 100% pure
  [19] Src [_run_schema_migrations]: _run_schema_migrations
      PURITY: 100% pure
  [20] Src [_handle_resource_registered]: _handle_resource_registered
      PURITY: 100% pure
  [21] Src [_handle_transfer_requested]: _handle_transfer_requested
      PURITY: 100% pure
  [22] Src [_handle_transfer_completed]: _handle_transfer_completed
      PURITY: 100% pure
  [23] Src [_handle_transfer_failed]: _handle_transfer_failed
      PURITY: 100% pure
  [24] Src [_handle_task_created]: _handle_task_created
      PURITY: 100% pure
  [25] Src [_handle_task_assigned]: _handle_task_assigned
      PURITY: 100% pure
  [26] Src [_handle_task_started]: _handle_task_started → _update_status
      PURITY: 100% pure
  [27] Src [_handle_task_completed]: _handle_task_completed
      PURITY: 100% pure
  [28] Src [_handle_task_failed]: _handle_task_failed
      PURITY: 100% pure
  [29] Src [_handle_rag_request_failed]: _handle_rag_request_failed → _upsert_rag_quality → _error_code
      PURITY: 100% pure
  [30] Src [_handle_incident_detected]: _handle_incident_detected → _error_code
      PURITY: 100% pure
  [31] Src [_handle_incident_classified]: _handle_incident_classified → _error_code
      PURITY: 100% pure
  [32] Src [_handle_diagnostics_started]: _handle_diagnostics_started → _update_incident_status
      PURITY: 100% pure
  [33] Src [_handle_diagnostics_completed]: _handle_diagnostics_completed → _checks_payload → _raw_checks
      PURITY: 100% pure
  [34] Src [_handle_remediation_started]: _handle_remediation_started → _update_incident_status
      PURITY: 100% pure
  [35] Src [_handle_remediation_finished]: _handle_remediation_finished → _update_incident_status
      PURITY: 100% pure
  [36] Src [_handle_post_remediation_verification]: _handle_post_remediation_verification → _update_incident_status
      PURITY: 100% pure
  [37] Src [_handle_agent_registered]: _handle_agent_registered
      PURITY: 100% pure
  [38] Src [_handle_agent_heartbeat]: _handle_agent_heartbeat
      PURITY: 100% pure
  [39] Src [_handle_task_assigned_to_agent]: _handle_task_assigned_to_agent
      PURITY: 100% pure
  [40] Src [_handle_agent_marked_idle]: _handle_agent_marked_idle
      PURITY: 100% pure
  [41] Src [record_feedback]: record_feedback → _resolve_feedback_inputs → _find_turn_context
      PURITY: 100% pure
  [42] Src [list_feedback]: list_feedback → _read_jsonl_tail
      PURITY: 100% pure
  [43] Src [aggregate_learnings]: aggregate_learnings → _read_jsonl_tail
      PURITY: 100% pure
  [44] Src [new_turn_id]: new_turn_id
      PURITY: 100% pure
  [45] Src [add_event]: add_event
      PURITY: 100% pure
  [46] Src [get_artifact]: get_artifact → get_session
      PURITY: 100% pure
  [47] Src [workspace_state]: workspace_state → get_or_create → new_session
      PURITY: 100% pure
  [48] Src [propose_task_draft]: propose_task_draft → build_task_payload → get_or_create → new_session
      PURITY: 100% pure
  [49] Src [handle_chat_message]: handle_chat_message → get_or_create → new_session
      PURITY: 100% pure
  [50] Src [create_task_from_draft]: create_task_from_draft → create_task_immediate → get_or_create → new_session
      PURITY: 100% pure

LAYERS:
  services/                       CC̄=2.9    ←in:0  →out:0
  │ !! conductor                 1525L  1C   61m  CC=11     ←2
  │ !! workspace                 1438L  2C  100m  CC=7      ←6
  │ !! workspace.js              1401L  0C  183m  CC=14     ←3
  │ !! chat                      1071L  0C   82m  CC=9      ←0
  │ !! command_bus                989L  1C   44m  CC=8      ←0
  │ !! prompt_router              926L  1C   44m  CC=13     ←1
  │ !! routing_trace              739L  3C   29m  CC=16     ←1
  │ !! agent_workroom             642L  2C   33m  CC=6      ←0
  │ !! incidents                  580L  2C   40m  CC=6      ←2
  │ routing_feedback           412L  1C   18m  CC=11     ←0
  │ pipeline                   405L  1C   10m  CC=5      ←0
  │ export                     397L  0C   23m  CC=9      ←1
  │ commands                   379L  14C   23m  CC=4      ←0
  │ main                       340L  0C   15m  CC=4      ←0
  │ incidents                  331L  0C   19m  CC=6      ←1
  │ main.jsx                   290L  0C   22m  CC=6      ←0
  │ store                      283L  1C   21m  CC=5      ←0
  │ rag_pipeline               270L  1C   10m  CC=5      ←0
  │ workroom.js                268L  0C   26m  CC=12     ←0
  │ incidents                  254L  10C    0m  CC=0.0    ←0
  │ access_matrix              248L  0C   19m  CC=6      ←1
  │ task                       244L  1C   20m  CC=4      ←0
  │ rag_diagnostics            222L  1C   12m  CC=6      ←0
  │ local_orient               207L  1C    6m  CC=13     ←2
  │ app.js                     206L  0C   22m  CC=8      ←0
  │ queries                    204L  4C    9m  CC=6      ←0
  │ evaluation                 202L  1C   10m  CC=6      ←0
  │ main                       195L  0C    5m  CC=6      ←0
  │ nlp2dsl_bridge             194L  0C   15m  CC=7      ←0
  │ task_routes                190L  0C   19m  CC=6      ←0
  │ eventstore_esdb            186L  1C    8m  CC=4      ←0
  │ eventstore                 182L  2C    9m  CC=6      ←3
  │ routing_policy             182L  2C   12m  CC=10     ←3
  │ chat_routes                181L  0C   13m  CC=5      ←0
  │ resource_areas             171L  0C    5m  CC=5      ←1
  │ routing_schemas            171L  4C    9m  CC=4      ←2
  │ workflows                  167L  7C    0m  CC=0.0    ←0
  │ access.js                  157L  0C   21m  CC=11     ←2
  │ task_board                 153L  0C    7m  CC=3      ←1
  │ approval_gate              146L  1C    6m  CC=5      ←1
  │ workflow                   144L  1C    9m  CC=3      ←0
  │ ticket_schemas             143L  4C    4m  CC=5      ←1
  │ rag                        142L  2C    6m  CC=3      ←0
  │ access                     136L  3C    8m  CC=4      ←0
  │ tasks                      133L  5C    0m  CC=0.0    ←0
  │ resources                  132L  5C    0m  CC=0.0    ←0
  │ policy_engine              131L  2C   10m  CC=6      ←0
  │ resource_registry          130L  0C    5m  CC=3      ←1
  │ openrouter                 128L  1C    9m  CC=6      ←1
  │ approvals                  126L  5C    0m  CC=0.0    ←0
  │ plugins                    118L  5C    0m  CC=0.0    ←0
  │ indexer                    115L  1C    8m  CC=5      ←0
  │ observability              112L  1C    5m  CC=3      ←0
  │ nlp2cmd_plugin             110L  1C    5m  CC=9      ←0
  │ routing_policy.yaml        106L  0C    0m  CC=0.0    ←0
  │ main                       104L  0C    5m  CC=1      ←0
  │ evolution                  104L  2C    5m  CC=4      ←0
  │ retriever                  103L  1C    8m  CC=5      ←0
  │ __init__                   103L  0C    0m  CC=0.0    ←0
  │ planfile_bridge            102L  0C    6m  CC=9      ←1
  │ resource                   100L  1C    6m  CC=3      ←0
  │ agent_fleet                 97L  0C    5m  CC=3      ←1
  │ plugin                      97L  2C    7m  CC=2      ←0
  │ approval                    97L  2C    6m  CC=2      ←0
  │ registry                    95L  0C    7m  CC=4      ←3
  │ agents                      95L  4C    0m  CC=0.0    ←0
  │ postgres                    92L  1C    7m  CC=5      ←0
  │ catalog                     92L  1C    6m  CC=4      ←0
  │ models                      91L  12C    0m  CC=0.0    ←0
  │ router_routes               87L  0C    6m  CC=9      ←0
  │ __init__                    85L  11C    2m  CC=4      ←0
  │ agent                       83L  1C    7m  CC=2      ←0
  │ base                        81L  1C    7m  CC=3      ←0
  │ workspace_routes            80L  0C    5m  CC=2      ←0
  │ approval_requests           79L  0C    1m  CC=6      ←1
  │ transport                   77L  1C    7m  CC=4      ←0
  │ experiments                 76L  1C    4m  CC=2      ←0
  │ localfs                     71L  1C    5m  CC=4      ←0
  │ operational_feed            70L  0C    3m  CC=6      ←1
  │ eventstore_factory          66L  0C    4m  CC=5      ←1
  │ task_routing                66L  0C    4m  CC=5      ←1
  │ protocol                    63L  2C    3m  CC=4      ←0
  │ context                     59L  0C    6m  CC=5      ←7
  │ logging                     59L  0C    2m  CC=3      ←4
  │ eventstore_dual             57L  1C    5m  CC=2      ←0
  │ db                          56L  1C    6m  CC=4      ←0
  │ workroom_routes             54L  0C    5m  CC=2      ←0
  │ config                      54L  1C    1m  CC=1      ←0
  │ feedback_routes             51L  0C    4m  CC=2      ←0
  │ nats_bus                    49L  1C    5m  CC=4      ←0
  │ http_adapter                49L  1C    4m  CC=3      ←0
  │ workflow_versions           47L  0C    1m  CC=5      ←1
  │ dispatcher                  47L  0C    4m  CC=4      ←2
  │ access_routes               46L  0C    6m  CC=1      ←0
  │ tickets                     45L  0C    4m  CC=4      ←1
  │ uri                         43L  1C    2m  CC=6      ←3
  │ plugin_catalog              42L  0C    1m  CC=5      ←1
  │ catalog                     41L  0C    7m  CC=1      ←0
  │ base                        33L  2C    3m  CC=1      ←0
  │ chunking                    30L  0C    2m  CC=4      ←1
  │ Dockerfile                  27L  0C    0m  CC=0.0    ←0
  │ api_routes                  25L  0C    0m  CC=0.0    ←0
  │ nlp2dsl_plugin              22L  1C    2m  CC=1      ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  21L  0C    0m  CC=0.0    ←0
  │ middleware                  19L  1C    1m  CC=3      ←0
  │ __init__                    19L  0C    0m  CC=0.0    ←0
  │ package.json                18L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    1m  CC=2      ←1
  │ config                      16L  0C    0m  CC=0.0    ←0
  │ requirements.txt            16L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ agents_routes               13L  0C    1m  CC=1      ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   8L  0C    0m  CC=0.0    ←0
  │ requirements.txt             7L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ requirements.txt             5L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ requirements-esdb.txt        2L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  agents/                         CC̄=2.3    ←in:0  →out:0
  │ executor                    48L  1C    2m  CC=4      ←1
  │ nats_consumer               47L  1C    3m  CC=4      ←0
  │ main                        26L  0C    1m  CC=2      ←0
  │ Dockerfile                  14L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:0  →out:0
  │ e2e-chat-routing.sh         79L  0C    0m  CC=0.0    ←0
  │ run-propact-pact.sh         71L  0C    1m  CC=0.0    ←0
  │ test-quality.sh             62L  0C    0m  CC=0.0    ←0
  │ wait-for-web.sh             22L  0C    0m  CC=0.0    ←0
  │ test.sh                     13L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  509L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md               366L  0C    0m  CC=0.0    ←0
  │ TODO.md                    241L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml         229L  0C    0m  CC=0.0    ←0
  │ README.md                  213L  0C    0m  CC=0.0    ←0
  │ Makefile                   137L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ intract.yaml                74L  0C    0m  CC=0.0    ←0
  │ project.sh                  52L  0C    0m  CC=0.0    ←0
  │ requirements-dev.txt         7L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   7L  0C    0m  CC=0.0    ←0
  │ requirements-quality.txt     4L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ !! README.md                 1181L  0C    0m  CC=0.0    ←0
  │ e2e-chat-routing.md        140L  0C    0m  CC=0.0    ←0
  │ prompt-router.md           136L  0C    0m  CC=0.0    ←0
  │ multi-agent-workroom.md     88L  0C    0m  CC=0.0    ←0
  │ roadmap-90d.md              83L  0C    0m  CC=0.0    ←0
  │ agent-orchestration.md      69L  0C    0m  CC=0.0    ←0
  │ architecture-service-integrations.md    66L  0C    0m  CC=0.0    ←0
  │ routing-feedback-loop.md    66L  0C    0m  CC=0.0    ←0
  │ quality-intract-propact.md    58L  0C    0m  CC=0.0    ←0
  │ ticket-queues-and-planfile.md    55L  0C    0m  CC=0.0    ←0
  │ observability.md            50L  0C    0m  CC=0.0    ←0
  │ architecture.md             46L  0C    0m  CC=0.0    ←0
  │ workspace-conductor.md      43L  0C    0m  CC=0.0    ←0
  │ workspace-simple.md         40L  0C    0m  CC=0.0    ←0
  │ events.md                   38L  0C    0m  CC=0.0    ←0
  │ workspace-ui.md             30L  0C    0m  CC=0.0    ←0
  │ domain.md                   24L  0C    0m  CC=0.0    ←0
  │
  TODO/                           CC̄=0.0    ←in:0  →out:0
  │ 4.md                       394L  0C    0m  CC=0.0    ←0
  │ 3.md                       291L  0C    0m  CC=0.0    ←0
  │ 2.md                       187L  0C    0m  CC=0.0    ←0
  │ 1.md                       142L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    40L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    34L  0C    0m  CC=0.0    ←0
  │
  catalog/                        CC̄=0.0    ←in:0  →out:0
  │ policies.json               49L  0C    0m  CC=0.0    ←0
  │ capabilities.json           48L  0C    0m  CC=0.0    ←0
  │ task.json                   46L  0C    0m  CC=0.0    ←0
  │ evolution.json              45L  0C    0m  CC=0.0    ←0
  │ workflow.json               42L  0C    0m  CC=0.0    ←0
  │ services.json               39L  0C    0m  CC=0.0    ←0
  │ domains.json                30L  0C    0m  CC=0.0    ←0
  │ access.json                 30L  0C    0m  CC=0.0    ←0
  │ index.json                  19L  0C    0m  CC=0.0    ←0
  │ rag.json                    15L  0C    0m  CC=0.0    ←0
  │
  integrations/                   CC̄=0.0    ←in:0  →out:0
  │ mullm_registry              32L  0C    0m  CC=0.0    ←0
  │ schemas.json                30L  0C    0m  CC=0.0    ←0
  │ agent_manifest.yaml         23L  0C    0m  CC=0.0    ←0
  │ agent_manifest.yaml         17L  0C    0m  CC=0.0    ←0
  │ README.md                   12L  0C    0m  CC=0.0    ←0
  │ patch_startup                7L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     services/web/app/__init__.py              0L

COUPLING:
                         services.orchestrator           services.web     services.projector
  services.orchestrator                     ──                      5                      1
           services.web                     ←5                     ──                         hub
     services.projector                     ←1                                            ──
  CYCLES: none
  HUB: services.web/ (fan-in=5)

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 35 groups | 123f 19808L | 2026-06-05

SUMMARY:
  files_scanned: 123
  total_lines:   19808
  dup_groups:    35
  dup_fragments: 90
  saved_lines:   674
  scan_ms:       2717

HOTSPOTS[7] (files with most duplication):
  services/projector/app/main.py  dup=217L  groups=2  frags=12  (1.1%)
  services/orchestrator/app/observability/export.py  dup=161L  groups=4  frags=8  (0.8%)
  services/orchestrator/app/api/commands.py  dup=105L  groups=1  frags=7  (0.5%)
  services/web/app/conductor.py  dup=64L  groups=2  frags=5  (0.3%)
  services/orchestrator/app/api/queries.py  dup=60L  groups=1  frags=3  (0.3%)
  services/web/app/nlp2dsl_bridge.py  dup=36L  groups=1  frags=2  (0.2%)
  services/web/app/agent_workroom.py  dup=36L  groups=2  frags=4  (0.2%)

DUPLICATES[35] (ranked by impact):
  [fc5b148fddf5c532] !! STRU  task_board  L=26 N=5 saved=104 sim=1.00
      services/projector/app/main.py:94-119  (task_board)
      services/projector/app/main.py:123-148  (agent_fleet)
      services/projector/app/main.py:152-177  (approval_requests)
      services/projector/app/main.py:181-206  (plugin_catalog)
      services/projector/app/main.py:226-251  (incident_feed)
  [473cb3f4b32851a9] ! STRU  create_task  L=15 N=7 saved=90 sim=1.00
      services/orchestrator/app/api/commands.py:139-153  (create_task)
      services/orchestrator/app/api/commands.py:157-171  (assign_task)
      services/orchestrator/app/api/commands.py:175-189  (start_task)
      services/orchestrator/app/api/commands.py:193-207  (complete_task)
      services/orchestrator/app/api/commands.py:211-225  (fail_task)
      services/orchestrator/app/api/commands.py:229-243  (register_agent)
      services/orchestrator/app/api/commands.py:247-261  (start_workflow)
  [dbf84d387ab88bdb] ! STRU  operational_feed  L=14 N=7 saved=84 sim=1.00
      services/projector/app/main.py:77-90  (operational_feed)
      services/projector/app/main.py:210-222  (rag_documents)
      services/projector/app/main.py:255-266  (service_health)
      services/projector/app/main.py:270-281  (remediation_history)
      services/projector/app/main.py:285-296  (rag_quality_board)
      services/projector/app/main.py:300-311  (resource_registry)
      services/projector/app/main.py:315-326  (workflow_versions)
  [8182d5c2ea80ccd7] ! STRU  _fetch_incidents  L=31 N=3 saved=62 sim=1.00
      services/orchestrator/app/observability/export.py:269-299  (_fetch_incidents)
      services/orchestrator/app/observability/export.py:321-349  (_fetch_incident_feed)
      services/orchestrator/app/observability/export.py:371-397  (_fetch_rag_snapshots)
  [c88ebf49370e38e4] ! STRU  get_task  L=20 N=3 saved=40 sim=1.00
      services/orchestrator/app/api/queries.py:29-48  (get_task)
      services/orchestrator/app/api/queries.py:52-71  (get_agent)
      services/orchestrator/app/api/queries.py:75-94  (get_workflow)
  [e6484eb2e73fb4fc] ! STRU  backend_candidates  L=18 N=3 saved=36 sim=1.00
      services/web/app/agent_plugins/nlp2cmd_plugin.py:21-38  (backend_candidates)
      services/web/app/nlp2dsl_bridge.py:19-36  (backend_candidates)
      services/web/app/nlp2dsl_bridge.py:73-90  (nlp_service_candidates)
  [dd30f40d83785484] ! STRU  _safe_fetch_incidents  L=17 N=3 saved=34 sim=1.00
      services/orchestrator/app/observability/export.py:250-266  (_safe_fetch_incidents)
      services/orchestrator/app/observability/export.py:302-318  (_safe_fetch_incident_feed)
      services/orchestrator/app/observability/export.py:352-368  (_safe_fetch_rag_snapshots)
  [b487de8e81871639]   STRU  _nlp2dsl_continue_decision  L=10 N=3 saved=20 sim=1.00
      services/web/app/conductor.py:774-783  (_nlp2dsl_continue_decision)
      services/web/app/conductor.py:786-795  (_mullm_continue_clarify_decision)
      services/web/app/conductor.py:871-880  (_rag_probe_decision)
  [cbbb67a75ff65ca7]   STRU  transfer_resource  L=9 N=3 saved=18 sim=1.00
      services/orchestrator/app/api/access.py:49-57  (transfer_resource)
      services/orchestrator/app/api/evolution.py:84-92  (propose_change)
      services/orchestrator/app/api/evolution.py:96-104  (shadow_workflow)
  [707ff8ed8b0c1bdf]   STRU  _append_nfo  L=17 N=2 saved=17 sim=1.00
      services/orchestrator/app/observability/export.py:88-104  (_append_nfo)
      services/web/app/workspace.py:955-974  (_append_nfo_section)
  [3fe0219ba048af7c]   STRU  _execute_file_list_route  L=17 N=2 saved=17 sim=1.00
      services/web/app/conductor.py:140-156  (_execute_file_list_route)
      services/web/app/conductor.py:418-434  (_execute_rag_route)
  [aa890be89093e6d5]   STRU  data  L=6 N=3 saved=12 sim=1.00
      services/orchestrator/app/domain/events/plugins.py:48-53  (data)
      services/orchestrator/app/domain/events/plugins.py:69-74  (data)
      services/orchestrator/app/domain/events/plugins.py:90-95  (data)
  [4fb7f74cf43032f1]   STRU  list_resources  L=11 N=2 saved=11 sim=1.00
      services/orchestrator/app/api/access.py:77-87  (list_resources)
      services/orchestrator/app/api/evolution.py:75-80  (capability_registry)
  [9de574130a2bfbd2]   STRU  _run_analyze_workroom_step  L=11 N=2 saved=11 sim=1.00
      services/web/app/agent_workroom.py:353-363  (_run_analyze_workroom_step)
      services/web/app/agent_workroom.py:400-410  (_run_summarize_workroom_step)
  [9c4fc13f5f917a64]   STRU  project_agent_fleet  L=10 N=2 saved=10 sim=1.00
      services/projector/app/projections/agent_fleet.py:7-16  (project_agent_fleet)
      services/projector/app/projections/resource_registry.py:7-16  (project_resource_registry)
  [32839d90ea67fb47]   EXAC  _projector  L=7 N=2 saved=7 sim=1.00
      services/web/app/chat.py:45-51  (_projector)
      services/web/app/workspace.py:28-34  (_projector)
  [46f02a3f0dd7583d]   STRU  agent_may_access_resource  L=7 N=2 saved=7 sim=1.00
      services/web/app/access_matrix.py:218-224  (agent_may_access_resource)
      services/web/app/access_matrix.py:227-233  (human_may_use_agent)
  [454ed159e8c7ebbf]   STRU  _run_analyze_step  L=7 N=2 saved=7 sim=1.00
      services/web/app/agent_workroom.py:422-428  (_run_analyze_step)
      services/web/app/agent_workroom.py:603-609  (_run_summarize_step)
  [c438d6044e10a938]   STRU  parse_nlp2cmd_response  L=7 N=2 saved=7 sim=1.00
      services/web/app/routing_schemas.py:120-126  (parse_nlp2cmd_response)
      services/web/app/routing_schemas.py:129-135  (parse_llm_classifier)
  [1fb3398c7c69da23]   EXAC  data  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/domain/events/incidents.py:227-232  (data)
      services/orchestrator/app/domain/events/incidents.py:249-254  (data)
  [bcc6214a4a9b2b8c]   EXAC  clamp_log_export_limit  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/observability/export.py:37-42  (clamp_log_export_limit)
      services/web/app/workspace.py:695-700  (clamp_log_export_limit)
  [9a129a96b21d1689]   EXAC  _checks_list_payload  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/observability/incidents.py:508-513  (_checks_list_payload)
      services/projector/app/projections/incidents.py:288-293  (_checks_list_payload)
  [8d49c56953675bd9]   STRU  data  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/domain/events/workflows.py:72-77  (data)
      services/orchestrator/app/domain/events/workflows.py:139-144  (data)
  [89dfe849b85b91ed]   STRU  _empty_agent_resource  L=6 N=2 saved=6 sim=1.00
      services/web/app/access_matrix.py:61-66  (_empty_agent_resource)
      services/web/app/access_matrix.py:69-72  (_empty_human_agent)
  [bd20ef24149cc1ac]   STRU  _incident_trace_part  L=6 N=2 saved=6 sim=1.00
      services/web/app/chat.py:609-614  (_incident_trace_part)
      services/web/app/chat.py:625-630  (_incident_fallback_part)
  [0344e427af6677d5]   STRU  probe_uri  L=5 N=2 saved=5 sim=1.00
      services/orchestrator/app/api/access.py:61-65  (probe_uri)
      services/orchestrator/app/api/access.py:69-73  (fetch_uri)
  [f3827ff1e1ab62f3]   STRU  connect  L=5 N=2 saved=5 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:50-54  (connect)
      services/projector/app/db.py:22-26  (connect)
  [15724f5cdeaa84de]   STRU  execute  L=5 N=2 saved=5 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:61-65  (execute)
      services/projector/app/db.py:33-37  (execute)
  [87cc9c48b4d7af20]   STRU  fetch  L=5 N=2 saved=5 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:67-71  (fetch)
      services/projector/app/db.py:39-43  (fetch)
  [d6dcf24fe1d352d6]   STRU  _nlp2cmd_min_confidence  L=5 N=2 saved=5 sim=1.00
      services/web/app/prompt_router.py:541-545  (_nlp2cmd_min_confidence)
      services/web/app/prompt_router.py:556-560  (_local_min_confidence)
  [529be22a4705ecaf]   STRU  feedback_dir  L=5 N=2 saved=5 sim=1.00
      services/web/app/routing_feedback.py:62-66  (feedback_dir)
      services/web/app/routing_policy.py:93-97  (_policy_path)
  [9cf59ab30a3c0ba7]   EXAC  disconnect  L=4 N=2 saved=4 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:56-59  (disconnect)
      services/projector/app/db.py:28-31  (disconnect)
  [734df5e9c9a59d8b]   STRU  _feedback_path  L=4 N=2 saved=4 sim=1.00
      services/web/app/routing_feedback.py:69-72  (_feedback_path)
      services/web/app/routing_feedback.py:75-78  (_improvements_path)
  [a45a0af197a0ec34]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:46-48  (__init__)
      services/projector/app/db.py:18-20  (__init__)
  [c89d26a3db18ab2e]   STRU  routing_schemas_get  L=3 N=2 saved=3 sim=1.00
      services/web/app/api/router_routes.py:34-36  (routing_schemas_get)
      services/web/app/api/router_routes.py:40-42  (ticket_schemas_get)

REFACTOR[35] (ranked by priority):
  [1] ○ extract_function   → services/projector/app/utils/task_board.py
      WHY: 5 occurrences of 26-line block across 1 files — saves 104 lines
      FILES: services/projector/app/main.py
  [2] ○ extract_function   → services/orchestrator/app/api/utils/create_task.py
      WHY: 7 occurrences of 15-line block across 1 files — saves 90 lines
      FILES: services/orchestrator/app/api/commands.py
  [3] ○ extract_function   → services/projector/app/utils/operational_feed.py
      WHY: 7 occurrences of 14-line block across 1 files — saves 84 lines
      FILES: services/projector/app/main.py
  [4] ○ extract_function   → services/orchestrator/app/observability/utils/_fetch_incidents.py
      WHY: 3 occurrences of 31-line block across 1 files — saves 62 lines
      FILES: services/orchestrator/app/observability/export.py
  [5] ○ extract_function   → services/orchestrator/app/api/utils/get_task.py
      WHY: 3 occurrences of 20-line block across 1 files — saves 40 lines
      FILES: services/orchestrator/app/api/queries.py
  [6] ○ extract_function   → services/web/app/utils/backend_candidates.py
      WHY: 3 occurrences of 18-line block across 2 files — saves 36 lines
      FILES: services/web/app/agent_plugins/nlp2cmd_plugin.py, services/web/app/nlp2dsl_bridge.py
  [7] ○ extract_function   → services/orchestrator/app/observability/utils/_safe_fetch_incidents.py
      WHY: 3 occurrences of 17-line block across 1 files — saves 34 lines
      FILES: services/orchestrator/app/observability/export.py
  [8] ○ extract_function   → services/web/app/utils/_nlp2dsl_continue_decision.py
      WHY: 3 occurrences of 10-line block across 1 files — saves 20 lines
      FILES: services/web/app/conductor.py
  [9] ○ extract_function   → services/orchestrator/app/api/utils/transfer_resource.py
      WHY: 3 occurrences of 9-line block across 2 files — saves 18 lines
      FILES: services/orchestrator/app/api/access.py, services/orchestrator/app/api/evolution.py
  [10] ○ extract_function   → services/utils/_append_nfo.py
      WHY: 2 occurrences of 17-line block across 2 files — saves 17 lines
      FILES: services/orchestrator/app/observability/export.py, services/web/app/workspace.py
  [11] ○ extract_function   → services/web/app/utils/_execute_file_list_route.py
      WHY: 2 occurrences of 17-line block across 1 files — saves 17 lines
      FILES: services/web/app/conductor.py
  [12] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 3 occurrences of 6-line block across 1 files — saves 12 lines
      FILES: services/orchestrator/app/domain/events/plugins.py
  [13] ○ extract_function   → services/orchestrator/app/api/utils/list_resources.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: services/orchestrator/app/api/access.py, services/orchestrator/app/api/evolution.py
  [14] ○ extract_function   → services/web/app/utils/_run_analyze_workroom_step.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: services/web/app/agent_workroom.py
  [15] ○ extract_function   → services/projector/app/projections/utils/project_agent_fleet.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: services/projector/app/projections/agent_fleet.py, services/projector/app/projections/resource_registry.py
  [16] ○ extract_function   → services/web/app/utils/_projector.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: services/web/app/chat.py, services/web/app/workspace.py
  [17] ○ extract_function   → services/web/app/utils/agent_may_access_resource.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: services/web/app/access_matrix.py
  [18] ○ extract_function   → services/web/app/utils/_run_analyze_step.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: services/web/app/agent_workroom.py
  [19] ○ extract_function   → services/web/app/utils/parse_nlp2cmd_response.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: services/web/app/routing_schemas.py
  [20] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/orchestrator/app/domain/events/incidents.py
  [21] ○ extract_function   → services/utils/clamp_log_export_limit.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: services/orchestrator/app/observability/export.py, services/web/app/workspace.py
  [22] ○ extract_function   → services/utils/_checks_list_payload.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: services/orchestrator/app/observability/incidents.py, services/projector/app/projections/incidents.py
  [23] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/orchestrator/app/domain/events/workflows.py
  [24] ○ extract_function   → services/web/app/utils/_empty_agent_resource.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/web/app/access_matrix.py
  [25] ○ extract_function   → services/web/app/utils/_incident_trace_part.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/web/app/chat.py
  [26] ○ extract_function   → services/orchestrator/app/api/utils/probe_uri.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: services/orchestrator/app/api/access.py
  [27] ○ extract_function   → services/utils/connect.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [28] ○ extract_function   → services/utils/execute.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [29] ○ extract_function   → services/utils/fetch.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [30] ○ extract_function   → services/web/app/utils/_nlp2cmd_min_confidence.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: services/web/app/prompt_router.py
  [31] ○ extract_function   → services/web/app/utils/feedback_dir.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/web/app/routing_feedback.py, services/web/app/routing_policy.py
  [32] ○ extract_function   → services/utils/disconnect.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [33] ○ extract_function   → services/web/app/utils/_feedback_path.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: services/web/app/routing_feedback.py
  [34] ○ extract_function   → services/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [35] ○ extract_function   → services/web/app/api/utils/routing_schemas_get.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: services/web/app/api/router_routes.py

QUICK_WINS[25] (low risk, high savings — do first):
  [1] extract_function   saved=104L  → services/projector/app/utils/task_board.py
      FILES: main.py
  [2] extract_function   saved=90L  → services/orchestrator/app/api/utils/create_task.py
      FILES: commands.py
  [3] extract_function   saved=84L  → services/projector/app/utils/operational_feed.py
      FILES: main.py
  [4] extract_function   saved=62L  → services/orchestrator/app/observability/utils/_fetch_incidents.py
      FILES: export.py
  [5] extract_function   saved=40L  → services/orchestrator/app/api/utils/get_task.py
      FILES: queries.py
  [6] extract_function   saved=36L  → services/web/app/utils/backend_candidates.py
      FILES: nlp2cmd_plugin.py, nlp2dsl_bridge.py
  [7] extract_function   saved=34L  → services/orchestrator/app/observability/utils/_safe_fetch_incidents.py
      FILES: export.py
  [8] extract_function   saved=20L  → services/web/app/utils/_nlp2dsl_continue_decision.py
      FILES: conductor.py
  [9] extract_function   saved=18L  → services/orchestrator/app/api/utils/transfer_resource.py
      FILES: access.py, evolution.py
  [10] extract_function   saved=17L  → services/utils/_append_nfo.py
      FILES: export.py, workspace.py

EFFORT_ESTIMATE (total ≈ 23.5h):
  hard   task_board                          saved=104L  ~208min
  hard   create_task                         saved=90L  ~180min
  hard   operational_feed                    saved=84L  ~168min
  hard   _fetch_incidents                    saved=62L  ~186min
  medium get_task                            saved=40L  ~80min
  medium backend_candidates                  saved=36L  ~72min
  medium _safe_fetch_incidents               saved=34L  ~68min
  medium _nlp2dsl_continue_decision          saved=20L  ~40min
  medium transfer_resource                   saved=18L  ~36min
  medium _append_nfo                         saved=17L  ~34min
  ... +25 more (~338min)

METRICS-TARGET:
  dup_groups:  35 → 0
  saved_lines: 674 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1304 func | 97f | 2026-06-05
# generated in 0.00s

NEXT[4] (ranked by impact):
  [1] !! SPLIT           services/web/app/static/workspace.js
      WHY: 1401L, 0 classes, max CC=14
      EFFORT: ~4h  IMPACT: 19614

  [2] !! SPLIT           services/web/app/conductor.py
      WHY: 1525L, 1 classes, max CC=11
      EFFORT: ~4h  IMPACT: 16775

  [3] !! SPLIT           services/web/app/workspace.py
      WHY: 1438L, 2 classes, max CC=7
      EFFORT: ~4h  IMPACT: 10066

  [4] !  SPLIT-FUNC      explain_pipeline  CC=16  fan=15
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 240


RISKS[3]:
  ⚠ Splitting services/web/app/conductor.py may break 61 import paths
  ⚠ Splitting services/web/app/workspace.py may break 100 import paths
  ⚠ Splitting services/web/app/static/workspace.js may break 183 import paths

METRICS-TARGET:
  CC̄:          2.9 → ≤2.0
  max-CC:      16 → ≤8
  god-modules: 12 → 0
  high-CC(≥15): 1 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=2.9 → now CC̄=2.9
```

## Intent

Mullm - Multi-Agent Learning and Labor Management
