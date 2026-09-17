# Landscape: agent configuration scanners and permission diff tools

Checked on **2026-09-17** (issue #15). Star counts and dates come from the GitHub API on that day; scope comes from each project's README. Nothing here was executed or tested; this is a reading of what each project *says* it does.

## What exists

| Project | Stars / created | What it looks at | What it does NOT do (per README) | License |
|---|---|---|---|---|
| [snyk/agent-scan](https://github.com/snyk/agent-scan) (formerly Invariant `mcp-scan`) | 3,059 · 2025-04 | Discovers MCP servers and agent skills across 14 coding agents (Cursor, Claude Code, Copilot, Gemini CLI…); tool poisoning, rug pulls, secrets; connects to servers | No risk score, no base-vs-PR diff, no standards mapping, no declared-intent check | Apache-2.0 |
| [affaan-m/agentshield](https://github.com/affaan-m/agentshield) | 1,196 · 2026-02 | `.claude/` config: secrets, 17 permission rules (`Bash(*)`, missing deny…), hooks, MCP, agent configs; CLI + Action + GitHub App; optional LLM analysis | No blast-radius number, no diff, Claude-Code-centric | MIT |
| [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | 1,074 · 2025-09 | MCP server tool definitions: YARA + LLM-as-judge + Cisco AI Defense API | Needs LLM/API keys for most value; no config diff, no score | Apache-2.0 |
| [nqtplus/agentcapdiff](https://github.com/nqtplus/agentcapdiff) | 1 · 2026-08 | **Static capability inventory** from serialized tool metadata (MCP, OpenAI, Claude, LangChain/LangGraph, CrewAI) → normalized capability IDs → policy-as-code → **snapshot + diff in PR** → SARIF. Unknown is not safe. | No risk bands, no standards mapping, no declared-vs-observed; single author, no license file (NOASSERTION) | none stated |
| [saagpatel/agent-permission-diff-bot](https://github.com/saagpatel/agent-permission-diff-bot) | 0 · 2026-06 | Permission changes in PRs: MCP configs, GitHub Actions token permissions, OIDC; SARIF | Same niche as agentcapdiff, smaller | MIT |
| [emanalshazly/monna-agent-permission-diff](https://github.com/emanalshazly/monna-agent-permission-diff), [DebadityaHait/agent-permission-diff](https://github.com/DebadityaHait/agent-permission-diff) | 0 · 2026-08/09 | Offline permission change review; CLI + browser demo + Action | Same niche, one commit each | MIT |
| [Kpoiut/ruleblast](https://github.com/Kpoiut/ruleblast) | 19 · 2026-08 | Blast radius of **instruction file** changes (AGENTS.md, CLAUDE.md): which files inherit a different instruction stack | Instructions, not permissions | Apache-2.0 |
| [eSentire-Labs/mcp-scanner](https://github.com/eSentire-Labs/mcp-scanner), [helpfuldolphin/AgentAuditKit](https://github.com/helpfuldolphin/AgentAuditKit) | 6 / 2 | MCP server vulnerability scanning; misconfig, secrets, taint | Vulnerability scanners, not capability review | — |

## Reading

1. **"Scan agent configs for vulnerabilities" is taken.** Three funded or ecosystem-backed projects (Snyk, Cisco, agentshield) with 1k–3k stars each, all active this week. Competing there with a solo repo is a losing move.
2. **"Capability diff in PR" — the plan-C idea — already has ~5 implementations, all born June–September 2026, all with 0–1 stars.** `agentcapdiff` is the most complete and is a near-exact description of what issues #9/#10/#12 asked for. Two conclusions: the idea is obvious enough that several people built it independently, and nobody has found distribution or a reason for others to adopt it. A sixth clone would not change that.
3. **Nobody in the table does three things `agent-assurance` already does or can do cheaply:**
   - a **transparent risk score with bands** ("how much can this agent break", reproducible by hand);
   - a **standards mapping** (none of the six READMEs mentions OWASP at all — checked by keyword);
   - a **declared manifest** that can be *verified against* the observed configuration.
4. All of them target **coding agents** (Cursor, Claude Code, MCP on a laptop). Business agents in production (CrewAI/LangGraph/OpenAI Agents writing to CRMs, ERPs, banks) are only touched by `agentcapdiff`, statically, without traction.

## What this means for agent-assurance

Plan C as written on 2026-09-17 ("scan → diff, Dependabot for agent permissions") would be a sixth clone of `agentcapdiff`. The defensible position is the one none of them occupy:

> **Declared vs observed.** The repo *claims* what the agent is allowed to do (`agent-assurance.yaml`: read-only, no external send, autonomy L2, these systems). The scan finds what the configuration *actually grants*. The check fails when the claim is broken, scores the observed blast radius, maps it to OWASP ASI, and leaves a SARIF trail per commit. The PR diff then reads: *"this change breaks the claim 'no external send'"*.

That turns the manifest from a questionnaire into an attestation, reuses every line already built, does not compete with vulnerability scanners (they find poison; we verify promises), and is the technical shape of the "evidence" that the company lane needs later.

Decision recorded in the programme notebook (doc 12 §1, 2026-09-17, second entry).

## Open questions (not answered today)

- Can the config discovery of `snyk/agent-scan` (Apache-2.0, Python) be reused as a library instead of re-implementing `.mcp.json` / Claude Code parsers? Worth one hour before #9.
- `agentcapdiff` has no license file: not reusable, and a reason its idea is free to take.
- Re-check this table before v0.3 (diff): the niche moves monthly.
