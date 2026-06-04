# Mullm - Multi-Agent Learning and Labor Management

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `mullm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements-dev.txt, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(5 analysis files)

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

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
}
```

## Call Graph

*255 nodes · 313 edges · 52 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_format_export_text` *(in services.web.app.workspace)* | 47 ⚠ | 1 | 97 | **98** |
| `format_logs_text` *(in services.orchestrator.app.observability.export)* | 29 ⚠ | 1 | 66 | **67** |
| `project_incidents` *(in services.projector.app.projections.incidents)* | 23 ⚠ | 1 | 51 | **52** |
| `run_workroom` *(in services.web.app.agent_workroom)* | 22 ⚠ | 0 | 45 | **45** |
| `handle_chat_message` *(in services.web.app.workspace)* | 21 ⚠ | 0 | 40 | **40** |
| `ask` *(in services.orchestrator.app.observability.rag_pipeline.RagPipeline)* | 10 ⚠ | 0 | 36 | **36** |
| `format_file_list_reply` *(in services.web.app.chat)* | 22 ⚠ | 1 | 35 | **36** |
| `_nlp2dsl_turn` *(in services.web.app.conductor)* | 23 ⚠ | 1 | 35 | **36** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/mullm
# generated in 0.14s
# nodes: 255 | edges: 313 | modules: 52
# CC̄=3.8

HUBS[20]:
  services.web.app.workspace._format_export_text
    CC=47  in:1  out:97  total:98
  services.orchestrator.app.observability.export.format_logs_text
    CC=29  in:1  out:66  total:67
  services.projector.app.projections.incidents.project_incidents
    CC=23  in:1  out:51  total:52
  services.web.app.agent_workroom.run_workroom
    CC=22  in:0  out:45  total:45
  services.web.app.workspace.handle_chat_message
    CC=21  in:0  out:40  total:40
  services.orchestrator.app.observability.rag_pipeline.RagPipeline.ask
    CC=10  in:0  out:36  total:36
  services.web.app.chat.format_file_list_reply
    CC=22  in:1  out:35  total:36
  services.web.app.conductor._nlp2dsl_turn
    CC=23  in:1  out:35  total:36
  services.web.app.chat.handle_message
    CC=33  in:0  out:35  total:35
  services.orchestrator.app.observability.incidents._event_payload
    CC=19  in:1  out:28  total:29
  services.web.app.workspace.export_debug_logs
    CC=15  in:0  out:26  total:26
  services.web.app.static.workspace.api
    CC=6  in:20  out:4  total:24
  services.orchestrator.app.observability.incidents.IncidentRecorder.record
    CC=16  in:0  out:23  total:23
  services.orchestrator.app.api.commands._dispatch
    CC=4  in:14  out:9  total:23
  services.orchestrator.app.observability.rag_diagnostics.RagDiagnostics.run
    CC=12  in:0  out:23  total:23
  services.orchestrator.app.rag.indexer.RagIndexer.ingest_resource
    CC=13  in:0  out:22  total:22
  services.orchestrator.app.api.rag.search
    CC=3  in:0  out:22  total:22
  services.web.app.static.workspace.refreshWorkspace
    CC=7  in:8  out:13  total:21
  services.orchestrator.app.application.command_bus.CommandBus._create_task
    CC=6  in:0  out:20  total:20
  services.orchestrator.app.api.access.upload_resource
    CC=4  in:0  out:19  total:19

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
  services.projector.app.projections.incidents  [7 funcs]
    _checks_payload  CC=10  out:11
    _diagnostics_ok  CC=6  out:4
    _error_code  CC=4  out:3
    _root_cause  CC=4  out:5
    _upsert_rag_quality  CC=1  out:4
    _upsert_service_health  CC=1  out:2
    project_incidents  CC=23  out:51
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
  services.web.app.chat  [10 funcs]
    _append  CC=1  out:2
    _dedupe_rows_by_uri  CC=8  out:10
    _format_history  CC=3  out:3
    _orch  CC=2  out:2
    create_task  CC=7  out:8
    fetch_file_inventory  CC=7  out:15
    format_file_list_reply  CC=22  out:35
    get_history  CC=1  out:2
    handle_message  CC=33  out:35
    is_file_list_intent  CC=7  out:5
  services.web.app.conductor  [6 funcs]
    _extract_shell  CC=3  out:5
    _fallback_turn  CC=4  out:7
    _local_clarify  CC=3  out:3
    _mullm_file_list_turn  CC=1  out:5
    _nlp2dsl_turn  CC=23  out:35
    handle_turn  CC=7  out:8
  services.web.app.nlp2dsl_bridge  [6 funcs]
    _post_json  CC=4  out:6
    backend_candidates  CC=4  out:6
    backend_url  CC=1  out:1
    chat_message  CC=1  out:1
    chat_start  CC=1  out:1
    health  CC=4  out:3
  services.web.app.resource_areas  [2 funcs]
    list_areas  CC=2  out:1
    list_groups  CC=1  out:0
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
  services.web.app.static.workspace  [50 funcs]
    api  CC=6  out:4
    appendMsg  CC=1  out:1
    appendMsgTo  CC=6  out:2
    archiveTicket  CC=2  out:5
    collectClarifyValues  CC=4  out:4
    color  CC=1  out:1
    confirmTicket  CC=1  out:6
    copyChatToClipboard  CC=10  out:11
    copyLogsToClipboard  CC=2  out:5
    copyText  CC=2  out:7
  services.web.app.tickets  [4 funcs]
    enrich_task  CC=4  out:6
    status_meta  CC=3  out:2
    ticket_uri  CC=1  out:0
    ticket_web_path  CC=1  out:0
  services.web.app.workspace  [17 funcs]
    _extract_shell_command  CC=4  out:8
    _extract_ticket  CC=2  out:2
    _format_export_text  CC=47  out:97
    archive_task  CC=2  out:3
    attach_context  CC=12  out:7
    build_task_payload  CC=4  out:7
    create_and_run  CC=5  out:9
    create_task_from_draft  CC=4  out:5
    create_task_immediate  CC=3  out:7
    export_debug_logs  CC=15  out:26
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
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._checks_payload
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._diagnostics_ok
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._upsert_rag_quality
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._upsert_service_health
  services.projector.app.projections.incidents._upsert_rag_quality → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._root_cause → services.projector.app.projections.incidents._error_code
  services.web.app.workspace.get_or_create → services.web.app.workspace.new_session
  services.web.app.workspace.workspace_state → services.web.app.workspace.get_or_create
  services.web.app.workspace.attach_context → services.web.app.workspace.get_or_create
  services.web.app.workspace.build_task_payload → services.web.app.workspace.get_or_create
  services.web.app.workspace.build_task_payload → services.web.app.workspace._extract_shell_command
  services.web.app.workspace.build_task_payload → services.web.app.workspace._extract_ticket
  services.web.app.workspace.propose_task_draft → services.web.app.workspace.build_task_payload
  services.web.app.workspace.create_task_immediate → services.web.app.workspace.get_or_create
  services.web.app.workspace.create_task_immediate → services.web.app.workspace.link_ticket
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.get_or_create
  services.web.app.workspace.handle_chat_message → services.web.app.workspace._extract_ticket
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.attach_context
  services.web.app.workspace.handle_chat_message → services.web.app.workspace._extract_shell_command
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.build_task_payload
  services.web.app.workspace.create_task_from_draft → services.web.app.workspace.create_task_immediate
  services.web.app.workspace.create_task_from_draft → services.web.app.workspace.get_or_create
  services.web.app.workspace.create_and_run → services.web.app.workspace.create_task_immediate
  services.web.app.workspace.create_and_run → services.web.app.workspace.get_or_create
  services.web.app.workspace.export_debug_logs → services.web.app.workspace.get_or_create
  services.web.app.workspace.export_debug_logs → services.web.app.workspace._format_export_text
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
# generated in 0.14s
# nodes: 255 | edges: 313 | modules: 52
# CC̄=3.8

HUBS[20]:
  services.web.app.workspace._format_export_text
    CC=47  in:1  out:97  total:98
  services.orchestrator.app.observability.export.format_logs_text
    CC=29  in:1  out:66  total:67
  services.projector.app.projections.incidents.project_incidents
    CC=23  in:1  out:51  total:52
  services.web.app.agent_workroom.run_workroom
    CC=22  in:0  out:45  total:45
  services.web.app.workspace.handle_chat_message
    CC=21  in:0  out:40  total:40
  services.orchestrator.app.observability.rag_pipeline.RagPipeline.ask
    CC=10  in:0  out:36  total:36
  services.web.app.chat.format_file_list_reply
    CC=22  in:1  out:35  total:36
  services.web.app.conductor._nlp2dsl_turn
    CC=23  in:1  out:35  total:36
  services.web.app.chat.handle_message
    CC=33  in:0  out:35  total:35
  services.orchestrator.app.observability.incidents._event_payload
    CC=19  in:1  out:28  total:29
  services.web.app.workspace.export_debug_logs
    CC=15  in:0  out:26  total:26
  services.web.app.static.workspace.api
    CC=6  in:20  out:4  total:24
  services.orchestrator.app.observability.incidents.IncidentRecorder.record
    CC=16  in:0  out:23  total:23
  services.orchestrator.app.api.commands._dispatch
    CC=4  in:14  out:9  total:23
  services.orchestrator.app.observability.rag_diagnostics.RagDiagnostics.run
    CC=12  in:0  out:23  total:23
  services.orchestrator.app.rag.indexer.RagIndexer.ingest_resource
    CC=13  in:0  out:22  total:22
  services.orchestrator.app.api.rag.search
    CC=3  in:0  out:22  total:22
  services.web.app.static.workspace.refreshWorkspace
    CC=7  in:8  out:13  total:21
  services.orchestrator.app.application.command_bus.CommandBus._create_task
    CC=6  in:0  out:20  total:20
  services.orchestrator.app.api.access.upload_resource
    CC=4  in:0  out:19  total:19

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
  services.projector.app.projections.incidents  [7 funcs]
    _checks_payload  CC=10  out:11
    _diagnostics_ok  CC=6  out:4
    _error_code  CC=4  out:3
    _root_cause  CC=4  out:5
    _upsert_rag_quality  CC=1  out:4
    _upsert_service_health  CC=1  out:2
    project_incidents  CC=23  out:51
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
  services.web.app.chat  [10 funcs]
    _append  CC=1  out:2
    _dedupe_rows_by_uri  CC=8  out:10
    _format_history  CC=3  out:3
    _orch  CC=2  out:2
    create_task  CC=7  out:8
    fetch_file_inventory  CC=7  out:15
    format_file_list_reply  CC=22  out:35
    get_history  CC=1  out:2
    handle_message  CC=33  out:35
    is_file_list_intent  CC=7  out:5
  services.web.app.conductor  [6 funcs]
    _extract_shell  CC=3  out:5
    _fallback_turn  CC=4  out:7
    _local_clarify  CC=3  out:3
    _mullm_file_list_turn  CC=1  out:5
    _nlp2dsl_turn  CC=23  out:35
    handle_turn  CC=7  out:8
  services.web.app.nlp2dsl_bridge  [6 funcs]
    _post_json  CC=4  out:6
    backend_candidates  CC=4  out:6
    backend_url  CC=1  out:1
    chat_message  CC=1  out:1
    chat_start  CC=1  out:1
    health  CC=4  out:3
  services.web.app.resource_areas  [2 funcs]
    list_areas  CC=2  out:1
    list_groups  CC=1  out:0
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
  services.web.app.static.workspace  [50 funcs]
    api  CC=6  out:4
    appendMsg  CC=1  out:1
    appendMsgTo  CC=6  out:2
    archiveTicket  CC=2  out:5
    collectClarifyValues  CC=4  out:4
    color  CC=1  out:1
    confirmTicket  CC=1  out:6
    copyChatToClipboard  CC=10  out:11
    copyLogsToClipboard  CC=2  out:5
    copyText  CC=2  out:7
  services.web.app.tickets  [4 funcs]
    enrich_task  CC=4  out:6
    status_meta  CC=3  out:2
    ticket_uri  CC=1  out:0
    ticket_web_path  CC=1  out:0
  services.web.app.workspace  [17 funcs]
    _extract_shell_command  CC=4  out:8
    _extract_ticket  CC=2  out:2
    _format_export_text  CC=47  out:97
    archive_task  CC=2  out:3
    attach_context  CC=12  out:7
    build_task_payload  CC=4  out:7
    create_and_run  CC=5  out:9
    create_task_from_draft  CC=4  out:5
    create_task_immediate  CC=3  out:7
    export_debug_logs  CC=15  out:26
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
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._checks_payload
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._diagnostics_ok
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._upsert_rag_quality
  services.projector.app.projections.incidents.project_incidents → services.projector.app.projections.incidents._upsert_service_health
  services.projector.app.projections.incidents._upsert_rag_quality → services.projector.app.projections.incidents._error_code
  services.projector.app.projections.incidents._root_cause → services.projector.app.projections.incidents._error_code
  services.web.app.workspace.get_or_create → services.web.app.workspace.new_session
  services.web.app.workspace.workspace_state → services.web.app.workspace.get_or_create
  services.web.app.workspace.attach_context → services.web.app.workspace.get_or_create
  services.web.app.workspace.build_task_payload → services.web.app.workspace.get_or_create
  services.web.app.workspace.build_task_payload → services.web.app.workspace._extract_shell_command
  services.web.app.workspace.build_task_payload → services.web.app.workspace._extract_ticket
  services.web.app.workspace.propose_task_draft → services.web.app.workspace.build_task_payload
  services.web.app.workspace.create_task_immediate → services.web.app.workspace.get_or_create
  services.web.app.workspace.create_task_immediate → services.web.app.workspace.link_ticket
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.get_or_create
  services.web.app.workspace.handle_chat_message → services.web.app.workspace._extract_ticket
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.attach_context
  services.web.app.workspace.handle_chat_message → services.web.app.workspace._extract_shell_command
  services.web.app.workspace.handle_chat_message → services.web.app.workspace.build_task_payload
  services.web.app.workspace.create_task_from_draft → services.web.app.workspace.create_task_immediate
  services.web.app.workspace.create_task_from_draft → services.web.app.workspace.get_or_create
  services.web.app.workspace.create_and_run → services.web.app.workspace.create_task_immediate
  services.web.app.workspace.create_and_run → services.web.app.workspace.get_or_create
  services.web.app.workspace.export_debug_logs → services.web.app.workspace.get_or_create
  services.web.app.workspace.export_debug_logs → services.web.app.workspace._format_export_text
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 134f 18312L | python:83,md:16,json:11,txt:6,yaml:5,javascript:4,shell:3,ini:1,yml:1 | 2026-06-04
# generated in 0.03s
# CC̅=3.8 | critical:24/571 | dups:0 | cycles:0

HEALTH[20]:
  🔴 GOD   services/orchestrator/app/domain/events/__init__.py = 1045L, 42 classes, 3m, max CC=7
  🟡 CC    project_incidents CC=23 (limit:15)
  🟡 CC    handle_chat_message CC=21 (limit:15)
  🟡 CC    export_debug_logs CC=15 (limit:15)
  🟡 CC    _format_export_text CC=47 (limit:15)
  🟡 CC    format_file_list_reply CC=22 (limit:15)
  🟡 CC    _format_incident CC=15 (limit:15)
  🟡 CC    handle_message CC=33 (limit:15)
  🟡 CC    renderTicketDetail CC=24 (limit:15)
  🟡 CC    renderContext CC=16 (limit:15)
  🟡 CC    sendChat CC=23 (limit:15)
  🟡 CC    formValues CC=18 (limit:15)
  🟡 CC    createFromDraft CC=15 (limit:15)
  🟡 CC    text CC=16 (limit:15)
  🟡 CC    ORCHESTRATOR_URL CC=15 (limit:15)
  🟡 CC    PROJECTOR_URL CC=15 (limit:15)
  🟡 CC    App CC=15 (limit:15)
  🟡 CC    handle CC=29 (limit:15)
  🟡 CC    format_logs_text CC=29 (limit:15)
  🟡 CC    classify_rag_failure CC=15 (limit:15)

REFACTOR[2]:
  1. split services/orchestrator/app/domain/events/__init__.py  (god module)
  2. split 19 high-CC methods  (CC>15)

PIPELINES[370]:
  [1] Src [lifespan]: lifespan → project_event → _normalize_event
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
  [20] Src [add_event]: add_event
      PURITY: 100% pure
  [21] Src [get_session]: get_session
      PURITY: 100% pure
  [22] Src [workspace_state]: workspace_state → get_or_create → new_session
      PURITY: 100% pure
  [23] Src [propose_task_draft]: propose_task_draft → build_task_payload → get_or_create → new_session
      PURITY: 100% pure
  [24] Src [handle_chat_message]: handle_chat_message → get_or_create → new_session
      PURITY: 100% pure
  [25] Src [create_task_from_draft]: create_task_from_draft → create_task_immediate → get_or_create → new_session
      PURITY: 100% pure
  [26] Src [create_and_run]: create_and_run → create_task_immediate → get_or_create → new_session
      PURITY: 100% pure
  [27] Src [export_debug_logs]: export_debug_logs → get_or_create → new_session
      PURITY: 100% pure
  [28] Src [archive_task]: archive_task → get_or_create → new_session
      PURITY: 100% pure
  [29] Src [fetch_live_board]: fetch_live_board → items → toast
      PURITY: 100% pure
  [30] Src [backend_url]: backend_url → backend_candidates
      PURITY: 100% pure
  [31] Src [health]: health → backend_candidates
      PURITY: 100% pure
  [32] Src [chat_start]: chat_start → _post_json → backend_candidates
      PURITY: 100% pure
  [33] Src [chat_message]: chat_message → _post_json → backend_candidates
      PURITY: 100% pure
  [34] Src [form_to_prompt]: form_to_prompt
      PURITY: 100% pure
  [35] Src [primary_action]: primary_action
      PURITY: 100% pure
  [36] Src [step_config]: step_config
      PURITY: 100% pure
  [37] Src [new_session_id]: new_session_id
      PURITY: 100% pure
  [38] Src [handle_message]: handle_message → _append
      PURITY: 100% pure
  [39] Src [create_task]: create_task → _orch
      PURITY: 100% pure
  [40] Src [r]: r
      PURITY: 100% pure
  [41] Src [state]: state → api
      PURITY: 100% pure
  [42] Src [t]: t → renderTicketDetail → escapeHtml
      PURITY: 100% pure
  [43] Src [color]: color → escapeHtml
      PURITY: 100% pure
  [44] Src [initRouting]: initRouting → selectTicket → ticketWebUrl
      PURITY: 100% pure
  [45] Src [deep]: deep → selectTicket → ticketWebUrl
      PURITY: 100% pure
  [46] Src [m2]: m2 → renderTicketDetail → escapeHtml
      PURITY: 100% pure
  [47] Src [names]: names → escapeHtml
      PURITY: 100% pure
  [48] Src [fields]: fields → escapeHtml
      PURITY: 100% pure
  [49] Src [req]: req → escapeHtml
      PURITY: 100% pure
  [50] Src [fd]: fd
      PURITY: 100% pure

LAYERS:
  services/                       CC̄=3.8    ←in:0  →out:0
  │ !! __init__                  1045L  42C    3m  CC=7      ←0
  │ !! command_bus                982L  1C   41m  CC=29     ←0
  │ !! workspace.js               669L  0C   71m  CC=24     ←3
  │ !! workspace                  604L  2C   22m  CC=47     ←0
  │ !! api_routes                 443L  10C   24m  CC=19     ←0
  │ commands                   379L  14C   23m  CC=4      ←0
  │ !! chat                       354L  0C   13m  CC=33     ←0
  │ !! agent_workroom             354L  2C   10m  CC=22     ←0
  │ main                       340L  0C   15m  CC=4      ←0
  │ !! incidents                  337L  2C   12m  CC=19     ←2
  │ pipeline                   321L  1C    8m  CC=14     ←0
  │ !! incidents                  294L  0C    8m  CC=23     ←1
  │ !! conductor                  283L  0C    6m  CC=23     ←2
  │ store                      240L  1C   12m  CC=10     ←0
  │ task                       231L  1C   15m  CC=11     ←0
  │ rag_diagnostics            204L  1C    8m  CC=12     ←0
  │ !! main.jsx                   203L  0C   14m  CC=15     ←0
  │ main                       195L  0C    5m  CC=6      ←0
  │ !! app.js                     193L  0C   19m  CC=16     ←0
  │ !! export                     190L  0C    2m  CC=29     ←1
  │ eventstore_esdb            186L  1C    8m  CC=4      ←0
  │ workroom.js                186L  0C   17m  CC=11     ←0
  │ eventstore                 182L  2C    9m  CC=6      ←3
  │ queries                    180L  4C    6m  CC=10     ←0
  │ evaluation                 146L  1C    4m  CC=13     ←0
  │ workflow                   144L  1C    9m  CC=3      ←0
  │ resource_areas             144L  0C    3m  CC=7      ←1
  │ rag_pipeline               142L  1C    2m  CC=10     ←0
  │ rag                        142L  2C    6m  CC=3      ←0
  │ access                     136L  3C    8m  CC=4      ←0
  │ approval_gate              129L  1C    4m  CC=8      ←1
  │ resource_registry          118L  0C    1m  CC=8      ←1
  │ task_board                 115L  0C    2m  CC=9      ←1
  │ openrouter                 111L  1C    6m  CC=9      ←1
  │ observability              108L  1C    5m  CC=3      ←0
  │ evolution                  104L  2C    5m  CC=4      ←0
  │ policy_engine              103L  2C    5m  CC=14     ←0
  │ nlp2dsl_bridge             100L  0C    9m  CC=6      ←0
  │ resource                   100L  1C    6m  CC=3      ←0
  │ main                        99L  0C    4m  CC=1      ←0
  │ plugin                      97L  2C    7m  CC=2      ←0
  │ approval                    97L  2C    6m  CC=2      ←0
  │ postgres                    92L  1C    7m  CC=5      ←0
  │ catalog                     92L  1C    6m  CC=4      ←0
  │ retriever                   87L  1C    3m  CC=8      ←0
  │ indexer                     85L  1C    2m  CC=13     ←0
  │ __init__                    85L  11C    2m  CC=4      ←0
  │ agent                       83L  1C    7m  CC=2      ←0
  │ agent_fleet                 81L  0C    1m  CC=8      ←1
  │ approval_requests           79L  0C    1m  CC=6      ←1
  │ transport                   77L  1C    7m  CC=4      ←0
  │ experiments                 76L  1C    4m  CC=2      ←0
  │ localfs                     71L  1C    5m  CC=4      ←0
  │ operational_feed            69L  0C    3m  CC=11     ←1
  │ task_routing                61L  0C    2m  CC=10     ←1
  │ context                     59L  0C    6m  CC=5      ←7
  │ eventstore_dual             57L  1C    5m  CC=2      ←0
  │ db                          56L  1C    6m  CC=4      ←0
  │ config                      54L  1C    1m  CC=1      ←0
  │ eventstore_factory          50L  0C    1m  CC=8      ←1
  │ nats_bus                    49L  1C    5m  CC=4      ←0
  │ http_adapter                49L  1C    4m  CC=3      ←0
  │ workflow_versions           47L  0C    1m  CC=5      ←1
  │ tickets                     45L  0C    4m  CC=4      ←1
  │ uri                         43L  1C    2m  CC=6      ←3
  │ logging                     43L  0C    1m  CC=3      ←3
  │ plugin_catalog              42L  0C    1m  CC=5      ←1
  │ dispatcher                  41L  0C    2m  CC=7      ←1
  │ catalog                     41L  0C    7m  CC=1      ←0
  │ base                        33L  2C    3m  CC=1      ←0
  │ chunking                    27L  0C    1m  CC=7      ←1
  │ Dockerfile                  27L  0C    0m  CC=0.0    ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  21L  0C    0m  CC=0.0    ←0
  │ middleware                  19L  1C    1m  CC=3      ←0
  │ package.json                18L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    1m  CC=2      ←1
  │ requirements.txt            15L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   7L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ requirements.txt             5L  0C    0m  CC=0.0    ←0
  │ requirements.txt             5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ requirements-esdb.txt        2L  0C    0m  CC=0.0    ←0
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
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  509L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md               225L  0C    0m  CC=0.0    ←0
  │ TODO.md                    214L  0C    0m  CC=0.0    ←0
  │ README.md                  209L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml         204L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  52L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   6L  0C    0m  CC=0.0    ←0
  │ requirements-dev.txt         5L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ !! README.md                  776L  0C    0m  CC=0.0    ←0
  │ roadmap-90d.md              83L  0C    0m  CC=0.0    ←0
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
  scripts/                        CC̄=0.0    ←in:0  →out:0
  │ test.sh                     13L  0C    0m  CC=0.0    ←0
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
  │ patch_startup                7L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     services/web/app/__init__.py              0L

COUPLING:
                         services.orchestrator           services.web
  services.orchestrator                     ──                      1
           services.web                     ←1                     ──
  CYCLES: none

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 16 groups | 90f 11521L | 2026-06-04

SUMMARY:
  files_scanned: 90
  total_lines:   11521
  dup_groups:    16
  dup_fragments: 48
  saved_lines:   405
  scan_ms:       2310

HOTSPOTS[7] (files with most duplication):
  services/projector/app/main.py  dup=217L  groups=2  frags=12  (1.9%)
  services/orchestrator/app/api/commands.py  dup=105L  groups=1  frags=7  (0.9%)
  services/orchestrator/app/api/queries.py  dup=60L  groups=1  frags=3  (0.5%)
  services/orchestrator/app/domain/events/__init__.py  dup=42L  groups=3  frags=7  (0.4%)
  services/orchestrator/app/api/access.py  dup=30L  groups=3  frags=4  (0.3%)
  services/orchestrator/app/api/evolution.py  dup=24L  groups=2  frags=3  (0.2%)
  services/orchestrator/app/infrastructure/postgres.py  dup=22L  groups=5  frags=5  (0.2%)

DUPLICATES[16] (ranked by impact):
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
  [c88ebf49370e38e4] ! STRU  get_task  L=20 N=3 saved=40 sim=1.00
      services/orchestrator/app/api/queries.py:29-48  (get_task)
      services/orchestrator/app/api/queries.py:52-71  (get_agent)
      services/orchestrator/app/api/queries.py:75-94  (get_workflow)
  [cbbb67a75ff65ca7]   STRU  transfer_resource  L=9 N=3 saved=18 sim=1.00
      services/orchestrator/app/api/access.py:49-57  (transfer_resource)
      services/orchestrator/app/api/evolution.py:84-92  (propose_change)
      services/orchestrator/app/api/evolution.py:96-104  (shadow_workflow)
  [aa890be89093e6d5]   STRU  data  L=6 N=3 saved=12 sim=1.00
      services/orchestrator/app/domain/events/__init__.py:483-488  (data)
      services/orchestrator/app/domain/events/__init__.py:504-509  (data)
      services/orchestrator/app/domain/events/__init__.py:525-530  (data)
  [4fb7f74cf43032f1]   STRU  list_resources  L=11 N=2 saved=11 sim=1.00
      services/orchestrator/app/api/access.py:77-87  (list_resources)
      services/orchestrator/app/api/evolution.py:75-80  (capability_registry)
  [32839d90ea67fb47]   EXAC  _projector  L=7 N=2 saved=7 sim=1.00
      services/web/app/chat.py:27-33  (_projector)
      services/web/app/workspace.py:19-25  (_projector)
  [1fb3398c7c69da23]   EXAC  data  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/domain/events/__init__.py:1018-1023  (data)
      services/orchestrator/app/domain/events/__init__.py:1040-1045  (data)
  [8d49c56953675bd9]   STRU  data  L=6 N=2 saved=6 sim=1.00
      services/orchestrator/app/domain/events/__init__.py:347-352  (data)
      services/orchestrator/app/domain/events/__init__.py:414-419  (data)
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
  [9cf59ab30a3c0ba7]   EXAC  disconnect  L=4 N=2 saved=4 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:56-59  (disconnect)
      services/projector/app/db.py:28-31  (disconnect)
  [a45a0af197a0ec34]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      services/orchestrator/app/infrastructure/postgres.py:46-48  (__init__)
      services/projector/app/db.py:18-20  (__init__)

REFACTOR[16] (ranked by priority):
  [1] ○ extract_function   → services/projector/app/utils/task_board.py
      WHY: 5 occurrences of 26-line block across 1 files — saves 104 lines
      FILES: services/projector/app/main.py
  [2] ○ extract_function   → services/orchestrator/app/api/utils/create_task.py
      WHY: 7 occurrences of 15-line block across 1 files — saves 90 lines
      FILES: services/orchestrator/app/api/commands.py
  [3] ○ extract_function   → services/projector/app/utils/operational_feed.py
      WHY: 7 occurrences of 14-line block across 1 files — saves 84 lines
      FILES: services/projector/app/main.py
  [4] ○ extract_function   → services/orchestrator/app/api/utils/get_task.py
      WHY: 3 occurrences of 20-line block across 1 files — saves 40 lines
      FILES: services/orchestrator/app/api/queries.py
  [5] ○ extract_function   → services/orchestrator/app/api/utils/transfer_resource.py
      WHY: 3 occurrences of 9-line block across 2 files — saves 18 lines
      FILES: services/orchestrator/app/api/access.py, services/orchestrator/app/api/evolution.py
  [6] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 3 occurrences of 6-line block across 1 files — saves 12 lines
      FILES: services/orchestrator/app/domain/events/__init__.py
  [7] ○ extract_function   → services/orchestrator/app/api/utils/list_resources.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: services/orchestrator/app/api/access.py, services/orchestrator/app/api/evolution.py
  [8] ○ extract_function   → services/web/app/utils/_projector.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: services/web/app/chat.py, services/web/app/workspace.py
  [9] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/orchestrator/app/domain/events/__init__.py
  [10] ○ extract_function   → services/orchestrator/app/domain/events/utils/data.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: services/orchestrator/app/domain/events/__init__.py
  [11] ○ extract_function   → services/orchestrator/app/api/utils/probe_uri.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: services/orchestrator/app/api/access.py
  [12] ○ extract_function   → services/utils/connect.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [13] ○ extract_function   → services/utils/execute.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [14] ○ extract_function   → services/utils/fetch.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [15] ○ extract_function   → services/utils/disconnect.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py
  [16] ○ extract_function   → services/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: services/orchestrator/app/infrastructure/postgres.py, services/projector/app/db.py

QUICK_WINS[10] (low risk, high savings — do first):
  [1] extract_function   saved=104L  → services/projector/app/utils/task_board.py
      FILES: main.py
  [2] extract_function   saved=90L  → services/orchestrator/app/api/utils/create_task.py
      FILES: commands.py
  [3] extract_function   saved=84L  → services/projector/app/utils/operational_feed.py
      FILES: main.py
  [4] extract_function   saved=40L  → services/orchestrator/app/api/utils/get_task.py
      FILES: queries.py
  [5] extract_function   saved=18L  → services/orchestrator/app/api/utils/transfer_resource.py
      FILES: access.py, evolution.py
  [6] extract_function   saved=12L  → services/orchestrator/app/domain/events/utils/data.py
      FILES: __init__.py
  [7] extract_function   saved=11L  → services/orchestrator/app/api/utils/list_resources.py
      FILES: access.py, evolution.py
  [8] extract_function   saved=7L  → services/web/app/utils/_projector.py
      FILES: chat.py, workspace.py
  [9] extract_function   saved=6L  → services/orchestrator/app/domain/events/utils/data.py
      FILES: __init__.py
  [10] extract_function   saved=6L  → services/orchestrator/app/domain/events/utils/data.py
      FILES: __init__.py

EFFORT_ESTIMATE (total ≈ 13.5h):
  hard   task_board                          saved=104L  ~208min
  hard   create_task                         saved=90L  ~180min
  hard   operational_feed                    saved=84L  ~168min
  medium get_task                            saved=40L  ~80min
  medium transfer_resource                   saved=18L  ~36min
  easy   data                                saved=12L  ~24min
  easy   list_resources                      saved=11L  ~22min
  easy   _projector                          saved=7L  ~14min
  easy   data                                saved=6L  ~12min
  easy   data                                saved=6L  ~12min
  ... +6 more (~54min)

METRICS-TARGET:
  dup_groups:  16 → 0
  saved_lines: 405 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 571 func | 76f | 2026-06-04
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           services/orchestrator/app/application/command_bus.py
      WHY: 982L, 1 classes, max CC=29
      EFFORT: ~4h  IMPACT: 28478

  [2] !! SPLIT           services/orchestrator/app/domain/events/__init__.py
      WHY: 1045L, 42 classes, max CC=7
      EFFORT: ~4h  IMPACT: 7315

  [3] !! SPLIT-FUNC      _format_export_text  CC=47  fan=20
      WHY: CC=47 exceeds 15
      EFFORT: ~1h  IMPACT: 940

  [4] !! SPLIT-FUNC      CommandBus.handle  CC=29  fan=29
      WHY: CC=29 exceeds 15
      EFFORT: ~1h  IMPACT: 841

  [5] !! SPLIT-FUNC      handle_message  CC=33  fan=21
      WHY: CC=33 exceeds 15
      EFFORT: ~1h  IMPACT: 693

  [6] !  SPLIT-FUNC      sendChat  CC=23  fan=19
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 437

  [7] !  SPLIT-FUNC      run_workroom  CC=22  fan=19
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 418

  [8] !! SPLIT-FUNC      format_logs_text  CC=29  fan=14
      WHY: CC=29 exceeds 15
      EFFORT: ~1h  IMPACT: 406

  [9] !  SPLIT-FUNC      handle_chat_message  CC=21  fan=18
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 378

  [10] !  SPLIT-FUNC      ORCHESTRATOR_URL  CC=15  fan=24
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 360


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting services/orchestrator/app/domain/events/__init__.py may break 3 import paths
  ⚠ Splitting services/orchestrator/app/application/command_bus.py may break 41 import paths

METRICS-TARGET:
  CC̄:          3.8 → ≤2.7
  max-CC:      47 → ≤20
  god-modules: 7 → 0
  high-CC(≥15): 24 → ≤12
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
  prev CC̄=3.8 → now CC̄=3.8
```

## Intent

Mullm - Multi-Agent Learning and Labor Management
