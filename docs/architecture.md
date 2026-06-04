# Mullm — architektura

Mullm to event-sourced control plane dla multi-agent runtime (CQRS + ES + NATS).

## Warstwy

| Warstwa | Odpowiedzialność |
|--------|------------------|
| **Runtime** | Shell/browser agenci wykonują zadania |
| **Orchestration** | Command bus, agregaty, zapis eventów, sagi |
| **Query** | Projector → read modele w Postgres |
| **Evolution** | Workflow/plugin versioning + approval gate |

## Przepływ MVP

1. Web/API → `POST /api/commands` (envelope CQRS)
2. Orchestrator → agregat → event store (Postgres `events`)
3. Orchestrator → NATS `mullm.events`
4. Projector → `operational_feed`, `task_board`, `agent_fleet`, …
5. Saga → NATS `task.assigned.shell` → shell agent → `CompleteTask` / `FailTask`

## Stack Compose

- Postgres (event store + projections)
- NATS (runtime bus)
- orchestrator, projector, shell-agent(s), web
