# 第四问：多个请求同时进行，每个请求带编号

## 这一问要做什么

- 客户端连续发两个 "count"，第二个在第一个没做完时就到，两个都要打印 7；count 和 topology 混着同时发也要各自打印对。
- 接口不变，客户端发的还是纯 "count" / "topology"，不带任何编号。

## 核心思路

- 接口不变。节点之间的消息统一成四段 "种类:操作名:请求编号:内容"，encode 拼、decode 用 split(":", 3) 拆。REQ 是往下的请求，内容为空；RES 是往上的回复。
- 新增字段 next_seq：只有根用，回答"下一个请求编号是什么"。编号是 node_id 加短横线加 next_seq，比如 "1-1"、"1-2"。
- pending 的键从操作名改成请求编号，值是 Pending 对象，里面 op 记操作名、replies 记 {孩子 id: 结果}。
- receive_message 三条路径：from_id 是 EXTERNAL 就 next_seq 加 1、调 _start(message, 编号)；REQ 调 _start(op, req_id)；RES 用 pending.get(req_id)，查不到丢弃，查到存 replies[from_id]，调 _finish_if_ready(req_id)。
- _start 和 _finish_if_ready 和第三问一样，键换成 req_id；完成时 del pending[req_id]。
- 复杂度：每个请求还是 2(n-1) 条消息；每个节点内存是进行中的请求数乘孩子数。

## 思考与反问

- 编号由谁生成？题面规定客户端只发 "count"，改不了，所以由根起：根是唯一知道"这是一个新请求"的节点，所有请求都经过它，序号不重复。这决定了 receive_message 先看 from_id 是不是 EXTERNAL。多棵树各有根或根会重启时，编号要加随机部分或时间戳，提一句。
- 第三问的代码为什么坏：两个 count 都存在 pending["count"]，第二个请求到节点 3 时把字典置空，第一个请求已收到的 5 的回复被清掉；之后两个请求的回复混进同一个字典，条目到 2 就完成，另一个请求永远收不齐。
- 编号为什么要走到每一层而不是只在根上记：2 和 3 也各收到两条请求，它们也要分清各自的回复属于哪个，否则同样的混乱在 2 和 3 上发生。
- 做完为什么一定 del pending[req_id]：不删，一万个节点、每秒 10 个请求，一天每个节点留 86 万条 Pending，没有一条还有用。
- 追问"客户端分不清哪个结果对应哪个请求"：题面只要求打印结果；要分清就在 printer 打印的内容里带上编号，一行改动。

## 测试要点

- test_same_op_twice_at_the_same_time：两个 count 同时跑，20 个随机顺序都打印两次 7，做完 pending 为空；第三问的代码在这里会失败。
- test_many_mixed_requests_at_once：10 个 count 和 10 个 topology 同时发，每个各打印一次，20 个请求的状态都清掉。
- test_request_ids_are_unique：直接给根喂两条外部请求，根的 pending 键是 "1-1"、"1-2"。

## 更多说明

### 两个 count 同时跑，看节点 3

第一个请求编号 1-1，第二个 1-2。

| 步骤 | 3 收到什么 | pending | 动作 |
|---|---|---|---|
| 1 | REQ:count:1-1: | {1-1: {}} | 给 5、6 发 REQ:count:1-1: |
| 2 | 5 回 RES:count:1-1:1 | {1-1: {5: 1}} | 还差 6 |
| 3 | REQ:count:1-2: | {1-1: {5: 1}, 1-2: {}} | 给 5、6 发 REQ:count:1-2:，1-1 的进度没被动 |
| 4 | 6 回 RES:count:1-2:2 | {1-1: {5: 1}, 1-2: {6: 2}} | 回复按编号归位 |
| 5 | 6 回 RES:count:1-1:2 | {1-2: {6: 2}} | 1-1 收齐，回 RES:count:1-1:4，删 1-1 |
| 6 | 5 回 RES:count:1-2:1 | {} | 1-2 收齐，回 RES:count:1-2:4，删 1-2 |

### 消息格式变化

| 第几问 | 往下 | 往上 |
|---|---|---|
| 一、二 | count / topology | count_result:7 / topology_result:... |
| 三 | count / topology | RES:count:7 |
| 四 | REQ:count:1-1: | RES:count:1-1:7 |
