"""
技术指标计算模块
实现各种技术指标的计算
"""
import pandas as pd
import numpy as np
from typing import Optional


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(data: pd.Series, period: int) -> pd.Series:
        """
        计算移动平均线 (Moving Average)
        
        Args:
            data: 价格数据序列
            period: 周期
            
        Returns:
            MA序列
        """
        return data.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线 (Exponential Moving Average)
        
        Args:
            data: 价格数据序列
            period: 周期
            
        Returns:
            EMA序列
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        计算相对强弱指标 (Relative Strength Index)
        
        Args:
            data: 价格数据序列
            period: 周期，默认14
            
        Returns:
            RSI序列
        """
        # 计算价格变化
        delta = data.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss.replace(0, 1e-10)  # 避免除零
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> tuple:
        """
        计算MACD指标
        
        Args:
            data: 价格数据序列
            fast: 快线周期，默认12
            slow: 慢线周期，默认26
            signal: 信号线周期，默认9
            
        Returns:
            (MACD, Signal, Histogram)元组
        """
        # 计算快慢EMA
        ema_fast = TechnicalIndicators.calculate_ema(data, fast)
        ema_slow = TechnicalIndicators.calculate_ema(data, slow)
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal)
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, 
                                  std_dev: float = 2.0) -> tuple:
        """
        计算布林带 (Bollinger Bands)
        
        Args:
            data: 价格数据序列
            period: 周期，默认20
            std_dev: 标准差倍数，默认2.0
            
        Returns:
            (上轨, 中轨, 下轨)元组
        """
        # 中轨是移动平均线
        middle_band = TechnicalIndicators.calculate_ma(data, period)
        
        # 计算标准差
        std = data.rolling(window=period, min_periods=1).std()
        
        # 上下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
                     n: int = 9, m1: int = 3, m2: int = 3) -> tuple:
        """
        计算KDJ指标
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            n: RSV周期，默认9
            m1: K值周期，默认3
            m2: D值周期，默认3
            
        Returns:
            (K, D, J)元组
        """
        # 计算RSV
        low_min = low.rolling(window=n, min_periods=1).min()
        high_max = high.rolling(window=n, min_periods=1).max()
        
        rsv = (close - low_min) / (high_max - low_min).replace(0, 1e-10) * 100
        
        # 计算K值
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        
        # 计算D值
        d = k.ewm(com=m2-1, adjust=False).mean()
        
        # 计算J值
        j = 3 * k - 2 * d
        
        return k, d, j
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 14) -> pd.Series:
        """
        计算平均真实波幅 (Average True Range)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期，默认14
            
        Returns:
            ATR序列
        """
        # 计算真实波幅
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR
        atr = tr.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    @staticmethod
    def calculate_volume_ma(volume: pd.Series, period: int) -> pd.Series:
        """
        计算成交量移动平均 (Volume Moving Average)
        
        Args:
            volume: 成交量序列
            period: 周期
            
        Returns:
            成交量MA序列
        """
        return volume.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        计算能量潮指标 (On Balance Volume)
        
        Args:
            close: 收盘价序列
            volume: 成交量序列
            
        Returns:
            OBV序列
        """
        # 价格变化方向
        direction = np.sign(close.diff())
        direction[direction == 0] = 1  # 平盘视为上涨
        
        # 计算OBV
        obv = (direction * volume).cumsum()
        
        return obv
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加了所有指标的DataFrame
        """
        result = df.copy()
        
        # 确保列名正确
        close = result['close']
        high = result['high']
        low = result['low']
        volume = result['volume']
        
        # 移动平均线
        for period in [5, 10, 20, 30, 50, 60, 120, 250]:
            result[f'MA{period}'] = TechnicalIndicators.calculate_ma(close, period)
        
        # RSI
        for period in [6, 12, 14, 24, 30]:
            result[f'RSI{period}'] = TechnicalIndicators.calculate_rsi(close, period)
        
        # MACD
        macd, signal, hist = TechnicalIndicators.calculate_macd(close)
        result['MACD'] = macd
        result['MACD_signal'] = signal
        result['MACD_hist'] = hist
        
        # 布林带
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
        result['BOLL_upper'] = upper
        result['BOLL_middle'] = middle
        result['BOLL_lower'] = lower
        
        # KDJ
        k, d, j = TechnicalIndicators.calculate_kdj(high, low, close)
        result['KDJ_K'] = k
        result['KDJ_D'] = d
        result['KDJ_J'] = j
        
        # ATR
        result['ATR'] = TechnicalIndicators.calculate_atr(high, low, close)
        
        # 成交量均线
        for period in [5, 10, 20]:
            result[f'VOL_MA{period}'] = TechnicalIndicators.calculate_volume_ma(volume, period)
        
        # OBV
        result['OBV'] = TechnicalIndicators.calculate_obv(close, volume)
        
        return result
