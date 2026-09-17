# Real-world scans

Public repositories scanned on 2026-09-17 with agent-assurance v0.3.0, exactly as `agent-assurance scan <clone>` printed them. Only public configuration files were read; nothing was executed. Each repo is pinned to the commit scanned. None of them declares an `agent-assurance.yaml`, so these are observed-only reports (AA-001); with a manifest they would also get AA-002.

These are not judgements about the projects. They show what the tool sees, what it does not (`UNKNOWN`, unsupported files) and how the verdict reads.

## [Doist/todoist-mcp](https://github.com/Doist/todoist-mcp) @ `3bfac51`

```markdown
## 🤖 Agent Assurance

⚠️ **AGENT ASSURANCE — REVIEW RECOMMENDED**

**Agent:** `Doist_todoist-mcp` v0.0.0
**Framework:** mcp · **Autonomy:** L1
**Mode:** scan — observed configuration only (no manifest declared)

### ⚠️ AA-001 — Blast Radius · REVIEW

Blast radius HIGH (score 21)

- Systems affected: docs, shell, todoist
- Sensitive data: pii
- Write capabilities: todoist.write, todoist.delete
- External side effects: todoist.remote
- Autonomy: L1
- Risk score: 21 (HIGH)

_Standards: OWASP-ASI:ASI08, OWASP-ASI:ASI03, OWASP-APTS:APTS-SC-020 (adapted)_

**Sources scanned**

| File | Kind | Status | Notes |
|---|---|---|---|
| `.mcp.json` | mcp.json (Claude Code) | parsed | todoist: todoist (delete, read, write) |
| `.cursor/mcp.json` | cursor-mcp | parsed | context7: docs (read) |
| `.claude/settings.json` | claude-code-settings | parsed | allow 1 rule(s) -> read shell (scoped); allow 4 rule(s) -> execute shell (scoped) |
| `AGENTS.md` | agent instructions (not permissions; see ruleblast for instruction blast radius) | detected, not supported | detected, not supported yet |

---
⚠️ **Human governance review recommended before merge.**
```

## [Archive228/loopkit](https://github.com/Archive228/loopkit) @ `5ae033e`

```markdown
## 🤖 Agent Assurance

⚠️ **AGENT ASSURANCE — REVIEW RECOMMENDED**

**Agent:** `Archive228_loopkit` v0.0.0
**Framework:** mcp · **Autonomy:** L1
**Mode:** scan — observed configuration only (no manifest declared)

### ⚠️ AA-001 — Blast Radius · REVIEW

Blast radius HIGH (score 17)

- Systems affected: docs, filesystem, github, shell
- Sensitive data: credential, internal
- Write capabilities: github.write, github.push
- Autonomy: L1
- Risk score: 17 (HIGH)

_Standards: OWASP-ASI:ASI08, OWASP-ASI:ASI03, OWASP-APTS:APTS-SC-020 (adapted)_

**Sources scanned**

| File | Kind | Status | Notes |
|---|---|---|---|
| `.mcp.json` | mcp.json (Claude Code) | parsed | github: github (read, write); context7: docs (read) |
| `.claude/settings.json` | claude-code-settings | parsed | deny Bash(rm -rf:*); deny Bash(git push --force:*); allow 5 rule(s) -> read shell (scoped); allow 1 rule(s) -> read filesystem |
| `AGENTS.md` | agent instructions (not permissions; see ruleblast for instruction blast radius) | detected, not supported | detected, not supported yet |

---
⚠️ **Human governance review recommended before merge.**
```

## [YoshiiRyo1/document-templates-for-aws](https://github.com/YoshiiRyo1/document-templates-for-aws) @ `16967f6`

