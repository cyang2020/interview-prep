from collections import deque
from functools import cache
from math import inf
from typing import NamedTuple

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _infection_days(grid, D=None, K=1):
    # 先收下 D 和 K，后续恢复、阈值版本沿用这个调用方式。
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    infection_day = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == 1:
                infection_day[row][col] = 0
                queue.append((row, col))

    # 先到期再传播，D=1 的来源在第一次传播前就消失。
    if D == 1:
        return infection_day

    # 只有多个邻居才能触发感染时，才需要累积这些计数。
    infected_neighbors = [[0] * cols for _ in range(rows)] if K > 1 else None
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            if (0 <= r < rows and 0 <= c < cols
                    and grid[r][c] == 0 and infection_day[r][c] == -1):
                if K > 1:
                    infected_neighbors[r][c] += 1
                if K == 1 or infected_neighbors[r][c] == K:
                    # 入队时记下日期，多个来源就不会重复安排同一个位置。
                    infection_day[r][c] = infection_day[row][col] + 1
                    queue.append((r, c))
    return infection_day


def _full_infection_days(grid, infection_day):
    days = 0
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if grid[row][col] == 0:
                if infection_day[row][col] == -1:
                    return -1
                days = max(days, infection_day[row][col])
    return days


def time_to_full_infection(grid):
    # 返回值要求全部健康格感染；不可达位置必须在这里报 -1。
    return _full_infection_days(grid, _infection_days(grid))


def time_to_full_infection_with_immunity(grid):
    # 传播只进入 0，免疫格 2 无需入队，也不计入必须感染的位置。
    return time_to_full_infection(grid)


def time_to_stable_state(grid, D):
    if D < 1:
        raise ValueError("D 必须至少为 1")
    infection_day = _infection_days(grid, D=D)
    last_infection_day = max((day for row in infection_day for day in row), default=-1)
    # 稳定只要求没有感染，健康格可一直保留，不能沿用全部感染的 -1。
    return 0 if last_infection_day == -1 else last_infection_day + D


def time_to_full_infection_threshold(grid, K):
    if not 1 <= K <= 4:
        raise ValueError("K 必须在 1 到 4 之间")
    # 这里的 K 是感染阈值，此分支没有恢复。
    return _full_infection_days(grid, _infection_days(grid, K=K))


def time_to_end_with_deaths(grid, D, K):
    if D < 1 or not 1 <= K <= 4:
        raise ValueError("需要 D>=1 且 1<=K<=4")
    infection_day = _infection_days(grid, D=D)
    rows, cols = len(grid), len(grid[0]) if grid else 0
    last_infection_day = -1
    deaths = 0
    for row in range(rows):
        for col in range(cols):
            day = infection_day[row][col]
            if day >= 0:
                last_infection_day = max(last_infection_day, day)
                # 初始来源按第 0 天判定；后来感染的只数前一日的邻居。
                neighbor_day = 0 if day == 0 else day - 1
                infected_neighbor_count = 0
                for dr, dc in DIRECTIONS:
                    r, c = row + dr, col + dc
                    if (0 <= r < rows and 0 <= c < cols
                            and infection_day[r][c] == neighbor_day):
                        infected_neighbor_count += 1
                deaths += infected_neighbor_count >= K
    # 输入中已有的死格只作墙，本函数不把它们再次计入新增病死人数。
    end_day = 0 if last_infection_day == -1 else last_infection_day + D
    return end_day, deaths


