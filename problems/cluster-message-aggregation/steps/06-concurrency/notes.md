# 第六问：并发调用加锁，一万节点的链不爆栈

## 这一问要做什么

- 同一个节点的 receive_message 和 on_timer 会被多个线程同时调用，结果仍要对、不能抛异常。
- 一万个节点连成一条链时也要能跑完 count 和 topology，不能因为调用太深出错。

## 核心思路

- 接口不变。节点多一个字段 lock（threading.Lock）。receive_message 变成"with self.lock 调 _receive"，on_timer 变成"with self.lock 调 _on_timer"，原方法体改名成 _receive 和 _on_timer，一行不动。
- 锁保护的是"存一条回复、检查收齐、删进度"这一串，必须一口气做完，中间不能被另一条消息的处理插进来。
- 不同节点各自一把锁，互不相关。send_async_message 只是把消息交出去立刻返回，不会同步调目标节点的方法，所以拿着锁发消息不会去拿别人的锁，不会死锁。
- 一万节点的链不递归：每一跳是 run() 循环里一次独立的 receive_message 调用，调用返回后才投下一条，调用栈深度始终是 1。Python 默认递归上限 1000，递归写法第 1000 层就抛 RecursionError。
- ThreadedCluster 只用来测并发安全：线程池投递，send_async_message 提交一个任务，任务里调目标节点的 receive_message；run() 等 inflight 归零；节点里抛的异常收进 errors 由 run() 重新抛出；set_timer 是空操作，不做丢包。
- 复杂度和第五问一样，锁的开销是常数。规模数字：n 一万每个请求两万条消息；一万层链的 topology 字符串近六万字符；每个节点内存是进行中请求数乘孩子数，加 done 的上限条数。

## 思考与反问

- 同一节点的 receive_message 和 on_timer 会不会被不同线程同时调？按会，每个节点一把锁把两个方法整个包住。按不会的话第五问的代码直接用。
- 不加锁会怎样，看节点 3：5 和 6 的回复同时到，两个线程各写一条 replies，都看到条目数是 2，都调 _finish_if_ready，都发回复给 1，都去 del pending[1-1]。1 收到两条一样的回复字典覆盖不算错，但第二个 del 抛 KeyError，done 并发写也可能损坏。加锁后第二次进来 pending 里已没有 1-1，走丢弃分支。
- 什么时候会死锁：send_async_message 如果是同步的，在调用里直接调目标节点的 receive_message，那 3 拿着锁调 1、1 拿着锁调 3，互相等。题面明说是异步的，面试里把这句说出来。
- 一万节点的链为什么测试里 timeout 传 None：一万个节点都在等，一次往返要两万条消息，每隔 timeout 都会重发并收 ACK，结果不会错，但模拟要多跑几十万条消息；这个测试只验证深度。
- 追问"一个节点五千个孩子"：星形树，根上 pending 的 replies 五千条，topology 字符串两万多字符，都是线性的。
- 追问"锁粒度能不能更细"：可以按请求编号分锁，但 pending 字典本身的增删还要一把锁，收益小；每节点一把锁够用，一次消息处理最多 O(孩子数)。

## 测试要点

- test_threaded_many_concurrent_requests：ThreadedCluster 8 个线程投递，100 个 count 和 100 个 topology 混着跑，每个各打印一次，pending 清空；没有锁时节点里的 KeyError 会由 run() 抛出。
- test_chain_of_10000_nodes_does_not_recurse：n 大于 sys.getrecursionlimit()，一万层链 count 打印 10000，topology 拼出一万层括号。
- test_wide_tree_with_5000_children：根有 5000 个孩子，count 打印 5001，topology 是 1(2,3,...,5001)。

## 更多说明

### 不加锁和加锁的区别

| 不加锁 | 加锁 |
|---|---|
| 两个线程同时看到"收齐"，各自完成一次 | 第一个线程完成并删掉状态，第二个线程进来时查不到，丢弃 |
| 第二次 del pending 抛 KeyError | 不会 |

### 拿着锁发消息

| 场景 | 3 的锁 | 1 的锁 | 结果 |
|---|---|---|---|
| 异步发消息 | 3 拿着，发完就放 | 1 拿着，发完就放 | 各自返回 |
| 同步调对方的方法 | 3 拿着，等 1 处理完 | 1 拿着，等 3 处理完 | 互相等，死锁 |
