"""Reference solution: hash map, O(n) time, O(n) space."""

import sys


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return
    n, x = data[0], data[1]
    a = data[2 : 2 + n]
    seen: dict = {}
    for i, v in enumerate(a):
        need = x - v
        if need in seen:
            print(seen[need], i)
            return
        if v not in seen:
            seen[v] = i
    print(-1)


if __name__ == "__main__":
    main()
