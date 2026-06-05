# Mullm chat routing — propact (referencja)

Użyj **`propact run`**, nie `propact <plik>`.

## Szybki start

```bash
propact run tests/pacts/mullm-health.md \
  --openapi tests/pacts/mullm-openapi.json \
  --base-url http://127.0.0.1:3003 \
  --method GET
```

Pełny scenariusz (sesja + chat + router): `./scripts/run-propact-pact.sh`

## Format bloków

Propact wykonuje tylko sekcje w fence:

```propact:rest
GET /health
```

Dokumentacja scenariuszy (bez bloków) — patrz `scripts/e2e-chat-routing.sh` (curl/jq).
