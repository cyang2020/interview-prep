# 第一问：单局，先跑对、不违规

## 这一问要做什么

- 写 find_number(upper_bound, server)：答案是 1 到 upper_bound 之间的一个整数，反复调 server.check(guess) 把它找出来并返回。
- check 的返回说的是上一次交的数：第一次返回 PENDING，之后返回上一次那个数是 TOO_LOW、TOO_HIGH 还是 CORRECT。
- 这一问只要求一定答对、每次交的数在 1 到 upper_bound 之间、不和之前交过的重复；调几次不管。

## 核心思路

- 接口 find_number(upper_bound, server)：server.check(guess) 返回的是上一次交的那个数的结果，第一次返回 PENDING。每次调用都必须交一个新数，没有空调用。
- 三个变量：lo、hi 是还可能是答案的区间，pending 是已经交出去、结果还没回来的那个数。
- 每轮先看 lo == hi，是就直接返回 lo，不多调一次确认；否则 guess 取中点 (lo + hi) // 2，撞上 pending 就挪 1（先试 +1，到 hi 了就 -1）。
- 调 check(guess) 拿到的是 pending 的结果：CORRECT 返回 pending；TOO_LOW 把 lo 抬到 pending + 1；TOO_HIGH 把 hi 压到 pending - 1。最后 pending = guess。
- lo 用 max、hi 用 min：pending 取自上一轮缩小前的区间，可能已经在区间外，它的结果不能让区间往回扩。
- 不重复只靠躲 pending：每个有结果的数都被 lo 或 hi 挤出了区间，区间里唯一猜过的数就是 pending。
- 复杂度：O(1) 空间；最坏约 2 × log2(n) 次调用，upper_bound 1e9 要 58 次。

## 思考与反问

- 返回值说的是哪个数？按"上一次交的数"做，第一次调用只换回 PENDING。所以代码里 resp 配 pending，不配刚交的 guess。
- 能不能重复猜、能不能越界？都按不行做，tests 里的 GuessServer 当裁判，违反直接 assert。guess 永远取在 [lo, hi] 里就不越界；撞 pending 挪 1 就不重复，不挪的话第 2 次调用区间还没变，中点和第 1 次交的是同一个数。
- 要不要收到 CORRECT 才算答出来？按不要求做，lo == hi 直接返回。要求的话 upper_bound = 2 做不到：1 和 2 都交过，没有第三个合法的数去换回最后那个结果。
- 为什么不等上一个结果回来再猜？接口不允许空调用，每次都要交新数，所以总有一个数在路上，这就是 pending 存在的原因。
- 追问"最坏多少次"：10 要 5 次，1000 要 18，1e6 要 38，1e9 要 58，没有延迟的普通二分是 30。guess 是缩小前区间的中点，结果回来区间砍一半，guess 有一半概率落在砍掉的那半里白扔，平均两次调用才缩一半。
- 追问"能不能更少"：能，把新数放的位置改成按剩余预算切、不白扔，1e9 从 58 降到 43，这是第二问。

## 测试要点

- test_examples_from_problem：题面三个例子 (10, 6)、(50, 17)、(31, 25) 都答对。
- test_every_secret_small_range：upper_bound 1 到 300 每个 secret 都答对，裁判没报越界或重复；最坏次数和对抗搜索 simple_worst_case 算出的值一致。
- test_upper_bound_one_needs_no_call：upper_bound = 1 时一次 check 都不调，直接返回 1。
- test_large_upper_bound：upper_bound 1e9，边界值 1、2、n-1、n 和 200 个随机 secret 都答对，次数不超对抗搜索的最坏值。
- test_worst_case_table：对抗搜索给出 10 → 5、1000 → 18、1e6 → 38、1e9 → 58，是上面那组数字的来源。

## 更多说明

### upper_bound = 10，secret = 3 走一遍（最坏 5 次）

| 调用 | lo, hi | pending | guess | check 返回，说的是 pending | 更新 |
|---|---|---|---|---|---|
| 1 | 1, 10 | 无 | 5 | PENDING | pending = 5 |
| 2 | 1, 10 | 5 | 6，中点 5 撞 pending 挪 1 | TOO_HIGH | hi = 4，pending = 6，已在区间外 |
| 3 | 1, 4 | 6 | 2 | TOO_HIGH | hi = min(4, 5) = 4 没变，白扔 |
| 4 | 1, 4 | 2 | 3，中点 2 撞 pending 挪 1 | TOO_LOW | lo = 3，pending = 3 |
| 5 | 3, 4 | 3 | 4，中点 3 撞 pending 挪 1 | CORRECT | 返回 pending = 3 |

第 3 次就是白扔的那种调用：6 已经不在 [1, 4] 里，它的结果不带新信息。secret = 6 时只要 3 次：check(5) 换回 PENDING，check(6) 换回 5 的 TOO_LOW，check(8) 换回 6 的 CORRECT。
