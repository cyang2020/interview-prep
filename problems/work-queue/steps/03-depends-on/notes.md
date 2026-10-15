# 第三问：depends_on，任务形成 DAG

## 接口改一处

enqueue 多一个参数 depends_on，是一个 job_id 列表，表示"这个任务要等列表里的任务都做完才能领"。其余四个方法签名不动。

```python
def enqueue(self, job_id, timeout, max_retry, depends_on=None):
    pass
```

## 思路

**开口先定四个口径。**

1. 什么叫"前置做完"：前置到达 completed，也就是成功完成。失败重试中、超时中都不算。
2. depends_on 里的任务还没 enqueue 怎么办：拒绝入队，返回 False。这条规则有个附带好处：一个任务只能依赖已经入队的任务，后入队的不可能被先入队的依赖，所以环根本构造不出来，不用写环检测。这点要主动说。
3. 前置进了 DLQ，等它的任务怎么办：它永远等不到了。我选"跟着进 DLQ"，让人在同一份名单里看到。另两种可选：一直 blocked 不管它，或者直接放行。再往后 enqueue 一个依赖已放弃任务的新任务，直接拒绝。
4. depends_on 里有重复的，去重后算一个。

**状态加 blocked，排在 ready 前面。** 意思是"还有前置没完成，不能领"。reserve 遇到 blocked 和遇到 reserved 一样拒绝，代码不用改，因为 reserve 本来就只放行 ready。

**记录加一个字段，队列加一张表。** 字段 remaining_deps：这个任务还有几个前置没完成。表 dependents：前置 job_id 到"等它的 job_id 列表"，叫反向表，因为 depends_on 是"我等谁"，这张表是"谁等我"。

**为什么要反向表，不这么做会怎样。** A 完成时要找出所有等 A 的任务去减计数。不建反向表就得把 jobs 里每条记录的 depends_on 扫一遍看有没有 A，一次完成 O(任务总数)。有了反向表，一次完成只碰等 A 的那几个，O(等 A 的任务数)。

**enqueue 怎么变。** 先按口径 2 和 3 检查前置：有不存在的或已放弃的，拒绝。然后数 depends_on 里还没 completed 的有几个，写进 remaining_deps，并且在反向表里每个这样的前置下面登记"这个任务等我"。已经 completed 的前置不计数、不登记，不然它的完成早就发生过了，这个任务永远等不到。remaining_deps 为 0 就和以前一样 ready 入队，大于 0 就 blocked，不入队。

**pass_ 怎么变。** 状态改成 completed 之后，多一步：查反向表，等它的每个任务 remaining_deps 减 1，减到 0 的从 blocked 改 ready 入队。这一步只在 pass_ 里出现，而且写在 token 检查通过、状态改成 completed 的紧后面。reserve、fail、超时、被拒绝的迟到 pass 都不碰 remaining_deps。

**为什么放行只能跟在 completed 后面。** 用例子：D 等 C。C 第一次被 worker 1 领走，超时，第 12 秒 worker 2 重新领走。第 15 秒 worker 1 迟到调 pass_。如果这次 pass_ 不被拒、或者被拒了但仍然去减 D 的计数，D 就被放出去了，而 C 实际上还没做完。所以减计数这步必须和 completed 绑在同一个地方，第二问的 token 检查在这里又挡了一次。

**前置放弃时怎么级联。** 第二问里"改 dead、追加 DLQ"原来是两行，现在抽成一个方法：改 dead、追加 DLQ，然后查反向表，等它的每个任务如果还是 blocked，就对它做同样的事，一层层传下去。为什么要查"还是 blocked"：D 等 A 和 B，A、B 都放弃，A 放弃时 D 已经进了 DLQ，B 放弃时再碰到 D 不能让它第二次进。这就是"一个任务进 DLQ 只进一次"在第三问的体现。

**菱形例子走一遍。** A；B 等 A；C 等 A；D 等 B 和 C。timeout 10 秒，max_retry=1。

- 四个入队后：A ready，B、C、D blocked，D 的 remaining_deps=2。反向表：A 下面挂 B、C；B 下面挂 D；C 下面挂 D。不指名 reserve 只能拿到 A，指名 reserve("B") 被拒。
- pass A：查反向表，B、C 各减 1 变 0，都变 ready。
- reserve B、reserve C。pass B：D 从 2 减到 1，仍 blocked。
- fail C：C 第一次失败回 ready，D 不动。再 reserve C。
- C 第二次超时：次数用完，C 进 DLQ；查反向表 D 还是 blocked，D 跟着进 DLQ。get_dlq 返回 [C, D]。

**复杂度。** 建反向表 O(V+E)，V 是任务数，E 是去重后的依赖边数。一次完成或一次放弃的传播 O(等它的任务数)。第二问的堆和重试代价另算。

## 常见疑问

### 反向表是什么，为什么归队列做

**反向表是什么。** depends_on 记的方向是"我等谁"：D 的 depends_on 是 [B, C]，意思是 D 等 B 和 C。但队列真正要用的时候，问题是反过来的：B 做完了，谁在等 B？要回答这个问题，就把每条"我等谁"倒过来存一份，变成"谁等我"。dependents 这张表就是倒过来的那份，所以叫反向表。

用菱形例子看两张表的内容。A；B 等 A；C 等 A；D 等 B 和 C。

| 任务 | depends_on，我等谁 | dependents，谁等我 |
|---|---|---|
| A | 没有 | B、C |
| B | A | D |
| C | A | D |
| D | B、C | 没有 |

左边一列是 enqueue 时调用方传进来的，右边一列是队列在 enqueue 时顺手倒过来记的：enqueue D 时看到 D 等 B，就在 B 名下记一笔"D 等我"；看到 D 等 C，就在 C 名下记一笔"D 等我"。

**用的时候走一遍。** worker 调 pass_("B")。队列把 B 改成 completed，然后查反向表 B 名下：D。于是把 D 的 remaining_deps 从 2 减到 1。再 pass_("C")，查 C 名下：D，D 从 1 减到 0，D 变 ready。

**不建反向表会怎样。** B 做完时队列只有左边那列，要知道谁在等 B，得把所有任务的 depends_on 逐个翻一遍，看谁的列表里有 B。100 万个任务就要查 100 万次，每完成一个任务都这么查一遍。有了右边那列，直接查 B 名下，只碰等 B 的那几个。

**为什么这事归队列做，不归 worker。** worker 做完 B 只知道一件事：B 做完了。它不知道 D 的存在，更不知道 D 在等 B。知道所有任务和所有 depends_on 的只有队列，因为 depends_on 是通过 enqueue 交给队列的。所以只有队列能把"B 做完了"翻译成"D 现在可以领了"。如果让 worker 或者调用方来做，就得由他们自己记住 D 等 B，做完 B 之后再来调一个"放行 D"的方法，队列就没法保证 D 一定是在 B、C 都真正完成之后才放出去的，谁都可以提前把 D 放出来。题目要求的正是"队列要保证前置没完成的任务领不到"，这个保证只能由掌握全部依赖关系的那一方给。

**为什么放在 WorkQueue 的一个字典里，而不是放在 Job 记录上。** 这两种写法等价。也可以在每个 Job 记录上加一个字段，比如 waiting_on_me 列表，B 的记录里存 [D]。我用字典是让 Job 记录只放自己的状态，依赖关系集中在队列一处。面试时两种都行，说一句你选哪种就够。
