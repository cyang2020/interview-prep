import heapq
import time
from collections import deque
from enum import Enum


class State(Enum):
    READY = "ready"          # 可领取
    RESERVED = "reserved"    # 已被某个 worker 领走，正在执行
    COMPLETED = "completed"  # 做成了，终态
    DEAD = "dead"            # 次数用完，进了 DLQ，终态


class Job:
    def __init__(self, job_id, timeout, max_retry):
        self.job_id = job_id
        self.state = State.READY
        self.attempts = 0                   # 被领走过几次
        self.timeout = timeout              # 领走后多少秒内必须汇报
        self.max_attempts = max_retry + 1   # 口径：max_retry 是失败后再试几次
        self.token = 0                      # 当前这次领取的编号，每次 reserve 加 1
        self.deadline = None                # 当前这次领取的到期时刻


class WorkQueue:
    def __init__(self, clock=time.monotonic):
        self.jobs = {}        # job_id -> Job，唯一的记录，所有判断以它为准
        self.ready = deque()  # 可领取的 job_id，按入队顺序，只是索引
        self.clock = clock    # 返回"现在几点"的函数，测试里换成假时钟
        self.leases = []      # 最小堆，(deadline, job_id, token)，只是索引
        self.dlq = []         # 进了 DLQ 的 job_id，按进入先后

    def enqueue(self, job_id, timeout, max_retry):
        self._expire_leases()
        if job_id in self.jobs:
            return False
        self.jobs[job_id] = Job(job_id, timeout, max_retry)
        self.ready.append(job_id)
        return True

    def reserve(self, job_id=None):
        self._expire_leases()
        if job_id is None:                     # 另一版本的接口：不指名，发下一个
            job_id = self._next_ready()
            if job_id is None:
                return None
        job = self.jobs.get(job_id)
        if job is None or job.state != State.READY:
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
            job.state = State.DEAD
            self.dlq.append(job.job_id)

    def _expire_leases(self):
        # 每个公开方法开头都先调一次：把已经到期的领取处理掉
        now = self.clock()
        while self.leases and self.leases[0][0] <= now:
            _, job_id, token = heapq.heappop(self.leases)
            job = self.jobs[job_id]
            if job.state != State.RESERVED or job.token != token:
                continue      # 旧条目：这次领取早就 pass/fail 过了，丢掉
            self._attempt_failed(job)
