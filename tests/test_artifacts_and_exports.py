from __future__ import annotations

import json
from pathlib import Path

from psi_coprocessor_mcp.config import ServerSettings
from psi_coprocessor_mcp.db import Database
from psi_coprocessor_mcp.models import MemoryLane
from psi_coprocessor_mcp.repository import Repository
from psi_coprocessor_mcp.service import PsiService


def test_artifact_sync_generates_full_bundle(service, repository):
    result = service.reflect(
        task="Build a durable MCP server with artifact sync and explicit run-state.",
        attached_context="Source note: preserve the source artifact register with explicit provenance.",
        project_name="Artifact Project",
    )
    synced = service.sync_artifacts(result["run_id"])
    assert len(synced["artifacts"]) == 21
    artifact_types = {artifact["artifact_type"] for artifact in synced["artifacts"]}
    assert "field_state_register" in artifact_types
    stored = repository.list_artifacts(result["run_id"])
    assert len(stored) == 21
    state = service.get_run_state(result["run_id"])
    assert state["compact"]["open_artifacts"] == []
    source_register = next(item for item in stored if item.artifact_type.value == "source_register")
    component_ledger = next(item for item in stored if item.artifact_type.value == "component_ledger")
    trace_ledger = next(item for item in stored if item.artifact_type.value == "trace_ledger")
    assert "source-register" in source_register.content
    assert "task:" in source_register.content or "context:" in source_register.content
    assert source_register.authoritative is True
    assert component_ledger.authoritative is True
    assert trace_ledger.authoritative is True


def test_export_import_round_trip(service, settings):
    result = service.reflect(
        task="Track export and import of a PSI run with anchors, memory, and artifacts.",
        project_name="Export Project",
    )
    run_id = result["run_id"]
    project_id = result["project_id"]
    service.register_anchor(
        name="durability gate",
        description="Durability gate must remain blocking by default.",
        project_id=project_id,
        run_id=run_id,
        centrality=0.95,
        fragility=0.75,
    )
    service.commit_memory(
        lane="project",
        key="export-note",
        title="Export note",
        content="Round-trip should preserve project memory.",
        project_id=project_id,
    )
    service.sync_artifacts(run_id)
    exported = service.export_run(run_id)
    bundle = json.loads((Path(exported["export_path"]) / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["typed_claims"]
    assert bundle["compliance"]["status"] in {"PASS", "WARN", "BLOCKED"}
    assert bundle["source_objects"]
    assert bundle["components"]
    assert bundle["state_variables"]
    assert bundle["primitive_operators"]
    assert bundle["interlocks"]
    assert bundle["traces"]
    assert bundle["gaps"] is not None
    assert bundle["search_records"] is not None
    assert bundle["basins"]
    assert bundle["skeptic_findings"] is not None
    assert bundle["antipattern_findings"] is not None
    assert bundle["machine_readable_run_state"]["psi_run"]["metadata"]["schema_version"] == "1.2.0"
    assert bundle["machine_readable_run_state"]["psi_run"]["metadata"]["run_class"] in {"exploratory", "working", "canonical"}
    assert bundle["machine_readable_run_state"]["psi_run"]["state"]["current_phase"]

    import_settings = ServerSettings(
        data_dir=settings.data_dir.parent / "imported",
        database_path=settings.data_dir.parent / "imported" / "psi.sqlite3",
        export_dir=settings.data_dir.parent / "imported" / "exports",
    )
    import_db = Database(import_settings)
    try:
        import_repo = Repository(import_db)
        import_service = PsiService(import_repo, import_settings)
        imported = import_service.import_run(str(Path(exported["export_path"]) / "bundle.json"))
        assert imported["run_id"] == run_id
        imported_state = import_service.get_run_state(run_id)
        assert imported_state["compact"]["project_id"] == project_id
        imported_artifacts = import_repo.list_artifacts(run_id)
        assert len(imported_artifacts) == 21
        imported_sources = import_repo.list_source_objects(run_id)
        assert imported_sources
        assert import_repo.list_primitive_components(run_id)
        assert import_repo.list_interlocks(run_id)
        assert import_repo.list_trace_steps(run_id)
        assert import_repo.list_basin_records(run_id)
        imported_project_memory = import_repo.list_memory_entries(
            lane=MemoryLane.PROJECT,
            project_id=project_id,
        )
        assert any(entry.key == "export-note" for entry in imported_project_memory)
    finally:
        import_db.close()
