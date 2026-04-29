"""Pre-emission PSI compliance checking."""

from __future__ import annotations

from ..models import (
    ArtifactSnapshot,
    ArtifactType,
    ComplianceIssue,
    ComplianceReport,
    DurabilityClass,
    PsiRunState,
    TransitionDecision,
)


CORE_STABLE_ARTIFACTS = {
    ArtifactType.SOURCE_REGISTER,
    ArtifactType.SCOPE_LOCK,
    ArtifactType.FIELD_STATE_REGISTER,
    ArtifactType.VISIBILITY_EVENT_LOG,
    ArtifactType.COHERENCE_SWEEP_LOG,
    ArtifactType.ANCHOR_REGISTER,
    ArtifactType.FRICTION_TYPE_LOG,
    ArtifactType.HYPOTHESIS_BASIN_LEDGER,
}

STRUCTURAL_ARTIFACTS = {
    ArtifactType.SOURCE_REGISTER,
    ArtifactType.COMPONENT_LEDGER,
    ArtifactType.STATE_VARIABLE_LEDGER,
    ArtifactType.OPERATOR_LEDGER,
    ArtifactType.DEPENDENCY_AND_INTERLOCK_MAP,
    ArtifactType.TRACE_LEDGER,
    ArtifactType.HYPOTHESIS_BASIN_LEDGER,
    ArtifactType.STRESS_TEST_REPORT,
}


