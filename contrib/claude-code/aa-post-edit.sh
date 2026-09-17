#!/usr/bin/env bash
# Claude Code PostToolUse hook: after the agent edits an agent-configuration
# file, verify the repo's promise. Exit 2 feeds the verdict back to the agent
# as an error it must deal with — the agent learns, in the same turn, that it
# just broke the promise, and can revert or ask.
#
# Install: see contrib/claude-code/README.md
set -u
input=$(cat)
path=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)
case "$path" in
  *.mcp.json|*/.claude/settings.json|*/.claude/settings.local.json|*/.cursor/mcp.json|*/.vscode/mcp.json|*/.gemini/settings.json|*/agent-assurance.yaml) ;;
  *) exit 0 ;;
esac
root=$(git -C "$(dirname "$path")" rev-parse --show-toplevel 2>/dev/null || pwd)
out=$(agent-assurance scan "$root" --format md 2>/dev/null); code=$?
if [ "$code" -eq 1 ]; then
  {
    echo "agent-assurance: this edit breaks the promise declared in agent-assurance.yaml."
    printf '%s\n' "$out" | grep -E "BROKEN|Promise|Blast radius" | head -12
    echo "Revert the change, or update agent-assurance.yaml if the wider reach is intended and approved."
  } >&2
  exit 2
fi
exit 0
