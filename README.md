# PSI Coprocessor MCP

PSI Coprocessor MCP is a local-first Model Context Protocol server that operationalizes Progressive Structural Illumination as a persistent cognitive coprocessor for code, architecture, debugging, and research work.

Canonical implementation authority is defined by the source pair documented in `docs/canonical-source-corpus.md`, not by derivative notes or repo-local summaries.

It ships as a typed Python package with:

- FastMCP tools, resources, and prompts
- direct regime tools for source audit, structure extraction, tracing, gap analysis, search planning, basin generation, and stress passes
- explicit PSI run-state
- normalization-map control layer with mode-weighted control families
- SQLite persistence with migrations and FTS5 retrieval
- artifact regeneration from live state
- import/export
- stdio and streamable-HTTP transports
- unit and integration tests

## Quick Start

```powershell
uv sync --extra dev
uv run psi-coprocessor-mcp diagnose
uv run psi-coprocessor-mcp stdio
```

If you run `uv` commands from a Windows synced folder such as OneDrive and hit a hardlink error, use:

```powershell
$env:UV_LINK_MODE = "copy"
uv sync --extra dev
```

For streamable HTTP:

```powershell
uv run psi-coprocessor-mcp http --port 8765
```

Recommended host routing instruction:

> When a task involves ambiguity, hidden dependencies, contradiction, scope drift, architecture design, debugging dead ends, or revision of prior conclusions, call `psi.reflect` before finalizing a plan, patch, or design.

## Documentation

- [Installation](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Canonical Source Corpus](docs/canonical-source-corpus.md)
- [Build Contract Coverage Audit](docs/build-contract-coverage-audit.md)
- [Tool / Resource / Prompt Reference](docs/tool-resource-prompt-reference.md)
- [Schema Reference](docs/schema-reference.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Known Limitations](docs/known-limitations.md)
- [Export / Import Example](examples/export-import-example.md)

## Validation

```powershell
uv run pytest
```

Current test status: `24 passed`
