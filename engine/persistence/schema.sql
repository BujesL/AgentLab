CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunk (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL
);

-- No ivfflat/hnsw index: an approximate index needs a dataset large enough to
-- train its clusters (ivfflat's default lists=100 on a handful of rows returns
-- near-random neighbors — confirmed empirically during T-pipeline validation, see
-- docs/specs/rag-pipeline/tasks.md). Exact brute-force <=> scan is correct and
-- fast enough at the MVP's dataset sizes; adding an approximate index is a later
-- decision to make once real document volume justifies it.
DROP INDEX IF EXISTS document_chunk_embedding_idx;

CREATE TABLE IF NOT EXISTS dataset (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS agent (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS agent_version (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    code_ref TEXT NOT NULL DEFAULT '',
    UNIQUE (agent_id, version)
);

CREATE TABLE IF NOT EXISTS prompt_version (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS experiment (
    id TEXT PRIMARY KEY,
    agent_version_id TEXT NOT NULL REFERENCES agent_version(id) ON DELETE CASCADE,
    dataset_id TEXT NOT NULL,
    model TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'running',
    prompt_version_id TEXT REFERENCES prompt_version(id) ON DELETE SET NULL
);

ALTER TABLE experiment ADD COLUMN IF NOT EXISTS prompt_version_id TEXT
    REFERENCES prompt_version(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS trace (
    id UUID PRIMARY KEY,
    experiment_id TEXT,
    case_id TEXT NOT NULL,
    started_at DOUBLE PRECISION NOT NULL,
    duration_ms DOUBLE PRECISION NOT NULL,
    token_usage INTEGER,
    cost DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS trace_event (
    id SERIAL PRIMARY KEY,
    trace_id UUID NOT NULL REFERENCES trace(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    UNIQUE (trace_id, sequence)
);

CREATE TABLE IF NOT EXISTS evaluation_result (
    id SERIAL PRIMARY KEY,
    case_id TEXT NOT NULL,
    trace_id UUID REFERENCES trace(id) ON DELETE SET NULL,
    experiment_id TEXT REFERENCES experiment(id) ON DELETE SET NULL,
    scores JSONB NOT NULL,
    passed BOOLEAN NOT NULL,
    failure_reason TEXT
);

ALTER TABLE evaluation_result ADD COLUMN IF NOT EXISTS experiment_id TEXT
    REFERENCES experiment(id) ON DELETE SET NULL;
