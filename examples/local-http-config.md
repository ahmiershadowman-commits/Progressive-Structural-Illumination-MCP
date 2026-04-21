# Local HTTP Usage

Run the server:

```powershell
uv run psi-coprocessor-mcp http --port 8765
```

Connect the host to:

```text
http://127.0.0.1:8765/mcp
```

Recommended use:

- call `psi.reflect` before finalizing plans, patches, or designs
- call `psi.artifacts.sync` when a run stabilizes
- call `psi.export.run` before moving the run between machines or databases
