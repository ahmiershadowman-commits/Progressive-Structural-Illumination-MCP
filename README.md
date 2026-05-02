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

**No clone needed.** Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (free, one-time install).

**Claude Desktop / Cursor / Windsurf / LM Studio / Jan AI / OpenCode / Codex / Gemini CLI** — see [full installation guide](docs/installation.md) for step-by-step instructions per client.

**Claude Desktop (quick version):** add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

Or run directly:

```sh
uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp stdio
```

For HTTP (multi-client or Open WebUI):

```sh
uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp http --port 8765
```

**Making your AI use it automatically:** add the [auto-use template](docs/installation.md#auto-use-template) to `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` / `.windsurfrules` / `.cursor/rules/` in your project, or paste the [system prompt](examples/system_prompt.md) into LM Studio / Jan AI / Qwen.

## Updating

`uvx` caches by git SHA. Pull the latest version with:

```sh
uvx --refresh --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp diagnose
```

Then restart your MCP host. Run history and database are untouched — migrations apply automatically.

## Local Dev

```powershell
uv sync --extra dev
uv run psi-coprocessor-mcp diagnose
uv run psi-coprocessor-mcp stdio
```

If you're on Windows with OneDrive sync and hit hardlink errors, prefix with `$env:UV_LINK_MODE = "copy"`.

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

Current test status: `35 passed`
