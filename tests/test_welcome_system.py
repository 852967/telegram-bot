import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.welcome_system import WelcomeSystem
from src.checkin import Base

class TestWelcomeSystem(unittest.IsolatedAsyncioTestCase):
    """测试欢迎系统功能"""
    
    def setUp(self):
        """创建测试数据库"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Mock Redis连接
        self.redis_patch = patch('src.welcome_system.redis_conn')
        self.mock_redis = self.redis_patch.start()
        self.mock_redis.get.return_value = None  # 默认返回空欢迎语
        self.mock_redis.sismember.return_value = False  # 默认不启用验证
        
        # 模拟新成员消息
        self.update = MagicMock()
        self.chat = MagicMock()
        self.chat.id = 123
        self.update.effective_chat = self.chat
        
        self.new_member = MagicMock()
        self.new_member.id = 456
        self.new_member.username = "test_user"
        self.new_member.full_name = "Test User"
        
        self.update.message = MagicMock()
        self.update.message.new_chat_members = [self.new_member]
        
        # 模拟上下文
        self.context = MagicMock()
        self.context.bot = AsyncMock()
    
    def tearDown(self):
        self.redis_patch.stop()
        self.engine.dispose()
    
    async def test_handle_new_member(self):
        """测试处理新成员"""
        system = WelcomeSystem(self.Session())
        await system.handle_new_member(self.update, self.context)
        
        # 验证发送了欢迎消息
        self.context.bot.send_message.assert_awaited_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs['chat_id'], 123)
        self.assertIn("test_user", kwargs['text'])
        
    async def test_custom_welcome(self):
        """测试自定义欢迎语"""
        custom_msg = "欢迎{username}"
        self.mock_redis.get.return_value = custom_msg.encode('utf-8')
        system = WelcomeSystem(self.Session())
        
        await system.handle_new_member(self.update, self.context)
        
        # 验证使用了自定义欢迎语
        self.context.bot.send_message.assert_awaited_once()
        _, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs['text'], custom_msg.format(username="test_user"))

if __name__ == '__main__':
    unittest.main()