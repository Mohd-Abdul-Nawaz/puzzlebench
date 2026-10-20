"""Challenge specifications and test loading."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class SpecError(ValueError):
    """Raised when a challenge specification is missing or malformed."""


@dataclass(frozen=True)
class TestCase:
    name: str
    input: str
    expected: str
    hidden: bool = False


@dataclass(frozen=True)
class Spec:
    id: str
    title: str
    difficulty: str
    time_limit_ms: int
    comparison: str
    statement: str
    tags: tuple
    root: Path
    tests: tuple


def default_challenges_dir() -> Path:
    env = os.environ.get("PUZZLEBENCH_CHALLENGES")
    if env:
        return Path(env)
    cwd_challenges = Path.cwd() / "challenges"
    if cwd_challenges.is_dir():
        return cwd_challenges
    return Path(__file__).resolve().parent.parent / "challenges"


def compare(comparison: str, actual: str, expected: str) -> bool:
    """Compare a program's stdout with the expected output."""
    if comparison == "tokens":
        return actual.split() == expected.split()
    if comparison == "exact":
        normalize = lambda text: text.replace("\r\n", "\n").replace("\r", "\n")
        return normalize(actual) == normalize(expected)
    raise SpecError(f"unknown comparison mode: {comparison!r}")


def _read_json(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SpecError(f"missing file: {path}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SpecError(f"invalid JSON in {path}: {exc}") from exc


def load_spec(challenge_dir: str | Path) -> Spec:
    root = Path(challenge_dir)
    spec_path = root / "spec.json"
    data = _read_json(spec_path)
    if not isinstance(data, dict):
        raise SpecError(f"{spec_path}: top-level value must be an object")
    for key in ("id", "title", "time_limit_ms", "comparison", "tests"):
        if key not in data:
            raise SpecError(f"{spec_path}: missing required field {key!r}")
    if data["comparison"] not in ("tokens", "exact"):
        raise SpecError(
            f"{spec_path}: comparison must be 'tokens' or 'exact', got {data['comparison']!r}"
        )
    if int(data["time_limit_ms"]) <= 0:
        raise SpecError(f"{spec_path}: time_limit_ms must be positive")

    tests = []
    seen_names = set()
    for rel in data["tests"]:
        entries = _read_json(root / rel)
        if not isinstance(entries, list):
            raise SpecError(f"{root / rel}: test file must be a JSON array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise SpecError(f"{root / rel}: each test must be an object")
            for key in ("name", "input", "expected"):
                if key not in entry:
                    raise SpecError(f"{root / rel}: test is missing required field {key!r}")
            name = str(entry["name"])
            if name in seen_names:
                raise SpecError(f"{root}: duplicate test name {name!r}")
            seen_names.add(name)
            tests.append(
                TestCase(
                    name=name,
                    input=str(entry["input"]),
                    expected=str(entry["expected"]),
                    hidden=bool(entry.get("hidden", False)),
                )
            )
    if not tests:
        raise SpecError(f"{root}: challenge defines no tests")
    if all(t.hidden for t in tests):
        raise SpecError(f"{root}: at least one test must be public")

    statement_path = root / str(data.get("statement", "statement.md"))
    statement = statement_path.read_text(encoding="utf-8") if statement_path.is_file() else ""

    tags: Iterable = data.get("tags", ())
    if not isinstance(tags, (list, tuple)) or not all(isinstance(t, str) for t in tags):
        raise SpecError(f"{spec_path}: tags must be a list of strings")

    return Spec(
        id=str(data["id"]),
        title=str(data["title"]),
        difficulty=str(data.get("difficulty", "unknown")),
        time_limit_ms=int(data["time_limit_ms"]),
        comparison=str(data["comparison"]),
        statement=statement,
        tags=tuple(tags),
        root=root,
        tests=tuple(tests),
    )


def discover_challenges(challenges_dir: str | Path) -> dict:
    """Return {challenge_id: directory} for every direct child with a spec.json."""
    base = Path(challenges_dir)
    if not base.is_dir():
        raise SpecError(f"challenges directory not found: {base}")
    found: dict = {}
    for child in sorted(base.iterdir()):
        if child.is_dir() and (child / "spec.json").is_file():
            data = _read_json(child / "spec.json")
            cid = str(data.get("id", child.name)) if isinstance(data, dict) else child.name
            if cid in found:
                raise SpecError(f"duplicate challenge id {cid!r}")
            found[cid] = child
    return found
