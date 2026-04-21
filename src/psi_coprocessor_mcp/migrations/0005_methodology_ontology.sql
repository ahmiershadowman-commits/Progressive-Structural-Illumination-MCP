CREATE TABLE IF NOT EXISTS source_objects (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    source_kind TEXT NOT NULL,
    title TEXT NOT NULL,
    locator TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    canonical INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS primitive_components (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    component_kind TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_variables (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    variable_kind TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL DEFAULT '',
    timescale TEXT NOT NULL DEFAULT '',
    write_roles_json TEXT NOT NULL DEFAULT '[]',
    read_roles_json TEXT NOT NULL DEFAULT '[]',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS primitive_operators (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    family TEXT NOT NULL,
    object_ref TEXT NOT NULL DEFAULT '',
    state_variable_ref TEXT NOT NULL DEFAULT '',
    trigger_text TEXT NOT NULL DEFAULT '',
    direct_action TEXT NOT NULL DEFAULT '',
    target TEXT NOT NULL DEFAULT '',
    changes_json TEXT NOT NULL DEFAULT '[]',
    cannot_do_json TEXT NOT NULL DEFAULT '[]',
    where_text TEXT NOT NULL DEFAULT '',
    when_text TEXT NOT NULL DEFAULT '',
    directionality TEXT NOT NULL DEFAULT '',
    timescale TEXT NOT NULL DEFAULT '',
    persistence TEXT NOT NULL DEFAULT '',
    reversibility TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS interlocks (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'provisional',
    scope TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trace_steps (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    cascade_id TEXT NOT NULL DEFAULT '',
    step_index INTEGER NOT NULL DEFAULT 0,
    branch_key TEXT NOT NULL DEFAULT '',
    operator_ref TEXT NOT NULL DEFAULT '',
    from_state TEXT NOT NULL DEFAULT '',
    to_state TEXT NOT NULL DEFAULT '',
    trigger_text TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    divergence_class TEXT,
    blocking INTEGER NOT NULL DEFAULT 0,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gap_records (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    gap_type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    likely_origin TEXT NOT NULL,
    nearly_covers_json TEXT NOT NULL DEFAULT '[]',
    insufficient_because TEXT NOT NULL DEFAULT '',
    dissolved_by_json TEXT NOT NULL DEFAULT '[]',
    discriminator TEXT NOT NULL DEFAULT '',
    blocking INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'OPEN',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_records (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    target_object TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    findings_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS basin_records (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    basin_type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'OPEN',
    preserves_json TEXT NOT NULL DEFAULT '[]',
    conflicts_json TEXT NOT NULL DEFAULT '[]',
    discriminator TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skeptic_findings (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    claim_ref TEXT NOT NULL DEFAULT '',
    question TEXT NOT NULL,
    impact TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'warning',
    blocking INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS antipattern_findings (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pattern_type TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    severity TEXT NOT NULL DEFAULT 'warning',
    blocking INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_objects_run_id ON source_objects(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_primitive_components_run_id ON primitive_components(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_state_variables_run_id ON state_variables(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_primitive_operators_run_id ON primitive_operators(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_interlocks_run_id ON interlocks(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_trace_steps_run_id ON trace_steps(run_id, step_index ASC, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_gap_records_run_id ON gap_records(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_records_run_id ON search_records(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_basin_records_run_id ON basin_records(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_skeptic_findings_run_id ON skeptic_findings(run_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_antipattern_findings_run_id ON antipattern_findings(run_id, updated_at DESC);
