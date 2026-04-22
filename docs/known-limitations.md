# Known Limitations

1. The PSI analysis is deterministic and heuristic. It preserves structure and pressure explicitly, but it does not replace the host model's semantic reasoning.

2. Sweep weighting is currently configured in code. There is no user-facing weight profile editor yet.

3. Export/import restores runs, entities, artifacts, sweeps, and committed memory, but it does not replay prior export history rows.

4. Method-lane content is a condensed operational seed, not a verbatim mirror of the full source methodology document.

5. Resources open against the same local SQLite state through a read-only service path rather than reusing tool lifespan context.
