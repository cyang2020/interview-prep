# 第五问：消息会丢、机器会挂，超时重发和去重

## 这一问要做什么

- 节点之间的消息会丢，某台机器可能挂掉。丢了的消息要重发，根最后仍要打印对；重发造成的重复消息不能让结果算两遍。
- 某个孩子怎么发都没回音时不能一直等，要在根打印一条失败信息，说明哪个节点联系不上。
- 多一个假设：节点有本地定时器 set_timer(node_id, delay, key)，到点回调 on_timer(key)，on_timer 要你写。

## 核心思路

- 接口多一样：节点要有本地定时器。Cluster 提供 set_timer(node_id, delay, key)，到点回调节点的 on_timer(key)，key 就是请求编号。面试里说"假设有这个定时器"，面试官一般认可。
- 消息种类加两种：ERR 往上报失败，内容是联系不上的节点 id；ACK 是孩子对重复请求的回答"我还在算"，内容为空。
- 节点多四个字段：timeout（等多久没收齐就重发，None 表示不设）、max_attempts（最多发几轮）、done（OrderedDict，请求编号到最终发给父亲的那条消息）、done_cache（done 最多留几条）。Pending 多 attempts：{孩子 id: 已发几轮}，第一轮算 1。
- 收到 REQ 分三种：req_id 在 done 里，把 done[req_id] 原样再发给父亲，不重新往下问；在 pending 里，回一条 ACK；都不在，走 _start。
- 收到 RES：pending 里没有就丢弃；有就 replies[from_id] = payload，同一个孩子回两次后一次覆盖前一次，条目数不变。收到 ACK：attempts[from_id] = 1。收到 ERR：req_id 在 pending 里就调 _fail(req_id, payload)。
- on_timer(req_id)：pending 里没有就返回；逐个看没回的孩子，attempts[child] 已到 max_attempts 就 _fail(req_id, child) 并返回，否则 attempts 加 1、只给它重发 REQ；最后再 set_timer 一次。
- 成功和失败都走 _complete(req_id, final_message, printed)：成功的 final_message 是 RES，失败的是 ERR；del pending，done[req_id] = final_message，超过 done_cache 丢最老的，根打印 printed，不是根发 final_message 给父亲。根打印的失败信息长这样："count failed: no reply from 6"。
- 复杂度：不丢包时和第四问一样，只多定时器；每丢一条消息多一轮 timeout 等待加一条重发。

## 思考与反问

- 丢消息后做什么？重发，只发给还没回的孩子；某个孩子连续 max_attempts 轮没回音就当它挂了，整个请求报 ERR，根打印哪个节点联系不上。另一种口径是打印部分结果，我没选：topology 的部分结果格式说不清，count 打出 5 客户端也不知道少了谁。要部分结果改 _fail，把 missing 当成结果为 "?" 的孩子走 _finish_if_ready。
- "没回音"和"慢"必须分开，靠 ACK。6 挂了，根和 3 用同样的 timeout 和 max_attempts，根早 2 个单位开始计时：没有 ACK 的话根在 400 先放弃报 "no reply from 3"，而 3 要到 402 才试完；有 ACK，根每次重发 3 都回"还在算"，attempts[3] 归 1，根不会先于 3 放弃。
- 重试次数为什么按孩子分别记：3 有 5 和 6 两个孩子，5 早回了、6 一直没回音，次数要落在 6 头上；整个请求记一个数，5 的 ACK 会把 6 的账也清掉，6 永远判不了挂。
- 父亲重问时孩子为什么回 done 里存的，不重新算：重新算要再问整棵子树，一次丢包的代价变成整棵子树重做；而且树在变时第二次算的结果可能不一样，父亲拿到的是哪一次说不清。
- done 为什么要有上限：不设，每个请求在每个节点永远留一条。超出上限后父亲重问会被当成新请求重新算，结果仍对只是慢，所以上限定成"父亲最晚可能重问的时间内经过的请求数"够用。
- 追问"timeout 定多短会出错"：不会出错。30 层的链、timeout 20，根的定时器到期十几次，每次收到 ACK，最后照样打印 30；代价是每隔 timeout 多一对 REQ 和 ACK，所以 timeout 还是按子树最深路径往返时间乘余量定。

## 测试要点

- test_lost_request_is_resent：3 发给 6 的第一条 REQ 丢了，3 超时后只给 6 重发，最后打印 7。
- test_lost_reply_is_answered_from_done_cache_not_recounted：6 回给 3 的第一条 RES 丢了，3 重问，6 从 done 原样重发不再问 7，打印 7 不是 8。
- test_duplicate_reply_before_finish_counts_once：2 的回复到两次只算一次；做完后迟到的回复丢弃，不会第二次打印。
- test_random_loss_still_correct：两成丢包、10 个随机种子，count 和 topology 都算对，pending 清空。
- test_unreachable_node_reports_error_at_root：发给 6 的消息全丢，根只打印一次 "count failed: no reply from 6"，失败也清状态。
- test_retry_rounds_are_bounded：max_attempts=3，3 总共只给 6 发 3 条 REQ。
- test_done_cache_is_bounded：done_cache=2，跑 5 次后每个节点 done 不超过 2 条。
- test_slow_subtree_acks_instead_of_failing：30 层链、timeout=20、max_attempts=2，没丢包，收到超过 10 条 ACK，打印 30 没有误报。
- test_parent_does_not_give_up_before_child_finishes_retrying：6 挂了，根报的是 6 不是 3。
- test_chain_counts_depth：第一问沿用，改成 timeout=None，50 层链只验证结果，不跑定时器。

## 更多说明

### 6 回给 3 的回复丢了（timeout 100，max_attempts 4，每条消息传 2 个单位）

| 时刻 | 谁 | 发生什么 |
|---|---|---|
| 0 | 1 | 收到 count，编号 1-1，给 2、3 发 REQ，定时器定在 100 |
| 2 | 3 | 收到 REQ，给 5、6 发 REQ，定时器定在 102 |
| 8 | 6 | 收齐 7 的回复，算出 2，存 done[1-1] = RES:count:1-1:2，发给 3，这条丢了 |
| 100 | 1 | 定时器到，3 没回，attempts[3] 变 2，给 3 重发 REQ |
| 102 | 3 | 收到 1 的重复 REQ，1-1 在 pending 里，回 ACK；自己定时器到，6 没回，attempts[6] 变 2，只给 6 重发 REQ |
| 104 | 1 | 收到 3 的 ACK，attempts[3] 归 1 |
| 104 | 6 | 收到重复 REQ，1-1 在 done 里，原样重发 RES:count:1-1:2，不再问 7 |
| 106 | 3 | 收到 6 的回复，收齐，算出 4 发给 1 |
| 108 | 1 | 收齐，打印 7 |

### 6 这台机器挂了

3 在 102、202、302 各给 6 重发一次，402 时 attempts[6] 已经是 4，3 调 _fail，发 ERR:count:1-1:6 给 1，1 打印 "count failed: no reply from 6"。期间根在 100、200、300、400 各给 3 重发一次，3 每次回 ACK，根的 attempts[3] 一直归 1，所以根报的是 6 不是 3。如果 8 那一行丢的是 3 发给 6 的 REQ，102 重发后 6 从头算一次，结果一样。

### timeout 和子树往返时间的关系

| timeout 和子树往返时间 | 后果 |
|---|---|
| timeout 大于往返时间 | 不丢包时定时器到期前已收齐，零额外消息 |
| timeout 小于往返时间 | 结果仍然正确，但每隔 timeout 多一对 REQ 和 ACK |
