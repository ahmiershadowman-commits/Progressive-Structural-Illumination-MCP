"""Deterministic artifact generation from live PSI state."""

from __future__ import annotations

from textwrap import indent

import yaml

from ..models import ARTIFACT_SEQUENCE, ArtifactPointers, ArtifactSnapshot, ArtifactType, PsiRunState
from ..utils import sha256_text, utc_now


def _bullet(lines: list[str]) -> str:
    if not lines:
        return "- none"
    return "\n".join(f"- {line}" for line in lines)


def _anchor_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{anchor.name} [{anchor.status}] centrality={anchor.centrality:.2f} fragility={anchor.fragility:.2f}"
        for anchor in run_state.state.A
    ]


def _tension_lines(run_state: PsiRunState) -> list[str]:
    return [f"{tension.title} [{tension.status}] severity={tension.severity:.2f}" for tension in run_state.state.U]


def _hypothesis_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{hypothesis.title} [{hypothesis.status}] confidence={hypothesis.confidence.value} "
        f"burden={'; '.join(hypothesis.explanatory_burden[:2]) or 'unspecified'}"
        for hypothesis in run_state.state.H
    ]


def _friction_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{signal.friction_type.value} severity={signal.severity:.2f} -> {signal.routing_regime.value}: {signal.rationale}"
        for signal in run_state.state.F
    ]


def _probe_lines(run_state: PsiRunState) -> list[str]:
    return [f"{probe.title} (value={probe.revelatory_value:.2f}) {probe.rationale}" for probe in run_state.state.P]


def _claim_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{claim.provenance.value}:{claim.structural_role or 'claim'} durability={claim.durability_class.value} "
        f"load_bearing={'yes' if claim.load_bearing else 'no'} "
        f"axes={claim.confidence_axes.evidence_confidence.value}/{claim.confidence_axes.causal_confidence.value}/"
        f"{claim.confidence_axes.scope_confidence.value}/{claim.confidence_axes.representation_confidence.value} "
        f":: {claim.statement}"
        for claim in run_state.state.C
    ]


def _component_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{component.name} kind={component.component_kind or 'structural-object'} scope={component.scope or 'run'}"
        for component in run_state.state.components
    ]


def _state_variable_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{state_variable.name} kind={state_variable.variable_kind or 'state'} timescale={state_variable.timescale or 'unspecified'}"
        for state_variable in run_state.state.state_variables
    ]


def _primitive_operator_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{operator.name} [{operator.family.value}] trigger={operator.trigger[:60]} target={operator.target or operator.state_variable_ref}"
        for operator in run_state.state.primitive_operators
    ]


def _interlock_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{relation.source_ref} {relation.relation_type.value} {relation.target_ref}: {relation.description}"
        for relation in run_state.state.interlocks
    ]


def _trace_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"step={trace.step_index} branch={trace.branch_key or 'primary'} "
        f"{trace.operator_ref or 'operator?'} -> {trace.outcome} "
        f"[{trace.divergence_class.value if trace.divergence_class else 'in-flight'}]"
        for trace in run_state.state.traces
    ]


def _gap_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{gap.title} [{gap.gap_type.value}] origin={gap.likely_origin.value} "
        f"smallest_unit={gap.smallest_discriminative_unit or 'unspecified'} "
        f"blocking={'yes' if gap.blocking else 'no'}"
        for gap in run_state.state.gaps
    ]


def _search_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{search.status.value}: {search.query} -> "
        f"{search.smallest_discriminative_unit or search.target_object or 'smallest discriminative unresolved unit'}"
        for search in run_state.state.searches
    ]


def _basin_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{basin.title} [{basin.basin_type.value}] status={basin.status} "
        f"burden={'; '.join(basin.explanatory_burden[:2]) or 'unspecified'} "
        f"path={'; '.join(basin.discriminator_path[:2]) or 'unspecified'}"
        for basin in run_state.state.basins
    ]


def _stress_lines(run_state: PsiRunState) -> list[str]:
    skeptic = [f"SKEPTIC {finding.severity.value}: {finding.question}" for finding in run_state.state.skeptic_findings]
    antipatterns = [
        f"ANTIPATTERN {finding.pattern_type.value}: {finding.description}"
        for finding in run_state.state.antipattern_findings
    ]
    return skeptic + antipatterns


def _control_family_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{family.family.value} [{family.activation.level.value}] weight={family.activation.weight:.2f} "
        f"hard_gate={'yes' if family.hard_gate else 'no'}"
        for family in run_state.state.control_families
    ]


