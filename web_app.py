"""
量化决策系统 - Web API服务
提供RESTful API接口，支持所有量化分析功能
"""
import sys
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import json
import traceback

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager
from src.data_fetcher import DataFetcher
from src.strategy_manager import StrategyManager
from indicators.technical_indicators import TechnicalIndicators

app = Flask(__name__, static_folder='web_static', static_url_path='')
CORS(app)  # 启用跨域支持

# 初始化系统组件
db = DatabaseManager()
fetcher = DataFetcher()
strategy_manager = StrategyManager()
# TechnicalIndicators 使用静态方法，无需实例化

# 初始化邮件发送器和任务调度器
from utils.email_sender import EmailSender
from utils.task_scheduler import TaskScheduler

# 从配置文件加载邮件配置
def load_email_config():
    """加载邮件配置"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'email_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config.get('enabled', False):
                    print("[邮件配置] 邮件功能已启用")
                    return EmailSender(
                        smtp_server=config.get('smtp_server', 'smtp.qq.com'),
                        smtp_port=config.get('smtp_port', 465),
                        sender_email=config.get('sender_email', ''),
                        sender_password=config.get('sender_password', '')
                    )
                else:
                    print("[邮件配置] 邮件功能未启用，请在 config/email_config.json 中配置")
        else:
            print("[邮件配置] 配置文件不存在，使用默认配置")
    except Exception as e:
        print(f"[邮件配置] 加载失败: {e}")
    
    # 返回默认配置（未启用）
    return EmailSender()

email_sender = load_email_config()
task_scheduler = TaskScheduler(db, email_sender)


# ==================== 工具函数 ====================

def format_response(success=True, data=None, message="", error=None):
    """标准化API响应格式"""
    response = {
        "success": success,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    if error:
        response["error"] = str(error)
    return jsonify(response)


def dataframe_to_dict(df):
    """将DataFrame转换为JSON友好的格式"""
    if df is None or df.empty:
        return []
    
    # 处理日期时间列
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    
    return df.to_dict(orient='records')


# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    """主页"""
    return send_from_directory('web_static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """静态文件"""
    return send_from_directory('web_static', path)


# ==================== 系统信息API ====================

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """获取系统信息"""
    try:
        watchlist = db.get_watchlist()
        strategies = strategy_manager.list_strategies()
        
        info = {
            "version": "2.1 Web版",
            "watchlist_count": len(watchlist),
            "strategy_count": len(strategies),
            "database_path": db.db_path
        }
        
        return format_response(data=info, message="系统信息获取成功")
    except Exception as e:
        return format_response(success=False, error=e), 500


# ==================== 监控列表API ====================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """获取监控列表"""
    try:
        watchlist = db.get_watchlist()
        data = dataframe_to_dict(watchlist)
        
        return format_response(data=data, message="监控列表获取成功")
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/watchlist', methods=['POST'])
def add_watchlist():
    """添加监控项"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        name = data.get('name')
        index_type = data.get('type')
        
        if not symbol or not name:
            return format_response(success=False, message="缺少必要参数"), 400
        
        # 如果没有指定类型，自动检测
        if not index_type:
            index_type = fetcher._detect_index_type(symbol)
        
        success = db.add_to_watchlist(symbol, name, index_type)
        
        if success:
            return format_response(message=f"成功添加监控项: {name}")
        else:
            return format_response(success=False, message="添加失败，可能已存在"), 400
            
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def delete_watchlist(symbol):
    """删除监控项"""
    try:
        success = db.remove_from_watchlist(symbol)
        
        if success:
            return format_response(message=f"成功删除监控项: {symbol}")
        else:
            return format_response(success=False, message="删除失败，项目不存在"), 404
            
    except Exception as e:
        return format_response(success=False, error=e), 500


# ==================== 数据获取API ====================

