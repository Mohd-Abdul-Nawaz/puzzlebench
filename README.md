# PuzzleBench

A small, **reproducible local judge** for self-contained coding challenges — the kind of tool a puzzle-solver uses daily: public + hidden tests, OJ-style verdicts, and SHA-256 verified reports.

Built by **Mohd Abdul Nawaz** · Python + C++ · MIT

## Why this exists

Solving a puzzle is only half the work. The other half is proving the solution is correct, fast, and reproducible. PuzzleBench gives you:

- 📦 **Self-contained challenges** — `spec.json` + `statement.md` + `public.json` + `hidden.json`
- 🧪 **OJ verdicts** — `OK / WA / TLE / RE / CE`
- 🐍➕⚙️ **Python + C/C++** runners (C++ compiled with `-O2 -std=c++17`)
- 🔒 **Hidden tests stay hidden** — WA on hidden tests never leaks input/output
- 🧾 **Reproducible JSON reports** with solution SHA-256 + verdict digest
- ✅ `puzzlebench verify` re-runs a report and checks the digest

## Challenges included

| ID | Title | Concepts | Tests |
|----|-------|----------|-------|
| `two-sum` | Two Sum | arrays, hash-map, two-pointers | 2 public + 4 hidden |
| `lis` | Longest Increasing Subsequence | DP, patience sorting, `bisect` | 2 public + 3 hidden |
| `shortest-path` | Shortest Path | graphs, Dijkstra, heap | 2 public + 3 hidden |

Hidden tests are adversarial: reference solutions pass 100%, planted bugs (`two_sum_bug.py`, `lis_bug.py`) pass all public tests but are caught by hidden tests.

## Quickstart

```bash
# Python 3.9+
pip install -e .

# list challenges
python -m puzzlebench list

# show a statement
python -m puzzlebench show lis

# run a solution (public + hidden)
python -m puzzlebench run two-sum solutions/two_sum.py

# debug mode — public tests only
python -m puzzlebench run two-sum solutions/two_sum_bug.py --no-hidden

# save a reproducible report + print JSON
python -m puzzlebench run lis solutions/lis.py --report reports/lis.json --json

# C++ solution (requires g++)
python -m puzzlebench run shortest-path solutions/shortest_path.cpp

# verify a previous report (re-runs everything, checks digest)
python -m puzzlebench verify reports/lis.json
```

Example output:

```
challenge: two-sum (easy)  time limit 2000 ms  comparison: tokens
solution:  solutions/two_sum.py  [python]  compile 0.3 ms
  [OK ] public-1             public   28.1 ms
  [OK ] public-2             public   27.4 ms
  [OK ] hidden-1             hidden   26.9 ms
  [OK ] hidden-2             hidden   27.2 ms
result: 6/6 passed
```

## Adding your own challenge

```
challenges/my-puzzle/
  spec.json        # id, title, time_limit_ms, comparison, tests:[...]
  statement.md     # problem statement shown by `puzzlebench show`
  tests/
    public.json    # [{name, input, expected}]
    hidden.json    # [{name, input, expected, hidden:true}...] (inputs withheld on WA)
```

See `challenges/two-sum/` as a template. Rules enforced by the loader: at least one public test, unique test names, `comparison` is `tokens` or `exact`, positive time limit.

## Reports

Each `--report` JSON contains: tool version, timestamp, challenge meta, solution path + SHA-256, environment (python/platform/compiler), per-test verdicts + timings + `input_sha256`, summary, and a 64-char `verdict_digest = sha256(challenge|solution_sha|name:verdict...)`. `verify` fails if the solution file changed or any verdict differs — ideal for AI-training audit trails.

## Testing

```bash
python -m unittest discover -s tests -v
```

Covers: spec loading/discovery, token vs exact comparison, all five verdicts, C++ compile + run, reference-solution sweeps, bug-catch guarantees, report determinism, hidden-test privacy, CLI exit codes (`0` pass / `1` fail / `2` usage or spec error), and verify round-trips. CI runs on Python 3.9 + 3.12.

## Layout

```
PuzzleBench/
  puzzlebench/      # spec.py, runner.py, report.py, cli.py
  challenges/       # 3 challenges × public/hidden tests
  solutions/        # Python + C++ references, 2 planted bugs
  tests/            # unittest suite (no third-party deps)
  .github/workflows/ci.yml
```

## Skills demonstrated

Algorithms & data structures (hash-maps, patience sorting, Dijkstra), process isolation + timeouts, cross-language tooling, reproducible evaluation harness design — directly aligned with **Puzzle Solver (Coding)** work: read an unfamiliar spec, implement, stress against hidden constraints, ship a verifiable artifact.
