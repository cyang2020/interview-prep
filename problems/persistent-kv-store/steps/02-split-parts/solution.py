# ---- 字节工具：所有长度、计数都是 4 字节大端无符号整数 ----
U32 = 4


def _u32(n):
    return n.to_bytes(U32, "big")


class _Reader:
    """带游标的读取器。所有"字节不够"的检查都集中在 read 里，调用方不用各写一遍。"""

    def __init__(self, blob):
        self.blob = blob
        self.pos = 0

    def read(self, n):
        if self.pos + n > len(self.blob):
            raise ValueError("blob truncated")
        chunk = self.blob[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def read_u32(self):
        return int.from_bytes(self.read(U32), "big")

    def read_str(self):
        # 先读长度（字节数），再按字节数切，再解码；surrogatepass 和写入侧对称
        return self.read(self.read_u32()).decode("utf-8", errors="surrogatepass")

    def expect_end(self):
        if self.pos != len(self.blob):
            raise ValueError("trailing bytes after last entry")


# ---- 存储介质：题面给的接口，Java 名字照用。只认字节，不认字符串 ----
class Medium:
    def saveBlob(self, data):
        raise NotImplementedError

    def getBlob(self):
        raise NotImplementedError


class InMemoryMedium(Medium):
    """模拟一个目录：files 是文件名到文件内容。每个文件 = 8 字节文件头 + 一段正文。"""

    HEADER = 8                           # 4 字节"第几份" + 4 字节"一共几份"

    def __init__(self, size_limit):
        if size_limit <= self.HEADER:
            raise ValueError(f"size_limit must exceed header size {self.HEADER}")
        self.size_limit = size_limit
        self.capacity = size_limit - self.HEADER   # 文件头算在 size_limit 里，正文只剩这么多
        self.files = {}                            # 文件名 -> bytes，模拟目录

    def saveBlob(self, data):
        data = bytes(data)
        self.files.clear()                         # 先删上一次的全部文件，不留旧份
        total = max(1, -(-len(data) // self.capacity))   # 向上取整；空数据也写 1 份，和"没存过"分开
        for i in range(total):
            body = data[i * self.capacity:(i + 1) * self.capacity]   # 按字节切，不管里面是什么
            self.files[_part_name(i)] = _u32(i) + _u32(total) + body

    def getBlob(self):
        if not self.files:
            return None                            # 从没存过
        first = self.files.get(_part_name(0))
        if first is None:
            raise ValueError("part 0 missing")
        total = int.from_bytes(first[4:8], "big")  # 第 0 份说一共几份，就按这个数点名取
        chunks = []
        for i in range(total):
            part = self.files.get(_part_name(i))
            if part is None:
                raise ValueError(f"part {i} of {total} missing")
            index = int.from_bytes(part[0:4], "big")
            count = int.from_bytes(part[4:8], "big")
            if index != i or count != total:
                raise ValueError(f"part {i} header mismatch")   # 文件名和头里的序号互相核对
            chunks.append(part[self.HEADER:])
        return b"".join(chunks)


def _part_name(i):
    return f"part-{i:05d}"               # 补零让按名字排序就是按序号排序


# ---- KVStore：格式是 流头 + 每条 (len, key, len, value)。第二问一行不改 ----
MAGIC = b"KV"      # 流头前 2 字节，restore 时一眼认出是不是我们写的
VERSION = 1        # 以后改格式时加 1，restore 按版本分流


class KVStore:
    def __init__(self, medium):
        self.medium = medium
        self.data = {}        # key -> value，内存里唯一的一份
        self.closed = False   # shutdown 之后为 True，四个方法都拒绝

    def put(self, key, value):
        self._check_open()
        self.data[key] = value

    def get(self, key):
        self._check_open()
        return self.data.get(key, "")

    def shutdown(self):
        self._check_open()
        self.medium.saveBlob(self._encode())
        self.closed = True            # 放在 saveBlob 之后：写失败时实例还开着，能重试

    def restore(self):
        self._check_open()
        blob = self.medium.getBlob()
        if not blob:                      # None 或 b""：没存过，变成空表
            self.data = {}
            return
        self.data = self._decode(blob)    # 整体替换，不是 update；解码失败抛错，data 不动

    def _encode(self):
        parts = [MAGIC, bytes([VERSION]), _u32(len(self.data))]
        for key, value in self.data.items():
            for s in (key, value):
                # 长度前缀记的是 UTF-8 字节数，不是字符数；surrogatepass 让单独的代理项也能往返
                raw = s.encode("utf-8", errors="surrogatepass")
                parts.append(_u32(len(raw)))
                parts.append(raw)
        return b"".join(parts)            # 用 list 收集再 join，不用 bytes += 拼

    def _decode(self, blob):
        reader = _Reader(blob)
        if reader.read(len(MAGIC)) != MAGIC:
            raise ValueError("not a KVStore blob")
        version = reader.read(1)[0]
        if version != VERSION:
            raise ValueError(f"unsupported version {version}")
        count = reader.read_u32()
        data = {}
        for _ in range(count):
            key = reader.read_str()
            data[key] = reader.read_str()
        reader.expect_end()               # 多出字节也算坏：说明写入侧和读取侧对格式理解不一致
        return data

    def _check_open(self):
        if self.closed:
            raise RuntimeError("KVStore is closed")
