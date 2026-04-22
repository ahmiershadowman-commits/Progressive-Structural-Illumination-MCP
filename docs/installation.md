# Installation

## Requirements

- Python 3.11+
- `uv`
- no cloud services
- no remote accounts

## Local Setup

```powershell
uv sync --extra dev
uv run psi-coprocessor-mcp diagnose
```

If you run `uv` commands from a Windows synced folder such as OneDrive, set:

```powershell
$env:UV_LINK_MODE = "copy"
```

before `uv sync`, `uv run`, or `uv build` to avoid hardlink failures in the uv cache.

The server stores local state in:

- Windows default: `%LOCALAPPDATA%\psi-coprocessor-mcp`
- override with `PSI_MCP_DATA_DIR`

Optional environment variables:

- `PSI_MCP_DATA_DIR`
- `PSI_MCP_DB_PATH`
- `PSI_MCP_EXPORT_DIR`
- `PSI_MCP_DURABILITY_MODE`
- `PSI_MCP_HTTP_HOST`
- `PSI_MCP_HTTP_PORT`
- `PSI_MCP_HTTP_PATH`
- `PSI_MCP_LOG_LEVEL`
- `PSI_MCP_SEED_USER_LANE`

`PSI_MCP_DATA_DIR`, `PSI_MCP_DB_PATH`, and `PSI_MCP_EXPORT_DIR` support `%VAR%` and `~` expansion on the server side.

## Running

### STDIO

```powershell
uv run psi-coprocessor-mcp stdio
```

### Streamable HTTP

```powershell
uv run psi-coprocessor-mcp http --port 8765
```

The HTTP endpoint is exposed at `/mcp`.

## Host Examples

See:

- [Claude Desktop config](../examples/claude-desktop-config.json)
- [Local HTTP config notes](../examples/local-http-config.md)

## Validation

```powershell
uv run pytest
```
