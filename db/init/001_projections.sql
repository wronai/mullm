create table if not exists events (
  id bigserial primary key,
  event_id text not null unique,
  stream_id text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  event_type text not null,
  revision integer not null,
  occurred_at timestamptz not null,
  causation_id text,
  correlation_id text,
  payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  unique (stream_id, revision)
);

create index if not exists idx_events_stream_revision
  on events (stream_id, revision);

create index if not exists idx_events_aggregate
  on events (aggregate_type, aggregate_id);

create index if not exists idx_events_occurred_at
  on events (occurred_at);

create table if not exists operational_feed (
  id bigserial primary key,
  event_id text not null unique,
  stream_id text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  event_type text not null,
  occurred_at timestamptz not null,
  correlation_id text,
  causation_id text,
  actor_type text,
  actor_id text,
  title text,
  summary text,
  payload jsonb not null default '{}'::jsonb
);

create index if not exists idx_operational_feed_occurred_at
  on operational_feed (occurred_at desc);

create table if not exists task_board (
  task_id text primary key,
  flow_id text,
  title text not null,
  status text not null,
  priority text not null default 'medium',
  execution_mode text not null default 'semi_auto',
  assigned_agent_id text,
  assigned_human_id text,
  required_capabilities jsonb not null default '[]'::jsonb,
  last_event_type text,
  result jsonb not null default '{}'::jsonb,
  error text,
  updated_at timestamptz not null,
  created_at timestamptz not null
);

create index if not exists idx_task_board_status_priority
  on task_board (status, priority, updated_at desc);

create table if not exists agent_fleet (
  agent_id text primary key,
  machine_id text,
  agent_type text not null,
  status text not null,
  capabilities jsonb not null default '[]'::jsonb,
  current_task_id text,
  heartbeat_at timestamptz,
  load_score integer not null default 0,
  updated_at timestamptz not null
);

create index if not exists idx_agent_fleet_status
  on agent_fleet (status, updated_at desc);

create table if not exists workflow_versions (
  workflow_id text not null,
  version integer not null,
  status text not null,
  definition jsonb not null,
  proposed_at timestamptz not null,
  activated_at timestamptz,
  primary key (workflow_id, version)
);

create table if not exists approval_requests (
  approval_id text primary key,
  action_type text not null,
  target_id text not null,
  risk_level text not null default 'medium',
  requested_by text not null,
  status text not null,
  approved_by text,
  rejected_by text,
  reject_reason text,
  updated_at timestamptz not null,
  created_at timestamptz not null
);

create index if not exists idx_approval_requests_status
  on approval_requests (status, updated_at desc);

create table if not exists plugin_catalog (
  plugin_id text not null,
  version text not null,
  status text not null,
  capabilities jsonb not null default '[]'::jsonb,
  manifest jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null,
  primary key (plugin_id, version)
);

create index if not exists idx_plugin_catalog_status
  on plugin_catalog (status, updated_at desc);
