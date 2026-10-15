NEG = float("-inf")   # "到不了"的标记。格子值可能是负数，所以不能拿 0 代表到不了

# 四种走法：(行偏移, 列偏移, 消耗几次特殊跳)。前三种是普通一步，第四种是跳过一行的特殊跳
MOVES = ((1, -1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 1))


def _fill(board, p, K, X=0, Y=0):
    """填表。状态多一位 c：走进 (i, j) 这一步是否严格上升（上一格的值 < 这一格的值）。
    dp[i][j][k][c] = 从 (0, p) 走到 (i, j)、恰好跳了 k 次、最后一步上升与否为 c 的最大调整后得分；到不了是 NEG。
    parent[i][j][k][c] = 取到这个最大值时的前驱状态 (pi, pj, pk, pc)；起点和到不了的是 None。
    count[i][j][k][c] = 能拿到 dp[i][j][k][c] 这个分的路线条数；到不了的是 0。"""
    n, m = len(board), len(board[0])
    kmax = min(K, (n - 1) // 2)   # 每次特殊跳过 2 行，从第 0 行到第 n-1 行最多跳这么多次
    dp = [[[[NEG, NEG] for _ in range(kmax + 1)] for _ in range(m)] for _ in range(n)]
    parent = [[[[None, None] for _ in range(kmax + 1)] for _ in range(m)] for _ in range(n)]
    count = [[[[0, 0] for _ in range(kmax + 1)] for _ in range(m)] for _ in range(n)]
    dp[0][p][0][0] = board[0][p]     # 起点没有上一步，c 记 0：从起点走出的第一步拿不到 Y
    count[0][p][0][0] = 1
    for i in range(1, n):
        for j in range(m):
            cur = board[i][j]
            for k in range(kmax + 1):
                best, who, ways = [NEG, NEG], [None, None], [0, 0]
                for di, dj, dk in MOVES:
                    pi, pj, pk = i - di, j - dj, k - dk   # 反推：从哪个状态一步能走到 (i, j, k)
                    if pi < 0 or not 0 <= pj < m or pk < 0:
                        continue
                    prev = board[pi][pj]                   # 特殊跳时 pi = i - 2，中间那格根本不读
                    c = 1 if prev < cur else 0             # 这一步是否上升，决定结果落到 c=0 还是 c=1
                    gain = cur + (X if prev == cur else 0) # 相邻相等的 X 奖励只看这两格
                    for pc in (0, 1):                      # 前驱那一步上升与否
                        # 前驱那一步上升、这一步又上升，就是三格严格递增，拿 Y
                        cand = dp[pi][pj][pk][pc] + gain + (Y if pc and c else 0)
                        if cand > best[c]:                 # 严格大于：打平时留第一个遇到的前驱
                            best[c], who[c], ways[c] = cand, (pi, pj, pk, pc), count[pi][pj][pk][pc]
                        elif cand == best[c]:              # 打平的前驱：它们的路线都能拿到这个分，条数相加
                            ways[c] += count[pi][pj][pk][pc]
                for c in (0, 1):
                    dp[i][j][k][c] = best[c]
                    parent[i][j][k][c] = who[c]
                    count[i][j][k][c] = ways[c]
    return dp, parent, count


def _bottom_states(dp):
    """底行所有状态：(得分, 列 j, 跳了 k 次, 最后一步是否上升 c)。终点可以是底行任意列、任意跳跃次数。"""
    bottom = dp[-1]
    return [(bottom[j][k][c], j, k, c) for j in range(len(bottom)) for k in range(len(bottom[j])) for c in (0, 1)]


def max_score(board, p, K, X=0, Y=0):
    dp, _, _ = _fill(board, p, K, X, Y)
    return max(s for s, _, _, _ in _bottom_states(dp))


def best_path(board, p, K, X=0, Y=0):
    dp, parent, _ = _fill(board, p, K, X, Y)
    _, j, k, c = max(_bottom_states(dp))     # 底行得分最高的状态；打平时随便选一个都是最优路径
    path, state = [], (len(board) - 1, j, k, c)
    while state is not None:                 # 沿 parent 一路退回起点，起点的 parent 是 None
        i, j, k, c = state
        path.append([i, j])
        state = parent[i][j][k][c]
    path.reverse()
    return path


def count_best_paths(board, p, K, X=0, Y=0):
    dp, _, count = _fill(board, p, K, X, Y)
    states = _bottom_states(dp)
    top = max(s for s, _, _, _ in states)
    # 底行所有打到最高分的状态都算。不同 (j, k, c) 的路线坐标序列一定不同，相加不会重复
    return sum(count[-1][j][k][c] for s, j, k, c in states if s == top)
