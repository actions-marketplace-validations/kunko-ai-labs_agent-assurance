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
Blast radius CRITICAL (score 41)
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

`--format sarif` surfaces findings in the GitHub Security tab. Exit code is `1` on FAIL (or on REVIEW with `--fail-on review`), so it gates a pipeline out of the box.

## GitHub Action

```yaml
- uses: kunko-ai-labs/agent-assurance@v0.1
  with:
    manifest: agent-assurance.yaml
    fail-on: fail        # or: review
    sarif: aa.sarif      # optional: upload to code scanning
```

## Standards mapping

Checks map primarily to the **OWASP Top 10 for Agentic Applications** (business agents). Where a control is borrowed from **OWASP APTS** (a standard for *autonomous penetration-testing* platforms), it is labelled `(adapted)` — we do not claim APTS conformance for business agents. Honesty about relation is part of the tool.

## Roadmap

`AA-001 Blast Radius` ships today. Next: `governance-diff` (base vs PR), `evidence-contract`, `action-trust` (model confidence ≠ action trust — arXiv:2609.07395), `behavior-drift`, `agent-chaos`.

## License

Apache-2.0.
