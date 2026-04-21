"""Built-in methodology and stable-user memory seed data."""

from __future__ import annotations

from collections.abc import Iterable


METHOD_MEMORY_SEED: list[dict[str, object]] = [
    {
        "key": "current",
        "title": "PSI operating frame",
        "content": (
            "Progressive Structural Illumination treats visibility events as the atomic unit of progress, "
            "requires weighted whole-field coherence sweeps after meaningful updates, treats phases as re-entrant "
            "control regimes, and blocks known-bad continuity through a durability/native-minimality gate."
        ),
        "tags": ["psi", "operating-frame", "whole-field", "durability"],
        "metadata": {
            "source": "master methodology",
            "sections": ["0", "3.0", "6.1", "7.0", "10.5", "14.2", "14.3", "14.4"],
        },
    },
    {
        "key": "question-operators",
        "title": "Question operators",
        "content": (
            "Questions do structural work. Lens operators stabilize legitimacy conditions; primitive operators strip "
            "fake primitives; exposure operators force local contact; tension operators preserve instability; "
            "discriminator operators search for field-separating observations; durability operators block poisoned "
            "continuity; propagation operators force non-local revision."
        ),
        "tags": ["psi", "operators", "questions"],
        "metadata": {
            "operators": [
                "LENS_OPERATOR",
                "PRIMITIVE_OPERATOR",
                "EXPOSURE_OPERATOR",
                "TENSION_OPERATOR",
                "DISCRIMINATOR_OPERATOR",
                "DURABILITY_OPERATOR",
                "PROPAGATION_OPERATOR",
            ]
        },
    },
    {
        "key": "ai-contract",
        "title": "AI collaboration contract",
        "content": (
            "A PSI-compliant AI must not patch a local coordinate without stating field impact, must report uncertainty "
            "honestly when propagation cannot be completed, and must refuse stable continuation built on placeholders, "
            "convenience scaffolds, or known rewrite debt."
        ),
        "tags": ["psi", "ai-contract", "durability"],
        "metadata": {
            "constraints": [
                "no local-update patching without field impact",
                "uncertainty honesty",
                "no stable continuation on known-bad continuity",
            ]
        },
    },
    {
        "key": "normalization-map",
        "title": "PSI normalization map",
        "content": (
            "PSI remains the primary operating frame. The normalization rubric is an execution and control layer that "
            "preserves visibility events as atomic units, separates hard gates from soft heuristics, keeps summary "
            "distinct from structure, keeps unknown distinct from placeholder, and separates confidence from durability "
            "or reuse safety."
        ),
        "tags": ["psi", "normalization", "rubric", "control-layer"],
        "metadata": {
            "control_families": 6,
            "canonical_distinctions": [
                "confidence != durability",
                "summary != structure",
                "unknown != placeholder",
            ],
        },
    },
    {
        "key": "control-families",
        "title": "Canonical control families",
        "content": (
            "The canonical execution families are epistemic typing, primitive integrity, whole-field propagation, "
            "basin and tension control, durability/native-minimality, and regime/transition control. These are not "
            "phase labels; they are always-available control pressures with mode-specific activation."
        ),
        "tags": ["psi", "control-families", "routing"],
        "metadata": {
            "families": [
                "epistemic_typing",
                "primitive_integrity",
                "whole_field_propagation",
                "basin_tension_control",
                "durability_native_minimality",
                "regime_transition_control",
            ]
        },
    },
    {
        "key": "mode-profiles",
        "title": "Mode activation profiles",
        "content": (
            "Survey, closure, construction, audit, and repair each activate the same control families with different "
            "weights. Survey keeps basins live; closure intensifies propagation and durability; construction intensifies "
            "primitive integrity and durability; audit intensifies typing, stress, and anti-smoothing; repair "
            "prioritizes propagation re-entry and upstream restoration."
        ),
        "tags": ["psi", "modes", "activation-profiles"],
        "metadata": {
            "modes": ["survey", "closure", "construction", "audit", "repair"],
            "note": "Activation profiles modulate control pressure; they do not replace PSI regimes.",
        },
    },
    {
        "key": "compliance-checker",
        "title": "Pre-emission compliance checker",
        "content": (
            "Before stable emission, PSI should check for missing core artifacts, untyped claims, durability misuse, "
            "stale anchor reuse, untyped friction, and local-update prohibition failures. Compliance reports are not "
            "the reasoning process itself; they verify that the current surface has not drifted from PSI obligations."
        ),
        "tags": ["psi", "compliance", "quality-gate"],
        "metadata": {
            "checks": [
                "missing_artifacts",
                "untyped_claims",
                "durability_misuse",
                "stale_anchor_reuse",
                "untyped_friction",
                "local_update_prohibition",
            ]
        },
    },
    {
        "key": "control-regimes",
        "title": "Re-entrant control regimes",
        "content": (
            "The server must route work across scope lock, grounding, decomposition, dependency mapping, forward trace, "
            "coherence sweep, gap-pressure analysis, basin generation, synthesis, stress test, and iteration/halt. "
            "High-centrality or high-fragility anchor destabilization forces upstream re-entry instead of local repair."
        ),
        "tags": ["psi", "regimes", "routing"],
        "metadata": {
            "reentry": "earliest relevant upstream regime",
            "interrupt": "whole-field coherence sweep",
        },
    },
    {
        "key": "anti-patterns",
        "title": "PSI anti-pattern watchlist",
        "content": (
            "Never allow macro-term smuggling, purpose smuggling, correlation-as-causation, gap filling by plausibility, "
            "category collapse, confidence laundering, timescale laundering, evidence borrowing, stage collapse, or "
            "checklist gaming."
        ),
        "tags": ["psi", "anti-patterns"],
        "metadata": {
            "watchlist": [
                "macro-term smuggling",
                "purpose smuggling",
                "correlation-as-causation",
                "gap filling by plausibility",
                "category collapse",
                "confidence laundering",
                "timescale laundering",
                "evidence borrowing",
                "stage collapse",
                "checklist gaming",
            ]
        },
    },
]


