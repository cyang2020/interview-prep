# 第一问：add_user / follow / create_snapshot / is_following

## 面试官给的骨架

这个版本题面附了签名和规则，直接按它写。

```python
class SocialNetwork:
    def add_user(self, user_id: str) -> None: ...
        # 用户已存在抛 ValueError

    def follow(self, follower: str, followee: str) -> None: ...
        # 任一方不存在抛 ValueError；自己关注自己不做任何事；重复关注不做任何事

    def create_snapshot(self) -> 'Snapshot': ...
        # 返回的对象不受之后 follow() 的影响

class Snapshot:
    def is_following(self, follower: str, followee: str) -> bool: ...
```

## 思路

**开口先定的口径。**

1. 快照是主表那一刻的一份复制品，复制要到每个用户的集合这一层。这决定了 Snapshot 的构造函数里要对每个集合新建一份，不能只新建外层表。
2. 用户不存在报错，自己关注自己和重复关注不报错。区分理由：前者是调用方的错误，吞掉会让数据悄悄变脏；后两者无害，重试不该炸。
3. 快照里查不存在的用户返回 False，不报错。快照是只读查询，查一个快照之后才加的用户，答"没关注"比抛错合理。
4. 快照对象自己不可改。用 frozenset 在类型上保证，不靠约定。

**数据结构。** SocialNetwork._following 是一张表，用户 → 他关注的人的 set。用 set 不用 list：判断"是否已关注"是常数时间；往 set 里加已有元素不会变，所以"重复关注不做任何事"不用额外写判断。Snapshot._following 是同样形状的表，但每个值是 frozenset。

**四个方法各做什么。**

- add_user：键已存在抛 ValueError；否则加一个键，值是空 set。
- follow：先查两个用户都在表里，不在抛 ValueError；follower 等于 followee 直接返回；否则往 _following[follower] 里加 followee。
- create_snapshot：把 _following 交给 Snapshot 的构造函数，自己不改任何东西。
- Snapshot.is_following：在自己那份表里查 followee 是否在 _following[follower] 里；follower 不在表里就当空集合。

**为什么只复制外层会错。** 主表是 {A: set_A, B: set_B}。写成 dict(主表) 得到一张新表，但新表里 A 对应的还是 set_A 这同一个对象。之后 follow(A, C) 执行的是 set_A.add(C)，快照那张表里 A 对应的也是 set_A，所以快照查 (A, C) 变成 True。写成 {u: frozenset(s) for u, s in 主表.items()} 时，每个用户都新建了一个集合对象，主表再改 set_A 和快照无关。

**用例子走一遍。**

| 步骤 | 操作 | 主表 | 快照 |
|---|---|---|---|
| 1 | add_user A、B、C | A:{} B:{} C:{} | |
| 2 | follow(A, B) | A:{B} B:{} C:{} | |
| 3 | s1 = create_snapshot() | 不变 | s1: A:{B} B:{} C:{} |
| 4 | follow(A, C) | A:{B, C} B:{} C:{} | s1 不变 |
| 5 | s2 = create_snapshot() | 不变 | s2: A:{B, C} B:{} C:{} |
| 6 | add_user D；follow(A, D) | A:{B, C, D} B:{} C:{} D:{} | s1、s2 不变 |

s1.is_following(A, C) 是 False，s2.is_following(A, C) 是 True，s2.is_following(A, D) 是 False。只复制外层的话，第 4 步之后 s1 查 (A, C) 错成 True。

**复杂度。** add_user、follow、is_following 常数时间。create_snapshot 复制整张表，时间和内存都是 O(用户数 + 关注关系数)。这是追问"快照太贵"的入口。

## 常见疑问

### frozenset(s) 是复制还是引用

是新建。frozenset(s) 读 s 里的元素，造一个新的不可变集合对象，和 s 没有关系。s 之后再加元素，frozenset 不变。用 set(s) 也是新建，区别只是 set(s) 还能被改，frozenset 不能，所以快照用 frozenset 多一层保证。

### 为什么 is_following 对不存在的用户不报错，follow 却报错

follow 是写操作，写到一个不存在的用户上会产生没人创建过的记录，所以要拦住。is_following 是读操作，读不到就是没有，返回 False 不会产生任何副作用。读写两边口径不同是合理的，但要在面试里说出来。

### 快照之后新加的用户，快照里查得到吗

查不到。Snapshot 构造时只复制了当时表里的用户。之后 add_user D、follow(A, D)，快照里 A 的集合是 frozenset({B})，没有 D；D 本身也不是快照表的键。两个方向查都是 False。
