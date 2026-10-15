"""延迟一拍的猜数字 —— 第二问：单局，调用次数压到最少"""

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
