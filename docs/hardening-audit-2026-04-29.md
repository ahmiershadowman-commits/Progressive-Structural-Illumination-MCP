# Hardening Audit — 2026-04-29

Final hardening pass against `psi-coprocessor-mcp` 1.0.1 at commit `576d394`. Findings only; no code changes made by this audit.

**Method.** One direct pass over `app.py` / `cli.py` / `config.py` / `db.py` / `utils.py` / parts of `service.py` and `repository.py` / tests / `pyproject.toml`, plus five parallel specialist passes (security, bug, silent-failure, contracts, test-coverage) covering `models.py`, deeper sweeps of `service.py` / `repository.py`, and migration files.

**Confidence tags.** `VERIFIED` = read in this audit; `AGENT` = surfaced by a specialist agent and the supporting code path is consistent but not every line was opened by the consolidator.

**Note on commit `6045fdb` ("hardening: thread safety, port validation, …").** The diff only added `check_same_thread=False`, a port int-cast guard, and the `skip_backfill` flag. It did **not** add any locking, so all concurrency findings below stand.

---

## Critical

### C1. `psi.export.run` — path traversal via caller-controlled `run_id`
- VERIFIED at `src/psi_coprocessor_mcp/service.py:1443`
- `export_root = ensure_directory(self.settings.export_dir / f"{run_id}-{timestamp}")` with no validation. Combined with `psi.run.start` preserving explicit caller-supplied ids (commit `576d394`), a `run_id` like `"../../AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/x"` writes outside `export_dir`. RCE-class in HTTP mode on Windows.
- Fix: regex-validate `run_id` (e.g. `^[A-Za-z0-9_.\-]{1,64}$`) and assert `export_root.resolve().is_relative_to(self.settings.export_dir.resolve())`.

### C2. `sync_artifacts` runs the entire artifact pipeline twice
- VERIFIED at `src/psi_coprocessor_mcp/service.py:1366-1387`
- `generate_artifacts` + `save_artifact` loop + `evaluate_compliance` + `_refresh_control_state` execute, then the same block repeats. Doubles writes, retrieval-doc upserts, and `updated_at` bumps per sync.
- Fix: delete lines 1385-1401.

### C3. `_parse_datetime` silently fabricates "now" and produces mixed naive/aware datetimes
- VERIFIED at `src/psi_coprocessor_mcp/repository.py:67-68`
- `datetime.fromisoformat(value) if value else datetime.fromisoformat(utc_now_iso())`. Used 50+ times during hydration. NULL `created_at` becomes call-time, corrupting audit/supersession ordering. Mixed tz across rows breaks subtraction and Pydantic JSON dump consistency.
- Fix: raise on NULL (rows have `NOT NULL` columns; NULL is data corruption, not a default). Standardize on aware UTC everywhere.

### C4. Single SQLite connection shared across threads with no Lock
- VERIFIED — commit `6045fdb` only added `check_same_thread=False`; no `threading.Lock` exists in the package
- Sync FastMCP tool handlers run in a thread executor. `Database.transaction()` (`db.py:118-125`) uses one shared `sqlite3.Connection`. Two concurrent tool calls can interleave: A's `rollback()` discards B's pending writes.
- Fix: `threading.Lock` around `Database.transaction()` (minimum) or per-request connection.

### C5. In-memory mutations to `run_state` are silently lost
- VERIFIED at `src/psi_coprocessor_mcp/service.py:878` (`record_event`) and `service.py:892` (`friction_type`)
- Code mutates `run_state.state.O = stored` / `run_state.state.F = frictions`, then calls `_evaluate_and_store_compliance` (which only persists compliance) but never `save_run`. Next hydrate reverts. Same shape as the `block_on_poison` "mutates state then raises" anti-pattern.
- Fix: `save_run(run_state, summary)` after every state mutation, or remove the in-memory writes.

---

## High

