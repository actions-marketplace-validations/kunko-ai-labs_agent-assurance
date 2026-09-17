"""diff: what did this change do to the agent's reach and its promise?"""

from __future__ import annotations

import json
import pathlib
import shutil

from agent_assurance import cli, diff

REPOS = pathlib.Path(__file__).resolve().parents[1] / "examples" / "repos"
KEPT = str(REPOS / "mcp-promise-kept")
BROKEN = str(REPOS / "mcp-promise-broken")
UNKNOWN = str(REPOS / "mcp-unknown-server")


def test_no_change_is_no_delta():
    d = diff.compute(KEPT, KEPT)
    assert d is not None and not d.has_delta and not d.regressed
    assert "No change" in diff.to_markdown(d)


def test_cosmetic_change_is_no_delta(tmp_path):
    shutil.copytree(KEPT, tmp_path / "head")
    f = tmp_path / "head" / ".mcp.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    # reorder servers + reformat: same capabilities
    data["mcpServers"] = dict(reversed(list(data["mcpServers"].items())))
    f.write_text(json.dumps(data, indent=4), encoding="utf-8")
    d = diff.compute(KEPT, str(tmp_path / "head"))
    assert not d.has_delta


def test_promise_broken_by_change():
    d = diff.compute(KEPT, BROKEN)
    assert d.band_from == "LOW" and d.band_to == "HIGH" and d.band_up
    assert d.promise_from.value == "PASS" and d.promise_to.value == "FAIL"
    assert d.promise_regressed and d.regressed
    assert any("github.write" in x for x in d.newly_broken)
    assert {t.system for t in d.added} == {"github", "slack"}
    assert d.removed == []
    md = diff.to_markdown(d)
    assert "PROMISE BROKEN BY THIS CHANGE" in md and "LOW → **HIGH**" in md


def test_promise_fixed_by_change():
    d = diff.compute(BROKEN, KEPT)
    assert d.band_down and not d.regressed
    assert d.fixed and d.newly_broken == []
    assert {t.system for t in d.removed} == {"github", "slack"}
    assert "Fixed" in diff.to_markdown(d)


def test_new_unknown_is_a_regression(tmp_path):
    shutil.copytree(KEPT, tmp_path / "head")
    f = tmp_path / "head" / ".mcp.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["mcpServers"]["mystery"] = {"command": "node", "args": ["srv.js"]}
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")
    d = diff.compute(KEPT, str(tmp_path / "head"))
    assert d.regressed  # unknown is not read, so reach grew into the unknown
    assert d.promise_to.value == "REVIEW"


def test_base_without_config_makes_everything_new(tmp_path):
    (tmp_path / "base").mkdir()
    shutil.copy(pathlib.Path(KEPT) / "agent-assurance.yaml", tmp_path / "base" / "agent-assurance.yaml")
    d = diff.compute(str(tmp_path / "base"), KEPT)
    assert len(d.added) == 2 and not d.regressed  # two reads within the promise


# --- CLI contract -------------------------------------------------------------


def test_cli_diff_gates_on_delta(tmp_path):
    out = tmp_path / "d.md"
    assert cli.main(["diff", KEPT, BROKEN, "-o", str(out)]) == cli.EXIT_GATE  # head FAILs anyway
    assert cli.main(["diff", KEPT, KEPT, "--fail-on-delta", "-o", str(out)]) == cli.EXIT_OK
    assert cli.main(["diff", BROKEN, KEPT, "--fail-on-delta", "-o", str(out)]) == cli.EXIT_OK  # improvement
    assert cli.main(["diff", KEPT, "nope", "-o", str(out)]) == cli.EXIT_USAGE


def test_cli_diff_json_and_sarif_baseline(tmp_path):
    out = tmp_path / "d.json"
    cli.main(["diff", KEPT, BROKEN, "--format", "json", "-o", str(out)])
    j = json.loads(out.read_text(encoding="utf-8"))
    assert j["kind"] == "diff" and j["regressed"] and j["band"] == {"from": "LOW", "to": "HIGH"}
    assert j["promise"]["from"] == "PASS" and j["promise"]["to"] == "FAIL"

    sarif = tmp_path / "d.sarif"
    cli.main(["diff", KEPT, BROKEN, "--format", "sarif", "-o", str(sarif)])
    s = json.loads(sarif.read_text(encoding="utf-8"))
    states = {r["ruleId"]: r["baselineState"] for r in s["runs"][0]["results"]}
    assert states == {"AA-001": "new", "AA-002": "new"}

    cli.main(["diff", BROKEN, BROKEN, "--format", "sarif", "-o", str(sarif)])
    s = json.loads(sarif.read_text(encoding="utf-8"))
    states = {r["ruleId"]: r["baselineState"] for r in s["runs"][0]["results"]}
    assert states == {"AA-001": "unchanged", "AA-002": "unchanged"}
