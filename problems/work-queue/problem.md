# 题面

## 原题要点

> Implement a work queue with enqueue / reserve / complete-or-pass / fail operations, then extend it with reservation timeouts, retries, and a dead-letter queue under at-least-once delivery. The follow-up adds `depends_on` so tasks form a DAG. Clarify timeout and retry-limit semantics before coding.

Phone-screen 版本给的接口，题面没有附真正的代码，只有这五个签名：

```
enqueue(job_id, timeout, max_retry)
reserve(job_id)
pass_(job_id)      # 口头叫 pass；pass 在 Python 里是保留字
fail(job_id)
get_dlq()
```

Follow-up：enqueue 多一个参数 `depends_on: List[job_id]`。

## 这题要你写的东西是什么

一个 work queue（工作队列）：一个程序，别人往里放任务，若干 worker（执行任务的进程）来领任务去做，做完回来汇报结果。举个例子：用户上传了视频 123 要转码，网站把"转码视频 123"放进队列；10 台转码机各自来队列领任务，谁领到谁转；转完回来说"123 做完了"，或者"123 做失败了"。队列要负责的事：一个任务不能同时发给两台机器；失败了要安排重做；领走以后机器失联了要能发现。

## 五个方法分别是什么意思

- enqueue(job_id, timeout, max_retry)：放一个任务进去。timeout 是这个任务被领走之后，worker 最多多少秒内必须汇报结果，超过就当它失联。max_retry 是失败之后最多再试几次。
- reserve(job_id)：worker 领任务。领走之后别的 worker 不能再领同一个。
- pass_(job_id)：worker 汇报"做成了"。注意这里 pass 是"通过、完成"的意思，不是跳过；另一个版本叫 complete，同一件事。
- fail(job_id)：worker 汇报"做砸了"。
- get_dlq()：返回所有"试了规定次数还是没成，彻底放弃"的任务名单。DLQ 是 dead-letter queue（死信队列），就是这份放弃名单。

## 题目分三问，一问比一问多一层要求

1. 基础版：只有 enqueue、reserve、pass、fail。任务被领走、做完、或者失败了回队列。没有超时，没有次数限制。
2. 加超时、重试、DLQ。worker 领走任务后在 timeout 内没汇报，任务要重新发给别人；失败了按 max_retry 再试；次数用完进 DLQ。题面点明这是 at-least-once（至少一次投递）：原 worker 可能只是慢，其实还在做，队列照样会把任务再发一份出去，所以同一任务被做两遍是允许的，队列不负责阻止。
3. follow-up：enqueue 多一个参数 depends_on，列出这个任务要等哪几个任务先做完。很多任务的依赖关系连起来是一个 DAG（有向无环图：A 等 B、B 等 C，不会绕回 A）。队列要保证前置任务没做完的任务，worker 领不到。

## 题面故意没说清楚的地方，面试官就是要看你开口问

- max_retry=1 是总共试 1 次，还是失败后再试 1 次、总共 2 次。
- 超时怎么算时间：真实时钟，还是测试代码能控制的时间。超时算不算一次失败、消耗次数。
- get_dlq 返回 job_id 还是整条任务记录，按什么顺序。
- 第三问：前置任务"做完"是指成功完成吗。如果前置任务进了 DLQ，等它的那些任务怎么办。

## 面试形式

电面 15 分钟做五方法版本，也就是第一、二问合在一起；时间够再问第三问。也有分两段的技术面，题面明说第一段全跑通比赶第二段重要，有候选人第二段没跑起来也算过了。
