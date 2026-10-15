# 整体思路

**一句话。** 内存里就是一个 dict；格式用"长度前缀 + UTF-8 字节"，每个字符串先写它占几个字节再写字节本身，所以空串、任意 Unicode、任何特殊字符都不需要转义；shutdown 和 restore 是同一个格式的正反两个方向；第二问只在 medium 里把一整串字节按字节切成多个文件，KVStore 一行不改。

**两问是叠加关系。** 第一问定格式、定关闭和替换的规矩。第二问把 medium 换成会切文件的实现。关键是分层：格式是 KVStore 的事，文件是 medium 的事。题面说 restore 向 medium 要"拼好的完整逻辑字节流"，就是在提示这个分法。第二问的 diff 只有 InMemoryMedium 一个类。

## KVStore 的状态转移

实例只有两个状态：open 和 closed。

| 当前状态 | 触发 | 条件 | 结果 |
|---|---|---|---|
| open | put | | data[key] = value，已有就覆盖 |
| open | get | key 在 | 返回 value |
| open | get | key 不在 | 返回 "" |
| open | shutdown | | 编码 data 写入 medium，变 closed |
| open | restore | medium 返回 None 或空 | data 变空 dict |
| open | restore | medium 返回非空且格式对 | 解码结果整体替换 data |
| open | restore | medium 返回非空但格式坏 | 抛 ValueError，data 不动 |
| closed | put / get / restore / shutdown | | 抛 RuntimeError |

## 字节格式

这是整道题的核心不变量：写出去的每个字节在哪、是什么，读的时候按同一张表反着来。

| 位置 | 长度 | 内容 |
|---|---|---|
| 流头 | 2 字节 | 魔数 "KV" |
| 流头 | 1 字节 | 版本号，现在是 1 |
| 流头 | 4 字节 | 条目数 n，大端无符号 |
| 每条 | 4 字节 | key 的 UTF-8 字节数 |
| 每条 | 变长 | key 的 UTF-8 字节 |
| 每条 | 4 字节 | value 的 UTF-8 字节数 |
| 每条 | 变长 | value 的 UTF-8 字节 |

第二问每个文件：

| 位置 | 长度 | 内容 |
|---|---|---|
| 文件头 | 4 字节 | 这是第几份，从 0 起 |
| 文件头 | 4 字节 | 一共几份 |
| 正文 | 最多 sizeLimit − 8 | 上面那条流的一段 |

## 数据结构

| 结构 | 存什么 | 回答什么问题 | 第几问出现 |
|---|---|---|---|
| KVStore.data（dict） | key 到 value | get 返回什么 | 一 |
| KVStore.closed（bool） | 是否已 shutdown | 四个方法该不该抛错 | 一 |
| _Reader.pos（int） | 解码读到第几个字节 | 下一个字段从哪读、字节够不够 | 一 |
| InMemoryMedium.blob（bytes 或 None） | 最近一次 saveBlob 的字节 | getBlob 返回什么 | 一 |
| InMemoryMedium.files（dict） | 文件名到文件内容 | 分了几份、每份多大、缺没缺 | 二 |

## 面试节奏

- 前 3 分钟定口径，不要等面试官问：字符串用长度前缀不用分隔符；长度 4 字节大端；UTF-8；closed 后四个方法全抛错；restore 整体替换不是合并；格式坏了抛错不当空表。
- 写代码顺序：Medium 接口和 InMemoryMedium 两个类先放上去；KVStore 的 data 和 closed 两个字段，put 和 get；_encode；带游标的 _Reader 和 _decode；最后 shutdown 和 restore 各调一下。
- 留 5 分钟写三个测试：题面例子逐条核对；空串加 emoji 往返；shutdown 后 put 抛错，并且 restore 把没保存的 put 冲掉。
- follow-up 先说三句话：切分放 medium 里，KVStore 不动；按字节切不按条切，因为一条可以比一个文件大；每个文件带序号和总数，缺一份能发现。再改 saveBlob 和 getBlob，补三个测试：每份不超过 sizeLimit、往返一致、重存变少时旧文件不残留。

## 常见追问

| 追问 | 答法 |
|---|---|
| 为什么不用 JSON 或 pickle | 题面禁止。JSON 要转义引号和控制字符，非 ASCII 会膨胀成 \uXXXX，还得写解析器；pickle 别的语言读不了，反序列化不可信数据能执行代码。长度前缀不转义、不依赖语言、解析就是读长度加切片 |
| 长度为什么用 4 字节不用 2 字节 | 按题面约束 2 字节刚好够（10⁴ 个 emoji 是 40000 字节，小于 65535），但格式一旦定了很难改，多花 2 字节换来 4GB 上限。要省空间可以换变长整数 varint，小数用 1 字节 |
| 文件损坏怎么发现 | 流尾加 4 字节 CRC32，restore 先校验再解析。第二问每个文件头再放一个 CRC，能定位到哪一份坏了 |
| shutdown 写到一半进程崩了 | 先写到临时名，全部写完再改名替换，改名是原子的。第二问先写新一组文件，最后写一个 manifest 文件指向它们，替换 manifest 才算生效 |
| 数据大到内存放不下 | _encode 改成逐条产出字节的生成器，medium 边收边写；_decode 改成从文件按需读，不要一次 getBlob 全读进来 |
| put 很频繁，每次 shutdown 都全量写太慢 | 改成追加日志：每次 put 追加一条记录，restore 顺序重放，后写的覆盖先写的。日志太长时重写成一份快照，这叫 compaction |
| 要支持 delete | 内存里 dict.pop。全量快照格式不需要额外记录。追加日志格式才要写一条删除记录，叫 tombstone，重放时遇到就从 dict 里删 |
| 以后格式要改 | 流头已经有版本字节。restore 读到 1 走现在的解析，读到 2 走新的。新字段加在条目尾部，老版本的读取器按长度跳过 |
| 多线程同时 put 和 shutdown | 四个公开方法整个加一把锁。不加的话 _encode 遍历 dict 时别人 put 会报"dict changed size during iteration" |
| 第二问能不能并行读多个文件 | 能，每份独立读入内存，按序号放到对应位置再拼。但解析必须拼完才做，因为一条记录可能跨两个文件 |
| 为什么不让每个文件能独立解析 | 独立解析要求每个文件只放完整条目，一条超过 sizeLimit 的条目放不进任何文件，得再加续传标记，格式复杂一倍，而且 KVStore 得知道文件边界，分层就破了 |
| key 顺序要不要保持 | 题面不要求。dict 保留插入顺序，写出和读回顺序一致。要按 key 范围查就 restore 后排序 |
