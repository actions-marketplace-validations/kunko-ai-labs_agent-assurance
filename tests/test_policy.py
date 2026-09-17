"""Policy file: tune the model, never silently. No policy = built-in model."""

from __future__ import annotations

import json
import pathlib

from agent_assurance import cli, policy, risk
from agent_assurance.manifest import Manifest
from agent_assurance.scan import catalog

REPOS = pathlib.Path(__file__).resolve().parents[1] / "examples" / "repos"
ORG = REPOS / "policy-org"
KEPT = REPOS / "mcp-promise-kept"


def test_defaults_equal_documented_model():
    p = policy.Policy()
    assert p.is_default
    assert p.weights.tools.as_map() == risk.TOOL_WEIGHTS
    assert p.weights.data.as_map() == risk.DATA_WEIGHTS
    assert p.bands.table() == risk.BANDS
    assert p.weights.production == risk.PRODUCTION_WEIGHT
    assert p.weights.auto_approval == risk.AUTO_APPROVAL_WEIGHT


def test_policy_is_discovered_and_recorded(tmp_path):
    out = tmp_path / "r.json"
    cli.main(["scan", str(ORG), "--format", "json", "-o", str(out)])
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["policy"]["name"] == "acme-corp-2026-09"
    assert len(r["policy"]["sha256"]) == 64
    assert r["policy"]["path"].endswith("agent-assurance.policy.yaml")


def test_policy_catalog_turns_unknown_into_known():
    loaded = policy.load(str(ORG / "agent-assurance.policy.yaml"))
    assert catalog.lookup("acme-erp", "") is None
    policy.activate(loaded)
    entry = catalog.lookup("acme-erp", "")
    assert entry is not None and entry.system == "acme-erp" and entry.source.startswith("internal")


def test_policy_gate_and_promise_semantics(tmp_path):
    out = tmp_path / "r.json"
    code = cli.main(["scan", str(ORG), "--format", "json", "-o", str(out)])
    r = json.loads(out.read_text(encoding="utf-8"))
    aa1 = next(c for c in r["checks"] if c["id"] == "AA-001")
    aa2 = next(c for c in r["checks"] if c["id"] == "AA-002")
    # stricter gate: MEDIUM is already review
    assert aa1["data"]["band"] == "MEDIUM" and aa1["status"] == "REVIEW"
    # external_send removed from breaking: the remote server is review, not broken
    assert aa2["status"] == "REVIEW" and aa2["data"]["broken"] == []
    assert code == cli.EXIT_OK


def test_policy_weights_change_the_score(tmp_path):
    pol = tmp_path / "p.yaml"
    pol.write_text("apiVersion: agent-assurance/policy/v1\nname: heavy\nweights:\n  tools: {read: 10}\n", encoding="utf-8")
    m = Manifest.from_file(str(KEPT / "agent-assurance.yaml"))
    assert risk.assess(m).score == 3
    policy.activate(policy.load(str(pol)))
    assert risk.assess(m).score == 21  # two reads at 10 + internal data 1


def test_policy_read_only_commands_extend_defaults(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text('{"permissions": {"allow": ["Bash(poetry run pytest:*)"]}}', encoding="utf-8")
    (tmp_path / "agent-assurance.policy.yaml").write_text(
        "apiVersion: agent-assurance/policy/v1\nname: t\nread_only_commands: [poetry run pytest]\n", encoding="utf-8"
    )
    out = tmp_path / "r.json"
    cli.main(["scan", str(tmp_path), "--format", "json", "-o", str(out)])
    r = json.loads(out.read_text(encoding="utf-8"))
    tools = r["checks"][0]["data"]
    assert tools["write_capabilities"] == [] and tools["auto_approved"] == []


def test_invalid_policy_is_usage_error(tmp_path, capsys):
    bad = tmp_path / "p.yaml"
    bad.write_text("apiVersion: agent-assurance/policy/v9\n", encoding="utf-8")
    assert cli.main(["scan", str(KEPT), "--policy", str(bad)]) == cli.EXIT_USAGE
    bad.write_text("apiVersion: agent-assurance/policy/v1\nweights: {tools: {read: many}}\n", encoding="utf-8")
    assert cli.main(["scan", str(KEPT), "--policy", str(bad)]) == cli.EXIT_USAGE
    assert "invalid policy" in capsys.readouterr().err
    assert cli.main(["scan", str(KEPT), "--policy", str(tmp_path / "nope.yaml")]) == cli.EXIT_USAGE


def test_policy_does_not_leak_between_runs(tmp_path):
    out = tmp_path / "r.json"
    cli.main(["scan", str(ORG), "--format", "json", "-o", str(out)])
    cli.main(["scan", str(KEPT), "--format", "json", "-o", str(out)])
    assert json.loads(out.read_text(encoding="utf-8"))["policy"] is None
