# 第一问：update / check，带时间戳的关注关系

## 面试官给的骨架

题面只给了两个方法的签名，没有附代码，按签名还原成一个空壳。第二个版本的 following 参数是我自己加的，为追问"取消关注"预留，第一问默认 True。

```python
class FollowGraph:
    def update(self, a, b, t):
        """A 在 t 时刻开始关注 B。"""
        pass

    def check(self, a, b, t):
        """在 t 时刻，A 是否关注 B。"""
        pass
```

## 思路

**开口先定的口径。**

1. check 问的是过去某个时刻 t，不是现在。所以不能只存当前状态，要保留每对人之间关系的全部变化。这决定了存的是"事件列表"而不是"集合"。
2. 方法叫 update 不叫 follow，暗示后面会有取消关注。所以事件带一个 following 布尔值，第一问全是 True。
3. t 恰好等于关注时刻算关注，闭区间。这决定了二分查找用 bisect_right。
4. update 默认按时间顺序到达，追加到末尾；乱序到达就按位置插入。先问面试官，两种都要能说。
5. 同一对人、同一时刻两条 update，后到的生效。
6. 自己关注自己不记录。

**数据结构。** _history 是两层 map：外层按关注者 a 分，内层按被关注者 b 分，最里面是 _PairHistory。_PairHistory 存两个平行列表：times 是每次变化的时刻，states 是那一刻起是否关注。分两个列表是为了能直接对 times 做二分查找。

**为什么按 a 分层而不是以 (a, b) 为键。** 两种对 check 一样。但第二问推荐需要"a 关注的所有人"，按 (a, b) 为键要扫全部键才能找出 a 的所有 b，按 a 分层直接取 _history[a] 的所有键。现在多想一步，第二问不用重构。

**update 做的事。** 取出 _history[a][b] 这一对的 _PairHistory，调 record(t, following)。record 看 t 是否不早于 times 的最后一个元素：是就直接追加；不是就用 bisect_right 找到插入位置，往 times 和 states 同一位置插入。不这么做（直接追加不管顺序）的话，乱序到达时 times 不再有序，二分查找结果错。

**check 做的事。** 取 _history[a][b]，取不到就返回 False。取到就调 state_at(t)：bisect_right(times, t) 得到"时刻不超过 t 的事件条数" i，i 为 0 返回 False，否则返回 states[i - 1]。取 _history 时用 get 而不是方括号，不这么做的话 defaultdict 会在查询时建出空记录，check 就改了状态。

**用例子走一遍。** A 在第 1 秒关注 B，第 5 秒取消，第 9 秒再关注。这一对的 times 是 [1, 5, 9]，states 是 [True, False, True]。

| 查询 | bisect_right(times, t) | states[i - 1] | 结果 |
|---|---|---|---|
| check(A, B, 0) | 0 | 无 | False |
| check(A, B, 1) | 1 | states[0] = True | True |
| check(A, B, 3) | 1 | states[0] = True | True |
| check(A, B, 5) | 2 | states[1] = False | False |
| check(A, B, 7) | 2 | states[1] = False | False |
| check(A, B, 10) | 3 | states[2] = True | True |

**复杂度。** update 按序到达时追加，O(1)；乱序时插入，O(这一对的事件数)。check 二分查找，O(log 这一对的事件数)。内存是全部事件总数。

## 常见疑问

### 为什么 bisect_right 得到的是"不超过 t 的事件条数"

bisect_right 返回的是把 t 插进有序列表时、插在所有等于 t 的元素右边的位置。这个位置左边的元素全都不超过 t，所以它的值就是不超过 t 的元素个数。times 是 [1, 5, 9]，查 t=5：等于 5 的元素在下标 1，插在它右边是下标 2，所以返回 2，左边两个元素 1 和 5 都不超过 5。如果改用 bisect_left，查 t=5 返回 1，就把恰好第 5 秒那条事件漏掉了，变成开区间。

### 为什么 states 不能只存最后一个

A 第 1 秒关注、第 5 秒取消、第 9 秒再关注。只存最后一个状态就是 True。查 check(A, B, 7) 应该是 False，但只有最后状态答不出来。历史一旦被覆盖就找不回来，所以每次变化都要留一条。

### 为什么同一时刻后到的要排在先到的后面

record 里用 t >= times[-1] 追加，乱序路径用 bisect_right 插入，两条路径都把同一时刻的新事件放到旧事件后面。state_at 取的是不超过 t 的最后一条，所以后到的生效。这是定的口径，面试官要是说应该报错，把 record 改成检查 times 里有没有相同的 t 就行。