@app.route('/api/data/search', methods=['GET'])
def search_index():
    """搜索指数"""
    try:
        query = request.args.get('q', '')
        index_type = request.args.get('type', 'all')
        
        results = []
        
        # 搜索行业板块
        if index_type in ['all', 'industry']:
            industry_list = fetcher.get_index_list()
            if not industry_list.empty:
                filtered = industry_list[industry_list['板块名称'].str.contains(query, case=False, na=False)]
                for _, row in filtered.head(20).iterrows():
                    results.append({
                        'symbol': row['板块名称'],
                        'name': row['板块名称'],
                        'type': 'industry'
                    })
        
        # 搜索概念板块
        if index_type in ['all', 'concept']:
            concept_list = fetcher.get_sector_list()
            if not concept_list.empty:
                filtered = concept_list[concept_list['板块名称'].str.contains(query, case=False, na=False)]
                for _, row in filtered.head(20).iterrows():
                    results.append({
                        'symbol': row['板块名称'],
                        'name': row['板块名称'],
                        'type': 'concept'
                    })
        
        return format_response(data=results, message="搜索完成")
        
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/data/update', methods=['POST'])
def update_data():
    """更新数据"""
    try:
        data = request.get_json()
        symbol = data.get('symbol') if data else None
        
        print(f"\n[API] 收到更新数据请求: symbol={symbol}")
        
        if symbol:
            # 更新单个指数
            print(f"[API] 更新单个指数: {symbol}")
            watchlist = db.get_watchlist()
            item = watchlist[watchlist['symbol'] == symbol]
            
            if item.empty:
                print(f"[API] 指数 {symbol} 不在监控列表中")
                return format_response(success=False, message="指数不在监控列表中"), 404
            
            row = item.iloc[0]
            print(f"[API] 开始获取数据: {row['name']} ({row['symbol']}) 类型={row['type']}")
            
            # 获取最后更新日期，用于增量更新
            last_date = db.get_latest_date(symbol)
            if last_date:
                print(f"[API] 上次更新日期: {last_date}，进行增量更新")
                df = fetcher.fetch_incremental_data(row['symbol'], last_date, row['type'])
            else:
                print(f"[API] 首次更新，获取全量数据")
                df = fetcher.fetch_data(row['symbol'], row['type'])
            
            if not df.empty:
                print(f"[API] 数据获取成功，保存 {len(df)} 条记录")
                # 打印日期范围
                latest_date = None
                if '日期' in df.columns:
                    latest_date = df['日期'].iloc[-1]
                    print(f"[API] 数据日期范围: {df['日期'].iloc[0]} ~ {latest_date}")
                
                count = db.save_market_data(symbol, df)
                print(f"[API] 保存完成，实际插入 {count} 条新记录")
                
                # 构造消息
                if count > 0:
                    from datetime import datetime
                    today = datetime.now().strftime('%Y-%m-%d')
                    if latest_date and latest_date < today:
                        message = f"成功更新 {row['name']} 数据，新增 {count} 条记录（最新数据日期: {latest_date}，今日数据可能尚未公布）"
                    else:
                        message = f"成功更新 {row['name']} 数据，新增 {count} 条记录"
                else:
                    message = f"{row['name']} 数据已是最新（最新: {latest_date or '未知'}）"
                
                return format_response(
                    data={'records_updated': count, 'latest_date': latest_date},
                    message=message
                )
            else:
                print(f"[API] 数据获取失败：数据为空")
                return format_response(success=False, message="数据获取失败或已是最新"), 200
        else:
            # 更新所有监控项
            watchlist = db.get_watchlist()
            print(f"[API] 更新所有监控项，共 {len(watchlist)} 个")
            results = []
            
            for idx, row in watchlist.iterrows():
                try:
                    print(f"\n[API] [{idx+1}/{len(watchlist)}] 更新: {row['name']} ({row['symbol']})")
                    df = fetcher.fetch_data(row['symbol'], row['type'])
                    if not df.empty:
                        count = db.save_market_data(row['symbol'], df)
                        print(f"[API] 成功保存 {count} 条记录")
                        results.append({
                            'symbol': row['symbol'],
                            'name': row['name'],
                            'records': count,
                            'success': True
                        })
                    else:
                        print(f"[API] 数据为空")
                        results.append({
                            'symbol': row['symbol'],
                            'name': row['name'],
                            'success': False,
                            'error': '数据为空'
                        })
                except Exception as e:
                    print(f"[API] 更新失败: {e}")
                    traceback.print_exc()
                    results.append({
                        'symbol': row['symbol'],
                        'name': row['name'],
                        'success': False,
                        'error': str(e)
                    })
            
            success_count = sum(1 for r in results if r['success'])
            print(f"\n[API] 批量更新完成: 成功 {success_count}/{len(results)}")
            return format_response(data=results, message=f"批量更新完成: 成功 {success_count}/{len(results)}")
            
    except Exception as e:
        print(f"[API] 更新数据异常: {e}")
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/data/market/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """获取市场数据"""
    try:
        days = request.args.get('days', 250, type=int)
        
        df = db.get_market_data(symbol, limit=days)
        
        if df.empty:
            return format_response(success=False, message="数据不存在"), 404
        
        # 计算技术指标
        df = TechnicalIndicators.calculate_all_indicators(df)
        
        data = dataframe_to_dict(df)
        
        return format_response(data=data, message="市场数据获取成功")
        
    except Exception as e:
        return format_response(success=False, error=e), 500