STABLE_USER_MEMORY_SEED: list[dict[str, object]] = [
    {
        "key": "durability-intolerance",
        "title": "Reject placeholders and rewrite debt",
        "content": (
            "The user rejects placeholders, mocked core logic, convenience scaffolds, fake persistence, and any known-bad "
            "continuity that would require future tear-out."
        ),
        "tags": ["user", "durability", "constraints"],
        "metadata": {"priority": "high"},
    },
    {
        "key": "global-propagation",
        "title": "Expect global back-propagation",
        "content": (
            "A local update is not acceptable unless its upstream dependencies, downstream consequences, stance geometry, "
            "admissible abstractions, active tensions, and prior anchors are accounted for."
        ),
        "tags": ["user", "whole-field", "propagation"],
        "metadata": {"priority": "high"},
    },
    {
        "key": "research-build-unity",
        "title": "Research and building are one epistemic act",
        "content": (
            "The user treats research, debugging, architecture design, and construction as the same visibility-driven act. "
            "The system should not split cognition from implementation."
        ),
        "tags": ["user", "epistemics"],
        "metadata": {"priority": "medium"},
    },
    {
        "key": "structural-illumination",
        "title": "Prefer structural illumination over isolated extraction",
        "content": (
            "The user prefers structural illumination, preserved tensions, discriminator search, and durability-gated "
            "closure over isolated part extraction or checklist completion."
        ),
        "tags": ["user", "method", "tension-preservation"],
        "metadata": {"priority": "high"},
    },
]


def iter_seed_rows(include_user_lane: bool) -> Iterable[tuple[str, list[dict[str, object]]]]:
    yield "method", METHOD_MEMORY_SEED
    if include_user_lane:
        yield "user", STABLE_USER_MEMORY_SEED
