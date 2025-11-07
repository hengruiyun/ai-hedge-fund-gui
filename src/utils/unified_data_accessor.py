"""
统一数据访问适配器
提供简单的接口，将data_enhancer和data_prefetcher集成到一起，供分析师代理使用
"""

from typing import Dict, List, Any, Optional
import logging
from src.utils.data_enhancer import data_enhancer
from src.utils.data_prefetch import data_prefetcher

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class UnifiedDataAccessor:
    """统一数据访问适配器，整合数据增强器和数据预取器"""
    
    def __init__(self):
        self.data_enhancer = data_enhancer
        self.data_prefetcher = data_prefetcher
        
    def get_enhanced_data(self, ticker: str, prefetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取增强的财务数据，整合了数据预取和数据增强
        
        Args:
            ticker: 股票代码
            prefetched_data: 预获取的数据
            
        Returns:
            增强后的财务数据
        """
        try:
            logger.info(f"开始获取 {ticker} 的增强数据")
            
            # 首先从预取数据中获取综合数据
            comprehensive_data = self.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
            
            # 提取增强的财务数据
            enhanced_financial_data = comprehensive_data.get('enhanced_financial_data', {})
            
            # 如果增强数据为空，尝试从基础数据构建
            if not enhanced_financial_data:
                logger.warning(f"{ticker} 增强财务数据为空，尝试从基础数据构建")
                
                # 获取基础财务数据
                financial_metrics = comprehensive_data.get('financial_metrics', [])
                line_items = comprehensive_data.get('line_items', [])
                market_cap = comprehensive_data.get('market_cap')
                akshare_data = comprehensive_data.get('akshare_comprehensive_data', {})
                
                # 从多个数据源构建增强数据
                enhanced_financial_data = {}
                
                # 1. 优先使用validated_financial_data
                validated_data = comprehensive_data.get('validated_financial_data', {})
                if validated_data:
                    enhanced_financial_data.update(validated_data)
                    logger.debug(f"{ticker} 使用验证财务数据，字段数: {len(validated_data)}")
                
                # 2. 使用akshare_comprehensive_data
                if akshare_data:
                    enhanced_financial_data.update(akshare_data)
                    logger.debug(f"{ticker} 添加AKShare数据，总字段数: {len(enhanced_financial_data)}")
                
                # 3. 从financial_metrics提取数据
                if financial_metrics:
                    extracted_from_metrics = self._extract_from_financial_metrics(financial_metrics)
                    enhanced_financial_data.update(extracted_from_metrics)
                    logger.debug(f"{ticker} 从财务指标提取数据，字段数: {len(extracted_from_metrics)}")
                
                # 4. 从line_items提取数据
                if line_items:
                    extracted_from_line_items = self._extract_from_line_items(line_items)
                    enhanced_financial_data.update(extracted_from_line_items)
                    logger.debug(f"{ticker} 从项目数据提取数据，字段数: {len(extracted_from_line_items)}")
                
                # 5. 添加市值数据
                if market_cap:
                    enhanced_financial_data['market_cap'] = market_cap
                
                # 使用数据增强器进一步增强数据
                enhanced_financial_data = self.data_enhancer.enhance_financial_data(enhanced_financial_data)
                
                logger.info(f"{ticker} 构建增强数据完成，总字段数: {len(enhanced_financial_data)}")
            
            else:
                # 对已有的增强数据进行进一步处理
                enhanced_financial_data = self.data_enhancer.enhance_financial_data(enhanced_financial_data)
                logger.info(f"{ticker} 进一步增强数据，字段数: {len(enhanced_financial_data)}")
            
            # 返回结构化数据
            return {
                'enhanced_financial_data': enhanced_financial_data,
                'market_cap': comprehensive_data.get('market_cap'),
                'data_sources': comprehensive_data.get('data_sources', [])
            }
            
        except Exception as e:
            logger.error(f"获取 {ticker} 增强数据失败: {e}")
            return {
                'enhanced_financial_data': {},
                'market_cap': None,
                'data_sources': []
            }
    
    def _extract_from_financial_metrics(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """从financial_metrics数据中提取有用信息"""
        extracted = {}
        
        try:
            if isinstance(metrics_data, list) and metrics_data:
                for metric_item in metrics_data:
                    if isinstance(metric_item, dict):
                        # 直接更新字典
                        extracted.update(metric_item)
                    elif hasattr(metric_item, '__dict__'):
                        # 如果是对象，提取属性
                        for attr_name in dir(metric_item):
                            if not attr_name.startswith('_'):
                                try:
                                    attr_value = getattr(metric_item, attr_name)
                                    if not callable(attr_value) and attr_value is not None:
                                        extracted[attr_name] = attr_value
                                except:
                                    pass
            
            # 过滤无效值
            filtered = {}
            for key, value in extracted.items():
                if value is not None and str(value).lower() not in ['nan', 'none', 'null', '']:
                    try:
                        # 尝试转换为数值
                        if isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                            filtered[key] = float(value)
                        else:
                            filtered[key] = value
                    except:
                        filtered[key] = value
            
            return filtered
            
        except Exception as e:
            logger.warning(f"提取financial_metrics数据失败: {e}")
            return {}
    
    def _extract_from_line_items(self, line_items_data: List[Dict]) -> Dict[str, Any]:
        """从line_items数据中提取有用信息"""
        extracted = {}
        
        try:
            if isinstance(line_items_data, list) and line_items_data:
                for item in line_items_data:
                    if isinstance(item, dict):
                        extracted.update(item)
                    elif hasattr(item, '__dict__'):
                        # 如果是对象，提取属性
                        for attr_name in dir(item):
                            if not attr_name.startswith('_'):
                                try:
                                    attr_value = getattr(item, attr_name)
                                    if not callable(attr_value) and attr_value is not None:
                                        extracted[attr_name] = attr_value
                                except:
                                    pass
            
            # 过滤和转换
            filtered = {}
            for key, value in extracted.items():
                if value is not None and str(value).lower() not in ['nan', 'none', 'null', '']:
                    try:
                        if isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                            filtered[key] = float(value)
                        else:
                            filtered[key] = value
                    except:
                        filtered[key] = value
            
            return filtered
            
        except Exception as e:
            logger.warning(f"提取line_items数据失败: {e}")
            return {}

    def safe_get(self, data: dict, key: str, default=None, calculate_if_missing=True):
        """
        安全获取数据，支持智能计算和估算
        
        Args:
            data: 数据字典
            key: 要获取的键
            default: 默认值
            calculate_if_missing: 是否在缺失时尝试计算
        """
        # 支持嵌套键访问 (例如 'financial_data.revenue')
        if '.' in key:
            keys = key.split('.')
            value = data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = None
                    break
        else:
            value = data.get(key)
        
        # 如果找到有效值，直接返回
        if value is not None and value != 0 and str(value).lower() not in ['nan', 'none', 'null', '']:
            return value
        
        # 如果没有找到值且启用计算，尝试智能计算
        if calculate_if_missing and value is None:
            calculated_value = self._calculate_missing_metric(data, key)
            if calculated_value is not None:
                return calculated_value
        
        return default
    
    def _calculate_missing_metric(self, data: dict, metric_key: str):
        """为缺失的指标计算估算值"""
        try:
            revenue = data.get('revenue') or data.get('total_revenue') or data.get('sales')
            net_income = data.get('net_income') or data.get('net_earnings')
            total_assets = data.get('total_assets') or data.get('total_asset')
            equity = data.get('shareholders_equity') or data.get('stockholders_equity')
            current_assets = data.get('current_assets')
            current_liabilities = data.get('current_liabilities')
            total_debt = data.get('total_debt') or data.get('debt')
            operating_income = data.get('operating_income') or data.get('operating_profit')
            
            # 根据指标类型进行计算
            if metric_key == 'roe' or metric_key == 'return_on_equity':
                if net_income and equity and equity > 0:
                    return net_income / equity
                    
            elif metric_key == 'roa' or metric_key == 'return_on_assets':
                if net_income and total_assets and total_assets > 0:
                    return net_income / total_assets
                    
            elif metric_key == 'current_ratio':
                if current_assets and current_liabilities and current_liabilities > 0:
                    return current_assets / current_liabilities
                    
            elif metric_key == 'debt_to_equity':
                if total_debt is not None and equity and equity > 0:
                    return total_debt / equity
                    
            elif metric_key == 'operating_margin':
                if operating_income and revenue and revenue > 0:
                    return operating_income / revenue
                elif net_income and revenue and revenue > 0:
                    # 估算：运营利润通常比净利润高20-30%
                    return (net_income * 1.25) / revenue
                    
            elif metric_key == 'net_margin' or metric_key == 'net_profit_margin':
                if net_income and revenue and revenue > 0:
                    return net_income / revenue
                    
            elif metric_key == 'gross_margin':
                # 如果没有毛利率，尝试从行业平均值估算
                if revenue and revenue > 0:
                    # 根据净利润率估算毛利率（通常为净利润率的2-4倍）
                    if net_income:
                        net_margin = net_income / revenue
                        if net_margin > 0:
                            return min(net_margin * 3, 0.6)  # 最高60%
                        
            elif metric_key == 'asset_turnover':
                if revenue and total_assets and total_assets > 0:
                    return revenue / total_assets
                    
            elif metric_key == 'free_cash_flow':
                # 如果没有FCF，用净利润的80%估算（保守估计）
                if net_income and net_income > 0:
                    return net_income * 0.8
                    
            elif metric_key == 'pe_ratio' or metric_key == 'price_to_earnings':
                market_cap = data.get('market_cap')
                if market_cap and net_income and net_income > 0:
                    return market_cap / net_income
                    
            elif metric_key == 'price_to_book':
                market_cap = data.get('market_cap')
                if market_cap and equity and equity > 0:
                    return market_cap / equity
                    
        except Exception as e:
            logger.debug(f"计算 {metric_key} 时出错: {e}")
            
        return None

    def get_all_data(self, ticker: str, prefetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取所有可用数据，包括增强数据和原始数据
        
        Args:
            ticker: 股票代码
            prefetched_data: 预获取的数据
            
        Returns:
            包含所有数据的字典
        """
        try:
            # 获取综合数据
            comprehensive_data = self.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
            
            # 获取增强数据
            enhanced_data = self.get_enhanced_data(ticker, prefetched_data)
            
            # 合并数据
            all_data = {
                'enhanced_data': enhanced_data,
                'financial_metrics': comprehensive_data.get('financial_metrics', []),
                'line_items': comprehensive_data.get('line_items', []),
                'market_cap': comprehensive_data.get('market_cap'),
                'company_news': comprehensive_data.get('company_news', []),
                'prices': comprehensive_data.get('prices', []),
                'akshare_comprehensive_data': comprehensive_data.get('akshare_comprehensive_data', {}),
                'validated_financial_data': comprehensive_data.get('validated_financial_data', {}),
                'macro_economic_data': comprehensive_data.get('macro_economic_data', {})
            }
            
            return all_data
            
        except Exception as e:
            logger.error(f"获取 {ticker} 所有数据失败: {e}")
            return {}
    
    def get_financial_metrics(self, ticker: str, prefetched_data: Dict[str, Any]) -> List[Any]:
        """获取财务指标"""
        return self.data_prefetcher.get_financial_metrics_from_cache(ticker, prefetched_data)
    
    def get_line_items(self, ticker: str, prefetched_data: Dict[str, Any], items: List[str] = None) -> List[Any]:
        """获取财务报表项目"""
        return self.data_prefetcher.get_line_items_from_cache(ticker, prefetched_data, items)
    
    def get_market_cap(self, ticker: str, prefetched_data: Dict[str, Any]) -> Optional[float]:
        """获取市值"""
        return self.data_prefetcher.get_market_cap_from_cache(ticker, prefetched_data)
    
    def get_company_news(self, ticker: str, prefetched_data: Dict[str, Any]) -> List[Any]:
        """获取公司新闻"""
        return self.data_prefetcher.get_company_news_from_cache(ticker, prefetched_data)
    
    def get_prices(self, ticker: str, prefetched_data: Dict[str, Any]) -> List[Any]:
        """获取价格数据"""
        return self.data_prefetcher.get_prices_from_cache(ticker, prefetched_data)
    
    def get_macro_economic_data(self, ticker: str, prefetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取宏观经济数据"""
        return self.data_prefetcher.get_macro_economic_data_from_cache(ticker, prefetched_data)
    
    def get_akshare_comprehensive_data(self, ticker: str, prefetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取AKShare综合财务数据"""
        return self.data_prefetcher.get_akshare_comprehensive_data_from_cache(ticker, prefetched_data)
    
    def get_validated_financial_data(self, ticker: str, prefetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取验证和修复后的财务数据"""
        return self.data_prefetcher.get_validated_financial_data_from_cache(ticker, prefetched_data)


# 创建全局实例
unified_data_accessor = UnifiedDataAccessor()