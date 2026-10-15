from solution import (time_to_full_infection, time_to_full_infection_with_immunity)


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

def test_immune_wall_blocks_a_healthy_cell():
    assert time_to_full_infection_with_immunity([[1, 2, 0]]) == -1  # 不能越过永久免疫格。


def test_spread_can_go_around_a_wall():
    grid = [[1, 2, 0], [0, 2, 0], [0, 0, 0]]
    assert time_to_full_infection_with_immunity(grid) == 6  # 右上角要沿下方绕行六条边。


def test_immune_cells_do_not_need_infection():
    assert time_to_full_infection_with_immunity([[2, 2]]) == 0  # 没有健康格就已经完成。
    assert time_to_full_infection_with_immunity([[1, 2]]) == 0  # 免疫格不计入剩余健康人数。


def test_sources_on_both_sides_of_a_wall():
    assert time_to_full_infection_with_immunity([[1, 0, 2, 0, 1]]) == 1  # 两侧各自有来源。


if __name__ == "__main__":
    tests = [
        test_empty_grid_and_single_cell,
        test_no_source_cannot_start,
        test_new_infection_waits_until_next_day,
        test_only_four_neighbors_spread,
        test_all_sources_start_on_day_zero,
        test_single_column_uses_row_bounds,
        test_dates_do_not_overwrite_input,
        test_immune_wall_blocks_a_healthy_cell,
        test_spread_can_go_around_a_wall,
        test_immune_cells_do_not_need_infection,
        test_sources_on_both_sides_of_a_wall,
    ]
    for test in tests:
        test()
    print(f"all {len(tests)} passed")
