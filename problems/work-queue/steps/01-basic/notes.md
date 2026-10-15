# 第一问：enqueue / reserve / pass / fail 基础版

## 这一问要做什么

- 写 WorkQueue 的 enqueue、reserve、pass_、fail：放任务、领任务、汇报做成、汇报做砸。做砸的任务回队列等人再领。
- 没有超时、没有次数限制。timeout 和 max_retry 两个参数先收下不用。

## 核心思路

- 每个 job 一条记录：job_id、state、attempts、timeout、max_retry（后两个第一问先收下不用）。状态三个：ready、reserved、completed。
- 四个方法就是四条状态转移，每条先核对当前状态，不对就拒绝，返回 False 或 None。
- enqueue：新建记录置 ready，job_id 进 ready 队列尾。reserve：ready 改 reserved，attempts 加 1。pass_：reserved 改 completed。fail：reserved 改回 ready，重新入队。
- 两个数据结构：jobs 这个 map 回答"某个任务现在什么状态"；ready 这个双端队列回答"不指名时下一个发谁"。
- 队列只是索引，map 才算数：指名领走的任务 job_id 还留在队列里，不指名弹出时要对照 map 确认它仍是 ready，不是就丢掉继续弹。
- 全部操作 O(1)。

## 思考与反问

- reserve(job_id) 是指名领，还是 reserve() 按顺序发下一个？两种都支持，job_id 传 None 走后者。只有指名版的话 ready 队列整个可以不要。
- pass_ 的含义按"做成了"。Python 里 pass 是保留字，方法名带下划线。
- 为什么每条转移都先核对状态：不核对，没被领走的 job 收到误发的 pass 会直接 completed，没有 worker 跑过它；已完成的 job 收到迟到的 fail 会回队列重跑一遍。
- 为什么不只用 map：不指名发任务要按先来后到，map 没顺序，扫一遍是 O(n)。为什么不只用队列：reserved、completed 的记录队列里放不下，pass_ 和 fail 要能查到它们。

## 测试要点

- test_state_machine：四条转移各走一次；对 ready 的 job 调 pass_、对 completed 的 job 调 reserve 或 fail 都被拒。
- test_reserve_next：A、B、C 入队，指名领走 B 后，不指名两次拿到 A、C，跳过队列里过时的 B。

## 更多说明

### reserve 和 pass 是干嘛的

三方：往队列放任务的（网站）、队列本身（WorkQueue）、干活的 worker（转码机）。队列不干活，只记账。用视频 123 走一遍：

1. 网站调 enqueue("123")：队列记一条，123 ready，意思是没人做、可以领。
2. 转码机 1 调 reserve("123")：123 是 ready，改 reserved，回答"归你了"。接下来 5 分钟转码，队列不参与。
3. 这 5 分钟里转码机 2 调 reserve("123")：123 已经是 reserved，拒绝。一个任务同一时间只能有一台机器在做。
4. 转码机 1 转完调 pass_("123")：改 completed，以后谁来 reserve 都领不到。
5. 另一种结局：转码机 1 调 fail("123")：改回 ready，转码机 2 再来 reserve 就能领到。

领任务和报结果分两步，是因为干活要花时间还可能失败，中间那 5 分钟队列必须知道"123 正在被谁做"。

### 两个结构在每一步长什么样

| 操作 | jobs 里的状态 | ready 队列 |
|---|---|---|
| enqueue A、B、C | A ready，B ready，C ready | [A, B, C] |
| reserve("B") 指名 | B 变 reserved | [A, B, C]，B 还留在里面 |
| reserve() 不指名 | 弹出 A，是 ready，发出去，A 变 reserved | [B, C] |
| reserve() 不指名 | 弹出 B，查 map 是 reserved，丢掉；再弹出 C，发出去 | [] |
| pass_("B") | B 变 completed | [] |
| fail("A") | A 变 ready，放回队列 | [A] |

第四行就是"队列只是索引，map 才算数"：队列里的 B 已经过时，弹出来要对照 map 才知道该不该发。
