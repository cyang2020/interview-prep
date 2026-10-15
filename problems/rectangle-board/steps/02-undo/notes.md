# 第2问：undo

## 面试官给的骨架

```
boolean undo()
```

其余方法签名不变，行为也不变，只是成功的 add 和成功的 remove 要留下记录。

## 思路

### 开口先定的口径

题目在这一问给的判定规则很细，先逐条确认，每一条都直接对应代码里的一行：

| 规则 | 代码里怎么体现 |
|---|---|
| 成功的 add 算一条 | `addRectangle` 末尾写历史 |
| 成功的 remove 算一条，哪怕它被完全压住、画面没变 | `removeRectangle` 翻标记后写历史，不看可见性 |
| 失败的 remove 不算 | 写历史那行放在 `return False` 之后 |
| `getAt` 不算 | `getAt` 不碰 history |
| 成功的 `undo` 吃掉它撤销的那条，自己不留记录 | `history.pop()`，之后不 append |
| 编号不回退 | 编号仍然来自 `len(self.rects) + 1`，而撤销 add 不从 `rects` 里删元素 |

还要问一句：需要 redo 吗？题目没要求，所以一个栈够了。要是需要，再加一个栈即可。

### 历史里存什么

一条记录只要两样东西：**这次是贴还是撕，涉及哪些编号**。坐标不用存，因为矩形对象从来没删过。叠放位置也不用存，因为编号就是叠放位置。

于是撤销变成一个对称的动作：

- 撤销一次 add → 把这些编号改成不活跃
- 撤销一次 remove → 把这些编号改成活跃

两边都只是给 `active` 赋一个布尔值，代码里就一行 `alive = action == "remove"`。

编号这一项现在写成**列表**，虽然这一问每条记录里只有一个编号。这是为第四问的批量移除留的位置：到那时 `undo` 一行都不用改。不这么写，第四问就得给 undo 加一个分支去区分"单个"和"一批"。

### 走一遍题目的例子

4 列 3 行，`add(1,0,2,1)` → 1，`add(2,1,3,2)` → 2，然后 `removeRectangle(1)`。注意这一步画面完全没变，因为 `(2,1)` 上面还盖着 2，而 1 的其他格子本来就只有它自己——但记录照样要留。

| 调用 | 历史栈（左旧右新） | 活跃的编号 | 返回 |
|---|---|---|---|
| add → 1 | add[1] | 1 | 1 |
| add → 2 | add[1], add[2] | 1,2 | 2 |
| removeRectangle(1) | add[1], add[2], remove[1] | 2 | true |
| undo | add[1], add[2] | 1,2 | true |
| getAt(2,1) | 不变 | 1,2 | 2 |
| undo | add[1] | 1 | true |
| getAt(2,1) | 不变 | 1 | 1 |
| undo | 空 | 无 | true |
| undo | 空 | 无 | false |

第四行是整问的点：`undo` 只把 1 的 `active` 改回 True，没有任何"插回第几层"的动作，而 `getAt(2,1)` 立刻又变回 2——因为 2 的编号更大。

### 一个不用校验的不变量

有人会担心：撤销一条 `add[5]` 的时候，万一编号 5 此刻已经被撕掉了，那不就把一个已经不活跃的改成不活跃？

不会发生。撕掉 5 的那条 `remove[5]` 一定压在 `add[5]` 之上（时间上更晚），栈是后进先出，所以一定先撤销 `remove[5]` 把 5 复活，才轮到 `add[5]`。再加上"第二次撕同一张返回 false 且不记历史"，一张矩形最多只有一条 remove 记录。所以 `undo` 里不需要任何一致性检查。

### 复杂度

`undo` 是 O(k)，k 是这条记录里的编号个数（这一问恒等于 1）。add / remove 各多一次 append，仍是 O(1)。内存多了历史栈 O(操作数)。

## 常见疑问

### 被完全压住的矩形被撕掉，画面没变，为什么也算一次操作

题目原话：Removing an active rectangle counts as a change even when another rectangle completely covers it。判定看的是板子的内容变了没有，不是看画面变了没有。

举个最小例子：矩形 1 和矩形 2 都是 `(0,0)-(2,2)` 铺满整板。`removeRectangle(1)` 之后，每一格的 `getAt` 都还是 2，一个像素都没变，但记录必须留下。不留的话接下来一次 `undo` 会跑去撤销 `add[2]`，结果变成 1 和 2 都不在板上——两张都丢了。

### 撤销了编号 2 的添加，下一次 add 发几号

发 3。题目原话：IDs assigned by later additions continue increasing even if an earlier addition has been undone。

代码里这一点是自动成立的：编号来自 `len(self.rects) + 1`，而撤销 add 只是把 `active` 改成 False，并不把元素从 `rects` 里弹出来。所以长度不变，下一个编号继续往上走。顺带一个推论：这时 `removeRectangle(2)` 返回 false，因为 2 不活跃。

### 为什么不需要把"原来的叠放位置"存下来

因为位置不是一个独立的状态。矩形 2 在矩形 1 之上、矩形 3 之下，这件事完全由 1 < 2 < 3 决定。只要 `rects` 里的对象和它的编号没动过，把 `active` 翻回 True 的那一刻，它就自动回到原来那一层。

如果面试官加一个 `bringToFront(id)`，这条就不成立了——那时要另开一个只增的层次序号，`getAt` 比层次序号而不是比编号。

### 能不能 undo 完再 undo 回来（redo）

题目没要求。要加就再开一个栈：`undo` 时把弹出的记录压进 redo 栈，`redo` 时反着做一遍；任何新的 add / remove / removeAt / batchRemove 把 redo 栈清空。现有结构不用改。
