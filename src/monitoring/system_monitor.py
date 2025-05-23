import logging
import os
import psutil
from time import sleep
from threading import Thread
from prometheus_client import start_http_server, Gauge, Counter
from telegram import Bot
from datetime import datetime

class SystemMonitor:
    """系统监控核心类"""
    
    # 定义监控指标
    CPU_USAGE = Gauge('cpu_usage', 'CPU使用率百分比')
    MEMORY_USAGE = Gauge('memory_usage', '内存使用率百分比')
    REQUEST_COUNT = Counter('http_requests_total', 'HTTP请求总数')
    ERROR_COUNT = Counter('errors_total', '系统错误总数')

    def __init__(self, telegram_token: str):
        self.logger = logging.getLogger(__name__)
        self.bot = Bot(token=telegram_token)
        self.alert_channels = []
        self._running = False
        
        # 从环境变量加载配置
        self.prometheus_port = int(os.getenv('PROMETHEUS_PORT', '8000'))
        self.cpu_alert_threshold = int(os.getenv('CPU_ALERT_THRESHOLD', '90'))
        self.memory_alert_threshold = int(os.getenv('MEMORY_ALERT_THRESHOLD', '85'))

    def start(self):
        """启动监控系统"""
        # 启动Prometheus指标服务器
        start_http_server(self.prometheus_port)
        self.logger.info(f"Prometheus指标服务器启动在 {self.prometheus_port} 端口")
        
        # 启动监控线程
        self._running = True
        monitor_thread = Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def stop(self):
        """停止监控系统"""
        self._running = False

    def add_alert_channel(self, channel_type: str, config: dict):
        """添加报警通道"""
        self.alert_channels.append({
            'type': channel_type,
            'config': config
        })

    def _monitor_loop(self):
        """监控主循环"""
        while self._running:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent()
                mem_percent = psutil.virtual_memory().percent
                
                # 更新Prometheus指标
                self.CPU_USAGE.set(cpu_percent)
                self.MEMORY_USAGE.set(mem_percent)
                
                # 检查异常条件
                if cpu_percent > self.cpu_alert_threshold:
                    self._trigger_alert(
                        f"CPU使用率超过阈值({self.cpu_alert_threshold}%): {cpu_percent}%",
                        severity="high"
                    )
                
                if mem_percent > self.memory_alert_threshold:
                    self._trigger_alert(
                        f"内存使用率超过阈值({self.memory_alert_threshold}%): {mem_percent}%", 
                        severity="medium"
                    )
                
                # 每5秒采集一次
                sleep(5)
                
            except Exception as e:
                self.logger.error(f"监控采集失败: {e}")
                self.ERROR_COUNT.inc()

    def _trigger_alert(self, message: str, severity: str = "medium"):
        """触发报警"""
        self.logger.warning(f"系统报警: {message}")
        
        # 发送到所有报警通道
        for channel in self.alert_channels:
            try:
                if channel['type'] == 'telegram':
                    self._send_telegram_alert(
                        channel['config']['chat_id'],
                        f"[{severity.upper()}] {message}"
                    )
                elif channel['type'] == 'email':
                    self._send_email_alert(
                        channel['config']['recipient'],
                        message,
                        severity
                    )
            except Exception as e:
                self.logger.error(f"发送报警失败: {e}")

    def _send_telegram_alert(self, chat_id: str, message: str):
        """发送Telegram报警"""
        self.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 系统报警\n{message}\n时间: {datetime.now()}"
        )

    def _send_email_alert(self, recipient: str, message: str, severity: str):
        """发送邮件报警"""
        # 实现邮件发送逻辑
        pass

    def health_check(self):
        """健康检查端点"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent
            }
        }