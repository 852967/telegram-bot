import unittest
from unittest.mock import AsyncMock, MagicMock
from src.main import start

class TestBasicFunctions(unittest.IsolatedAsyncioTestCase):
    async def test_start_command(self):
        """测试/start命令响应"""
        update = MagicMock()
        context = MagicMock()
        
        # 使用AsyncMock模拟异步方法
        update.message = MagicMock()
        update.message.reply_text = AsyncMock(return_value=None)
        
        # 调用异步处理函数
        await start(update, context)
        
        # 验证回复是否正确
        update.message.reply_text.assert_awaited_once_with('欢迎使用群管机器人!')

if __name__ == '__main__':
    unittest.main()