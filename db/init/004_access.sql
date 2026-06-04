create table if not exists resource_registry (
  resource_id text primary key,
  uri text not null unique,
  name text not null,
  adapter text not null,
  classification text not null default 'document',
  status text not null,
  metadata jsonb not null default '{}'::jsonb,
  last_transfer_id text,
  updated_at timestamptz not null,
  created_at timestamptz not null
);

create index if not exists idx_resource_registry_adapter
  on resource_registry (adapter, status);

create table if not exists transfer_log (
  transfer_id text primary key,
  resource_id text not null,
  source_uri text not null,
  destination_uri text not null,
  status text not null,
  requested_by text,
  outcome jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null,
  completed_at timestamptz
);

create index if not exists idx_transfer_log_resource
  on transfer_log (resource_id, started_at desc);
