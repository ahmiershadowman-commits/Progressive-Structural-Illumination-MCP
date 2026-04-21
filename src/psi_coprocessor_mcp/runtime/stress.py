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

    return skeptic_findings, antipattern_findings
