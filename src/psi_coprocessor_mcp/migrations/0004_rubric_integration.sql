ALTER TABLE anchors ADD COLUMN durability_class TEXT NOT NULL DEFAULT 'PROVISIONAL';
ALTER TABLE hypotheses ADD COLUMN durability_class TEXT NOT NULL DEFAULT 'PROVISIONAL';

CREATE TABLE IF NOT EXISTS typed_claims (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    statement TEXT NOT NULL,
    provenance_tag TEXT NOT NULL,
    load_bearing INTEGER NOT NULL DEFAULT 0,
    structural_role TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'provisional',
    durability_class TEXT NOT NULL DEFAULT 'UNKNOWN',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    notes_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS compliance_reports (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES runs(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    blocking INTEGER NOT NULL DEFAULT 0,
    requested_action TEXT NOT NULL DEFAULT '',
    issues_json TEXT NOT NULL DEFAULT '[]',
    checked_artifacts_json TEXT NOT NULL DEFAULT '[]',
    notes_json TEXT NOT NULL DEFAULT '[]',
    checked_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_typed_claims_run_id ON typed_claims(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_typed_claims_project_id ON typed_claims(project_id, updated_at DESC);
