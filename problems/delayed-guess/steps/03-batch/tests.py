import random
import sys
from functools import lru_cache
from solution import (find_number, find_numbers, _build_table, _min_calls,
                      PENDING, TOO_LOW, TOO_HIGH, CORRECT)

random.seed(7)
A = _build_table(10 ** 9)


class GuessServer:
    """单局模拟服务器，同时当裁判：越界或重复猜直接 assert 失败。"""

    def __init__(self, upper_bound, secret):
        self.ub, self.secret = upper_bound, secret
        self.pending, self.used, self.calls = None, set(), 0

    def check(self, guess):
        assert 1 <= guess <= self.ub, f"越界: {guess} 不在 [1,{self.ub}]"
        assert guess not in self.used, f"重复猜: {guess}"
        self.used.add(guess)
        self.calls += 1
        p = self.pending
        out = (PENDING if p is None else
               CORRECT if p == self.secret else
               TOO_LOW if p < self.secret else TOO_HIGH)
        self.pending = guess
        return out


class BatchGuessServer:
    """多局模拟服务器，裁判规则：数组长度、-1 之后不能再交、按局越界、按局重复。"""

    def __init__(self, upper_bounds, secrets):
        self.ub, self.secrets = upper_bounds, secrets
        self.n = len(upper_bounds)
        self.pending = [None] * self.n
        self.used = [set() for _ in range(self.n)]
        self.declared = [False] * self.n      # 已经用 -1 宣告完成的局
        self.batches = 0
        self.guesses = 0

    def check_batch(self, gs):
        assert len(gs) == self.n, "数组长度必须等于局数"
        self.batches += 1
        for i, g in enumerate(gs):
            if g == -1:
                self.declared[i] = True
            else:
                assert not self.declared[i], f"局 {i}: 宣告完成后又交了猜测"
                assert 1 <= g <= self.ub[i], f"局 {i}: 越界 {g}"
                assert g not in self.used[i], f"局 {i}: 重复猜 {g}"
                self.used[i].add(g)
                self.guesses += 1
        out = []
        for i, g in enumerate(gs):
            p = self.pending[i]
            out.append(PENDING if p is None else
                       CORRECT if p == self.secrets[i] else
                       TOO_LOW if p < self.secrets[i] else TOO_HIGH)
            self.pending[i] = None if g == -1 else g   # 上一批是 -1，这一批就回 PENDING
        return out


def brute_force_optimal(n):
    """不设任何前提的博弈树搜索，证明 A 表给的数是下界。"""
    sys.setrecursionlimit(100000)

    @lru_cache(maxsize=None)
    def cost(lo, hi, pending, used):
        if lo == hi:
            return 0
        best = 10 ** 9
        for q in range(1, n + 1):
            if used >> (q - 1) & 1:
                continue
            nused = used | (1 << (q - 1))
            if pending == 0:
                worst = cost(lo, hi, q, nused)
            else:
                p, worst = pending, 0
                if lo <= p <= hi:
                    branches = []
                    if lo <= p - 1: branches.append((lo, p - 1))
                    if p + 1 <= hi: branches.append((p + 1, hi))
                else:
                    branches = [(lo, hi)]
                for nlo, nhi in branches:
                    np = q if nlo <= q <= nhi else 0
                    worst = max(worst, cost(nlo, nhi, np, nused))
            best = min(best, 1 + worst)
            if best == 1:
                break
        return best

    return cost(1, n, 0, 0)


# ---------------- 第二问的测试原样保留 ----------------

def test_table_values():
    assert A[:9] == [1, 1, 3, 5, 9, 15, 25, 41, 67]
    assert _min_calls(10 ** 9, A) == 43


def test_matches_brute_force():
    for n in range(1, 12):
        assert brute_force_optimal(n) == _min_calls(n, A), n


def test_single_every_secret_small_range_hits_bound():
    for n in range(1, 301):
        worst = 0
        for s in range(1, n + 1):
            srv = GuessServer(n, s)
            assert find_number(n, srv) == s
            worst = max(worst, srv.calls)
        assert worst == _min_calls(n, A), (n, worst)


def test_single_large_upper_bounds():
    for n in (10 ** 9, 2 ** 30):
        bound = _min_calls(n, A)
        for s in [1, 2, n - 1, n] + [random.randint(1, n) for _ in range(100)]:
            srv = GuessServer(n, s)
            assert find_number(n, srv) == s
            assert srv.calls <= bound


# ---------------- 第三问新增 ----------------

def test_batch_examples_from_problem():
    for ubs, secs in ([[4, 3], [3, 1]],
                      [[10, 50, 8], [6, 17, 4]],
                      [[20, 20, 20, 20], [2, 13, 8, 17]]):
        srv = BatchGuessServer(ubs, secs)
        assert find_numbers(ubs, srv) == secs                     # 题面三个例子
        assert srv.batches == max(_min_calls(u, A) for u in ubs)  # 批次 = 最慢那一局


def test_batch_count_never_exceeds_slowest_game():
    shapes = [[1], [1, 1, 1], [1, 10 ** 9], [2, 3, 4, 5], [10 ** 9] * 5, list(range(1, 41))]
    for _ in range(40):
        shapes.append([random.randint(1, random.choice([3, 30, 5000, 10 ** 9]))
                       for _ in range(random.randint(1, 30))])
    for ubs in shapes:
        bound = max(_min_calls(u, A) for u in ubs)
        for secs in ([random.randint(1, u) for u in ubs] for _ in range(3)):
            srv = BatchGuessServer(ubs, secs)
            assert find_numbers(ubs, srv) == secs                 # 答案全对
            assert srv.batches <= bound                           # 裁判没报违规，批次不超上限
        secs = list(ubs)                                          # 全取上界也试一遍
        srv = BatchGuessServer(ubs, secs)
        assert find_numbers(ubs, srv) == secs
        assert srv.batches <= bound


def test_batch_all_upper_bound_one_makes_no_call():
    srv = BatchGuessServer([1, 1, 1], [1, 1, 1])
    assert find_numbers([1, 1, 1], srv) == [1, 1, 1]
    assert srv.batches == 0                                       # 全都一开始就定了，一次不调


def test_batch_declared_game_keeps_sending_minus_one():
    ubs, secs = [4, 3], [3, 1]
    srv = BatchGuessServer(ubs, secs)
    find_numbers(ubs, srv)
    assert srv.declared[1]                                        # 局 1 确实用 -1 宣告过
    assert len(srv.used[1]) < srv.batches                         # 宣告之后没再交过猜测


def test_batch_max_scale():
    ubs = [10 ** 9] + [random.randint(1, 10 ** 9) for _ in range(999)]
    secs = [random.randint(1, u) for u in ubs]
    srv = BatchGuessServer(ubs, secs)
    assert find_numbers(ubs, srv) == secs
    assert srv.batches == 43                                      # 1000 局、最大 1e9：43 批


if __name__ == "__main__":
    tests = [test_table_values, test_matches_brute_force,
             test_single_every_secret_small_range_hits_bound, test_single_large_upper_bounds,
             test_batch_examples_from_problem, test_batch_count_never_exceeds_slowest_game,
             test_batch_all_upper_bound_one_makes_no_call,
             test_batch_declared_game_keeps_sending_minus_one, test_batch_max_scale]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
