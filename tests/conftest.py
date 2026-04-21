from __future__ import annotations

from pathlib import Path

import pytest

from psi_coprocessor_mcp.config import ServerSettings
from psi_coprocessor_mcp.db import Database
from psi_coprocessor_mcp.repository import Repository
from psi_coprocessor_mcp.service import PsiService


@pytest.fixture()
def settings(tmp_path: Path) -> ServerSettings:
    data_dir = tmp_path / "data"
    return ServerSettings(
        data_dir=data_dir,
        database_path=data_dir / "psi.sqlite3",
        export_dir=data_dir / "exports",
        default_durability_mode="blocking",
    )


@pytest.fixture()
def database(settings: ServerSettings):
    db = Database(settings)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def repository(database: Database) -> Repository:
    return Repository(database)


@pytest.fixture()
def service(repository: Repository, settings: ServerSettings) -> PsiService:
    return PsiService(repository, settings)
