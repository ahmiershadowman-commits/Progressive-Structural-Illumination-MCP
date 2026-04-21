"""Weighted coherence sweeps and blast-radius estimation."""

from __future__ import annotations

from ..models import (
    Anchor,
    BlastRadiusImpact,
    ConstraintItem,
    DurabilityClass,
    FrictionSignal,
    FrictionType,
    Hypothesis,
    InterlockRelation,
    GapRecord,
    PrimitiveComponent,
    PrimitiveOperatorRecord,
    Regime,
    RunMode,
    StateVariableRecord,
    TraceStep,
    TransitionDecision,
    TransitionState,
    Tension,
)
from .analysis import AnalysisPayload
from .control import build_friction_routing


def route_regimes(
    frictions: list[FrictionSignal],
    mode: RunMode = RunMode.SURVEY,
    impacts: list[BlastRadiusImpact] | None = None,
    durability_blocked: bool = False,
) -> list[Regime]:
    regimes: list[Regime] = [Regime.WHOLE_FIELD_COHERENCE_SWEEP]
    routing = build_friction_routing(
        frictions=frictions,
        mode=mode,
        impacts=impacts or [],
        durability_blocked=durability_blocked,
    )
    for decision in routing:
        regimes.extend(decision.ordered_regimes)
    deduped: list[Regime] = []
    for regime in regimes:
        if regime not in deduped:
            deduped.append(regime)
    return deduped


def _extract_terms(text: str) -> set[str]:
    return {token for token in text.lower().replace("/", " ").replace("\\", " ").split() if token}


def _match_score(changed_terms: set[str], candidate_terms: set[str]) -> float:
    if not candidate_terms:
        return 0.35
    overlap = len(changed_terms & candidate_terms)
    return min(1.0, 0.25 + (overlap / max(len(candidate_terms), 1)))


def _stance_sensitivity(name: str, hints: list[str]) -> float:
    lowered = name.lower()
    if any(hint.lower() in lowered for hint in hints):
        return 0.85
    return 0.35


def _constraint_coupling(constraints: list[ConstraintItem], candidate_terms: set[str]) -> float:
    if not constraints:
        return 0.2
    hits = 0
    for constraint in constraints:
        text = f"{constraint.constraint_type} {constraint.category} {constraint.description}".lower()
        if candidate_terms & set(text.split()):
            hits += 1
    return min(1.0, 0.2 + (hits / max(len(constraints), 1)))


def _durability_relevance(frictions: list[FrictionSignal], candidate_terms: set[str]) -> float:
    base = 0.25
    if any(friction.friction_type == FrictionType.CONTINUITY_POISON for friction in frictions):
        base += 0.4
    if {"placeholder", "rewrite", "durability"} & candidate_terms:
        base += 0.2
    return min(1.0, base)


def _durability_weight(durability_class: DurabilityClass) -> float:
    return {
        DurabilityClass.UNKNOWN: 0.35,
        DurabilityClass.SANDBOXED: 0.4,
        DurabilityClass.PROVISIONAL: 0.55,
        DurabilityClass.CONDITIONAL: 0.65,
        DurabilityClass.DURABLE: 0.9,
        DurabilityClass.POISONED: 0.95,
    }[durability_class]


def _timescale_proximity(payload: AnalysisPayload, candidate_terms: set[str]) -> float:
    text = payload.source_text.lower()
    score = 0.2
    if any(term in text for term in candidate_terms):
        score += 0.25
    if any(token in text for token in {"test", "compile", "runtime", "migration", "schema"}):
        score += 0.2
    if any(token in candidate_terms for token in {"runtime", "schema", "migration", "transport"}):
        score += 0.2
    return min(1.0, score)


def _graph_degree(entity_ref: str, interlocks: list[InterlockRelation]) -> float:
    if not interlocks:
        return 0.2
    incident = sum(1 for relation in interlocks if entity_ref in {relation.source_ref, relation.target_ref})
    return min(1.0, 0.2 + (incident / max(len(interlocks), 1)))


def _trace_pressure(entity_ref: str, traces: list[TraceStep]) -> float:
    related = [
        trace
        for trace in traces
        if entity_ref and entity_ref in {trace.operator_ref, trace.from_state, trace.to_state}
    ]
    if not related:
        return 0.2
    blocking = sum(1 for trace in related if trace.blocking or trace.divergence_class)
    return min(1.0, 0.25 + (blocking / max(len(related), 1)))


