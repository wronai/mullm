create table if not exists capability_registry (
  capability_id text primary key,
  kind text not null default 'runtime',
  description text,
  provided_by jsonb not null default '[]'::jsonb,
  risk_level text not null default 'medium',
  status text not null default 'active',
  manifest jsonb not null default '{}'::jsonb,
  source text not null default 'catalog',
  updated_at timestamptz not null
);

create table if not exists evolution_metrics (
  id bigserial primary key,
  subject_type text not null,
  subject_id text not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  sample_count integer not null default 0,
  success_count integer not null default 0,
  failure_count integer not null default 0,
  retry_count integer not null default 0,
  human_takeover_count integer not null default 0,
  rollback_count integer not null default 0,
  total_duration_ms bigint not null default 0,
  success_rate double precision not null default 0,
  human_takeover_rate double precision not null default 0,
  median_duration_ms double precision not null default 0,
  updated_at timestamptz not null,
  unique (subject_type, subject_id, window_start)
);

create index if not exists idx_evolution_metrics_subject
  on evolution_metrics (subject_type, subject_id, updated_at desc);

create table if not exists experiments (
  experiment_id text primary key,
  subject_type text not null,
  subject_id text not null,
  version text not null,
  mode text not null,
  traffic_percent integer not null default 0,
  status text not null,
  outcome text,
  metrics jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  started_at timestamptz not null,
  completed_at timestamptz
);

create index if not exists idx_experiments_subject
  on experiments (subject_type, subject_id, status);

create table if not exists change_proposals (
  change_id text primary key,
  change_type text not null,
  target_id text not null,
  status text not null,
  hypothesis text,
  proposed_by text not null,
  payload jsonb not null default '{}'::jsonb,
  evaluation jsonb not null default '{}'::jsonb,
  created_at timestamptz not null,
  updated_at timestamptz not null
);
