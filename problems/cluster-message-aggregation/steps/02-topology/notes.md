# 第二问：topology，按 children 顺序拼字符串

## 这一问要做什么

- 收到 "topology" 时根打印整棵树的结构：叶子是自己的 id，非叶子是 id(孩子1,孩子2,...)，孩子按 children 列表顺序。例子打印 1(2(4),3(5,6(7)))。
- count 的功能保留，两种消息都要能处理。

## 核心思路

- 接口不变，多支持两种消息：往下的请求 "topology"，往上的回复 "topology_result:字符串"。拆的时候切掉固定前缀，剩下整段就是结果，不再按冒号拆，所以结果里的括号逗号不碍事。
- 新增字段 topo_replies：字典，孩子 id 到它回来的子树字符串，回答"收齐了没、每个孩子的结果是什么"。收齐的判断是条目数等于孩子数。
- 收到 "topology"：topo_replies 置空字典，给每个孩子发 "topology"，调一次 _finish_topology_if_ready。
- 收到 "topology_result:s"：topo_replies[from_id] = s，调一次 _finish_topology_if_ready。按 from_id 存，不能收到一个拼一个。
- _finish_topology_if_ready：没收齐返回；有孩子就按 self.children 顺序逐个从 topo_replies 取，拼成 id(孩子1,孩子2,...)；没孩子结果就是 node_id；根打印，不是根发 "topology_result:结果" 给 parent_id。
- 和 count 的区别只有两处：叶子的值（1 对 node_id）和合并方式（加起来加 1 对拼括号）。消息流程、完成条件、根打印的判断完全一样。
- 复杂度：消息数还是 2(n-1)；每个节点拼字符串的代价是它子树的字符串长度，根上约 n 乘 id 平均长度。

## 思考与反问

- 输出顺序按 children 列表还是按回复到达顺序？按 children，这决定了回复必须先存进 topo_replies，收齐后按 self.children 取。
- 为什么不能收到一个拼一个：根给 2、3 发请求，3 的子树回复可能先到，收到一个拼一个得到 1(3(5,6(7)),2(4))，题面要的是 1(2(4),3(5,6(7)))。测试用 lifo 投递顺序专门造这个情况。
- id 会不会含冒号？题面例子里 id 都是数字，我按"id 和结果里没有冒号"做。这一问只切固定前缀，id 含冒号也没事；第四问消息要按冒号拆多段，到时 id 含冒号就得换 JSON 或"长度:内容"编码。
- count 为什么这一问不改成字典：两个数字够用，不动。第三问合并两种操作时统一改成字典，第五问还能靠字典按孩子 id 覆盖去重。
- 追问"拼出来的字符串多大"：根上是整棵树的字符串，n 一万、id 平均 4 个字符，加括号逗号五六万字符，一次拼接没问题。

## 测试要点

- test_example_topology：题面的树打印 1(2(4),3(5,6(7)))。
- test_single_node_topology：根没有孩子，打印 "1"，叶子不带括号。
- test_children_order_kept_when_replies_arrive_reversed：lifo 投递，后发的先到，3 的回复先于 2 到，输出仍按 children 顺序。
- test_topology_any_delivery_order：20 个随机到达顺序结果都一样。
- test_chain_topology：5 层的链拼出 1(2(3(4(5))))。
- test_count_then_topology：先 count 再 topology，count_replies、count_sum 和 topo_replies 互不干扰。

## 更多说明

### 节点 3 走一遍，6 的回复先到

| 步骤 | 3 收到什么 | topo_replies | 动作 |
|---|---|---|---|
| 1 | "topology" | {} | 给 5、6 发 "topology" |
| 2 | 6 回的 "topology_result:6(7)" | {"6": "6(7)"} | 1 个，还差 1 个 |
| 3 | 5 回的 "topology_result:5" | {"6": "6(7)", "5": "5"} | 收齐，按 children 顺序 [5, 6] 取，拼成 3(5,6(7)) |

### 消息怎么拆

| 消息 | 怎么拆 | 拆出来 |
|---|---|---|
| "topology_result:3(5,6(7))" | 切掉固定前缀 | "3(5,6(7))" |
| "topology_result:5" | 切掉固定前缀 | "5" |
| "count_result:4" | 切掉固定前缀，转整数 | 4 |
