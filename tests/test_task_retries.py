import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.task_scheduler import TaskScheduler
import asyncio

class TestTaskRetries:
    """Test task retry mechanisms"""
    
    @pytest.fixture
    def scheduler(self, monkeypatch):
        # Mock整个TaskMetrics类
        mock_metrics = MagicMock()
        tracker = MagicMock()
        mock_metrics.track_task.return_value = tracker
        
        monkeypatch.setattr(
            'src.task_scheduler.TaskMetrics',
            lambda: mock_metrics
        )
        
        app = MagicMock()
        app.session = MagicMock()
        scheduler = TaskScheduler(app)
        scheduler._get_active_chats = MagicMock(return_value=[123])
        return scheduler

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, scheduler):
        """Test task retry logic"""
        with patch.object(scheduler, '_send_report', side_effect=Exception("DB error")) as mock_send:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with patch.object(scheduler, '_log_task_failure') as mock_log:
                    await scheduler._generate_daily_report()
                    
                    assert mock_send.call_count == 4  # 0(首次) + 3次重试
                    assert mock_log.call_count == 1  # 最终失败记录
                    assert mock_sleep.call_count == 4  # 首次+3次重试
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_backoff_strategy(self, scheduler):
        """Test exponential backoff"""
        with patch.object(scheduler, '_send_report', side_effect=Exception("DB error")):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await scheduler._generate_daily_report()
                
                assert mock_sleep.call_args_list[0][0][0] == 5  # 2^0*5
                assert mock_sleep.call_args_list[1][0][0] == 10  # 2^1*5 
                assert mock_sleep.call_args_list[2][0][0] == 20  # 2^2*5