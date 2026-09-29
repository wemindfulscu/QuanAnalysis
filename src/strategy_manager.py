"""
策略管理和执行模块
管理交易策略，执行信号检测
"""
import json
import os
from typing import List, Dict, Optional
import pandas as pd
from src.expression_parser import ExpressionParser
from indicators.technical_indicators import TechnicalIndicators


class Strategy:
    """交易策略类"""
    
    def __init__(self, name: str, buy_expression: str, sell_expression: str):
        """
        初始化策略
        
        Args:
            name: 策略名称
            buy_expression: 买入条件表达式
            sell_expression: 卖出条件表达式
        """
        self.name = name
        self.buy_expression = buy_expression
        self.sell_expression = sell_expression
        self.parser = ExpressionParser()
    
    def check_buy_signal(self, df: pd.DataFrame) -> bool:
        """
        检查买入信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            是否产生买入信号
        """
        return self.parser.evaluate_expression(self.buy_expression, df)
    
    def check_sell_signal(self, df: pd.DataFrame) -> bool:
        """
        检查卖出信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            是否产生卖出信号
        """
        return self.parser.evaluate_expression(self.sell_expression, df)
    
    def get_signal(self, df: pd.DataFrame) -> Optional[str]:
        """
        获取交易信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            'BUY', 'SELL' 或 None
        """
        if self.check_buy_signal(df):
            return 'BUY'
        elif self.check_sell_signal(df):
            return 'SELL'
        return None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'buy_expression': self.buy_expression,
            'sell_expression': self.sell_expression
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Strategy':
        """从字典创建策略"""
        return cls(
            name=data['name'],
            buy_expression=data['buy_expression'],
            sell_expression=data['sell_expression']
        )


class StrategyManager:
    """策略管理器"""
    
    def __init__(self, config_path: str = "config/strategies.json"):
        """
        初始化策略管理器
        
        Args:
            config_path: 策略配置文件路径
        """
        self.config_path = config_path
        self.strategies: List[Strategy] = []
        self.load_strategies()
    
    def load_strategies(self):
        """从配置文件加载策略"""
        if not os.path.exists(self.config_path):
            print(f"策略配置文件不存在: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.strategies = []
            for strategy_data in config.get('strategies', []):
                strategy = Strategy.from_dict(strategy_data)
                self.strategies.append(strategy)
            
            print(f"成功加载 {len(self.strategies)} 个策略")
            
        except Exception as e:
            print(f"加载策略配置失败: {e}")
    
    def save_strategies(self):
        """保存策略到配置文件"""
        try:
            config = {
                'strategies': [s.to_dict() for s in self.strategies]
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"策略已保存到 {self.config_path}")
            
        except Exception as e:
            print(f"保存策略配置失败: {e}")
    
    def add_strategy(self, name: str, buy_expression: str, sell_expression: str) -> bool:
        """
        添加新策略
        
        Args:
            name: 策略名称
            buy_expression: 买入条件
            sell_expression: 卖出条件
            
        Returns:
            是否添加成功
        """
        # 检查是否已存在
        if any(s.name == name for s in self.strategies):
            print(f"策略 {name} 已存在")
            return False
        
        strategy = Strategy(name, buy_expression, sell_expression)
        self.strategies.append(strategy)
        self.save_strategies()
        
        print(f"成功添加策略: {name}")
        return True
    
    def remove_strategy(self, name: str) -> bool:
        """
        删除策略
        
        Args:
            name: 策略名称
            
        Returns:
            是否删除成功
        """
        original_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s.name != name]
        
        if len(self.strategies) < original_count:
            self.save_strategies()
            print(f"成功删除策略: {name}")
            return True
        else:
            print(f"策略 {name} 不存在")
            return False
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """
        获取指定策略
        
        Args:
            name: 策略名称
            
        Returns:
            策略对象或None
        """
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        return None
    
    def list_strategies(self) -> List[Dict]:
        """
        列出所有策略
        
        Returns:
            策略列表
        """
        return [s.to_dict() for s in self.strategies]
    
    def scan_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        扫描所有策略信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            信号列表，每个信号包含策略名和信号类型
        """
        signals = []
        
        for strategy in self.strategies:
            signal = strategy.get_signal(df)
            if signal:
                signals.append({
                    'strategy_name': strategy.name,
                    'signal_type': signal,
                    'buy_expression': strategy.buy_expression,
                    'sell_expression': strategy.sell_expression
                })
        
        return signals
    
    def analyze_data(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        分析数据并生成报告
        
        Args:
            symbol: 指数代码
            df: 原始市场数据
            
        Returns:
            分析报告
        """
        if df.empty:
            return {
                'symbol': symbol,
                'error': '无数据'
            }
        
        # 计算技术指标
        df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
        
        # 扫描信号
        signals = self.scan_signals(df_with_indicators)
        
        # 获取最新数据
        latest = df_with_indicators.iloc[-1]
        
        # 确定主要信号（如果有多个策略信号，取第一个）
        main_signal = None
        if signals:
            main_signal = signals[0]['signal_type']
        
        report = {
            'symbol': symbol,
            'date': latest.get('trade_date', ''),
            'close': latest.get('close', 0),
            'signal': main_signal,  # 主要信号：BUY/SELL/None
            'signals': signals,      # 详细信号列表
            'indicators': {
                'RSI14': latest.get('RSI14', 0),
                'MA5': latest.get('MA5', 0),
                'MA20': latest.get('MA20', 0),
                'MA50': latest.get('MA50', 0),
                'MACD': latest.get('MACD', 0),
                'volume': latest.get('volume', 0)
            }
        }
        
        return report
