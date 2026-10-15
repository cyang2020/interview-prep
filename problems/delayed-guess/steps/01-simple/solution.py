"""延迟一拍的猜数字 —— 第一问：单局，先跑对、不违规"""

PENDING  = "PENDING"
TOO_LOW  = "TOO_LOW"
TOO_HIGH = "TOO_HIGH"
CORRECT  = "CORRECT"


def find_number(upper_bound, server):
    lo, hi = 1, upper_bound             # 还活着的候选区间
    pending = None                      # 上一次交出去、结果还没回来的那个数

    while True:
        if lo == hi:
            return lo                   # 信息够了就直接返回，不用再调一次确认

        guess = (lo + hi) // 2          # 在候选区间里取中点
        if guess == pending:            # 区间里唯一用过的数就是 pending，躲开它就不会重复
            guess = guess + 1 if guess + 1 <= hi else guess - 1

        resp = server.check(guess)      # 返回值说的是 pending，不是刚交的 guess

        if pending is not None:
            if resp == CORRECT:
                return pending
            if resp == TOO_LOW:
                lo = max(lo, pending + 1)   # pending 可能已经在区间外，不能让 lo 往回退
            elif resp == TOO_HIGH:
                hi = min(hi, pending - 1)

        pending = guess
