from solution import InMemoryMedium, KVStore


def test_example_from_problem():
    medium = InMemoryMedium()
    store1 = KVStore(medium)
    store1.put("key1", "value1")
    store1.put("key2", "value2_is_longer")
    store1.put("key3", "value3")
    assert store1.get("key1") == "value1"
    assert store1.get("key4") == ""              # 没有的 key 返回空串
    store1.shutdown()

    store2 = KVStore(medium)
    assert store2.get("key1") == ""              # 还没 restore，是空表
    store2.put("key4", "value4")
    store2.restore()
    assert store2.get("key1") == "value1"
    assert store2.get("key2") == "value2_is_longer"
    assert store2.get("key3") == "value3"
    assert store2.get("key4") == ""              # 没保存过的 put 被 restore 冲掉


def test_put_overwrites():
    store = KVStore(InMemoryMedium())
    store.put("a", "1")
    store.put("a", "2")
    assert store.get("a") == "2"                 # 同 key 覆盖，不是追加


def test_unicode_and_empty_strings_round_trip():
    medium = InMemoryMedium()
    store = KVStore(medium)
    pairs = [
        ("", ""),                          # 空 key 空 value
        ("empty-value", ""),
        ("名字", "张三"),
        ("emoji", "😀🎉"),
        ("mixed", "a中😀\n\t\x00,|\""),     # 换行、制表、NUL、逗号、竖线、引号都不需要转义
        ("lone-surrogate", "\ud800"),      # 单独的代理项也要原样往返
        ("long", "😀" * 10_000),           # 10⁴ 个字符，UTF-8 占 40000 字节
    ]
    for k, v in pairs:
        store.put(k, v)
    store.shutdown()

    back = KVStore(medium)
    back.restore()
    for k, v in pairs:
        assert back.get(k) == v                  # 每一对都精确恢复
    assert len(back.data) == len(pairs)          # 没多没少


def test_byte_layout_is_our_own_format():
    medium = InMemoryMedium()
    store = KVStore(medium)
    store.put("key1", "value1")
    store.shutdown()
    expected = (
        b"KV" + b"\x01" + (1).to_bytes(4, "big")      # 魔数、版本、1 条
        + (4).to_bytes(4, "big") + b"key1"            # key 字节数 + key
        + (6).to_bytes(4, "big") + b"value1"          # value 字节数 + value
    )
    assert medium.getBlob() == expected               # 25 字节，和 notes 里的表一致


def test_closed_store_rejects_everything():
    store = KVStore(InMemoryMedium())
    store.put("a", "1")
    store.shutdown()
    calls = [lambda: store.put("b", "2"), lambda: store.get("a"),
             lambda: store.restore(), lambda: store.shutdown()]
    for call in calls:
        try:
            call()
            assert False, "closed store must raise"
        except RuntimeError:
            pass                                      # 关闭后四个方法都抛错


def test_restore_with_nothing_saved_gives_empty_store():
    store = KVStore(InMemoryMedium())                 # getBlob 返回 None
    store.put("a", "1")
    store.restore()
    assert store.get("a") == ""                       # 没存过：变空表，未保存的 put 丢弃

    medium = InMemoryMedium()
    medium.saveBlob(b"")                              # 存过但是空
    store = KVStore(medium)
    store.put("a", "1")
    store.restore()
    assert store.get("a") == ""


def test_restore_then_continue_working():
    medium = InMemoryMedium()
    s1 = KVStore(medium)
    s1.put("a", "1")
    s1.shutdown()
    s2 = KVStore(medium)
    s2.restore()
    s2.put("b", "2")                                  # restore 不关闭实例，能继续用
    s2.shutdown()                                     # 再存一次，覆盖上一份
    s3 = KVStore(medium)
    s3.restore()
    assert s3.get("a") == "1" and s3.get("b") == "2"


def test_corrupt_blob_raises_and_keeps_data():
    medium = InMemoryMedium()
    s1 = KVStore(medium)
    s1.put("a", "1")
    s1.shutdown()
    good = medium.getBlob()

    bad_blobs = [good[:-1],                           # 少一个字节
                 good + b"\x00",                      # 多一个字节
                 b"XX" + good[2:],                    # 魔数不对
                 good[:2] + b"\x02" + good[3:]]       # 版本不认识
    for bad in bad_blobs:
        medium.saveBlob(bad)
        s = KVStore(medium)
        s.put("keep", "me")
        try:
            s.restore()
            assert False, "corrupt blob must raise"
        except ValueError:
            pass
        assert s.get("keep") == "me"                  # 抛错时内存数据不动


if __name__ == "__main__":
    tests = [
        test_example_from_problem, test_put_overwrites,
        test_unicode_and_empty_strings_round_trip, test_byte_layout_is_our_own_format,
        test_closed_store_rejects_everything, test_restore_with_nothing_saved_gives_empty_store,
        test_restore_then_continue_working, test_corrupt_blob_raises_and_keeps_data,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
