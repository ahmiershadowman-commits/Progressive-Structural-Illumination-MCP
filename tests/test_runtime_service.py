from __future__ import annotations

from pathlib import Path


def _fixture_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_architecture_design_with_ambiguity(service):
    result = service.reflect(
        task="Design a local MCP server with typed persistence, hidden dependency tracking, and scope boundaries that may need revision.",
        project_name="Architecture Project",
    )
    assert result["transition_recommendation"]["decision"] in {"CONTINUE", "RESCOPE"}
    assert result["active_lens_summary"]["object_in_play"] in {"architecture", "revision", "structural-question"}
    assert result["whole_field_impact_summary"]
    assert result["typed_claims"]
    assert result["control_families"]
    assert result["compliance_report"]["status"] in {"PASS", "WARN", "BLOCKED"}


def test_code_patch_triggers_continuity_poison(service):
    diff = _fixture_text(Path(__file__).parent / "fixtures" / "continuity_poison.diff")
    result = service.diff_analyze(diff=diff, task="Review the patch for PSI continuity issues")
    assert result["local_patch_drift_risk"] is True
    assert "CONTINUITY_POISON" in result["friction_types"]


def test_debugging_session_types_structural_mismatch(service):
    result = service.reflect(
        task="The local fix passes in one module but causes global incoherence and a topology mismatch in the runtime.",
        project_name="Debug Project",
    )
    assert "STRUCTURAL_MISMATCH" in result["friction_types"]


def test_scope_expansion_prefers_rescope(service):
    result = service.reflect(
        task="The scope boundary widened and we need to reframe the project boundary before continuing.",
        project_name="Scope Project",
    )
    assert result["transition_recommendation"]["decision"] == "RESCOPE"


def test_substrate_failure_can_escalate(service):
    task = "\n".join(
        [
            "Build failed with dependency break.",
            "Import error raised an exception.",
            "Compile timeout makes the current trace unreliable.",
            "The build failure cannot be reproduced from the current context alone.",
        ]
    )
    result = service.reflect(task=task, project_name="Failure Project")
    assert result["transition_recommendation"]["decision"] == "ESCALATE"
    assert "SUBSTRATE_FRICTION" in result["friction_types"]


def test_anchor_invalidation_after_new_evidence(service, repository):
    started = service.start_run(title="Anchors", scope="Track anchors", project_name="Anchor Project")
    project_id = started["project_id"]
    run_id = started["run_id"]
    anchor = service.register_anchor(
        name="schema contract",
        description="The schema contract is currently stable.",
        project_id=project_id,
        run_id=run_id,
        centrality=0.9,
        fragility=0.8,
    )
    invalidated = service.invalidate_anchor(
        anchor_id=anchor["id"],
        reason="New evidence broke the schema assumption.",
        run_id=run_id,
        project_id=project_id,
    )
    assert invalidated["status"] == "invalidated"
    supersessions = repository.database.connection.execute(
        "SELECT COUNT(*) AS count FROM supersession_history WHERE entity_id = ?",
        (anchor["id"],),
    ).fetchone()["count"]
    assert supersessions == 1


def test_ai_local_update_prohibition_failure_case(service):
    diff = "diff --git a/app.py b/app.py\n+ change one line without field impact"
    result = service.diff_analyze(diff=diff, task="Local one-line patch without impact statement")
    assert result["local_patch_drift_risk"] is True


def test_test_failure_ingest_records_substrate_friction(service):
    started = service.start_run(title="Tests", scope="Debug failing tests", project_name="Tests Project")
    run_id = started["run_id"]
    failure_log = _fixture_text(Path(__file__).parent / "fixtures" / "test_failure.log")
    result = service.ingest_test_failure(run_id=run_id, failure_log=failure_log)
    assert result["event"]["type"] == "failure"
    assert any(item["friction_type"] == "SUBSTRATE_FRICTION" for item in result["friction_types"])


def test_project_snapshot_captures_project_context(service):
    started = service.start_run(title="Snapshot", scope="Create project snapshot", project_name="Snapshot Project")
    project_id = started["project_id"]
    service.register_anchor(
        name="field register",
        description="State register must stay synced.",
        project_id=project_id,
        run_id=started["run_id"],
    )
    snapshot = service.project_snapshot(project_id=project_id, run_id=started["run_id"], title="baseline")
    assert snapshot["title"] == "baseline"
    assert snapshot["summary"]["project"]["project_id"] == project_id


def test_anchor_and_hypothesis_accept_durability_classes(service):
    started = service.start_run(title="Durability", scope="Track reusable structure", project_name="Durability Project")
    project_id = started["project_id"]
    run_id = started["run_id"]
    anchor = service.register_anchor(
        name="native runtime boundary",
        description="The runtime boundary is durable enough to reuse.",
        project_id=project_id,
        run_id=run_id,
        durability_class="DURABLE",
    )
    hypothesis = service.update_hypothesis(
        item_type="hypothesis",
        action="add",
        title="partial repair path",
        description="This remains provisional until a discriminator lands.",
        project_id=project_id,
        run_id=run_id,
        durability_class="CONDITIONAL",
    )
    assert anchor["durability_class"] == "DURABLE"
    assert hypothesis["durability_class"] == "CONDITIONAL"


