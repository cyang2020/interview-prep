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

    # 后续的到期规则放在首次传播之前处理。
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
