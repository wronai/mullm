-- Observability / incident management (MVP)

create table if not exists incidents (
    incident_id text primary key,
    correlation_id text,
    retrieval_trace_id text,
    chat_session_id text,
    incident_code text not null,
    severity text not null default 'warning',
    component text not null default 'rag',
    service text not null default 'orchestrator',
    message text not null,
    diagnostics jsonb,
    remediation jsonb,
    status text not null default 'open',
    fallback_taken text,
    created_at timestamptz not null default now(),
    resolved_at timestamptz
);

create index if not exists idx_incidents_correlation on incidents(correlation_id);
create index if not exists idx_incidents_code on incidents(incident_code);
create index if not exists idx_incidents_created on incidents(created_at desc);

-- incident_feed: see 006_incidents.sql (projector aggregate view)

create table if not exists rag_health_snapshots (
    snapshot_id text primary key,
    retrieval_trace_id text,
    correlation_id text,
    status text not null,
    checks jsonb not null,
    created_at timestamptz not null default now()
);
