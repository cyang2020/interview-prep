# 题面

## 题目

- 写一个关注关系表：记谁关注了谁。再写一个快照：把某一刻的关注关系复制一份，之后主表怎么改，快照都不变，查历史状态都在快照上查。
- add_user(user_id)：建一个用户，已存在抛 ValueError。follow(follower, followee)：follower 关注 followee；任一方不存在抛 ValueError，自己关注自己、重复关注什么都不做。
- create_snapshot()：返回一个 Snapshot 对象，固定为此刻的关注关系。Snapshot.is_following(follower, followee)：在快照上查 follower 是否关注 followee，返回 True / False。
- Snapshot.get_following(user_id)：快照上 user_id 关注的人的列表。Snapshot.get_followers(user_id)：快照上关注 user_id 的人的列表。
- Snapshot.recommend(user_id, k)：在快照上给 user_id 推荐"他关注的人也在关注的人"，按有几个这样的中间人从多到少排，取前 k 个；不推荐他自己和他已关注的人。
- 第一问：add_user / follow / create_snapshot / is_following。快照建好之后主表再 follow、再 add_user，快照查出来的结果不能变。
- 第二问：Snapshot 上加 get_following / get_followers，两个列表都只看快照那一刻的关系。
- 第三问：Snapshot 上加 recommend，只看快照那一刻的关系。

## 要问清楚的地方

- 快照上查不存在的用户（包括快照之后才 add_user 的人），返回 False / 空列表还是报错。
- get_following / get_followers 返回的列表有没有顺序要求。
- recommend 里中间人数相同的候选怎么排。
- 有没有 unfollow。
