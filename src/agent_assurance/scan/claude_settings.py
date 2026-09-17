"""Scanner for Claude Code project permissions:
`.claude/settings.json` and `.claude/settings.local.json`.

Reference: Claude Code settings documentation, "permissions" section
(https://docs.claude.com/en/docs/claude-code/settings), as read on 2026-09-17.
Rules are strings of the form `Tool` or `Tool(specifier)`, listed under
`permissions.allow`, `permissions.ask` and `permissions.deny`. Precedence is
deny > ask > allow. `permissions.defaultMode` can auto-approve classes of
tools ("acceptEdits") or everything ("bypassPermissions").

What a rule means for assurance — and this is the part worth getting right:
Claude Code's built-in tools exist whether or not they are listed. A rule does
not *grant* a capability; it decides whether a **human approves** its use.
So `allow` = the capability runs with no one watching (approval "auto"),
`ask` = a person confirms, `deny` = the capability is removed. Autonomy, not
access class, is what these files change.

Built-in tools map to classes as follows; anything else is UNKNOWN:
  Bash                              -> execute (shell)
  Edit, Write, MultiEdit, NotebookEdit -> write (filesystem)
  Read, Glob, Grep, LS              -> read (filesystem)
  WebFetch, WebSearch               -> read (web)
  Agent, Task                       -> execute (subagents) — delegation
  mcp__<server>__<tool>, mcp__<server> -> the server's class from the catalogue
"""

from __future__ import annotations

import json
import os
import re

from ..manifest import Tool, ToolAccess
from . import catalog
from .base import Observation, Scanner, Source

FILES = (".claude/settings.json", ".claude/settings.local.json")

_BUILTIN: dict[str, tuple[ToolAccess, str]] = {
    "Bash": (ToolAccess.EXECUTE, "shell"),
    "Edit": (ToolAccess.WRITE, "filesystem"),
    "Write": (ToolAccess.WRITE, "filesystem"),
    "MultiEdit": (ToolAccess.WRITE, "filesystem"),
    "NotebookEdit": (ToolAccess.WRITE, "filesystem"),
    "Read": (ToolAccess.READ, "filesystem"),
    "Glob": (ToolAccess.READ, "filesystem"),
    "Grep": (ToolAccess.READ, "filesystem"),
    "LS": (ToolAccess.READ, "filesystem"),
    "WebFetch": (ToolAccess.READ, "web"),
    "WebSearch": (ToolAccess.READ, "web"),
    "Agent": (ToolAccess.EXECUTE, "subagents"),
    "Task": (ToolAccess.EXECUTE, "subagents"),
}
_RULE_RE = re.compile(r"^(?P<tool>[A-Za-z_][A-Za-z0-9_]*)(?:\((?P<spec>.*)\))?$")
_MODE_TO_APPROVAL = {"allow": "auto", "ask": "ask"}


def _line_of(text: str, needle: str) -> int:
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return i
    return 1


def _classify(tool: str) -> tuple[ToolAccess, str] | None:
    if tool in _BUILTIN:
        return _BUILTIN[tool]
    if tool.startswith("mcp__"):
        parts = tool.split("__")  # mcp__<server>__<tool> or mcp__<server>
        server = parts[1] if len(parts) > 1 and parts[1] else tool
        entry = catalog.lookup(server, "")
        if entry is None:
            return (ToolAccess.UNKNOWN, server)
        # Whole-server rule or a tool we cannot name: take the server's widest class.
        widest = max(entry.capabilities, key=lambda c: _RANK.get(c.access, 0)).access
        return (widest, entry.system)
    return None


_RANK = {
    ToolAccess.READ: 0,
    ToolAccess.WRITE: 2,
    ToolAccess.EXECUTE: 2,
    ToolAccess.EXTERNAL_SEND: 2,
    ToolAccess.DELETE: 3,
    ToolAccess.FINANCIAL: 3,
    ToolAccess.UNKNOWN: 1,
}


class ClaudeSettingsScanner(Scanner):
    kind = "claude-code-settings"

    def detect(self, root: str) -> list[str]:
        return [f for f in FILES if os.path.isfile(os.path.join(root, f))]

    def parse(self, root: str, rel_path: str) -> Observation:
        with open(os.path.join(root, rel_path), encoding="utf-8") as fh:
            text = fh.read()
        source = Source(path=rel_path, kind=self.kind, supported=True)
        obs = Observation(source=source)

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            source.supported = False
            source.note = f"invalid JSON: {exc.msg} (line {exc.lineno})"
            return obs

        perms = raw.get("permissions") if isinstance(raw, dict) else None
        if not isinstance(perms, dict):
            source.note = "no permissions block"
            return obs

        notes: list[str] = []

        # deny wins over everything: collect bare-tool denials first.
        denied_tools: set[str] = set()
        for rule in perms.get("deny") or []:
            m = _RULE_RE.match(str(rule))
            if m and not m.group("spec"):
                denied_tools.add(m.group("tool"))
            if m:
                notes.append(f"deny {rule}")

        for mode in ("ask", "allow"):
            for rule in perms.get(mode) or []:
                m = _RULE_RE.match(str(rule))
                if not m:
                    continue
                tool, spec = m.group("tool"), m.group("spec")
                if tool in denied_tools:
                    notes.append(f"{mode} {rule} overridden by deny")
                    continue
                where = f"{rel_path}:{_line_of(text, str(rule))}"
                cls = _classify(tool)
                name = f"claude-code.{rule}"
                if cls is None:
                    obs.tools.append(Tool(name=name, type=ToolAccess.UNKNOWN, system=tool, source=where, approval=_MODE_TO_APPROVAL[mode]))
                    obs.unknowns.append(str(rule))
                    notes.append(f"{mode} {rule}: unknown tool -> UNKNOWN")
                    continue
                access, system = cls
                if access is ToolAccess.UNKNOWN:
                    obs.unknowns.append(str(rule))
                obs.tools.append(
                    Tool(name=name, type=access, system=system, source=where, approval=_MODE_TO_APPROVAL[mode])
                )
                scoped = f" (scoped: {spec})" if spec and spec != "*" else ""
                notes.append(f"{mode} {tool}{scoped} -> {access.value}")

        default_mode = perms.get("defaultMode")
        if default_mode == "bypassPermissions":
            where = f"{rel_path}:{_line_of(text, 'bypassPermissions')}"
            obs.tools.append(
                Tool(name="claude-code.defaultMode=bypassPermissions", type=ToolAccess.EXECUTE, system="shell", source=where, approval="auto")
            )
            notes.append("defaultMode=bypassPermissions: every tool runs without approval")
        elif default_mode == "acceptEdits":
            where = f"{rel_path}:{_line_of(text, 'acceptEdits')}"
            obs.tools.append(
                Tool(name="claude-code.defaultMode=acceptEdits", type=ToolAccess.WRITE, system="filesystem", source=where, approval="auto")
            )
            notes.append("defaultMode=acceptEdits: file edits run without approval")

        source.note = "; ".join(notes) if notes else "no rules"
        return obs
