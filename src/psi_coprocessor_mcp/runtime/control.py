"""Control-family metadata, mode activation, operator parsing, and friction routing."""

from __future__ import annotations

from ..models import (
    ActivationLevel,
    ArtifactType,
    BlastRadiusImpact,
    ControlFamily,
    ControlFamilyState,
    FrictionRoutingDecision,
    FrictionSignal,
    FrictionType,
    ModeActivation,
    OperatorFamily,
    Regime,
    RunMode,
)
from .analysis import AnalysisPayload


CONTROL_FAMILY_DESCRIPTIONS: dict[ControlFamily, str] = {
    ControlFamily.EPISTEMIC_TYPING: "Types load-bearing claims by provenance and keeps claim typing separate from durability.",
    ControlFamily.PRIMITIVE_INTEGRITY: "Forces structural articulation down to objects, operators, triggers, actions, and consequences.",
    ControlFamily.WHOLE_FIELD_PROPAGATION: "Turns local changes into weighted coherence sweeps and blocks local patch drift.",
    ControlFamily.BASIN_TENSION_CONTROL: "Preserves unresolved tensions, live basins, and discriminator paths.",
    ControlFamily.DURABILITY_NATIVE_MINIMALITY: "Separates confidence from reuse safety and blocks known-bad continuity.",
    ControlFamily.REGIME_TRANSITION_CONTROL: "Routes operator-triggered mode shifts and transition choice across re-entrant PSI regimes.",
}


CONTROL_FAMILY_METADATA: dict[ControlFamily, dict[str, object]] = {
    ControlFamily.EPISTEMIC_TYPING: {
        "hard_gate": True,
        "primary_homes": [Regime.SOURCE_GROUNDING, Regime.PRIMITIVE_STABILIZATION],
        "artifact_inputs": [ArtifactType.SOURCE_REGISTER, ArtifactType.TRACE_LEDGER],
        "artifact_outputs": [ArtifactType.PROVISIONAL_DISTINCTION_LEDGER, ArtifactType.FIELD_STATE_REGISTER],
        "quality_gates": ["claim provenance on load-bearing statements", "unknown is not placeholder"],
        "notes": ["Do not collapse provenance into confidence or durability."],
    },
    ControlFamily.PRIMITIVE_INTEGRITY: {
        "hard_gate": True,
        "primary_homes": [Regime.PRIMITIVE_STABILIZATION, Regime.DEPENDENCY_MAPPING],
        "artifact_inputs": [ArtifactType.COMPONENT_LEDGER, ArtifactType.OPERATOR_LEDGER],
        "artifact_outputs": [ArtifactType.COMPONENT_LEDGER, ArtifactType.STATE_VARIABLE_LEDGER],
        "quality_gates": ["fake primitive stripping", "mechanics over macro labels"],
        "notes": ["Operational cash-out is required before structural reuse."],
    },
    ControlFamily.WHOLE_FIELD_PROPAGATION: {
        "hard_gate": True,
        "primary_homes": [Regime.WHOLE_FIELD_COHERENCE_SWEEP, Regime.DEPENDENCY_MAPPING],
        "artifact_inputs": [ArtifactType.DEPENDENCY_AND_INTERLOCK_MAP, ArtifactType.FIELD_STATE_REGISTER],
        "artifact_outputs": [ArtifactType.COHERENCE_SWEEP_LOG, ArtifactType.FIELD_STATE_REGISTER],
        "quality_gates": ["no local-update patching without field impact", "stale anchor invalidation"],
        "notes": ["This is an interrupt regime, not a late cleanup step."],
    },
    ControlFamily.BASIN_TENSION_CONTROL: {
        "hard_gate": False,
        "primary_homes": [Regime.GAP_PRESSURE, Regime.HYPOTHESIS_BASIN],
        "artifact_inputs": [ArtifactType.GAP_AND_PRESSURE_LEDGER, ArtifactType.HYPOTHESIS_BASIN_LEDGER],
        "artifact_outputs": [ArtifactType.HYPOTHESIS_BASIN_LEDGER, ArtifactType.SEARCH_LOG],
        "quality_gates": ["tension retention", "discriminator path on live basins"],
        "notes": ["Unresolved tension is active state, not residue."],
    },
    ControlFamily.DURABILITY_NATIVE_MINIMALITY: {
        "hard_gate": True,
        "primary_homes": [Regime.SYNTHESIS_CONSTRUCTION, Regime.STRESS_TEST],
        "artifact_inputs": [ArtifactType.CONSTRUCTION_SPEC, ArtifactType.STRESS_TEST_REPORT],
        "artifact_outputs": [ArtifactType.STRESS_TEST_REPORT, ArtifactType.ANCHOR_REGISTER],
        "quality_gates": ["placeholder blocking", "durability tagging distinct from confidence"],
        "notes": ["Temporary scaffolds are admissible only when explicit, bounded, and non-substitutive."],
    },
    ControlFamily.REGIME_TRANSITION_CONTROL: {
        "hard_gate": True,
        "primary_homes": [Regime.TASK_CONTRACT_SCOPE_LOCK, Regime.ITERATION_HALT],
        "artifact_inputs": [ArtifactType.SCOPE_LOCK, ArtifactType.FIELD_STATE_REGISTER],
        "artifact_outputs": [ArtifactType.CONSTRUCTION_SPEC, ArtifactType.FINAL_SYNTHESIS],
        "quality_gates": ["questions act as operators", "continue is earned, not default"],
        "notes": ["Wrong frame is an upstream problem, not a local defect."],
    },
}


