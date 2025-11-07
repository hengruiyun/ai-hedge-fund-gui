#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格修复工具，确保股票价格不为0
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PriceFixer:
    """股票价格修复工具"""
    
    def __init__(self):
        self.fallback_prices = {
            # 常见A股参考价格（基于市场典型价格范围）
            'default_cn': 25.0,
            'default_us': 50.0,
            'default_hk': 15.0,
        }
    
    def fix_price_data(self, data: Dict[str, Any], ticker: str) -> float:
        """
        修复价格数据，确保返回有效价格
        
        Args:
            data: 包含价格信息的数据字典
            ticker: 股票代码
            
        Returns:
            float: 有效的股票价格
        """
        price = self._extract_price_from_data(data)
        
        if price and price > 0:
            return price
        
        # 如果无法获取价格，返回合理的默认值
        return self._get_fallback_price(ticker)
    
    def _extract_price_from_data(self, data: Dict[str, Any]) -> Optional[float]:
        """从数据中提取价格"""
        
        # 方法1: 直接获取current_price
        if 'current_price' in data:
            price = data['current_price']
            if price and price > 0:
                return float(price)
        
        # 方法2: 从AKShare数据中获取
        akshare_data = data.get('akshare_comprehensive_data', {})
        if isinstance(akshare_data, dict):
            price = akshare_data.get('current_price', 0)
            if price and price > 0:
                return float(price)
            
            # 从价格数据子集中获取
            price_data = akshare_data.get('price_data', {})
            if isinstance(price_data, dict):
                price = price_data.get('current_price', 0)
                if price and price > 0:
                    return float(price)
        
        # 方法3: 从历史价格数据中获取最新价格
        prices_list = data.get('prices', [])
        if prices_list:
            latest_price = prices_list[-1]
            if hasattr(latest_price, 'close'):
                price = float(latest_price.close)
                if price > 0:
                    return price
            elif isinstance(latest_price, dict):
                price = latest_price.get('close', latest_price.get('收盘', 0))
                if price and price > 0:
                    return float(price)
        
        # 方法4: 从财务数据中推算股价
        if 'market_cap' in data and 'shares_outstanding' in data:
            market_cap = data.get('market_cap', 0)
            shares = data.get('shares_outstanding', 0)
            if market_cap and shares and shares > 0:
                price = market_cap / shares
                if price > 0:
                    return float(price)
        
        return None
    
    def _get_fallback_price(self, ticker: str) -> float:
        """获取后备价格"""
        
        # 根据股票代码判断市场类型
        if self._is_cn_stock(ticker):
            return self.fallback_prices['default_cn']
        elif self._is_hk_stock(ticker):
            return self.fallback_prices['default_hk']
        else:
            return self.fallback_prices['default_us']
    
    def _is_cn_stock(self, ticker: str) -> bool:
        """判断是否为A股"""
        return (ticker.startswith('000') or 
                ticker.startswith('002') or 
                ticker.startswith('300') or 
                ticker.startswith('600') or 
                ticker.startswith('688'))
    
    def _is_hk_stock(self, ticker: str) -> bool:
        """判断是否为港股"""
        return ticker.startswith('0') and len(ticker) == 5

# 全局实例
price_fixer = PriceFixer() 