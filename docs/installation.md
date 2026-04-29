# Installation

## Requirements

- Python 3.11+
- `uv`
- no cloud services
- no remote accounts

## Install from GitHub (no clone required)

Any MCP-capable agent or host can install directly from the repo:

```sh
uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp stdio
```

### Claude Desktop

Paste this into your `claude_desktop_config.json`:

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

Data is stored automatically in `%LOCALAPPDATA%\psi-coprocessor-mcp` on Windows or `~/.psi-coprocessor-mcp` on macOS/Linux. Override with `PSI_MCP_DATA_DIR` if you want a custom location.

## Updating

`uvx` caches the git installation by resolved SHA. To pull the latest version from `main`, run:

```sh
uvx --refresh --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp diagnose
```

After that command completes, restart Claude Desktop (or whichever MCP host you use) and the new version is active. Your SQLite database and run history are unaffected — migrations run automatically on first connect with the new build.

## Local Dev Setup

Clone the repo, then:

```powershell
uv sync --extra dev
uv run psi-coprocessor-mcp diagnose
```

If you run `uv` commands from a Windows synced folder such as OneDrive, set:

```powershell
$env:UV_LINK_MODE = "copy"
```

before `uv sync`, `uv run`, or `uv build` to avoid hardlink failures in the uv cache.

## Data Location

- Windows default: `%LOCALAPPDATA%\psi-coprocessor-mcp`
- macOS/Linux default: `~/.psi-coprocessor-mcp`
- Override with `PSI_MCP_DATA_DIR`

## Environment Variables

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

## Running (local dev)

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
