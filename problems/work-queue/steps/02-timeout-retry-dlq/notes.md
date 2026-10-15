# 第二问：超时、重试、DLQ，at-least-once

## 接口上动了两处

第二问不换骨架，还是那五个方法。变的是语义：enqueue 里的 timeout 和 max_retry 开始起作用，get_dlq 要返回真东西。我在接口上动了两处，开口就要跟面试官说：

- reserve 返回 (job_id, token)，多了一个 token，就是"这次领取的编号"。
- pass_ 和 fail 多收一个 token 参数。

不这么改，题面要求的"超时后被重新领走，原 worker 迟到的 pass 要被拒绝"这个测试写不出来，下面讲为什么。

## 思路

**开口先定三个口径，每个都决定代码怎么写。**

1. max_retry=1 我按"失败后再试 1 次，总共 2 次尝试"做。代码里存 max_attempts = max_retry + 1，判断只在一处："这次失败时 attempts 已经等于 max_attempts，进 DLQ"。
2. 时间从哪来：构造 WorkQueue 时传进一个"返回现在几点"的函数，默认用系统时钟，测试里换成能手动往前拨的假时钟。不这么做，测 10 秒超时就得真等 10 秒。
3. 超时算一次失败，和 fail 一样消耗次数。get_dlq 返回 job_id 列表，按进 DLQ 的先后排。进了 DLQ 就是终态，迟到的 pass 不救。

**记录多三个字段，状态多一个。** 字段：max_attempts、token（当前这次领取的编号，每次 reserve 加 1，从 1 开始）、deadline（当前这次领取的到期时刻）。状态加 dead，意思是次数用完进了 DLQ。

**超时谁来发现。** 不开后台线程。每个公开方法开头先调一次"到期处理"：看堆顶，到期时刻小于等于现在的全弹出来处理掉，然后再做本方法的事。这样第 12 秒 worker 2 来 reserve 时，第 10 秒就该到期的任务会在这一刻被处理，worker 2 正好能领到。

**到期处理需要一个新索引：按 deadline 排序的最小堆。** 每次 reserve 往堆里压一条 (deadline, job_id, token)。为什么要堆：到期处理要回答"最早到期的是哪个"，堆顶 O(1) 拿到，不用把所有 reserved 的任务扫一遍。

**四个方法怎么变。**

- reserve：原来的检查不变，另外 token 加 1，deadline 置为现在加 timeout，往堆里压一条。返回 (job_id, token)。
- pass_(job_id, token)：记录必须处于 reserved，并且传来的 token 等于记录当前的 token。两条都对才改 completed。
- fail(job_id, token)：同样两条检查。通过后走"消耗一次尝试"：attempts 小于 max_attempts 就回 ready 入队，等于就改 dead、追加到 DLQ 列表。
- 到期处理弹出一条 (deadline, job_id, token)：对照记录，记录不是 reserved、或者 token 和记录当前的不一样，这条是旧的，丢掉；都对上，这个任务真超时了，走和 fail 同一段"消耗一次尝试"。这段只写一份，fail 和到期都调它，不然两处的"小于还是小于等于"容易写得不一致。

**为什么必须有 token，走一遍。** timeout 10 秒，总共 2 次尝试。

- 第 0 秒：worker 1 reserve("A")，拿到 token=1，deadline 第 10 秒。worker 1 的进程卡住了。
- 第 12 秒：worker 2 reserve("A")。开头的到期处理发现 A 的领取过期，attempts=1 小于 2，A 回 ready。接着 worker 2 领到 A，attempts=2，token=2，deadline 第 22 秒。
- 第 15 秒：worker 1 恢复了，调 pass_("A", 1)。记录当前 token 是 2，不等，拒绝。
- 之后 worker 2 调 pass_("A", 2)，token 对，A 变 completed。

没有 token 会怎样：第 15 秒 worker 1 的 pass 只能查"A 是不是 reserved"，是，就成功了。但 worker 1 卡住那段时间实际做到哪一步没人知道，A 却被标成完成；worker 2 后面的 pass 被拒，它的活白干。如果 worker 1 调的是 fail，A 还会多消耗一次尝试，次数就乱了。

**这就是题面说的 at-least-once（至少一次投递）。** 第 12 秒到第 15 秒之间 worker 1 和 worker 2 确实在同时做 A，队列拦不住，重复执行是这个模型接受的。队列保证的是两件事：只有当前这次领取的 pass 或 fail 算数；一个任务进 DLQ 只进一次，因为只有 reserved 变 dead 这一条转移往 DLQ 列表追加，dead 之后任何操作都被状态检查拒绝。

**堆里为什么会有旧条目，再走一遍。** 第 0 秒 worker 1 领 A，token=1，堆里有 (10, A, 1)。第 5 秒 worker 1 调 fail，A 回 ready。第 6 秒 worker 2 领 A，token=2，堆里新增 (16, A, 2)。第 10 秒到期处理弹出 (10, A, 1)，对照记录 token 是 2，不等，丢掉。不比对的话，A 会被当成超时，worker 2 手里正常的领取被作废，A 被发第三次。为什么不在 fail 的时候把 (10, A, 1) 从堆里删掉：堆不支持删中间元素，留着等它弹出来再丢，和第一问 ready 队列里留着旧 job_id 是同一个原则，索引可能过期，以记录为准。

**复杂度。** map 和双端队列 O(1)，堆每次压入或弹出 O(log n)。

## 常见疑问

### DLQ 是什么

DLQ 是 dead-letter queue，中文叫死信队列。它就是一份名单：试了规定次数还是没做成、队列决定不再重试的任务，都放进这份名单。

**用视频 123 走一遍。** enqueue 的时候定了 max_retry=1，也就是总共给 2 次机会。

- 第 1 次：转码机 1 领走，转到一半报 fail。队列把 123 放回 ready，等人再领。
- 第 2 次：转码机 2 领走，又报 fail。这时 2 次机会用完了。

用完之后队列有两个选择。一是继续放回 ready 无限重试，但这个视频可能本身就是坏文件，谁来转都失败，会一直占着转码机。二是不再重试，把 123 标成 dead，记进一份"放弃名单"。DLQ 就是这第二个选择里的那份名单。

**名单有什么用。** 任务没做成不能当没发生过，得让人知道。运维或者程序定期调 get_dlq() 看这份名单，看到 123 在里面，就去查：是文件坏了，还是转码机的 bug，修好之后手动重新 enqueue。所以 DLQ 的作用是把"自动处理不了的任务"从正常流程里拿出来，单独交给人处理，既不让它堵着别的任务，也不让它悄悄消失。

**超时也算失败。** worker 领走后到了 timeout 还没汇报，队列当它失联，和报 fail 一样消耗一次机会。所以 2 次机会可以是两次 fail、两次超时、或者一次 fail 一次超时，用完都进 DLQ。

**为什么叫这个名字。** dead letter 原本是邮政用词，指地址错误、退回也退不了、没人能收的信件，邮局会把它们集中放在一处。借过来指"没法正常送达的任务"。面试时直接说 DLQ 或 dead-letter queue 就行，这是业内通用词。
