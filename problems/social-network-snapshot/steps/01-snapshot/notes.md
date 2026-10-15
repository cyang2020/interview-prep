# 第一问：add_user / follow / create_snapshot / is_following

## 这一问要做什么

- 写 SocialNetwork 的 add_user、follow、create_snapshot，和 Snapshot 的 is_following。add_user 建用户，follow 让一个人关注另一个人，create_snapshot 返回一个 Snapshot 对象。
- is_following(follower, followee) 在快照上查 follower 是否关注 followee，返回 True / False。
- 规则：快照建好之后主表再 follow、再 add_user，快照查出来的结果不能变。add_user 已存在、follow 任一方不存在要抛 ValueError；自己关注自己、重复关注什么都不做。

## 核心思路

- 主表 SocialNetwork._following：用户 → 他关注的人的 set，回答"现在谁关注谁"。用 set 不用 list：查"是否已关注"O(1)，往 set 里加已有元素不变，"重复关注不做任何事"不用额外写判断。
- add_user：键已存在抛 ValueError，否则加一个键，值是空 set。follow：先查 follower、followee 都在表里，不在抛 ValueError；follower == followee 直接 return；否则 _following[follower].add(followee)。
- create_snapshot：把 _following 交给 Snapshot 构造函数，主表自己什么都不改。
- Snapshot._following：和主表同形状，但每个值是 frozenset(f) 新建的。构造函数写 `{user: frozenset(f) for user, f in following.items()}`，复制到每个用户的集合这一层，不是只复制外层 dict。
- Snapshot.is_following：`followee in self._following.get(follower, frozenset())`。follower 不在快照里就当空集合，返回 False。
- 复杂度：add_user、follow、is_following 都 O(1)；create_snapshot 抄整张表，时间和内存 O(用户数 + 关注关系数)。

## 思考与反问

- 快照复制到哪一层？按"每个用户的集合都新建一份"做，决定了 Snapshot.__init__ 里对每个 f 调 frozenset(f)。只写 dict(following) 的话：主表是 {A: set_A}，快照里 A 对应的还是 set_A 同一个对象，之后 follow(A, C) 执行 set_A.add(C)，快照查 (A, C) 也变成 True。
- 哪些情况报错？用户不存在抛 ValueError；自己关注自己、重复关注不报错也不记录。前者是调用方的错，吞掉数据会悄悄变脏；后两者无害，调用方重试不该炸。
- 快照上查不存在的用户怎么办？按返回 False 做，所以 is_following 用 .get(follower, frozenset())。快照是只读查询，查一个快照之后才 add_user 的人，答"没关注"比抛错合理；follow 是写操作，写到不存在的用户上会产生没人创建过的记录，必须拦。读写两边口径不同，要主动说。
- 为什么用 frozenset 不用 set(f)：两者都是新建对象，区别是 frozenset 改不了，快照"不可改"由类型保证，不靠约定。
- 追问"建快照抄全表太贵"：写时复制，主表集合也用 frozenset，follow 时换一个新集合，快照只抄外层 dict，O(用户数)。再追问就是边记时间戳、快照只是一个版本号。
- 追问"快照之后新加的用户在快照里算什么"：构造时只抄了当时表里的键，add_user D 后再 follow(A, D)，快照里 A 的集合没有 D，D 也不是键，(A, D) 和 (D, A) 都 False。

## 测试要点

- test_add_user_duplicate_raises：同一个 user_id 加两次，第二次抛 ValueError。
- test_follow_unknown_user_raises：follower 不存在、followee 不存在，各抛一次 ValueError。
- test_follow_is_directional：follow(A, B) 后 is_following(A, B) 为 True，(B, A) 为 False。
- test_self_follow_and_duplicate_follow_are_noops：follow(A, A) 和两次 follow(A, B) 后 _following[A] 仍是 {B}，不报错。
- test_snapshot_ignores_later_follow：快照后再 follow(A, C)，旧快照 is_following(A, C) 仍为 False。只复制外层 dict 会挂在这一条。
- test_two_snapshots_are_independent：先后两张快照，s1 查 (A, C) 是 False，s2 是 True，互不影响。
- test_snapshot_ignores_later_add_user：快照后 add_user D 并 follow(A, D)，快照里 (A, D) 和 (D, A) 都 False。
- test_empty_network_snapshot：空主表建快照，查任何人都 False，不报错。

## 更多说明

### 用例子走一遍

| 步骤 | 操作 | 主表 _following | 快照 |
|---|---|---|---|
| 1 | add_user A、B、C | A:{} B:{} C:{} | |
| 2 | follow(A, B) | A:{B} B:{} C:{} | |
| 3 | s1 = create_snapshot() | 不变 | s1：A:{B} B:{} C:{} |
| 4 | follow(A, C) | A:{B, C} B:{} C:{} | s1 不变 |
| 5 | s2 = create_snapshot() | 不变 | s2：A:{B, C} B:{} C:{} |
| 6 | add_user D；follow(A, D) | A:{B, C, D} B:{} C:{} D:{} | s1、s2 不变 |

s1.is_following(A, C) 是 False，s2.is_following(A, C) 是 True，s2.is_following(A, D) 是 False。只复制外层 dict 的话，第 4 步 set_A.add(C) 改的正是 s1 里 A 对应的那个对象，s1 查 (A, C) 会错成 True。
