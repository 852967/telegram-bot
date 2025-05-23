# 监控系统使用指南

## 监控指标

### 系统指标
- `cpu_usage`: CPU使用率百分比
- `memory_usage`: 内存使用率百分比
- `http_requests_total`: HTTP请求总数
- `errors_total`: 系统错误总数

### 业务指标
- `user_checkins_total`: 用户签到次数
- `messages_count`: 消息处理数量
- `admin_actions`: 管理操作次数

## 报警配置

### 报警阈值设置
在`.env`文件中配置:
```ini
CPU_ALERT_THRESHOLD=90      # CPU报警阈值(%)
MEMORY_ALERT_THRESHOLD=85   # 内存报警阈值(%)
```

### 报警通道
当前支持的报警通道:
1. Telegram通知
   ```python
   monitor.add_alert_channel('telegram', {
       'chat_id': '管理员ChatID'
   })
   ```

## Grafana仪表板

1. 添加Prometheus数据源:
   - URL: `http://localhost:9090`
   - Type: Prometheus

2. 导入默认仪表板:
   ```json
   {
     "dashboard": "机器人监控",
     "panels": [
       {
         "title": "CPU使用率",
         "targets": [{"expr": "cpu_usage"}]
       }
     ]
   }
   ```
   ```

## 常见问题

### 指标不更新
1. 检查Prometheus是否正常运行
2. 验证端口配置(默认8000)
3. 检查防火墙设置

### 报警未触发
1. 确认阈值设置
2. 检查Telegram token配置
3. 查看日志文件
```