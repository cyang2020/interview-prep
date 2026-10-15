from solution import (time_to_full_infection, time_to_full_infection_with_immunity, time_to_stable_state, time_to_full_infection_threshold, time_to_end_with_deaths)
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

def _threshold_simulation(grid, K):
    board = [row[:] for row in grid]
    rows, cols = len(board), len(board[0]) if board else 0
    day = 0
    while any(0 in row for row in board):
        changes = []
        for row in range(rows):
            for col in range(cols):
                count = sum(0 <= r < rows and 0 <= c < cols and board[r][c] == 1
                            for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)))
                if board[row][col] == 0 and count >= K:
                    changes.append((row, col))
        if not changes:
            return -1
        for row, col in changes:
            board[row][col] = 1
        day += 1
    return day


def test_threshold_counts_distinct_infected_neighbors():
    assert time_to_full_infection_threshold([[1, 0, 1]], K=2) == 1  # 两个不同来源各贡献一次。
    assert time_to_full_infection_threshold([[1, 0, 0]], K=2) == -1  # 同一个来源不能每天重复加一。


def test_threshold_new_layer_waits_one_day():
    assert time_to_full_infection_threshold([[1, 0, 0], [1, 0, 1]], K=2) == 3  # 三层依次在第一、二、三天触发。


def test_threshold_handles_immunity_and_no_healthy_cells():
    assert time_to_full_infection_threshold([[2, 1]], K=4) == 0  # 没有健康格就无需达到阈值。
    assert time_to_full_infection_threshold([[1, 2, 0]], K=1) == -1  # 阈值为一也不能穿过免疫墙。


def test_threshold_matches_synchronous_simulation():
    rng = Random(4004)
    for _ in range(100):
        grid = [[rng.randrange(3) for _ in range(3)] for _ in range(3)]
        K = rng.randint(1, 4)
        assert time_to_full_infection_threshold(grid, K) == _threshold_simulation(grid, K)  # 不依赖队列实现来算期望值。


def test_initial_death_flags_use_day_zero_neighbors():
    assert time_to_end_with_deaths([[1, 1]], D=2, K=1) == (2, 2)  # 初始相邻感染都被判为必死。


def test_new_infections_do_not_count_each_other():
    assert time_to_end_with_deaths([[1, 0, 0, 1]], D=2, K=2) == (3, 0)  # 中间两格同日新感染，不能互相补成两个邻居。


def test_death_flag_survives_neighbors_recovery():
    assert time_to_end_with_deaths([[1, 0, 1]], D=2, K=2) == (3, 1)  # 来源第二天恢复，中心第三天仍会死亡。


def test_death_with_one_day_lifetime_does_not_spread():
    assert time_to_end_with_deaths([[1, 1, 0]], D=1, K=1) == (1, 2)  # 只计算两个初始必死来源。
    assert time_to_end_with_deaths([[0, 2]], D=1, K=1) == (0, 0)  # 没有感染就没有新增病死。


def test_fixed_death_matches_literal_simulation():
    rng = Random(4040)
    for _ in range(150):
        grid = [[rng.randrange(3) for _ in range(3)] for _ in range(2)]
        D, K = rng.randint(1, 5), rng.randint(1, 4)
        assert time_to_end_with_deaths(grid, D, K) == _simulate_until_done(grid, D, K)  # 结束日和死亡数都须一致。


def test_threshold_rejects_values_outside_four_neighbors():
    try:
        time_to_full_infection_threshold([[1, 0]], K=5)
    except ValueError:
        return
    assert False  # 四邻居版本只接受一到四的阈值。


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
        test_threshold_counts_distinct_infected_neighbors,
        test_threshold_new_layer_waits_one_day,
        test_threshold_handles_immunity_and_no_healthy_cells,
        test_threshold_matches_synchronous_simulation,
        test_initial_death_flags_use_day_zero_neighbors,
        test_new_infections_do_not_count_each_other,
        test_death_flag_survives_neighbors_recovery,
        test_death_with_one_day_lifetime_does_not_spread,
        test_fixed_death_matches_literal_simulation,
        test_threshold_rejects_values_outside_four_neighbors,
    ]
    for test in tests:
        test()
    print(f"all {len(tests)} passed")
