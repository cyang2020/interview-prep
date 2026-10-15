# 第三问：快照上的 recommend(user_id, k)

## 这一问要做什么

- 在 Snapshot 上加 recommend(user_id, k)：返回一个列表，里面是 user_id 还没关注、但他关注的人里有人在关注的用户。
- 排序规则：user_id 关注的人里有几个关注了这个候选人，数越大越靠前，取前 k 个。不推荐 user_id 自己和他已关注的人。

## 核心思路

- 接口：Snapshot 加 recommend(user_id, k)，返回 list。推荐"user_id 关注的人也在关注的人"，按中间人数从多到少取前 k。只用 _following，不碰 _followers，快照上不加新字段。
- 三步：first_hop = _following.get(user_id, frozenset())；对 first_hop 里每个 b，遍历 _following[b] 里每个 c，c == user_id 或 c in first_hop 就 continue，否则 count[c] 加 1；`ranked = sorted(count, key=lambda c: (-count[c], c))`，返回 ranked[:k]。
- count 是方法内的局部 dict：候选人 → 中间人数，即"user_id 关注的人里有几个关注了 c"。
- 剔除放在内层循环里，不是算完 count 再删键：不要的人连计数都不做，count 里只有真候选，排序也少几项。算完再删也对，只是多存几个键。
- _following[b] 用方括号不用 get：b 来自 first_hop，follow 写入前检查过 followee 存在，b 一定是键。user_id 自己用 get，因为他可能是快照后才 add_user 的人。
- 复杂度：计数 O(F × G)，F 是 first_hop 大小，G 是每个中间人的关注数；排序 O(C log C)，C 是候选数；内存 O(C)。

## 思考与反问

- 开口确认两件事：候选只到第二层，不往第三层走；剔除 user_id 自己和 first_hop 里已关注的人。后者决定了 first_hop 要整体先拿到、内层循环每次做 continue 判断。不剔除的话，B 回关 A 之后 A 会被推荐给自己。
- 并列怎么排？按名字升序，key 的第二项 c 就是干这个的，只为结果确定。这个版本没有时间戳，没有"最近"可用；面试官说并列任意也行。
- k 的边界：k 为 0 返回 []，k 超过候选数返回全部，都靠 ranked[:k] 自然成立。k 为负数代码没拦，ranked[:k] 会从尾部切掉，面试里说明按 k >= 0 假设。
- 追问"k 很小、候选很多"：sorted 是 O(C log C)，换成大小为 k 的堆是 O(C log k)，Python 里 heapq.nsmallest(k, count, key=...) 一行。
- 追问"大 V 中间人"：A 关注的某个人关注了一百万人，第二层就要扫一百万。答法：每个中间人只取前 N 个、离线算好存 top-N、或抽样。
- 追问"为什么不用 _followers"：推荐走的是正向方向，A 关注的人、他们关注的人；_followers 回答"谁关注了 X"，这里用不上。变体"关注你的人也关注的人"才用它。

## 测试要点

- test_recommend_ranks_by_intermediary_count：题面例子里 D 有 B、C 两个中间人排第一，E、F 各一个并列按名字，recommend(A, 2) 是 [D, E]。
- test_recommend_excludes_self_and_already_followed：加上 B 回关 A、C 关注 B，第二层出现 A 自己和已关注的 B，结果仍是 [D, E, F]。
- test_recommend_k_bounds：k 为 0 返回 []，k 为 1 返回 [D]，k 为 100 返回全部 3 个。
- test_recommend_without_followees_or_unknown_user：D 没关注任何人、Z 不存在，都返回 []，不报错。
- test_recommend_ignores_later_follow：快照后 A 直接关注 D，旧快照 recommend(A, 1) 仍是 [D]，新快照里 D 已关注，变成 [E]。

## 更多说明

### 题面例子走一遍

A 关注 B、C；B 关注 D、E；C 关注 D、F。

| 步骤 | 看谁的那一行 | 遇到谁 | 剔除 | count |
|---|---|---|---|---|
| 0 | first_hop = {B, C} | | | 空 |
| 1 | B:{D, E} | D、E | 无 | D:1 E:1 |
| 2 | C:{D, F} | D、F | 无 | D:2 E:1 F:1 |
| 3 | 排序 | | | D、E、F |

recommend(A, 2) 切前 2 是 [D, E]。

### 剔除怎么起作用

再加两条边：B 关注 A，C 关注 B。看 B 那行多出 A，c == user_id，跳过。看 C 那行多出 B，c in first_hop，跳过。count 不变，结果还是 [D, E, F]。不剔除的话 count 会多出 A:1、B:1，按 (-count, 名字) 排完 recommend(A, 10) 变成 [D, A, B, E, F]，把自己和已关注的人推荐出来。
