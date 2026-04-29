"""Primitive extraction and dependency consolidation helpers."""

from __future__ import annotations

import re

from ..models import (
    ConfidenceLevel,
    FrictionSignal,
    OperatorFamily,
    PrimitiveComponent,
    PrimitiveOperatorRecord,
    RelationType,
    InterlockRelation,
    SourceObject,
    StateVariableRecord,
    TypedClaim,
)
from ..utils import sha256_text, unique_preserve_order
from .analysis import AnalysisPayload


COMPONENT_HINTS = {
    "server",
    "runtime",
    "schema",
    "database",
    "sqlite",
    "artifact",
    "ledger",
    "constraint",
    "anchor",
    "transition",
    "tool",
    "resource",
    "prompt",
    "module",
    "transport",
    "state",
    "memory",
    "coherence",
    "trace",
    "sweep",
}


CANONICAL_STATE_VARIABLES = [
    ("scope_boundary", "Scope boundary of the current work.", "scope"),
    ("durability_gate", "Durability and native-minimality admissibility state.", "durability"),
    ("transition_state", "Current transition decision and block status.", "transition"),
    ("blast_radius", "Weighted whole-field propagation priority surface.", "propagation"),
    ("anchor_status", "Stability and validity state of live anchors.", "anchor"),
    ("tension_state", "Severity and openness of unresolved tensions.", "tension"),
    ("hypothesis_state", "Viability state of live basins and hypotheses.", "hypothesis"),
    ("friction_load", "Typed friction currently resisting continuation.", "friction"),
    ("compliance_state", "Pre-emission structural integrity status.", "compliance"),
]


def _source_lines(payload: AnalysisPayload) -> list[str]:
    return [
        line.strip()
        for line in payload.source_text.splitlines()
        if line.strip()
    ]


def _component_candidates(payload: AnalysisPayload, claims: list[TypedClaim]) -> list[str]:
    candidates: list[str] = []
    for token in re.findall(r"[A-Za-z0-9_./:-]+", payload.source_text):
        lowered = token.lower()
        if "/" in token or "\\" in token or "." in token:
            candidates.append(token)
            continue
        if any(lowered.endswith(hint) or lowered == hint for hint in COMPONENT_HINTS):
            candidates.append(token)
    for claim in claims:
        if claim.structural_role in {"constraint", "scope", "transition", "tension"}:
            for token in re.findall(r"[A-Za-z0-9_./:-]+", claim.statement):
                lowered = token.lower()
                if any(hint in lowered for hint in COMPONENT_HINTS):
                    candidates.append(token)
    return unique_preserve_order(candidates)[:16]


def extract_components(payload: AnalysisPayload, claims: list[TypedClaim], run_id: str = "") -> list[PrimitiveComponent]:
    components: list[PrimitiveComponent] = []
    for candidate in _component_candidates(payload, claims):
        components.append(
            PrimitiveComponent(
                id=f"component::{run_id}::{sha256_text(candidate)[:12]}" if run_id else f"component::{sha256_text(candidate)[:12]}",
                name=candidate,
                description=f"Retained component candidate derived from active PSI material: {candidate}",
                component_kind="path" if any(ch in candidate for ch in {"/", "\\", "."}) else "structural-object",
                scope="run",
                evidence=[candidate],
                metadata={"derived": True},
            )
        )
    return components


def extract_state_variables(
    payload: AnalysisPayload,
    claims: list[TypedClaim],
    frictions: list[FrictionSignal],
    run_id: str = "",
) -> list[StateVariableRecord]:
    text = payload.source_text.lower()
    variables: list[StateVariableRecord] = []
    for name, description, kind in CANONICAL_STATE_VARIABLES:
        if kind in text or any(kind in claim.statement.lower() for claim in claims):
            write_roles = [signal.friction_type.value for signal in frictions if kind in signal.rationale.lower()]
            variables.append(
                StateVariableRecord(
                    id=f"state::{run_id}::{name}" if run_id else f"state::{name}",
                    name=name,
                    description=description,
                    variable_kind=kind,
                    scope="run",
                    timescale="local_regime" if kind not in {"blast_radius", "scope"} else "architectural",
                    write_roles=write_roles,
                    read_roles=[claim.structural_role for claim in claims if claim.structural_role],
                    evidence=[claim.statement for claim in claims if kind in claim.statement.lower()][:4],
                    metadata={"derived": True},
                )
            )
    return variables