def test_summary_generation_surfaces_compliance(service):
    result = service.reflect(
        task="Audit the current construction and verify it can emit stable output.",
        project_name="Summary Project",
    )
    summary = service.generate_summary(result["run_id"])
    assert "compliance_report" in summary
    assert summary["compliance_report"]["status"] in {"PASS", "WARN", "BLOCKED"}


def test_operator_and_provenance_extensions_are_available(service):
    result = service.reflect(
        task="What changed, and what literally happens at the boundary?",
        attached_context="Grounded evidence: reproduced failure with direct evidence from the source note.",
        project_name="Operator Project",
    )
    assert "exposure" in result["operator_families"]
    provenances = {claim["provenance"] for claim in result["typed_claims"]}
    assert "SOURCE" in provenances or "GROUNDED" in provenances


def test_state_management_and_transition_alias_are_canonical(service):
    result = service.reflect(
        task="Track an architecture repair with ambiguity, field impact, and exportable artifacts.",
        project_name="Control State Project",
    )
    run_id = result["run_id"]
    state = service.get_run_state(run_id)
    assert state["compact"]["run_class"] in {"exploratory", "working", "canonical"}
    assert state["compact"]["current_phase"]
    assert state["compact"]["next_gating_condition"]
    transition = service.set_transition(run_id, decision="ROLLBACK", rationale="legacy alias input")
    assert transition["decision"] == "ROLLBACK_REQUIRED"


def test_start_run_creates_or_resumes_explicit_run_id(service):
    run_id = "psi-smoke-explicit-20260429-001"

    started = service.start_run(
        title="Explicit run",
        scope="Create a caller-addressable PSI run.",
        project_name="Explicit Run Project",
        run_id=run_id,
    )
    resumed = service.start_run(
        title="Ignored on resume",
        scope="Resume the same caller-addressable PSI run.",
        project_name="Explicit Run Project",
        run_id=run_id,
    )

    assert started["run_id"] == run_id
    assert started["resumed"] is False
    assert service.get_run_state(run_id)["compact"]["run_id"] == run_id
    assert resumed["run_id"] == run_id
    assert resumed["resumed"] is True


def test_reflect_preserves_new_explicit_run_id(service):
    run_id = "psi-reflect-explicit-20260429-001"

    result = service.reflect(
        task="Use the caller-supplied run id when opening a new reflected PSI pass.",
        project_name="Explicit Reflect Project",
        run_id=run_id,
    )

    assert result["run_id"] == run_id
    assert service.get_run_state(run_id)["compact"]["run_id"] == run_id


def test_source_audit_detects_duplicates_and_missing_artifacts(service):
    missing_path = r"C:\definitely-missing\psi_contract.md"
    result = service.reflect(
        task=missing_path,
        attached_context=missing_path,
        project_name="Source Audit Project",
    )
    audit = service.source_audit(result["run_id"])
    assert audit["audit"]["duplicates"] >= 1
    assert audit["audit"]["missing_artifacts"] >= 1
    assert any("missing_artifact:" in issue for issue in audit["audit"]["issues"])


def test_source_audit_handles_spaced_paths_without_false_posix_noise(service, tmp_path: Path):
    source_dir = tmp_path / "folder with spaces"
    source_dir.mkdir()
    source_file = source_dir / "canonical note.md"
    source_file.write_text("canonical evidence", encoding="utf-8")
    result = service.reflect(
        task="Validate grounded source intake.",
        attached_context=f"Grounded source: {source_file}\nTyped claim surface: INFERRED/PROVISIONAL.",
        project_name="Path Audit Project",
    )
    audit = service.source_audit(result["run_id"])
    issues = audit["audit"]["issues"]
    assert audit["audit"]["stale_references"] == 0
    assert audit["audit"]["missing_artifacts"] == 0
    assert not any("/PROVISIONAL" in issue for issue in issues)
    assert not any(issue == f"missing_artifact:{source_file}" for issue in issues)
    assert not any(issue == f"stale_reference:{source_file}" for issue in issues)


def test_direct_regime_tools_return_authoritative_structures(service):
    result = service.reflect(
        task="Trace the dependency field and preserve competing basins for this architecture change.",
        project_name="Direct Regime Project",
    )
    run_id = result["run_id"]
    structure = service.structure_extract(run_id)
    traces = service.trace_run(run_id)
    gaps = service.gap_analyze(run_id)
    searches = service.search_plan(run_id)
    basins = service.basin_generate(run_id)
    stress = service.stress_run(run_id)
    assert structure["components"]
    assert structure["interlocks"]
    assert traces["traces"]
    assert gaps["gaps"] is not None
    assert searches["search_records"] is not None
    assert basins["basins"]
    assert stress["compliance_report"]["status"] in {"PASS", "WARN", "BLOCKED"}
