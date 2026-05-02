"""Configuration for the PSI Coprocessor MCP server."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("psi_coprocessor_mcp")


def _expand_path(value: str | os.PathLike[str]) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(str(value))))


def _default_data_dir() -> Path:
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return _expand_path(local_app_data) / "psi-coprocessor-mcp"
    return Path.home() / ".psi-coprocessor-mcp"


@dataclass(slots=True)
class ServerSettings:
    """Runtime settings for the local server."""

    data_dir: Path = field(default_factory=_default_data_dir)
    database_path: Path | None = None
    export_dir: Path | None = None
    default_durability_mode: str = "blocking"
    http_host: str = "127.0.0.1"
    http_port: int = 8765
    http_mount_path: str = "/mcp"
    log_level: str = "INFO"
    enable_seed_user_lane: bool = True

    def __post_init__(self) -> None:
        if self.database_path is None:
            self.database_path = self.data_dir / "psi.sqlite3"
        if self.export_dir is None:
            self.export_dir = self.data_dir / "exports"
        if not self.http_mount_path:
            self.http_mount_path = "/mcp"
        if not self.http_mount_path.startswith("/"):
            self.http_mount_path = f"/{self.http_mount_path}"
        if len(self.http_mount_path) > 1:
            self.http_mount_path = self.http_mount_path.rstrip("/")

    @classmethod
    def from_env(cls) -> "ServerSettings":
        data_dir = _expand_path(os.getenv("PSI_MCP_DATA_DIR", _default_data_dir()))
        database_path = _expand_path(os.getenv("PSI_MCP_DB_PATH", data_dir / "psi.sqlite3"))
        export_dir = _expand_path(os.getenv("PSI_MCP_EXPORT_DIR", data_dir / "exports"))
        default_durability_mode = os.getenv("PSI_MCP_DURABILITY_MODE", "blocking").lower()
        if default_durability_mode not in {"blocking", "advisory"}:
            raise ValueError(
                f"PSI_MCP_DURABILITY_MODE must be 'blocking' or 'advisory'; got {default_durability_mode!r}"
            )
        http_host = os.getenv("PSI_MCP_HTTP_HOST", "127.0.0.1")
        if http_host not in {"127.0.0.1", "localhost", "::1", "[::1]"}:
            logger.warning(
                "PSI_MCP_HTTP_HOST is set to %r — server will be reachable on non-loopback interfaces.",
                http_host,
            )
        _raw_port = os.getenv("PSI_MCP_HTTP_PORT", "8765")
        try:
            http_port = int(_raw_port)
        except ValueError as exc:
            logger.error("Invalid PSI_MCP_HTTP_PORT: %s", _raw_port)
            raise ValueError(
                f"PSI_MCP_HTTP_PORT must be an integer; got {_raw_port!r}"
            ) from exc
        http_mount_path = os.getenv("PSI_MCP_HTTP_PATH", "/mcp")
        log_level = os.getenv("PSI_MCP_LOG_LEVEL", "INFO").upper()
        enable_seed_user_lane = os.getenv("PSI_MCP_SEED_USER_LANE", "true").lower() not in {
            "0",
            "false",
            "no",
        }
        return cls(
            data_dir=data_dir,
            database_path=database_path,
            export_dir=export_dir,
            default_durability_mode=default_durability_mode,
            http_host=http_host,
            http_port=http_port,
            http_mount_path=http_mount_path,
            log_level=log_level,
            enable_seed_user_lane=enable_seed_user_lane,
        )

    def ensure_directories(self) -> None:
        if self.database_path is None or self.export_dir is None:
            raise RuntimeError("ServerSettings paths must be initialized before creating directories")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
