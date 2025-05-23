import pytest
from unittest.mock import MagicMock, patch
from src.monitoring.system_monitor import SystemMonitor

class TestMonitorExceptions:
    """监控系统异常处理测试"""
    
    @pytest.fixture
    def monitor(self):
        with patch('src.monitoring.system_monitor.Bot'):
            return SystemMonitor("test_token")

    @pytest.mark.asyncio
    async def test_alert_channel_failure(self, monitor):
        """测试报警通道失败处理"""
        monitor.alert_channels = [{
            'type': 'telegram',
            'config': {'chat_id': 'test_chat'}
        }]
        
        # 模拟发送失败
        monitor.bot.send_message.side_effect = Exception("API error")
        
        # 应捕获异常不中断程序
        await monitor._trigger_alert("Test alert")
        
        # 验证错误日志记录
        assert "发送报警失败" in monitor.logger.method_calls[0][1][0]

    @pytest.mark.asyncio 
    async def test_high_load_handling(self, monitor):
        """测试高负载处理"""
        with patch('psutil.cpu_percent', return_value=99):
            with patch.object(monitor, '_trigger_alert') as mock_alert:
                await monitor._monitor_loop()
                mock_alert.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_health_check_failure(self, monitor):
        """测试健康检查异常"""
        with patch('psutil.cpu_percent', side_effect=Exception("Monitor error")):
            status = monitor.health_check()
            assert status["status"] == "unhealthy"

