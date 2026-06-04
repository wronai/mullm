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
