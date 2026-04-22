ALTER TABLE runs ADD COLUMN run_class TEXT NOT NULL DEFAULT 'exploratory';
ALTER TABLE runs ADD COLUMN current_phase TEXT NOT NULL DEFAULT 'task_contract_scope_lock';
ALTER TABLE runs ADD COLUMN next_gating_condition TEXT NOT NULL DEFAULT '';
ALTER TABLE runs ADD COLUMN last_supersession_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE runs ADD COLUMN applicability_json TEXT NOT NULL DEFAULT '{}';

ALTER TABLE typed_claims ADD COLUMN confidence_axes_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE typed_claims ADD COLUMN scaffold_json TEXT NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_runs_run_class ON runs(run_class, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_current_phase ON runs(current_phase, updated_at DESC);
