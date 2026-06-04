# Mullm chat routing — propact smoke

Sprawdza żywy BFF Mullm (domyślnie `http://127.0.0.1:3003`).

## Health

GET /health — Mullm web is alive

```json
{}
```

## Agents

GET /api/agents/status — list plugin agents nlp2cmd and nlp2dsl health

## Routing policy

GET /api/routing/policy — ingress must include agent_shell step

## Dry-run: file list (not shell)

GET /api/router/decide?message=lista%20plikow%20usera&use_rag=false — route must be mullm_file_list

## Dry-run: shell prefix

GET /api/router/decide?message=run%20ls%20-la%20~&use_rag=false — route must be mullm_shell

## Session

POST /api/chat/session — create workspace session

```json
{}
```

## Chat: file list registry

POST /api/chat/message — lista plikow usera uses registry not shell

```json
{
  "session_id": "${SESSION_ID}",
  "message": "lista plikow usera",
  "mode": "discuss",
  "use_rag": false
}
```
