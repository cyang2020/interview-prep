# 题面

## 原题要点

> You are implementing a message-based protocol for a distributed system organized as a rooted n-ary tree. Each node represents a machine, identified by a unique string ID. Each node stores its parent's ID (-1 for the root) and a list of its children's IDs. Nodes communicate only with their immediate parent and children using a provided asynchronous messaging API. Support two operations, both triggered by an external client sending a message to the root: "count" makes the root print the total node count; "topology" makes the root print the tree as a string, where a leaf is its own ID and an internal node is "ID(child1,child2,...)" with children in the order of the children list. All inter-node communication must go through sendAsyncMessage and receiveMessage. 1 ≤ n ≤ 10^4.

原题给的是 Java 签名，Cluster 已实现，只写 receiveMessage：

```
class Node {
    String nodeId;
    String parentId;          // 根是 -1
    List<String> children;    // 孩子 id，顺序就是输出顺序
    void receiveMessage(String fromId, String message);   // 要你写；外部客户端发来的 fromId 是 -1
}
class Cluster {
    void sendAsyncMessage(String targetId, String message, String fromId);   // 已实现，异步，无返回值
}
```

题面例子：1 的孩子是 2、3；2 的孩子是 4；3 的孩子是 5、6；6 的孩子是 7。给根发 "count" 打印 7，发 "topology" 打印 1(2(4),3(5,6(7)))。

## 这题要你写的东西是什么

一个机房里有 n 台机器，连成一棵树：每台机器只认识自己的上级和直接下级，只能和它们通信，没有任何一台机器知道整个机房有多少台、长什么样。运维在根机器上敲一个命令 "count"，要求根最后报出总台数；敲 "topology"，要求根最后报出整棵树的结构。你写的是每台机器上的同一段程序：收到一条消息时该做什么。

## 每个方法和输入分别是什么意思

- receive_message(from_id, message)：系统在消息到达时自动调用，告诉这台机器"谁发来的、内容是什么"。你在里面决定改什么内部记录、给谁再发什么、要不要打印。方法要立刻返回，不能在里面等别人回话。
- send_async_message(target_id, message, from_id)：把一段文字发给某个邻居，只能是父亲或孩子。发出去就返回，没有返回值，对方什么时候收到、几条消息按什么顺序到，都不保证。
- from_id 等于 "-1"：这条消息来自外部客户端，只有根会收到。parent_id 等于 "-1"：这台机器是根。
- message 只是字符串。请求和回复怎么区分、回复里怎么带数据，格式由你定。

## 题目分几问

题面只明确给了 count 和 topology 两个操作。后面四问是这类题的标准追问方向，按面试里的推进顺序排。

1. count：往下广播请求，往上汇总数字，根打印总数。
2. topology：同样的流程，汇总的是字符串，而且要按 children 列表的顺序拼。
3. 把两种操作合并成一套流程，每种操作只提供"怎么合并孩子的结果"。
4. 多个请求同时进行：每个请求带编号，状态按编号分开存。
5. 消息会丢、机器会挂：超时重发、重复请求和重复回复去重、重发到上限就报失败。
6. receive_message 会被多线程同时调用：加锁。一万节点的链：不能递归。

## 题面故意没说清楚的地方

- 同一台机器的 receive_message 是一次处理一条，还是会被并发调用。
- 消息会不会丢、会不会乱序。
- 会不会有多个客户端请求同时在跑。
- 节点 id 会不会含特殊字符，这决定消息里能不能用冒号做分隔。
- 操作进行中树会不会变。
- 题面里 fromId 一处写 String 一处写 int，按面试官给的签名来。

## 面试形式

prep 站标的阶段是 screening，也就是电话筛选轮，60 分钟 coding。第一、二问必须写出来跑通；第三问是写完第二问时主动做的小重构；第四问大概率会追问并要求改代码；第五、六问多数时候口头讲思路，时间够再写。来源说明：题面和"3 天前有人报告"来自 prep 站的整理，不是第一人称面经。
