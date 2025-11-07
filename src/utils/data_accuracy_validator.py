#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据准确性验证模块
用于验证计算得出的增强数据的准确性，删除偏差超过30%的数据
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import math

logger = logging.getLogger(__name__)

class DataAccuracyValidator:
    """数据准确性验证器"""
    
    def __init__(self, max_deviation_threshold: float = 0.30):
        """
        初始化验证器
        Args:
            max_deviation_threshold: 最大允许偏差阈值（默认30%）
        """
        self.max_deviation_threshold = max_deviation_threshold
        self.validation_results = {}
    
    def validate_enhanced_data(self, raw_data: Dict[str, Any], enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证增强数据的准确性
        Args:
            raw_data: 原始真实数据
            enhanced_data: 增强/计算后的数据
        Returns:
            验证后的清理数据
        """
        logger.info("开始验证增强数据准确性...")
        
        validated_data = enhanced_data.copy()
        removed_fields = []
        validation_summary = {
            'total_fields': 0,
            'validated_fields': 0,
            'removed_fields': 0,
            'deviation_details': {}
        }
        
        # 验证财务比率
        validated_data, ratio_results = self._validate_financial_ratios(raw_data, validated_data)
        removed_fields.extend(ratio_results['removed'])
        validation_summary['deviation_details'].update(ratio_results['details'])
        
        # 验证增长率
        validated_data, growth_results = self._validate_growth_rates(raw_data, validated_data)
        removed_fields.extend(growth_results['removed'])
        validation_summary['deviation_details'].update(growth_results['details'])
        
        # 验证估值指标
        validated_data, valuation_results = self._validate_valuation_metrics(raw_data, validated_data)
        removed_fields.extend(valuation_results['removed'])
        validation_summary['deviation_details'].update(valuation_results['details'])
        
        # 更新统计信息
        validation_summary['total_fields'] = len(enhanced_data)
        validation_summary['removed_fields'] = len(removed_fields)
        validation_summary['validated_fields'] = validation_summary['total_fields'] - validation_summary['removed_fields']
        
        # 记录验证结果
        if removed_fields:
            logger.warning(f"移除了 {len(removed_fields)} 个偏差过大的字段: {removed_fields}")
        else:
            logger.info("所有增强数据都通过了准确性验证")
        
        # 添加验证元数据
        validated_data['_validation_meta'] = validation_summary
        
        return validated_data
    
    def _validate_financial_ratios(self, raw_data: Dict, enhanced_data: Dict) -> Tuple[Dict, Dict]:
        """验证财务比率类数据"""
        cleaned_data = enhanced_data.copy()
        removed_fields = []
        deviation_details = {}
        
        # 验证利润率相关比率
        margin_ratios = [
            ('gross_margin', 'gross_profit', 'revenue'),
            ('operating_margin', 'operating_income', 'revenue'),
            ('net_profit_margin', 'net_income', 'revenue')
        ]
        
        for ratio_name, numerator, denominator in margin_ratios:
            if ratio_name in enhanced_data:
                deviation = self._calculate_ratio_deviation(
                    raw_data, enhanced_data, ratio_name, numerator, denominator
                )
                if deviation is not None:
                    deviation_details[ratio_name] = deviation
                    if deviation > self.max_deviation_threshold:
                        cleaned_data.pop(ratio_name, None)
                        removed_fields.append(ratio_name)
        
        # 验证财务健康比率
        health_ratios = [
            ('current_ratio', 'current_assets', 'current_liabilities'),
            ('debt_to_equity', 'total_debt', 'total_equity'),
            ('asset_turnover', 'revenue', 'total_assets')
        ]
        
        for ratio_name, numerator, denominator in health_ratios:
            if ratio_name in enhanced_data:
                deviation = self._calculate_ratio_deviation(
                    raw_data, enhanced_data, ratio_name, numerator, denominator
                )
                if deviation is not None:
                    deviation_details[ratio_name] = deviation
                    if deviation > self.max_deviation_threshold:
                        cleaned_data.pop(ratio_name, None)
                        removed_fields.append(ratio_name)
        
        return cleaned_data, {'removed': removed_fields, 'details': deviation_details}
    
    def _validate_growth_rates(self, raw_data: Dict, enhanced_data: Dict) -> Tuple[Dict, Dict]:
        """验证增长率数据"""
        cleaned_data = enhanced_data.copy()
        removed_fields = []
        deviation_details = {}
        
        # 获取历史数据进行增长率验证
        growth_fields = [
            'revenue_growth_rate', 'eps_growth_rate', 'dividend_growth_rate',
            'operating_income_growth_rate', 'total_assets_growth_rate'
        ]
        
        for field in growth_fields:
            if field in enhanced_data:
                # 检查增长率是否合理（简化验证）
                growth_rate = enhanced_data[field]
                if isinstance(growth_rate, (int, float)):
                    # 增长率超过1000%或低于-90%被认为不合理
                    if abs(growth_rate) > 10.0 or growth_rate < -0.9:
                        deviation_details[field] = abs(growth_rate)
                        cleaned_data.pop(field, None)
                        removed_fields.append(field)
                        logger.warning(f"移除不合理的增长率 {field}: {growth_rate}")
        
        return cleaned_data, {'removed': removed_fields, 'details': deviation_details}
    
    def _validate_valuation_metrics(self, raw_data: Dict, enhanced_data: Dict) -> Tuple[Dict, Dict]:
        """验证估值指标数据"""
        cleaned_data = enhanced_data.copy()
        removed_fields = []
        deviation_details = {}
        
        # 验证市盈率相关指标
        pe_validation = self._validate_pe_ratio(raw_data, enhanced_data)
        if pe_validation['should_remove']:
            cleaned_data.pop('pe_ratio', None)
            removed_fields.append('pe_ratio')
            deviation_details['pe_ratio'] = pe_validation['deviation']
        
        # 验证市净率
        pb_validation = self._validate_pb_ratio(raw_data, enhanced_data)
        if pb_validation['should_remove']:
            cleaned_data.pop('pb_ratio', None)
            removed_fields.append('pb_ratio')
            deviation_details['pb_ratio'] = pb_validation['deviation']
        
        # 验证ROE/ROA
        roe_validation = self._validate_roe(raw_data, enhanced_data)
        if roe_validation['should_remove']:
            cleaned_data.pop('roe', None)
            removed_fields.append('roe')
            deviation_details['roe'] = roe_validation['deviation']
        
        return cleaned_data, {'removed': removed_fields, 'details': deviation_details}
    
    def _calculate_ratio_deviation(self, raw_data: Dict, enhanced_data: Dict, 
                                 ratio_name: str, numerator: str, denominator: str) -> Optional[float]:
        """计算比率的偏差"""
        try:
            # 从原始数据计算真实比率
            num_val = self._safe_get_numeric(raw_data, numerator)
            den_val = self._safe_get_numeric(raw_data, denominator)
            
            if num_val is None or den_val is None or den_val == 0:
                return None
            
            true_ratio = num_val / den_val
            enhanced_ratio = enhanced_data.get(ratio_name)
            
            if enhanced_ratio is None or true_ratio == 0:
                return None
            
            # 计算相对偏差
            deviation = abs(enhanced_ratio - true_ratio) / abs(true_ratio)
            return deviation
            
        except Exception as e:
            logger.warning(f"计算 {ratio_name} 偏差时出错: {e}")
            return None
    
    def _validate_pe_ratio(self, raw_data: Dict, enhanced_data: Dict) -> Dict:
        """验证市盈率"""
        try:
            price = self._safe_get_numeric(raw_data, 'current_price') or self._safe_get_numeric(raw_data, 'price')
            eps = self._safe_get_numeric(raw_data, 'earnings_per_share') or self._safe_get_numeric(raw_data, 'eps')
            enhanced_pe = enhanced_data.get('pe_ratio')
            
            if price and eps and eps > 0 and enhanced_pe:
                true_pe = price / eps
                deviation = abs(enhanced_pe - true_pe) / true_pe
                return {
                    'should_remove': deviation > self.max_deviation_threshold,
                    'deviation': deviation
                }
        except Exception:
            pass
        
        # 检查PE是否在合理范围内（0-100），将上限从1000降低到100
        if enhanced_data.get('pe_ratio'):
            pe_value = enhanced_data['pe_ratio']
            if pe_value < 0 or pe_value > 100:
                logger.warning(f"移除异常PE比率: {pe_value}")
                return {'should_remove': True, 'deviation': 999}
        
        return {'should_remove': False, 'deviation': 0}
    
    def _validate_pb_ratio(self, raw_data: Dict, enhanced_data: Dict) -> Dict:
        """验证市净率"""
        try:
            price = self._safe_get_numeric(raw_data, 'current_price') or self._safe_get_numeric(raw_data, 'price')
            bvps = self._safe_get_numeric(raw_data, 'book_value_per_share')
            enhanced_pb = enhanced_data.get('pb_ratio')
            
            if price and bvps and bvps > 0 and enhanced_pb:
                true_pb = price / bvps
                deviation = abs(enhanced_pb - true_pb) / true_pb
                return {
                    'should_remove': deviation > self.max_deviation_threshold,
                    'deviation': deviation
                }
        except Exception:
            pass
        
        # 检查PB是否在合理范围内（0-50）
        if enhanced_data.get('pb_ratio'):
            pb_value = enhanced_data['pb_ratio']
            if pb_value < 0 or pb_value > 50:
                return {'should_remove': True, 'deviation': 999}
        
        return {'should_remove': False, 'deviation': 0}
    
    def _validate_roe(self, raw_data: Dict, enhanced_data: Dict) -> Dict:
        """验证ROE"""
        try:
            net_income = self._safe_get_numeric(raw_data, 'net_income')
            equity = self._safe_get_numeric(raw_data, 'total_equity') or self._safe_get_numeric(raw_data, 'shareholders_equity')
            enhanced_roe = enhanced_data.get('roe')
            
            if net_income is not None and equity and equity > 0 and enhanced_roe is not None:
                true_roe = net_income / equity
                deviation = abs(enhanced_roe - true_roe) / abs(true_roe) if true_roe != 0 else 999
                return {
                    'should_remove': deviation > self.max_deviation_threshold,
                    'deviation': deviation
                }
        except Exception:
            pass
        
        # 检查ROE是否在合理范围内（-100% to 100%）
        if enhanced_data.get('roe'):
            roe_value = enhanced_data['roe']
            if abs(roe_value) > 1.0:  # 100%
                return {'should_remove': True, 'deviation': 999}
        
        return {'should_remove': False, 'deviation': 0}
    
    def _safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """安全获取数值"""
        value = data.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return self.validation_results.copy()

# 全局实例
data_accuracy_validator = DataAccuracyValidator()