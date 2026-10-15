NEG = float("-inf")   # "到不了"的标记。格子值可能是负数，所以不能拿 0 代表到不了

# 四种走法：(行偏移, 列偏移, 消耗几次特殊跳)。前三种是普通一步，第四种是跳过一行的特殊跳
MOVES = ((1, -1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 1))


def _fill(board, p, K):
    """填表。dp[i][j][k] = 从 (0, p) 走到 (i, j)、恰好用了 k 次特殊跳的最大得分；到不了是 NEG。
    parent[i][j][k] = 取到这个最大值时的前驱状态 (pi, pj, pk)；起点和到不了的是 None。
    count[i][j][k] = 能拿到 dp[i][j][k] 这个分的路线条数；到不了的是 0。"""
    n, m = len(board), len(board[0])
    kmax = min(K, (n - 1) // 2)   # 每次特殊跳过 2 行，从第 0 行到第 n-1 行最多跳这么多次
    dp = [[[NEG] * (kmax + 1) for _ in range(m)] for _ in range(n)]
    parent = [[[None] * (kmax + 1) for _ in range(m)] for _ in range(n)]
    count = [[[0] * (kmax + 1) for _ in range(m)] for _ in range(n)]
    dp[0][p][0] = board[0][p]
    count[0][p][0] = 1
    for i in range(1, n):
        for j in range(m):
            for k in range(kmax + 1):
                best, who, ways = NEG, None, 0
                for di, dj, dk in MOVES:
                    pi, pj, pk = i - di, j - dj, k - dk   # 反推：从哪个状态一步能走到 (i, j, k)
                    if pi < 0 or not 0 <= pj < m or pk < 0:
                        continue
                    cand = dp[pi][pj][pk] + board[i][j]   # 前驱到不了时 NEG 加任何数仍是 NEG
                    if cand > best:                        # 严格大于：打平时留第一个遇到的前驱
                        best, who, ways = cand, (pi, pj, pk), count[pi][pj][pk]
                    elif cand == best:                     # 打平的前驱：它们的路线都能拿到这个分，条数相加
                        ways += count[pi][pj][pk]          # 到不了的前驱 count 是 0，加了不影响
                dp[i][j][k] = best
                parent[i][j][k] = who
                count[i][j][k] = ways
    return dp, parent, count


def _bottom_states(dp):
    """底行所有状态：(得分, 列 j, 跳了 k 次)。终点可以是底行任意列、任意跳跃次数。"""
    bottom = dp[-1]
    return [(bottom[j][k], j, k) for j in range(len(bottom)) for k in range(len(bottom[j]))]


def max_score(board, p, K):
    dp, _, _ = _fill(board, p, K)
    return max(s for s, _, _ in _bottom_states(dp))


def best_path(board, p, K):
    dp, parent, _ = _fill(board, p, K)
    _, j, k = max(_bottom_states(dp))        # 底行得分最高的状态；打平时随便选一个都是最优路径
    path, state = [], (len(board) - 1, j, k)
    while state is not None:                 # 沿 parent 一路退回起点，起点的 parent 是 None
        i, j, k = state
        path.append([i, j])
        state = parent[i][j][k]
    path.reverse()
    return path


def count_best_paths(board, p, K):
    dp, _, count = _fill(board, p, K)
    states = _bottom_states(dp)
    top = max(s for s, _, _ in states)
    # 底行所有打到最高分的状态都算。不同 (j, k) 的路线坐标序列一定不同，相加不会重复
    return sum(count[-1][j][k] for s, j, k in states if s == top)
