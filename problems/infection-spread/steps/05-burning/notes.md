# 第五问：每天选烧一行、一列或不烧，求最小死亡

## 这一问要做什么

- 写 minimum_deaths(grid, D, K)：规则同第四问死亡版，但每天你可以选一整行或一整列烧掉，也可以不烧；烧到的格子都算死。
- 每天先烧，再处理到期，再传染；没有感染格了就结束。
- 返回所有烧法里最少的总死亡数，烧死加病死，每格只算一次。

## 核心思路

- 题面入口 minimum_deaths(grid, D, K) 调 min_deaths_daily_fast。规则：每天先烧（也可以不烧），再处理到期，再同步传播；烧死和病死都算死亡，每格最多计 1 次；没有感染格时结束。
- 做法是对每天的动作穷举：当前局面 state，试全部 R+C 条线加"不烧"，每个动作算"今天新增死亡 + 下一局面的最小未来死亡"，取最小；solve 用 @cache 按 state 缓存，同一局面只算一次。
- state 是五个常量组成的 tuple：HEALTHY_CELL；SPREAD_SAFE（感染、还没传播、烧死要计 1）；SPREAD_DOOMED（感染、还没传播、死亡已记过）；SAFE_CELL（免疫或传播完的不死感染，烧死计 1）；DEATH_COUNTED（已死或已记账的必死）。
- 为什么不存剩余天数：D≥2 时每个感染格只在感染的次日传播一次，之后活多久不影响别人；必死标记一定下就先记 1（initial_deaths 或 new_doomed），烧到它时不再加，所以哪天病死也不用记。
- spread_once：SPREAD_SAFE 变 SAFE_CELL、SPREAD_DOOMED 变 DEATH_COUNTED；HEALTHY_CELL 有至少 1 个 SPREAD_SAFE 或 SPREAD_DOOMED 邻居就感染，至少 K 个就变 SPREAD_DOOMED 并 additional_deaths 加 1。burn_line：线上 HEALTHY_CELL、SPREAD_SAFE、SAFE_CELL 各计 1，全线改 DEATH_COUNTED。
- solve 的剪枝：best 先取 deaths_if_no_more_burns（从此不烧，用第四问的 BFS 算剩余病死）作可行上界；候选按费用排序，烧死数已经不小于 best 的跳过；没有 SPREAD_SAFE 和 SPREAD_DOOMED 时返回 0。
- D=1 不进搜索：没有传播，答案就是 initial_deaths，必须烧时再加最便宜一条线的烧死数。
- 复杂度：最多 5^(RC) 个 state，每个试 R+C+1 个动作，指数级穷举。练习规模限制在总格数 9 以内。

## 思考与反问

- 每天必须烧还是可不烧？原题原文是 "Each day, choose any row or column and burn everything on it. Minimize total deaths."，即每天必须烧；"choose a row, a column, or no burn" 是少数版本。本题库主线按可不烧做（allow_no_burn=True），两版答案不同：[[1, 0]]、D=2、K=2，可不烧 0，必须烧 1。
- 烧死算不算"死亡"？按算，count_burned=True，burn_line 对线上每个没死的格子（含免疫格）计 1。只算病死的话免费烧整行就能把答案压低，[[1, 0, 1, 0, 1]]、D=2、K=2 从 1 变 0，那要用 best_daily_burn(count_burned=False)。
- 已经全死的行列能不能再烧？按能、不花钱。所以"必须烧"版本只有第一天真被强制（first_burn_required），之后反复烧那条死线等于不烧，min_deaths_daily_fast 只多一个首次标记。禁止重复烧的话每天都在消耗没死的格子，要用保留 burns_left 的 best_daily_burn。
- 烧在第 0 天标记确定之前还是之后？按之后：第 1 天烧的时候 initial 已把 will_die 定好。[[1, 1]]、D=1、K=1：先烧再定标记答案 1（best_initial_burn），先定标记第 1 天再烧答案 2（best_timed_burn）。
- 为什么只烧一次不够：[[0, 1, 0, 0, 1]]、D=2、K=1 最多烧一次（含不烧）最少死 3（best_timed_burn），第 1 天烧第 1 列、第 2 天烧第 3 列只死 2（minimum_deaths）。
- 追问"一格只感染一次为什么还要搜索"：动作序列定了传播才定，不同动作序列让不同格子感染，必须比较全部序列。追问"只算前 N 天的死亡呢"：必死的 1 不能提前记，要用保留 remaining 和 days_left 的 best_daily_burn(horizon=N)。

## 测试要点

