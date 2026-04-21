# Troubleshooting

## The host cannot connect over stdio

- Run `uv run psi-coprocessor-mcp diagnose`
- Confirm the host launches from the repo root
- Confirm `uv sync --extra dev` completed successfully

## The host cannot connect over HTTP

- Confirm the server is running: `uv run psi-coprocessor-mcp http --port 8765`
- Confirm the client targets `http://127.0.0.1:8765/mcp`
- Check whether another process already owns the port

## Resource reads fail

- Confirm the database path in `diagnose` points to the expected local state
- Ensure the referenced run or project already exists

## Export or import fails

- Sync artifacts before export: `psi.artifacts.sync`
- Import from `bundle.json` or `bundle.yaml`
- Confirm the imported database path is writable

## Durability gate blocks a move unexpectedly

- Inspect `durability_assessment` in the tool output
- Look for placeholder, scaffold, mock, or rewrite-debt language in the provided text
- Switch to advisory mode only when you explicitly want warnings instead of hard blocking
