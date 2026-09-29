"""
量化决策系统主程序
支持监控列表管理、数据更新、信号检测
"""
import sys
import os
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager
from src.data_fetcher import DataFetcher
from src.strategy_manager import StrategyManager
from indicators.technical_indicators import TechnicalIndicators


class QuantAnalysisSystem:
    """量化分析系统"""
    
    def __init__(self, db_path: str = "data/quant_analysis.db"):
        """
        初始化系统
        
        Args:
            db_path: 数据库路径
        """
        self.db = DatabaseManager(db_path)
        self.fetcher = DataFetcher()
        self.strategy_manager = StrategyManager()
        
        print("=" * 60)
        print("量化决策系统启动")
        print("=" * 60)
    
    def add_watchlist_item(self, symbol: str, name: str, index_type: str = None):
        """
        添加监控项
        
        Args:
            symbol: 指数代码/名称
            name: 显示名称
            index_type: 类型（industry/concept/csindex/hk_tech），None则自动检测
        """
        # 如果没有指定类型，自动检测
        if index_type is None:
            index_type = self.fetcher._detect_index_type(symbol)
        
        success = self.db.add_to_watchlist(symbol, name, index_type)
        if success:
            print(f"✓ 已添加到监控列表: {name} ({symbol}) - 类型: {index_type}")
        else:
            print(f"✗ 添加失败: {name} ({symbol})")
    
    def remove_watchlist_item(self, symbol: str):
        """
        移除监控项
        
        Args:
            symbol: 指数代码
        """
        success = self.db.remove_from_watchlist(symbol)
        if success:
            print(f"✓ 已从监控列表移除: {symbol}")
        else:
            print(f"✗ 移除失败: {symbol}")
    
    def list_watchlist(self):
        """显示监控列表"""
        watchlist = self.db.get_watchlist()
        
        if watchlist.empty:
            print("监控列表为空")
            return
        
        print("\n" + "=" * 60)
        print("当前监控列表")
        print("=" * 60)
        
        for idx, row in watchlist.iterrows():
            print(f"{idx+1}. {row['name']} ({row['symbol']}) - {row['type']}")
    
    def update_all_data(self):
        """更新所有监控项的数据"""
        watchlist = self.db.get_watchlist()
        
        if watchlist.empty:
            print("监控列表为空，无需更新")
            return
        
        print("\n" + "=" * 60)
        print(f"开始更新数据 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        for idx, row in watchlist.iterrows():
            symbol = row['symbol']
            name = row['name']
            index_type = row['type']
            
            print(f"\n正在更新: {name} ({symbol})...")
            
            # 获取最新日期
            last_date = self.db.get_latest_date(symbol)
            
            if last_date:
                print(f"  上次更新: {last_date}")
            else:
                print(f"  首次获取数据")
            
            # 获取增量数据
            data = self.fetcher.fetch_incremental_data(symbol, last_date, index_type)
            
            if not data.empty:
                # 保存数据
                count = self.db.save_market_data(symbol, data)
                print(f"  ✓ 保存了 {count} 条新数据")
            else:
                print(f"  - 无新数据")
        
        print("\n" + "=" * 60)
        print("数据更新完成")
        print("=" * 60)
    
    def scan_signals(self, days: int = 1):
        """
        扫描交易信号
        
        Args:
            days: 检查最近几天的数据
        """
        watchlist = self.db.get_watchlist()
        
        if watchlist.empty:
            print("监控列表为空")
            return
        
        print("\n" + "=" * 60)
        print(f"信号扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_signals = []
        
        for idx, row in watchlist.iterrows():
            symbol = row['symbol']
            name = row['name']
            
            # 获取最近的数据（需要足够的数据计算指标）
            data = self.db.get_market_data(symbol, limit=250)
            
            if data.empty or len(data) < 50:
                print(f"\n{name} ({symbol}): 数据不足")
                continue
            
            # 分析数据
            report = self.strategy_manager.analyze_data(symbol, data)
            
            if 'error' in report:
                print(f"\n{name} ({symbol}): {report['error']}")
                continue
            
            # 显示结果
            signals = report.get('signals', [])
            
            if signals:
                print(f"\n【{name}】 ({symbol})")
                print(f"  日期: {report['date']}")
                print(f"  收盘: {report['close']:.2f}")
                print(f"  RSI(14): {report['indicators']['RSI14']:.2f}")
                print(f"  MA5: {report['indicators']['MA5']:.2f}")
                print(f"  MA20: {report['indicators']['MA20']:.2f}")
                print(f"  MACD: {report['indicators']['MACD']:.4f}")
                print(f"\n  检测到信号:")
                
                for signal in signals:
                    signal_type = signal['signal_type']
                    strategy_name = signal['strategy_name']
                    
                    emoji = "🔴 买入" if signal_type == 'BUY' else "🟢 卖出"
                    print(f"    {emoji} - {strategy_name}")
                    
                    # 保存信号到数据库
                    self.db.save_signal(
                        symbol=symbol,
                        strategy_name=strategy_name,
                        signal_type=signal_type,
                        signal_date=report['date'],
                        close_price=report['close']
                    )
                    
                    all_signals.append({
                        'symbol': symbol,
                        'name': name,
                        'signal': signal
                    })
        
        if not all_signals:
            print("\n未检测到任何信号")
        else:
            print(f"\n共检测到 {len(all_signals)} 个信号")
        
        print("=" * 60)
    
    def show_statistics(self):
        """显示统计信息"""
        watchlist = self.db.get_watchlist()
        
        print("\n" + "=" * 60)
        print("系统统计")
        print("=" * 60)
        print(f"监控项目数: {len(watchlist)}")
        print(f"策略数量: {len(self.strategy_manager.strategies)}")
        
        # 显示最近信号
        recent_signals = self.db.get_signals(days=7)
        print(f"最近7天信号: {len(recent_signals)}")
        
        print("=" * 60)
    
    def search_index(self, keyword: str):
        """
        搜索指数
        
        Args:
            keyword: 搜索关键词
        """
        print(f"\n搜索: {keyword}")
        print("=" * 60)
        
        results = self.fetcher.search_index(keyword)
        
        if results.empty:
            print("未找到匹配的指数")
            return
        
        print(f"找到 {len(results)} 个结果:\n")
        
        for idx, row in results.iterrows():
            code = row.get('代码', 'N/A')
            name = row.get('名称', row.get('板块名称', 'N/A'))
            index_type = row.get('类型', 'N/A')
            print(f"{idx+1}. [{code}] {name} - {index_type}")
    
    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n" + "=" * 60)
            print("量化决策系统")
            print("=" * 60)
            print("1. 查看监控列表")
            print("2. 添加监控项")
            print("3. 移除监控项")
            print("4. 更新数据")
            print("5. 扫描信号")
            print("6. 搜索指数")
            print("7. 查看统计")
            print("8. 策略管理")
            print("0. 退出")
            print("=" * 60)
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                self.list_watchlist()
            
            elif choice == '2':
                print("\n提示:")
                print("  - 板块代码以BK开头（如：BK0447）")
                print("  - 中证指数代码以93开头（如：931643）")
                print("  - 恒生科技指数输入：恒生科技")
                symbol = input("请输入指数代码/名称: ").strip()
                name = input("请输入显示名称: ").strip()
                print("类型说明: industry=行业板块, concept=概念板块, csindex=中证指数, hk_tech=港股指数")
                index_type = input("请输入类型(自动检测请留空): ").strip() or None
                self.add_watchlist_item(symbol, name, index_type)
            
            elif choice == '3':
                symbol = input("请输入要移除的指数代码: ").strip()
                self.remove_watchlist_item(symbol)
            
            elif choice == '4':
                self.update_all_data()
            
            elif choice == '5':
                self.scan_signals()
            
            elif choice == '6':
                keyword = input("请输入搜索关键词: ").strip()
                self.search_index(keyword)
            
            elif choice == '7':
                self.show_statistics()
            
            elif choice == '8':
                self.strategy_menu()
            
            elif choice == '0':
                print("感谢使用，再见！")
                break
            
            else:
                print("无效的选择，请重试")
    
    def strategy_menu(self):
        """策略管理菜单"""
        while True:
            print("\n" + "=" * 60)
            print("策略管理")
            print("=" * 60)
            print("1. 查看所有策略")
            print("2. 添加策略")
            print("3. 删除策略")
            print("0. 返回")
            print("=" * 60)
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                strategies = self.strategy_manager.list_strategies()
                for idx, strategy in enumerate(strategies, 1):
                    print(f"\n{idx}. {strategy['name']}")
                    print(f"   买入: {strategy['buy_expression']}")
                    print(f"   卖出: {strategy['sell_expression']}")
            
            elif choice == '2':
                name = input("策略名称: ").strip()
                buy_expr = input("买入表达式: ").strip()
                sell_expr = input("卖出表达式: ").strip()
                self.strategy_manager.add_strategy(name, buy_expr, sell_expr)
            
            elif choice == '3':
                name = input("要删除的策略名称: ").strip()
                self.strategy_manager.remove_strategy(name)
            
            elif choice == '0':
                break
            
            else:
                print("无效的选择，请重试")


def main():
    """主函数"""
    system = QuantAnalysisSystem()
    
    # 如果有命令行参数，执行对应命令
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'update':
            system.update_all_data()
        elif command == 'scan':
            system.scan_signals()
        elif command == 'list':
            system.list_watchlist()
        elif command == 'stats':
            system.show_statistics()
        else:
            print(f"未知命令: {command}")
            print("可用命令: update, scan, list, stats")
    else:
        # 进入交互模式
        system.interactive_menu()


if __name__ == "__main__":
    main()
