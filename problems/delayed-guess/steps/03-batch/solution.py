"""延迟一拍的猜数字 —— 第三问：多局并行，批次最少"""

PENDING  = "PENDING"
TOO_LOW  = "TOO_LOW"
TOO_HIGH = "TOO_HIGH"
CORRECT  = "CORRECT"


def _build_table(limit):
    """A[k] = 还剩 k 次调用、在等结果的数对区间没用时，最多能搞定多少个候选。
    A[k] = 1 + A[k-1] + A[k-2]：新数落在的那一侧只少 1 次，另一侧白扔一手，少 2 次。"""
    A = [1, 1]
    while A[-1] < limit:
        A.append(1 + A[-1] + A[-2])
    return A


def _min_calls(n, A):
    for k, v in enumerate(A):
        if v >= n:
            return k


def find_number(upper_bound, server):
    if upper_bound == 1:
        return 1

    A = _build_table(upper_bound)
    k = _min_calls(upper_bound, A)      # 预算：还允许调用几次
    lo, hi = 1, upper_bound             # 还活着的候选区间
    pending = None                      # 上一次交出去、结果还没回来的那个数

    while True:
        if lo == hi:
            return lo                   # 信息够了就直接返回，不用再调一次确认

        if pending is None:
            # 情况一：在等结果的那个数已经不在区间里，它的结果没用。
            # 这一次调用的唯一作用是把下一个数摆到位置上：下方吃满 A[k-1]，上方自然 <= A[k-2]。
            guess = lo + min(hi - lo, A[k - 1])
            server.check(guess)         # 返回值跟当前区间无关，丢掉
            pending = guess
            k -= 1
            continue

        # 情况二：在等结果的那个数还在区间里，它的结果有用
        a = pending - lo                # pending 下方还剩多少候选
        b = hi - pending                # pending 上方还剩多少候选
        if a == 0 and b == 0:
            return pending

        low_ok = a >= 1 and a <= A[k] and b <= A[k - 1]   # 下方够大、上方能用 k-1 次兜住
        if low_ok:
            guess = lo + min(a - 1, A[k - 1])             # 新数放进下方那块
        else:
            guess = pending + 1 + min(b - 1, A[k - 1])    # 新数放进上方那块

        resp = server.check(guess)      # 这一次拿到的是 pending 的结果
        k -= 1

        if resp == CORRECT:
            return pending
        if resp == TOO_HIGH:
            hi = pending - 1
        else:
            lo = pending + 1

        pending = guess if lo <= guess <= hi else None    # 赚的一边继续用它，赔的一边当没有


# ---- 第三问新增：把上面的循环翻成状态机，propose() 交一个数，absorb() 收一条结果 ----

class _Game:
    def __init__(self, upper_bound, A):
        self.A = A
        self.lo, self.hi = 1, upper_bound
        self.k = _min_calls(upper_bound, A)
        self.pending = None             # 上一批交的、结果还没回来的数
        self.sent = None                # 本批刚交的数，要等 absorb 时才转正成 pending
        self.answer = 1 if upper_bound == 1 else None   # 只有一个候选，一开始就定了

    def propose(self):
        """这一批要交什么。已定的局返回 -1。选数规则和 find_number 一字不差。"""
        if self.answer is not None:
            self.sent = None
            return -1

        if self.pending is None:
            q = self.lo + min(self.hi - self.lo, self.A[self.k - 1])
        else:
            a = self.pending - self.lo
            b = self.hi - self.pending
            low_ok = a >= 1 and a <= self.A[self.k] and b <= self.A[self.k - 1]
            if low_ok:
                q = self.lo + min(a - 1, self.A[self.k - 1])
            else:
                q = self.pending + 1 + min(b - 1, self.A[self.k - 1])

        self.sent = q
        return q

    def absorb(self, resp):
        """收上一批那个数（pending）的结果。已定的局直接跳过，它收到的 CORRECT / PENDING 都不用看。"""
        if self.answer is not None:
            return

        p = self.pending
        if p is not None:
            if resp == CORRECT:
                self.answer = p
            elif resp == TOO_HIGH:
                self.hi = p - 1
            elif resp == TOO_LOW:
                self.lo = p + 1

        self.pending = self.sent        # 本批交的数现在开始等结果
        self.sent = None
        self.k -= 1

        if self.answer is None:
            if self.lo == self.hi:
                self.answer = self.lo
            elif self.pending is not None and not (self.lo <= self.pending <= self.hi):
                self.pending = None     # 它已经出了区间，结果没信息了


def find_numbers(upper_bounds, server):
    A = _build_table(max(upper_bounds))
    games = [_Game(ub, A) for ub in upper_bounds]

    while any(g.answer is None for g in games):     # 全定了就退出，最后一批的结果不去取
        guesses = [g.propose() for g in games]      # 先让每一局各自算出这批交什么
        feedback = server.check_batch(guesses)      # 一次调用
        for g, r in zip(games, feedback):           # 再让每一局各自收上一批的结果
            g.absorb(r)

    return [g.answer for g in games]
