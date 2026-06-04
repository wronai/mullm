<!-- code2docs:start --># mullm

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.9-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1069-green)
> **1069** functions | **139** classes | **166** files | CC̄ = 2.8

> Auto-generated project documentation from source code analysis.

**Author:** Tom Softreck <tom@sapletta.com>  
**License:** MIT[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/wronai/mullm](https://github.com/wronai/mullm)

## Installation

### From PyPI

```bash
pip install mullm
```

### From Source

```bash
git clone https://github.com/wronai/mullm
cd mullm
pip install -e .
```


## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
mullm ./my-project

# Only regenerate README
mullm ./my-project --readme-only

# Preview what would be generated (no file writes)
mullm ./my-project --dry-run

# Check documentation health
mullm check ./my-project

# Sync — regenerate only changed modules
mullm sync ./my-project
```

### Python API

```python
from mullm import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
mullm/
├── requirements-dev
├── goal
├── planfile
├── Makefile
├── docker-compose
├── tree
├── pytest
├── prefact
├── CHANGELOG
├── project
├── README
    ├── observability
    ├── workspace-ui
    ├── prompt-router
    ├── workspace-simple
    ├── multi-agent-workroom
    ├── roadmap-90d
    ├── domain
    ├── workspace-conductor
    ├── architecture
    ├── README
    ├── events
        ├── requirements
        ├── Dockerfile
        ├── app/
            ├── main
            ├── db
                ├── resource_registry
            ├── projections/
                ├── task_board
                ├── workflow_versions
                ├── operational_feed
                ├── approval_requests
                ├── incidents
                ├── agent_fleet
                ├── plugin_catalog
        ├── requirements
        ├── package
        ├── Dockerfile
            ├── api_routes
            ├── routing_policy
            ├── resource_areas
        ├── app/
            ├── prompt_router
            ├── agent_workroom
            ├── tickets
            ├── nlp2dsl_bridge
            ├── main
                ├── access
                ├── workroom
                ├── app
                ├── config
                ├── router_routes
            ├── api/
                ├── chat_routes
                ├── models
                ├── workspace_routes
                ├── workroom_routes
                ├── access_routes
            ├── main
            ├── routing_policy
        ├── requirements-esdb
        ├── requirements
        ├── Dockerfile
            ├── config
            ├── main
                ├── eventstore_dual
                ├── eventstore
                ├── nats_bus
                ├── postgres
                ├── eventstore_factory
                ├── eventstore_esdb
                ├── retriever
                ├── store
                ├── openrouter
            ├── rag/
                ├── chunking
                ├── indexer
            ├── incidents/
                ├── pipeline
                ├── command_bus
                ├── sagas/
                    ├── task_routing
                    ├── approval_gate
                ├── uri
            ├── access/
                ├── transport
                    ├── base
                    ├── localfs
                ├── adapters/
                    ├── http_adapter
                ├── catalog
            ├── evolution/
                ├── policy_engine
                ├── evaluation
                ├── experiments
                ├── value_objects/
                    ├── resources
                    ├── base
                    ├── plugins
                ├── events/
                    ├── agents
                    ├── workflows
                    ├── approvals
                    ├── tasks
                    ├── incidents
                    ├── plugin
                    ├── agent
                    ├── approval
                    ├── resource
                    ├── task
                    ├── workflow
                ├── export
            ├── observability/
                ├── rag_pipeline
                ├── context
                ├── middleware
                ├── logging
                ├── rag_diagnostics
                ├── incidents
                ├── commands
                ├── evolution
                ├── catalog
                ├── observability
                ├── queries
                ├── rag
                ├── access
    ├── 4
    ├── 1
    ├── 2
    ├── 3
    ├── test
            ├── toon
            ├── toon
    ├── index
    ├── services
    ├── domains
    ├── policies
    ├── capabilities
        ├── task
        ├── rag
        ├── workflow
        ├── evolution
        ├── access
        ├── mullm_registry
        ├── patch_startup
        ├── requirements
        ├── Dockerfile
            ├── nats_consumer
            ├── executor
            ├── main
├── TODO
                ├── dispatcher
            ├── workspace
            ├── chat
            ├── access_matrix
            ├── conductor
                ├── workspace
                ├── task_routes
```

## API Overview

### Classes

- **`Database`** — —
- **`RagProbeSettings`** — —
- **`RoutingPolicy`** — —
- **`RouteDecision`** — Audytowalna decyzja routingu (ingress Mullm BFF).
- **`LedgerEntry`** — —
- **`WorkroomSession`** — —
- **`ChatSessionStart`** — —
- **`ChatMessage`** — —
- **`TaskDraftRequest`** — —
- **`CreateTaskBody`** — —
- **`CreateFromDraftBody`** — —
- **`ConfirmTicketBody`** — —
- **`SessionRef`** — —
- **`ContextAttachBody`** — —
- **`WorkroomStart`** — —
- **`WorkroomMessage`** — —
- **`AccessMatrixBody`** — —
- **`Settings`** — —
- **`DualEventStore`** — Zapis do Postgres (odczyt) + mirror do EventStoreDB.
- **`EventRecord`** — —
- **`EventStore`** — —
- **`NATSBus`** — —
- **`PostgresConnection`** — —
- **`EsdbEventStore`** — Adapter EventStoreDB przez pakiet `esdbclient`.
- **`RagRetriever`** — —
- **`RagStore`** — —
- **`OpenRouterClient`** — Klient OpenRouter — embeddings i chat (LLM_MODEL z .env).
- **`RagIndexer`** — Ingest zasobu po rejestracji — fetch → chunk → embed → store.
- **`IncidentPipeline`** — —
- **`CommandBus`** — —
- **`ApprovalRequired`** — Komenda wymaga wcześniejszego ApprovalGranted.
- **`MullmUri`** — —
- **`TransportService`** — Access Fabric — probe, fetch, copy między adapterami.
- **`AdapterResult`** — —
- **`ResourceAdapter`** — —
- **`LocalFsAdapter`** — —
- **`HttpAdapter`** — —
- **`ArchitectureCatalog`** — Samopiszący katalog architektury mullm (domains, events, capabilities, policies).
- **`PolicyViolation`** — —
- **`PolicyEngine`** — Reguły first — AI proponuje tylko w granicach polityk z katalogu.
- **`EvaluationEngine`** — Pętla oceny skutków — metryki jakości ewolucji i runtime.
- **`ExperimentManager`** — Shadow / canary — stan eksperymentu powiązany z wersją workflow lub pluginu.
- **`TaskId`** — —
- **`AgentId`** — —
- **`WorkflowId`** — —
- **`PluginId`** — —
- **`ApprovalId`** — —
- **`ResourceId`** — —
- **`Priority`** — —
- **`TaskStatus`** — —
- **`ExecutionMode`** — —
- **`AgentStatus`** — —
- **`WorkflowStatus`** — —
- **`CapabilityRegistered`** — —
- **`ResourceRegistered`** — —
- **`TransferRequested`** — —
- **`TransferCompleted`** — —
- **`TransferFailed`** — —
- **`DomainEvent`** — —
- **`PluginProposed`** — —
- **`PluginValidated`** — —
- **`PluginInstalled`** — —
- **`PluginActivated`** — —
- **`PluginRolledBack`** — —
- **`AgentRegistered`** — —
- **`AgentHeartbeatReceived`** — —
- **`TaskAssignedToAgent`** — —
- **`AgentMarkedIdle`** — —
- **`WorkflowStarted`** — —
- **`WorkflowVersionProposed`** — —
- **`WorkflowVersionValidated`** — —
- **`WorkflowVersionApproved`** — —
- **`WorkflowVersionShadowed`** — —
- **`WorkflowVersionActivated`** — —
- **`WorkflowVersionRolledBack`** — —
- **`ApprovalRequested`** — —
- **`ApprovalGranted`** — —
- **`ApprovalRejected`** — —
- **`ApprovalExpired`** — —
- **`ChangeProposed`** — —
- **`TaskCreated`** — —
- **`TaskAssigned`** — —
- **`TaskStarted`** — —
- **`TaskCompleted`** — —
- **`TaskFailed`** — —
- **`RagRequestFailed`** — —
- **`IncidentDetected`** — —
- **`IncidentClassified`** — —
- **`DiagnosticsStarted`** — —
- **`DiagnosticsCompleted`** — —
- **`RemediationStarted`** — —
- **`RemediationSucceeded`** — —
- **`RemediationFailed`** — —
- **`PostRemediationVerificationPassed`** — —
- **`PostRemediationVerificationFailed`** — —
- **`PluginStatus`** — —
- **`Plugin`** — —
- **`Agent`** — —
- **`ApprovalStatus`** — —
- **`Approval`** — —
- **`Resource`** — —
- **`Task`** — —
- **`Workflow`** — —
- **`RagPipeline`** — —
- **`CorrelationMiddleware`** — —
- **`RagDiagnostics`** — —
- **`IncidentCode`** — —
- **`IncidentRecorder`** — —
- **`CommandEnvelope`** — —
- **`CreateTaskCommand`** — —
- **`AssignTaskCommand`** — —
- **`StartTaskCommand`** — —
- **`CompleteTaskCommand`** — —
- **`FailTaskCommand`** — —
- **`RegisterAgentCommand`** — —
- **`StartWorkflowCommand`** — —
- **`ProposeWorkflowVersionCommand`** — —
- **`WorkflowVersionCommand`** — —
- **`ProposePluginCommand`** — —
- **`PluginIdCommand`** — —
- **`CreateApprovalCommand`** — —
- **`ApprovalActionCommand`** — —
- **`ProposeChangeCommand`** — —
- **`ShadowWorkflowCommand`** — —
- **`DiagnoseBody`** — —
- **`TaskQuery`** — —
- **`AgentQuery`** — —
- **`WorkflowQuery`** — —
- **`TaskListQuery`** — —
- **`SearchQuery`** — —
- **`AskQuery`** — —
- **`RegisterResourceCommand`** — —
- **`TransferResourceCommand`** — —
- **`ProbeUriCommand`** — —
- **`ShellAgent`** — —
- **`ShellResult`** — —
- **`WorkspaceContext`** — —
- **`WorkspaceSession`** — —
- **`TurnState`** — —

### Functions

- `lifespan(app)` — —
- `health_check()` — —
- `operational_feed(limit, offset)` — —
- `task_board(status, limit, offset)` — —
- `agent_fleet(status, limit, offset)` — —
- `approval_requests(status, limit, offset)` — —
- `plugin_catalog(status, limit, offset)` — —
- `rag_documents(limit, offset)` — —
- `incident_feed(status, limit, offset)` — —
- `service_health(limit, offset)` — —
- `remediation_history(limit, offset)` — —
- `rag_quality_board(limit, offset)` — —
- `resource_registry(limit, offset)` — —
- `workflow_versions(limit, offset)` — —
- `project_resource_registry(db, event)` — —
- `project_task_board(db, event)` — —
- `project_workflow_versions(db, event)` — —
- `project_operational_feed(db, event)` — —
- `project_approval_requests(db, event)` — —
- `project_incidents(db, event)` — —
- `project_agent_fleet(db, event)` — —
- `project_plugin_catalog(db, event)` — —
- `load_policy()` — —
- `list_areas()` — —
- `list_groups()` — Grupy logiczne — filtrowanie polityk po labelach.
- `agent_may_access(role_id, area_id, action)` — Decyzja MVP: allow | deny | approval (+ macierz z /access).
- `decide_route_rules(message)` — Kaskada reguł z listą kandydatów (ranking confidence).
- `decide_route_llm(message)` — Opcjonalna klasyfikacja JSON przez OpenRouter.
- `decide_route(message)` — —
- `record_route_event(session_id, decision)` — Zapis do ledger sesji (observability).
- `create_workroom()` — —
- `get_workroom(workroom_id)` — —
- `format_workroom_export(session)` — Pełna treść workroom do schowka (wątek + ledger + odpowiedź).
- `run_workroom(workroom_id, user_message)` — —
- `workroom_catalog()` — —
- `ticket_uri(task_id)` — —
- `ticket_web_path(task_id)` — —
- `status_meta(status)` — —
- `enrich_task(row)` — —
- `backend_url()` — —
- `backend_candidates()` — —
- `health()` — —
- `chat_start(text)` — —
- `chat_message(conversation_id, text)` — —
- `form_to_prompt(form, values)` — —
- `primary_action(dsl)` — —
- `step_config(dsl)` — —
- `health()` — —
- `workspace_home(request, task_id)` — —
- `agent_workroom_page(request)` — —
- `access_matrix_page(request)` — —
- `dashboard(request)` — —
- `state()` — —
- `toast()` — —
- `api()` — —
- `r()` — —
- `data()` — —
- `escapeHtml()` — —
- `renderAgentResourceMatrix()` — —
- `resources()` — —
- `agents()` — —
- `matrix()` — —
- `checked()` — —
- `renderHumanAgentMatrix()` — —
- `humans()` — —
- `renderAll()` — —
- `load()` — —
- `diag()` — —
- `save()` — —
- `res()` — —
- `resetAll()` — —
- `id()` — —
- `title()` — —
- `workroomId()` — —
- `userSessionId()` — —
- `toast()` — —
- `api()` — —
- `r()` — —
- `data()` — —
- `escapeHtml()` — —
- `ensureWorkroom()` — —
- `renderCatalog()` — —
- `loadAreas()` — —
- `renderThread()` — —
- `st()` — —
- `renderLedger()` — —
- `lastState()` — —
- `renderState()` — —
- `copyText()` — —
- `ta()` — —
- `buildLedgerExport()` — —
- `buildFallbackExport()` — —
- `who()` — —
- `text()` — —
- `copyWorkroomAll()` — —
- `copyWorkroomLogs()` — —
- `state()` — —
- `runAgents()` — —
- `refresh()` — —
- `sessionId()` — —
- `toast()` — —
- `appendMessage()` — —
- `div()` — —
- `m()` — —
- `renderHistory()` — —
- `ensureSession()` — —
- `r()` — —
- `data()` — —
- `uploadFiles()` — —
- `files()` — —
- `fd()` — —
- `text()` — —
- `uploaded()` — —
- `rowTask()` — —
- `escapeHtml()` — —
- `refreshTables()` — —
- `tasksBody()` — —
- `tasks()` — —
- `router_decide(message, mode, use_rag)` — Podgląd trasy promptu (debug): reguły lub LLM (PROMPT_ROUTER_MODE).
- `routing_policy_get(reload)` — Aktualna polityka ingress (YAML + domyślne).
- `start_chat_session(body)` — —
- `get_chat_session(session_id)` — —
- `workspace_state(session_id)` — —
- `chat_message(body)` — —
- `task_draft(body)` — —
- `context_attach(body)` — —
- `upload_files(session_id, files, classification)` — —
- `board_snapshot()` — —
- `workspace_list_artifacts(session_id)` — —
- `workspace_get_artifact(session_id, artifact_id)` — —
- `workspace_file_list_export(session_id, message, scope)` — Lista plików jako artefakt (text + json).
- `workspace_chat_export(session_id)` — Transkrypt chatu do schowka (rozmowa + routing, bez RAG health).
- `workspace_logs_export(session_id, limit)` — Paczka logów do schowka: RAG health, incydenty, historia sesji, feed.
- `workroom_start(body)` — —
- `workroom_get(workroom_id)` — —
- `workroom_export(workroom_id)` — Pełna zawartość workroom (wątek, ledger, odpowiedź) — pole text do schowka.
- `workroom_run(workroom_id, body)` — —
- `api_resource_areas()` — —
- `api_role_scopes()` — —
- `access_matrix_get()` — —
- `access_matrix_put(body)` — —
- `access_matrix_reset()` — —
- `access_diagnose_file_list()` — —
- `ORCHESTRATOR_URL()` — —
- `PROJECTOR_URL()` — —
- `envUrl()` — —
- `fetchJson()` — —
- `response()` — —
- `postJson()` — —
- `taskMetrics()` — —
- `App()` — —
- `metrics()` — —
- `refresh()` — —
- `createTask()` — —
- `created()` — —
- `timer()` — —
- `Sidebar()` — —
- `Topbar()` — —
- `Metrics()` — —
- `Metric()` — —
- `TaskForm()` — —
- `TaskBoard()` — —
- `TaskRow()` — —
- `AgentsPanel()` — —
- `FeedPanel()` — —
- `lifespan(app)` — —
- `health_check()` — —
- `root()` — —
- `build_event_store()` — Tworzy event store wg EVENT_STORE_BACKEND.
- `normalize_openrouter_model(model)` — OpenRouter API nie akceptuje prefiksu openrouter/ z lokalnego .env.
- `chunk_text(text)` — Proste dzielenie tekstu na nakładające się fragmenty.
- `classify_rag_error(error)` — —
- `pick_idle_agent(event_store, required_capabilities)` — Wybiera pierwszego idle agenta spełniającego wymagane capability.
- `maybe_auto_assign(command_bus)` — Po CreateTask opcjonalnie przypisuje zadanie do wolnego agenta (saga MVP).
- `ensure_approval(event_store, command_type, data)` — Weryfikuje, że ryzykowna komenda ma przyznaną zgodę.
- `follow_up_after_grant(command_bus)` — Po ApprovalGranted wykonuje powiązaną komendę (saga kontynuacji).
- `parse_uri(uri)` — —
- `build_uri(adapter, path)` — —
- `get_adapter(name)` — —
- `format_logs_text(bundle)` — —
- `build_orchestrator_bundle()` — —
- `new_correlation_id()` — —
- `new_retrieval_trace_id()` — —
- `get_correlation_id()` — —
- `get_retrieval_trace_id()` — —
- `get_chat_session_id()` — —
- `observability_context()` — —
- `log_event()` — —
- `classify_rag_failure()` — —
- `post_command(command, request)` — Submit a CQRS command envelope.
- `create_task(command, request)` — Create a new task
- `assign_task(command, request)` — Assign a task to an agent
- `start_task(command, request)` — Mark a task as running.
- `complete_task(command, request)` — Mark a task as completed
- `fail_task(command, request)` — Mark a task as failed.
- `register_agent(command, request)` — Register a new agent
- `start_workflow(command, request)` — Start a new workflow
- `propose_workflow_version(command, request)` — —
- `validate_workflow_version(command, request)` — —
- `approve_workflow_version(command, request)` — —
- `activate_workflow_version(command, request)` — —
- `rollback_workflow_version(command, request)` — —
- `propose_plugin(command, request)` — —
- `validate_plugin(command, request)` — —
- `install_plugin(command, request)` — —
- `activate_plugin(command, request)` — —
- `rollback_plugin(command, request)` — —
- `create_approval(command, request)` — —
- `approve_request(command, request)` — —
- `reject_request(command, request)` — —
- `expire_approval(command, request)` — —
- `evolution_metrics(request, subject_type, subject_id, limit)` — —
- `list_experiments(request, status, limit)` — —
- `capability_registry(request, limit)` — —
- `propose_change(command, request)` — —
- `shadow_workflow(command, request)` — —
- `catalog_index(request)` — —
- `catalog_graph(request)` — —
- `catalog_domains(request)` — —
- `catalog_events(request)` — —
- `catalog_capabilities(request)` — —
- `catalog_services(request)` — —
- `catalog_policies(request)` — —
- `rag_health(request)` — —
- `rag_diagnose(body, request)` — —
- `list_playbooks()` — —
- `export_logs(request, correlation_id, limit)` — Paczka diagnostyczna (JSON + pole `text` do schowka).
- `list_incidents(request, limit)` — —
- `get_task(task_id, request)` — Get task by ID
- `get_agent(agent_id, request)` — Get agent by ID
- `get_workflow(workflow_id, request)` — Get workflow by ID
- `list_tasks(request, status, agent_id, limit)` — List tasks with optional filtering
- `list_agents(request, limit, offset)` — List all agents
- `rag_health(request)` — —
- `list_documents(request, limit)` — —
- `search(body, request)` — —
- `ask(body, request)` — —
- `ingest_resource(resource_id, request)` — —
- `register_resource(command, request)` — —
- `transfer_resource(command, request)` — —
- `probe_uri(command, request)` — —
- `fetch_uri(command, request)` — —
- `list_resources(request, limit)` — —
- `build_resource_uri(adapter, path)` — —
- `upload_resource(request, file, classification)` — Zapisuje plik w localfs (chat/) i rejestruje zasób + RAG ingest.
- `run_shell_command(command, timeout_seconds)` — —
- `main()` — —
- `project_event(db, event)` — —
- `new_session()` — —
- `get_session(session_id)` — —
- `get_or_create(session_id)` — —
- `register_artifact(session, artifact)` — Zapisuje artefakt w sesji (lista + podgląd po prawej w UI).
- `artifact_summaries(session)` — Metadane do listy (bez dużego json — pełny podgląd po id).
- `get_artifact(session_id, artifact_id)` — —
- `workspace_state(session_id)` — —
- `attach_context(session_id)` — —
- `build_task_payload(session_id, message)` — Szkic pól zadania (tylko API /tasks/draft) — nie zapisuje sesji.
- `propose_task_draft(session_id, message)` — Kompatybilność API — zwraca payload bez trzymania szkicu w sesji.
- `create_task_immediate(session_id)` — Tworzy ticket od razu; domyślnie przypisuje agenta (uruchomienie).
- `handle_chat_message()` — —
- `create_task_from_draft(session_id)` — —
- `create_and_run(session_id)` — —
- `format_chat_export_text(session)` — Transkrypt czatu do schowka (rozmowa + routing pod odpowiedziami AI).
- `export_debug_logs(session_id)` — Zbiera logi sesji + orchestrator + feed do kopiowania do schowka.
- `archive_task(session_id, task_id)` — —
- `link_ticket(session_id, task_id)` — —
- `fetch_live_board()` — —
- `is_file_list_intent(message)` — —
- `file_list_scope(message)` — Zakres listy: all | user | system | session | rag.
- `filter_file_inventory(inventory, list_scope)` — Filtruje rejestr i RAG według zakresu.
- `fetch_file_inventory()` — —
- `format_file_list_reply(inventory)` — —
- `build_file_list_artifact(reply_text, inventory)` — Artefakt do pobrania w UI (Blob) lub ponownego exportu API.
- `new_session_id()` — —
- `get_history(session_id)` — —
- `stamp_last_assistant_routing(session_id, routing)` — Dołącza decyzję routera do ostatniej wiadomości asystenta (badge w UI).
- `handle_message()` — —
- `probe_rag()` — Lekkie wyszukiwanie RAG (bez LLM) — krok rag_probe w polityce ingress.
- `create_task()` — —
- `default_state()` — —
- `load_state()` — —
- `save_state(state)` — —
- `agent_may_access_resource(agent_id, resource_id)` — —
- `human_may_use_agent(human_id, agent_id)` — —
- `diagnose_file_list_command()` — Wyjaśnienie: lista plików ≠ shell, ≠ dysk hosta.
- `handle_turn()` — Pipeline ingress z routing_policy.yaml (domyślnie: rag_probe → rules → nlp2dsl → rag_answer).
- `sessionId()` — —
- `currentDraft()` — —
- `selectedTaskId()` — —
- `pendingClarify()` — —
- `artifactFullCache()` — —
- `selectedArtifactId()` — —
- `ticketWebUrl()` — —
- `ticketUri()` — —
- `toast()` — —
- `api()` — —
- `r()` — —
- `data()` — —
- `detail()` — —
- `ensureSession()` — —
- `loadTickets()` — —
- `refreshWorkspace()` — —
- `state()` — —
- `t()` — —
- `filterTasks()` — —
- `q()` — —
- `loadTicketDetail()` — —
- `selectTicket()` — —
- `renderTicketDetail()` — —
- `renderEmptyTicketDetail()` — —
- `ticketStatus()` — —
- `key()` — —
- `ticketDetailHtml()` — —
- `status()` — —
- `bindTicketDetailActions()` — —
- `confirmTicket()` — —
- `archiveTicket()` — —
- `initRouting()` — —
- `deep()` — —
- `m()` — —
- `id()` — —
- `m2()` — —
- `renderContext()` — —
- `setInputValue()` — —
- `renderTextList()` — —
- `renderDraft()` — —
- `renderClarify()` — —
- `fields()` — —
- `req()` — —
- `collectClarifyValues()` — —
- `fd()` — —
- `routingTraceRows()` — —
- `seen()` — —
- `assistantIdx()` — —
- `renderRoutingPolicy()` — —
- `saveSessionAgent()` — —
- `agentId()` — —
- `renderRoutingTrace()` — —
- `rows()` — —
- `pct()` — —
- `codes()` — —
- `label()` — —
- `n2()` — —
- `n2html()` — —
- `routingTraceText()` — —
- `formatChatContent()` — —
- `renderChat()` — —
- `items()` — —
- `meta()` — —
- `appendMsg()` — —
- `cacheArtifactFull()` — —
- `syncArtifacts()` — —
- `clearArtifactPreview()` — —
- `renderArtifactList()` — —
- `active()` — —
- `when()` — —
- `selectArtifact()` — —
- `art()` — —
- `showArtifactPreview()` — —
- `preferredArtifactTab()` — —
- `updateArtifactPreviewTabs()` — —
- `hasText()` — —
- `hasJson()` — —
- `updateArtifactTab()` — —
- `renderArtifactPreviewBody()` — —
- `downloadArtifact()` — —
- `name()` — —
- `url()` — —
- `link()` — —
- `msgRoleLabel()` — —
- `formatNlp2dslBadge()` — —
- `action()` — —
- `src()` — —
- `auth()` — —
- `formatRouteBadge()` — —
- `ms()` — —
- `fb()` — —
- `appendRouteBadge()` — —
- `badge()` — —
- `appendMsgTo()` — —
- `div()` — —
- `raw()` — —
- `head()` — —
- `copyBtn()` — —
- `body()` — —
- `renderTasks()` — —
- `sk()` — —
- `stClass()` — —
- `color()` — —
- `renderFileChips()` — —
- `escapeHtml()` — —
- `saveContextFromForm()` — —
- `syncContextNote()` — —
- `uploadFiles()` — —
- `sendChat()` — —
- `input()` — —
- `chatInput()` — —
- `uploadPendingChatFiles()` — —
- `appendPendingChatInput()` — —
- `formValuesText()` — —
- `clearChatInput()` — —
- `chatPayload()` — —
- `handleChatResponse()` — —
- `showFileListToast()` — —
- `showRoutingToast()` — —
- `focusCreatedTicket()` — —
- `setChatSending()` — —
- `resetChatFiles()` — —
- `createFromDraft()` — —
- `draft()` — —
- `ensureDraftFromInput()` — —
- `text()` — —
- `drafted()` — —
- `submitDraft()` — —
- `draftCreated()` — —
- `finishDraftCreation()` — —
- `tid()` — —
- `openTicketDialogFromDraft()` — —
- `d()` — —
- `copyText()` — —
- `ta()` — —
- `routingLineFromMsgEl()` — —
- `buildChatTextFromDom()` — —
- `routeLine()` — —
- `copyChatToClipboard()` — —
- `copyChatViewToClipboard()` — —
- `copyLogsToClipboard()` — —
- `bindCopyChatButtons()` — —
- `handlerFull()` — —
- `handlerView()` — —
- `note()` — —
- `submitTaskForm()` — —
- `wait()` — —
- `create_task(body)` — —
- `create_task_from_draft(body)` — —
- `create_and_run_task(body)` — —
- `list_tickets(session_id, view)` — —
- `ticket_statuses()` — —
- `get_ticket(task_id, session_id)` — —
- `confirm_ticket(task_id, body)` — —
- `archive_ticket(task_id, body)` — —
- `link_ticket(task_id, body)` — —


## Project Structure

📄 `CHANGELOG`
📄 `Makefile`
📄 `README`
📄 `TODO`
📄 `TODO.1`
📄 `TODO.2`
📄 `TODO.3`
📄 `TODO.4`
📄 `agents.shell-agent.Dockerfile`
📄 `agents.shell-agent.app.executor` (2 functions, 1 classes)
📄 `agents.shell-agent.app.main` (1 functions)
📄 `agents.shell-agent.app.nats_consumer` (3 functions, 1 classes)
📄 `agents.shell-agent.requirements`
📄 `catalog.capabilities`
📄 `catalog.domains`
📄 `catalog.events.access`
📄 `catalog.events.evolution`
📄 `catalog.events.rag`
📄 `catalog.events.task`
📄 `catalog.events.workflow`
📄 `catalog.index`
📄 `catalog.policies`
📄 `catalog.services`
📄 `docker-compose`
📄 `docs.README`
📄 `docs.architecture`
📄 `docs.domain`
📄 `docs.events`
📄 `docs.multi-agent-workroom`
📄 `docs.observability`
📄 `docs.prompt-router`
📄 `docs.roadmap-90d`
📄 `docs.workspace-conductor`
📄 `docs.workspace-simple`
📄 `docs.workspace-ui`
📄 `goal`
📄 `integrations.nlp2dsl.mullm_registry`
📄 `integrations.nlp2dsl.patch_startup`
📄 `planfile`
📄 `prefact`
📄 `project`
📄 `pytest`
📄 `requirements-dev`
📄 `scripts.test`
📄 `services.orchestrator.Dockerfile`
📦 `services.orchestrator.app.access`
📦 `services.orchestrator.app.access.adapters` (1 functions)
📄 `services.orchestrator.app.access.adapters.base` (3 functions, 2 classes)
📄 `services.orchestrator.app.access.adapters.http_adapter` (4 functions, 1 classes)
📄 `services.orchestrator.app.access.adapters.localfs` (5 functions, 1 classes)
📄 `services.orchestrator.app.access.transport` (7 functions, 1 classes)
📄 `services.orchestrator.app.access.uri` (2 functions, 1 classes)
📄 `services.orchestrator.app.api.access` (8 functions, 3 classes)
📄 `services.orchestrator.app.api.catalog` (7 functions)
📄 `services.orchestrator.app.api.commands` (23 functions, 14 classes)
📄 `services.orchestrator.app.api.evolution` (5 functions, 2 classes)
📄 `services.orchestrator.app.api.observability` (5 functions, 1 classes)
📄 `services.orchestrator.app.api.queries` (9 functions, 4 classes)
📄 `services.orchestrator.app.api.rag` (6 functions, 2 classes)
📄 `services.orchestrator.app.application.command_bus` (44 functions, 1 classes)
📦 `services.orchestrator.app.application.sagas`
📄 `services.orchestrator.app.application.sagas.approval_gate` (6 functions, 1 classes)
📄 `services.orchestrator.app.application.sagas.task_routing` (4 functions)
📄 `services.orchestrator.app.config` (1 functions, 1 classes)
📄 `services.orchestrator.app.domain.aggregates.agent` (7 functions, 1 classes)
📄 `services.orchestrator.app.domain.aggregates.approval` (6 functions, 2 classes)
📄 `services.orchestrator.app.domain.aggregates.plugin` (7 functions, 2 classes)
📄 `services.orchestrator.app.domain.aggregates.resource` (6 functions, 1 classes)
📄 `services.orchestrator.app.domain.aggregates.task` (20 functions, 1 classes)
📄 `services.orchestrator.app.domain.aggregates.workflow` (9 functions, 1 classes)
📦 `services.orchestrator.app.domain.events`
📄 `services.orchestrator.app.domain.events.agents` (4 classes)
📄 `services.orchestrator.app.domain.events.approvals` (5 classes)
📄 `services.orchestrator.app.domain.events.base` (3 functions, 1 classes)
📄 `services.orchestrator.app.domain.events.incidents` (10 classes)
📄 `services.orchestrator.app.domain.events.plugins` (5 classes)
📄 `services.orchestrator.app.domain.events.resources` (5 classes)
📄 `services.orchestrator.app.domain.events.tasks` (5 classes)
📄 `services.orchestrator.app.domain.events.workflows` (7 classes)
📦 `services.orchestrator.app.domain.value_objects` (2 functions, 11 classes)
📦 `services.orchestrator.app.evolution`
📄 `services.orchestrator.app.evolution.catalog` (6 functions, 1 classes)
📄 `services.orchestrator.app.evolution.evaluation` (7 functions, 1 classes)
📄 `services.orchestrator.app.evolution.experiments` (4 functions, 1 classes)
📄 `services.orchestrator.app.evolution.policy_engine` (8 functions, 2 classes)
📦 `services.orchestrator.app.incidents`
📄 `services.orchestrator.app.incidents.pipeline` (12 functions, 1 classes)
📄 `services.orchestrator.app.infrastructure.eventstore` (9 functions, 2 classes)
📄 `services.orchestrator.app.infrastructure.eventstore_dual` (5 functions, 1 classes)
📄 `services.orchestrator.app.infrastructure.eventstore_esdb` (8 functions, 1 classes)
📄 `services.orchestrator.app.infrastructure.eventstore_factory` (4 functions)
📄 `services.orchestrator.app.infrastructure.nats_bus` (5 functions, 1 classes)
📄 `services.orchestrator.app.infrastructure.postgres` (7 functions, 1 classes)
📄 `services.orchestrator.app.main` (5 functions)
📦 `services.orchestrator.app.observability`
📄 `services.orchestrator.app.observability.context` (6 functions)
📄 `services.orchestrator.app.observability.export` (17 functions)
📄 `services.orchestrator.app.observability.incidents` (37 functions, 2 classes)
📄 `services.orchestrator.app.observability.logging` (1 functions)
📄 `services.orchestrator.app.observability.middleware` (1 functions, 1 classes)
📄 `services.orchestrator.app.observability.rag_diagnostics` (12 functions, 1 classes)
📄 `services.orchestrator.app.observability.rag_pipeline` (10 functions, 1 classes)
📦 `services.orchestrator.app.rag`
📄 `services.orchestrator.app.rag.chunking` (1 functions)
📄 `services.orchestrator.app.rag.indexer` (8 functions, 1 classes)
📄 `services.orchestrator.app.rag.openrouter` (9 functions, 1 classes)
📄 `services.orchestrator.app.rag.retriever` (8 functions, 1 classes)
📄 `services.orchestrator.app.rag.store` (21 functions, 1 classes)
📄 `services.orchestrator.requirements`
📄 `services.orchestrator.requirements-esdb`
📄 `services.projector.Dockerfile`
📦 `services.projector.app`
📄 `services.projector.app.db` (6 functions, 1 classes)
📄 `services.projector.app.main` (15 functions)
📦 `services.projector.app.projections`
📄 `services.projector.app.projections.agent_fleet` (5 functions)
📄 `services.projector.app.projections.approval_requests` (1 functions)
📄 `services.projector.app.projections.dispatcher` (4 functions)
📄 `services.projector.app.projections.incidents` (19 functions)
📄 `services.projector.app.projections.operational_feed` (3 functions)
📄 `services.projector.app.projections.plugin_catalog` (1 functions)
📄 `services.projector.app.projections.resource_registry` (5 functions)
📄 `services.projector.app.projections.task_board` (7 functions)
📄 `services.projector.app.projections.workflow_versions` (1 functions)
📄 `services.projector.requirements`
📄 `services.web.Dockerfile`
📦 `services.web.app`
📄 `services.web.app.access_matrix` (19 functions)
📄 `services.web.app.agent_workroom` (33 functions, 2 classes)
📦 `services.web.app.api`
📄 `services.web.app.api.access_routes` (6 functions)
📄 `services.web.app.api.chat_routes` (9 functions)
📄 `services.web.app.api.config`
📄 `services.web.app.api.models` (11 classes)
📄 `services.web.app.api.router_routes` (2 functions)
📄 `services.web.app.api.task_routes` (18 functions)
📄 `services.web.app.api.workroom_routes` (5 functions)
📄 `services.web.app.api.workspace_routes` (5 functions)
📄 `services.web.app.api_routes`
📄 `services.web.app.chat` (74 functions)
📄 `services.web.app.conductor` (42 functions, 1 classes)
📄 `services.web.app.main` (5 functions)
📄 `services.web.app.nlp2dsl_bridge` (9 functions)
📄 `services.web.app.prompt_router` (23 functions, 1 classes)
📄 `services.web.app.resource_areas` (5 functions)
📄 `services.web.app.routing_policy` (11 functions, 2 classes)
📄 `services.web.app.static.access` (25 functions)
📄 `services.web.app.static.app` (28 functions)
📄 `services.web.app.static.workroom` (33 functions)
📄 `services.web.app.static.workspace` (178 functions)
📄 `services.web.app.tickets` (4 functions)
📄 `services.web.app.workspace` (80 functions, 2 classes)
📄 `services.web.data.routing_policy`
📄 `services.web.package`
📄 `services.web.requirements`
📄 `services.web.src.main` (23 functions)
📄 `testql-scenarios.generated-api-smoke.testql.toon`
📄 `testql-scenarios.generated-from-pytests.testql.toon`
📄 `tree`

## Requirements



## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/wronai/mullm
cd mullm

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 🏛️ [Architecture](./docs/architecture.md) — Architecture with diagrams

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |

<!-- code2docs:end -->