# 题面

## 原题要点

> Part 1 — users, follows & snapshots: add_user / follow / create_snapshot, plus Snapshot.is_following. A snapshot must not observe later follow() calls.
> Part 2 — follower/following lists: extend Snapshot with get_following / get_followers, motivating the eager reverse index.
> Part 3 — follow recommendations: add Snapshot.recommend (top-k 2-hop).
> The trap is treating the snapshot as a shallow view; the snapshot constructor must copy each followee set rather than alias it.

```python
class SocialNetwork:
    def add_user(self, user_id: str) -> None           # 已存在抛 ValueError
    def follow(self, follower: str, followee: str)     # 任一方不存在抛 ValueError；自己关注自己、重复关注不做任何事
    def create_snapshot(self) -> Snapshot              # 之后的 follow 不影响返回的对象

class Snapshot:
    def is_following(self, follower, followee) -> bool
    def get_following(self, user_id) -> list[str]
    def get_followers(self, user_id) -> list[str]
    def recommend(self, user_id, k) -> list[str]
```

## 这题要你写的东西是什么

还是关注关系，但没有时间戳。主表只存"现在谁关注谁"。想保留某一刻的状态，就调 create_snapshot 拿一个快照，之后所有对历史状态的查询都在快照上做。产品里的场景：每天凌晨拍一张快照给离线任务算推荐、算统计，白天主表继续被用户改，离线任务看到的永远是凌晨那张。

## 每个方法分别是什么意思

- add_user：建一个用户。
- follow：A 关注 B，改主表。
- create_snapshot：把主表此刻的状态复制一份，返回快照对象。
- Snapshot.is_following：快照上 A 是否关注 B。
- Snapshot.get_following：快照上 X 关注的人的名单。
- Snapshot.get_followers：快照上关注 X 的人的名单。
- Snapshot.recommend：快照上给 X 推荐"他关注的人也在关注的人"，取前 k。

## 题目分几问

1. add_user / follow / create_snapshot / is_following。要点是快照要逐个集合复制，不能只复制外层。
2. get_following / get_followers。要点是建快照时顺手建反向表。
3. recommend。要点是两层计数、剔除自己和已关注、取前 k。

## 题面故意没说清楚的地方

- 快照上查不存在的用户，返回 False / 空列表还是报错。
- 返回的名单有没有顺序。
- 推荐并列怎么排。
- 有没有 unfollow。
- 快照之后 add_user 的用户在快照里算不算存在。

## 面试形式

电话面 60 分钟，三段递进，每段写完就加测试。第一段是陷阱题，面试官看你会不会只复制外层。追问集中在"快照太贵怎么办"和并发。
