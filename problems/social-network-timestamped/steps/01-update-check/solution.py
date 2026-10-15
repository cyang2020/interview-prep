from bisect import bisect_right
from collections import defaultdict


class _PairHistory:
    """一对人 (A, B) 之间关系的全部变化，按时间排好序。

    times[i] 是第 i 次变化发生的时刻，states[i] 是从那一刻起 A 是否关注 B。
    两个列表分开存，是为了能直接对 times 做二分查找。
    """

    def __init__(self):
        self.times = []
        self.states = []

    def record(self, t, following):
        # 常见情况：事件按时间顺序到达，直接追加到末尾，列表天然有序。
        # 用 >= 而不是 >，是让同一时刻后到的事件排在先到的后面，查询时后写的生效。
        if not self.times or t >= self.times[-1]:
            self.times.append(t)
            self.states.append(following)
            return
        # 乱序到达：找到它该在的位置插进去，保持 times 有序。
        i = bisect_right(self.times, t)
        self.times.insert(i, t)
        self.states.insert(i, following)

    def state_at(self, t):
        # 时刻不超过 t 的事件有 i 条；i 为 0 说明 t 早于第一次关注。
        # bisect_right 让"恰好等于 t"的事件也算进去，所以是闭区间。
        i = bisect_right(self.times, t)
        return self.states[i - 1] if i else False


class FollowGraph:
    def __init__(self):
        # 外层按关注者 A 分，内层按被关注者 B 分，最里面是这一对的历史。
        # 按 A 分层而不是以 (A, B) 为键，是为了下一问能直接枚举"A 关注的所有人"。
        self._history = defaultdict(lambda: defaultdict(_PairHistory))

    def update(self, a, b, t, following=True):
        """A 在 t 时刻开始关注 B。following=False 表示 t 时刻取消关注（追问时加）。"""
        if a == b:
            return  # 自己关注自己不记录，和快照版的口径一致
        self._history[a][b].record(t, following)

    def check(self, a, b, t):
        """在 t 时刻 A 是否关注 B。"""
        # 用 get 而不是 []，否则 defaultdict 会在查询时顺手建出空记录，check 就改了状态。
        by_a = self._history.get(a)
        if by_a is None:
            return False
        hist = by_a.get(b)
        if hist is None:
            return False
        return hist.state_at(t)