### H1. Zero logging anywhere in the package
- VERIFIED via grep (no `logging`, `logger`, `sys.stderr`, `stderr.write` in `src/psi_coprocessor_mcp/`)
- Every caught exception, every fallback, every gate decision evaporates. On stdio, stderr is the only legitimate diagnostic channel.
- Fix: module-level `logger = logging.getLogger("psi_coprocessor_mcp")`. Instrument every `except`, every fallback, every compliance/durability decision. Configure stdio handlers to write to stderr only.

### H2. Repository `KeyError` leaks straight to MCP clients
- VERIFIED at `repository.py:229, 757, 766, 1399, 2117`
- Tools surface opaque internal errors; resources return broken responses with no actionable message. Over HTTP, also functions as an ID-enumeration oracle.
- Fix: wrap lookups in service / app layer, raise `ToolError("Unknown run_id 'X'. …")`, log details server-side.

### H3. Resource handlers reopen `Database` (migrations + seed) on every read
- VERIFIED at `app.py:441-635`
- All 22 resources call `_read_only_service(settings)` → fresh `Database()` → `apply_migrations` + `seed_builtin_memory` per request. With `stateless_http=True`, this is per HTTP call.
- Fix: change resource signatures to take `Context` and reuse `ctx.request_context.lifespan_context.repository`. Delete `_read_only_service`.

### H4. `import_run` is unhardened
- VERIFIED at `service.py:1524-1639`
- Specifically:
  - No size cap on input file.
  - `yaml.safe_load(...)` returning `None` on empty input → `payload["run_state"]` raises `TypeError`.
  - `payload["run_state"]` and `payload["summary"]` unguarded `KeyError`.
  - No symlink rejection — attacker-placed `bundle.json` symlink leaks file contents.
  - No `schema_version` check despite `manifest.schema_version="1.2.0"` being declared.
  - `model_validate` failures mid-loop commit prior items (no transaction wraps the whole import).
  - Caller-supplied `id`/`created_at`/`checksum` on artifacts/anchors are trusted and persisted (`save_artifact` trusts `checksum`).
- Fix: cap size, reject symlinks, transaction-wrap, version-gate, strip caller-controlled identity fields before upsert.

### H5. Compliance `blocking` is enforced in only two places
- AGENT-REPORTED + spot-checked
- `psi.reflect` (opt-in via `block_on_poison`, default `False`) and `export_run`. `psi.run.start`, `psi.transition.set`, `psi.artifacts.sync`, `psi.import.run`, `psi.memory.commit`, `psi.discriminator.record`, `psi.anchor.register` proceed regardless when status=BLOCKED + durability=BLOCKING.
- Fix: centralize a `_gate(run_state)` helper called from every mutating tool, OR document that `blocking` is advisory.

### H6. `_ensure_run_for_operation` silently converts "resume" to "create"
- VERIFIED at `service.py:603-617`
- Caller-supplied `run_id` that doesn't resolve becomes a brand-new run with that exact id (since commit `576d394`). Typos silently create phantom runs.
- Fix: error on miss, OR signal `resumed: false, created: true` in the response and log a warning.

### H7. Migrations: `executescript` does not honor `BEGIN/COMMIT`
- VERIFIED at `db.py:48-59` and migration files (only 2 `IF NOT EXISTS` in `0006_control_surface.sql`)
- `executescript` issues an implicit COMMIT before each statement. Failure mid-file leaves partial DDL with no `schema_migrations` row, and retry blows up on `CREATE TABLE` collisions.
- Fix: run statements one-at-a-time inside an explicit transaction, OR add `IF NOT EXISTS` to every CREATE in every migration.

### H8. FTS5 query operators not sanitized
- AGENT-REPORTED at `repository.py:2142`
- User input is split on whitespace but `*`, `^`, `NEAR`, `OR`, `AND`, `NOT`, `(`, `)`, `+`, `-` pass through. A `query` of `"a OR b OR c OR …"` or `"*"` enables CPU/IO DoS over HTTP.
- Fix: wrap each token as a quoted phrase or strip FTS-reserved tokens.

### H9. No `Origin` validation on streamable HTTP
- Best-practices: DNS-rebinding protection for local HTTP servers. Bind is `127.0.0.1` (good), but a malicious local web page with rebinding can still hit `/mcp`.
- Fix: validate `Origin` against an allowlist; document the threat model in `known-limitations.md`.

