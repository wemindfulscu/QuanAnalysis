"""
测试修复后的功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager
from src.strategy_manager import StrategyManager
from indicators.technical_indicators import TechnicalIndicators

print("="*60)
print("测试数据去重和信号检测")
print("="*60)

# 初始化
db = DatabaseManager()
strategy_manager = StrategyManager()

# 测试1: 检查策略加载
print("\n[测试1] 策略加载")
strategies = strategy_manager.list_strategies()
print(f"✓ 已加载 {len(strategies)} 个策略")
for s in strategies[:3]:
    print(f"  - {s['name']}")

# 测试2: 获取监控列表
print("\n[测试2] 监控列表")
watchlist = db.get_watchlist()
print(f"✓ 监控列表中有 {len(watchlist)} 个项目")

if len(watchlist) > 0:
    # 测试3: 获取市场数据
    print("\n[测试3] 市场数据")
    symbol = watchlist.iloc[0]['symbol']
    name = watchlist.iloc[0]['name']
    print(f"测试指数: {name} ({symbol})")
    
    df = db.get_market_data(symbol, limit=100)
    if not df.empty:
        print(f"✓ 获取到 {len(df)} 条数据")
        print(f"  日期范围: {df.iloc[0]['date']} 到 {df.iloc[-1]['date']}")
        
        # 测试4: 计算技术指标
        print("\n[测试4] 技术指标计算")
        df = TechnicalIndicators.calculate_all_indicators(df)
        print(f"✓ 技术指标计算完成")
        print(f"  列数: {len(df.columns)}")
        
        # 显示部分指标
        latest = df.iloc[-1]
        print(f"  最新RSI14: {latest.get('RSI14', 'N/A')}")
        print(f"  最新MA5: {latest.get('MA5', 'N/A')}")
        print(f"  最新MA20: {latest.get('MA20', 'N/A')}")
        print(f"  最新MACD: {latest.get('MACD', 'N/A')}")
        
        # 测试5: 信号检测
        print("\n[测试5] 信号检测")
        analysis = strategy_manager.analyze_data(symbol, df)
        print(f"✓ 分析完成")
        print(f"  主要信号: {analysis.get('signal', 'None')}")
        print(f"  详细信号数: {len(analysis.get('signals', []))}")
        
        if analysis.get('signals'):
            print("  检测到的信号:")
            for sig in analysis['signals']:
                print(f"    - {sig['strategy_name']}: {sig['signal_type']}")
        else:
            print("  未检测到信号")
            
            # 显示一些关键指标值用于调试
            print("\n  关键指标值（用于调试）:")
            print(f"    RSI14 (最新): {latest.get('RSI14', 'N/A')}")
            print(f"    RSI14 (前一天): {df.iloc[-2].get('RSI14', 'N/A') if len(df) > 1 else 'N/A'}")
            print(f"    MA5: {latest.get('MA5', 'N/A')}")
            print(f"    MA50: {latest.get('MA50', 'N/A')}")
            print(f"    MACD: {latest.get('MACD', 'N/A')}")
            print(f"    MACD (前一天): {df.iloc[-2].get('MACD', 'N/A') if len(df) > 1 else 'N/A'}")
    else:
        print("✗ 无市场数据")
        print("  请先运行数据更新")
else:
    print("监控列表为空，请先添加监控项")

print("\n" + "="*60)
print("测试完成")
print("="*60)
