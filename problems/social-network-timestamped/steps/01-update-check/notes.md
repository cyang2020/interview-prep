# 第一问：update / check，带时间戳的关注关系

## 这一问要做什么

- 写 FollowGraph 的 update(a, b, t) 和 check(a, b, t)：前者记一笔"a 从 t 时刻起关注 b"，后者返回 t 时刻 a 是否关注 b。
- t 可以是过去任意时刻，不只是现在。update 带 following=False 时表示 a 从 t 时刻起取消关注 b。

## 核心思路

- 两个方法：update(a, b, t, following=True) 记一笔"a 从 t 时刻起关注 b"；check(a, b, t) 查过去任意时刻 t 是否关注。following 第一问全是 True，为取消关注预留。
- 存的是每对人的全部变化，不是当前状态。_history 是两层 map：外层按关注者 a，内层按被关注者 b，最里面是一个 _PairHistory。
- _PairHistory 两个平行列表：times 是每次变化的时刻，升序；states 是从那一刻起是否关注。分开存是为了直接对 times 做二分。
- update：a == b 直接返回，不记录；否则 _history[a][b].record(t, following)。record 里 t 不早于 times 末尾就追加，否则 bisect_right 找位置，times 和 states 同一下标插入。
- check：用 get 取 _history[a] 再取 b，任一取不到返回 False；取到调 state_at(t)：i = bisect_right(times, t)，i 为 0 返回 False，否则返回 states[i - 1]。
- 按 a 分层而不是以 (a, b) 为键：对 check 两种一样，但第二问要列举"a 关注的所有人"，按 a 分层直接取 _history[a] 的全部键，不用扫所有对。
- 复杂度：update 按序到达追加 O(1)，乱序插入 O(这一对的事件数)；check 二分 O(log 这一对的事件数)；内存是全部事件总数。

## 思考与反问

- check 问的是过去某时刻还是现在？按过去任意 t，所以每对人存事件列表不存一个布尔值。只存最后状态的话，A 第 1 秒关注、第 5 秒取消、第 9 秒再关注，check(A, B, 7) 答不出 False。
- t 恰好等于关注时刻算不算关注？按算，闭区间，决定了 state_at 用 bisect_right。换成 bisect_left，times 是 [1, 5, 9] 查 t=5 返回 1 而不是 2，第 5 秒那条取消被漏掉，check(A, B, 5) 错答 True。
- update 按时间顺序到达吗？两种都接。record 先看 t >= times[-1] 直接追加；不满足走 bisect_right 插入。只追加不插入的话，第 9 秒先到、第 1 秒后到，times 变成 [9, 1]，二分结果错。
- 同一对人同一时刻两条 update？按后到的生效。record 的追加用 >= 不用 >，插入用 bisect_right 不用 bisect_left，两条路径都把新事件放在同时刻旧事件后面，state_at 取最后一条。面试官要报错，就在 record 里查 times 有没有相同的 t。
- 方法名叫 update 不叫 follow，是在暗示有取消关注。所以第一问就让 record 带 following 布尔值，第二问 tests 直接用 following=False，不用改签名。
- 追问 check 里为什么用 get 不用方括号：_history 是 defaultdict，方括号查不存在的键会顺手建出空记录，一次只读查询就改了状态，内存也随查询增长。

## 测试要点

- test_never_followed：没有任何历史的两个人，第 0 秒和第 100 秒查都是 False。
- test_follow_then_time_boundaries：第 5 秒关注，查第 4 秒 False、第 5 秒 True、第 100 秒 True，保护闭区间。
- test_follow_unfollow_refollow：第 1 秒关注、第 5 秒取消、第 9 秒再关注，六个时刻各查一次，保护"历史全部保留、取消那一刻起不关注"。
- test_direction：A 关注 B 后 check(B, A, 2) 是 False，关注是单向的。
- test_pairs_independent：A 取消关注 B 不影响 A 对 M 的关注，每对人的历史独立。
- test_out_of_order_updates：第 9、1、5 秒的 update 乱序到达，查询结果和按序到达一样。
- test_same_time_last_write_wins：第 5 秒先关注后取消，check(A, B, 5) 和第 6 秒都是 False。
- test_self_follow_ignored：update(A, A, 1) 后 check(A, A, 2) 是 False。
- test_check_does_not_create_state：对从没出现过的 X、Y 调一次 check，_history 里不能出现 X。

## 更多说明

### 用例子走一遍

A 在第 1 秒关注 B，第 5 秒取消，第 9 秒再关注。这一对的 times 是 [1, 5, 9]，states 是 [True, False, True]。

| 查询 | bisect_right(times, t) | states[i - 1] | 结果 |
|---|---|---|---|
| check(A, B, 0) | 0 | 无 | False |
| check(A, B, 1) | 1 | states[0] = True | True |
| check(A, B, 3) | 1 | states[0] = True | True |
| check(A, B, 5) | 2 | states[1] = False | False |
| check(A, B, 7) | 2 | states[1] = False | False |
| check(A, B, 10) | 3 | states[2] = True | True |

### bisect_right 为什么等于"不超过 t 的事件条数"

bisect_right 返回把 t 插进有序列表时、放在所有等于 t 的元素右边的那个位置。这个位置左边的元素全都不超过 t，所以它的值就是不超过 t 的元素个数。times 是 [1, 5, 9]，查 t=5：等于 5 的元素在下标 1，插在它右边是下标 2，返回 2，左边的 1 和 5 都不超过 5。改用 bisect_left 查 t=5 返回 1，第 5 秒那条事件被漏掉，闭区间变成开区间。

### 乱序到达时 record 在做什么

第 9 秒的 update 先到，times 是 [9]。第 1 秒的到了，1 < 9 走插入路径，bisect_right([9], 1) 是 0，插到下标 0，times 变 [1, 9]，states 在同一下标插入。第 5 秒的取消到了，bisect_right([1, 9], 5) 是 1，插到中间，times 变 [1, 5, 9]，states 变 [True, False, True]。结果和按序到达完全一样，check 不用改。
