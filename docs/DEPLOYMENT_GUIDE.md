# Telegram群管机器人部署指南

## 1. 环境准备

### 系统要求
- Python 3.10+
- Redis 6.2+
- SQLite 3.32+

### 依赖安装
```bash
pip install -r requirements.txt
```

## 2. 监控系统配置

### Prometheus设置
```yaml
# config/prometheus.yml
scrape_configs:
  - job_name: 'telegram_bot'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']  # 监控端口
```

### 告警规则示例
```yaml
# config/alerts.yml
groups:
- name: task_alerts
  rules:
  - alert: HighTaskFailure
    expr: rate(task_failures_total[5m]) > 0.1
    for: 10m
    labels:
      severity: 'warning'
```

### Grafana看板
1. 导入仪表板ID: 13759
2. 配置Prometheus数据源
3. 设置变量: `$task_name`

## 3. 服务启动

### 开发模式
```bash
python src/main.py
```

### 生产模式
```bash
pm2 start src/main.py --interpreter python
```

## 4. 维护操作

### 日志管理
```bash
# 查看日志
pm2 logs
```

### 数据备份
```bash
# 备份SQLite数据库
sqlite3 db/telegram_bot.db ".backup backup/telegram_bot.db"
```