import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from src.checkin import handle_checkin
from src.member_management import MemberManager
from src.message_stats import MessageStats
from src.welcome_system import WelcomeSystem
from src.task_scheduler import TaskScheduler
from src.monitoring.system_monitor import SystemMonitor

# 加载环境变量
load_dotenv('../config/.env')

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 初始化数据库 (通过checkin模块的init_db)
from src.checkin import init_db
init_db()

async def start(update, context):
    """处理/start命令"""
    await update.message.reply_text(
        '欢迎使用群管机器人!\n\n'
        '可用命令:\n'
        '/start - 显示帮助\n'
        '/checkin - 每日签到\n'
        '/rank - 活跃度排行\n'
        '/setwelcome - 设置欢迎语\n'
        '/ban - 封禁用户\n'
        '/mute - 禁言用户\n'
        '/unban - 解封用户'
    )

async def set_welcome(update, context):
    """设置欢迎语"""
    if not context.args:
        await update.message.reply_text("请提供欢迎语内容")
        return
    
    welcome_text = ' '.join(context.args)
    welcome_system.set_welcome_message(
        update.effective_chat.id,
        welcome_text
    )
    await update.message.reply_text("✅ 欢迎语设置成功")

async def show_rank(update, context):
    """显示活跃度排行榜"""
    chat_id = update.effective_chat.id
    rankings = message_stats.get_leaderboard(chat_id)
    
    response = "🏆 活跃度排行榜:\n"
    for i, rank in enumerate(rankings[:10], 1):
        response += f"{i}. 用户 {rank['user_id']}: {rank['count']}条\n"
    
    await update.message.reply_text(response)

def main():
    """主程序入口"""
    # 创建应用实例
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    # 初始化管理器
    member_manager = MemberManager(get_session)
    message_stats = MessageStats(get_session())
    welcome_system = WelcomeSystem(get_session())
    
    # 初始化监控系统
    monitor = SystemMonitor(os.getenv('BOT_TOKEN'))
    monitor.add_alert_channel('telegram', {
        'chat_id': os.getenv('ADMIN_CHAT_ID')
    })
    
    # 初始化任务调度器
    task_scheduler = TaskScheduler(application)
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("checkin", handle_checkin))
    application.add_handler(MessageHandler(
        filters=filters.TEXT & ~filters.COMMAND,
        callback=message_stats.record_message
    ))
    
    # 消息处理器
    application.add_handler(MessageHandler(
        filters=filters.StatusUpdate.NEW_CHAT_MEMBERS,
        callback=welcome_system.handle_new_member
    ))
    
    # 回调查询处理器
    application.add_handler(CallbackQueryHandler(
        welcome_system.verify_member,
        pattern=r"^verify_\d+$"
    ))
    
    # 欢迎系统命令
    application.add_handler(CommandHandler(
        "setwelcome", 
        set_welcome,
        filters=filters.ChatType.GROUPS & filters.User.ADMIN
    ))
    
    # 统计命令
    application.add_handler(CommandHandler("rank", show_rank))
    
    # 成员管理命令
    application.add_handler(CommandHandler(
        "ban", 
        lambda u, c: member_manager.ban_member(u, c, u.args[0] if u.args else None)
    ))
    application.add_handler(CommandHandler(
        "unban",
        lambda u, c: member_manager.unban_member(u, c, u.args[0] if u.args else None)
    ))
    application.add_handler(CommandHandler(
        "mute",
        lambda u, c: member_manager.mute_member(u, c, u.args[0] if u.args else None)
    ))
    
    # 启动监控系统
    monitor.start()
    
    # 启动任务调度器
    task_scheduler.start()
    
    try:
        # 启动机器人
        application.run_polling()
    finally:
        # 关闭监控系统
        monitor.stop()
        # 关闭任务调度器
        task_scheduler.shutdown()

if __name__ == '__main__':
    main()