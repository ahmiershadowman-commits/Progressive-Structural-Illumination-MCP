# Tool, Resource, and Prompt Reference

## Tools

- `psi.reflect`: full PSI pass over a task, draft, diff, or issue
- `psi.run.start`: create or resume a run
- `psi.run.get_state`: compact and full run-state
- `psi.event.record`: persist a visibility event
- `psi.friction.type`: classify friction and route regimes
- `psi.sweep.run`: weighted coherence sweep with blast-radius scoring
- `psi.anchor.register`: create or update an anchor
- `psi.anchor.invalidate`: invalidate or downgrade an anchor
- `psi.hypothesis.update`: manage hypotheses and tensions
- `psi.discriminator.record`: persist a discriminator
- `psi.transition.set`: set or recommend the next transition
- `psi.memory.retrieve`: FTS-backed retrieval across typed lanes
- `psi.memory.commit`: commit method, user, project, or run memory
- `psi.compliance.check`: run the pre-emission PSI compliance checker
- `psi.artifacts.sync`: regenerate artifact snapshots from live state
- `psi.export.run`: export a run bundle
- `psi.import.run`: import a run bundle
- `psi.diff.analyze`: detect local patch drift and durability risk in diffs
- `psi.test_failure.ingest`: convert failing tests into PSI state
- `psi.project.snapshot`: capture a durable project snapshot
- `psi.dead_end.record`: persist dead ends and learnings
- `psi.regime.explain`: explain PSI control regimes
- `psi.summary.generate`: generate expert/plain summaries
- `psi.source.audit`: normalize source intake, duplicates, stale references, and canonical grounding
- `psi.structure.extract`: return authoritative components, state variables, primitive operators, and interlocks
- `psi.trace.run`: return forward traces and blocking cascades
- `psi.gap.analyze`: return gap-origin and pressure analysis
- `psi.search.plan`: return targeted search plans for unresolved objects
- `psi.basin.generate`: return competing hypothesis basins
- `psi.stress.run`: run skeptic/anti-pattern stress and compliance

## Resources

Exact resources:

- `psi://method/current`
- `psi://method/question-operators`
- `psi://method/ai-contract`
- `psi://method/normalization-map`
- `psi://method/control-families`
- `psi://method/mode-profiles`

Templated resources:

- `psi://project/{project_id}/summary`
- `psi://project/{project_id}/anchors`
- `psi://project/{project_id}/tensions`
- `psi://project/{project_id}/constraints`
- `psi://run/{run_id}/state`
- `psi://run/{run_id}/sources`
- `psi://run/{run_id}/components`
- `psi://run/{run_id}/interlocks`
- `psi://run/{run_id}/traces`
- `psi://run/{run_id}/gaps`
- `psi://run/{run_id}/stress`
- `psi://run/{run_id}/events`
- `psi://run/{run_id}/sweeps`
- `psi://run/{run_id}/artifacts`
- `psi://run/{run_id}/claims`
- `psi://run/{run_id}/compliance`
- `psi://run/{run_id}/summary`

## Prompts

- `start_psi_pass`
- `resume_psi_pass`
- `run_visibility_event`
- `run_coherence_sweep`
- `run_audit_pass`
- `run_construction_pass`
- `prepare_transition_decision`
- `prepare_halt_decision`
