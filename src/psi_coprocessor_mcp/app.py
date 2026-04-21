"""FastMCP application wiring for PSI Coprocessor MCP."""

from __future__ import annotations

import contextlib
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from starlette.applications import Starlette
from starlette.routing import Mount

from .config import ServerSettings
from .db import Database
from .repository import Repository
from .service import PsiService
from .utils import canonical_json


@dataclass(slots=True)
class AppContext:
    settings: ServerSettings
    database: Database
    repository: Repository
    service: PsiService


def _ctx_service(ctx: Context) -> PsiService:
    return ctx.request_context.lifespan_context.service


def _parse_metadata(raw: str) -> dict[str, object]:
    if not raw.strip():
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid metadata_json: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ToolError("metadata_json must decode to an object")
    return loaded


def _block_on_durability(output: dict[str, object], block_on_poison: bool) -> None:
    durability = output.get("durability_assessment", {})
    compliance = output.get("compliance_report", {})
    if block_on_poison and (
        (isinstance(durability, dict) and durability.get("blocked"))
        or (isinstance(compliance, dict) and compliance.get("blocking"))
    ):
        raise ToolError(
            "PSI blocked the move because durability poison or a blocking compliance failure was detected."
        )


def _read_only_service(settings: ServerSettings) -> PsiService:
    database = Database(settings)
    repository = Repository(database)
    return PsiService(repository, settings)


