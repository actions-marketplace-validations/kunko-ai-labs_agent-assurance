# Agent Assurance

**Declare what your agent may do. Verify it on every PR.**

Your repo *promises* what an AI agent is allowed to do (`agent-assurance.yaml`: read the CRM, no external send, autonomy L2). Agent Assurance *observes* what the repo's configuration actually grants (`.mcp.json` today, more sources coming), scores the blast radius, maps it to OWASP Agentic security standards, and fails the PR when the promise is broken — pointing at the file and line that broke it. No dashboard, no backend, no LLM in the verdict. A rule-based model you can read and reproduce by hand.

```bash
pip install agent-assurance
agent-assurance scan .            # observe the config, verify the promise if agent-assurance.yaml exists
agent-assurance check all agent-assurance.yaml   # the promise alone: how much could this agent break?
```

```
❌ AA-002 — Declared vs Observed · FAIL
Promise broken: 5 undeclared capabilities
- Declared: read; data: internal
- BROKEN — `github.write` grants **write**, not declared (.mcp.json:11)
- BROKEN — `slack.post_message` grants **external_send**, not declared (.mcp.json:16)
- BROKEN — access to **credential** data (github), not declared (.mcp.json:11)
```

---

## Why

Agents are moving from chat into production: writing to CRMs, sending email, touching infrastructure, moving money. When an agent changes — a new MCP server, a broader permission, a jump in autonomy — nobody notices until something breaks.

Vulnerability scanners look for poisoned tools and leaked secrets. Permission-diff bots show what changed. Neither answers the governance question: **does this agent still do only what we said it does?** Agent Assurance answers it where developers already work — the PR — with deterministic checks that map to the **OWASP Top 10 for Agentic Applications (ASI01–ASI10)**, and leaves a per-commit record an auditor can reconstruct (the shape EU AI Act art. 12 asks for).

## Two inputs, one verdict

| | What it is | Where it comes from |
|---|---|---|
| **Declared** | The promise: which capability classes, systems, data and autonomy the agent is *meant* to have | `agent-assurance.yaml`, written by the team |
| **Observed** | What the configuration *actually grants* | `scan`: `.mcp.json` (project MCP servers) via a [curated catalogue](src/agent_assurance/scan/catalog.py); unknown servers are `UNKNOWN`, never guessed |

Checks:

| Check | Question | Verdict |
|---|---|---|
| **AA-001 Blast Radius** | If this agent misbehaves, how much can it break? | LOW/MEDIUM pass · HIGH review · CRITICAL fail · any `UNKNOWN` ≥ review |
| **AA-002 Declared vs Observed** | Does the configuration stay within the promise? | Undeclared write/delete/execute/external_send/financial or sensitive data → **fail** · extra reach or `UNKNOWN` → review · within → pass |

`scan` without a manifest still works: you get the observed blast radius and a "Sources scanned" table. `check` on a manifest alone runs AA-001 only.

## The manifest is the promise

Every check consumes the same representation, `agent-assurance/v1`. Written by hand it is a declaration; produced by `scan` it is an observation, with `source: path:line` on every tool.

```yaml
apiVersion: agent-assurance/v1
agent:
  name: support-agent
  version: 1.0.0
framework:
  name: langgraph
model:
  provider: ollama
  name: llama-3.1
tools:
  - name: crm.read
    type: read
    system: crm
  - name: crm.write
    type: write
    system: crm
data:
  - type: pii
    systems: [crm]
autonomy: 2
delegation:
  enabled: false
```

Define it once; blast-radius, governance-diff, evidence-contract and action-trust all read it.

## What you get in a PR

```
🤖 Agent Assurance

❌ AGENT ASSURANCE FAILED

Agent: autonomous-finance-agent v0.9.0
Framework: crewai · Autonomy: L4

### ❌ AA-001 — Blast Radius · FAIL
Blast radius CRITICAL (score 50)
- Systems affected: aws, bank, crm, email
- Sensitive data: credential, financial, pii
- Write capabilities: crm.write, aws.delete
- External side effects: email.send
- Irreversible actions: aws.delete, bank.transfer
- Autonomy: L4
Standards: OWASP-ASI:ASI08, OWASP-ASI:ASI03, OWASP-APTS:APTS-SC-020 (adapted)
```

