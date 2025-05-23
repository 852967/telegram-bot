import json
import logging
from datetime import datetime
from typing import Optional
from telegram import ChatPermissions
from telegram import Update, User
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from sqlalchemy.orm import Session
from redis import Redis

# 初始化Redis连接
redis_conn = Redis(host='localhost', port=6379, db=1)

class MemberManager:
    """成员管理核心类"""
    
    def __init__(self, session_factory):
        self.get_session = session_factory
        self.logger = logging.getLogger(__name__)

    async def ban_member(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        reason: Optional[str] = None
    ):
        """封禁群成员"""
        try:
            from src.monitoring.system_monitor import SystemMonitor
            
            # 权限验证
            if not await self._check_admin_permission(update):
                await update.message.reply_text("❌ 需要管理员权限")
                return False
            
            # 执行封禁
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            )
            
            # 记录管理操作
            SystemMonitor.REQUEST_COUNT.inc()
            
            # 记录日志
            self._log_action(
                action='ban',
                operator=update.effective_user.id,
                target=user_id,
                reason=reason
            )
            
            await update.message.reply_text(
                f"✅ 用户 {user_id} 已被封禁\n"
                f"原因: {reason or '违反群规'}"
            )
            return True
            
        except BadRequest as e:
            self.logger.error(f"封禁失败: {e}")
            await update.message.reply_text("封禁操作失败")
            return False

    async def mute_member(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        duration: int = 3600,
        reason: Optional[str] = None
    ):
        """禁言群成员"""
        try:
            # 权限验证
            if not await self._check_admin_permission(update):
                await update.message.reply_text("❌ 需要管理员权限")
                return False
                
            # 执行禁言
            until_date = int(datetime.now().timestamp()) + duration
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False
                ),
                until_date=until_date
            )
            
            # 记录到Redis
            redis_conn.setex(
                f"mute:{update.effective_chat.id}:{user_id}",
                duration,
                str(reason)
            )
            
            await update.message.reply_text(
                f"⏳ 用户 {user_id} 已被禁言 {duration//3600}小时\n"
                f"原因: {reason or '违反发言规则'}"
            )
            return True
            
        except BadRequest as e:
            self.logger.error(f"禁言失败: {e}")
            await update.message.reply_text("禁言操作失败")
            return False

    async def _check_admin_permission(self, update: Update) -> bool:
        """验证管理员权限"""
        admins = await update.effective_chat.get_administrators()
        return update.effective_user.id in [admin.user.id for admin in admins]

    def _log_action(self, action: str, operator: int, target: int, reason: Optional[str]):
        """记录管理操作日志"""
        log_entry = {
            'action': action,
            'operator': operator,
            'target': target,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        # 写入数据库
        # 同时写入Redis缓存
        redis_conn.rpush(
            'admin_actions',
            json.dumps(log_entry)
        )

# 工具函数
async def parse_user_reference(message_text: str) -> Optional[int]:
    """解析消息中的用户引用"""
    # 匹配 @用户名 或 user_id
    match = re.search(r'(?:@(\w+)|(\d+))', message_text)
    if match:
        return int(match.group(2)) if match.group(2) else match.group(1)
    return None