MODE_ACTIVATION_MATRIX: dict[RunMode, dict[ControlFamily, tuple[ActivationLevel, float, str]]] = {
    RunMode.SURVEY: {
        ControlFamily.EPISTEMIC_TYPING: (ActivationLevel.HARD, 0.95, "Survey mode must type claims before they carry weight."),
        ControlFamily.PRIMITIVE_INTEGRITY: (ActivationLevel.SOFT, 0.65, "Survey can tolerate partial articulation while structure is still emerging."),
        ControlFamily.WHOLE_FIELD_PROPAGATION: (ActivationLevel.SOFT, 0.7, "Sweep obligations remain active, but exploration can keep more items provisional."),
        ControlFamily.BASIN_TENSION_CONTROL: (ActivationLevel.HARD, 0.95, "Survey should keep alternatives and tensions live."),
        ControlFamily.DURABILITY_NATIVE_MINIMALITY: (ActivationLevel.SOFT, 0.6, "Survey should mark scaffolds clearly without over-blocking exploration."),
        ControlFamily.REGIME_TRANSITION_CONTROL: (ActivationLevel.SOFT, 0.7, "Survey still needs explicit routing, but not closure pressure."),
    },
    RunMode.CLOSURE: {
        ControlFamily.EPISTEMIC_TYPING: (ActivationLevel.HARD, 0.9, "Closure requires typed support on claims that are about to stabilize."),
        ControlFamily.PRIMITIVE_INTEGRITY: (ActivationLevel.HARD, 0.85, "Closure should reject unresolved macro-term shortcuts."),
        ControlFamily.WHOLE_FIELD_PROPAGATION: (ActivationLevel.HARD, 0.95, "Closure must propagate meaningful changes before stabilizing output."),
        ControlFamily.BASIN_TENSION_CONTROL: (ActivationLevel.SOFT, 0.55, "Some basins can narrow, but unresolved live tensions should remain explicit."),
        ControlFamily.DURABILITY_NATIVE_MINIMALITY: (ActivationLevel.HARD, 0.95, "Closure cannot canonize convenience continuity."),
        ControlFamily.REGIME_TRANSITION_CONTROL: (ActivationLevel.HARD, 0.95, "Transition discipline is central in closure mode."),
    },
    RunMode.CONSTRUCTION: {
        ControlFamily.EPISTEMIC_TYPING: (ActivationLevel.SOFT, 0.7, "Construction needs claim typing, but build pressure shifts focus toward implementation obligations."),
        ControlFamily.PRIMITIVE_INTEGRITY: (ActivationLevel.HARD, 0.85, "Construction must resist cargo-cult named-module substitution."),
        ControlFamily.WHOLE_FIELD_PROPAGATION: (ActivationLevel.HARD, 0.9, "Construction changes must state field impact or stop."),
        ControlFamily.BASIN_TENSION_CONTROL: (ActivationLevel.SOFT, 0.6, "Construction can narrow basins, but not erase informative tension."),
        ControlFamily.DURABILITY_NATIVE_MINIMALITY: (ActivationLevel.HARD, 0.95, "Build outputs must not smuggle placeholders into stable structure."),
        ControlFamily.REGIME_TRANSITION_CONTROL: (ActivationLevel.HARD, 0.85, "Construction still requires explicit transition logic."),
    },
    RunMode.AUDIT: {
        ControlFamily.EPISTEMIC_TYPING: (ActivationLevel.HARD, 0.95, "Audit should aggressively separate observation, inference, and construction."),
        ControlFamily.PRIMITIVE_INTEGRITY: (ActivationLevel.HARD, 0.95, "Audit treats fake primitives as a primary defect class."),
        ControlFamily.WHOLE_FIELD_PROPAGATION: (ActivationLevel.HARD, 0.95, "Audit should force sweep discipline on suspicious local fixes."),
        ControlFamily.BASIN_TENSION_CONTROL: (ActivationLevel.HARD, 0.85, "Audit preserves alternatives instead of collapsing to the first critique."),
        ControlFamily.DURABILITY_NATIVE_MINIMALITY: (ActivationLevel.HARD, 0.95, "Audit should aggressively surface reuse poison."),
        ControlFamily.REGIME_TRANSITION_CONTROL: (ActivationLevel.HARD, 0.9, "Audit should prefer explicit rollback, rescope, or escalate decisions over implicit drift."),
    },
    RunMode.REPAIR: {
        ControlFamily.EPISTEMIC_TYPING: (ActivationLevel.SOFT, 0.75, "Repair still needs typed support, but primary pressure is on restoring coherent structure."),
        ControlFamily.PRIMITIVE_INTEGRITY: (ActivationLevel.HARD, 0.85, "Repair should re-ground the failing surface in concrete articulation."),
        ControlFamily.WHOLE_FIELD_PROPAGATION: (ActivationLevel.HARD, 0.95, "Repair exists because propagation failed or must be re-run."),
        ControlFamily.BASIN_TENSION_CONTROL: (ActivationLevel.SOFT, 0.65, "Repair should preserve unresolved alternatives without reopening everything."),
        ControlFamily.DURABILITY_NATIVE_MINIMALITY: (ActivationLevel.HARD, 0.95, "Repair must not continue from poisoned continuity."),
        ControlFamily.REGIME_TRANSITION_CONTROL: (ActivationLevel.HARD, 0.95, "Repair depends on explicit re-entry and transition control."),
    },
}


