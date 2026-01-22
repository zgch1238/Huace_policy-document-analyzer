"""定时任务调度器"""
import os
import logging

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler 未安装，定时任务功能不可用。请运行: pip install APScheduler")

logger = logging.getLogger(__name__)


class AnalysisScheduler:
    """分析任务调度器"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.scheduler = None

    def start(self, interval_days: int = 30, run_at_startup: bool = True, block: bool = False):
        """启动调度器

        Args:
            interval_days: 定时任务间隔天数
            run_at_startup: 是否在启动时执行分析
            block: 是否阻塞等待启动时分析完成
        """
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler 不可用，跳过定时任务启动")
            return None

        project_root = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(project_root, 'policy_document')

        # 如果需要启动时执行且阻塞等待
        if run_at_startup and block:
            logger.info("执行启动时政策文档分析（同步）...")
            self.analyzer.run_analysis(policy_dir)
            logger.info("启动时分析完成")

        self.scheduler = BackgroundScheduler()

        # 添加定时任务（30天一次）
        self.scheduler.add_job(
            func=lambda: self.analyzer.run_analysis(policy_dir),
            trigger=IntervalTrigger(days=interval_days),
            id='scheduled_analyze',
            name='定时政策文档分析',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"定时任务调度器已启动（每 {interval_days} 天执行一次）")

        return self.scheduler

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已关闭")
