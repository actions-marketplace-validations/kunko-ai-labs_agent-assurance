"""Scanner for OpenAI Codex CLI project configuration: `.codex/config.toml`.

Format (Codex CLI docs, config reference, read on 2026-09-17):

    [mcp_servers.<name>]
    command = "npx"
    args = ["-y", "@modelcontextprotocol/server-github"]
    env = { GITHUB_TOKEN = "..." }

    [mcp_servers.<name>]
    url = "https://..."

Same server shape as the JSON hosts, so classification is shared with them.
TOML parsing uses the standard library on Python 3.11+ and `tomli` on 3.10.
"""

from __future__ import annotations

import os
import re

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

from .base import Observation, Scanner, Source
from .mcp_json import observe_servers

FILE = ".codex/config.toml"


def _line_of(text: str, name: str) -> int:
    pat = re.compile(r"^\s*\[mcp_servers\." + re.escape(name) + r"(\.|\]|\s)")
    for i, line in enumerate(text.splitlines(), start=1):
        if pat.match(line) or pat.match(line.replace('"', "")):
            return i
    return 1


class CodexTomlScanner(Scanner):
    kind = "codex-config"

    def detect(self, root: str) -> list[str]:
        return [FILE] if os.path.isfile(os.path.join(root, FILE)) else []

    def parse(self, root: str, rel_path: str) -> Observation:
        with open(os.path.join(root, rel_path), encoding="utf-8") as fh:
            text = fh.read()
        source = Source(path=rel_path, kind=self.kind, supported=True)
        obs = Observation(source=source)
        try:
            raw = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            source.supported = False
            source.note = f"invalid TOML: {exc}"
            return obs
        servers = raw.get("mcp_servers")
        if not isinstance(servers, dict):
            source.note = "no mcp_servers table"
            return obs
        observe_servers(servers, rel_path, obs, lambda n: _line_of(text, n))
        return obs
