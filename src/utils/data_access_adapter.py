"""
数据访问适配器模块
提供数据标准化、访问接口等功能
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataAccessAdapter:
    """数据访问适配器，用于标准化和访问财务数据"""
    
    def __init__(self):
        # 字段名映射：中文字段名 -> 英文标准字段名
        self.field_mapping = {
            # 基础财务数据
            '营业收入': 'revenue',
            '总营业收入': 'revenue', 
            'total_revenue': 'revenue',
            '净利润': 'net_income',
            '归母净利润': 'net_income',
            'net_earnings': 'net_income',
            '总资产': 'total_assets',
            '资产总计': 'total_assets',
            'total_asset': 'total_assets',
            '负债总计': 'total_liabilities',
            '负债合计': 'total_liabilities',
            'total_liability': 'total_liabilities',
            '股东权益合计': 'shareholders_equity',
            '所有者权益': 'shareholders_equity',
            'stockholders_equity': 'shareholders_equity',
            '流动资产合计': 'current_assets',
            'current_asset': 'current_assets',
            '流动负债合计': 'current_liabilities',
            'current_liability': 'current_liabilities',
            '货币资金': 'cash_and_cash_equivalents',
            'cash': 'cash_and_cash_equivalents',
            'cash_and_equivalents': 'cash_and_cash_equivalents',
            
            # 现金流数据
            '经营活动产生的现金流量净额': 'operating_cash_flow',
            'operating_cash_flows': 'operating_cash_flow',
            '投资活动产生的现金流量净额': 'investing_cash_flow',
            '筹资活动产生的现金流量净额': 'financing_cash_flow',
            '自由现金流': 'free_cash_flow',
            
            # 利润表数据
            '营业利润': 'operating_income',
            'operating_profit': 'operating_income',
            '毛利润': 'gross_profit',
            'gross_income': 'gross_profit',
            'ebit': 'operating_income',
            'ebitda': 'ebitda',
            
            # 股本数据
            '流通股数': 'shares_outstanding',
            'outstanding_shares': 'shares_outstanding',
            '总股本': 'total_shares',
            
            # 市场数据
            '总市值': 'market_cap',
            '流通市值': 'circulating_market_cap',
            '市盈率': 'pe_ratio',
            'price_to_earnings': 'pe_ratio',
            '市净率': 'pb_ratio',
            'price_to_book': 'pb_ratio',
            '市销率': 'ps_ratio',
            'price_to_sales': 'ps_ratio',
            
            # 财务比率
            '资产负债率': 'debt_to_assets',
            '流动比率': 'current_ratio',
            '速动比率': 'quick_ratio',
            '净资产收益率': 'roe',
            'return_on_equity': 'roe',
            '总资产收益率': 'roa',
            'return_on_assets': 'roa',
            '投入资本回报率': 'roic',
            'return_on_invested_capital': 'roic',
            '毛利率': 'gross_margin',
            '营业利润率': 'operating_margin',
            '净利率': 'net_margin',
            '净利润率': 'net_margin',
            
            # 其他指标
            '研发费用': 'research_and_development',
            'rd_expense': 'research_and_development',
            '存货': 'inventory',
            'inventories': 'inventory',
            '商誉': 'goodwill',
            '无形资产': 'intangible_assets',
            '折旧': 'depreciation',
            'depreciation_and_amortization': 'depreciation',
        }
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化数据字段名"""
        if not data:
            return {}
        
        normalized = {}
        
        for key, value in data.items():
            # 获取标准化的字段名
            standard_key = self.field_mapping.get(key, key)
            
            # 如果值不为空且有效
            if value is not None and str(value).lower() not in ['nan', 'none', 'null', '']:
                try:
                    # 尝试转换为数值类型
                    if isinstance(value, str) and value.replace('.', '').replace('-', '').replace('+', '').isdigit():
                        normalized[standard_key] = float(value)
                    elif isinstance(value, (int, float)):
                        normalized[standard_key] = float(value)
                    else:
                        normalized[standard_key] = value
                except (ValueError, TypeError):
                    normalized[standard_key] = value
        
        return normalized
    
    def safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """安全获取数据，支持字段名映射"""
        # 直接查找
        if key in data:
            return data[key]
        
        # 查找映射的字段名
        for original_key, standard_key in self.field_mapping.items():
            if standard_key == key and original_key in data:
                return data[original_key]
        
        return default

class EnhancedDataAccessor:
    """增强的数据访问器，提供更智能的数据访问"""
    
    def __init__(self, financial_data: Dict[str, Any]):
        self.data = financial_data or {}
        self.adapter = DataAccessAdapter()
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取数据，支持计算和估算"""
        value = self.adapter.safe_get(self.data, key, None)
        
        if value is not None:
            return value
        
        # 尝试计算缺失的指标
        calculated = self._calculate_metric(key)
        if calculated is not None:
            return calculated
        
        return default
    
    def _calculate_metric(self, metric_key: str) -> Optional[float]:
        """计算缺失的财务指标"""
        try:
            revenue = self.adapter.safe_get(self.data, 'revenue')
            net_income = self.adapter.safe_get(self.data, 'net_income')
            total_assets = self.adapter.safe_get(self.data, 'total_assets')
            shareholders_equity = self.adapter.safe_get(self.data, 'shareholders_equity')
            current_assets = self.adapter.safe_get(self.data, 'current_assets')
            current_liabilities = self.adapter.safe_get(self.data, 'current_liabilities')
            
            # 计算不同的财务指标
            if metric_key == 'roe' and net_income and shareholders_equity and shareholders_equity > 0:
                return net_income / shareholders_equity
            
            elif metric_key == 'roa' and net_income and total_assets and total_assets > 0:
                return net_income / total_assets
            
            elif metric_key == 'current_ratio' and current_assets and current_liabilities and current_liabilities > 0:
                return current_assets / current_liabilities
            
            elif metric_key == 'net_margin' and net_income and revenue and revenue > 0:
                return net_income / revenue
            
            elif metric_key == 'debt_to_equity':
                total_liabilities = self.adapter.safe_get(self.data, 'total_liabilities')
                if total_liabilities and shareholders_equity and shareholders_equity > 0:
                    return total_liabilities / shareholders_equity
            
            # 如果无法计算，返回None
            return None
            
        except Exception as e:
            logger.debug(f"计算 {metric_key} 失败: {e}")
            return None

def create_enhanced_accessor(financial_data: Dict[str, Any]) -> EnhancedDataAccessor:
    """创建增强数据访问器的工厂函数"""
    return EnhancedDataAccessor(financial_data)

# 创建全局实例
data_access_adapter = DataAccessAdapter() 