# ==================== 策略管理API ====================

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """获取策略列表"""
    try:
        strategies = strategy_manager.list_strategies()
        return format_response(data=strategies, message="策略列表获取成功")
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/strategies', methods=['POST'])
def add_strategy():
    """添加策略"""
    try:
        data = request.get_json()
        name = data.get('name')
        buy_expression = data.get('buy_expression')
        sell_expression = data.get('sell_expression')
        
        if not all([name, buy_expression, sell_expression]):
            return format_response(success=False, message="缺少必要参数"), 400
        
        success = strategy_manager.add_strategy(name, buy_expression, sell_expression)
        
        if success:
            return format_response(message=f"成功添加策略: {name}")
        else:
            return format_response(success=False, message="添加失败，策略已存在"), 400
            
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/strategies/<name>', methods=['DELETE'])
def delete_strategy(name):
    """删除策略"""
    try:
        success = strategy_manager.remove_strategy(name)
        
        if success:
            return format_response(message=f"成功删除策略: {name}")
        else:
            return format_response(success=False, message="删除失败，策略不存在"), 404
            
    except Exception as e:
        return format_response(success=False, error=e), 500


# ==================== 信号分析API ====================

@app.route('/api/signals/scan', methods=['POST'])
def scan_signals():
    """扫描信号（可指定单个symbol或扫描所有）"""
    try:
        data = request.get_json() or {}
        strategy_name = data.get('strategy', 'default')
        symbol = data.get('symbol')  # 如果指定symbol，只扫描该项
        
        # 获取要扫描的监控项
        watchlist = db.get_watchlist()
        if symbol:
            watchlist = watchlist[watchlist['symbol'] == symbol]
            if watchlist.empty:
                return format_response(success=False, message="指定的监控项不存在"), 404
            print(f"[API] 扫描单个信号: {symbol}")
        else:
            print(f"[API] 扫描所有监控项信号，共 {len(watchlist)} 个")
        
        results = []
        
        for idx, row in watchlist.iterrows():
            try:
                # 获取市场数据
                df = db.get_market_data(row['symbol'], limit=100)
                
                if df.empty:
                    continue
                
                # 添加技术指标
                df = TechnicalIndicators.calculate_all_indicators(df)
                
                # 分析数据
                analysis = strategy_manager.analyze_data(row['symbol'], df)
                
                # 检查是否有信号
                if analysis.get('signals'):
                    # 为每个策略信号创建一个结果
                    for signal_info in analysis['signals']:
                        results.append({
                            'symbol': row['symbol'],
                            'name': row['name'],
                            'type': row['type'],
                            'signal': signal_info['signal_type'],
                            'price': float(df.iloc[-1]['close']) if 'close' in df.columns else 0,
                            'date': str(df.iloc[-1]['date']) if 'date' in df.columns else '',
                            'strategy': signal_info['strategy_name']
                        })
                    
            except Exception as e:
                print(f"扫描 {row['symbol']} 失败: {e}")
                continue
        
        return format_response(data=results, message=f"扫描完成，发现 {len(results)} 个信号")
        
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/signals/<symbol>', methods=['GET'])
def get_signals(symbol):
    """获取指定指数的信号"""
    try:
        days = request.args.get('days', 30, type=int)
        
        signals = db.get_signals(symbol, days=days)
        data = dataframe_to_dict(signals)
        
        return format_response(data=data, message="信号获取成功")
        
    except Exception as e:
        return format_response(success=False, error=e), 500


