from collections import deque

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
