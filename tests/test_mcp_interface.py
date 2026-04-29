from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

from psi_coprocessor_mcp.app import create_http_app
from psi_coprocessor_mcp.config import ServerSettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def _call_stdio(tmp_path: Path):
    env = os.environ | {"PSI_MCP_DATA_DIR": str(tmp_path / "stdio-data")}
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "psi_coprocessor_mcp", "stdio"],
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            templates = await session.list_resource_templates()
            prompts = await session.list_prompts()
            reflect = await session.call_tool(
                "psi.reflect",
                {"task": "Evaluate an ambiguous architecture change with no placeholders."},
            )
            run_id = reflect.structuredContent["run_id"]
            state = await session.call_tool("psi.run.get_state", {"run_id": run_id})
            explicit_run_id = "psi-stdio-explicit-20260429-001"
            explicit_started = await session.call_tool(
                "psi.run.start",
                {
                    "title": "Explicit stdio run",
                    "scope": "Create a caller-addressable PSI run through MCP.",
                    "run_id": explicit_run_id,
                },
            )
            explicit_state = await session.call_tool("psi.run.get_state", {"run_id": explicit_run_id})
            compliance_before = await session.read_resource(f"psi://run/{run_id}/compliance")
            summary_resource = await session.read_resource(f"psi://run/{run_id}/summary")
            compliance_after = await session.read_resource(f"psi://run/{run_id}/compliance")
            resource = await session.read_resource("psi://method/current")
            prompt = await session.get_prompt("start_psi_pass", {"task": "build the server"})
            return {
                "tool_names": [tool.name for tool in tools.tools],
                "resources": [str(resource.uri) for resource in resources.resources],
                "resource_templates": [template.uriTemplate for template in templates.resourceTemplates],
                "prompt_names": [prompt_item.name for prompt_item in prompts.prompts],
                "reflect": reflect.structuredContent,
                "state": state.structuredContent,
                "explicit_started": explicit_started.structuredContent,
                "explicit_state": explicit_state.structuredContent,
                "compliance_before_summary_read": json.loads(compliance_before.contents[0].text),
                "summary_resource": json.loads(summary_resource.contents[0].text),
                "compliance_after_summary_read": json.loads(compliance_after.contents[0].text),
                "resource_text": resource.contents[0].text,
                "prompt_messages": prompt.messages,
            }


def _pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def _call_http(tmp_path: Path):
    port = _pick_port()
    env = os.environ | {"PSI_MCP_DATA_DIR": str(tmp_path / "http-data")}
    process = subprocess.Popen(
        [sys.executable, "-m", "psi_coprocessor_mcp", "http", "--port", str(port)],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    await client.get(f"http://127.0.0.1:{port}/mcp")
                break
            except Exception:
                await asyncio.sleep(0.25)
        async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [tool.name for tool in tools.tools]
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.mark.asyncio
async def test_stdio_mcp_surface(tmp_path: Path):
    result = await _call_stdio(tmp_path)
    required_tools = {
        "psi.reflect",
        "psi.run.start",
        "psi.run.get_state",
        "psi.event.record",
        "psi.friction.type",
        "psi.sweep.run",
        "psi.anchor.register",
        "psi.anchor.invalidate",
        "psi.hypothesis.update",
        "psi.discriminator.record",
        "psi.transition.set",
        "psi.memory.retrieve",
        "psi.memory.commit",
        "psi.compliance.check",
        "psi.artifacts.sync",
        "psi.export.run",
        "psi.import.run",
        "psi.diff.analyze",
        "psi.test_failure.ingest",
        "psi.project.snapshot",
        "psi.dead_end.record",
        "psi.regime.explain",
        "psi.summary.generate",
        "psi.source.audit",
        "psi.structure.extract",
        "psi.trace.run",
        "psi.gap.analyze",
        "psi.search.plan",
        "psi.basin.generate",
        "psi.stress.run",
    }
    assert required_tools.issubset(set(result["tool_names"]))
    assert "psi://method/current" in set(result["resources"]) | set(result["resource_templates"])
    assert "psi://run/{run_id}/compliance" in set(result["resource_templates"])
    assert "psi://run/{run_id}/sources" in set(result["resource_templates"])
    assert "psi://run/{run_id}/traces" in set(result["resource_templates"])
    assert "start_psi_pass" in result["prompt_names"]
    assert result["reflect"]["run_id"]
    assert result["state"]["compact"]["run_id"] == result["reflect"]["run_id"]
    assert result["explicit_started"]["run_id"] == "psi-stdio-explicit-20260429-001"
    assert result["explicit_started"]["resumed"] is False
    assert result["explicit_state"]["compact"]["run_id"] == "psi-stdio-explicit-20260429-001"
    assert result["summary_resource"]["run_id"] == result["reflect"]["run_id"]
    assert result["compliance_after_summary_read"] == result["compliance_before_summary_read"]
    assert "Progressive Structural Illumination" in result["resource_text"]
    assert result["prompt_messages"]


@pytest.mark.asyncio
async def test_streamable_http_mcp_surface(tmp_path: Path):
    tools = await _call_http(tmp_path)
    assert "psi.reflect" in tools


def test_streamable_http_uses_configured_mount_path(tmp_path: Path):
    settings = ServerSettings(data_dir=tmp_path / "http-path-data", http_mount_path="/custom-mcp")
    app = create_http_app(settings)
    inner_app = app.routes[0].app

    assert [route.path for route in inner_app.routes] == ["/custom-mcp"]
