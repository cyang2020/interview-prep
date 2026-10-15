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


def _example_graph():
    # 时刻 1..9 的事件，推荐测试共用这一张图
    g = FollowGraph()
    g.update("A", "B", 1)
    g.update("A", "M", 2)
    g.update("B", "C", 3)
    g.update("B", "D", 4)
    g.update("M", "C", 5)
    g.update("B", "A", 6)                    # B 回关 A，第二层会出现 A 自己
    g.update("M", "B", 7)                    # M 关注 B，第二层会出现 A 已关注的 B
    g.update("A", "D", 8)                    # A 直接关注 D，D 不再是候选
    g.update("B", "C", 9, following=False)   # B 取消关注 C，C 少一个中间人
    return g


def test_following_at_respects_time():
    g = _example_graph()
    assert g.following_at("A", 0) == {}                       # 还没关注任何人
    assert g.following_at("A", 1) == {"B": 1}                 # 恰好第 1 秒
    assert g.following_at("A", 8) == {"B": 1, "M": 2, "D": 8} # 值是这段关注开始的时刻
    assert g.following_at("B", 9) == {"D": 4, "A": 6}         # C 已取消，不在列表里


def test_recommend_counts_intermediaries():
    g = _example_graph()
    assert g.recommend("A", 5) == ["C", "D"]  # C 有 B、M 两个中间人，D 只有 B


def test_recommend_excludes_self_and_already_followed():
    g = _example_graph()
    assert g.recommend("A", 7) == ["C", "D"]  # 第二层出现的 A（自己）和 B（已关注）被剔除


def test_recommend_excludes_newly_followed():
    g = _example_graph()
    assert g.recommend("A", 8) == ["C"]       # 第 8 秒 A 直接关注了 D，D 不再推荐


def test_recommend_drops_count_after_unfollow():
    g = _example_graph()
    assert g.recommend("A", 9) == ["C"]       # B 取消关注 C 后 C 仍由 M 到达，计数变 1
    assert g.recommend("A", 2) == []          # 第 2 秒 B、M 还没关注任何人


def test_recommend_tie_break_by_recency():
    g = FollowGraph()
    g.update("A", "B", 1)
    g.update("A", "M", 2)
    g.update("B", "X", 3)
    g.update("M", "Y", 4)
    assert g.recommend("A", 4) == ["Y", "X"]  # 都是 1 个中间人，指向 Y 的边更新，排前面


def test_recommend_top_k():
    g = _example_graph()
    assert g.recommend("A", 5, k=1) == ["C"]  # 只要前 1 个
    assert g.recommend("A", 5, k=5) == ["C", "D"]  # k 大于候选数，返回全部


def test_recommend_unknown_user():
    g = _example_graph()
    assert g.recommend("Z", 9) == []          # 没有任何关注的人，推荐为空


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
        test_following_at_respects_time,
        test_recommend_counts_intermediaries,
        test_recommend_excludes_self_and_already_followed,
        test_recommend_excludes_newly_followed,
        test_recommend_drops_count_after_unfollow,
        test_recommend_tie_break_by_recency,
        test_recommend_top_k,
        test_recommend_unknown_user,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
