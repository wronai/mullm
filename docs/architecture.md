# Mullm — architektura

Mullm to event-sourced control plane dla multi-agent runtime (CQRS + ES + NATS).

## Warstwy

| Warstwa | Odpowiedzialność |
|--------|------------------|
| **Runtime** | Shell/browser agenci wykonują zadania |
| **Orchestration** | Command bus, agregaty, zapis eventów, sagi |
| **Query** | Projector → read modele w Postgres |
| **Evolution** | Katalog, policy, evaluation, eksperymenty, controlled change |
| **Access** (plan) | Resource registry, transport, URI `mullm://` |
| **RAG** | OpenRouter embed + FTS, auto-ingest on `RegisterResource`, `/api/rag` |

## Evolution control plane

```
obserwacja → proposal → walidacja (policy) → approval → eksperyment (shadow)
    → rollout → evaluation (metryki) → utrwalenie / rollback
```

- **Architecture catalog** (`catalog/`) — żyjące źródło prawdy o eventach i capability
- **Policy engine** — rules first, potem approval gate
- **Evaluation engine** — success_rate, human_takeover_rate w `evolution_metrics`
- **Experiment manager** — `experiments` + `WorkflowVersionShadowed`

## Przepływ MVP

1. Web/API → `POST /api/commands` (envelope CQRS)
2. Orchestrator → agregat → event store (Postgres `events`)
3. Orchestrator → NATS `mullm.events`
4. Projector → `operational_feed`, `task_board`, `agent_fleet`, …
5. Saga (`maybe_auto_assign`) przy `CreateTask` z `auto_assign: true` → `AssignTask` → NATS `task.assigned.shell`
6. Shell agent → `CompleteTask` / `FailTask`

## Stack Compose

- Postgres (projections + domyślny event store)
- EventStoreDB (opcjonalny trwały log — `EVENT_STORE_BACKEND=dual`)
- NATS (runtime bus)
- orchestrator, projector, shell-agent(s), web

## Approval gate

Ryzykowne komendy (`ActivatePlugin`, `RollbackPlugin`, `ActivateWorkflowVersion`, …) wymagają `approval_id` ze statusem `granted`. Po `ApproveRequest` saga może automatycznie wykonać powiązaną komendę (`follow_up`).
