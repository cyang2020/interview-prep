# 第一问：自定义二进制格式，shutdown / restore

## 这一问要做什么

- 写 KVStore 的 put、get、shutdown、restore：put 写一项，get 读一项没有返回 ""，shutdown 把整张表变成一串字节存进 medium 然后关闭实例，restore 从 medium 读回字节整个替换内存里的表。
- 字节格式自己定，不许用 JSON、pickle；空串、中文、emoji 存进去再读出来必须一模一样。shutdown 之后再 put、get 要抛错。
- InMemoryMedium 题目给好：saveBlob 存一串字节，getBlob 取回最近存的那串，没存过返回 None。

## 核心思路

- KVStore 两个字段：data 是 dict，key 到 value，get 查它；closed 是 bool，四个公开方法开头都先过 _check_open。InMemoryMedium 一个字段 blob，None 表示从没存过。
- 字节布局：流头 7 字节 = MAGIC "KV"（2）+ VERSION 1（1）+ 条目数（4）；每条 = key 字节数（4）+ key 的 UTF-8 字节 + value 字节数（4）+ value 的 UTF-8 字节。所有整数都是 4 字节大端，写用 _u32，读用 read_u32。
- 字符串用长度前缀不用分隔符，长度记 UTF-8 字节数不是字符数，encode 和 decode 都带 surrogatepass；所以空串、中文、emoji、NUL、单独代理项都不需要转义，原样往返。
- put：data[key] = value，已有就覆盖。get：data.get(key, "")。shutdown：saveBlob(_encode()) 成功后才 closed = True，写失败实例还开着能重试。
- restore：getBlob 返回 None 或 b"" 就 data = {}；否则 data = _decode(blob)，整体替换不是 update，_decode 抛错时 data 不动。
- _decode 靠 _Reader：pos 是游标，read(n) 统一检查 pos + n 不超过 len(blob)，不够抛 ValueError；魔数不是 "KV" 或版本不是 1 抛 ValueError；读完 expect_end 要求 pos 正好等于 len(blob)，多出字节也算坏。
- 复杂度：put、get O(1)；shutdown、restore 各扫一遍全部字节 O(总字节数)。_encode 用 list 收集再 b"".join，不用 bytes += 拼，后者每次复制整串是 O(n²)。

## 思考与反问

- 字符串之间怎么分界？按长度前缀，_encode 里每个字符串前写 _u32(len(raw))。不这么做：用逗号分隔，value 里本身有逗号就得转义，而且空串和"这一项不存在"分不清。
- 长度用 2 字节还是 4 字节？按 4 字节，U32 = 4。题面上限 10⁴ 个 emoji 是 40000 字节，2 字节够用，但格式定了很难改，多 2 字节换 4GB 上限；追问省空间就答 varint，小数只占 1 字节。
- closed 后哪些方法抛错？题面只说 put、get，我让 restore、shutdown 也抛 RuntimeError，关了的实例不该再被读回数据继续用；面试官要 restore 能用，删 restore 开头的 _check_open 一行。
- restore 是整体替换还是合并进现有 data？按替换，self.data = self._decode(blob)。题面例子里 restore 前 put 的 key4 之后必须返回 ""，合并就错了。
- blob 非空但格式坏，抛错还是当空表？按抛 ValueError 且 data 不动。不这么做：少一个字节的 blob 静默变成"少了一条"，比抛错难查得多。
- 追问"为什么不用 JSON 或 pickle"：题面禁；JSON 要转义引号和控制字符，中文膨胀成 \uXXXX 六个字符，还得写解析器；pickle 别的语言读不了，反序列化不可信数据能执行代码。长度前缀不转义、跨语言、解析就是读长度加切片。

## 测试要点

- test_example_from_problem：题面例子逐条核对；新建 store2 不自动 restore，get 返回 ""；restore 冲掉没保存的 key4。
- test_put_overwrites：同 key 第二次 put 覆盖，get 返回新值。
- test_unicode_and_empty_strings_round_trip：空 key 空 value、中文、emoji、含 NUL 换行逗号引号的串、单独代理项、10⁴ 个 emoji，shutdown 再 restore 每对一样，条数不多不少。
- test_byte_layout_is_our_own_format：put("key1", "value1") 后 getBlob 正好是 25 字节，7 字节流头 + 4 + 4 + 4 + 6。
- test_closed_store_rejects_everything：shutdown 后 put、get、restore、shutdown 四个都抛 RuntimeError。
- test_restore_with_nothing_saved_gives_empty_store：getBlob 返回 None 或 b""，restore 后都变空表，没保存的 put 丢掉。
- test_restore_then_continue_working：restore 不关闭实例，之后能 put、再 shutdown，第三个实例 restore 两条都在。
- test_corrupt_blob_raises_and_keeps_data：少一字节、多一字节、魔数 "XX"、版本 2 四种 blob 都抛 ValueError，内存里的 keep 不动。

## 更多说明

### put("key1", "value1") 后的 25 字节

| 偏移 | 字节（十六进制） | 意思 |
|---|---|---|
| 0 到 1 | 4B 56 | "KV" |
| 2 | 01 | 版本 1 |
| 3 到 6 | 00 00 00 01 | 1 条 |
| 7 到 10 | 00 00 00 04 | key 占 4 字节 |
| 11 到 14 | 6B 65 79 31 | "key1" |
| 15 到 18 | 00 00 00 06 | value 占 6 字节 |
| 19 到 24 | 76 61 6C 75 65 31 | "value1" |

restore 反着来：读 2 字节核对 "KV"，读 1 字节核对版本 1，读 4 字节得条目数 1，循环 1 次：读 4 得 4、切 4 字节解码成 "key1"，读 4 得 6、切 6 字节解码成 "value1"，最后 pos 必须正好停在 25。

### 字节数和字符数

| 字符串 | 字符数 len(s) | UTF-8 字节数 len(s.encode()) |
|---|---|---|
| "key1" | 4 | 4 |
| "名字" | 2 | 6 |
| "😀" | 1 | 4 |
| "" | 0 | 0 |

长度前缀必须记字节数：一个字符占 1 到 4 字节，记字符数的话 decode 时不知道要切多少字节。put("", "") 写出 8 个 00，读回两个长度 0，切出两个空 bytes，解码成两个空串。

### 大端是什么意思

4 字节整数 1 有两种摆法：00 00 00 01 是大端，高位在前；01 00 00 00 是小端，低位在前。两种都行，但写和读必须一致，文件格式和网络协议习惯用大端。代码里写是 n.to_bytes(4, "big")，读是 int.from_bytes(b, "big")。

### 单独的代理项（lone surrogate）

Python 字符串里可以出现 "\ud800" 这种单独的代理项：正常它必须成对出现，合起来才表示一个 emoji 之类的字符，单独一个不是合法 Unicode 文本，但是合法的 Python str。s.encode("utf-8") 默认遇到它抛 UnicodeEncodeError；加 errors="surrogatepass" 会原样编成 3 字节，decode 同样加 surrogatepass 就原样读回。一行成本换来"任何 str 都能往返"，面试时提一句就行。
