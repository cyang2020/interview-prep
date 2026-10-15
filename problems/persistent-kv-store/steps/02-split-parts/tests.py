from solution import InMemoryMedium, KVStore


def assert_parts_within_limit(medium):
    assert medium.files, "保存后至少有 1 个文件"
    for name, content in medium.files.items():
        assert len(content) <= medium.size_limit, f"{name} 超过 size_limit"   # 文件头也算在内


# ---- 第一问的测试，改成 InMemoryMedium(64)：每一条都会被切开存 ----
def test_example_from_problem():
    medium = InMemoryMedium(64)
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
    store = KVStore(InMemoryMedium(64))
    store.put("a", "1")
    store.put("a", "2")
    assert store.get("a") == "2"                 # 同 key 覆盖，不是追加


def test_unicode_and_empty_strings_round_trip():
    # 第二问题面收窄到 ASCII，实现不需要收窄，第一问的往返测试照跑
    medium = InMemoryMedium(64)
    store = KVStore(medium)
    pairs = [
        ("", ""),                          # 空 key 空 value
        ("empty-value", ""),
        ("名字", "张三"),
        ("emoji", "😀🎉"),
        ("mixed", "a中😀\n\t\x00,|\""),     # 换行、制表、NUL、逗号、竖线、引号都不需要转义
        ("lone-surrogate", "\ud800"),      # 单独的代理项也要原样往返
        ("long", "😀" * 10_000),           # 10⁴ 个字符，UTF-8 占 40000 字节，跨 700 多个文件
    ]
    for k, v in pairs:
        store.put(k, v)
    store.shutdown()
    assert_parts_within_limit(medium)

    back = KVStore(medium)
    back.restore()
    for k, v in pairs:
        assert back.get(k) == v                  # 每一对都精确恢复，哪怕一个 emoji 的 4 字节被切在两个文件里
    assert len(back.data) == len(pairs)          # 没多没少


def test_byte_layout_is_our_own_format():
    medium = InMemoryMedium(64)
    store = KVStore(medium)
    store.put("key1", "value1")
    store.shutdown()
    expected = (
        b"KV" + b"\x01" + (1).to_bytes(4, "big")      # 魔数、版本、1 条
        + (4).to_bytes(4, "big") + b"key1"            # key 字节数 + key
        + (6).to_bytes(4, "big") + b"value1"          # value 字节数 + value
    )
    assert medium.getBlob() == expected               # 拼回来的逻辑流和第一问一字不差


def test_closed_store_rejects_everything():
    store = KVStore(InMemoryMedium(64))
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
    store = KVStore(InMemoryMedium(64))               # getBlob 返回 None
    store.put("a", "1")
    store.restore()
    assert store.get("a") == ""                       # 没存过：变空表，未保存的 put 丢弃

    medium = InMemoryMedium(64)
    medium.saveBlob(b"")                              # 存过但是空
    store = KVStore(medium)
    store.put("a", "1")
    store.restore()
    assert store.get("a") == ""


def test_restore_then_continue_working():
    medium = InMemoryMedium(64)
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
    medium = InMemoryMedium(64)
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


# ---- 第二问的测试 ----
def test_example_from_follow_up():
    medium = InMemoryMedium(64)
    store1 = KVStore(medium)
    store1.put("user1", "Alice_Johnson_from_New_York")
    store1.put("user2", "Bob_Smith_from_Los_Angeles")
    store1.put("user3", "Charlie_Brown_from_Chicago")
    store1.put("user4", "Diana_Prince_from_San_Francisco")
    store1.put("user5", "Eve_Williams_from_Seattle")
    assert store1.get("user1") == "Alice_Johnson_from_New_York"
    assert store1.get("user3") == "Charlie_Brown_from_Chicago"
    assert store1.get("user_nonexistent") == ""
    store1.shutdown()
    assert len(medium.getBlob()) == 207               # 7 字节流头 + 40 + 39 + 39 + 44 + 38
    assert len(medium.files) == 4                     # 正文每份 56 字节，207 / 56 向上取整
    assert_parts_within_limit(medium)

    store2 = KVStore(medium)
    assert store2.get("user1") == ""                  # 还没 restore
    store2.put("temp_key", "temp_value")
    store2.restore()
    assert store2.get("user1") == "Alice_Johnson_from_New_York"
    assert store2.get("user2") == "Bob_Smith_from_Los_Angeles"
    assert store2.get("user5") == "Eve_Williams_from_Seattle"
    assert store2.get("temp_key") == ""               # 没保存过的 put 被 restore 冲掉


