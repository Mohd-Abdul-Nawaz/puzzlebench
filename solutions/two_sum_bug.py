"""DELIBERATELY BUGGY solution kept to demonstrate PuzzleBench's hidden tests.

Bug: assumes the input array is already sorted. It runs two pointers on a sorted
copy and prints positions inside that copy. It passes the sorted public tests but
is rejected by the unsorted hidden tests (WA on indices).
"""

import sys


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return
    n, x = data[0], data[1]
    a = data[2 : 2 + n]
    b = sorted(a)
    i, j = 0, n - 1
    while i < j:
        s = b[i] + b[j]
        if s == x:
            print(i, j)  # BUG: indices into the sorted copy, not the original array
            return
        if s < x:
            i += 1
        else:
            j -= 1
    print(-1)


if __name__ == "__main__":
    main()
