# Claude Code integration

Two ways to put the promise in front of the agent itself, not only in front of the reviewer.

## 1. MCP server — the agent asks before it widens itself

```bash
pip install "agent-assurance[mcp]"
claude mcp add agent-assurance -- agent-assurance-mcp
```

Tools exposed: `scan`, `check`, `would_break`. With the server's instructions loaded, an agent that is about to add an MCP server or a permission rule can call `would_break` first and see, in the same shape as the PR comment, whether the change breaks `agent-assurance.yaml`. Nothing is written; the change is simulated in a temporary copy.

## 2. PostToolUse hook — the agent learns the moment it breaks the promise

`aa-post-edit.sh` runs after every `Edit`/`Write`. If the file is an agent-configuration file and the repo's promise is now broken, the hook exits 2 with the verdict, which Claude Code hands back to the agent as an error to act on.

`.claude/settings.json` in the target repo:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "/path/to/agent-assurance/contrib/claude-code/aa-post-edit.sh" }
        ]
      }
    ]
  }
}
```

Requires `agent-assurance` on `PATH` (`pipx install agent-assurance`).

Reference: Claude Code hooks documentation (https://docs.claude.com/en/docs/claude-code/hooks), read on 2026-09-17. Hook input arrives as JSON on stdin with `tool_input.file_path`; exit code 2 returns stderr to the model.
