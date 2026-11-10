-- Atlas development schema, rebuilt into every store whose recorded schema
-- text differs from this file's, until stage 4 freezes it into
-- migrations/0001_baseline.sql. Tables arrive with the commands that first use
-- them. Times are UTC ISO-8601 text ("2026-11-10T12:00:00+00:00"), so text
-- order is time order.

-- One row per stored source. key_link is the cleaned link the reader reported
-- after redirects (the cleaned given link when it reported none). Identity
-- columns are set when the source is stored; the summary columns are the
-- summary's. unchangeable and escalated are 0 or 1. Archive sets archived_at.
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    key_link TEXT NOT NULL UNIQUE,
    title TEXT,
    author TEXT,
    author_aliases TEXT,
    publisher TEXT,
    platform TEXT,
    published TEXT,
    kind TEXT NOT NULL,
    unchangeable INTEGER NOT NULL CHECK (unchangeable IN (0, 1)),
    scope_choice TEXT,
    read_share REAL,
    first_seen TEXT NOT NULL,
    last_read TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    text_origin TEXT NOT NULL CHECK (text_origin IN ('read', 'agent')),
    abstract TEXT,
    rubric_version TEXT,
    model TEXT,
    thinking TEXT,
    escalated INTEGER CHECK (escalated IN (0, 1)),
    rethink_line TEXT,
    dropped_claims INTEGER,
    support_status TEXT,
    copies_status TEXT,
    topics_status TEXT,
    archived_at TEXT
);
CREATE INDEX sources_by_hash ON sources (content_hash);

-- Every cleaned link that led to a source: its key link, the other links that
-- were joined to it, and the repo a picked item came from.
CREATE TABLE links (
    link TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources (id),
    kind TEXT NOT NULL CHECK (kind IN ('key', 'other', 'related_repo')),
    added_at TEXT NOT NULL
);
CREATE INDEX links_by_source ON links (source_id);

-- The cleaned page text of each source, zlib-compressed and never searched,
-- with each image's SHA-256 in page order (space-separated hex, empty for none)
-- and the text's 64-value MinHash (64 little-endian uint32).
CREATE TABLE page_text (
    source_id INTEGER PRIMARY KEY REFERENCES sources (id),
    text BLOB NOT NULL,
    image_hashes TEXT NOT NULL,
    minhash BLOB NOT NULL CHECK (length(minhash) = 256)
);

-- Links kept for later, unsummarized; a link leaves once a source holds it.
CREATE TABLE inbox (
    link TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    origin TEXT NOT NULL
);

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
