# Build Contract Coverage Audit

This file maps the original build contract, the core PSI methodology document, and the normalization rubric onto the current implementation.

Status labels:

- `IMPLEMENTED`: materially present in code, persistence, MCP surface, artifacts, and tests
- `PARTIAL`: represented faithfully enough for the server to function, but implemented with bounded deterministic heuristics or compressed object mapping rather than a separate canonical subsystem

## Summary

The contract-required server surface is implemented.

The remaining caveats documented below are bounded implementation choices, not omitted contract subsystems.

The server now includes:

- a local installable FastMCP server with stdio and streamable HTTP
- explicit PSI run-state with typed memory lanes and persistence
- authoritative typed structures for source objects, components, state variables, primitive operators, interlocks, traces, gaps, searches, basins, skeptic findings, and anti-pattern findings
- graph-aware weighted coherence sweeps that use interlocks, traces, gaps, and supersession history
- durability/native-minimality blocking and pre-emission compliance
- deterministic artifact regeneration with authoritative-vs-fallback marking
- export/import with machine-readable schema metadata
- direct regime tools and run resources for source audit, structure extraction, tracing, gap analysis, search planning, basin generation, and stress testing
- end-to-end tests covering runtime, persistence, MCP surface, artifact sync, import/export, migrations, and scenario behavior

Residual limitations are not missing subsystems. They are bounded implementation choices:

1. Structural extraction is deterministic and heuristic rather than a learned semantic parser.
2. A few methodology concepts such as `LAYER`, `DERIVED_DYNAMIC`, and `EVIDENCE_OBJECT` are represented inline across typed records and metadata rather than as standalone top-level tables.
3. Regime expansion is host-invoked and friction-routed rather than autonomously self-spawning inside the server.

## Contract Matrix

### Product shape

| Requirement | Status | Notes |
|---|---|---|
| Local installable MCP server | IMPLEMENTED | Python package with CLI, stdio, and streamable HTTP. |
| Local-first / no cloud dependency | IMPLEMENTED | SQLite, local filesystem, and local transports only. |
| Typed / stateful / persistent / exportable / inspectable / testable | IMPLEMENTED | Present in code, schema, exports, docs, and tests. |
| Durable enough to avoid later re-architecture | IMPLEMENTED | The persistence/runtime/MCP substrate and methodology-depth surfaces are integrated rather than bolted on. |

### MCP semantics and host integration

| Requirement | Status | Notes |
|---|---|---|
| Current MCP semantics: tools, resources, prompts | IMPLEMENTED | FastMCP surface follows current semantics. |
| STDIO transport | IMPLEMENTED | Present and tested. |
| Streamable HTTP transport | IMPLEMENTED | Present and tested. |
| Host config examples / install docs | IMPLEMENTED | Present in `docs/` and `examples/`. |
| Thin host routing instruction | IMPLEMENTED | Present in app instructions and README. |

### Required architecture layers

| Requirement | Status | Notes |
|---|---|---|
| Layer 1: MCP interface | IMPLEMENTED | Tools, resources, prompts, transports, and CLI. |
| Layer 2: PSI runtime | IMPLEMENTED | Event routing, source audit, structure extraction, coherence sweep, tracing, gap analysis, basin generation, stress, transition, and artifacts. |
| Layer 3: persistence | IMPLEMENTED | SQLite, migrations, authoritative typed tables, artifacts, exports, FTS5 retrieval. |
| Layer 4: support services | IMPLEMENTED | Validation, diagnostics, import/export, project snapshots, summaries, retrieval helpers. |

### Memory design

| Requirement | Status | Notes |
|---|---|---|
| Method lane | IMPLEMENTED | Seeded and retrievable. |
| Stable user lane | IMPLEMENTED | Seeded and retrievable. |
| Project lane | IMPLEMENTED | Anchors, tensions, hypotheses, constraints, memory, snapshots. |
| Run-state lane | IMPLEMENTED | Run state, claims, compliance, retrieval docs, artifacts. |
| Do not collapse lanes | IMPLEMENTED | Distinct persistence and retrieval lanes remain separate. |

