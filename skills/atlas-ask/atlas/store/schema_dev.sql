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

-- Every cleaned link that led to a source: its key link and the other links
-- that were joined to it.
CREATE TABLE links (
    link TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources (id),
    kind TEXT NOT NULL CHECK (kind IN ('key', 'other')),
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

-- One row per claim, recommendation or caveat of a source's summary, in
-- summary order (ord). A re-read that revises or removes a claim sets its
-- replaced_at; a revised claim is a new row, so unchanged claims keep their id.
CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources (id),
    ord INTEGER NOT NULL,
    section TEXT NOT NULL CHECK (section IN ('claim', 'recommendation', 'caveat')),
    text TEXT NOT NULL,
    basis TEXT NOT NULL CHECK (basis IN ('measured', 'demonstrated', 'cited', 'asserted')),
    created_at TEXT NOT NULL,
    replaced_at TEXT
);
CREATE INDEX claims_by_source ON claims (source_id, replaced_at, ord);

-- Each claim's 1-3 quotes, copied word for word from the page, with the
-- character span [start, end) where code found each in the stored page text.
CREATE TABLE quotes (
    claim_id INTEGER NOT NULL REFERENCES claims (id),
    ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    start INTEGER NOT NULL,
    "end" INTEGER NOT NULL,
    PRIMARY KEY (claim_id, ord)
);

-- The judge's claim-support answer for a claim: the likeliest verdict, p the
-- probability of "supports" (the mean when asked twice), flagged when p is
-- under 0.8, and the judge model version that answered.
CREATE TABLE claim_flags (
    claim_id INTEGER PRIMARY KEY REFERENCES claims (id),
    verdict TEXT NOT NULL CHECK (verdict IN ('supports', 'contradicts', 'says nothing')),
    p REAL NOT NULL,
    flagged INTEGER NOT NULL CHECK (flagged IN (0, 1)),
    judge_model TEXT NOT NULL,
    at TEXT NOT NULL
);

-- Links related to a source. origin page: the page presents the link as its
-- source or next reading. origin expansion: the source is an item or link of
-- that page, added under an expanding choice (see expansions); it replaces a
-- page row for the same link.
CREATE TABLE related_links (
    source_id INTEGER NOT NULL REFERENCES sources (id),
    link TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('page', 'expansion')),
    PRIMARY KEY (source_id, link)
);
CREATE INDEX related_links_by_link ON related_links (link, origin);

-- The expanding choice the user made for a page link (the cleaned link the
-- user named): each item of a repo, each link of a link list, or both the page
-- and its items. The sources it produced are the related_links rows of origin
-- expansion for that link.
CREATE TABLE expansions (
    link TEXT PRIMARY KEY,
    choice TEXT NOT NULL CHECK (choice IN ('each_item', 'each_link', 'both')),
    at TEXT NOT NULL
);

-- The judge's answer whether another stored source is the same work: p the
-- probability, flagged at 0.5 or more, and the judge model version.
CREATE TABLE copy_flags (
    source_id INTEGER NOT NULL REFERENCES sources (id),
    other_source_id INTEGER NOT NULL REFERENCES sources (id),
    p REAL NOT NULL,
    flagged INTEGER NOT NULL CHECK (flagged IN (0, 1)),
    judge_model TEXT NOT NULL,
    at TEXT NOT NULL,
    PRIMARY KEY (source_id, other_source_id)
);

-- One row each time a summary is written or revised.
CREATE TABLE summary_history (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources (id),
    at TEXT NOT NULL,
    event TEXT NOT NULL CHECK (event IN ('added', 'reread', 'redone', 'redo_failed')),
    rubric_version TEXT NOT NULL,
    model TEXT NOT NULL,
    escalated INTEGER NOT NULL CHECK (escalated IN (0, 1))
);
CREATE INDEX summary_history_by_source ON summary_history (source_id, at);

-- BM25 search over each source's title, abstract and current claims; the
-- rowid is the source id.
CREATE VIRTUAL TABLE source_fts USING fts5 (title, abstract, claims);

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

-- One row per find and ask: the user's original words, the agent's
-- self-contained question, the phrasings searched (JSON array of text: the
-- agent's, the rewrites, or the question when the rewrite failed), the context,
-- the ranker that ordered the result (jev, atlas_rerank, or bm25 when both
-- failed), each Jev answer as a JSON array of {link, p, model} (NULL when Jev
-- did not rank), and the fallback notes the reply gave.
CREATE TABLE queries (
    id INTEGER PRIMARY KEY,
    at TEXT NOT NULL,
    op TEXT NOT NULL CHECK (op IN ('find', 'ask')),
    original TEXT NOT NULL,
    question TEXT NOT NULL,
    phrasings TEXT NOT NULL,
    context TEXT,
    ranker TEXT NOT NULL CHECK (ranker IN ('jev', 'atlas_rerank', 'bm25')),
    judge_records TEXT,
    note TEXT
);

-- Trust-evidence lines an answer gave, stored without a stop: who (an author
-- or publisher), the subject, the source link that shows it, and the direction
-- (towards or against). proposed_at is set when a note proposal used the line.
CREATE TABLE tally (
    id INTEGER PRIMARY KEY,
    who TEXT NOT NULL,
    subject TEXT NOT NULL,
    link TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('towards', 'against')),
    at TEXT NOT NULL,
    proposed_at TEXT
);
CREATE INDEX tally_by_pair ON tally (who, subject, proposed_at);
