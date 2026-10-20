#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n, x;
    if (!(cin >> n >> x)) return 0;
    unordered_map<long long, int> seen;
    seen.reserve(static_cast<size_t>(n) * 2 + 1);
    for (int i = 0; i < n; ++i) {
        long long v;
        cin >> v;
        auto it = seen.find(x - v);
        if (it != seen.end()) {
            cout << it->second << ' ' << i << '\n';
            return 0;
        }
        if (!seen.count(v)) seen[v] = i;
    }
    cout << -1 << '\n';
    return 0;
}
