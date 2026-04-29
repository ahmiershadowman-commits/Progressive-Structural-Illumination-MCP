"""Gap/pressure, search, and basin helpers."""

from __future__ import annotations

from ..models import (
    BasinRecord,
    BasinType,
    DivergenceClass,
    FrictionSignal,
    FrictionType,
    GapOrigin,
    GapRecord,
    GapType,
    Hypothesis,
    SearchRecord,
    SearchStatus,
    Tension,
    TraceStep,
)
from ..utils import sha256_text, unique_preserve_order
from .analysis import AnalysisPayload


def _gap_from_trace(trace: TraceStep) -> tuple[GapType, GapOrigin]:
    mapping = {
        "parameter_gap": (GapType.DEPENDENCY, GapOrigin.UNDEREXTRACTION),
        "missing_interlock": (GapType.INTEGRATION, GapOrigin.TRUE_STRUCTURAL_ABSENCE),
        "missing_edge": (GapType.DEPENDENCY, GapOrigin.TRUE_STRUCTURAL_ABSENCE),
        "missing_operator": (GapType.MECHANISM, GapOrigin.COMPRESSION_DAMAGE),
        "scope_limitation": (GapType.SCOPE, GapOrigin.SCOPE_MISMATCH),
        "analysis_artifact": (GapType.LENS, GapOrigin.FRAMING_FAILURE),
        "empirical_unknown": (GapType.EVIDENCE, GapOrigin.EVIDENCE_INSUFFICIENCY),
        "resolved": (GapType.IMPLEMENTATION, GapOrigin.TRUE_STRUCTURAL_ABSENCE),
    }
    return mapping.get(trace.divergence_class.value if trace.divergence_class else "resolved", (GapType.IMPLEMENTATION, GapOrigin.TRUE_STRUCTURAL_ABSENCE))


def _smallest_discriminative_unit(trace: TraceStep) -> str:
    if trace.operator_ref:
        return f"operator::{trace.operator_ref}"
    if trace.divergence_class == DivergenceClass.MISSING_INTERLOCK:
        return f"interlock::{trace.from_state}->{trace.to_state}"
    if trace.divergence_class == DivergenceClass.SCOPE_LIMITATION:
        return f"regime::{trace.branch_key or 'primary'}"
    return trace.trigger[:160] or trace.outcome[:160]


def derive_gap_records(
    payload: AnalysisPayload,
    traces: list[TraceStep],
    frictions: list[FrictionSignal],
    run_id: str = "",
) -> list[GapRecord]:
    gaps: list[GapRecord] = []
    for trace in traces:
        if not trace.divergence_class or trace.divergence_class.value == "resolved":
            continue
        gap_type, origin = _gap_from_trace(trace)
        gaps.append(
            GapRecord(
                id=f"gap::{trace.id}",
                title=f"{trace.divergence_class.value.replace('_', ' ')} gap",
                gap_type=gap_type,
                description=trace.outcome,
                likely_origin=origin,
                nearly_covers=[trace.operator_ref] if trace.operator_ref else [],
                insufficient_because="Forward tracing terminated with an unresolved divergence.",
                dissolved_by=[f"resolve::{trace.divergence_class.value}"],
                smallest_discriminative_unit=_smallest_discriminative_unit(trace),
                discriminator=trace.trigger[:200],
                blocking=trace.blocking,
                metadata={"derived": True, "trace_id": trace.id},
            )
        )
    if not gaps and frictions:
        friction = frictions[0]
        origin = {
            FrictionType.SUBSTRATE_FRICTION: GapOrigin.SCOPE_MISMATCH,
            FrictionType.CONCEPTUAL_DRIFT: GapOrigin.FRAMING_FAILURE,
            FrictionType.STRUCTURAL_MISMATCH: GapOrigin.TRUE_STRUCTURAL_ABSENCE,
            FrictionType.CONTINUITY_POISON: GapOrigin.COMPRESSION_DAMAGE,
        }[friction.friction_type]
        gaps.append(
            GapRecord(
                id=f"gap::{run_id}::{sha256_text(friction.rationale)[:12]}" if run_id else f"gap::{sha256_text(friction.rationale)[:12]}",
                title=friction.friction_type.value.lower(),
                gap_type=GapType.INTEGRATION,
                description=friction.rationale,
                likely_origin=origin,
                insufficient_because="Typed friction indicates a surviving unresolved object.",
                smallest_discriminative_unit=friction.criteria[0] if friction.criteria else friction.rationale[:160],
                discriminator=friction.rationale[:200],
                blocking=friction.severity >= 0.7,
                metadata={"derived": True},
            )
        )
    return gaps


