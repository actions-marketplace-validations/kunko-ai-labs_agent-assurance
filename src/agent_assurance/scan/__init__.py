"""Scan a repository for what its configuration grants an AI agent.

`scan_directory()` runs every scanner, merges what they observed into one
*observed* manifest and reports which files were looked at — including files
we recognise but do not parse yet, so "found nothing" is never confused with
"looked at nothing".
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from ..manifest import AgentInfo, DataSource, FrameworkSpec, Manifest, Tool
from .base import Observation, Scanner, Source
from .claude_settings import ClaudeSettingsScanner
from .codex_toml import CodexTomlScanner
from .mcp_json import McpJsonScanner
from .tool_defs import ToolDefsScanner

SCANNERS: list[Scanner] = [McpJsonScanner(), CodexTomlScanner(), ClaudeSettingsScanner(), ToolDefsScanner()]

# Recognised but not parsed yet. Listed so the report can say "detected, not
# supported" instead of staying silent. Each becomes a scanner in its own issue.
KNOWN_UNSUPPORTED: dict[str, str] = {
    "claude_desktop_config.json": "claude-desktop (user scope, not a repo file)",
    "AGENTS.md": "agent instructions (not permissions; see ruleblast for instruction blast radius)",
}


@dataclass
class ScanResult:
    observed: Manifest
    sources: list[Source] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    @property
    def found_anything(self) -> bool:
        return any(s.supported for s in self.sources)


def _merge(observations: list[Observation], declared: Manifest | None, root: str) -> Manifest:
    tools: list[Tool] = []
    data: list[DataSource] = []
    seen_tools: set[tuple] = set()
    seen_data: set[tuple[str, str]] = set()
    for obs in observations:
        for t in obs.tools:
            # The same server declared for several hosts (.mcp.json and
            # .cursor/mcp.json, say) is one capability, not two.
            key = (t.name, t.type.value, t.system, t.approval, t.scoped)
            if key not in seen_tools:
                seen_tools.add(key)
                tools.append(t)
        for d in obs.data:
            key = (d.type.value, ",".join(sorted(d.systems)))
            if key not in seen_data:
                seen_data.add(key)
                data.append(d)

    if declared is not None:
        # Identity, autonomy and delegation are not observable from config
        # files; they come from the declaration. Capabilities come from the scan.
        return declared.model_copy(update={"tools": tools, "data": data})

    name = os.path.basename(os.path.abspath(root)) or "agent"
    return Manifest(
        agent=AgentInfo(name=name),
        framework=FrameworkSpec(name="mcp"),
        tools=tools,
        data=data,
    )


def scan_directory(root: str, declared: Manifest | None = None) -> ScanResult:
    observations: list[Observation] = []
    sources: list[Source] = []
    unknowns: list[str] = []

    for scanner in SCANNERS:
        for rel in scanner.detect(root):
            obs = scanner.parse(root, rel)
            observations.append(obs)
            sources.append(obs.source)
            unknowns.extend(obs.unknowns)

    for rel, kind in KNOWN_UNSUPPORTED.items():
        if os.path.isfile(os.path.join(root, rel)):
            sources.append(Source(path=rel, kind=kind, supported=False, note="detected, not supported yet"))

    return ScanResult(
        observed=_merge(observations, declared, root),
        sources=sources,
        unknowns=unknowns,
    )


__all__ = ["KNOWN_UNSUPPORTED", "SCANNERS", "ScanResult", "Source", "scan_directory"]
