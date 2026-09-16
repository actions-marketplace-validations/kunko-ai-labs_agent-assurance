"""Tests for the manifest loader and the risk/blast-radius pipeline.

These lock in the transparent contract: known manifests -> known bands.
Run: pytest
"""

from __future__ import annotations

import pathlib

import pytest

from agent_assurance import engine
from agent_assurance.checks.base import Status
from agent_assurance.manifest import Manifest, ManifestError

EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"


def _report_for(name: str):
    m = Manifest.from_file(str(EXAMPLES / name))
    return engine.run(m, ["AA-001"])


def test_safe_agent_passes():
    report = _report_for("safe-agent.yaml")
    assert report.verdict is Status.PASS
    assert report.passed is True
    r = report.results[0]
    assert r.data["band"] == "LOW"


def test_medium_agent_is_not_critical():
    report = _report_for("medium-agent.yaml")
    # crm.read(1) + crm.write(3) + ticket.create write(3) + pii(3) = 10 -> MEDIUM
    r = report.results[0]
    assert r.data["band"] == "MEDIUM"
    assert report.verdict is Status.PASS


def test_dangerous_agent_is_critical_and_fails():
    report = _report_for("dangerous-agent.yaml")
    r = report.results[0]
    assert r.data["band"] == "CRITICAL"
    assert report.verdict is Status.FAIL
    assert report.passed is False
    # Irreversible + financial + credential + production must surface.
    assert "bank.transfer" in r.data["irreversible_actions"]
    assert "aws.delete" in r.data["irreversible_actions"]
    assert "email.send" in r.data["external_side_effects"]
    assert "credential" in r.data["data_classes"]


def test_risk_breakdown_is_transparent():
    """Every point must be attributable to a named factor (no black box)."""
    report = _report_for("dangerous-agent.yaml")
    r = report.results[0]
    total = sum(f["points"] for f in r.data["factors"])
    assert total == r.data["score"]
    assert all(f["reason"] for f in r.data["factors"])


def test_standards_mapping_present():
    report = _report_for("safe-agent.yaml")
    frameworks = {s.framework for s in report.results[0].standards}
    assert "OWASP-ASI" in frameworks


def test_bad_apiversion_rejected():
    with pytest.raises(ManifestError):
        Manifest.load({"apiVersion": "wrong/v9", "agent": {"name": "x"}})


def test_missing_agent_rejected():
    with pytest.raises(ManifestError):
        Manifest.load({"apiVersion": "agent-assurance/v1"})
