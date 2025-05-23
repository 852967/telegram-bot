import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.checkin import UserCheckIn, calculate_level, handle_checkin, Base

class TestCheckInSystem(unittest.IsolatedAsyncioTestCase):
    """测试签到系统"""
    
    def setUp(self):
        """创建测试数据库"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    async def test_first_checkin(self):
        """测试首次签到"""
        # 创建测试用户
        user = MagicMock()
        user.id = 123
        user.username = 'test_user'
        
        session = self.Session()
        mock_session_factory = MagicMock(return_value=session)
        
        update = MagicMock()
        update.effective_user = user
        update.message = AsyncMock()
        
        # 调用签到处理
        await handle_checkin(update, None, mock_session_factory)
        
        # 验证结果
        record = session.query(UserCheckIn).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.streak_days, 1)
        update.message.reply_text.assert_awaited_once()

    async def test_consecutive_checkin(self):
        """测试连续签到"""
        # 创建测试用户
        user = MagicMock()
        user.id = 123
        user.username = 'test_user'
        
        session = self.Session()
        # 添加昨天的签到记录
        yesterday = datetime.now().date() - timedelta(days=1)
        session.add(UserCheckIn(
            user_id=user.id,
            username=user.username,
            checkin_date=yesterday,
            streak_days=3,
            total_points=30
        ))
        session.commit()
        
        mock_session_factory = MagicMock(return_value=session)
        
        update = MagicMock()
        update.effective_user = user
        update.message = AsyncMock()
        
        # 调用签到处理
        await handle_checkin(update, None, mock_session_factory)
        
        # 验证结果
        record = session.query(UserCheckIn).filter_by(
            checkin_date=datetime.now().date()
        ).first()
        self.assertEqual(record.streak_days, 4)
        update.message.reply_text.assert_awaited_once()

    async def test_duplicate_checkin(self):
        """测试重复签到"""
        # 创建测试用户
        user = MagicMock()
        user.id = 123
        user.username = 'test_user'
        
        session = self.Session()
        # 添加今天的签到记录
        session.add(UserCheckIn(
            user_id=user.id,
            username=user.username,
            checkin_date=datetime.now().date(),
            streak_days=1,
            total_points=10
        ))
        session.commit()
        
        mock_session_factory = MagicMock(return_value=session)
        
        update = MagicMock()
        update.effective_user = user
        update.message = AsyncMock()
        
        # 调用签到处理
        await handle_checkin(update, None, mock_session_factory)
        
        # 验证拒绝重复签到
        update.message.reply_text.assert_awaited_once_with(
            f'@{user.username} 今天已经签到过了哦~'
        )

    def test_level_calculation(self):
        """测试等级计算"""
        self.assertEqual(calculate_level(50), 1)
        self.assertEqual(calculate_level(150), 2)
        self.assertEqual(calculate_level(950), 10)  # 测试上限

if __name__ == '__main__':
    unittest.main()