def min_deaths_one_burn(grid, D, K, *, allow_no_burn=True, count_burned=True):
    """开始前最多或恰好烧一次，第四问的 BFS 负责计算剩余病死人数。"""
    if not grid or not grid[0]:
        return 0, None
    rows, cols = len(grid), len(grid[0])
    existing_deaths = sum(value == 3 for row in grid for value in row)
    best = (inf, None)
    if allow_no_burn:
        _, natural_deaths = time_to_end_with_deaths(grid, D, K)
        best = (existing_deaths + natural_deaths, None)

    actions = [("row", r) for r in range(rows)] + [("col", c) for c in range(cols)]
    for axis, index in actions:
        # 每个候选都必须从原始网格开始，不能继承另一个候选的焚烧。
        candidate = [row[:] for row in grid]
        cells = ([(index, c) for c in range(cols)] if axis == "row"
                 else [(r, index) for r in range(rows)])
        burn_deaths = 0
        for r, c in cells:
            burn_deaths += int(count_burned and candidate[r][c] != 3)
            candidate[r][c] = 3
        _, natural_deaths = time_to_end_with_deaths(candidate, D, K)
        deaths = existing_deaths + burn_deaths + natural_deaths
        if deaths < best[0]:
            best = (deaths, (axis, index))
    return best


HEALTHY, INFECTED, IMMUNE, DEAD = range(4)


class Cell(NamedTuple):
    status: int
    remaining: int = 0
    will_die: bool = False


class Burn(NamedTuple):
    axis: str
    index: int


class Choice(NamedTuple):
    deaths: int
    action: Burn | None
    day: int | None = None


class GridModel:
    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.neighbors = tuple(
            tuple(nr * cols + nc for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                  if 0 <= nr < rows and 0 <= nc < cols)
            for r in range(rows) for c in range(cols)
        )
        self.actions = tuple([Burn("row", r) for r in range(rows)] + [Burn("col", c) for c in range(cols)])
        self.lines = {
            action: tuple(range(action.index * cols, (action.index + 1) * cols)
                          if action.axis == "row" else range(action.index, rows * cols, cols))
            for action in self.actions
        }

    def burn(self, state, action, count_burned=True):
        if action is None:
            return state, 0
        result = list(state)
        deaths = 0
        for i in self.lines[action]:
            if result[i].status != DEAD:
                deaths += int(count_burned)
                result[i] = Cell(DEAD)
        return tuple(result), deaths

    def counts(self, state):
        return [sum(state[j].status == INFECTED for j in adjacent) for adjacent in self.neighbors]

    def has_empty_burn_line(self, state):
        return any(all(state[i].status == DEAD for i in line) for line in self.lines.values())

    def terminal(self, state, days_left):
        return days_left == 0

    def unavoidable_deaths(self, state, days_left, count_burned):
        if not count_burned:
            return 0
        return sum(cell.status == INFECTED and cell.will_die and
                   (days_left is None or cell.remaining <= days_left)
                   for cell in state)


class FixedLifetime(GridModel):
    """感染后统一经过 D 天到期，免疫永久有效。"""

    def __init__(self, rows, cols, D, death_threshold):
        super().__init__(rows, cols)
        if D < 1 or not 1 <= death_threshold <= 4:
            raise ValueError("Require D >= 1 and 1 <= death_threshold <= 4.")
        self.D, self.death_threshold = D, death_threshold

    def initial(self, grid):
        state = tuple(Cell(value) for row in grid for value in row)
        counts = self.counts(state)
        return tuple(Cell(INFECTED, self.D, counts[i] >= self.death_threshold)
                     if cell.status == INFECTED else cell
                     for i, cell in enumerate(state))

    def terminal(self, state, days_left):
        return days_left == 0 or all(cell.status != INFECTED for cell in state)

    def step(self, state):
        after_expiration = list(state)
        deaths = 0
        for i, cell in enumerate(state):
            if cell.status == INFECTED:
                if cell.remaining == 1:
                    after_expiration[i] = Cell(DEAD if cell.will_die else IMMUNE)
                    deaths += int(cell.will_die)
                else:
                    after_expiration[i] = cell._replace(remaining=cell.remaining - 1)
        counts = self.counts(after_expiration)
        result = tuple(Cell(INFECTED, self.D, counts[i] >= self.death_threshold)
                       if cell.status == HEALTHY and counts[i] > 0 else cell
                       for i, cell in enumerate(after_expiration))
        return result, deaths

    def deaths_without_burn(self, state, days_left=None):
        """保留已有的剩余时间和死亡标记，计算之后不再焚烧的新增病死。"""
        if days_left == 0:
            return 0
        deaths = sum(cell.status == INFECTED and cell.will_die and
                     (days_left is None or cell.remaining <= days_left)
                     for cell in state)
        if self.D == 1:
            return deaths
        infection_day = [-1] * len(state)
        queue = deque()
        for i, cell in enumerate(state):
            # 剩一天会先到期，不能作为下一次传播的来源。
            if cell.status == INFECTED and cell.remaining >= 2:
                infection_day[i] = 0
                queue.append(i)
        while queue:
            i = queue.popleft()
            for j in self.neighbors[i]:
                if state[j].status == HEALTHY and infection_day[j] == -1:
                    infection_day[j] = infection_day[i] + 1
                    queue.append(j)
        for i, day in enumerate(infection_day):
            if day > 0 and (days_left is None or day + self.D <= days_left):
                count = sum(infection_day[j] == day - 1 for j in self.neighbors[i])
                deaths += int(count >= self.death_threshold)
        return deaths


