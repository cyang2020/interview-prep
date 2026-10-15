# 第二问：超时、重试、DLQ，at-least-once

## 这一问要做什么

- 领走的任务超过 timeout 秒没汇报，要能被别人重新领走。
- fail 和超时都算一次失败，失败次数用完的任务进 DLQ，get_dlq 返回这份名单。

## 核心思路

- 接口改两处：reserve 返回 (job_id, token)；pass_ 和 fail 多收一个 token。token 是"这次领取的编号"，每次 reserve 加 1。
- 记录多三个字段：max_attempts = max_retry + 1、token、deadline。状态多一个 dead，表示次数用完进了 DLQ。
- 超时不开线程：每个公开方法开头先调一次到期处理，把 deadline 小于等于现在的领取按失败处理，然后再做本方法的事。
- 到期处理用一个按 deadline 排的最小堆，每次 reserve 压入 (deadline, job_id, token)。弹出时对照记录：不是 reserved 或 token 不等，就是旧条目，丢掉。
- fail 和超时走同一段"消耗一次尝试"：attempts 小于 max_attempts 就回 ready 入队，等于就改 dead、追加 DLQ。只写一份，两处边界才不会写得不一样。
- pass_ 和 fail 要两条都对：状态是 reserved，且传来的 token 等于记录当前的 token。迟到的汇报由此被拒。
- 时钟注入：构造时传一个"返回现在几点"的函数，测试换成能手动拨的假时钟，不用真等。
- 复杂度：map 和双端队列 O(1)，堆每次压入或弹出 O(log n)。

## 思考与反问

- max_retry=1 是"失败后再试 1 次，共 2 次尝试"还是"共 1 次"？我按前者，代码里只在一处判断 attempts 是否等于 max_attempts。
- 超时算不算一次失败？按算。get_dlq 返回什么？job_id 列表，按进入先后。进了 DLQ 是终态，迟到的 pass 不救。
- 为什么必须有 token：worker 1 第 0 秒领 A 后卡住，第 12 秒超时后 worker 2 领走，第 15 秒 worker 1 恢复调 pass_。没有 token 这次 pass 会成功，A 被标完成但没人知道它做到哪，worker 2 的活白干；如果调的是 fail，次数还会多扣一次。
- at-least-once 的含义：第 12 到 15 秒 worker 1 和 worker 2 确实同时在做 A，队列不拦重复执行。队列只保证两件事：当前这次领取的汇报才算数；每个任务进 DLQ 只进一次。
- 堆里的旧条目为什么不删：堆不支持删中间元素，留着等弹出时对照丢掉。和第一问 ready 队列里留过时 job_id 是同一个原则，索引可能过期，以记录为准。

## 测试要点

- test_fail_twice_goes_to_dlq_once：max_retry=1，两次 fail 后进 DLQ，第三次领不到，DLQ 里只出现一次。
- test_timeout_then_late_pass_rejected：第 0 秒领、第 12 秒被别人领走、第 15 秒原 worker 的 pass 被拒，新 worker 的 pass 成功。
- test_timeout_consumes_attempts：两次超时同样进 DLQ。
- test_stale_heap_entry_ignored：fail 后重新领取，旧堆条目到期不会误伤新的领取。
- test_dlq_only_has_exhausted_jobs：正常完成的任务不进 DLQ。

## 更多说明

### DLQ 是什么

DLQ 是 dead-letter queue，死信队列：试了规定次数还没做成、队列决定不再重试的任务名单。视频 123 定了 max_retry=1，共 2 次机会：转码机 1 领走报 fail，回 ready；转码机 2 领走又报 fail，机会用完。这时要么无限重试（坏文件会一直占着机器），要么标成 dead 记进名单。DLQ 就是这份名单。运维定期调 get_dlq() 看名单，查原因，修好后手动重新 enqueue。超时也算一次失败，所以两次 fail、两次超时、一次 fail 一次超时，用完都进 DLQ。

### 堆里为什么会有旧条目

第 0 秒 worker 1 领 A，token=1，堆里有 (10, A, 1)。第 5 秒 worker 1 调 fail，A 回 ready。第 6 秒 worker 2 领 A，token=2，堆里新增 (16, A, 2)。第 10 秒到期处理弹出 (10, A, 1)，记录当前 token 是 2，不等，丢掉。不比对的话 A 会被当成超时，worker 2 正常的领取被作废，A 被发第三次。