## The risk model is transparent

Not an "AI risk score". Every point is attributable:

| Property | Points |
|---|---|
| tool `read` / `execute`,`write`,`external_send` / `delete`,`financial` | 1 / 3 / 5 |
| data `pii` / `health`,`financial` / `credential` | 3 / 4 / 5 |
| production system | +5 |
| irreversible action | +5 |
| delegation enabled | +3 |
| autonomy above L2 | +2 per level |

Bands: LOW `<8` · MEDIUM `<16` · HIGH `<28` · CRITICAL `>=28`. HIGH → review, CRITICAL → fail (configurable with `--fail-on`).

## CLI

```bash
agent-assurance validate agent-assurance.yaml          # schema-check the manifest
agent-assurance check blast-radius agent-assurance.yaml # run a check (markdown)
agent-assurance check all agent-assurance.yaml --format json
agent-assurance scan .                                  # observe + verify (picks up ./agent-assurance.yaml)
agent-assurance scan path/to/repo -m promise.yaml --format sarif -o aa.sarif
```

Try the bundled repos: `examples/repos/mcp-promise-kept` (PASS), `mcp-promise-broken` (FAIL), `mcp-unknown-server` (REVIEW).

`--format sarif` surfaces findings in the GitHub Security tab (a PASS is emitted as `kind: pass`, so a clean agent never creates an alert).

Exit codes are a contract: `0` pass (REVIEW too, unless `--fail-on review`) · `1` gate tripped · `2` usage/manifest error. That is what lets it gate a pipeline out of the box.

## GitHub Action

```yaml
permissions:
  contents: read
  security-events: write   # only if upload-sarif: true

steps:
  - uses: actions/checkout@v4
  - uses: kunko-ai-labs/agent-assurance@v0.1
    with:
      mode: scan             # observe .mcp.json and verify it against the manifest
      manifest: agent-assurance.yaml
      fail-on: fail          # or: review
      sarif: aa.sarif        # optional: write a SARIF file
      upload-sarif: "true"   # optional: send it to the Security tab
```

The markdown report lands in the job summary; the job fails when the gate trips. See [`.github/workflows/assurance.yml`](.github/workflows/assurance.yml) for the repo's own dogfood, which asserts that the gate blocks what it should.

## Standards mapping

Checks map primarily to the **OWASP Top 10 for Agentic Applications** (business agents). Where a control is borrowed from **OWASP APTS** (a standard for *autonomous penetration-testing* platforms), it is labelled `(adapted)` — we do not claim APTS conformance for business agents. Honesty about relation is part of the tool.

## Roadmap

`AA-001 Blast Radius` ships today, computed from a hand-written manifest. A declared manifest is an audit artefact; it only becomes a *control* when the input is observed, not declared. That is where v0.2 goes:

| Version | What | Why |
|---|---|---|
| **v0.2 — `scan` + AA-002** | Observe `.mcp.json` (done), then Claude Code `permissions` in `.claude/settings.json`; verify against the declaration. Unknown sources are `UNKNOWN`, never guessed. | The manifest becomes an attestation, not a questionnaire. |
| **v0.3 — `diff`** | Compare base vs PR: *"new MCP server `github` (write); blast radius MEDIUM → HIGH; promise broken: the manifest declares read-only"*. Gate on the delta. | The moment a PR widens what an agent can do — or breaks what it promised — the reviewer sees it. |
| later | More observed sources (Cursor, VS Code, Gemini CLI, framework tool definitions); more questions on the same input (delegation budget, external-send allowlist). | Same input, more questions. |

See [`docs/landscape.md`](docs/landscape.md) for what already exists around this and why this tool sits where it sits.

Out of scope on purpose: no LLM in the verdict, no runtime interception, no auto-fixing permissions. Runtime governance is a different product; this tool checks what the repo says the agent can do.

## License

Apache-2.0.
