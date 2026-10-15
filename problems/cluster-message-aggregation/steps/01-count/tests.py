from solution import Cluster, Node, EXTERNAL

# 题面例子里的树：1 的孩子是 2、3；2 的孩子是 4；3 的孩子是 5、6；6 的孩子是 7
EXAMPLE = {"1": ["2", "3"], "2": ["4"], "3": ["5", "6"], "4": [], "5": [], "6": ["7"], "7": []}


def make_cluster(tree, seed=0, order="random"):
    """按 {节点: 孩子列表} 建集群；根打印的内容收进 out 列表返回。"""
    out = []
    cluster = Cluster(seed=seed, order=order)
    parent = {c: p for p, cs in tree.items() for c in cs}
    for node_id, children in tree.items():
        cluster.add(Node(node_id, parent.get(node_id, EXTERNAL), children, printer=out.append))
    return cluster, out


def chain(n):
    return {str(i): ([str(i + 1)] if i < n else []) for i in range(1, n + 1)}


def test_example_count():
    cluster, out = make_cluster(EXAMPLE)
    cluster.send_async_message("1", "count", EXTERNAL)
    cluster.run()
    assert out == ["7"]                      # 只有根打印，且只打印一次


def test_single_node_root_prints_one():
    cluster, out = make_cluster({"1": []})
    cluster.send_async_message("1", "count", EXTERNAL)
    cluster.run()
    assert out == ["1"]                      # 根没有孩子，收不到任何回复，也必须完成


def test_any_delivery_order():
    for seed in range(20):
        cluster, out = make_cluster(EXAMPLE, seed=seed)
        cluster.send_async_message("1", "count", EXTERNAL)
        cluster.run()
        assert out == ["7"], seed            # 消息到达顺序怎么变都是 7
    for order in ("fifo", "lifo"):
        cluster, out = make_cluster(EXAMPLE, order=order)
        cluster.send_async_message("1", "count", EXTERNAL)
        cluster.run()
        assert out == ["7"], order


def test_chain_counts_depth():
    cluster, out = make_cluster(chain(50))
    cluster.send_async_message("1", "count", EXTERNAL)
    cluster.run()
    assert out == ["50"]                     # 一条链，每层只有一个孩子


def test_count_twice_in_a_row():
    cluster, out = make_cluster(EXAMPLE)
    cluster.send_async_message("1", "count", EXTERNAL)
    cluster.run()
    cluster.send_async_message("1", "count", EXTERNAL)   # 上一次做完再发一次，状态要能重置
    cluster.run()
    assert out == ["7", "7"]


if __name__ == "__main__":
    tests = [
        test_example_count, test_single_node_root_prints_one, test_any_delivery_order,
        test_chain_counts_depth, test_count_twice_in_a_row,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
