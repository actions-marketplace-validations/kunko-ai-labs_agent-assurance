"""Scanner for serialized agent tool definitions (business agents, not only
coding agents): OpenAI function tools, OpenAI Agents SDK, MCP tool objects,
Claude client tools, LangChain / LangGraph / CrewAI serialized metadata, or a
plain `tools:` list.

Where it looks: `agent-tools.json|yaml|yml` at the repo root, plus any path
listed under `tool_definition_files` in the organisation policy. Nothing is
imported or executed; only the serialized metadata is read.

Recognised tool shapes (any of):
  {"type": "function", "function": {"name", "description", "parameters"}}   OpenAI
  {"name", "description", "parameters" | "params_json_schema"}              OpenAI / Agents SDK
  {"name", "inputSchema"}                                                    MCP
  {"name", "input_schema"}                                                   Claude
  {"name", "args_schema" | "tool_call_schema"}                               LangChain / CrewAI

Classification: a tool definition carries a name and a description, not an
access class. The class is *inferred* from verbs in the name (then the
description) with the table below, and every such tool is marked
`inferred=True`: it scores like its class, but AA-002 reports an undeclared
inferred class as *review*, never as *broken* — a guess must not fail a build.
Anything the table does not match is UNKNOWN.
"""

from __future__ import annotations

import json
import os
import re

import yaml

from .. import policy
from ..manifest import Tool, ToolAccess
from .base import Observation, Scanner, Source

FILES = ("agent-tools.json", "agent-tools.yaml", "agent-tools.yml")

# Order matters: the first class whose verb matches wins.
_VERBS: list[tuple[ToolAccess, tuple[str, ...]]] = [
    (ToolAccess.FINANCIAL, ("pay", "refund", "transfer", "charge", "invoice", "payout", "purchase", "wire")),
    (ToolAccess.DELETE, ("delete", "remove", "drop", "destroy", "purge", "erase")),
    (ToolAccess.EXTERNAL_SEND, ("send", "email", "notify", "post_message", "publish", "tweet", "sms", "message")),
    (ToolAccess.EXECUTE, ("exec", "execute", "run", "shell", "command", "bash", "deploy")),
    (ToolAccess.WRITE, ("create", "update", "write", "insert", "upsert", "edit", "set", "modify", "push", "commit", "add", "save", "put", "patch")),
    (ToolAccess.READ, ("get", "list", "read", "search", "fetch", "query", "find", "lookup", "describe", "retrieve", "show", "view", "check")),
]


def classify(name: str, description: str = "") -> ToolAccess:
    tokens = set(re.split(r"[^a-z0-9]+", name.lower()))
    for access, verbs in _VERBS:
        if tokens & set(verbs):
            return access
    words = set(re.split(r"[^a-z0-9]+", description.lower()))
    for access, verbs in _VERBS:
        if words & set(verbs):
            return access
    return ToolAccess.UNKNOWN


def _tools_in(raw) -> list[dict]:
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("tools") or raw.get("functions") or []
    else:
        items = []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if it.get("type") == "function" and isinstance(it.get("function"), dict):
            it = it["function"]
        if "name" in it and any(k in it for k in ("parameters", "params_json_schema", "inputSchema", "input_schema", "args_schema", "tool_call_schema", "description")):
            out.append(it)
    return out


def _line_of(text: str, name: str) -> int:
    pat = re.compile(r'["\']?name["\']?\s*:\s*["\']?' + re.escape(name) + r'["\']?')
    for i, line in enumerate(text.splitlines(), start=1):
        if pat.search(line):
            return i
    return 1


class ToolDefsScanner(Scanner):
    kind = "tool-definitions"

    def detect(self, root: str) -> list[str]:
        found = [f for f in FILES if os.path.isfile(os.path.join(root, f))]
        for extra in getattr(policy.current(), "tool_definition_files", []):
            if os.path.isfile(os.path.join(root, extra)) and extra not in found:
                found.append(extra)
        return found

    def parse(self, root: str, rel_path: str) -> Observation:
        with open(os.path.join(root, rel_path), encoding="utf-8") as fh:
            text = fh.read()
        source = Source(path=rel_path, kind=self.kind, supported=True)
        obs = Observation(source=source)
        try:
            raw = json.loads(text) if rel_path.endswith(".json") else yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            source.supported = False
            source.note = f"invalid file: {str(exc).splitlines()[0]}"
            return obs
        tools = _tools_in(raw)
        if not tools:
            source.note = "no recognised tool definitions"
            return obs
        notes = []
        for t in tools:
            name = str(t["name"])
            access = classify(name, str(t.get("description", "")))
            system = name.split(".")[0] if "." in name else None
            where = f"{rel_path}:{_line_of(text, name)}"
            obs.tools.append(Tool(name=name, type=access, system=system, source=where, inferred=access is not ToolAccess.UNKNOWN))
            if access is ToolAccess.UNKNOWN:
                obs.unknowns.append(name)
            notes.append(f"{name} -> {access.value}{' (inferred)' if access is not ToolAccess.UNKNOWN else ''}")
        source.note = "; ".join(notes)
        return obs
