"""Contract tests for the CLI: exit codes and SARIF shape.

The GitHub Action and any CI consumer rely on exactly this contract:
  0 = pass (or review without --fail-on review), 1 = gate tripped, 2 = usage error.
A change here is a breaking change for every pipeline using the Action.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from agent_assurance import cli

EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"
SAFE = str(EXAMPLES / "safe-agent.yaml")
HIGH = str(EXAMPLES / "high-agent.yaml")
DANGEROUS = str(EXAMPLES / "dangerous-agent.yaml")


# --- exit codes -------------------------------------------------------------


@pytest.mark.parametrize(
    ("manifest", "fail_on", "expected"),
    [
        (SAFE, "fail", cli.EXIT_OK),
        (SAFE, "review", cli.EXIT_OK),
        (HIGH, "fail", cli.EXIT_OK),  # REVIEW does not gate by default
        (HIGH, "review", cli.EXIT_GATE),  # ...but does when asked
        (DANGEROUS, "fail", cli.EXIT_GATE),
        (DANGEROUS, "review", cli.EXIT_GATE),
    ],
)
def test_check_exit_codes(capsys, manifest, fail_on, expected):
    code = cli.main(["check", "all", manifest, "--fail-on", fail_on])
    assert code == expected
    assert isinstance(code, int)


def test_missing_manifest_is_usage_error(capsys):
    assert cli.main(["check", "all", "does/not/exist.yaml"]) == cli.EXIT_USAGE
    assert "not found" in capsys.readouterr().err


def test_invalid_manifest_is_usage_error(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("apiVersion: nope/v0\nagent: {name: x}\n", encoding="utf-8")
    assert cli.main(["check", "all", str(bad)]) == cli.EXIT_USAGE
    assert cli.main(["validate", str(bad)]) == cli.EXIT_USAGE


def test_unknown_check_is_usage_error(capsys):
    assert cli.main(["check", "AA-999", SAFE]) == cli.EXIT_USAGE


def test_validate_ok():
    assert cli.main(["validate", SAFE]) == cli.EXIT_OK


def test_output_file_is_written(tmp_path):
    out = tmp_path / "report.md"
    cli.main(["check", "all", SAFE, "--format", "md", "-o", str(out)])
    assert "Agent Assurance" in out.read_text(encoding="utf-8")


# --- SARIF ------------------------------------------------------------------


def _sarif_for(manifest: str, tmp_path) -> dict:
    out = tmp_path / "aa.sarif"
    cli.main(["check", "all", manifest, "--format", "sarif", "-o", str(out)])
    return json.loads(out.read_text(encoding="utf-8"))


def test_sarif_points_at_the_real_manifest(tmp_path):
    """Code scanning drops findings whose file does not exist in the repo."""
    sarif = _sarif_for(DANGEROUS, tmp_path)
    run = sarif["runs"][0]
    result = run["results"][0]
    loc = result["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == DANGEROUS
    assert loc["region"]["startLine"] >= 1
    assert DANGEROUS in result["partialFingerprints"]["agentAssurance/v1"]


def test_sarif_fail_is_an_error_alert(tmp_path):
    result = _sarif_for(DANGEROUS, tmp_path)["runs"][0]["results"][0]
    assert result["kind"] == "fail"
    assert result["level"] == "error"


def test_sarif_review_is_a_warning_alert(tmp_path):
    result = _sarif_for(HIGH, tmp_path)["runs"][0]["results"][0]
    assert result["kind"] == "fail"
    assert result["level"] == "warning"


def test_sarif_pass_does_not_raise_an_alert(tmp_path):
    """A clean check must not show up as noise in the Security tab."""
    result = _sarif_for(SAFE, tmp_path)["runs"][0]["results"][0]
    assert result["kind"] == "pass"


def test_sarif_driver_metadata(tmp_path):
    run = _sarif_for(SAFE, tmp_path)["runs"][0]
    driver = run["tool"]["driver"]
    assert driver["name"] == "agent-assurance"
    assert driver["version"] == cli.__version__
    assert driver["rules"][0]["id"] == "AA-001"
    assert driver["rules"][0]["defaultConfiguration"]["level"] == "error"
    assert run["automationDetails"]["id"].startswith("agent-assurance/")
