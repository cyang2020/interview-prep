import random
from solution import find_number, PENDING, TOO_LOW, TOO_HIGH, CORRECT

random.seed(7)


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


def simple_worst_case(n):
    """对抗搜索：算出第一问在 upperBound=n 时最坏要调几次。
    算法的决定只取决于 (区间长度, pending 在区间里的偏移)，和绝对位置无关，
    所以把状态写成相对坐标，1e9 也能算完。"""
    memo = {}

    def cost(size, off):                # off=None 表示 pending 不在区间里
        if size == 1:
            return 0
        key = (size, off)
        if key in memo:
            return memo[key]
        g = (size - 1) // 2             # 和 solution 里取中点的规则一致
        if g == off:
            g = g + 1 if g + 1 <= size - 1 else g - 1
        if off is None:
            r = 1 + cost(size, g)
        else:
            worst = 0
            if off >= 1:                                        # pending 偏大那一支
                worst = max(worst, cost(off, g if g < off else None))
            if size - 1 - off >= 1:                             # pending 偏小那一支
                worst = max(worst, cost(size - 1 - off, g - off - 1 if g > off else None))
            r = 1 + worst
        memo[key] = r
        return r

    return cost(n, None)


def test_examples_from_problem():
    for ub, secret in ((10, 6), (50, 17), (31, 25)):
        assert find_number(ub, GuessServer(ub, secret)) == secret  # 题面三个例子


def test_every_secret_small_range():
    for n in range(1, 301):
        worst = 0
        for s in range(1, n + 1):
            srv = GuessServer(n, s)
            assert find_number(n, srv) == s          # 每个 secret 都答对
            worst = max(worst, srv.calls)            # 裁判没有 assert，说明没越界没重复
        assert worst == simple_worst_case(n), (n, worst)  # 对抗搜索的最坏值和实测一致


def test_upper_bound_one_needs_no_call():
    srv = GuessServer(1, 1)
    assert find_number(1, srv) == 1
    assert srv.calls == 0                            # 只有一个候选，一次都不用调


def test_large_upper_bound():
    n = 10 ** 9
    bound = simple_worst_case(n)
    for s in [1, 2, n - 1, n] + [random.randint(1, n) for _ in range(200)]:
        srv = GuessServer(n, s)
        assert find_number(n, srv) == s
        assert srv.calls <= bound                    # 不超过对抗搜索给的最坏值


def test_worst_case_table():
    table = {10: 5, 1000: 18, 10 ** 6: 38, 10 ** 9: 58}
    for n, calls in table.items():
        assert simple_worst_case(n) == calls         # notes 里那张表的来源


if __name__ == "__main__":
    tests = [test_examples_from_problem, test_every_secret_small_range,
             test_upper_bound_one_needs_no_call, test_large_upper_bound,
             test_worst_case_table]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