class Countdown(GridModel):
    """有限天数的另一套规则：旧倒计时减一，新倒计时当天不减。"""

    def __init__(self, rows, cols, D, T, K, permanent_immunity=False):
        super().__init__(rows, cols)
        if D < 1 or not 0 <= T <= K <= 4:
            raise ValueError("Require D >= 1 and 0 <= T <= K <= 4.")
        self.D, self.T, self.K = D, T, K
        self.permanent_immunity = permanent_immunity

    def initial(self, grid):
        return tuple(Cell(value) for row in grid for value in row)

    def step(self, state):
        counts = self.counts(state)
        result = list(state)
        deaths = 0
        for i, cell in enumerate(state):
            if cell.remaining:
                if cell.remaining == 1:
                    result[i] = Cell(DEAD if cell.will_die else IMMUNE)
                    deaths += int(cell.will_die)
                else:
                    result[i] = cell._replace(remaining=cell.remaining - 1)
            elif cell.status != DEAD and not (self.permanent_immunity and cell.status == IMMUNE):
                if counts[i] >= self.T:
                    result[i] = Cell(INFECTED, self.D, counts[i] >= self.K)
        return tuple(result), deaths

    def deaths_without_burn(self, state, days_left):
        if days_left is None:
            raise ValueError("The countdown variant requires a finite day horizon.")
        deaths = 0
        for _ in range(days_left):
            next_state, additional = self.step(state)
            deaths += additional
            if next_state == state:
                break
            state = next_state
        return deaths


def decode_grid(rows):
    """把题面中的 H、I、R、D 转成格子值。"""
    codes = {"H": HEALTHY, "I": INFECTED, "R": IMMUNE, "D": DEAD}
    return [[codes[char] for char in row] for row in rows]


def initial_dead_count(grid):
    return sum(value == DEAD for row in grid for value in row)


def best_initial_burn(grid, model, *, allow_no_burn=False,
                      count_burned=True, horizon=None):
    """在第 0 天死亡标记计算之前烧一次，枚举全部合法动作。"""
    if not grid or not grid[0]:
        return Choice(0, None, None)
    choices = list(model.actions) + ([None] if allow_no_burn else [])
    best = Choice(inf, None, None)
    raw = tuple(Cell(value) for row in grid for value in row)
    for action in choices:
        burned, cost = model.burn(raw, action, count_burned)
        candidate = [[burned[r * model.cols + c].status for c in range(model.cols)]
                     for r in range(model.rows)]
        deaths = initial_dead_count(grid) + cost + model.deaths_without_burn(model.initial(candidate), horizon)
        if deaths < best.deaths:
            best = Choice(deaths, action, 0 if action is not None else None)
    return best


