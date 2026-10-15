# 题面

## 题目

- 写一个 KVStore：内存里一张 key 到 value 的表，key 和 value 都是字符串。程序退出时整张表变成一串字节存进 medium，下次启动再从那串字节变回来。字节格式自己定，不许用 JSON、pickle 这类现成的序列化。
- Medium.saveBlob(data) / getBlob()：题目给好的存储接口。saveBlob 存一串字节，再存就覆盖上一份；getBlob 取回最近存的那串，没存过返回 None。
- KVStore(medium)：建一张空表，记住往哪个 medium 存。不自动读 medium 里的东西。
- put(key, value)：写一项，key 已有就覆盖。get(key)：读一项，没有返回空串。
- shutdown()：整张表变成一串字节，调 saveBlob 存进去，然后实例关闭，再 put 或 get 要抛错。
- restore()：调 getBlob 拿回字节，变回表，整个替换内存里的表。medium 里什么都没有就变成空表。
- 第一问：定一个二进制格式，空串、中文、emoji 存进去再读出来一模一样；加上关闭后抛错、restore 整体替换两条规则。
- 第二问：InMemoryMedium 构造多收一个 sizeLimit，saveBlob 把字节切成多个文件，每个不超过 sizeLimit 字节；getBlob 按顺序拼回一整串。KVStore 不用动。

## 要问清楚的地方

- shutdown 之后 restore 算不算合法；restore 之后能不能继续 put、再 shutdown。
- medium 里的字节非空但格式是坏的，抛错还是当成空表。
- 第二问：文件头算不算在 sizeLimit 里；一条 key 加 value 比 sizeLimit 大怎么办。
- 第二问：少了一个文件要不要报错，还是能读多少读多少。
- 第二问：第二次保存的文件数比上次少，上次多出来的旧文件怎么处理。
