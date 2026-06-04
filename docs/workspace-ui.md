# Mullm Workspace UI

Główny panel operacyjny: **http://localhost:3003/** (port z `MULLM_WEB_HOST_PORT`).

## Layout (cockpit)

| Strefa | Funkcja |
|--------|---------|
| Lewa | Kolejka zadań — status, priorytet, agent |
| Środek | Chat + draft zadania z NL |
| Prawa | Kontekst — ticket, projekt, branch, agent, URI, notatki |
| Dół | Pliki (drag-and-drop), operational feed |

## API (BFF w `services/web`)

- `POST /api/chat/session` — nowa sesja workspace
- `GET /api/workspace/state?session_id=` — stan + board
- `POST /api/chat/message` — tryb: `discuss`, `create_task`, `run_task`, `search_context`
- `POST /api/tasks/draft` — propozycja zadania z wiadomości
- `POST /api/tasks/create` / `create-and-run` — z draftu
- `POST /api/context/attach` — przypnij kontekst
- `POST /api/files/upload` — upload + RAG ingest

## Przepływ hybrydowy

1. Operator pisze w chacie np. „dodaj import raportów PLF-074”.
2. System pokazuje **draft** (tytuł, opis, shell jeśli wykryty).
3. Akcje: **Utwórz ticket** | **Utwórz i uruchom** | **Dodaj do kolejki**.

Stary widok tabel: `/dashboard`.
