"""
任务调度器模块
使用APScheduler定时执行数据更新和信号扫描任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
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
    
    def schedule_task(self, task):
        """
        为任务设置定时调度
        
        Args:
            task: 任务记录（DataFrame行）
        """
        try:
            task_id = int(task['id'])
            symbol = task['symbol']
            task_name = task['task_name']
            email = task['email']
            update_schedule = task.get('update_schedule', '09:30')
            scan_schedule = task.get('scan_schedule', '15:30')
            strategy = task.get('strategy', 'default')
            
            print(f"[TaskScheduler] 调度任务 #{task_id}: {task_name}")
            print(f"  - 数据更新: {update_schedule}")
            print(f"  - 信号扫描: {scan_schedule}")
            
            # 解析时间 HH:MM
            update_hour, update_minute = map(int, update_schedule.split(':'))
            scan_hour, scan_minute = map(int, scan_schedule.split(':'))
            
            # 添加数据更新任务
            update_job_id = f"update_{task_id}"
            self.scheduler.add_job(
                self.update_task_data,
                trigger=CronTrigger(hour=update_hour, minute=update_minute),
                args=[task_id, symbol, task_name],
                id=update_job_id,
                replace_existing=True
            )
            
            # 添加信号扫描任务
            scan_job_id = f"scan_{task_id}"
            self.scheduler.add_job(
                self.scan_task_signal,
                trigger=CronTrigger(hour=scan_hour, minute=scan_minute),
                args=[task_id, symbol, task_name, email, strategy],
                id=scan_job_id,
                replace_existing=True
            )
            
            self.scheduled_jobs[task_id] = {
                'update_job': update_job_id,
                'scan_job': scan_job_id
            }
            
        except Exception as e:
            print(f"[TaskScheduler] 调度任务失败: {e}")
            traceback.print_exc()
    
    def update_task_data(self, task_id: int, symbol: str, task_name: str):
        """
        更新任务的市场数据
        
        Args:
            task_id: 任务ID
            symbol: 指数代码
            task_name: 任务名称
        """
        try:
            print(f"\n[TaskScheduler] 执行数据更新 - 任务#{task_id}: {task_name}")
            print(f"  指数: {symbol}")
            
            # 从监控列表获取指数类型
            watchlist = self.db.get_watchlist()
            item = watchlist[watchlist['symbol'] == symbol]
            
            if item.empty:
                print(f"[TaskScheduler] 指数 {symbol} 不在监控列表中")
                return
            
            index_type = item.iloc[0]['type']
            print(f"  类型: {index_type}")
            
            # 获取数据
            df = self.fetcher.fetch_data(symbol, index_type)
            
            if df is not None and not df.empty:
                print(f"[TaskScheduler] 获取到 {len(df)} 条数据")
                print(f"[TaskScheduler] 数据列: {list(df.columns)}")
                
                # 获取日期列（可能是中文"日期"或英文"date"）
                date_col = '日期' if '日期' in df.columns else 'date' if 'date' in df.columns else 'trade_date'
                if date_col in df.columns:
                    first_date = df.iloc[0][date_col]
                    last_date = df.iloc[-1][date_col]
                    print(f"[TaskScheduler] 日期范围: {first_date} ~ {last_date}")
                else:
                    print(f"[TaskScheduler] 未找到日期列")
                
                # 保存到数据库
                count = self.db.save_market_data(symbol, df)
                
                if count > 0:
                    # 更新任务的last_update时间
                    self.db.update_task_update_time(task_id)
                    print(f"[TaskScheduler] 数据更新成功: 新增 {count} 条记录")
                elif count == 0:
                    print(f"[TaskScheduler] 数据已是最新，无需更新")
                    # 即使没有新数据，也更新时间戳
                    self.db.update_task_update_time(task_id)
                else:
                    print(f"[TaskScheduler] 数据保存失败")
            else:
                print(f"[TaskScheduler] 获取数据失败或数据为空")
                
        except Exception as e:
            print(f"[TaskScheduler] 更新数据失败: {e}")
            traceback.print_exc()
    
    def scan_task_signal(self, task_id: int, symbol: str, task_name: str, 
                        email: str, strategy: str = 'default'):
        """
        扫描任务信号并发送邮件
        
        Args:
            task_id: 任务ID
            symbol: 指数代码
            task_name: 任务名称
            email: 接收邮箱
            strategy: 策略配置（可能是单个策略名或JSON数组）
        """
        try:
            # 解析策略配置
            import json
            strategies = []
            try:
                parsed = json.loads(strategy)
                strategies = parsed if isinstance(parsed, list) else [strategy]
            except (json.JSONDecodeError, TypeError):
                strategies = [strategy] if strategy else ['default']
            
            print(f"\n[TaskScheduler] 执行信号扫描 - 任务#{task_id}: {task_name}")
            print(f"  指数: {symbol}, 策略: {strategies}")
            
            # 获取市场数据
            df = self.db.get_market_data(symbol, limit=100)
            
            if df.empty:
                print(f"[TaskScheduler] 无市场数据")
                return
            
            # 计算技术指标
            from indicators.technical_indicators import TechnicalIndicators
            df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
            
            if df_with_indicators.empty:
                print(f"[TaskScheduler] 计算技术指标失败")
                return
            
            # 执行信号扫描（针对选定的策略）
            if strategies and strategies != ['default']:
                # 扫描指定策略
                signal_results = []
                for strategy_name in strategies:
                    results = self.strategy_manager.scan_signals(df_with_indicators)
                    # 过滤出指定策略的信号
                    strategy_signals = [s for s in results if s['strategy_name'] == strategy_name]
                    signal_results.extend(strategy_signals)
            else:
                # 扫描所有策略
                signal_results = self.strategy_manager.scan_signals(df_with_indicators)
            
            # 更新扫描时间
            self.db.update_task_scan_time(task_id)
            
            if signal_results:
                print(f"[TaskScheduler] 检测到 {len(signal_results)} 个信号")
                
                # 获取最新数据行
                latest = df_with_indicators.iloc[-1]
                latest_date = str(latest.get('trade_date', ''))
                close_price = float(latest.get('close', 0))
                
                # 构造信号列表用于邮件和数据库
                signals = []
                for sig in signal_results:
                    signal_info = {
                        'strategy': sig['strategy_name'],
                        'signal': sig['signal_type'],
                        'date': latest_date,
                        'close': close_price
                    }
                    signals.append(signal_info)
                    
                    # 保存信号到数据库
                    self.db.save_signal(
                        symbol=symbol,
                        strategy_name=sig['strategy_name'],
                        signal_type=sig['signal_type'],
                        signal_date=latest_date,
                        close_price=close_price
                    )
                
                # 准备邮件数据
                market_data = {
                    'symbol': symbol,
                    'name': task_name,
                    'close': f"{close_price:.2f}",
                    'date': latest_date,
                    'signals': signals
                }
                
                # 发送信号邮件
                success = self.send_signal_email(email, symbol, task_name, signals, market_data)
                
                if success:
                    print(f"[TaskScheduler] 邮件发送成功")
                else:
                    print(f"[TaskScheduler] 邮件发送失败")
            else:
                print(f"[TaskScheduler] 未检测到信号")
                
        except Exception as e:
            print(f"[TaskScheduler] 扫描信号失败: {e}")
            traceback.print_exc()
    
    def send_signal_email(self, email: str, symbol: str, name: str, signals: list, market_data: dict) -> bool:
        """
        发送信号邮件
        
        Args:
            email: 接收邮箱
            symbol: 指数代码
            name: 指数名称
            signals: 信号列表
            market_data: 市场数据
            
        Returns:
            是否发送成功
        """
        try:
            # 构造邮件内容
            signal_texts = []
            for signal in signals:
                signal_type = "买入" if signal['signal'] == 'BUY' else "卖出"
                signal_texts.append(f"{signal['date']}: {signal_type}信号 (策略:{signal['strategy']}, 价格:{signal['close']:.2f})")
            
            # 使用EmailSender的test方法发送（临时方案）
            conditions = [
                {"description": text, "value": ""} for text in signal_texts
            ]
            
            return self.email_sender.send_monitor_alert(
                email, symbol, name, conditions, market_data
            )
        except Exception as e:
            print(f"[TaskScheduler] 发送信号邮件失败: {e}")
            return False
