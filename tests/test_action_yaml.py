"""action.yml and the workflows must stay valid YAML with the shape GitHub expects.

A bad step name once took every job down in five seconds; this is cheaper.
"""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_action_yml_is_valid():
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    for inp in ("mode", "directory", "manifest", "check", "fail-on", "sarif", "upload-sarif", "comment", "fail-on-delta", "attest", "card", "policy"):
        assert inp in action["inputs"], inp
    names = [s.get("name", "") for s in action["runs"]["steps"]]
    assert all(isinstance(n, str) for n in names)
    for step in action["runs"]["steps"]:
        assert "run" in step or "uses" in step
        if "run" in step:
            assert step.get("shell") == "bash"


def test_workflows_are_valid():
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        assert doc.get("jobs"), wf.name
        for job in doc["jobs"].values():
            assert job["steps"], wf.name
