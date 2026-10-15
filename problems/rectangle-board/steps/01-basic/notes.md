# 第1问：贴、撕、查

## 这一问要做什么

- 写 RectangleBoard 的 addRectangle、removeRectangle、getAt：贴一张矩形拿到编号、按编号撕掉整张、查某格最上面是哪张。
- 后贴的压在先贴的上面；撕掉上面那张后，下面被压住的要重新露出来。编号从 1 递增，撕掉也不回收。

## 核心思路

- 每张矩形一个 Rect 对象：rid、x1、y1、x2、y2、active。active 回答"这张现在在不在板上"，移除只翻它，坐标永远留着。
- rects 是按添加顺序排的列表，矩形永不从里面删除。下标 i 存编号 i+1，所以 _find 按编号取矩形是 O(1)，不用另开字典。
- 叠放顺序不单独存：编号按添加顺序递增且不复用，所以编号大的一定压着编号小的。
- addRectangle：rid = len(rects) + 1，append，返回 rid。removeRectangle：_find 取不到或 active 已是 False 返回 False；否则翻成 False 返回 True。
- getAt：从 rects 尾部往前扫，第一个 active 且 covers(x, y) 的 rid 就是答案，扫完没有返回 -1。尾部是编号最大的，所以第一个命中就是最上面的。
- covers 两边都带等号：x1 <= x <= x2 and y1 <= y <= y2，边界格也算覆盖。
- 复杂度：add、remove O(1)；getAt O(n)，n 是累计添加过的矩形数，最多 2000；内存 O(n)。

## 思考与反问

- 有没有"把某张挪到最上面"这类操作？按没有。这决定了 getAt 只比 rid、不另存层次序号；有的话编号就不再等于叠放顺序。
- 移除是整张撕掉，还是只擦它在某格的覆盖？按整张。这决定了 Rect 只有一个 active 标记，不用按格记部分覆盖。
- 编号会不会复用？按不复用且连续递增。这决定了 rid 用 len(rects) + 1 算，rects 下标直接当编号表。
- 为什么不开一个 50×50 的二维表记每格最上面是谁：removeRectangle(2) 之后被 2 压住的 1 要重新露出来，二维表里只剩 2 没有 1，得按编号把所有活跃矩形重刷一遍，O(矩形数 × 面积)，第二问 undo 又要重刷。
- 为什么撕掉的矩形不从 rects 里删：删了 len(rects) + 1 发出的编号会重复，第二问 undo 也需要坐标还在。代价是 getAt 多扫几个不活跃的，n 上限 2000，不值得省。
- 追问 getAt 调用量极大怎么办：每格挂一个编号列表，add 时往覆盖的每格追加，查询从列表尾部找第一个活跃的；add 变 O(面积)，查询变 O(该格深度)。

## 测试要点

- test_official_example：题目例子；(2,1) 被 1、2 都盖住时返回 2，移除 2 后露出 1，(3,2) 变 -1，再移除 2 返回 False。
- test_boundary_is_inclusive：(1,1)-(3,3) 的左上角和右下角本身算覆盖，紧挨着的 (0,1)、(4,3) 不算。
- test_single_cell_rectangle：(0,0)-(0,0) 是合法矩形，getAt(0,0) 能查到。
- test_remove_removes_whole_rectangle：横条和竖条在 (0,0) 相交，移除竖条后它在 (0,3) 的格子也一起消失。
- test_bad_ids：编号 0、-5、99 都返回 False，失败的移除不改板子。
- test_ids_never_reused：移除 1 后再 add 发 2，不补 1。
- test_stacking_follows_id_order：三张铺满，移除 3 露出 2；移除底下的 1 画面不变；全移除后 -1。

## 更多说明

### 用题目的例子走一遍

4 列 3 行。addRectangle(1,0,2,1) 发到 1，addRectangle(2,1,3,2) 发到 2，rects = [Rect1(active), Rect2(active)]。

| 调用 | 从尾部往前第一个命中 | 返回 |
|---|---|---|
| getAt(2,1) | Rect2 active，x∈[2,3]、y∈[1,2] 含 (2,1) | 2 |
| removeRectangle(2) | Rect2 active 翻成 False | True |
| getAt(2,1) | Rect2 跳过；Rect1 的 x∈[1,2]、y∈[0,1] 含 (2,1) | 1 |
| getAt(3,2) | Rect2 跳过；Rect1 的 x∈[1,2] 不含 3 | -1 |
| removeRectangle(2) | Rect2 已经不 active | False |

### 为什么"最上面"等于"编号最大"

编号 5 一定比 3 后加，一定压着 3；中间撕掉 4 不影响这两张的关系。三张铺满整板的矩形：

| 操作 | active 的编号 | getAt(1,1) |
|---|---|---|
| 加 1、2、3 | 1,2,3 | 3 |
| 撕掉 3 | 1,2 | 2 |
| 撕掉 1 | 2 | 2，画面不变但 1 确实不在了 |
| 撕掉 2 | 无 | -1 |

每一行的答案都是 active 集合里的最大编号，不需要任何额外记录。

### covers 为什么两边都带等号

题面写了 including every cell on its boundaries。(1,1)-(3,3) 覆盖 x = 1,2,3 和 y = 1,2,3 共 9 格，不是 4 格。一边漏等号，单格矩形 (0,0)-(0,0) 就永远查不到。
