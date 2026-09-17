"""Scanner for project-scoped MCP server configuration files.

The same shape is used by several hosts, so one scanner covers all of them
(formats as documented by each vendor, read on 2026-09-17):

    .mcp.json              Claude Code      {"mcpServers": {...}}
    .cursor/mcp.json       Cursor           {"mcpServers": {...}}   cursor.com/docs/mcp
    .gemini/settings.json  Gemini CLI       {"mcpServers": {...}}   geminicli.com/docs/tools/mcp-server
    .vscode/mcp.json       VS Code/Copilot  {"servers": {...}}      code.visualstudio.com/docs/agents/reference/mcp-configuration

Each server entry is either local ({"command", "args", "env"}) or remote
({"type": "http"|"sse", "url", "headers"}).

What can be known without running anything:
- the server exists (-> a system the agent can reach);
- its package/command (-> catalogue lookup for the access classes);
- whether it is remote (`url`) -> network egress to that host;
- whether env/headers carry credential-looking names -> credential access.
  Only the *name* of the variable is inspected, never its value.

Anything not in the catalogue is reported as UNKNOWN with its path:line.
"""

from __future__ import annotations

import json
import os
import re

from ..manifest import DataClass, DataSource, Tool, ToolAccess
from . import catalog
from .base import Observation, Scanner, Source

# (relative path, kind label, top-level key holding the servers)
FILES: tuple[tuple[str, str, str], ...] = (
    (".mcp.json", "mcp.json (Claude Code)", "mcpServers"),
    (".cursor/mcp.json", "cursor-mcp", "mcpServers"),
    (".gemini/settings.json", "gemini-cli-settings", "mcpServers"),
    (".vscode/mcp.json", "vscode-mcp", "servers"),
)
_CRED_RE = re.compile(r"(token|secret|key|password|passwd|credential|auth)", re.IGNORECASE)


def _line_of_server(text: str, name: str, block_key: str) -> int:
    """Line number of the `"<name>":` key inside the servers block (1 if not found)."""
    key = re.compile(r'^\s*"' + re.escape(name) + r'"\s*:')
    seen_block = False
    for i, line in enumerate(text.splitlines(), start=1):
        if f'"{block_key}"' in line:
            seen_block = True
            continue
        if seen_block and key.match(line):
            return i
    return 1


def observe_servers(servers: dict, rel_path: str, obs: Observation, line_of) -> None:
    """Shared by every MCP config format: classify each server entry.

    `servers` maps name -> spec ({command,args,env} or {url,headers}).
    `line_of(name)` returns the line where the entry starts.
    """
    notes: list[str] = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        line = line_of(name)
        where = f"{rel_path}:{line}"
        command_line = " ".join(
            [str(spec.get("command", ""))]
            + [str(a) for a in spec.get("args", []) or []]
            + [str(spec.get("url", ""))]
        )
        entry = catalog.lookup(name, command_line)

        if entry is None:
            obs.tools.append(
                Tool(name=f"{name}.*", type=ToolAccess.UNKNOWN, system=name, source=where)
            )
            obs.unknowns.append(name)
            notes.append(f"{name}: not in catalogue -> UNKNOWN")
        else:
            for cap in entry.capabilities:
                obs.tools.append(
                    Tool(
                        name=f"{name}.{cap.suffix}",
                        type=cap.access,
                        system=entry.system,
                        irreversible=cap.irreversible,
                        source=where,
                    )
                )
            for dc in entry.data:
                obs.data.append(DataSource(type=dc, systems=[entry.system], source=where))
            classes = sorted({c.access.value for c in entry.capabilities})
            notes.append(f"{name}: {entry.system} ({', '.join(classes)})")

        # Remote transport = the agent talks to an external host.
        if spec.get("url"):
            obs.tools.append(
                Tool(
                    name=f"{name}.remote",
                    type=ToolAccess.EXTERNAL_SEND,
                    system=entry.system if entry else name,
                    source=where,
                )
            )

        # Credential-looking env/header names -> the agent holds a secret
        # for this system. The value is never read.
        names = list((spec.get("env") or {}).keys()) + list((spec.get("headers") or {}).keys())
        if any(_CRED_RE.search(str(n)) for n in names):
            obs.data.append(
                DataSource(
                    type=DataClass.CREDENTIAL,
                    systems=[entry.system if entry else name],
                    source=where,
                )
            )
        obs.source.note = "; ".join(notes) if notes else "no servers"

class McpJsonScanner(Scanner):
    kind = "mcp-config"

    def detect(self, root: str) -> list[str]:
        return [rel for rel, _, _ in FILES if os.path.isfile(os.path.join(root, rel))]

    def parse(self, root: str, rel_path: str) -> Observation:
        kind, block_key = next((k, b) for rel, k, b in FILES if rel == rel_path)
        path = os.path.join(root, rel_path)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        source = Source(path=rel_path, kind=kind, supported=True)
        obs = Observation(source=source)

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            source.supported = False
            source.note = f"invalid JSON: {exc.msg} (line {exc.lineno})"
            return obs

        servers = raw.get(block_key) if isinstance(raw, dict) else None
        if not isinstance(servers, dict):
            source.note = f"no {block_key} block"
            return obs

        observe_servers(servers, rel_path, obs, lambda n: _line_of_server(text, n, block_key))
        return obs
