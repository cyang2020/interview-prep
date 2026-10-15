NEG = float("-inf")   # "到不了"的标记。格子值可能是负数，所以不能拿 0 代表到不了

# 四种走法：(行偏移, 列偏移, 消耗几次特殊跳)。前三种是普通一步，第四种是跳过一行的特殊跳
MOVES = ((1, -1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 1))


def _fill(board, p, K):
    """填表。dp[i][j][k] = 从 (0, p) 走到 (i, j)、恰好用了 k 次特殊跳的最大得分；到不了是 NEG。"""
    n, m = len(board), len(board[0])
    kmax = min(K, (n - 1) // 2)   # 每次特殊跳过 2 行，从第 0 行到第 n-1 行最多跳这么多次
    dp = [[[NEG] * (kmax + 1) for _ in range(m)] for _ in range(n)]
    dp[0][p][0] = board[0][p]
    for i in range(1, n):
        for j in range(m):
            for k in range(kmax + 1):
                best = NEG
                for di, dj, dk in MOVES:
                    pi, pj, pk = i - di, j - dj, k - dk   # 反推：从哪个状态一步能走到 (i, j, k)
                    if pi < 0 or not 0 <= pj < m or pk < 0:
                        continue
                    cand = dp[pi][pj][pk] + board[i][j]   # 前驱到不了时 NEG 加任何数仍是 NEG
                    if cand > best:
                        best = cand
                dp[i][j][k] = best
    return dp


def _bottom_states(dp):
    """底行所有状态：(得分, 列 j, 跳了 k 次)。终点可以是底行任意列、任意跳跃次数。"""
    bottom = dp[-1]
    return [(bottom[j][k], j, k) for j in range(len(bottom)) for k in range(len(bottom[j]))]


def max_score(board, p, K):
    dp = _fill(board, p, K)
    return max(s for s, _, _ in _bottom_states(dp))
