"""Heuristic PSI analysis helpers."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from ..models import (
    ConfidenceLevel,
    DurabilityClass,
    DurabilityAssessment,
    DurabilityMode,
    FrictionSignal,
    FrictionType,
    LensState,
    Probe,
    Regime,
    ScopeBoundaries,
    SourceKind,
    SourceObject,
    SubstrateConstraints,
    TimescaleBands,
    TypedClaim,
    ProvenanceTag,
    VisibilityEvent,
    VisibilityEventType,
)
from ..utils import sha256_text, unique_preserve_order

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bstub\b",
    r"\bplaceholder\b",
    r"\bmock(ed)?\b",
    r"\btemp(orary)?\b",
    r"\bprototype\b",
    r"\bv1\b",
    r"\brewrite later\b",
    r"\bdefer(red)?\b",
]

STRUCTURAL_PATTERNS = [
    r"\bmismatch\b",
    r"\bdoes(n't| not) fit\b",
    r"\bincoheren(t|ce)\b",
    r"\bforced articulation\b",
    r"\btopology\b",
    r"\bglobal\b.*\blocal\b",
]

CONCEPTUAL_PATTERNS = [
    r"\btoo clean\b",
    r"\bhand-?wave\b",
    r"\bgeneric\b",
    r"\belegan(t|ce)\b",
    r"\bjust\b",
    r"\bobvious(ly)?\b",
    r"\bmacro\b",
    r"\bchecklist\b",
]

SUBSTRATE_PATTERNS = [
    r"\berror\b",
    r"\bexception\b",
    r"\btraceback\b",
    r"\bfail(ed|ure)?\b",
    r"\bdependency\b.*\bbreak\b",
    r"\bcompile\b",
    r"\bimport\b.*\berror\b",
    r"\bconstraint\b",
    r"\btimeout\b",
]

ARCHITECTURE_KEYWORDS = {"architecture", "design", "schema", "runtime", "server", "protocol"}
DEBUG_KEYWORDS = {"debug", "failure", "error", "broken", "test", "traceback", "mismatch"}
PATCH_KEYWORDS = {"diff", "patch", "update", "change", "refactor", "migration"}
RESEARCH_KEYWORDS = {"why", "how", "evidence", "hypothesis", "tension", "constraint"}
LOAD_BEARING_KEYWORDS = {
    "must",
    "should",
    "need",
    "non-negotiable",
    "required",
    "durable",
    "architecture",
    "runtime",
    "schema",
    "scope",
    "boundary",
    "transition",
    "artifact",
    "anchor",
    "propagation",
}
SPECULATIVE_CUES = {"maybe", "might", "could", "possibly", "hypothesis", "suspect"}
UNKNOWN_CUES = {"unknown", "unclear", "not sure", "unresolved"}
WINDOWS_PATH_PATTERN = r"[A-Za-z]:\\[^\s\"']+"
POSIX_PATH_PATTERN = r"(?<![A-Za-z]:)(/[^\s\"']+)"
VERSION_PATTERN = r"\bv(?:ersion)?\s*(\d+(?:\.\d+)*)\b"


@dataclass(slots=True)
class AnalysisPayload:
    source_text: str
    task: str
    draft: str
    diff: str
    attached_context: str
    test_failure: str


def build_analysis_payload(
    task: str,
    draft: str = "",
    diff: str = "",
    attached_context: str = "",
    test_failure: str = "",
) -> AnalysisPayload:
    combined = "\n".join(part for part in [task, draft, diff, attached_context, test_failure] if part)
    return AnalysisPayload(
        source_text=combined,
        task=task,
        draft=draft,
        diff=diff,
        attached_context=attached_context,
        test_failure=test_failure,
    )


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_./:-]+", text.lower())


def _keywords(text: str) -> set[str]:
    return set(_tokens(text))


def _extract_signal_lines(text: str, patterns: list[str]) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if "not a placeholder" in lowered or "no placeholder" in lowered:
            continue
        if "not mocked" in lowered or "not a mock" in lowered:
            continue
        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
            lines.append(line)
    return lines[:8]


def detect_visibility_events(payload: AnalysisPayload) -> list[VisibilityEvent]:
    events: list[VisibilityEvent] = []
    task_lower = payload.task.lower()
    if payload.test_failure.strip():
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.FAILURE,
                title="test failure",
                description=payload.test_failure.strip().splitlines()[0][:200],
                source="test_failure",
                severity=0.9,
                evidence=payload.test_failure.strip().splitlines()[:5],
            )
        )
    if payload.diff.strip():
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.BUILD_RESULT,
                title="diff presented",
                description="A diff or patch was provided and changes must be propagated across the field.",
                source="diff",
                severity=0.7,
                evidence=payload.diff.strip().splitlines()[:8],
            )
        )
    if "?" in payload.task or any(word in task_lower for word in {"why", "how", "what"}):
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.QUESTION,
                title="operator question",
                description=payload.task.strip()[:240],
                source="task",
                severity=0.6,
            )
        )
    if any(word in task_lower for word in {"contradiction", "doesn't fit", "incoherent", "mismatch"}):
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.CONTRADICTION,
                title="contradiction surfaced",
                description=payload.task.strip()[:240],
                source="task",
                severity=0.8,
            )
        )
    if any(word in task_lower for word in {"reframe", "scope", "boundary", "rescope"}):
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.REFRAME,
                title="scope or lens change",
                description=payload.task.strip()[:240],
                source="task",
                severity=0.65,
            )
        )
    if not events:
        events.append(
            VisibilityEvent(
                type=VisibilityEventType.OBSERVATION,
                title="new observation",
                description=payload.task.strip()[:240],
                source="task",
                severity=0.5,
            )
        )
    return events


def infer_lens(payload: AnalysisPayload) -> LensState:
    terms = _keywords(payload.source_text)
    object_in_play = "task"
    admissible_level = "implementation"
    if terms & ARCHITECTURE_KEYWORDS:
        object_in_play = "architecture"
        admissible_level = "system-design"
    elif terms & DEBUG_KEYWORDS:
        object_in_play = "debugging-session"
        admissible_level = "failure-mechanism"
    elif terms & PATCH_KEYWORDS:
        object_in_play = "revision"
        admissible_level = "change-surface"
    elif terms & RESEARCH_KEYWORDS:
        object_in_play = "structural-question"
        admissible_level = "mechanistic-relation"
    real_units = sorted(
        {
            token
            for token in _tokens(payload.source_text)
            if any(ch in token for ch in {"/", ".", "_"})
            or token.endswith(("server", "runtime", "schema", "state", "anchor", "constraint"))
        }
    )[:12]
    exclusions = []
    if re.search(r"\bnot\b", payload.task, flags=re.IGNORECASE):
        exclusions.append("respect explicit user exclusions from the task statement")
    legitimacy_conditions = [
        "state the whole-field impact before advancing a local change",
        "preserve unresolved tensions rather than smoothing them away",
        "apply the durability gate before treating continuity as legitimate",
    ]
    return LensState(
        object_in_play=object_in_play,
        admissible_level=admissible_level,
        real_units=real_units,
        exclusions=exclusions,
        legitimacy_conditions=legitimacy_conditions,
    )


def infer_scope(payload: AnalysisPayload) -> ScopeBoundaries:
    included = [payload.task.strip()[:180]] if payload.task.strip() else []
    if payload.diff.strip():
        included.append("provided diff or patch")
    if payload.test_failure.strip():
        included.append("provided failure log")
    excluded = []
    for line in payload.task.splitlines():
        if "do not" in line.lower():
            excluded.append(line.strip())
    success_criteria = [
        "field impact articulated",
        "durability gate passed or explicitly blocked",
        "transition selected with rationale",
    ]
    assumptions = [
        "the input text is a partial view of the active field",
        "blast radius can be prioritized without exhaustive re-audit",
    ]
    return ScopeBoundaries(
        included=included,
        excluded=excluded,
        success_criteria=success_criteria,
        assumptions=assumptions,
    )


def _claim_role(statement: str) -> str:
    lowered = statement.lower()
    if any(token in lowered for token in {"must", "required", "non-negotiable", "constraint"}):
        return "constraint"
    if any(token in lowered for token in {"scope", "boundary", "exclude"}):
        return "scope"
    if any(token in lowered for token in {"error", "failure", "traceback", "diff --git", "failed"}):
        return "observation"
    if any(token in lowered for token in {"mismatch", "tension", "unresolved", "contradiction"}):
        return "tension"
    if any(token in lowered for token in {"anchor", "rollback", "rescope", "continue", "halt", "escalate"}):
        return "transition"
    return "proposal"


def _claim_provenance(statement: str, source: str) -> ProvenanceTag:
    lowered = statement.lower()
    if source == "attached_context":
        return ProvenanceTag.SOURCE
    if any(token in lowered for token in {"grounded", "verified", "reproduced", "measured", "direct evidence"}):
        return ProvenanceTag.GROUNDED
    if any(token in lowered for token in UNKNOWN_CUES):
        return ProvenanceTag.UNKNOWN
    if any(token in lowered for token in SPECULATIVE_CUES):
        return ProvenanceTag.SPECULATIVE
    if source in {"diff", "test_failure", "attached_context"}:
        return ProvenanceTag.OBSERVED
    if source == "draft":
        return ProvenanceTag.CONSTRUCTED
    if source == "task":
        return ProvenanceTag.INFERRED
    return ProvenanceTag.UNKNOWN


def _claim_confidence(statement: str, provenance: ProvenanceTag) -> ConfidenceLevel:
    lowered = statement.lower()
    if provenance == ProvenanceTag.OBSERVED:
        return ConfidenceLevel.MODERATE
    if provenance == ProvenanceTag.SOURCE:
        return ConfidenceLevel.MODERATE
    if provenance == ProvenanceTag.GROUNDED:
        return ConfidenceLevel.STRONG
    if provenance == ProvenanceTag.CONSTRUCTED:
        return ConfidenceLevel.PROVISIONAL
    if provenance == ProvenanceTag.SPECULATIVE:
        return ConfidenceLevel.WEAK
    if provenance == ProvenanceTag.UNKNOWN:
        return ConfidenceLevel.UNRESOLVED
    if any(token in lowered for token in {"must", "non-negotiable", "required"}):
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.PROVISIONAL


def _claim_durability(statement: str) -> DurabilityClass:
    lowered = statement.lower()
    if any(re.search(pattern, statement, flags=re.IGNORECASE) for pattern in PLACEHOLDER_PATTERNS):
        return DurabilityClass.POISONED
    if any(token in lowered for token in {"sandbox", "temporary", "prototype", "experimental"}):
        return DurabilityClass.SANDBOXED
    if any(token in lowered for token in {"durable", "native-minimal", "production-ready", "field-tested"}):
        return DurabilityClass.DURABLE
    if any(token in lowered for token in {"provisional", "for now", "interim", "bounded"}):
        return DurabilityClass.CONDITIONAL
    if any(token in lowered for token in UNKNOWN_CUES):
        return DurabilityClass.UNKNOWN
    return DurabilityClass.PROVISIONAL


def infer_typed_claims(payload: AnalysisPayload) -> list[TypedClaim]:
    raw_claims: list[tuple[str, str]] = []
    sources = [
        ("task", payload.task),
        ("draft", payload.draft),
        ("diff", payload.diff),
        ("attached_context", payload.attached_context),
        ("test_failure", payload.test_failure),
    ]
    for source, text in sources:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            raw_claims.append((source, line[:320]))
    deduped = unique_preserve_order(raw_claims)
    claims: list[TypedClaim] = []
    for idx, (source, statement) in enumerate(deduped[:12], start=1):
        lowered = statement.lower()
        load_bearing = any(keyword in lowered for keyword in LOAD_BEARING_KEYWORDS) or source in {"diff", "test_failure"}
        provenance = _claim_provenance(statement, source)
        claims.append(
            TypedClaim(
                id=f"claim_{idx}",
                statement=statement,
                provenance=provenance,
                load_bearing=load_bearing,
                structural_role=_claim_role(statement),
                confidence=_claim_confidence(statement, provenance),
                durability_class=_claim_durability(statement),
                evidence=[statement] if source in {"diff", "test_failure", "attached_context"} else [],
                notes=["derived heuristically from source text"],
                source=source,
            )
        )
    return claims


def infer_source_objects(payload: AnalysisPayload) -> list[SourceObject]:
    records: list[SourceObject] = []
    sources: list[tuple[SourceKind, str, str]] = [
        (SourceKind.TASK, "task", payload.task),
        (SourceKind.DRAFT, "draft", payload.draft),
        (SourceKind.DIFF, "diff", payload.diff),
        (SourceKind.CONTEXT, "attached_context", payload.attached_context),
        (SourceKind.TEST_FAILURE, "test_failure", payload.test_failure),
    ]
    for kind, locator, text in sources:
        stripped = text.strip()
        if not stripped:
            continue
        path_candidates = unique_preserve_order(
            re.findall(WINDOWS_PATH_PATTERN, stripped) + re.findall(POSIX_PATH_PATTERN, stripped)
        )[:8]
        version_match = re.search(VERSION_PATTERN, stripped, flags=re.IGNORECASE)
        records.append(
            SourceObject(
                id=f"source::{kind.value}::{sha256_text(stripped)[:12]}",
                source_kind=kind,
                title=stripped.splitlines()[0][:120],
                locator=locator,
                version=version_match.group(1) if version_match else "",
                content_hash=sha256_text(stripped),
                canonical=False,
                metadata={
                    "line_count": len(stripped.splitlines()),
                    "path_candidates": path_candidates,
                    "first_line": stripped.splitlines()[0][:240],
                },
            )
        )
    return records


def type_friction(payload: AnalysisPayload) -> list[FrictionSignal]:
    source = payload.source_text
    typed: list[FrictionSignal] = []
    pattern_map = [
        (
            FrictionType.CONTINUITY_POISON,
            PLACEHOLDER_PATTERNS,
            Regime.REPAIR,
            "Known-bad continuity or placeholder dependence was detected.",
        ),
        (
            FrictionType.STRUCTURAL_MISMATCH,
            STRUCTURAL_PATTERNS,
            Regime.DEPENDENCY_MAPPING,
            "Local fit and global fit are diverging or topology is inconsistent.",
        ),
        (
            FrictionType.CONCEPTUAL_DRIFT,
            CONCEPTUAL_PATTERNS,
            Regime.PRIMITIVE_STABILIZATION,
            "Narrative smoothing or elegance substitution is displacing grounded articulation.",
        ),
        (
            FrictionType.SUBSTRATE_FRICTION,
            SUBSTRATE_PATTERNS,
            Regime.FORWARD_TRACING,
            "Concrete build, dependency, or implementation constraints are resisting the current move.",
        ),
    ]
    for friction_type, patterns, routing_regime, rationale in pattern_map:
        evidence = _extract_signal_lines(source, patterns)
        if evidence:
            typed.append(
                FrictionSignal(
                    friction_type=friction_type,
                    severity=min(1.0, 0.45 + (len(evidence) * 0.1)),
                    routing_regime=routing_regime,
                    rationale=rationale,
                    criteria=evidence,
                    evidence=evidence,
                )
            )
    if not typed:
        typed.append(
            FrictionSignal(
                friction_type=FrictionType.CONCEPTUAL_DRIFT,
                severity=0.25,
                routing_regime=Regime.WHOLE_FIELD_COHERENCE_SWEEP,
                rationale="No explicit friction markers surfaced, so the lowest-risk default is a conceptual-drift check.",
                criteria=["fallback friction typing"],
                evidence=[],
            )
        )
    return typed


def assess_durability(payload: AnalysisPayload, mode: DurabilityMode) -> DurabilityAssessment:
    text = payload.source_text
    placeholders = _extract_signal_lines(text, PLACEHOLDER_PATTERNS)
    convenience_scaffolds = [
        line
        for line in text.splitlines()
        if re.search(r"\b(scaffold|temporary|later|future work|stub)\b", line, flags=re.IGNORECASE)
    ][:8]
    known_badness = [
        line
        for line in text.splitlines()
        if re.search(r"\b(rewrite debt|known-bad|poison|hack)\b", line, flags=re.IGNORECASE)
    ][:8]
    rewrite_debt = [
        line
        for line in text.splitlines()
        if re.search(r"\brewrite\b|\btear[- ]out\b|\bredo later\b", line, flags=re.IGNORECASE)
    ][:8]
    blocked = mode == DurabilityMode.BLOCKING and bool(
        placeholders or convenience_scaffolds or known_badness or rewrite_debt
    )
    notes = []
    if blocked:
        notes.append("Blocking mode is active and known-bad continuity signals were detected.")
    elif placeholders or convenience_scaffolds or known_badness or rewrite_debt:
        notes.append("Durability concerns detected; advisory mode leaves the move visible but not blocked.")
    else:
        notes.append("No placeholder or rewrite-debt markers were detected in the provided material.")
    return DurabilityAssessment(
        placeholders=placeholders,
        convenience_scaffolds=convenience_scaffolds,
        known_badness=known_badness,
        rewrite_debt=rewrite_debt,
        mode=mode,
        blocked=blocked,
        notes=notes,
    )


def infer_timescale_bands(payload: AnalysisPayload) -> TimescaleBands:
    text = payload.source_text.lower()
    immediate = [item for item in ["compile", "test", "syntax", "import", "diff"] if item in text]
    local_regime = [item for item in ["function", "module", "class", "tool", "resource"] if item in text]
    architectural = [item for item in ["schema", "migration", "runtime", "persistence", "transport"] if item in text]
    long_horizon = [item for item in ["maintenance", "durable", "future", "resume", "export"] if item in text]
    return TimescaleBands(
        immediate=immediate,
        local_regime=local_regime,
        architectural=architectural,
        long_horizon=long_horizon,
    )


def infer_substrate_constraints(payload: AnalysisPayload) -> SubstrateConstraints:
    tokens = _keywords(payload.source_text)
    physical = sorted(tokens & {"memory", "disk", "latency", "network"})[:8]
    computational = sorted(tokens & {"sqlite", "json", "yaml", "fts5", "python", "mcp"})[:8]
    material = sorted(tokens & {"schema", "file", "artifact", "diff", "patch"})[:8]
    implementation = sorted(tokens & {"tool", "resource", "prompt", "transport", "server", "cli"})[:8]
    interface_context = sorted(tokens & {"host", "stdio", "http", "streamable-http", "session"})[:8]
    return SubstrateConstraints(
        physical=physical,
        computational=computational,
        material=material,
        implementation=implementation,
        interface_context=interface_context,
    )


def summarize_local_articulation(payload: AnalysisPayload) -> dict[str, object]:
    source = payload.diff or payload.task or payload.attached_context
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    changed_files = [line for line in lines if re.search(r"[A-Za-z]:\\|/|\.py|\.md|\.json|\.sql", line)]
    bullets = lines[:6]
    return {
        "changed_surface": changed_files[:8],
        "articulation_points": bullets,
        "unexplained_residue": [
            line for line in bullets if "?" in line or "TODO" in line or "why" in line.lower()
        ][:4],
    }


def suggest_probes(
    frictions: list[FrictionSignal],
    payload: AnalysisPayload,
    articulation: dict[str, object],
) -> list[Probe]:
    probes: list[Probe] = []
    seen: set[str] = set()
    for friction in frictions:
        if friction.friction_type == FrictionType.SUBSTRATE_FRICTION:
            title = "reproduce the concrete failure"
            rationale = "Shortest-timescale concrete reproduction will expose whether the issue is substrate-bound."
        elif friction.friction_type == FrictionType.CONTINUITY_POISON:
            title = "replace the placeholder with a durable articulation"
            rationale = "Continuity poison should be discharged before forward movement."
        elif friction.friction_type == FrictionType.STRUCTURAL_MISMATCH:
            title = "trace the dependency joint that no longer composes"
            rationale = "Mismatch requires identifying the incompatible interlock rather than repairing locally."
        else:
            title = "strip abstraction and restate the local mechanism"
            rationale = "Conceptual drift is best countered by concrete articulation."
        if title in seen:
            continue
        seen.add(title)
        probes.append(
            Probe(
                title=title,
                description=(articulation.get("articulation_points") or [payload.task])[0],
                rationale=rationale,
                revelatory_value=min(0.95, 0.45 + friction.severity / 2),
                load_bearing_entities=friction.criteria[:4],
            )
        )
    return probes


def choose_best_discriminator(frictions: list[FrictionSignal], probes: list[Probe]) -> str:
    if not probes:
        return "No probe candidates are active."
    if any(signal.friction_type == FrictionType.CONTINUITY_POISON for signal in frictions):
        return "Replace the known placeholder path with the smallest durable implementation and re-run the coherence sweep."
    if any(signal.friction_type == FrictionType.STRUCTURAL_MISMATCH for signal in frictions):
        return "Trace which dependency or interlock fails first when the local articulation is propagated upstream and downstream."
    if any(signal.friction_type == FrictionType.SUBSTRATE_FRICTION for signal in frictions):
        return "Construct the smallest reproduction that preserves the observed failure."
    return probes[0].title


def summarize_whole_field_impact(
    payload: AnalysisPayload,
    frictions: list[FrictionSignal],
    articulation: dict[str, object],
) -> list[str]:
    effects: list[str] = []
    if payload.diff.strip():
        effects.append("A concrete change surface exists and must be propagated beyond the local patch.")
    if any(signal.friction_type == FrictionType.STRUCTURAL_MISMATCH for signal in frictions):
        effects.append("At least one dependency or topology assumption should be re-evaluated, not merely the touched surface.")
    if any(signal.friction_type == FrictionType.CONTINUITY_POISON for signal in frictions):
        effects.append("Durability legitimacy is compromised until placeholder continuity is removed or explicitly rejected.")
    if articulation.get("unexplained_residue"):
        effects.append("Residual unexplained local articulation should stay live as tension rather than be smoothed over.")
    if not effects:
        effects.append("No central destabilization is obvious yet, but a lightweight coherence sweep is still required.")
    return effects


def classify_active_mode(payload: AnalysisPayload) -> str:
    token_counts = Counter(_tokens(payload.source_text))
    if any(token_counts[keyword] for keyword in DEBUG_KEYWORDS):
        return "repair"
    if any(token_counts[keyword] for keyword in ARCHITECTURE_KEYWORDS):
        return "construction"
    if any(token_counts[keyword] for keyword in RESEARCH_KEYWORDS):
        return "survey"
    return "audit"
