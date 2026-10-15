import random

from solution import max_score, best_path, count_best_paths

# 三个官方例子：(board, p, K)
EX1 = ([[1, 2, 3, 4], [5, 6, 1, 2], [7, 8, 9, 1], [3, 2, 5, 6]], 1, 1)
EX2 = ([[1, 5, 1], [-100, -100, -100], [1, 50, 1], [1, 1, 200]], 1, 1)
EX3 = ([[2, 1, 3], [-5, 10, -1], [4, -2, 6]], 1, 0)

MOVES = ((1, -1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 1))


def all_paths(board, p, K):
    """暴力枚举：从 (0, p) 出发、特殊跳不超过 K 次、停在底行的全部路径。只给小棋盘用。"""
    n, m = len(board), len(board[0])
    out = []

    def go(i, j, used, path):
        if i == n - 1:
            out.append(list(path))
            return
        for di, dj, dk in MOVES:
            ni, nj, nk = i + di, j + dj, used + dk
            if ni < n and 0 <= nj < m and nk <= K:
                path.append([ni, nj])
                go(ni, nj, nk, path)
                path.pop()

    go(0, p, 0, [[0, p]])
    return out


def score_of(board, path):
    return sum(board[i][j] for i, j in path)


def random_board(rng, n, m, lo=-9, hi=9):
    return [[rng.randint(lo, hi) for _ in range(m)] for _ in range(n)]


def is_valid_path(board, path, p, K):
    """路径从 [0, p] 开始、在底行结束、每一步是四种走法之一、跳数不超 K。"""
    n, m = len(board), len(board[0])
    if path[0] != [0, p] or path[-1][0] != n - 1:
        return False
    jumps = 0
    for (a, b), (c, d) in zip(path, path[1:]):
        if not 0 <= d < m:
            return False
        if c == a + 1 and abs(d - b) <= 1:
            continue
        if c == a + 2 and d == b:
            jumps += 1
            continue
        return False
    return jumps <= K


def test_official_examples():
    assert max_score(*EX1) == 23      # (0,1)->(1,1)->(2,2)->(3,3)：2+6+9+6
    assert max_score(*EX2) == 255     # 跳过整行 -100：5+50+200
    assert max_score(*EX3) == 17      # 不许跳：1+10+6


def test_single_row_is_already_at_bottom():
    assert max_score([[4, -2, 7]], 1, 3) == -2   # 起点就在底行，得分只有起点自己


def test_unreachable_cells_are_not_zero():
    # (0,1) 到不了。表初始化成 0 的话 (1,0) 会从 (0,1) 的"0"转移过来，得 -10
    assert max_score([[-10, 0], [-10, -10]], 0, 0) == -20


def test_jump_cannot_overshoot_bottom():
    assert max_score([[0], [-5]], 0, 5) == -5   # 只有两行，跳两行会跳出棋盘，只能一步走到 -5


def test_jump_can_land_exactly_on_bottom():
    assert max_score([[0], [-5], [0]], 0, 1) == 0   # 从第 0 行跳到第 2 行，正好是底行


def test_jump_budget_is_enforced():
    board = [[0], [-5], [0], [-5], [0]]
    assert max_score(board, 0, 0) == -10   # 不许跳，两个 -5 都得踩
    assert max_score(board, 0, 1) == -5    # 一次跳只能躲掉一个
    assert max_score(board, 0, 2) == 0     # 两次跳全躲掉
    assert max_score(board, 0, 99) == 0    # 预算再多也只能跳两次


def test_jump_is_straight_down_only():
    # 斜着跳不存在：(0,0) 跳不到 (2,1) 的 5，只能跳到 (2,0) 的 0，或者踩 -9 再走到 5 得 -4
    assert max_score([[0, 0], [-9, -9], [0, 5]], 0, 1) == 0


def test_matches_brute_force_on_random_boards():
    rng = random.Random(1)
    for _ in range(150):
        n, m = rng.randint(1, 6), rng.randint(1, 4)
        board = random_board(rng, n, m)
        p, K = rng.randrange(m), rng.randint(0, 3)
        want = max(score_of(board, path) for path in all_paths(board, p, K))
        assert max_score(board, p, K) == want   # 和暴力枚举的最大值一致


