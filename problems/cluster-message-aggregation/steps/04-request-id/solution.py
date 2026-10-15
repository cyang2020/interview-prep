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


# 每种操作只需要定义一件事：拿到孩子们按 children 顺序排好的结果之后，怎么算出自己的结果。
# 叶子没有孩子，传进来的是空列表，所以叶子的值也由同一个函数给出，不用单独写分支。
def combine_count(node, child_results):
    return str(1 + sum(int(r) for r in child_results))


def combine_topology(node, child_results):
    if not child_results:
        return node.node_id
    return node.node_id + "(" + ",".join(child_results) + ")"


OPS = {"count": combine_count, "topology": combine_topology}


# 节点之间的消息固定四段：种类:操作名:请求编号:内容。REQ 是往下的请求，内容为空；RES 是往上的回复。
# 用冒号分隔的前提是节点 id 和结果里没有冒号，题面保证 id 是数字字符串，结果只含数字、括号、逗号。
def encode(kind, op, req_id, payload=""):
    return f"{kind}:{op}:{req_id}:{payload}"


def decode(message):
    kind, op, req_id, payload = message.split(":", 3)
    return kind, op, req_id, payload


class Pending:
    """一个请求在这个节点上的进度。"""

    def __init__(self, op):
        self.op = op
        self.replies = {}                      # 孩子 id -> 它回来的结果


class Node:
    def __init__(self, node_id, parent_id, children, printer=print):
        self.node_id = node_id
        self.parent_id = parent_id             # 根是 EXTERNAL
        self.children = list(children)         # 孩子 id，顺序就是题面要求的输出顺序
        self.cluster = None                    # Cluster.add 时注入，发消息用
        self.printer = printer                 # 只有根会调用；测试里换成往列表里收
        # 正在进行中的汇总：请求编号 -> Pending。同一种操作可以有多个请求同时在跑
        self.pending = {}
        self.next_seq = 0                      # 只有根用到：给每个外部请求起一个编号

    def receive_message(self, from_id, message):
        if from_id == EXTERNAL:
            # 外部客户端只发 "count" / "topology"，不带编号。编号由根起，之后每条消息都带着它
            self.next_seq += 1
            self._start(message, f"{self.node_id}-{self.next_seq}")
            return
        kind, op, req_id, payload = decode(message)
        if kind == "REQ":
            self._start(op, req_id)
        elif kind == "RES":
            state = self.pending.get(req_id)
            if state is None:
                return                         # 这个请求在本节点已经结束，丢弃（第五问会讲这种消息从哪来）
            state.replies[from_id] = payload
            self._finish_if_ready(req_id)

    def _start(self, op, req_id):
        if op not in OPS:
            raise ValueError(f"unknown op {op!r}")
        self.pending[req_id] = Pending(op)     # 先把状态准备好再发消息
        for child in self.children:
            self.cluster.send_async_message(child, encode("REQ", op, req_id), self.node_id)
        self._finish_if_ready(req_id)          # 没有孩子的节点在这里直接完成

    def _finish_if_ready(self, req_id):
        state = self.pending[req_id]
        if len(state.replies) < len(self.children):
            return                             # 还有孩子没回，继续等
        ordered = [state.replies[child] for child in self.children]   # 按 children 顺序，不按到达顺序
        result = OPS[state.op](self, ordered)
        del self.pending[req_id]               # 做完就删，不然每个请求都留一份，内存只增不减
        if self.parent_id == EXTERNAL:
            self.printer(result)               # 根：打印，不再往上发
        else:
            self.cluster.send_async_message(self.parent_id, encode("RES", state.op, req_id, result), self.node_id)
