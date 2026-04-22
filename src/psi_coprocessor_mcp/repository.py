"""Persistence repository for PSI entities and retrieval."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from .db import Database
from .models import (
    AntiPatternFinding,
    AntiPatternType,
    Anchor,
    ApplicabilityAssessment,
    ArtifactSnapshot,
    BasinType,
    BasinRecord,
    BlastRadiusImpact,
    ComplianceReport,
    ConfidenceLevel,
    ConfidenceAxes,
    ConstraintItem,
    Discriminator,
    DurabilityClass,
    DivergenceClass,
    ExportManifest,
    FindingSeverity,
    FrictionSignal,
    GapOrigin,
    GapRecord,
    GapType,
    InterlockRelation,
    MemoryEntry,
    MemoryLane,
    OperatorFamily,
    PrimitiveComponent,
    PrimitiveOperatorRecord,
    ProjectSummary,
    PsiRunState,
    RunClass,
    RetrievalHit,
    RelationType,
    ScaffoldBoundary,
    SearchRecord,
    SearchStatus,
    SkepticFinding,
    SourceObject,
    StateVariableRecord,
    SummaryBundle,
    Tension,
    TraceStep,
    TypedClaim,
    VisibilityEvent,
)
from .models import Hypothesis as PsiHypothesis
from .utils import compact_json, utc_now_iso


def _loads(value: str | None, fallback: object) -> object:
    if not value:
        return fallback
    return json.loads(value)


def _parse_datetime(value: str | None) -> datetime:
    return datetime.fromisoformat(value) if value else datetime.fromisoformat(utc_now_iso())

class Repository:
    def __init__(self, database: Database):
        self.database = database
        self._backfill_retrieval_index()

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"

    def _upsert_retrieval_document(
        self,
        lane: MemoryLane,
        document_type: str,
        ref_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        timestamp = utc_now_iso()
        payload_tags = compact_json(tags or [])
        payload_metadata = compact_json(metadata or {})
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO retrieval_documents (
                    id, lane, document_type, ref_id, title, content, tags_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lane, document_type, ref_id) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    f"retrieval::{lane.value}::{document_type}::{ref_id}",
                    lane.value,
                    document_type,
                    ref_id,
                    title,
                    content,
                    payload_tags,
                    payload_metadata,
                    timestamp,
                    timestamp,
                ),
            )

    def _backfill_retrieval_index(self) -> None:
        with self.database.transaction() as connection:
            connection.execute("DELETE FROM retrieval_documents WHERE lane IN ('method', 'stable_user')")
            for row in connection.execute(
                "SELECT id, memory_key, title, content, tags_json, metadata_json FROM method_memory"
            ).fetchall():
                connection.execute(
                    """
                    INSERT INTO retrieval_documents (
                        id, lane, document_type, ref_id, title, content, tags_json, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(lane, document_type, ref_id) DO UPDATE SET
                        title = excluded.title,
                        content = excluded.content,
                        tags_json = excluded.tags_json,
                        metadata_json = excluded.metadata_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        f"retrieval::method::memory::{row['memory_key']}",
                        MemoryLane.METHOD.value,
                        "memory",
                        row["memory_key"],
                        row["title"],
                        row["content"],
                        row["tags_json"],
                        row["metadata_json"],
                        utc_now_iso(),
                        utc_now_iso(),
                    ),
                )
            for row in connection.execute(
                "SELECT id, memory_key, title, content, tags_json, metadata_json FROM user_memory"
            ).fetchall():
                connection.execute(
                    """
                    INSERT INTO retrieval_documents (
                        id, lane, document_type, ref_id, title, content, tags_json, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(lane, document_type, ref_id) DO UPDATE SET
                        title = excluded.title,
                        content = excluded.content,
                        tags_json = excluded.tags_json,
                        metadata_json = excluded.metadata_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        f"retrieval::stable_user::memory::{row['memory_key']}",
                        MemoryLane.STABLE_USER.value,
                        "memory",
                        row["memory_key"],
                        row["title"],
                        row["content"],
                        row["tags_json"],
                        row["metadata_json"],
                        utc_now_iso(),
                        utc_now_iso(),
                    ),
                )

    def ensure_project(
        self,
        name: str,
        scope_summary: str,
        project_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSummary:
        project_id = project_id or self._new_id("project")
        timestamp = utc_now_iso()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, scope_summary, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    scope_summary = excluded.scope_summary,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    name,
                    scope_summary,
                    compact_json(metadata or {}),
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_project_summary(project_id)

    def get_project_summary(self, project_id: str) -> ProjectSummary:
        row = self.database.connection.execute(
            """
            SELECT
                p.id,
                p.name,
                p.scope_summary,
                p.updated_at,
                (SELECT COUNT(*) FROM anchors WHERE project_id = p.id) AS anchor_count,
                (SELECT COUNT(*) FROM tensions WHERE project_id = p.id) AS tension_count,
                (SELECT COUNT(*) FROM hypotheses WHERE project_id = p.id) AS hypothesis_count,
                (SELECT COUNT(*) FROM constraints WHERE project_id = p.id AND active = 1) AS constraint_count,
                (SELECT id FROM runs WHERE project_id = p.id ORDER BY updated_at DESC LIMIT 1) AS last_run_id
            FROM projects p
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown project_id: {project_id}")
        return ProjectSummary(
            project_id=row["id"],
            name=row["name"],
            scope_summary=row["scope_summary"],
            anchor_count=row["anchor_count"],
            tension_count=row["tension_count"],
            hypothesis_count=row["hypothesis_count"],
            constraint_count=row["constraint_count"],
            last_run_id=row["last_run_id"],
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def _replace_extended_run_state(self, connection, run_state: PsiRunState) -> None:
        run_id = run_state.metadata.run_id
        project_id = run_state.metadata.project_id

        connection.execute("DELETE FROM source_objects WHERE run_id = ?", (run_id,))
        for source in run_state.state.sources:
            connection.execute(
                """
                INSERT INTO source_objects (
                    id, project_id, run_id, source_kind, title, locator, version, content_hash,
                    canonical, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.id or self._new_id("source"),
                    project_id,
                    run_id,
                    source.source_kind.value,
                    source.title,
                    source.locator,
                    source.version,
                    source.content_hash,
                    1 if source.canonical else 0,
                    compact_json(source.metadata),
                    source.created_at.isoformat(),
                    source.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM primitive_components WHERE run_id = ?", (run_id,))
        for component in run_state.state.components:
            connection.execute(
                """
                INSERT INTO primitive_components (
                    id, project_id, run_id, name, description, component_kind, scope,
                    evidence_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    component.id or self._new_id("component"),
                    project_id,
                    run_id,
                    component.name,
                    component.description,
                    component.component_kind,
                    component.scope,
                    compact_json(component.evidence),
                    compact_json(component.metadata),
                    component.created_at.isoformat(),
                    component.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM state_variables WHERE run_id = ?", (run_id,))
        for state_variable in run_state.state.state_variables:
            connection.execute(
                """
                INSERT INTO state_variables (
                    id, project_id, run_id, name, description, variable_kind, scope, timescale,
                    write_roles_json, read_roles_json, evidence_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state_variable.id or self._new_id("statevar"),
                    project_id,
                    run_id,
                    state_variable.name,
                    state_variable.description,
                    state_variable.variable_kind,
                    state_variable.scope,
                    state_variable.timescale,
                    compact_json(state_variable.write_roles),
                    compact_json(state_variable.read_roles),
                    compact_json(state_variable.evidence),
                    compact_json(state_variable.metadata),
                    state_variable.created_at.isoformat(),
                    state_variable.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM primitive_operators WHERE run_id = ?", (run_id,))
        for operator in run_state.state.primitive_operators:
            connection.execute(
                """
                INSERT INTO primitive_operators (
                    id, project_id, run_id, name, family, object_ref, state_variable_ref, trigger_text,
                    direct_action, target, changes_json, cannot_do_json, where_text, when_text,
                    directionality, timescale, persistence, reversibility, scope, evidence_json,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operator.id or self._new_id("operator"),
                    project_id,
                    run_id,
                    operator.name,
                    operator.family.value,
                    operator.object_ref,
                    operator.state_variable_ref,
                    operator.trigger,
                    operator.direct_action,
                    operator.target,
                    compact_json(operator.changes),
                    compact_json(operator.cannot_do),
                    operator.where,
                    operator.when,
                    operator.directionality,
                    operator.timescale,
                    operator.persistence,
                    operator.reversibility,
                    operator.scope,
                    compact_json(operator.evidence),
                    compact_json(operator.metadata),
                    operator.created_at.isoformat(),
                    operator.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM interlocks WHERE run_id = ?", (run_id,))
        for relation in run_state.state.interlocks:
            connection.execute(
                """
                INSERT INTO interlocks (
                    id, project_id, run_id, relation_type, source_ref, target_ref, description,
                    confidence, scope, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    relation.id or self._new_id("interlock"),
                    project_id,
                    run_id,
                    relation.relation_type.value,
                    relation.source_ref,
                    relation.target_ref,
                    relation.description,
                    relation.confidence.value,
                    relation.scope,
                    compact_json(relation.metadata),
                    relation.created_at.isoformat(),
                    relation.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM trace_steps WHERE run_id = ?", (run_id,))
        for trace in run_state.state.traces:
            connection.execute(
                """
                INSERT INTO trace_steps (
                    id, project_id, run_id, cascade_id, step_index, branch_key, operator_ref,
                    from_state, to_state, trigger_text, outcome, divergence_class, blocking,
                    evidence_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.id or self._new_id("trace"),
                    project_id,
                    run_id,
                    trace.cascade_id,
                    trace.step_index,
                    trace.branch_key,
                    trace.operator_ref,
                    trace.from_state,
                    trace.to_state,
                    trace.trigger,
                    trace.outcome,
                    trace.divergence_class.value if trace.divergence_class else None,
                    1 if trace.blocking else 0,
                    compact_json(trace.evidence),
                    compact_json(trace.metadata),
                    trace.created_at.isoformat(),
                    trace.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM gap_records WHERE run_id = ?", (run_id,))
        for gap in run_state.state.gaps:
            metadata = {
                **gap.metadata,
                "smallest_discriminative_unit": gap.smallest_discriminative_unit,
            }
            connection.execute(
                """
                INSERT INTO gap_records (
                    id, project_id, run_id, title, gap_type, description, likely_origin,
                    nearly_covers_json, insufficient_because, dissolved_by_json, discriminator,
                    blocking, status, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gap.id or self._new_id("gap"),
                    project_id,
                    run_id,
                    gap.title,
                    gap.gap_type.value,
                    gap.description,
                    gap.likely_origin.value,
                    compact_json(gap.nearly_covers),
                    gap.insufficient_because,
                    compact_json(gap.dissolved_by),
                    gap.discriminator,
                    1 if gap.blocking else 0,
                    gap.status,
                    compact_json(metadata),
                    gap.created_at.isoformat(),
                    gap.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM search_records WHERE run_id = ?", (run_id,))
        for search in run_state.state.searches:
            metadata = {
                **search.metadata,
                "smallest_discriminative_unit": search.smallest_discriminative_unit,
            }
            connection.execute(
                """
                INSERT INTO search_records (
                    id, project_id, run_id, query, target_object, rationale, status,
                    findings_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    search.id or self._new_id("search"),
                    project_id,
                    run_id,
                    search.query,
                    search.target_object,
                    search.rationale,
                    search.status.value,
                    compact_json(search.findings),
                    compact_json(metadata),
                    search.created_at.isoformat(),
                    search.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM basin_records WHERE run_id = ?", (run_id,))
        for basin in run_state.state.basins:
            metadata = {
                **basin.metadata,
                "explanatory_burden": basin.explanatory_burden,
                "weakening_conditions": basin.weakening_conditions,
                "discriminator_path": basin.discriminator_path,
            }
            connection.execute(
                """
                INSERT INTO basin_records (
                    id, project_id, run_id, title, basin_type, description, status,
                    preserves_json, conflicts_json, discriminator, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    basin.id or self._new_id("basin"),
                    project_id,
                    run_id,
                    basin.title,
                    basin.basin_type.value,
                    basin.description,
                    basin.status,
                    compact_json(basin.preserves),
                    compact_json(basin.conflicts),
                    basin.discriminator,
                    compact_json(metadata),
                    basin.created_at.isoformat(),
                    basin.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM skeptic_findings WHERE run_id = ?", (run_id,))
        for finding in run_state.state.skeptic_findings:
            connection.execute(
                """
                INSERT INTO skeptic_findings (
                    id, project_id, run_id, claim_ref, question, impact, severity, blocking,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    finding.id or self._new_id("skeptic"),
                    project_id,
                    run_id,
                    finding.claim_ref,
                    finding.question,
                    finding.impact,
                    finding.severity.value,
                    1 if finding.blocking else 0,
                    compact_json(finding.metadata),
                    finding.created_at.isoformat(),
                    finding.updated_at.isoformat(),
                ),
            )

        connection.execute("DELETE FROM antipattern_findings WHERE run_id = ?", (run_id,))
        for finding in run_state.state.antipattern_findings:
            connection.execute(
                """
                INSERT INTO antipattern_findings (
                    id, project_id, run_id, pattern_type, description, evidence_json, severity,
                    blocking, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    finding.id or self._new_id("antipattern"),
                    project_id,
                    run_id,
                    finding.pattern_type.value,
                    finding.description,
                    compact_json(finding.evidence),
                    finding.severity.value,
                    1 if finding.blocking else 0,
                    compact_json(finding.metadata),
                    finding.created_at.isoformat(),
                    finding.updated_at.isoformat(),
                ),
            )

    def save_run(self, run_state: PsiRunState, summary: SummaryBundle | None = None) -> PsiRunState:
        timestamp = utc_now_iso()
        payload = run_state.model_dump(mode="json")
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    id, project_id, title, mode, status, durability_mode, scope_summary,
                    active_regimes_json, current_transition, current_discriminator,
                    last_sweep_status, last_blast_radius_json, run_class, current_phase,
                    next_gating_condition, last_supersession_json, applicability_json,
                    run_state_json, summary_json, created_at, updated_at, last_synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    mode = excluded.mode,
                    status = excluded.status,
                    durability_mode = excluded.durability_mode,
                    scope_summary = excluded.scope_summary,
                    active_regimes_json = excluded.active_regimes_json,
                    current_transition = excluded.current_transition,
                    current_discriminator = excluded.current_discriminator,
                    last_sweep_status = excluded.last_sweep_status,
                    last_blast_radius_json = excluded.last_blast_radius_json,
                    run_class = excluded.run_class,
                    current_phase = excluded.current_phase,
                    next_gating_condition = excluded.next_gating_condition,
                    last_supersession_json = excluded.last_supersession_json,
                    applicability_json = excluded.applicability_json,
                    run_state_json = excluded.run_state_json,
                    summary_json = excluded.summary_json,
                    updated_at = excluded.updated_at,
                    last_synced_at = excluded.last_synced_at
                """,
                (
                    run_state.metadata.run_id,
                    run_state.metadata.project_id,
                    run_state.metadata.title,
                    run_state.metadata.mode.value,
                    run_state.metadata.status.value,
                    run_state.metadata.durability_mode.value,
                    "; ".join(run_state.state.B.included),
                    compact_json([regime.value for regime in run_state.state.active_regimes]),
                    run_state.state.transition.decision.value,
                    run_state.state.current_discriminator,
                    run_state.state.current_sweep_status.status,
                    compact_json([impact.model_dump(mode="json") for impact in run_state.state.current_blast_radius]),
                    run_state.metadata.run_class.value,
                    run_state.state.current_phase.value,
                    run_state.state.next_gating_condition,
                    compact_json(
                        run_state.state.last_supersession.model_dump(mode="json")
                        if run_state.state.last_supersession
                        else {}
                    ),
                    compact_json(run_state.state.applicability.model_dump(mode="json")),
                    compact_json(payload),
                    compact_json((summary or SummaryBundle()).model_dump(mode="json")),
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
            self._replace_extended_run_state(connection, run_state)
            connection.execute("DELETE FROM typed_claims WHERE run_id = ?", (run_state.metadata.run_id,))
            for claim in run_state.state.C:
                connection.execute(
                    """
                    INSERT INTO typed_claims (
                        id, project_id, run_id, statement, provenance_tag, load_bearing, structural_role,
                        confidence, durability_class, confidence_axes_json, scaffold_json,
                        evidence_json, notes_json, source, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim.id or self._new_id("claim"),
                        run_state.metadata.project_id,
                        run_state.metadata.run_id,
                        claim.statement,
                        claim.provenance.value,
                        1 if claim.load_bearing else 0,
                        claim.structural_role,
                        claim.confidence.value,
                        claim.durability_class.value,
                        compact_json(claim.confidence_axes.model_dump(mode="json")),
                        compact_json(claim.scaffold_boundary.model_dump(mode="json") if claim.scaffold_boundary else {}),
                        compact_json(claim.evidence),
                        compact_json(claim.notes),
                        claim.source,
                        claim.created_at.isoformat(),
                        claim.updated_at.isoformat(),
                    ),
                )
            if run_state.state.compliance:
                compliance = run_state.state.compliance
                connection.execute(
                    """
                    INSERT INTO compliance_reports (
                        id, run_id, status, blocking, requested_action, issues_json,
                        checked_artifacts_json, notes_json, checked_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(run_id) DO UPDATE SET
                        status = excluded.status,
                        blocking = excluded.blocking,
                        requested_action = excluded.requested_action,
                        issues_json = excluded.issues_json,
                        checked_artifacts_json = excluded.checked_artifacts_json,
                        notes_json = excluded.notes_json,
                        checked_at = excluded.checked_at
                    """,
                    (
                        f"compliance::{run_state.metadata.run_id}",
                        run_state.metadata.run_id,
                        compliance.status,
                        1 if compliance.blocking else 0,
                        compliance.requested_action,
                        compact_json([issue.model_dump(mode="json") for issue in compliance.issues]),
                        compact_json(compliance.checked_artifacts),
                        compact_json(compliance.notes),
                        compliance.checked_at.isoformat(),
                    ),
                )
            else:
                connection.execute("DELETE FROM compliance_reports WHERE run_id = ?", (run_state.metadata.run_id,))
            connection.execute(
                "DELETE FROM retrieval_documents WHERE lane = ? AND document_type = ? AND ref_id LIKE ?",
                (MemoryLane.RUN_STATE.value, "typed_claim", f"{run_state.metadata.run_id}:%"),
            )
            connection.execute(
                "DELETE FROM retrieval_documents WHERE lane = ? AND document_type = ? AND ref_id = ?",
                (MemoryLane.RUN_STATE.value, "compliance", run_state.metadata.run_id),
            )
        retrieval_content = summary.compact_summary if summary else run_state.state.transition.rationale
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE,
            "run",
            run_state.metadata.run_id,
            run_state.metadata.title or run_state.metadata.run_id,
            retrieval_content or run_state.metadata.mode.value,
            ["run", run_state.metadata.mode.value, run_state.metadata.status.value],
            {"project_id": run_state.metadata.project_id},
        )
        for claim in run_state.state.C:
            self._upsert_retrieval_document(
                MemoryLane.RUN_STATE,
                "typed_claim",
                f"{run_state.metadata.run_id}:{claim.id or claim.statement[:48]}",
                claim.structural_role or "typed-claim",
                claim.statement,
                [
                    "typed-claim",
                    claim.provenance.value,
                    claim.durability_class.value,
                    "load-bearing" if claim.load_bearing else "supporting",
                ],
                {
                    "project_id": run_state.metadata.project_id,
                    "run_id": run_state.metadata.run_id,
                    "confidence": claim.confidence.value,
                    "source": claim.source,
                },
            )
        if run_state.state.compliance:
            compliance = run_state.state.compliance
            self._upsert_retrieval_document(
                MemoryLane.RUN_STATE,
                "compliance",
                run_state.metadata.run_id,
                f"compliance::{compliance.status.lower()}",
                " | ".join(issue.message for issue in compliance.issues[:4]) or "PSI compliance check passed.",
                ["compliance", compliance.status.lower(), "blocking" if compliance.blocking else "non-blocking"],
                {
                    "project_id": run_state.metadata.project_id,
                    "run_id": run_state.metadata.run_id,
                    "requested_action": compliance.requested_action,
                },
            )
        return run_state

    def get_run_state(self, run_id: str) -> PsiRunState:
        row = self.database.connection.execute(
            "SELECT run_state_json FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return PsiRunState.model_validate(_loads(row["run_state_json"], {}))

    def get_run_summary(self, run_id: str) -> SummaryBundle:
        row = self.database.connection.execute(
            "SELECT summary_json FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return SummaryBundle.model_validate(_loads(row["summary_json"], {}))

    def record_visibility_event(
        self,
        project_id: str | None,
        run_id: str,
        event: VisibilityEvent,
    ) -> VisibilityEvent:
        event_id = event.id or self._new_id("event")
        payload = event.model_copy(update={"id": event_id})
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO visibility_events (
                    id, project_id, run_id, event_type, title, description, source, severity,
                    affected_entities_json, evidence_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.type.value,
                    payload.title,
                    payload.description,
                    payload.source,
                    payload.severity,
                    compact_json(payload.affected_entities),
                    compact_json(payload.evidence),
                    compact_json(payload.metadata),
                    payload.created_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE,
            "visibility_event",
            payload.id,
            payload.title,
            payload.description,
            [payload.type.value, "visibility-event"],
            {"run_id": run_id, "project_id": project_id},
        )
        return payload

    def list_visibility_events(self, run_id: str) -> list[VisibilityEvent]:
        rows = self.database.connection.execute(
            """
            SELECT id, event_type, title, description, source, severity, affected_entities_json,
                   evidence_json, metadata_json, created_at
            FROM visibility_events
            WHERE run_id = ?
            ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            VisibilityEvent(
                id=row["id"],
                type=row["event_type"],
                title=row["title"],
                description=row["description"],
                source=row["source"],
                severity=row["severity"],
                affected_entities=_loads(row["affected_entities_json"], []),
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]

    def upsert_source_object(
        self,
        project_id: str | None,
        run_id: str,
        source_object: SourceObject,
    ) -> SourceObject:
        source_id = source_object.id or self._new_id("source")
        payload = source_object.model_copy(
            update={"id": source_id, "updated_at": datetime.fromisoformat(utc_now_iso())}
        )
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO source_objects (
                    id, project_id, run_id, source_kind, title, locator, version, content_hash,
                    canonical, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    source_kind = excluded.source_kind,
                    title = excluded.title,
                    locator = excluded.locator,
                    version = excluded.version,
                    content_hash = excluded.content_hash,
                    canonical = excluded.canonical,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.source_kind.value,
                    payload.title,
                    payload.locator,
                    payload.version,
                    payload.content_hash,
                    1 if payload.canonical else 0,
                    compact_json(payload.metadata),
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE,
            "source_object",
            payload.id,
            payload.title,
            payload.locator or payload.title,
            ["source-object", payload.source_kind.value],
            {"project_id": project_id, "run_id": run_id, "canonical": payload.canonical},
        )
        return payload

    def list_source_objects(self, run_id: str) -> list[SourceObject]:
        rows = self.database.connection.execute(
            """
            SELECT id, source_kind, title, locator, version, content_hash, canonical,
                   metadata_json, created_at, updated_at
            FROM source_objects
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            SourceObject(
                id=row["id"],
                source_kind=row["source_kind"],
                title=row["title"],
                locator=row["locator"],
                version=row["version"],
                content_hash=row["content_hash"],
                canonical=bool(row["canonical"]),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_primitive_components(self, run_id: str) -> list[PrimitiveComponent]:
        rows = self.database.connection.execute(
            """
            SELECT id, name, description, component_kind, scope, evidence_json, metadata_json, created_at, updated_at
            FROM primitive_components
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            PrimitiveComponent(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                component_kind=row["component_kind"],
                scope=row["scope"],
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_state_variables(self, run_id: str) -> list[StateVariableRecord]:
        rows = self.database.connection.execute(
            """
            SELECT id, name, description, variable_kind, scope, timescale, write_roles_json,
                   read_roles_json, evidence_json, metadata_json, created_at, updated_at
            FROM state_variables
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            StateVariableRecord(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                variable_kind=row["variable_kind"],
                scope=row["scope"],
                timescale=row["timescale"],
                write_roles=_loads(row["write_roles_json"], []),
                read_roles=_loads(row["read_roles_json"], []),
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_primitive_operators(self, run_id: str) -> list[PrimitiveOperatorRecord]:
        rows = self.database.connection.execute(
            """
            SELECT id, name, family, object_ref, state_variable_ref, trigger_text, direct_action, target,
                   changes_json, cannot_do_json, where_text, when_text, directionality, timescale,
                   persistence, reversibility, scope, evidence_json, metadata_json, created_at, updated_at
            FROM primitive_operators
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            PrimitiveOperatorRecord(
                id=row["id"],
                name=row["name"],
                family=OperatorFamily(row["family"]),
                object_ref=row["object_ref"],
                state_variable_ref=row["state_variable_ref"],
                trigger=row["trigger_text"],
                direct_action=row["direct_action"],
                target=row["target"],
                changes=_loads(row["changes_json"], []),
                cannot_do=_loads(row["cannot_do_json"], []),
                where=row["where_text"],
                when=row["when_text"],
                directionality=row["directionality"],
                timescale=row["timescale"],
                persistence=row["persistence"],
                reversibility=row["reversibility"],
                scope=row["scope"],
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_interlocks(self, run_id: str) -> list[InterlockRelation]:
        rows = self.database.connection.execute(
            """
            SELECT id, relation_type, source_ref, target_ref, description, confidence, scope,
                   metadata_json, created_at, updated_at
            FROM interlocks
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            InterlockRelation(
                id=row["id"],
                relation_type=RelationType(row["relation_type"]),
                source_ref=row["source_ref"],
                target_ref=row["target_ref"],
                description=row["description"],
                confidence=ConfidenceLevel(row["confidence"]),
                scope=row["scope"],
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_trace_steps(self, run_id: str) -> list[TraceStep]:
        rows = self.database.connection.execute(
            """
            SELECT id, cascade_id, step_index, branch_key, operator_ref, from_state, to_state,
                   trigger_text, outcome, divergence_class, blocking, evidence_json, metadata_json,
                   created_at, updated_at
            FROM trace_steps
            WHERE run_id = ?
            ORDER BY step_index ASC, updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            TraceStep(
                id=row["id"],
                cascade_id=row["cascade_id"],
                step_index=row["step_index"],
                branch_key=row["branch_key"],
                operator_ref=row["operator_ref"],
                from_state=row["from_state"],
                to_state=row["to_state"],
                trigger=row["trigger_text"],
                outcome=row["outcome"],
                divergence_class=DivergenceClass(row["divergence_class"]) if row["divergence_class"] else None,
                blocking=bool(row["blocking"]),
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_gap_records(self, run_id: str) -> list[GapRecord]:
        rows = self.database.connection.execute(
            """
            SELECT id, title, gap_type, description, likely_origin, nearly_covers_json,
                   insufficient_because, dissolved_by_json, discriminator, blocking, status,
                   metadata_json, created_at, updated_at
            FROM gap_records
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            GapRecord(
                id=row["id"],
                title=row["title"],
                gap_type=GapType(row["gap_type"]),
                description=row["description"],
                likely_origin=GapOrigin(row["likely_origin"]),
                nearly_covers=_loads(row["nearly_covers_json"], []),
                insufficient_because=row["insufficient_because"],
                dissolved_by=_loads(row["dissolved_by_json"], []),
                smallest_discriminative_unit=_loads(row["metadata_json"], {}).get("smallest_discriminative_unit", ""),
                discriminator=row["discriminator"],
                blocking=bool(row["blocking"]),
                status=row["status"],
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_search_records(self, run_id: str) -> list[SearchRecord]:
        rows = self.database.connection.execute(
            """
            SELECT id, query, target_object, rationale, status, findings_json, metadata_json, created_at, updated_at
            FROM search_records
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            SearchRecord(
                id=row["id"],
                query=row["query"],
                target_object=row["target_object"],
                smallest_discriminative_unit=_loads(row["metadata_json"], {}).get("smallest_discriminative_unit", ""),
                rationale=row["rationale"],
                status=SearchStatus(row["status"]),
                findings=_loads(row["findings_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_basin_records(self, run_id: str) -> list[BasinRecord]:
        rows = self.database.connection.execute(
            """
            SELECT id, title, basin_type, description, status, preserves_json, conflicts_json,
                   discriminator, metadata_json, created_at, updated_at
            FROM basin_records
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            BasinRecord(
                id=row["id"],
                title=row["title"],
                basin_type=BasinType(row["basin_type"]),
                description=row["description"],
                status=row["status"],
                preserves=_loads(row["preserves_json"], []),
                conflicts=_loads(row["conflicts_json"], []),
                explanatory_burden=_loads(row["metadata_json"], {}).get("explanatory_burden", []),
                weakening_conditions=_loads(row["metadata_json"], {}).get("weakening_conditions", []),
                discriminator_path=_loads(row["metadata_json"], {}).get("discriminator_path", []),
                discriminator=row["discriminator"],
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_skeptic_findings(self, run_id: str) -> list[SkepticFinding]:
        rows = self.database.connection.execute(
            """
            SELECT id, claim_ref, question, impact, severity, blocking, metadata_json, created_at, updated_at
            FROM skeptic_findings
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            SkepticFinding(
                id=row["id"],
                claim_ref=row["claim_ref"],
                question=row["question"],
                impact=row["impact"],
                severity=FindingSeverity(row["severity"]),
                blocking=bool(row["blocking"]),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_antipattern_findings(self, run_id: str) -> list[AntiPatternFinding]:
        rows = self.database.connection.execute(
            """
            SELECT id, pattern_type, description, evidence_json, severity, blocking, metadata_json, created_at, updated_at
            FROM antipattern_findings
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            AntiPatternFinding(
                id=row["id"],
                pattern_type=AntiPatternType(row["pattern_type"]),
                description=row["description"],
                evidence=_loads(row["evidence_json"], []),
                severity=FindingSeverity(row["severity"]),
                blocking=bool(row["blocking"]),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def record_friction(
        self,
        project_id: str | None,
        run_id: str | None,
        signal: FrictionSignal,
    ) -> FrictionSignal:
        signal_id = signal.id or self._new_id("friction")
        payload = signal.model_copy(update={"id": signal_id})
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO friction_logs (
                    id, project_id, run_id, friction_type, severity, routing_regime,
                    rationale, evidence_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.friction_type.value,
                    payload.severity,
                    payload.routing_regime.value,
                    payload.rationale,
                    compact_json(payload.evidence),
                    compact_json(payload.metadata),
                    payload.created_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE if run_id else MemoryLane.PROJECT,
            "friction",
            payload.id,
            payload.friction_type.value,
            payload.rationale,
            [payload.friction_type.value, payload.routing_regime.value],
            {"run_id": run_id, "project_id": project_id},
        )
        return payload

    def list_friction_logs(self, run_id: str) -> list[FrictionSignal]:
        rows = self.database.connection.execute(
            """
            SELECT id, friction_type, severity, routing_regime, rationale, evidence_json, metadata_json, created_at
            FROM friction_logs
            WHERE run_id = ?
            ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            FrictionSignal(
                id=row["id"],
                friction_type=row["friction_type"],
                severity=row["severity"],
                routing_regime=row["routing_regime"],
                rationale=row["rationale"],
                evidence=_loads(row["evidence_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]

    def upsert_anchor(self, project_id: str | None, run_id: str | None, anchor: Anchor) -> Anchor:
        anchor_id = anchor.id or self._new_id("anchor")
        payload = anchor.model_copy(update={"id": anchor_id, "updated_at": datetime.fromisoformat(utc_now_iso())})
        metadata = {
            **payload.metadata,
            "weakening_conditions": payload.weakening_conditions,
            "explanatory_burden": payload.explanatory_burden,
            "scaffold_boundary": payload.scaffold_boundary.model_dump(mode="json") if payload.scaffold_boundary else None,
            "user_promoted": payload.user_promoted,
            "sweep_survival_count": payload.sweep_survival_count,
        }
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO anchors (
                    id, project_id, run_id, name, status, description, centrality, fragility,
                    confidence, durability_class, rationale, dependencies_json, implications_json, metadata_json,
                    invalidated_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    name = excluded.name,
                    status = excluded.status,
                    description = excluded.description,
                    centrality = excluded.centrality,
                    fragility = excluded.fragility,
                    confidence = excluded.confidence,
                    durability_class = excluded.durability_class,
                    rationale = excluded.rationale,
                    dependencies_json = excluded.dependencies_json,
                    implications_json = excluded.implications_json,
                    metadata_json = excluded.metadata_json,
                    invalidated_by = excluded.invalidated_by,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.name,
                    payload.status,
                    payload.description,
                    payload.centrality,
                    payload.fragility,
                    payload.confidence.value,
                    payload.durability_class.value,
                    payload.rationale,
                    compact_json(payload.dependencies),
                    compact_json(payload.implications),
                    compact_json(metadata),
                    payload.invalidated_by,
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "anchor",
            payload.id,
            payload.name,
            payload.description or payload.rationale,
            [payload.status, payload.confidence.value],
            {"project_id": project_id, "run_id": run_id},
        )
        return payload

    def list_anchors(self, project_id: str) -> list[Anchor]:
        rows = self.database.connection.execute(
            """
            SELECT id, name, status, description, centrality, fragility, confidence,
                   durability_class, rationale, dependencies_json, implications_json, metadata_json,
                   invalidated_by, created_at, updated_at
            FROM anchors
            WHERE project_id = ?
            ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [
            Anchor(
                id=row["id"],
                name=row["name"],
                status=row["status"],
                description=row["description"],
                centrality=row["centrality"],
                fragility=row["fragility"],
                confidence=ConfidenceLevel(row["confidence"]),
                durability_class=DurabilityClass(row["durability_class"]),
                rationale=row["rationale"],
                dependencies=_loads(row["dependencies_json"], []),
                implications=_loads(row["implications_json"], []),
                weakening_conditions=_loads(row["metadata_json"], {}).get("weakening_conditions", []),
                explanatory_burden=_loads(row["metadata_json"], {}).get("explanatory_burden", []),
                scaffold_boundary=(
                    ScaffoldBoundary.model_validate(_loads(row["metadata_json"], {}).get("scaffold_boundary"))
                    if _loads(row["metadata_json"], {}).get("scaffold_boundary")
                    else None
                ),
                user_promoted=bool(_loads(row["metadata_json"], {}).get("user_promoted", False)),
                sweep_survival_count=int(_loads(row["metadata_json"], {}).get("sweep_survival_count", 0)),
                metadata=_loads(row["metadata_json"], {}),
                invalidated_by=row["invalidated_by"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def invalidate_anchor(
        self,
        anchor_id: str,
        invalidated_by: str | None,
        reason: str,
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> Anchor:
        row = self.database.connection.execute(
            "SELECT * FROM anchors WHERE id = ?",
            (anchor_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown anchor_id: {anchor_id}")
        anchor = Anchor(
            id=row["id"],
            name=row["name"],
            status="invalidated",
            description=row["description"],
            centrality=row["centrality"],
            fragility=row["fragility"],
            confidence=ConfidenceLevel(row["confidence"]),
            durability_class=DurabilityClass(row["durability_class"]),
            rationale=reason,
            dependencies=_loads(row["dependencies_json"], []),
            implications=_loads(row["implications_json"], []),
            weakening_conditions=_loads(row["metadata_json"], {}).get("weakening_conditions", []),
            explanatory_burden=_loads(row["metadata_json"], {}).get("explanatory_burden", []),
            scaffold_boundary=(
                ScaffoldBoundary.model_validate(_loads(row["metadata_json"], {}).get("scaffold_boundary"))
                if _loads(row["metadata_json"], {}).get("scaffold_boundary")
                else None
            ),
            user_promoted=bool(_loads(row["metadata_json"], {}).get("user_promoted", False)),
            sweep_survival_count=int(_loads(row["metadata_json"], {}).get("sweep_survival_count", 0)),
            metadata=_loads(row["metadata_json"], {}),
            invalidated_by=invalidated_by,
            created_at=_parse_datetime(row["created_at"]),
            updated_at=datetime.fromisoformat(utc_now_iso()),
        )
        stored = self.upsert_anchor(project_id, run_id, anchor)
        self.record_supersession_history_item(
            project_id=project_id,
            run_id=run_id,
            entity_type="anchor",
            entity_id=anchor_id,
            superseded_by=invalidated_by or anchor_id,
            reason=reason,
        )
        return stored

    def record_supersession_history_item(
        self,
        project_id: str | None,
        run_id: str | None,
        entity_type: str,
        entity_id: str,
        superseded_by: str,
        reason: str,
        metadata: dict[str, object] | None = None,
        history_id: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, object]:
        payload = {
            "id": history_id or self._new_id("supersession"),
            "project_id": project_id,
            "run_id": run_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "superseded_by": superseded_by,
            "reason": reason,
            "metadata": metadata or {},
            "created_at": created_at or utc_now_iso(),
        }
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO supersession_history (
                    id, project_id, run_id, entity_type, entity_id, superseded_by, reason, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    entity_type = excluded.entity_type,
                    entity_id = excluded.entity_id,
                    superseded_by = excluded.superseded_by,
                    reason = excluded.reason,
                    metadata_json = excluded.metadata_json,
                    created_at = excluded.created_at
                """,
                (
                    payload["id"],
                    payload["project_id"],
                    payload["run_id"],
                    payload["entity_type"],
                    payload["entity_id"],
                    payload["superseded_by"],
                    payload["reason"],
                    compact_json(payload["metadata"]),
                    payload["created_at"],
                ),
            )
        return payload

    def upsert_tension(self, project_id: str | None, run_id: str | None, tension: Tension) -> Tension:
        tension_id = tension.id or self._new_id("tension")
        payload = tension.model_copy(update={"id": tension_id, "updated_at": datetime.fromisoformat(utc_now_iso())})
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO tensions (
                    id, project_id, run_id, title, status, description, severity, forces_json,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    title = excluded.title,
                    status = excluded.status,
                    description = excluded.description,
                    severity = excluded.severity,
                    forces_json = excluded.forces_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.title,
                    payload.status,
                    payload.description,
                    payload.severity,
                    compact_json(payload.forces),
                    compact_json(payload.metadata),
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "tension",
            payload.id,
            payload.title,
            payload.description,
            [payload.status, "tension"],
            {"project_id": project_id, "run_id": run_id},
        )
        return payload

    def list_tensions(self, project_id: str) -> list[Tension]:
        rows = self.database.connection.execute(
            """
            SELECT id, title, status, description, severity, forces_json, metadata_json, created_at, updated_at
            FROM tensions WHERE project_id = ? ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [
            Tension(
                id=row["id"],
                title=row["title"],
                status=row["status"],
                description=row["description"],
                severity=row["severity"],
                forces=_loads(row["forces_json"], []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def upsert_hypothesis(
        self,
        project_id: str | None,
        run_id: str | None,
        hypothesis: PsiHypothesis,
    ) -> PsiHypothesis:
        hypothesis_id = hypothesis.id or self._new_id("hypothesis")
        payload = hypothesis.model_copy(
            update={"id": hypothesis_id, "updated_at": datetime.fromisoformat(utc_now_iso())}
        )
        metadata = {
            **payload.metadata,
            "weakening_conditions": payload.weakening_conditions,
            "discriminator_path": payload.discriminator_path,
            "explanatory_burden": payload.explanatory_burden,
        }
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO hypotheses (
                    id, project_id, run_id, title, status, description, confidence,
                    durability_class, preserves_json, risks_json, discriminators_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    title = excluded.title,
                    status = excluded.status,
                    description = excluded.description,
                    confidence = excluded.confidence,
                    durability_class = excluded.durability_class,
                    preserves_json = excluded.preserves_json,
                    risks_json = excluded.risks_json,
                    discriminators_json = excluded.discriminators_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.title,
                    payload.status,
                    payload.description,
                    payload.confidence.value,
                    payload.durability_class.value,
                    compact_json(payload.preserves),
                    compact_json(payload.risks),
                    compact_json(payload.discriminators),
                    compact_json(metadata),
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "hypothesis",
            payload.id,
            payload.title,
            payload.description,
            [payload.status, payload.confidence.value],
            {"project_id": project_id, "run_id": run_id},
        )
        return payload

    def list_hypotheses(self, project_id: str) -> list[PsiHypothesis]:
        rows = self.database.connection.execute(
            """
            SELECT id, title, status, description, confidence, durability_class, preserves_json,
                   risks_json, discriminators_json, metadata_json, created_at, updated_at
            FROM hypotheses WHERE project_id = ? ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [
            PsiHypothesis(
                id=row["id"],
                title=row["title"],
                status=row["status"],
                description=row["description"],
                confidence=row["confidence"],
                durability_class=DurabilityClass(row["durability_class"]),
                preserves=_loads(row["preserves_json"], []),
                risks=_loads(row["risks_json"], []),
                discriminators=_loads(row["discriminators_json"], []),
                weakening_conditions=_loads(row["metadata_json"], {}).get("weakening_conditions", []),
                discriminator_path=_loads(row["metadata_json"], {}).get("discriminator_path", []),
                explanatory_burden=_loads(row["metadata_json"], {}).get("explanatory_burden", []),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def list_typed_claims(self, run_id: str) -> list[TypedClaim]:
        rows = self.database.connection.execute(
            """
            SELECT id, statement, provenance_tag, load_bearing, structural_role, confidence,
                   durability_class, confidence_axes_json, scaffold_json,
                   evidence_json, notes_json, source, created_at, updated_at
            FROM typed_claims
            WHERE run_id = ?
            ORDER BY updated_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            TypedClaim(
                id=row["id"],
                statement=row["statement"],
                provenance=row["provenance_tag"],
                load_bearing=bool(row["load_bearing"]),
                structural_role=row["structural_role"],
                confidence=row["confidence"],
                durability_class=DurabilityClass(row["durability_class"]),
                confidence_axes=ConfidenceAxes.model_validate(_loads(row["confidence_axes_json"], {})),
                scaffold_boundary=(
                    ScaffoldBoundary.model_validate(_loads(row["scaffold_json"], {}))
                    if _loads(row["scaffold_json"], {})
                    else None
                ),
                evidence=_loads(row["evidence_json"], []),
                notes=_loads(row["notes_json"], []),
                source=row["source"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def get_compliance_report(self, run_id: str) -> ComplianceReport | None:
        row = self.database.connection.execute(
            """
            SELECT status, blocking, requested_action, issues_json, checked_artifacts_json, notes_json, checked_at
            FROM compliance_reports
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return ComplianceReport(
            status=row["status"],
            blocking=bool(row["blocking"]),
            requested_action=row["requested_action"],
            issues=_loads(row["issues_json"], []),
            checked_artifacts=_loads(row["checked_artifacts_json"], []),
            notes=_loads(row["notes_json"], []),
            checked_at=_parse_datetime(row["checked_at"]),
        )

    def upsert_discriminator(
        self,
        project_id: str | None,
        run_id: str | None,
        discriminator: Discriminator,
    ) -> Discriminator:
        discriminator_id = discriminator.id or self._new_id("discriminator")
        payload = discriminator.model_copy(
            update={"id": discriminator_id, "updated_at": datetime.fromisoformat(utc_now_iso())}
        )
        metadata = {
            **payload.metadata,
            "expected_outcome_map": payload.expected_outcome_map,
        }
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO discriminators (
                    id, project_id, run_id, title, description, target_json, best_next_probe,
                    confidence_gain, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    title = excluded.title,
                    description = excluded.description,
                    target_json = excluded.target_json,
                    best_next_probe = excluded.best_next_probe,
                    confidence_gain = excluded.confidence_gain,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.title,
                    payload.description,
                    compact_json(payload.target),
                    payload.best_next_probe,
                    payload.confidence_gain,
                    compact_json(metadata),
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "discriminator",
            payload.id,
            payload.title,
            payload.description,
            ["discriminator"],
            {"project_id": project_id, "run_id": run_id},
        )
        return payload

    def list_discriminators(self, project_id: str) -> list[Discriminator]:
        rows = self.database.connection.execute(
            """
            SELECT id, title, description, target_json, best_next_probe, confidence_gain,
                   metadata_json, created_at, updated_at
            FROM discriminators WHERE project_id = ? ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [
            Discriminator(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                target=_loads(row["target_json"], []),
                best_next_probe=row["best_next_probe"],
                confidence_gain=row["confidence_gain"],
                expected_outcome_map=_loads(row["metadata_json"], {}).get("expected_outcome_map", {}),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def upsert_constraint(
        self,
        project_id: str | None,
        run_id: str | None,
        constraint: ConstraintItem,
    ) -> ConstraintItem:
        constraint_id = constraint.id or self._new_id("constraint")
        payload = constraint.model_copy(
            update={"id": constraint_id, "updated_at": datetime.fromisoformat(utc_now_iso())}
        )
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO constraints (
                    id, project_id, run_id, constraint_type, category, severity, description,
                    source, timescale, active, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    run_id = excluded.run_id,
                    constraint_type = excluded.constraint_type,
                    category = excluded.category,
                    severity = excluded.severity,
                    description = excluded.description,
                    source = excluded.source,
                    timescale = excluded.timescale,
                    active = excluded.active,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    project_id,
                    run_id,
                    payload.constraint_type,
                    payload.category,
                    payload.severity,
                    payload.description,
                    payload.source,
                    payload.timescale,
                    1 if payload.active else 0,
                    compact_json(payload.metadata),
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "constraint",
            payload.id,
            payload.constraint_type,
            payload.description,
            [payload.category, payload.severity],
            {"project_id": project_id, "run_id": run_id},
        )
        return payload

    def list_constraints(self, project_id: str) -> list[ConstraintItem]:
        rows = self.database.connection.execute(
            """
            SELECT id, constraint_type, category, severity, description, source, timescale,
                   active, metadata_json, created_at, updated_at
            FROM constraints WHERE project_id = ? ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [
            ConstraintItem(
                id=row["id"],
                constraint_type=row["constraint_type"],
                category=row["category"],
                severity=row["severity"],
                description=row["description"],
                source=row["source"],
                timescale=row["timescale"],
                active=bool(row["active"]),
                metadata=_loads(row["metadata_json"], {}),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def save_artifact(self, run_id: str, artifact: ArtifactSnapshot) -> ArtifactSnapshot:
        artifact_id = artifact.id or self._new_id("artifact")
        payload = artifact.model_copy(update={"id": artifact_id, "updated_at": datetime.fromisoformat(utc_now_iso())})
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (
                    id, run_id, artifact_type, format, content, checksum, authoritative, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, artifact_type, format) DO UPDATE SET
                    content = excluded.content,
                    checksum = excluded.checksum,
                    authoritative = excluded.authoritative,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.id,
                    run_id,
                    payload.artifact_type.value,
                    payload.format,
                    payload.content,
                    payload.checksum,
                    1 if payload.authoritative else 0,
                    payload.created_at.isoformat(),
                    payload.updated_at.isoformat(),
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE,
            "artifact",
            f"{run_id}:{payload.artifact_type.value}",
            payload.artifact_type.value,
            payload.content,
            [payload.artifact_type.value, payload.format],
            {"run_id": run_id},
        )
        return payload

    def list_artifacts(self, run_id: str) -> list[ArtifactSnapshot]:
        rows = self.database.connection.execute(
            """
            SELECT id, artifact_type, format, content, checksum, authoritative, created_at, updated_at
            FROM artifacts WHERE run_id = ? ORDER BY artifact_type
            """,
            (run_id,),
        ).fetchall()
        return [
            ArtifactSnapshot(
                id=row["id"],
                artifact_type=row["artifact_type"],
                format=row["format"],
                content=row["content"],
                checksum=row["checksum"],
                authoritative=bool(row["authoritative"]),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]

    def record_sweep(
        self,
        project_id: str | None,
        run_id: str,
        trigger_event_id: str | None,
        summary: str,
        impacted_entities: list[str],
        blast_radius: list[BlastRadiusImpact],
        deferred_entities: list[str],
        transition: dict[str, object],
        metadata: dict[str, object] | None = None,
        sweep_id: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, object]:
        sweep_id = sweep_id or self._new_id("sweep")
        created_at = created_at or utc_now_iso()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO coherence_sweeps (
                    id, project_id, run_id, trigger_event_id, summary, impacted_entities_json,
                    blast_radius_json, deferred_entities_json, transition_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sweep_id,
                    project_id,
                    run_id,
                    trigger_event_id,
                    summary,
                    compact_json(impacted_entities),
                    compact_json([impact.model_dump(mode="json") for impact in blast_radius]),
                    compact_json(deferred_entities),
                    compact_json(transition),
                    compact_json(metadata or {}),
                    created_at,
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.RUN_STATE,
            "sweep",
            sweep_id,
            "coherence_sweep",
            summary,
            ["coherence-sweep"],
            {"run_id": run_id, "project_id": project_id},
        )
        return {
            "id": sweep_id,
            "project_id": project_id,
            "run_id": run_id,
            "trigger_event_id": trigger_event_id,
            "summary": summary,
            "impacted_entities": impacted_entities,
            "blast_radius": [impact.model_dump(mode="json") for impact in blast_radius],
            "deferred_entities": deferred_entities,
            "transition": transition,
            "metadata": metadata or {},
            "created_at": created_at,
        }

    def list_sweeps(self, run_id: str) -> list[dict[str, object]]:
        rows = self.database.connection.execute(
            """
            SELECT id, trigger_event_id, summary, impacted_entities_json, blast_radius_json,
                   deferred_entities_json, transition_json, metadata_json, created_at
            FROM coherence_sweeps WHERE run_id = ? ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "trigger_event_id": row["trigger_event_id"],
                "summary": row["summary"],
                "impacted_entities": _loads(row["impacted_entities_json"], []),
                "blast_radius": _loads(row["blast_radius_json"], []),
                "deferred_entities": _loads(row["deferred_entities_json"], []),
                "transition": _loads(row["transition_json"], {}),
                "metadata": _loads(row["metadata_json"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def upsert_memory(self, entry: MemoryEntry) -> MemoryEntry:
        timestamp = utc_now_iso()
        stable_ref = (
            entry.key
            if entry.lane in {MemoryLane.METHOD, MemoryLane.STABLE_USER}
            else f"{entry.project_id or entry.run_id}:{entry.key}"
        )
        entry_id = entry.id or f"memory::{entry.lane.value}::{stable_ref}"
        payload = entry.model_copy(update={"id": entry_id, "updated_at": datetime.fromisoformat(timestamp)})
        table = {
            MemoryLane.METHOD: "method_memory",
            MemoryLane.STABLE_USER: "user_memory",
            MemoryLane.PROJECT: "project_memory",
            MemoryLane.RUN_STATE: "run_memory",
        }[payload.lane]
        id_column = {
            MemoryLane.METHOD: None,
            MemoryLane.STABLE_USER: None,
            MemoryLane.PROJECT: "project_id",
            MemoryLane.RUN_STATE: "run_id",
        }[payload.lane]
        if payload.lane == MemoryLane.PROJECT and not payload.project_id:
            raise ValueError("project_id is required for PROJECT lane commits")
        if payload.lane == MemoryLane.RUN_STATE and not payload.run_id:
            raise ValueError("run_id is required for RUN_STATE lane commits")
        columns = ["id"]
        values: list[object] = [payload.id]
        if id_column == "project_id":
            columns.append("project_id")
            values.append(payload.project_id)
        if id_column == "run_id":
            columns.append("run_id")
            values.append(payload.run_id)
        columns.extend(["memory_key", "title", "content", "tags_json", "metadata_json", "created_at", "updated_at"])
        values.extend(
            [
                payload.key,
                payload.title,
                payload.content,
                compact_json(payload.tags),
                compact_json(payload.metadata),
                payload.created_at.isoformat(),
                payload.updated_at.isoformat(),
            ]
        )
        unique_target = {
            MemoryLane.METHOD: "(memory_key)",
            MemoryLane.STABLE_USER: "(memory_key)",
            MemoryLane.PROJECT: "(project_id, memory_key)",
            MemoryLane.RUN_STATE: "(run_id, memory_key)",
        }[payload.lane]
        with self.database.transaction() as connection:
            connection.execute(
                f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join('?' for _ in values)})
                ON CONFLICT {unique_target} DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                values,
            )
        self._upsert_retrieval_document(
            payload.lane,
            "memory",
            stable_ref,
            payload.title,
            payload.content,
            payload.tags,
            {
                "project_id": payload.project_id,
                "run_id": payload.run_id,
                **payload.metadata,
            },
        )
        return payload

    def get_method_memory(self, key: str) -> MemoryEntry:
        row = self.database.connection.execute(
            "SELECT * FROM method_memory WHERE memory_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown method memory key: {key}")
        return MemoryEntry(
            id=row["id"],
            lane=MemoryLane.METHOD,
            key=row["memory_key"],
            title=row["title"],
            content=row["content"],
            tags=_loads(row["tags_json"], []),
            metadata=_loads(row["metadata_json"], {}),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def retrieve(
        self,
        query: str,
        lanes: list[MemoryLane],
        limit: int = 8,
    ) -> list[RetrievalHit]:
        lane_values = [lane.value for lane in lanes]
        placeholders = ", ".join("?" for _ in lane_values)
        parameters: list[object] = []
        if query.strip():
            sanitized_query = " ".join(part for part in query.replace('"', " ").replace("'", " ").split() if part)
            parameters.extend([sanitized_query, *lane_values, limit])
            rows = self.database.connection.execute(
                f"""
                SELECT rd.lane, rd.document_type, rd.ref_id, rd.title, rd.content, rd.tags_json,
                       rd.metadata_json, bm25(retrieval_documents_fts) AS score
                FROM retrieval_documents_fts
                JOIN retrieval_documents rd ON rd.rowid = retrieval_documents_fts.rowid
                WHERE retrieval_documents_fts MATCH ?
                  AND rd.lane IN ({placeholders})
                ORDER BY score
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        else:
            parameters.extend([*lane_values, limit])
            rows = self.database.connection.execute(
                f"""
                SELECT lane, document_type, ref_id, title, content, tags_json, metadata_json, 0.0 AS score
                FROM retrieval_documents
                WHERE lane IN ({placeholders})
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return [
            RetrievalHit(
                lane=row["lane"],
                document_type=row["document_type"],
                ref_id=row["ref_id"],
                title=row["title"],
                content=row["content"],
                score=float(abs(row["score"])),
                tags=_loads(row["tags_json"], []),
                metadata=_loads(row["metadata_json"], {}),
            )
            for row in rows
        ]

    def list_memory_entries(
        self,
        lane: MemoryLane,
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> list[MemoryEntry]:
        table = {
            MemoryLane.METHOD: "method_memory",
            MemoryLane.STABLE_USER: "user_memory",
            MemoryLane.PROJECT: "project_memory",
            MemoryLane.RUN_STATE: "run_memory",
        }[lane]
        where = ""
        parameters: list[object] = []
        if lane == MemoryLane.PROJECT:
            where = "WHERE project_id = ?"
            parameters.append(project_id)
        if lane == MemoryLane.RUN_STATE:
            where = "WHERE run_id = ?"
            parameters.append(run_id)
        rows = self.database.connection.execute(
            f"SELECT * FROM {table} {where} ORDER BY updated_at DESC",
            parameters,
        ).fetchall()
        entries: list[MemoryEntry] = []
        for row in rows:
            entries.append(
                MemoryEntry(
                    id=row["id"],
                    lane=lane,
                    key=row["memory_key"],
                    title=row["title"],
                    content=row["content"],
                    tags=_loads(row["tags_json"], []),
                    metadata=_loads(row["metadata_json"], {}),
                    project_id=row["project_id"] if "project_id" in row.keys() else None,
                    run_id=row["run_id"] if "run_id" in row.keys() else None,
                    created_at=_parse_datetime(row["created_at"]),
                    updated_at=_parse_datetime(row["updated_at"]),
                )
            )
        return entries

    def record_export(self, manifest: ExportManifest, export_path: str) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO exports (id, run_id, export_format, export_path, manifest_json, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.export_id,
                    manifest.run_id,
                    manifest.export_format,
                    export_path,
                    compact_json(manifest.model_dump(mode="json")),
                    compact_json(manifest.checksums),
                    manifest.exported_at.isoformat(),
                ),
            )

    def record_dead_end(
        self,
        project_id: str | None,
        run_id: str | None,
        title: str,
        description: str,
        cause: str,
        learnings: list[str],
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        dead_end_id = self._new_id("dead_end")
        created_at = utc_now_iso()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO dead_ends (
                    id, project_id, run_id, title, description, cause, learnings_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dead_end_id,
                    project_id,
                    run_id,
                    title,
                    description,
                    cause,
                    compact_json(learnings),
                    compact_json(metadata or {}),
                    created_at,
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT if project_id else MemoryLane.RUN_STATE,
            "dead_end",
            dead_end_id,
            title,
            description,
            ["dead-end", cause],
            {"run_id": run_id, "project_id": project_id},
        )
        return {
            "id": dead_end_id,
            "project_id": project_id,
            "run_id": run_id,
            "title": title,
            "description": description,
            "cause": cause,
            "learnings": learnings,
            "metadata": metadata or {},
            "created_at": created_at,
        }

    def create_project_snapshot(
        self,
        project_id: str,
        run_id: str | None,
        title: str,
        summary: dict[str, object],
    ) -> dict[str, object]:
        snapshot_id = self._new_id("snapshot")
        created_at = utc_now_iso()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO project_snapshots (id, project_id, run_id, title, summary_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    project_id,
                    run_id,
                    title,
                    compact_json(summary),
                    created_at,
                ),
            )
        self._upsert_retrieval_document(
            MemoryLane.PROJECT,
            "project_snapshot",
            snapshot_id,
            title,
            json.dumps(summary, indent=2, sort_keys=True),
            ["project-snapshot"],
            {"project_id": project_id, "run_id": run_id},
        )
        return {
            "id": snapshot_id,
            "project_id": project_id,
            "run_id": run_id,
            "title": title,
            "summary": summary,
            "created_at": created_at,
        }

    def list_supersession_history(self, run_id: str) -> list[dict[str, object]]:
        rows = self.database.connection.execute(
            """
            SELECT id, entity_type, entity_id, superseded_by, reason, metadata_json, created_at
            FROM supersession_history
            WHERE run_id = ?
            ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "superseded_by": row["superseded_by"],
                "reason": row["reason"],
                "metadata": _loads(row["metadata_json"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def collect_run_context(self, run_id: str) -> dict[str, object]:
        run_state = self.get_run_state(run_id)
        project_id = run_state.metadata.project_id
        return {
            "run_state": run_state,
            "summary": self.get_run_summary(run_id),
            "events": self.list_visibility_events(run_id),
            "friction_logs": self.list_friction_logs(run_id),
            "sweeps": self.list_sweeps(run_id),
            "artifacts": self.list_artifacts(run_id),
            "source_objects": self.list_source_objects(run_id),
            "components": self.list_primitive_components(run_id),
            "state_variables": self.list_state_variables(run_id),
            "primitive_operators": self.list_primitive_operators(run_id),
            "interlocks": self.list_interlocks(run_id),
            "traces": self.list_trace_steps(run_id),
            "gaps": self.list_gap_records(run_id),
            "searches": self.list_search_records(run_id),
            "basins": self.list_basin_records(run_id),
            "skeptic_findings": self.list_skeptic_findings(run_id),
            "antipattern_findings": self.list_antipattern_findings(run_id),
            "anchors": self.list_anchors(project_id) if project_id else [],
            "tensions": self.list_tensions(project_id) if project_id else [],
            "hypotheses": self.list_hypotheses(project_id) if project_id else [],
            "discriminators": self.list_discriminators(project_id) if project_id else [],
            "constraints": self.list_constraints(project_id) if project_id else [],
            "supersessions": self.list_supersession_history(run_id),
            "typed_claims": self.list_typed_claims(run_id),
            "compliance": self.get_compliance_report(run_id),
        }
