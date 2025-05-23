# API参考文档

## 监控指标端点

默认端口: `8000`

### `GET /metrics`
返回Prometheus格式的监控指标数据

**端口配置**:
```yaml
# 默认监控端点
http://localhost:8000/metrics
```

**示例响应**:
```
# HELP task_retries_total 任务重试次数
# TYPE task_retries_total counter
task_retries_total{task_name="daily_report"} 3

# HELP task_duration_seconds 任务执行耗时
# TYPE task_duration_seconds histogram
task_duration_seconds_bucket{task_name="daily_report",le="1"} 2
```

## 任务调度API

### 重试策略
```python
{
    "max_retries": 3,
    "backoff_factor": 5,  # 秒
    "max_wait": 60  # 最大等待时间(秒)
}
```

## 健康检查端点

### `GET /health`
返回系统健康状态

**响应示例**:
```json
{
    "status": "healthy",
    "metrics": {
        "active_tasks": 2,
        "last_error": null
    }
}
```