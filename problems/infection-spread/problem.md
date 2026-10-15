# 题面

## 原题要点

以下英文逐句摘自提供的题型汇总，不是 OpenAI 官方发布的完整试卷。汇总同时记录了互不相同的第四、第五问版本，不能把所有句子合并成同一套规则。

> M×N grid with infected cells (X) and susceptible cells (./*); infection propagates each day under escalating rules.

> Each day every infected cell (1) simultaneously infects all 4-neighbor healthy (0) cells (orthogonal only, no diagonals); cells newly infected today only start propagating tomorrow.

> Introduce immune cells (2): never get infected, never propagate, skipped when counting neighbors.

> After being infected for D days, a cell becomes immune (2, self-heals — no longer propagates).

> Watch day semantics / off-by-one: a cell infected on day t becomes immune when current_day - t >= D; immunity takes effect before spread on the same tick.

> Variant A: a healthy cell only becomes infected next day if it has ≥ K infected 4-neighbors (threshold spread).

> In the stricter version, a cell that was infected while surrounded by at least K infected neighbors dies when its recovery timer expires instead of becoming immune. Return days-to-end + final death count.

> Each day, choose any row or column and burn everything on it. Minimize total deaths.

> Minority variant: choose a row, a column, or no burn to minimize total deaths; clarify whether this is a single choice or a repeated daily decision before coding.

前三问资料给出以下签名，没有完整实现：

```python
def time_to_full_infection(grid: list[list[int]]) -> int:
    pass

def time_to_full_infection_with_immunity(grid: list[list[int]]) -> int:
    pass

def time_to_stable_state(grid: list[list[int]], D: int) -> int:
    pass
```

第四、第五问没有统一的函数名。按需要返回的结果，练习使用以下签名：

```python
def time_to_full_infection_threshold(grid: list[list[int]], K: int) -> int:
    pass

def time_to_end_with_deaths(grid: list[list[int]], D: int, K: int) -> tuple[int, int]:
    pass

def minimum_deaths(grid: list[list[int]], D: int, K: int) -> int:
    pass
```

## 这题要你写的东西是什么

测试程序给你一块 3 行 3 列花圃的状态。每个位置是一株植物，中心已经感染，其他位置健康。程序问第一次调用的函数：过几天整个花圃都会感染。按四邻居规则，第 1 天上下左右四株感染，第 2 天四个角感染，函数返回 2。

后续调用会增加免疫位置、恢复期限、死亡条件。函数只计算结果，不需要等待真实的一天，也不需要连接外部服务。最后一问由求解器选择每天烧哪条行列，测试程序检查最终死亡人数是不是所有合法选择中的最小值。

## 每个输入和返回值分别是什么意思

- grid：矩形整数网格，grid[row][col] 是第 row 行第 col 列。0 健康，1 感染，2 永久免疫，3 死亡。坐标从 0 开始。
- D：感染到结束感染的天数。初始感染日为 0，第 t 天感染的细胞在第 t+D 天开始时到期。每天先处理到期，再传播。
- K：阈值版中是感染需要的邻居数；死亡版中是刚感染时判为必死的邻居数。死亡版感染本身仍只需要一个感染邻居。
- time_to_full_infection 和 time_to_full_infection_with_immunity：返回所有健康格都感染所需天数，有健康格永远不可达时返回 -1；没有健康格时返回 0。
- time_to_stable_state：返回没有感染格所需天数，允许还有健康格；没有初始感染时返回 0。
- time_to_full_infection_threshold：返回全部健康格达到感染条件的天数，稳定后仍有健康格时返回 -1。
- time_to_end_with_deaths：返回结束日和新增病死人数。没有初始感染时返回 (0, 0)。初始输入只含 0、1、2，内部复用时已有的 3 不重复计入新增病死。
- minimum_deaths：每天先选择烧一行、一列或不烧，再处理到期，再同步传播。返回焚烧与病死人数之和的最小值，每格最多计一次。

所有位置在同一天同时更新，新感染只能下一天开始传播。本实现保留传入的 grid，重复调用不会因为前一次计算而改变结果。

## 题目分五问

1. 基础传播：只含 0 和 1，感染永久有效。多个来源允许同时存在。空网格返回 0。
2. 加入免疫：2 永远不会感染，也不能把感染传到另一侧。有任意健康格最终无法感染就返回 -1。
3. 加入恢复：感染 D 天后永久免疫，改问什么时候没有感染。D=1 时初始感染在第一次传播前恢复。
4. 两个独立分支：阈值版要求至少 K 个感染邻居，感染永久有效；死亡版感染阈值仍为 1，在刚感染时固定死亡标记，第 D 天死亡或恢复。本题库两种都写，不把它们混成一个规则。
5. 选择焚烧：主线是每天可烧一行、一列或不烧，求最终最小死亡。也给出开始前一次、任选一天一次、每日必须烧、有限次数、只计病死和有限期限的明确版本。

第五问主线先在第 0 天根据初始网格确定死亡标记，第 1 天烧邻居不会撤销这些标记。开始前一次的变种先烧再初始化，二者可能有不同答案。每天都可以重复选择已经烧空的行列。没有感染时日程结束，不再强制做动作。

练习规模取第一、二问行列各不超过 200，第三问各不超过 50，第四问各不超过 30；第五问主线总格子数不超过 9。D 为正整数，四邻居版本的 K 在 1 到 4 之间。这是为了让不同阶段有可执行的练习范围，不是所有面经都给过同样限制。

## 题面故意没说清楚的地方

- 相邻是四邻居还是八邻居。是否包含对角线会改变每个例子的天数。
- 停止条件是全部健康格感染，还是系统没有变化，还是没有感染格。全健康输入在第一问返回 -1，在第三问返回 0。
- 免疫编码是 2、-1 还是 I。练习统一为 2，避免同一个数字在不同函数中换含义。
- 到期发生在当天传播之前还是之后。这里先到期，D=1 不会向外传播。
- 死亡标记在感染时确定，还是感染期间触发新的倒计时，还是到期时重新检查。这三种行为不能共用未修改的判定逻辑。
- 烧发生在初始化前还是第 1 天；总共能烧一次还是每天一次；是否可以不烧；是否允许重复烧空线。
- 烧死算不算目标中的死亡；是否只数 N 天以内的死亡。免费焚烧和有限期限都会改变题目要优化的数值。

这些问题用于面试中确认题面。本站代码和测试已经写死了上述明确口径，学习时不需要再自行补条件。

## 面试形式

公司是 OpenAI，资料标记为 phone-screen · tech-screen，五部分约 60 分钟。第四问有不同分支，不代表一次面试会同时要求所有版本。频率 Very high、最近记录 2026-09-26 沿用提供的资料，是题型记录日期。

练习时先把前三问的同步传播、边界和时间顺序做清楚，再处理第四问的计数。第五问先把允许的动作和死亡计费说完整，再动代码。资料建议把前三问练到 30 到 40 分钟内完成；最终评价并不只由做到第几问决定。
