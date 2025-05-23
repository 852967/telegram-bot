import unittest
from unittest.mock import MagicMock, patch
from src.monitoring.system_monitor import SystemMonitor

class TestSystemMonitor(unittest.TestCase):
    """测试系统监控功能"""
    
    def setUp(self):
        """创建测试实例"""
        with patch('prometheus_client.start_http_server'):
            self.monitor = SystemMonitor("test_token")
            self.monitor.bot = MagicMock()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_monitor_loop(self, mock_mem, mock_cpu):
        """测试监控循环"""
        # 设置mock返回值
        mock_cpu.return_value = 50
        mock_mem.return_value.percent = 60
        
        # 启动监控
        self.monitor._running = True
        self.monitor._monitor_loop()
        
        # 验证指标更新
        self.assertEqual(self.monitor.CPU_USAGE._value.get(), 50)
        self.assertEqual(self.monitor.MEMORY_USAGE._value.get(), 60)
    
    def test_alert_trigger(self):
        """测试报警触发"""
        # 添加Telegram报警通道
        self.monitor.add_alert_channel('telegram', {
            'chat_id': 'test_chat'
        })
        
        # 触发报警
        self.monitor._trigger_alert("Test alert")
        
        # 验证报警发送
        self.monitor.bot.send_message.assert_called_once()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_health_check(self, mock_mem, mock_cpu):
        """测试健康检查"""
        mock_cpu.return_value = 30
        mock_mem.return_value.percent = 40
        
        health = self.monitor.health_check()
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['metrics']['cpu_usage'], 30)
        self.assertEqual(health['metrics']['memory_usage'], 40)

if __name__ == '__main__':
    unittest.main()