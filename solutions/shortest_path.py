"""Reference solution: Dijkstra with a binary heap, O((n + m) log n)."""

import heapq
import sys


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return
    n, m = data[0], data[1]
    adj: list = [[] for _ in range(n + 1)]
    idx = 2
    for _ in range(m):
        u, v, w = data[idx], data[idx + 1], data[idx + 2]
        idx += 3
        adj[u].append((v, w))
        adj[v].append((u, w))

    inf = 10**18
    dist = [inf] * (n + 1)
    dist[1] = 0
    heap = [(0, 1)]
    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        if u == n:
            break
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    print(-1 if dist[n] >= inf else dist[n])


if __name__ == "__main__":
    main()
