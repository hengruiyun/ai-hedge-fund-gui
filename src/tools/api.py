import datetime
import os
import pandas as pd
import requests
import time
import threading
import numpy as np
from typing import List, Dict, Any, Optional
import random
from functools import wraps
import re

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
    CompanyFactsResponse,
)

# 导入AKShare库和辅助工具
try:
    import akshare as ak
    from src.utils.akshare_helper import akshare_helper, akshare_retry
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    ak = None
    akshare_helper = None

# 导入技术指标计算库
try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    talib = None





# 全局配置
REQUEST_DELAY_MIN = 1.0  # 最小延迟时间（秒）
REQUEST_DELAY_MAX = 3.0  # 最大延迟时间（秒）
MAX_RETRIES = 3  # 最大重试次数
RETRY_BASE_DELAY = 2  # 重试基础延迟（秒）


def parse_tickers_input(input_str: str) -> List[str]:
    """
    解析股票代码输入，支持多种分隔符
    
    支持的分隔符：逗号(,)、分号(;)、空格、制表符、换行符
    自动去除空格和转换为大写
    
    Args:
        input_str: 用户输入的股票代码字符串
        
    Returns:
        清理后的股票代码列表
        
    Examples:
        parse_tickers_input("AAPL,MSFT;GOOGL TSLA") -> ["AAPL", "MSFT", "GOOGL", "TSLA"]
        parse_tickers_input("000001.SZ, 600519.SH ; 00700") -> ["000001.SZ", "600519.SH", "00700"]
    """
    if not input_str or not input_str.strip():
        return []
    
    # 使用正则表达式分割，支持逗号、分号、空格、制表符、换行符
    # 支持多个连续分隔符
    tickers = re.split(r'[,;\s\t\n]+', input_str.strip())
    
    # 过滤空字符串并转换为大写
    cleaned_tickers = []
    for ticker in tickers:
        ticker = ticker.strip().upper()
        if ticker:  # 过滤空字符串
            cleaned_tickers.append(ticker)
    
    return cleaned_tickers


def rate_limit(min_delay=REQUEST_DELAY_MIN, max_delay=REQUEST_DELAY_MAX):
    """速率限制装饰器，在请求之间添加随机延迟"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 检查是否需要延迟（避免在缓存命中时延迟）
            if hasattr(wrapper, '_last_call_time'):
                elapsed = time.time() - wrapper._last_call_time
                min_interval = min_delay
                if elapsed < min_interval:
                    sleep_time = random.uniform(min_delay, max_delay)
                    time.sleep(sleep_time)
            
            try:
                result = func(*args, **kwargs)
                wrapper._last_call_time = time.time()
                return result
            except Exception as e:
                wrapper._last_call_time = time.time()
                raise e
        return wrapper
    return decorator

def retry_on_failure(max_retries=MAX_RETRIES, base_delay=RETRY_BASE_DELAY):
    """重试装饰器，在失败时进行重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    # 计算重试延迟时间
                    delay = min(base_delay * (2 ** attempt), 30)  # 最大30秒
                    print(f"尝试 {attempt + 1} 失败，{delay}秒后重试: {str(e)[:50]}...")
                    time.sleep(delay)
            
            # 所有重试都失败，抛出最后的异常
            raise last_exception
        return wrapper
    return decorator

# Global cache instance
_cache = get_cache()

# Global interrupt flag for GUI
_interrupt_flag = threading.Event()


def set_api_interrupt():
    """设置API中断标志，用于停止正在进行的API请求"""
    _interrupt_flag.set()


def clear_api_interrupt():
    """清除API中断标志"""
    _interrupt_flag.clear()


def clear_cache():
    """清空所有API缓存数据"""
    return _cache.clear_cache()


def get_cache_info():
    """获取API缓存信息"""
    return _cache.get_cache_info()


def _check_akshare_available():
    """检查AKShare是否可用"""
    if not HAS_AKSHARE:
        raise ImportError("AKShare库未安装，请运行: pip install akshare")


def _safe_float(value):
    """安全转换为浮点数"""
    try:
        if pd.isna(value) or value == '' or value == '-' or value is None:
            return 0.0
        return float(value)
    except:
        return 0.0


def _safe_int(value):
    """安全转换为整数"""
    try:
        if pd.isna(value) or value == '' or value == '-' or value is None:
            return 0
        return int(float(value))
    except:
        return 0


def _detect_market(symbol: str) -> str:
    """检测股票所属市场 - 增强版"""
    # 去除空格和转换为大写
    symbol = symbol.strip().upper()
    
    # 处理带交易所后缀的情况
    if symbol.endswith('.SH') or symbol.endswith('.SZ'):
        return 'CN'
    elif symbol.endswith('.HK'):
        return 'HK'
    elif symbol.endswith('.US'):
        return 'US'
    
    # 基于长度和字符类型判断
    if len(symbol) == 6 and symbol.isdigit():
        return 'CN'  # A股：6位数字
    elif len(symbol) <= 5 and symbol.isdigit():
        return 'HK'  # 港股：1-5位数字
    elif symbol.isalpha() and 1 <= len(symbol) <= 5:
        return 'US'  # 美股：1-5位字母
    
    # 默认返回US（对于未知格式）
    return 'US'


def _convert_cn_symbol(symbol: str) -> str:
    """转换CN市场股票代码为标准格式"""
    symbol = symbol.strip().upper()
    
    # 如果带有交易所后缀，去除后缀
    if symbol.endswith('.SH') or symbol.endswith('.SZ'):
        return symbol[:-3]
    
    # 如果是6位数字，直接返回
    if len(symbol) == 6 and symbol.isdigit():
        return symbol
    
    return symbol


def _convert_hk_symbol(symbol: str) -> str:
    """转换港股代码为AKShare标准格式"""
    symbol = symbol.strip().upper()
    
    # 去除.HK后缀
    if symbol.endswith('.HK'):
        symbol = symbol[:-3]
    
    # 港股代码补齐到5位数字（前面补0）
    if symbol.isdigit():
        return symbol.zfill(5)
    
    return symbol


def _convert_us_symbol(symbol: str) -> str:
    """转换美股代码为标准格式"""
    symbol = symbol.strip().upper()
    
    # 去除.US后缀
    if symbol.endswith('.US'):
        return symbol[:-3]
    
    return symbol


# =============================================================================
# 计算函数 - 为不支持的数据生成计算逻辑
# =============================================================================

def _calculate_enterprise_value(market_cap: float, total_debt: float, cash: float) -> float:
    """计算企业价值 = 市值 + 总债务 - 现金及现金等价物"""
    if market_cap is None:
        return None
    debt = total_debt or 0.0
    cash_amount = cash or 0.0
    return market_cap + debt - cash_amount


def _calculate_ev_to_ebitda(enterprise_value: float, ebitda: float) -> float:
    """计算EV/EBITDA比率"""
    if not enterprise_value or not ebitda or ebitda <= 0:
        return None
    return enterprise_value / ebitda


def _calculate_ev_to_sales(enterprise_value: float, revenue: float) -> float:
    """计算EV/Sales比率"""
    if not enterprise_value or not revenue or revenue <= 0:
        return None
    return enterprise_value / revenue