### Required state model

| Requirement | Status | Notes |
|---|---|---|
| Explicit `W/L/B/O/A/U/H/D/F/N/P/T/S/G` | IMPLEMENTED | First-class in models, persistence, exports, and MCP reads. |
| Live run-state as active control surface | IMPLEMENTED | Runtime decisions are driven by live state. |
| Machine-readable schema | IMPLEMENTED | Exported with schema metadata and versioned manifest. |

### Provenance / status / operator obligations

| Requirement | Status | Notes |
|---|---|---|
| Provenance tags include `SOURCE` and `GROUNDED` | IMPLEMENTED | Present and used in claim typing. |
| Provenance tags include `OBSERVED/INFERRED/CONSTRUCTED/SPECULATIVE/UNKNOWN` | IMPLEMENTED | Present and used. |
| Exposure operator support | IMPLEMENTED | Present in operator detection and typed primitive operators. |
| Questions act as operators in routing | IMPLEMENTED | Question events and operator-family detection both affect routing. |
| Resolution / transition tags | IMPLEMENTED | Transition now uses `ROLLBACK_REQUIRED`; legacy input `ROLLBACK` is accepted as a compatibility alias. |

### Methodology ontology

| Requirement | Status | Notes |
|---|---|---|
| `WHOLE_FIELD`, `VISIBILITY_EVENT`, `LENS_STATE`, `STANCE_GEOMETRY`, `TIMESCALE_BAND`, `SUBSTRATE_CONSTRAINT` | IMPLEMENTED | Present as first-class models. |
| `SOURCE_OBJECT` | IMPLEMENTED | Table, repository, audit pass, export/import, resource, artifact. |
| `COMPONENT` | IMPLEMENTED | Table, repository, artifact, resource, export/import. |
| `STATE_VARIABLE` | IMPLEMENTED | Table, repository, artifact, resource, export/import. |
| `OPERATOR` | IMPLEMENTED | Primitive operator records are first-class and persisted. |
| `STRUCTURAL_CONSTRAINT` | PARTIAL | Constraint items are explicit, but not split into a separate subclass beyond metadata/category typing. |
| `INTERLOCK` | IMPLEMENTED | Relation-edge graph exists and drives sweeps/artifacts/resources. |
| `CASCADE` | IMPLEMENTED | Trace records carry `cascade_id` and divergence classification. |
| `REGIME` | IMPLEMENTED | Enum plus direct MCP tools and routing. |
| `GAP_OBJECT` | IMPLEMENTED | First-class gap records with origin, discriminator, and blocking status. |
| `SEARCH_RECORD` / targeted evidence search | IMPLEMENTED | Planned search records are persisted and exposed. |
| `BASIN_RECORD` | IMPLEMENTED | Null, reinterpretive, literal, and failure-mode basins are explicit. |
| `SKEPTIC_FINDING` / `ANTIPATTERN_FINDING` | IMPLEMENTED | First-class stored findings. |
| `LAYER`, `DERIVED_DYNAMIC`, `EVIDENCE_OBJECT` | PARTIAL | Represented inline across metadata/evidence fields rather than standalone tables. |

### Required runtime behavior

| Requirement | Status | Notes |
|---|---|---|
| Detect friction or visibility event | IMPLEMENTED | Present. |
| Stabilize lens and scope | IMPLEMENTED | Present. |
| Isolate what became newly visible | IMPLEMENTED | Visibility events and source audit keep the triggering surface explicit. |
| De-abstract before explaining | IMPLEMENTED | Primitive extraction produces explicit components, state variables, and operators. |
| Trace local articulation | IMPLEMENTED | Trace records and trace ledger exist. |
| Weighted whole-field coherence sweep | IMPLEMENTED | Present and graph-aware. |
| Preserve live tensions | IMPLEMENTED | Tensions and basins remain explicit. |
| Search for discriminators | IMPLEMENTED | Present. |
| Select next highest-revelation probe | IMPLEMENTED | Present. |
| Apply durability/native-minimality gate | IMPLEMENTED | Present with advisory/blocking. |
| Recommend or set transition | IMPLEMENTED | Present. |
| Sync artifacts and memory | IMPLEMENTED | Present. |

