"""End-to-end judge tests: reference solutions pass, planted bugs are caught."""

from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from puzzlebench.runner import run_challenge
from puzzlebench.spec import discover_challenges, load_spec

CHALLENGES = REPO / "challenges"
SOLUTIONS = REPO / "solutions"
HAS_CXX = shutil.which("g++") or shutil.which("clang++")

REFERENCE_SOLUTIONS = {
    "two-sum": ["two_sum.py", "two_sum.cpp"],
    "lis": ["lis.py", "lis.cpp"],
    "shortest-path": ["shortest_path.py", "shortest_path.cpp"],
}
BUGGY_SOLUTIONS = {
    "two-sum": "two_sum_bug.py",
    "lis": "lis_bug.py",
}


def _spec(challenge_id: str):
    return load_spec(discover_challenges(CHALLENGES)[challenge_id])


def _describe(results) -> str:
    return "; ".join(
        f"{r.name}={r.verdict} ({r.message})" for r in results if r.verdict != "OK"
    )


class ReferenceSolutionTests(unittest.TestCase):
    def test_python_references_accept_every_test(self):
        for cid, sols in REFERENCE_SOLUTIONS.items():
            spec = _spec(cid)
            for sol_name in sols:
                if sol_name.endswith((".cpp", ".c")):
                    continue  # compiled separately below
                with self.subTest(challenge=cid, solution=sol_name):
                    _, results, compile_ms = run_challenge(spec, SOLUTIONS / sol_name)
                    bad = [r for r in results if r.verdict != "OK"]
                    self.assertEqual(bad, [], _describe(results))
                    self.assertGreaterEqual(compile_ms, 0.0)

    @unittest.skipUnless(HAS_CXX, "no C++ compiler on PATH")
    def test_cpp_references_accept_every_test(self):
        for cid, sols in REFERENCE_SOLUTIONS.items():
            spec = _spec(cid)
            for sol_name in sols:
                if not sol_name.endswith(".cpp"):
                    continue
                with self.subTest(challenge=cid, solution=sol_name):
                    prepared, results, _ = run_challenge(spec, SOLUTIONS / sol_name)
                    self.assertEqual(prepared.kind, "c++")
                    bad = [r for r in results if r.verdict != "OK"]
                    self.assertEqual(bad, [], _describe(results))


class BuggySolutionTests(unittest.TestCase):
    def test_bugs_pass_public_tests_but_hidden_tests_expose_them(self):
        for cid, sol_name in BUGGY_SOLUTIONS.items():
            with self.subTest(challenge=cid, solution=sol_name):
                spec = _spec(cid)
                _, results, _ = run_challenge(spec, SOLUTIONS / sol_name)
                public = [r for r in results if not r.hidden]
                hidden = [r for r in results if r.hidden]
                self.assertTrue(
                    all(r.verdict == "OK" for r in public),
                    "bug should slip through public tests: " + _describe(results),
                )
                caught = [r for r in hidden if r.verdict != "OK"]
                self.assertTrue(caught, "hidden tests must expose the planted bug")


if __name__ == "__main__":
    unittest.main()