def _calculate_ebitda(operating_income: float, depreciation: float, amortization: float = 0) -> float:
    """计算EBITDA = 营业利润 + 折旧 + 摊销"""
    if operating_income is None:
        return None
    depreciation_amount = depreciation or 0.0
    amortization_amount = amortization or 0.0
    return operating_income + depreciation_amount + amortization_amount


def _calculate_ebitda_margin(ebitda: float, revenue: float) -> float:
    """计算EBITDA利润率"""
    if not ebitda or not revenue or revenue <= 0:
        return None
    return ebitda / revenue


def _calculate_working_capital(current_assets: float, current_liabilities: float) -> float:
    """计算营运资金 = 流动资产 - 流动负债"""
    if current_assets is None or current_liabilities is None:
        return None
    return current_assets - current_liabilities


def _calculate_free_cash_flow(operating_cash_flow: float, capital_expenditures: float) -> float:
    """计算自由现金流 = 经营现金流 - 资本支出"""
    if operating_cash_flow is None or capital_expenditures is None:
        return None
    return operating_cash_flow - capital_expenditures


def _calculate_return_on_invested_capital(ebit: float, tax_rate: float, invested_capital: float) -> float:
    """计算投入资本回报率 = EBIT * (1 - 税率) / 投入资本"""
    if not ebit or not invested_capital or invested_capital <= 0:
        return None
    tax_rate_val = tax_rate or 0.25  # 默认税率25%
    return (ebit * (1 - tax_rate_val)) / invested_capital


def _calculate_shares_outstanding(market_cap: float, stock_price: float) -> float:
    """计算流通股数 = 市值 / 股价"""
    if not market_cap or not stock_price or stock_price <= 0:
        return None
    return market_cap / stock_price


def _estimate_tax_rate(tax_expense: float, pretax_income: float) -> float:
    """估算税率 = 税费 / 税前利润"""
    if not tax_expense or not pretax_income or pretax_income <= 0:
        return 0.25  # 默认税率25%
    return tax_expense / pretax_income


def _calculate_book_value_per_share(shareholders_equity: float, shares_outstanding: float) -> float:
    """计算每股净资产 = 股东权益 / 流通股数"""
    if not shareholders_equity or not shares_outstanding or shares_outstanding <= 0:
        return None
    return shareholders_equity / shares_outstanding


def _calculate_price_to_book_ratio(stock_price: float, book_value_per_share: float) -> float:
    """计算市净率 = 股价 / 每股净资产"""
    if not stock_price or not book_value_per_share or book_value_per_share <= 0:
        return None
    return stock_price / book_value_per_share


def _calculate_price_to_sales_ratio(market_cap: float, revenue: float) -> float:
    """计算市销率 = 市值 / 营业收入"""
    if not market_cap or not revenue or revenue <= 0:
        return None
    return market_cap / revenue


def _calculate_peg_ratio(pe_ratio: float, earnings_growth_rate: float) -> float:
    """计算PEG比率 = 市盈率 / 盈利增长率"""
    if not pe_ratio or not earnings_growth_rate or earnings_growth_rate <= 0:
        return None
    return pe_ratio / (earnings_growth_rate * 100)  # 增长率转换为百分比


def _calculate_debt_to_total_capital(total_debt: float, shareholders_equity: float) -> float:
    """计算债务占总资本比率 = 总债务 / (总债务 + 股东权益)"""
    if total_debt is None or shareholders_equity is None:
        return None
    total_capital = total_debt + shareholders_equity
    if total_capital <= 0:
        return None
    return total_debt / total_capital


def _interpolate_financial_data(financial_data: List[Dict], missing_fields: List[str]) -> List[Dict]:
    """为缺失的财务数据字段进行插值或计算"""
    enhanced_data = []
    
    for data in financial_data:
        enhanced = data.copy()
        
        # 获取基础数据
        revenue = enhanced.get('revenue', 0)
        net_income = enhanced.get('net_income', 0)
        operating_income = enhanced.get('operating_income', 0)
        total_assets = enhanced.get('total_assets', 0)
        total_liabilities = enhanced.get('total_liabilities', 0)
        shareholders_equity = enhanced.get('shareholders_equity', 0)
        total_debt = enhanced.get('total_debt', 0)
        current_assets = enhanced.get('current_assets', 0)
        current_liabilities = enhanced.get('current_liabilities', 0)
        operating_cash_flow = enhanced.get('operating_cash_flow', 0)
        capital_expenditures = enhanced.get('capital_expenditures', 0)
        depreciation = enhanced.get('depreciation_and_amortization', 0)
        market_cap = enhanced.get('market_cap', 0)
        cash = enhanced.get('cash_and_cash_equivalents', 0)
        
        # 计算缺失字段
        if 'ebitda' in missing_fields and not enhanced.get('ebitda'):
            enhanced['ebitda'] = _calculate_ebitda(operating_income, depreciation)
        
        if 'ebitda_margin' in missing_fields and not enhanced.get('ebitda_margin'):
            ebitda = enhanced.get('ebitda', 0)
            enhanced['ebitda_margin'] = _calculate_ebitda_margin(ebitda, revenue)
        
        if 'enterprise_value' in missing_fields and not enhanced.get('enterprise_value'):
            enhanced['enterprise_value'] = _calculate_enterprise_value(market_cap, total_debt, cash)
        
        if 'ev_to_ebitda' in missing_fields and not enhanced.get('ev_to_ebitda'):
            ev = enhanced.get('enterprise_value', 0)
            ebitda = enhanced.get('ebitda', 0)
            enhanced['ev_to_ebitda'] = _calculate_ev_to_ebitda(ev, ebitda)
        
        if 'ev_to_sales' in missing_fields and not enhanced.get('ev_to_sales'):
            ev = enhanced.get('enterprise_value', 0)
            enhanced['ev_to_sales'] = _calculate_ev_to_sales(ev, revenue)
        
        if 'working_capital' in missing_fields and not enhanced.get('working_capital'):
            enhanced['working_capital'] = _calculate_working_capital(current_assets, current_liabilities)
        
        if 'free_cash_flow' in missing_fields and not enhanced.get('free_cash_flow'):
            enhanced['free_cash_flow'] = _calculate_free_cash_flow(operating_cash_flow, capital_expenditures)
        
        if 'debt_to_total_capital' in missing_fields and not enhanced.get('debt_to_total_capital'):
            enhanced['debt_to_total_capital'] = _calculate_debt_to_total_capital(total_debt, shareholders_equity)
        
        enhanced_data.append(enhanced)
    
    return enhanced_data


