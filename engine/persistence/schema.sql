CREATE TABLE IF NOT EXISTS dataset (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

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
    scores JSONB NOT NULL,
    passed BOOLEAN NOT NULL,
    failure_reason TEXT
);
