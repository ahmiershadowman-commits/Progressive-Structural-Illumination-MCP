"""Pre-emission PSI compliance checking."""

from __future__ import annotations

from ..models import (
    ArtifactSnapshot,
    ArtifactType,
    ComplianceIssue,
    ComplianceReport,
    DurabilityClass,
    FrictionType,
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

    if not run_state.state.C:
        issues.append(
            ComplianceIssue(
                issue_type="untyped_claims",
                severity="warning",
                blocking=False,
                message="No typed claims are present; load-bearing claims should be provenance-tagged.",
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

    blocking = any(issue.blocking for issue in issues)
    status = "BLOCKED" if blocking else ("WARN" if issues else "PASS")
    requested_action = ""
    if any(issue.issue_type == "missing_artifacts" for issue in issues):
        requested_action = "sync_artifacts"
    if any(issue.issue_type in {"summary_without_structure", "missing_structure"} for issue in issues):
        requested_action = "rebuild_structure"
    if any(issue.issue_type == "source_grounding" for issue in issues):
        requested_action = "run_source_audit"
    if any(issue.issue_type in {"stale_anchor_reuse", "untyped_friction", "local_update_prohibition"} for issue in issues):
        requested_action = "run_sweep"
    if any(issue.issue_type in {"durability_misuse", "known_bad_continuity"} for issue in issues):
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
