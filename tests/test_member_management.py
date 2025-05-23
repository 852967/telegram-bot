import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.member_management import MemberManager
from src.checkin import Base

class TestMemberManagement(unittest.IsolatedAsyncioTestCase):
    """测试成员管理功能"""
    
    def setUp(self):
        """创建测试数据库"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Mock Redis连接
        self.redis_patch = patch('src.member_management.redis_conn')
        self.mock_redis = self.redis_patch.start()
        
        # 创建测试用户
        self.user = MagicMock()
        self.user.id = 123
        self.user.username = 'test_user'
        
        # 模拟消息
        self.update = MagicMock()
        self.update.effective_user = self.user
        self.update.message = AsyncMock()
        self.update.effective_chat.id = 456
        
        # 模拟上下文
        self.context = MagicMock()
        self.context.bot = AsyncMock()
        
    def tearDown(self):
        self.redis_patch.stop()
        self.engine.dispose()
    
    async def test_ban_member_success(self):
        """测试成功封禁成员"""
        # 设置管理员权限
        admin = MagicMock()
        admin.user.id = self.user.id
        self.update.effective_chat.get_administrators = AsyncMock(
            return_value=[admin]
        )
        
        manager = MemberManager(self.Session())
        result = await manager.ban_member(
            self.update, 
            self.context,
            user_id=789,
            reason="测试封禁"
        )
        
        self.assertTrue(result)
        self.context.bot.ban_chat_member.assert_awaited_once()
        self.update.message.reply_text.assert_awaited_once()
        
    async def test_ban_permission_denied(self):
        """测试无权限封禁"""
        self.update.effective_chat.get_administrators = AsyncMock(
            return_value=[]  # 无管理员权限
        )
        
        manager = MemberManager(self.Session())
        result = await manager.ban_member(
            self.update,
            self.context,
            user_id=789
        )
        
        self.assertFalse(result)
        self.update.message.reply_text.assert_awaited_with("❌ 需要管理员权限")
        
    async def test_mute_member(self):
        """测试禁言功能"""
        # 设置管理员权限
        admin = MagicMock()
        admin.user.id = self.user.id
        self.update.effective_chat.get_administrators = AsyncMock(
            return_value=[admin]
        )
        
        manager = MemberManager(self.Session())
        result = await manager.mute_member(
            self.update,
            self.context,
            user_id=789,
            duration=3600,
            reason="测试禁言"
        )
        
        self.assertTrue(result)
        self.context.bot.restrict_chat_member.assert_awaited_once()
        self.mock_redis.setex.assert_called_once()

if __name__ == '__main__':
    unittest.main()