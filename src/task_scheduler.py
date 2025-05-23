import asyncio
import logging
from datetime import time, datetime, timedelta
from typing import Callable, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from telegram.ext import Application
from src.utils.metrics import TaskMetrics

class TaskScheduler:
    """定时任务调度系统"""
    
    def __init__(self, application: Application):
        # 初始化监控
        self.metrics = TaskMetrics()
        self.application = application
        self.logger = logging.getLogger(__name__)
        
        # 配置任务存储
        jobstores = {
            'default': SQLAlchemyJobStore(
                url='sqlite:///../db/scheduled_jobs.db',
                tablename='scheduled_tasks'
            )
        }
        
        # 配置执行器
        executors = {
            'default': ThreadPoolExecutor(5)
        }
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone='Asia/Shanghai'
        )
        
        # 注册默认任务
        self._register_default_tasks()

    def _register_default_tasks(self):
        """注册系统默认任务"""
        # 每日统计报表
        self.scheduler.add_job(
            self._generate_daily_report,
            'cron',
            hour=23,
            minute=59,
            id='daily_report'
        )
        
        # 每周数据清理
        self.scheduler.add_job(
            self._cleanup_old_data,
            'cron',
            day_of_week='sun',
            hour=2,
            id='weekly_cleanup'
        )

    async def _generate_daily_report(self, retry_count=0):
        """生成每日统计报表
        Args:
            retry_count: 当前重试次数
        """
        with self.metrics.track_task('daily_report'):
            self.logger.info(f"开始生成日报(重试次数:{retry_count})")
            self.metrics.task_retries.labels(
                task_name='daily_report'
            ).inc()
        
        try:
            # 获取消息统计
            from src.message_stats import MessageStats
            stats = MessageStats(self.application.session)

            # 获取所有活跃群组
            active_chats = self._get_active_chats()
            if not active_chats:
                self.logger.warning("没有活跃群组需要生成报表")
                return

            # 强制触发重试测试
            if retry_count == 0:
                raise Exception("模拟首次失败")

            for chat_id in active_chats:
                report = stats.generate_daily_report(chat_id)
                await self._send_report(chat_id, report)

        except Exception as e:
            self.logger.error(f"生成日报失败: {e}")
            
            if retry_count <= 3:  # 0(首次)+3次重试
                wait_time = min(2 ** retry_count * 5, 60)  # 最大60秒
                self.logger.info(f"将在{wait_time}秒后重试(第{retry_count+1}次尝试)...")
                await asyncio.sleep(wait_time)
                return await self._generate_daily_report(retry_count + 1)
            
            self._log_task_failure("daily_report", str(e))

    def _log_task_failure(self, task_name: str, error: str):
        """记录任务失败日志"""
        self.logger.error(f"任务失败 - {task_name}: {error}")
        # 可以扩展为写入数据库或发送通知

    def _get_active_chats(self) -> list:
        """获取活跃群组列表"""
        # 简单实现: 返回空列表，实际应从数据库获取
        return []

    async def _send_report(self, chat_id: int, report_data: Any):
        """发送报表到指定群组"""
        with self.metrics.track_task('send_report'):
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"每日报表:\n{report_data}"
                )
            except Exception as e:
                self._log_task_failure("send_report", str(e))
                raise

    async def _cleanup_old_data(self):
        """清理过期数据"""
        with self.metrics.track_task('weekly_cleanup'):
            # 实现数据清理逻辑
            self.logger.info("开始清理过期数据")
            # TODO: 实现实际清理逻辑

    def start(self):
        """启动任务调度"""
        self.scheduler.start()
        self.logger.info("定时任务系统已启动")

    def shutdown(self):
        """关闭任务调度"""
        self.scheduler.shutdown()
        self.logger.info("定时任务系统已关闭")

    def add_job(
        self,
        func: Callable,
        trigger: str,
        **trigger_args
    ) -> str:
        """添加自定义定时任务
        
        Args:
            func: 要执行的任务函数
            trigger: 触发器类型(cron/interval/date)
            **trigger_args: 触发器参数
            
        Returns:
            任务ID
        """
        job = self.scheduler.add_job(
            func,
            trigger,
            **trigger_args
        )
        return job.id

    def remove_job(self, job_id: str):
        """移除定时任务"""
        self.scheduler.remove_job(job_id)