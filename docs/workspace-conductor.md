# Workspace + nlp2dsl (chat-first)

## Idea

Jeden **chat** — bez klikania draftu / trybów. [nlp2dsl](https://github.com/wronai/nlp2dsl) prowadzi rozmowę i **dopytuje** o brakujące pola; Mullm **wykonuje** gotowe intencje (lista plików, ticket, shell).

## Uruchomienie

```bash
# Mullm
docker compose --profile core --profile rag up -d

# nlp2dsl (obok, w repo nlp2dsl)
cd ../nlp2dsl && cp .env.example .env && docker compose up -d
# backend: http://localhost:8010, NLP service: http://localhost:8012
# albo z mullm:
docker compose --profile core --profile nlp2dsl up -d
```

Web: http://localhost:3003 — domyślnie pełny ekran chatu. **◎** otwiera listę ticketów ze statusami kolorem.

## Przepływ

1. Piszesz: „lista plików” / „uruchom ls -la” / „wyślij fakturę 1500 PLN”
2. nlp2dsl → `in_progress` + formularz (jeden przycisk **Wyślij odpowiedź**)
3. Gdy `ready`:
   - `system_file_list` → lista z Mullm Access/RAG
   - `mullm_shell_task` / `run …` → ticket + agent shell
   - inne akcje → komunikat (worker nlp2dsl)

Bez nlp2dsl: fallback RAG + lokalne dopytywanie o shell.

## Akcje Mullm w nlp2dsl

Dodaj do `nlp2dsl/nlp-service/app/registry.py` (lub import `integrations/nlp2dsl/mullm_registry.py`):

- `mullm_shell_task` — wymaga `shell_command`
- `mullm_create_ticket` — tylko kolejka

## API

- `POST /api/chat/message` — `{ message, form_values? }`
- `form_values` wypełnia brakujące pola bez ponownego pisania w czacie
