#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AKShare辅助工具，提供错误处理和重试机制"""

import akshare as ak
import time
import random
import requests
import os
from typing import Any, Optional, Callable
from functools import wraps
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class AKShareHelper:
    """AKShare辅助类，提供错误处理和重试机制"""
    
    def __init__(self):
        self.max_retries = 2  # 增加重试次数
        self.base_delay = 3.0  # 增加基础延迟
        self.max_delay = 10.0  # 增加最大延迟
        self.backoff_factor = 2.0  # 指数退避因子
        
        # 配置requests会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 设置AKShare的requests会话
        # 注意：AKShare大部分接口不需要token，移除空token设置
        # 如果需要特定接口的token，请在.env文件中配置AKSHARE_TOKEN
        akshare_token = os.getenv('AKSHARE_TOKEN')
        if akshare_token:
            try:
                ak.set_token(akshare_token)
                logger.info("AKShare token已设置")
            except Exception as e:
                logger.warning(f"设置AKShare token失败: {e}")
        else:
            logger.info("未配置AKShare token，使用免费接口")
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数，支持重试机制"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 添加延迟（第一次调用也有延迟）
                if attempt > 0:
                    delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
                    logger.info(f"重试第 {attempt} 次，延迟 {delay:.1f} 秒")
                    time.sleep(delay)
                else:
                    time.sleep(self.base_delay)
                
                # 执行函数
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"重试成功，第 {attempt} 次尝试")
                return result
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                if attempt < self.max_retries and self._is_retryable_error(e):
                    logger.warning(f"调用失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {error_msg}")
                    continue
                else:
                    logger.error(f"调用最终失败: {error_msg}")
                    break
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_msg = str(error).lower()
        
        # 网络相关错误
        network_errors = [
            'connection', 'timeout', 'network', 'dns',
            'socket', 'ssl', 'certificate', 'unreachable',
            'refused', 'reset', 'broken pipe', 'connection aborted',
            'remote end closed connection', 'connection error',
            'read timeout', 'connection timeout'
        ]
        
        # 服务器错误
        server_errors = [
            '500', '502', '503', '504', 'internal server error',
            'bad gateway', 'service unavailable', 'gateway timeout',
            'server error', 'upstream', 'temporary failure'
        ]
        
        # 限流错误
        rate_limit_errors = [
            'rate limit', 'too many requests', '429',
            'quota exceeded', 'api limit', 'frequency limit',
            'request limit', 'throttle'
        ]
        
        # AKShare特定错误
        akshare_errors = [
            'akshare', 'ak.', 'data source error',
            'no data', 'empty response', 'invalid response'
        ]
        
        # 临时性错误
        temporary_errors = [
            'temporary', 'temporarily', 'try again',
            'retry', 'unavailable', 'busy'
        ]
        
        all_retryable = network_errors + server_errors + rate_limit_errors + akshare_errors + temporary_errors
        
        # 检查是否为可重试错误
        is_retryable = any(err in error_msg for err in all_retryable)
        
        # 排除明确不可重试的错误
        non_retryable_errors = [
            'invalid symbol', 'symbol not found', 'invalid parameter',
            'authentication', 'unauthorized', '401', '403',
            'not found', '404', 'method not allowed', '405'
        ]
        
        is_non_retryable = any(err in error_msg for err in non_retryable_errors)
        
        return is_retryable and not is_non_retryable
    
    def safe_call(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """安全调用AKShare函数，返回None如果失败"""
        try:
            return self.retry_with_backoff(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"AKShare调用最终失败: {func.__name__} - {e}")
            return None
    
    # 包装常用的AKShare函数
    def get_stock_list(self):
        """获取股票列表 (已禁用，经常连接失败)"""
        # return self.safe_call(ak.stock_zh_a_spot_em)
        logger.info("股票列表API已禁用，因为经常连接失败")
        return None
    
    def get_stock_info(self, symbol: str):
        """获取股票基本信息"""
        return self.safe_call(ak.stock_individual_info_em, symbol=symbol)
    
    def get_financial_abstract(self, symbol: str):
        """获取财务摘要"""
        return self.safe_call(ak.stock_financial_abstract, symbol=symbol)
    
    def get_stock_history(self, symbol: str, period: str = "daily", 
                         start_date: str = None, end_date: str = None, 
                         adjust: str = "qfq"):
        """获取股票历史数据"""
        kwargs = {
            'symbol': symbol,
            'period': period,
            'adjust': adjust
        }
        
        if start_date:
            kwargs['start_date'] = start_date
        if end_date:
            kwargs['end_date'] = end_date
            
        return self.safe_call(ak.stock_zh_a_hist, **kwargs)
    
    def get_stock_news(self, symbol: str):
        """获取股票新闻"""
        return self.safe_call(ak.stock_news_em, symbol=symbol)
    
    def get_stock_financial_data(self, symbol: str, indicator: str = "资产负债表", period: str = "yearly"):
        """获取财务数据"""
        try:
            if indicator == "资产负债表":
                # 资产负债表只有按年度的接口
                return self.safe_call(ak.stock_balance_sheet_by_yearly_em, symbol=symbol)
            elif indicator == "利润表":
                if period == "quarterly":
                    return self.safe_call(ak.stock_profit_sheet_by_quarterly_em, symbol=symbol)
                else:
                    return self.safe_call(ak.stock_profit_sheet_by_yearly_em, symbol=symbol)
            elif indicator == "现金流量表":
                if period == "quarterly":
                    return self.safe_call(ak.stock_cash_flow_sheet_by_quarterly_em, symbol=symbol)
                else:
                    return self.safe_call(ak.stock_cash_flow_sheet_by_yearly_em, symbol=symbol)
            else:
                logger.warning(f"未知的财务指标类型: {indicator}")
                return None
        except Exception as e:
            logger.error(f"获取财务数据失败: {symbol} - {indicator} - {e}")
            return None
    
    def get_macro_economic_data(self, limit: int = 100):
        """获取宏观经济数据 - 全球事件
        
        Args:
            limit: 数据条数限制，默认100条
            
        Returns:
            宏观经济数据DataFrame或None
        """
        try:
            # 获取宏观-全球事件数据
            macro_data = self.safe_call(ak.news_economic_baidu)
            
            if macro_data is None or macro_data.empty:
                logger.warning("宏观经济数据为空")
                return None
            
            # 限制数据条数
            if len(macro_data) > limit:
                macro_data = macro_data.head(limit)
            
            # 过滤最近一年的数据
            if '时间' in macro_data.columns:
                try:
                    import pandas as pd
                    # 转换时间列为datetime
                    macro_data['时间'] = pd.to_datetime(macro_data['时间'])
                    # 获取最近一年的数据
                    one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
                    macro_data = macro_data[macro_data['时间'] >= one_year_ago]
                except Exception as e:
                    logger.warning(f"时间过滤失败: {e}")
            
            logger.info(f"成功获取{len(macro_data)}条宏观经济数据")
            return macro_data
            
        except Exception as e:
            logger.error(f"获取宏观经济数据失败: {e}")
            return None
    
    # ==================== 扩展数据获取功能 ====================
    
    def get_stock_technical_indicators(self, symbol: str, period: str = "daily", adjust: str = "qfq"):
        """获取股票技术指标数据"""
        try:
            # 获取历史数据用于计算技术指标
            hist_data = self.get_stock_history(symbol, period=period, adjust=adjust)
            if hist_data is None or hist_data.empty:
                return None
            
            # 返回原始数据，技术指标计算在其他模块中进行
            return hist_data
        except Exception as e:
            logger.error(f"获取技术指标数据失败: {symbol} - {e}")
            return None
    
    def get_stock_realtime_data(self, symbol: str):
        """获取股票实时数据"""
        return self.safe_call(ak.stock_zh_a_spot_em)
    
    def get_stock_minute_data(self, symbol: str, period: str = "1"):
        """获取股票分钟级数据
        
        Args:
            symbol: 股票代码
            period: 分钟周期，可选 1, 5, 15, 30, 60
        """
        return self.safe_call(ak.stock_zh_a_hist_min_em, symbol=symbol, period=period)
    
    def get_stock_holder_data(self, symbol: str):
        """获取股东数据"""
        try:
            # 获取十大股东
            top_holders = self.safe_call(ak.stock_top_10_holders_em, symbol=symbol)
            
            # 获取十大流通股东
            top_tradable_holders = self.safe_call(ak.stock_top_10_tradable_holders_em, symbol=symbol)
            
            return {
                "top_holders": top_holders,
                "top_tradable_holders": top_tradable_holders
            }
        except Exception as e:
            logger.error(f"获取股东数据失败: {symbol} - {e}")
            return None
    
    def get_stock_margin_data(self, symbol: str):
        """获取融资融券数据"""
        return self.safe_call(ak.stock_margin_detail_em, symbol=symbol)
    
    def get_stock_fund_flow(self, symbol: str):
        """获取资金流向数据"""
        try:
            # 获取个股资金流向
            fund_flow = self.safe_call(ak.stock_individual_fund_flow_em, symbol=symbol)
            
            # 获取主力资金流向
            main_fund_flow = self.safe_call(ak.stock_main_fund_flow_em, symbol=symbol)
            
            return {
                "individual_flow": fund_flow,
                "main_flow": main_fund_flow
            }
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {symbol} - {e}")
            return None
    
    def get_stock_dragon_tiger_data(self, symbol: str = None, date: str = None):
        """获取龙虎榜数据
        
        Args:
            symbol: 股票代码，可选
            date: 日期，格式YYYYMMDD，可选
        """
        try:
            if symbol:
                # 获取个股龙虎榜数据
                return self.safe_call(ak.stock_lhb_detail_em, symbol=symbol)
            else:
                # 获取龙虎榜汇总数据
                if date:
                    return self.safe_call(ak.stock_lhb_em, date=date)
                else:
                    return self.safe_call(ak.stock_lhb_em)
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {symbol} - {e}")
            return None
    
    def get_industry_data(self, symbol: str = None):
        """获取行业数据"""
        try:
            if symbol:
                # 获取个股所属行业
                stock_info = self.get_stock_info(symbol)
                if stock_info is not None:
                    info_dict = dict(zip(stock_info['item'], stock_info['value']))
                    industry = info_dict.get('所属行业', '')
                    return {"industry": industry}
            
            # 获取行业板块数据
            industry_data = self.safe_call(ak.stock_board_industry_name_em)
            return {"industry_list": industry_data}
            
        except Exception as e:
            logger.error(f"获取行业数据失败: {symbol} - {e}")
            return None
    
    def get_concept_data(self, symbol: str = None):
        """获取概念板块数据"""
        try:
            if symbol:
                # 获取个股概念
                concept_data = self.safe_call(ak.stock_board_concept_cons_em, symbol=symbol)
                return {"stock_concepts": concept_data}
            else:
                # 获取概念板块列表
                concept_list = self.safe_call(ak.stock_board_concept_name_em)
                return {"concept_list": concept_list}
                
        except Exception as e:
            logger.error(f"获取概念数据失败: {symbol} - {e}")
            return None
    
    def get_market_sentiment_indicators(self):
        """获取市场情绪指标"""
        try:
            sentiment_data = {}
            
            # 获取A股成交额
            try:
                turnover = self.safe_call(ak.stock_zh_a_spot_em)
                if turnover is not None and not turnover.empty:
                    total_turnover = turnover['成交额'].sum() if '成交额' in turnover.columns else 0
                    sentiment_data['total_turnover'] = total_turnover
            except Exception:
                pass
            
            # 获取涨跌停数据
            try:
                limit_up = self.safe_call(ak.stock_zh_a_st_em, symbol="涨停")
                limit_down = self.safe_call(ak.stock_zh_a_st_em, symbol="跌停")
                
                sentiment_data['limit_up_count'] = len(limit_up) if limit_up is not None else 0
                sentiment_data['limit_down_count'] = len(limit_down) if limit_down is not None else 0
            except Exception:
                pass
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"获取市场情绪指标失败: {e}")
            return None
    
    def get_financial_ratios(self, symbol: str):
        """获取财务比率数据"""
        try:
            # 获取财务指标
            financial_indicators = self.safe_call(ak.stock_financial_em, symbol=symbol)
            
            # 获取杜邦分析
            dupont_data = self.safe_call(ak.stock_dupont_em, symbol=symbol)
            
            return {
                "financial_indicators": financial_indicators,
                "dupont_analysis": dupont_data
            }
            
        except Exception as e:
            logger.error(f"获取财务比率失败: {symbol} - {e}")
            return None
    
    def get_analyst_ratings(self, symbol: str):
        """获取分析师评级数据"""
        try:
            # 获取机构评级
            ratings = self.safe_call(ak.stock_institute_recommend_em, symbol=symbol)
            
            # 获取业绩预告
            forecast = self.safe_call(ak.stock_forecast_em, symbol=symbol)
            
            return {
                "ratings": ratings,
                "forecast": forecast
            }
            
        except Exception as e:
            logger.error(f"获取分析师评级失败: {symbol} - {e}")
            return None
    
    def get_risk_indicators(self, symbol: str):
        """获取风险指标数据"""
        try:
            risk_data = {}
            
            # 获取历史数据计算波动率
            hist_data = self.get_stock_history(symbol, period="daily")
            if hist_data is not None and not hist_data.empty and len(hist_data) > 20:
                import pandas as pd
                import numpy as np
                
                # 计算收益率
                hist_data['returns'] = hist_data['收盘'].pct_change()
                
                # 计算波动率（年化）
                volatility = hist_data['returns'].std() * np.sqrt(252)
                risk_data['volatility'] = volatility
                
                # 计算最大回撤
                cumulative = (1 + hist_data['returns']).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()
                risk_data['max_drawdown'] = abs(max_drawdown)
                
                # 计算VaR (95%置信度)
                var_95 = hist_data['returns'].quantile(0.05)
                risk_data['var_95'] = abs(var_95)
            
            # 获取财务风险指标
            financial_data = self.get_financial_ratios(symbol)
            if financial_data and financial_data.get('financial_indicators') is not None:
                fin_indicators = financial_data['financial_indicators']
                if not fin_indicators.empty:
                    # 提取关键风险指标
                    latest_data = fin_indicators.iloc[0] if len(fin_indicators) > 0 else None
                    if latest_data is not None:
                        # 资产负债率
                        if '资产负债率' in latest_data:
                            risk_data['debt_ratio'] = latest_data['资产负债率']
                        
                        # 流动比率
                        if '流动比率' in latest_data:
                            risk_data['current_ratio'] = latest_data['流动比率']
            
            return risk_data
            
        except Exception as e:
            logger.error(f"获取风险指标失败: {symbol} - {e}")
            return None
    
    def get_comprehensive_stock_data(self, symbol: str):
        """获取股票综合数据"""
        try:
            comprehensive_data = {
                "basic_info": self.get_stock_info(symbol),
                "price_data": self.get_stock_history(symbol),
                "financial_data": self.get_financial_ratios(symbol),
                "fund_flow": self.get_stock_fund_flow(symbol),
                "holder_data": self.get_stock_holder_data(symbol),
                "industry_data": self.get_industry_data(symbol),
                "concept_data": self.get_concept_data(symbol),
                "analyst_ratings": self.get_analyst_ratings(symbol),
                "risk_indicators": self.get_risk_indicators(symbol),
                "margin_data": self.get_stock_margin_data(symbol),
                "dragon_tiger": self.get_stock_dragon_tiger_data(symbol)
            }
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"获取综合股票数据失败: {symbol} - {e}")
            return None