```markdown
## 🤖 Agent Assurance

⚠️ **AGENT ASSURANCE — REVIEW RECOMMENDED**

**Agent:** `YoshiiRyo1_document-templates-for-aws` v0.0.0
**Framework:** mcp · **Autonomy:** L1
**Mode:** scan — observed configuration only (no manifest declared)

### ⚠️ AA-001 — Blast Radius · REVIEW

Blast radius HIGH (score 26) — 1 unknown capability

- Systems affected: aws-docs, claude-code, document-loader, filesystem, shell, subagents, web
- Write capabilities: claude-code.filesystem[Edit, Write]
- Unknown capabilities (scored as write): document-loader.*
- Runs without human approval: claude-code.shell[Bash], claude-code.filesystem[Edit, Write], claude-code.subagents[Task]
- Autonomy: L1
- Risk score: 26 (HIGH)

_Standards: OWASP-ASI:ASI08, OWASP-ASI:ASI03, OWASP-APTS:APTS-SC-020 (adapted)_

**Sources scanned**

| File | Kind | Status | Notes |
|---|---|---|---|
| `.mcp.json` | mcp.json (Claude Code) | parsed | aws-knowledge: aws-docs (read); document-loader: not in catalogue -> UNKNOWN |
| `.claude/settings.json` | claude-code-settings | parsed | deny Bash(rm -rf /:*); deny Bash(sudo:*); deny Bash(shutdown:*); deny Bash(reboot:*); ask 3 rule(s) -> execute shell (scoped); allow 1 rule(s) -> execute shell; allow 2 rule(s) -> write filesystem; allow 1 rule(s) -> read filesystem; allow 1 rule(s) -> read claude-code; allow 1 rule(s) -> execute subagents; allow 2 rule(s) -> read web |

---
⚠️ **Human governance review recommended before merge.**
```

## [Kpoiut/ruleblast](https://github.com/Kpoiut/ruleblast) @ `d826c90`

```markdown
## 🤖 Agent Assurance

⚠️ **AGENT ASSURANCE — REVIEW RECOMMENDED**

**Agent:** `Kpoiut_ruleblast` v0.0.0
**Framework:** mcp · **Autonomy:** L1
**Mode:** scan — observed configuration only (no manifest declared)

### ⚠️ AA-001 — Blast Radius · REVIEW

Blast radius LOW (score 3) — 1 unknown capability

- Systems affected: ruleblast
- Unknown capabilities (scored as write): ruleblast.*
- Autonomy: L1
- Risk score: 3 (LOW)

_Standards: OWASP-ASI:ASI08, OWASP-ASI:ASI03, OWASP-APTS:APTS-SC-020 (adapted)_

**Sources scanned**

| File | Kind | Status | Notes |
|---|---|---|---|
| `.mcp.json` | mcp.json (Claude Code) | parsed | ruleblast: not in catalogue -> UNKNOWN |
| `.cursor/mcp.json` | cursor-mcp | parsed | ruleblast: not in catalogue -> UNKNOWN |
| `.vscode/mcp.json` | vscode-mcp | parsed | ruleblast: not in catalogue -> UNKNOWN |
| `.codex/config.toml` | codex-config (TOML: [mcp_servers.<name>]) | detected, not supported | detected, not supported yet |
| `AGENTS.md` | agent instructions (not permissions; see ruleblast for instruction blast radius) | detected, not supported | detected, not supported yet |

---
⚠️ **Human governance review recommended before merge.**
```

## What this taught us

The first pass over these repos produced three false positives that a senior reviewer would have rejected on sight, and each changed the model (v0.3.0):

- `allow: Bash(grep:*)`, `Bash(git status:*)`, `Bash(npm test:*)` were scored as unattended shells, one per rule. A harmless config came out CRITICAL. Rules now collapse per capability class, read-only commands are reads, and a scoped grant is *review*, not *broken*.
- `aws-knowledge` (documentation, read-only) matched the `aws` catalogue entry (delete). Matching is package-first and token-based on names; the catalogue got aws-docs, context7 and todoist.
- Claude Code housekeeping tools (`Skill`, `TodoWrite`) came out UNKNOWN.

Servers still UNKNOWN in this set: `document-loader`, `ruleblast` (project-local servers). Adding a catalogue entry is one line plus its source.
