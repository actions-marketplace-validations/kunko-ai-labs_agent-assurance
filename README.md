# Agent Assurance

**Transparent, framework-agnostic assurance checks for AI agents — in your CI, mapped to OWASP Agentic security standards.**

Point it at a manifest describing your agent (tools, data, autonomy, delegation) and it tells you — in your pull request — how much damage that agent could do if it misbehaves or is compromised. No dashboard, no backend, no SaaS, no LLM in the scoring path. Just a rule-based model you can read and reproduce by hand.

```bash
pip install agent-assurance
agent-assurance check blast-radius agent-assurance.yaml
```

---

## Why

Agents are moving from chat into production: writing to CRMs, sending email, touching infrastructure, moving money. When an agent changes — a new tool, a broader permission, a jump in autonomy — nobody notices until something breaks.

Agent Assurance makes that visible where developers already work: the PR. It reads one manifest and runs deterministic checks that map to the **OWASP Top 10 for Agentic Applications (ASI01–ASI10)**.

## The manifest is the point

Every check consumes the same representation, `agent-assurance/v1`:

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
agent-assurance check all agent-assurance.yaml --format sarif -o aa.sarif
```

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
| **v0.2 — `scan`** | Derive the manifest from the agent configuration that already lives in the repo (`.mcp.json`, Claude Code `settings.json` permissions first; more formats after). Unsupported sources are reported as `UNKNOWN`, never guessed. | Zero configuration: install the Action and get the report on the next PR. |
| **v0.3 — `diff`** | Compare base vs PR: *"this change gives the agent shell execution / a new MCP server with write scope; blast radius moves MEDIUM → CRITICAL"*. Gate on the delta. | Dependabot for agent permissions: the moment a PR widens what an agent can do, the reviewer sees it. |
| later | More checks on the observed manifest (delegation budget, external-send allowlist, evidence that goes stale when the config changes). | Same input, more questions. |

Out of scope on purpose: no LLM in the verdict, no runtime interception, no auto-fixing permissions. Runtime governance is a different product; this tool checks what the repo says the agent can do.

## License

Apache-2.0.
