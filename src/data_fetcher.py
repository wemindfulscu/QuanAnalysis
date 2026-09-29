"""
数据获取模块
使用AKShare获取行业指数、板块指数、中证指数和恒生科技指数数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time
import re


class DataFetcher:
    """数据获取器，使用AKShare获取市场数据"""
    
    def __init__(self):
        """初始化数据获取器"""
        self.retry_times = 3
        self.retry_delay = 2  # 秒
    
    def _retry_request(self, func, *args, **kwargs):
        """
        带重试的请求函数
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数执行结果
        """
        for i in range(self.retry_times):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"请求失败 (尝试 {i+1}/{self.retry_times}): {e}")
                if i < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def get_index_list(self) -> pd.DataFrame:
        """
        获取可用的指数列表
        
        Returns:
            指数列表DataFrame
        """
        try:
            # 获取所有行业板块指数
            df = self._retry_request(ak.stock_board_industry_name_em)
            return df
        except Exception as e:
            print(f"获取指数列表失败: {e}")
            return pd.DataFrame()
    
    def get_sector_list(self) -> pd.DataFrame:
        """
        获取概念板块列表
        
        Returns:
            板块列表DataFrame
        """
        try:
            # 获取概念板块
            df = self._retry_request(ak.stock_board_concept_name_em)
            return df
        except Exception as e:
            print(f"获取板块列表失败: {e}")
            return pd.DataFrame()
    
    def get_index_daily(self, symbol: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            symbol: 指数代码或名称
            start_date: 开始日期 (YYYY-MM-DD)，默认为1年前
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            日线数据DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
        
        try:
            # 获取行业板块历史行情
            df = self._retry_request(
                ak.stock_board_industry_hist_em,
                symbol=symbol,
                period="日k",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if df.empty:
                print(f"未获取到 {symbol} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_columns(df)
            return df
            
        except Exception as e:
            print(f"获取指数数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_concept_daily(self, symbol: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取概念板块日线数据
        
        Args:
            symbol: 板块名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日线数据DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
        
        try:
            # 获取概念板块历史行情
            df = self._retry_request(
                ak.stock_board_concept_hist_em,
                symbol=symbol,
                period="日k",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if df.empty:
                print(f"未获取到 {symbol} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_columns(df)
            return df
            
        except Exception as e:
            print(f"获取概念板块数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_csindex_daily(self, symbol: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取中证指数日线数据
        
        Args:
            symbol: 中证指数代码（如：931643）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日线数据DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
        
        try:
            # 获取中证指数历史行情
            df = self._retry_request(
                ak.stock_zh_index_hist_csindex,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                print(f"未获取到中证指数 {symbol} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_columns(df)
            return df
            
        except Exception as e:
            print(f"获取中证指数数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_hk_tech_daily(self, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取恒生科技指数日线数据
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日线数据DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
        
        try:
            # 获取恒生科技指数历史行情
            df = self._retry_request(
                ak.stock_hk_index_daily_em,
                symbol="恒生科技"
            )
            
            if df.empty:
                print(f"未获取到恒生科技指数的数据")
                return pd.DataFrame()
            
            # 过滤日期范围
            df['日期'] = pd.to_datetime(df['日期'])
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            df = df[(df['日期'] >= start_dt) & (df['日期'] <= end_dt)]
            
            # 标准化列名
            df = self._standardize_columns(df)
            return df
            
        except Exception as e:
            print(f"获取恒生科技指数数据失败: {e}")
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准化后的DataFrame
        """
        # AKShare返回的列名映射
        column_map = {
            '日期': '日期',
            '开盘': '开盘',
            '收盘': '收盘',
            '最高': '最高',
            '最低': '最低',
            '成交量': '成交量',
            '成交额': '成交额',
            '振幅': '振幅',
            '涨跌幅': '涨跌幅',
            '涨跌额': '涨跌额',
            '换手率': '换手率'
        }
        
        # 重命名列
        df = df.rename(columns=column_map)
        
        # 确保日期格式统一
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        
        return df
    
    def _detect_index_type(self, symbol: str) -> str:
        """
        自动检测指数类型
        
        Args:
            symbol: 指数代码或名称
            
        Returns:
            指数类型 (csindex/hk_tech/industry/concept)
        """
        # 中证指数：以93开头的代码
        if re.match(r'^93\d+$', symbol):
            return 'csindex'
        
        # 恒生科技指数
        if symbol in ['恒生科技', 'HSTECH', 'HSI TECH']:
            return 'hk_tech'
        
        # 板块代码：以BK开头
        if symbol.startswith('BK'):
            # 这里默认返回industry，实际可能是概念板块
            return 'industry'
        
        # 默认返回industry
        return 'industry'
    
    def fetch_incremental_data(self, symbol: str, last_date: Optional[str] = None,
                              index_type: Optional[str] = None) -> pd.DataFrame:
        """
        增量获取数据（从上次更新日期之后）
        
        Args:
            symbol: 指数代码或名称
            last_date: 上次更新的日期 (YYYY-MM-DD)
            index_type: 类型 (industry/concept/csindex/hk_tech)，None则自动检测
            
        Returns:
            增量数据DataFrame
        """
        # 如果没有指定类型，自动检测
        if index_type is None:
            index_type = self._detect_index_type(symbol)
        
        # 如果没有上次日期，获取最近一年的数据
        if last_date:
            # 从上次日期的下一天开始
            try:
                start_date = (datetime.strptime(last_date, '%Y-%m-%d') + 
                             timedelta(days=1)).strftime('%Y-%m-%d')
            except:
                # 如果日期格式不对，尝试其他格式
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"[DataFetcher] 增量更新: {symbol}, 日期范围: {start_date} ~ {end_date}")
        
        # 如果开始日期晚于结束日期，说明已是最新
        if start_date > end_date:
            print(f"[DataFetcher] {symbol} 数据已是最新 (start > end)")
            return pd.DataFrame()
        
        # 根据类型获取数据
        df = pd.DataFrame()
        try:
            if index_type == "csindex":
                df = self.get_csindex_daily(symbol, start_date, end_date)
            elif index_type == "hk_tech":
                df = self.get_hk_tech_daily(start_date, end_date)
            elif index_type == "concept":
                df = self.get_concept_daily(symbol, start_date, end_date)
            else:
                df = self.get_index_daily(symbol, start_date, end_date)
            
            if not df.empty:
                print(f"[DataFetcher] 增量获取到 {len(df)} 条数据")
            else:
                print(f"[DataFetcher] 增量获取：无新数据")
                
        except Exception as e:
            print(f"[DataFetcher] 增量获取失败: {e}")
            
        return df
    
    def get_csindex_list(self) -> pd.DataFrame:
        """
        获取中证指数列表
        
        Returns:
            中证指数列表DataFrame
        """
        try:
            # 获取中证指数列表
            df = self._retry_request(ak.index_stock_info_csindex)
            if not df.empty:
                # 重命名列以保持一致性
                if '指数代码' in df.columns and '指数名称' in df.columns:
                    df = df.rename(columns={'指数代码': '代码', '指数名称': '名称'})
            return df
        except Exception as e:
            print(f"获取中证指数列表失败: {e}")
            return pd.DataFrame()
    
    def search_index(self, keyword: str) -> pd.DataFrame:
        """
        搜索指数（支持行业板块、概念板块、中证指数）
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的指数列表
        """
        try:
            results = []
            
            # 搜索行业板块
            industry_df = self.get_index_list()
            if not industry_df.empty and '板块名称' in industry_df.columns:
                industry_result = industry_df[
                    industry_df['板块名称'].str.contains(keyword, na=False)
                ].copy()
                if not industry_result.empty:
                    industry_result['类型'] = '行业板块'
                    if '板块代码' in industry_result.columns:
                        industry_result['代码'] = industry_result['板块代码']
                    if '板块名称' in industry_result.columns:
                        industry_result['名称'] = industry_result['板块名称']
                    results.append(industry_result)
            
            # 搜索概念板块
            concept_df = self.get_sector_list()
            if not concept_df.empty and '板块名称' in concept_df.columns:
                concept_result = concept_df[
                    concept_df['板块名称'].str.contains(keyword, na=False)
                ].copy()
                if not concept_result.empty:
                    concept_result['类型'] = '概念板块'
                    if '板块代码' in concept_result.columns:
                        concept_result['代码'] = concept_result['板块代码']
                    if '板块名称' in concept_result.columns:
                        concept_result['名称'] = concept_result['板块名称']
                    results.append(concept_result)
            
            # 搜索中证指数
            csindex_df = self.get_csindex_list()
            if not csindex_df.empty:
                # 检查列名
                name_col = '名称' if '名称' in csindex_df.columns else '指数名称'
                if name_col in csindex_df.columns:
                    csindex_result = csindex_df[
                        csindex_df[name_col].str.contains(keyword, na=False)
                    ].copy()
                    if not csindex_result.empty:
                        csindex_result['类型'] = '中证指数'
                        if '指数代码' in csindex_result.columns and '代码' not in csindex_result.columns:
                            csindex_result['代码'] = csindex_result['指数代码']
                        if '指数名称' in csindex_result.columns and '名称' not in csindex_result.columns:
                            csindex_result['名称'] = csindex_result['指数名称']
                        results.append(csindex_result)
            
            # 检查是否搜索恒生科技
            if keyword in ['恒生科技', '恒生', '科技', 'HSTECH']:
                hk_tech_result = pd.DataFrame([{
                    '代码': 'HSTECH',
                    '名称': '恒生科技指数',
                    '类型': '港股指数'
                }])
                results.append(hk_tech_result)
            
            # 合并结果
            if results:
                result = pd.concat(results, ignore_index=True)
                # 选择显示的列
                display_cols = ['代码', '名称', '类型']
                display_cols = [col for col in display_cols if col in result.columns]
                if display_cols:
                    result = result[display_cols]
                return result
            else:
                return pd.DataFrame()
            
        except Exception as e:
            print(f"搜索指数失败: {e}")
            return pd.DataFrame()
    
    def fetch_data(self, symbol: str, index_type: str, 
                   start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        统一的数据获取接口（根据类型调用相应方法）
        
        Args:
            symbol: 指数代码或名称
            index_type: 指数类型 ('industry', 'concept', 'csindex', 'hk_tech')
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日线数据DataFrame
        """
        try:
            print(f"[DataFetcher] 开始获取数据: symbol={symbol}, type={index_type}")
            
            if index_type == 'industry':
                df = self.get_index_daily(symbol, start_date, end_date)
            elif index_type == 'concept':
                df = self.get_concept_daily(symbol, start_date, end_date)
            elif index_type == 'csindex':
                df = self.get_csindex_daily(symbol, start_date, end_date)
            elif index_type == 'hk_tech':
                df = self.get_hk_tech_daily(start_date, end_date)
            else:
                print(f"[DataFetcher] 未知的指数类型: {index_type}")
                return pd.DataFrame()
            
            if not df.empty:
                print(f"[DataFetcher] 成功获取 {len(df)} 条数据")
            else:
                print(f"[DataFetcher] 数据为空")
            
            return df
            
        except Exception as e:
            print(f"[DataFetcher] 获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
