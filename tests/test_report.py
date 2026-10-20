"""Report determinism, hidden-test privacy, and digest verification tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from puzzlebench.report import build_report, format_results, load_report, verify_report, write_report
from puzzlebench.runner import run_challenge
from puzzlebench.spec import discover_challenges, load_spec

CHALLENGES = REPO / "challenges"
SOLUTIONS = REPO / "solutions"


def _spec(cid: str):
    return load_spec(discover_challenges(CHALLENGES)[cid])


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = _spec("lis")
        cls.solution = SOLUTIONS / "lis.py"
        cls.prepared, cls.results, cls.compile_ms = run_challenge(cls.spec, cls.solution)
        cls.report = build_report(
            cls.spec,
            cls.solution,
            cls.results,
            compile_ms=cls.compile_ms,
            kind=cls.prepared.kind,
        )

    def test_report_has_required_sections(self):
        for key in (
            "tool", "version", "generated_at", "challenge", "solution",
            "environment", "compile_ms", "tests", "summary", "verdict_digest",
        ):
            self.assertIn(key, self.report)
        self.assertEqual(self.report["tool"], "puzzlebench")
        self.assertEqual(self.report["summary"]["failed"], 0)
        self.assertEqual(len(self.report["tests"]), len(self.spec.tests))
        self.assertEqual(len(self.report["verdict_digest"]), 64)

    def test_hidden_inputs_and_expected_outputs_are_not_leaked(self):
        blob = json.dumps(self.report)
        for case in self.spec.tests:
            if not case.hidden:
                continue
            for raw in (case.input, case.expected):
                for needle in (raw.strip(), raw.strip().replace("\n", "\\n")):
                    if len(needle) >= 6:
                        self.assertNotIn(needle, blob, f"leaked hidden test {case.name}")
            self.assertTrue(case.name.startswith("hidden-"))

    def test_verdict_digest_is_deterministic_across_runs(self):
        _, results2, compile2 = run_challenge(self.spec, self.solution)
        report2 = build_report(
            self.spec, self.solution, results2, compile_ms=compile2, kind="python"
        )
        self.assertEqual(self.report["verdict_digest"], report2["verdict_digest"])
        self.assertEqual(
            [t["verdict"] for t in self.report["tests"]],
            [t["verdict"] for t in report2["tests"]],
        )

    def test_write_and_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_report(self.report, path)
            loaded = load_report(path)
            self.assertEqual(loaded["verdict_digest"], self.report["verdict_digest"])
            ok, message = verify_report(path, challenges_dir=CHALLENGES)
            self.assertTrue(ok, message)
            self.assertIn("reproduced", message)

    def test_verify_rejects_modified_solution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_report(self.report, path)
            other = Path(tmp) / "other.py"
            other.write_text("print('tampered')\n", encoding="utf-8")
            ok, message = verify_report(path, challenges_dir=CHALLENGES, solution=other)
            self.assertFalse(ok)
            self.assertIn("changed", message)

    def test_verify_detects_tampered_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            tampered = json.loads(json.dumps(self.report))
            tampered["verdict_digest"] = "0" * 64
            path.write_text(json.dumps(tampered), encoding="utf-8")
            ok, message = verify_report(path, challenges_dir=CHALLENGES)
            self.assertFalse(ok)
            self.assertIn("digest", message)

    def test_format_results_renders_verdicts_and_summary(self):
        text = format_results(
            self.spec, self.solution, self.results, self.compile_ms, "python"
        )
        self.assertIn("[OK ]", text)
        self.assertIn("result: 5/5 passed", text)
        self.assertIn("lis", text)


if __name__ == "__main__":
    unittest.main()
