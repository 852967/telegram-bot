import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

# 数据库模型
Base = declarative_base()

class UserCheckIn(Base):
    """用户签到记录表"""
    __tablename__ = 'user_checkins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String)
    checkin_date = Column(Date, nullable=False)
    streak_days = Column(Integer, default=1)
    total_points = Column(Integer, default=0)

from contextlib import contextmanager
from src.utils.db import DatabaseManager

# 数据库连接（生产环境使用）
db_manager = DatabaseManager('sqlite:///../db/telegram_bot.db')
Base.metadata.create_all(db_manager.engine)

def init_db(db_url: str = 'sqlite:///../db/telegram_bot.db'):
    """初始化数据库连接"""
    global db_manager
    db_manager = DatabaseManager(db_url)
    Base.metadata.create_all(db_manager.engine)

@contextmanager
def get_session():
    """获取数据库会话"""
    with db_manager.get_session() as session:
        yield session

__all__ = ['init_db', 'get_session', 'UserCheckIn', 'calculate_level', 'handle_checkin']

# 等级计算
def calculate_level(points: int) -> int:
    """根据积分计算用户等级"""
    return min(points // 100 + 1, 10)  # 最大10级

async def handle_checkin(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    session_factory=get_session
):
    """处理签到命令"""
    user = update.effective_user
    today = datetime.now().date()
    
    try:
        session = session_factory()
        # 检查今日是否已签到
        existing = session.query(UserCheckIn).filter_by(
            user_id=user.id,
            checkin_date=today
        ).first()
        
        if existing:
            await update.message.reply_text(f'@{user.username} 今天已经签到过了哦~')
            return
        
        # 计算连续签到天数
        yesterday = session.query(UserCheckIn).filter_by(
            user_id=user.id,
            checkin_date=today.replace(day=today.day-1)
        ).first()
        
        streak = 1 if not yesterday else yesterday.streak_days + 1
        points = streak * 10  # 基础10分，连续签到加倍
        
        # 创建签到记录
        new_checkin = UserCheckIn(
            user_id=user.id,
            username=user.username,
            checkin_date=today,
            streak_days=streak,
            total_points=points
        )
        
        session.add(new_checkin)
        session.commit()
        
        level = calculate_level(points)
        await update.message.reply_text(
            f'🎉 @{user.username} 签到成功！\n'
            f'连续签到: {streak}天\n'
            f'今日获得: {points}积分\n'
            f'当前等级: Lv.{level}'
        )
        
    except Exception as e:
        logging.error(f"签到处理错误: {e}")
        await update.message.reply_text('签到失败，请稍后再试~')