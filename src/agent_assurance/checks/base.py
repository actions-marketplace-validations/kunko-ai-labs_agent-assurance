"""Check framework: the base types every assurance check implements.

A check consumes a Manifest and returns a CheckResult. Checks map to standards
(primarily OWASP Agentic Top 10 / ASI; APTS where the control genuinely
transfers from the pentest domain). Keeping this contract tiny is what lets the
GitHub Action stay a thin wrapper over a growing set of checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from ..manifest import Manifest


class Status(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


@dataclass
class StandardRef:
    """A mapping from a check to a published standard control.

    `relation` is honest about strength:
      - "maps"        : the control is directly about this (business agents)
      - "adapted"     : transferred from a neighbouring domain (e.g. APTS pentest)
    """

    framework: str  # "OWASP-ASI", "OWASP-APTS", "arXiv"
    control: str  # "ASI08", "APTS-SC-020", "2609.07395"
    relation: str = "maps"


@dataclass
class CheckResult:
    check_id: str
    title: str
    status: Status
    summary: str
    details: list[str] = field(default_factory=list)
    standards: list[StandardRef] = field(default_factory=list)
    # Machine-readable extras for JSON/SARIF consumers.
    data: dict = field(default_factory=dict)


class Check:
    """Base class. Subclasses set id/title/standards and implement run()."""

    check_id: str = "AA-000"
    title: str = "Unnamed check"
    standards: ClassVar[list[StandardRef]] = []

    def run(self, manifest: Manifest) -> CheckResult:  # pragma: no cover - abstract
        raise NotImplementedError
