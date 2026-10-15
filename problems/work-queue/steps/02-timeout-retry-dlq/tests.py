from solution import WorkQueue


class FakeClock:
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


# ---- 第一问的测试，按第二问的接口改写：reserve 返回 (job_id, token)，pass_/fail 带 token ----
def test_state_machine():
    q = WorkQueue(clock=FakeClock())
    assert q.enqueue("A", timeout=10, max_retry=5)
    assert not q.enqueue("A", timeout=10, max_retry=5)   # 重复 id 拒绝

    assert q.pass_("A", 1) is False      # 没领走就 pass，拒绝
    assert q.fail("A", 1) is False       # 没领走就 fail，拒绝

    _, t1 = q.reserve("A")
    assert q.reserve("A") is None        # 已被领走，别人领不到

    assert q.fail("A", t1)               # 失败回 ready
    _, t2 = q.reserve("A")               # 能再领
    assert q.pass_("A", t2)              # 完成
    assert q.pass_("A", t2) is False     # 重复 pass 拒绝
    assert q.fail("A", t2) is False      # 完成后 fail 拒绝
    assert q.reserve("A") is None        # 完成后领不到
    assert q.get_dlq() == []


def test_reserve_next():
    q = WorkQueue(clock=FakeClock())
    q.enqueue("A", 10, 1)
    q.enqueue("B", 10, 1)
    q.enqueue("C", 10, 1)
    assert q.reserve("B")[0] == "B"      # 指名领走排在中间的
    assert q.reserve()[0] == "A"         # 不指名，按顺序发下一个
    assert q.reserve()[0] == "C"         # B 留在队列里的旧条目被跳过
    assert q.reserve() is None


# ---- 第二问的测试 ----
def test_fail_twice_goes_to_dlq_once():
    q = WorkQueue(clock=FakeClock())
    q.enqueue("A", timeout=10, max_retry=1)        # 总共 2 次尝试

    _, t1 = q.reserve("A")
    assert q.fail("A", t1)                         # 第 1 次失败，回 ready
    assert q.get_dlq() == []

    _, t2 = q.reserve("A")
    assert q.fail("A", t2)                         # 第 2 次失败，进 DLQ
    assert q.get_dlq() == ["A"]

    assert q.reserve("A") is None                  # dead 的领不到
    assert q.pass_("A", t2) is False               # dead 的 pass 拒绝
    assert q.fail("A", t2) is False                # dead 的 fail 拒绝
    assert q.get_dlq() == ["A"]                    # 只进一次


def test_timeout_then_late_pass_rejected():
    clock = FakeClock()
    q = WorkQueue(clock=clock)
    q.enqueue("A", timeout=10, max_retry=1)

    _, t1 = q.reserve("A")                         # 第 0 秒，worker 1 领走，到期第 10 秒
    clock.advance(12)
    _, t2 = q.reserve("A")                         # 第 12 秒，worker 2 领走（先把过期的处理掉）
    assert t2 != t1

    clock.advance(3)
    assert q.pass_("A", t1) is False               # 第 15 秒，worker 1 迟到的 pass 被拒
    assert q.pass_("A", t2)                        # worker 2 的 pass 算数
    assert q.get_dlq() == []


def test_timeout_consumes_attempts():
    clock = FakeClock()
    q = WorkQueue(clock=clock)
    q.enqueue("A", timeout=10, max_retry=1)

    q.reserve("A")                                 # 第 0 秒，第 1 次
    clock.advance(10)
    assert q.reserve("A") is not None              # 第 10 秒到期，回 ready，立刻再领，第 2 次
    clock.advance(10)
    assert q.get_dlq() == ["A"]                    # 第 20 秒再到期，次数用完


def test_stale_heap_entry_ignored():
    clock = FakeClock()
    q = WorkQueue(clock=clock)
    q.enqueue("A", timeout=10, max_retry=1)

    _, t1 = q.reserve("A")                         # 第 0 秒，堆里 (10, A, 1)
    clock.advance(5)
    assert q.fail("A", t1)                         # 第 5 秒失败，回 ready
    clock.advance(1)
    _, t2 = q.reserve("A")                         # 第 6 秒再领，堆里新增 (16, A, 2)
    clock.advance(4)
    assert q.get_dlq() == []                       # 第 10 秒，(10, A, 1) 弹出，token 不对，丢掉
    clock.advance(1)
    assert q.pass_("A", t2)                        # 第 11 秒，worker 2 的领取没被误伤


def test_dlq_only_has_exhausted_jobs():
    q = WorkQueue(clock=FakeClock())
    for j in ["A", "B", "C"]:
        q.enqueue(j, timeout=10, max_retry=0)      # 只有 1 次尝试
    _, ta = q.reserve("A")
    q.fail("A", ta)
    q.reserve("C")
    assert q.get_dlq() == ["A"]                    # B 还是 ready，C 正在 reserved


if __name__ == "__main__":
    tests = [
        test_state_machine, test_reserve_next,
        test_fail_twice_goes_to_dlq_once, test_timeout_then_late_pass_rejected,
        test_timeout_consumes_attempts, test_stale_heap_entry_ignored,
        test_dlq_only_has_exhausted_jobs,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
