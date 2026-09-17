"""Codex config.toml and serialized tool definitions (inferred classes)."""

from __future__ import annotations

import json
import pathlib

from agent_assurance import cli
from agent_assurance.manifest import ToolAccess
from agent_assurance.scan import scan_directory
from agent_assurance.scan.tool_defs import classify

REPOS = pathlib.Path(__file__).resolve().parents[1] / "examples" / "repos"
CT = str(REPOS / "codex-and-tools")


def test_codex_toml_servers_share_the_mcp_classification():
    r = scan_directory(CT)
    codex = next(s for s in r.sources if s.path == ".codex/config.toml")
    assert codex.supported and "github: github" in codex.note
    by = {t.name: t for t in r.observed.tools}
    assert by["github.write"].type is ToolAccess.WRITE and by["github.write"].source == ".codex/config.toml:4"
    assert by["acme-crm.remote"].type is ToolAccess.EXTERNAL_SEND and by["acme-crm.remote"].source == ".codex/config.toml:9"
    assert "acme-crm" in r.unknowns
    assert any(d.type.value == "credential" and d.systems == ["github"] for d in r.observed.data)


def test_tool_definitions_are_inferred_and_marked():
    r = scan_directory(CT)
    by = {t.name: t for t in r.observed.tools}
    assert by["crm.search_contacts"].type is ToolAccess.READ and by["crm.search_contacts"].inferred
    assert by["crm.update_contact"].type is ToolAccess.WRITE and by["crm.update_contact"].system == "crm"
    assert by["billing.issue_refund"].type is ToolAccess.FINANCIAL and by["billing.issue_refund"].inferred
    assert by["wibble"].type is ToolAccess.UNKNOWN and not by["wibble"].inferred
    assert by["billing.issue_refund"].source == "agent-tools.json:19"


def test_inferred_breaking_class_is_review_not_broken(tmp_path):
    out = tmp_path / "r.json"
    cli.main(["scan", CT, "--format", "json", "-o", str(out)])
    r = json.loads(out.read_text(encoding="utf-8"))
    aa2 = next(c for c in r["checks"] if c["id"] == "AA-002")
    # the GitHub token from Codex is a catalogue/config fact -> broken; issue_refund is a guess -> review
    assert any("credential" in m and "github" in m for m in aa2["data"]["broken"])
    assert any("billing.issue_refund" in m and "inferred" in m for m in aa2["data"]["review"])
    assert not any("billing.issue_refund" in m for m in aa2["data"]["broken"])


def test_classify_table():
    assert classify("send_email") is ToolAccess.EXTERNAL_SEND
    assert classify("deleteRecord") is ToolAccess.UNKNOWN  # camelCase is not split; honest UNKNOWN
    assert classify("delete_record") is ToolAccess.DELETE
    assert classify("run_query") is ToolAccess.EXECUTE  # 'run' wins over 'query': execute is checked first
    assert classify("thing", "Transfer funds between accounts") is ToolAccess.FINANCIAL
    assert classify("thing", "") is ToolAccess.UNKNOWN


def test_policy_can_add_tool_definition_files(tmp_path):
    (tmp_path / "defs.yaml").write_text("tools:\n  - name: notify_ops\n    description: Post to Slack\n    parameters: {}\n", encoding="utf-8")
    (tmp_path / "agent-assurance.policy.yaml").write_text(
        "apiVersion: agent-assurance/policy/v1\nname: t\ntool_definition_files: [defs.yaml]\n", encoding="utf-8"
    )
    out = tmp_path / "r.json"
    assert cli.main(["scan", str(tmp_path), "--format", "json", "-o", str(out)]) == cli.EXIT_OK
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["checks"][0]["data"]["external_side_effects"] == ["notify_ops"]
