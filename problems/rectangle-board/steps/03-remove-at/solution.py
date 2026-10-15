class Rect:
    """一张矩形贴纸。坐标是闭区间，边界上的单元格也算被它覆盖。"""

    __slots__ = ("rid", "x1", "y1", "x2", "y2", "active")

    def __init__(self, rid, x1, y1, x2, y2):
        self.rid = rid
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.active = True    # 被移除时只翻这个标记，坐标永远留着

    def covers(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class RectangleBoard:
    def __init__(self, width, height):
        self.width = width        # 题目保证查询不越界，存着备用
        self.height = height
        # 下标 i 存编号 i+1 的矩形：编号从 1 连续发、永不复用，所以列表下标就是编号表。
        # 列表顺序同时就是叠放顺序——后加的在后面，也就在上面。
        self.rects = []
        # 历史栈，每条是 ("add" | "remove", [编号...])。只记成功且改了内容的操作
        self.history = []

    def addRectangle(self, x1, y1, x2, y2):
        rid = len(self.rects) + 1
        self.rects.append(Rect(rid, x1, y1, x2, y2))
        self.history.append(("add", [rid]))
        return rid

    def removeRectangle(self, rectangleId):
        rect = self._find(rectangleId)
        if rect is None or not rect.active:
            return False          # 编号没发过，或者已经移除过：不记历史
        rect.active = False
        self.history.append(("remove", [rectangleId]))
        return True

    def getAt(self, x, y):
        # 最上面 = 编号最大，所以从列表尾部往前找第一个还活着且覆盖这格的
        for rect in reversed(self.rects):
            if rect.active and rect.covers(x, y):
                return rect.rid
        return -1

    def removeAt(self, x, y):
        rid = self.getAt(x, y)                # 选中的就是这格最上面那张
        if rid == -1:
            return -1                         # 空格子：不动画板，也不记历史
        self.removeRectangle(rid)             # 复用它：翻标记和记历史都在里面
        return rid

    def undo(self):
        if not self.history:
            return False
        action, ids = self.history.pop()      # 撤销就把这条记录吃掉，不再写新记录
        # 撤销一次移除 = 把它们改回活着；撤销一次添加 = 把它改成不活
        alive = action == "remove"
        for rid in ids:
            self.rects[rid - 1].active = alive
        return True

    def _find(self, rid):
        if 1 <= rid <= len(self.rects):
            return self.rects[rid - 1]
        return None
