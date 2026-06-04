# Observability (MVP)

Warstwa **Poziom 1–2**: structured logs, correlation IDs, klasyfikacja incydentów RAG, diagnostyka, feed zdarzeń.

## Przepływ RAG

1. `RagRequestStarted` → diagnostyka (opcjonalnie) → wyszukiwanie → odpowiedź lub incydent
2. Każde `/api/rag/ask` dostaje `retrieval_trace_id` i `X-Correlation-ID`
3. Błędy mapowane na kody: `RAG_BACKEND_UNAVAILABLE`, `LLM_UNAVAILABLE`, `RETRIEVER_EMPTY_RESULT`, …

## API

| Endpoint | Opis |
|----------|------|
| `GET /api/observability/health/rag` | Healthcheck pipeline (postgres, indeks, OpenRouter, embedding) |
| `POST /api/observability/rag/diagnose` | Diagnostyka z opcjonalnym `query` |
| `GET /api/observability/incidents` | Ostatnie incydenty |

## SQL

```bash
docker exec -i mullm-postgres-1 psql -U mullm -d mullm < db/init/006_observability.sql
```

## UI

Workspace chat pokazuje `[KOD — message — trace=…]` zamiast samego „RAG niedostępny (500)”.

### Kopiowanie logów do schowka

1. **Workspace** — przycisk **„Kopiuj logi”** w górnym pasku (lub **„Kopiuj”** przy Live events).
2. API: `GET /api/workspace/logs/export?session_id=<uuid>&limit=40` → pole `text` (plain text + JSON na końcu).
3. Orchestrator bezpośrednio: `GET /api/observability/logs/export?correlation_id=<session_id>`.

Przykład z konsoli przeglądarki (F12):

```javascript
const sid = localStorage.getItem('mullm_workspace_session');
const r = await fetch(`/api/workspace/logs/export?session_id=${sid}`);
const { text } = await r.json();
await navigator.clipboard.writeText(text);
```

Wymaga HTTPS lub `localhost` — inaczej przeglądarka może zablokować `clipboard` (UI ma fallback `execCommand`).

## Kolejne kroki (Poziom 3)

- Auto-remediacja: restart smoke, reindex ostatnich zasobów
- Weryfikacja po naprawie (`PostRemediationVerificationPassed`)
- Docker stack (Loki/Prometheus) — opcjonalnie