FRICTION_TO_FAMILIES: dict[FrictionType, list[ControlFamily]] = {
    FrictionType.SUBSTRATE_FRICTION: [
        ControlFamily.WHOLE_FIELD_PROPAGATION,
        ControlFamily.REGIME_TRANSITION_CONTROL,
    ],
    FrictionType.CONCEPTUAL_DRIFT: [
        ControlFamily.EPISTEMIC_TYPING,
        ControlFamily.PRIMITIVE_INTEGRITY,
    ],
    FrictionType.STRUCTURAL_MISMATCH: [
        ControlFamily.WHOLE_FIELD_PROPAGATION,
        ControlFamily.BASIN_TENSION_CONTROL,
        ControlFamily.REGIME_TRANSITION_CONTROL,
    ],
    FrictionType.CONTINUITY_POISON: [
        ControlFamily.DURABILITY_NATIVE_MINIMALITY,
        ControlFamily.WHOLE_FIELD_PROPAGATION,
        ControlFamily.REGIME_TRANSITION_CONTROL,
    ],
}


DEFAULT_ROUTING: dict[FrictionType, list[Regime]] = {
    FrictionType.SUBSTRATE_FRICTION: [
        Regime.FORWARD_TRACING,
        Regime.REPAIR,
        Regime.WHOLE_FIELD_COHERENCE_SWEEP,
    ],
    FrictionType.CONCEPTUAL_DRIFT: [
        Regime.PRIMITIVE_STABILIZATION,
        Regime.SOURCE_GROUNDING,
        Regime.WHOLE_FIELD_COHERENCE_SWEEP,
    ],
    FrictionType.STRUCTURAL_MISMATCH: [
        Regime.DEPENDENCY_MAPPING,
        Regime.WHOLE_FIELD_COHERENCE_SWEEP,
        Regime.REPAIR,
    ],
    FrictionType.CONTINUITY_POISON: [
        Regime.SYNTHESIS_CONSTRUCTION,
        Regime.STRESS_TEST,
        Regime.REPAIR,
    ],
}


def build_control_family_states(mode: RunMode) -> list[ControlFamilyState]:
    states: list[ControlFamilyState] = []
    mode_profile = MODE_ACTIVATION_MATRIX[mode]
    for family, activation_tuple in mode_profile.items():
        level, weight, rationale = activation_tuple
        metadata = CONTROL_FAMILY_METADATA[family]
        states.append(
            ControlFamilyState(
                family=family,
                description=CONTROL_FAMILY_DESCRIPTIONS[family],
                activation=ModeActivation(mode=mode, level=level, weight=weight, rationale=rationale),
                hard_gate=bool(metadata["hard_gate"]),
                primary_homes=list(metadata["primary_homes"]),
                artifact_inputs=list(metadata["artifact_inputs"]),
                artifact_outputs=list(metadata["artifact_outputs"]),
                quality_gates=list(metadata["quality_gates"]),
                notes=list(metadata["notes"]),
            )
        )
    return states


def mode_profile_catalog() -> dict[str, list[dict[str, object]]]:
    catalog: dict[str, list[dict[str, object]]] = {}
    for mode in RunMode:
        catalog[mode.value] = [family.model_dump(mode="json") for family in build_control_family_states(mode)]
    return catalog


