"""Solution preparation (compilation) and test execution."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .spec import Spec, TestCase, compare


class CompileError(RuntimeError):
    """Raised when a solution cannot be compiled or launched."""


@dataclass(frozen=True)
class PreparedSolution:
    command: tuple
    kind: str  # "python" | "c++" | "c"


@dataclass(frozen=True)
class CaseResult:
    name: str
    hidden: bool
    verdict: str  # OK | WA | TLE | RE
    time_ms: float
    message: str
    stdout: str = ""
    stderr: str = ""


def prepare_solution(solution: str | Path, build_dir: str | Path) -> PreparedSolution:
    """Turn a source file into an executable command (compiling C/C++ if needed)."""
    solution = Path(solution).resolve()
    if not solution.is_file():
        raise CompileError(f"solution not found: {solution}")
    suffix = solution.suffix.lower()
    if suffix == ".py":
        return PreparedSolution((sys.executable, str(solution)), "python")

    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    if suffix in (".cpp", ".cc", ".cxx"):
        compiler = os.environ.get("CXX", "g++")
        std, kind = "-std=c++17", "c++"
    elif suffix == ".c":
        compiler = os.environ.get("CC", "gcc")
        std, kind = "-std=c11", "c"
    else:
        raise CompileError(f"unsupported solution type {suffix!r} (use .py, .c or .cpp)")
    if shutil.which(compiler) is None:
        raise CompileError(f"compiler not found on PATH: {compiler}")

    exe = build_dir / (solution.stem + (".exe" if os.name == "nt" else ""))
    proc = subprocess.run(
        [compiler, "-O2", "-pipe", std, str(solution), "-o", str(exe)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if proc.returncode != 0:
        raise CompileError("compilation failed:\n" + (proc.stderr or proc.stdout).strip())
    return PreparedSolution((str(exe),), kind)


def _clip(text: str, limit: int = 300) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def run_test_case(
    command: tuple,
    case: TestCase,
    *,
    time_limit_s: float,
    comparison: str,
) -> CaseResult:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            list(command),
            input=case.input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=time_limit_s,
        )
    except subprocess.TimeoutExpired:
        elapsed = (time.perf_counter() - start) * 1000.0
        return CaseResult(
            case.name,
            case.hidden,
            "TLE",
            elapsed,
            f"exceeded time limit of {time_limit_s * 1000:.0f} ms",
        )
    except OSError as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return CaseResult(case.name, case.hidden, "RE", elapsed, f"failed to launch: {exc}")
    elapsed = (time.perf_counter() - start) * 1000.0

    if proc.returncode != 0:
        detail = f"exit code {proc.returncode}"
        stderr_tail = _clip(proc.stderr or "", 400)
        if stderr_tail:
            detail += f": {stderr_tail}"
        return CaseResult(case.name, case.hidden, "RE", elapsed, detail, stderr=stderr_tail)

    if not compare(comparison, proc.stdout, case.expected):
        if case.hidden:
            message = "output mismatch (input withheld)"
        else:
            message = f"expected {_clip(case.expected)!r}, got {_clip(proc.stdout)!r}"
        return CaseResult(
            case.name, case.hidden, "WA", elapsed, message, stdout=_clip(proc.stdout, 400)
        )
    return CaseResult(case.name, case.hidden, "OK", elapsed, "accepted")


def run_challenge(
    spec: Spec,
    solution: str | Path,
    *,
    include_hidden: bool = True,
) -> tuple:
    """Run a solution against every test. Returns (prepared, results, compile_ms)."""
    build_dir = Path(tempfile.mkdtemp(prefix="puzzlebench-build-"))
    try:
        start = time.perf_counter()
        prepared = prepare_solution(solution, build_dir)
        compile_ms = (time.perf_counter() - start) * 1000.0

        time_limit_s = spec.time_limit_ms / 1000.0
        results = []
        for case in spec.tests:
            if case.hidden and not include_hidden:
                continue
            results.append(
                run_test_case(
                    prepared.command,
                    case,
                    time_limit_s=time_limit_s,
                    comparison=spec.comparison,
                )
            )
        return prepared, results, compile_ms
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
