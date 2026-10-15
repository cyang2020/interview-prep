import random
import sys
from functools import lru_cache
from solution import (find_number, _build_table, _min_calls,
                      PENDING, TOO_LOW, TOO_HIGH, CORRECT)

random.seed(7)
A = _build_table(10 ** 9)


class GuessServer:
    """模拟服务器，同时当裁判：越界或重复猜直接 assert 失败。"""

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
        self.pending = guess            # 这次交的数要到下一次调用才有结果
        return out


def brute_force_optimal(n):
    """不设任何前提的博弈树搜索：枚举每一步所有合法猜测（含区间外的、任意位置的），
    求最坏情况下最少要调几次。用来证明 A 表给的数就是下界，不是我们这套策略的巧合。"""
    sys.setrecursionlimit(100000)

    @lru_cache(maxsize=None)
    def cost(lo, hi, pending, used):    # pending=0 表示没有在等结果的数；used 是位图
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
                    branches = [(lo, hi)]          # 区间外的数，结果没信息
                for nlo, nhi in branches:
                    np = q if nlo <= q <= nhi else 0
                    worst = max(worst, cost(nlo, nhi, np, nused))
            best = min(best, 1 + worst)
            if best == 1:
                break
        return best

    return cost(1, n, 0, 0)


def test_table_values():
    assert A[:9] == [1, 1, 3, 5, 9, 15, 25, 41, 67]           # 递推 A[k] = 1 + A[k-1] + A[k-2]
    assert [_min_calls(n, A) for n in (1, 2, 3, 5, 9, 10, 50, 31)] == [0, 2, 2, 3, 4, 5, 8, 7]
    assert _min_calls(10 ** 9, A) == 43                      # 1e9 要 43 次


def test_matches_brute_force():
    for n in range(1, 12):
        assert brute_force_optimal(n) == _min_calls(n, A), n   # 无前提搜索 == 公式，说明是下界


def test_examples_from_problem():
    for ub, secret in ((10, 6), (50, 17), (31, 25)):
        assert find_number(ub, GuessServer(ub, secret)) == secret  # 题面三个例子


def test_every_secret_small_range_hits_bound():
    for n in range(1, 301):
        worst = 0
        for s in range(1, n + 1):
            srv = GuessServer(n, s)
            assert find_number(n, srv) == s          # 每个 secret 都答对，裁判没报违规
            worst = max(worst, srv.calls)
        assert worst == _min_calls(n, A), (n, worst) # 实测最坏次数正好等于下界，一次不多


def test_upper_bound_one_needs_no_call():
    srv = GuessServer(1, 1)
    assert find_number(1, srv) == 1
    assert srv.calls == 0                            # 只有一个候选，一次都不用调


def test_large_upper_bounds():
    for n in (10 ** 9, 999_999_937, 7 ** 10, 2 ** 30):
        bound = _min_calls(n, A)
        for s in [1, 2, n - 1, n] + [random.randint(1, n) for _ in range(200)]:
            srv = GuessServer(n, s)
            assert find_number(n, srv) == s
            assert srv.calls <= bound                # 大数也不超过预算


if __name__ == "__main__":
    tests = [test_table_values, test_matches_brute_force, test_examples_from_problem,
             test_every_secret_small_range_hits_bound, test_upper_bound_one_needs_no_call,
             test_large_upper_bounds]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