def _gap_pressure(entity_ref: str, gaps: list[GapRecord]) -> float:
    related = [
        gap
        for gap in gaps
        if entity_ref and (entity_ref in gap.nearly_covers or entity_ref in gap.dissolved_by)
    ]
    if not related:
        return 0.2
    blocking = sum(1 for gap in related if gap.blocking or gap.status == "OPEN")
    return min(1.0, 0.25 + (blocking / max(len(related), 1)))


def _supersession_risk(entity_ref: str, supersessions: list[dict[str, object]]) -> float:
    return 0.9 if any(item.get("entity_id") == entity_ref for item in supersessions) else 0.0


def estimate_blast_radius(
    payload: AnalysisPayload,
    frictions: list[FrictionSignal],
    anchors: list[Anchor],
    tensions: list[Tension],
    hypotheses: list[Hypothesis],
    constraints: list[ConstraintItem],
    stance_hints: list[str],
    components: list[PrimitiveComponent] | None = None,
    state_variables: list[StateVariableRecord] | None = None,
    primitive_operators: list[PrimitiveOperatorRecord] | None = None,
    interlocks: list[InterlockRelation] | None = None,
    traces: list[TraceStep] | None = None,
    gaps: list[GapRecord] | None = None,
    supersessions: list[dict[str, object]] | None = None,
) -> tuple[list[BlastRadiusImpact], list[str]]:
    changed_terms = _extract_terms(payload.source_text)
    components = components or []
    state_variables = state_variables or []
    primitive_operators = primitive_operators or []
    interlocks = interlocks or []
    traces = traces or []
    gaps = gaps or []
    supersessions = supersessions or []
    impacts: list[BlastRadiusImpact] = []
    for anchor in anchors:
        candidate_terms = _extract_terms(
            " ".join([anchor.name, anchor.description, *anchor.dependencies, *anchor.implications])
        )
        overlap = _match_score(changed_terms, candidate_terms)
        dependency_density = min(1.0, 0.2 + (len(anchor.dependencies) / 6))
        substrate_coupling = _constraint_coupling(constraints, candidate_terms)
        durability_relevance = min(
            1.0,
            (_durability_relevance(frictions, candidate_terms) * 0.6)
            + (_durability_weight(anchor.durability_class) * 0.4),
        )
        stance_sensitivity = _stance_sensitivity(anchor.name, stance_hints)
        timescale_proximity = _timescale_proximity(payload, candidate_terms)
        score = min(
            1.0,
            (
                (anchor.centrality * 0.23)
                + (anchor.fragility * 0.22)
                + (dependency_density * 0.15)
                + (timescale_proximity * 0.12)
                + (substrate_coupling * 0.11)
                + (durability_relevance * 0.1)
                + (stance_sensitivity * 0.07)
            )
            * overlap,
        )
        impacts.append(
            BlastRadiusImpact(
                entity_type="anchor",
                entity_id=anchor.id or anchor.name,
                entity_name=anchor.name,
                score=score,
                centrality=anchor.centrality,
                fragility=anchor.fragility,
                dependency_density=dependency_density,
                timescale_proximity=timescale_proximity,
                substrate_coupling=substrate_coupling,
                durability_relevance=durability_relevance,
                stance_sensitivity=stance_sensitivity,
                rationale="Anchor scored by centrality, fragility, dependency density, timescale, substrate, durability class, and stance overlap.",
            )
        )
    for tension in tensions:
        candidate_terms = _extract_terms(" ".join([tension.title, tension.description, *tension.forces]))
        overlap = _match_score(changed_terms, candidate_terms)
        severity = min(1.0, 0.25 + tension.severity)
        score = min(1.0, severity * overlap)
        impacts.append(
            BlastRadiusImpact(
                entity_type="tension",
                entity_id=tension.id or tension.title,
                entity_name=tension.title,
                score=score,
                centrality=severity,
                fragility=severity,
                dependency_density=min(1.0, 0.25 + len(tension.forces) / 6),
                timescale_proximity=_timescale_proximity(payload, candidate_terms),
                substrate_coupling=_constraint_coupling(constraints, candidate_terms),
                durability_relevance=_durability_relevance(frictions, candidate_terms),
                stance_sensitivity=_stance_sensitivity(tension.title, stance_hints),
                rationale="Tension impact reflects unresolved force coupling and overlap with the changed surface.",
            )
        )
    for hypothesis in hypotheses:
        candidate_terms = _extract_terms(
            " ".join([hypothesis.title, hypothesis.description, *hypothesis.preserves, *hypothesis.risks])
        )
        overlap = _match_score(changed_terms, candidate_terms)
        confidence = {
            "strong": 0.85,
            "moderate": 0.7,
            "weak": 0.45,
            "provisional": 0.55,
            "unresolved": 0.4,
        }.get(hypothesis.confidence.value, 0.5)
        durability_weight = _durability_weight(hypothesis.durability_class)
        score = min(1.0, overlap * (0.25 + confidence / 3 + durability_weight / 3))
        impacts.append(
            BlastRadiusImpact(
                entity_type="hypothesis",
                entity_id=hypothesis.id or hypothesis.title,
                entity_name=hypothesis.title,
                score=score,
                centrality=confidence,
                fragility=1.0 - confidence,
                dependency_density=min(1.0, 0.2 + len(hypothesis.preserves) / 6),
                timescale_proximity=_timescale_proximity(payload, candidate_terms),
                substrate_coupling=_constraint_coupling(constraints, candidate_terms),
                durability_relevance=min(
                    1.0,
                    (_durability_relevance(frictions, candidate_terms) * 0.6)
                    + (durability_weight * 0.4),
                ),
                stance_sensitivity=_stance_sensitivity(hypothesis.title, stance_hints),
                rationale="Hypothesis impact captures how much a candidate basin remains load-bearing under the changed field, separate from its durability class.",
            )
        )
    for component in components:
        entity_ref = component.id or component.name
        candidate_terms = _extract_terms(" ".join([component.name, component.description, *component.evidence]))
        overlap = max(
            _match_score(changed_terms, candidate_terms),
            0.25 + (_graph_degree(entity_ref, interlocks) * 0.25),
        )
        dependency_density = _graph_degree(entity_ref, interlocks)
        trace_pressure = _trace_pressure(entity_ref, traces)
        gap_pressure = _gap_pressure(entity_ref, gaps)
        fragility = min(1.0, 0.2 + (trace_pressure * 0.45) + (gap_pressure * 0.25) + (_supersession_risk(entity_ref, supersessions) * 0.1))
        centrality = min(1.0, 0.25 + (dependency_density * 0.55) + (0.2 if component.component_kind == "path" else 0.0))
        timescale_proximity = _timescale_proximity(payload, candidate_terms)
        substrate_coupling = _constraint_coupling(constraints, candidate_terms)
        durability_relevance = _durability_relevance(frictions, candidate_terms)
        stance_sensitivity = _stance_sensitivity(component.name, stance_hints)
        score = min(
            1.0,
            overlap
            * (
                (centrality * 0.24)
                + (fragility * 0.21)
                + (dependency_density * 0.18)
                + (timescale_proximity * 0.12)
                + (substrate_coupling * 0.1)
                + (durability_relevance * 0.09)
                + (stance_sensitivity * 0.06)
            ),
        )
        impacts.append(
            BlastRadiusImpact(
                entity_type="component",
                entity_id=entity_ref,
                entity_name=component.name,
                score=score,
                centrality=centrality,
                fragility=fragility,
                dependency_density=dependency_density,
                timescale_proximity=timescale_proximity,
                substrate_coupling=substrate_coupling,
                durability_relevance=durability_relevance,
                stance_sensitivity=stance_sensitivity,
                rationale="Component score uses the explicit interlock graph, trace pressure, gap pressure, and supersession risk.",
            )
        )
    for state_variable in state_variables:
        entity_ref = state_variable.id or state_variable.name
        candidate_terms = _extract_terms(
            " ".join(
                [
                    state_variable.name,
                    state_variable.description,
                    state_variable.variable_kind,
                    *state_variable.write_roles,
                    *state_variable.read_roles,
                    *state_variable.evidence,
                ]
            )
        )
        dependency_density = _graph_degree(entity_ref, interlocks)
        trace_pressure = _trace_pressure(entity_ref, traces)
        gap_pressure = _gap_pressure(entity_ref, gaps)
        overlap = max(_match_score(changed_terms, candidate_terms), 0.25 + (dependency_density * 0.2))
        centrality = min(
            1.0,
            0.3
            + (dependency_density * 0.35)
            + (min(1.0, len(state_variable.write_roles) / 4) * 0.2)
            + (min(1.0, len(state_variable.read_roles) / 6) * 0.15),
        )
        fragility = min(1.0, 0.2 + (trace_pressure * 0.4) + (gap_pressure * 0.25))
        timescale_proximity = _timescale_proximity(payload, candidate_terms)
        substrate_coupling = _constraint_coupling(constraints, candidate_terms)
        durability_relevance = _durability_relevance(frictions, candidate_terms)
        stance_sensitivity = _stance_sensitivity(state_variable.name, stance_hints)
        score = min(
            1.0,
            overlap
            * (
                (centrality * 0.24)
                + (fragility * 0.21)
                + (dependency_density * 0.17)
                + (timescale_proximity * 0.12)
                + (substrate_coupling * 0.1)
                + (durability_relevance * 0.1)
                + (stance_sensitivity * 0.06)
            ),
        )
        impacts.append(
            BlastRadiusImpact(
                entity_type="state_variable",
                entity_id=entity_ref,
                entity_name=state_variable.name,
                score=score,
                centrality=centrality,
                fragility=fragility,
                dependency_density=dependency_density,
                timescale_proximity=timescale_proximity,
                substrate_coupling=substrate_coupling,
                durability_relevance=durability_relevance,
                stance_sensitivity=stance_sensitivity,
                rationale="State-variable score captures write-side density, graph incidence, and blocking trace pressure.",
            )
        )
    for operator in primitive_operators:
        entity_ref = operator.id or operator.name
        candidate_terms = _extract_terms(
            " ".join(
                [
                    operator.name,
                    operator.trigger,
                    operator.direct_action,
                    operator.target,
                    *operator.changes,
                    *operator.cannot_do,
                    *operator.evidence,
                ]
            )
        )
        dependency_density = _graph_degree(entity_ref, interlocks)
        trace_pressure = _trace_pressure(entity_ref, traces)
        overlap = max(_match_score(changed_terms, candidate_terms), 0.2 + (trace_pressure * 0.3))
        centrality = min(1.0, 0.25 + (dependency_density * 0.4) + (trace_pressure * 0.25))
        fragility = min(1.0, 0.2 + (trace_pressure * 0.45) + (_supersession_risk(entity_ref, supersessions) * 0.15))
        timescale_proximity = _timescale_proximity(payload, candidate_terms)
        substrate_coupling = _constraint_coupling(constraints, candidate_terms)
        durability_relevance = _durability_relevance(frictions, candidate_terms)
        stance_sensitivity = _stance_sensitivity(operator.name, stance_hints)
        score = min(
            1.0,
            overlap
            * (
                (centrality * 0.23)
                + (fragility * 0.22)
                + (dependency_density * 0.18)
                + (timescale_proximity * 0.12)
                + (substrate_coupling * 0.09)
                + (durability_relevance * 0.1)
                + (stance_sensitivity * 0.06)
            ),
        )
        impacts.append(
            BlastRadiusImpact(
                entity_type="primitive_operator",
                entity_id=entity_ref,
                entity_name=operator.name,
                score=score,
                centrality=centrality,
                fragility=fragility,
                dependency_density=dependency_density,
                timescale_proximity=timescale_proximity,
                substrate_coupling=substrate_coupling,
                durability_relevance=durability_relevance,
                stance_sensitivity=stance_sensitivity,
                rationale="Primitive-operator score uses interlocks plus trace divergence instead of text overlap alone.",
            )
        )
    for gap in gaps:
        candidate_terms = _extract_terms(" ".join([gap.title, gap.description, gap.discriminator, *gap.nearly_covers]))
        overlap = _match_score(changed_terms, candidate_terms)
        centrality = 0.75 if gap.blocking else 0.55
        fragility = 0.9 if gap.blocking else 0.65
        dependency_density = min(1.0, 0.2 + (len(gap.nearly_covers) / 4))
        timescale_proximity = _timescale_proximity(payload, candidate_terms)
        substrate_coupling = _constraint_coupling(constraints, candidate_terms)
        durability_relevance = _durability_relevance(frictions, candidate_terms)
        stance_sensitivity = _stance_sensitivity(gap.title, stance_hints)
        score = min(
            1.0,
            max(overlap, 0.45)
            * (
                (centrality * 0.24)
                + (fragility * 0.24)
                + (dependency_density * 0.15)
                + (timescale_proximity * 0.12)
                + (substrate_coupling * 0.08)
                + (durability_relevance * 0.1)
                + (stance_sensitivity * 0.07)
            ),
        )
        impacts.append(
            BlastRadiusImpact(
                entity_type="gap",
                entity_id=gap.id or gap.title,
                entity_name=gap.title,
                score=score,
                centrality=centrality,
                fragility=fragility,
                dependency_density=dependency_density,
                timescale_proximity=timescale_proximity,
                substrate_coupling=substrate_coupling,
                durability_relevance=durability_relevance,
                stance_sensitivity=stance_sensitivity,
                rationale="Open gaps stay high in the sweep because they represent unresolved structural loss.",
            )
        )
    if not impacts:
        fallbacks = [
            ("state-domain", "durability_gate", 0.72, 0.8, 0.9, "Durability domain"),
            ("state-domain", "scope_boundary", 0.65, 0.7, 0.7, "Scope boundary"),
            ("state-domain", "dependency_map", 0.6, 0.8, 0.6, "Dependency map"),
        ]
        for entity_type, entity_name, score, centrality, fragility, rationale in fallbacks:
            impacts.append(
                BlastRadiusImpact(
                    entity_type=entity_type,
                    entity_id=entity_name,
                    entity_name=entity_name,
                    score=score,
                    centrality=centrality,
                    fragility=fragility,
                    dependency_density=0.6,
                    timescale_proximity=0.6,
                    substrate_coupling=0.5,
                    durability_relevance=0.7,
                    stance_sensitivity=0.5,
                    rationale=rationale,
                )
            )
    impacts = sorted(impacts, key=lambda impact: impact.score, reverse=True)
    deferred = [impact.entity_name for impact in impacts[5:] if impact.score < 0.5]
    return impacts[:8], deferred


