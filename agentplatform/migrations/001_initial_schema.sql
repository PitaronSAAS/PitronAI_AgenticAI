-- PitronAgent Platform — Initial Schema
-- Run once in your Supabase SQL editor

-- ── Extensions ────────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";
create extension if not exists vector;          -- pgvector for semantic FAQ search

-- ── Tenants (each paying client is one tenant) ───────────────────────────────
create table tenants (
    id              uuid primary key default uuid_generate_v4(),
    name            varchar(120) not null,
    slug            varchar(80)  not null unique,     -- used in widget URL, URL-safe
    api_key         varchar(80)  not null unique,     -- "pak_" + 32 hex chars
    plan            varchar(20)  not null default 'starter',  -- starter | pro | enterprise
    stripe_customer_id  varchar(40),
    stripe_sub_id       varchar(40),
    status          varchar(20)  not null default 'active',   -- active | suspended | cancelled
    allowed_origins text[]       not null default '{}',       -- CORS whitelist
    created_at      timestamptz  not null default now(),
    updated_at      timestamptz  not null default now()
);
create index idx_tenants_api_key on tenants(api_key);
create index idx_tenants_slug    on tenants(slug);

-- ── Agent configuration (one per tenant) ─────────────────────────────────────
create table agent_configs (
    id               uuid primary key default uuid_generate_v4(),
    tenant_id        uuid not null references tenants(id) on delete cascade,
    agent_name       varchar(80)  not null default 'Assistant',
    persona_prompt   text         not null default 'You are a helpful business assistant.',
    primary_color    varchar(7)   not null default '#6366f1',
    welcome_message  text         not null default 'Hi! How can I help you today?',
    business_info    jsonb        not null default '{}',   -- hours, address, phone, etc.
    tools_enabled    text[]       not null default array['search_knowledge_base','capture_lead','get_business_info'],
    escalation_email varchar(200),
    max_turns        smallint     not null default 20,
    created_at       timestamptz  not null default now(),
    updated_at       timestamptz  not null default now(),
    unique(tenant_id)
);

-- ── Knowledge base (FAQ entries per tenant) ───────────────────────────────────
create table knowledge_entries (
    id          uuid primary key default uuid_generate_v4(),
    tenant_id   uuid not null references tenants(id) on delete cascade,
    category    varchar(80),
    question    text not null,
    answer      text not null,
    keywords    text[] not null default '{}',
    embedding   vector(1536),           -- populated async after insert/update
    is_active   boolean not null default true,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);
create index idx_knowledge_tenant   on knowledge_entries(tenant_id) where is_active = true;
create index idx_knowledge_keywords on knowledge_entries using gin(keywords);
-- ivfflat index (run after data exists): CREATE INDEX CONCURRENTLY idx_knowledge_vec
-- on knowledge_entries using ivfflat (embedding vector_cosine_ops) with (lists=50);

-- ── Conversations ─────────────────────────────────────────────────────────────
create table conversations (
    id             uuid primary key default uuid_generate_v4(),
    tenant_id      uuid not null references tenants(id) on delete cascade,
    session_id     varchar(64) not null,
    started_at     timestamptz not null default now(),
    last_activity  timestamptz not null default now(),
    turn_count     smallint not null default 0,
    is_escalated   boolean not null default false,
    metadata       jsonb default '{}'       -- page_url, referrer
);
create index idx_conv_session  on conversations(tenant_id, session_id);
create index idx_conv_activity on conversations(tenant_id, last_activity desc);

-- ── Messages ──────────────────────────────────────────────────────────────────
create table messages (
    id              uuid primary key default uuid_generate_v4(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    role            varchar(12) not null check (role in ('user','assistant')),
    content         text not null,
    created_at      timestamptz not null default now()
);
create index idx_messages_conv on messages(conversation_id, created_at asc);

-- ── Leads captured by the agent ───────────────────────────────────────────────
create table leads (
    id              uuid primary key default uuid_generate_v4(),
    tenant_id       uuid not null references tenants(id) on delete cascade,
    conversation_id uuid references conversations(id) on delete set null,
    name            varchar(120),
    email           varchar(200) not null,
    phone           varchar(30),
    interest_notes  text,
    source_page     text,
    status          varchar(20) not null default 'new',   -- new | contacted | qualified | closed
    created_at      timestamptz not null default now()
);
create index idx_leads_tenant on leads(tenant_id, created_at desc);
create index idx_leads_email  on leads(tenant_id, email);
