# 第二问：medium 按 sizeLimit 切成多个文件

## 这一问要做什么

- KVStore 四个方法不变。改 InMemoryMedium：构造多收一个 size_limit，saveBlob 要把一整串字节切成多个文件存，每个文件连文件头不超过 size_limit 字节。
- getBlob 把这些文件按顺序拼回一整串字节交给 restore，restore 拿到的和第一问一样。

## 核心思路

- KVStore 一行不改，只改 InMemoryMedium：格式归 KVStore，文件归 medium，restore 向 medium 要的仍然是拼好的一整串字节。
- 新字段三个：size_limit；capacity = size_limit − HEADER，HEADER 是 8，每份正文的上限；files 是 dict，文件名到 bytes，模拟一个目录。文件名由 _part_name(i) 生成，part-00000 这种五位补零。
- 每个文件的字节布局：4 字节序号 i + 4 字节总数 total + 最多 capacity 字节正文，文件头算在 size_limit 里。
- saveBlob：先 files.clear()，total = max(1, len(data) 除以 capacity 向上取整)，第 i 份正文是 data 从 i × capacity 到 (i + 1) × capacity 的切片，按字节定长切，不管切到的是半个长度前缀还是半个 emoji。空数据也写 1 份。
- getBlob：files 为空返回 None；读 part-00000 头里的 total，i 从 0 到 total − 1 逐个取，缺一份、头里 index 不等于 i 或 count 不等于 total 都抛 ValueError；正文 part[8:] 按序 b"".join。
- 构造时 size_limit ≤ 8 抛 ValueError：文件头就占 8 字节，正文一个字节都放不下。
- 复杂度：saveBlob、getBlob 各 O(总字节数)；文件数是总字节数除以 capacity 向上取整。

## 思考与反问

- 切分放哪一层？放 medium，KVStore 不动，题面"restore 向 medium 要拼好的完整逻辑字节流"说的就是这个分法。不这么做：KVStore 要知道文件边界，换一种 medium 实现就得改 KVStore。
- 按字节切还是按条切？按字节，saveBlob 就是对 bytes 做定长切片。不这么做：一条 key 加 value 最长 2 × 10⁴ 字节，sizeLimit 可以是 64，一条比一个文件大，按条切放不进任何文件。
- 文件头算不算在 sizeLimit 里？按算，所以 capacity = size_limit − 8。不算的话"每个文件不超过 sizeLimit"就不成立。
- 文件名已有序号，为什么头里还写总数、缺一份为什么报错不是能读多少读多少？丢最后一份只看目录发现不了：part-00000 到 00002 都在，不知道是正好 3 份还是丢了第 4 份；第 0 份头里写 4 就能报 "part 3 of 4 missing"，不报的话拼出截断流交给 _decode 只报 "blob truncated"，看不出丢了哪个文件。
- 重存时文件数变少，旧文件怎么办？saveBlob 开头 files.clear()。不清：上次 4 份这次 1 份，part-00001 到 00003 还留在 files 里，靠 total 能挡住不被拼进去，但真实磁盘上是空间泄漏，用户以为删了的数据其实还在。
- 追问"为什么不让每个文件能独立解析"：独立解析要求每份只放完整条目，一条超过 capacity 的放不进任何文件，得再加续传标记，格式复杂一倍，而且 KVStore 得知道文件边界。作为追问讲，作为实现不选。

## 测试要点

- test_example_from_follow_up：题面 5 条共 207 字节，size_limit 64 切成 4 份，每份不超 64；restore 后 5 条都对，temp_key 被冲掉。
- test_every_part_within_limit_for_many_limits：200 条数据在 size_limit 9、10、17、64、1000、2²⁰ 下每份都不超限，restore 回来的 data 一字不差。
- test_entry_larger_than_one_file：size_limit 16 存一条 2008 字节的 key 加 value，切成 252 份，restore 读回原值。
- test_size_limit_too_small_rejected：size_limit 0 和 8 构造抛 ValueError，9 合法。
- test_resave_smaller_data_leaves_no_stale_parts：先存 200 字节得 4 份，再存 10 字节只剩 1 份，getBlob 是新数据。
- test_missing_part_raises：删中间的 part-00002 或删最后的 part-00003，getBlob 都抛 ValueError。
- test_empty_blob_distinguished_from_never_saved：没存过 getBlob 是 None；saveBlob(b"") 后 files 有 1 份，getBlob 是 b""。
- test_unicode_and_empty_strings_round_trip（改写）：size_limit 64 下 10⁴ 个 emoji 跨 717 个文件，一个 emoji 的 4 字节被切在两份里也原样读回，每份都不超限。

## 更多说明

### 207 字节切成 4 份长什么样

5 条共 207 字节：7 字节流头，加 5 条各 40、39、39、44、38 字节（每条 8 字节两个长度前缀加 key 和 value 本身）。size_limit 64，capacity 56，207 除以 56 向上取整是 4：

| 文件 | 文件头（序号, 总数） | 正文 | 文件大小 |
|---|---|---|---|
| part-00000 | 0, 4 | 流的第 0 到 55 字节 | 64 |
| part-00001 | 1, 4 | 第 56 到 111 字节 | 64 |
| part-00002 | 2, 4 | 第 112 到 167 字节 | 64 |
| part-00003 | 3, 4 | 第 168 到 206 字节，共 39 字节 | 47 |

题面说"约 197 字节、3 或 4 个文件"，prep 站的字节数是估的，文件数一致。getBlob 读 part-00000 头得 total 4，i 从 0 到 3 逐个取正文追加，最后 join 回 207 字节。

### 一条比一个文件大

key 长 1000、value 长 1000，size_limit 16，capacity 8：这一条 2008 字节加 7 字节流头是 2015 字节，切成 252 份。第 0 份正文是 "KV"、版本、条目数 4 字节、key 长度的第 1 个字节；第 1 份是 key 长度的后 3 字节加 key 的前 5 个字符。每份里是什么无所谓，拼回来 _decode 看到的是完整的 2015 字节，这就是按字节切的全部理由。

### emoji 被切在两个文件里

"😀" 的 UTF-8 是 4 字节 F0 9F 98 80。capacity 56 时这 4 字节可能前 2 个在 part-00003 末尾、后 2 个在 part-00004 开头。getBlob 先把所有正文按字节拼成一整串，4 字节重新连在一起，之后 _decode 才按长度切、才 decode；没有任何一步在单个文件上做 UTF-8 解码，所以不会错。

### 重存变少时 files 里有什么

| 操作 | files 里有什么 |
|---|---|
| saveBlob 207 字节 | part-00000 到 part-00003，4 个 |
| 再 saveBlob 25 字节，假设不 clear | part-00000 是新的，part-00001 到 00003 还是旧的 |
| 再 saveBlob 25 字节，先 clear 再写 | 只有 part-00000 |

### 文件头为什么是 8 字节

序号和总数各 4 字节，和第一问所有整数宽度一致，少一种宽度少一种出错可能。各用 2 字节最多 65535 份，但 10⁶ 字节总量除以最小 capacity 1 字节是 10⁶ 份，不够。代价是每份少存 8 字节正文，size_limit 64 时是 12.5%，4096 时是 0.2%。
