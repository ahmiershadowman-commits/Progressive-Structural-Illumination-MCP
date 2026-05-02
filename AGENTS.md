# Agent Instructions: PSI Coprocessor MCP

This file provides high-signal, repo-specific guidance for agents working with the PSI Coprocessor MCP.

## Core Rule

The PSI MCP is your persistent reasoning layer. **Do not create markdown files or documents to record PSI state.** Use `psi.memory.commit` to store findings, `psi.anchor.register` for decisions, and `psi.hypothesis.update` for open hypotheses. The MCP database is the storage layer.

## Required Workflow

For every non-trivial task (code change, design decision, debugging, analysis):

1. **Start or resume a run**
   `psi.run.start(title="<what you're doing>", scope="<what's in/out>", mode="<see below>", project_id="psi_coprocessor_mcp")`
   If continuing earlier work: `psi.run.get_state(run_id="<prior-id>")`

2. **Reflect before acting**
   `psi.reflect(task="<what you're solving>", draft_answer="<your plan>", run_id="<run_id>", project_id="psi_coprocessor_mcp")`
   Call this before writing code, proposing a design, or finalizing a plan.

3. **Record discoveries**
   - Finding: `psi.event.record`
   - Contradiction: `psi.friction.type`
   - Decision: `psi.anchor.register`
   - Open question: `psi.hypothesis.update`
   - Dead end: `psi.dead_end.record`

4. **Check compliance before emitting a final answer**
   `psi.compliance.check(run_id="<run_id>")`

5. **Persist durable findings**
   `psi.memory.commit(lane="project", key="<slug>", title="<title>", content="<summary>", project_id="psi_coprocessor_mcp")`

## Naming Conventions

| Field | Value |
|-------|-------|
| `project_id` | `psi_coprocessor_mcp` — stable across all sessions |
| `mode` | `survey` (explore) / `construction` (implement) / `audit` (review) / `repair` (fix) / `closure` (wrap up) |
| `run_id` | Omit to auto-generate; supply a slug only to resume a named run |

## Specialized Tools

`psi.reflect` covers 80% of cases. Use these when you need deeper structure:

- Stuck on root cause → `psi.gap.analyze`, then `psi.basin.generate`
- Ripple effects from a change → `psi.sweep.run`
- Sources unclear or duplicated → `psi.source.audit`
- Reviewing a diff for hidden risks → `psi.diff.analyze`
- Test failure to analyze → `psi.test_failure.ingest`
- Validate before finishing → `psi.stress.run`, then `psi.compliance.check`

## Core Functionality

- **Purpose:** PSI Coprocessor MCP is a local-first Model Context Protocol (MCP) server that operationalizes Progressive Structural Illumination as a persistent cognitive coprocessor.
- **Canonical Authority:** Defined by `docs/canonical-source-corpus.md`, not local summaries.

## Running the Coprocessor

- **stdio:** `uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp stdio`
- **HTTP:** `uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp http --port 8765`

## Updating

- Run `uvx --refresh --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp diagnose`.
- Restart your MCP host after updating.

## Local Development

- **Setup:** `uv sync --extra dev`
- **Run:**
  - `uv run psi-coprocessor-mcp diagnose`
  - `uv run psi-coprocessor-mcp stdio`
- **Windows OneDrive Quirk:** If hardlink errors occur, prefix commands with `$env:UV_LINK_MODE = "copy"`.

## Validation

- Run tests with: `uv run pytest`
- Current test status: `35 passed`
- **Key Test Gaps:** Focus on `import_run` paths, HTTP transport, concurrent SQLite access, resource not-found paths, and compliance blocking enforcement.

## Hardening Fixes Applied (2026-04-30)

### Critical & High Priority

- **Finding #1 - Path Traversal:** `export_run` now validates `run_id` against `^[A-Za-z0-9_.-]{1,64}$` and asserts `is_relative_to()` on export paths.
- **Finding #2 - sync_artifacts Double Execution:** Investigated. The second pass is intentional — compliance changes from BLOCKED to PASS after the second artifact generation. No fix applied.
- **Finding #3 - Datetimes:** `_parse_datetime` now raises `ValueError` on NULL timestamps and ensures all returned datetimes are timezone-aware (UTC).
- **Finding #4 - SQLite Concurrency:** Added `threading.RLock` around `Database.transaction()` to prevent interleaved transactions.
- **Finding #5 - In-Memory State Mutations:** Investigated. Code persists mutations through `_evaluate_and_store_compliance()` which calls `save_run`. No clear bug found.
- **Finding #6 - Centralized Logging:** Added `logging.getLogger("psi_coprocessor_mcp")` to `db.py`, `service.py`, `app.py`, and `config.py`.
- **Finding #7 - KeyError Leaks:** Added `_call_service()` helper in `app.py` that catches `KeyError` and converts to `ToolError` with user-friendly messages.
- **Finding #8 - Resource Handlers Reopen Database:** Refactored to use `_get_read_only_service()` which caches the service instance, avoiding repeated database re-opening.
- **Finding #9 - Unsafe import_run:** Added file size caps (100MB), symlink rejection, required field validation, schema version check, run_id validation, and transaction wrapping.
- **Finding #10 - Compliance Blocking:** Added `_gate()` helper method to `PsiService` and instrumented it in `record_event`, `friction_type`, `run_sweep`, `set_transition`, and `sync_artifacts`.
- **Finding #11 - Silent Resume to Create:** Added clear warning logging when `_ensure_run_for_operation` creates a new run with an explicit run_id.
- **Finding #12 - Migration executescript:** Investigated. All migrations already use `IF NOT EXISTS`. The executescript approach is retained for compatibility.
- **Finding #13 - FTS5 Query Operators:** Sanitized queries by stripping special characters (`*^()+\-`) and FTS operators (`NEAR`, `OR`, `AND`, `NOT`), then wrapping tokens in quotes.
- **Finding #14 - HTTP Origin Validation:** Added `OriginValidationMiddleware` to the HTTP app that rejects requests from unauthorized origins.

### Medium & Low Priority

- **Finding #15 - Schema Evolution:** Changed `extra="forbid"` to `extra="ignore"` on `PSIModel` base class to allow forward-compatible imports.
- **Finding #16 - Tool Signatures:** Standardized `project_id` and `run_id` parameter shapes across tools.
- **Finding #17 - Enum Validation:** String-typed enums now use `Literal[...]` types in tool signatures where applicable.
- **Finding #18 - Numerical Clamping:** Added `Field(ge=0.0, le=1.0)` validation to numerical fields.
- **Finding #19 - Markdown MIME Type:** Changed method memory resources from `text/plain` to `text/markdown`.
- **Finding #20 - Divergent Serializers:** Investigated. Both formats serve different purposes; retained both with clear documentation.
- **Finding #21 - Tool Annotations:** Added `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint` annotations to tools.
- **Finding #22 - Memory Retrieve:** Added pagination envelope and improved metadata handling.
- **Finding #23 - JSON Serialization:** Added `default=str` to `canonical_json()` and `compact_json()` to handle datetimes, enums, and Paths.
- **Finding #24 - LOCALAPPDATA:** Gated `LOCALAPPDATA` access on `os.name == "nt"`.
- **Finding #25 - Database.close() Leak:** Fixed by addressing Finding #8 (resource handler caching).
- **Finding #26 - Test Gaps:** Added `test_export_run_path_traversal` and `test_parse_datetime_*` tests.

## Key Documentation References

- `docs/canonical-source-corpus.md`: Primary source of truth for canonical authority.
- Other documentation: `docs/installation.md`, `docs/architecture.md`.
