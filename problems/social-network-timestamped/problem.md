# 题面

## 原题要点

> Build a follower/followee data structure with timestamped queries and friend-of-friend recommendations.
> update(A, B, t): A starts following B at time t
> check(A, B, t): at time t, is A following B?
> 2-hop recommendation: if A → B → C, A → B → D, A → M → C, recommend [C, D] to A — C ranks higher because it has 2 intermediaries.
> Each edge carries a timestamp; recommendation sorts by intermediary count, break ties by recency.
> Evaluation explicitly covers comprehensive unit tests and a clear explanation of state transitions.

```
update(A, B, t) -> None
check(A, B, t) -> bool
recommend(A, t, k=None) -> list    # 题面只给规则，签名按规则还原
```

## 这题要你写的东西是什么

一个放在内存里的关注关系记录。社交产品里用户点"关注"，系统调 update 记一笔"A 从 t 时刻起关注 B"。之后任何人可以问"t 时刻 A 是否关注 B"：客服查某条投诉发生时两个人是不是关注关系，审计回放某一天的状态。推荐系统再拿这些关系给 A 算"你可能认识的人"。

## 每个方法分别是什么意思

- update(A, B, t)：记一笔。A 在 t 时刻开始关注 B。追问时加 following=False 表示 t 时刻取消关注。
- check(A, B, t)：查一笔。在 t 时刻 A 是否正在关注 B。t 可以是过去任意时刻。
- recommend(A, t, k)：t 时刻给 A 推荐。候选是 A 关注的人关注的人，按有几个中间人排序，取前 k。

## 题目分几问

1. update 和 check。要点是保留历史，能回答过去任意 t。
2. 2-hop 推荐，带 t。要点是"t 时刻 A 关注的所有人"这个列举操作，以及剔除自己和已关注的人。

## 题面故意没说清楚的地方

- update 是否按时间顺序到达。
- 有没有取消关注。方法名叫 update 不叫 follow，是在暗示有。
- t 恰好等于关注时刻算不算关注。
- 同一对人同一时刻两条 update 怎么办。
- 推荐并列时"最近"指哪条边：指向候选人的边，还是 A 出去的边。
- 自己关注自己怎么处理。

## 面试形式

电话面 60 分钟或 onsite 一轮。先 update/check，写完加测试，再加推荐。打分点写明两条：单元测试要全，状态变化要讲清楚。后半段可能追问"设计 Twitter"里的时间线合并，或快照版的追问。
