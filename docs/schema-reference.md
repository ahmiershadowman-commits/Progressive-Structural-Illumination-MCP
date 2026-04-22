# Schema Reference

## Run-State Model

The live PSI vector is stored in `PsiRunState`:

- `W`: whole-field representation
- `L`: active lens / legitimacy conditions
- `B`: scope boundaries
- `O`: current visibility event
- `sources`: typed source objects with audit metadata
- `C`: typed claims with provenance and durability class
- `components`: authoritative primitive components
- `state_variables`: authoritative state variables
- `primitive_operators`: authoritative primitive operators
- `interlocks`: relation-edge graph
- `traces`: forward trace / cascade steps
- `gaps`: typed gap-origin records
- `searches`: targeted search plans
- `basins`: competing explanatory / construction basins
- `skeptic_findings`: skeptic-pass findings
- `antipattern_findings`: anti-pattern findings
- `A`: anchored articulations
- `U`: unresolved tensions
- `H`: live hypotheses
- `D`: discriminators
- `F`: friction signals
- `N`: durability / native-minimality assessment
- `P`: candidate probes
- `T`: timescale bands
- `S`: substrate constraints
- `G`: stance geometry
- `applicability`: Phase 0 method-fit boundary
- `current_phase`: active re-entrant regime
- `phase_history`: regime re-entry history
- `next_gating_condition`: next explicit control obligation
- `open_artifacts`: missing or non-authoritative artifact surfaces
- `last_supersession`: latest supersession event, if any
- `smallest_discriminative_unit`: smallest unresolved unit currently targeted

Additional run-state fields:

- schema metadata version (`1.2.0`) in machine-readable exports
- run class metadata (`exploratory | working | canonical`)
- active regimes
- current blast radius
- current sweep status
- current discriminator
- operator families
- control families
- friction routing
- transition
- compliance
- uncertainty

Typed substructures now also carry:

- typed-claim confidence axes (`evidence`, `causal`, `scope`, `representation`)
- optional scaffold-boundary metadata on typed claims and anchors
- hypothesis weakening conditions, discriminator paths, and explanatory burden
- discriminator expected-outcome maps
- gap/search smallest discriminative unresolved units
- basin burden, weakening, and discriminator-path fields

## Persistence Tables

- `projects`
- `runs`
- `visibility_events`
- `coherence_sweeps`
- `anchors`
- `tensions`
- `hypotheses`
- `discriminators`
- `friction_logs`
- `constraints`
- `source_objects`
- `primitive_components`
- `state_variables`
- `primitive_operators`
- `interlocks`
- `trace_steps`
- `gap_records`
- `search_records`
- `basin_records`
- `skeptic_findings`
- `antipattern_findings`
- `typed_claims`
- `compliance_reports`
- `method_memory`
- `user_memory`
- `project_memory`
- `run_memory`
- `artifacts`
- `exports`
- `supersession_history`
- `dead_ends`
- `project_snapshots`
- `retrieval_documents`
- `retrieval_documents_fts`
- `schema_migrations`

## Memory Lanes

- `method`
- `stable_user`
- `project`
- `run_state`

## Artifact Types

- `source_register`
- `scope_lock`
- `provisional_distinction_ledger`
- `component_ledger`
- `state_variable_ledger`
- `operator_ledger`
- `constraint_ledger`
- `dependency_and_interlock_map`
- `trace_ledger`
- `gap_and_pressure_ledger`
- `search_log`
- `hypothesis_basin_ledger`
- `construction_spec`
- `stress_test_report`
- `supersession_ledger`
- `final_synthesis`
- `field_state_register`
- `visibility_event_log`
- `coherence_sweep_log`
- `anchor_register`
- `friction_type_log`