def create_mcp(settings: ServerSettings | None = None) -> FastMCP:
    settings = settings or ServerSettings.from_env()

    @contextlib.asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
        database = Database(settings)
        repository = Repository(database)
        service = PsiService(repository, settings)
        try:
            yield AppContext(settings=settings, database=database, repository=repository, service=service)
        finally:
            database.close()

    mcp = FastMCP(
        name="PSI Coprocessor MCP",
        instructions=(
            "When a task involves ambiguity, hidden dependencies, contradiction, scope drift, architecture design, "
            "debugging dead ends, or revision of prior conclusions, call psi.reflect before finalizing a plan, patch, or design."
        ),
        lifespan=lifespan,
        stateless_http=True,
        json_response=True,
    )

    @mcp.tool(name="psi.reflect", description="Primary PSI cognitive augmentation pass.")
    def psi_reflect(
        ctx: Context,
        task: str,
        draft_answer: str = "",
        diff: str = "",
        project_id: str = "",
        project_name: str = "",
        run_id: str = "",
        attached_context: str = "",
        durability_mode: str = "",
        block_on_poison: bool = False,
    ) -> dict[str, object]:
        output = _ctx_service(ctx).reflect(
            task=task,
            draft_answer=draft_answer,
            diff=diff,
            project_id=project_id or None,
            project_name=project_name or None,
            run_id=run_id or None,
            attached_context=attached_context,
            durability_mode=durability_mode or None,
        )
        _block_on_durability(output, block_on_poison)
        return output

    @mcp.tool(name="psi.run.start", description="Create or resume a PSI run with explicit scope and mode.")
    def psi_run_start(
        ctx: Context,
        title: str,
        scope: str,
        mode: str = "survey",
        project_id: str = "",
        project_name: str = "",
        run_id: str = "",
        attached_context: str = "",
        durability_mode: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).start_run(
            title=title,
            scope=scope,
            mode=mode,
            project_id=project_id or None,
            project_name=project_name or None,
            run_id=run_id or None,
            attached_context=attached_context,
            durability_mode=durability_mode or None,
        )

    @mcp.tool(name="psi.run.get_state", description="Return current live PSI run-state in compact and full forms.")
    def psi_run_get_state(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).get_run_state(run_id)

    @mcp.tool(name="psi.event.record", description="Record a visibility event explicitly.")
    def psi_event_record(
        ctx: Context,
        run_id: str,
        event_type: str,
        title: str,
        description: str,
        source: str = "",
        severity: float = 0.5,
        evidence: list[str] | None = None,
    ) -> dict[str, object]:
        return _ctx_service(ctx).record_event(
            run_id=run_id,
            event_type=event_type,
            title=title,
            description=description,
            source=source,
            severity=severity,
            evidence=evidence,
        )

    @mcp.tool(name="psi.friction.type", description="Type friction against PSI categories and route to regimes.")
    def psi_friction_type(
        ctx: Context,
        text: str,
        run_id: str = "",
        project_id: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).friction_type(text=text, run_id=run_id or None, project_id=project_id or None)

    @mcp.tool(name="psi.sweep.run", description="Run a weighted coherence sweep with blast-radius estimation.")
    def psi_sweep_run(
        ctx: Context,
        run_id: str,
        changed_text: str = "",
        trigger_event_id: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).run_sweep(
            run_id=run_id,
            changed_text=changed_text,
            trigger_event_id=trigger_event_id or None,
        )

    @mcp.tool(name="psi.anchor.register", description="Register a durable anchor.")
    def psi_anchor_register(
        ctx: Context,
        name: str,
        description: str,
        project_id: str,
        run_id: str = "",
        centrality: float = 0.5,
        fragility: float = 0.5,
        confidence: str = "provisional",
        durability_class: str = "PROVISIONAL",
        rationale: str = "",
        dependencies: list[str] | None = None,
        implications: list[str] | None = None,
    ) -> dict[str, object]:
        return _ctx_service(ctx).register_anchor(
            name=name,
            description=description,
            project_id=project_id,
            run_id=run_id or None,
            centrality=centrality,
            fragility=fragility,
            confidence=confidence,
            durability_class=durability_class,
            rationale=rationale,
            dependencies=dependencies,
            implications=implications,
        )

    @mcp.tool(name="psi.anchor.invalidate", description="Invalidate or downgrade an anchor.")
    def psi_anchor_invalidate(
        ctx: Context,
        anchor_id: str,
        reason: str,
        run_id: str = "",
        project_id: str = "",
        invalidated_by: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).invalidate_anchor(
            anchor_id=anchor_id,
            reason=reason,
            run_id=run_id or None,
            project_id=project_id or None,
            invalidated_by=invalidated_by or None,
        )

    @mcp.tool(name="psi.hypothesis.update", description="Add, modify, or retire live hypotheses and tensions.")
    def psi_hypothesis_update(
        ctx: Context,
        item_type: str,
        action: str,
        title: str,
        description: str,
        project_id: str,
        run_id: str = "",
        confidence: str = "provisional",
        durability_class: str = "PROVISIONAL",
        severity: float = 0.5,
        preserves: list[str] | None = None,
        risks: list[str] | None = None,
        discriminators: list[str] | None = None,
        forces: list[str] | None = None,
    ) -> dict[str, object]:
        return _ctx_service(ctx).update_hypothesis(
            item_type=item_type,
            action=action,
            title=title,
            description=description,
            project_id=project_id,
            run_id=run_id or None,
            confidence=confidence,
            durability_class=durability_class,
            severity=severity,
            preserves=preserves,
            risks=risks,
            discriminators=discriminators,
            forces=forces,
        )

    @mcp.tool(name="psi.discriminator.record", description="Record the best current discriminator.")
    def psi_discriminator_record(
        ctx: Context,
        title: str,
        description: str,
        project_id: str,
        run_id: str = "",
        target: list[str] | None = None,
        best_next_probe: str = "",
        confidence_gain: float = 0.5,
    ) -> dict[str, object]:
        return _ctx_service(ctx).record_discriminator(
            title=title,
            description=description,
            project_id=project_id,
            run_id=run_id or None,
            target=target,
            best_next_probe=best_next_probe,
            confidence_gain=confidence_gain,
        )

    @mcp.tool(name="psi.transition.set", description="Set or recommend ANCHOR, ROLLBACK, RESCOPE, ESCALATE, CONTINUE, or HALT.")
    def psi_transition_set(
        ctx: Context,
        run_id: str,
        decision: str = "",
        rationale: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).set_transition(run_id=run_id, decision=decision or None, rationale=rationale)

    @mcp.tool(name="psi.memory.retrieve", description="Retrieve relevant method, user, project, or run context by typed lane.")
    def psi_memory_retrieve(
        ctx: Context,
        query: str = "",
        lanes: list[str] | None = None,
        limit: int = 8,
    ) -> dict[str, object]:
        return _ctx_service(ctx).retrieve_memory(query=query, lanes=lanes, limit=limit)

    @mcp.tool(name="psi.memory.commit", description="Commit durable results to the correct typed memory lane.")
    def psi_memory_commit(
        ctx: Context,
        lane: str,
        key: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        metadata_json: str = "{}",
        project_id: str = "",
        run_id: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).commit_memory(
            lane=lane,
            key=key,
            title=title,
            content=content,
            tags=tags,
            metadata=_parse_metadata(metadata_json),
            project_id=project_id or None,
            run_id=run_id or None,
        )

    @mcp.tool(name="psi.compliance.check", description="Run the PSI pre-emission compliance checker against the current run-state.")
    def psi_compliance_check(ctx: Context, run_id: str, action: str = "summary") -> dict[str, object]:
        return _ctx_service(ctx).check_compliance(run_id=run_id, action=action)

    @mcp.tool(name="psi.artifacts.sync", description="Regenerate artifacts from live run-state and ensure sync.")
    def psi_artifacts_sync(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).sync_artifacts(run_id)

    @mcp.tool(name="psi.export.run", description="Export the full run package.")
    def psi_export_run(ctx: Context, run_id: str, export_format: str = "both") -> dict[str, object]:
        return _ctx_service(ctx).export_run(run_id=run_id, export_format=export_format)

    @mcp.tool(name="psi.import.run", description="Import or reload a previously exported run package.")
    def psi_import_run(ctx: Context, import_path: str) -> dict[str, object]:
        return _ctx_service(ctx).import_run(import_path)

    @mcp.tool(name="psi.diff.analyze", description="Analyze a diff for local patch drift, durability risk, and field impact.")
    def psi_diff_analyze(
        ctx: Context,
        diff: str,
        task: str = "",
        run_id: str = "",
        project_id: str = "",
    ) -> dict[str, object]:
        return _ctx_service(ctx).diff_analyze(
            diff=diff,
            task=task,
            run_id=run_id or None,
            project_id=project_id or None,
        )

    @mcp.tool(name="psi.test_failure.ingest", description="Ingest a test failure as a visibility event and typed friction.")
    def psi_test_failure_ingest(ctx: Context, run_id: str, failure_log: str) -> dict[str, object]:
        return _ctx_service(ctx).ingest_test_failure(run_id=run_id, failure_log=failure_log)

    @mcp.tool(name="psi.project.snapshot", description="Capture a durable project snapshot.")
    def psi_project_snapshot(
        ctx: Context,
        project_id: str,
        run_id: str = "",
        title: str = "project snapshot",
    ) -> dict[str, object]:
        return _ctx_service(ctx).project_snapshot(project_id=project_id, run_id=run_id or None, title=title)

    @mcp.tool(name="psi.dead_end.record", description="Record a known dead end and what it taught.")
    def psi_dead_end_record(
        ctx: Context,
        title: str,
        description: str,
        cause: str,
        project_id: str = "",
        run_id: str = "",
        learnings: list[str] | None = None,
    ) -> dict[str, object]:
        return _ctx_service(ctx).record_dead_end(
            title=title,
            description=description,
            cause=cause,
            project_id=project_id or None,
            run_id=run_id or None,
            learnings=learnings,
        )

    @mcp.tool(name="psi.regime.explain", description="Explain the currently active PSI regime(s) or a named regime.")
    def psi_regime_explain(ctx: Context, regime: str = "", run_id: str = "") -> dict[str, object]:
        return _ctx_service(ctx).explain_regime(regime=regime or None, run_id=run_id or None)

    @mcp.tool(name="psi.summary.generate", description="Generate expert and plain-language summaries for the run.")
    def psi_summary_generate(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).generate_summary(run_id)

    @mcp.tool(name="psi.source.audit", description="Normalize source intake, duplicates, stale references, and canonical grounding for a run.")
    def psi_source_audit(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).source_audit(run_id)

    @mcp.tool(name="psi.structure.extract", description="Return the authoritative component, state-variable, operator, and interlock structures for a run.")
    def psi_structure_extract(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).structure_extract(run_id)

    @mcp.tool(name="psi.trace.run", description="Return the current forward trace/cascade surface for a run.")
    def psi_trace_run(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).trace_run(run_id)

    @mcp.tool(name="psi.gap.analyze", description="Return the current gap-origin and pressure analysis for a run.")
    def psi_gap_analyze(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).gap_analyze(run_id)

    @mcp.tool(name="psi.search.plan", description="Return the current targeted search plan for unresolved PSI objects.")
    def psi_search_plan(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).search_plan(run_id)

    @mcp.tool(name="psi.basin.generate", description="Return the current competing hypothesis basins for a run.")
    def psi_basin_generate(ctx: Context, run_id: str) -> dict[str, object]:
        return _ctx_service(ctx).basin_generate(run_id)

    @mcp.tool(name="psi.stress.run", description="Run the skeptic/anti-pattern stress pass and return compliance effects.")
    def psi_stress_run(ctx: Context, run_id: str, action: str = "summary") -> dict[str, object]:
        return _ctx_service(ctx).stress_run(run_id, action=action)

    @mcp.resource("psi://method/current", name="psi://method/current", mime_type="text/plain")
    def resource_method_current() -> str:
        service = _read_only_service(settings)
        try:
            return service.repository.get_method_memory("current").content
        finally:
            service.repository.database.close()

    @mcp.resource("psi://method/question-operators", name="psi://method/question-operators", mime_type="text/plain")
    def resource_method_question_operators() -> str:
        service = _read_only_service(settings)
        try:
            return service.repository.get_method_memory("question-operators").content
        finally:
            service.repository.database.close()

    @mcp.resource("psi://method/ai-contract", name="psi://method/ai-contract", mime_type="text/plain")
    def resource_method_ai_contract() -> str:
        service = _read_only_service(settings)
        try:
            return service.repository.get_method_memory("ai-contract").content
        finally:
            service.repository.database.close()

    @mcp.resource("psi://method/normalization-map", name="psi://method/normalization-map", mime_type="text/plain")
    def resource_method_normalization_map() -> str:
        service = _read_only_service(settings)
        try:
            return service.repository.get_method_memory("normalization-map").content
        finally:
            service.repository.database.close()

    @mcp.resource("psi://method/control-families", name="psi://method/control-families", mime_type="application/json")
    def resource_method_control_families() -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.explain_regime()["control_families"])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://method/mode-profiles", name="psi://method/mode-profiles", mime_type="application/json")
    def resource_method_mode_profiles() -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.explain_regime()["mode_profiles"])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://project/{project_id}/summary", mime_type="application/json")
    def resource_project_summary(project_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.repository.get_project_summary(project_id).model_dump(mode="json"))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://project/{project_id}/anchors", mime_type="application/json")
    def resource_project_anchors(project_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json([anchor.model_dump(mode="json") for anchor in service.repository.list_anchors(project_id)])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://project/{project_id}/tensions", mime_type="application/json")
    def resource_project_tensions(project_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json([tension.model_dump(mode="json") for tension in service.repository.list_tensions(project_id)])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://project/{project_id}/constraints", mime_type="application/json")
    def resource_project_constraints(project_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json([constraint.model_dump(mode="json") for constraint in service.repository.list_constraints(project_id)])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/state", mime_type="application/json")
    def resource_run_state(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.get_run_state(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/sources", mime_type="application/json")
    def resource_run_sources(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.source_audit(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/components", mime_type="application/json")
    def resource_run_components(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.structure_extract(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/interlocks", mime_type="application/json")
    def resource_run_interlocks(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.structure_extract(run_id)["interlocks"])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/traces", mime_type="application/json")
    def resource_run_traces(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.trace_run(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/gaps", mime_type="application/json")
    def resource_run_gaps(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.gap_analyze(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/stress", mime_type="application/json")
    def resource_run_stress(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.stress_run(run_id, action="summary"))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/events", mime_type="application/json")
    def resource_run_events(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json([event.model_dump(mode="json") for event in service.repository.list_visibility_events(run_id)])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/sweeps", mime_type="application/json")
    def resource_run_sweeps(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.repository.list_sweeps(run_id))
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/artifacts", mime_type="application/json")
    def resource_run_artifacts(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            artifacts = service.repository.list_artifacts(run_id)
            return canonical_json(
                [
                    {
                        "artifact_type": artifact.artifact_type.value,
                        "checksum": artifact.checksum,
                        "format": artifact.format,
                        "authoritative": artifact.authoritative,
                    }
                    for artifact in artifacts
                ]
            )
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/claims", mime_type="application/json")
    def resource_run_claims(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json([claim.model_dump(mode="json") for claim in service.repository.list_typed_claims(run_id)])
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/compliance", mime_type="application/json")
    def resource_run_compliance(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            report = service.repository.get_compliance_report(run_id)
            return canonical_json(report.model_dump(mode="json") if report else {})
        finally:
            service.repository.database.close()

    @mcp.resource("psi://run/{run_id}/summary", mime_type="application/json")
    def resource_run_summary(run_id: str) -> str:
        service = _read_only_service(settings)
        try:
            return canonical_json(service.generate_summary(run_id))
        finally:
            service.repository.database.close()

    @mcp.prompt(name="start_psi_pass", description="Start a PSI-guided pass for a new task.")
    def prompt_start_psi_pass(task: str, mode: str = "construction", project_id: str = "") -> str:
        return (
            f"Start a PSI pass in {mode} mode.\n"
            f"Task: {task}\n"
            f"Project ID: {project_id or '[new project or ad hoc run]'}\n"
            "Before proposing a plan or patch, call psi.run.start and psi.reflect."
        )

    @mcp.prompt(name="resume_psi_pass", description="Resume an existing PSI run.")
    def prompt_resume_psi_pass(run_id: str) -> str:
        return (
            f"Resume PSI run {run_id}.\n"
            "Call psi.run.get_state, inspect unresolved tensions, then call psi.reflect before finalizing the next move."
        )

    @mcp.prompt(name="run_visibility_event", description="Record or process a visibility event.")
    def prompt_run_visibility_event(run_id: str, event_description: str) -> str:
        return (
            f"Visibility event for run {run_id}: {event_description}\n"
            "Call psi.event.record, then psi.sweep.run if the event changes accepted structure."
        )

    @mcp.prompt(name="run_coherence_sweep", description="Run a weighted whole-field coherence sweep.")
    def prompt_run_coherence_sweep(run_id: str, changed_text: str = "") -> str:
        return (
            f"Run a weighted coherence sweep for {run_id}.\n"
            f"Changed text: {changed_text or '[use current run-state event]'}\n"
            "Prioritize blast radius by centrality, fragility, dependency density, timescale proximity, substrate coupling, and durability relevance."
        )

    @mcp.prompt(name="run_audit_pass", description="Run a PSI audit pass against an existing draft or design.")
    def prompt_run_audit_pass(task: str, draft_answer: str = "") -> str:
        return (
            f"Audit the following work under PSI:\nTask: {task}\nDraft: {draft_answer}\n"
            "Call psi.reflect, preserve live tensions, run psi.compliance.check before stabilizing output, and do not smooth over continuity poison."
        )

    @mcp.prompt(name="run_construction_pass", description="Run a PSI construction pass that builds from obligations and constraints.")
    def prompt_run_construction_pass(task: str, project_id: str = "") -> str:
        return (
            f"Construct under PSI for task: {task}\nProject ID: {project_id or '[optional]'}\n"
            "Use psi.reflect before finalizing a design, then sync artifacts if the run stabilizes."
        )

    @mcp.prompt(name="prepare_transition_decision", description="Prepare a transition decision under PSI.")
    def prompt_prepare_transition_decision(run_id: str) -> str:
        return (
            f"Prepare the next transition for run {run_id}.\n"
            "Inspect run-state, strongest tension, current discriminator, and durability gate before selecting ANCHOR, ROLLBACK, RESCOPE, ESCALATE, CONTINUE, or HALT."
        )

    @mcp.prompt(name="prepare_halt_decision", description="Prepare a halt decision under PSI.")
    def prompt_prepare_halt_decision(run_id: str) -> str:
        return (
            f"Evaluate whether run {run_id} can HALT.\n"
            "Only halt if no category-breaking failures remain, remaining gaps are correctly classified, the scope boundary is explicit, no known-bad continuity survives, and psi.compliance.check does not block."
        )

    return mcp


def create_http_app(settings: ServerSettings | None = None) -> Starlette:
    mcp = create_mcp(settings)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        async with contextlib.AsyncExitStack() as stack:
            await stack.enter_async_context(mcp.session_manager.run())
            yield

    return Starlette(routes=[Mount("/", mcp.streamable_http_app())], lifespan=lifespan)
