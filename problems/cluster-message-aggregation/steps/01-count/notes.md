# 第一问：count，往下广播、往上汇总

## 这一问要做什么

- 写 receive_message(from_id, message)：收到 "count" 时该做什么。根收到客户端的 "count" 后，最后要打印整棵树的节点总数。
- 只能通过 send_async_message 和父亲、孩子通信，消息格式自己定；方法要立刻返回，不能在里面等别人回话。

## 核心思路

- 只写 receive_message(from_id, message)。消息格式自己定：往下的请求就是字符串 "count"，往上的回复是 "count_result:数字"。from_id 等于 EXTERNAL（"-1"）表示外部客户端，只有根会收到；根的 parent_id 也是 EXTERNAL。
- 每个节点两个字段：count_replies 回答"已收到几个孩子的回复"，count_sum 回答"这些回复加起来多少"。
- 收到 "count"：两个字段清零，给每个孩子发 "count"，然后调一次 _finish_count_if_ready。
- 收到 "count_result:k"：count_sum 加 k，count_replies 加 1，调一次 _finish_count_if_ready。
- _finish_count_if_ready：count_replies 小于孩子数就返回；收齐了算 count_sum + 1，根调 printer 打印，不是根就发 "count_result:总数" 给 parent_id。
- 不能写成递归：send_async_message 没有返回值，孩子的答案以后另发一条消息进来，所以"收到几个、加到多少"只能存在成员变量里，等下一次 receive_message 被调时接着用。
- 复杂度：每条边一条请求一条回复，共 2(n-1) 条消息；每个节点处理一条消息 O(1)，内存 O(1)；延迟是树深那么多轮往返。

## 思考与反问

- 开口定三条口径：消息到达顺序不保证；同一节点一次处理一条消息；消息不丢、一次只有一个请求。前两条决定代码不能假设"先发给 2 的先回来"但不用加锁；后一条决定状态直接放成员变量、count_replies 等于孩子数就算收齐，不用超时。
- 题面 fromId 一处写 String 一处写 int，问面试官按哪个。我统一用字符串，常量 EXTERNAL = "-1"。
- 为什么收到 "count" 后要立刻调一次 _finish_count_if_ready：叶子没有孩子，永远收不到回复；只在收到回复时检查，叶子永远不回话，整棵树卡住。n=1 时根自己就是叶子，这一条决定根能不能打印 1。
- 为什么先清零再发消息：第六问允许并发后，孩子的回复可能在 for 循环还没发完时到达；清零放在发完之后，先到的回复会被清掉。从第一问就按这个顺序写，后面不用改。
- 追问"消息里为什么要带 count_result 前缀，靠 from_id 是父亲还是孩子不行吗"：这一问行，但第四、五问要加请求编号和失败报告，靠方向分不出来。
- 追问"能不能在 receive_message 里原地等回复"：不能。回复也是通过调这个方法进来的，方法不返回回复就投不进来；一万节点的链每层都在等下层，调用栈一万层。

## 测试要点

- test_example_count：题面的 7 节点树，根只打印一次 "7"。
- test_single_node_root_prints_one：根没有孩子也要完成并打印 "1"，保护"收到请求后立刻检查一次完成"。
- test_any_delivery_order：20 个随机到达顺序加 fifo、lifo 两种固定顺序，结果都是 7。
- test_chain_counts_depth：50 层的链，每层只有一个孩子，打印 50。
- test_count_twice_in_a_row：上一次做完再发一次 "count"，count_replies 和 count_sum 要能重置，打印两次 7。

## 更多说明

### 用题面的树走一遍

1 的孩子是 2、3；2 的孩子是 4；3 的孩子是 5、6；6 的孩子是 7。步骤 2 到 6 的先后在真实系统里是随机的，加法不分先后，结果一样。

| 步骤 | 谁收到什么 | 做了什么 |
|---|---|---|
| 1 | 1 收到客户端的 "count" | 清零，给 2、3 发 "count"，孩子数 2，没收齐 |
| 2 | 4 收到 "count" | 没孩子，立刻回 2 一条 "count_result:1" |
| 3 | 2 收到 4 的回复 | count_sum=1，收齐，回 1 一条 "count_result:2" |
| 4 | 6 收到 7 的回复 | count_sum=1，收齐，回 3 一条 "count_result:2" |
| 5 | 3 收到 5 的回复 | count_sum=1，还差 1 个 |
| 6 | 3 收到 6 的回复 | count_sum=3，收齐，回 1 一条 "count_result:4" |
| 7 | 1 收到 2 的回复 | count_sum=2，还差 1 个 |
| 8 | 1 收到 3 的回复 | count_sum=6，收齐，根，打印 7 |

### 节点 3 的 receive_message 被调三次

| 第几次 | 收到什么 | count_replies | count_sum | 动作 |
|---|---|---|---|---|
| 1 | "count" | 0 | 0 | 给 5、6 发请求，返回，这时还不知道答案 |
| 2 | 5 回的 "count_result:1" | 1 | 1 | 还差一个 |
| 3 | 6 回的 "count_result:2" | 2 | 3 | 收齐，回父亲 4 |

递归写法里 3 调"算 5"等到返回 1，再调"算 6"等到返回 2，一次调用算完。这里三次调用之间，进度只能存在 3 自己的成员变量里，这就是 count_replies 和 count_sum 存在的原因。
