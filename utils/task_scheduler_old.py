"""
任务调度器模块
使用APScheduler定时执行数据更新和信号扫描任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
import traceback

from utils.database import DatabaseManager
from utils.email_sender import EmailSender
from src.data_fetcher import DataFetcher
from src.strategy_manager import StrategyManager


class TaskScheduler:
    """监控任务调度器"""
    
    def __init__(self, db: DatabaseManager, email_sender: EmailSender):
        """
        初始化任务调度器
        
        Args:
            db: 数据库管理器
            email_sender: 邮件发送器
        """
        self.db = db
        self.email_sender = email_sender
        self.fetcher = DataFetcher()
        self.strategy_manager = StrategyManager()
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.scheduled_jobs = {}  # 记录已调度的任务
    
    def start(self):
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            self.reload_tasks()
            print("[TaskScheduler] 任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            self.scheduled_jobs.clear()
            print("[TaskScheduler] 任务调度器已停止")
    
    def reload_tasks(self):
        """重新加载所有任务的调度"""
        try:
            # 清除所有现有调度
            self.scheduler.remove_all_jobs()
            self.scheduled_jobs.clear()
            
            # 获取所有启用的任务
            tasks = self.db.get_monitor_tasks(enabled_only=True)
            
            if tasks.empty:
                print("[TaskScheduler] 没有启用的监控任务")
                return
            
            print(f"[TaskScheduler] 加载 {len(tasks)} 个监控任务...")
            
            for _, task in tasks.iterrows():
                self.schedule_task(task)
                
            print(f"[TaskScheduler] 任务调度完成")
            
        except Exception as e:
            print(f"[TaskScheduler] 重新加载任务失败: {e}")
            traceback.print_exc()
    
    def check_all_tasks(self):
        """检查所有启用的监控任务"""
        try:
            # 获取所有启用的任务
            tasks = self.db.get_monitor_tasks(enabled_only=True)
            
            if tasks.empty:
                return
            
            print(f"\n[TaskScheduler] 开始检查 {len(tasks)} 个监控任务...")
            
            for _, task in tasks.iterrows():
                self.check_task(task)
                
        except Exception as e:
            print(f"[TaskScheduler] 检查任务时出错: {e}")
            traceback.print_exc()
    
    def check_task(self, task):
        """
        检查单个监控任务
        
        Args:
            task: 任务记录（DataFrame行）
        """
        try:
            task_id = task['id']
            symbol = task['symbol']
            task_name = task['task_name']
            conditions_json = task['conditions']
            email = task['email']
            
            print(f"[TaskScheduler] 检查任务: {task_name} ({symbol})")
            
            # 更新最后检查时间
            self.db.update_task_check_time(task_id)
            
            # 获取最新市场数据
            df = self.db.get_market_data(symbol, limit=100)
            
            if df.empty:
                print(f"[TaskScheduler] 任务 {task_name}: 无市场数据")
                return
            
            # 计算技术指标
            df = TechnicalIndicators.calculate_all_indicators(df)
            
            # 解析监控条件
            conditions = json.loads(conditions_json)
            
            # 检查条件是否满足
            triggered_conditions = []
            for condition in conditions:
                if self.evaluate_condition(condition, df):
                    triggered_conditions.append(condition)
            
            # 如果有条件触发，发送邮件
            if triggered_conditions:
                print(f"[TaskScheduler] 任务 {task_name}: 触发 {len(triggered_conditions)} 个条件")
                
                # 准备市场数据
                latest = df.iloc[-1]
                market_data = {
                    'close': f"{latest.get('close', 0):.2f}",
                    'ma': f"{latest.get('MA20', 0):.2f}",
                    'ratio': f"{((latest.get('close', 0) - latest.get('MA20', 0)) / latest.get('MA20', 1) * 100):.2f}%",
                    'rsi14': f"{latest.get('RSI14', 0):.2f}",
                    'rsi30': f"{latest.get('RSI30', 0):.2f}",
                    'date': str(latest.get('date', ''))
                }
                
                # 获取监控对象名称
                watchlist = self.db.get_watchlist()
                name = watchlist[watchlist['symbol'] == symbol]['name'].iloc[0] if not watchlist.empty else symbol
                
                # 发送邮件
                success = self.email_sender.send_monitor_alert(
                    email, symbol, name, triggered_conditions, market_data
                )
                
                if success:
                    # 更新最后触发时间
                    self.db.update_task_trigger_time(task_id)
                    print(f"[TaskScheduler] 任务 {task_name}: 邮件发送成功")
                else:
                    print(f"[TaskScheduler] 任务 {task_name}: 邮件发送失败")
            else:
                print(f"[TaskScheduler] 任务 {task_name}: 无条件触发")
                
        except Exception as e:
            print(f"[TaskScheduler] 检查任务 {task.get('task_name', 'unknown')} 时出错: {e}")
            traceback.print_exc()
    
    def evaluate_condition(self, condition: Dict, df) -> bool:
        """
        评估监控条件
        
        Args:
            condition: 条件配置
            df: 包含技术指标的DataFrame
            
        Returns:
            条件是否满足
        """
        try:
            condition_type = condition.get('type')
            expression = condition.get('expression')
            
            if condition_type == 'expression':
                # 使用表达式解析器评估
                result = self.parser.evaluate_expression(expression, df)
                return bool(result)
            
            return False
            
        except Exception as e:
            print(f"[TaskScheduler] 评估条件失败: {e}")
            return False
