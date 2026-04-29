"""High-level PSI runtime service."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml

from .config import ServerSettings
from .models import (
    Anchor,
    ArtifactType,
    BlastRadiusImpact,
    ComplianceReport,
    ConfidenceLevel,
    ConstraintItem,
    Discriminator,
    DurabilityClass,
    DurabilityMode,
    ExportManifest,
    FrictionSignal,
    FrictionType,
    MemoryEntry,
    MemoryLane,
    PhaseRecord,
    ProjectSummary,
    PsiRunState,
    Regime,
    RunMetadata,
    RunClass,
    RunMode,
    RunStateVector,
    RunStatus,
    ScaffoldBoundary,
    SourceObject,
    SummaryBundle,
    SupersessionSnapshot,
    Tension,
    TransitionDecision,
    TransitionState,
    VisibilityEvent,
    VisibilityEventType,
)
from .models import Hypothesis as PsiHypothesis
from .repository import Repository
from .runtime.analysis import (
    AnalysisPayload,
    assess_applicability,
    assess_durability,
    build_analysis_payload,
    choose_best_discriminator,
    classify_active_mode,
    detect_visibility_events,
    infer_lens,
    infer_scope,
    infer_source_objects,
    infer_substrate_constraints,
    infer_typed_claims,
    infer_timescale_bands,
    suggest_probes,
    summarize_local_articulation,
    summarize_whole_field_impact,
    type_friction,
)
from .runtime.artifacts import generate_artifacts
from .runtime.compliance import evaluate_compliance
from .runtime.coherence import estimate_blast_radius, recommend_transition, route_regimes, summarize_impacts
from .runtime.control import (
    build_control_family_states,
    build_friction_routing,
    control_family_catalog,
    detect_operator_families,
    mode_profile_catalog,
)
from .runtime.gaps import derive_basin_records, derive_gap_records, derive_search_records
from .runtime.source_audit import audit_source_objects
from .runtime.stress import generate_stress_findings
from .runtime.structure import (
    extract_components,
    extract_interlocks,
    extract_primitive_operators,
    extract_state_variables,
)
from .runtime.summaries import generate_summary_bundle
from .runtime.tracing import build_trace_steps
from .utils import canonical_json, ensure_directory, sha256_text, unique_preserve_order, utc_now

REGIME_EXPLANATIONS = {
    "task_contract_scope_lock": "Defines what object is in play, what is excluded, and what would count as completion.",
    "source_grounding": "Re-checks whether the current move remains anchored to concrete evidence or source material.",
    "primitive_stabilization": "Strips fake primitives, elegance substitution, and narrative shorthand.",
    "dependency_mapping": "Maps enabling, constraining, competing, and same-root relations before treating mismatch as real.",
    "forward_tracing": "Follows shortest-timescale enabled transitions first and stops at failures, unknown branches, or dead ends.",
    "whole_field_coherence_sweep": "Prioritized non-local re-evaluation driven by blast radius, not exhaustive serial re-audit.",
    "gap_pressure": "Distinguishes true missing support from framing damage, overload, or decomposition artifacts.",
    "hypothesis_basin": "Keeps competing basins live until a discriminator kills or stabilizes them.",
    "synthesis_construction": "Builds only from obligations, preserved invariants, accepted dependencies, and hard constraints.",
    "stress_test": "Attacks formation quality, false closure, hidden scaffolds, and under-propagated revisions.",
    "iteration_halt": "Determines whether to continue, anchor, rescope, escalate, rollback, or halt.",
    "repair": "Re-enters upstream structure after failure, corruption, or continuity poison invalidates the current surface.",
}


class PsiService:
    def __init__(self, repository: Repository, settings: ServerSettings):
        self.repository = repository
        self.settings = settings

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"

    def _effective_durability_mode(self, override: str | None = None) -> DurabilityMode:
        raw = (override or self.settings.default_durability_mode).lower()
        return DurabilityMode.BLOCKING if raw == "blocking" else DurabilityMode.ADVISORY

    def _ensure_project(
        self,
        project_id: str | None,
        project_name: str | None,
        scope_summary: str,
    ) -> ProjectSummary | None:
        if not project_id and not project_name:
            return None
        return self.repository.ensure_project(
            name=project_name or project_id or "PSI Project",
            scope_summary=scope_summary,
            project_id=project_id,
        )

    def _hydrate_run_state(self, run_state: PsiRunState) -> PsiRunState:
        project_id = run_state.metadata.project_id
        if project_id:
            run_state.state.A = self.repository.list_anchors(project_id)
            run_state.state.U = self.repository.list_tensions(project_id)
            run_state.state.H = self.repository.list_hypotheses(project_id)
            run_state.state.D = self.repository.list_discriminators(project_id)
        run_state.state.sources = self.repository.list_source_objects(run_state.metadata.run_id)
        run_state.state.components = self.repository.list_primitive_components(run_state.metadata.run_id)
        run_state.state.state_variables = self.repository.list_state_variables(run_state.metadata.run_id)
        run_state.state.primitive_operators = self.repository.list_primitive_operators(run_state.metadata.run_id)
        run_state.state.interlocks = self.repository.list_interlocks(run_state.metadata.run_id)
        run_state.state.traces = self.repository.list_trace_steps(run_state.metadata.run_id)
        run_state.state.gaps = self.repository.list_gap_records(run_state.metadata.run_id)
        run_state.state.searches = self.repository.list_search_records(run_state.metadata.run_id)
        run_state.state.basins = self.repository.list_basin_records(run_state.metadata.run_id)
        run_state.state.skeptic_findings = self.repository.list_skeptic_findings(run_state.metadata.run_id)
        run_state.state.antipattern_findings = self.repository.list_antipattern_findings(run_state.metadata.run_id)
        persisted_claims = self.repository.list_typed_claims(run_state.metadata.run_id)
        if persisted_claims:
            run_state.state.C = persisted_claims
        persisted_compliance = self.repository.get_compliance_report(run_state.metadata.run_id)
        if persisted_compliance:
            run_state.state.compliance = persisted_compliance
        if not run_state.state.control_families:
            run_state.state.control_families = build_control_family_states(run_state.metadata.mode)
        return run_state

    def _apply_runtime_control_surface(
        self,
        run_state: PsiRunState,
        payload: AnalysisPayload,
        impacts: list[BlastRadiusImpact],
        frictions: list[FrictionSignal],
        durability_blocked: bool,
    ) -> None:
        run_state.state.C = infer_typed_claims(payload, run_id=run_state.metadata.run_id)
        run_state.state.active_operators = detect_operator_families(payload)
        run_state.state.control_families = build_control_family_states(run_state.metadata.mode)
        run_state.state.friction_routing = build_friction_routing(
            frictions=frictions,
            mode=run_state.metadata.mode,
            impacts=impacts,
            durability_blocked=durability_blocked,
        )
        run_state.state.active_regimes = route_regimes(
            frictions,
            mode=run_state.metadata.mode,
            impacts=impacts,
            durability_blocked=durability_blocked,
        )

    def _refresh_methodology_objects(
        self,
        run_state: PsiRunState,
        payload: AnalysisPayload,
        frictions: list[FrictionSignal],
    ) -> None:
        run_id = run_state.metadata.run_id
        run_state.state.sources = infer_source_objects(payload, run_id=run_id)
        run_state.state.components = extract_components(payload, run_state.state.C, run_id=run_id)
        run_state.state.state_variables = extract_state_variables(payload, run_state.state.C, frictions, run_id=run_id)
        run_state.state.primitive_operators = extract_primitive_operators(
            payload=payload,
            active_operators=run_state.state.active_operators,
            components=run_state.state.components,
            state_variables=run_state.state.state_variables,
            run_id=run_id,
        )
        run_state.state.interlocks = extract_interlocks(
            components=run_state.state.components,
            state_variables=run_state.state.state_variables,
            primitive_operators=run_state.state.primitive_operators,
            claims=run_state.state.C,
        )
        run_state.state.traces = build_trace_steps(
            payload=payload,
            primitive_operators=run_state.state.primitive_operators,
            frictions=frictions,
        )
        run_state.state.gaps = derive_gap_records(payload, run_state.state.traces, frictions, run_id=run_id)
        run_state.state.searches = derive_search_records(run_state.state.gaps)
        run_state.state.basins = derive_basin_records(
            payload=payload,
            hypotheses=run_state.state.H,
            tensions=run_state.state.U,
            frictions=frictions,
            run_id=run_id,
        )
        skeptic_findings, antipattern_findings = generate_stress_findings(run_state)
        run_state.state.skeptic_findings = skeptic_findings
        run_state.state.antipattern_findings = antipattern_findings

    def _audit_sources(self, run_state: PsiRunState) -> dict[str, object]:
        audited_sources, audit_summary = audit_source_objects(
            run_state.state.sources,
            artifacts=self.repository.list_artifacts(run_state.metadata.run_id),
        )
        run_state.state.sources = audited_sources
        return audit_summary

    def _ensure_authoritative_structures(self, run_state: PsiRunState, summary: SummaryBundle) -> None:
        if (
            run_state.state.sources
            and run_state.state.components
            and run_state.state.state_variables
            and run_state.state.primitive_operators
            and run_state.state.interlocks
            and run_state.state.traces
            and run_state.state.basins
        ):
            return
        payload = build_analysis_payload(
            task=(run_state.state.O.description if run_state.state.O else run_state.metadata.title) or summary.compact_summary,
            draft=summary.expert_summary,
            attached_context="\n".join(
                unique_preserve_order(
                    [str(source.metadata.get("first_line", source.title)) for source in run_state.state.sources]
                    + [claim.statement for claim in run_state.state.C[:8]]
                )
            ),
        )
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=[],
            frictions=run_state.state.F,
            durability_blocked=run_state.state.N.blocked,
        )
        self._refresh_methodology_objects(run_state, payload, run_state.state.F)
        self._audit_sources(run_state)

    def _evaluate_and_store_compliance(
        self,
        run_state: PsiRunState,
        summary: SummaryBundle,
        action: str,
        artifacts: list[object] | None = None,
    ) -> ComplianceReport:
        report = evaluate_compliance(
            run_state=run_state,
            artifacts=artifacts or self.repository.list_artifacts(run_state.metadata.run_id),
            action=action,
        )
        run_state.state.compliance = report
        self.repository.save_run(run_state, summary)
        return report

    def _apply_compliance_pressure(
        self,
        transition: TransitionState,
        compliance: ComplianceReport,
    ) -> TransitionState:
        if not compliance.issues:
            return transition
        recommended_regimes = unique_preserve_order(
            [
                *transition.recommended_regimes,
                *(
                    [Regime.WHOLE_FIELD_COHERENCE_SWEEP, Regime.DEPENDENCY_MAPPING]
                    if compliance.requested_action == "run_sweep"
                    else []
                ),
                *(
                    [Regime.SYNTHESIS_CONSTRUCTION, Regime.STRESS_TEST, Regime.REPAIR]
                    if compliance.requested_action == "rollback"
                    else []
                ),
                *(
                    [Regime.SOURCE_GROUNDING, Regime.TASK_CONTRACT_SCOPE_LOCK]
                    if compliance.requested_action == "run_source_audit"
                    else []
                ),
                *(
                    [Regime.TASK_CONTRACT_SCOPE_LOCK]
                    if compliance.requested_action == "rescope"
                    else []
                ),
                *(
                    [
                        Regime.SOURCE_GROUNDING,
                        Regime.PRIMITIVE_STABILIZATION,
                        Regime.DEPENDENCY_MAPPING,
                        Regime.FORWARD_TRACING,
                        Regime.GAP_PRESSURE,
                        Regime.HYPOTHESIS_BASIN,
                        Regime.STRESS_TEST,
                    ]
                    if compliance.requested_action == "rebuild_structure"
                    else []
                ),
            ]
        )
        blocking_reasons = unique_preserve_order(
            [
                *transition.blocking_reasons,
                *([f"compliance::{issue.issue_type}" for issue in compliance.issues if issue.blocking]),
            ]
        )
        rationale = transition.rationale
        if compliance.requested_action == "rollback" and compliance.blocking:
            return TransitionState(
                decision=TransitionDecision.ROLLBACK_REQUIRED,
                rationale=f"{transition.rationale} PSI compliance also requires rollback before stable continuation.",
                blocking_reasons=blocking_reasons,
                recommended_regimes=recommended_regimes,
            )
        if compliance.requested_action == "run_sweep" and compliance.blocking:
            return TransitionState(
                decision=TransitionDecision.CONTINUE,
                rationale=f"{transition.rationale} PSI compliance requires another weighted coherence sweep before closure.",
                blocking_reasons=blocking_reasons,
                recommended_regimes=recommended_regimes,
            )
        if compliance.requested_action == "rescope" and compliance.blocking:
            return TransitionState(
                decision=TransitionDecision.RESCOPE,
                rationale=f"{transition.rationale} PSI compliance requires Phase 0 rescoping before stable continuation.",
                blocking_reasons=blocking_reasons,
                recommended_regimes=recommended_regimes,
            )
        if compliance.requested_action == "sync_artifacts":
            rationale = f"{transition.rationale} Stable emission still requires synchronized artifacts."
        return TransitionState(
            decision=transition.decision,
            rationale=rationale,
            blocking_reasons=blocking_reasons,
            recommended_regimes=recommended_regimes or transition.recommended_regimes,
        )

    def _status_from_transition(self, decision: TransitionDecision) -> RunStatus:
        mapping = {
            TransitionDecision.ANCHOR: RunStatus.PARTIALLY_RESOLVED,
            TransitionDecision.ROLLBACK_REQUIRED: RunStatus.ROLLBACK_REQUIRED,
            TransitionDecision.RESCOPE: RunStatus.SCOPE,
            TransitionDecision.ESCALATE: RunStatus.PARAMETRIC,
            TransitionDecision.CONTINUE: RunStatus.OPEN,
            TransitionDecision.HALT: RunStatus.HALT,
        }
        return mapping[decision]

    def _strongest_live_tension(self, run_state: PsiRunState) -> str:
        if run_state.state.U:
            strongest = sorted(run_state.state.U, key=lambda tension: tension.severity, reverse=True)[0]
            return strongest.title
        if any(signal.friction_type == FrictionType.CONTINUITY_POISON for signal in run_state.state.F):
            return "forward movement vs durability legitimacy"
        if any(signal.friction_type == FrictionType.STRUCTURAL_MISMATCH for signal in run_state.state.F):
            return "local fit vs global coherence"
        return "field remains open but no explicit tension has been registered"

    def _uncertainty_limits(
        self,
        payload: AnalysisPayload,
        run_state: PsiRunState,
        impacts: list[BlastRadiusImpact],
    ) -> list[str]:
        limits: list[str] = []
        if not run_state.metadata.project_id:
            limits.append("No project_id was supplied, so retrieval is limited to run-local and seeded memory.")
        if not run_state.state.A:
            limits.append("No anchors are registered yet; blast radius is estimated from state domains and tensions.")
        if not payload.diff and any(signal.friction_type == FrictionType.SUBSTRATE_FRICTION for signal in run_state.state.F):
            limits.append("No concrete diff was supplied alongside substrate friction.")
        if not impacts:
            limits.append("No persisted entities were available to score for blast radius.")
        return limits

    def _merge_scope(self, current: list[str], proposed: list[str]) -> list[str]:
        merged = [*current]
        for item in proposed:
            if item and item not in merged:
                merged.append(item)
        return merged

    def _parse_transition_decision(self, decision: str | TransitionDecision) -> TransitionDecision:
        if isinstance(decision, TransitionDecision):
            return decision
        normalized = decision.strip().upper()
        if normalized == "ROLLBACK":
            normalized = TransitionDecision.ROLLBACK_REQUIRED.value
        valid = {member.value for member in TransitionDecision}
        if normalized not in valid:
            raise ValueError(
                f"Unknown transition decision {decision!r}. Valid values: {sorted(valid)}"
            )
        return TransitionDecision(normalized)

    def _infer_run_class(self, run_state: PsiRunState) -> RunClass:
        stable = (
            run_state.state.transition.decision in {TransitionDecision.ANCHOR, TransitionDecision.HALT}
            and not run_state.state.open_artifacts
            and bool(run_state.state.sources)
            and bool(run_state.state.components)
            and bool(run_state.state.state_variables)
            and bool(run_state.state.primitive_operators)
            and bool(run_state.state.interlocks)
            and bool(run_state.state.traces)
            and bool(run_state.state.basins)
            and not (run_state.state.compliance and run_state.state.compliance.blocking)
        )
        if stable:
            return RunClass.CANONICAL
        if (
            run_state.state.components
            or run_state.state.interlocks
            or run_state.state.traces
            or run_state.state.gaps
            or run_state.state.basins
        ):
            return RunClass.WORKING
        return RunClass.EXPLORATORY

    def _next_gating_condition(self, run_state: PsiRunState) -> str:
        if run_state.state.compliance and run_state.state.compliance.requested_action:
            return run_state.state.compliance.requested_action
        if not run_state.state.applicability.applicable:
            return "rescope_or_halt_on_method_fit"
        if run_state.state.N.blocked:
            return "clear_durability_poison"
        if run_state.state.open_artifacts:
            return "sync_open_artifacts"
        if any(gap.blocking for gap in run_state.state.gaps):
            return "reduce_smallest_discriminative_unit"
        if run_state.state.uncertainty.propagation_limits:
            return "state_partial_propagation_limits"
        if run_state.state.transition.decision in {TransitionDecision.ANCHOR, TransitionDecision.HALT}:
            return "stable_output_ready"
        if run_state.state.current_discriminator:
            return f"probe::{run_state.state.current_discriminator}"
        return "continue_re-entrant_pass"

    def _select_smallest_discriminative_unit(self, run_state: PsiRunState) -> str:
        for gap in run_state.state.gaps:
            if gap.blocking and gap.smallest_discriminative_unit:
                return gap.smallest_discriminative_unit
        for search in run_state.state.searches:
            if search.smallest_discriminative_unit:
                return search.smallest_discriminative_unit
        return ""

    def _update_phase_history(self, run_state: PsiRunState, reason: str = "", trigger: str = "") -> None:
        current_phase = run_state.state.active_regimes[0] if run_state.state.active_regimes else Regime.TASK_CONTRACT_SCOPE_LOCK
        previous = run_state.state.phase_history[-1].regime if run_state.state.phase_history else None
        run_state.state.current_phase = current_phase
        if previous != current_phase:
            run_state.state.phase_history.append(
                PhaseRecord(
                    regime=current_phase,
                    reason=reason,
                    trigger=trigger,
                )
            )

    def _refresh_control_state(
        self,
        run_state: PsiRunState,
        artifacts: list[object] | None = None,
        phase_reason: str = "",
        trigger: str = "",
    ) -> None:
        artifact_snapshots = artifacts if artifacts is not None else self.repository.list_artifacts(run_state.metadata.run_id)
        available = {artifact.artifact_type for artifact in artifact_snapshots}
        open_artifacts = [artifact for artifact in ArtifactType if artifact not in available]
        open_artifacts.extend(
            artifact.artifact_type
            for artifact in artifact_snapshots
            if not artifact.authoritative and artifact.artifact_type not in open_artifacts
        )
        run_state.state.open_artifacts = open_artifacts
        supersessions = self.repository.list_supersession_history(run_state.metadata.run_id)
        if supersessions:
            run_state.state.last_supersession = SupersessionSnapshot.model_validate(supersessions[0])
        else:
            run_state.state.last_supersession = None
        run_state.state.smallest_discriminative_unit = self._select_smallest_discriminative_unit(run_state)
        run_state.state.uncertainty.partial_propagation_warnings = [
            f"partial::{limit}" for limit in run_state.state.uncertainty.propagation_limits
        ]
        self._update_phase_history(run_state, reason=phase_reason, trigger=trigger)
        run_state.state.next_gating_condition = self._next_gating_condition(run_state)
        run_state.metadata.run_class = self._infer_run_class(run_state)

    def start_run(
        self,
        title: str,
        scope: str,
        mode: str | RunMode = RunMode.SURVEY,
        project_id: str | None = None,
        project_name: str | None = None,
        run_id: str | None = None,
        attached_context: str = "",
        durability_mode: str | None = None,
    ) -> dict[str, object]:
        if run_id:
            try:
                run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            except KeyError:
                pass
            else:
                self._refresh_control_state(run_state)
                return {
                    "project_id": run_state.metadata.project_id,
                    "run_id": run_state.metadata.run_id,
                    "mode": run_state.metadata.mode.value,
                    "status": run_state.metadata.status.value,
                    "resumed": True,
                    "state": run_state.machine_readable(),
                }
        project = self._ensure_project(project_id, project_name, scope)
        run_mode = RunMode(mode) if isinstance(mode, str) else mode
        payload = build_analysis_payload(scope, attached_context=attached_context)
        run_state = PsiRunState(
            metadata=RunMetadata(
                run_id=run_id or self._new_id("run"),
                project_id=project.project_id if project else None,
                title=title,
                mode=run_mode,
                run_class=RunClass.EXPLORATORY,
                status=RunStatus.OPEN,
                durability_mode=self._effective_durability_mode(durability_mode),
            ),
            state=RunStateVector(
                L=infer_lens(payload),
                B=infer_scope(payload),
                T=infer_timescale_bands(payload),
                S=infer_substrate_constraints(payload),
                applicability=assess_applicability(payload),
            ),
        )
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=[],
            frictions=[],
            durability_blocked=False,
        )
        self._refresh_methodology_objects(run_state, payload, [])
        source_audit = self._audit_sources(run_state)
        run_state.state.W.notes = self._merge_scope(run_state.state.W.notes, [f"source_audit={source_audit}"])
        self._refresh_control_state(
            run_state,
            artifacts=[],
            phase_reason="run started",
            trigger="start_run",
        )
        summary = SummaryBundle(
            expert_summary=f"Run opened for {title}",
            plain_summary=f"Started PSI run for {title}.",
            compact_summary=title,
        )
        self.repository.save_run(run_state, summary)
        self._evaluate_and_store_compliance(run_state, summary, action="start")
        return {
            "project_id": run_state.metadata.project_id,
            "run_id": run_state.metadata.run_id,
            "mode": run_state.metadata.mode.value,
            "status": run_state.metadata.status.value,
            "resumed": False,
            "state": run_state.machine_readable(),
        }

    def _ensure_run_for_operation(
        self,
        task: str,
        project_id: str | None = None,
        project_name: str | None = None,
        run_id: str | None = None,
        mode: str | None = None,
        durability_mode: str | None = None,
    ) -> PsiRunState:
        if run_id:
            try:
                return self._hydrate_run_state(self.repository.get_run_state(run_id))
            except KeyError:
                pass  # caller-supplied run_id not found; fall through and create a new run
        started = self.start_run(
            title=task[:80] or "PSI pass",
            scope=task,
            mode=mode or classify_active_mode(build_analysis_payload(task)),
            project_id=project_id,
            project_name=project_name,
            durability_mode=durability_mode,
            run_id=run_id,
        )
        return self._hydrate_run_state(self.repository.get_run_state(started["run_id"]))

    def get_run_state(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._refresh_control_state(run_state)
        compact = {
            "run_id": run_state.metadata.run_id,
            "project_id": run_state.metadata.project_id,
            "mode": run_state.metadata.mode.value,
            "run_class": run_state.metadata.run_class.value,
            "status": run_state.metadata.status.value,
            "transition": run_state.state.transition.decision.value,
            "current_phase": run_state.state.current_phase.value,
            "active_regimes": [regime.value for regime in run_state.state.active_regimes],
            "open_artifacts": [artifact.value for artifact in run_state.state.open_artifacts],
            "next_gating_condition": run_state.state.next_gating_condition,
            "best_discriminator": run_state.state.current_discriminator,
            "smallest_discriminative_unit": run_state.state.smallest_discriminative_unit,
            "compliance_status": run_state.state.compliance.status if run_state.state.compliance else "UNKNOWN",
            "summary": summary.compact_summary,
        }
        return {
            "compact": compact,
            "full": run_state.machine_readable(),
        }

    def reflect(
        self,
        task: str,
        draft_answer: str = "",
        diff: str = "",
        project_id: str | None = None,
        project_name: str | None = None,
        run_id: str | None = None,
        attached_context: str = "",
        durability_mode: str | None = None,
    ) -> dict[str, object]:
        run_state = self._ensure_run_for_operation(
            task=task,
            project_id=project_id,
            project_name=project_name,
            run_id=run_id,
            durability_mode=durability_mode,
        )
        payload = build_analysis_payload(
            task=task,
            draft=draft_answer,
            diff=diff,
            attached_context=attached_context,
        )
        events = detect_visibility_events(payload)
        frictions = type_friction(payload)
        durability = assess_durability(payload, run_state.metadata.durability_mode)
        lens = infer_lens(payload)
        scope = infer_scope(payload)
        applicability = assess_applicability(payload)
        articulation = summarize_local_articulation(payload)
        probes = suggest_probes(frictions, payload, articulation)
        best_discriminator = choose_best_discriminator(frictions, probes)
        whole_field_impact_summary = summarize_whole_field_impact(payload, frictions, articulation)
        constraints = self.repository.list_constraints(run_state.metadata.project_id) if run_state.metadata.project_id else []
        primary_event = max(events, key=lambda event: event.severity)
        run_state.state.O = primary_event
        run_state.state.F = frictions
        run_state.state.N = durability
        run_state.state.L = lens
        run_state.state.applicability = applicability
        run_state.state.B.included = self._merge_scope(run_state.state.B.included, scope.included)
        run_state.state.B.excluded = self._merge_scope(run_state.state.B.excluded, scope.excluded)
        run_state.state.B.success_criteria = self._merge_scope(run_state.state.B.success_criteria, scope.success_criteria)
        run_state.state.B.assumptions = self._merge_scope(run_state.state.B.assumptions, scope.assumptions)
        run_state.state.P = probes
        run_state.state.current_discriminator = best_discriminator
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=[],
            frictions=frictions,
            durability_blocked=durability.blocked,
        )
        self._refresh_methodology_objects(run_state, payload, frictions)
        source_audit = self._audit_sources(run_state)
        run_state.state.T = infer_timescale_bands(payload)
        run_state.state.S = infer_substrate_constraints(payload)
        impacts, deferred = estimate_blast_radius(
            payload=payload,
            frictions=frictions,
            anchors=run_state.state.A,
            tensions=run_state.state.U,
            hypotheses=run_state.state.H,
            constraints=constraints,
            stance_hints=run_state.state.G.centrality.high + run_state.state.G.fragility.high + run_state.state.G.suspicion,
            components=run_state.state.components,
            state_variables=run_state.state.state_variables,
            primitive_operators=run_state.state.primitive_operators,
            interlocks=run_state.state.interlocks,
            traces=run_state.state.traces,
            gaps=run_state.state.gaps,
            supersessions=self.repository.list_supersession_history(run_state.metadata.run_id),
        )
        uncertainty_limits = self._uncertainty_limits(payload, run_state, impacts)
        scope_shift_detected = any(event.type == VisibilityEventType.REFRAME for event in events)
        transition = recommend_transition(
            frictions=frictions,
            impacts=impacts,
            durability_blocked=durability.blocked,
            scope_shift_detected=scope_shift_detected,
            uncertainty_limits=uncertainty_limits,
        )
        if not applicability.applicable:
            transition = TransitionState(
                decision=TransitionDecision.RESCOPE,
                rationale="Phase 0 applicability check says PSI is not a clean fit for the current target without rescoping.",
                blocking_reasons=applicability.failure_modes[:4],
                recommended_regimes=[Regime.TASK_CONTRACT_SCOPE_LOCK],
            )
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=impacts,
            frictions=frictions,
            durability_blocked=durability.blocked,
        )
        run_state.state.current_blast_radius = impacts
        run_state.state.current_sweep_status.status = "completed"
        run_state.state.current_sweep_status.impacted_entities = [impact.entity_name for impact in impacts]
        run_state.state.current_sweep_status.deferred_entities = deferred
        run_state.state.current_sweep_status.last_run_at = utc_now()
        run_state.state.uncertainty.propagation_limits = uncertainty_limits
        run_state.state.W.dependencies_changed = whole_field_impact_summary
        run_state.state.W.salience_updates = [impact.entity_name for impact in impacts[:4]]
        run_state.state.W.abstraction_updates = [f"lens={lens.object_in_play}@{lens.admissible_level}"]
        run_state.state.W.stance_updates = [regime.value for regime in run_state.state.active_regimes]
        run_state.state.W.anchor_updates = [impact.entity_name for impact in impacts if impact.entity_type == "anchor"]
        run_state.state.W.tension_updates = [impact.entity_name for impact in impacts if impact.entity_type == "tension"]
        run_state.state.W.possibility_updates = [impact.entity_name for impact in impacts if impact.entity_type == "hypothesis"]
        run_state.state.W.notes = self._merge_scope(run_state.state.W.notes, [f"source_audit={source_audit}"])
        run_state.state.G.centrality.high = [impact.entity_name for impact in impacts[:3]]
        run_state.state.G.centrality.medium = [impact.entity_name for impact in impacts[3:6]]
        run_state.state.G.fragility.high = [impact.entity_name for impact in impacts if impact.fragility >= 0.7][:4]
        run_state.state.G.fragility.medium = [impact.entity_name for impact in impacts if 0.45 <= impact.fragility < 0.7][:4]
        run_state.state.G.suspicion = [signal.friction_type.value for signal in frictions]
        run_state.state.G.salience.promoted = [impact.entity_name for impact in impacts[:4]]
        run_state.state.G.salience.demoted = deferred[:4]
        run_state.state.transition = transition
        existing_artifacts = self.repository.list_artifacts(run_state.metadata.run_id)
        compliance = evaluate_compliance(run_state, artifacts=existing_artifacts, action="reflect")
        transition = self._apply_compliance_pressure(transition, compliance)
        run_state.state.transition = transition
        run_state.state.compliance = compliance
        run_state.metadata.status = self._status_from_transition(transition.decision)
        run_state.metadata.timestamp = utc_now()
        persisted_events = [
            self.repository.record_visibility_event(run_state.metadata.project_id, run_state.metadata.run_id, event)
            for event in events
        ]
        stored_primary_event = next(
            (
                event
                for event in persisted_events
                if event.type == primary_event.type and event.title == primary_event.title
            ),
            persisted_events[0] if persisted_events else None,
        )
        for signal in frictions:
            self.repository.record_friction(run_state.metadata.project_id, run_state.metadata.run_id, signal)
        recorded_sweep = self.repository.record_sweep(
            project_id=run_state.metadata.project_id,
            run_id=run_state.metadata.run_id,
            trigger_event_id=stored_primary_event.id if stored_primary_event else None,
            summary=" | ".join(whole_field_impact_summary[:3]),
            impacted_entities=[impact.entity_name for impact in impacts],
            blast_radius=impacts,
            deferred_entities=deferred,
            transition=transition.model_dump(mode="json"),
            metadata={"best_discriminator": best_discriminator},
        )
        run_state.state.current_sweep_status.trigger_event_id = stored_primary_event.id if stored_primary_event else None
        self._refresh_control_state(
            run_state,
            artifacts=existing_artifacts,
            phase_reason="reflect pass completed",
            trigger=primary_event.type.value,
        )
        strongest_tension = self._strongest_live_tension(run_state)
        summary = generate_summary_bundle(
            run_state=run_state,
            local_articulation_summary=articulation,
            whole_field_impact_summary=whole_field_impact_summary,
            strongest_tension=strongest_tension,
            best_discriminator=best_discriminator,
        )
        self.repository.save_run(run_state, summary)
        return {
            "project_id": run_state.metadata.project_id,
            "run_id": run_state.metadata.run_id,
            "run_class": run_state.metadata.run_class.value,
            "detected_visibility_events": [event.model_dump(mode="json") for event in persisted_events],
            "active_lens_summary": run_state.state.L.model_dump(mode="json"),
            "friction_types": [signal.friction_type.value for signal in frictions],
            "applicability": run_state.state.applicability.model_dump(mode="json"),
            "source_objects": [source.model_dump(mode="json") for source in run_state.state.sources],
            "source_audit": source_audit,
            "typed_claims": [claim.model_dump(mode="json") for claim in run_state.state.C],
            "components": [component.model_dump(mode="json") for component in run_state.state.components],
            "state_variables": [state_variable.model_dump(mode="json") for state_variable in run_state.state.state_variables],
            "primitive_operators": [operator.model_dump(mode="json") for operator in run_state.state.primitive_operators],
            "interlocks": [relation.model_dump(mode="json") for relation in run_state.state.interlocks],
            "traces": [trace.model_dump(mode="json") for trace in run_state.state.traces],
            "gaps": [gap.model_dump(mode="json") for gap in run_state.state.gaps],
            "search_records": [search.model_dump(mode="json") for search in run_state.state.searches],
            "basins": [basin.model_dump(mode="json") for basin in run_state.state.basins],
            "skeptic_findings": [finding.model_dump(mode="json") for finding in run_state.state.skeptic_findings],
            "antipattern_findings": [finding.model_dump(mode="json") for finding in run_state.state.antipattern_findings],
            "operator_families": [operator.value for operator in run_state.state.active_operators],
            "control_families": [family.model_dump(mode="json") for family in run_state.state.control_families],
            "friction_routing": [routing.model_dump(mode="json") for routing in run_state.state.friction_routing],
            "local_articulation_summary": articulation,
            "whole_field_impact_summary": whole_field_impact_summary,
            "affected_anchors": [
                impact.model_dump(mode="json") for impact in impacts if impact.entity_type == "anchor"
            ],
            "strongest_live_tension": strongest_tension,
            "best_discriminator": best_discriminator,
            "durability_assessment": durability.model_dump(mode="json"),
            "transition_recommendation": transition.model_dump(mode="json"),
            "compliance_report": compliance.model_dump(mode="json"),
            "current_phase": run_state.state.current_phase.value,
            "open_artifacts": [artifact.value for artifact in run_state.state.open_artifacts],
            "next_gating_condition": run_state.state.next_gating_condition,
            "last_supersession": run_state.state.last_supersession.model_dump(mode="json")
            if run_state.state.last_supersession
            else None,
            "uncertainty": run_state.state.uncertainty.model_dump(mode="json"),
            "smallest_discriminative_unit": run_state.state.smallest_discriminative_unit,
            "propagation_trace": summarize_impacts(impacts),
            "summary": summary.model_dump(mode="json"),
            "sweep_id": recorded_sweep["id"],
        }

    def record_event(
        self,
        run_id: str,
        event_type: str,
        title: str,
        description: str,
        source: str = "",
        severity: float = 0.5,
        evidence: list[str] | None = None,
    ) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        event = VisibilityEvent(
            type=VisibilityEventType(event_type),
            title=title,
            description=description,
            source=source,
            severity=severity,
            evidence=evidence or [],
        )
        stored = self.repository.record_visibility_event(run_state.metadata.project_id, run_id, event)
        run_state.state.O = stored
        self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
        return stored.model_dump(mode="json")

    def friction_type(
        self,
        text: str,
        run_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, object]:
        payload = build_analysis_payload(text)
        frictions = type_friction(payload)
        if run_id:
            run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            run_state.state.F = frictions
            self._apply_runtime_control_surface(
                run_state=run_state,
                payload=payload,
                impacts=run_state.state.current_blast_radius,
                frictions=frictions,
                durability_blocked=run_state.state.N.blocked,
            )
            self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
            for signal in frictions:
                self.repository.record_friction(project_id or run_state.metadata.project_id, run_id, signal)
        return {
            "friction_types": [signal.model_dump(mode="json") for signal in frictions],
            "routed_regimes": [
                regime.value for regime in route_regimes(frictions, mode=run_state.metadata.mode if run_id else RunMode.SURVEY)
            ],
            "routing": [
                decision.model_dump(mode="json")
                for decision in build_friction_routing(
                    frictions=frictions,
                    mode=run_state.metadata.mode if run_id else RunMode.SURVEY,
                    impacts=run_state.state.current_blast_radius if run_id else [],
                    durability_blocked=run_state.state.N.blocked if run_id else False,
                )
            ],
        }

    def run_sweep(
        self,
        run_id: str,
        changed_text: str = "",
        trigger_event_id: str | None = None,
    ) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        if trigger_event_id:
            event = next(
                (event for event in self.repository.list_visibility_events(run_id) if event.id == trigger_event_id),
                None,
            )
            if event:
                changed_text = f"{changed_text}\n{event.description}".strip()
                run_state.state.O = event
        payload = build_analysis_payload(changed_text or (run_state.state.O.description if run_state.state.O else run_state.metadata.title))
        run_state.state.applicability = assess_applicability(payload)
        constraints = self.repository.list_constraints(run_state.metadata.project_id) if run_state.metadata.project_id else []
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=[],
            frictions=run_state.state.F,
            durability_blocked=run_state.state.N.blocked,
        )
        self._refresh_methodology_objects(run_state, payload, run_state.state.F)
        source_audit = self._audit_sources(run_state)
        impacts, deferred = estimate_blast_radius(
            payload=payload,
            frictions=run_state.state.F,
            anchors=run_state.state.A,
            tensions=run_state.state.U,
            hypotheses=run_state.state.H,
            constraints=constraints,
            stance_hints=run_state.state.G.centrality.high + run_state.state.G.fragility.high + run_state.state.G.suspicion,
            components=run_state.state.components,
            state_variables=run_state.state.state_variables,
            primitive_operators=run_state.state.primitive_operators,
            interlocks=run_state.state.interlocks,
            traces=run_state.state.traces,
            gaps=run_state.state.gaps,
            supersessions=self.repository.list_supersession_history(run_id),
        )
        transition = recommend_transition(
            frictions=run_state.state.F,
            impacts=impacts,
            durability_blocked=run_state.state.N.blocked,
            scope_shift_detected=bool(run_state.state.O and run_state.state.O.type == VisibilityEventType.REFRAME),
            uncertainty_limits=run_state.state.uncertainty.propagation_limits,
        )
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=impacts,
            frictions=run_state.state.F,
            durability_blocked=run_state.state.N.blocked,
        )
        run_state.state.current_blast_radius = impacts
        run_state.state.current_sweep_status.status = "completed"
        run_state.state.current_sweep_status.trigger_event_id = trigger_event_id
        run_state.state.current_sweep_status.impacted_entities = [impact.entity_name for impact in impacts]
        run_state.state.current_sweep_status.deferred_entities = deferred
        run_state.state.current_sweep_status.last_run_at = utc_now()
        run_state.state.W.notes = self._merge_scope(run_state.state.W.notes, [f"source_audit={source_audit}"])
        run_state.state.transition = transition
        compliance = evaluate_compliance(
            run_state,
            artifacts=self.repository.list_artifacts(run_id),
            action="reflect",
        )
        run_state.state.transition = self._apply_compliance_pressure(transition, compliance)
        run_state.state.compliance = compliance
        run_state.metadata.status = self._status_from_transition(run_state.state.transition.decision)
        self._refresh_control_state(
            run_state,
            artifacts=self.repository.list_artifacts(run_id),
            phase_reason="coherence sweep completed",
            trigger=trigger_event_id or "sweep_run",
        )
        local_articulation_summary = summarize_local_articulation(payload)
        strongest_tension = self._strongest_live_tension(run_state)
        best_discriminator = run_state.state.current_discriminator or "re-run discriminator search"
        summary = generate_summary_bundle(
            run_state=run_state,
            local_articulation_summary=local_articulation_summary,
            whole_field_impact_summary=summarize_impacts(impacts),
            strongest_tension=strongest_tension,
            best_discriminator=best_discriminator,
        )
        self.repository.save_run(run_state, summary)
        sweep = self.repository.record_sweep(
            project_id=run_state.metadata.project_id,
            run_id=run_id,
            trigger_event_id=trigger_event_id,
            summary="weighted coherence sweep",
            impacted_entities=[impact.entity_name for impact in impacts],
            blast_radius=impacts,
            deferred_entities=deferred,
            transition=transition.model_dump(mode="json"),
        )
        return {
            "run_id": run_id,
            "sweep": sweep,
            "impacts": [impact.model_dump(mode="json") for impact in impacts],
            "deferred_entities": deferred,
            "transition": run_state.state.transition.model_dump(mode="json"),
            "compliance_report": compliance.model_dump(mode="json"),
            "current_phase": run_state.state.current_phase.value,
            "next_gating_condition": run_state.state.next_gating_condition,
            "smallest_discriminative_unit": run_state.state.smallest_discriminative_unit,
        }

    def register_anchor(
        self,
        name: str,
        description: str,
        project_id: str,
        run_id: str | None = None,
        centrality: float = 0.5,
        fragility: float = 0.5,
        confidence: str = "provisional",
        durability_class: str = "PROVISIONAL",
        rationale: str = "",
        dependencies: list[str] | None = None,
        implications: list[str] | None = None,
        weakening_conditions: list[str] | None = None,
        explanatory_burden: list[str] | None = None,
        scaffold_boundary: dict[str, object] | None = None,
        user_promoted: bool = False,
    ) -> dict[str, object]:
        anchor = Anchor(
            name=name,
            description=description,
            centrality=centrality,
            fragility=fragility,
            confidence=ConfidenceLevel(confidence),
            durability_class=DurabilityClass(durability_class),
            rationale=rationale,
            dependencies=dependencies or [],
            implications=implications or [],
            weakening_conditions=weakening_conditions or [],
            explanatory_burden=explanatory_burden or [],
            scaffold_boundary=ScaffoldBoundary.model_validate(scaffold_boundary) if scaffold_boundary else None,
            user_promoted=user_promoted,
        )
        stored = self.repository.upsert_anchor(project_id, run_id, anchor)
        if run_id:
            run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            run_state.state.A = self.repository.list_anchors(project_id)
            self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
        return stored.model_dump(mode="json")

    def invalidate_anchor(
        self,
        anchor_id: str,
        reason: str,
        run_id: str | None = None,
        project_id: str | None = None,
        invalidated_by: str | None = None,
    ) -> dict[str, object]:
        stored = self.repository.invalidate_anchor(anchor_id, invalidated_by, reason, project_id, run_id)
        if run_id and project_id:
            run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            run_state.state.A = self.repository.list_anchors(project_id)
            self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
        return stored.model_dump(mode="json")

    def update_hypothesis(
        self,
        item_type: str,
        action: str,
        title: str,
        description: str,
        project_id: str,
        run_id: str | None = None,
        confidence: str = "provisional",
        durability_class: str = "PROVISIONAL",
        severity: float = 0.5,
        preserves: list[str] | None = None,
        risks: list[str] | None = None,
        discriminators: list[str] | None = None,
        forces: list[str] | None = None,
        weakening_conditions: list[str] | None = None,
        explanatory_burden: list[str] | None = None,
        discriminator_path: list[str] | None = None,
    ) -> dict[str, object]:
        if item_type == "hypothesis":
            status = {"retire": "SUPERSEDED", "modify": "OPEN", "add": "OPEN"}.get(action, "OPEN")
            stored = self.repository.upsert_hypothesis(
                project_id,
                run_id,
                PsiHypothesis(
                    title=title,
                    description=description,
                    status=status,
                    confidence=ConfidenceLevel(confidence),
                    durability_class=DurabilityClass(durability_class),
                    preserves=preserves or [],
                    risks=risks or [],
                    discriminators=discriminators or [],
                    weakening_conditions=weakening_conditions or [],
                    explanatory_burden=explanatory_burden or [],
                    discriminator_path=discriminator_path or [],
                ),
            )
        elif item_type == "tension":
            status = {"retire": "RESOLVED", "modify": "OPEN", "add": "OPEN"}.get(action, "OPEN")
            stored = self.repository.upsert_tension(
                project_id,
                run_id,
                Tension(
                    title=title,
                    description=description,
                    status=status,
                    severity=severity,
                    forces=forces or [],
                ),
            )
        else:
            raise ValueError("item_type must be 'hypothesis' or 'tension'")
        if run_id:
            run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
        return stored.model_dump(mode="json")

    def record_discriminator(
        self,
        title: str,
        description: str,
        project_id: str,
        run_id: str | None = None,
        target: list[str] | None = None,
        best_next_probe: str = "",
        confidence_gain: float = 0.5,
        expected_outcome_map: dict[str, str] | None = None,
    ) -> dict[str, object]:
        stored = self.repository.upsert_discriminator(
            project_id,
            run_id,
            Discriminator(
                title=title,
                description=description,
                target=target or [],
                best_next_probe=best_next_probe,
                confidence_gain=confidence_gain,
                expected_outcome_map=expected_outcome_map or {},
            ),
        )
        if run_id:
            run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
            run_state.state.current_discriminator = stored.best_next_probe or stored.title
            self._evaluate_and_store_compliance(run_state, self.repository.get_run_summary(run_id), action="reflect")
        return stored.model_dump(mode="json")

    def set_transition(
        self,
        run_id: str,
        decision: str | None = None,
        rationale: str = "",
    ) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        if decision is None:
            transition = recommend_transition(
                frictions=run_state.state.F,
                impacts=run_state.state.current_blast_radius,
                durability_blocked=run_state.state.N.blocked,
                scope_shift_detected=bool(run_state.state.O and run_state.state.O.type == VisibilityEventType.REFRAME),
                uncertainty_limits=run_state.state.uncertainty.propagation_limits,
            )
        else:
            transition = TransitionState(
                decision=self._parse_transition_decision(decision),
                rationale=rationale or "Transition set explicitly.",
                recommended_regimes=run_state.state.active_regimes,
            )
        run_state.state.transition = transition
        run_state.metadata.status = self._status_from_transition(transition.decision)
        self._refresh_control_state(run_state, phase_reason="transition set", trigger="set_transition")
        summary = self.repository.get_run_summary(run_id)
        self._evaluate_and_store_compliance(run_state, summary, action="reflect")
        return transition.model_dump(mode="json")

    def retrieve_memory(
        self,
        query: str,
        lanes: list[str] | None = None,
        limit: int = 8,
    ) -> dict[str, object]:
        selected_lanes = [MemoryLane(lane) for lane in (lanes or [lane.value for lane in MemoryLane])]
        hits = self.repository.retrieve(query, selected_lanes, limit=limit)
        return {
            "query": query,
            "hits": [hit.model_dump(mode="json") for hit in hits],
        }

    def commit_memory(
        self,
        lane: str,
        key: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, object] | None = None,
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, object]:
        stored = self.repository.upsert_memory(
            MemoryEntry(
                lane=MemoryLane(lane),
                key=key,
                title=title,
                content=content,
                tags=tags or [],
                metadata=metadata or {},
                project_id=project_id,
                run_id=run_id,
            )
        )
        return stored.model_dump(mode="json")

    def check_compliance(self, run_id: str, action: str = "summary") -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._refresh_control_state(run_state, phase_reason="compliance check", trigger=action)
        report = self._evaluate_and_store_compliance(
            run_state=run_state,
            summary=summary,
            action=action,
        )
        return report.model_dump(mode="json")

    def source_audit(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        audit_summary = self._audit_sources(run_state)
        self._refresh_control_state(run_state, phase_reason="source audit", trigger="source_audit")
        self.repository.save_run(run_state, summary)
        return {
            "run_id": run_id,
            "audit": audit_summary,
            "source_objects": [source.model_dump(mode="json") for source in run_state.state.sources],
        }

    def structure_extract(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        self._refresh_control_state(run_state, phase_reason="structure extract", trigger="structure_extract")
        self.repository.save_run(run_state, summary)
        return {
            "run_id": run_id,
            "components": [component.model_dump(mode="json") for component in run_state.state.components],
            "state_variables": [state_variable.model_dump(mode="json") for state_variable in run_state.state.state_variables],
            "primitive_operators": [operator.model_dump(mode="json") for operator in run_state.state.primitive_operators],
            "interlocks": [relation.model_dump(mode="json") for relation in run_state.state.interlocks],
        }

    def trace_run(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        self._refresh_control_state(run_state, phase_reason="trace run", trigger="trace_run")
        self.repository.save_run(run_state, summary)
        blocking = [trace for trace in run_state.state.traces if trace.blocking or trace.divergence_class]
        return {
            "run_id": run_id,
            "cascade_ids": unique_preserve_order(trace.cascade_id for trace in run_state.state.traces if trace.cascade_id),
            "blocking_traces": [trace.model_dump(mode="json") for trace in blocking],
            "traces": [trace.model_dump(mode="json") for trace in run_state.state.traces],
        }

    def gap_analyze(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        self._refresh_control_state(run_state, phase_reason="gap analyze", trigger="gap_analyze")
        self.repository.save_run(run_state, summary)
        blocking = [gap for gap in run_state.state.gaps if gap.blocking or gap.status == "OPEN"]
        return {
            "run_id": run_id,
            "blocking_gaps": [gap.model_dump(mode="json") for gap in blocking],
            "gaps": [gap.model_dump(mode="json") for gap in run_state.state.gaps],
            "search_records": [search.model_dump(mode="json") for search in run_state.state.searches],
        }

    def search_plan(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        self._refresh_control_state(run_state, phase_reason="search plan", trigger="search_plan")
        self.repository.save_run(run_state, summary)
        return {
            "run_id": run_id,
            "planned_queries": [search.query for search in run_state.state.searches],
            "search_records": [search.model_dump(mode="json") for search in run_state.state.searches],
        }

    def basin_generate(self, run_id: str) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        self._refresh_control_state(run_state, phase_reason="basin generate", trigger="basin_generate")
        self.repository.save_run(run_state, summary)
        return {
            "run_id": run_id,
            "basins": [basin.model_dump(mode="json") for basin in run_state.state.basins],
        }

    def stress_run(self, run_id: str, action: str = "summary") -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        summary = self.repository.get_run_summary(run_id)
        self._ensure_authoritative_structures(run_state, summary)
        skeptic_findings, antipattern_findings = generate_stress_findings(run_state)
        run_state.state.skeptic_findings = skeptic_findings
        run_state.state.antipattern_findings = antipattern_findings
        self._refresh_control_state(run_state, phase_reason="stress run", trigger="stress_run")
        report = self._evaluate_and_store_compliance(run_state=run_state, summary=summary, action=action)
        return {
            "run_id": run_id,
            "skeptic_findings": [finding.model_dump(mode="json") for finding in skeptic_findings],
            "antipattern_findings": [finding.model_dump(mode="json") for finding in antipattern_findings],
            "compliance_report": report.model_dump(mode="json"),
        }

    def sync_artifacts(self, run_id: str) -> dict[str, object]:
        context = self.repository.collect_run_context(run_id)
        run_state: PsiRunState = self._hydrate_run_state(context["run_state"])
        self._ensure_authoritative_structures(run_state, context["summary"])
        self._audit_sources(run_state)
        context["run_state"] = run_state
        context["source_objects"] = run_state.state.sources
        context["components"] = run_state.state.components
        context["state_variables"] = run_state.state.state_variables
        context["primitive_operators"] = run_state.state.primitive_operators
        context["interlocks"] = run_state.state.interlocks
        context["traces"] = run_state.state.traces
        context["gaps"] = run_state.state.gaps
        context["searches"] = run_state.state.searches
        context["basins"] = run_state.state.basins
        context["skeptic_findings"] = run_state.state.skeptic_findings
        context["antipattern_findings"] = run_state.state.antipattern_findings
        run_state.state.compliance = evaluate_compliance(
            run_state=run_state,
            artifacts=context["artifacts"],
            action="artifact_promotion",
        )
        artifacts, pointers = generate_artifacts(context)
        for artifact in artifacts:
            self.repository.save_artifact(run_id, artifact)
        final_artifacts = self.repository.list_artifacts(run_id)
        context["artifacts"] = final_artifacts
        run_state.artifacts = pointers
        self._audit_sources(run_state)
        run_state.state.compliance = evaluate_compliance(
            run_state=run_state,
            artifacts=final_artifacts,
            action="artifact_promotion",
        )
        self._refresh_control_state(
            run_state,
            artifacts=final_artifacts,
            phase_reason="artifact sync",
            trigger="sync_artifacts",
        )
        context["run_state"] = run_state
        final_artifacts, pointers = generate_artifacts(context)
        for artifact in final_artifacts:
            self.repository.save_artifact(run_id, artifact)
        final_artifacts = self.repository.list_artifacts(run_id)
        run_state.artifacts = pointers
        self._audit_sources(run_state)
        run_state.state.compliance = evaluate_compliance(
            run_state=run_state,
            artifacts=final_artifacts,
            action="artifact_promotion",
        )
        self._refresh_control_state(
            run_state,
            artifacts=final_artifacts,
            phase_reason="artifact sync",
            trigger="sync_artifacts",
        )
        summary = context["summary"]
        self.repository.save_run(run_state, summary)
        return {
            "run_id": run_id,
            "artifacts": [
                {
                    "artifact_type": artifact.artifact_type.value,
                    "checksum": artifact.checksum,
                    "pointer": getattr(pointers, artifact.artifact_type.value),
                }
                for artifact in final_artifacts
            ],
            "compliance_report": run_state.state.compliance.model_dump(mode="json") if run_state.state.compliance else None,
        }

    def export_run(self, run_id: str, export_format: str = "both") -> dict[str, object]:
        self.sync_artifacts(run_id)
        compliance = self.check_compliance(run_id, action="export")
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        if run_state.metadata.durability_mode == DurabilityMode.BLOCKING and compliance["blocking"]:
            raise ValueError(
                "PSI compliance blocked export because stable emission requirements are not satisfied."
            )
        context = self.repository.collect_run_context(run_id)
        run_state = self._hydrate_run_state(context["run_state"])
        self._ensure_authoritative_structures(run_state, context["summary"])
        self._audit_sources(run_state)
        self._refresh_control_state(run_state, artifacts=context["artifacts"], phase_reason="export", trigger="export_run")
        context["run_state"] = run_state
        context["source_objects"] = run_state.state.sources
        context["components"] = run_state.state.components
        context["state_variables"] = run_state.state.state_variables
        context["primitive_operators"] = run_state.state.primitive_operators
        context["interlocks"] = run_state.state.interlocks
        context["traces"] = run_state.state.traces
        context["gaps"] = run_state.state.gaps
        context["searches"] = run_state.state.searches
        context["basins"] = run_state.state.basins
        context["skeptic_findings"] = run_state.state.skeptic_findings
        context["antipattern_findings"] = run_state.state.antipattern_findings
        timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        export_root = ensure_directory(self.settings.export_dir / f"{run_id}-{timestamp}")
        artifacts_dir = ensure_directory(export_root / "artifacts")
        bundle = {
            "run_state": run_state.model_dump(mode="json"),
            "machine_readable_run_state": run_state.machine_readable(),
            "summary": context["summary"].model_dump(mode="json"),
            "project_summary": self.repository.get_project_summary(run_state.metadata.project_id).model_dump(mode="json")
            if run_state.metadata.project_id
            else None,
            "events": [event.model_dump(mode="json") for event in context["events"]],
            "friction_logs": [signal.model_dump(mode="json") for signal in context["friction_logs"]],
            "sweeps": context["sweeps"],
            "anchors": [anchor.model_dump(mode="json") for anchor in context["anchors"]],
            "tensions": [tension.model_dump(mode="json") for tension in context["tensions"]],
            "hypotheses": [hypothesis.model_dump(mode="json") for hypothesis in context["hypotheses"]],
            "discriminators": [discriminator.model_dump(mode="json") for discriminator in context["discriminators"]],
            "constraints": [constraint.model_dump(mode="json") for constraint in context["constraints"]],
            "source_objects": [source.model_dump(mode="json") for source in context["source_objects"]],
            "components": [component.model_dump(mode="json") for component in context["components"]],
            "state_variables": [state_variable.model_dump(mode="json") for state_variable in context["state_variables"]],
            "primitive_operators": [operator.model_dump(mode="json") for operator in context["primitive_operators"]],
            "interlocks": [relation.model_dump(mode="json") for relation in context["interlocks"]],
            "traces": [trace.model_dump(mode="json") for trace in context["traces"]],
            "gaps": [gap.model_dump(mode="json") for gap in context["gaps"]],
            "search_records": [search.model_dump(mode="json") for search in context["searches"]],
            "basins": [basin.model_dump(mode="json") for basin in context["basins"]],
            "skeptic_findings": [finding.model_dump(mode="json") for finding in context["skeptic_findings"]],
            "antipattern_findings": [finding.model_dump(mode="json") for finding in context["antipattern_findings"]],
            "supersession_history": context["supersessions"],
            "typed_claims": [claim.model_dump(mode="json") for claim in context["typed_claims"]],
            "compliance": context["compliance"].model_dump(mode="json") if context["compliance"] else None,
            "project_memory": [
                entry.model_dump(mode="json")
                for entry in self.repository.list_memory_entries(MemoryLane.PROJECT, project_id=run_state.metadata.project_id)
            ]
            if run_state.metadata.project_id
            else [],
            "run_memory": [
                entry.model_dump(mode="json")
                for entry in self.repository.list_memory_entries(MemoryLane.RUN_STATE, run_id=run_id)
            ],
            "artifacts": [artifact.model_dump(mode="json") for artifact in context["artifacts"]],
        }
        files: list[str] = []
        checksums: dict[str, str] = {}
        for artifact in context["artifacts"]:
            artifact_path = artifacts_dir / f"{artifact.artifact_type.value}.md"
            artifact_path.write_text(artifact.content, encoding="utf-8")
            rel = str(artifact_path.relative_to(export_root))
            files.append(rel)
            checksums[rel] = artifact.checksum
        manifest = ExportManifest(
            export_id=self._new_id("export"),
            run_id=run_id,
            project_id=run_state.metadata.project_id,
            export_format=export_format,
            files=sorted(files),
            checksums=checksums,
        )
        if export_format in {"json", "both"}:
            bundle_json_path = export_root / "bundle.json"
            bundle_json_path.write_text(canonical_json({"manifest": manifest.model_dump(mode="json"), **bundle}), encoding="utf-8")
            files.append("bundle.json")
            checksums["bundle.json"] = sha256_text(bundle_json_path.read_text(encoding="utf-8"))
        if export_format in {"yaml", "both"}:
            bundle_yaml_path = export_root / "bundle.yaml"
            bundle_yaml_path.write_text(
                yaml.safe_dump({"manifest": manifest.model_dump(mode="json"), **bundle}, sort_keys=False),
                encoding="utf-8",
            )
            files.append("bundle.yaml")
            checksums["bundle.yaml"] = sha256_text(bundle_yaml_path.read_text(encoding="utf-8"))
        manifest.files = sorted(files)
        manifest.checksums = checksums
        self.repository.record_export(manifest, str(export_root))
        return {
            "run_id": run_id,
            "export_path": str(export_root),
            "manifest": manifest.model_dump(mode="json"),
        }

    def import_run(self, import_path: str) -> dict[str, object]:
        path = Path(import_path)
        if path.is_dir():
            bundle_path = path / "bundle.json"
            if not bundle_path.exists():
                bundle_path = path / "bundle.yaml"
        else:
            bundle_path = path
        if bundle_path.suffix.lower() == ".json":
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
        run_state = PsiRunState.model_validate(payload["run_state"])
        summary = SummaryBundle.model_validate(payload["summary"])
        if run_state.metadata.project_id:
            project_summary = payload.get("project_summary") or {}
            self.repository.ensure_project(
                project_id=run_state.metadata.project_id,
                name=project_summary.get("name", run_state.metadata.project_id),
                scope_summary=project_summary.get(
                    "scope_summary",
                    "; ".join(run_state.state.B.included),
                ),
                metadata={"imported": True},
            )
        self._refresh_control_state(run_state, phase_reason="import", trigger="import_run")
        self.repository.save_run(run_state, summary)
        for event_payload in payload.get("events", []):
            self.repository.record_visibility_event(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                VisibilityEvent.model_validate(event_payload),
            )
        for friction_payload in payload.get("friction_logs", []):
            self.repository.record_friction(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                FrictionSignal.model_validate(friction_payload),
            )
        for sweep_payload in payload.get("sweeps", []):
            self.repository.record_sweep(
                project_id=run_state.metadata.project_id,
                run_id=run_state.metadata.run_id,
                trigger_event_id=sweep_payload.get("trigger_event_id"),
                summary=sweep_payload.get("summary", ""),
                impacted_entities=sweep_payload.get("impacted_entities", []),
                blast_radius=[BlastRadiusImpact.model_validate(item) for item in sweep_payload.get("blast_radius", [])],
                deferred_entities=sweep_payload.get("deferred_entities", []),
                transition=sweep_payload.get("transition", {}),
                metadata=sweep_payload.get("metadata", {}),
                sweep_id=sweep_payload.get("id"),
                created_at=sweep_payload.get("created_at"),
            )
        for anchor_payload in payload.get("anchors", []):
            self.repository.upsert_anchor(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                Anchor.model_validate(anchor_payload),
            )
        for tension_payload in payload.get("tensions", []):
            self.repository.upsert_tension(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                Tension.model_validate(tension_payload),
            )
        for hypothesis_payload in payload.get("hypotheses", []):
            self.repository.upsert_hypothesis(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                PsiHypothesis.model_validate(hypothesis_payload),
            )
        for discriminator_payload in payload.get("discriminators", []):
            self.repository.upsert_discriminator(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                Discriminator.model_validate(discriminator_payload),
            )
        for constraint_payload in payload.get("constraints", []):
            self.repository.upsert_constraint(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                ConstraintItem.model_validate(constraint_payload),
            )
        for source_payload in payload.get("source_objects", []):
            self.repository.upsert_source_object(
                run_state.metadata.project_id,
                run_state.metadata.run_id,
                SourceObject.model_validate(source_payload),
            )
        for supersession_payload in payload.get("supersession_history", []):
            self.repository.record_supersession_history_item(
                project_id=run_state.metadata.project_id,
                run_id=run_state.metadata.run_id,
                entity_type=supersession_payload.get("entity_type", ""),
                entity_id=supersession_payload.get("entity_id", ""),
                superseded_by=supersession_payload.get("superseded_by", ""),
                reason=supersession_payload.get("reason", ""),
                metadata=supersession_payload.get("metadata", {}),
                history_id=supersession_payload.get("id"),
                created_at=supersession_payload.get("created_at"),
            )
        for memory_payload in payload.get("project_memory", []):
            self.repository.upsert_memory(MemoryEntry.model_validate(memory_payload))
        for memory_payload in payload.get("run_memory", []):
            self.repository.upsert_memory(MemoryEntry.model_validate(memory_payload))
        for artifact_payload in payload.get("artifacts", []):
            from .models import ArtifactSnapshot

            self.repository.save_artifact(run_state.metadata.run_id, ArtifactSnapshot.model_validate(artifact_payload))
        final_state = self._hydrate_run_state(run_state)
        self.repository.save_run(final_state, summary)
        return {
            "run_id": run_state.metadata.run_id,
            "project_id": run_state.metadata.project_id,
            "status": "imported",
        }

    def diff_analyze(
        self,
        diff: str,
        task: str = "",
        run_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, object]:
        payload = build_analysis_payload(task or "diff analysis", diff=diff)
        frictions = type_friction(payload)
        articulation = summarize_local_articulation(payload)
        impacts = summarize_whole_field_impact(payload, frictions, articulation)
        task_lower = task.lower()
        local_patch_drift_risk = (
            any(signal.friction_type == FrictionType.CONTINUITY_POISON for signal in frictions)
            or "without impact" in task_lower
            or "one-line" in task_lower
            or "local patch" in task_lower
            or not impacts
        )
        response = {
            "friction_types": [signal.friction_type.value for signal in frictions],
            "typed_claims": [claim.model_dump(mode="json") for claim in infer_typed_claims(payload)],
            "local_articulation_summary": articulation,
            "whole_field_impact_summary": impacts,
            "local_patch_drift_risk": local_patch_drift_risk,
            "drift_reason": (
                "Diff changes are visible without sufficient whole-field propagation."
                if local_patch_drift_risk
                else "Diff appears to state a broader field impact."
            ),
        }
        if run_id or project_id:
            response["reflect"] = self.reflect(
                task=task or "diff analysis",
                diff=diff,
                run_id=run_id,
                project_id=project_id,
            )
        return response

    def ingest_test_failure(
        self,
        run_id: str,
        failure_log: str,
    ) -> dict[str, object]:
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        event = self.repository.record_visibility_event(
            run_state.metadata.project_id,
            run_id,
            VisibilityEvent(
                type=VisibilityEventType.FAILURE,
                title="test failure",
                description=failure_log.splitlines()[0][:200],
                source="test_failure",
                severity=0.9,
                evidence=failure_log.splitlines()[:10],
            ),
        )
        frictions = type_friction(build_analysis_payload("test failure", test_failure=failure_log))
        stored = [
            self.repository.record_friction(run_state.metadata.project_id, run_id, signal)
            for signal in frictions
        ]
        payload = build_analysis_payload("test failure", test_failure=failure_log)
        run_state.state.O = event
        run_state.state.F = stored
        self._apply_runtime_control_surface(
            run_state=run_state,
            payload=payload,
            impacts=run_state.state.current_blast_radius,
            frictions=stored,
            durability_blocked=run_state.state.N.blocked,
        )
        self._refresh_methodology_objects(run_state, payload, stored)
        source_audit = self._audit_sources(run_state)
        compliance = self._evaluate_and_store_compliance(
            run_state,
            self.repository.get_run_summary(run_id),
            action="reflect",
        )
        return {
            "event": event.model_dump(mode="json"),
            "friction_types": [signal.model_dump(mode="json") for signal in stored],
            "source_audit": source_audit,
            "compliance_report": compliance.model_dump(mode="json"),
        }

    def project_snapshot(self, project_id: str, run_id: str | None = None, title: str = "project snapshot") -> dict[str, object]:
        summary = self.repository.get_project_summary(project_id)
        snapshot = self.repository.create_project_snapshot(
            project_id=project_id,
            run_id=run_id,
            title=title,
            summary={
                "project": summary.model_dump(mode="json"),
                "anchors": [anchor.model_dump(mode="json") for anchor in self.repository.list_anchors(project_id)],
                "tensions": [tension.model_dump(mode="json") for tension in self.repository.list_tensions(project_id)],
                "constraints": [constraint.model_dump(mode="json") for constraint in self.repository.list_constraints(project_id)],
            },
        )
        return snapshot

    def record_dead_end(
        self,
        title: str,
        description: str,
        cause: str,
        project_id: str | None = None,
        run_id: str | None = None,
        learnings: list[str] | None = None,
    ) -> dict[str, object]:
        return self.repository.record_dead_end(
            project_id=project_id,
            run_id=run_id,
            title=title,
            description=description,
            cause=cause,
            learnings=learnings or [],
        )

    def explain_regime(self, regime: str | None = None, run_id: str | None = None) -> dict[str, object]:
        if regime:
            selected = [regime]
        elif run_id:
            run_state = self.repository.get_run_state(run_id)
            selected = [entry.value for entry in run_state.state.active_regimes]
        else:
            selected = list(REGIME_EXPLANATIONS)
        return {
            "regimes": [
                {"name": key, "explanation": REGIME_EXPLANATIONS[key]}
                for key in selected
            ],
            "control_families": control_family_catalog(),
            "mode_profiles": mode_profile_catalog(),
        }

    def read_summary(self, run_id: str) -> dict[str, object]:
        summary = self.repository.get_run_summary(run_id)
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        compliance = self.repository.get_compliance_report(run_id) or run_state.state.compliance
        return {
            "run_id": run_id,
            "summary": summary.model_dump(mode="json"),
            "transition": run_state.state.transition.model_dump(mode="json"),
            "compliance_report": compliance.model_dump(mode="json") if compliance else {},
        }

    def generate_summary(self, run_id: str) -> dict[str, object]:
        summary = self.repository.get_run_summary(run_id)
        run_state = self._hydrate_run_state(self.repository.get_run_state(run_id))
        self._refresh_control_state(run_state, phase_reason="summary", trigger="generate_summary")
        compliance = self._evaluate_and_store_compliance(run_state, summary, action="summary")
        return {
            "run_id": run_id,
            "summary": summary.model_dump(mode="json"),
            "transition": run_state.state.transition.model_dump(mode="json"),
            "compliance_report": compliance.model_dump(mode="json"),
        }
