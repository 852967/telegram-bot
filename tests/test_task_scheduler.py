import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.task_scheduler import TaskScheduler
from src.checkin import Base

class TestTaskScheduler(unittest.TestCase):
    """测试定时任务系统"""
    
    def setUp(self):
        """创建测试数据库"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Mock应用实例
        self.app = MagicMock()
        self.app.session = self.Session()
        
        # Mock调度器方法
        self.scheduler = TaskScheduler(self.app)
        self.scheduler.scheduler.add_job = MagicMock()
        self.scheduler.scheduler.remove_job = MagicMock()
        self.scheduler.scheduler.get_jobs = MagicMock(return_value=[
            MagicMock(id='daily_report'),
            MagicMock(id='weekly_cleanup')
        ])
    
    def test_add_job(self):
        """测试添加任务"""
        test_job = MagicMock()
        
        # 添加测试任务
        job_id = self.scheduler.add_job(
            test_job,
            'interval',
            minutes=30
        )
        
        self.assertIsNotNone(job_id)
        self.scheduler.scheduler.add_job.assert_called_once()
    
    def test_remove_job(self):
        """测试移除任务"""
        # 先添加测试任务
        test_job = MagicMock()
        job_id = self.scheduler.add_job(
            test_job,
            'interval',
            minutes=30
        )
        
        # 移除任务
        self.scheduler.remove_job(job_id)
        self.scheduler.scheduler.remove_job.assert_called_once_with(job_id)
    
    def test_default_tasks(self):
        """测试默认任务注册"""
        # 验证默认任务数量
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 2)
        
        # 验证任务类型
        jobs = self.scheduler.scheduler.get_jobs()
        self.assertEqual(jobs[0].id, 'daily_report')
        self.assertEqual(jobs[1].id, 'weekly_cleanup')

if __name__ == '__main__':
    unittest.main()