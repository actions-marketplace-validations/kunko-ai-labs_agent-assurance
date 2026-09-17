#!/usr/bin/env bash
# Prepares /tmp/pr-head: the demo repo after a PR adds a GitHub MCP server.
set -e
export PATH="$PWD/.venv/bin:$PATH"
rm -rf /tmp/pr-head
cp -R examples/demo/analytics-helper /tmp/pr-head
python3 - <<'PY'
import json
p = "/tmp/pr-head/.mcp.json"
d = json.load(open(p))
d["mcpServers"]["github"] = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}}
json.dump(d, open(p, "w"), indent=2)
PY