### Phase / regime completeness

| Methodology regime | Status | Notes |
|---|---|---|
| Task contract / scope lock | IMPLEMENTED | Run start and scope state. |
| Source intake / provenance audit | IMPLEMENTED | First-class audit subsystem and MCP tool/resource. |
| Mining and provisional structure | IMPLEMENTED | Typed claims and provisional distinction ledger. |
| Primitive and operator extraction | IMPLEMENTED | Components, state variables, primitive operators. |
| Dependency consolidation | IMPLEMENTED | Interlock graph persisted and surfaced. |
| Forward tracing and divergence detection | IMPLEMENTED | Trace records with divergence classes and blocking state. |
| Whole-field coherence sweep | IMPLEMENTED | Graph-aware prioritization. |
| Gap / pressure analysis | IMPLEMENTED | Gap records and search planning. |
| Targeted evidence search planning | IMPLEMENTED | Search records and MCP tool/resource. |
| Hypothesis basin generation | IMPLEMENTED | Basin records and ledger. |
| Synthesis and construction | IMPLEMENTED | Construction spec and transition control. |
| Stress test and minimalization | IMPLEMENTED | Skeptic findings, anti-pattern findings, compliance, stress tool/resource. |
| Iteration / halt / packaging | IMPLEMENTED | Summary, export, halt prompt, artifacts, compliance gates. |
| Emergent interaction / regime expansion | PARTIAL | Exposed through direct regime tools and friction routing rather than a separate autonomous subsystem. |

### Friction model

| Requirement | Status | Notes |
|---|---|---|
| `SUBSTRATE_FRICTION` | IMPLEMENTED | Present. |
| `CONCEPTUAL_DRIFT` | IMPLEMENTED | Present. |
| `STRUCTURAL_MISMATCH` | IMPLEMENTED | Present. |
| `CONTINUITY_POISON` | IMPLEMENTED | Present. |
| Explicit detection criteria | IMPLEMENTED | Deterministic detection logic exists. |
| Routing to regimes | IMPLEMENTED | Present. |
| Affects transition scoring | IMPLEMENTED | Present. |
| Stored in logs and retrievable | IMPLEMENTED | Present. |

### Durability / native-minimality

| Requirement | Status | Notes |
|---|---|---|
| Blocks placeholders, convenience scaffolds, known-bad continuity, rewrite debt | IMPLEMENTED | Present. |
| Advisory mode | IMPLEMENTED | Present. |
| Blocking mode | IMPLEMENTED | Present. |
| Distinguish durability from confidence | IMPLEMENTED | Present. |
| Temporary scaffolds only when explicit and bounded | IMPLEMENTED | Typed scaffold-boundary state is present on claims/anchors and enforced in compliance/stress. |

### AI collaboration contract

| Requirement | Status | Notes |
|---|---|---|
| No local patching without field impact | IMPLEMENTED | Enforced in diff analysis and compliance. |
| Uncertainty honesty when propagation cannot complete | IMPLEMENTED | Explicit uncertainty state. |
| No stable continuation on recognized placeholder / rewrite debt | IMPLEMENTED | Durability and compliance both block it. |
| Output format makes local patch drift obvious | IMPLEMENTED | Diff analysis, propagation trace, compliance, and authoritative artifacts expose drift. |

### Persistence

| Requirement | Status | Notes |
|---|---|---|
| Runs / projects / events / sweeps / anchors / tensions / hypotheses / discriminators / friction / constraints / memory / artifacts / exports / supersession history | IMPLEMENTED | Present. |
| Run-state store | IMPLEMENTED | `runs.run_state_json`. |
| Artifact/log store | IMPLEMENTED | Present. |
| Retrieval index | IMPLEMENTED | FTS5. |
| Migrations | IMPLEMENTED | Six migrations, including methodology ontology and the control-surface extension. |
| Atomic writes / rollback-safe updates | IMPLEMENTED | SQLite transaction boundaries. |
| Deterministic regeneration of artifacts from live state | IMPLEMENTED | Present. |
| Sync between live run-state and artifact snapshots | IMPLEMENTED | Present and tested. |

