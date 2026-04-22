# Architecture

## Layer 1: MCP Interface

The FastMCP surface exposes:

- 30 tools
- exact resources for method documents
- templated resources for project and run state, including direct structural run resources
- 8 prompts for common PSI passes

The interface is intentionally thin. Tool handlers delegate to `PsiService` and avoid embedding business logic in decorator bodies.

## Layer 2: PSI Runtime

Runtime logic lives in:

- `runtime/analysis.py`
- `runtime/source_audit.py`
- `runtime/coherence.py`
- `runtime/control.py`
- `runtime/compliance.py`
- `runtime/structure.py`
- `runtime/tracing.py`
- `runtime/gaps.py`
- `runtime/stress.py`
- `runtime/summaries.py`
- `runtime/artifacts.py`
- `service.py`

Core behaviors:

- visibility-event detection
- applicability boundary assessment
- source intake normalization and canonicalization
- friction typing
- lens and scope stabilization
- primitive extraction
- dependency consolidation via interlock graph
- local articulation tracing and forward tracing
- gap-origin and search-plan derivation against the smallest discriminative unresolved unit
- basin generation and skeptic / anti-pattern stress
- weighted whole-field coherence sweeps
- blast-radius prioritization
- provenance-typed claims and durability classes
- confidence axes separated from durability
- bounded scaffold semantics for temporary structure
- mode-weighted control family activation
- friction routing with default-placement metadata
- pre-emission compliance checking
- durability/native-minimality gating
- transition recommendation and setting
- deterministic artifact sync
- current-phase, phase-history, open-artifact, next-gate, and supersession tracking

## Layer 3: Persistence

Persistence uses SQLite with six migrations:

- `0001_core.sql`
- `0002_retrieval_fts.sql`
- `0003_indexes.sql`
- `0004_rubric_integration.sql`
- `0005_methodology_ontology.sql`
- `0006_control_surface.sql`

State is stored across:

- runs
- projects
- visibility events
- coherence sweeps
- anchors
- tensions
- hypotheses
- discriminators
- friction logs
- constraints
- source objects
- primitive components
- state variables
- primitive operators
- interlocks
- trace steps
- gap records
- search records
- basin records
- skeptic findings
- anti-pattern findings
- typed claims
- compliance reports
- memory lanes
- artifacts
- exports
- supersession history
- dead ends
- project snapshots

FTS5 powers `psi.memory.retrieve`.

## Layer 4: Support Services

Support capabilities include:

- schema validation through Pydantic
- import/export manifests
- diagnostics via CLI
- summary generation
- retrieval helpers
- project snapshotting

## PSI Mapping

### Whole-field priority

`runtime/coherence.py` prioritizes propagation by:

- centrality
- fragility
- dependency density
- timescale proximity
- substrate coupling
- durability relevance
- stance sensitivity

It now scores both project-level and run-level structural objects using:

- interlock graph incidence
- blocking trace pressure
- open gap pressure
- supersession history

### Run-state vector

`PsiRunState` keeps `W/L/B/O/C/A/U/H/D/F/N/P/T/S/G` explicit in code and persistence, plus applicability, current phase, phase history, open artifacts, next gating condition, smallest discriminative unit, operator families, control families, friction routing, and compliance state.

### Durability gate

`runtime/analysis.py` detects:

- placeholders
- convenience scaffolds
- known-bad continuity
- rewrite debt

Blocking mode can raise a tool error when the caller requests hard blocking.

### Normalization layer

`runtime/control.py` turns the normalization-map additions into executable state:

- six canonical control families
- mode activation profiles for survey, closure, construction, audit, and repair
- friction-to-regime routing metadata
- explicit separation of provenance, confidence, and durability

`runtime/compliance.py` then checks whether a would-be stable surface still violates PSI obligations, including Phase 0 applicability, bounded temporary scaffolds, basin burden, and uncertainty-honesty state.

## Design Departures

These are explicit, deliberate departures from a purely human PSI workflow:

1. The server uses deterministic heuristics rather than autonomous model-side reasoning inside the server.
Reason: MCP servers should remain reliable, local, and host-agnostic. The host model remains the primary reasoner; the server externalizes PSI state and pressure.

2. Streamable HTTP is configured as stateless at the transport layer while persistence stays stateful in SQLite.
Reason: operational state lives in the database, not in transport sessions. This improves local durability and simplifies restart behavior.

3. Resource reads use a read-only service path rather than request lifespan context.
Reason: this keeps resource reads reliable under current FastMCP resource semantics while still reading the same local SQLite state.
