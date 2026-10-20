"""Reproducible report building, writing and verification."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .runner import CaseResult, run_challenge
from .spec import Spec, default_challenges_dir, discover_challenges, load_spec

TOOL_NAME = "puzzlebench"
TOOL_VERSION = "1.0.0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _compiler_version() -> str | None:
    for candidate in (os.environ.get("CXX", ""), "g++", "clang++", "gcc"):
        if candidate and shutil.which(candidate):
            try:
                proc = subprocess.run(
                    [candidate, "--version"], capture_output=True, text=True, timeout=10
                )
                first = (proc.stdout or proc.stderr).splitlines()[0]
                return f"{candidate} ({first.strip()})"
            except (OSError, subprocess.SubprocessError):
                continue
    return None


def environment_info() -> dict:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "compiler": _compiler_version(),
    }


def verdict_digest(challenge_id: str, solution_sha: str, results: list) -> str:
    payload = "|".join(
        [challenge_id, solution_sha] + [f"{r.name}:{r.verdict}" for r in results]
    )
    return sha256_text(payload)


def build_report(
    spec: Spec,
    solution: str | Path,
    results: list,
    *,
    compile_ms: float,
    kind: str,
) -> dict:
    solution = Path(solution)
    solution_sha = sha256_file(solution)
    inputs_by_name = {t.name: t.input for t in spec.tests}

    tests = []
    for r in results:
        entry = {
            "name": r.name,
            "hidden": r.hidden,
            "verdict": r.verdict,
            "time_ms": round(r.time_ms, 3),
            "message": r.message,
            "input_sha256": sha256_text(inputs_by_name.get(r.name, "")),
        }
        if r.verdict == "WA" and not r.hidden and r.stdout:
            entry["stdout"] = r.stdout
        tests.append(entry)

    passed = sum(1 for r in results if r.verdict == "OK")
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "challenge": {
            "id": spec.id,
            "title": spec.title,
            "difficulty": spec.difficulty,
            "time_limit_ms": spec.time_limit_ms,
            "comparison": spec.comparison,
            "test_count": len(spec.tests),
        },
        "solution": {"path": str(solution), "sha256": solution_sha, "language": kind},
        "environment": environment_info(),
        "compile_ms": round(compile_ms, 3),
        "tests": tests,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "max_time_ms": round(max((r.time_ms for r in results), default=0.0), 3),
        },
        "verdict_digest": verdict_digest(spec.id, solution_sha, results),
    }


def write_report(report: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_report(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"report not found: {path}")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("tool") != TOOL_NAME:
        raise ValueError(f"{path} is not a {TOOL_NAME} report")
    return report


def verify_report(
    report_path: str | Path,
    *,
    challenges_dir: str | Path | None = None,
    solution: str | Path | None = None,
) -> tuple:
    """Re-run a recorded report; return (reproduced, message)."""
    report = load_report(report_path)
    challenge_id = report.get("challenge", {}).get("id")
    base = Path(challenges_dir) if challenges_dir else default_challenges_dir()
    dirs = discover_challenges(base)
    if challenge_id not in dirs:
        return False, f"challenge {challenge_id!r} not found in {base}"
    spec = load_spec(dirs[challenge_id])

    sol = Path(solution) if solution else Path(report["solution"]["path"])
    if not sol.is_file():
        return False, f"solution not found: {sol}"
    current_sha = sha256_file(sol)
    if current_sha != report["solution"]["sha256"]:
        return False, "solution file changed since the report was written"

    prepared, results, _ = run_challenge(spec, sol)
    new_digest = verdict_digest(spec.id, current_sha, results)
    old_digest = report.get("verdict_digest", "")
    if new_digest == old_digest:
        return True, f"reproduced verdict digest {new_digest[:16]}"
    old = {t["name"]: t["verdict"] for t in report.get("tests", [])}
    diffs = [
        f"{r.name}: {old.get(r.name, '?')} -> {r.verdict}"
        for r in results
        if old.get(r.name) != r.verdict
    ]
    detail = "; ".join(diffs) if diffs else "digest mismatch with no verdict changes"
    return False, f"digest {old_digest[:16]} != {new_digest[:16]} ({detail})"


def format_results(spec: Spec, solution: Path, results: list, compile_ms: float, kind: str) -> str:
    lines = [
        f"challenge: {spec.id} ({spec.difficulty})  time limit {spec.time_limit_ms} ms  "
        f"comparison: {spec.comparison}",
        f"solution:  {solution}  [{kind}]  compile {compile_ms:.1f} ms",
    ]
    for r in results:
        mark = {"OK": "OK ", "WA": "WA", "TLE": "TLE", "RE": "RE", "CE": "CE"}.get(
            r.verdict, r.verdict
        )
        scope = "hidden" if r.hidden else "public"
        suffix = "" if r.verdict == "OK" else f"  {r.message}"
        lines.append(f"  [{mark}] {r.name:<20} {scope:<6} {r.time_ms:8.1f} ms{suffix}")
    passed = sum(1 for r in results if r.verdict == "OK")
    failed = len(results) - passed
    outcome = "passed" if failed == 0 else f"failed ({failed} rejected)"
    lines.append(f"result: {passed}/{len(results)} {outcome}")
    return "\n".join(lines)
