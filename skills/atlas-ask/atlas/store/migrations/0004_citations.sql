-- Atlas migration 0004: repo citations (stage 8).
-- Frozen once shipped: a later schema change is the next numbered migration,
-- never an edit here. Times are UTC ISO-8601 text. Archive sets archived_at;
-- nothing is deleted.

-- One row per fact "this file of this repo relied on this": a source (source_id)
-- or one saved version of a topic (topic_id and n), never both and never
-- neither. repo is the owner/name of the citing repo, file its repo-root-relative
-- path and at the time the row was written. A later add for the same repo and
-- file archives the file's earlier rows (archived_at) instead of deleting them.
CREATE TABLE citations (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES sources (id),
    topic_id INTEGER,
    n INTEGER,
    repo TEXT NOT NULL,
    file TEXT NOT NULL,
    at TEXT NOT NULL,
    archived_at TEXT,
    CHECK (
        (source_id IS NOT NULL AND topic_id IS NULL AND n IS NULL)
        OR (source_id IS NULL AND topic_id IS NOT NULL AND n IS NOT NULL)
    ),
    FOREIGN KEY (topic_id, n) REFERENCES versions (topic_id, n)
);
CREATE INDEX citations_by_file ON citations (repo, file);
