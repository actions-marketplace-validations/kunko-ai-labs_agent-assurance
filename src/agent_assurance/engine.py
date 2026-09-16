"""Assurance engine: runs checks over a manifest and aggregates the verdict.

The engine is intentionally thin. It is shared by the CLI and the GitHub Action,
so both produce identical results. The overall verdict is the worst status of
any check (FAIL > REVIEW > PASS).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .checks import ALL_CHECKS
from .checks.base import CheckResult, Status
from .manifest import Manifest

# Ordering for "worst wins" aggregation.
_SEVERITY = {Status.PASS: 0, Status.REVIEW: 1, Status.FAIL: 2}


@dataclass
class AssuranceReport:
    manifest: Manifest
    results: list[CheckResult] = field(default_factory=list)

    @property
    def verdict(self) -> Status:
        worst = Status.PASS
        for r in self.results:
            if _SEVERITY[r.status] > _SEVERITY[worst]:
                worst = r.status
        return worst

    @property
    def passed(self) -> bool:
        return self.verdict != Status.FAIL


def run(manifest: Manifest, check_ids: list[str] | None = None) -> AssuranceReport:
    """Run the requested checks (or all of them) against a manifest."""
    selected = check_ids or list(ALL_CHECKS.keys())
    results: list[CheckResult] = []
    for cid in selected:
        check_cls = ALL_CHECKS.get(cid)
        if check_cls is None:
            raise KeyError(f"unknown check id: {cid}")
        results.append(check_cls().run(manifest))
    return AssuranceReport(manifest=manifest, results=results)
