# 第三问：depends_on，任务形成 DAG

## 这一问要做什么

- enqueue 多一个 depends_on 列表：这个任务要等列表里的任务都做完才能被领。
- 任务之间的依赖连成 DAG。前置没完成的任务，reserve 领不到。

## 核心思路

- enqueue 多一个 depends_on 列表。状态加 blocked，排在 ready 前面；reserve 本来只放行 ready，不用改。
- 记录加 remaining_deps：还有几个前置没完成。队列加反向表 dependents：前置 job_id 到"等它的 job_id 列表"。
- enqueue：前置不存在或已 dead 就拒绝；去重后数未完成的前置写进 remaining_deps，并在每个未完成前置名下登记；为 0 则 ready 入队，否则 blocked 不入队。已完成的前置不计数也不登记。
- pass_：改 completed 之后查反向表，每个等它的任务 remaining_deps 减 1，减到 0 的从 blocked 改 ready 入队。全部代码里只有这一处减计数。
- 前置进 DLQ 时级联：改 dead、追加 DLQ，然后查反向表，仍是 blocked 的任务做同样的事，一层层传。查"仍是 blocked"保证每个任务只进一次 DLQ。
- 复杂度：建表 O(V+E)，V 任务数，E 去重后的依赖边数；一次完成或放弃的传播 O(等它的任务数)。

## 思考与反问

- "前置做完"指 completed。失败重试中、超时中都不算。
- depends_on 里有还没入队的怎么办？拒绝。附带好处：只能依赖已入队的任务，环构造不出来，不用写环检测，要主动说。
- 前置进了 DLQ，等它的任务怎么办？我选跟着进 DLQ，人在同一份名单里看到。可选项：一直 blocked，或直接放行。问面试官要哪种。
- 为什么减计数必须跟在 completed 后面、过 token 检查：C 超时后被 worker 2 重领，worker 1 迟到的 pass 若去减 D 的计数，D 会在 C 没做完时被放出去。
- 为什么要反向表：A 完成时要找"谁等 A"，没有反向表得扫全部记录的 depends_on，O(任务总数)；有了只碰等 A 的那几个。
- 反向表为什么归队列不归 worker：worker 只知道"B 做完了"，不知道 D 在等 B；全部依赖关系只有队列通过 enqueue 拿到。放在 Job 记录上还是队列的字典里，两种等价，说一句选哪种。

## 测试要点

- test_diamond：A；B、C 等 A；D 等 B 和 C。pass A 放行 B、C；pass B 后 D 仍 blocked；C 两次失败后 C、D 依次进 DLQ。
- test_late_pass_does_not_release_dependent：前置超时被重领，原 worker 迟到的 pass 不放行依赖它的任务。
- test_exhausted_prereq_cascades_once：D 等 A 和 B，A、B 都放弃，D 只进一次 DLQ。
- test_completed_or_unknown_prereq：依赖已完成的任务直接 ready；依赖不存在的任务拒绝入队。

## 更多说明

### 反向表是什么

depends_on 记的是"我等谁"，队列用的时候问题是反的："B 做完了，谁在等 B"。dependents 就是把每条"我等谁"倒过来存一份。菱形例子：

| 任务 | depends_on，我等谁 | dependents，谁等我 |
|---|---|---|
| A | 没有 | B、C |
| B | A | D |
| C | A | D |
| D | B、C | 没有 |

右边一列是 enqueue 时顺手记的：enqueue D 看到 D 等 B，就在 B 名下记"D 等我"。pass_("B") 时查 B 名下得到 D，D 的 remaining_deps 从 2 减到 1；pass_("C") 再减到 0，D 变 ready。

### 菱形例子走一遍

timeout 10 秒，max_retry=1。四个入队后：A ready，B、C、D blocked，D 的 remaining_deps=2。pass A：B、C 各减 1 变 0，都 ready。reserve B、C，pass B：D 减到 1 仍 blocked。fail C：C 回 ready，D 不动。再 reserve C，C 第二次超时：次数用完进 DLQ；查反向表 D 还是 blocked，跟着进。get_dlq 返回 [C, D]。
