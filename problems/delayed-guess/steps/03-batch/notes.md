# 第三问：多局并行，批次最少

## 这一问要做什么

- 写 find_numbers(upper_bounds, server)：多局同时猜，每局各有一个上界和一个答案，按局的顺序返回全部答案。
- 服务器换成 server.check_batch(guesses)：每一批要给每个没定的局交一个新数，定了的局填 -1；返回每局上一批那个数的结果，上一批是 -1 就返回 PENDING。
- 要求调 check_batch 的批次最少。最多 1000 局，每局上界最大 1e9。

## 核心思路

- 接口换成 find_numbers(upper_bounds, server)：server.check_batch(guesses) 一次收一个列表、每局一个数，返回每局上一批那个数的结果。已定的局交 -1，之后不能再交数。目标是 check_batch 的调用次数最少。
- 第二问的 find_number 自己在循环里调 server，多局没法一起交，所以把它翻成 _Game 状态机：propose() 算这一批交什么，absorb(resp) 收上一批那个数的结果。放数规则和 find_number 一字不差。
- 字段：lo、hi、k、pending 同第二问；新增 sent 是本批刚交的数，answer 不是 None 就表示这局定了。upper_bound = 1 的局构造时 answer 直接是 1。
- propose：answer 已定返回 -1；否则按 pending 是否为 None 走第二问的两条放数规则，结果记到 sent。
- absorb：answer 已定直接跳过，收到什么都不看；否则按 resp 更新 pending 对应的 answer、hi 或 lo，再把 sent 转正成 pending、k 减 1；lo == hi 就 answer = lo，pending 出了区间就置 None。
- find_numbers：按 max(upper_bounds) 建一张 A 表所有局共用；循环到所有 answer 都不是 None，每轮先每局 propose、一次 check_batch、再每局 absorb。全定了就退出，最后一批的结果不去取。
- 复杂度：批次 = 各局 _min_calls 的最大值，1000 局最大 1e9 是 43 批；每批 O(局数)，空间每局几个整数加一张 44 项的表。

## 思考与反问

- -1 的口径：某局交了 -1，这一格从下一批起返回 PENDING，再交数算违规。按此做：propose 对 answer 已定的局永远返回 -1，absorb 对它直接 return。
- "这局完成"按我自己推断出来算，不等服务器回 CORRECT：题面例 1 的局 1 收到 2 的 TOO_HIGH 就填 -1。代码里 absorb 看到 lo == hi 就定 answer，upper_bound = 1 构造时就定，全部局都是 1 时 check_batch 一次都不调。
- 为什么不逐局调 find_number：它一局跑完才轮到下一局，批次是各局 k 之和，1000 局 1e9 要 43000 批；拆成 propose、absorb 让所有局同一批交，43 批。
- 为什么要 sent 和 pending 两个字段：absorb 要先用 resp 更新上一批那个数 pending 对应的 lo、hi，然后才知道本批那个数 sent 还在不在新区间里。upper_bound = 50 的局第 2 批交 26、收到的是 42 的 TOO_HIGH，若 propose 时就把 26 写进 pending，hi 会错收成 25 而不是 41。
- 批次能不能比最慢那局更少？不能，局之间不共享任何信息，最慢那局单独也要 k 次，第二问的博弈树已经证明 k 是下界。
- 追问：题面说非 -1 的值都算一次猜测，猜测总数是不是也最少？是。一局的猜测数等于它未完成的批次数，就是它自己的 k，第二问已压到最少；CORRECT 回来那批刚交的 sent 是白扔的一个，和单局最后一次调用一样，下一批起 propose 返回 -1。

## 测试要点

- test_batch_examples_from_problem：[4, 3]、[10, 50, 8]、[20, 20, 20, 20] 三个例子答案全对，批次恰好等于最慢那局的 _min_calls。
- test_batch_count_never_exceeds_slowest_game：几十种局数和上界组合，含 [1, 1e9]、1 到 40 连号、全部 secret 取上界，答案全对、裁判没报违规、批次不超最慢那局。
- test_batch_all_upper_bound_one_makes_no_call：[1, 1, 1] 一批都不调，返回 [1, 1, 1]。
- test_batch_declared_game_keeps_sending_minus_one：局 1 用 -1 宣告过，之后再没交过数，它交过的数比批次数少。
- test_batch_max_scale：1000 局、最大上界 1e9，正好 43 批。
- test_single_every_secret_small_range_hits_bound：第二问的单局测试改名保留，1 到 300 每个 secret 最坏次数仍正好等于 _min_calls。
- test_single_large_upper_bounds：第二问的单局测试改名保留，1e9 和 2^30 不超预算，确认 find_number 没被改坏。

## 更多说明

### [4, 3]，secret [3, 1] 走一遍（3 批）

A = [1, 1, 3, 5]。局 0 上界 4，k = 3；局 1 上界 3，k = 2。

| 批 | propose 交的 | check_batch 返回，说的是上一批 | absorb 后 |
|---|---|---|---|
| 1 | [4, 2] | [PENDING, PENDING] | 局 0 pending = 4，k = 2；局 1 pending = 2，k = 1 |
| 2 | [2, 1] | [TOO_HIGH, TOO_HIGH] | 局 0 hi = 3，pending = 2，k = 1；局 1 hi = 1，lo == hi，answer = 1 |
| 3 | [1, -1] | [TOO_LOW, CORRECT] | 局 0 lo = 3，lo == hi，answer = 3；局 1 已定，跳过 |

第 3 批局 1 交的是 -1，服务器照样返回它上一批那个数 1 的结果 CORRECT，absorb 不看。两局都定了循环退出，第 3 批局 0 交的 1 的结果不去取。批次 3 = max(3, 2)。题面例 1 给的序列是 [2, 2]、[3, 1]、[4, -1]，交的数不同，也是 3 批。

### 已定的局之后每批会收到什么

[10, 50, 8]，secret [6, 17, 4] 的例子里，局 0 第 3 批收到 CORRECT 定了，第 4 批交 -1 却收到 TOO_LOW：那是它第 3 批交的数 4 的结果，白扔的那一个。第 5 批起服务器对 -1 的格子返回 PENDING。absorb 开头判 answer 已定就 return，所以这三种返回值都不用区分。
