from solution import WorkQueue


def test_state_machine():
    q = WorkQueue()
    assert q.enqueue("A", timeout=10, max_retry=1)
    assert not q.enqueue("A", timeout=10, max_retry=1)  # 重复 id 拒绝

    assert q.pass_("A") is False     # 没领走就 pass，拒绝
    assert q.fail("A") is False      # 没领走就 fail，拒绝

    assert q.reserve("A") == "A"
    assert q.reserve("A") is None    # 已被领走，别人领不到

    assert q.fail("A")               # 失败回 ready
    assert q.reserve("A") == "A"     # 能再领
    assert q.pass_("A")              # 完成
    assert q.pass_("A") is False     # 重复 pass 拒绝
    assert q.fail("A") is False      # 完成后 fail 拒绝
    assert q.reserve("A") is None    # 完成后领不到
    assert q.get_dlq() == []


def test_reserve_next():
    q = WorkQueue()
    q.enqueue("A", 10, 1)
    q.enqueue("B", 10, 1)
    q.enqueue("C", 10, 1)
    assert q.reserve("B") == "B"     # 指名领走排在中间的
    assert q.reserve() == "A"        # 不指名，按顺序发下一个
    assert q.reserve() == "C"        # B 留在队列里的旧条目被跳过
    assert q.reserve() is None


if __name__ == "__main__":
    tests = [test_state_machine, test_reserve_next]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