def extract_primitive_operators(
    payload: AnalysisPayload,
    active_operators: list[OperatorFamily],
    components: list[PrimitiveComponent],
    state_variables: list[StateVariableRecord],
    run_id: str = "",
) -> list[PrimitiveOperatorRecord]:
    component_ref = components[0].id if components else ""
    variable_refs = {variable.variable_kind: variable.id for variable in state_variables}
    family_defaults = {
        OperatorFamily.LENS: ("lens-stabilizer", "reset legitimacy conditions", "scope"),
        OperatorFamily.EXPOSURE: ("exposure-probe", "force local contact", "propagation"),
        OperatorFamily.PRIMITIVE: ("primitive-stripper", "de-abstract to explicit mechanics", "durability"),
        OperatorFamily.TENSION: ("tension-preserver", "retain informative instability", "tension"),
        OperatorFamily.DISCRIMINATOR: ("discriminator-search", "separate live alternatives", "hypothesis"),
        OperatorFamily.DURABILITY: ("durability-gate", "block poisoned continuity", "durability"),
        OperatorFamily.PROPAGATION: ("propagation-sweep", "propagate local change across the field", "propagation"),
    }
    operators: list[PrimitiveOperatorRecord] = []
    for family in active_operators:
        name, action, variable_kind = family_defaults[family]
        operators.append(
            PrimitiveOperatorRecord(
                id=f"operator::{run_id}::{family.value}" if run_id else f"operator::{family.value}",
                name=name,
                family=family,
                object_ref=component_ref,
                state_variable_ref=variable_refs.get(variable_kind, ""),
                trigger=payload.task[:160],
                direct_action=action,
                target=variable_kind,
                changes=[f"{variable_kind}_updated"],
                cannot_do=["advance silently without field impact"] if family == OperatorFamily.PROPAGATION else [],
                where="run-state",
                when="on visibility event or friction",
                directionality="forward" if family != OperatorFamily.TENSION else "bidirectional",
                timescale="immediate" if family in {OperatorFamily.EXPOSURE, OperatorFamily.DURABILITY} else "local_regime",
                persistence="re-entrant",
                reversibility="conditional",
                scope="whole-field" if family == OperatorFamily.PROPAGATION else "local-regime",
                evidence=[payload.task[:160]],
                metadata={"derived": True},
            )
        )
    return operators


def extract_interlocks(
    components: list[PrimitiveComponent],
    state_variables: list[StateVariableRecord],
    primitive_operators: list[PrimitiveOperatorRecord],
    claims: list[TypedClaim],
) -> list[InterlockRelation]:
    relations: list[InterlockRelation] = []
    for operator in primitive_operators:
        if operator.object_ref:
            relations.append(
                InterlockRelation(
                    id=f"interlock::{operator.id}::component",
                    relation_type=RelationType.REQUIRES,
                    source_ref=operator.id,
                    target_ref=operator.object_ref,
                    description=f"{operator.name} depends on a retained component surface.",
                    confidence=ConfidenceLevel.PROVISIONAL,
                    scope="run",
                    metadata={"derived": True},
                )
            )
        if operator.state_variable_ref:
            relations.append(
                InterlockRelation(
                    id=f"interlock::{operator.id}::state",
                    relation_type=RelationType.MODIFIES,
                    source_ref=operator.id,
                    target_ref=operator.state_variable_ref,
                    description=f"{operator.name} writes or retunes {operator.target}.",
                    confidence=ConfidenceLevel.PROVISIONAL,
                    scope="run",
                    metadata={"derived": True},
                )
            )
    if len(components) > 1:
        for left, right in zip(components, components[1:]):
            relations.append(
                InterlockRelation(
                    id=f"interlock::{left.id}::{right.id}",
                    relation_type=RelationType.COMPLEMENTS,
                    source_ref=left.id,
                    target_ref=right.id,
                    description="Retained components co-determine the active work surface.",
                    confidence=ConfidenceLevel.PROVISIONAL,
                    scope="run",
                    metadata={"derived": True},
                )
            )
    if claims:
        claim = claims[0]
        for variable in state_variables[:2]:
            relations.append(
                InterlockRelation(
                    id=f"interlock::claim::{variable.id}",
                    relation_type=RelationType.CONSTRAINS if claim.load_bearing else RelationType.UNDERDETERMINED,
                    source_ref=claim.id,
                    target_ref=variable.id,
                    description="Typed claims constrain or underdetermine state variables.",
                    confidence=claim.confidence,
                    scope="run",
                    metadata={"derived": True},
                )
            )
    deduped: list[InterlockRelation] = []
    seen_ids: set[str] = set()
    for relation in relations:
        if relation.id in seen_ids:
            continue
        seen_ids.add(relation.id)
        deduped.append(relation)
    return deduped
