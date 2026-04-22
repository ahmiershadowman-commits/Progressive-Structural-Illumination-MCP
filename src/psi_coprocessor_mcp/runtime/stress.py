"""Skeptic and anti-pattern passes."""

from __future__ import annotations

from ..models import (
    AntiPatternFinding,
    AntiPatternType,
    FindingSeverity,
    PsiRunState,
    SkepticFinding,
)
from ..utils import sha256_text


def generate_stress_findings(run_state: PsiRunState) -> tuple[list[SkepticFinding], list[AntiPatternFinding]]:
    skeptic_findings: list[SkepticFinding] = []
    antipattern_findings: list[AntiPatternFinding] = []

    if not run_state.state.applicability.applicable:
        skeptic_findings.append(
            SkepticFinding(
                id=f"skeptic::applicability::{sha256_text(run_state.metadata.run_id)[:12]}",
                claim_ref="",
                question="Why is PSI being run on a target that the applicability check does not accept without rescoping?",
                impact=run_state.state.applicability.rationale,
                severity=FindingSeverity.ERROR,
                blocking=True,
                metadata={"derived": True},
            )
        )

    for claim in run_state.state.C:
        if claim.load_bearing and not claim.evidence:
            skeptic_findings.append(
                SkepticFinding(
                    id=f"skeptic::{claim.id}",
                    claim_ref=claim.id,
                    question="What new evidence actually changed this claim?",
                    impact="Load-bearing claim lacks direct evidence in the current surface.",
                    severity=FindingSeverity.WARNING,
                    blocking=False,
                    metadata={"derived": True},
                )
            )
        if claim.provenance.value == "UNKNOWN" and claim.load_bearing:
            skeptic_findings.append(
                SkepticFinding(
                    id=f"skeptic::unknown::{claim.id}",
                    claim_ref=claim.id,
                    question="Why is this claim still carrying load while provenance remains UNKNOWN?",
                    impact="Unknown provenance on a load-bearing claim risks silent drift.",
                    severity=FindingSeverity.ERROR,
                    blocking=True,
                    metadata={"derived": True},
                )
            )

        lowered = claim.statement.lower()
        if any(token in lowered for token in {"obvious", "clearly", "just", "simply"}):
            antipattern_findings.append(
                AntiPatternFinding(
                    id=f"antipattern::plausibility::{claim.id}",
                    pattern_type=AntiPatternType.GAP_FILLING_BY_PLAUSIBILITY,
                    description="Claim uses plausibility or smoothing language instead of structural support.",
                    evidence=[claim.statement],
                    severity=FindingSeverity.WARNING,
                    blocking=False,
                    metadata={"derived": True},
                )
            )
        if "confidence" in lowered and "durab" in lowered:
            antipattern_findings.append(
                AntiPatternFinding(
                    id=f"antipattern::category::{claim.id}",
                    pattern_type=AntiPatternType.CATEGORY_COLLAPSE,
                    description="Claim risks collapsing truth confidence and reuse durability.",
                    evidence=[claim.statement],
                    severity=FindingSeverity.ERROR,
                    blocking=False,
                    metadata={"derived": True},
                )
            )
        if claim.provenance.value == "INFERRED" and claim.load_bearing and not claim.evidence:
            antipattern_findings.append(
                AntiPatternFinding(
                    id=f"antipattern::evidence::{claim.id}",
                    pattern_type=AntiPatternType.EVIDENCE_BORROWING,
                    description="Inferred claim carries structural load without direct support.",
                    evidence=[claim.statement],
                    severity=FindingSeverity.WARNING,
                    blocking=False,
                    metadata={"derived": True},
                )
            )
        if claim.scaffold_boundary and (
            not claim.scaffold_boundary.bounded or claim.scaffold_boundary.substitute_for_real_structure
        ):
            skeptic_findings.append(
                SkepticFinding(
                    id=f"skeptic::scaffold::{claim.id}",
                    claim_ref=claim.id,
                    question="What explicitly bounds this temporary scaffold, and what retires it before stable reuse?",
                    impact="Temporary structure is present without a safe boundary or exit condition.",
                    severity=FindingSeverity.ERROR if claim.load_bearing else FindingSeverity.WARNING,
                    blocking=claim.load_bearing,
                    metadata={"derived": True},
                )
            )

    if run_state.state.transition.decision.value in {"ANCHOR", "HALT"} and run_state.state.gaps:
        antipattern_findings.append(
            AntiPatternFinding(
                id=f"antipattern::stage::{sha256_text(run_state.metadata.run_id)[:12]}",
                pattern_type=AntiPatternType.STAGE_COLLAPSE,
                description="A stabilizing transition was selected while explicit gap records remain open.",
                evidence=[gap.title for gap in run_state.state.gaps[:4]],
                severity=FindingSeverity.WARNING,
                blocking=False,
                metadata={"derived": True},
                )
            )

    for basin in run_state.state.basins:
        if not basin.explanatory_burden:
            skeptic_findings.append(
                SkepticFinding(
                    id=f"skeptic::basin_burden::{basin.id}",
                    claim_ref=basin.id,
                    question="What explanatory work does this basin do that a weaker alternative cannot?",
                    impact="Live basin lacks explicit burden and risks performative pluralism.",
                    severity=FindingSeverity.WARNING,
                    blocking=False,
                    metadata={"derived": True},
                )
            )
        if not basin.discriminator_path:
            skeptic_findings.append(
                SkepticFinding(
                    id=f"skeptic::basin_path::{basin.id}",
                    claim_ref=basin.id,
                    question="What discriminator path would actually kill or stabilize this basin?",
                    impact="Live basin lacks a discriminator path.",
                    severity=FindingSeverity.WARNING,
                    blocking=False,
                    metadata={"derived": True},
                )
            )

    if any(gap.blocking and not gap.smallest_discriminative_unit for gap in run_state.state.gaps):
        antipattern_findings.append(
            AntiPatternFinding(
                id=f"antipattern::resolution::{sha256_text(run_state.metadata.run_id)[:12]}",
                pattern_type=AntiPatternType.CHECKLIST_GAMING,
                description="Blocking gaps remain without a smallest discriminative unresolved unit, encouraging diffuse search.",
                evidence=[gap.title for gap in run_state.state.gaps if gap.blocking][:4],
                severity=FindingSeverity.WARNING,
                blocking=False,
                metadata={"derived": True},
            )
        )

    return skeptic_findings, antipattern_findings
