# 第2问：undo

## 这一问要做什么

- 加 undo()：撤销最近一次改动过板子的操作，返回 true；没有可撤的返回 false。
- 成功的 addRectangle 和成功的 removeRectangle 各算一次改动，撕掉被完全压住、画面没变的也算；失败的 remove、getAt、undo 本身不算。
- 撤销一次 add 之后，下一次 add 的编号照样往上发，不回退。

## 核心思路

- 接口加一个 undo()。其余方法签名不变，只是 addRectangle 和 removeRectangle 成功时各多一行写历史。
- 新增 history 栈，每条是 ("add" 或 "remove", [编号列表])，回答"最近一次改动板子的操作是什么、涉及哪些编号"。坐标不存，矩形对象没删过；层次不存，编号就是层次。
- 哪些进历史：addRectangle 必进；removeRectangle 只在翻了 active 之后进，return False 那条路不进；getAt 不碰 history。
- undo：history 空返回 False；否则 pop 一条，alive = action == "remove"，把 ids 里每个编号的 active 设成 alive，返回 True。撤销后不再 append，所以 undo 自己不占历史。
- 编号不回退：rid 仍来自 len(rects) + 1，撤销 add 只把 active 改成 False，不从 rects 弹元素，下一次 add 继续往上发。
- 编号那一项从这一问就写成列表，虽然现在每条只有一个编号：第四问 batchRemove 一条记录装 n 个编号，undo 一行不用改。
- 复杂度：undo O(k)，k 是这条记录里的编号数，这一问恒为 1；add、remove 各多一次 append，仍 O(1)；history 内存 O(操作数)。

## 思考与反问

- 被完全压住的矩形被撕掉、画面没变，算一次改动吗？按算，removeRectangle 写历史不看可见性。不算的话：1、2 都铺满，removeRectangle(1) 后 undo 会撤销 add[2]，两张全丢。
- 失败的 remove、getAt 算不算？按不算。写历史那行放在 return False 之后，getAt 里没有 history。算了的话之后每次 undo 都错位一格。
- 要 redo 吗？按不要，一个栈够。要的话再开一个 redo 栈，undo 时把弹出的记录压进去，任何新的 add / remove 把它清空。
- 为什么恢复 remove 时不用存"原来在第几层"：三张铺满，removeRectangle(2) 再 undo，getAt(1,1) 还是 3；2 回到 1 上、3 下，是因为 1 < 2 < 3，不是因为记了位置。加了 bringToFront 这条就不成立。
- 撤销 add[5] 时 5 会不会已经被撕掉了：不会。撕 5 的 remove[5] 一定压在 add[5] 之上，栈先弹 remove[5] 复活 5 再轮到 add[5]；第二次撕同一张返回 False 不记历史，所以栈里一张矩形最多一条 remove。undo 里不需要校验。

## 测试要点

- test_undo_official_example：removeRectangle(1) 在画面不变时也算一条；三次 undo 依次放回 1、撤销 add 2、撤销 add 1，第四次返回 False。
- test_failed_remove_writes_no_history：removeRectangle(77) 和第二次 removeRectangle(1) 都不占历史，两次 undo 后历史就空了。
- test_getat_writes_no_history：两次 getAt 后第一次 undo 撤销的仍是 add。
- test_undo_does_not_create_history：add 后 undo 成功，再 undo 返回 False，undo 自己不是一条可撤销的操作。
- test_ids_keep_increasing_after_undo：撤销 add 2 后下一次 add 发 3；此时 removeRectangle(2) 返回 False。
- test_undo_restores_stacking_position：三张铺满，removeRectangle(2) 再 undo，getAt(1,1) 还是 3；移除 3 后才是 2。

## 更多说明

### 走一遍题目的例子

4 列 3 行，add(1,0,2,1) 发 1，add(2,1,3,2) 发 2，然后 removeRectangle(1)。这一步画面完全没变：(2,1) 上还盖着 2，1 的其他格子本来就只有它自己。

| 调用 | history（左旧右新） | active 的编号 | 返回 |
|---|---|---|---|
| add → 1 | add[1] | 1 | 1 |
| add → 2 | add[1], add[2] | 1,2 | 2 |
| removeRectangle(1) | add[1], add[2], remove[1] | 2 | True |
| undo | add[1], add[2] | 1,2 | True |
| undo | add[1] | 1 | True |
| undo | 空 | 无 | True |
| undo | 空 | 无 | False |

第四行 undo 只把 1 的 active 改回 True，没有"插回第几层"的动作，这时 getAt(2,1) 是 2，因为 2 的编号更大。

### 规则对照代码

| 规则 | 代码里哪一行 |
|---|---|
| 成功的 add 算一条 | addRectangle 末尾 history.append(("add", [rid])) |
| 成功的 remove 算一条，不看可见性 | removeRectangle 翻 active 后 history.append(("remove", [rectangleId])) |
| 失败的 remove 不算 | 写历史那行在 return False 之后 |
| getAt 不算 | getAt 不碰 history |
| undo 吃掉它撤销的那条，自己不留 | history.pop()，之后不 append |
| 编号不回退 | rid 仍是 len(rects) + 1，撤销 add 不从 rects 删元素 |
