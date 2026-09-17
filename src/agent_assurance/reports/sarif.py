"""SARIF 2.1.0 renderer.

SARIF is how findings surface in the GitHub "Security" tab / code scanning.
Emitting it puts agent-assurance inside the ecosystem developers already use,
without a dashboard or backend of our own.
"""

from __future__ import annotations

import json

from .. import __version__
from ..checks.base import Status
from ..engine import AssuranceReport

# SARIF levels: error / warning / note.
_LEVEL = {Status.FAIL: "error", Status.REVIEW: "warning", Status.PASS: "note"}
_TOOL_URI = "https://github.com/kunko-ai-labs/agent-assurance"

# Code scanning needs a location it can resolve inside the repo. The manifest is
# the artifact under review, so findings anchor there. Line 1 is deliberate: the
# finding is a property of the manifest as a whole, not of a single line.
_DEFAULT_MANIFEST = "agent-assurance.yaml"
_ANCHOR_LINE = 1


def to_dict(report: AssuranceReport, manifest_path: str = _DEFAULT_MANIFEST) -> dict:
    rules = []
    results = []
    seen_rules: set[str] = set()
    agent = report.manifest.agent.name

    for r in report.results:
        if r.check_id not in seen_rules:
            seen_rules.add(r.check_id)
            standards = ", ".join(
                f"{s.framework}:{s.control}" for s in r.standards
            )
            rules.append(
                {
                    "id": r.check_id,
                    "name": r.title.replace(" ", ""),
                    "shortDescription": {"text": r.title},
                    "fullDescription": {
                        "text": f"{r.title}. Standards: {standards}"
                        if standards
                        else r.title
                    },
                    "helpUri": _TOOL_URI,
                    # A rule's default severity is a property of the rule, not
                    # of one run's outcome; the per-result level carries that.
                    "defaultConfiguration": {"level": "error"},
                    "properties": {
                        "tags": ["agent-assurance", "ai-security"],
                        "standards": standards,
                    },
                }
            )
        # A check that knows where the finding lives (scan) anchors there;
        # otherwise the manifest as a whole.
        anchors = [(loc.path, loc.line) for loc in r.locations] or [(manifest_path, _ANCHOR_LINE)]
        results.append(
            {
                "ruleId": r.check_id,
                # kind=pass keeps a clean check out of the Security tab: GitHub
                # only raises alerts for kind=fail (the default).
                "kind": "pass" if r.status is Status.PASS else "fail",
                "level": _LEVEL[r.status],
                "message": {"text": f"{r.summary}\n" + "\n".join(r.details)},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": path},
                            "region": {"startLine": line},
                        }
                    }
                    for path, line in anchors
                ],
                # Stable across runs so code scanning tracks one finding over
                # time instead of opening a new alert on every push.
                "partialFingerprints": {
                    "agentAssurance/v1": f"{r.check_id}:{agent}:{manifest_path}"
                },
            }
        )

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "agent-assurance",
                        "version": __version__,
                        "semanticVersion": __version__,
                        "informationUri": _TOOL_URI,
                        "rules": rules,
                    }
                },
                "automationDetails": {"id": f"agent-assurance/{agent}/"},
                "results": results,
            }
        ],
    }


def to_sarif(report: AssuranceReport, manifest_path: str = _DEFAULT_MANIFEST) -> str:
    return json.dumps(to_dict(report, manifest_path), indent=2, ensure_ascii=False)
