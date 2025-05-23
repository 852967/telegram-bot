from prometheus_client import Counter, Histogram, Gauge
from typing import Optional
import time

class TaskMetrics:
    """任务监控指标收集"""
    
    def __init__(self):
        # 定义Prometheus指标
        self.task_retries = Counter(
            'task_retries_total',
            '任务重试次数',
            ['task_name']
        )
        self.task_duration = Histogram(
            'task_duration_seconds',
            '任务执行耗时',
            ['task_name'],
            buckets=(0.1, 0.5, 1, 5, 10, 30, 60)
        )
        self.task_failures = Counter(
            'task_failures_total',
            '任务失败次数',
            ['task_name', 'error_type']
        )
        self.active_tasks = Gauge(
            'active_tasks',
            '当前活跃任务数'
        )

    def track_task(self, task_name: str):
        """任务执行跟踪上下文"""
        return TaskTracker(self, task_name)

class TaskTracker:
    """单个任务执行跟踪"""
    
    def __init__(self, metrics: TaskMetrics, task_name: str):
        self.metrics = metrics
        self.task_name = task_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.metrics.active_tasks.inc()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 记录执行时长
        duration = time.time() - self.start_time
        self.metrics.task_duration.labels(
            task_name=self.task_name
        ).observe(duration)
        
        # 记录失败
        if exc_type is not None:
            error_type = exc_type.__name__
            self.metrics.task_failures.labels(
                task_name=self.task_name,
                error_type=error_type
            ).inc()
            
        self.metrics.active_tasks.dec()
        return False