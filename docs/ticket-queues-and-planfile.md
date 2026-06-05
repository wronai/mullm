# Ticket queues — Mullm vs planfile

## Trzy kolejki w Mullm (dziś)

| Kind | Gdzie | URI | Do czego |
|------|--------|-----|----------|
| **execution** | Orchestrator EventStore + projector | `mullm://ticket/{uuid}` | Shell (`nlp2cmd` → `shell-agent-a/b` NATS) |
| **improvement** | `data/routing_feedback/improvements.jsonl` | `mullm://routing-improvement/{uuid}` | Oczekiwana trasa / ocena 👎 |
| **workflow** | nlp2dsl `conversation_id` | `mullm://nlp2dsl/{id}` | Dopytania DSL, formularz clarify |

UI **◎ Tickety** = tylko **execution** (projector `/projections/tasks`).  
Panel **Ewolucja** = **improvement** (nie planfile).

Schematy: `GET /api/tickets/schemas` (`mullm.tickets.schemas.v1`).

## Standardy tworzenia (Mullm)

- **execution** — `ExecutionTicketCreate` → `POST /api/commands/tasks` (Pydantic w orchestratorze: `CreateTaskCommand`)
- **improvement** — `ImprovementTicket` (`mullm.routing.improvement_ticket.v1`) → `POST /api/routing/feedback` (rating `bad`/`partial`)
- **workflow** — stan nlp2dsl; Mullm nie tworzy UUID, trzyma `nlp2dsl_conversation_id` w sesji

## Czy planfile może zastąpić Mullm tickets?

| Obszar | Zastąpienie | Uwagi |
|--------|-------------|--------|
| **improvement** | **Tak** | `executor: human`, `queue: mullm-routing` — już most (`planfile_bridge`) |
| **workflow** | **Częściowo** | planfile `waiting_input` + formularz; nlp2dsl nadal silnik NL→DSL |
| **execution (shell)** | **Nie od razu** | Mullm = EventStore + NATS + shell-agent; planfile `executor: shell` + `koru --queue` to **inna** ścieżka wykonania |

**Rekomendacja:** planfile jako **wspólna lista pracy człowieka** (routing, YAML, review); orchestrator zostaje **runtime wykonania** shell do czasu adaptera `planfile ticket complete` → NATS.

## Integracja improvement → planfile

```bash
# W .env Mullm (repo z .planfile/, np. mullm lub koru)
MULLM_PLANFILE_PROJECT=/home/tom/github/wronai/mullm

# Po 👎 z expected_route:
# 1. JSONL improvements.jsonl (jak dotąd)
# 2. planfile ticket create --source mullm.routing --label routing-improvement
```

Wymaga `planfile` w PATH w kontenerze `web` (opcjonalnie; bez env sync wyłączony).

## Wiele systemów kolejkowych

Planfile (Koru) jest projektowany jako **execution gateway** z polami:

- `executor.kind` — human | shell | mcp | api | llm
- `execution.queue` — np. `default`, `mullm-routing`, `mullm-shell`
- `source` / `labels` — deduplikacja (`dedupe:mullm-routing-{turn_id}`)

Mullm nie powinien duplikować YAML sprintu — tylko **emitować** tickety z `source=mullm.*` do wskazanego `.planfile/`.

Powiązane: [routing-feedback-loop.md](./routing-feedback-loop.md), Koru [planfile-execution-gateway.md](https://github.com/semcod/koru/blob/main/docs/planfile-execution-gateway.md).