### Artifact system

| Artifact | Status | Notes |
|---|---|---|
| `source-register` | IMPLEMENTED | Includes canonicalization and audit issues from source objects. |
| `scope-lock` | IMPLEMENTED | Present. |
| `provisional-distinction-ledger` | IMPLEMENTED | Backed by typed claims and field updates. |
| `component-ledger` | IMPLEMENTED | Uses authoritative components. |
| `state-variable-ledger` | IMPLEMENTED | Uses authoritative state variables. |
| `operator-ledger` | IMPLEMENTED | Uses primitive operators plus control/operator families. |
| `constraint-ledger` | IMPLEMENTED | Present. |
| `dependency-and-interlock-map` | IMPLEMENTED | Uses persisted interlocks. |
| `trace-ledger` | IMPLEMENTED | Uses persisted traces. |
| `gap-and-pressure-ledger` | IMPLEMENTED | Uses gap records plus tensions/uncertainty. |
| `search-log` | IMPLEMENTED | Uses search records. |
| `hypothesis-basin-ledger` | IMPLEMENTED | Uses basin records plus hypotheses/tensions. |
| `construction-spec` | IMPLEMENTED | Present. |
| `stress-test-report` | IMPLEMENTED | Includes skeptic findings, anti-pattern findings, friction, routing, and compliance. |
| `supersession-ledger` | IMPLEMENTED | Uses persisted supersession history. |
| `final-synthesis` | IMPLEMENTED | Present. |
| `field-state-register` | IMPLEMENTED | Present and schema-versioned. |
| `visibility-event-log` | IMPLEMENTED | Present. |
| `coherence-sweep-log` | IMPLEMENTED | Present. |
| `anchor-register` | IMPLEMENTED | Present. |
| `friction-type-log` | IMPLEMENTED | Present. |

### MCP surface

| Requirement | Status | Notes |
|---|---|---|
| 22 required tools from contract | IMPLEMENTED | Present. |
| Direct regime tools for source audit / structure / tracing / gap analysis / search planning / basin generation / stress | IMPLEMENTED | Added as separate MCP tools. |
| Required resources from contract | IMPLEMENTED | Present. |
| Extended run resources for sources/components/interlocks/traces/gaps/stress | IMPLEMENTED | Present. |
| Required prompts from contract | IMPLEMENTED | Present. |

### Testing / validation

| Requirement | Status | Notes |
|---|---|---|
| Unit tests | IMPLEMENTED | Present. |
| Integration tests | IMPLEMENTED | Present. |
| Persistence tests | IMPLEMENTED | Present. |
| Migration tests | IMPLEMENTED | Present. |
| MCP interface tests | IMPLEMENTED | Present. |
| Artifact sync tests | IMPLEMENTED | Present. |
| Durability gate tests | IMPLEMENTED | Present. |
| Coherence sweep tests | IMPLEMENTED | Present. |
| Blast-radius prioritization tests | IMPLEMENTED | Present. |
| Import/export round-trip tests | IMPLEMENTED | Present. |
| Scenario tests for architecture ambiguity, continuity poison, structural mismatch, scope discrimination, anchor invalidation, local-update prohibition | IMPLEMENTED | Present. |
| Tests for source audit, direct regime tools, authoritative artifacts, rich export payloads | IMPLEMENTED | Present. |

## Residual Non-Blocking Limitations

1. Primitive extraction, relation discovery, and gap classification are deterministic heuristics over the supplied text surface.
2. Some methodology abstractions remain represented as metadata on richer typed records rather than isolated top-level entity classes.
3. Search planning exists locally, but actual evidence collection remains host-driven.
