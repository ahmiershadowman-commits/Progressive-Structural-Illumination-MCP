# Export / Import Example

## Export

```text
psi.export.run(run_id="run_...")
```

This writes a bundle directory containing:

- `bundle.json`
- `bundle.yaml`
- `artifacts/*.md`

## Import

```text
psi.import.run(import_path="C:\\path\\to\\bundle.json")
```

Imported content includes:

- run-state
- summary
- visibility events
- friction logs
- sweep logs
- anchors
- tensions
- hypotheses
- discriminators
- constraints
- committed project and run memory
- artifacts