def test_every_part_within_limit_for_many_limits():
    pairs = {f"k{i}": "v" * (i % 37) for i in range(200)}
    for limit in (9, 10, 17, 64, 1000, 1 << 20):      # 9 是最小合法值：正文每份 1 字节
        medium = InMemoryMedium(limit)
        s = KVStore(medium)
        for k, v in pairs.items():
            s.put(k, v)
        s.shutdown()
        assert_parts_within_limit(medium)
        back = KVStore(medium)
        back.restore()
        assert back.data == pairs                     # 不管切多碎，拼回来都一样


def test_entry_larger_than_one_file():
    medium = InMemoryMedium(16)                       # 正文每份 8 字节
    s = KVStore(medium)
    s.put("k" * 1000, "v" * 1000)                     # 一条 2008 字节，一个文件装不下
    s.shutdown()
    assert len(medium.files) > 250                    # 跨 250 多个文件
    assert_parts_within_limit(medium)
    back = KVStore(medium)
    back.restore()
    assert back.get("k" * 1000) == "v" * 1000


def test_size_limit_too_small_rejected():
    for bad in (0, 8):
        try:
            InMemoryMedium(bad)
            assert False, "no room for body must raise"
        except ValueError:
            pass                                      # 文件头就占 8 字节，正文一个字节都放不下
    InMemoryMedium(9)                                 # 正文 1 字节，合法


def test_resave_smaller_data_leaves_no_stale_parts():
    medium = InMemoryMedium(64)
    medium.saveBlob(b"x" * 200)
    assert len(medium.files) == 4                     # 200 / 56 向上取整
    medium.saveBlob(b"y" * 10)
    assert len(medium.files) == 1                     # 旧的 part-00001 到 00003 没残留
    assert medium.getBlob() == b"y" * 10


def test_missing_part_raises():
    medium = InMemoryMedium(64)
    medium.saveBlob(b"x" * 200)
    del medium.files["part-00002"]                    # 中间丢一份
    try:
        medium.getBlob()
        assert False, "missing part must raise"
    except ValueError:
        pass
    medium.saveBlob(b"x" * 200)
    del medium.files["part-00003"]                    # 丢最后一份：只看目录发现不了，靠头里的"一共几份"
    try:
        medium.getBlob()
        assert False, "missing last part must raise"
    except ValueError:
        pass


def test_empty_blob_distinguished_from_never_saved():
    medium = InMemoryMedium(64)
    assert medium.getBlob() is None                   # 从没存过
    medium.saveBlob(b"")
    assert len(medium.files) == 1                     # 空数据也写 1 份
    assert medium.getBlob() == b""                    # 存过但是空


if __name__ == "__main__":
    tests = [
        test_example_from_problem, test_put_overwrites,
        test_unicode_and_empty_strings_round_trip, test_byte_layout_is_our_own_format,
        test_closed_store_rejects_everything, test_restore_with_nothing_saved_gives_empty_store,
        test_restore_then_continue_working, test_corrupt_blob_raises_and_keeps_data,
        test_example_from_follow_up, test_every_part_within_limit_for_many_limits,
        test_entry_larger_than_one_file, test_size_limit_too_small_rejected,
        test_resave_smaller_data_leaves_no_stale_parts, test_missing_part_raises,
        test_empty_blob_distinguished_from_never_saved,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