---

## Medium (contracts / forward-compat)

### M1. `extra="forbid"` on Pydantic models + no `schema_version` enforcement on import
- AGENT-REPORTED, supporting code in `models.py` (PSIModel base) + `service.py:1536`
- Adding any new field to `PsiRunState` breaks import of every existing 1.0.x bundle.
- Fix: relax to `extra="ignore"` for inbound deserialization, OR add a `schema_version` gate that migrates the bundle, OR commit to never-evolve.

### M2. Inconsistent `project_id`/`run_id` parameter shapes across 30 tools
- VERIFIED via `app.py`
- Some `str = ""` (empty-string-as-None), some required `str`, some `Optional[str]`. `psi.anchor.register` requires `project_id`; `psi.anchor.invalidate` makes it optional.
- Fix: pick one shape (`Optional[str] = None`) and apply uniformly.

### M3. String-typed enums on tool inputs with no validation
- VERIFIED — `confidence`, `durability_class`, `event_type`, `lane`, `decision`, `mode` are all `str` in tool signatures. `Enum(value)` raises `ValueError` on bad input → surfaced as raw 500.
- Fix: use `Literal[...]` types in the tool signatures so FastMCP validates pre-call.

### M4. Severity / centrality / fragility silently clamp to [0,1]
- AGENT-REPORTED at `models.py:401-410, 446-455, 489-492`
- Caller passing `severity=5.0` gets `1.0` with no error.
- Fix: replace clamps with `Field(ge=0.0, le=1.0)`.

### M5. `text/plain` MIME type on markdown method-memory resources
- VERIFIED at `app.py:441, 449, 457, 465`
- Content is markdown. Change to `text/markdown` before consumers depend on it.

### M6. Two divergent serializers on `PsiRunState`
- AGENT-REPORTED — `model_dump(mode="json")` vs `machine_readable()` use different field names (`L` vs `lens`, `H` vs `live_hypotheses`, etc.). Export bundle includes BOTH at `service.py:1446-1447`.
- Fix: pick one canonical wire format, deprecate the other.

### M7. No tool annotations, no `outputSchema`
- VERIFIED via `app.py`
- 30 `@mcp.tool` registrations have no `readOnlyHint`/`destructiveHint`/`idempotentHint`/`openWorldHint` and no `outputSchema`.
- Fix: annotate each tool; derive `outputSchema` from existing Pydantic models.

### M8. `psi.memory.retrieve` no pagination envelope
- VERIFIED at `app.py:310-317`, `service.py:1208-1212`
- Returns `{"query", "hits"}` only. No `total`, `has_more`, `next_offset`. No upper bound on `limit`.
- Fix: clamp `limit` (e.g. ≤200), return standard pagination envelope.

### M9. `metadata_json: str` parameter shape
- VERIFIED at `app.py:319-340`
- `psi.memory.commit` takes JSON-encoded string for metadata. FastMCP/Pydantic supports `dict[str, object]` directly.
- Fix: drop `_parse_metadata`, accept a real dict.

### M10. Tool naming uses dots (`psi.reflect`) not snake_case
- Best-practices style deviation. Several MCP clients treat `.` as a namespace separator, which can interact oddly with autocompletion.
- Fix: either rename to `psi_reflect` etc., or document the convention in README.

### M11. `block_on_poison` raises after mutating state
- VERIFIED at `app.py:46-56, 89-113`
- `psi_reflect` calls service.reflect (which writes to DB), then raises `ToolError` if blocking. State mutation persists regardless of the gate.
- Fix: evaluate poison/blocking before commit.

### M12. Legacy `ROLLBACK` alias undocumented removal path
- VERIFIED at `app.py:301`, `service.py:407-418`
- Description says "Legacy input ROLLBACK is accepted as an alias" — no deprecation warning emitted, no removal version named.
- Fix: emit a structured deprecation warning + target version, or commit to "permanent alias" in docs.

### M13. `sqlite3` `transaction()` re-raises but never logs the rollback
- VERIFIED at `db.py:118-125`
- Resolved automatically once H1 (logging) lands.

