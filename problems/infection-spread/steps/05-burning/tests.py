from solution import (time_to_full_infection, time_to_full_infection_with_immunity, time_to_stable_state, time_to_full_infection_threshold, time_to_end_with_deaths, min_deaths_one_burn, best_initial_burn, best_timed_burn, best_daily_burn, min_deaths_daily_fast, minimum_deaths, FixedLifetime, Countdown, Burn, decode_grid)
from random import Random
from functools import cache


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

def _reference_daily_minimum(grid, D, K, allow_no_burn=True, count_burned=True,
                             burn_before=True, horizon=None, budget=None, require_one_burn=False):
    # 独立穷举按原始计时规则逐日算，不使用被测转移函数和任何剪枝。
    rows, cols = len(grid), len(grid[0]) if grid else 0
    neighbors = []
    for row in range(rows):
        for col in range(cols):
            neighbors.append(tuple(r * cols + c for r, c in
                                   ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                                   if 0 <= r < rows and 0 <= c < cols))
    values = [value for row in grid for value in row]
    initial = tuple((value, D if value == 1 else 0,
                     value == 1 and sum(values[j] == 1 for j in neighbors[i]) >= K)
                    for i, value in enumerate(values))
    lines = [tuple(r * cols + c for c in range(cols)) for r in range(rows)]
    lines += [tuple(r * cols + c for r in range(rows)) for c in range(cols)]

    def burn(state, line):
        result = list(state)
        cost = 0
        for i in line or ():
            if result[i][0] != 3:
                cost += int(count_burned)
                result[i] = (3, 0, False)
        return tuple(result), cost

    def day_step(state):
        result = list(state)
        deaths = 0
        for i, (value, remaining, will_die) in enumerate(state):
            if value == 1:
                if remaining == 1:
                    result[i] = (3 if will_die else 2, 0, False)
                    deaths += will_die
                else:
                    result[i] = (1, remaining - 1, will_die)
        snapshot = tuple(result)
        for i, (value, remaining, will_die) in enumerate(snapshot):
            count = sum(snapshot[j][0] == 1 for j in neighbors[i])
            if value == 0 and count > 0:
                result[i] = (1, D, count >= K)
        return tuple(result), deaths

    @cache
    def search(state, burns_left, days_left, must_burn):
        if days_left == 0 or not any(value == 1 for value, remaining, will_die in state):
            return float('inf') if must_burn else 0
        actions = [None] if burns_left == 0 else lines + ([None] if allow_no_burn else [])
        best = float('inf')
        for line in actions:
            if burn_before:
                burned, burn_cost = burn(state, line)
                next_state, natural_cost = day_step(burned)
            else:
                evolved, natural_cost = day_step(state)
                next_state, burn_cost = burn(evolved, line)
            next_budget = burns_left if line is None or burns_left is None else burns_left - 1
            next_days = None if days_left is None else days_left - 1
            future = search(next_state, next_budget, next_days, must_burn and line is None)
            best = min(best, burn_cost + natural_cost + future)
        return best

    return sum(value == 3 for value in values) + search(initial, budget, horizon, require_one_burn)


def test_burning_before_initial_flags_differs_from_day_one():
    grid = [[1, 1]]
    model = FixedLifetime(1, 2, D=1, death_threshold=1)
    assert best_initial_burn(grid, model).deaths == 1  # 先删一个来源，另一个初始标记不再是必死。
    assert best_timed_burn(grid, model, allow_no_burn=False).deaths == 2  # 第零天的两个必死标记不能撤销。


def test_one_burn_reuses_the_no_burn_bfs():
    grid = [[1, 0, 1, 0, 1]]
    assert min_deaths_one_burn(grid, D=2, K=2) == (1, ('col', 2))  # 去掉中间来源，剩余新感染都只接触一个来源。
    assert grid == [[1, 0, 1, 0, 1]]  # 候选之间和调用者输入之间不能互相污染。


