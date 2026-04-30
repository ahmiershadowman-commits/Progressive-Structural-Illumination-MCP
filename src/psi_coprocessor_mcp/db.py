"""SQLite connection and migration helpers."""

from __future__ import annotations

import logging
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import resources
from pathlib import Path

from .config import ServerSettings
from .seed import iter_seed_rows
from .utils import compact_json, utc_now_iso

logger = logging.getLogger("psi_coprocessor_mcp")

MIGRATIONS = [
    "0001_core.sql",
    "0002_retrieval_fts.sql",
    "0003_indexes.sql",
    "0004_rubric_integration.sql",
    "0005_methodology_ontology.sql",
    "0006_control_surface.sql",
]


def connect_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def apply_migrations(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    applied = {
        row["version"]
        for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    for filename in MIGRATIONS:
        if filename in applied:
            continue
        sql = resources.files("psi_coprocessor_mcp").joinpath("migrations", filename).read_text(
            encoding="utf-8"
        )
        with connection:
            connection.executescript(sql)
            connection.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (filename, utc_now_iso()),
            )


def seed_builtin_memory(connection: sqlite3.Connection, settings: ServerSettings) -> None:
    timestamp = utc_now_iso()
    rows_to_seed = list(iter_seed_rows(settings.enable_seed_user_lane))
    with connection:
        for lane, rows in rows_to_seed:
            for row in rows:
                if lane == "method":
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO method_memory (
                            id, memory_key, title, content, tags_json, metadata_json, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"method::{row['key']}",
                            row["key"],
                            row["title"],
                            row["content"],
                            compact_json(row["tags"]),
                            compact_json(row["metadata"]),
                            timestamp,
                            timestamp,
                        ),
                    )
                if lane == "user":
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO user_memory (
                            id, memory_key, title, content, tags_json, metadata_json, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"user::{row['key']}",
                            row["key"],
                            row["title"],
                            row["content"],
                            compact_json(row["tags"]),
                            compact_json(row["metadata"]),
                            timestamp,
                            timestamp,
                        ),
                    )


class Database:
    """Thin database wrapper with transactional helpers."""

    def __init__(self, settings: ServerSettings):
        self.settings = settings
        self.settings.ensure_directories()
        if self.settings.database_path is None:
            raise RuntimeError("ServerSettings.database_path must be initialized before connecting")
        self.connection = connect_database(self.settings.database_path)
        apply_migrations(self.connection)
        seed_builtin_memory(self.connection, settings)
        self._lock = threading.RLock()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                logger.exception("Database transaction failed, rolling back")
                self.connection.rollback()
                raise

    def execute(self, sql: str, parameters: tuple[object, ...] | None = None) -> sqlite3.Cursor:
        """Execute SQL with thread-safety lock."""
        with self._lock:
            if parameters is not None:
                return self.connection.execute(sql, parameters)
            return self.connection.execute(sql)

    def close(self) -> None:
        self.connection.close()
