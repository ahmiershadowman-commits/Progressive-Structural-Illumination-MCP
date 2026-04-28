# Canonical Source Corpus

This file records which documents actually define the intended PSI MCP build, which documents only describe the current implementation, and which documents are derivative pressure-tests or unrelated user/account overlays.

It exists to stop source drift during future audits and migrations.

## Authority Order

### 1. Primary canonical methodology sources

These are the highest-authority build sources for the PSI MCP:

1. Internal research documentation: PSI methodology core specification (v4, surgical variant)
2. Internal research documentation: PSI normalization and control layer specification (v2, surgical variant)

Use them together:

- `master-methodology-psi-integrated-v4-surgical.md` defines the PSI methodology, ontology, artifact bundle, run-state, phase/regime structure, quality gates, AI collaboration contract, and machine-readable run-state skeleton.
- `psi_normalization_map_v2_surgical.docx` defines how the rubric/control layer must normalize into PSI without creating a second competing methodology.

### 2. Canonical precursors and retained-nuance sources

These are not the top authority, but they contain retained nuance that informs interpretation when the primary pair compresses or assumes earlier material:

1. Internal research documentation: PSI methodology core specification (v3, AI integration variant)
2. Internal research documentation: PSI methodology core specification (v2)
3. Internal research documentation: PSI methodology core specification (initial version)
4. Internal research documentation: Pre-PSI baseline methodology specification
5. Internal research documentation: Unified synthesis and closure pipeline specification
6. Internal research documentation: PSI normalization and control layer specification (v1)

Interpretation rule:

- if a precursor introduces a rule that is preserved, tightened, or merely compressed in the primary pair, keep it
- if a precursor conflicts with the primary pair, the primary pair wins
- if a precursor adds a new abstraction that the primary pair deliberately removed, do not silently reintroduce it

Important retained precursor nuances:

- applicability boundary / explicit method-fit check
- smallest discriminative unresolved unit targeting
- burden discipline for introduced structure
- confidence axes kept distinct when needed
- run-class distinction for light survey vs closure vs full canonical runs

### 3. Applied specimen sources

These are not ontology authorities, but they are methodology-bearing exemplars of how the method is expected to run in practice:

1. Internal applied example: Neuro decomposition completion design specification
2. Internal applied example: Neuro decomposition completion execution plan

Use them for:

- loop execution semantics
- layer-by-layer expansion behavior
- targeted evidence search discipline
- forward cascade tracing expectations
- explicit file/artifact discipline in a real applied run

Do not use them to override the primary ontology or transition vocabulary.

## Implementation Docs

These describe what the current repo claims to implement. They are not canonical methodology authority:

- `README.md`
- `docs/architecture.md`
- `docs/schema-reference.md`
- `docs/tool-resource-prompt-reference.md`
- `docs/installation.md`
- `docs/troubleshooting.md`
- `docs/known-limitations.md`
- `docs/build-contract-coverage-audit.md`

Evaluation rule:

- implementation docs may be used as evidence of current repo claims
- they may not be used to redefine what PSI canonically requires
- when implementation docs conflict with canonical methodology sources, the methodology sources win

## Derivative Or Non-Canonical Sources

These may still be useful as pressure-tests, but they are not canonical build authority:

- Internal development notes: MCP hardening and structural specification
- Internal development notes: Execution directives and workflows
- Internal development notes: Execution pipeline specification
- Internal development notes: Work stack and execution order (v2)

Classification:

- `MCP stuff.txt` is a derivative hardening/specification attempt. It includes useful pressure and some good structural checks, but it also makes completeness claims that cannot be treated as canonical without verification against the actual methodology sources.
- `Directives.txt`, `EXECUTION_PIPELINE.txt`, and `WORK_STACK_V2.txt` are user/account behavior overlays. They do not define PSI MCP architecture.

## Canonical Intended Build

The intended PSI MCP build, taken across the canonical source corpus, is:

- PSI is the only methodology. The rubric layer is an execution/control layer inside PSI, not a parallel framework.
- Visibility events are the atomic unit of progress.
- The whole field is the canonical object of work.
- Phases are re-entrant control regimes, not a one-way waterfall.
- Meaningful changes require weighted whole-field propagation via coherence sweep, not local patch continuation.
- Durability/native-minimality is a hard continuity gate.
- Questions are operators with routing consequences.
- The canonical run-state is explicit and live: `W/L/B/O/A/U/H/D/F/N/P/T/S/G`.
- The standard artifact bundle is mandatory for serious runs.
- Friction must be typed and routed.
- The AI collaboration contract is real, especially:
  - no local patching without field impact
  - uncertainty honesty when propagation is partial
  - no stable continuation on known-bad continuity
- The normalization layer must remain thin and PSI-native:
  - control families
  - mode activation profiles
  - friction re-entry priorities
  - default execution placement metadata
  - pre-emission compliance checking

## Version Notes

### Master-methodology line

- `master-methodology-psi-integrated-v4-surgical.md` is the current top authority.
- `master-methodology-psi-integrated-v3-ai.md` is effectively the same authority line without material section loss.
- `master-methodology-psi-integrated-v2.md` and `master-methodology-psi-integrated.md` are earlier PSI-integrated forms.
- `master-methodology.md` is the pre-PSI baseline and must not be treated as sufficient by itself.

### Normalization-map line

- `psi_normalization_map_v2_surgical.docx` is the current top authority.
- `psi_normalization_map.docx` is the earlier normalization map.

The main meaningful additions in `v2_surgical` are execution-layer clarifications, not a second ontology:

- pre-emission PSI compliance checker
- mode activation profiles
- friction-to-re-entry priority defaults
- default execution placement metadata on control families

## Audit Rule

Any future implementation audit should proceed in this order:

1. compare code and persistence against the primary canonical pair
2. use the precursor set only to recover retained nuance or disambiguate compressed language
3. use applied specimen docs to test whether the runtime behaves like the method in practice
4. use implementation docs only to measure repo claims against source truth
5. use derivative notes only as non-authoritative pressure-tests