### M14. `_loads(...).get("key", default)` masks "stored-empty vs never-set"
- AGENT-REPORTED at `repository.py:1095, 1152, 1369-1377, 1644-1646, 1785`
- Callers cannot tell whether a field was stored as `[]` or never set. Latent footgun on schema evolution.
- Fix: separate "missing" from "empty" at the persistence boundary.

### M15. `record_visibility_event`'s reachability assumption on `events`
- AGENT-REPORTED at `service.py:679`
- `primary_event = max(events, key=lambda event: event.severity)` crashes on empty `events`. `detect_visibility_events` must always return ≥1 — undocumented and unasserted.
- Fix: explicit guard or assert in the analysis layer.

---

## Low (polish)

### L1. `canonical_json` / `compact_json` lack `default=str`
- AGENT-REPORTED at `utils.py:23-28`
- Any datetime/Enum/Path that slips into a metadata dict crashes the call.
- Fix: pass `default=str` to `json.dumps`.

### L2. `_default_data_dir()` reads `LOCALAPPDATA` regardless of OS
- AGENT-REPORTED at `config.py:14-18`
- WSL/CI Linux with that env var set ends up with a Windows-style path.
- Fix: gate on `os.name == "nt"`.

### L3. CLI lacks explicit `--db-path`/`--data-dir`
- VERIFIED at `cli.py`
- Settings come only from env. Useful for ops invocations and `diagnose`.

### L4. `import_run` path-suffix dispatch is case-sensitive
- VERIFIED at `service.py:1532-1535`
- `bundle.JSON` won't be recognized on Linux. Lowercase the suffix before the comparison.

### L5. README does not document `PSI_MCP_*` env vars
- `config.from_env` reads 7 env vars; none listed in README.
- Fix: short table.

---

## Test gaps that map to real risk

Top items from the dedicated coverage pass (full list omitted here for brevity — see audit notes):

1. `import_run` malformed/missing-key/symlink/oversize/wrong-version paths (currently only the happy path is tested).
2. HTTP transport beyond `tools/list` — no test calls a tool or reads a resource over HTTP.
3. Concurrent SQLite access (~8 threads each calling `service.reflect`) — would catch C4.
4. Resource not-found paths for all 22 templates — would catch H2.
5. Compliance `blocking` actually preventing promotion — would catch H5.
6. Idempotency of repeat `psi.reflect` calls (recent `idempotent typed_claims upsert` commit suggests this matters and is not regression-tested).
7. Partial-migration startup (only 0001-0003 applied, then construct `Database(settings)`).
8. `block_on_poison` `ToolError` path on `psi.reflect` end-to-end.
9. `PSI_MCP_*` env-var matrix beyond `PSI_MCP_DATA_DIR` and mount path.
10. Pydantic model round-trip stability (parametrized over every model).

`pytest filterwarnings = ["error"]` (`pyproject.toml:60-62`) combined with `mcp>=1.27` and `pydantic>=2.11` will likely break CI on the next dependency deprecation. Add explicit `ignore` entries for `pydantic`, `mcp`, and `starlette`.

---

## Suggested fix order

A single PR that disproportionately reduces risk:

1. **C1** (path traversal — RCE class).
2. **C2** (drop the duplicate `sync_artifacts` pass — one-liner).
3. **C3 + H1** (datetime hardening + add a logger; both touch the same hydration paths).
4. **C4 + H3** (Lock + per-request DB reuse — same surface).
5. **C5** (in-memory mutation persistence — small, high impact).

Then the next cluster: **H2** (KeyError → ToolError), **H4** (`import_run` hardening), **H5** (centralize the blocking gate).

After that, the contracts cluster (M1–M7) before any external consumer pins to the 1.0 wire format.

---

## Out of scope for this audit

- `src/psi_coprocessor_mcp/runtime/*.py` — lightly inspected by the bug-hunter agent but not deeply audited.
- Performance benchmarking beyond static analysis.
- Threat-modeling of the streamable-HTTP transport beyond DNS-rebind / `Origin` validation.
