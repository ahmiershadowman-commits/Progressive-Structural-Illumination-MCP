# PSI Coprocessor MCP — Codebase Audit & Blast Radius Map

Generated: 2026-04-30

## Architecture Overview

```
Layer 3: Transport
  app.py          (FastMCP tools/resources/prompts, HTTP middleware)
  cli.py          (argparse entrypoint)

Layer 2: Business Logic
  service.py      (PsiService — orchestrator, ~1880 lines)
  runtime/        (11 heuristic analysis modules, ~2800 lines)

Layer 1: Persistence
  repository.py   (SQL CRUD, ~2400 lines)
  db.py           (SQLite connection, migrations, transactions)
  seed.py         (Static methodology memory)

Layer 0: Foundation
  models.py       (Pydantic domain models, ~1050 lines)
  config.py       (ServerSettings dataclass)
  utils.py        (JSON, datetime, hashing helpers)
```

## Dependency Graph

```
cli → app, config
app → config, db, repository, service, utils, mcp, starlette
service → config, models, repository, utils, runtime/*
repository → db, models, utils
runtime/* → models, utils
```

## Blast Radius Matrix

| Component | Direct Consumers | Lines | Risk Level | Change Impact |
|-----------|-----------------|-------|------------|---------------|
| **models.py** | ALL modules | 1050 | CRITICAL | Any field/type change ripples everywhere. `PSIModel` base class (`extra="ignore"`) is the global compatibility gate. |
| **utils.py** | service, repository, db, app, runtime/* | 53 | HIGH | JSON serialization (`canonical_json`, `compact_json`) affects persistence format. |
| **config.py** | db, app, service, cli, tests | 90 | MEDIUM-HIGH | Env var changes affect deployment. `_default_data_dir()` is Windows-aware. |
| **db.py** | repository, app (lifespan), tests | 135 | HIGH | Migration or connection changes can corrupt data. `Database.execute()` is now thread-safe with RLock. |
| **repository.py** | service, app (resources), tests | 2400 | HIGH | SQL changes must stay synced with migrations. All 34 execute calls now use thread-safe `db.execute()`. |
| **service.py** | app, tests | 1880 | HIGH | Business logic changes affect all tool behavior. `_gate()` enforces compliance blocking. |
| **runtime/*.py** | service only | 2800 | MEDIUM | Heuristic changes affect all `reflect()` outputs. Pure functions over text payloads. |
| **app.py** | cli, tests | 691 | MEDIUM | Tool/resource/prompt signatures affect MCP clients. Read-only service cache prevents DB reopening. |
| **seed.py** | db only | 224 | LOW | Content changes affect seeded memory. |
| **migrations/*.sql** | db, repository | 6 files | CRITICAL | Schema changes require matching repository SQL. All use `IF NOT EXISTS`. |

## Critical Hotspots

### 1. `service.py:reflect()` — The Central Pipeline
- **Lines**: ~650-830
- **What it does**: Orchestrates the entire PSI cognitive pipeline — visibility events, friction typing, blast radius estimation, transition recommendation, compliance checking.
- **Blast radius**: Any change affects every `psi.reflect` call. Calls 10+ runtime modules in sequence.
- **Risk**: High. The order of operations matters for state consistency.

### 2. `repository.py` — The Monolithic ORM
- **Lines**: 2400+
- **What it does**: CRUD for 15+ entity types. Heavy inline SQL.
- **Blast radius**: Schema changes in migrations require updates here.
- **Risk**: High. 34 database execute calls (now thread-safe via `Database.execute()`).

### 3. `models.py:PSIModel` — The Compatibility Gate
- **Config**: `extra="ignore"` (was `"forbid"`)
- **Blast radius**: All model validation. Changing to `"forbid"` would break bundle imports.
- **Risk**: Critical. This is the forward-compatibility mechanism.

### 4. `app.py:_get_read_only_service()` — Resource Handler Cache
- **What it does**: Caches PsiService instances per database path to avoid reopening DB on every resource read.
- **Blast radius**: All 22 resource handlers.
- **Risk**: Medium. Stale connections if DB file changes. Leaks connections if many unique paths used.

### 5. `db.py:Database.transaction()` — Concurrency Control
- **What it does**: RLock-protected transaction context manager.
- **Blast radius**: All write operations through repository.
- **Risk**: High. The `execute()` method now also uses the lock for reads, preventing interleaved cursor access.

## Additional Issues Found (Beyond Original 26)

### A. Thread Safety — FIXED
**Issue**: `repository.py` had 34 direct `self.database.connection.execute()` calls bypassing the RLock.
**Fix**: Added `Database.execute()` method with lock acquisition. Replaced all direct access.
**Blast radius**: repository.py, db.py

### B. Compliance Error Handling — FIXED
**Issue**: `_gate()` raises `ValueError` on blocked compliance, but `_call_service()` only caught `KeyError`.
**Fix**: Added `ValueError` catch in `_call_service()` converting to `ToolError`.
**Blast radius**: app.py

### C. SQLite Busy Timeout — FIXED
**Issue**: WAL mode without `PRAGMA busy_timeout` causes immediate `SQLITE_BUSY` errors under concurrent load.
**Fix**: Added `PRAGMA busy_timeout = 5000` (5 seconds).
**Blast radius**: db.py

### D. God Classes — ACKNOWLEDGED
**Issue**: `PsiService` (~1880 lines) and `Repository` (~2400 lines) violate Single Responsibility Principle.
**Mitigation**: Documented. No immediate refactor planned — would be high-risk.
**Blast radius**: N/A (architectural debt)

### E. In-Place Mutation — ACKNOWLEDGED
**Issue**: `_hydrate_run_state()` mutates passed object in place, making state tracking harder.
**Mitigation**: Documented. Current pattern is used throughout runtime modules.
**Blast radius**: N/A (pattern consistency)

### F. `default=str` in JSON Serializers — ACCEPTED
**Issue**: Silent conversion of unhandled types to strings could mask bugs.
**Rationale**: Necessary for datetime/enum/Path serialization. Errors would crash the MCP server.
**Blast radius**: utils.py

## Test Coverage Map

| File | Tests | Coverage Focus |
|------|-------|---------------|
| test_artifacts_and_exports.py | 3 | Artifact sync, export/import round-trip, path traversal |
| test_mcp_interface.py | 3 | stdio/HTTP transport, tool listing, full reflect round-trip |
| test_migrations_and_memory.py | 7 | Migrations, memory CRUD, datetime parsing, Windows paths |
| test_runtime_service.py | 18 | Reflect, diff analyze, sweep, anchors, transitions, state mgmt |
| **Total** | **31** | |

**Gaps**: No isolated runtime/ module tests, no concurrency stress tests, no resource 404 tests.

## Change Safety Guide

| If you change... | You must also check... | Tests to run |
|-------------------|----------------------|------------|
| `models.py` | `repository.py` SQL, `migrations/*.sql`, `service.py` state mutations | All tests |
| `migrations/*.sql` | `repository.py` matching tables/columns | `test_migrations_and_memory.py` |
| `db.py` | `repository.py` execute patterns, `app.py` lifespan | All tests |
| `service.py` | `app.py` tool signatures, `runtime/*` imports | All tests |
| `runtime/*.py` | `service.py` call sites, output shapes | `test_runtime_service.py` |
| `app.py` | `cli.py` entry points, `tests/test_mcp_interface.py` | `test_mcp_interface.py` |
| `config.py` | `db.py` default paths, `tests/conftest.py` fixtures | All tests |
| `utils.py` | `repository.py` JSON columns, `service.py` serialization | All tests |
