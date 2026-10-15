from solution import (time_to_full_infection, time_to_full_infection_with_immunity, time_to_stable_state)
from random import Random


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

def _simulate_until_done(grid, D, K=5):
    # 独立对照逐日处理，不用被测代码中的 BFS 日期或前一层判定。
    board = [row[:] for row in grid]
    rows, cols = len(board), len(board[0]) if board else 0

    def count(row, col):
        return sum(0 <= r < rows and 0 <= c < cols and board[r][c] == 1
                   for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)))

    infected_cells = {(r, c): (0, count(r, c) >= K)
                      for r in range(rows) for c in range(cols) if board[r][c] == 1}
    day = deaths = 0
    while infected_cells:
        day += 1
        expired = [cell for cell, (start, will_die) in infected_cells.items() if day - start >= D]
        for r, c in expired:
            _, will_die = infected_cells.pop((r, c))
            board[r][c] = 3 if will_die else 2
            deaths += will_die
        newly_infected = []
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 0 and count(r, c) > 0:
                    newly_infected.append((r, c, count(r, c) >= K))
        for r, c, will_die in newly_infected:
            board[r][c] = 1
            infected_cells[(r, c)] = (day, will_die)
    return day, deaths


def test_no_infection_is_already_stable():
    assert time_to_stable_state([[0, 2, 0]], D=3) == 0  # 稳定不要求健康格都感染。
    assert time_to_stable_state([], D=3) == 0  # 空网格从第零天就没有感染。


def test_recovery_happens_before_spread():
    assert time_to_stable_state([[1, 0, 0]], D=1) == 1  # 第一天到期，来不及感染邻居。


def test_last_infection_waits_its_own_lifetime():
    assert time_to_stable_state([[1, 0, 0]], D=2) == 4  # 最右格第二天感染，第四天恢复。
    assert time_to_stable_state([[1, 1]], D=4) == 4  # 初始来源仍需等满四天。


def test_large_lifetime_does_not_require_daily_scans():
    assert time_to_stable_state([[1, 0, 0]], D=1000000) == 1000002  # 最晚感染日加寿命即可。


def test_recovery_with_an_unreachable_healthy_cell():
    assert time_to_stable_state([[1, 2, 0]], D=2) == 2  # 右侧始终健康，不妨碍最终稳定。


def test_recovery_matches_literal_days():
    rng = Random(3003)
    for _ in range(100):
        grid = [[rng.randrange(3) for _ in range(3)] for _ in range(2)]
        D = rng.randint(1, 5)
        assert time_to_stable_state(grid, D) == _simulate_until_done(grid, D)[0]  # 与真实逐日过程一致。


def test_recovery_rejects_zero_lifetime():
    try:
        time_to_stable_state([[1]], D=0)
    except ValueError:
        return
    assert False  # 当前规则只定义正整数寿命。


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
        test_no_infection_is_already_stable,
        test_recovery_happens_before_spread,
        test_last_infection_waits_its_own_lifetime,
        test_large_lifetime_does_not_require_daily_scans,
        test_recovery_with_an_unreachable_healthy_cell,
        test_recovery_matches_literal_days,
        test_recovery_rejects_zero_lifetime,
    ]
    for test in tests:
        test()
    print(f"all {len(tests)} passed")
