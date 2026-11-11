-- Atlas migration 0003: topics, versions, marks and research plans (stage 7).
-- Frozen once shipped: a later schema change is the next numbered migration,
-- never an edit here. Times are UTC ISO-8601 text. Archive sets archived_at;
-- nothing is deleted.

-- One row per topic: its name (unique; the code trims it and compares it
-- case-insensitively before it is stored), the brief that says what it is
-- about, whether the catch-up follows it, the time the user last reviewed it
-- with nothing to save (reviewed_up_to), and the last catch-up's verdict as
-- JSON (new-source ids, the changed flag and the time).
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    brief TEXT NOT NULL,
    followed INTEGER NOT NULL DEFAULT 1 CHECK (followed IN (0, 1)),
    reviewed_up_to TEXT,
    last_catchup TEXT,
    archived_at TEXT
);

-- One row per saved version, numbered per topic from 1: the reviewed text, the
-- model and thinking that wrote the draft, the cross-check status (complete,
-- or "not cross-checked: <reason>"), the reviewers (a JSON list of text), the
-- run, the changes the review made and the diff, as the review gave them.
CREATE TABLE versions (
    topic_id INTEGER NOT NULL REFERENCES topics (id),
    n INTEGER NOT NULL CHECK (n >= 1),
    text TEXT NOT NULL,
    writer_model TEXT,
    thinking TEXT,
    cross_check TEXT NOT NULL CHECK (cross_check = 'complete' OR cross_check LIKE 'not cross-checked: %'),
    reviewers TEXT,
    run TEXT,
    changes TEXT,
    diff TEXT,
    saved_at TEXT NOT NULL,
    PRIMARY KEY (topic_id, n)
);

-- The claims a version cites, copied as they were when it was saved: the text
-- and the quote texts (a JSON list of text). claim_id names the claim the copy
-- was made from, which a redo or re-read may since have replaced, so the source
-- a version cites stays known.
CREATE TABLE version_claims (
    topic_id INTEGER NOT NULL,
    n INTEGER NOT NULL,
    claim_id INTEGER NOT NULL REFERENCES claims (id),
    text TEXT NOT NULL,
    quotes TEXT NOT NULL,
    PRIMARY KEY (topic_id, n, claim_id),
    FOREIGN KEY (topic_id, n) REFERENCES versions (topic_id, n)
);

-- A mark: the judge's answer that a source matters to a topic (p, and the
-- judge's model version), made when the source was added or redone, and
-- cleared when a version is saved or the user picks nothing to save.
CREATE TABLE marks (
    id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics (id),
    source_id INTEGER NOT NULL REFERENCES sources (id),
    p REAL NOT NULL,
    judge_model TEXT NOT NULL,
    at TEXT NOT NULL,
    cleared_at TEXT
);
CREATE INDEX marks_by_topic ON marks (topic_id, cleared_at);

-- One row per reviewed research plan, with the cross-check status, reviewers,
-- run and changes of its review, and one row per plan item: its place, kind
-- (question, search, source or page), text, state (open, done or skipped) and
-- the time that state was set.
CREATE TABLE plans (
    id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics (id),
    text TEXT NOT NULL,
    cross_check TEXT NOT NULL CHECK (cross_check = 'complete' OR cross_check LIKE 'not cross-checked: %'),
    reviewers TEXT,
    run TEXT,
    changes TEXT,
    saved_at TEXT NOT NULL
);
CREATE INDEX plans_by_topic ON plans (topic_id);

CREATE TABLE plan_items (
    plan_id INTEGER NOT NULL REFERENCES plans (id),
    ord INTEGER NOT NULL CHECK (ord >= 1),
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'done', 'skipped')),
    at TEXT NOT NULL,
    PRIMARY KEY (plan_id, ord)
);
