# Integracje Mullm (pluginy agentów)

Każdy katalog to **manifest + dokumentacja**; kod mostu HTTP: `services/web/app/agent_plugins/`.

| Katalog | Usługa Docker? | Rola |
|---------|----------------|------|
| `nlp2cmd/` | **Tak** (`profile nlp2cmd`) | NL → polecenie shell → ticket `shell_agent` |
| `nlp2dsl/` | **Tak** (profil `nlp2dsl`) | Workflow / DSL → `coordinator` |

Narzędzia **bez** kontenera: intract (`intract.yaml`), propact (`tests/pacts/`, `scripts/run-propact-pact.sh`).

Architektura: [docs/architecture-service-integrations.md](../docs/architecture-service-integrations.md)
