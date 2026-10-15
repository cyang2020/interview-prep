import heapq
import time
from collections import deque
from enum import Enum


class State(Enum):
    READY = "ready"          # 可领取
    RESERVED = "reserved"    # 已被某个 worker 领走，正在执行
    COMPLETED = "completed"  # 做成了，终态
    DEAD = "dead"            # 次数用完，进了 DLQ，终态
    BLOCKED = "blocked"      # 还有前置任务没完成，不能领


class Job:
    def __init__(self, job_id, timeout, max_retry):
        self.job_id = job_id
        self.state = State.READY
        self.attempts = 0                   # 被领走过几次
        self.timeout = timeout              # 领走后多少秒内必须汇报
        self.max_attempts = max_retry + 1   # 口径：max_retry 是失败后再试几次
        self.token = 0                      # 当前这次领取的编号，每次 reserve 加 1
        self.deadline = None                # 当前这次领取的到期时刻
        self.remaining_deps = 0             # 还没完成的前置任务数


class WorkQueue:
    def __init__(self, clock=time.monotonic):
        self.jobs = {}        # job_id -> Job，唯一的记录，所有判断以它为准
        self.ready = deque()  # 可领取的 job_id，按入队顺序，只是索引
        self.clock = clock    # 返回"现在几点"的函数，测试里换成假时钟
        self.leases = []      # 最小堆，(deadline, job_id, token)，只是索引
        self.dlq = []         # 进了 DLQ 的 job_id，按进入先后
        self.dependents = {}  # 前置 job_id -> 等它的 job_id 列表（反向表）

    def enqueue(self, job_id, timeout, max_retry, depends_on=None):
        self._expire_leases()
        if job_id in self.jobs:
            return False
        deps = set(depends_on or [])                # 去重
        for dep in deps:
            if dep not in self.jobs:                # 前置必须已经入队，没有就拒绝
                return False
            if self.jobs[dep].state == State.DEAD:  # 前置已经放弃了，这个也做不了，拒绝
                return False
        job = Job(job_id, timeout, max_retry)
        self.jobs[job_id] = job
        for dep in deps:
            if self.jobs[dep].state != State.COMPLETED:
                job.remaining_deps += 1
                self.dependents.setdefault(dep, []).append(job_id)
        if job.remaining_deps > 0:
            job.state = State.BLOCKED               # 不进 ready 队列
            return True
        self.ready.append(job_id)
        return True

    def reserve(self, job_id=None):
        self._expire_leases()
        if job_id is None:                     # 另一版本的接口：不指名，发下一个
            job_id = self._next_ready()
            if job_id is None:
                return None
        job = self.jobs.get(job_id)
        if job is None or job.state != State.READY:   # blocked 的在这里被拒
            return None
        job.state = State.RESERVED
        job.attempts += 1
        job.token += 1
        job.deadline = self.clock() + job.timeout
        heapq.heappush(self.leases, (job.deadline, job.job_id, job.token))
        return job.job_id, job.token

    def pass_(self, job_id, token):
        self._expire_leases()
        job = self._current_reservation(job_id, token)
        if job is None:
            return False
        job.state = State.COMPLETED
        self._release_dependents(job)          # 只有这一处会放行等它的任务
        return True

    def fail(self, job_id, token):
        self._expire_leases()
        job = self._current_reservation(job_id, token)
        if job is None:
            return False
        self._attempt_failed(job)
        return True

    def get_dlq(self):
        self._expire_leases()
        return list(self.dlq)

    def _next_ready(self):
        # ready 里可能留着已被指名领走的 job_id，弹出来要对照 jobs 里的状态
        while self.ready:
            job_id = self.ready.popleft()
            if self.jobs[job_id].state == State.READY:
                return job_id
        return None

    def _current_reservation(self, job_id, token):
        # 只有"处于 reserved 且 token 是当前这次领取"的 pass/fail 才算数
        job = self.jobs.get(job_id)
        if job is None or job.state != State.RESERVED or job.token != token:
            return None
        return job

    def _attempt_failed(self, job):
        # fail 和超时共用：消耗了一次尝试，看还剩不剩
        if job.attempts < job.max_attempts:
            job.state = State.READY
            self.ready.append(job.job_id)
        else:
            self._mark_dead(job)

    def _expire_leases(self):
        # 每个公开方法开头都先调一次：把已经到期的领取处理掉
        now = self.clock()
        while self.leases and self.leases[0][0] <= now:
            _, job_id, token = heapq.heappop(self.leases)
            job = self.jobs[job_id]
            if job.state != State.RESERVED or job.token != token:
                continue      # 旧条目：这次领取早就 pass/fail 过了，丢掉
            self._attempt_failed(job)

    def _release_dependents(self, job):
        # job 刚刚变成 completed：等它的任务各减 1，减到 0 的放进 ready
        for dep_id in self.dependents.pop(job.job_id, []):
            dependent = self.jobs[dep_id]
            dependent.remaining_deps -= 1
            if dependent.remaining_deps == 0 and dependent.state == State.BLOCKED:
                dependent.state = State.READY
                self.ready.append(dep_id)

    def _mark_dead(self, job):
        # 进 DLQ；等它的任务永远等不到了，按选定的口径一起进 DLQ
        job.state = State.DEAD
        self.dlq.append(job.job_id)
        for dep_id in self.dependents.pop(job.job_id, []):
            dependent = self.jobs[dep_id]
            if dependent.state == State.BLOCKED:   # 可能已经因为别的前置进过 DLQ，只进一次
                self._mark_dead(dependent)
