# 题面

## 题目

- 写一个任务队列：别人往里放任务，worker 来领任务去做，做完回来汇报成功或失败。
- enqueue(job_id, timeout, max_retry)：放一个任务。timeout 是领走后多少秒内必须汇报，max_retry 是失败后最多再试几次。
- reserve(job_id)：领一个任务，领走后别人不能再领同一个。
- pass_(job_id)：汇报做成了。fail(job_id)：汇报做砸了。
- get_dlq()：返回彻底放弃的任务名单。DLQ 是 dead-letter queue。
- 第一问：只做 enqueue / reserve / pass_ / fail。失败的任务回队列，没有超时和次数限制。
- 第二问：领走后超过 timeout 没汇报，任务要重新发给别人；失败按 max_retry 重试；次数用完进 DLQ。同一个任务可能被做两遍，题目允许，这叫 at-least-once。
- 第三问：enqueue 多一个 depends_on 列表，列出要等哪些任务先做完。前置没做完的任务，worker 领不到。

## 要问清楚的地方

- max_retry=1 是总共试 1 次，还是失败后再试 1 次。
- 超时算不算一次失败。时间从真实时钟来，还是测试能控制。
- get_dlq 返回 job_id 还是整条记录，按什么顺序。
- 前置任务进了 DLQ，等它的任务怎么办。
