"""Verdict tests: OK / WA / TLE / RE / CE detection, including C++ compilation."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from puzzlebench.runner import CompileError, prepare_solution, run_test_case
from puzzlebench.spec import TestCase

HAS_CXX = shutil.which("g++") or shutil.which("clang++")


class VerdictTests(unittest.TestCase):
    def setUp(self):
        self.workdir = Path(tempfile.mkdtemp(prefix="pb-verdict-"))
        self.addCleanup(shutil.rmtree, self.workdir, ignore_errors=True)

    def _run(self, source: str, *, expected: str = "", time_limit_s: float = 2.0,
             hidden: bool = False, stdin: str = ""):
        path = self.workdir / "sol.py"
        path.write_text(source, encoding="utf-8")
        prepared = prepare_solution(path, self.workdir / "build")
        case = TestCase(name="t", input=stdin, expected=expected, hidden=hidden)
        return run_test_case(
            prepared.command, case, time_limit_s=time_limit_s, comparison="tokens"
        )

    def test_ok_verdict(self):
        result = self._run("print(42)\n", expected="42")
        self.assertEqual(result.verdict, "OK")

    def test_wa_verdict_shows_expected_and_actual_for_public(self):
        result = self._run("print(41)\n", expected="42")
        self.assertEqual(result.verdict, "WA")
        self.assertIn("expected", result.message)
        self.assertIn("41", result.message)

    def test_wa_on_hidden_test_withholds_output(self):
        result = self._run("print(41)\n", expected="42", hidden=True)
        self.assertEqual(result.verdict, "WA")
        self.assertIn("withheld", result.message)

    def test_tle_verdict(self):
        result = self._run("import time\ntime.sleep(5)\n", time_limit_s=0.4)
        self.assertEqual(result.verdict, "TLE")
        self.assertIn("time limit", result.message)

    def test_re_verdict_reports_exit_code(self):
        result = self._run("import sys\nprint('boom')\nsys.exit(7)\n")
        self.assertEqual(result.verdict, "RE")
        self.assertIn("exit code 7", result.message)

    @unittest.skipUnless(HAS_CXX, "no C++ compiler on PATH")
    def test_compile_error_for_invalid_cpp(self):
        bad = self.workdir / "bad.cpp"
        bad.write_text("int main( { return 0; }", encoding="utf-8")
        with self.assertRaises(CompileError):
            prepare_solution(bad, self.workdir / "build-cpp")

    @unittest.skipUnless(HAS_CXX, "no C++ compiler on PATH")
    def test_cpp_solution_runs_and_passes(self):
        good = self.workdir / "good.cpp"
        good.write_text(
            "#include <iostream>\nint main(){ long long a, b; "
            "if(std::cin >> a >> b) std::cout << a + b << '\\n'; return 0; }\n",
            encoding="utf-8",
        )
        prepared = prepare_solution(good, self.workdir / "build-cpp")
        self.assertEqual(prepared.kind, "c++")
        case = TestCase(name="t", input="20 22\n", expected="42")
        result = run_test_case(prepared.command, case, time_limit_s=5.0, comparison="tokens")
        self.assertEqual(result.verdict, "OK")


if __name__ == "__main__":
    unittest.main()
