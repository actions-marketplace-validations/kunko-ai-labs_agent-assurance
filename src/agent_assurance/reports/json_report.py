"""JSON renderer — machine-readable output for pipelines and other tools."""

from __future__ import annotations

import json

from ..engine import AssuranceReport


def to_dict(report: AssuranceReport) -> dict:
    return {
        "apiVersion": "agent-assurance/v1",
        "agent": {
            "name": report.manifest.agent.name,
            "version": report.manifest.agent.version,
        },
        "verdict": report.verdict.value,
        "passed": report.passed,
        "checks": [
            {
                "id": r.check_id,
                "title": r.title,
                "status": r.status.value,
                "summary": r.summary,
                "details": r.details,
                "standards": [
                    {
                        "framework": s.framework,
                        "control": s.control,
                        "relation": s.relation,
                    }
                    for s in r.standards
                ],
                "data": r.data,
            }
            for r in report.results
        ],
    }


def to_json(report: AssuranceReport, indent: int = 2) -> str:
    return json.dumps(to_dict(report), indent=indent, ensure_ascii=False)