@app.route('/api/analysis/<symbol>', methods=['GET'])
def analyze_index(symbol):
    """分析指数"""
    try:
        days = request.args.get('days', 100, type=int)
        
        # 获取市场数据
        df = db.get_market_data(symbol, limit=days)
        
        if df.empty:
            return format_response(success=False, message="数据不存在"), 404
        
        # 添加技术指标
        df = TechnicalIndicators.calculate_all_indicators(df)
        
        # 执行分析
        analysis = strategy_manager.analyze_data(symbol, df)
        
        # 添加最新数据点
        latest = df.iloc[-1]
        analysis['latest_data'] = {
            'date': str(latest.get('date', '')),
            'close': float(latest.get('close', 0)),
            'volume': float(latest.get('volume', 0)),
            'rsi': float(latest.get('RSI14', 0)),
            'macd': float(latest.get('MACD', 0)),
            'ma5': float(latest.get('MA5', 0)),
            'ma20': float(latest.get('MA20', 0))
        }
        
        return format_response(data=analysis, message="分析完成")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


# ==================== 图表数据API ====================

@app.route('/api/chart/<symbol>', methods=['GET'])
def get_chart_data(symbol):
    """获取图表数据"""
    try:
        days = request.args.get('days', 250, type=int)
        
        # 获取市场数据
        df = db.get_market_data(symbol, limit=days)
        
        if df.empty:
            return format_response(success=False, message="数据不存在"), 404
        
        # 添加技术指标
        df = TechnicalIndicators.calculate_all_indicators(df)
        
        # 获取信号
        signals_df = db.get_signals(symbol, days=days)
        signals = dataframe_to_dict(signals_df)
        
        # 准备图表数据
        chart_data = {
            'ohlcv': [],
            'ma': {'ma5': [], 'ma20': [], 'ma60': []},
            'boll': {'upper': [], 'middle': [], 'lower': []},
            'atr': [],
            'volume': [],
            'volume_ma': {'ma5': [], 'ma10': []},
            'rsi': [],
            'macd': {'macd': [], 'signal': [], 'histogram': []},
            'kdj': {'k': [], 'd': [], 'j': []},
            'signals': signals,
            'dates': []
        }
        
        for _, row in df.iterrows():
            date_str = str(row.get('date', ''))
            chart_data['dates'].append(date_str)
            
            # OHLCV
            chart_data['ohlcv'].append([
                float(row.get('open', 0)),
                float(row.get('close', 0)),
                float(row.get('low', 0)),
                float(row.get('high', 0))
            ])
            
            chart_data['volume'].append(float(row.get('volume', 0)))
            
            # 成交量均线
            chart_data['volume_ma']['ma5'].append(float(row.get('VOL_MA5', 0)) if pd.notna(row.get('VOL_MA5')) else None)
            chart_data['volume_ma']['ma10'].append(float(row.get('VOL_MA10', 0)) if pd.notna(row.get('VOL_MA10')) else None)
            
            # 均线
            chart_data['ma']['ma5'].append(float(row.get('MA5', 0)) if pd.notna(row.get('MA5')) else None)
            chart_data['ma']['ma20'].append(float(row.get('MA20', 0)) if pd.notna(row.get('MA20')) else None)
            chart_data['ma']['ma60'].append(float(row.get('MA60', 0)) if pd.notna(row.get('MA60')) else None)
            
            # 布林带
            chart_data['boll']['upper'].append(float(row.get('BOLL_upper', 0)) if pd.notna(row.get('BOLL_upper')) else None)
            chart_data['boll']['middle'].append(float(row.get('BOLL_middle', 0)) if pd.notna(row.get('BOLL_middle')) else None)
            chart_data['boll']['lower'].append(float(row.get('BOLL_lower', 0)) if pd.notna(row.get('BOLL_lower')) else None)
            
            # ATR
            chart_data['atr'].append(float(row.get('ATR', 0)) if pd.notna(row.get('ATR')) else None)
            
            # RSI
            chart_data['rsi'].append(float(row.get('RSI14', 0)) if pd.notna(row.get('RSI14')) else None)
            
            # MACD
            chart_data['macd']['macd'].append(float(row.get('MACD', 0)) if pd.notna(row.get('MACD')) else None)
            chart_data['macd']['signal'].append(float(row.get('MACD_signal', 0)) if pd.notna(row.get('MACD_signal')) else None)
            chart_data['macd']['histogram'].append(float(row.get('MACD_hist', 0)) if pd.notna(row.get('MACD_hist')) else None)
            
            # KDJ
            chart_data['kdj']['k'].append(float(row.get('KDJ_K', 0)) if pd.notna(row.get('KDJ_K')) else None)
            chart_data['kdj']['d'].append(float(row.get('KDJ_D', 0)) if pd.notna(row.get('KDJ_D')) else None)
            chart_data['kdj']['j'].append(float(row.get('KDJ_J', 0)) if pd.notna(row.get('KDJ_J')) else None)
        
        return format_response(data=chart_data, message="图表数据获取成功")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


