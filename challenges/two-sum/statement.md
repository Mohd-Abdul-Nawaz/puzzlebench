# Two Sum

Given an array of `n` integers and a target value `x`, find two **distinct** indices
`i < j` such that `a_i + a_j = x`.

## Input

- First line: two integers `n` and `x`.
- Second line: `n` integers `a_1 a_2 ... a_n` (space separated).

## Output

- One line with the two 0-based indices `i j` (`i < j`), or `-1` if no such pair exists.

## Constraints

- `1 <= n <= 10^5`
- `-10^9 <= a_i, x <= 10^9`
- Whenever a solution exists, it is **unique**.

## Example

```
Input:
4 9
2 7 11 15

Output:
0 1
```
