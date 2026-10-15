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

    while queue:
        row, col = queue.popleft()
        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            if (0 <= r < rows and 0 <= c < cols
                    and grid[r][c] == 0 and infection_day[r][c] == -1):
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
