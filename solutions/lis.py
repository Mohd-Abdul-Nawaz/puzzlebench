"""Reference solution: O(n log n) patience method with bisect_left (strict LIS)."""

import bisect
import sys


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return
    n = data[0]
    tails: list = []
    for x in data[1 : 1 + n]:
        pos = bisect.bisect_left(tails, x)
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    print(len(tails))


if __name__ == "__main__":
    main()
