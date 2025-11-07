#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本过滤器 - 用于过滤分析师评语中的异常数字
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TextFilter:
    """文本过滤器，用于处理分析师评语中的异常数字"""
    
    def __init__(self):
        # 定义异常数字的阈值
        self.pe_max_threshold = 100  # PE比率最大合理值
        self.pb_max_threshold = 50   # PB比率最大合理值
        self.general_max_threshold = 1000  # 一般数字最大合理值
        
        # 定义需要特殊处理的财务指标模式
        self.financial_patterns = {
            'pe': r'P/E[\s=:：]*([0-9]+(?:\.[0-9]+)?)',
            'pb': r'P/B[\s=:：]*([0-9]+(?:\.[0-9]+)?)',
            'roe': r'ROE[\s=:：]*([0-9]+(?:\.[0-9]+)?)%?',
            'roa': r'ROA[\s=:：]*([0-9]+(?:\.[0-9]+)?)%?',
            'margin': r'利润率[\s=:：]*([0-9]+(?:\.[0-9]+)?)%?',
            'growth': r'增长率[\s=:：]*([0-9]+(?:\.[0-9]+)?)%?'
        }
    
    def filter_abnormal_numbers(self, text: str) -> str:
        """过滤文本中的异常数字，保持文字通顺"""
        if not text:
            return text
            
        filtered_text = text
        
        # 处理PE比率异常值
        filtered_text = self._filter_pe_ratio(filtered_text)
        
        # 处理PB比率异常值
        filtered_text = self._filter_pb_ratio(filtered_text)
        
        # 处理其他异常大数字
        filtered_text = self._filter_large_numbers(filtered_text)
        
        # 清理多余的空格和标点
        filtered_text = self._clean_text(filtered_text)
        
        return filtered_text
    
    def _filter_pe_ratio(self, text: str) -> str:
        """过滤PE比率异常值"""
        pattern = self.financial_patterns['pe']
        
        def replace_abnormal_pe(match):
            pe_value = float(match.group(1))
            if pe_value > self.pe_max_threshold:
                logger.warning(f"过滤异常PE值: {pe_value}")
                return "P/E较高"
            return match.group(0)
        
        return re.sub(pattern, replace_abnormal_pe, text, flags=re.IGNORECASE)
    
    def _filter_pb_ratio(self, text: str) -> str:
        """过滤PB比率异常值"""
        pattern = self.financial_patterns['pb']
        
        def replace_abnormal_pb(match):
            pb_value = float(match.group(1))
            if pb_value > self.pb_max_threshold:
                logger.warning(f"过滤异常PB值: {pb_value}")
                return "P/B较高"
            return match.group(0)
        
        return re.sub(pattern, replace_abnormal_pb, text, flags=re.IGNORECASE)
    
    def _filter_large_numbers(self, text: str) -> str:
        """过滤其他异常大数字"""
        # 匹配独立的大数字（不在财务比率中）
        pattern = r'(?<!P/E[\s=:：])(?<!P/B[\s=:：])(?<!ROE[\s=:：])(?<!ROA[\s=:：])\b([0-9]{4,})(?:\.[0-9]+)?\b'
        
        def replace_large_number(match):
            number = float(match.group(1))
            if number > self.general_max_threshold:
                logger.warning(f"过滤异常大数字: {number}")
                return "数值较大"
            return match.group(0)
        
        return re.sub(pattern, replace_large_number, text)
    
    def _clean_text(self, text: str) -> str:
        """清理文本，确保通顺"""
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        # 修复标点符号前的空格
        text = re.sub(r'\s+([，。；：！？])', r'\1', text)
        
        # 修复连续的标点符号
        text = re.sub(r'([，。；：])\s*\1+', r'\1', text)
        
        # 移除开头和结尾的空格
        text = text.strip()
        
        return text
    
    def validate_financial_metrics(self, metrics: dict) -> dict:
        """验证财务指标数据，移除异常值"""
        cleaned_metrics = metrics.copy()
        
        # 验证PE比率
        if 'pe_ratio' in cleaned_metrics:
            pe_value = cleaned_metrics['pe_ratio']
            if isinstance(pe_value, (int, float)) and pe_value > self.pe_max_threshold:
                logger.warning(f"移除异常PE比率: {pe_value}")
                del cleaned_metrics['pe_ratio']
        
        # 验证PB比率
        if 'pb_ratio' in cleaned_metrics:
            pb_value = cleaned_metrics['pb_ratio']
            if isinstance(pb_value, (int, float)) and pb_value > self.pb_max_threshold:
                logger.warning(f"移除异常PB比率: {pb_value}")
                del cleaned_metrics['pb_ratio']
        
        # 验证其他比率
        ratio_fields = ['roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin']
        for field in ratio_fields:
            if field in cleaned_metrics:
                value = cleaned_metrics[field]
                if isinstance(value, (int, float)) and abs(value) > 1.0:  # 超过100%
                    logger.warning(f"移除异常{field}: {value}")
                    del cleaned_metrics[field]
        
        return cleaned_metrics

# 全局实例
text_filter = TextFilter()