def test_no_burn_is_a_real_candidate():
    assert min_deaths_one_burn([[1, 0]], D=2, K=2)[0] == 0  # 不烧时两个细胞都会恢复。
    assert min_deaths_one_burn([[1, 0]], D=2, K=2, allow_no_burn=False)[0] == 1  # 必须烧就至少付出一个死亡。


def test_waiting_can_improve_a_single_burn():
    grid = [[1, 0, 0, 1, 0], [2, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    model = FixedLifetime(3, 5, D=2, death_threshold=2)
    state = model.initial(grid)
    early = [model.deaths_without_burn(state)]
    for action in model.actions:
        burned, cost = model.burn(state, action)
        early.append(cost + model.deaths_without_burn(burned))
    assert min(early) == 4  # 第一天烧任意线或完全不烧，最少仍死四个。
    choice = best_timed_burn(grid, model)
    assert (choice.deaths, choice.day, choice.action) == (3, 2, Burn('col', 3))  # 第二天烧第三列只死三个。


def test_repeated_burns_can_beat_every_single_burn():
    grid = [[0, 1, 0, 0, 1]]
    model = FixedLifetime(1, 5, D=2, death_threshold=1)
    assert best_timed_burn(grid, model).deaths == 3  # 单次任意选时也只能做到三人死亡。
    assert minimum_deaths(grid, D=2, K=1) == 2  # 第一天烧第一列，第二天烧第三列。


def test_required_daily_burn_can_reuse_a_dead_line():
    grid = [[0, 1, 0, 0, 1]]
    model = FixedLifetime(1, 5, D=3, death_threshold=1)
    assert min_deaths_daily_fast(grid, 3, 1, allow_no_burn=False) == 2  # 后续可以反复选择同一条死线。
    assert best_daily_burn(grid, model, allow_no_burn=False) == 2  # 完整计时版本给出相同最优值。


def test_free_burns_have_a_different_objective():
    grid = [[1, 0, 1, 0, 1]]
    model = FixedLifetime(1, 5, D=2, death_threshold=2)
    assert best_daily_burn(grid, model) == 1  # 全部死亡都计费时至少牺牲一个。
    assert best_daily_burn(grid, model, count_burned=False) == 0  # 免费烧整行可以避免全部病死。


def test_burn_after_spreading_cannot_undo_new_death_flags():
    grid = [[1, 0, 1, 0, 1]]
    model = FixedLifetime(1, 5, D=2, death_threshold=2)
    assert best_daily_burn(grid, model, burn_before=False) == 2  # 中间两个新感染已经被判为必死。


def test_budget_and_required_action_are_part_of_the_state():
    grid = [[0, 1, 0, 0, 1]]
    model = FixedLifetime(1, 5, D=2, death_threshold=1)
    assert best_daily_burn(grid, model, budget=0) == 3  # 没有次数就完全不干预。
    assert best_daily_burn(grid, model, budget=1) == 3  # 只允许一次仍至少死三个。
    assert best_daily_burn(grid, model, budget=2) == 2  # 两次可以阻断第二段传播。
    safe = FixedLifetime(1, 2, D=2, death_threshold=2)
    assert best_daily_burn([[1, 0]], safe, budget=1, require_one_burn=True) == 1  # 必须实际完成一次，不能拿完全不烧的零作答案。


def test_finite_horizon_does_not_charge_future_deaths():
    grid = [[1, 0, 1]]
    model = FixedLifetime(1, 3, D=2, death_threshold=2)
    assert best_daily_burn(grid, model, budget=0, horizon=2) == 0  # 中心第三天才死，两天目标不收费。
    assert best_daily_burn(grid, model, budget=0, horizon=3) == 1  # 期限覆盖到期日时必须收费。


def test_death_paid_once_even_if_burned_at_expiration():
    model = FixedLifetime(1, 2, D=1, death_threshold=1)
    assert best_daily_burn([[1, 1]], model) == 2  # 烧死一个再到期死一个，总数不是三个。


def test_stable_grid_does_not_require_an_extra_action():
    assert minimum_deaths([[0, 2, 0]], D=2, K=1) == 0  # 无感染时日程已经结束。
    assert minimum_deaths([], D=2, K=1) == 0  # 空网格没有动作和死亡。


def test_compressed_state_handles_large_lifetime():
    assert minimum_deaths([[0, 1, 0, 0, 1]], D=1000000, K=1) == 2  # 计入最终全部死亡时无需逐日等百万天。


def test_cached_and_compressed_search_match_unpruned_search():
    rng = Random(5005)
    for _ in range(60):
        grid = [[rng.randrange(3) for _ in range(3)] for _ in range(2)]
        D, K = rng.randint(1, 3), rng.randint(1, 4)
        model = FixedLifetime(2, 3, D, K)
        options = dict(allow_no_burn=bool(rng.randrange(2)), count_burned=bool(rng.randrange(2)),
                       burn_before=bool(rng.randrange(2)), budget=rng.choice([None, 0, 1, 2]),
                       horizon=rng.choice([None, 1, 2, 4]))
        options['require_one_burn'] = options['budget'] == 1 and bool(rng.randrange(2))
        expected = _reference_daily_minimum(grid, D, K, **options)
        assert best_daily_burn(grid, model, **options) == expected  # 缓存键、费用和剪枝都必须与无剪枝搜索一致。
        for optional in (True, False):
            expected = _reference_daily_minimum(grid, D, K, allow_no_burn=optional)
            assert min_deaths_daily_fast(grid, D, K, allow_no_burn=optional) == expected  # 五状态简化不能改变最终最小人数。


def test_countdown_uses_a_different_daily_order():
    grid = decode_grid(['II', 'IH'])
    model = Countdown(2, 2, D=1, T=1, K=2)
    state = model.initial(grid)
    first, first_deaths = model.step(state)
    second, second_deaths = model.step(first)
    assert first_deaths == 0  # 当天新开始的倒计时当天不减一。
    assert second_deaths == 2  # 第二天才结算两个死亡标记。
    assert [cell.status for cell in second] == [3, 2, 2, 3]  # 结果为 DR、RD。


def test_countdown_initial_burn_example():
    grid = decode_grid(['HIHH', 'HIHH', 'HHHH'])
    model = Countdown(3, 4, D=1, T=1, K=2)
    result = best_initial_burn(grid, model, horizon=3)
    assert (result.deaths, result.action) == (3, Burn('col', 1))  # 三天版本最优是烧掉第二列三个格子。


def test_zero_countdown_threshold_can_start_without_a_source():
    model = Countdown(1, 1, D=1, T=0, K=0)
    assert model.deaths_without_burn(model.initial([[0]]), days_left=2) == 1  # 不能套用固定模型的无来源提前结束。


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
        test_burning_before_initial_flags_differs_from_day_one,
        test_one_burn_reuses_the_no_burn_bfs,
        test_no_burn_is_a_real_candidate,
        test_waiting_can_improve_a_single_burn,
        test_repeated_burns_can_beat_every_single_burn,
        test_required_daily_burn_can_reuse_a_dead_line,
        test_free_burns_have_a_different_objective,
        test_burn_after_spreading_cannot_undo_new_death_flags,
        test_budget_and_required_action_are_part_of_the_state,
        test_finite_horizon_does_not_charge_future_deaths,
        test_death_paid_once_even_if_burned_at_expiration,
        test_stable_grid_does_not_require_an_extra_action,
        test_compressed_state_handles_large_lifetime,
        test_cached_and_compressed_search_match_unpruned_search,
        test_countdown_uses_a_different_daily_order,
        test_countdown_initial_burn_example,
        test_zero_countdown_threshold_can_start_without_a_source,
    ]
    for test in tests:
        test()
    print(f"all {len(tests)} passed")
