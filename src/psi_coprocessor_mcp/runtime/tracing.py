"""Forward tracing and divergence helpers."""

from __future__ import annotations

from ..models import (
    DivergenceClass,
    FrictionSignal,
    FrictionType,
    PrimitiveOperatorRecord,
    TraceStep,
)
from ..utils import sha256_text
from .analysis import AnalysisPayload


def _divergence_from_friction(friction_type: FrictionType) -> DivergenceClass:
    return {
        FrictionType.SUBSTRATE_FRICTION: DivergenceClass.SCOPE_LIMITATION,
        FrictionType.CONCEPTUAL_DRIFT: DivergenceClass.ANALYSIS_ARTIFACT,
        FrictionType.STRUCTURAL_MISMATCH: DivergenceClass.MISSING_INTERLOCK,
        FrictionType.CONTINUITY_POISON: DivergenceClass.MISSING_OPERATOR,
    }[friction_type]


def build_trace_steps(
    payload: AnalysisPayload,
    primitive_operators: list[PrimitiveOperatorRecord],
    frictions: list[FrictionSignal],
) -> list[TraceStep]:
    cascade_id = f"cascade::{sha256_text(payload.source_text or payload.task)[:12]}"
    traces: list[TraceStep] = []
    for index, operator in enumerate(primitive_operators, start=1):
        traces.append(
            TraceStep(
                id=f"trace::{operator.id}",
                cascade_id=cascade_id,
                step_index=index,
                branch_key="primary",
                operator_ref=operator.id,
                from_state=operator.state_variable_ref or "input",
                to_state=f"{operator.target or operator.family.value}_updated",
                trigger=operator.trigger,
                outcome=operator.direct_action,
                divergence_class=None,
                blocking=False,
                evidence=operator.evidence[:2],
                metadata={"derived": True},
            )
        )
    if not frictions:
        traces.append(
            TraceStep(
                id=f"trace::{cascade_id}::resolved",
                cascade_id=cascade_id,
                step_index=len(traces) + 1,
                branch_key="primary",
                operator_ref=primitive_operators[-1].id if primitive_operators else "",
                from_state="field_before",
                to_state="field_after",
                trigger=payload.task[:160],
                outcome="trace resolved under currently accepted structure",
                divergence_class=DivergenceClass.RESOLVED,
                blocking=False,
                evidence=[payload.task[:160]],
                metadata={"derived": True},
            )
        )
        return traces
    for offset, friction in enumerate(frictions, start=1):
        divergence = _divergence_from_friction(friction.friction_type)
        traces.append(
            TraceStep(
                id=f"trace::{cascade_id}::{friction.friction_type.value.lower()}",
                cascade_id=cascade_id,
                step_index=len(primitive_operators) + offset,
                branch_key="primary" if offset == 1 else f"branch-{offset}",
                operator_ref=primitive_operators[-1].id if primitive_operators else "",
                from_state="accepted_structure",
                to_state="divergence",
                trigger=friction.rationale,
                outcome=f"{friction.friction_type.value} forced a divergence",
                divergence_class=divergence,
                blocking=divergence != DivergenceClass.RESOLVED,
                evidence=friction.evidence[:4],
                metadata={"friction_type": friction.friction_type.value, "derived": True},
            )
        )
    return traces