- test_one_burn_reuses_the_no_burn_bfs：[[1, 0, 1, 0, 1]]、D=2、K=2 开始前烧第 2 列答案 1，调用后 grid 不变。
- test_no_burn_is_a_real_candidate：[[1, 0]]、D=2、K=2 可不烧 0，allow_no_burn=False 时 1。
- test_burning_before_initial_flags_differs_from_day_one：[[1, 1]]、D=1、K=1 先烧再定标记 1，先定标记第 1 天烧 2。
- test_repeated_burns_can_beat_every_single_burn：[[0, 1, 0, 0, 1]]、D=2、K=1 最多烧一次 3，每天可烧 2。
- test_required_daily_burn_can_reuse_a_dead_line：allow_no_burn=False 时反复烧死线，min_deaths_daily_fast 和 best_daily_burn 都是 2。
- test_free_burns_have_a_different_objective：count_burned=False 时 [[1, 0, 1, 0, 1]] 答案从 1 变 0。
- test_burn_after_spreading_cannot_undo_new_death_flags：burn_before=False 先传播再烧，中间两格已标必死，答案 2。
- test_death_paid_once_even_if_burned_at_expiration：[[1, 1]]、D=1、K=1 烧死一个、到期死一个，共 2 不是 3。
- test_compressed_state_handles_large_lifetime：D=1000000 答案 2，state 不存剩余天数所以不用等。
- test_cached_and_compressed_search_match_unpruned_search：60 个随机 2×3 网格，best_daily_burn 和 min_deaths_daily_fast 都和无剪枝的 _reference_daily_minimum 一致。

## 更多说明

### [[0, 1, 0, 0, 1]]、D=2、K=1 最优方案每天长什么样

| 天 | 动作 | 日末状态 | 累计死亡 |
|---|---|---|---|
| 0 | 无 | [0, 1, 0, 0, 1] | 0 |
| 1 | 烧第 1 列 | [0, 3, 0, 1, 1] | 1 |
| 2 | 烧第 3 列 | [0, 3, 0, 3, 2] | 2 |

K=1 时每个新感染都必死。第 1 天不烧会新增 3 个必死格，烧整行死 5，烧任一列先死 1 且剩下的来源还能再感染 1 个，所以 2 是下界。

### 五个状态在上面例子里怎么变

| 时刻 | state 变化 | 新增死亡 |
|---|---|---|
| 初始 | (HEALTHY_CELL, SPREAD_SAFE, HEALTHY_CELL, HEALTHY_CELL, SPREAD_SAFE)，两个来源都没有感染邻居，不必死 | initial_deaths=0 |
| 第 1 天 burn_line 第 1 列 | 第 1 格 SPREAD_SAFE 变 DEATH_COUNTED | 1 |
| 第 1 天 spread_once | 第 4 格变 SAFE_CELL；第 3 格有 1 个传播邻居，K=1，变 SPREAD_DOOMED | 1 |
| 第 2 天 burn_line 第 3 列 | 第 3 格 SPREAD_DOOMED 变 DEATH_COUNTED，已记过 | 0 |
| 第 2 天 spread_once | 没有 SPREAD_SAFE 和 SPREAD_DOOMED 了，solve 返回 0 | 0 |

### 其他入口对应哪种规则

| 入口 | 规则 | 返回 |
|---|---|---|
| min_deaths_one_burn(grid, D, K) | 初始化前最多烧一次，复用第四问 time_to_end_with_deaths 算剩余病死 | (最小死亡, (axis, index)) |
| best_initial_burn(grid, model) | 同上，走 model 接口，可换 Countdown | Choice(deaths, action, day) |
| best_timed_burn(grid, model) | 第 0 天标记定好后，任选一天烧一次 | Choice |
| best_daily_burn(grid, model, ...) | 每日决策的完整版，Cell 保留 remaining、will_die，缓存键还带 burns_left、days_left、still_must_burn | 最小死亡 |
| min_deaths_daily_fast(grid, D, K) | 主线五状态压缩版 | 最小死亡 |

### best_daily_burn 的开关

| 参数 | 改变的规则 |
|---|---|
| count_burned=False | 只算病死，烧死免费 |
| burn_before=False | 先到期、传播，再烧 |
| budget=B | 最多烧 B 次 |
| budget=1、require_one_burn=True | 恰好烧一次 |
| horizon=N | 只算前 N 天内的死亡 |
| model=Countdown(...)、horizon=N | 邻居数到 T 开始倒计时、到 K 判死的另一套规则，必须给 horizon |

### 单次烧的例子 [[1, 0, 1, 0, 1]]、D=2、K=2

| 候选 | 烧死 | 后续病死 | 总数 |
|---|---|---|---|
| 不烧 | 0 | 2 | 2 |
| 烧第 2 列 | 1 | 0 | 1 |
| 烧整行 | 5 | 0 | 5 |

不烧时第 1、3 列各挨着两个来源，感染时就必死；烧掉中间来源后剩下的新感染只挨一个来源。