def best_timed_burn(grid, model, *, allow_no_burn=True, count_burned=True,
                    burn_before=True, horizon=None):
    """保留第 0 天标记，共用无干预前缀，枚举第一次也是唯一一次焚烧。"""
    if isinstance(model, Countdown) and horizon is None:
        raise ValueError("The countdown variant requires a finite day horizon.")
    state = model.initial(grid)
    past_deaths = initial_dead_count(grid)
    best = Choice(past_deaths + model.deaths_without_burn(state, horizon), None, None) if allow_no_burn else Choice(inf, None, None)
    day = 1
    while not model.terminal(state, None if horizon is None else horizon - day + 1):
        next_state, natural_deaths = model.step(state)
        for action in model.actions:
            before_burn = state if burn_before else next_state
            burned, burn_cost = model.burn(before_burn, action, count_burned)
            remaining_days = None if horizon is None else horizon - day + int(burn_before)
            cost = past_deaths + burn_cost + (0 if burn_before else natural_deaths)
            cost += model.deaths_without_burn(burned, remaining_days)
            if cost < best.deaths:
                best = Choice(cost, action, day)
        # 没有新增感染后，未来不会再增长，推迟同一条线的焚烧不会更优。
        no_new_infections = all(not (a.status == HEALTHY and b.status == INFECTED)
                                for a, b in zip(state, next_state))
        if isinstance(model, FixedLifetime) and horizon is None:
            # K=1 时后续感染全会死亡，提前阻断同一条线不会增加线外感染。
            if no_new_infections or (model.death_threshold == 1 and count_burned):
                break
        state = next_state
        past_deaths += natural_deaths
        day += 1
    return best


def best_daily_burn(grid, model, *, allow_no_burn=True, count_burned=True,
                    burn_before=True, horizon=None, budget=None,
                    require_one_burn=False):
    """缓存完整状态的精确搜索；每次返回未来最少还会增加的死亡。"""
    if isinstance(model, Countdown) and horizon is None:
        raise ValueError("The countdown variant requires a finite day horizon.")
    if horizon is not None and horizon < 0 or budget is not None and budget < 0:
        raise ValueError("horizon and budget must be nonnegative.")
    state = model.initial(grid)

    @cache
    def solve(state, burns_left, days_left, still_must_burn):
        if model.terminal(state, days_left):
            return inf if still_must_burn else 0
        if burns_left == 0:
            return inf if still_must_burn else model.deaths_without_burn(state, days_left)

        lower_bound = model.unavoidable_deaths(state, days_left, count_burned)
        # 已经全死的行列可以反复选，强制每日焚烧也能维持零额外干预。
        empty_line = model.has_empty_burn_line(state)
        can_wait = allow_no_burn or (empty_line and burns_left is None)
        best = (model.deaths_without_burn(state, days_left)
                if (allow_no_burn or empty_line) and not still_must_burn else inf)
        if best == lower_bound:
            return best

        actions = list(model.actions) + ([None] if can_wait else [])
        days_after = None if days_left is None else days_left - 1
        after_step = None if burn_before else model.step(state)
        candidates = {}
        for action in actions:
            if burn_before:
                burned, burn_cost = model.burn(state, action, count_burned)
                next_state, natural_deaths = model.step(burned)
            else:
                evolved, natural_deaths = after_step
                next_state, burn_cost = model.burn(evolved, action, count_burned)
            next_budget = burns_left if action is None or burns_left is None else burns_left - 1
            must_burn = still_must_burn and action is None
            key = (next_state, next_budget, days_after, must_burn)
            cost = burn_cost + natural_deaths
            candidates[key] = min(cost, candidates.get(key, inf))

        ordered = sorted(candidates.items(), key=lambda item: (
            item[1], sum(cell.status == INFECTED for cell in item[0][0])))
        for (next_state, next_budget, next_days, must_burn), cost in ordered:
            bound = model.unavoidable_deaths(next_state, next_days, count_burned)
            if cost + bound >= best:
                continue
            best = min(best, cost + solve(next_state, next_budget, next_days, must_burn))
            if best == lower_bound:
                break
        return best

    return initial_dead_count(grid) + solve(state, budget, horizon, require_one_burn)


