-- RAG Fabric (Sprint 6)

create table if not exists rag_documents (
    resource_id text primary key,
    uri text not null,
    name text not null default '',
    classification text not null default 'document',
    status text not null default 'pending',
    chunk_count int not null default 0,
    embedding_model text,
    error text,
    indexed_at timestamptz,
    updated_at timestamptz not null default now()
);

create table if not exists rag_chunks (
    chunk_id text primary key,
    resource_id text not null references rag_documents(resource_id) on delete cascade,
    position int not null,
    content text not null,
    embedding jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_rag_chunks_resource on rag_chunks(resource_id);
create index if not exists idx_rag_documents_status on rag_documents(status);

create index if not exists idx_rag_chunks_fts on rag_chunks
    using gin (to_tsvector('english', content));
