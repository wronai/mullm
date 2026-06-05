# Pętla oceny routingu (użytkownik → ewolucja)

## Cel

Użytkownik ocenia odpowiedzi asystenta; system zapisuje **decision_tree**, **routing** i kontekst sesji, tworzy **ticket poprawy** dla operatora i agreguje **learnings** (propozycje `user_expectations` w YAML).

Automatyczna zmiana `routing_policy.yaml` / kodu **nie** następuje — review człowieka, potem wdrożenie.

Opcjonalnie: `MULLM_PLANFILE_PROJECT` tworzy równoległy ticket w planfile (`task tickets:next`).
Szczegóły: [ticket-queues-and-planfile.md](./ticket-queues-and-planfile.md).

## API

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| `POST` | `/api/routing/feedback` | Ocena tury (`turn_id` z `routing`) |
| `GET` | `/api/routing/feedback?session_id=` | Historia ocen |
| `GET` | `/api/routing/learnings` | Statystyki + propozycje YAML |
| `GET` | `/api/routing/improvements?status=open` | Tickety poprawy |

### Body `POST /api/routing/feedback`

```json
{
  "session_id": "...",
  "turn_id": "...",
  "rating": "good | partial | bad",
  "expected_route": "mullm_file_list",
  "expected_reply_hint": "Lista z rejestru, nie ls",
  "improvement_notes": "Traktować jako file_list nie shell",
  "tags": ["user_reported"]
}
```

Przy `bad` / `partial` zwracane jest `improvement_ticket` z `suggested_actions`.

## UI (workspace)

Pod odpowiedzią asystenta: **👍** / **～** / **👎** (formularz: oczekiwana trasa, notatki).

Panel **Ewolucja** w kolumnie artefaktów — podsumowanie z `/api/routing/learnings`.

## Zapis

`MULLM_FEEDBACK_DIR` (domyślnie `services/web/data/routing_feedback/`):

- `feedback.jsonl` — każda ocena
- `improvements.jsonl` — tickety poprawy (status `open`)

Zdarzenia sesji: `RouteFeedbackRecorded`, `RoutingImprovementTicket`.

## Wdrażanie learnings

1. `GET /api/routing/learnings` → `proposals[].yaml_hint`
2. Skopiuj do `user_expectations` w `routing_policy.yaml` (lub dopasuj regex w `chat.py`)
3. `docker compose build web` + `make test-quality`

Powiązane: [e2e-chat-routing.md](./e2e-chat-routing.md) (drzewo decyzji, explain).

## nlp2dsl — dopytania w trakcie rozmowy

nlp2dsl (`build_incomplete_response`) zwraca `status=in_progress`, `missing`, `form` — Mullm pokazuje panel **clarify** w UI.

Pipeline ingress (pierwszy krok): **`nlp2dsl_resume`** — wznawia rozmowę gdy sesja ma `nlp2dsl_conversation_id` i status `in_progress`/`ready` (nie tylko słowo „kontynuuj”). Przerwanie: jawna intencja `file_list` lub prefix `run`/`exec`.

Gdy brak polecenia shell: `_missing_shell_response` deleguje do nlp2dsl zamiast sztywnego „podaj run …”.
