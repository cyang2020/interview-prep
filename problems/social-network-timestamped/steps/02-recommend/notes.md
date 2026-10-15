# 第二问：2-hop 推荐，带时间

## 这一问要做什么

- 加 recommend(a, t, k=None)：t 时刻给 a 推荐"a 关注的人也在关注的人"，返回排好序的名字列表，k 不给就返回全部。
- 排序：中间人多的排前面；中间人一样多，指向候选人的关注边更新的排前面。
- 只算 t 时刻还在的关注关系；a 自己和 a 在 t 时刻已经关注的人不推荐。update / check 不变。

## 核心思路

- 第一问的 update / check 和两层 map 一行不改，只加三个方法：_PairHistory.followed_since(t)、FollowGraph.following_at(a, t)、FollowGraph.recommend(a, t, k=None)。
- followed_since(t)：i = bisect_right(times, t)，i 不为 0 且 states[i - 1] 为 True 就返回 times[i - 1]，否则返回 None。关注和取消交替时，这就是 t 时刻这段关注开始的时刻。
- following_at(a, t)：遍历 _history[a] 的全部键，这是 a 关注过的所有人，含已取消的；每个调 followed_since(t)，不是 None 的留下，返回 {被关注者: 开始时刻}。
- recommend 三步：first_hop = following_at(a, t)；对 first_hop 里每个 b 遍历 following_at(b, t)，c == a 或 c in first_hop 跳过，否则 count[c] 加 1、latest[c] 取 max(latest[c], since)；最后按 (-count[c], -latest[c], c) 排序，k 为 None 返回全部，否则切前 k。
- count 回答"c 有几个中间人"，是排序主键；latest 回答"指向 c 的最新一条关注边是什么时候"，是并列键；再并列按名字，只为结果确定。
- 剔除判断写在内层循环，每次遇到都判：a 自己和已关注的人可能被多个中间人指到，只在第一次遇到时判，第二次还会被计数。
- 复杂度：第一层 F 个人，每个中间人关注过 G 个人，每条关系一次二分，F × G × log(历史长度)；排序 C log C，C 是候选数；count 和 latest 两张表内存 O(C)。

## 思考与反问

- 两步都按 t 时刻的关系算，还是按当前关系？按 t 时刻，所以先写 following_at(a, t)，recommend 不读任何"当前关注集合"。B 第 3 秒关注 C、第 9 秒取消，recommend(A, 9) 里 C 的 count 从 2 降到 1。
- 并列时"最近"指哪条边？按指向候选人的那条边 b → c 的时刻，不是 a → b 的时刻。这决定了 following_at 返回 {b: since} 而不是集合，latest 直接用 since。两种口径一般给出不同顺序，开口先说选哪种。
- 剔除哪些候选？a 自己，和 a 在 t 时刻已关注的人。不剔除的话，第 6 秒 B 回关 A，recommend(A, 7) 会把 A 推荐给 A 自己；第 7 秒 M 关注 B，已被 A 关注的 B 也会被推出来。
- k 怎么处理？k 为 None 返回全部，k 大于候选数也返回全部，不报错。再并列按名字排只为测试好写，面试里说"剩下顺序任意"即可。
- 追问：following_at 为什么遍历"关注过的所有人"而不是只看"现在关注的"？_history[a] 的键含已取消的，历史不删，必须逐个二分判断。A 第 1 秒关注 B、第 5 秒取消、第 9 秒再关注，following_at(A, 10) 要有 B，following_at(A, 7) 不能有。
- 追问：一个大 V 中间人关注了一百万人？following_at(大 V, t) 要扫一百万条历史。答：每个中间人只取最近关注的 N 个；或离线算好推荐结果查询时直接读；k 小 C 大时排序换成大小为 k 的堆，C log k。

## 测试要点

