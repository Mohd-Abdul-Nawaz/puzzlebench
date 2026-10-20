"""Spec loading, discovery and output-comparison tests."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from puzzlebench.spec import SpecError, compare, discover_challenges, load_spec

CHALLENGES = REPO / "challenges"
EXPECTED_IDS = {"two-sum", "lis", "shortest-path"}


class SpecLoadingTests(unittest.TestCase):
    def test_discover_finds_all_challenges(self):
        found = discover_challenges(CHALLENGES)
        self.assertEqual(set(found), EXPECTED_IDS)

    def test_discover_missing_dir_raises(self):
        with self.assertRaises(SpecError):
            discover_challenges(REPO / "does-not-exist")

    def test_each_challenge_loads_with_public_and_hidden_tests(self):
        found = discover_challenges(CHALLENGES)
        for cid, path in found.items():
            with self.subTest(challenge=cid):
                spec = load_spec(path)
                self.assertEqual(spec.id, cid)
                self.assertTrue(spec.title)
                self.assertGreater(spec.time_limit_ms, 0)
                self.assertIn(spec.comparison, ("tokens", "exact"))
                public = [t for t in spec.tests if not t.hidden]
                hidden = [t for t in spec.tests if t.hidden]
                self.assertGreaterEqual(len(public), 2)
                self.assertGreaterEqual(len(hidden), 3)
                self.assertTrue(spec.statement.strip(), "statement.md must not be empty")
                names = [t.name for t in spec.tests]
                self.assertEqual(len(names), len(set(names)), "test names must be unique")

    def test_missing_spec_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SpecError):
                load_spec(tmp)

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "spec.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(SpecError):
                load_spec(tmp)

    def test_missing_required_field_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "spec.json").write_text(
                json.dumps({"id": "x", "title": "X", "tests": ["t.json"]}),
                encoding="utf-8",
            )
            Path(tmp, "t.json").write_text(
                json.dumps([{"name": "a", "input": "", "expected": ""}]),
                encoding="utf-8",
            )
            with self.assertRaises(SpecError):
                load_spec(tmp)

    def test_all_hidden_tests_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "spec.json").write_text(
                json.dumps(
                    {
                        "id": "x",
                        "title": "X",
                        "time_limit_ms": 1000,
                        "comparison": "tokens",
                        "tests": ["t.json"],
                    }
                ),
                encoding="utf-8",
            )
            Path(tmp, "t.json").write_text(
                json.dumps(
                    [{"name": "a", "input": "", "expected": "", "hidden": True}]
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SpecError):
                load_spec(tmp)


class CompareTests(unittest.TestCase):
    def test_tokens_ignores_whitespace_layout(self):
        self.assertTrue(compare("tokens", "1 2\n3\n", "1 2 3\n"))
        self.assertTrue(compare("tokens", "ok\n", "  ok   "))

    def test_tokens_detects_difference(self):
        self.assertFalse(compare("tokens", "1 2", "1 3"))

    def test_exact_requires_matching_layout(self):
        self.assertFalse(compare("exact", "1 2\n3\n", "1 2 3\n"))
        self.assertTrue(compare("exact", "1 2\n", "1 2\r\n"))  # CRLF tolerated

    def test_unknown_mode_raises(self):
        with self.assertRaises(SpecError):
            compare("fuzzy", "a", "a")


if __name__ == "__main__":
    unittest.main()