def _routing_lines(run_state: PsiRunState) -> list[str]:
    return [
        f"{decision.friction_type.value} -> {', '.join(regime.value for regime in decision.ordered_regimes)}"
        for decision in run_state.state.friction_routing
    ]


def _artifact_content(artifact_type: ArtifactType, context: dict[str, object]) -> tuple[str, bool]:
    run_state: PsiRunState = context["run_state"]
    summary = context["summary"]
    events = context["events"]
    sweeps = context["sweeps"]
    constraints = context["constraints"]
    source_objects = context.get("source_objects", [])
    supersessions = context.get("supersessions", [])
    if artifact_type == ArtifactType.SOURCE_REGISTER:
        sources = [
            f"{source.source_kind.value}:{source.locator or source.title} canonical={'yes' if source.canonical else 'no'} "
            f"issues={','.join(source.metadata.get('audit_issues', [])) or 'none'}"
            for source in source_objects
        ] or [event.source or event.type.value for event in events]
        return f"# source-register\n\n{_bullet(sources)}\n", bool(source_objects)
    if artifact_type == ArtifactType.SCOPE_LOCK:
        return (
            "# scope-lock\n\n"
            f"## Applicability\n- applicable={'yes' if run_state.state.applicability.applicable else 'no'}\n"
            f"- rationale={run_state.state.applicability.rationale or 'n/a'}\n"
            f"- run_class={run_state.metadata.run_class.value}\n\n"
            f"## Included\n{_bullet(run_state.state.B.included)}\n\n"
            f"## Excluded\n{_bullet(run_state.state.B.excluded)}\n\n"
            f"## Success Criteria\n{_bullet(run_state.state.B.success_criteria)}\n"
        ), True
    if artifact_type == ArtifactType.PROVISIONAL_DISTINCTION_LEDGER:
        lines = run_state.state.W.abstraction_updates + run_state.state.W.possibility_updates + _claim_lines(run_state)
        return f"# provisional-distinction-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.C)
    if artifact_type == ArtifactType.COMPONENT_LEDGER:
        lines = _component_lines(run_state) or (run_state.state.L.real_units + [anchor.name for anchor in run_state.state.A])
        return f"# component-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.components)
    if artifact_type == ArtifactType.STATE_VARIABLE_LEDGER:
        lines = _state_variable_lines(run_state) or (run_state.state.W.dependencies_changed + run_state.state.W.anchor_updates)
        return f"# state-variable-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.state_variables)
    if artifact_type == ArtifactType.OPERATOR_LEDGER:
        lines = _primitive_operator_lines(run_state) + [operator.value for operator in run_state.state.active_operators] + _control_family_lines(run_state)
        return f"# operator-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.primitive_operators)
    if artifact_type == ArtifactType.CONSTRAINT_LEDGER:
        lines = [constraint.description for constraint in constraints] + run_state.state.S.implementation
        return f"# constraint-ledger\n\n{_bullet(lines)}\n", True
    if artifact_type == ArtifactType.DEPENDENCY_AND_INTERLOCK_MAP:
        lines = _interlock_lines(run_state) or (run_state.state.W.dependencies_changed + [impact.entity_name for impact in run_state.state.current_blast_radius])
        return f"# dependency-and-interlock-map\n\n{_bullet(lines)}\n", bool(run_state.state.interlocks)
    if artifact_type == ArtifactType.TRACE_LEDGER:
        lines = _trace_lines(run_state) or ([event.description for event in events] + _claim_lines(run_state))
        return f"# trace-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.traces)
    if artifact_type == ArtifactType.GAP_AND_PRESSURE_LEDGER:
        lines = _gap_lines(run_state) + _tension_lines(run_state) + run_state.state.uncertainty.evidence_limits
        return f"# gap-and-pressure-ledger\n\n{_bullet(lines)}\n", bool(run_state.state.gaps)
    if artifact_type == ArtifactType.SEARCH_LOG:
        lines = _search_lines(run_state) or ([event.title for event in events if event.type.value in {"question", "reframe"}] + _probe_lines(run_state))
        return f"# search-log\n\n{_bullet(lines)}\n", True
    if artifact_type == ArtifactType.HYPOTHESIS_BASIN_LEDGER:
        return (
            f"# hypothesis-basin-ledger\n\n{_bullet(_basin_lines(run_state) + _hypothesis_lines(run_state) + _tension_lines(run_state))}\n",
            bool(run_state.state.basins),
        )
    if artifact_type == ArtifactType.CONSTRUCTION_SPEC:
        lines = [
            f"transition={run_state.state.transition.decision.value}",
            f"current_phase={run_state.state.current_phase.value}",
            f"run_class={run_state.metadata.run_class.value}",
            f"active_regimes={', '.join(regime.value for regime in run_state.state.active_regimes)}",
            f"next_gating_condition={run_state.state.next_gating_condition}",
            f"smallest_discriminative_unit={run_state.state.smallest_discriminative_unit or 'unspecified'}",
            f"compliance={run_state.state.compliance.status if run_state.state.compliance else 'UNKNOWN'}",
            summary.expert_summary,
        ]
        return f"# construction-spec\n\n{_bullet(lines)}\n", True
    if artifact_type == ArtifactType.STRESS_TEST_REPORT:
        compliance_lines = (
            [issue.message for issue in run_state.state.compliance.issues]
            if run_state.state.compliance
            else []
        )
        lines = (
            _friction_lines(run_state)
            + _routing_lines(run_state)
            + run_state.state.N.notes
            + [f"partial_propagation::{item}" for item in run_state.state.uncertainty.partial_propagation_warnings]
            + compliance_lines
            + _stress_lines(run_state)
        )
        return f"# stress-test-report\n\n{_bullet(lines)}\n", bool(run_state.state.skeptic_findings or run_state.state.antipattern_findings or compliance_lines)
    if artifact_type == ArtifactType.SUPERSESSION_LEDGER:
        lines = [
            f"{item['entity_type']}:{item['entity_id']} -> {item['superseded_by']} :: {item['reason']}"
            for item in supersessions
        ]
        return f"# supersession-ledger\n\n{_bullet(lines)}\n", True
    if artifact_type == ArtifactType.FINAL_SYNTHESIS:
        return (
            "# final-synthesis\n\n"
            f"## Expert Summary\n{summary.expert_summary}\n\n"
            f"## Plain Summary\n{summary.plain_summary}\n\n"
            f"## Compliance\n{run_state.state.compliance.status if run_state.state.compliance else 'UNKNOWN'}\n"
        ), True
    if artifact_type == ArtifactType.FIELD_STATE_REGISTER:
        dumped = yaml.safe_dump(run_state.machine_readable(), sort_keys=False)
        return f"# field-state-register\n\n```yaml\n{dumped}```\n", True
    if artifact_type == ArtifactType.VISIBILITY_EVENT_LOG:
        lines = [f"{event.type.value}: {event.title} -> {event.description}" for event in events]
        return f"# visibility-event-log\n\n{_bullet(lines)}\n", bool(events)
    if artifact_type == ArtifactType.COHERENCE_SWEEP_LOG:
        lines = [
            f"{sweep['id']}: {sweep['summary']} -> {sweep['transition'].get('decision', 'n/a')}"
            for sweep in sweeps
        ] + _routing_lines(run_state)
        return f"# coherence-sweep-log\n\n{_bullet(lines)}\n", bool(sweeps)
    if artifact_type == ArtifactType.ANCHOR_REGISTER:
        return f"# anchor-register\n\n{_bullet(_anchor_lines(run_state))}\n", True
    if artifact_type == ArtifactType.FRICTION_TYPE_LOG:
        return f"# friction-type-log\n\n{_bullet(_friction_lines(run_state))}\n", bool(run_state.state.F)
    raise ValueError(f"Unsupported artifact type: {artifact_type.value}")


def generate_artifacts(context: dict[str, object]) -> tuple[list[ArtifactSnapshot], ArtifactPointers]:
    run_state: PsiRunState = context["run_state"]
    now = utc_now()
    pointers = ArtifactPointers()
    artifacts: list[ArtifactSnapshot] = []
    for artifact_type in ARTIFACT_SEQUENCE:
        content, authoritative = _artifact_content(artifact_type, context)
        checksum = sha256_text(content)
        artifact = ArtifactSnapshot(
            artifact_type=artifact_type,
            format="markdown",
            content=content,
            checksum=checksum,
            authoritative=authoritative,
            created_at=now,
            updated_at=now,
        )
        setattr(pointers, artifact_type.value, f"artifact://{run_state.metadata.run_id}/{artifact_type.value}.md")
        artifacts.append(artifact)
    return artifacts, pointers
