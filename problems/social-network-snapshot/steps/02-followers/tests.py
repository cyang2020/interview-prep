from solution import SocialNetwork


def _raises_value_error(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def _network(*users):
    net = SocialNetwork()
    for u in users:
        net.add_user(u)
    return net


def test_add_user_duplicate_raises():
    net = _network("A")
    assert _raises_value_error(lambda: net.add_user("A"))   # 已存在的用户再加，报错


def test_follow_unknown_user_raises():
    net = _network("A")
    assert _raises_value_error(lambda: net.follow("A", "B"))  # 被关注者不存在
    assert _raises_value_error(lambda: net.follow("B", "A"))  # 关注者不存在


def test_follow_is_directional():
    net = _network("A", "B")
    net.follow("A", "B")
    s = net.create_snapshot()
    assert s.is_following("A", "B") is True
    assert s.is_following("B", "A") is False                  # 关注是单向的


def test_self_follow_and_duplicate_follow_are_noops():
    net = _network("A", "B")
    net.follow("A", "A")
    net.follow("A", "B")
    net.follow("A", "B")
    assert net._following["A"] == {"B"}                       # 自己不在集合里，B 只有一份
    s = net.create_snapshot()
    assert s.is_following("A", "A") is False


def test_snapshot_ignores_later_follow():
    net = _network("A", "B", "C")
    net.follow("A", "B")
    s1 = net.create_snapshot()
    net.follow("A", "C")
    assert s1.is_following("A", "B") is True                  # 快照前的关注，看得到
    assert s1.is_following("A", "C") is False                 # 快照后的关注，看不到


def test_two_snapshots_are_independent():
    net = _network("A", "B", "C")
    net.follow("A", "B")
    s1 = net.create_snapshot()
    net.follow("A", "C")
    s2 = net.create_snapshot()
    assert s1.is_following("A", "C") is False
    assert s2.is_following("A", "C") is True                  # 后一个快照包含新关注
    assert s2.is_following("A", "B") is True                  # 也包含旧关注


def test_snapshot_ignores_later_add_user():
    net = _network("A")
    s = net.create_snapshot()
    net.add_user("D")
    net.follow("A", "D")
    assert s.is_following("A", "D") is False                  # D 是快照后加的
    assert s.is_following("D", "A") is False                  # 不存在的用户当作没关注任何人


def test_empty_network_snapshot():
    s = SocialNetwork().create_snapshot()
    assert s.is_following("A", "B") is False


def _example_snapshot():
    # A 关注 B、C；B 关注 C。反向表应为 A:{} B:{A} C:{A, B}
    net = _network("A", "B", "C")
    net.follow("A", "B")
    net.follow("A", "C")
    net.follow("B", "C")
    return net, net.create_snapshot()


def test_get_following():
    _, s = _example_snapshot()
    assert s.get_following("A") == ["B", "C"]                 # 排序后返回
    assert s.get_following("B") == ["C"]
    assert s.get_following("C") == []                         # 没关注任何人


def test_get_followers():
    _, s = _example_snapshot()
    assert s.get_followers("C") == ["A", "B"]                 # 两个人关注 C
    assert s.get_followers("B") == ["A"]
    assert s.get_followers("A") == []                         # 没人关注 A


def test_lists_for_unknown_user_are_empty():
    _, s = _example_snapshot()
    assert s.get_following("Z") == []
    assert s.get_followers("Z") == []


def test_following_and_followers_are_consistent():
    _, s = _example_snapshot()
    for user in ("A", "B", "C"):
        for followee in s.get_following(user):
            assert user in s.get_followers(followee)          # 正向表里有的，反向表里一定有


def test_lists_ignore_later_follow():
    net, s = _example_snapshot()
    net.follow("C", "A")
    assert s.get_followers("A") == []                         # 快照后的关注不进反向表
    assert s.get_following("C") == []                         # 也不进正向表
    assert net.create_snapshot().get_followers("A") == ["C"]  # 新快照才有


if __name__ == "__main__":
    tests = [
        test_add_user_duplicate_raises,
        test_follow_unknown_user_raises,
        test_follow_is_directional,
        test_self_follow_and_duplicate_follow_are_noops,
        test_snapshot_ignores_later_follow,
        test_two_snapshots_are_independent,
        test_snapshot_ignores_later_add_user,
        test_empty_network_snapshot,
        test_get_following,
        test_get_followers,
        test_lists_for_unknown_user_are_empty,
        test_following_and_followers_are_consistent,
        test_lists_ignore_later_follow,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
