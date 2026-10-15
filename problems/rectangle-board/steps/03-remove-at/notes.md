# 第3问：按单元格移除

## 这一问要做什么

- 加 removeAt(x, y)：把这格最上面那张整张撕掉，返回它的编号；这格没有矩形返回 -1。
- 成功的 removeAt 在 undo 历史里算一条，和 removeRectangle 一样；点到空格子不算。

## 核心思路

- 接口加一个 removeAt(x, y)，返回被撕掉的编号，空格子返回 -1。其余方法一行没改。
- 没有新字段。"这格最上面那张"就是 getAt(x, y) 的答案，选中规则和它完全同义。
- removeAt：rid = getAt(x, y)；rid == -1 直接返回 -1，不动板子不记历史；否则调 removeRectangle(rid)，返回 rid。
- removeRectangle 的返回值不检查：rid 来自 getAt，一定 active，removeRectangle 一定返回 True。
- 历史里 removeAt 和 removeRectangle 没区别，都是一条 ("remove", [rid])，所以写历史的代码仍只有 removeRectangle 一处。
- 复杂度：一次 getAt，O(n)；后面翻标记和 append 都 O(1)。

## 思考与反问

- 点在重叠格上撕哪几张？按只撕最上面那一张、整张撕，全部撕是第四问 batchRemove 的事。这决定了 removeAt 用 getAt 选中，不自己扫。
- 这格是空的怎么办？按返回 -1 且不记历史。占了历史的话紧接着的 undo 会空跑一次返回 True，后面所有撤销错位一格。
- 成功的 removeAt 在历史里和 removeRectangle 有区别吗？按没有，题目说 one operation in the existing undo history。这决定了 removeAt 复用 removeRectangle 而不是自己写历史。
- 不复用、自己翻标记自己写历史会怎样：写历史变成两处，第四问再加一处是三处，改历史格式时三处容易不一致。
- 追问：撤销 removeAt 后矩形回到最上面还是原来那层？原来那层。三张铺满，removeRectangle(3) 再 removeAt(1,1) 拿走 2，undo 后 getAt(1,1) 是 2 不是 3，3 还在撕掉状态。
- 追问：removeAt 返回 -1 和 removeRectangle 返回 False 是一回事吗？都表示什么都没做、不改板子不记历史，只是返回类型一个 int 一个 boolean。

## 测试要点

- test_remove_at_official_example：removeAt(2,1) 撕掉整张 2 返回 2，露出 1；undo 后 2 回到 1 上面；removeAt(0,2) 空格子返回 -1。
- test_remove_at_only_takes_the_top_one：三张铺满，连点两次 (1,1) 依次拿走 3、2，剩 1。
- test_remove_at_removes_whole_rectangle：在 (1,1) 点掉中间那张 2，它在 (2,2) 的格子也一起消失。
- test_remove_at_miss_writes_no_history：点空格子返回 -1 后，第一次 undo 撤销的是 add，不是那次空点击。
- test_remove_at_undo_restores_middle_layer：先 removeRectangle(3) 再 removeAt 拿走 2，undo 后 getAt 是 2；再 undo 放回 3 才是 3。

## 更多说明

### 走一遍题目的例子

4 列 3 行，矩形 1 占 (1,0)-(2,1)，矩形 2 占 (2,1)-(3,2)。

| 调用 | getAt 内部得到 | history | 返回 |
|---|---|---|---|
| removeAt(2,1) | 2 | add[1], add[2], remove[2] | 2 |
| getAt(2,1) | 1，2 走了露出 1 | 不变 | 1 |
| undo | — | add[1], add[2] | True |
| getAt(2,1) | 2，编号大自动回到上面 | 不变 | 2 |
| removeAt(0,2) | -1，这格没人盖 | 不变 | -1 |

最后一行那次空点击不占历史，是这一问最容易丢分的地方。

### 连点同一格

三张铺满整板，连点 (1,1)：

| 调用 | 返回 | 之后 getAt(1,1) |
|---|---|---|
| removeAt(1,1) | 3 | 2 |
| removeAt(1,1) | 2 | 1 |
| removeAt(1,1) | 1 | -1 |
| removeAt(1,1) | -1 | -1 |

每次只拿走一层，第四次没东西可拿，返回 -1 且不记历史。