# ==================== 错误处理 ====================

# ==================== 监控任务API ====================

@app.route('/api/monitor/tasks', methods=['GET'])
def get_monitor_tasks():
    """获取监控任务列表"""
    try:
        symbol = request.args.get('symbol')
        tasks = db.get_monitor_tasks(symbol=symbol)
        
        return format_response(data=dataframe_to_dict(tasks), message="获取成功")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/tasks', methods=['POST'])
def create_monitor_task():
    """创建监控任务"""
    try:
        data = request.get_json()
        
        symbol = data.get('symbol')
        task_name = data.get('task_name')
        email = data.get('email')
        update_schedule = data.get('update_schedule', '09:30')
        scan_schedule = data.get('scan_schedule', '15:30')
        strategy = data.get('strategy', 'default')
        remark = data.get('remark', '')
        
        if not all([symbol, task_name, email]):
            return format_response(success=False, message="缺少必要参数"), 400
        
        task_id = db.add_monitor_task(
            symbol, task_name, email, 
            update_schedule, scan_schedule, 
            strategy, remark
        )
        
        if task_id > 0:
            return format_response(data={'task_id': task_id}, message="创建成功")
        else:
            return format_response(success=False, message="创建失败"), 500
            
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/tasks/<int:task_id>', methods=['PUT'])
def update_monitor_task(task_id):
    """更新监控任务"""
    try:
        data = request.get_json()
        
        # 如果有conditions字段，转换为JSON字符串
        if 'conditions' in data:
            data['conditions'] = json.dumps(data['conditions'], ensure_ascii=False)
        
        success = db.update_monitor_task(task_id, **data)
        
        if success:
            return format_response(message="更新成功")
        else:
            return format_response(success=False, message="更新失败"), 404
            
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/tasks/<int:task_id>', methods=['DELETE'])
def delete_monitor_task(task_id):
    """删除监控任务"""
    try:
        success = db.delete_monitor_task(task_id)
        
        if success:
            return format_response(message="删除成功")
        else:
            return format_response(success=False, message="删除失败"), 404
            
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_monitor_task(task_id):
    """启用/禁用监控任务"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        success = db.toggle_monitor_task(task_id, enabled)
        
        if success:
            status = "启用" if enabled else "禁用"
            return format_response(message=f"任务已{status}")
        else:
            return format_response(success=False, message="操作失败"), 404
            
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/test-email', methods=['POST'])
def test_email():
    """测试邮件发送"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return format_response(success=False, message="请提供邮箱地址"), 400
        
        success = email_sender.send_test_email(email)
        
        if success:
            return format_response(message="测试邮件发送成功")
        else:
            return format_response(success=False, message="邮件发送失败"), 500
            
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动任务调度器"""
    try:
        task_scheduler.start()
        return format_response(message="调度器已启动")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止任务调度器"""
    try:
        task_scheduler.stop()
        return format_response(message="调度器已停止")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/scheduler/reload', methods=['POST'])
def reload_scheduler():
    """重新加载任务调度"""
    try:
        task_scheduler.reload_tasks()
        return format_response(message="任务调度已重新加载")
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


@app.route('/api/monitor/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """获取调度器状态"""
    try:
        status = {
            'running': task_scheduler.running,
            'jobs_count': len(task_scheduler.scheduled_jobs)
        }
        return format_response(data=status)
        
    except Exception as e:
        traceback.print_exc()
        return format_response(success=False, error=e), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return format_response(success=False, message="资源不存在"), 404


@app.errorhandler(500)
def internal_error(error):
    return format_response(success=False, message="服务器内部错误"), 500


# ==================== 启动服务 ====================

if __name__ == '__main__':
    print("=" * 60)
    print("量化决策系统 Web 版本")
    print("=" * 60)
    print("服务启动在: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动任务调度器
    try:
        task_scheduler.start()
        print("✓ 任务调度器已启动")
    except Exception as e:
        print(f"✗ 任务调度器启动失败: {e}")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # 停止调度器
        task_scheduler.stop()
