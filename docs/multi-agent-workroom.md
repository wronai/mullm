# Multi-agent Workroom (Mullm)

## Dwa czaty

| UI | Ścieżka | Rola |
|----|---------|------|
| **Chat użytkownika** | `/` | Ty ↔ conductor (nlp2dsl + Mullm + RAG) |
| **Agent Workroom** | `/workroom` | Zespół agentów ↔ między sobą + ledger |

## MVP (obecny)

- **Coordinator** — plan kroków
- **Files Agent** — lista plików (Access + RAG), obszar `mullm:rag`
- **Shell Agent** — ticket + uruchomienie (`create_task_immediate`)
- **Ledger** — goal, plan, step, message, result, permission
- **Resource Areas** — katalog obszarów (email, fs, docker, chrome, …)
- **Grupy + etykiety** — filtrowanie polityk (`/api/resource-areas`)

## API

```
POST /api/agent-workroom/session     { user_session_id? }
GET  /api/agent-workroom/{id}
POST /api/agent-workroom/{id}/run    { message, wait_for_confirmation? }
GET  /api/resource-areas
GET  /api/resource-areas/roles
```

## Obszary dostępu (rozszerzanie)

Nowy obszar = wpis w `services/web/app/resource_areas.py` → `AREA_CATALOG` + connector w orchestratorze (później).

Przykład:

```python
"email": {
    "connector_type": "email",
    "default_policy": "approval",
    "labels": ["communication", "external"],
}
```

**Grupy** (`list_groups`) łączą wiele `area_id` pod wspólnymi etykietami — przy dużej liczbie zasobów polityki nadajesz na grupę/label, nie na każdy URI.

## Uprawnienia agentów

`DEFAULT_ROLE_SCOPES` + `agent_may_access(role, area_id, action)` → `allow` | `deny` | `approval`.

Kolejne fazy: eventy `PermissionRequested` / `PermissionGranted`, projection `permission_requests`, UI zatwierdzania.

## Docker Compose

W `.env`:

```env
COMPOSE_PROFILES=core,web
```

Bez profilu: `docker compose up -d` zwraca **no service selected**.

Z nlp2dsl:

```env
COMPOSE_PROFILES=core,web,nlp2dsl
```

## Lista plików w czacie użytkownika

Intencja `lista plików` jest obsługiwana **przed** nlp2dsl (`conductor._mullm_file_list_turn`), żeby uniknąć odpowiedzi „Nie rozpoznałem intencji”.

| Komenda | Zakres | Źródło danych |
|---------|--------|----------------|
| `lista plikow` | all | Access Fabric + RAG + URI sesji |
| `lista plikow usera` | user | tylko `mullm://localfs/…`, upload, `file://` |
| `list aplikow usera` | user | jak wyżej (literówka „aplikow”) |

**Nie używa shell agenta** — to rejestr Mullm (projector + orchestrator), nie `ls` na hoście. Shell: tryb **Shell** lub `run ls -la` w czacie głównym.

Workroom (`/workroom`) używa tego samego filtra w kroku `files_agent`.

UI: `/` — artefakt po prawej, **⎘** na wiadomościach, **Cały chat** / **Logi** w nagłówku. Macierze ACL: `/access`.

## Roadmap (skrót)

1. Event store + projections dla workroom
2. Policy Engine w orchestratorze (nie tylko web MVP)
3. Connectors: email, docker, chrome
4. LLM-driven planner zamiast reguł w `agent_workroom.py`
