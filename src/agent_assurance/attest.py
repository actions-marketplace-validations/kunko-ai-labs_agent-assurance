"""Evidence that survives the repo: an in-toto Statement about what the agent
could do at a given commit, and whether it matched the promise.

`build()` produces an in-toto Statement v1 (https://in-toto.io/Statement/v1):

  subject        the files the verdict was computed from (manifest + every
                 parsed configuration file), each with its sha256
  predicateType  https://github.com/kunko-ai-labs/agent-assurance/attestation/v1
  predicate      tool version, timestamp, git commit if available, the declared
                 manifest, the observed manifest, the full report and sources

Unsigned, the statement is an audit record you can archive next to a release:
"at commit X, the configuration granted Y, the promise said Z, verdict W". In
GitHub Actions, `actions/attest` signs it with Sigstore and binds it to the
workflow identity (input `attest: "true"`), and `gh attestation verify` checks
it later. That is the shape EU AI Act art. 12 (record-keeping that allows
reconstruction) and SOC 2 change-management reviewers ask for; the mapping is
`adapted`, not a conformance claim.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess

from . import __version__, engine
from .reports.json_report import to_dict as report_dict

PREDICATE_TYPE = "https://github.com/kunko-ai-labs/agent-assurance/attestation/v1"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(root: str, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, check=True, timeout=5
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def subjects_for(root: str, manifest_path: str | None, report: engine.AssuranceReport) -> list[dict]:
    """Files the verdict depends on, with digests. Paths are repo-relative."""
    files: list[str] = []
    if manifest_path and os.path.isfile(manifest_path):
        files.append(manifest_path)
    for src in report.sources:
        if src.supported:
            files.append(os.path.join(root, src.path))
    out = []
    for f in files:
        rel = os.path.relpath(f, root) if os.path.isabs(f) or f.startswith(root) else f
        out.append({"name": rel.replace(os.sep, "/"), "digest": {"sha256": _sha256(f)}})
    return out


def build(root: str, manifest_path: str | None, report: engine.AssuranceReport) -> dict:
    commit = _git(root, "rev-parse", "HEAD")
    predicate = {
        "tool": {"name": "agent-assurance", "version": __version__},
        "generatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "git": {"commit": commit, "dirty": bool(_git(root, "status", "--porcelain"))} if commit else None,
        "declared": report.declared.model_dump(mode="json") if report.declared else None,
        "observed": report.manifest.model_dump(mode="json"),
        "report": report_dict(report),
        "standards": sorted(
            {f"{s.framework}:{s.control}" for r in report.results for s in r.standards}
        ),
    }
    return {
        "_type": STATEMENT_TYPE,
        "subject": subjects_for(root, manifest_path, report),
        "predicateType": PREDICATE_TYPE,
        "predicate": predicate,
    }


def to_json(statement: dict) -> str:
    return json.dumps(statement, indent=2, ensure_ascii=False)