- test_following_at_respects_time：第 0 秒是 {}，第 1 秒恰好 {B: 1}，第 8 秒 {B: 1, M: 2, D: 8} 值是开始时刻，B 在第 9 秒的列表里没有已取消的 C。
- test_recommend_counts_intermediaries：recommend(A, 5) 是 [C, D]，C 有 B、M 两个中间人，排在只有 B 的 D 前面。
- test_recommend_excludes_self_and_already_followed：第 6 秒 B 回关 A、第 7 秒 M 关注 B 之后，recommend(A, 7) 仍是 [C, D]，A 和 B 被剔除。
- test_recommend_excludes_newly_followed：第 8 秒 A 直接关注 D 后，recommend(A, 8) 只剩 [C]。
- test_recommend_drops_count_after_unfollow：第 9 秒 B 取消关注 C，C 仍由 M 到达，count 变 1 仍返回 [C]；recommend(A, 2) 时 B、M 还没关注任何人，返回 []。
- test_recommend_tie_break_by_recency：X、Y 都只有 1 个中间人，指向 Y 的边第 4 秒比指向 X 的第 3 秒新，结果 [Y, X]。
- test_recommend_top_k：k=1 只返回 [C]；k=5 大于候选数，返回全部 [C, D]。
- test_recommend_unknown_user：从没关注过任何人的 Z，recommend(Z, 9) 返回 []。

## 更多说明

### 测试共用的那张图

推荐测试都用 _example_graph 这 9 条事件，按时刻顺序 update 进去：

| 时刻 | 事件 | 时刻 | 事件 |
|---|---|---|---|
| 1 | A 关注 B | 6 | B 回关 A |
| 2 | A 关注 M | 7 | M 关注 B |
| 3 | B 关注 C | 8 | A 关注 D |
| 4 | B 关注 D | 9 | B 取消关注 C |
| 5 | M 关注 C | | |

### 每次查询长什么样

| 查询 | first_hop | 第二层遇到的 | 剔除 | count / latest | 结果 |
|---|---|---|---|---|---|
| recommend(A, 2) | {B, M} | 无 | 无 | 空 | [] |
| recommend(A, 5) | {B, M} | B→C, B→D, M→C | 无 | C: 2 / 5；D: 1 / 4 | [C, D] |
| recommend(A, 7) | {B, M} | B→C, B→D, B→A, M→C, M→B | A 是自己，B 已关注 | C: 2 / 5；D: 1 / 4 | [C, D] |
| recommend(A, 8) | {B, M, D} | 同上，D 没关注任何人 | A、B，加上 D 已关注 | C: 2 / 5 | [C] |
| recommend(A, 9) | {B, M, D} | B→D, B→A, M→C, M→B | A、B、D | C: 1 / 5 | [C] |

latest 一列记的是 b → c 这条边的 since：C 被 B 第 3 秒、M 第 5 秒指到，取 max 得 5。

### "最近"两种口径会给不同结果

A 第 1 秒关注 B、第 4 秒关注 M；B 第 3 秒关注 X；M 第 2 秒关注 Y。X、Y 都只有 1 个中间人。按指向候选人的边：X 是第 3 秒，Y 是第 2 秒，X 排前。按 A 出去的边：到 X 经过 B 是第 1 秒，到 Y 经过 M 是第 4 秒，Y 排前。代码按前者，latest 存的是 following_at(b, t) 返回的 since，也就是 b → c 这条边的时刻。

### followed_since 返回的到底是什么时刻

i = bisect_right(times, t) 找到不超过 t 的最后一条事件，states[i - 1] 为 True 才有返回值，返回 times[i - 1]。关注和取消交替出现时，这就是当前这段关注开始的时刻。如果同一对人连续两条 following=True（第 1 秒和第 3 秒各一条、中间没取消），返回的是第 3 秒不是第 1 秒，latest 排序时会把这次重复关注当成更新的边。要严格按"这段开始"算，record 时跳过和上一条 states 相同的事件即可。
