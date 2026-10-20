"""PuzzleBench — a small, reproducible local judge for self-contained coding challenges.

Features:
  * public + hidden test sets per challenge
  * verdicts: OK / WA / TLE / RE / CE (like an online judge)
  * runs Python and C/C++ solutions (compiled with -O2)
  * JSON reports with SHA-256 fingerprints and a verdict digest
  * `puzzlebench verify` re-runs a report and checks the digest
"""

__version__ = "1.0.0"
