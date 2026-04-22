"""Typed PSI state, runtime, and persistence models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PSIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, use_enum_values=False)


class RunMode(str, Enum):
    SURVEY = "survey"
    CLOSURE = "closure"
    CONSTRUCTION = "construction"
    AUDIT = "audit"
    REPAIR = "repair"


class RunStatus(str, Enum):
    OPEN = "OPEN"
    PARAMETRIC = "PARAMETRIC"
    SCOPE = "SCOPE"
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    UNRESOLVABLE = "UNRESOLVABLE"
    SUPERSEDED = "SUPERSEDED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    HALT = "HALT"


class TransitionDecision(str, Enum):
    ANCHOR = "ANCHOR"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    RESCOPE = "RESCOPE"
    ESCALATE = "ESCALATE"
    CONTINUE = "CONTINUE"
    HALT = "HALT"


class FrictionType(str, Enum):
    SUBSTRATE_FRICTION = "SUBSTRATE_FRICTION"
    CONCEPTUAL_DRIFT = "CONCEPTUAL_DRIFT"
    STRUCTURAL_MISMATCH = "STRUCTURAL_MISMATCH"
    CONTINUITY_POISON = "CONTINUITY_POISON"


class VisibilityEventType(str, Enum):
    OBSERVATION = "observation"
    CONTRADICTION = "contradiction"
    FAILURE = "failure"
    BUILD_RESULT = "build_result"
    WEIRD_FIT = "weird_fit"
    QUESTION = "question"
    REFRAME = "reframe"
    FRICTION = "friction"


class ProvenanceTag(str, Enum):
    SOURCE = "SOURCE"
    OBSERVED = "OBSERVED"
    GROUNDED = "GROUNDED"
    INFERRED = "INFERRED"
    CONSTRUCTED = "CONSTRUCTED"
    SPECULATIVE = "SPECULATIVE"
    UNKNOWN = "UNKNOWN"


class DurabilityMode(str, Enum):
    ADVISORY = "advisory"
    BLOCKING = "blocking"


class DurabilityClass(str, Enum):
    UNKNOWN = "UNKNOWN"
    SANDBOXED = "SANDBOXED"
    PROVISIONAL = "PROVISIONAL"
    CONDITIONAL = "CONDITIONAL"
    DURABLE = "DURABLE"
    POISONED = "POISONED"


class ConfidenceLevel(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    PROVISIONAL = "provisional"
    UNRESOLVED = "unresolved"


class RunClass(str, Enum):
    EXPLORATORY = "exploratory"
    WORKING = "working"
    CANONICAL = "canonical"


class MemoryLane(str, Enum):
    METHOD = "method"
    STABLE_USER = "stable_user"
    PROJECT = "project"
    RUN_STATE = "run_state"


class ActivationLevel(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    DORMANT = "dormant"


class ControlFamily(str, Enum):
    EPISTEMIC_TYPING = "epistemic_typing"
    PRIMITIVE_INTEGRITY = "primitive_integrity"
    WHOLE_FIELD_PROPAGATION = "whole_field_propagation"
    BASIN_TENSION_CONTROL = "basin_tension_control"
    DURABILITY_NATIVE_MINIMALITY = "durability_native_minimality"
    REGIME_TRANSITION_CONTROL = "regime_transition_control"


class OperatorFamily(str, Enum):
    LENS = "lens"
    PRIMITIVE = "primitive"
    EXPOSURE = "exposure"
    TENSION = "tension"
    DISCRIMINATOR = "discriminator"
    DURABILITY = "durability"
    PROPAGATION = "propagation"


class SourceKind(str, Enum):
    TASK = "task"
    DRAFT = "draft"
    DIFF = "diff"
    CONTEXT = "context"
    TEST_FAILURE = "test_failure"
    FILE = "file"
    NOTE = "note"
    SPEC = "spec"
    CODE = "code"


class RelationType(str, Enum):
    ENABLES = "enables"
    REQUIRES = "requires"
    CONSTRAINS = "constrains"
    MODIFIES = "modifies"
    PARAMETERIZES = "parameterizes"
    COMPLEMENTS = "complements"
    COMPETES_WITH = "competes_with"
    CONFLICTS_WITH = "conflicts_with"
    SAME_ROOT_DIFFERENT_FORM = "same_root_different_form"
    UNDERDETERMINED = "underdetermined"
    DIFFERENT_SCALE_VIEW_OF = "different_scale_view_of"


class DivergenceClass(str, Enum):
    RESOLVED = "resolved"
    PARAMETER_GAP = "parameter_gap"
    MISSING_INTERLOCK = "missing_interlock"
    MISSING_EDGE = "missing_edge"
    MISSING_OPERATOR = "missing_operator"
    SCOPE_LIMITATION = "scope_limitation"
    ANALYSIS_ARTIFACT = "analysis_artifact"
    EMPIRICAL_UNKNOWN = "empirical_unknown"


class GapType(str, Enum):
    EVIDENCE = "evidence"
    ONTOLOGY = "ontology"
    THEORY = "theory"
    MECHANISM = "mechanism"
    DEPENDENCY = "dependency"
    INTEGRATION = "integration"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    SCOPE = "scope"
    LENS = "lens"


class GapOrigin(str, Enum):
    EVIDENCE_INSUFFICIENCY = "evidence_insufficiency"
    UNDEREXTRACTION = "underextraction"
    COMPRESSION_DAMAGE = "compression_damage"
    FRAMING_FAILURE = "framing_failure"
    SCOPE_MISMATCH = "scope_mismatch"
    PLANE_MISMATCH = "plane_mismatch"
    TRUE_STRUCTURAL_ABSENCE = "true_structural_absence"


class SearchStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"


class BasinType(str, Enum):
    LITERAL = "literal"
    REINTERPRETIVE = "reinterpretive"
    SAME_ROOT_DIFFERENT_FORM = "same_root_different_form"
    SCALE_SHIFT = "scale_shift"
    NULL = "null"
    FAILURE_MODE = "failure_mode"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AntiPatternType(str, Enum):
    MACRO_TERM_SMUGGLING = "macro_term_smuggling"
    PURPOSE_SMUGGLING = "purpose_smuggling"
    CORRELATION_AS_CAUSATION = "correlation_as_causation"
    GAP_FILLING_BY_PLAUSIBILITY = "gap_filling_by_plausibility"
    CATEGORY_COLLAPSE = "category_collapse"
    CONFIDENCE_LAUNDERING = "confidence_laundering"
    TIMESCALE_LAUNDERING = "timescale_laundering"
    EVIDENCE_BORROWING = "evidence_borrowing"
    STAGE_COLLAPSE = "stage_collapse"
    CHECKLIST_GAMING = "checklist_gaming"


class Regime(str, Enum):
    TASK_CONTRACT_SCOPE_LOCK = "task_contract_scope_lock"
    SOURCE_GROUNDING = "source_grounding"
    PRIMITIVE_STABILIZATION = "primitive_stabilization"
    DEPENDENCY_MAPPING = "dependency_mapping"
    FORWARD_TRACING = "forward_tracing"
    WHOLE_FIELD_COHERENCE_SWEEP = "whole_field_coherence_sweep"
    GAP_PRESSURE = "gap_pressure"
    HYPOTHESIS_BASIN = "hypothesis_basin"
    SYNTHESIS_CONSTRUCTION = "synthesis_construction"
    STRESS_TEST = "stress_test"
    ITERATION_HALT = "iteration_halt"
    REPAIR = "repair"


class ArtifactType(str, Enum):
    SOURCE_REGISTER = "source_register"
    SCOPE_LOCK = "scope_lock"
    PROVISIONAL_DISTINCTION_LEDGER = "provisional_distinction_ledger"
    COMPONENT_LEDGER = "component_ledger"
    STATE_VARIABLE_LEDGER = "state_variable_ledger"
    OPERATOR_LEDGER = "operator_ledger"
    CONSTRAINT_LEDGER = "constraint_ledger"
    DEPENDENCY_AND_INTERLOCK_MAP = "dependency_and_interlock_map"
    TRACE_LEDGER = "trace_ledger"
    GAP_AND_PRESSURE_LEDGER = "gap_and_pressure_ledger"
    SEARCH_LOG = "search_log"
    HYPOTHESIS_BASIN_LEDGER = "hypothesis_basin_ledger"
    CONSTRUCTION_SPEC = "construction_spec"
    STRESS_TEST_REPORT = "stress_test_report"
    SUPERSESSION_LEDGER = "supersession_ledger"
    FINAL_SYNTHESIS = "final_synthesis"
    FIELD_STATE_REGISTER = "field_state_register"
    VISIBILITY_EVENT_LOG = "visibility_event_log"
    COHERENCE_SWEEP_LOG = "coherence_sweep_log"
    ANCHOR_REGISTER = "anchor_register"
    FRICTION_TYPE_LOG = "friction_type_log"


ARTIFACT_SEQUENCE = [
    ArtifactType.SOURCE_REGISTER,
    ArtifactType.SCOPE_LOCK,
    ArtifactType.PROVISIONAL_DISTINCTION_LEDGER,
    ArtifactType.COMPONENT_LEDGER,
    ArtifactType.STATE_VARIABLE_LEDGER,
    ArtifactType.OPERATOR_LEDGER,
    ArtifactType.CONSTRAINT_LEDGER,
    ArtifactType.DEPENDENCY_AND_INTERLOCK_MAP,
    ArtifactType.TRACE_LEDGER,
    ArtifactType.GAP_AND_PRESSURE_LEDGER,
    ArtifactType.SEARCH_LOG,
    ArtifactType.HYPOTHESIS_BASIN_LEDGER,
    ArtifactType.CONSTRUCTION_SPEC,
    ArtifactType.STRESS_TEST_REPORT,
    ArtifactType.SUPERSESSION_LEDGER,
    ArtifactType.FINAL_SYNTHESIS,
    ArtifactType.FIELD_STATE_REGISTER,
    ArtifactType.VISIBILITY_EVENT_LOG,
    ArtifactType.COHERENCE_SWEEP_LOG,
    ArtifactType.ANCHOR_REGISTER,
    ArtifactType.FRICTION_TYPE_LOG,
]


class TieredLabels(PSIModel):
    high: list[str] = Field(default_factory=list)
    medium: list[str] = Field(default_factory=list)
    low: list[str] = Field(default_factory=list)


class SalienceShift(PSIModel):
    promoted: list[str] = Field(default_factory=list)
    demoted: list[str] = Field(default_factory=list)


class WholeFieldRepresentation(PSIModel):
    dependencies_changed: list[str] = Field(default_factory=list)
    salience_updates: list[str] = Field(default_factory=list)
    abstraction_updates: list[str] = Field(default_factory=list)
    stance_updates: list[str] = Field(default_factory=list)
    anchor_updates: list[str] = Field(default_factory=list)
    tension_updates: list[str] = Field(default_factory=list)
    possibility_updates: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class LensState(PSIModel):
    object_in_play: str = ""
    admissible_level: str = ""
    real_units: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    legitimacy_conditions: list[str] = Field(default_factory=list)


class ScopeBoundaries(PSIModel):
    included: list[str] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class StanceGeometry(PSIModel):
    centrality: TieredLabels = Field(default_factory=TieredLabels)
    fragility: TieredLabels = Field(default_factory=TieredLabels)
    suspicion: list[str] = Field(default_factory=list)
    salience: SalienceShift = Field(default_factory=SalienceShift)


class TimescaleBands(PSIModel):
    immediate: list[str] = Field(default_factory=list)
    local_regime: list[str] = Field(default_factory=list)
    architectural: list[str] = Field(default_factory=list)
    long_horizon: list[str] = Field(default_factory=list)


class SubstrateConstraints(PSIModel):
    physical: list[str] = Field(default_factory=list)
    computational: list[str] = Field(default_factory=list)
    material: list[str] = Field(default_factory=list)
    implementation: list[str] = Field(default_factory=list)
    interface_context: list[str] = Field(default_factory=list)


class UncertaintyState(PSIModel):
    propagation_limits: list[str] = Field(default_factory=list)
    evidence_limits: list[str] = Field(default_factory=list)
    partial_propagation_warnings: list[str] = Field(default_factory=list)


class ConfidenceAxes(PSIModel):
    evidence_confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    causal_confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    scope_confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    representation_confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL


class ScaffoldBoundary(PSIModel):
    label: str = ""
    bounded: bool = False
    boundary: str = ""
    exit_condition: str = ""
    substitute_for_real_structure: bool = False
    notes: list[str] = Field(default_factory=list)


class ApplicabilityAssessment(PSIModel):
    applicable: bool = True
    rationale: str = ""
    boundaries: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PhaseRecord(PSIModel):
    regime: Regime
    reason: str = ""
    trigger: str = ""
    entered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SupersessionSnapshot(PSIModel):
    entity_type: str = ""
    entity_id: str = ""
    superseded_by: str = ""
    reason: str = ""
    created_at: str = ""


class VisibilityEvent(PSIModel):
    id: str = ""
    type: VisibilityEventType = VisibilityEventType.OBSERVATION
    title: str = ""
    description: str = ""
    source: str = ""
    severity: float = 0.5
    affected_entities: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("severity")
    @classmethod
    def _validate_severity(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class Anchor(PSIModel):
    id: str = ""
    name: str
    status: str = "active"
    description: str = ""
    centrality: float = 0.5
    fragility: float = 0.5
    confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    durability_class: DurabilityClass = DurabilityClass.PROVISIONAL
    rationale: str = ""
    dependencies: list[str] = Field(default_factory=list)
    implications: list[str] = Field(default_factory=list)
    weakening_conditions: list[str] = Field(default_factory=list)
    explanatory_burden: list[str] = Field(default_factory=list)
    scaffold_boundary: ScaffoldBoundary | None = None
    user_promoted: bool = False
    sweep_survival_count: int = 0
    metadata: dict[str, object] = Field(default_factory=dict)
    invalidated_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("centrality", "fragility")
    @classmethod
    def _clamp_weight(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class Tension(PSIModel):
    id: str = ""
    title: str
    status: str = "OPEN"
    description: str = ""
    severity: float = 0.5
    forces: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("severity")
    @classmethod
    def _clamp_severity(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class Hypothesis(PSIModel):
    id: str = ""
    title: str
    status: str = "OPEN"
    description: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    durability_class: DurabilityClass = DurabilityClass.PROVISIONAL
    preserves: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    discriminators: list[str] = Field(default_factory=list)
    weakening_conditions: list[str] = Field(default_factory=list)
    discriminator_path: list[str] = Field(default_factory=list)
    explanatory_burden: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Discriminator(PSIModel):
    id: str = ""
    title: str
    description: str = ""
    target: list[str] = Field(default_factory=list)
    best_next_probe: str = ""
    confidence_gain: float = 0.5
    expected_outcome_map: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("confidence_gain")
    @classmethod
    def _clamp_gain(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class Probe(PSIModel):
    id: str = ""
    title: str
    description: str = ""
    rationale: str = ""
    revelatory_value: float = 0.5
    load_bearing_entities: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("revelatory_value")
    @classmethod
    def _clamp_value(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class FrictionSignal(PSIModel):
    id: str = ""
    friction_type: FrictionType
    severity: float = 0.5
    routing_regime: Regime = Regime.WHOLE_FIELD_COHERENCE_SWEEP
    rationale: str = ""
    criteria: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("severity")
    @classmethod
    def _clamp_severity(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class TypedClaim(PSIModel):
    id: str = ""
    statement: str
    provenance: ProvenanceTag = ProvenanceTag.UNKNOWN
    load_bearing: bool = False
    structural_role: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    durability_class: DurabilityClass = DurabilityClass.UNKNOWN
    confidence_axes: ConfidenceAxes = Field(default_factory=ConfidenceAxes)
    scaffold_boundary: ScaffoldBoundary | None = None
    evidence: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    source: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModeActivation(PSIModel):
    mode: RunMode
    level: ActivationLevel
    weight: float
    rationale: str = ""

    @field_validator("weight")
    @classmethod
    def _clamp_weight(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class ControlFamilyState(PSIModel):
    family: ControlFamily
    description: str
    activation: ModeActivation
    hard_gate: bool = False
    primary_homes: list[Regime] = Field(default_factory=list)
    artifact_inputs: list[ArtifactType] = Field(default_factory=list)
    artifact_outputs: list[ArtifactType] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FrictionRoutingDecision(PSIModel):
    friction_type: FrictionType
    ordered_regimes: list[Regime] = Field(default_factory=list)
    primary_regime: Regime = Regime.WHOLE_FIELD_COHERENCE_SWEEP
    control_families: list[ControlFamily] = Field(default_factory=list)
    override_reasons: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DurabilityAssessment(PSIModel):
    placeholders: list[str] = Field(default_factory=list)
    convenience_scaffolds: list[str] = Field(default_factory=list)
    known_badness: list[str] = Field(default_factory=list)
    rewrite_debt: list[str] = Field(default_factory=list)
    mode: DurabilityMode = DurabilityMode.BLOCKING
    blocked: bool = False
    notes: list[str] = Field(default_factory=list)


class ConstraintItem(PSIModel):
    id: str = ""
    constraint_type: str
    category: str
    severity: str
    description: str
    source: str = ""
    timescale: str = ""
    active: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SourceObject(PSIModel):
    id: str = ""
    source_kind: SourceKind
    title: str
    locator: str = ""
    version: str = ""
    content_hash: str = ""
    canonical: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PrimitiveComponent(PSIModel):
    id: str = ""
    name: str
    description: str = ""
    component_kind: str = ""
    scope: str = ""
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StateVariableRecord(PSIModel):
    id: str = ""
    name: str
    description: str = ""
    variable_kind: str = ""
    scope: str = ""
    timescale: str = ""
    write_roles: list[str] = Field(default_factory=list)
    read_roles: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PrimitiveOperatorRecord(PSIModel):
    id: str = ""
    name: str
    family: OperatorFamily
    object_ref: str = ""
    state_variable_ref: str = ""
    trigger: str = ""
    direct_action: str = ""
    target: str = ""
    changes: list[str] = Field(default_factory=list)
    cannot_do: list[str] = Field(default_factory=list)
    where: str = ""
    when: str = ""
    directionality: str = ""
    timescale: str = ""
    persistence: str = ""
    reversibility: str = ""
    scope: str = ""
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InterlockRelation(PSIModel):
    id: str = ""
    relation_type: RelationType
    source_ref: str
    target_ref: str
    description: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.PROVISIONAL
    scope: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TraceStep(PSIModel):
    id: str = ""
    cascade_id: str = ""
    step_index: int = 0
    branch_key: str = ""
    operator_ref: str = ""
    from_state: str = ""
    to_state: str = ""
    trigger: str = ""
    outcome: str = ""
    divergence_class: DivergenceClass | None = None
    blocking: bool = False
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GapRecord(PSIModel):
    id: str = ""
    title: str
    gap_type: GapType
    description: str = ""
    likely_origin: GapOrigin = GapOrigin.TRUE_STRUCTURAL_ABSENCE
    nearly_covers: list[str] = Field(default_factory=list)
    insufficient_because: str = ""
    dissolved_by: list[str] = Field(default_factory=list)
    smallest_discriminative_unit: str = ""
    discriminator: str = ""
    blocking: bool = False
    status: str = "OPEN"
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SearchRecord(PSIModel):
    id: str = ""
    query: str
    target_object: str = ""
    smallest_discriminative_unit: str = ""
    rationale: str = ""
    status: SearchStatus = SearchStatus.PLANNED
    findings: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BasinRecord(PSIModel):
    id: str = ""
    title: str
    basin_type: BasinType
    description: str = ""
    status: str = "OPEN"
    preserves: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    explanatory_burden: list[str] = Field(default_factory=list)
    weakening_conditions: list[str] = Field(default_factory=list)
    discriminator_path: list[str] = Field(default_factory=list)
    discriminator: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SkepticFinding(PSIModel):
    id: str = ""
    claim_ref: str = ""
    question: str
    impact: str = ""
    severity: FindingSeverity = FindingSeverity.WARNING
    blocking: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AntiPatternFinding(PSIModel):
    id: str = ""
    pattern_type: AntiPatternType
    description: str
    evidence: list[str] = Field(default_factory=list)
    severity: FindingSeverity = FindingSeverity.WARNING
    blocking: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BlastRadiusImpact(PSIModel):
    entity_type: str
    entity_id: str
    entity_name: str
    score: float
    centrality: float
    fragility: float
    dependency_density: float
    timescale_proximity: float
    substrate_coupling: float
    durability_relevance: float
    stance_sensitivity: float
    rationale: str

    @field_validator(
        "score",
        "centrality",
        "fragility",
        "dependency_density",
        "timescale_proximity",
        "substrate_coupling",
        "durability_relevance",
        "stance_sensitivity",
    )
    @classmethod
    def _clamp_weight(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class TransitionState(PSIModel):
    decision: TransitionDecision = TransitionDecision.CONTINUE
    rationale: str = ""
    blocking_reasons: list[str] = Field(default_factory=list)
    recommended_regimes: list[Regime] = Field(default_factory=list)


class ComplianceIssue(PSIModel):
    issue_type: str
    severity: str
    blocking: bool = False
    message: str
    related_entities: list[str] = Field(default_factory=list)


class ComplianceReport(PSIModel):
    status: str = "PASS"
    blocking: bool = False
    requested_action: str = ""
    issues: list[ComplianceIssue] = Field(default_factory=list)
    checked_artifacts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SweepState(PSIModel):
    status: str = "idle"
    trigger_event_id: str | None = None
    impacted_entities: list[str] = Field(default_factory=list)
    deferred_entities: list[str] = Field(default_factory=list)
    last_run_at: datetime | None = None


class ArtifactPointers(PSIModel):
    source_register: str = ""
    scope_lock: str = ""
    provisional_distinction_ledger: str = ""
    component_ledger: str = ""
    state_variable_ledger: str = ""
    operator_ledger: str = ""
    constraint_ledger: str = ""
    dependency_and_interlock_map: str = ""
    trace_ledger: str = ""
    gap_and_pressure_ledger: str = ""
    search_log: str = ""
    hypothesis_basin_ledger: str = ""
    construction_spec: str = ""
    stress_test_report: str = ""
    supersession_ledger: str = ""
    final_synthesis: str = ""
    field_state_register: str = ""
    visibility_event_log: str = ""
    coherence_sweep_log: str = ""
    anchor_register: str = ""
    friction_type_log: str = ""


class ArtifactSnapshot(PSIModel):
    id: str = ""
    artifact_type: ArtifactType
    format: str = "markdown"
    content: str
    checksum: str
    authoritative: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SummaryBundle(PSIModel):
    expert_summary: str = ""
    plain_summary: str = ""
    compact_summary: str = ""


class RunMetadata(PSIModel):
    run_id: str
    project_id: str | None = None
    title: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mode: RunMode = RunMode.SURVEY
    run_class: RunClass = RunClass.EXPLORATORY
    status: RunStatus = RunStatus.OPEN
    durability_mode: DurabilityMode = DurabilityMode.BLOCKING


class RunStateVector(PSIModel):
    W: WholeFieldRepresentation = Field(default_factory=WholeFieldRepresentation)
    L: LensState = Field(default_factory=LensState)
    B: ScopeBoundaries = Field(default_factory=ScopeBoundaries)
    O: VisibilityEvent | None = None
    sources: list[SourceObject] = Field(default_factory=list)
    C: list[TypedClaim] = Field(default_factory=list)
    components: list[PrimitiveComponent] = Field(default_factory=list)
    state_variables: list[StateVariableRecord] = Field(default_factory=list)
    primitive_operators: list[PrimitiveOperatorRecord] = Field(default_factory=list)
    interlocks: list[InterlockRelation] = Field(default_factory=list)
    traces: list[TraceStep] = Field(default_factory=list)
    gaps: list[GapRecord] = Field(default_factory=list)
    searches: list[SearchRecord] = Field(default_factory=list)
    basins: list[BasinRecord] = Field(default_factory=list)
    skeptic_findings: list[SkepticFinding] = Field(default_factory=list)
    antipattern_findings: list[AntiPatternFinding] = Field(default_factory=list)
    A: list[Anchor] = Field(default_factory=list)
    U: list[Tension] = Field(default_factory=list)
    H: list[Hypothesis] = Field(default_factory=list)
    D: list[Discriminator] = Field(default_factory=list)
    F: list[FrictionSignal] = Field(default_factory=list)
    N: DurabilityAssessment = Field(default_factory=DurabilityAssessment)
    P: list[Probe] = Field(default_factory=list)
    T: TimescaleBands = Field(default_factory=TimescaleBands)
    S: SubstrateConstraints = Field(default_factory=SubstrateConstraints)
    G: StanceGeometry = Field(default_factory=StanceGeometry)
    applicability: ApplicabilityAssessment = Field(default_factory=ApplicabilityAssessment)
    current_phase: Regime = Regime.TASK_CONTRACT_SCOPE_LOCK
    phase_history: list[PhaseRecord] = Field(default_factory=list)
    next_gating_condition: str = ""
    open_artifacts: list[ArtifactType] = Field(default_factory=list)
    last_supersession: SupersessionSnapshot | None = None
    smallest_discriminative_unit: str = ""
    active_regimes: list[Regime] = Field(default_factory=lambda: [Regime.TASK_CONTRACT_SCOPE_LOCK])
    current_blast_radius: list[BlastRadiusImpact] = Field(default_factory=list)
    current_sweep_status: SweepState = Field(default_factory=SweepState)
    current_discriminator: str = ""
    active_operators: list[OperatorFamily] = Field(default_factory=list)
    control_families: list[ControlFamilyState] = Field(default_factory=list)
    friction_routing: list[FrictionRoutingDecision] = Field(default_factory=list)
    transition: TransitionState = Field(default_factory=TransitionState)
    compliance: ComplianceReport | None = None
    uncertainty: UncertaintyState = Field(default_factory=UncertaintyState)


class PsiRunState(PSIModel):
    metadata: RunMetadata
    state: RunStateVector = Field(default_factory=RunStateVector)
    artifacts: ArtifactPointers = Field(default_factory=ArtifactPointers)

    def machine_readable(self) -> dict[str, object]:
        visibility_event = self.state.O.model_dump(mode="json") if self.state.O else {
            "type": VisibilityEventType.OBSERVATION.value,
            "description": "",
        }
        friction_types = [signal.friction_type.value for signal in self.state.F]
        return {
            "psi_run": {
                "metadata": {
                    "schema_version": "1.2.0",
                    "run_id": self.metadata.run_id,
                    "project_id": self.metadata.project_id,
                    "timestamp": self.metadata.timestamp.isoformat(),
                    "mode": self.metadata.mode.value,
                    "run_class": self.metadata.run_class.value,
                    "status": self.metadata.status.value,
                    "durability_mode": self.metadata.durability_mode.value,
                },
                "state": {
                    "visibility_event": visibility_event,
                    "lens": self.state.L.model_dump(mode="json"),
                    "scope_boundaries": self.state.B.model_dump(mode="json"),
                    "field": self.state.W.model_dump(mode="json"),
                    "source_objects": [source.model_dump(mode="json") for source in self.state.sources],
                    "typed_claims": [claim.model_dump(mode="json") for claim in self.state.C],
                    "components": [component.model_dump(mode="json") for component in self.state.components],
                    "state_variables": [state_variable.model_dump(mode="json") for state_variable in self.state.state_variables],
                    "primitive_operators": [operator.model_dump(mode="json") for operator in self.state.primitive_operators],
                    "interlocks": [relation.model_dump(mode="json") for relation in self.state.interlocks],
                    "traces": [trace.model_dump(mode="json") for trace in self.state.traces],
                    "gaps": [gap.model_dump(mode="json") for gap in self.state.gaps],
                    "search_records": [search.model_dump(mode="json") for search in self.state.searches],
                    "basins": [basin.model_dump(mode="json") for basin in self.state.basins],
                    "skeptic_findings": [finding.model_dump(mode="json") for finding in self.state.skeptic_findings],
                    "antipattern_findings": [finding.model_dump(mode="json") for finding in self.state.antipattern_findings],
                    "stance_geometry": {
                        "centrality": self.state.G.centrality.model_dump(mode="json"),
                        "fragility": self.state.G.fragility.model_dump(mode="json"),
                        "suspicion": {"active": self.state.G.suspicion},
                        "salience": self.state.G.salience.model_dump(mode="json"),
                    },
                    "timescale_bands": self.state.T.model_dump(mode="json"),
                    "substrate_constraints": self.state.S.model_dump(mode="json"),
                    "friction": {"types": friction_types, "notes": self.state.transition.rationale},
                    "anchored_articulations": [anchor.model_dump(mode="json") for anchor in self.state.A],
                    "durability_constraints": self.state.N.model_dump(mode="json"),
                    "live_hypotheses": [hypothesis.model_dump(mode="json") for hypothesis in self.state.H],
                    "unresolved_tensions": [tension.model_dump(mode="json") for tension in self.state.U],
                    "discriminators": [discriminator.model_dump(mode="json") for discriminator in self.state.D],
                    "candidate_probes": [probe.model_dump(mode="json") for probe in self.state.P],
                    "operator_families": [operator.value for operator in self.state.active_operators],
                    "control_families": [family.model_dump(mode="json") for family in self.state.control_families],
                    "friction_routing": [routing.model_dump(mode="json") for routing in self.state.friction_routing],
                    "applicability": self.state.applicability.model_dump(mode="json"),
                    "current_phase": self.state.current_phase.value,
                    "phase_history": [entry.model_dump(mode="json") for entry in self.state.phase_history],
                    "next_gating_condition": self.state.next_gating_condition,
                    "open_artifacts": [artifact.value for artifact in self.state.open_artifacts],
                    "last_supersession": self.state.last_supersession.model_dump(mode="json")
                    if self.state.last_supersession
                    else None,
                    "smallest_discriminative_unit": self.state.smallest_discriminative_unit,
                    "transition": self.state.transition.model_dump(mode="json"),
                    "compliance": self.state.compliance.model_dump(mode="json") if self.state.compliance else None,
                    "uncertainty": self.state.uncertainty.model_dump(mode="json"),
                },
                "artifacts": self.artifacts.model_dump(mode="json"),
            }
        }


class MemoryEntry(PSIModel):
    id: str = ""
    lane: MemoryLane
    key: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    project_id: str | None = None
    run_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectSummary(PSIModel):
    project_id: str
    name: str
    scope_summary: str
    anchor_count: int = 0
    tension_count: int = 0
    hypothesis_count: int = 0
    constraint_count: int = 0
    last_run_id: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RetrievalHit(PSIModel):
    lane: MemoryLane
    document_type: str
    ref_id: str
    title: str
    content: str
    score: float = 0.0
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class ExportManifest(PSIModel):
    export_id: str
    run_id: str
    project_id: str | None = None
    export_format: str
    exported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    schema_version: str = "1.2.0"
