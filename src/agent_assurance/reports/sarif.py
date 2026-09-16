"""SARIF 2.1.0 renderer.

SARIF is how findings surface in the GitHub "Security" tab / code scanning.
Emitting it puts agent-assurance inside the ecosystem developers already use,
without a dashboard or backend of our own.
"""

from __future__ import annotations

import json

from ..checks.base import Status
from ..engine import AssuranceReport

# SARIF levels: error / warning / note.
_LEVEL = {Status.FAIL: "error", Status.REVIEW: "warning", Status.PASS: "note"}
_TOOL_URI = "https://github.com/kunko-ai/agent-assurance"


def to_dict(report: AssuranceReport, manifest_path: str = "agent-assurance.yaml") -> dict:
    rules = []
    results = []
    seen_rules: set[str] = set()

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
                    "properties": {"tags": ["agent-assurance", "ai-security"]},
                }
            )
        results.append(
            {
                "ruleId": r.check_id,
                "level": _LEVEL[r.status],
                "message": {"text": f"{r.summary}\n" + "\n".join(r.details)},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": manifest_path},
                        }
                    }
                ],
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
                        "informationUri": _TOOL_URI,
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def to_sarif(report: AssuranceReport, manifest_path: str = "agent-assurance.yaml") -> str:
    return json.dumps(to_dict(report, manifest_path), indent=2, ensure_ascii=False)
