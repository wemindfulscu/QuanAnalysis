"""
表达式解析引擎
解析和执行策略表达式
支持格式：[指标名,偏移量,数据类型,参数...]
例如：[RSI,0,c,14] 表示当天的14日RSI
"""
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from indicators.technical_indicators import TechnicalIndicators


class ExpressionParser:
    """策略表达式解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.indicator_pattern = r'\[([^\]]+)\]'
        self.operators = ['&&', '||', '>=', '<=', '>', '<', '==', '!=']
    
    def parse_indicator(self, expression: str) -> tuple:
        """
        解析指标表达式
        
        Args:
            expression: 指标表达式，如 [RSI,0,c,14]
            
        Returns:
            (指标名, 偏移量, 数据类型, 参数列表)
        """
        # 去除方括号并分割
        parts = expression.strip('[]').split(',')
        
        indicator_name = parts[0].strip()
        offset = int(parts[1].strip()) if len(parts) > 1 else 0
        data_type = parts[2].strip() if len(parts) > 2 else 'c'
        params = [p.strip() for p in parts[3:]] if len(parts) > 3 else []
        
        return indicator_name, offset, data_type, params
    
    def get_indicator_value(self, df: pd.DataFrame, indicator_name: str,
                           offset: int, data_type: str, params: List[str]) -> float:
        """
        获取指标值
        
        Args:
            df: 包含技术指标的DataFrame
            indicator_name: 指标名称
            offset: 偏移量（0=当前，-1=前一天）
            data_type: 数据类型（c=收盘价相关，t=成交量相关）
            params: 参数列表
            
        Returns:
            指标值
        """
        # 计算实际索引
        # offset=0 表示最新数据（最后一行）
        # offset=-1 表示前一天数据（倒数第二行）
        # offset=1 表示未来数据（通常不用）
        if offset <= 0:
            index = offset - 1  # 0 -> -1, -1 -> -2, -2 -> -3
        else:
            index = -1 - offset  # 1 -> -2（通常不会用到）
        
        try:
            if indicator_name == 'RSI':
                period = int(params[0]) if params else 14
                column_name = f'RSI{period}'
                if column_name in df.columns:
                    return df.iloc[index][column_name]
            
            elif indicator_name == 'MA':
                period = int(params[0]) if params else 20
                column_name = f'MA{period}'
                if column_name in df.columns:
                    return df.iloc[index][column_name]
            
            elif indicator_name == 'MACD':
                # 返回MACD柱状图值
                if 'MACD' in df.columns:
                    return df.iloc[index]['MACD']
            
            elif indicator_name == 'CLOSE':
                if 'close' in df.columns:
                    return df.iloc[index]['close']
            
            elif indicator_name == 'OPEN':
                if 'open' in df.columns:
                    return df.iloc[index]['open']
            
            elif indicator_name == 'HIGH':
                if 'high' in df.columns:
                    return df.iloc[index]['high']
            
            elif indicator_name == 'LOW':
                if 'low' in df.columns:
                    return df.iloc[index]['low']
            
            elif indicator_name == 'VOLUME' or indicator_name == 'TR':
                # TR表示成交量
                if 'volume' in df.columns:
                    return df.iloc[index]['volume']
            
            elif indicator_name == 'MTR':
                # MTR表示成交量均线
                period = int(params[0]) if params else 5
                column_name = f'VOL_MA{period}'
                if column_name in df.columns:
                    return df.iloc[index][column_name]
            
            elif indicator_name == 'KDJ_K':
                if 'KDJ_K' in df.columns:
                    return df.iloc[index]['KDJ_K']
            
            elif indicator_name == 'KDJ_D':
                if 'KDJ_D' in df.columns:
                    return df.iloc[index]['KDJ_D']
            
            elif indicator_name == 'KDJ_J':
                if 'KDJ_J' in df.columns:
                    return df.iloc[index]['KDJ_J']
            
            elif indicator_name == 'BOLL_upper':
                if 'BOLL_upper' in df.columns:
                    return df.iloc[index]['BOLL_upper']
            
            elif indicator_name == 'BOLL_lower':
                if 'BOLL_lower' in df.columns:
                    return df.iloc[index]['BOLL_lower']
            
            # 如果没有匹配，返回0
            return 0.0
            
        except (IndexError, KeyError) as e:
            print(f"获取指标值失败: {indicator_name}, 偏移: {offset}, 错误: {e}")
            return 0.0
    
    def evaluate_expression(self, expression: str, df: pd.DataFrame) -> bool:
        """
        评估表达式
        
        Args:
            expression: 策略表达式
            df: 包含技术指标的DataFrame
            
        Returns:
            表达式结果（True/False）
        """
        if df.empty or len(df) < 2:
            return False
        
        try:
            # 替换所有指标表达式为实际值
            working_expr = expression
            
            # 查找所有指标表达式
            matches = re.findall(self.indicator_pattern, working_expr)
            
            for match in matches:
                # 解析指标
                indicator_name, offset, data_type, params = self.parse_indicator(f'[{match}]')
                
                # 获取指标值
                value = self.get_indicator_value(df, indicator_name, offset, data_type, params)
                
                # 替换表达式
                working_expr = working_expr.replace(f'[{match}]', str(value), 1)
            
            # 替换逻辑运算符
            working_expr = working_expr.replace('&&', ' and ')
            working_expr = working_expr.replace('||', ' or ')
            
            # 评估表达式
            result = eval(working_expr)
            
            return bool(result)
            
        except Exception as e:
            print(f"评估表达式失败: {expression}, 错误: {e}")
            return False
    
    def validate_expression(self, expression: str) -> bool:
        """
        验证表达式格式是否正确
        
        Args:
            expression: 表达式字符串
            
        Returns:
            是否有效
        """
        try:
            # 检查括号匹配
            if expression.count('[') != expression.count(']'):
                return False
            
            # 检查是否包含指标
            matches = re.findall(self.indicator_pattern, expression)
            if not matches and expression not in ['0<50', '0>80']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def explain_expression(self, expression: str) -> str:
        """
        解释表达式含义
        
        Args:
            expression: 表达式字符串
            
        Returns:
            表达式的自然语言描述
        """
        explanation = expression
        
        # 替换常见模式
        replacements = {
            '[RSI,0,c,14]<30': 'RSI(14)小于30(超卖)',
            '[RSI,0,c,14]>70': 'RSI(14)大于70(超买)',
            '[MA,0,c,5]>[MA,0,c,50]': '5日均线上穿50日均线',
            '[MA,0,c,5]<[MA,0,c,50]': '5日均线下穿50日均线',
            '[MACD,0,c]>0': 'MACD大于0',
            '[MACD,0,c]<0': 'MACD小于0',
            '&&': '且',
            '||': '或'
        }
        
        for pattern, replacement in replacements.items():
            explanation = explanation.replace(pattern, replacement)
        
        return explanation