# 创建全局实例
akshare_helper = AKShareHelper()

# 装饰器函数
def akshare_retry(max_retries: int = 3, base_delay: float = 1.0):
    """AKShare重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            helper = AKShareHelper()
            helper.max_retries = max_retries
            helper.base_delay = base_delay
            return helper.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator

# 测试函数
def test_akshare_helper():
    """测试AKShare辅助工具"""
    print("测试AKShare辅助工具")
    print("=" * 50)
    
    helper = AKShareHelper()
    
    # 测试1: 获取股票列表
    print("\n1. 测试获取股票列表...")
    df_stocks = helper.get_stock_list()
    if df_stocks is not None and not df_stocks.empty:
        print(f"   成功获取 {len(df_stocks)} 只股票")
        print(f"   示例: {df_stocks.head(3)[['代码', '名称']].to_string(index=False)}")
    else:
        print("   失败")
    
    # 测试2: 获取特定股票信息
    print("\n2. 测试获取股票信息 (600030)...")
    df_info = helper.get_stock_info("600030")
    if df_info is not None and not df_info.empty:
        print(f"   成功获取股票信息，共 {len(df_info)} 项")
        info_dict = dict(zip(df_info['item'], df_info['value']))
        for key in ['股票代码', '股票简称', '总市值']:
            if key in info_dict:
                print(f"   {key}: {info_dict[key]}")
    else:
        print("   失败")
    
    # 测试3: 获取财务摘要
    print("\n3. 测试获取财务摘要 (600030)...")
    df_abstract = helper.get_financial_abstract("600030")
    if df_abstract is not None and not df_abstract.empty:
        print(f"   成功获取财务摘要，共 {len(df_abstract)} 项指标")
        print(f"   示例指标: {df_abstract.head(3)['指标'].tolist()}")
    else:
        print("   失败")
    
    # 测试4: 获取历史价格
    print("\n4. 测试获取历史价格 (600030)...")
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    df_hist = helper.get_stock_history("600030", start_date=start_date, end_date=end_date)
    if df_hist is not None and not df_hist.empty:
        print(f"   成功获取历史价格，共 {len(df_hist)} 个交易日")
        print(f"   最新价格: {df_hist.iloc[-1]['收盘']:.2f}")
    else:
        print("   失败")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_akshare_helper()