def recommend_transition(
    frictions: list[FrictionSignal],
    impacts: list[BlastRadiusImpact],
    durability_blocked: bool,
    scope_shift_detected: bool,
    uncertainty_limits: list[str],
) -> TransitionState:
    if durability_blocked:
        return TransitionState(
            decision=TransitionDecision.ROLLBACK,
            rationale="Durability/native-minimality gate blocked forward movement due to known-bad continuity.",
            blocking_reasons=["durability gate blocked"],
            recommended_regimes=[Regime.SYNTHESIS_CONSTRUCTION, Regime.STRESS_TEST, Regime.REPAIR],
        )
    if any(
        impact.entity_type in {"anchor", "component", "state_variable"}
        and impact.score >= 0.72
        and impact.centrality >= 0.75
        and impact.fragility >= 0.7
        for impact in impacts
    ):
        return TransitionState(
            decision=TransitionDecision.ROLLBACK,
            rationale="A high-centrality and high-fragility upstream object destabilized under the sweep.",
            blocking_reasons=["fragile central upstream object destabilized"],
            recommended_regimes=[Regime.DEPENDENCY_MAPPING, Regime.REPAIR, Regime.WHOLE_FIELD_COHERENCE_SWEEP],
        )
    if scope_shift_detected:
        return TransitionState(
            decision=TransitionDecision.RESCOPE,
            rationale="The active visibility event changes the admissible slice or boundary of the work.",
            recommended_regimes=[Regime.TASK_CONTRACT_SCOPE_LOCK, Regime.WHOLE_FIELD_COHERENCE_SWEEP],
        )
    if uncertainty_limits and any(
        friction.friction_type == FrictionType.SUBSTRATE_FRICTION and friction.severity >= 0.7
        for friction in frictions
    ):
        return TransitionState(
            decision=TransitionDecision.ESCALATE,
            rationale="Propagation depends on missing evidence or a concrete failure reproduction that is not yet available.",
            blocking_reasons=uncertainty_limits[:4],
            recommended_regimes=[Regime.FORWARD_TRACING, Regime.REPAIR],
        )
    if impacts and impacts[0].score < 0.45 and not frictions:
        return TransitionState(
            decision=TransitionDecision.ANCHOR,
            rationale="No load-bearing destabilization is active and the current articulation survives the sweep.",
            recommended_regimes=[Regime.ITERATION_HALT],
        )
    return TransitionState(
        decision=TransitionDecision.CONTINUE,
        rationale="The field remains underdetermined; continue with the highest-revelation probe while preserving live tensions.",
        recommended_regimes=route_regimes(frictions),
    )


def summarize_impacts(impacts: list[BlastRadiusImpact]) -> list[str]:
    return [
        f"{impact.entity_type}:{impact.entity_name} score={impact.score:.2f} "
        f"(centrality={impact.centrality:.2f}, fragility={impact.fragility:.2f})"
        for impact in impacts
    ]
