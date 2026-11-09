-- Atlas development schema, rebuilt into every store whose recorded schema
-- text differs from this file's, until stage 4 freezes it into
-- migrations/0001_baseline.sql. Tables arrive with the commands that first use
-- them. Times are UTC ISO-8601 text ("2026-11-10T12:00:00+00:00"), so text
-- order is time order.

-- One row per paid call. Cost kind billed: the provider's bill; estimated: the
-- price table's list price; unknown: no price row, so no dollar amount.
CREATE TABLE calls (
    id INTEGER PRIMARY KEY,
    at TEXT NOT NULL,
    command TEXT NOT NULL,
    role TEXT NOT NULL,
    model TEXT NOT NULL,
    thinking TEXT,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cache_read INTEGER NOT NULL,
    cache_write INTEGER NOT NULL,
    cost_usd REAL,
    cost_kind TEXT NOT NULL CHECK (cost_kind IN ('billed', 'estimated', 'unknown')),
    CHECK ((cost_kind = 'unknown') = (cost_usd IS NULL))
);
CREATE INDEX calls_by_time ON calls (at);
CREATE INDEX calls_by_role ON calls (role, at);

-- One row per applied change. by: request (the user's own words), confirm (the
-- user's answer to a decision) or never (the change's confirm setting is never).
CREATE TABLE approvals (
    id INTEGER PRIMARY KEY,
    at TEXT NOT NULL,
    command TEXT NOT NULL,
    change_kind TEXT NOT NULL,
    by TEXT NOT NULL CHECK (by IN ('request', 'confirm', 'never')),
    words TEXT,
    decision_id TEXT
);
