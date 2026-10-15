# 第3问：按单元格移除

## 面试官给的骨架

```
int removeAt(int x, int y)
```

其余方法完全不变。

## 思路

### 开口先定的口径

- 点在重叠的格子上，撕掉哪几张？**只撕最上面那一张**，整张撕掉，不是只撕它在这格上的那一块。
- 这格是空的怎么办？返回 -1，而且**不许留历史记录**。
- 成功的 `removeAt` 和成功的 `removeRectangle` 在历史里有区别吗？**没有**。题目原话：A successful removeAt call is one operation in the existing undo history，撤销它要把同一张矩形放回原来那一层。

最后这条口径决定了代码的形状：既然历史里没区别，那 `removeAt` 就不该自己写历史，而应该调用 `removeRectangle`，让写历史的逻辑只有一处。

### 两行拼起来

"这格最上面那张是谁"已经有现成答案了，就是 `getAt(x, y)`。所以：

| 步骤 | 做什么 | 为什么 |
|---|---|---|
| 1 | `rid = self.getAt(x, y)` | 选中规则和 getAt 的"最上面"完全同义 |
| 2 | `rid == -1` 就直接返回 -1 | 空格子不动板子、不记历史 |
| 3 | `self.removeRectangle(rid)` | 翻标记 + 写历史都在它里面 |
| 4 | 返回 `rid` | 题目要返回被撕掉的编号 |

第 3 步不检查返回值：`rid` 来自 `getAt`，它一定是活跃的，`removeRectangle` 一定返回 true。

不复用 `removeRectangle`、自己翻标记自己写历史，会怎样？代码会变成两处写历史。第四问再加一处，就是三处——以后任何一处改了历史格式，另外两处就不一致。

### 走一遍题目的例子

4 列 3 行，矩形 1 占 `(1,0)-(2,1)`，矩形 2 占 `(2,1)-(3,2)`。

| 调用 | getAt 内部得到 | 历史栈 | 返回 |
|---|---|---|---|
| removeAt(2,1) | 2（这格最上面） | add[1], add[2], remove[2] | 2 |
| getAt(2,1) | 1（2 走了露出 1） | 不变 | 1 |
| undo | — | add[1], add[2] | true |
| getAt(2,1) | 2（编号大的自动回到上面） | 不变 | 2 |
| removeAt(0,2) | -1（这格没人盖） | **不变** | -1 |

最后一行是最容易丢分的地方：那次空点击不能占一条历史。占了的话，紧接着的一次 `undo` 会白跑一趟（什么都没撤销却返回 true），后面所有撤销全部错位一格。

### 复杂度

`removeAt` 就是一次 `getAt`，O(n)，n 是累计添加过的矩形数。后面两步都是 O(1)。

## 常见疑问

### 为什么只撕最上面一张，而不是这格上的全部

题目原话：The selected cell identifies the topmost active rectangle covering it。这是"鼠标点一下选中一个图层"的语义——一次点击选中一个对象。全部撕掉是第四问 `batchRemove` 的事。

三张铺满整板的矩形，连点三次：

| 调用 | 返回 | 之后 getAt(1,1) |
|---|---|---|
| removeAt(1,1) | 3 | 2 |
| removeAt(1,1) | 2 | 1 |
| removeAt(1,1) | 1 | -1 |
| removeAt(1,1) | -1 | -1 |

每次只拿走一层，第四次没东西可拿，返回 -1 并且不记历史。

### 撤销一次 removeAt，矩形回到最上面还是回到原来那层

回到原来那层。把三张铺满的矩形先 `removeRectangle(3)`，再 `removeAt(1,1)` 拿走 2，然后 `undo`：2 回来以后 `getAt(1,1)` 是 2 而不是 3，因为 3 还在"已撕掉"的状态；再 `undo` 一次把 3 放回来，`getAt(1,1)` 才变成 3。全程没有任何代码在管层次，都是编号大小自动排出来的。

### removeAt 返回 -1 和 removeRectangle 返回 false 有什么关系

两个都是"什么都没做"的信号，只是类型不同：`removeAt` 返回 int，所以用 -1；`removeRectangle` 返回 boolean，所以用 false。共同点是两者都不改板子、不写历史。