def test_large_k_equals_capped_k():
    rng = random.Random(2)
    board = random_board(rng, 60, 60, -100, 100)
    assert max_score(board, 30, 60) == max_score(board, 30, 29)   # 60 行最多跳 29 次，预算给到 60 答案一样


def test_path_official_examples():
    # 三个例子的最优路径都唯一，可以精确比对
    assert best_path(*EX1) == [[0, 1], [1, 1], [2, 2], [3, 3]]
    assert best_path(*EX2) == [[0, 1], [2, 1], [3, 2]]
    assert best_path(*EX3) == [[0, 1], [1, 1], [2, 2]]


def test_path_single_row():
    assert best_path([[4, -2, 7]], 1, 3) == [[0, 1]]   # 起点就是终点，路径只有一格


def test_path_skips_cell_on_jump():
    path = best_path(*EX2)
    assert [1, 1] not in path       # 跳过的 (1,1) 不算访问过，不能出现在路径里
    assert len(path) == 3           # 起点、落点、终点


def test_path_is_valid_and_optimal_on_random_boards():
    rng = random.Random(3)
    for _ in range(150):
        n, m = rng.randint(1, 6), rng.randint(1, 4)
        board = random_board(rng, n, m)
        p, K = rng.randrange(m), rng.randint(0, 3)
        path = best_path(board, p, K)
        assert is_valid_path(board, path, p, K)                  # 每一步合法、跳数不超
        assert score_of(board, path) == max_score(board, p, K)   # 得分就是最大分


def test_count_official_examples():
    assert count_best_paths(*EX1) == 1                                   # 23 分的路径只有一条
    assert count_best_paths([[0], [0], [0]], 0, 1) == 2                  # 一步一步走，或者一跳到底
    assert count_best_paths([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 1, 0) == 7


def test_count_ties_across_jump_choices():
    board = [[0], [0], [0], [0], [0]]
    assert count_best_paths(board, 0, 0) == 1   # 只有 1,1,1,1
    assert count_best_paths(board, 0, 1) == 4   # 再加 2,1,1 / 1,2,1 / 1,1,2
    assert count_best_paths(board, 0, 2) == 5   # 再加 2,2


def test_count_only_counts_max_score_paths():
    board = [[0, 0], [5, 0], [1, 0]]
    assert max_score(board, 0, 0) == 6            # (0,0)->(1,0)->(2,0)
    assert count_best_paths(board, 0, 0) == 1     # 走 (2,1) 的那条只有 5 分，不算


def test_count_matches_brute_force_on_random_boards():
    rng = random.Random(4)
    for _ in range(150):
        n, m = rng.randint(1, 6), rng.randint(1, 4)
        board = random_board(rng, n, m, -2, 2)   # 值域小，故意制造很多平局
        p, K = rng.randrange(m), rng.randint(0, 3)
        paths = all_paths(board, p, K)
        top = max(score_of(board, path) for path in paths)
        want = sum(1 for path in paths if score_of(board, path) == top)
        assert count_best_paths(board, p, K) == want   # 和暴力数出来的条数一致


def test_count_can_exceed_32_bits():
    board = [[0, 0] for _ in range(30)]
    assert count_best_paths(board, 0, 0) == 2 ** 29   # 两列全 0，29 步每步 2 个选择


if __name__ == "__main__":
    tests = [
        test_official_examples,
        test_single_row_is_already_at_bottom,
        test_unreachable_cells_are_not_zero,
        test_jump_cannot_overshoot_bottom,
        test_jump_can_land_exactly_on_bottom,
        test_jump_budget_is_enforced,
        test_jump_is_straight_down_only,
        test_matches_brute_force_on_random_boards,
        test_large_k_equals_capped_k,
        test_path_official_examples,
        test_path_single_row,
        test_path_skips_cell_on_jump,
        test_path_is_valid_and_optimal_on_random_boards,
        test_count_official_examples,
        test_count_ties_across_jump_choices,
        test_count_only_counts_max_score_paths,
        test_count_matches_brute_force_on_random_boards,
        test_count_can_exceed_32_bits,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
