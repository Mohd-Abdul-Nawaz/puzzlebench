# Shortest Path

You are given an undirected weighted graph with `n` vertices and `m` edges.
Find the length of the shortest path from vertex `1` to vertex `n`.

## Input

- First line: two integers `n` and `m`.
- `m` lines, each with three integers `u v w` describing an undirected edge
  between `u` and `v` with weight `w`.

## Output

- One line with the length of the shortest path from `1` to `n`, or `-1` if
  `n` is unreachable from `1`.

## Constraints

- `2 <= n <= 10^5`, `0 <= m <= 2 * 10^5`
- `1 <= u, v <= n`, `0 <= w <= 10^9`
- The graph may contain parallel edges and self-loops (self-loops never help).

## Example

```
Input:
4 4
1 2 3
2 3 4
1 4 20
3 4 1

Output:
8
```
