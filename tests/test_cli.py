"""CLI behaviour tests: exit codes, output, JSON reports, verify command."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from puzzlebench.cli import main

CHALLENGES = REPO / "challenges"
SOLUTIONS = REPO / "solutions"


class CliTests(unittest.TestCase):
    def _run(self, *argv: str):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_list_prints_all_challenge_ids(self):
        code, out, _ = self._run("list", "--challenges-dir", str(CHALLENGES))
        self.assertEqual(code, 0)
        for cid in ("two-sum", "lis", "shortest-path"):
            self.assertIn(cid, out)

    def test_show_prints_statement(self):
        code, out, _ = self._run("show", "lis", "--challenges-dir", str(CHALLENGES))
        self.assertEqual(code, 0)
        self.assertIn("strictly increasing", out)

    def test_run_reference_solution_exits_zero(self):
        code, _, _ = self._run(
            "run", "lis", str(SOLUTIONS / "lis.py"),
            "--challenges-dir", str(CHALLENGES), "--quiet",
        )
        self.assertEqual(code, 0)

    def test_run_buggy_solution_exits_one(self):
        code, _, _ = self._run(
            "run", "two-sum", str(SOLUTIONS / "two_sum_bug.py"),
            "--challenges-dir", str(CHALLENGES), "--quiet",
        )
        self.assertEqual(code, 1)

    def test_run_writes_and_emits_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "r.json"
            code, out, _ = self._run(
                "run", "lis", str(SOLUTIONS / "lis.py"),
                "--challenges-dir", str(CHALLENGES),
                "--report", str(report_path), "--json",
            )
            self.assertEqual(code, 0)
            printed = json.loads(out)
            stored = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(printed["verdict_digest"], stored["verdict_digest"])
            self.assertEqual(stored["tool"], "puzzlebench")

    def test_unknown_challenge_exits_two(self):
        code, _, err = self._run(
            "run", "nope", str(SOLUTIONS / "lis.py"), "--challenges-dir", str(CHALLENGES)
        )
        self.assertEqual(code, 2)
        self.assertIn("unknown challenge", err)

    def test_missing_solution_exits_two(self):
        code, _, _ = self._run(
            "run", "lis", str(REPO / "no_such_solution.py"),
            "--challenges-dir", str(CHALLENGES),
        )
        self.assertEqual(code, 2)

    def test_verify_after_run_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "r.json"
            self._run(
                "run", "lis", str(SOLUTIONS / "lis.py"),
                "--challenges-dir", str(CHALLENGES),
                "--report", str(report_path), "--quiet",
            )
            code, out, err = self._run(
                "verify", str(report_path), "--challenges-dir", str(CHALLENGES)
            )
            self.assertEqual(code, 0, f"stdout={out!r} stderr={err!r}")
            self.assertIn("PASS", out)


if __name__ == "__main__":
    unittest.main()