HEALTHY_CELL, SPREAD_SAFE, SPREAD_DOOMED, SAFE_CELL, DEATH_COUNTED = range(5)


def min_deaths_daily_fast(grid, D, K, *, allow_no_burn=True):
    """统计最终全部死亡时，传播一次并提前记账，使用五种格子状态。"""
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    model = FixedLifetime(rows, cols, D, K)
    initial = model.initial(grid)
    initial_deaths = sum(cell.status == DEAD or cell.will_die for cell in initial)
    state = tuple(
        HEALTHY_CELL if cell.status == HEALTHY else
        (SPREAD_DOOMED if cell.will_die else SPREAD_SAFE) if cell.status == INFECTED else
        SAFE_CELL if cell.status == IMMUNE else DEATH_COUNTED
        for cell in initial
    )

    def burn_line(state, action):
        if action is None:
            return state, 0
        result = list(state)
        additional_deaths = 0
        for i in model.lines[action]:
            # 已经记过必死费用的格子，被烧时不能再加一。
            additional_deaths += state[i] in (HEALTHY_CELL, SPREAD_SAFE, SAFE_CELL)
            result[i] = DEATH_COUNTED
        return tuple(result), additional_deaths

    def spread_once(state):
        result = list(state)
        additional_deaths = 0
        for i, cell in enumerate(state):
            if cell in (SPREAD_SAFE, SPREAD_DOOMED):
                result[i] = SAFE_CELL if cell == SPREAD_SAFE else DEATH_COUNTED
            elif cell == HEALTHY_CELL:
                infected_neighbors = sum(state[j] in (SPREAD_SAFE, SPREAD_DOOMED)
                                         for j in model.neighbors[i])
                if infected_neighbors > 0:
                    doomed = infected_neighbors >= K
                    result[i] = SPREAD_DOOMED if doomed else SPREAD_SAFE
                    additional_deaths += doomed
        return tuple(result), additional_deaths

    def deaths_if_no_more_burns(state):
        # 已有必死费用已经计入，复用 BFS 时只计算未来新感染的死亡。
        original_state = tuple(
            Cell(HEALTHY) if cell == HEALTHY_CELL else
            Cell(INFECTED, D, False) if cell in (SPREAD_SAFE, SPREAD_DOOMED) else
            Cell(IMMUNE) if cell == SAFE_CELL else Cell(DEAD)
            for cell in state
        )
        return model.deaths_without_burn(original_state)

    if not any(cell.status == INFECTED for cell in initial):
        return initial_deaths
    if D == 1:
        extra = 0 if allow_no_burn else min(burn_line(state, action)[1] for action in model.actions)
        return initial_deaths + extra

    @cache
    def solve(state, first_burn_required):
        if not any(cell in (SPREAD_SAFE, SPREAD_DOOMED) for cell in state):
            return 0

        # 第一次烧出的整条死线可以重复选，此后允许零效果动作。
        best = inf if first_burn_required else deaths_if_no_more_burns(state)
        if best == 0:
            return 0
        actions = list(model.actions) + ([] if first_burn_required else [None])
        successors = {}
        for action in actions:
            burned, burn_deaths = burn_line(state, action)
            if burn_deaths >= best:
                continue
            next_state, new_doomed = spread_once(burned)
            cost = burn_deaths + new_doomed
            successors[next_state] = min(cost, successors.get(next_state, inf))
        for next_state, cost in sorted(successors.items(), key=lambda pair: pair[1]):
            if cost < best:
                best = min(best, cost + solve(next_state, False))
                if best == 0:
                    break
        return best

    return initial_deaths + solve(state, not allow_no_burn)


def minimum_deaths(grid, D, K):
    # 练习主线只统计最终全部死亡，满足省掉计时器的条件。
    return min_deaths_daily_fast(grid, D, K)
