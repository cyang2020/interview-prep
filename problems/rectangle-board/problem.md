# 题面

## 原题要点

> Design a rectangular board with width columns and height rows. The board is initially empty. Coordinates are zero-indexed: in (x, y), x is the column and y is the row. Each rectangle is defined by its top-left corner (x1, y1) and bottom-right corner (x2, y2), including every cell on its boundaries.

> Rectangles may overlap. At a cell covered by multiple active rectangles, the one added most recently appears on top. Each addition receives the next positive rectangle ID, starting at 1. An ID is never reused, even after its rectangle is removed.

```
RectangleBoard(int width, int height)
int     addRectangle(int x1, int y1, int x2, int y2)
boolean removeRectangle(int rectangleId)
int     getAt(int x, int y)
boolean undo()                      # 第二问
int     removeAt(int x, int y)      # 第三问
int     batchRemove(int x, int y)   # 第四问
```

约束：`1 ≤ width, height ≤ 50`；`0 ≤ x1 ≤ x2 < width`；`0 ≤ y1 ≤ y2 < height`；查询坐标一定在板内；一块板上最多 2000 次调用。

## 这题要你写的东西是什么

一个画图工具里的色块图层管理。板子是画布，最大 50 列 × 50 行。每次 `addRectangle` 是贴一张矩形色块，坐标给的是左上角和右下角，边界那一行一列也算被盖住。贴纸可以互相压住，后贴的盖在先贴的上面。`getAt(x, y)` 是用吸管点一下某个单元格，问这一点现在看到的是哪张贴纸。

`x` 是列、`y` 是行，`y` 往下增长。用题目给的例子（4 列 3 行），贴纸 1 占 `(1,0)-(2,1)`，贴纸 2 占 `(2,1)-(3,2)`，每格显示的是最上面那张的编号：

```
       x=0  x=1  x=2  x=3
y=0     .    1    1    .
y=1     .    1    2    2
y=2     .    .    2    2
```

`(2,1)` 被两张同时盖住，2 后贴，所以吸管点它得到 2。把 2 移除以后这格露出 1，而 `(3,2)` 只有 2 盖过，就变回空的。

## 每个方法分别是什么意思

- `addRectangle(x1, y1, x2, y2)`：贴一张，返回新发的编号。编号从 1 开始，每贴一张加一，移除过的编号不回收。
- `removeRectangle(rectangleId)`：按编号撕掉**整张**，不是只撕它在某一格上的那一块。在板上就撕掉并返回 true；编号没发过、或者已经撕过了，返回 false 且不改动板子。
- `getAt(x, y)`：返回盖住这格的、还在板上的、最上面那张的编号，没有就返回 -1。
- `undo()`：撤销最近一次改动过板子内容的操作，返回 true；历史空了返回 false。
- `removeAt(x, y)`：把这格最上面那张整张撕掉，返回它的编号；这格没有任何贴纸就返回 -1。
- `batchRemove(x, y)`：把盖住这格的所有贴纸全部整张撕掉，返回撕掉的数量；一张都没有就返回 0。

## 分几问

| 问 | 新增 | 新增的难点 |
|---|---|---|
| 一 | add / remove / getAt | 移除要能让下面的露出来 |
| 二 | undo | 哪些操作进历史；恢复原来的叠放位置 |
| 三 | removeAt | 按单元格选中最上面那张 |
| 四 | batchRemove | 一次撕一批，一次 undo 整批放回 |

第二问的判定细节最多：成功的 add 和成功的 remove 进历史；被完全压住的贴纸被撕掉、画面没变，也算一次改动；失败的 remove 和 `getAt` 不进历史；成功的 `undo` 吃掉它撤销的那条记录，自己不再留记录。编号不回退——撤销了第 2 次 add，下一次 add 拿到 3。

## 题面故意没说清的地方

- 没有"把某张挪到最上面"这类操作吗？（有的话编号就不再等于叠放顺序，设计要变）
- `undo` 之后还能 redo 吗？（题目只要 undo）
- `batchRemove` 返回的数量要不要算那些已经撕掉的？（算活着的那些）
- 同一块板上会不会贴 2000 张全屏矩形？（上限是 2000 次调用，决定了能不能线性扫）

## 面试形式

一道题四问，60 分钟电话轮的典型节奏：第一问 10 分钟内写完，第二问是重头戏，第三、四问各 5 分钟就能加上去。考点不是算法，是第一问的数据结构能不能原封不动吃下后面三问。
