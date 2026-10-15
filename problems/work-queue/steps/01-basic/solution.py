from collections import deque
from enum import Enum


class State(Enum):
    READY = "ready"          # 可领取
    RESERVED = "reserved"    # 已被某个 worker 领走，正在执行
    COMPLETED = "completed"  # 做成了，终态


class Job:
    def __init__(self, job_id, timeout, max_retry):
        self.job_id = job_id
        self.state = State.READY
        self.attempts = 0                   # 被领走过几次
        self.timeout = timeout              # 第一问不用，先存着
        self.max_retry = max_retry          # 第一问不用，先存着


class WorkQueue:
    def __init__(self):
        self.jobs = {}        # job_id -> Job，唯一的记录，所有判断以它为准
        self.ready = deque()  # 可领取的 job_id，按入队顺序，只是索引

    def enqueue(self, job_id, timeout, max_retry):
        if job_id in self.jobs:
            return False
        self.jobs[job_id] = Job(job_id, timeout, max_retry)
        self.ready.append(job_id)
        return True

    def reserve(self, job_id=None):
        if job_id is None:                     # 另一版本的接口：不指名，发下一个
            job_id = self._next_ready()
            if job_id is None:
                return None
        job = self.jobs.get(job_id)
        if job is None or job.state != State.READY:
            return None
        job.state = State.RESERVED
        job.attempts += 1
        return job.job_id

    def pass_(self, job_id):
        job = self.jobs.get(job_id)
        if job is None or job.state != State.RESERVED:
            return False
        job.state = State.COMPLETED
        return True

    def fail(self, job_id):
        job = self.jobs.get(job_id)
        if job is None or job.state != State.RESERVED:
            return False
        job.state = State.READY
        self.ready.append(job_id)
        return True

    def get_dlq(self):
        return []             # 第一问没有 DLQ

    def _next_ready(self):
        # ready 里可能留着已被指名领走的 job_id，弹出来要对照 jobs 里的状态
        while self.ready:
            job_id = self.ready.popleft()
            if self.jobs[job_id].state == State.READY:
                return job_id
        return None
