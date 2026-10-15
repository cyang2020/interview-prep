from solution import (time_to_full_infection)


def test_empty_grid_and_single_cell():
    assert time_to_full_infection([]) == 0  # 空网格没有等待感染的格子。
    assert time_to_full_infection([[]]) == 0  # 零列网格也已完成。
    assert time_to_full_infection([[1]]) == 0  # 初始已经全部感染。
    assert time_to_full_infection([[0]]) == -1  # 单个健康格没有感染源。


def test_no_source_cannot_start():
    assert time_to_full_infection([[0, 0], [0, 0]]) == -1  # 健康格不会自行感染。


def test_new_infection_waits_until_next_day():
    assert time_to_full_infection([[1, 0, 0, 0, 0]]) == 4  # 同一天不能连续跨过四条边。


def test_only_four_neighbors_spread():
    assert time_to_full_infection([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == 2  # 对角线不算邻居。


def test_all_sources_start_on_day_zero():
    assert time_to_full_infection([[1, 0, 0], [0, 0, 0], [0, 0, 1]]) == 2  # 两个来源同时开始。


def test_single_column_uses_row_bounds():
    assert time_to_full_infection([[1], [0], [0]]) == 2  # 行列下标不能对调。


def test_dates_do_not_overwrite_input():
    grid = [[1, 0, 0]]
    assert time_to_full_infection(grid) == 2  # 首次调用得到两天。
    assert grid == [[1, 0, 0]]  # 本实现单独记录日期，保留调用者输入。
    assert time_to_full_infection(grid) == 2  # 同一输入再次调用结果不变。


if __name__ == "__main__":
    tests = [
        test_empty_grid_and_single_cell,
        test_no_source_cannot_start,
        test_new_infection_waits_until_next_day,
        test_only_four_neighbors_spread,
        test_all_sources_start_on_day_zero,
        test_single_column_uses_row_bounds,
        test_dates_do_not_overwrite_input,
    ]
    for test in tests:
        test()
    print(f"all {len(tests)} passed")
