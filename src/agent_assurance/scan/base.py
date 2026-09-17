"""Scanner contract: what every source parser produces.

A scanner reads one kind of configuration file (`.mcp.json`, Claude Code
`settings.json`, ...) and returns the tools/data it *observes*, each with the
`path:line` that grants it. It never executes anything, never contacts a
server and never reads the value of a secret.

The scan layer is deliberately separate from the checks: scanners answer
"what does the repo grant?", checks answer "is that acceptable / does it match
what was promised?".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..manifest import DataSource, Tool


@dataclass
class Source:
    """One configuration file the scan looked at (or noticed)."""

    path: str  # relative to the scanned directory
    kind: str  # "mcp.json", "claude-code-settings", ...
    supported: bool  # False = detected but not parsed yet
    note: str = ""  # what was deduced, or why it was skipped


@dataclass
class Observation:
    """Everything one scanner found in one file."""

    source: Source
    tools: list[Tool] = field(default_factory=list)
    data: list[DataSource] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)  # names classified UNKNOWN


class Scanner:
    """Base class. Subclasses set `kind` and implement detect()/parse()."""

    kind: str = "unknown"

    def detect(self, root: str) -> list[str]:  # pragma: no cover - abstract
        """Return relative paths this scanner knows how to read under root."""
        raise NotImplementedError

    def parse(self, root: str, rel_path: str) -> Observation:  # pragma: no cover
        raise NotImplementedError