def derive_search_records(gaps: list[GapRecord]) -> list[SearchRecord]:
    searches: list[SearchRecord] = []
    for gap in gaps:
        if gap.gap_type not in {GapType.EVIDENCE, GapType.MECHANISM, GapType.VALIDATION, GapType.DEPENDENCY}:
            continue
        searches.append(
            SearchRecord(
                id=f"search::{gap.id}",
                query=gap.discriminator or gap.smallest_discriminative_unit or gap.title,
                target_object=gap.title,
                smallest_discriminative_unit=gap.smallest_discriminative_unit or gap.title,
                rationale=f"Search the smallest discriminative unresolved unit exposed by {gap.title}.",
                status=SearchStatus.PLANNED,
                findings=[],
                metadata={"derived_from_gap": gap.id},
            )
        )
    return searches


def derive_basin_records(
    payload: AnalysisPayload,
    hypotheses: list[Hypothesis],
    tensions: list[Tension],
    frictions: list[FrictionSignal],
    run_id: str = "",
) -> list[BasinRecord]:
    basins: list[BasinRecord] = []
    for hypothesis in hypotheses:
        basins.append(
            BasinRecord(
                id=f"basin::{run_id}::{hypothesis.id or sha256_text(hypothesis.title)[:12]}" if run_id else f"basin::{hypothesis.id or sha256_text(hypothesis.title)[:12]}",
                title=hypothesis.title,
                basin_type=BasinType.LITERAL,
                description=hypothesis.description,
                status=hypothesis.status,
                preserves=hypothesis.preserves,
                conflicts=hypothesis.risks,
                explanatory_burden=hypothesis.explanatory_burden,
                weakening_conditions=hypothesis.weakening_conditions,
                discriminator_path=hypothesis.discriminator_path,
                discriminator=", ".join(hypothesis.discriminators[:2]),
                metadata={"derived_from": "hypothesis"},
            )
        )
    if tensions:
        basins.append(
            BasinRecord(
                id=f"basin::{run_id}::reinterpretive::{sha256_text(tensions[0].title)[:12]}" if run_id else f"basin::reinterpretive::{sha256_text(tensions[0].title)[:12]}",
                title="reinterpretive basin",
                basin_type=BasinType.REINTERPRETIVE,
                description="Preserve alternate readings while tensions remain unresolved.",
                status="OPEN",
                preserves=[tension.title for tension in tensions[:3]],
                conflicts=[tension.description for tension in tensions[:2]],
                explanatory_burden=["Keeps unresolved forces explicit until a discriminator kills a branch."],
                weakening_conditions=["Tensions resolve cleanly under a single basin without residue."],
                discriminator_path=[tensions[0].title],
                discriminator=tensions[0].title,
                metadata={"derived": True},
            )
        )
    if any(friction.friction_type == FrictionType.CONTINUITY_POISON for friction in frictions):
        basins.append(
            BasinRecord(
                id=f"basin::{run_id}::failure::{sha256_text(payload.task)[:12]}" if run_id else f"basin::failure::{sha256_text(payload.task)[:12]}",
                title="failure-mode basin",
                basin_type=BasinType.FAILURE_MODE,
                description="Known-bad continuity remains a live competing explanation of the current surface.",
                status="OPEN",
                preserves=["durability pressure"],
                conflicts=["stable continuation"],
                explanatory_burden=["Explains why continuity poison may be the real source of apparent progress."],
                weakening_conditions=["Placeholder continuity is removed and the sweep no longer reopens the field."],
                discriminator_path=["replace_poisoned_continuity", "rerun_sweep"],
                discriminator="replace the poisoned continuity and re-run the sweep",
                metadata={"derived": True},
            )
        )
    if not basins:
        basins.append(
            BasinRecord(
                id=f"basin::{run_id}::null::{sha256_text(payload.task)[:12]}" if run_id else f"basin::null::{sha256_text(payload.task)[:12]}",
                title="null basin",
                basin_type=BasinType.NULL,
                description="No alternate basin is yet well-articulated.",
                status="OPEN",
                preserves=[],
                conflicts=[],
                explanatory_burden=["Marks that alternate basins are still under-articulated."],
                weakening_conditions=["A stronger literal or reinterpretive basin becomes explicit."],
                discriminator_path=["gather_first_discriminator"],
                discriminator="gather a first discriminator before stabilizing",
                metadata={"derived": True},
            )
        )
    deduped: list[BasinRecord] = []
    seen_ids: set[str] = set()
    for basin in basins:
        if basin.id in seen_ids:
            continue
        seen_ids.add(basin.id)
        deduped.append(basin)
    return deduped
