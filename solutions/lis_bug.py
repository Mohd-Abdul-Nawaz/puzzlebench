"""DELIBERATELY BUGGY solution kept to demonstrate PuzzleBench's hidden tests.

Bug: uses bisect_right instead of bisect_left, which computes the longest
*non-decreasing* subsequence. The public tests contain distinct values, where
both variants agree; the hidden tests contain duplicates and expose the bug.
"""

import bisect
import sys


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return
    n = data[0]
    tails: list = []
    for x in data[1 : 1 + n]:
        pos = bisect.bisect_right(tails, x)  # BUG: should be bisect_left
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    print(len(tails))


if __name__ == "__main__":
    main()
