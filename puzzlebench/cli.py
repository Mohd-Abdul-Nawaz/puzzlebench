"""Command-line interface for PuzzleBench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import (
    TOOL_VERSION,
    build_report,
    format_results,
    verify_report,
    write_report,
)
from .runner import CompileError, run_challenge
from .spec import SpecError, default_challenges_dir, discover_challenges, load_spec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="puzzlebench",
        description="Reproducible local judge for self-contained coding challenges.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {TOOL_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list available challenges")
    p_list.add_argument("--challenges-dir", type=Path, default=None)

    p_show = sub.add_parser("show", help="print a challenge statement")
    p_show.add_argument("challenge")
    p_show.add_argument("--challenges-dir", type=Path, default=None)

    p_run = sub.add_parser("run", help="run a solution against a challenge")
    p_run.add_argument("challenge", help="challenge id (see `puzzlebench list`)")
    p_run.add_argument("solution", type=Path, help=".py / .c / .cpp solution file")
    p_run.add_argument("--challenges-dir", type=Path, default=None)
    p_run.add_argument("--report", type=Path, default=None, help="write JSON report here")
    p_run.add_argument("--json", action="store_true", help="print JSON report to stdout")
    p_run.add_argument(
        "--no-hidden", action="store_true", help="run public tests only (debug mode)"
    )
    p_run.add_argument("--quiet", "-q", action="store_true", help="suppress human output")

    p_verify = sub.add_parser(
        "verify", help="re-run a previous report and check its verdict digest"
    )
    p_verify.add_argument("report", type=Path)
    p_verify.add_argument("--solution", type=Path, default=None, help="override solution path")
    p_verify.add_argument("--challenges-dir", type=Path, default=None)
    return parser


def _challenges_dir(args: argparse.Namespace) -> Path:
    return Path(args.challenges_dir) if args.challenges_dir else default_challenges_dir()


def _resolve_challenge(challenge_id: str, base: Path) -> Path:
    dirs = discover_challenges(base)
    if challenge_id in dirs:
        return dirs[challenge_id]
    available = ", ".join(dirs) or "(none)"
    raise SpecError(f"unknown challenge {challenge_id!r}; available: {available}")


def _cmd_list(args: argparse.Namespace) -> int:
    dirs = discover_challenges(_challenges_dir(args))
    if not dirs:
        print(f"no challenges found in {_challenges_dir(args)}")
        return 0
    print(f"{'ID':<18} {'DIFFICULTY':<10} {'TESTS':<6} {'TL (ms)':<8} TITLE")
    for cid, path in dirs.items():
        spec = load_spec(path)
        hidden = sum(1 for t in spec.tests if t.hidden)
        tests = f"{len(spec.tests)} ({hidden} hidden)"
        print(f"{spec.id:<18} {spec.difficulty:<10} {tests:<14} {spec.time_limit_ms:<8} {spec.title}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    spec = load_spec(_resolve_challenge(args.challenge, _challenges_dir(args)))
    print(f"{spec.title}  [{spec.id}]  difficulty: {spec.difficulty}")
    print(f"time limit: {spec.time_limit_ms} ms | comparison: {spec.comparison} | tags: {', '.join(spec.tags) or '-'}")
    print("-" * 60)
    print(spec.statement or "(no statement.md)")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        challenge_dir = _resolve_challenge(args.challenge, _challenges_dir(args))
        spec = load_spec(challenge_dir)
        prepared, results, compile_ms = run_challenge(
            spec, args.solution, include_hidden=not args.no_hidden
        )
    except SpecError as exc:
        print(f"spec error: {exc}", file=sys.stderr)
        return 2
    except CompileError as exc:
        print(f"CE: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = build_report(
        spec, args.solution, results, compile_ms=compile_ms, kind=prepared.kind
    )
    if args.report:
        write_report(report, args.report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.quiet:
        print(format_results(spec, Path(args.solution), results, compile_ms, prepared.kind))
        if args.report:
            print(f"report written: {args.report}")

    return 0 if report["summary"]["failed"] == 0 else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        reproduced, message = verify_report(
            args.report,
            challenges_dir=_challenges_dir(args),
            solution=args.solution,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SpecError as exc:
        print(f"spec error: {exc}", file=sys.stderr)
        return 2
    except CompileError as exc:
        print(f"CE: {exc}", file=sys.stderr)
        return 2
    if reproduced:
        print(f"PASS: {message}")
        return 0
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "list": _cmd_list,
        "show": _cmd_show,
        "run": _cmd_run,
        "verify": _cmd_verify,
    }
    try:
        return handlers[args.command](args)
    except SpecError as exc:
        print(f"spec error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
