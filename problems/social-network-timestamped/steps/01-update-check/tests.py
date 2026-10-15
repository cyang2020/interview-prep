from solution import FollowGraph


def test_never_followed():
    g = FollowGraph()
    assert g.check("A", "B", 0) is False     # 没有任何历史
    assert g.check("A", "B", 100) is False   # 任何时刻都不关注


def test_follow_then_time_boundaries():
    g = FollowGraph()
    g.update("A", "B", 5)
    assert g.check("A", "B", 4) is False     # 早于关注时刻
    assert g.check("A", "B", 5) is True      # 恰好等于关注时刻，闭区间
    assert g.check("A", "B", 100) is True    # 之后一直关注


def test_follow_unfollow_refollow():
    g = FollowGraph()
    g.update("A", "B", 1)
    g.update("A", "B", 5, following=False)
    g.update("A", "B", 9)
    assert g.check("A", "B", 0) is False     # 第一次关注之前
    assert g.check("A", "B", 3) is True      # 关注段
    assert g.check("A", "B", 5) is False     # 取消那一刻起不关注
    assert g.check("A", "B", 7) is False     # 取消段
    assert g.check("A", "B", 9) is True      # 再关注那一刻起
    assert g.check("A", "B", 10) is True


def test_direction():
    g = FollowGraph()
    g.update("A", "B", 1)
    assert g.check("B", "A", 2) is False     # 关注是单向的


def test_pairs_independent():
    g = FollowGraph()
    g.update("A", "B", 1)
    g.update("A", "M", 3)
    g.update("A", "B", 5, following=False)
    assert g.check("A", "M", 6) is True      # 取消 B 不影响 M
    assert g.check("A", "B", 6) is False


def test_out_of_order_updates():
    g = FollowGraph()
    g.update("A", "B", 9)
    g.update("A", "B", 1)
    g.update("A", "B", 5, following=False)
    assert g.check("A", "B", 3) is True      # 乱序插入后历史仍按时间排好
    assert g.check("A", "B", 7) is False
    assert g.check("A", "B", 9) is True


def test_same_time_last_write_wins():
    g = FollowGraph()
    g.update("A", "B", 5)
    g.update("A", "B", 5, following=False)
    assert g.check("A", "B", 5) is False     # 同一时刻两条，后到的生效
    assert g.check("A", "B", 6) is False


def test_self_follow_ignored():
    g = FollowGraph()
    g.update("A", "A", 1)
    assert g.check("A", "A", 2) is False     # 自己关注自己不记录


def test_check_does_not_create_state():
    g = FollowGraph()
    g.check("X", "Y", 1)
    assert "X" not in g._history             # 查询不能顺手建出空记录


if __name__ == "__main__":
    tests = [
        test_never_followed,
        test_follow_then_time_boundaries,
        test_follow_unfollow_refollow,
        test_direction,
        test_pairs_independent,
        test_out_of_order_updates,
        test_same_time_last_write_wins,
        test_self_follow_ignored,
        test_check_does_not_create_state,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
