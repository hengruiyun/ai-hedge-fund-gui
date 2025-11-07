# -*- coding: utf-8 -*-
"""
数据质量修复模块

解决分析师算法中的数据质量问题，包括：
1. 数据验证和清洗
2. 缺失数据处理
3. 异常值检测和修正
4. 数据一致性检查
5. 错误处理和重试机制
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-89%
    FAIR = "fair"           # 50-69%
    POOR = "poor"           # 30-49%
    CRITICAL = "critical"   # 0-29%


@dataclass
class DataQualityReport:
    """数据质量报告"""
    ticker: str
    overall_score: float
    quality_level: DataQualityLevel
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    missing_fields: List[str]
    invalid_fields: List[str]
    warnings: List[str]
    recommendations: List[str]


class DataQualityFixer:
    """数据质量修复器"""
    
    def __init__(self):
        self.required_fields = {
            'financial_metrics': [
                'revenue', 'net_income', 'operating_income', 'total_assets',
                'shareholders_equity', 'operating_cash_flow'
            ],
            'line_items': [
                'revenue', 'net_income', 'total_assets', 'shareholders_equity'
            ],
            'market_data': ['market_cap'],
            'price_data': ['close', 'volume'],
        }
        
        self.optional_fields = {
            'financial_metrics': [
                'gross_profit', 'ebitda', 'free_cash_flow', 'total_debt',
                'current_assets', 'current_liabilities'
            ],
            'calculated_metrics': [
                'enterprise_value', 'ev_to_ebitda', 'ev_to_sales',
                'price_to_book', 'price_to_sales', 'debt_to_equity_ratio'
            ]
        }
        
        # 数据范围验证规则
        self.validation_rules = {
            'revenue': {'min': 0, 'max': 1e12},
            'net_income': {'min': -1e11, 'max': 1e11},
            'market_cap': {'min': 1e6, 'max': 1e13},
            'total_assets': {'min': 0, 'max': 1e13},
            'shareholders_equity': {'min': -1e12, 'max': 1e12},
            'operating_cash_flow': {'min': -1e11, 'max': 1e11},
            'pe_ratio': {'min': 0, 'max': 1000},  # PE比率不能为负
            'pb_ratio': {'min': 0, 'max': 100},
            'debt_to_equity_ratio': {'min': 0, 'max': 10}  # 债务权益比超过10通常被认为过高
        }
    
    def validate_data_completeness(self, data: Dict[str, Any], data_type: str) -> Tuple[float, List[str]]:
        """验证数据完整性"""
        required = self.required_fields.get(data_type, [])
        if not required:
            return 1.0, []
        
        missing_fields = []
        valid_count = 0
        
        for field in required:
            value = data.get(field)
            if value is None or value == 0 or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
            else:
                valid_count += 1
        
        completeness_score = valid_count / len(required) if required else 1.0
        return completeness_score, missing_fields
    
    def validate_data_accuracy(self, data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证数据准确性"""
        invalid_fields = []
        valid_count = 0
        total_count = 0
        
        for field, value in data.items():
            if field in self.validation_rules:
                total_count += 1
                rules = self.validation_rules[field]
                
                try:
                    numeric_value = float(value)
                    if rules['min'] <= numeric_value <= rules['max']:
                        valid_count += 1
                    else:
                        invalid_fields.append(f"{field}: {value} (范围: {rules['min']}-{rules['max']})")
                except (ValueError, TypeError):
                    invalid_fields.append(f"{field}: {value} (非数值)")
        
        accuracy_score = valid_count / total_count if total_count > 0 else 1.0
        return accuracy_score, invalid_fields
    
    def validate_data_consistency(self, data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证数据一致性"""
        warnings = []
        consistency_score = 1.0
        
        # 检查财务比率一致性
        try:
            revenue = data.get('revenue', 0)
            net_income = data.get('net_income', 0)
            total_assets = data.get('total_assets', 0)
            shareholders_equity = data.get('shareholders_equity', 0)
            
            # 检查净利率
            if revenue > 0 and net_income > 0:
                calculated_margin = net_income / revenue
                reported_margin = data.get('net_margin', calculated_margin)
                if abs(calculated_margin - reported_margin) > 0.05:  # 5%容差
                    warnings.append(f"净利率不一致: 计算值{calculated_margin:.3f} vs 报告值{reported_margin:.3f}")
                    consistency_score -= 0.1
            
            # 检查ROE
            if shareholders_equity > 0 and net_income > 0:
                calculated_roe = net_income / shareholders_equity
                reported_roe = data.get('roe', calculated_roe)
                if abs(calculated_roe - reported_roe) > 0.05:
                    warnings.append(f"ROE不一致: 计算值{calculated_roe:.3f} vs 报告值{reported_roe:.3f}")
                    consistency_score -= 0.1
            
            # 检查ROA
            if total_assets > 0 and net_income > 0:
                calculated_roa = net_income / total_assets
                reported_roa = data.get('roa', calculated_roa)
                if abs(calculated_roa - reported_roa) > 0.05:
                    warnings.append(f"ROA不一致: 计算值{calculated_roa:.3f} vs 报告值{reported_roa:.3f}")
                    consistency_score -= 0.1
                    
        except Exception as e:
            warnings.append(f"一致性检查异常: {e}")
            consistency_score -= 0.2
        
        return max(consistency_score, 0.0), warnings
    
    def generate_quality_report(self, ticker: str, data: Dict[str, Any]) -> DataQualityReport:
        """生成数据质量报告"""
        # 验证完整性
        completeness_score, missing_fields = self.validate_data_completeness(data, 'financial_metrics')
        
        # 验证准确性
        accuracy_score, invalid_fields = self.validate_data_accuracy(data)
        
        # 验证一致性
        consistency_score, consistency_warnings = self.validate_data_consistency(data)
        
        # 计算总体评分
        overall_score = (completeness_score * 0.4 + accuracy_score * 0.3 + consistency_score * 0.3)
        
        # 确定质量等级
        if overall_score >= 0.9:
            quality_level = DataQualityLevel.EXCELLENT
        elif overall_score >= 0.7:
            quality_level = DataQualityLevel.GOOD
        elif overall_score >= 0.5:
            quality_level = DataQualityLevel.FAIR
        elif overall_score >= 0.3:
            quality_level = DataQualityLevel.POOR
        else:
            quality_level = DataQualityLevel.CRITICAL
        
        # 生成建议
        recommendations = []
        if completeness_score < 0.8:
            recommendations.append("建议补充缺失的关键财务指标")
        if accuracy_score < 0.8:
            recommendations.append("建议检查和修正异常数值")
        if consistency_score < 0.8:
            recommendations.append("建议验证财务比率的计算一致性")
        
        warnings = consistency_warnings.copy()
        if missing_fields:
            warnings.extend([f"缺失字段: {field}" for field in missing_fields[:3]])
        if invalid_fields:
            warnings.extend(invalid_fields[:3])
        
        return DataQualityReport(
            ticker=ticker,
            overall_score=overall_score,
            quality_level=quality_level,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def repair_data_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复数据质量问题"""
        repaired_data = data.copy()
        
        # 1. 修复异常值
        for field, value in repaired_data.items():
            if field in self.validation_rules and isinstance(value, (int, float)):
                rules = self.validation_rules[field]
                if value < rules['min']:
                    repaired_data[field] = rules['min']
                    logger.warning(f"修复 {field}: {value} -> {rules['min']} (低于最小值)")
                elif value > rules['max']:
                    repaired_data[field] = rules['max']
                    logger.warning(f"修复 {field}: {value} -> {rules['max']} (超过最大值)")
        
        # 2. 补充缺失的关键指标
        self._fill_missing_metrics(repaired_data)
        
        # 3. 修复不一致的比率
        self._fix_inconsistent_ratios(repaired_data)
        
        return repaired_data
    
    def _fill_missing_metrics(self, data: Dict[str, Any]) -> None:
        """填充缺失的关键指标"""
        # 计算缺失的财务比率
        revenue = data.get('revenue', 0)
        net_income = data.get('net_income', 0)
        total_assets = data.get('total_assets', 0)
        shareholders_equity = data.get('shareholders_equity', 0)
        
        # 计算净利率
        if revenue > 0 and net_income > 0 and 'net_margin' not in data:
            data['net_margin'] = net_income / revenue
        
        # 计算ROE
        if shareholders_equity > 0 and net_income > 0 and 'roe' not in data:
            data['roe'] = net_income / shareholders_equity
        
        # 计算ROA
        if total_assets > 0 and net_income > 0 and 'roa' not in data:
            data['roa'] = net_income / total_assets
        
        # 计算债务权益比
        total_debt = data.get('total_debt', 0)
        if shareholders_equity > 0 and total_debt > 0 and 'debt_to_equity_ratio' not in data:
            data['debt_to_equity_ratio'] = total_debt / shareholders_equity
    
    def _fix_inconsistent_ratios(self, data: Dict[str, Any]) -> None:
        """修复不一致的比率"""
        revenue = data.get('revenue', 0)
        net_income = data.get('net_income', 0)
        total_assets = data.get('total_assets', 0)
        shareholders_equity = data.get('shareholders_equity', 0)
        
        # 修复净利率
        if revenue > 0 and net_income > 0:
            calculated_margin = net_income / revenue
            reported_margin = data.get('net_margin', calculated_margin)
            if abs(calculated_margin - reported_margin) > 0.05:
                data['net_margin'] = calculated_margin
                logger.info(f"修复净利率: {reported_margin:.3f} -> {calculated_margin:.3f}")
        
        # 修复ROE
        if shareholders_equity > 0 and net_income > 0:
            calculated_roe = net_income / shareholders_equity
            reported_roe = data.get('roe', calculated_roe)
            if abs(calculated_roe - reported_roe) > 0.05:
                data['roe'] = calculated_roe
                logger.info(f"修复ROE: {reported_roe:.3f} -> {calculated_roe:.3f}")
        
        # 修复ROA
        if total_assets > 0 and net_income > 0:
            calculated_roa = net_income / total_assets
            reported_roa = data.get('roa', calculated_roa)
            if abs(calculated_roa - reported_roa) > 0.05:
                data['roa'] = calculated_roa
                logger.info(f"修复ROA: {reported_roa:.3f} -> {calculated_roa:.3f}")
                rules = self.validation_rules[field]
                
                try:
                    numeric_value = float(value)
                    if rules['min'] <= numeric_value <= rules['max']:
                        valid_count += 1
                    else:
                        invalid_fields.append(f"{field}: {value} (范围: {rules['min']}-{rules['max']})")
                except (ValueError, TypeError):
                    invalid_fields.append(f"{field}: {value} (无法转换为数字)")
        
        accuracy_score = valid_count / total_count if total_count > 0 else 1.0
        return accuracy_score, invalid_fields
    
    def validate_data_consistency(self, data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证数据一致性"""
        warnings = []
        consistency_issues = 0
        total_checks = 0
        
        # 检查基本财务关系
        revenue = data.get('revenue', 0)
        net_income = data.get('net_income', 0)
        total_assets = data.get('total_assets', 0)
        shareholders_equity = data.get('shareholders_equity', 0)
        total_liabilities = data.get('total_liabilities', 0)
        
        # 检查1: 净利润率是否合理
        if revenue > 0 and net_income != 0:
            total_checks += 1
            net_margin = net_income / revenue
            if abs(net_margin) > 1:  # 净利润率超过100%
                consistency_issues += 1
                warnings.append(f"净利润率异常: {net_margin:.2%}")
        
        # 检查2: 资产负债表平衡
        if total_assets > 0 and shareholders_equity != 0 and total_liabilities > 0:
            total_checks += 1
            balance_diff = abs(total_assets - (shareholders_equity + total_liabilities))
            if balance_diff / total_assets > 0.05:  # 差异超过5%
                consistency_issues += 1
                warnings.append(f"资产负债表不平衡，差异: {balance_diff:,.0f}")
        
        # 检查3: 市值与财务数据的合理性
        market_cap = data.get('market_cap', 0)
        if market_cap > 0 and revenue > 0:
            total_checks += 1
            ps_ratio = market_cap / revenue
            if ps_ratio > 100:  # 市销率过高
                consistency_issues += 1
                warnings.append(f"市销率异常高: {ps_ratio:.1f}")
        
        consistency_score = 1 - (consistency_issues / total_checks) if total_checks > 0 else 1.0
        return consistency_score, warnings
    
    def fix_invalid_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复无效数据"""
        fixed_data = data.copy()
        
        for field, value in list(fixed_data.items()):
            if field in self.validation_rules and value is not None:
                rules = self.validation_rules[field]
                
                try:
                    numeric_value = float(value)
                    if not (rules['min'] <= numeric_value <= rules['max']):
                        logger.warning(f"警告: 字段 {field} 的值 {value} 超出有效范围 [{rules['min']}-{rules['max']}]，已从数据中删除.")
                        del fixed_data[field]
                except (ValueError, TypeError):
                    logger.warning(f"警告: 字段 {field} 的值 {value} 无法转换为数字，已从数据中删除.")
                    del fixed_data[field]
        
        return fixed_data
    
    def fix_missing_data(self, data: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """修复缺失数据"""
        fixed_data = data.copy()
        
        # 使用财务计算器补充缺失的计算指标
        try:
            from src.utils.financial_calculations import financial_calculator
            enhanced_data = financial_calculator.enhance_financial_metrics(fixed_data)
            fixed_data.update(enhanced_data)
        except Exception as e:
            logger.warning(f"财务指标增强失败 {ticker}: {e}")
        
        # 特殊处理：如果缺少关键数据，尝试从其他字段推导
        self._derive_missing_fields(fixed_data)
        
        return fixed_data
    
    def _derive_missing_fields(self, data: Dict[str, Any]):
        """从现有数据推导缺失字段"""
        # 如果缺少总负债，尝试从总资产和股东权益计算
        if not data.get('total_liabilities'):
            total_assets = data.get('total_assets', 0)
            shareholders_equity = data.get('shareholders_equity', 0)
            if total_assets > 0 and shareholders_equity > 0:
                data['total_liabilities'] = total_assets - shareholders_equity
        
        # 如果缺少毛利润，尝试从收入和销售成本计算
        if not data.get('gross_profit'):
            revenue = data.get('revenue', 0)
            cost_of_revenue = data.get('cost_of_revenue', 0)
            if revenue > 0 and cost_of_revenue > 0:
                data['gross_profit'] = revenue - cost_of_revenue
        
        # 如果缺少每股收益，尝试从净利润和流通股数计算
        if not data.get('earnings_per_share'):
            net_income = data.get('net_income', 0)
            shares_outstanding = data.get('shares_outstanding', 0)
            if net_income != 0 and shares_outstanding > 0:
                data['earnings_per_share'] = net_income / shares_outstanding


# 全局数据质量修复器实例
data_quality_fixer = DataQualityFixer()