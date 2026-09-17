"""The MCP server exposes the same engine; `would_break` never touches the repo."""

from __future__ import annotations

import pathlib

import pytest

pytest.importorskip("mcp")

from agent_assurance import mcp_server

REPOS = pathlib.Path(__file__).resolve().parents[1] / "examples" / "repos"
KEPT = str(REPOS / "mcp-promise-kept")


def test_scan_tool_returns_report():
    out = mcp_server.scan(KEPT)
    assert "AA-002" in out and "Promise kept" in out


def test_would_break_with_a_write_server():
    before = (pathlib.Path(KEPT) / ".mcp.json").read_text(encoding="utf-8")
    out = mcp_server.would_break(
        KEPT,
        mcp_server_name="github",
        mcp_server={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
    )
    assert out.startswith("**WOULD BREAK THE PROMISE**")
    assert "github.write" in out
    # nothing written to the real repo
    assert (pathlib.Path(KEPT) / ".mcp.json").read_text(encoding="utf-8") == before


def test_would_break_with_a_read_only_server_is_safe():
    out = mcp_server.would_break(
        KEPT, mcp_server_name="sentry", mcp_server={"command": "uvx", "args": ["mcp-server-sentry"]}
    )
    assert out.startswith("**would stretch the promise")
    assert "WOULD BREAK" not in out


def test_would_break_with_claude_permission():
    out = mcp_server.would_break(KEPT, claude_permission="Bash(*)", claude_permission_mode="allow")
    assert out.startswith("**WOULD BREAK THE PROMISE**")


@pytest.mark.anyio
async def test_tools_are_registered():
    tools = await mcp_server.server.list_tools()
    assert {t.name for t in tools} == {"scan", "check", "would_break"}
