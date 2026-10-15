# 第三问：两种操作合并成一套流程

## 这一问要做什么

- 接口不变。把 count 和 topology 两套几乎一样的代码合成一套流程，每种操作只写一个"拿到孩子的结果怎么算自己的结果"的函数。
- 验收标准：再加一种新操作时只加那个函数，收发消息的代码一行不改。

## 核心思路

- 接口不变。一种操作等于一个合并函数 (node, child_results) -> 结果字符串，child_results 是孩子们按 children 顺序排好的结果列表；叶子传进来空列表，叶子的值也由同一个函数给出。
- 两个合并函数：combine_count 返回 1 加所有孩子结果转整数的和；combine_topology 没孩子返回 node_id，有孩子返回 node_id(用逗号连接)。注册在字典 OPS，操作名到函数。
- 消息格式统一：请求就是操作名，回复是 "RES:操作名:结果"，用 split(":", 2) 拆。外部客户端发的也是操作名，根和内部节点的请求走同一个分支。
- 状态改成 pending：字典，操作名到 {孩子 id: 结果}，回答"这种操作在本节点收到了谁的结果"。count_replies、count_sum、topo_replies 全部删掉。
- receive_message 只剩两个分支。以 "RES:" 开头：pending.get(op) 为 None 就丢弃，否则 replies[from_id] = payload，调 _finish_if_ready(op)。其他：op 不在 OPS 里抛 ValueError；在就 pending[op] = {}，给每个孩子转发同一条消息，调 _finish_if_ready(op)。
- _finish_if_ready(op)：条目数小于孩子数返回；否则按 self.children 取出 ordered 列表，用 OPS[op] 算出 result，del pending[op]，根打印，不是根发 "RES:op:结果" 给父亲。
- 复杂度和前两问一样。

## 思考与反问

- 这一问一般不是面试官出的，是写完第二问主动说"两种操作的消息流程一模一样，我抽成一套，操作只提供合并函数"。面试官问"再加一种操作改哪里"时答：往 OPS 加一行。
- 合并函数收"按 children 排好的列表"还是收 {孩子 id: 结果} 字典自己排？我选列表：按 children 顺序是题面对所有操作的统一要求，在 _finish_if_ready 里写一次；每个合并函数不用各自记得排序，少一处出错。
- count 为什么也从两个数字改成字典：为了两种操作走同一段代码。附带好处是第五问同一个孩子的回复可能到两次，字典按孩子 id 存，第二次覆盖第一次，不会加两遍；计数器做不到。
- 收到不在等的回复怎么办：pending 里没有这个操作名就丢弃。这一问不会发生，第五问重发后会出现迟到的回复，这一行提前写上。
- 追问"count 和 topology 同时发到根行不行"：行，pending 按操作名分键，回复里带操作名各归各的。两个 count 同时发不行，它们共用 pending["count"]，第四问解决。

## 测试要点

- test_count_and_topology_at_the_same_time：count 和 topology 同时发到根，两个都算对，做完后所有节点 pending 为空。
- test_new_op_only_needs_a_combine_function：往 OPS 临时加 "depth"（叶子 1，非叶子 1 加孩子里最大的），消息流程一行不改，题面的树算出 4。
- test_unknown_op_rejected：发 "reboot" 这种不认识的操作名，抛 ValueError，不往下传。
- test_children_order_kept_when_replies_arrive_reversed：第二问沿用，改成字典后 lifo 顺序下输出仍按 children 排。

## 更多说明

### 流程给合并函数的是什么

流程收到 {"6": "6(7)", "5": "5"}，按 children [5, 6] 排成 ["5", "6(7)"] 再交给 combine_topology，它只管拼。

| 操作 | 流程给的列表，已按 children 排 | 合并函数算出 |
|---|---|---|
| count，节点 3 | ["1", "2"] | "4" |
| topology，节点 3 | ["5", "6(7)"] | "3(5,6(7))" |
| count，叶子 7 | [] | "1" |
| topology，叶子 7 | [] | "7" |

### 消息格式变化

| 第几问 | 往下 | 往上 |
|---|---|---|
| 一、二 | count / topology | count_result:7 / topology_result:... |
| 三 | count / topology | RES:count:7 |
