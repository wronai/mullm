-- Incident management / autonomous observability MVP

create table if not exists incident_feed (
    incident_id text primary key,
    incident_type text not null default '',
    incident_class text not null default '',
    severity text not null default 'warning',
    source text not null default '',
    error_code text not null default '',
    message text not null default '',
    status text not null default 'detected',
    playbook_id text,
    root_cause text,
    correlation_id text,
    context jsonb not null default '{}'::jsonb,
    diagnostics jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_incident_feed_status
  on incident_feed (status, updated_at desc);

create index if not exists idx_incident_feed_error_code
  on incident_feed (error_code, updated_at desc);

create table if not exists service_health (
    service_id text primary key,
    component text not null default '',
    status text not null,
    error_code text,
    details jsonb not null default '{}'::jsonb,
    last_check_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists remediation_history (
    id bigserial primary key,
    incident_id text not null,
    playbook_id text not null,
    action text,
    status text not null,
    result jsonb not null default '{}'::jsonb,
    error text,
    started_at timestamptz,
    finished_at timestamptz,
    updated_at timestamptz not null default now()
);

create index if not exists idx_remediation_history_incident
  on remediation_history (incident_id, updated_at desc);

create table if not exists rag_quality_board (
    error_code text primary key,
    failure_count integer not null default 0,
    last_query text,
    last_message text,
    last_failure_at timestamptz,
    updated_at timestamptz not null default now()
);
