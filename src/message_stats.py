import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import Column, Integer, String, DateTime, func
from src.checkin import Base
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes
from redis import Redis

# Redis连接
redis_conn = Redis(host='localhost', port=6379, db=2)

class MessageStats:
    """消息统计核心类"""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def record_message(self, update: Update):
        """记录用户消息"""
        try:
            from src.monitoring.system_monitor import SystemMonitor
            SystemMonitor.REQUEST_COUNT.inc()
            
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Redis实时计数
            redis_conn.zincrby(
                f"chat:{chat_id}:activity",
                1,
                str(user.id)
            )
            
            # 批量写入数据库
            if self._should_flush():
                self._flush_to_db()
                
        except Exception as e:
            self.logger.error(f"记录消息失败: {e}")

    def _should_flush(self) -> bool:
        """检查是否需要批量写入数据库"""
        return redis_conn.llen("message_queue") > 100

    def _flush_to_db(self):
        """批量写入数据库"""
        messages = []
        while redis_conn.llen("message_queue") > 0:
            msg_data = redis_conn.lpop("message_queue")
            if msg_data:
                messages.append(json.loads(msg_data))
        
        if messages:
            # 批量插入数据库
            self.session.bulk_insert_mappings(MessageRecord, messages)
            self.session.commit()

    def get_leaderboard(self, chat_id: int, limit: int = 10) -> List[Dict]:
        """获取活跃度排行榜"""
        # 从Redis获取实时排名
        rankings = redis_conn.zrevrange(
            f"chat:{chat_id}:activity",
            0,
            limit-1,
            withscores=True
        )
        
        return [
            {"user_id": int(uid.decode()), "count": int(count)}
            for uid, count in rankings
        ]

    def generate_daily_report(self, chat_id: int):
        """生成每日报表"""
        # 获取24小时数据
        stats = self.session.query(
            MessageRecord.user_id,
            func.count(MessageRecord.id).label('count')
        ).filter(
            MessageRecord.chat_id == chat_id,
            MessageRecord.timestamp >= datetime.now() - timedelta(days=1)
        ).group_by(
            MessageRecord.user_id
        ).order_by(
            func.count(MessageRecord.id).desc()
        ).limit(10).all()
        
        return stats

# 数据库模型
class MessageRecord(Base):
    """消息记录表"""
    __tablename__ = 'message_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    message_length = Column(Integer)