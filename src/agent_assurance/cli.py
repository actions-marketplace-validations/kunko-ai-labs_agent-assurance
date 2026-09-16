"""agent-assurance CLI.

Commands:
  agent-assurance validate <manifest>
  agent-assurance check [blast-radius|all] <manifest> [--format md|json|sarif] [--output FILE]

Exit codes: 0 = pass/review, 1 = FAIL, 2 = usage/manifest error.
Use --fail-on {fail,review} to control what gates the pipeline.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__, engine, reports
from .checks import CHECK_ALIASES
from .checks.base import Status
from .manifest import Manifest, ManifestError

_FORMATS = {
    "md": reports.to_markdown,
    "markdown": reports.to_markdown,
    "json": reports.to_json,
    "sarif": reports.to_sarif,
}


def _load(path: str) -> Manifest:
    try:
        return Manifest.from_file(path)
    except FileNotFoundError:
        print(f"error: manifest not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


def _resolve_checks(name: str) -> list[str] | None:
    if name in ("all", "*"):
        return None
    cid = CHECK_ALIASES.get(name, name)
    return [cid]


def cmd_validate(args: argparse.Namespace) -> int:
    m = _load(args.manifest)
    print(f"ok: {args.manifest} is a valid agent-assurance/v1 manifest")
    print(f"    agent={m.agent.name} v{m.agent.version} autonomy=L{m.autonomy} "
          f"tools={len(m.tools)} data={len(m.data)}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    m = _load(args.manifest)
    try:
        check_ids = _resolve_checks(args.check)
        report = engine.run(m, check_ids)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    renderer = _FORMATS[args.format]
    output = renderer(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"wrote {args.format} report to {args.output}", file=sys.stderr)
    else:
        print(output)

    gate_fail = report.verdict is Status.FAIL
    gate_review = report.verdict in (Status.FAIL, Status.REVIEW)
    if args.fail_on == "review" and gate_review:
        return 1
    if args.fail_on == "fail" and gate_fail:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-assurance",
        description="Transparent, framework-agnostic assurance checks for AI agents.",
    )
    p.add_argument("--version", action="version", version=f"agent-assurance {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pv = sub.add_parser("validate", help="validate a manifest")
    pv.add_argument("manifest")
    pv.set_defaults(func=cmd_validate)

    pc = sub.add_parser("check", help="run assurance checks")
    pc.add_argument("check", help="check name (e.g. blast-radius) or 'all'")
    pc.add_argument("manifest")
    pc.add_argument("--format", choices=list(_FORMATS.keys()), default="md")
    pc.add_argument("--output", "-o", default=None, help="write report to a file")
    pc.add_argument(
        "--fail-on",
        choices=["fail", "review"],
        default="fail",
        help="exit 1 on FAIL (default) or on REVIEW too",
    )
    pc.set_defaults(func=cmd_check)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
