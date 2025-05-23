import logging
from datetime import datetime
from typing import Optional, Dict
from telegram import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackContext
from sqlalchemy.orm import Session
from redis import Redis

# Redis连接
redis_conn = Redis(host='localhost', port=6379, db=3)

class WelcomeSystem:
    """新人欢迎系统"""
    
    DEFAULT_WELCOME = (
        "欢迎新成员 {username}！\n\n"
        "请阅读群规：\n"
        "1. 禁止广告\n"
        "2. 保持友善\n"
        "3. 遵守法律法规"
    )

    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def handle_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理新成员加入事件"""
        try:
            from src.monitoring.system_monitor import SystemMonitor
            SystemMonitor.REQUEST_COUNT.inc()
            
            if not update.message or not update.message.new_chat_members:
                return

            chat_id = update.effective_chat.id
            for new_member in update.message.new_chat_members:
                # 获取群组自定义欢迎语
                welcome_text = self._get_welcome_message(chat_id)
                
                # 替换模板变量
                formatted_text = welcome_text.format(
                    username=new_member.username or new_member.full_name,
                    user_id=new_member.id
                )
                
                # 发送欢迎消息
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    reply_markup=self._get_welcome_buttons(chat_id)
                )
                
                # 记录新人加入
                self._log_new_member(chat_id, new_member.id)

        except Exception as e:
            self.logger.error(f"欢迎新成员失败: {e}")

    def _get_welcome_message(self, chat_id: int) -> str:
        """获取群组欢迎语"""
        custom_msg = redis_conn.get(f"welcome:{chat_id}")
        return custom_msg.decode() if custom_msg else self.DEFAULT_WELCOME

    def _get_welcome_buttons(self, chat_id: int) -> Optional[InlineKeyboardMarkup]:
        """获取欢迎按钮"""
        # 检查是否启用验证
        if redis_conn.sismember("verified_chats", chat_id):
            keyboard = [
                [InlineKeyboardButton("我已阅读群规", callback_data=f"verify_{chat_id}")]
            ]
            return InlineKeyboardMarkup(keyboard)
        return None

    def _log_new_member(self, chat_id: int, user_id: int):
        """记录新成员"""
        redis_conn.hset(
            f"new_members:{chat_id}",
            str(user_id),
            str(datetime.now())
        )

    async def verify_member(self, update: Update, context: CallbackContext):
        """处理新人验证"""
        query = update.callback_query
        await query.answer()
        
        chat_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        
        # 验证是新成员
        if redis_conn.hexists(f"new_members:{chat_id}", str(user_id)):
            # 标记为已验证
            redis_conn.hdel(f"new_members:{chat_id}", str(user_id))
            await query.edit_message_text("✅ 验证成功，欢迎加入群聊！")

    def set_welcome_message(self, chat_id: int, message: str):
        """设置自定义欢迎语"""
        redis_conn.set(f"welcome:{chat_id}", message)