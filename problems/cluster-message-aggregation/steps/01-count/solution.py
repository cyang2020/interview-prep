import heapq
import random

EXTERNAL = "-1"   # 外部客户端的 from_id；根的 parent_id 也是它


class Cluster:
    """面试官提供的消息层，题面说"已经实现好了"，面试时不用写。

    这里给一个能跑的模拟：send_async_message 给消息随机定一个传输时间，放进按到达时刻排序的堆里，立刻返回；
    run() 按到达时刻一条条投递。传输时间各不相同，所以到达顺序和发送顺序不同，代码不能依赖"先发的先到"。
    order 可以指定 fifo / lifo，测试里用来制造特定的到达顺序。
    """

    def __init__(self, seed=0, order="random", max_latency=10):
        self.nodes = {}                  # node_id -> Node
        self.pending = []                # 还没投递的 (到达时刻, 序号, target_id, message, from_id)
        self.rng = random.Random(seed)
        self.order = order
        self.max_latency = max_latency   # 一条消息最多传多久
        self.now = 0                     # 模拟时钟
        self.seq = 0

    def add(self, node):
        self.nodes[node.node_id] = node
        node.cluster = self

    def send_async_message(self, target_id, message, from_id):
        self.seq += 1
        item = (self.now + self.rng.randint(1, self.max_latency), self.seq, target_id, message, from_id)
        if self.order == "random":
            heapq.heappush(self.pending, item)
        else:
            self.pending.append(item)    # fifo / lifo 不看传输时间，按发送顺序或者倒序

    def run(self):
        while self.pending:
            self._deliver_next()

    def _deliver_next(self):
        if self.order == "random":
            item = heapq.heappop(self.pending)       # 到达时刻最早的先投递
            self.now = item[0]
        else:
            item = self.pending.pop(0 if self.order == "fifo" else -1)
            self.now += 1
        _, _, target_id, message, from_id = item
        self.nodes[target_id].receive_message(from_id, message)


class Node:
    def __init__(self, node_id, parent_id, children, printer=print):
        self.node_id = node_id
        self.parent_id = parent_id             # 根是 EXTERNAL
        self.children = list(children)         # 孩子 id，顺序就是题面要求的输出顺序
        self.cluster = None                    # Cluster.add 时注入，发消息用
        self.printer = printer                 # 只有根会调用；测试里换成往列表里收
        # 一次 count 在这个节点上的进度：收到了几个孩子的回复、这些回复加起来是多少
        self.count_replies = 0
        self.count_sum = 0

    def receive_message(self, from_id, message):
        if message == "count":
            # 请求：来自父亲，或者来自外部客户端（只有根会收到后者）
            self.count_replies = 0             # 先把状态准备好再发消息，回复才不会先于初始化到达
            self.count_sum = 0
            for child in self.children:
                self.cluster.send_async_message(child, "count", self.node_id)
            self._finish_count_if_ready()      # 没有孩子的节点在这里直接完成
        elif message.startswith("count_result:"):
            # 回复：来自某个孩子，带着它那棵子树的节点数
            self.count_sum += int(message[len("count_result:"):])
            self.count_replies += 1
            self._finish_count_if_ready()

    def _finish_count_if_ready(self):
        if self.count_replies < len(self.children):
            return                             # 还有孩子没回，继续等
        total = self.count_sum + 1             # 加上自己
        if self.parent_id == EXTERNAL:
            self.printer(str(total))           # 根：打印，不再往上发
        else:
            self.cluster.send_async_message(self.parent_id, f"count_result:{total}", self.node_id)
