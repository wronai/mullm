# Mullm — roadmap 30/60/90 dni

Zasada: **najpierw zdarzenia i granice domen, potem zasoby/RAG, potem autonomia zmian** (controlled evolution).

## Dni 1–30 — fundament

| Sprint | Cel | Rezultat |
|--------|-----|----------|
| S1 | Event storming, bounded contexts | Mapa domen + backlog |
| S2 | Compose `core`, kontrakty eventów | Stack + envelope |
| S3 | Pilot Task → Agent → Outcome | E2E w read modelu |

**Stan w repo:** S2–S3 w dużej mierze zrealizowane (agregaty, projections, shell agents).

```bash
docker compose --profile core up -d
```

## Dni 31–60 — operacyjna platforma

| Sprint | Cel | Rezultat |
|--------|-----|----------|
| S4 | Resource + URI | `mullm://` registry |
| S5 | Access Fabric MVP | transport + adaptery |
| S6 | RAG ingest | indexer + retrieval |

**Stan w repo (S4–S5 MVP):**
- URI `mullm://{adapter}/{path}` — localfs, http/https
- `TransportService` — probe, fetch, copy
- `RegisterResource`, `RequestTransfer` + eventy + projection `resource_registry`
- API: `/api/access/*`, `GET /projections/resources`

```bash
docker compose --profile access up -d
```

## Dni 61–90 — evolution control plane

| Sprint | Cel | Rezultat |
|--------|-----|----------|
| S7 | Workflow registry + shadow | Wersjonowane workflowy |
| S8 | Capability + plugin manifests | Capability registry |
| S9 | Evaluation + eksperymenty | Metryki + canary/rollback |

**Stan w repo (S7–S9 MVP):**
- `catalog/` — samopiszący katalog (events, capabilities, policies, services)
- `app/evolution/` — policy engine, evaluation, experiments
- `GET /api/catalog/*`, `GET /api/evolution/*`
- Tabele: `capability_registry`, `evolution_metrics`, `experiments`, `change_proposals`
- `ShadowWorkflowVersion`, `ProposeChange`, `WorkflowVersionShadowed`

```bash
docker compose --profile evolution up -d
# lub pełny stack:
docker compose --profile full up -d
```

## Epiki (backlog)

- **E1** Core Orchestration — task, agent, workflow
- **E2** Event Contracts & Catalog — `catalog/events/*.json`
- **E3** Access Fabric — resource-registry (planned)
- **E4** RAG Fabric — indexer (planned)
- **E5** Workflow Registry — wersjonowanie + shadow
- **E6** Capability/Plugin System — manifesty + registry
- **E7** Evaluation & Observability — `evolution_metrics`
- **E8** Legacy ACL — anti-corruption layer (planned)

## Metryki sukcesu

- % flow przez mullm
- Liczba eventów ze schematem w `catalog/events/`
- Czas command → projection
- `success_rate`, `human_takeover_rate`, `rollback_rate` w `evolution_metrics`
- % zmian workflow z approval + evaluation

## Checklist gotowości

**Po 30 dniach:** 1 pionowy use case, spójne eventy, działanie obok legacy.

**Po 60 dniach:** URI zasobów, pierwszy retrieval, task z dostępem do zasobów.

**Po 90 dniach:** workflowy wersjonowane, capability jawne, ocena i rollback zmian.