def control_family_catalog() -> list[dict[str, object]]:
    catalog: list[dict[str, object]] = []
    for family in ControlFamily:
        state = build_control_family_states(RunMode.SURVEY)
        chosen = next(item for item in state if item.family == family)
        item = chosen.model_dump(mode="json")
        item["activation_profiles"] = {
            mode.value: {
                "level": MODE_ACTIVATION_MATRIX[mode][family][0].value,
                "weight": MODE_ACTIVATION_MATRIX[mode][family][1],
                "rationale": MODE_ACTIVATION_MATRIX[mode][family][2],
            }
            for mode in RunMode
        }
        catalog.append(item)
    return catalog


def detect_operator_families(payload: AnalysisPayload) -> list[OperatorFamily]:
    text = payload.source_text.lower()
    families: list[OperatorFamily] = []
    operator_patterns = {
        OperatorFamily.LENS: ["what are we actually doing", "what level", "scope", "boundary", "frame"],
        OperatorFamily.PRIMITIVE: ["what is actually there", "fake primitive", "primitive", "mechanics"],
        OperatorFamily.EXPOSURE: ["literally happens", "what changed", "local contact", "expose"],
        OperatorFamily.TENSION: ["doesn't fit", "does not fit", "unresolved", "tension", "mismatch"],
        OperatorFamily.DISCRIMINATOR: ["what would break", "what separates", "discriminator", "compare"],
        OperatorFamily.DURABILITY: ["placeholder", "toy", "rewrite debt", "durability", "scaffold"],
        OperatorFamily.PROPAGATION: ["what changes about the whole", "blast radius", "field impact", "what else must update"],
    }
    for family, patterns in operator_patterns.items():
        if any(pattern in text for pattern in patterns):
            families.append(family)
    if not families:
        families.extend([OperatorFamily.LENS, OperatorFamily.EXPOSURE, OperatorFamily.PROPAGATION])
    deduped: list[OperatorFamily] = []
    for family in families:
        if family not in deduped:
            deduped.append(family)
    return deduped


def build_friction_routing(
    frictions: list[FrictionSignal],
    mode: RunMode,
    impacts: list[BlastRadiusImpact] | None = None,
    durability_blocked: bool = False,
) -> list[FrictionRoutingDecision]:
    impacts = impacts or []
    high_anchor_instability = any(
        impact.entity_type == "anchor"
        and impact.centrality >= 0.75
        and impact.fragility >= 0.7
        and impact.score >= 0.7
        for impact in impacts
    )
    decisions: list[FrictionRoutingDecision] = []
    for friction in frictions:
        ordered = list(DEFAULT_ROUTING[friction.friction_type])
        override_reasons: list[str] = []
        if mode == RunMode.AUDIT and Regime.STRESS_TEST not in ordered:
            ordered.insert(1, Regime.STRESS_TEST)
            override_reasons.append("audit mode promotes stress testing early")
        if mode == RunMode.REPAIR and Regime.REPAIR in ordered:
            ordered.remove(Regime.REPAIR)
            ordered.insert(0, Regime.REPAIR)
            override_reasons.append("repair mode prioritizes upstream repair first")
        if mode == RunMode.SURVEY and friction.friction_type in {FrictionType.CONCEPTUAL_DRIFT, FrictionType.STRUCTURAL_MISMATCH}:
            if Regime.HYPOTHESIS_BASIN not in ordered:
                ordered.append(Regime.HYPOTHESIS_BASIN)
            override_reasons.append("survey mode keeps alternative basins live longer")
        if mode == RunMode.CLOSURE and Regime.ITERATION_HALT not in ordered:
            ordered.append(Regime.ITERATION_HALT)
            override_reasons.append("closure mode keeps halt/anchor pressure visible")
        if durability_blocked and friction.friction_type == FrictionType.CONTINUITY_POISON:
            ordered = [Regime.SYNTHESIS_CONSTRUCTION, Regime.REPAIR, *[regime for regime in ordered if regime not in {Regime.SYNTHESIS_CONSTRUCTION, Regime.REPAIR}]]
            override_reasons.append("durability block forces construction/repair re-entry")
        if high_anchor_instability and Regime.WHOLE_FIELD_COHERENCE_SWEEP not in ordered[:1]:
            ordered = [Regime.WHOLE_FIELD_COHERENCE_SWEEP, *[regime for regime in ordered if regime != Regime.WHOLE_FIELD_COHERENCE_SWEEP]]
            override_reasons.append("high-centrality anchor instability elevates the coherence sweep")
        deduped: list[Regime] = []
        for regime in ordered:
            if regime not in deduped:
                deduped.append(regime)
        decisions.append(
            FrictionRoutingDecision(
                friction_type=friction.friction_type,
                ordered_regimes=deduped,
                primary_regime=deduped[0],
                control_families=FRICTION_TO_FAMILIES[friction.friction_type],
                override_reasons=override_reasons,
                notes=[f"default placement metadata retained for {friction.friction_type.value.lower()}"],
            )
        )
    return decisions
