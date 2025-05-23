import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.checkin import handle_checkin
from sqlalchemy.exc import SQLAlchemyError

class TestCheckinExceptions:
    """签到系统异常测试"""
    
    @pytest.fixture
    def mock_env(self):
        with patch('src.checkin.get_session') as mock_session:
            mock_session.return_value = MagicMock()
            yield

    @pytest.mark.asyncio
    async def test_duplicate_checkin(self, mock_env):
        """测试重复签到处理"""
        update = MagicMock()
        update.effective_user.id = 123
        context = MagicMock()
        
        # 模拟已签到
        with patch('src.checkin.redis_conn.exists', return_value=1):
            await handle_checkin(update, context)
            update.message.reply_text.assert_called_with("今天已经签到过了哦~")

    @pytest.mark.asyncio
    async def test_db_failure(self, mock_env):
        """测试数据库故障"""
        update = MagicMock()
        context = MagicMock()
        
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("DB error")
        with patch('src.checkin.get_session', return_value=mock_session):
            await handle_checkin(update, context)
            update.message.reply_text.assert_called_with("签到失败，请稍后再试~")

    @pytest.mark.asyncio
    async def test_redis_failure(self, mock_env):
        """测试Redis故障"""
        update = MagicMock()
        context = MagicMock()
        
        with patch('src.checkin.redis_conn.incr', side_effect=Exception("Redis error")):
            await handle_checkin(update, context)
            assert "签到失败" in str(update.message.reply_text.call_args)