def evaluate_compliance(
    run_state: PsiRunState,
    artifacts: list[ArtifactSnapshot] | None = None,
    action: str = "reflect",
) -> ComplianceReport:
    artifacts = artifacts or []
    issues: list[ComplianceIssue] = []
    available_artifacts = {artifact.artifact_type for artifact in artifacts}
    stable_output = action in {"summary", "export", "artifact_promotion"} or run_state.state.transition.decision in {
        TransitionDecision.ANCHOR,
        TransitionDecision.HALT,
    }

    if stable_output:
        missing = sorted(artifact.value for artifact in CORE_STABLE_ARTIFACTS if artifact not in available_artifacts)
        if missing:
            issues.append(
                ComplianceIssue(
                    issue_type="missing_artifacts",
                    severity="error",
                    blocking=action in {"summary", "export"} or run_state.state.transition.decision == TransitionDecision.HALT,
                    message="Stable emission requires the core artifact set; summary is not structure.",
                    related_entities=missing,
                )
            )
        non_authoritative = sorted(
            artifact.artifact_type.value
            for artifact in artifacts
            if artifact.artifact_type in STRUCTURAL_ARTIFACTS and not artifact.authoritative
        )
        if non_authoritative:
            issues.append(
                ComplianceIssue(
                    issue_type="summary_without_structure",
                    severity="error",
                    blocking=True,
                    message="Stable emission is attempting to lean on degraded fallback ledgers rather than authoritative typed structure.",
                    related_entities=non_authoritative,
                )
            )

    if not run_state.state.applicability.applicable:
        issues.append(
            ComplianceIssue(
                issue_type="applicability_boundary",
                severity="error" if stable_output else "warning",
                blocking=stable_output,
                message="Phase 0 applicability boundary says the current target should be rescoped before stable PSI emission.",
                related_entities=run_state.state.applicability.failure_modes[:6],
            )
        )

    if not run_state.state.current_phase or not run_state.state.next_gating_condition:
        issues.append(
            ComplianceIssue(
                issue_type="state_management",
                severity="error" if stable_output else "warning",
                blocking=stable_output,
                message="Live run-state is missing current phase or next gating condition.",
            )
        )

    structure_gaps: list[str] = []
    if not run_state.state.sources:
        structure_gaps.append("sources")
    if not run_state.state.components:
        structure_gaps.append("components")
    if not run_state.state.state_variables:
        structure_gaps.append("state_variables")
    if not run_state.state.primitive_operators:
        structure_gaps.append("primitive_operators")
    if not run_state.state.interlocks:
        structure_gaps.append("interlocks")
    if not run_state.state.traces:
        structure_gaps.append("traces")
    if not run_state.state.basins:
        structure_gaps.append("basins")
    if stable_output and structure_gaps:
        issues.append(
            ComplianceIssue(
                issue_type="missing_structure",
                severity="error",
                blocking=True,
                message="Stable emission requires authoritative methodology objects, not only a summary surface.",
                related_entities=structure_gaps,
            )
        )

    open_artifacts = [artifact.value for artifact in run_state.state.open_artifacts]
    if stable_output and open_artifacts:
        issues.append(
            ComplianceIssue(
                issue_type="open_artifacts",
                severity="error",
                blocking=True,
                message="Stable emission is blocked while required artifacts are missing or non-authoritative.",
                related_entities=open_artifacts[:10],
            )
        )

    source_issues = [
        f"{source.id}:{issue}"
        for source in run_state.state.sources
        for issue in source.metadata.get("audit_issues", [])
    ]
    if source_issues:
        blocking_source_issues = [
            issue
            for issue in source_issues
            if any(token in issue for token in {"stale_reference:", "missing_artifact:", "missing_locator"})
        ]
        issues.append(
            ComplianceIssue(
                issue_type="source_grounding",
                severity="error" if blocking_source_issues else "warning",
                blocking=bool(blocking_source_issues and stable_output),
                message="Source intake normalization surfaced unresolved provenance or artifact problems.",
                related_entities=(blocking_source_issues or source_issues)[:10],
            )
        )

    scaffold_violations = [
        claim.statement
        for claim in run_state.state.C
        if claim.scaffold_boundary
        and (not claim.scaffold_boundary.bounded or claim.scaffold_boundary.substitute_for_real_structure)
        and claim.load_bearing
    ]
    if scaffold_violations:
        issues.append(
            ComplianceIssue(
                issue_type="bounded_scaffold_violation",
                severity="error",
                blocking=stable_output,
                message="Load-bearing temporary scaffolds must be explicit, bounded, and non-substitutive.",
                related_entities=scaffold_violations[:6],
            )
        )

    if not run_state.state.C:
        issues.append(
            ComplianceIssue(
                issue_type="untyped_claims",
                severity="warning",
                blocking=False,
                message="No typed claims are present; load-bearing claims should be provenance-tagged.",
            )
        )

    basin_gaps = [
        basin.title
        for basin in run_state.state.basins
        if not basin.explanatory_burden or not basin.weakening_conditions or not basin.discriminator_path
    ]
    if stable_output and basin_gaps:
        issues.append(
            ComplianceIssue(
                issue_type="basin_burden",
                severity="error",
                blocking=True,
                message="Stable emission requires live basins to expose burden, weakening conditions, and discriminator paths.",
                related_entities=basin_gaps[:6],
            )
        )
    else:
        unknown_load_bearing = [
            claim.statement
            for claim in run_state.state.C
            if claim.load_bearing and claim.provenance.value == "UNKNOWN"
        ]
        if unknown_load_bearing:
            issues.append(
                ComplianceIssue(
                    issue_type="untyped_claims",
                    severity="warning",
                    blocking=False,
                    message="Some load-bearing claims remain UNKNOWN rather than being typed by provenance.",
                    related_entities=unknown_load_bearing[:6],
                )
            )

    if run_state.state.N.blocked:
        durable_entities = [
            anchor.name
            for anchor in run_state.state.A
            if anchor.durability_class == DurabilityClass.DURABLE
        ] + [
            hypothesis.title
            for hypothesis in run_state.state.H
            if hypothesis.durability_class == DurabilityClass.DURABLE
        ] + [
            claim.statement
            for claim in run_state.state.C
            if claim.durability_class == DurabilityClass.DURABLE
        ]
        if durable_entities:
            issues.append(
                ComplianceIssue(
                    issue_type="durability_misuse",
                    severity="error",
                    blocking=True,
                    message="Durable reuse labels were assigned while the durability gate is blocked.",
                    related_entities=durable_entities[:8],
                )
            )

    stale_anchors = [anchor.name for anchor in run_state.state.A if anchor.status == "invalidated"]
    if stale_anchors:
        issues.append(
            ComplianceIssue(
                issue_type="stale_anchor_reuse",
                severity="error" if stable_output else "warning",
                blocking=stable_output,
                message="Invalidated anchors remain visible in the active field and must not be silently reused.",
                related_entities=stale_anchors[:8],
            )
        )

    if run_state.state.O and run_state.state.O.type in {"friction", "failure", "contradiction"} and not run_state.state.F:
        issues.append(
            ComplianceIssue(
                issue_type="untyped_friction",
                severity="error",
                blocking=True,
                message="A failure-like event is active but no typed friction is recorded.",
            )
        )

    if any(claim.source == "diff" and claim.load_bearing for claim in run_state.state.C):
        if not run_state.state.W.dependencies_changed or all(
            "no central destabilization" in item.lower() for item in run_state.state.W.dependencies_changed
        ):
            issues.append(
                ComplianceIssue(
                    issue_type="local_update_prohibition",
                    severity="error",
                    blocking=True,
                    message="A load-bearing diff claim exists without a credible field-impact articulation.",
                )
            )

    if any(
        claim.durability_class == DurabilityClass.POISONED and claim.provenance.value != "UNKNOWN"
        for claim in run_state.state.C
    ):
        issues.append(
            ComplianceIssue(
                issue_type="known_bad_continuity",
                severity="error",
                blocking=True,
                message="Known-bad continuity remains active in typed claims.",
            )
        )

    if run_state.state.uncertainty.propagation_limits and not run_state.state.uncertainty.partial_propagation_warnings:
        issues.append(
            ComplianceIssue(
                issue_type="uncertainty_honesty",
                severity="warning",
                blocking=False,
                message="Propagation limits are present but the partial-propagation warning surface is empty.",
            )
        )

    blocking = any(issue.blocking for issue in issues)
    status = "BLOCKED" if blocking else ("WARN" if issues else "PASS")
    requested_action = ""
    if any(issue.issue_type == "missing_artifacts" for issue in issues):
        requested_action = "sync_artifacts"
    if any(issue.issue_type in {"summary_without_structure", "missing_structure"} for issue in issues):
        requested_action = "rebuild_structure"
    if any(issue.issue_type == "source_grounding" for issue in issues):
        requested_action = "run_source_audit"
    if any(issue.issue_type == "applicability_boundary" for issue in issues):
        requested_action = "rescope"
    if any(issue.issue_type in {"stale_anchor_reuse", "untyped_friction", "local_update_prohibition"} for issue in issues):
        requested_action = "run_sweep"
    if any(issue.issue_type in {"durability_misuse", "known_bad_continuity"} for issue in issues):
        requested_action = "rollback"
    if any(issue.issue_type in {"open_artifacts", "bounded_scaffold_violation", "basin_burden"} for issue in issues):
        requested_action = "rollback"
    notes = [
        "Compliance checks verify state integrity after routing; they do not replace reasoning.",
        "Hard gates and soft heuristics remain distinct.",
    ]
    return ComplianceReport(
        status=status,
        blocking=blocking,
        requested_action=requested_action,
        issues=issues,
        checked_artifacts=sorted(artifact.value for artifact in available_artifacts),
        notes=notes,
    )
