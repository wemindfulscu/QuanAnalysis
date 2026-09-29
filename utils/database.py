"""
数据库管理模块
用于管理SQLite数据库的创建、数据存储和查询
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import List, Optional


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = "data/quant_analysis.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭数据库"""
        self.close()
        return False
    
    def close(self):
        """关闭所有数据库连接"""
        # SQLite的连接是在每次操作时临时创建的，这里主要是为了API一致性
        pass
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建监控列表表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT DEFAULT 'index',
                    added_date TEXT DEFAULT (date('now')),
                    active INTEGER DEFAULT 1
                )
            """)
            
            # 创建行情数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    change_pct REAL,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    UNIQUE(symbol, trade_date)
                )
            """)
            
            # 创建信号记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_date TEXT NOT NULL,
                    close_price REAL,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            
            # 创建监控任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitor_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    email TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    check_interval INTEGER DEFAULT 60,
                    last_check TEXT,
                    last_trigger TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol 
                ON market_data(symbol)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_date 
                ON market_data(trade_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol 
                ON signals(symbol)
            """)
            
            conn.commit()
    
    def add_to_watchlist(self, symbol: str, name: str, index_type: str = "index") -> bool:
        """
        添加到监控列表
        
        Args:
            symbol: 指数代码
            name: 指数名称
            index_type: 类型（index/sector）
            
        Returns:
            是否添加成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO watchlist (symbol, name, type, active)
                    VALUES (?, ?, ?, 1)
                """, (symbol, name, index_type))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加到监控列表失败: {e}")
            return False
    
    def remove_from_watchlist(self, symbol: str, delete_data: bool = True) -> bool:
        """
        从监控列表移除
        
        Args:
            symbol: 指数代码
            delete_data: 是否同时删除相关的市场数据和信号数据
            
        Returns:
            是否移除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if delete_data:
                    # 删除市场数据
                    cursor.execute("""
                        DELETE FROM market_data 
                        WHERE symbol = ?
                    """, (symbol,))
                    
                    # 删除信号数据
                    cursor.execute("""
                        DELETE FROM signals 
                        WHERE symbol = ?
                    """, (symbol,))
                    
                    print(f"已删除 {symbol} 的所有数据")
                
                # 软删除监控项
                cursor.execute("""
                    UPDATE watchlist SET active = 0 
                    WHERE symbol = ?
                """, (symbol,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"从监控列表移除失败: {e}")
            return False
    
    def get_watchlist(self, active_only: bool = True) -> pd.DataFrame:
        """
        获取监控列表
        
        Args:
            active_only: 只返回活跃的监控项
            
        Returns:
            监控列表DataFrame
        """
        query = "SELECT * FROM watchlist"
        if active_only:
            query += " WHERE active = 1"
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)
    
    def save_market_data(self, symbol: str, data: pd.DataFrame) -> int:
        """
        保存市场数据（增量更新）
        
        Args:
            symbol: 指数代码
            data: 市场数据DataFrame，需包含：日期、开高低收、成交量等
            
        Returns:
            插入的记录数
        """
        if data.empty:
            return 0
        
        # 准备数据
        data = data.copy()
        data['symbol'] = symbol
        
        # 重命名列以匹配数据库字段
        column_mapping = {
            '日期': 'trade_date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'change_pct'
        }
        
        data = data.rename(columns=column_mapping)
        
        # 选择需要的列
        columns = ['symbol', 'trade_date', 'open', 'high', 'low', 
                   'close', 'volume', 'amount', 'change_pct']
        data = data[[col for col in columns if col in data.columns]]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取已存在的日期
                cursor.execute("""
                    SELECT DISTINCT trade_date 
                    FROM market_data 
                    WHERE symbol = ?
                """, (symbol,))
                existing_dates = set(row[0] for row in cursor.fetchall())
                
                # 过滤掉已存在的数据
                if existing_dates:
                    data = data[~data['trade_date'].isin(existing_dates)]
                
                # 插入新数据（如果有）
                rows_inserted = 0
                if not data.empty:
                    rows_inserted = len(data)
                    data.to_sql('market_data', conn, if_exists='append', 
                               index=False, method=None)
                    print(f"[Database] 成功保存 {rows_inserted} 条新数据")
                else:
                    print(f"[Database] 过滤后无新数据需要保存")
                
                # 无论是否有新数据，都更新监控列表的最后更新时间
                cursor.execute("""
                    UPDATE watchlist 
                    SET last_update = datetime('now', 'localtime')
                    WHERE symbol = ?
                """, (symbol,))
                conn.commit()
                print(f"[Database] 更新了 {symbol} 的最后更新时间")
                
                return rows_inserted
        except Exception as e:
            print(f"[Database] 保存市场数据失败: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    def get_market_data(self, symbol: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        获取市场数据
        
        Args:
            symbol: 指数代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 限制返回条数（从最新开始）
            
        Returns:
            市场数据DataFrame
        """
        query = "SELECT * FROM market_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY trade_date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            # 按日期升序排列
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 添加 date 别名以兼容旧代码
            if 'trade_date' in df.columns and 'date' not in df.columns:
                df['date'] = df['trade_date']
            
            return df
    
    def get_latest_date(self, symbol: str) -> Optional[str]:
        """
        获取某个指数的最新数据日期
        
        Args:
            symbol: 指数代码
            
        Returns:
            最新日期字符串，如果没有数据返回None
        """
        query = """
            SELECT MAX(trade_date) as latest_date 
            FROM market_data 
            WHERE symbol = ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
    
    def save_signal(self, symbol: str, strategy_name: str, 
                   signal_type: str, signal_date: str, close_price: float):
        """
        保存交易信号
        
        Args:
            symbol: 指数代码
            strategy_name: 策略名称
            signal_type: 信号类型（BUY/SELL）
            signal_date: 信号日期
            close_price: 收盘价
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO signals (symbol, strategy_name, signal_type, signal_date, close_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (symbol, strategy_name, signal_type, signal_date, close_price))
                conn.commit()
        except Exception as e:
            print(f"保存信号失败: {e}")
    
    def get_signals(self, symbol: Optional[str] = None, 
                   days: int = 30) -> pd.DataFrame:
        """
        获取交易信号
        
        Args:
            symbol: 指数代码，None表示所有
            days: 最近多少天的信号
            
        Returns:
            信号DataFrame
        """
        query = """
            SELECT * FROM signals 
            WHERE signal_date >= date('now', '-{} days')
        """.format(days)
        
        params = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY signal_date DESC, created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params if params else None)
    
    # ==================== 监控任务管理 ====================
    
    def add_monitor_task(self, symbol: str, task_name: str, email: str,
                        update_schedule: str = '09:30', scan_schedule: str = '15:30',
                        strategy: str = 'default', remark: str = '') -> int:
        """
        添加监控任务
        
        Args:
            symbol: 监控的指数代码
            task_name: 任务名称
            email: 接收通知的邮箱
            update_schedule: 数据更新时间（HH:MM格式）
            scan_schedule: 信号扫描时间（HH:MM格式）
            strategy: 使用的策略名称
            remark: 备注信息
            
        Returns:
            任务ID，失败返回-1
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO monitor_tasks 
                    (symbol, task_name, email, update_schedule, scan_schedule, 
                     strategy, remark, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (symbol, task_name, email, update_schedule, scan_schedule, 
                      strategy, remark))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"添加监控任务失败: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    def update_monitor_task(self, task_id: int, **kwargs) -> bool:
        """
        更新监控任务
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        try:
            if not kwargs:
                return False
            
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            set_clause += ", updated_at = datetime('now', 'localtime')"
            values = list(kwargs.values()) + [task_id]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE monitor_tasks 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新监控任务失败: {e}")
            return False
    
    def delete_monitor_task(self, task_id: int) -> bool:
        """
        删除监控任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM monitor_tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除监控任务失败: {e}")
            return False
    
    def get_monitor_tasks(self, symbol: Optional[str] = None, 
                         enabled_only: bool = False) -> pd.DataFrame:
        """
        获取监控任务列表
        
        Args:
            symbol: 指数代码，None表示所有
            enabled_only: 是否只返回启用的任务
            
        Returns:
            任务DataFrame
        """
        query = "SELECT * FROM monitor_tasks WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if enabled_only:
            query += " AND enabled = 1"
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params if params else None)
    
    def toggle_monitor_task(self, task_id: int, enabled: bool) -> bool:
        """
        启用/禁用监控任务
        
        Args:
            task_id: 任务ID
            enabled: 是否启用
            
        Returns:
            是否操作成功
        """
        return self.update_monitor_task(task_id, enabled=1 if enabled else 0)
    
    def update_task_update_time(self, task_id: int) -> bool:
        """
        更新任务最后数据更新时间
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE monitor_tasks 
                    SET last_update = datetime('now', 'localtime'),
                        updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                """, (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新数据更新时间失败: {e}")
            return False
    
    def update_task_scan_time(self, task_id: int) -> bool:
        """
        更新任务最后扫描时间
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE monitor_tasks 
                    SET last_scan = datetime('now', 'localtime'),
                        updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                """, (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新触发时间失败: {e}")
            return False
