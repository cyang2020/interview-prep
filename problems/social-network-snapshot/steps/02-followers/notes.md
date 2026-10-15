# 第二问：快照上的 get_following / get_followers

## 面试官给的骨架

题面给了两个签名，加在 Snapshot 上。

```python
class Snapshot:
    def get_following(self, user_id: str) -> list[str]: ...
    def get_followers(self, user_id: str) -> list[str]: ...
        # 快照构造时建好反向表，get_followers 才不用扫全表
```

## 思路

**开口先定的口径。**

1. 反向表在 Snapshot 构造函数里建，不在主表里维护。快照建好不变，反向表建一次永远有效，follow 保持一步。另一种做法是主表平时维护正反两张、follow 写两次、快照抄两张，也对，说清取舍。
2. 返回列表排序。集合没有顺序，排序让结果确定、测试好写。不要求顺序可以去掉。
3. 查不存在的用户返回空列表，和 is_following 返回 False 一个口径。

**新增的字段。** Snapshot._followers，被关注者 → 关注他的人的 frozenset。形状和 _following 一样，方向相反。

**反向表怎么建。** 先给正向表里每个用户在反向表开一个空 set。然后遍历正向表的每一行：这一行是 user 关注的人 f，f 里每个 followee，往 _followers[followee] 里加 user。扫完把每个 set 转成 frozenset。followee 一定在反向表里有行，因为 follow 时已经检查过两个用户都存在。

**get_following(user_id)。** 取 _following[user_id]，排序成列表。
**get_followers(user_id)。** 取 _followers[user_id]，排序成列表。

**不建反向表会怎样。** get_followers(B) 只能遍历 _following 的每一行，看 B 在不在那行的集合里。代价是用户数加关系数，每查一次都付。建了反向表，查一次只花 B 的粉丝数。

**用例子走一遍。** A 关注 B、C，B 关注 C。

| 步骤 | 看正向表哪一行 | 往反向表写什么 | 反向表 |
|---|---|---|---|
| 0 | 初始化 | 每人一个空行 | A:{} B:{} C:{} |
| 1 | A:{B, C} | B 行加 A，C 行加 A | A:{} B:{A} C:{A} |
| 2 | B:{C} | C 行加 B | A:{} B:{A} C:{A, B} |
| 3 | C:{} | 不写 | A:{} B:{A} C:{A, B} |

get_followers(C) 取 C 行，排序，[A, B]。get_followers(A) 取 A 行，[]。

**复杂度。** 构造函数多扫一遍正向表，仍是 O(用户数 + 关系数)，内存翻倍。get_following、get_followers 各是那个人的列表长度，排序再乘个对数。

## 常见疑问

### 为什么不在第一次调 get_followers 时才建反向表

可以，叫延迟建。好处是没人查粉丝就不花这份时间和内存。坏处是第一次查的人要等一次全表扫描，而且构造函数之外多了一个"建过没有"的状态要管。面试里先写构造时建，面试官问到再说延迟建。

### 主表维护两张表的做法差在哪

follow(A, B) 要写 _following[A] 和 _followers[B] 两处，两处必须同时成功，多一个出错点。快照要抄两张表。好处是建快照不用再扫一遍。两种代价量级相同，选哪个看你想把工作放在 follow 还是放在 create_snapshot。

### 为什么反向表也用 frozenset

和正向表一个理由：快照不可改。反向表建好以后也不该有人往里加。
