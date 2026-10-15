from solution import RectangleBoard


def test_official_example():
    b = RectangleBoard(4, 3)
    assert b.addRectangle(1, 0, 2, 1) == 1
    assert b.addRectangle(2, 1, 3, 2) == 2
    assert b.getAt(2, 1) == 2          # 两张都盖住这格，后加的 2 在上面
    assert b.removeRectangle(2) is True
    assert b.getAt(2, 1) == 1          # 2 走了，露出下面的 1
    assert b.getAt(3, 2) == -1         # 这格只有 2 盖过，现在空了
    assert b.removeRectangle(2) is False   # 已经移除过


def test_boundary_is_inclusive():
    b = RectangleBoard(5, 5)
    b.addRectangle(1, 1, 3, 3)
    assert b.getAt(1, 1) == 1          # 左上角本身算覆盖
    assert b.getAt(3, 3) == 1          # 右下角本身算覆盖
    assert b.getAt(0, 1) == -1         # 左边一列没盖到
    assert b.getAt(4, 3) == -1         # 右边一列没盖到


def test_single_cell_rectangle():
    b = RectangleBoard(2, 2)
    assert b.addRectangle(0, 0, 0, 0) == 1   # 一个单元格也是合法矩形
    assert b.getAt(0, 0) == 1
    assert b.getAt(1, 1) == -1


def test_remove_removes_whole_rectangle():
    b = RectangleBoard(4, 4)
    b.addRectangle(0, 0, 3, 0)         # 横着一条
    b.addRectangle(0, 0, 0, 3)         # 竖着一条，压住 (0,0)
    assert b.getAt(0, 0) == 2
    assert b.removeRectangle(2) is True
    assert b.getAt(0, 0) == 1          # 竖条整条消失
    assert b.getAt(0, 3) == -1         # 包括它在别处的格子


def test_bad_ids():
    b = RectangleBoard(3, 3)
    b.addRectangle(0, 0, 1, 1)
    assert b.removeRectangle(0) is False     # 编号从 1 开始
    assert b.removeRectangle(-5) is False
    assert b.removeRectangle(99) is False    # 从来没发过的编号
    assert b.getAt(0, 0) == 1                # 失败的移除不能改动画板


def test_ids_never_reused():
    b = RectangleBoard(3, 3)
    assert b.addRectangle(0, 0, 0, 0) == 1
    assert b.removeRectangle(1) is True
    assert b.addRectangle(0, 0, 0, 0) == 2   # 1 号腾出来了也不回收


def test_stacking_follows_id_order():
    b = RectangleBoard(3, 3)
    b.addRectangle(0, 0, 2, 2)         # 1 铺满
    b.addRectangle(0, 0, 2, 2)         # 2 铺满
    b.addRectangle(0, 0, 2, 2)         # 3 铺满
    assert b.getAt(1, 1) == 3
    b.removeRectangle(3)
    assert b.getAt(1, 1) == 2          # 露出下一层
    b.removeRectangle(1)               # 移除被压在最底下的那张
    assert b.getAt(1, 1) == 2          # 画面不变，但 1 已经不在了
    b.removeRectangle(2)
    assert b.getAt(1, 1) == -1


if __name__ == "__main__":
    tests = [
        test_official_example,
        test_boundary_is_inclusive,
        test_single_cell_rectangle,
        test_remove_removes_whole_rectangle,
        test_bad_ids,
        test_ids_never_reused,
        test_stacking_follows_id_order,
    ]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
