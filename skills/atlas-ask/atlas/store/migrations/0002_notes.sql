-- Atlas migration 0002: trust notes (stage 6). Frozen once shipped: a later
-- schema change is the next numbered migration, never an edit here.

-- One row per trust note: who (an author or a publisher), the subject (free
-- text), the lean (towards or against), the reason, and when it was saved or
-- last changed (UTC ISO-8601 text). One unarchived note is held per who and
-- subject (trimmed, compared case-insensitively); changing it updates its
-- row in place. Archive sets archived_at; nothing is deleted.
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    who TEXT NOT NULL,
    subject TEXT NOT NULL,
    lean TEXT NOT NULL CHECK (lean IN ('towards', 'against')),
    reason TEXT NOT NULL,
    at TEXT NOT NULL,
    archived_at TEXT
);
CREATE INDEX notes_by_pair ON notes (who, subject);
