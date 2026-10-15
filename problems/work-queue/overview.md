# 整体思路

**一句话。** 每个 job 在 map 里只有一条记录，所有判断以它为准；任何操作都是"查记录、核对当前状态和 token、改状态、顺手维护索引"；ready 队列、到期堆、反向表都只是索引，和记录不一致时以记录为准。

**三问是叠加关系。** 第一问搭一个最小的状态机，第二问给 reserved 这个状态加到期时间和次数上限，第三问在 ready 前面再加一个 blocked 状态。五方法的 phone-screen 版本是把第一、二问合在一起 15 分钟做完，follow-up 的 depends_on 是第三问。

**面试官反复说"写代码前先澄清"**，是因为题面故意留了几处没定的地方，每一处都会改状态转移的条件。每一问的页面里都先列要澄清什么，再讲怎么做。

## 全部状态转移

面试时照着这张表念，就是题面说的 "narrate every transition"。

| 当前状态 | 触发 | 条件 | 下一状态 |
|---|---|---|---|
| 无 | enqueue | remaining_deps 为 0 | ready |
| 无 | enqueue | remaining_deps 大于 0 | blocked |
| blocked | 前置 completed | remaining_deps 减到 0 | ready |
| ready | reserve | 队列头或指名 | reserved |
| reserved | pass | token 匹配且未到期 | completed |
| reserved | fail 或到期 | attempts 小于 max_attempts | ready |
| reserved | fail 或到期 | attempts 等于 max_attempts | dead |
| blocked | 前置 dead | 级联 | dead |
| 其他任何组合 | 任何操作 | | 拒绝，状态不变 |

## 数据结构

| 结构 | 存什么 | 回答什么问题 | 第几问出现 |
|---|---|---|---|
| jobs（map） | job_id 到记录 | 任务 X 现在什么状态 | 一 |
| ready（双端队列） | 可领取的 job_id 顺序 | 下一个该发谁 | 一 |
| leases（最小堆） | (deadline, job_id, token) | 最早到期的是哪个 | 二 |
| dlq（列表） | 放弃的 job_id，按先后 | get_dlq 返回什么 | 二 |
| dependents（map） | 前置 job_id 到等它的 job_id 列表 | X 做完了谁在等它 | 三 |

jobs 是唯一不能丢的；其余四个都能从 jobs 重建，所以都叫索引。

## 15 分钟电面节奏

- 前 2 分钟，口头定三个口径，不要等面试官问：max_retry=1 按总共 2 次尝试；时间用注入的时钟函数；reserve 返回 token，pass_ 和 fail 带 token，并说清不带 token 会接受迟到的 pass。
- 中间 8 分钟写代码，顺序是：State 和 Job 两个类，jobs 字典和 ready 队列，四个方法的状态检查，然后 leases 堆和到期处理，最后"消耗一次尝试"和 get_dlq。每写一个方法说一句"这条转移从哪到哪、什么条件下拒绝"。
- 最后 5 分钟写三个测试：两次 fail 进 DLQ 且只进一次；超时后重新领取，旧 token 的 pass 被拒；get_dlq 只有用完次数的。
- 问到第三问时先说四个口径（成功完成才算、前置必须已入队所以无环、前置放弃则级联进 DLQ、去重），再写 blocked 状态、remaining_deps、dependents 反向表、pass_ 里的放行。时间不够就只讲不写，题面说过这样也能过。

## 讲完三问后常见的追问

| 追问 | 答法 |
|---|---|
| 多个 worker 同时调，多线程怎么办 | 每个公开方法整个加一把锁。每条转移都是"查状态再改状态"，中间被别人插进来就会两个 worker 同时领到一个任务 |
| 进程重启，内存里的东西全丢 | jobs 记录写数据库，是唯一不能丢的。ready 队列、leases 堆、dependents 反向表都能从 jobs 记录重建，因为它们只是索引 |
| 没人调方法，超时的任务一直不被处理 | 加一个后台线程定时做到期处理，或者按堆顶的 deadline 睡到那个时刻再醒 |
| 任务要分优先级 | ready 从双端队列换成按优先级排序的堆，fail 回队时带原优先级 |
| 要支持 cancel | blocked 和 ready 的直接改 cancelled；reserved 的改成"等汇报或超时后不再重试"；等它的任务按 dead 一样级联 |
| 允许依赖还没入队的任务 | 先给前置建一条占位记录。这时环就可能出现，enqueue 时要沿 depends_on 走一遍查有没有回到自己 |
| worker 做得比 timeout 久怎么办 | 加一个 extend(job_id, token) 方法，核对 token 后把 deadline 往后推，往堆里压新条目，旧条目弹出时 deadline 不等，也当旧条目丢掉 |
| pass 发出去了但 worker 没收到回复，又发一次 | 第二次查到状态已经 completed，拒绝，没有副作用。这就是重复调用安全 |
| leases 堆会不会越来越大 | 每次 reserve 压一条，到期弹出，上限是未到期的领取数。pass 和 fail 不删堆条目，所以峰值是"所有发出过且 deadline 还没到的领取" |
| 为什么 fail 回队尾不回队头 | 回队头会让一个反复失败的任务一直占着 worker，别的任务饿着。回队尾让其他任务先轮一遍 |
