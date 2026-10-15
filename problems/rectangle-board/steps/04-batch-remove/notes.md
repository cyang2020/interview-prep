# 第4问：批量移除

## 这一问要做什么

- 加 batchRemove(x, y)：把盖住这格的所有矩形整张撕掉，包括被压在下面看不见的，返回撕掉的张数；一张没有返回 0。
- 整批在 undo 历史里只算一条，一次 undo 全部放回；返回 0 的那次不算。

## 核心思路

- 接口加一个 batchRemove(x, y)，返回撕掉的张数，一张没撕到返回 0。其余方法包括 undo 一行没改。
- batchRemove：顺着 rects 扫一遍，收集 active 且 covers(x, y) 的 rid 到 hit；hit 为空返回 0 不记历史；否则把 hit 里每张的 active 翻成 False，history 压一条 ("remove", hit)，返回 len(hit)。
- 不能用 getAt 选中：getAt 只给最上面一张，被压在下面看不见的也要撕。
- 不能复用 removeRectangle：它每张写一条历史，撕 3 张要 3 次 undo 才放回来，题目要一次 undo 整批放回。
- undo 不用改：第二问就把编号写成列表，for rid in ids 直接把整批的 active 改回 True，每张回到自己编号对应的那一层。
- hit 的顺序无所谓（代码里是编号从小到大）：放回来后谁压谁由编号决定，不看列表顺序。
- 复杂度：扫一遍 O(n)，翻标记 O(命中数)；undo 这一批 O(命中数)。

## 思考与反问

- 撕哪些？按盖住这格的全部活跃矩形，包括看不见的，每张整张撕。这决定了用 r.active and r.covers(x, y) 全扫，不用 getAt。
- 返回数量算不算已经撕掉的？按不算，筛选条件里带 active。两张铺满先 removeRectangle(1) 再 batchRemove(1,1)：返回 1，历史是 remove[2]；第一次 undo 只放回 2，第二次 undo 才放回 1。
- 历史怎么记？按整批一条。复用 removeRectangle 撕三张铺满后历史是 remove[1], remove[2], remove[3]，一次 undo 后 getAt(1,1) 看着也是 3，但 removeRectangle(1) 返回 False，正确状态应返回 True。
- 一张都没撕到呢？按返回 0 不记历史。记了的话紧接着的 undo 空跑一次，两张矩形一张也放不回来。
- 追问：四问加完哪些老代码被改过？只有 __init__ 多了 history，addRectangle 和 removeRectangle 各多一行写历史，其余全是新增方法。第一问定下的"存矩形不存格子、编号即层次"没被推翻。

## 测试要点

- test_batch_remove_official_example：(2,1) 上 1、2 都盖住但只看得见 2，batchRemove 返回 2；再调返回 0；一次 undo 两张都回来，2 仍在上面。
- test_batch_remove_takes_hidden_ones：1、2 铺满、3 只在 (0,0)，batchRemove(1,1) 返回 2，3 不动。
- test_batch_remove_removes_whole_rectangles：横条竖条在 (0,0) 相交，batchRemove(0,0) 后两条远端的格子都清掉。
- test_batch_remove_miss_writes_no_history：点空格子返回 0，第一次 undo 撤销的是 add。
- test_batch_remove_skips_already_removed：先 removeRectangle(1) 再 batchRemove 返回 1，两次 undo 各管各的记录，1 回来后压在 2 下面。
- test_batch_undo_keeps_order_inside_batch：三张整批撕掉再 undo，getAt 是 3，之后 removeAt 依次拿到 3、2。
- test_mixed_operations_undo_chain：add 两张后 removeAt 撕 2、batchRemove 撕 1，四次 undo 倒序撤回每一条，第五次返回 False。

## 更多说明

### 走一遍题目的例子

4 列 3 行，矩形 1 占 (1,0)-(2,1)，矩形 2 占 (2,1)-(3,2)，两张都盖住 (2,1) 但只看得见 2。

| 调用 | hit | history | 返回 |
|---|---|---|---|
| batchRemove(2,1) | [1, 2] | add[1], add[2], remove[1,2] | 2 |
| getAt(2,1) | — | 不变 | -1 |
| batchRemove(2,1) | [] | 不变 | 0 |
| undo | — | add[1], add[2] | True |
| getAt(2,1) | — | 不变 | 2 |
| getAt(1,0) | — | 不变 | 1 |

第五行一次 undo 放回两张，(2,1) 上面是 2 而不是 1，代码里没有任何一处记过"2 原来在 1 上面"。

### 三种记录在 undo 里走同一条路

| 记录 | 来自哪 | undo 做什么 |
|---|---|---|
| ("add", [5]) | addRectangle | 5 的 active 改 False |
| ("remove", [5]) | removeRectangle / removeAt | 5 的 active 改 True |
| ("remove", [1,2,7]) | batchRemove | 1、2、7 的 active 都改 True |
