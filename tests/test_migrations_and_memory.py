from __future__ import annotations

import sqlite3

from psi_coprocessor_mcp.config import ServerSettings
from psi_coprocessor_mcp.models import MemoryLane


def test_migrations_apply_and_seed_memory(database: sqlite3.Connection, repository):
    migration_count = database.connection.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()["count"]
    assert migration_count == 6
    method = repository.get_method_memory("current")
    assert "visibility events" in method.content
    normalization = repository.get_method_memory("normalization-map")
    assert "confidence from durability" in normalization.content
    retrieval = repository.retrieve("durability", [MemoryLane.METHOD, MemoryLane.STABLE_USER], limit=5)
    assert retrieval
    assert any(hit.lane in {MemoryLane.METHOD, MemoryLane.STABLE_USER} for hit in retrieval)


def test_memory_commit_and_retrieve(repository, service):
    started = service.start_run(title="Memory", scope="Track durable constraints", project_name="Memory Project")
    project_id = started["project_id"]
    run_id = started["run_id"]

    service.commit_memory(
        lane="project",
        key="constraints",
        title="Project constraints",
        content="SQLite and typed persistence are non-negotiable.",
        tags=["constraints", "sqlite"],
        project_id=project_id,
    )
    service.commit_memory(
        lane="run_state",
        key="probe",
        title="Current probe",
        content="Check blast radius before accepting the patch.",
        tags=["probe"],
        run_id=run_id,
    )

    hits = service.retrieve_memory("blast radius", lanes=["project", "run_state"], limit=10)["hits"]
    assert len(hits) >= 1
    assert any("blast radius" in hit["content"].lower() or "constraints" in hit["title"].lower() for hit in hits)


def test_typed_claims_and_compliance_are_persisted(repository, service):
    result = service.reflect(
        task="We must preserve whole-field propagation and keep confidence separate from durability.",
        project_name="Claims Project",
    )
    claims = repository.list_typed_claims(result["run_id"])
    assert claims
    assert any(claim.load_bearing for claim in claims)
    assert all(claim.confidence_axes.evidence_confidence.value for claim in claims)
    compliance = repository.get_compliance_report(result["run_id"])
    assert compliance is not None
    assert compliance.status in {"PASS", "WARN", "BLOCKED"}


def test_source_objects_are_persisted(repository, service):
    result = service.reflect(
        task="Audit the architecture boundary.",
        attached_context="Spec excerpt: the source artifact defines the current boundary.",
        project_name="Source Project",
    )
    source_objects = repository.list_source_objects(result["run_id"])
    assert source_objects
    assert any(source.source_kind.value == "task" for source in source_objects)
    assert any(source.source_kind.value == "context" for source in source_objects)


def test_settings_expand_windows_style_env_paths(monkeypatch, tmp_path):
    local_app_data = tmp_path / "localappdata"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("PSI_MCP_DATA_DIR", r"%LOCALAPPDATA%\psi-coprocessor-mcp")
    monkeypatch.delenv("PSI_MCP_DB_PATH", raising=False)
    monkeypatch.delenv("PSI_MCP_EXPORT_DIR", raising=False)

    settings = ServerSettings.from_env()

    assert settings.data_dir == local_app_data / "psi-coprocessor-mcp"
    assert settings.database_path == settings.data_dir / "psi.sqlite3"
    assert settings.export_dir == settings.data_dir / "exports"


def test_parse_datetime_raises_on_null():
    from psi_coprocessor_mcp.repository import _parse_datetime
    import pytest

    with pytest.raises(ValueError, match="Timestamp cannot be None or empty"):
        _parse_datetime(None)

    with pytest.raises(ValueError, match="Timestamp cannot be None or empty"):
        _parse_datetime("")


def test_parse_datetime_ensures_aware():
    from psi_coprocessor_mcp.repository import _parse_datetime
    from datetime import UTC

    # Naive datetime should get UTC timezone
    dt = _parse_datetime("2023-10-01T12:00:00")
    assert dt.tzinfo is UTC

    # Aware datetime should keep its timezone
    dt = _parse_datetime("2023-10-01T12:00:00+05:00")
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == 18000



