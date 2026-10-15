# 第二问：快照上的 get_following / get_followers

## 这一问要做什么

- 在 Snapshot 上加 get_following(user_id) 和 get_followers(user_id)：前者返回快照上 user_id 关注的人的列表，后者返回快照上关注 user_id 的人的列表。
- 比上一问多的要求：要能按"被关注者"反过来查谁关注了他。主表 SocialNetwork 的三个方法不变。

## 核心思路

- 接口：Snapshot 加 get_following(user_id) 和 get_followers(user_id)，都返回排好序的 list。主表 SocialNetwork 的三个方法不动。
- 新增字段 Snapshot._followers：被关注者 → 关注他的人的 frozenset，回答"快照时刻谁关注了 X"。_following 只能按关注者查，回答这个问题要扫全表。
- 建法在 Snapshot.__init__ 里：先给 following 里每个用户开一个空 set；遍历每一行 (user, f)，f 里每个 followee 执行 followers[followee].add(user)；扫完每行转 frozenset。followee 一定有行，因为 follow 时检查过两个用户都存在。
- get_following：`sorted(self._following.get(user_id, frozenset()))`。get_followers：`sorted(self._followers.get(user_id, frozenset()))`。不存在的用户两边都返回 []。
- 复杂度：构造函数多扫一遍正向表，仍是 O(用户数 + 关系数)，内存翻倍；get_followers(X) 花 X 的粉丝数再乘排序的 log。不建反向表的话每次 get_followers 都要扫一遍 _following，O(用户数 + 关系数)。

## 思考与反问

- 反向表建在哪？按"Snapshot 构造时建一次"做，主表只维护 _following，follow 仍然只写一处。另一种是主表平时维护正反两张、follow 写两处、快照抄两张：建快照省一遍扫描，但 follow 多一个出错点，两种代价量级相同。
- 返回要不要排序？按排序做，get_following、get_followers 都套 sorted。集合没顺序，排序让结果确定、测试好写；面试官说不要求顺序就把 sorted 去掉。
- 不存在的用户返回什么？按返回 [] 做，和第一问 is_following 返回 False 一个口径，两个方法都用 .get(user_id, frozenset())。
- 为什么 _followers 也用 frozenset：快照不可改，反向表建好以后也不该有人往里加，和 _following 同一个理由。
- 追问"延迟建反向表"：第一次调 get_followers 时才建，没人查粉丝就不花这份时间和内存；代价是第一次查的人要等一次全表扫描，并且多一个"建过没有"的状态要管。先写构造时建，被问到再说这个。
- 追问"快照后 follow(C, A)，旧快照 get_followers(A) 是什么"：仍是 []。反向表是从快照自己那份 _following 建的，主表再改和它无关；新建一张快照才是 [C]。

## 测试要点

- test_get_following：A 关注 B、C 时 get_following(A) 是 [B, C]，排过序；C 没关注任何人返回 []。
- test_get_followers：A、B 都关注 C 时 get_followers(C) 是 [A, B]；没人关注 A 时返回 []。
- test_lists_for_unknown_user_are_empty：查不存在的 Z，两个方法都返回 []，不报错。
- test_following_and_followers_are_consistent：每个 user 的 get_following 里的每个 followee，其 get_followers 里都有 user，正反两张表对得上。
- test_lists_ignore_later_follow：快照后 follow(C, A)，旧快照 get_followers(A) 和 get_following(C) 都是 []，新快照 get_followers(A) 是 [C]。

## 更多说明

### 反向表怎么建出来

A 关注 B、C；B 关注 C。构造函数扫 following 的过程：

| 步骤 | 看 following 哪一行 | 往 followers 写什么 | followers |
|---|---|---|---|
| 0 | 初始化 | 每人一个空 set | A:{} B:{} C:{} |
| 1 | A:{B, C} | B 行加 A，C 行加 A | A:{} B:{A} C:{A} |
| 2 | B:{C} | C 行加 B | A:{} B:{A} C:{A, B} |
| 3 | C:{} | 不写 | A:{} B:{A} C:{A, B} |

扫完每行转 frozenset 存进 _followers。get_followers(C) 取 C 行排序得 [A, B]；get_followers(A) 取 A 行得 []。

### 不建反向表 get_followers 怎么查

get_followers(B) 只能遍历 _following 的每一行，看 B 在不在那行的集合里。1000 个用户、10 万条关系，查一次扫 10 万，每查一次都付。建了 _followers，查一次只花 B 的粉丝数。