def _make_api_request(url: str, headers: dict, method: str = "GET", json_data: dict = None, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.
    
    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        requests.Response: The response object
    
    Raises:
        Exception: If the request fails with a non-429 error
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 429:
            if attempt < max_retries:
                # 大幅减少等待时间，避免GUI长时间无响应
                # 原来的延迟：60s, 90s, 120s, 150s...
                # 新的延迟：2s, 4s, 6s, 8s...
                delay = 2 + (2 * attempt)
                print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying...")
                
                # 分段等待，每0.5秒检查一次，避免长时间阻塞
                for i in range(int(delay * 2)):
                    time.sleep(0.5)
                    # 检查中断标志
                    if _interrupt_flag.is_set():
                        print("API请求被用户中断")
                        raise Exception("API请求被用户中断")
                    
                continue
            else:
                # 最后一次尝试仍然429，直接失败
                print(f"Rate limited (429) after {max_retries + 1} attempts. Giving up.")
                raise Exception(f"API速率限制，已重试{max_retries + 1}次，请稍后再试")
        
        # Return the response (whether success, other errors, or final 429)
        return response


@rate_limit()
def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """获取价格数据 - 支持多数据源优先级策略，增强数据完整性检查"""
    
    # 检查参数有效性
    if not start_date or not end_date:
        print(f"Error: start_date or end_date is None for {ticker}")
        return []
    
    # 验证日期格式
    try:
        from datetime import datetime
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error: Invalid date format for {ticker}: {e}")
        return []
    
    # Check cache first
    cache_key = f"{ticker}_{start_date}_{end_date}"
    if cached_data := _cache.get_prices(cache_key):
        cached_prices = [Price(**price) for price in cached_data]
        # 验证缓存数据完整性
        if _validate_price_data_completeness(cached_prices, start_date, end_date):
            print(f"Using cached price data for {ticker}: {len(cached_prices)} records")
            return cached_prices
        else:
            print(f"Cached data incomplete for {ticker}, fetching fresh data")

    try:
        market = _detect_market(ticker)
        
        # 使用AKShare获取价格数据
        prices = _get_prices_akshare(ticker, start_date, end_date)
        
        # 验证数据完整性
        if prices and _validate_price_data_quality(prices, ticker):
            _cache.set_prices(cache_key, [price.model_dump() for price in prices])
            print(f"Successfully fetched {len(prices)} price records for {ticker}")
        elif prices:
            print(f"Warning: Price data quality issues detected for {ticker}, but using available data")
        else:
            print(f"Warning: No price data available for {ticker}")
        
        return prices

    except Exception as e:
        print(f"Error fetching prices for {ticker}: {e}")
        return []


def _get_prices_akshare(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """使用AKShare获取价格数据"""
    if not HAS_AKSHARE:
        return []
    
    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            # A股历史数据
            symbol = _convert_cn_symbol(ticker)
            
            # 使用AKShare辅助工具获取历史数据
            if akshare_helper:
                df = akshare_helper.get_stock_history(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"
                )
            else:
                df = ak.stock_zh_a_hist(
                    symbol=symbol, 
                    period="daily", 
                    start_date=start_date.replace('-', ''), 
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"  # 前复权
                )
            
            if df is not None and not df.empty:
                return _convert_akshare_to_prices(df, ticker)
                
        elif market == 'HK':
            # 港股历史数据
            symbol = _convert_hk_symbol(ticker)
            try:
                df = ak.stock_hk_daily(
                    symbol=symbol,
                    adjust="qfq"  # 前复权
                )
                
                # 根据日期范围过滤数据
                if df is not None and not df.empty and start_date and end_date:
                    df['date'] = pd.to_datetime(df['date'] if 'date' in df.columns else df.index)
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                
                if df is not None and not df.empty:
                    return _convert_akshare_to_prices(df, ticker, is_hk=True)
                    
            except Exception as e:
                print(f"获取港股数据失败 {ticker}: {e}")
                
        elif market == 'US':
            # 美股历史数据
            symbol = _convert_us_symbol(ticker)
            try:
                df = ak.stock_us_daily(
                    symbol=symbol,
                    adjust="qfq"  # 前复权
                )
                
                # 根据日期范围过滤数据
                if df is not None and not df.empty and start_date and end_date:
                    df['date'] = pd.to_datetime(df['date'])
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                
                if df is not None and not df.empty:
                    return _convert_akshare_to_prices(df, ticker, is_us=True)
                    
            except Exception as e:
                print(f"获取美股数据失败 {ticker}: {e}")
                
    except Exception as e:
        print(f"AKShare获取数据失败 {ticker}: {e}")
    
    return []








def _validate_price_data_completeness(prices: list[Price], start_date: str, end_date: str) -> bool:
    """验证价格数据的完整性"""
    if not prices:
        return False
    
    try:
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 计算期望的交易日数量（粗略估计，不考虑节假日）
        total_days = (end_dt - start_dt).days + 1
        expected_trading_days = total_days * 5 / 7  # 假设一周5个交易日
        
        # 如果实际数据量少于期望的70%，认为数据不完整
        completeness_ratio = len(prices) / expected_trading_days
        return completeness_ratio >= 0.7
        
    except Exception:
        return True  # 如果验证失败，假设数据完整


def _validate_price_data_quality(prices: list[Price], ticker: str) -> bool:
    """验证价格数据的质量"""
    if not prices:
        return False
    
    try:
        # 检查是否有有效的收盘价
        valid_prices = [p for p in prices if p.close and p.close > 0]
        if len(valid_prices) < len(prices) * 0.8:  # 至少80%的数据有有效收盘价
            print(f"Warning: {ticker} has too many invalid price records")
            return False
        
        # 检查价格是否有异常波动（单日涨跌超过50%可能是数据错误）
        for i in range(1, len(valid_prices)):
            prev_close = valid_prices[i-1].close
            curr_close = valid_prices[i].close
            if prev_close > 0:
                change_ratio = abs(curr_close - prev_close) / prev_close
                if change_ratio > 0.5:  # 50%的异常波动
                    print(f"Warning: {ticker} has suspicious price movement on {valid_prices[i].time}")
        
        return True
        
    except Exception as e:
        print(f"Error validating price data quality for {ticker}: {e}")
        return True  # 如果验证失败，假设数据质量可接受


def _convert_akshare_to_prices(df: pd.DataFrame, ticker: str, is_hk: bool = False, is_us: bool = False) -> list[Price]:
    """将AKShare数据转换为Price对象"""
    try:
        # 标准化列名
        if is_hk or is_us:
            # 港股和美股都使用英文列名，需要将date列重命名为time
            column_mapping = {
                'date': 'time',  # 港股和美股数据使用date列名
                'Date': 'time',
                '日期': 'time', 
                '开盘': 'open', 'Open': 'open', '开盘价': 'open',
                '收盘': 'close', 'Close': 'close', '收盘价': 'close',
                '最高': 'high', 'High': 'high', '最高价': 'high',
                '最低': 'low', 'Low': 'low', '最低价': 'low',
                '成交量': 'volume', 'Volume': 'volume', '成交股数': 'volume'
            }
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
        else:
            # A股标准列名
            df = df.rename(columns={
                '日期': 'time',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
        
        # 确保必要的列存在
        required_columns = ['time', 'open', 'close', 'high', 'low', 'volume']
        if not all(col in df.columns for col in required_columns):
            print(f"缺少必要的数据列: {ticker}")
            return []
        
        # 转换数据类型
        df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 数据清洗：移除无效行
        df = df.dropna(subset=['close'])  # 移除收盘价为空的行
        df = df[df['close'] > 0]  # 移除收盘价为0或负数的行
        
        # 按日期排序
        df = df.sort_values('time')
        
        # 转换为Price对象
        prices = []
        for _, row in df.iterrows():
            try:
                # 验证数据合理性
                close_price = float(row['close'])
                open_price = float(row['open']) if not pd.isna(row['open']) else close_price
                high_price = float(row['high']) if not pd.isna(row['high']) else close_price
                low_price = float(row['low']) if not pd.isna(row['low']) else close_price
                volume = int(row['volume']) if not pd.isna(row['volume']) and row['volume'] >= 0 else 0
                
                # 基本合理性检查
                if high_price < close_price or low_price > close_price:
                    # 如果高低价不合理，使用收盘价作为默认值
                    high_price = max(high_price, close_price, open_price)
                    low_price = min(low_price, close_price, open_price)
                
                prices.append(Price(
                    open=open_price,
                    close=close_price,
                    high=high_price,
                    low=low_price,
                    volume=volume,
                    time=str(row['time'])
                ))
            except (ValueError, TypeError) as e:
                print(f"Warning: Skipping invalid price record for {ticker}: {e}")
                continue
        
        market_type = "港股" if is_hk else "美股" if is_us else "A股"
        print(f"✓ AKShare{market_type}数据转换成功: {ticker} - {len(prices)} 条 (原始: {len(df)} 条)")
        return prices
        
    except Exception as e:
        print(f"AKShare数据转换失败 {ticker}: {e}")
        return []





@rate_limit()
def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 100,
) -> list[FinancialMetrics]:
    """获取财务指标数据 - 支持多数据源优先级策略"""
    
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{period}_{end_date}_{limit}"
    
    # Check cache first - simple exact match
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    try:
        market = _detect_market(ticker)
        
        # 使用AKShare获取财务指标数据
        metrics = _get_financial_metrics_akshare(ticker, end_date, period, limit)
        
        # 缓存结果
        if metrics:
            _cache.set_financial_metrics(cache_key, [m.model_dump() for m in metrics])
            print(f"Successfully fetched financial metrics for {ticker}")
        
        return metrics

    except Exception as e:
        print(f"Error fetching financial metrics for {ticker}: {e}")
        return []


def _get_financial_metrics_akshare(ticker: str, end_date: str, period: str, limit: int) -> list[FinancialMetrics]:
    """使用AKShare获取财务指标数据"""
    if not HAS_AKSHARE:
        return []
    
    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            symbol = _convert_cn_symbol(ticker)
            
            # 使用AKShare辅助工具获取财务摘要数据
            try:
                if akshare_helper:
                    df_financial = akshare_helper.get_financial_abstract(symbol)
                else:
                    df_financial = ak.stock_financial_abstract(symbol=symbol)
                
                if df_financial is not None and not df_financial.empty:
                    return _convert_akshare_financial_to_metrics(df_financial, ticker, period, limit)
                    
            except Exception as e:
                print(f"AKShare财务数据获取失败 {ticker}: {e}")
                
        # 对于港股，可能也支持一些财务数据
        elif market == 'HK':
            # 港股财务数据获取逻辑
            symbol = _convert_hk_symbol(ticker)
            try:
                # 这里可以添加港股财务数据获取逻辑
                print(f"港股财务数据获取尚未完全实现: {symbol}")
            except Exception as e:
                print(f"港股财务数据获取失败: {e}")
                
    except Exception as e:
        print(f"AKShare财务指标获取失败 {ticker}: {e}")
    
    return []


def _convert_akshare_financial_to_metrics(df_financial: pd.DataFrame, ticker: str, period: str, limit: int) -> list[FinancialMetrics]:
    """将AKShare财务数据转换为FinancialMetrics对象"""
    try:
        # stock_financial_abstract返回的是指标行，需要转置处理
        # 数据结构: 选项 | 指标 | 20250331 | 20241231 | ...
        
        # 获取可用的日期列（除了前两列）
        date_columns = [col for col in df_financial.columns if col not in ['选项', '指标']]
        if not date_columns:
            print("无可用的财务数据日期")
            return []
        
        # 创建多个metrics记录（根据limit参数）
        financial_metrics = []
        for i in range(min(limit, len(date_columns))):
            date_col = date_columns[i]
            
            # 解析该日期的数据
            period_data = {}
            for _, row in df_financial.iterrows():
                indicator_name = row['指标']
                value = row.get(date_col, 0)
                period_data[indicator_name] = _safe_float(value)
            
            # 创建符合模型要求的FinancialMetrics对象
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=date_col,
                period="TTM" if period == "ttm" else "ANNUAL",
                currency="CNY",
                market_cap=None,  # 将通过Yahoo补充
                enterprise_value=None,
                price_to_earnings_ratio=period_data.get('市盈率'),
                price_to_book_ratio=period_data.get('市净率'),
                price_to_sales_ratio=period_data.get('市销率'),
                enterprise_value_to_ebitda_ratio=None,
                enterprise_value_to_revenue_ratio=None,
                free_cash_flow_yield=None,
                peg_ratio=None,
                gross_margin=period_data.get('销售毛利率', 0) / 100 if period_data.get('销售毛利率') else None,
                operating_margin=None,
                net_margin=period_data.get('销售净利率', 0) / 100 if period_data.get('销售净利率') else None,
                return_on_equity=period_data.get('净资产收益率', 0) / 100 if period_data.get('净资产收益率') else None,
                return_on_assets=period_data.get('总资产收益率', 0) / 100 if period_data.get('总资产收益率') else None,
                return_on_invested_capital=None,
                asset_turnover=period_data.get('总资产周转率'),
                inventory_turnover=period_data.get('存货周转率'),
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=period_data.get('流动比率'),
                quick_ratio=period_data.get('速动比率'),
                cash_ratio=None,
                operating_cash_flow_ratio=None,
                debt_to_equity=period_data.get('产权比率'),
                debt_to_assets=period_data.get('资产负债率', 0) / 100 if period_data.get('资产负债率') else None,
                interest_coverage=None,
                revenue_growth=period_data.get('营业收入增长率', 0) / 100 if period_data.get('营业收入增长率') else None,
                earnings_growth=period_data.get('净利润增长率', 0) / 100 if period_data.get('净利润增长率') else None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=period_data.get('股利支付率', 0) / 100 if period_data.get('股利支付率') else None,
                earnings_per_share=period_data.get('基本每股收益'),
                book_value_per_share=period_data.get('每股净资产'),
                free_cash_flow_per_share=period_data.get('每股现金流量净额')
            )
            financial_metrics.append(metrics)
        
        print(f"✓ AKShare财务指标转换成功: {ticker} - {len(financial_metrics)} 条")
        return financial_metrics
        
    except Exception as e:
        print(f"AKShare财务数据转换失败 {ticker}: {e}")
        return []


def _merge_financial_metrics(target: FinancialMetrics, source: FinancialMetrics):
    """合并财务指标数据，target为主，source为补充"""
    try:
        # 只合并target中为None的字段
        for field in target.__fields__:
            if getattr(target, field) is None:
                source_value = getattr(source, field, None)
                if source_value is not None:
                    setattr(target, field, source_value)
    except Exception as e:
        print(f"财务指标合并失败: {e}")


@rate_limit()
def search_line_items(
    ticker: str,
    items: list[str],
    end_date: str,
    period: str = "annual",
    limit: int = 100,
) -> list[LineItem]:
    """搜索财务报表行项目数据"""
    _check_akshare_available()
    
    cache_key = f"{ticker}_{'_'.join(items)}_{end_date}_{period}_{limit}"
    
    if cached_data := _cache.get_line_items(cache_key):
        return [LineItem(**item) for item in cached_data]

    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            symbol = _convert_cn_symbol(ticker)
            
            # 获取财务报表数据
            line_items = []
            
            # 定义数据源映射
            data_sources = {
                # 资产负债表项目
                "total_assets": ("balance_sheet", "资产总计"),
                "total_liabilities": ("balance_sheet", "负债合计"),
                "shareholders_equity": ("balance_sheet", "股东权益合计"),
                "current_assets": ("balance_sheet", "流动资产合计"),
                "current_liabilities": ("balance_sheet", "流动负债合计"),
                "cash_and_cash_equivalents": ("balance_sheet", "货币资金"),
                
                # 利润表项目
                "revenue": ("income_statement", "营业收入"),
                "net_income": ("income_statement", "净利润"),
                "operating_income": ("income_statement", "营业利润"),
                "gross_profit": ("income_statement", "毛利润"),
                "research_and_development": ("income_statement", "研发费用"),
                
                # 现金流量表项目
                "operating_cash_flow": ("cash_flow", "经营活动产生的现金流量净额"),
                "capital_expenditure": ("cash_flow", "购建固定资产、无形资产和其他长期资产支付的现金"),
                "free_cash_flow": ("cash_flow", "自由现金流"),
            }
            
            # 尝试从财务摘要获取基础数据
            try:
                if akshare_helper:
                    df_abstract = akshare_helper.get_financial_abstract(symbol)
                else:
                    df_abstract = ak.stock_financial_abstract(symbol=symbol)
                
                if df_abstract is not None and not df_abstract.empty:
                    # 获取最新日期列
                    date_columns = [col for col in df_abstract.columns if col not in ['选项', '指标']]
                    if date_columns:
                        latest_date = date_columns[0]
                        
                        # 构建指标映射
                        indicator_map = {}
                        for _, row in df_abstract.iterrows():
                            indicator_name = row['指标']
                            value = row.get(latest_date, 0)
                            indicator_map[indicator_name] = _safe_float(value)
                        
                        # 处理请求的项目
                        for item in items:
                            value = 0
                            
                            # 直接映射
                            if item == "revenue" and "营业收入" in indicator_map:
                                value = indicator_map["营业收入"]
                            elif item == "net_income" and "归母净利润" in indicator_map:
                                value = indicator_map["归母净利润"]
                            elif item == "total_assets" and "总资产" in indicator_map:
                                value = indicator_map["总资产"]
                            elif item == "shareholders_equity" and "股东权益" in indicator_map:
                                value = indicator_map["股东权益"]
                            
                            # 创建LineItem对象
                            if value != 0:
                                line_item = LineItem(
                                    ticker=ticker,
                                    report_period=latest_date,
                                    period="ANNUAL",
                                    currency="CNY",
                                    name=item,
                                    value=value
                                )
                                # 设置动态属性以便直接访问
                                setattr(line_item, item, value)
                                line_items.append(line_item)
            
            except Exception as e:
                print(f"获取财务摘要数据失败: {e}")
            
            # 尝试计算缺失的财务指标
            try:
                from src.utils.financial_calculations import financial_calculator
                
                # 收集已有的财务数据
                financial_data = {}
                for line_item in line_items:
                    financial_data[line_item.name] = line_item.value
                
                # 如果没有基础数据，直接返回空列表
                if not financial_data:
                    print(f"警告: 无法获取 {ticker} 的财务数据")
                    return []
                
                # 不在这里获取市值和股价数据，避免重复调用
                # 这些数据将由DataPrefetcher统一获取和管理
                # 如果需要这些数据进行计算，应该从预获取的数据中获取
                
                # 使用财务计算器增强数据
                enhanced_data = financial_calculator.enhance_financial_metrics(financial_data)
                
                # 为请求的项目创建LineItem对象
                for item in items:
                    value = None
                    
                    # 首先检查原始数据
                    if item in financial_data:
                        value = financial_data[item]
                    # 然后检查计算出的数据
                    elif item in enhanced_data:
                        value = enhanced_data[item]
                    
                    # 特殊处理一些计算指标的别名
                    elif item == "enterprise_value" and "ev" in enhanced_data:
                        value = enhanced_data["ev"]
                    elif item == "ev_to_ebitda" and "ev_ebitda_ratio" in enhanced_data:
                        value = enhanced_data["ev_ebitda_ratio"]
                    elif item == "ev_to_sales" and "ev_sales_ratio" in enhanced_data:
                        value = enhanced_data["ev_sales_ratio"]
                    elif item == "price_to_book" and "pb_ratio" in enhanced_data:
                        value = enhanced_data["pb_ratio"]
                    elif item == "price_to_sales" and "ps_ratio" in enhanced_data:
                        value = enhanced_data["ps_ratio"]
                    elif item == "ebitda_margin" and "ebitda_margin" in enhanced_data:
                        value = enhanced_data["ebitda_margin"]
                    elif item == "working_capital" and "working_capital" in enhanced_data:
                        value = enhanced_data["working_capital"]
                    elif item == "return_on_invested_capital" and "roic" in enhanced_data:
                        value = enhanced_data["roic"]
                    elif item == "debt_to_total_capital" and "debt_to_total_capital" in enhanced_data:
                        value = enhanced_data["debt_to_total_capital"]
                    elif item == "book_value_per_share" and "book_value_per_share" in enhanced_data:
                        value = enhanced_data["book_value_per_share"]
                    elif item == "shares_outstanding" and "shares_outstanding" in enhanced_data:
                        value = enhanced_data["shares_outstanding"]
                    elif item == "effective_tax_rate" and "tax_rate" in enhanced_data:
                        value = enhanced_data["tax_rate"]
                    
                    # 创建LineItem对象
                    if value is not None and value != 0:
                        # 检查是否已存在该项目
                        existing_item = next((li for li in line_items if li.name == item), None)
                        if not existing_item:
                            line_item = LineItem(
                                ticker=ticker,
                                report_period=end_date,
                                period="ANNUAL",
                                currency="CNY",
                                name=item,
                                value=value
                            )
                            # 设置动态属性以便直接访问
                            setattr(line_item, item, value)
                            line_items.append(line_item)
                            
            except Exception as e:
                print(f"计算财务指标时出错: {e}")
                # 如果计算失败，返回已获取的真实数据（如果有的话）
                if not line_items:
                    print(f"警告: 无法计算 {ticker} 的财务指标")
                    return []
            
            # 缓存结果 - 只有有效数据才缓存
            if line_items and len(line_items) > 0:
                _cache.set_line_items(cache_key, [item.model_dump() for item in line_items])
                print(f"✓ {ticker} 财务报表项目数据缓存成功: {len(line_items)} 条")
                return line_items
            else:
                print(f"✗ {ticker} 财务报表项目数据为空，不进行缓存")
                return []
        
        elif market == 'HK':
            print(f"HK market line items for {ticker} not yet implemented")
            
        elif market == 'US':
            print(f"US market line items for {ticker} not yet implemented")

    except Exception as e:
        print(f"Error fetching line items for {ticker}: {e}")
        return []

    return []


@rate_limit()
def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """获取内部人交易数据（AKShare中国市场数据有限）"""
    # AKShare对于内部人交易数据支持有限，返回空列表
    print(f"Warning: Insider trade data not available for {ticker} in AKShare")
    return []


@rate_limit()
def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """获取公司新闻数据"""
    _check_akshare_available()
    
    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            symbol = _convert_cn_symbol(ticker)
            
            # 获取个股新闻
            if akshare_helper:
                df_news = akshare_helper.get_stock_news(symbol)
            else:
                df_news = ak.stock_news_em(symbol=symbol)
            
            if df_news is not None and not df_news.empty:
                news_list = []
                for _, row in df_news.head(limit).iterrows():
                    news = CompanyNews(
                        ticker=ticker,
                        title=str(row.get('新闻标题', '')),
                        author=str(row.get('来源', 'Unknown')),
                        source=str(row.get('来源', 'AKShare')),
                        date=str(row.get('发布时间', '')),
                        url=str(row.get('新闻链接', '')),
                        sentiment="neutral"  # AKShare不提供情感分析，默认中性
                    )
                    news_list.append(news)
                
                # 缓存结果 - 只有有效数据才缓存
                if news_list and len(news_list) > 0:
                    print(f"✓ {ticker} 公司新闻数据获取成功: {len(news_list)} 条")
                    return news_list
                else:
                    print(f"✗ {ticker} 公司新闻数据为空")
                    return []
        
        elif market in ['HK', 'US']:
            print(f"{market} market news for {ticker} not yet implemented")

    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

    return []


# 全局变量存储成功的策略信息
_successful_strategies = {
    "market_cap": ["策略2: 个股信息获取", "策略3: 股价×股本计算"],
    "last_test_results": {
        "strategy_2": 1812693425400,
        "strategy_3": 1812693425400,
        "consistency": "数据一致性良好 (差异: 0.00%)"
    }
}

@rate_limit()
def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """获取市值数据 - 优化版，仅使用测试成功的策略"""
    _check_akshare_available()
    
    cache_key = f"{ticker}_market_cap_{end_date}"
    
    if cached_data := _cache.get_line_items(cache_key):
        return cached_data[0] if cached_data else None

    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            symbol = _convert_cn_symbol(ticker)
            
            # 策略2: 从个股信息获取市值 (测试成功)
            try:
                if akshare_helper:
                    df_info = akshare_helper.get_stock_info(symbol)
                else:
                    df_info = ak.stock_individual_info_em(symbol=symbol)
                if df_info is not None and not df_info.empty:
                    info_dict = dict(zip(df_info['item'], df_info['value']))
                    if '总市值' in info_dict:
                        market_cap_str = str(info_dict['总市值'])
                        # 解析市值字符串（可能包含单位）
                        import re
                        numbers = re.findall(r'[\d.]+', market_cap_str)
                        if numbers:
                            market_cap_value = float(numbers[0])
                            if '万' in market_cap_str:
                                market_cap_value *= 10000
                            elif '亿' in market_cap_str:
                                market_cap_value *= 100000000
                            
                            if market_cap_value > 0:
                                _cache.set_line_items(cache_key, [market_cap_value])
                                print(f"✓ {ticker} 市值数据缓存成功 (策略2): {market_cap_value:,.0f}")
                                return market_cap_value
            except Exception as e:
                print(f"策略2失败: {e}")
            
            # 策略3: 通过股价和股本计算市值 (测试成功)
            try:
                # 获取当前股价
                if akshare_helper:
                    df_current = akshare_helper.get_stock_history(symbol=symbol, period="daily", adjust="qfq")
                else:
                    df_current = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
                    
                if df_current is not None and not df_current.empty:
                    current_price = df_current.iloc[-1]['收盘']
                    
                    # 获取股本信息
                    if akshare_helper:
                        df_capital = akshare_helper.get_stock_info(symbol)
                    else:
                        df_capital = ak.stock_individual_info_em(symbol=symbol)
                    if df_capital is not None and not df_capital.empty:
                        info_dict = dict(zip(df_capital['item'], df_capital['value']))
                        shares_key = None
                        for key in ['总股本', '流通股', '总股本(万股)']:
                            if key in info_dict:
                                shares_key = key
                                break
                        
                        if shares_key:
                            shares_str = str(info_dict[shares_key])
                            import re
                            numbers = re.findall(r'[\d.]+', shares_str)
                            if numbers:
                                shares = float(numbers[0])
                                if '万' in shares_str or '万股' in shares_key:
                                    shares *= 10000
                                elif '亿' in shares_str:
                                    shares *= 100000000
                                
                                market_cap = current_price * shares
                                if market_cap > 0:
                                    _cache.set_line_items(cache_key, [market_cap])
                                    print(f"✓ {ticker} 市值数据缓存成功 (策略3): {market_cap:,.0f}")
                                    return market_cap
            except Exception as e:
                print(f"策略3失败: {e}")
            
            print(f"所有市值获取策略都失败: {ticker}")
            return None
            
        elif market == 'HK':
            print(f"HK market cap for {ticker} not yet implemented")
            return None
            
        elif market == 'US':
            print(f"US market cap for {ticker} not yet implemented")
            return None

    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return None

    return None


@rate_limit()
def get_company_facts(ticker: str) -> dict:
    """获取公司基本信息"""
    _check_akshare_available()
    
    try:
        market = _detect_market(ticker)
        
        if market == 'CN':
            symbol = _convert_cn_symbol(ticker)
            
            # 获取公司基本信息
            if akshare_helper:
                df_info = akshare_helper.get_stock_info(symbol)
            else:
                df_info = ak.stock_individual_info_em(symbol=symbol)
            
            if df_info is not None and not df_info.empty:
                facts = {}
                for _, row in df_info.iterrows():
                    key = str(row.get('item', ''))
                    value = str(row.get('value', ''))
                    facts[key] = value
                
                return facts

    except Exception as e:
        print(f"Error fetching company facts for {ticker}: {e}")
        return {}

    return {}


def prices_to_df(prices: list) -> pd.DataFrame:
    """Convert prices to a DataFrame.
    
    Args:
        prices: List of price data (can be Price objects or dictionaries)
        
    Returns:
        pd.DataFrame: DataFrame with price data
    """
    if not prices:
        return pd.DataFrame()
    
    # Handle both Pydantic models and dictionaries
    price_data = []
    for p in prices:
        if hasattr(p, 'model_dump'):  # Pydantic model
            price_data.append(p.model_dump())
        elif isinstance(p, dict):  # Dictionary
            price_data.append(p)
        else:
            # Try to convert to dict
            try:
                price_data.append(dict(p))
            except:
                print(f"Warning: Unable to convert price data: {type(p)}")
                continue
    
    if not price_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(price_data)
    
    # Handle different date column names
    date_col = None
    for col in ['time', 'date', 'Date', 'timestamp']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        df["Date"] = pd.to_datetime(df[date_col])
        df.set_index("Date", inplace=True)
    
    # Convert numeric columns
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df.sort_index(inplace=True)
    return df


# ==================== 增强数据获取函数 ====================

@rate_limit()
def get_volume_analysis_data(ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    获取成交量分析数据
    """
    if not HAS_AKSHARE:
        return {"error": "AKShare未安装"}
    
    try:
        symbol = _convert_cn_symbol(ticker)
        
        # 获取基础价格数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                               start_date=start_date.replace('-', ''), 
                               end_date=end_date.replace('-', ''), 
                               adjust="qfq")
        
        if df.empty:
            return {"error": "无法获取数据"}
        
        # 计算成交量指标
        volume_data = {
            "avg_volume_5d": df['成交量'].rolling(5).mean().iloc[-1] if len(df) >= 5 else None,
            "avg_volume_20d": df['成交量'].rolling(20).mean().iloc[-1] if len(df) >= 20 else None,
            "volume_ratio": df['成交量'].iloc[-1] / df['成交量'].rolling(20).mean().iloc[-1] if len(df) >= 20 else None,
            "price_volume_trend": _calculate_price_volume_trend(df),
            "volume_spike_days": _count_volume_spikes(df),
            "money_flow_ratio": _calculate_money_flow_ratio(df)
        }
        
        return volume_data
        
    except Exception as e:
        return {"error": f"获取成交量数据失败: {str(e)}"}


@rate_limit()
def get_market_sentiment_data(ticker: str) -> Dict[str, Any]:
    """
    获取市场情绪数据
    """
    if not HAS_AKSHARE:
        return {"error": "AKShare未安装"}
    
    try:
        symbol = _convert_cn_symbol(ticker)
        sentiment_data = {}
        
        # 获取资金流向数据
        try:
            money_flow = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
            if not money_flow.empty:
                latest_flow = money_flow.iloc[-1]
                sentiment_data["money_flow"] = {
                    "main_net_inflow": float(latest_flow.get('主力净流入-净额', 0)),
                    "main_net_inflow_rate": float(latest_flow.get('主力净流入-净占比', 0)),
                    "super_large_net_inflow": float(latest_flow.get('超大单净流入-净额', 0)),
                    "large_net_inflow": float(latest_flow.get('大单净流入-净额', 0))
                }
        except Exception:
            sentiment_data["money_flow"] = {"error": "资金流向数据获取失败"}
        
        # 获取龙虎榜数据
        try:
            lhb_data = ak.stock_lhb_detail_em(symbol=symbol, start_date="20240101", end_date="20241231")
            sentiment_data["lhb_activity"] = len(lhb_data) if not lhb_data.empty else 0
        except Exception:
            sentiment_data["lhb_activity"] = 0
        
        return sentiment_data
        
    except Exception as e:
        return {"error": f"获取市场情绪数据失败: {str(e)}"}


@rate_limit()
def get_technical_indicators_data(ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    获取技术指标数据 - 增强版本
    使用专业的技术指标计算类，提供更准确和全面的技术分析数据
    """
    if not HAS_AKSHARE:
        return {"error": "AKShare未安装", "details": "请安装akshare库以获取技术指标数据"}
    
    try:
        # 首先尝试从缓存获取价格数据
        prices = get_prices(ticker, start_date, end_date)
        if not prices:
            return {"error": "无法获取价格数据", "details": f"股票代码 {ticker} 在指定时间范围内无价格数据"}
        
        # 转换为DataFrame格式
        df = prices_to_df(prices)
        
        if df.empty or len(df) < 20:
            return {
                "error": "数据不足，无法计算技术指标", 
                "details": f"需要至少20个交易日的数据，当前只有{len(df)}个交易日",
                "suggestion": "请扩大时间范围或检查股票代码是否正确"
            }
        
        # 使用专业的技术指标计算类
        try:
            from src.utils.technical_indicators import TechnicalIndicators
            indicators = TechnicalIndicators.calculate_all_indicators(df)
            
            # 添加当前价格和基础信息
            indicators.update({
                'current_price': df['close'].iloc[-1],
                'price_change': df['close'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0,
                'price_change_pct': ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0,
                'volume_latest': df['volume'].iloc[-1] if 'volume' in df.columns else 0,
                'data_points': len(df),
                'date_range': f"{df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}",
                'calculation_methods': {
                    'moving_averages': 'Simple Moving Average (SMA)',
                    'macd': 'MACD(12,26,9) - 指数移动平均收敛发散',
                    'rsi': 'RSI(14) - 相对强弱指数',
                    'bollinger_bands': 'Bollinger Bands(20,2) - 布林带',
                    'kdj': 'KDJ(9,3,3) - 随机指标',
                    'volume_indicators': 'OBV, A/D Line - 成交量指标',
                    'volatility': 'ATR, Bollinger Width - 波动率指标'
                }
            })
            
            return indicators
            
        except ImportError as ie:
            # 如果无法导入技术指标类，使用简化版本
            print(f"警告: 无法导入TechnicalIndicators类，使用简化计算: {ie}")
            return _calculate_basic_indicators(df, ticker)
            
    except Exception as e:
        error_msg = str(e)
        return {
            "error": f"获取技术指标数据失败: {error_msg}", 
            "details": f"处理股票 {ticker} 时发生错误",
            "troubleshooting": [
                "检查股票代码格式是否正确",
                "确认时间范围是否合理",
                "验证网络连接是否正常",
                "检查AKShare库是否正常工作"
            ]
        }


def _calculate_basic_indicators(df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
    """
    计算基础技术指标（备用方案）
    """
    try:
        indicators = {}
        
        # 移动平均线
        indicators["ma5"] = _safe_float(df['close'].rolling(5).mean().iloc[-1])
        indicators["ma10"] = _safe_float(df['close'].rolling(10).mean().iloc[-1])
        indicators["ma20"] = _safe_float(df['close'].rolling(20).mean().iloc[-1])
        indicators["ma60"] = _safe_float(df['close'].rolling(60).mean().iloc[-1]) if len(df) >= 60 else None
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        indicators["macd"] = {
            "macd_line": _safe_float(macd_line.iloc[-1]),
            "signal_line": _safe_float(signal_line.iloc[-1]),
            "histogram": _safe_float(histogram.iloc[-1])
        }
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators["rsi"] = _safe_float(rsi.iloc[-1])
        
        # 布林带
        bb_period = 20
        bb_std = 2
        bb_middle = df['close'].rolling(bb_period).mean()
        bb_std_dev = df['close'].rolling(bb_period).std()
        bb_upper = bb_middle + (bb_std_dev * bb_std)
        bb_lower = bb_middle - (bb_std_dev * bb_std)
        
        indicators["bollinger_bands"] = {
            "upper": _safe_float(bb_upper.iloc[-1]),
            "middle": _safe_float(bb_middle.iloc[-1]),
            "lower": _safe_float(bb_lower.iloc[-1]),
            "position": _safe_float((df['close'].iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]))
        }
        
        # KDJ
        low_min = df['low'].rolling(9).min()
        high_max = df['high'].rolling(9).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d
        
        indicators["kdj"] = {
            "k": _safe_float(k.iloc[-1]),
            "d": _safe_float(d.iloc[-1]),
            "j": _safe_float(j.iloc[-1])
        }
        
        # 添加基础信息
        indicators.update({
            'current_price': _safe_float(df['close'].iloc[-1]),
            'data_points': len(df),
            'calculation_mode': 'basic',
            'note': '使用基础计算方法'
        })
        
        return indicators
        
    except Exception as e:
        return {"error": f"基础指标计算失败: {str(e)}"}


@rate_limit()
def get_industry_analysis_data(ticker: str) -> Dict[str, Any]:
    """
    获取行业分析数据
    """
    if not HAS_AKSHARE:
        return {"error": "AKShare未安装"}
    
    try:
        symbol = _convert_cn_symbol(ticker)
        industry_data = {}
        
        # 获取股票基本信息
        try:
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            if not stock_info.empty:
                industry_data["industry"] = stock_info[stock_info['item'] == '行业']['value'].iloc[0] if len(stock_info[stock_info['item'] == '行业']) > 0 else "未知"
                industry_data["concept"] = stock_info[stock_info['item'] == '概念']['value'].iloc[0] if len(stock_info[stock_info['item'] == '概念']) > 0 else "未知"
        except Exception:
            industry_data["industry"] = "未知"
            industry_data["concept"] = "未知"
        
        # 获取行业资金流向
        try:
            industry_flow = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            if not industry_flow.empty and industry_data.get("industry") != "未知":
                industry_row = industry_flow[industry_flow['名称'].str.contains(industry_data["industry"][:2])]
                if not industry_row.empty:
                    industry_data["industry_flow"] = {
                        "net_inflow": float(industry_row['净流入'].iloc[0]),
                        "net_inflow_rate": float(industry_row['净流入率'].iloc[0]),
                        "rank": int(industry_row.index[0] + 1)
                    }
        except Exception:
            industry_data["industry_flow"] = {"error": "行业资金流向数据获取失败"}
        
        return industry_data
        
    except Exception as e:
        return {"error": f"获取行业分析数据失败: {str(e)}"}


# ==================== 辅助计算函数 ====================

def _calculate_price_volume_trend(df: pd.DataFrame) -> float:
    """
    计算价量趋势相关性
    """
    try:
        if len(df) < 10:
            return 0.0
        
        price_change = df['收盘'].pct_change().dropna()
        volume_change = df['成交量'].pct_change().dropna()
        
        if len(price_change) != len(volume_change):
            min_len = min(len(price_change), len(volume_change))
            price_change = price_change.iloc[-min_len:]
            volume_change = volume_change.iloc[-min_len:]
        
        correlation = price_change.corr(volume_change)
        return correlation if not pd.isna(correlation) else 0.0
    except Exception:
        return 0.0


def _count_volume_spikes(df: pd.DataFrame, threshold: float = 2.0) -> int:
    """
    统计成交量异常放大的天数
    """
    try:
        if len(df) < 20:
            return 0
        
        avg_volume = df['成交量'].rolling(20).mean()
        volume_ratio = df['成交量'] / avg_volume
        spikes = (volume_ratio > threshold).sum()
        return int(spikes)
    except Exception:
        return 0


def _calculate_money_flow_ratio(df: pd.DataFrame) -> float:
    """
    计算资金流入流出比例
    """
    try:
        if len(df) < 5:
            return 0.0
        
        # 简化的资金流向计算：上涨日成交额 / 总成交额
        up_days = df['涨跌幅'] > 0
        total_turnover = df['成交额'].sum()
        up_turnover = df[up_days]['成交额'].sum()
        
        return float(up_turnover / total_turnover) if total_turnover > 0 else 0.0
    except Exception:
        return 0.0


@rate_limit()
def get_technical_indicators(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    period: int = 200
) -> dict:
    """获取技术指标数据
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        start_date: 开始日期（可选）
        period: 数据周期（默认200天，足够计算大部分技术指标）
        
    Returns:
        包含所有技术指标的字典
    """
    try:
        # 如果没有指定开始日期，自动计算
        if start_date is None:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=period * 2)  # 预留足够的数据
            start_date = start_dt.strftime("%Y-%m-%d")
        
        # 获取价格数据
        df = get_price_data(ticker, start_date, end_date)
        
        if len(df) < 20:
            print(f"数据不足，无法计算技术指标: {ticker}")
            return {}
        
        # 计算技术指标
        from src.utils.technical_indicators import technical_indicators
        tech_indicators = technical_indicators.calculate_all_indicators(df)
        
        # 添加一些额外的市场信息
        tech_indicators.update({
            'current_price': df['close'].iloc[-1],
            'price_change': df['close'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0,
            'price_change_pct': ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0,
            'volume_latest': df['volume'].iloc[-1] if 'volume' in df.columns else 0,
            'high_52w': df['high'].rolling(252).max().iloc[-1] if len(df) >= 252 else df['high'].max(),
            'low_52w': df['low'].rolling(252).min().iloc[-1] if len(df) >= 252 else df['low'].min(),
        })
        
        return tech_indicators
        
    except Exception as e:
        print(f"获取技术指标失败: {ticker}, {e}")
        return {}


@rate_limit()
def get_enhanced_financial_data(
    ticker: str,
    end_date: str,
    include_technical: bool = True,
    include_calculated: bool = True
) -> dict:
    """获取增强的财务数据，包括计算出的指标和技术指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        include_technical: 是否包含技术指标
        include_calculated: 是否包含计算出的财务指标
        
    Returns:
        包含所有财务和技术数据的字典
    """
    enhanced_data = {}
    
    try:
        # 获取基础财务指标
        financial_metrics = get_financial_metrics(ticker, end_date, limit=100)
        if financial_metrics:
            enhanced_data['financial_metrics'] = financial_metrics[0].model_dump()
        
        # 获取财务报表行项目
        if include_calculated:
            line_items = search_line_items(
                ticker,
                [
                    "revenue", "net_income", "operating_income", "gross_profit",
                    "total_assets", "total_liabilities", "shareholders_equity",
                    "current_assets", "current_liabilities", "total_debt",
                    "operating_cash_flow", "capital_expenditure",
                    "cash_and_cash_equivalents", "enterprise_value",
                    "ev_to_ebitda", "ev_to_sales", "price_to_book",
                    "price_to_sales", "ebitda", "ebitda_margin",
                    "working_capital", "free_cash_flow", "return_on_invested_capital",
                    "debt_to_total_capital", "book_value_per_share",
                    "shares_outstanding", "effective_tax_rate"
                ],
                end_date,
                period="annual",
                limit=100
            )
            enhanced_data['line_items'] = {item.name: item.value for item in line_items}
        
        # 获取技术指标
        if include_technical:
            tech_indicators = get_technical_indicators(ticker, end_date)
            enhanced_data['technical_indicators'] = tech_indicators
        
        # 获取市值
        market_cap = get_market_cap(ticker, end_date)
        if market_cap:
            enhanced_data['market_cap'] = market_cap
        
        # 获取公司基本信息
        company_facts = get_company_facts(ticker)
        if company_facts:
            enhanced_data['company_facts'] = company_facts
            
    except Exception as e:
        print(f"获取增强财务数据失败: {ticker}, {e}")
    
    return enhanced_data


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame格式，集成技术指标计算"""
    prices = get_prices(ticker, start_date, end_date)
    df = prices_to_df(prices)
    
    # 如果数据足够，计算技术指标
    if len(df) >= 20:  # 至少需要20个数据点来计算大部分技术指标
        try:
            from src.utils.technical_indicators import technical_indicators
            
            # 计算所有技术指标
            tech_indicators = technical_indicators.calculate_all_indicators(df)
            
            # 将技术指标添加到DataFrame的属性中
            if hasattr(df, 'attrs'):
                df.attrs['technical_indicators'] = tech_indicators
            
            # 同时将最新的技术指标值添加为列（便于访问）
            for key, value in tech_indicators.items():
                if isinstance(value, (int, float)) and not pd.isna(value):
                    df.loc[df.index[-1], f'tech_{key}'] = value
                        
        except Exception as e:
            print(f"计算技术指标时出错: {e}")
    
    return df
