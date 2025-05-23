import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.message_stats import MessageStats, MessageRecord
from src.checkin import Base

class TestMessageStats(unittest.IsolatedAsyncioTestCase):
    """测试消息统计功能"""
    
    def setUp(self):
        """创建测试数据库"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Mock Redis连接
        self.redis_patch = patch('src.message_stats.redis_conn')
        self.mock_redis = self.redis_patch.start()
        self.mock_redis.zincrby = MagicMock()
        self.mock_redis.llen = MagicMock(return_value=0)
        
        # 模拟消息
        self.update = MagicMock()
        self.user = MagicMock()
        self.user.id = 123
        self.update.effective_user = self.user
        self.update.effective_chat.id = 456
        self.update.message = AsyncMock()
        
    def tearDown(self):
        self.redis_patch.stop()
        self.engine.dispose()
    
    async def test_record_message(self):
        """测试记录消息"""
        stats = MessageStats(self.Session())
        await stats.record_message(self.update)
        
        # 验证Redis调用
        self.mock_redis.zincrby.assert_called_once_with(
            f"chat:456:activity",
            1,
            "123"
        )
    
    def test_get_leaderboard(self):
        """测试获取排行榜"""
        stats = MessageStats(self.Session())
        
        # 设置Redis模拟数据
        self.mock_redis.zrevrange.return_value = [
            (b"123", 10.0),
            (b"456", 5.0)
        ]
        
        rankings = stats.get_leaderboard(456)
        self.assertEqual(len(rankings), 2)
        self.assertEqual(rankings[0]["user_id"], 123)
        self.assertEqual(rankings[0]["count"], 10)

if __name__ == '__main__':
    unittest.main()