"""CLI entrypoints for PSI Coprocessor MCP."""

from __future__ import annotations

import argparse
import json

import uvicorn

from .app import create_http_app, create_mcp
from .config import ServerSettings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="psi-coprocessor-mcp")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stdio", help="Run the server over stdio.")

    http_parser = subparsers.add_parser("http", help="Run the server over streamable HTTP.")
    http_parser.add_argument("--host", default=None)
    http_parser.add_argument("--port", type=int, default=None)

    subparsers.add_parser("diagnose", help="Print effective local configuration.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    settings = ServerSettings.from_env()

    if args.command == "stdio":
        create_mcp(settings).run(transport="stdio")
        return 0
    if args.command == "http":
        app = create_http_app(settings)
        uvicorn.run(
            app,
            host=args.host or settings.http_host,
            port=args.port or settings.http_port,
            log_level=settings.log_level.lower(),
        )
        return 0
    if args.command == "diagnose":
        print(
            json.dumps(
                {
                    "data_dir": str(settings.data_dir),
                    "database_path": str(settings.database_path),
                    "export_dir": str(settings.export_dir),
                    "default_durability_mode": settings.default_durability_mode,
                    "http_host": settings.http_host,
                    "http_port": settings.http_port,
                    "http_mount_path": settings.http_mount_path,
                    "log_level": settings.log_level,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2
