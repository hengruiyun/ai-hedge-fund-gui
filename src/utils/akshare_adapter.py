import akshare as ak
from typing import Dict, List, Any, Optional
import pandas as pd
import logging
import time

class AKShareAdapter:
    """AKShare数据适配器，用于补充财务数据"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _safe_get_data(self, func, *args, **kwargs):
        """安全获取数据，不进行重试"""
        try:
            result = func(*args, **kwargs)
            # 检查result是否为None，然后检查是否有empty属性且不为空
            if result is not None:
                if hasattr(result, 'empty'):
                    if not result.empty:
                        return result
                    else:
                        return None
                else:
                    # 如果没有empty属性，可能是其他类型的数据，直接返回
                    return result
            else:
                return None
        except (TypeError, AttributeError, KeyError, IndexError, ValueError) as e:
            # 静默处理所有常见错误，不输出警告
            return None
        except Exception as e:
            # 静默处理其他所有错误
            return None
    
    def get_financial_statements(self, stock_code: str) -> Dict[str, Any]:
        """获取财务报表数据"""
        try:
            statements = {}
            
            # 注释掉经常出错的财务报表API调用
            # 这些API经常返回NoneType错误，暂时禁用
            
            # # 获取资产负债表
            # try:
            #     balance_sheet = self._safe_get_data(ak.stock_balance_sheet_by_report_em, symbol=stock_code)
            #     if balance_sheet is not None and not balance_sheet.empty:
            #         statements['balance_sheet'] = balance_sheet.to_dict('records')
            # except Exception as e:
            #     self.logger.warning(f"获取资产负债表失败: {e}")
            # 
            # # 获取利润表
            # try:
            #     income_statement = self._safe_get_data(ak.stock_profit_sheet_by_report_em, symbol=stock_code)
            #     if income_statement is not None and not income_statement.empty:
            #         statements['income_statement'] = income_statement.to_dict('records')
            # except Exception as e:
            #     self.logger.warning(f"获取利润表失败: {e}")
            # 
            # # 获取现金流量表
            # try:
            #     cash_flow = self._safe_get_data(ak.stock_cash_flow_sheet_by_report_em, symbol=stock_code)
            #     if cash_flow is not None and not cash_flow.empty:
            #         statements['cash_flow'] = cash_flow.to_dict('records')
            # except Exception as e:
            #     self.logger.warning(f"获取现金流量表失败: {e}")
            
            self.logger.info(f"财务报表API已禁用以避免NoneType错误")
            
            return statements
        except Exception as e:
            self.logger.error(f"获取财务报表失败: {e}")
            return {}
    
    def get_financial_indicators(self, stock_code: str) -> Dict[str, Any]:
        """获取财务指标数据"""
        try:
            indicators = {}
            
            # 获取主要财务指标
            try:
                main_indicators = self._safe_get_data(ak.stock_financial_abstract_ths, symbol=stock_code)
                if main_indicators is not None and not main_indicators.empty:
                    indicators['main_indicators'] = main_indicators.to_dict('records')
            except Exception as e:
                self.logger.warning(f"获取主要财务指标失败: {e}")
            
            # 获取估值指标
            try:
                valuation = self._safe_get_data(ak.stock_a_indicator_lg, symbol=stock_code)
                if valuation is not None and not valuation.empty:
                    indicators['valuation'] = valuation.to_dict('records')
            except Exception as e:
                self.logger.warning(f"获取估值指标失败: {e}")
            
            return indicators
        except Exception as e:
            self.logger.error(f"获取财务指标失败: {e}")
            return {}
    
    def get_macro_economic_data(self, limit: int = 100) -> Dict[str, Any]:
        """获取宏观经济数据 - 全球事件
        
        Args:
            limit: 数据条数限制，默认100条
            
        Returns:
            包含宏观经济数据的字典
        """
        try:
            self.logger.info("开始获取宏观经济数据...")
            
            # 获取宏观-全球事件数据
            macro_data = self._safe_get_data(ak.news_economic_baidu)
            
            if macro_data is None:
                self.logger.warning("宏观经济数据API返回None")
                # 返回空数据而不是空字典，避免后续处理出错
                return {
                    'macro_events': [],
                    'total_records': 0,
                    'data_source': 'akshare_news_economic_baidu',
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'status': 'failed',
                    'error': 'API返回None'
                }
            
            if hasattr(macro_data, 'empty') and macro_data.empty:
                self.logger.warning("宏观经济数据为空DataFrame")
                return {
                    'macro_events': [],
                    'total_records': 0,
                    'data_source': 'akshare_news_economic_baidu',
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'status': 'empty',
                    'error': '数据为空'
                }
            
            self.logger.info(f"原始数据获取成功，共{len(macro_data)}条记录")
            
            # 限制数据条数
            if len(macro_data) > limit:
                macro_data = macro_data.head(limit)
                self.logger.info(f"数据已限制为{limit}条")
            
            # 过滤最近一年的数据
            if '时间' in macro_data.columns:
                try:
                    original_count = len(macro_data)
                    # 转换时间列为datetime，处理None值
                    macro_data = macro_data.dropna(subset=['时间'])
                    if not macro_data.empty:
                        macro_data['时间'] = pd.to_datetime(macro_data['时间'], errors='coerce')
                        # 删除时间转换失败的行
                        macro_data = macro_data.dropna(subset=['时间'])
                        if not macro_data.empty:
                            # 获取最近一年的数据
                            one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
                            macro_data = macro_data[macro_data['时间'] >= one_year_ago]
                            self.logger.info(f"时间过滤完成：{original_count} -> {len(macro_data)}条")
                except Exception as e:
                    self.logger.warning(f"时间过滤失败，使用原始数据: {e}")
            
            # 确保数据不为空
            if macro_data.empty:
                self.logger.warning("过滤后数据为空")
                return {
                    'macro_events': [],
                    'total_records': 0,
                    'data_source': 'akshare_news_economic_baidu',
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'status': 'filtered_empty',
                    'error': '过滤后数据为空'
                }
            
            # 转换为字典格式
            try:
                macro_events = macro_data.to_dict('records')
                result = {
                    'macro_events': macro_events,
                    'total_records': len(macro_data),
                    'data_source': 'akshare_news_economic_baidu',
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'status': 'success'
                }
                
                self.logger.info(f"成功获取{len(macro_data)}条宏观经济数据")
                return result
            except Exception as e:
                self.logger.error(f"数据转换失败: {e}")
                return {
                    'macro_events': [],
                    'total_records': 0,
                    'data_source': 'akshare_news_economic_baidu',
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'status': 'conversion_failed',
                    'error': f'数据转换失败: {e}'
                }
            
        except Exception as e:
            self.logger.error(f"获取宏观经济数据失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            # 返回结构化的错误信息而不是空字典
            return {
                'macro_events': [],
                'total_records': 0,
                'data_source': 'akshare_news_economic_baidu',
                'last_updated': pd.Timestamp.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_stock_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """获取股票基本信息 - 多数据源"""
        try:
            basic_info = {}
            
            # 数据源1: 东方财富个股信息
            try:
                em_info = self._safe_get_data(ak.stock_individual_info_em, symbol=stock_code)
                if em_info is not None and not em_info.empty:
                    basic_info['em_basic_info'] = em_info.to_dict('records')[0] if len(em_info) > 0 else {}
            except Exception as e:
                self.logger.warning(f"获取{stock_code}东方财富基本信息失败: {e}")
            
            # 数据源2: 新浪财经实时行情 (已禁用，经常连接失败)
            # try:
            #     sina_realtime = self._safe_get_data(ak.stock_zh_a_spot_em)
            #     if sina_realtime is not None and not sina_realtime.empty:
            #         # 查找对应股票代码的数据
            #         stock_data = sina_realtime[sina_realtime['代码'] == stock_code]
            #         if not stock_data.empty:
            #             basic_info['sina_realtime'] = stock_data.iloc[0].to_dict()
            # except Exception as e:
            #     self.logger.warning(f"获取{stock_code}新浪实时行情失败: {e}")
            
            self.logger.info(f"新浪实时行情API已禁用，因为经常连接失败")
            
            # 数据源3: 股票历史行情 (用于计算技术指标)
            try:
                hist_data = self._safe_get_data(ak.stock_zh_a_hist, symbol=stock_code, period="daily", start_date="20230101", adjust="qfq")
                if hist_data is not None and not hist_data.empty:
                    # 计算基本技术指标
                    basic_info['price_data'] = self._calculate_basic_technical_indicators(hist_data)
            except Exception as e:
                self.logger.warning(f"获取{stock_code}历史行情失败: {e}")
            
            return basic_info
        except Exception as e:
            self.logger.error(f"获取{stock_code}基本信息失败: {e}")
            return {}
    
    def _calculate_basic_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, Any]:
        """计算基本技术指标"""
        try:
            if hist_data is None or hist_data.empty or len(hist_data) < 20:
                return {}
            
            # 获取最新价格数据
            latest_price = hist_data['收盘'].iloc[-1] if '收盘' in hist_data.columns else None
            
            # 计算移动平均线
            ma_5 = hist_data['收盘'].rolling(window=5).mean().iloc[-1] if len(hist_data) >= 5 else None
            ma_20 = hist_data['收盘'].rolling(window=20).mean().iloc[-1] if len(hist_data) >= 20 else None
            ma_60 = hist_data['收盘'].rolling(window=60).mean().iloc[-1] if len(hist_data) >= 60 else None
            
            # 计算价格变化
            price_change_1d = ((latest_price - hist_data['收盘'].iloc[-2]) / hist_data['收盘'].iloc[-2]) if len(hist_data) >= 2 and latest_price else None
            price_change_5d = ((latest_price - hist_data['收盘'].iloc[-6]) / hist_data['收盘'].iloc[-6]) if len(hist_data) >= 6 and latest_price else None
            price_change_20d = ((latest_price - hist_data['收盘'].iloc[-21]) / hist_data['收盘'].iloc[-21]) if len(hist_data) >= 21 and latest_price else None
            
            # 计算波动率 (20日)
            returns = hist_data['收盘'].pct_change().dropna()
            volatility_20d = returns.rolling(window=20).std().iloc[-1] * (252 ** 0.5) if len(returns) >= 20 else None
            
            # 计算成交量指标
            avg_volume_20d = hist_data['成交量'].rolling(window=20).mean().iloc[-1] if '成交量' in hist_data.columns and len(hist_data) >= 20 else None
            latest_volume = hist_data['成交量'].iloc[-1] if '成交量' in hist_data.columns else None
            volume_ratio = (latest_volume / avg_volume_20d) if latest_volume and avg_volume_20d and avg_volume_20d > 0 else None
            
            return {
                'current_price': self._safe_float(latest_price),
                'ma_5': self._safe_float(ma_5),
                'ma_20': self._safe_float(ma_20),
                'ma_60': self._safe_float(ma_60),
                'price_change_1d': self._safe_float(price_change_1d),
                'price_change_5d': self._safe_float(price_change_5d),
                'price_change_20d': self._safe_float(price_change_20d),
                'volatility_20d': self._safe_float(volatility_20d),
                'volume_ratio': self._safe_float(volume_ratio),
                'avg_volume_20d': self._safe_float(avg_volume_20d)
            }
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {e}")
            return {}
    
    def get_comprehensive_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """获取综合财务数据 - 第四优先级增强版 (优化版)
        
        优先使用可用的API，从财务摘要中提取更多信息
        包括：财务摘要、估值数据、基础指标、历史行情等可用数据源
        """
        comprehensive_data = {}
        
        try:
            self.logger.info(f"开始获取{stock_code}的综合财务数据")
            
            # 1. 优先获取财务摘要数据 (可用API)
            financial_abstract = self.get_enhanced_financial_abstract(stock_code)
            if financial_abstract and 'periods' in financial_abstract:
                comprehensive_data.update(financial_abstract)
                self.logger.info(f"成功获取财务摘要数据，期数: {financial_abstract.get('total_periods', 0)}")
                
                # 从最新期财务摘要中提取更多有用信息
                if financial_abstract['periods']:
                    latest_period = financial_abstract['periods'][0]
                    extracted_data = self._extract_from_enhanced_financial_abstract(latest_period)
                    if extracted_data:
                        comprehensive_data.update(extracted_data)
                        self.logger.info(f"从财务摘要提取额外数据，字段数: {len(extracted_data)}")
            
            # 2. 获取估值数据 (可用API)
            try:
                valuation_data = self._get_enhanced_valuation_data(stock_code)
                if valuation_data:
                    comprehensive_data.update(valuation_data)
                    self.logger.info(f"成功获取估值数据，字段数: {len(valuation_data)}")
            except Exception as e:
                self.logger.warning(f"估值数据获取失败: {e}")
            
            # 3. 获取基础财务指标 (部分可用)
            try:
                basic_info = self.get_stock_basic_info(stock_code)
                if basic_info:
                    comprehensive_data.update(basic_info)
                    self.logger.info(f"成功获取基础财务指标，字段数: {len(basic_info)}")
            except Exception as e:
                self.logger.warning(f"基础财务指标获取失败: {e}")
            
            # 4. 获取历史行情数据 (可用API)
            try:
                historical_data = self._get_enhanced_historical_data(stock_code)
                if historical_data:
                    comprehensive_data.update(historical_data)
                    self.logger.info(f"成功获取历史行情数据，字段数: {len(historical_data)}")
            except Exception as e:
                self.logger.warning(f"历史行情数据获取失败: {e}")
            
            # 5. 尝试获取财务报表数据 (可能失败，但不影响主流程)
            try:
                balance_sheet = self._get_enhanced_balance_sheet_data(stock_code)
                if balance_sheet:
                    comprehensive_data.update(balance_sheet)
                    self.logger.info(f"成功获取资产负债表数据，字段数: {len(balance_sheet)}")
            except Exception as e:
                self.logger.warning(f"资产负债表API失败，跳过: {e}")
            
            try:
                income_statement = self._get_enhanced_income_statement_data(stock_code)
                if income_statement:
                    comprehensive_data.update(income_statement)
                    self.logger.info(f"成功获取利润表数据，字段数: {len(income_statement)}")
            except Exception as e:
                self.logger.warning(f"利润表API失败，跳过: {e}")
            
            try:
                cash_flow = self._get_enhanced_cash_flow_data(stock_code)
                if cash_flow:
                    comprehensive_data.update(cash_flow)
                    self.logger.info(f"成功获取现金流量表数据，字段数: {len(cash_flow)}")
            except Exception as e:
                self.logger.warning(f"现金流量表API失败，跳过: {e}")
            
            # 6. 获取分红数据 (尝试获取)
            try:
                dividend_data = self._get_enhanced_dividend_data(stock_code)
                if dividend_data:
                    comprehensive_data.update(dividend_data)
                    self.logger.info(f"成功获取分红数据，字段数: {len(dividend_data)}")
            except Exception as e:
                self.logger.warning(f"分红数据API失败，跳过: {e}")
            
            # 7. 获取技术指标数据
            try:
                technical_data = self._get_enhanced_technical_data(stock_code)
                if technical_data:
                    comprehensive_data.update(technical_data)
                    self.logger.info(f"成功获取技术指标数据，字段数: {len(technical_data)}")
            except Exception as e:
                self.logger.warning(f"技术指标数据获取失败: {e}")
            
            # 8. 数据质量验证和修复
            comprehensive_data = self.validate_and_repair_data(comprehensive_data)
            
            self.logger.info(f"综合财务数据获取完成，总字段数: {len(comprehensive_data)}")
            
        except Exception as e:
            self.logger.error(f"获取综合财务数据时发生错误: {e}")
        
        return comprehensive_data

    def _extract_from_financial_abstract(self, financial_abstract: Dict[str, Any]) -> Dict[str, Any]:
        """从财务摘要中提取更多有用信息"""
        extracted_data = {}
        
        try:
            # 从财务摘要中提取关键财务指标
            if '总资产' in financial_abstract:
                extracted_data['total_assets'] = financial_abstract['总资产']
            if '净资产' in financial_abstract:
                extracted_data['net_assets'] = financial_abstract['净资产']
            if '营业收入' in financial_abstract:
                extracted_data['operating_revenue'] = financial_abstract['营业收入']
            if '净利润' in financial_abstract:
                extracted_data['net_profit'] = financial_abstract['净利润']
            if '每股收益' in financial_abstract:
                extracted_data['eps'] = financial_abstract['每股收益']
            if '每股净资产' in financial_abstract:
                extracted_data['book_value_per_share'] = financial_abstract['每股净资产']
            if '净资产收益率' in financial_abstract:
                extracted_data['roe'] = financial_abstract['净资产收益率']
            if '总资产收益率' in financial_abstract:
                extracted_data['roa'] = financial_abstract['总资产收益率']
            if '毛利率' in financial_abstract:
                extracted_data['gross_margin'] = financial_abstract['毛利率']
            if '净利率' in financial_abstract:
                extracted_data['net_margin'] = financial_abstract['净利率']
            
            # 计算一些衍生指标
            if 'total_assets' in extracted_data and 'net_assets' in extracted_data:
                try:
                    total_debt = float(extracted_data['total_assets']) - float(extracted_data['net_assets'])
                    extracted_data['total_debt'] = total_debt
                    if float(extracted_data['net_assets']) > 0:
                        extracted_data['debt_to_equity'] = total_debt / float(extracted_data['net_assets'])
                except (ValueError, ZeroDivisionError):
                    pass
            
            self.logger.info(f"从财务摘要提取数据成功，提取字段数: {len(extracted_data)}")
            
        except Exception as e:
            self.logger.warning(f"从财务摘要提取数据失败: {e}")
        
        return extracted_data
    
    def _extract_from_enhanced_financial_abstract(self, latest_period: Dict[str, Any]) -> Dict[str, Any]:
        """从增强财务摘要的最新期数据中提取更多有用信息"""
        extracted_data = {}
        
        try:
            # 从标准化的财务摘要中提取关键财务指标
            if 'total_assets' in latest_period:
                extracted_data['total_assets'] = latest_period['total_assets']
            if 'shareholders_equity' in latest_period:
                extracted_data['net_assets'] = latest_period['shareholders_equity']
            if 'revenue' in latest_period:
                extracted_data['operating_revenue'] = latest_period['revenue']
            if 'net_income' in latest_period:
                extracted_data['net_profit'] = latest_period['net_income']
            if 'earnings_per_share' in latest_period:
                extracted_data['eps'] = latest_period['earnings_per_share']
            if 'book_value_per_share' in latest_period:
                extracted_data['book_value_per_share'] = latest_period['book_value_per_share']
            if 'return_on_equity' in latest_period:
                extracted_data['roe'] = latest_period['return_on_equity']
            if 'return_on_assets' in latest_period:
                extracted_data['roa'] = latest_period['return_on_assets']
            if 'current_assets' in latest_period:
                extracted_data['current_assets'] = latest_period['current_assets']
            if 'current_liabilities' in latest_period:
                extracted_data['current_liabilities'] = latest_period['current_liabilities']
            if 'total_liabilities' in latest_period:
                extracted_data['total_liabilities'] = latest_period['total_liabilities']
            if 'operating_cash_flow' in latest_period:
                extracted_data['operating_cash_flow'] = latest_period['operating_cash_flow']
            if 'cash_and_cash_equivalents' in latest_period:
                extracted_data['cash_and_equivalents'] = latest_period['cash_and_cash_equivalents']
            
            # 计算一些衍生指标
            if 'total_assets' in extracted_data and 'shareholders_equity' in latest_period:
                try:
                    total_debt = float(extracted_data['total_assets']) - float(latest_period['shareholders_equity'])
                    extracted_data['total_debt'] = total_debt
                    if float(latest_period['shareholders_equity']) > 0:
                        extracted_data['debt_to_equity'] = total_debt / float(latest_period['shareholders_equity'])
                except (ValueError, ZeroDivisionError):
                    pass
            
            # 计算流动比率
            if 'current_assets' in latest_period and 'current_liabilities' in latest_period:
                try:
                    if float(latest_period['current_liabilities']) > 0:
                        extracted_data['current_ratio'] = float(latest_period['current_assets']) / float(latest_period['current_liabilities'])
                except (ValueError, ZeroDivisionError):
                    pass
            
            # 计算毛利率和净利率
            if 'gross_profit' in latest_period and 'revenue' in latest_period:
                try:
                    if float(latest_period['revenue']) > 0:
                        extracted_data['gross_margin'] = float(latest_period['gross_profit']) / float(latest_period['revenue'])
                except (ValueError, ZeroDivisionError):
                    pass
            
            if 'net_income' in latest_period and 'revenue' in latest_period:
                try:
                    if float(latest_period['revenue']) > 0:
                        extracted_data['net_margin'] = float(latest_period['net_income']) / float(latest_period['revenue'])
                except (ValueError, ZeroDivisionError):
                    pass
            
            self.logger.info(f"从增强财务摘要提取数据成功，提取字段数: {len(extracted_data)}")
            
        except Exception as e:
            self.logger.warning(f"从增强财务摘要提取数据失败: {e}")
        
        return extracted_data
    
    def _get_enhanced_historical_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的历史行情数据"""
        historical_data = {}
        
        try:
            # 获取历史行情数据
            hist_data = self._safe_get_data(ak.stock_zh_a_hist, symbol=stock_code, period='daily', adjust='qfq')
            if hist_data is not None and not hist_data.empty:
                # 计算技术指标
                latest_price = hist_data['close'].iloc[-1] if 'close' in hist_data.columns else None
                if latest_price:
                    historical_data['latest_price'] = latest_price
                
                # 计算价格变化
                if len(hist_data) >= 2:
                    price_change = hist_data['close'].iloc[-1] - hist_data['close'].iloc[-2]
                    price_change_pct = (price_change / hist_data['close'].iloc[-2]) * 100
                    historical_data['price_change'] = price_change
                    historical_data['price_change_pct'] = price_change_pct
                
                # 计算移动平均线
                if len(hist_data) >= 20:
                    ma20 = hist_data['close'].rolling(window=20).mean().iloc[-1]
                    historical_data['ma20'] = ma20
                    if latest_price:
                        historical_data['price_vs_ma20'] = ((latest_price - ma20) / ma20) * 100
                
                if len(hist_data) >= 50:
                    ma50 = hist_data['close'].rolling(window=50).mean().iloc[-1]
                    historical_data['ma50'] = ma50
                    if latest_price:
                        historical_data['price_vs_ma50'] = ((latest_price - ma50) / ma50) * 100
                
                # 计算波动率
                if len(hist_data) >= 30:
                    returns = hist_data['close'].pct_change().dropna()
                    volatility = returns.std() * (252 ** 0.5) * 100  # 年化波动率
                    historical_data['volatility'] = volatility
                
                # 计算最高最低价
                high_52w = hist_data['high'].max() if 'high' in hist_data.columns else None
                low_52w = hist_data['low'].min() if 'low' in hist_data.columns else None
                if high_52w:
                    historical_data['high_52w'] = high_52w
                    if latest_price:
                        historical_data['price_vs_high_52w'] = ((latest_price - high_52w) / high_52w) * 100
                if low_52w:
                    historical_data['low_52w'] = low_52w
                    if latest_price:
                        historical_data['price_vs_low_52w'] = ((latest_price - low_52w) / low_52w) * 100
                
                self.logger.info(f"历史行情数据处理成功，计算指标数: {len(historical_data)}")
            
        except Exception as e:
            self.logger.warning(f"获取历史行情数据失败: {e}")
        
        return historical_data

    def _get_balance_sheet_data(self, stock_code: str) -> Dict[str, Any]:
        """获取资产负债表数据"""
        balance_data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_balance_sheet_by_yearly_em', '年度资产负债表'),
                ('stock_balance_sheet_by_report_em', '报告期资产负债表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新年度数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                balance_data.update({
                                    'total_assets': self._safe_float(latest_data.get('总资产')),
                                    'current_assets': self._safe_float(latest_data.get('流动资产合计')),
                                    'total_liabilities': self._safe_float(latest_data.get('负债合计')),
                                    'current_liabilities': self._safe_float(latest_data.get('流动负债合计')),
                                    'shareholders_equity': self._safe_float(latest_data.get('股东权益合计')),
                                    'cash_and_cash_equivalents': self._safe_float(latest_data.get('货币资金')),
                                    'inventory': self._safe_float(latest_data.get('存货')),
                                    'accounts_receivable': self._safe_float(latest_data.get('应收账款')),
                                    'long_term_debt': self._safe_float(latest_data.get('长期借款')),
                                    'short_term_debt': self._safe_float(latest_data.get('短期借款'))
                                })
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取资产负债表数据时发生错误: {e}")
        
        return balance_data
    
    def _get_income_statement_data(self, stock_code: str) -> Dict[str, Any]:
        """获取利润表数据"""
        income_data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_profit_sheet_by_yearly_em', '年度利润表'),
                ('stock_profit_sheet_by_report_em', '报告期利润表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新年度数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                income_data.update({
                                    'total_revenue': self._safe_float(latest_data.get('营业总收入')),
                                    'operating_revenue': self._safe_float(latest_data.get('营业收入')),
                                    'gross_profit': self._safe_float(latest_data.get('营业利润')),
                                    'operating_profit': self._safe_float(latest_data.get('营业利润')),
                                    'net_profit': self._safe_float(latest_data.get('净利润')),
                                    'ebitda': self._safe_float(latest_data.get('息税折旧摊销前利润')),
                                    'operating_expenses': self._safe_float(latest_data.get('营业总成本')),
                                    'interest_expense': self._safe_float(latest_data.get('利息费用')),
                                    'tax_expense': self._safe_float(latest_data.get('所得税费用')),
                                    'eps': self._safe_float(latest_data.get('基本每股收益'))
                                })
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取利润表数据时发生错误: {e}")
        
        return income_data
    
    def _get_cash_flow_data(self, stock_code: str) -> Dict[str, Any]:
        """获取现金流量表数据"""
        cash_flow_data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_cash_flow_sheet_by_yearly_em', '年度现金流量表'),
                ('stock_cash_flow_sheet_by_report_em', '报告期现金流量表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新年度数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                cash_flow_data.update({
                                    'operating_cash_flow': self._safe_float(latest_data.get('经营活动产生的现金流量净额')),
                                    'investing_cash_flow': self._safe_float(latest_data.get('投资活动产生的现金流量净额')),
                                    'financing_cash_flow': self._safe_float(latest_data.get('筹资活动产生的现金流量净额')),
                                    'free_cash_flow': self._safe_float(latest_data.get('自由现金流量')),
                                    'capital_expenditure': self._safe_float(latest_data.get('购建固定资产、无形资产和其他长期资产支付的现金')),
                                    'cash_flow_from_operations': self._safe_float(latest_data.get('经营活动现金流入小计'))
                                })
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取现金流量表数据时发生错误: {e}")
        
        return cash_flow_data
    
    def _get_dividend_data(self, stock_code: str) -> Dict[str, Any]:
        """获取分红数据"""
        dividend_data = {}
        
        # 注释掉不存在的分红数据API
        # try:
        #     df = self._safe_get_data(ak.stock_zh_a_dividend, symbol=stock_code)
        #     if df is not None and not df.empty:
        #         # 获取最新分红数据
        #         latest_dividend = df.iloc[-1] if len(df) > 0 else None
        #         if latest_dividend is not None:
        #             dividend_data.update({
        #                 'dividend_per_share': self._safe_float(latest_dividend.get('每股股利')),
        #                 'dividend_yield': self._safe_float(latest_dividend.get('股息率')),
        #                 'payout_ratio': self._safe_float(latest_dividend.get('分红比例')),
        #                 'ex_dividend_date': latest_dividend.get('除权除息日')
        #             })
        # except Exception as e:
        #     self.logger.warning(f"获取分红数据失败: {e}")
        
        self.logger.info(f"分红数据API已禁用，因为stock_zh_a_dividend不存在")
        
        return dividend_data
    
    def _get_valuation_data(self, stock_code: str) -> Dict[str, Any]:
        """获取估值数据"""
        valuation_data = {}
        
        try:
            # 尝试获取估值指标
            df = self._safe_get_data(ak.stock_zh_valuation_baidu, symbol=stock_code)
            if df is not None and not df.empty:
                latest_valuation = df.iloc[-1] if len(df) > 0 else None
                if latest_valuation is not None:
                    valuation_data.update({
                        'pe_ratio': self._safe_float(latest_valuation.get('市盈率')),
                        'pb_ratio': self._safe_float(latest_valuation.get('市净率')),
                        'ps_ratio': self._safe_float(latest_valuation.get('市销率')),
                        'market_cap': self._safe_float(latest_valuation.get('总市值')),
                        'enterprise_value': self._safe_float(latest_valuation.get('企业价值'))
                    })
        except Exception as e:
            self.logger.warning(f"获取估值数据失败: {e}")
        
        return valuation_data
    
    def validate_and_repair_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据质量验证和修复 - 第四优先级增强版
        
        包括：
        1. 检查关键财务指标的合理性
        2. 数据一致性检查
        3. 缺失数据修复
        4. 异常值检测和处理
        """
        validated_data = {}
        repair_log = []
        
        self.logger.debug(f"开始数据验证和修复，输入数据: {data}")
        
        try:
            # 1. 基础数据清理
            for key, value in data.items():
                # 过滤掉None值、空字符串和NaN
                if value is not None and value != '' and str(value).lower() not in ['nan', 'none', 'null']:
                    # 数值类型验证
                    if isinstance(value, (int, float)):
                        # 检查是否为无穷大或NaN
                        import math
                        if not (pd.isna(value) or math.isinf(value)):
                            validated_data[key] = value
                        else:
                            repair_log.append(f"移除无效数值: {key} = {value}")
                    else:
                        validated_data[key] = value
                else:
                    repair_log.append(f"移除空值: {key} = {value}")
            
            # 2. 关键财务指标合理性检查
            validated_data = self._check_financial_ratios_reasonableness(validated_data, repair_log)
            
            # 3. 数据一致性检查
            validated_data = self._check_data_consistency(validated_data, repair_log)
            
            # 4. 缺失数据修复
            validated_data = self._repair_missing_data(validated_data, repair_log)
            
            # 5. 异常值检测和处理
            validated_data = self._detect_and_handle_outliers(validated_data, repair_log)
            
            # 6. 记录修复日志
            if repair_log:
                self.logger.info(f"数据修复完成，修复项目: {len(repair_log)}")
                for log_item in repair_log[:5]:  # 只记录前5个修复项目
                    self.logger.debug(log_item)
            
        except Exception as e:
            self.logger.error(f"数据验证和修复时发生错误: {e}")
        
        return validated_data
    
    def _check_financial_ratios_reasonableness(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """
        检查关键财务指标的合理性
        """
        repaired_data = data.copy()
        
        # 定义合理性检查规则
        validations = [
            ('debt_to_equity', 0, 10, '债务权益比异常'),
            ('debt_to_equity_ratio', 0, 10, '债务权益比异常'),
            ('current_ratio', 0, 20, '流动比率异常'),
            ('quick_ratio', 0, 15, '速动比率异常'),
            ('gross_margin', -1, 1, '毛利率异常'),
            ('net_margin', -1, 1, '净利率异常'),
            ('roe', -1, 1, 'ROE异常'),
            ('roa', -1, 1, 'ROA异常'),
            ('pe_ratio', 0, 1000, '市盈率异常'),
            ('pb_ratio', 0, 50, '市净率异常')
        ]
        
        for field, min_val, max_val, message in validations:
            value = repaired_data.get(field)
            self.logger.debug(f"检查字段 {field}: 值={value}, 类型={type(value)}, 范围=[{min_val}, {max_val}]")
            if value is not None and isinstance(value, (int, float)):
                # 检查是否为异常值
                if value < min_val or value > max_val:
                    self.logger.debug(f"发现异常值: {field}={value}, 超出范围[{min_val}, {max_val}]")
                    repair_log.append(f"{message}: {field}={value:.4f}")
                    del repaired_data[field]
                    self.logger.debug(f"已从数据中删除异常值: {field}")
                    repaired_data[f"{field}_flag"] = "异常值"
                    repaired_data[f"{field}_original"] = value
                    # 移除异常值 - 直接删除键而不是设置为None
                    del repaired_data[field]
                    self.logger.debug(f"已移除异常值: {field}")
                else:
                    self.logger.debug(f"字段 {field} 值正常: {value}")
        
        return repaired_data
    
    def _check_data_consistency(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """
        数据一致性检查
        """
        repaired_data = data.copy()
        
        # 检查资产负债表平衡
        total_assets = repaired_data.get('total_assets')
        total_liabilities = repaired_data.get('total_liabilities')
        shareholders_equity = repaired_data.get('shareholders_equity')
        
        if all(x is not None for x in [total_assets, total_liabilities, shareholders_equity]):
            balance_check = abs(total_assets - (total_liabilities + shareholders_equity))
            if total_assets > 0 and balance_check / total_assets > 0.05:  # 5%容差
                repair_log.append(f"资产负债表不平衡: 差异{balance_check:,.0f}")
                repaired_data['balance_sheet_inconsistency'] = balance_check
        
        # 检查利润表一致性
        revenue = repaired_data.get('total_revenue')
        gross_profit = repaired_data.get('gross_profit')
        net_income = repaired_data.get('net_income')
        
        if revenue is not None and gross_profit is not None:
            if gross_profit > revenue:
                repair_log.append("毛利润大于营业收入")
                repaired_data['income_statement_inconsistency'] = True
        
        if gross_profit is not None and net_income is not None:
            if net_income > gross_profit:
                repair_log.append("净利润大于毛利润")
                repaired_data['income_statement_inconsistency'] = True
        
        return repaired_data
    
    def _repair_missing_data(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """
        缺失数据修复
        """
        repaired_data = data.copy()
        
        # 修复市值
        if repaired_data.get('market_cap') is None:
            price = repaired_data.get('current_price')
            shares = repaired_data.get('shares_outstanding')
            if price is not None and shares is not None:
                repaired_data['market_cap'] = price * shares
                repair_log.append("修复市值数据")
        
        # 修复企业价值
        if repaired_data.get('enterprise_value') is None:
            market_cap = repaired_data.get('market_cap')
            total_debt = repaired_data.get('total_debt', 0)
            cash = repaired_data.get('cash_and_cash_equivalents', 0)
            if market_cap is not None:
                repaired_data['enterprise_value'] = market_cap + total_debt - cash
                repair_log.append("修复企业价值数据")
        
        # 修复每股指标
        shares = repaired_data.get('shares_outstanding')
        if shares is not None and shares > 0:
            # 每股收益
            if repaired_data.get('earnings_per_share') is None:
                net_income = repaired_data.get('net_income')
                if net_income is not None:
                    repaired_data['earnings_per_share'] = net_income / shares
                    repair_log.append("修复每股收益数据")
            
            # 每股净资产
            if repaired_data.get('book_value_per_share') is None:
                shareholders_equity = repaired_data.get('shareholders_equity')
                if shareholders_equity is not None:
                    repaired_data['book_value_per_share'] = shareholders_equity / shares
                    repair_log.append("修复每股净资产数据")
        
        return repaired_data
    
    def _detect_and_handle_outliers(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """
        异常值检测和处理
        """
        repaired_data = data.copy()
        
        # 检测极端数值
        for key, value in repaired_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # 检测异常大的数值
                if abs(value) > 1e15:
                    repair_log.append(f"检测到异常大数值: {key}={value}")
                    repaired_data[f"{key}_outlier"] = True
                    repaired_data[key] = None
                
                # 检测NaN和无穷大
                import math
                if math.isnan(value) or math.isinf(value):
                    repair_log.append(f"检测到无效数值: {key}={value}")
                    repaired_data[key] = None
        
        return repaired_data
    
    def _get_enhanced_balance_sheet_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的资产负债表数据
        """
        data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_balance_sheet_by_report_em', {}),
                ('stock_financial_abstract', {}),
                ('stock_individual_info_em', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        df = source_func(symbol=stock_code, **params)
                        if not df.empty:
                            latest_data = df.iloc[-1].to_dict()
                            
                            # 标准化字段名
                            field_mapping = {
                                '总资产': 'total_assets',
                                '总负债': 'total_liabilities', 
                                '股东权益合计': 'shareholders_equity',
                                '流动资产': 'current_assets',
                                '流动负债': 'current_liabilities',
                                '货币资金': 'cash_and_cash_equivalents',
                                '应收账款': 'accounts_receivable',
                                '存货': 'inventory',
                                '固定资产': 'fixed_assets',
                                '无形资产': 'intangible_assets',
                                '短期借款': 'short_term_debt',
                                '长期借款': 'long_term_debt'
                            }
                            
                            for chinese_name, english_name in field_mapping.items():
                                if chinese_name in latest_data and latest_data[chinese_name] is not None:
                                    data[english_name] = float(latest_data[chinese_name])
                            
                            break
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强资产负债表数据失败: {e}")
        
        return data
    
    def _get_enhanced_income_statement_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的利润表数据
        """
        data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_profit_sheet_by_report_em', {}),
                ('stock_financial_abstract', {}),
                ('stock_individual_info_em', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        df = source_func(symbol=stock_code, **params)
                        if not df.empty:
                            latest_data = df.iloc[-1].to_dict()
                            
                            # 标准化字段名
                            field_mapping = {
                                '营业总收入': 'total_revenue',
                                '营业收入': 'operating_revenue',
                                '营业成本': 'cost_of_revenue',
                                '毛利润': 'gross_profit',
                                '营业利润': 'operating_income',
                                '利润总额': 'total_profit',
                                '净利润': 'net_income',
                                '基本每股收益': 'earnings_per_share',
                                '销售费用': 'selling_expenses',
                                '管理费用': 'administrative_expenses',
                                '财务费用': 'financial_expenses',
                                '研发费用': 'rd_expenses'
                            }
                            
                            for chinese_name, english_name in field_mapping.items():
                                if chinese_name in latest_data and latest_data[chinese_name] is not None:
                                    data[english_name] = float(latest_data[chinese_name])
                            
                            break
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强利润表数据失败: {e}")
        
        return data
    
    def _get_enhanced_cash_flow_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的现金流量表数据
        """
        data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_cash_flow_sheet_by_report_em', {}),
                ('stock_financial_abstract', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        df = source_func(symbol=stock_code, **params)
                        if not df.empty:
                            latest_data = df.iloc[-1].to_dict()
                            
                            # 标准化字段名
                            field_mapping = {
                                '经营活动产生的现金流量净额': 'operating_cash_flow',
                                '投资活动产生的现金流量净额': 'investing_cash_flow',
                                '筹资活动产生的现金流量净额': 'financing_cash_flow',
                                '现金及现金等价物净增加额': 'net_change_in_cash',
                                '销售商品、提供劳务收到的现金': 'cash_from_operations',
                                '购建固定资产、无形资产和其他长期资产支付的现金': 'capital_expenditures',
                                '自由现金流': 'free_cash_flow'
                            }
                            
                            for chinese_name, english_name in field_mapping.items():
                                if chinese_name in latest_data and latest_data[chinese_name] is not None:
                                    data[english_name] = float(latest_data[chinese_name])
                            
                            # 计算自由现金流（如果没有直接数据）
                            if 'free_cash_flow' not in data:
                                ocf = data.get('operating_cash_flow')
                                capex = data.get('capital_expenditures')
                                if ocf is not None and capex is not None:
                                    data['free_cash_flow'] = ocf - abs(capex)
                            
                            break
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强现金流量表数据失败: {e}")
        
        return data
    
    def _get_enhanced_dividend_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的分红数据
        """
        data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_dividend_detail', {}),
                ('stock_history_dividend_detail', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        df = source_func(symbol=stock_code, **params)
                        if not df.empty:
                            # 获取最近的分红数据
                            latest_dividend = df.iloc[-1]
                            
                            # 提取分红信息
                            if '每股派息' in df.columns:
                                data['dividend_per_share'] = float(latest_dividend.get('每股派息', 0))
                            if '股息率' in df.columns:
                                data['dividend_yield'] = float(latest_dividend.get('股息率', 0))
                            if '分红年度' in df.columns:
                                data['dividend_year'] = latest_dividend.get('分红年度')
                            
                            # 计算分红增长率
                            if len(df) >= 2:
                                current_dividend = df.iloc[-1].get('每股派息', 0)
                                previous_dividend = df.iloc[-2].get('每股派息', 0)
                                if previous_dividend > 0:
                                    growth_rate = (current_dividend - previous_dividend) / previous_dividend
                                    data['dividend_growth_rate'] = growth_rate
                            
                            break
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强分红数据失败: {e}")
        
        return data
    
    def _get_enhanced_valuation_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的估值数据
        """
        data = {}
        
        try:
            # 尝试多个数据源
            sources = [
                ('stock_individual_info_em', {}),
                ('stock_zh_a_hist', {'period': 'daily', 'adjust': 'qfq'}),
                ('stock_financial_abstract', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        
                        if source_name == 'stock_zh_a_hist':
                            # 获取历史价格数据
                            df = source_func(symbol=stock_code, **params)
                            if not df.empty:
                                latest_price = df.iloc[-1]
                                data['current_price'] = float(latest_price.get('收盘', 0))
                                data['volume'] = float(latest_price.get('成交量', 0))
                                data['turnover'] = float(latest_price.get('成交额', 0))
                        else:
                            df = source_func(symbol=stock_code, **params)
                            if not df.empty:
                                latest_data = df.iloc[-1].to_dict()
                                
                                # 标准化字段名
                                field_mapping = {
                                    '市盈率': 'pe_ratio',
                                    '市净率': 'pb_ratio',
                                    '市销率': 'ps_ratio',
                                    '总市值': 'market_cap',
                                    '流通市值': 'circulating_market_cap',
                                    '总股本': 'total_shares',
                                    '流通股': 'circulating_shares',
                                    '最新价': 'current_price'
                                }
                                
                                for chinese_name, english_name in field_mapping.items():
                                    if chinese_name in latest_data and latest_data[chinese_name] is not None:
                                        data[english_name] = float(latest_data[chinese_name])
                        
                        if data:  # 如果获取到数据就跳出
                            break
                            
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强估值数据失败: {e}")
        
        return data
    
    def _get_industry_comparison_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取行业对比数据
        """
        data = {}
        
        try:
            # 尝试获取行业数据
            sources = [
                ('stock_industry_pe_ratio_cninfo', {}),
                ('stock_board_industry_name_em', {}),
                ('stock_sector_detail', {})
            ]
            
            for source_name, params in sources:
                try:
                    if hasattr(ak, source_name):
                        source_func = getattr(ak, source_name)
                        df = source_func(**params)
                        if not df.empty:
                            # 尝试找到对应股票的行业信息
                            if '股票代码' in df.columns:
                                stock_info = df[df['股票代码'] == stock_code]
                                if not stock_info.empty:
                                    industry_data = stock_info.iloc[0].to_dict()
                                    
                                    # 提取行业对比指标
                                    field_mapping = {
                                        '行业': 'industry_name',
                                        '行业市盈率': 'industry_pe_ratio',
                                        '行业市净率': 'industry_pb_ratio',
                                        '行业平均ROE': 'industry_avg_roe',
                                        '行业平均毛利率': 'industry_avg_gross_margin'
                                    }
                                    
                                    for chinese_name, english_name in field_mapping.items():
                                        if chinese_name in industry_data and industry_data[chinese_name] is not None:
                                            if english_name != 'industry_name':
                                                data[english_name] = float(industry_data[chinese_name])
                                            else:
                                                data[english_name] = industry_data[chinese_name]
                            break
                except Exception as e:
                    self.logger.warning(f"获取{source_name}数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取行业对比数据失败: {e}")
        
        return data
    
    def _get_enhanced_technical_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取增强的技术指标数据
        """
        data = {}
        
        try:
            # 获取历史价格数据用于计算技术指标
            if hasattr(ak, 'stock_zh_a_hist'):
                df = ak.stock_zh_a_hist(symbol=stock_code, period='daily', adjust='qfq')
                if not df.empty and len(df) >= 20:
                    # 计算移动平均线
                    df['MA5'] = df['收盘'].rolling(window=5).mean()
                    df['MA10'] = df['收盘'].rolling(window=10).mean()
                    df['MA20'] = df['收盘'].rolling(window=20).mean()
                    
                    # 计算RSI
                    delta = df['收盘'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    
                    # 计算MACD
                    exp1 = df['收盘'].ewm(span=12).mean()
                    exp2 = df['收盘'].ewm(span=26).mean()
                    df['MACD'] = exp1 - exp2
                    df['Signal'] = df['MACD'].ewm(span=9).mean()
                    
                    # 获取最新技术指标值
                    latest = df.iloc[-1]
                    data.update({
                        'ma5': float(latest.get('MA5', 0)),
                        'ma10': float(latest.get('MA10', 0)),
                        'ma20': float(latest.get('MA20', 0)),
                        'rsi': float(latest.get('RSI', 0)),
                        'macd': float(latest.get('MACD', 0)),
                        'macd_signal': float(latest.get('Signal', 0))
                    })
                    
                    # 计算波动率（20日）
                    if len(df) >= 20:
                        returns = df['收盘'].pct_change().dropna()
                        volatility = returns.rolling(window=20).std().iloc[-1] * (252 ** 0.5)  # 年化波动率
                        data['volatility_20d'] = float(volatility)
        
        except Exception as e:
            self.logger.error(f"获取增强技术指标数据失败: {e}")
        
        return data
    
    def _calculate_dividend_growth_rate(self, dividend_data: List[Dict]) -> float:
        """
        计算分红增长率
        """
        try:
            if len(dividend_data) < 2:
                return 0.0
            
            # 按年度排序
            sorted_data = sorted(dividend_data, key=lambda x: x.get('year', 0))
            
            # 计算复合增长率
            first_dividend = sorted_data[0].get('dividend_per_share', 0)
            last_dividend = sorted_data[-1].get('dividend_per_share', 0)
            years = len(sorted_data) - 1
            
            if first_dividend > 0 and years > 0:
                growth_rate = (last_dividend / first_dividend) ** (1/years) - 1
                return growth_rate
            
            return 0.0
        
        except Exception as e:
            self.logger.error(f"计算分红增长率失败: {e}")
            return 0.0
    
    def enhance_financial_data_with_akshare(self, stock_code: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用AKShare数据增强现有财务数据 - 增强版"""
        enhanced_data = existing_data.copy()
        
        # 获取AKShare财务数据
        statements = self.get_financial_statements(stock_code)
        indicators = self.get_financial_indicators(stock_code)
        basic_info = self.get_stock_basic_info(stock_code)
        
        # 数据融合逻辑
        if statements:
            enhanced_data.update(self._extract_key_metrics_from_statements(statements))
        
        if indicators:
            enhanced_data.update(self._extract_key_metrics_from_indicators(indicators))
            # 提取历史数据用于计算增长率
            historical_data = indicators.get('historical_financial_data')
            if historical_data is not None:
                enhanced_data.update(self._extract_growth_metrics(historical_data))
        
        if basic_info:
            enhanced_data.update(self._extract_market_metrics(basic_info))
        
        return enhanced_data
    
    def _extract_balance_sheet_from_abstract(self, df_abstract: pd.DataFrame) -> pd.DataFrame:
        """从财务摘要中提取资产负债表相关数据"""
        try:
            if df_abstract is None or df_abstract.empty:
                return None
            
            # 检查必要的列是否存在
            if '指标' not in df_abstract.columns:
                self.logger.warning("财务摘要数据中缺少'指标'列")
                return None
            
            # 创建资产负债表格式的数据
            balance_sheet_data = {}
            
            # 获取日期列
            date_columns = [col for col in df_abstract.columns if col not in ['选项', '指标']]
            if not date_columns:
                return None
            
            # 提取资产负债表相关指标
            for _, row in df_abstract.iterrows():
                try:
                    indicator = row.get('指标', None)
                    if indicator and indicator in ['总资产', '负债合计', '股东权益', '流动资产', '流动负债', '货币资金']:
                        if date_columns:
                            balance_sheet_data[indicator] = row.get(date_columns[0], None)
                        else:
                            balance_sheet_data[indicator] = None
                except Exception as row_error:
                    self.logger.warning(f"处理行数据时出错: {row_error}")
                    continue
            
            if balance_sheet_data:
                return pd.DataFrame([balance_sheet_data])
            return None
        except Exception as e:
            self.logger.error(f"从财务摘要提取资产负债表数据失败: {e}")
            return None
    
    def _extract_income_statement_from_abstract(self, df_abstract: pd.DataFrame) -> pd.DataFrame:
        """从财务摘要中提取利润表相关数据"""
        try:
            if df_abstract is None or df_abstract.empty:
                return None
            
            # 检查必要的列是否存在
            if '指标' not in df_abstract.columns:
                self.logger.warning("财务摘要数据中缺少'指标'列")
                return None
            
            # 创建利润表格式的数据
            income_data = {}
            
            # 获取日期列
            date_columns = [col for col in df_abstract.columns if col not in ['选项', '指标']]
            if not date_columns:
                return None
            
            # 提取利润表相关指标
            for _, row in df_abstract.iterrows():
                try:
                    indicator = row.get('指标', None)
                    if indicator and indicator in ['营业收入', '归母净利润', '营业利润', '毛利润', '净利润']:
                        # 统一映射
                        if indicator == '归母净利润':
                            if date_columns:
                                income_data['净利润'] = row.get(date_columns[0], None)
                            else:
                                income_data['净利润'] = None
                        else:
                            if date_columns:
                                income_data[indicator] = row.get(date_columns[0], None)
                            else:
                                income_data[indicator] = None
                except Exception as row_error:
                    self.logger.warning(f"处理行数据时出错: {row_error}")
                    continue
            
            if income_data:
                return pd.DataFrame([income_data])
            return None
        except Exception as e:
            self.logger.error(f"从财务摘要提取利润表数据失败: {e}")
            return None
    
    def _extract_cash_flow_from_abstract(self, df_abstract: pd.DataFrame) -> pd.DataFrame:
        """从财务摘要中提取现金流量表相关数据"""
        try:
            if df_abstract is None or df_abstract.empty:
                return None
            
            # 检查必要的列是否存在
            if '指标' not in df_abstract.columns:
                self.logger.warning("财务摘要数据中缺少'指标'列")
                return None
            
            # 创建现金流量表格式的数据
            cash_flow_data = {}
            
            # 获取日期列
            date_columns = [col for col in df_abstract.columns if col not in ['选项', '指标']]
            if not date_columns:
                return None
            
            # 提取现金流量表相关指标
            for _, row in df_abstract.iterrows():
                try:
                    indicator = row.get('指标', None)
                    if indicator and indicator in ['经营现金流量净额', '投资现金流量净额', '筹资现金流量净额']:
                        # 映射到标准名称
                        if indicator == '经营现金流量净额':
                            if date_columns:
                                cash_flow_data['经营活动产生的现金流量净额'] = row.get(date_columns[0], None)
                            else:
                                cash_flow_data['经营活动产生的现金流量净额'] = None
                        elif indicator == '投资现金流量净额':
                            if date_columns:
                                cash_flow_data['投资活动产生的现金流量净额'] = row.get(date_columns[0], None)
                            else:
                                cash_flow_data['投资活动产生的现金流量净额'] = None
                        elif indicator == '筹资现金流量净额':
                            if date_columns:
                                cash_flow_data['筹资活动产生的现金流量净额'] = row.get(date_columns[0], None)
                            else:
                                cash_flow_data['筹资活动产生的现金流量净额'] = None
                except Exception as row_error:
                    self.logger.warning(f"处理行数据时出错: {row_error}")
                    continue
            
            if cash_flow_data:
                return pd.DataFrame([cash_flow_data])
            return None
        except Exception as e:
            self.logger.error(f"从财务摘要提取现金流量表数据失败: {e}")
            return None
    
    def _safe_float(self, value):
        """安全转换为浮点数"""
        try:
            if pd.isna(value) or value == '' or value == '-' or value is None:
                return None
            return float(value)
        except:
            return None
    
    def _filter_by_year(self, df: pd.DataFrame, target_year: int) -> pd.DataFrame:
        """按年份过滤数据"""
        try:
            if df is None or df.empty:
                return None
            
            # 查找包含年份信息的列
            date_columns = []
            for col in df.columns:
                if isinstance(col, str) and (str(target_year) in col or col.endswith(f'-12-31') or col.endswith(f'年')):
                    date_columns.append(col)
            
            # 如果找到了目标年份的列，只保留这些列
            if date_columns:
                # 保留非日期列和目标年份的列
                non_date_cols = [col for col in df.columns if col not in date_columns and not any(char.isdigit() for char in str(col))]
                keep_cols = non_date_cols + date_columns[:1]  # 只保留第一个匹配的年份列
                if keep_cols:
                    return df[keep_cols]
            
            # 如果没有找到特定年份，返回最新的数据
            return df
        except Exception as e:
            self.logger.warning(f"按年份过滤数据失败: {e}")
            return df
    
    def _filter_by_quarter(self, df: pd.DataFrame, target_year: int, target_quarter: int) -> pd.DataFrame:
        """按季度过滤数据"""
        try:
            if df is None or df.empty:
                return None
            
            # 查找包含目标年份和季度信息的列
            date_columns = []
            quarter_patterns = {
                1: ['-03-31', 'Q1', '第一季度', '一季度'],
                2: ['-06-30', 'Q2', '第二季度', '二季度'],
                3: ['-09-30', 'Q3', '第三季度', '三季度'],
                4: ['-12-31', 'Q4', '第四季度', '四季度']
            }
            
            target_patterns = quarter_patterns.get(target_quarter, [])
            
            for col in df.columns:
                if isinstance(col, str):
                    # 检查是否包含目标年份
                    if str(target_year) in col:
                        # 检查是否包含目标季度模式
                        for pattern in target_patterns:
                            if pattern in col:
                                date_columns.append(col)
                                break
            
            # 如果找到了目标季度的列，只保留这些列
            if date_columns:
                # 保留非日期列和目标季度的列
                non_date_cols = [col for col in df.columns if col not in date_columns and not any(char.isdigit() for char in str(col))]
                keep_cols = non_date_cols + date_columns[:1]  # 只保留第一个匹配的季度列
                if keep_cols:
                    return df[keep_cols]
            
            # 如果没有找到特定季度，返回最新的数据
            return df
        except Exception as e:
            self.logger.warning(f"按季度过滤数据失败: {e}")
            return df
    
    def _extract_key_metrics_from_statements(self, statements: Dict[str, Any]) -> Dict[str, Any]:
        """从财务报表中提取关键指标 - 改进版"""
        metrics = {}
        
        try:
            # 从资产负债表提取
            balance_sheet = statements.get('balance_sheet')
            if balance_sheet is not None and hasattr(balance_sheet, 'empty') and not balance_sheet.empty and len(balance_sheet) > 0:
                bs = balance_sheet.iloc[0]  # 最新期数据
                metrics.update({
                    'total_assets': self._safe_float(bs.get('总资产', None)),
                    'total_liabilities': self._safe_float(bs.get('负债合计', None)),
                    'shareholders_equity': self._safe_float(bs.get('股东权益', None)) or self._safe_float(bs.get('股东权益合计', None)),
                    'current_assets': self._safe_float(bs.get('流动资产', None)) or self._safe_float(bs.get('流动资产合计', None)),
                    'current_liabilities': self._safe_float(bs.get('流动负债', None)) or self._safe_float(bs.get('流动负债合计', None)),
                    'cash_and_cash_equivalents': self._safe_float(bs.get('货币资金', None))
                })
            
            # 从利润表提取
            profit_sheet = statements.get('profit_sheet')
            if profit_sheet is not None and hasattr(profit_sheet, 'empty') and not profit_sheet.empty and len(profit_sheet) > 0:
                ps = profit_sheet.iloc[0]  # 最新期数据
                metrics.update({
                    'revenue': self._safe_float(ps.get('营业收入', None)),
                    'net_income': self._safe_float(ps.get('净利润', None)),
                    'operating_income': self._safe_float(ps.get('营业利润', None)),
                    'gross_profit': self._safe_float(ps.get('毛利润', None))
                })
            
            # 从现金流量表提取
            cash_flow_sheet = statements.get('cash_flow_sheet')
            if cash_flow_sheet is not None and hasattr(cash_flow_sheet, 'empty') and not cash_flow_sheet.empty and len(cash_flow_sheet) > 0:
                cf = cash_flow_sheet.iloc[0]  # 最新期数据
                metrics.update({
                    'operating_cash_flow': self._safe_float(cf.get('经营活动产生的现金流量净额', None)),
                    'investing_cash_flow': self._safe_float(cf.get('投资活动产生的现金流量净额', None)),
                    'financing_cash_flow': self._safe_float(cf.get('筹资活动产生的现金流量净额', None))
                })
            
        except Exception as e:
            self.logger.error(f"从财务报表提取关键指标时出错: {e}")
        
        # 过滤掉None值
        return {k: v for k, v in metrics.items() if v is not None}
    
    def get_enhanced_financial_abstract(self, stock_code: str, limit: int = 100) -> Dict[str, Any]:
        """获取增强的财务摘要数据"""
        try:
            df_abstract = self._safe_get_data(ak.stock_financial_abstract, symbol=stock_code)
            if df_abstract is None or df_abstract.empty:
                return {}
            
            # 获取多期数据
            date_columns = [col for col in df_abstract.columns if col not in ['选项', '指标']]
            if not date_columns:
                return {}
            
            # 限制获取的期数
            date_columns = date_columns[:min(limit, len(date_columns))]
            
            enhanced_data = []
            for date_col in date_columns:
                period_data = {'report_period': date_col}
                
                # 提取所有指标
                for _, row in df_abstract.iterrows():
                    indicator = row['指标']
                    value = self._safe_float(row.get(date_col, None))
                    if value is not None:
                        # 标准化指标名称
                        standardized_name = self._standardize_indicator_name(indicator)
                        period_data[standardized_name] = value
                
                enhanced_data.append(period_data)
            
            return {'periods': enhanced_data, 'total_periods': len(enhanced_data)}
        except Exception as e:
            self.logger.error(f"获取增强财务摘要失败: {e}")
            return {}
    
    def _standardize_indicator_name(self, indicator: str) -> str:
        """标准化指标名称"""
        mapping = {
            '营业收入': 'revenue',
            '归母净利润': 'net_income',
            '净利润': 'net_income',
            '总资产': 'total_assets',
            '负债合计': 'total_liabilities',
            '股东权益': 'shareholders_equity',
            '流动资产': 'current_assets',
            '流动负债': 'current_liabilities',
            '货币资金': 'cash_and_cash_equivalents',
            '营业利润': 'operating_income',
            '毛利润': 'gross_profit',
            '经营现金流量净额': 'operating_cash_flow',
            '投资现金流量净额': 'investing_cash_flow',
            '筹资现金流量净额': 'financing_cash_flow',
            '每股收益': 'earnings_per_share',
            '每股净资产': 'book_value_per_share',
            '净资产收益率': 'return_on_equity',
            '总资产收益率': 'return_on_assets',
            '资产负债率': 'debt_to_assets',
            '流动比率': 'current_ratio',
            '速动比率': 'quick_ratio'
        }
        return mapping.get(indicator, indicator.lower().replace(' ', '_'))
    
    def _extract_growth_metrics(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """从历史财务数据中提取增长率指标"""
        metrics = {}
        
        try:
            if historical_data is None or historical_data.empty:
                return metrics
            
            # 获取日期列 (排除指标列)
            date_columns = [col for col in historical_data.columns if col not in ['选项', '指标']]
            if len(date_columns) < 2:
                return metrics
            
            # 按时间排序 (最新的在前)
            date_columns = sorted(date_columns, reverse=True)
            
            # 提取收入增长率
            revenue_rows = historical_data[historical_data['指标'] == '营业收入']
            if not revenue_rows.empty and len(date_columns) >= 2:
                current_revenue = self._safe_float(revenue_rows.iloc[0].get(date_columns[0], None))
                previous_revenue = self._safe_float(revenue_rows.iloc[0].get(date_columns[1], None))
                
                if current_revenue and previous_revenue and previous_revenue > 0:
                    metrics['revenue_growth_rate_akshare'] = (current_revenue - previous_revenue) / previous_revenue
            
            # 提取净利润增长率
            profit_rows = historical_data[historical_data['指标'].isin(['净利润', '归母净利润'])]
            if not profit_rows.empty and len(date_columns) >= 2:
                current_profit = self._safe_float(profit_rows.iloc[0].get(date_columns[0], None))
                previous_profit = self._safe_float(profit_rows.iloc[0].get(date_columns[1], None))
                
                if current_profit and previous_profit and previous_profit > 0:
                    metrics['net_income_growth_rate_akshare'] = (current_profit - previous_profit) / previous_profit
            
            # 提取总资产增长率
            asset_rows = historical_data[historical_data['指标'] == '总资产']
            if not asset_rows.empty and len(date_columns) >= 2:
                current_assets = self._safe_float(asset_rows.iloc[0].get(date_columns[0], None))
                previous_assets = self._safe_float(asset_rows.iloc[0].get(date_columns[1], None))
                
                if current_assets and previous_assets and previous_assets > 0:
                    metrics['total_assets_growth_rate_akshare'] = (current_assets - previous_assets) / previous_assets
            
            # 计算3年复合增长率 (如果有足够数据)
            if len(date_columns) >= 4:
                # 收入3年CAGR
                if not revenue_rows.empty:
                    current_revenue = self._safe_float(revenue_rows.iloc[0].get(date_columns[0], None))
                    three_year_revenue = self._safe_float(revenue_rows.iloc[0].get(date_columns[3], None))
                    
                    if current_revenue and three_year_revenue and three_year_revenue > 0:
                        metrics['revenue_cagr_3y_akshare'] = (current_revenue / three_year_revenue) ** (1/3) - 1
                
                # 净利润3年CAGR
                if not profit_rows.empty:
                    current_profit = self._safe_float(profit_rows.iloc[0].get(date_columns[0], None))
                    three_year_profit = self._safe_float(profit_rows.iloc[0].get(date_columns[3], None))
                    
                    if current_profit and three_year_profit and three_year_profit > 0:
                        metrics['net_income_cagr_3y_akshare'] = (current_profit / three_year_profit) ** (1/3) - 1
        
        except Exception as e:
            self.logger.error(f"提取增长率指标时出错: {e}")
        
        return {k: v for k, v in metrics.items() if v is not None}
    
    def _extract_market_metrics(self, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """从市场基本信息中提取关键指标"""
        metrics = {}
        
        try:
            # 从东方财富基本信息提取
            em_info = basic_info.get('em_basic_info', {})
            if em_info:
                metrics.update({
                    'market_cap_em': self._safe_float(em_info.get('总市值', None)),
                    'pe_ratio_em': self._safe_float(em_info.get('市盈率-动态', None)),
                    'pb_ratio_em': self._safe_float(em_info.get('市净率', None)),
                    'shares_outstanding_em': self._safe_float(em_info.get('总股本', None))
                })
            
            # 从实时行情提取
            sina_realtime = basic_info.get('sina_realtime', {})
            if sina_realtime:
                metrics.update({
                    'current_price_sina': self._safe_float(sina_realtime.get('最新价', None)),
                    'price_change_pct_sina': self._safe_float(sina_realtime.get('涨跌幅', None)),
                    'volume_sina': self._safe_float(sina_realtime.get('成交量', None)),
                    'turnover_sina': self._safe_float(sina_realtime.get('成交额', None))
                })
            
            # 从价格数据提取技术指标
            price_data = basic_info.get('price_data', {})
            if price_data:
                metrics.update(price_data)
        
        except Exception as e:
            self.logger.error(f"提取市场指标时出错: {e}")
        
        return {k: v for k, v in metrics.items() if v is not None}
    
    def _extract_key_metrics_from_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """从财务指标中提取关键数据"""
        metrics = {}
        
        try:
            financial_indicators = indicators.get('financial_indicators')
            if financial_indicators is not None and hasattr(financial_indicators, 'empty') and not financial_indicators.empty and len(financial_indicators) > 0:
                fi = financial_indicators.iloc[0]  # 最新期数据
                metrics.update({
                    'roe_akshare': self._safe_float(fi.get('净资产收益率', None)),
                    'roa_akshare': self._safe_float(fi.get('总资产收益率', None)),
                    'eps_akshare': self._safe_float(fi.get('每股收益', None)),
                    'debt_to_equity_ratio_akshare': self._safe_float(fi.get('资产负债率', None)),
                    'current_ratio_akshare': self._safe_float(fi.get('流动比率', None)),
                    'quick_ratio_akshare': self._safe_float(fi.get('速动比率', None))
                })
            
            valuation_metrics = indicators.get('valuation_metrics')
            if valuation_metrics is not None and hasattr(valuation_metrics, 'empty') and not valuation_metrics.empty and len(valuation_metrics) > 0:
                vm = valuation_metrics.iloc[0]  # 最新期数据
                metrics.update({
                    'pe_ratio_akshare': self._safe_float(vm.get('市盈率(TTM)', None)),
                    'pb_ratio_akshare': self._safe_float(vm.get('市净率', None)),
                    'market_cap_akshare': self._safe_float(vm.get('总市值', None))
                })
        except Exception as e:
            self.logger.error(f"从财务指标提取关键数据时出错: {e}")
        
        # 过滤掉None值
        return {k: v for k, v in metrics.items() if v is not None}

    def _get_enhanced_balance_sheet_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的资产负债表数据 - 多数据源备份"""
        balance_data = {}
        
        try:
            # 数据源优先级：东方财富 -> 同花顺 -> 财务摘要
            sources = [
                ('stock_balance_sheet_by_yearly_em', '东方财富年度资产负债表'),
                ('stock_balance_sheet_by_report_em', '东方财富报告期资产负债表'),
                ('stock_financial_debt_ths', '同花顺资产负债表'),
                ('stock_zcfz_em', '东方财富资产负债表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新年度数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                balance_data.update({
                                    'total_assets': self._safe_float(latest_data.get('总资产')),
                                    'current_assets': self._safe_float(latest_data.get('流动资产合计')),
                                    'non_current_assets': self._safe_float(latest_data.get('非流动资产合计')),
                                    'total_liabilities': self._safe_float(latest_data.get('负债合计')),
                                    'current_liabilities': self._safe_float(latest_data.get('流动负债合计')),
                                    'non_current_liabilities': self._safe_float(latest_data.get('非流动负债合计')),
                                    'shareholders_equity': self._safe_float(latest_data.get('股东权益合计')),
                                    'cash_and_cash_equivalents': self._safe_float(latest_data.get('货币资金')),
                                    'inventory': self._safe_float(latest_data.get('存货')),
                                    'accounts_receivable': self._safe_float(latest_data.get('应收账款')),
                                    'fixed_assets': self._safe_float(latest_data.get('固定资产')),
                                    'intangible_assets': self._safe_float(latest_data.get('无形资产')),
                                    'long_term_debt': self._safe_float(latest_data.get('长期借款')),
                                    'short_term_debt': self._safe_float(latest_data.get('短期借款')),
                                    'accounts_payable': self._safe_float(latest_data.get('应付账款')),
                                    'retained_earnings': self._safe_float(latest_data.get('未分配利润'))
                                })
                                self.logger.info(f"从{desc}成功获取资产负债表数据")
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强资产负债表数据时发生错误: {e}")
        
        return {k: v for k, v in balance_data.items() if v is not None}
    
    def _get_enhanced_income_statement_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的利润表数据 - 年度和季度数据"""
        income_data = {}
        
        try:
            # 数据源优先级：东方财富 -> 同花顺
            sources = [
                ('stock_profit_sheet_by_yearly_em', '东方财富年度利润表'),
                ('stock_profit_sheet_by_quarterly_em', '东方财富季度利润表'),
                ('stock_profit_sheet_by_report_em', '东方财富报告期利润表'),
                ('stock_financial_benefit_ths', '同花顺利润表'),
                ('stock_lrb_em', '东方财富利润表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新期数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                income_data.update({
                                    'total_revenue': self._safe_float(latest_data.get('营业总收入')),
                                    'operating_revenue': self._safe_float(latest_data.get('营业收入')),
                                    'operating_costs': self._safe_float(latest_data.get('营业成本')),
                                    'gross_profit': self._safe_float(latest_data.get('毛利润')),
                                    'operating_profit': self._safe_float(latest_data.get('营业利润')),
                                    'total_profit': self._safe_float(latest_data.get('利润总额')),
                                    'net_profit': self._safe_float(latest_data.get('净利润')),
                                    'net_profit_attributable_to_parent': self._safe_float(latest_data.get('归属于母公司所有者的净利润')),
                                    'ebitda': self._safe_float(latest_data.get('息税折旧摊销前利润')),
                                    'operating_expenses': self._safe_float(latest_data.get('营业总成本')),
                                    'selling_expenses': self._safe_float(latest_data.get('销售费用')),
                                    'admin_expenses': self._safe_float(latest_data.get('管理费用')),
                                    'rd_expenses': self._safe_float(latest_data.get('研发费用')),
                                    'financial_expenses': self._safe_float(latest_data.get('财务费用')),
                                    'interest_expense': self._safe_float(latest_data.get('利息费用')),
                                    'tax_expense': self._safe_float(latest_data.get('所得税费用')),
                                    'eps_basic': self._safe_float(latest_data.get('基本每股收益')),
                                    'eps_diluted': self._safe_float(latest_data.get('稀释每股收益'))
                                })
                                self.logger.info(f"从{desc}成功获取利润表数据")
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强利润表数据时发生错误: {e}")
        
        return {k: v for k, v in income_data.items() if v is not None}
    
    def _get_enhanced_cash_flow_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的现金流量表数据"""
        cash_flow_data = {}
        
        try:
            # 数据源优先级：东方财富 -> 同花顺
            sources = [
                ('stock_cash_flow_sheet_by_yearly_em', '东方财富年度现金流量表'),
                ('stock_cash_flow_sheet_by_quarterly_em', '东方财富季度现金流量表'),
                ('stock_cash_flow_sheet_by_report_em', '东方财富报告期现金流量表'),
                ('stock_financial_cash_ths', '同花顺现金流量表'),
                ('stock_xjll_em', '东方财富现金流量表')
            ]
            
            for source_func, desc in sources:
                try:
                    if hasattr(ak, source_func):
                        df = self._safe_get_data(getattr(ak, source_func), symbol=stock_code)
                        if df is not None and not df.empty:
                            # 获取最新期数据
                            latest_data = df.iloc[-1] if len(df) > 0 else None
                            if latest_data is not None:
                                cash_flow_data.update({
                                    'operating_cash_flow': self._safe_float(latest_data.get('经营活动产生的现金流量净额')),
                                    'investing_cash_flow': self._safe_float(latest_data.get('投资活动产生的现金流量净额')),
                                    'financing_cash_flow': self._safe_float(latest_data.get('筹资活动产生的现金流量净额')),
                                    'net_cash_flow': self._safe_float(latest_data.get('现金及现金等价物净增加额')),
                                    'free_cash_flow': self._safe_float(latest_data.get('自由现金流量')),
                                    'capital_expenditure': self._safe_float(latest_data.get('购建固定资产、无形资产和其他长期资产支付的现金')),
                                    'cash_from_operations': self._safe_float(latest_data.get('经营活动现金流入小计')),
                                    'cash_to_operations': self._safe_float(latest_data.get('经营活动现金流出小计')),
                                    'cash_from_investing': self._safe_float(latest_data.get('投资活动现金流入小计')),
                                    'cash_to_investing': self._safe_float(latest_data.get('投资活动现金流出小计')),
                                    'cash_from_financing': self._safe_float(latest_data.get('筹资活动现金流入小计')),
                                    'cash_to_financing': self._safe_float(latest_data.get('筹资活动现金流出小计'))
                                })
                                self.logger.info(f"从{desc}成功获取现金流量表数据")
                                break
                except Exception as e:
                    self.logger.warning(f"从{desc}获取数据失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取增强现金流量表数据时发生错误: {e}")
        
        return {k: v for k, v in cash_flow_data.items() if v is not None}
    
    def _get_enhanced_dividend_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的分红数据"""
        dividend_data = {}
        
        # 注释掉不存在的分红数据API
        # try:
        #     # 获取历史分红数据
        #     df = self._safe_get_data(ak.stock_zh_a_dividend, symbol=stock_code)
        #     if df is not None and not df.empty:
        #         # 获取最新分红数据
        #         latest_dividend = df.iloc[-1] if len(df) > 0 else None
        #         if latest_dividend is not None:
        #             dividend_data.update({
        #                 'dividend_per_share': self._safe_float(latest_dividend.get('每股股利')),
        #                 'dividend_yield': self._safe_float(latest_dividend.get('股息率')),
        #                 'payout_ratio': self._safe_float(latest_dividend.get('分红比例')),
        #                 'ex_dividend_date': latest_dividend.get('除权除息日'),
        #                 'dividend_announcement_date': latest_dividend.get('公告日期')
        #             })
        #         
        #         # 计算历史分红统计
        #         if len(df) > 1:
        #             dividend_data.update({
        #                 'dividend_history_years': len(df),
        #                 'avg_dividend_per_share': self._safe_float(df['每股股利'].mean()) if '每股股利' in df.columns else None,
        #                 'dividend_growth_rate': self._calculate_dividend_growth_rate(df)
        #             })
        # 
        # except Exception as e:
        #     self.logger.warning(f"获取分红数据失败: {e}")
        
        self.logger.info(f"增强分红数据API已禁用，因为stock_zh_a_dividend不存在")
        
        return {k: v for k, v in dividend_data.items() if v is not None}
    
    def _get_enhanced_valuation_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的估值数据 - 多数据源，优先使用AKShare官方PE/PB接口"""
        valuation_data = {}
        
        try:
            # 优先数据源1: 使用stock_industry_pe_ratio_cninfo获取PE数据 (推荐)
            try:
                df = self._safe_get_data(ak.stock_industry_pe_ratio_cninfo)
                if df is not None and not df.empty:
                    # 安全地查找对应股票代码的数据，处理Length mismatch错误
                    try:
                        if '股票代码' in df.columns:
                            stock_data = df[df['股票代码'] == stock_code]
                            if not stock_data.empty:
                                latest_data = stock_data.iloc[-1]
                                pe_ratio = self._safe_float(latest_data.get('市盈率'))
                                pb_ratio = self._safe_float(latest_data.get('市净率'))
                                
                                # 验证PE/PB数据的合理性
                                if pe_ratio is not None and 0 < pe_ratio <= 1000:
                                    valuation_data['pe_ratio'] = pe_ratio
                                    valuation_data['pe_ratio_source'] = 'cninfo_industry'
                                    self.logger.info(f"获取到CNINFO PE数据: {pe_ratio}")
                                
                                if pb_ratio is not None and 0 < pb_ratio <= 100:
                                    valuation_data['pb_ratio'] = pb_ratio
                                    valuation_data['pb_ratio_source'] = 'cninfo_industry'
                                    self.logger.info(f"获取到CNINFO PB数据: {pb_ratio}")
                                    
                                # 添加行业信息
                                if '行业名称' in latest_data:
                                    valuation_data['industry_name'] = latest_data.get('行业名称')
                        else:
                            self.logger.warning("CNINFO数据中缺少'股票代码'列")
                    except (KeyError, IndexError, ValueError) as e:
                        self.logger.warning(f"处理CNINFO数据时出现Length mismatch或索引错误: {e}")
                            
            except Exception as e:
                self.logger.warning(f"获取CNINFO行业PE数据失败: {e}")
            
            # 备份数据源1: AKShare官方A股个股市盈率、市净率和股息率指标
            if 'pe_ratio' not in valuation_data:  # 只有在主要数据源失败时才使用备份
                try:
                    df = self._safe_get_data(ak.stock_a_indicator_lg, symbol=stock_code)
                    if df is not None and not df.empty:
                        # 获取最新数据
                        latest_data = df.iloc[-1] if len(df) > 0 else None
                        if latest_data is not None:
                            pe_ratio = self._safe_float(latest_data.get('市盈率'))
                            pb_ratio = self._safe_float(latest_data.get('市净率'))
                            dividend_yield = self._safe_float(latest_data.get('股息率'))
                            
                            # 验证PE/PB数据的合理性
                            if pe_ratio is not None and 0 < pe_ratio <= 1000:
                                valuation_data['pe_ratio'] = pe_ratio
                                valuation_data['pe_ratio_source'] = 'akshare_official_backup'
                                self.logger.info(f"获取到官方PE备份数据: {pe_ratio}")
                            
                            if pb_ratio is not None and 0 < pb_ratio <= 100:
                                valuation_data['pb_ratio'] = pb_ratio
                                valuation_data['pb_ratio_source'] = 'akshare_official_backup'
                                self.logger.info(f"获取到官方PB备份数据: {pb_ratio}")
                            
                            if dividend_yield is not None:
                                valuation_data['dividend_yield'] = dividend_yield
                                
                            # 添加数据日期
                            if '日期' in latest_data:
                                valuation_data['valuation_date'] = latest_data.get('日期')
                                
                except Exception as e:
                    self.logger.warning(f"获取AKShare官方PE/PB数据失败: {e}")
            
            # 补充数据源2: 全部A股等权重市盈率、中位数市盈率
            try:
                if 'pe_ratio' not in valuation_data:  # 只有在没有获取到官方PE数据时才使用
                    df = self._safe_get_data(ak.stock_a_ttm_lyr)
                    if df is not None and not df.empty:
                        # 这个接口返回的是全市场数据，可以用作参考
                        latest_market_data = df.iloc[-1] if len(df) > 0 else None
                        if latest_market_data is not None:
                            valuation_data.update({
                                'market_avg_pe_equal_weight': self._safe_float(latest_market_data.get('等权重市盈率')),
                                'market_median_pe': self._safe_float(latest_market_data.get('中位数市盈率')),
                                'market_pe_date': latest_market_data.get('日期')
                            })
            except Exception as e:
                self.logger.warning(f"获取市场PE数据失败: {e}")
            
            # 补充数据源3: 全部A股等权重市净率、中位数市净率
            try:
                if 'pb_ratio' not in valuation_data:  # 只有在没有获取到官方PB数据时才使用
                    df = self._safe_get_data(ak.stock_a_all_pb)
                    if df is not None and not df.empty:
                        # 这个接口返回的是全市场数据，可以用作参考
                        latest_market_data = df.iloc[-1] if len(df) > 0 else None
                        if latest_market_data is not None:
                            valuation_data.update({
                                'market_avg_pb_equal_weight': self._safe_float(latest_market_data.get('等权重市净率')),
                                'market_median_pb': self._safe_float(latest_market_data.get('中位数市净率')),
                                'market_pb_date': latest_market_data.get('日期')
                            })
            except Exception as e:
                self.logger.warning(f"获取市场PB数据失败: {e}")
            
            # 备用数据源4: 百度估值数据 (仅在官方数据不可用时使用)
            try:
                if 'pe_ratio' not in valuation_data or 'pb_ratio' not in valuation_data:
                    df = self._safe_get_data(ak.stock_zh_valuation_baidu, symbol=stock_code)
                    if df is not None and not df.empty:
                        latest_valuation = df.iloc[-1] if len(df) > 0 else None
                        if latest_valuation is not None:
                            if 'pe_ratio' not in valuation_data:
                                pe_backup = self._safe_float(latest_valuation.get('市盈率'))
                                if pe_backup is not None and 0 < pe_backup <= 1000:
                                    valuation_data['pe_ratio'] = pe_backup
                                    valuation_data['pe_ratio_source'] = 'baidu_backup'
                            
                            if 'pb_ratio' not in valuation_data:
                                pb_backup = self._safe_float(latest_valuation.get('市净率'))
                                if pb_backup is not None and 0 < pb_backup <= 100:
                                    valuation_data['pb_ratio'] = pb_backup
                                    valuation_data['pb_ratio_source'] = 'baidu_backup'
                            
                            # 其他估值指标
                            valuation_data.update({
                                'ps_ratio': self._safe_float(latest_valuation.get('市销率')),
                                'market_cap': self._safe_float(latest_valuation.get('总市值')),
                                'enterprise_value': self._safe_float(latest_valuation.get('企业价值'))
                            })
            except Exception as e:
                self.logger.warning(f"获取百度估值数据失败: {e}")
            
            # 备用数据源5: 东方财富个股信息
            try:
                df = self._safe_get_data(ak.stock_individual_info_em, symbol=stock_code)
                if df is not None and not df.empty:
                    info = df.iloc[0] if len(df) > 0 else None
                    if info is not None:
                        # 作为备用数据源或验证数据
                        pe_em = self._safe_float(info.get('市盈率-动态'))
                        pb_em = self._safe_float(info.get('市净率'))
                        
                        if 'pe_ratio' not in valuation_data and pe_em is not None and 0 < pe_em <= 1000:
                            valuation_data['pe_ratio'] = pe_em
                            valuation_data['pe_ratio_source'] = 'em_backup'
                        
                        if 'pb_ratio' not in valuation_data and pb_em is not None and 0 < pb_em <= 100:
                            valuation_data['pb_ratio'] = pb_em
                            valuation_data['pb_ratio_source'] = 'em_backup'
                        
                        # 其他有用信息
                        valuation_data.update({
                            'pe_ratio_em': pe_em,
                            'pb_ratio_em': pb_em,
                            'market_cap_em': self._safe_float(info.get('总市值')),
                            'circulating_market_cap': self._safe_float(info.get('流通市值')),
                            'shares_outstanding': self._safe_float(info.get('总股本')),
                            'circulating_shares': self._safe_float(info.get('流通股'))
                        })
            except Exception as e:
                self.logger.warning(f"获取东方财富估值数据失败: {e}")
            
            # 备用数据源6: 同花顺财务指标
            try:
                df = self._safe_get_data(ak.stock_financial_abstract_ths, symbol=stock_code)
                if df is not None and not df.empty:
                    # 提取估值相关指标
                    for _, row in df.iterrows():
                        indicator = row.get('指标', '')
                        if '市盈率' in indicator:
                            pe_ths = self._safe_float(row.get('值'))
                            if 'pe_ratio' not in valuation_data and pe_ths is not None and 0 < pe_ths <= 1000:
                                valuation_data['pe_ratio'] = pe_ths
                                valuation_data['pe_ratio_source'] = 'ths_backup'
                            valuation_data['pe_ratio_ths'] = pe_ths
                        elif '市净率' in indicator:
                            pb_ths = self._safe_float(row.get('值'))
                            if 'pb_ratio' not in valuation_data and pb_ths is not None and 0 < pb_ths <= 100:
                                valuation_data['pb_ratio'] = pb_ths
                                valuation_data['pb_ratio_source'] = 'ths_backup'
                            valuation_data['pb_ratio_ths'] = pb_ths
            except Exception as e:
                self.logger.warning(f"获取同花顺估值数据失败: {e}")
        
        except Exception as e:
            self.logger.error(f"获取增强估值数据时发生错误: {e}")
        
        # 记录最终获取到的PE/PB数据来源
        if 'pe_ratio' in valuation_data:
            self.logger.info(f"最终PE数据: {valuation_data['pe_ratio']}, 来源: {valuation_data.get('pe_ratio_source', 'unknown')}")
        if 'pb_ratio' in valuation_data:
            self.logger.info(f"最终PB数据: {valuation_data['pb_ratio']}, 来源: {valuation_data.get('pb_ratio_source', 'unknown')}")
        
        return {k: v for k, v in valuation_data.items() if v is not None}
    
    def _get_industry_comparison_data(self, stock_code: str) -> Dict[str, Any]:
        """获取行业对比数据"""
        industry_data = {}
        
        try:
            # 获取股票所属行业
            df = self._safe_get_data(ak.stock_individual_info_em, symbol=stock_code)
            if df is not None and not df.empty:
                info = df.iloc[0] if len(df) > 0 else None
                if info is not None:
                    industry = info.get('所属行业', None)
                    if industry:
                        industry_data['industry'] = industry
                        
                        # 获取行业平均估值数据
                        try:
                            industry_df = self._safe_get_data(ak.stock_board_industry_cons_em, symbol=industry)
                            if industry_df is not None and not industry_df.empty:
                                # 计算行业平均值
                                industry_data.update({
                                    'industry_avg_pe': self._safe_float(industry_df['市盈率-动态'].mean()) if '市盈率-动态' in industry_df.columns else None,
                                    'industry_avg_pb': self._safe_float(industry_df['市净率'].mean()) if '市净率' in industry_df.columns else None,
                                    'industry_avg_roe': self._safe_float(industry_df['净资产收益率'].mean()) if '净资产收益率' in industry_df.columns else None,
                                    'industry_companies_count': len(industry_df)
                                })
                        except Exception as e:
                            self.logger.warning(f"获取行业对比数据失败: {e}")
        
        except Exception as e:
            self.logger.warning(f"获取行业信息失败: {e}")
        
        return {k: v for k, v in industry_data.items() if v is not None}
    
    def _get_enhanced_technical_data(self, stock_code: str) -> Dict[str, Any]:
        """获取增强的技术指标数据"""
        technical_data = {}
        
        try:
            # 获取历史价格数据
            hist_data = self._safe_get_data(ak.stock_zh_a_hist, symbol=stock_code, period="daily", start_date="20230101", adjust="qfq")
            if hist_data is not None and not hist_data.empty and len(hist_data) >= 60:
                # 计算技术指标
                close_prices = hist_data['收盘']
                volumes = hist_data['成交量'] if '成交量' in hist_data.columns else None
                
                # 移动平均线
                technical_data.update({
                    'ma_5': self._safe_float(close_prices.rolling(5).mean().iloc[-1]),
                    'ma_10': self._safe_float(close_prices.rolling(10).mean().iloc[-1]),
                    'ma_20': self._safe_float(close_prices.rolling(20).mean().iloc[-1]),
                    'ma_60': self._safe_float(close_prices.rolling(60).mean().iloc[-1]),
                    'current_price': self._safe_float(close_prices.iloc[-1])
                })
                
                # 价格变化率
                if len(close_prices) >= 20:
                    technical_data.update({
                        'price_change_1d': self._safe_float((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]),
                        'price_change_5d': self._safe_float((close_prices.iloc[-1] - close_prices.iloc[-6]) / close_prices.iloc[-6]),
                        'price_change_20d': self._safe_float((close_prices.iloc[-1] - close_prices.iloc[-21]) / close_prices.iloc[-21])
                    })
                
                # 波动率
                returns = close_prices.pct_change().dropna()
                if len(returns) >= 20:
                    technical_data.update({
                        'volatility_20d': self._safe_float(returns.rolling(20).std().iloc[-1] * (252 ** 0.5)),
                        'volatility_60d': self._safe_float(returns.rolling(60).std().iloc[-1] * (252 ** 0.5)) if len(returns) >= 60 else None
                    })
                
                # 成交量指标
                if volumes is not None and len(volumes) >= 20:
                    avg_volume_20d = volumes.rolling(20).mean().iloc[-1]
                    technical_data.update({
                        'volume_ratio': self._safe_float(volumes.iloc[-1] / avg_volume_20d) if avg_volume_20d > 0 else None,
                        'avg_volume_20d': self._safe_float(avg_volume_20d)
                    })
        
        except Exception as e:
            self.logger.warning(f"获取技术指标数据失败: {e}")
        
        return {k: v for k, v in technical_data.items() if v is not None}
    

    
    def _check_data_consistency(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """数据一致性检查"""
        try:
            # 检查总资产 = 负债 + 股东权益
            total_assets = data.get('total_assets')
            total_liabilities = data.get('total_liabilities')
            shareholders_equity = data.get('shareholders_equity')
            
            if all(v is not None for v in [total_assets, total_liabilities, shareholders_equity]):
                calculated_assets = total_liabilities + shareholders_equity
                if abs(total_assets - calculated_assets) / total_assets > 0.05:  # 5%容差
                    repair_log.append(f"资产负债表不平衡: 总资产={total_assets}, 负债+权益={calculated_assets}")
            
            # 检查流动比率一致性
            current_assets = data.get('current_assets')
            current_liabilities = data.get('current_liabilities')
            current_ratio = data.get('current_ratio_akshare')
            
            if all(v is not None for v in [current_assets, current_liabilities, current_ratio]) and current_liabilities > 0:
                calculated_ratio = current_assets / current_liabilities
                if abs(current_ratio - calculated_ratio) / current_ratio > 0.1:  # 10%容差
                    repair_log.append(f"流动比率不一致: 报告值={current_ratio}, 计算值={calculated_ratio}")
                    data['current_ratio_calculated'] = calculated_ratio
        
        except Exception as e:
            self.logger.warning(f"数据一致性检查失败: {e}")
        
        return data
    
    def _repair_missing_data(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """缺失数据修复"""
        try:
            # 修复缺失的自由现金流
            if 'free_cash_flow' not in data or data['free_cash_flow'] is None:
                operating_cf = data.get('operating_cash_flow')
                capex = data.get('capital_expenditure')
                if operating_cf is not None and capex is not None:
                    data['free_cash_flow'] = operating_cf - capex
                    repair_log.append("计算自由现金流 = 经营现金流 - 资本支出")
            
            # 修复缺失的毛利率
            if 'gross_margin' not in data:
                gross_profit = data.get('gross_profit')
                revenue = data.get('total_revenue') or data.get('operating_revenue')
                if gross_profit is not None and revenue is not None and revenue > 0:
                    data['gross_margin'] = gross_profit / revenue
                    repair_log.append("计算毛利率 = 毛利润 / 营业收入")
            
            # 修复缺失的净利率
            if 'net_margin' not in data:
                net_profit = data.get('net_profit')
                revenue = data.get('total_revenue') or data.get('operating_revenue')
                if net_profit is not None and revenue is not None and revenue > 0:
                    data['net_margin'] = net_profit / revenue
                    repair_log.append("计算净利率 = 净利润 / 营业收入")
            
            # 修复缺失的资产周转率
            if 'asset_turnover' not in data:
                revenue = data.get('total_revenue') or data.get('operating_revenue')
                total_assets = data.get('total_assets')
                if revenue is not None and total_assets is not None and total_assets > 0:
                    data['asset_turnover'] = revenue / total_assets
                    repair_log.append("计算资产周转率 = 营业收入 / 总资产")
        
        except Exception as e:
            self.logger.warning(f"缺失数据修复失败: {e}")
        
        return data
    
    def _detect_and_handle_outliers(self, data: Dict[str, Any], repair_log: List[str]) -> Dict[str, Any]:
        """异常值检测和处理"""
        try:
            # 检测价格相关异常值
            price_keys = ['current_price', 'current_price_sina']
            for key in price_keys:
                if key in data:
                    price = data[key]
                    if price <= 0 or price > 10000:  # 股价异常范围
                        repair_log.append(f"移除异常股价: {key} = {price}")
                        del data[key]
            
            # 检测成交量异常值
            volume_keys = ['volume_sina', 'avg_volume_20d']
            for key in volume_keys:
                if key in data:
                    volume = data[key]
                    if volume < 0:
                        repair_log.append(f"移除负成交量: {key} = {volume}")
                        del data[key]
        
        except Exception as e:
            self.logger.warning(f"异常值检测失败: {e}")
        
        return data
    
    def _calculate_dividend_growth_rate(self, dividend_df: pd.DataFrame) -> float:
        """计算分红增长率"""
        try:
            if len(dividend_df) < 2 or '每股股利' not in dividend_df.columns:
                return None
            
            dividends = dividend_df['每股股利'].dropna()
            if len(dividends) < 2:
                return None
            
            # 计算年化增长率
            first_dividend = dividends.iloc[0]
            last_dividend = dividends.iloc[-1]
            years = len(dividends) - 1
            
            if first_dividend > 0 and years > 0:
                growth_rate = (last_dividend / first_dividend) ** (1/years) - 1
                return self._safe_float(growth_rate)
        
        except Exception as e:
            self.logger.warning(f"计算分红增长率失败: {e}")
        
        return None

# 创建全局实例
akshare_adapter = AKShareAdapter()