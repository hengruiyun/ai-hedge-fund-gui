"""
数据分析规则模块
为所有分析师代理定义统一的分析规则和数据完整性评估标准
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_data_completeness_score(data: Dict[str, Any], required_metrics: list) -> tuple[int, int, float]:
    """
    计算数据完整性评分
    
    Args:
        data: 财务数据字典
        required_metrics: 必需的指标列表
        
    Returns:
        tuple: (可用指标数量, 总指标数量, 完整性百分比)
    """
    if not data or not required_metrics:
        return 0, len(required_metrics) if required_metrics else 0, 0.0
    
    available_count = 0
    total_count = len(required_metrics)
    
    for metric in required_metrics:
        value = data.get(metric)
        if value is not None and value != 0 and str(value).lower() not in ['nan', 'none', 'null', '']:
            available_count += 1
    
    completeness_percentage = (available_count / total_count * 100) if total_count > 0 else 0
    
    return available_count, total_count, completeness_percentage

def standardize_data_analysis_approach(data: Dict[str, Any], analyst_name: str, required_metrics: list) -> Dict[str, Any]:
    """
    标准化数据分析方法 - 核心规则：基于现有数据进行分析，现有数据就是100%
    
    Args:
        data: 财务数据
        analyst_name: 分析师名称
        required_metrics: 该分析师需要的指标列表
        
    Returns:
        包含分析规则和数据评估的字典
    """
    available_count, total_count, completeness_percentage = calculate_data_completeness_score(data, required_metrics)
    
    # 核心规则：现有数据就是我们的全部数据，基于此进行分析
    analysis_context = {
        'available_metrics': available_count,
        'total_expected_metrics': total_count,
        'data_completeness_percentage': completeness_percentage,
        'analysis_approach': 'comprehensive_with_available_data',
        'analysis_rules': {
            'rule_1': '基于现有数据进行分析，不因数据不完整而降低分析质量',
            'rule_2': '现有的财务数据代表100%的可用信息，充分利用',
            'rule_3': '通过可用数据推断和计算缺失指标，提供完整分析',
            'rule_4': '重点分析数据充足的维度，对数据有限的维度给出合理推断',
            'rule_5': '提供专业的投资建议，不因数据限制而回避决策'
        },
        'confidence_factors': {
            'high_confidence_threshold': 0.7,  # 70%以上数据可用时高置信度
            'medium_confidence_threshold': 0.4,  # 40%-70%数据可用时中等置信度
            'low_confidence_threshold': 0.2,   # 20%-40%数据可用时低置信度但仍需分析
            'minimum_analysis_threshold': 0.1  # 10%以上数据即可进行基础分析
        }
    }
    
    # 根据数据完整性调整分析策略
    if completeness_percentage >= 70:
        analysis_context['analysis_strategy'] = 'comprehensive_analysis'
        analysis_context['confidence_level'] = 'high'
        analysis_context['analysis_note'] = f'{analyst_name}拥有充足数据({completeness_percentage:.1f}%)，可进行全面深入分析'
    elif completeness_percentage >= 40:
        analysis_context['analysis_strategy'] = 'focused_analysis_with_inference'
        analysis_context['confidence_level'] = 'medium'
        analysis_context['analysis_note'] = f'{analyst_name}拥有适度数据({completeness_percentage:.1f}%)，重点分析核心指标并合理推断'
    elif completeness_percentage >= 20:
        analysis_context['analysis_strategy'] = 'core_analysis_with_estimation'
        analysis_context['confidence_level'] = 'medium_low'
        analysis_context['analysis_note'] = f'{analyst_name}基于核心数据({completeness_percentage:.1f}%)进行专业分析和估算'
    else:
        analysis_context['analysis_strategy'] = 'fundamental_analysis_with_assumptions'
        analysis_context['confidence_level'] = 'cautious_but_analytical'
        analysis_context['analysis_note'] = f'{analyst_name}基于有限数据({completeness_percentage:.1f}%)进行基础分析，结合经验判断'
    
    return analysis_context

def get_analysis_scoring_adjustment(data_context: Dict[str, Any]) -> Dict[str, float]:
    """
    获取基于数据完整性的评分调整策略
    确保评分反映分析师的专业判断，而非简单的数据缺失惩罚
    """
    completeness = data_context.get('data_completeness_percentage', 0)
    
    if completeness >= 70:
        # 高数据完整性：正常评分范围
        return {
            'min_score': 2.0,  # 最低2分，避免过低评分
            'max_score': 10.0, # 最高10分
            'score_multiplier': 1.0,
            'confidence_boost': 0.1
        }
    elif completeness >= 40:
        # 中等数据完整性：轻微调整
        return {
            'min_score': 3.0,  # 最低3分
            'max_score': 9.0,  # 最高9分
            'score_multiplier': 0.95,
            'confidence_boost': 0.0
        }
    elif completeness >= 20:
        # 较低数据完整性：保持分析深度
        return {
            'min_score': 4.0,  # 最低4分
            'max_score': 8.5,  # 最高8.5分
            'score_multiplier': 0.9,
            'confidence_boost': -0.1
        }
    else:
        # 很低数据完整性：谨慎但专业，仍给出合理评分
        return {
            'min_score': 5.0,  # 最低5分，确保合理评分
            'max_score': 8.0,  # 最高8分
            'score_multiplier': 0.85,
            'confidence_boost': -0.2
        }

def ensure_reasonable_score(score: float, min_score: float = 3.0) -> float:
    """
    确保评分在合理范围内，避免0分或过低评分
    
    Args:
        score: 原始评分
        min_score: 最低评分阈值
        
    Returns:
        调整后的合理评分
    """
    if score is None or score <= 0:
        return min_score
    
    # 确保评分不低于最低阈值
    return max(score, min_score)

def apply_scoring_rules(raw_score: float, data_context: Dict[str, Any]) -> float:
    """
    应用评分规则，确保分析师给出合理评分
    
    Args:
        raw_score: 原始计算得出的评分
        data_context: 数据上下文信息
        
    Returns:
        调整后的最终评分
    """
    scoring_adjustment = get_analysis_scoring_adjustment(data_context)
    
    # 应用评分调整
    adjusted_score = raw_score * scoring_adjustment.get('score_multiplier', 1.0)
    
    # 确保在合理范围内
    min_score = scoring_adjustment.get('min_score', 3.0)
    max_score = scoring_adjustment.get('max_score', 10.0)
    
    final_score = max(min_score, min(adjusted_score, max_score))
    
    return final_score

def format_analysis_reasoning(analyst_name: str, analysis_context: Dict[str, Any], 
                            analysis_results: Dict[str, Any]) -> str:
    """
    格式化分析推理，强调基于现有数据的专业分析
    """
    completeness = analysis_context.get('data_completeness_percentage', 0)
    available_metrics = analysis_context.get('available_metrics', 0)
    total_metrics = analysis_context.get('total_expected_metrics', 0)
    
    reasoning_parts = [
        f"【{analyst_name}专业分析】",
        f"数据基础：基于{available_metrics}项关键财务指标进行分析({completeness:.1f}%数据完整性)",
        analysis_context.get('analysis_note', ''),
    ]
    
    # 添加分析规则说明
    reasoning_parts.append("分析原则：现有数据代表完整的投资决策基础，充分发挥专业分析能力")
    
    # 添加具体分析结果
    if analysis_results:
        for key, value in analysis_results.items():
            if isinstance(value, (int, float)) and value > 0:
                reasoning_parts.append(f"{key}: {value}")
            elif isinstance(value, str) and value:
                reasoning_parts.append(f"{key}: {value}")
    
    return ".".join(filter(None, reasoning_parts))

def apply_minimum_score_rule(score: float, scoring_adjustment: Dict[str, Any]) -> float:
    """
    应用最低评分规则，确保评分在合理范围内
    
    Args:
        score: 原始评分
        scoring_adjustment: 评分调整参数
        
    Returns:
        调整后的评分
    """
    if scoring_adjustment is None:
        scoring_adjustment = {}
    
    min_score = scoring_adjustment.get('min_score', 2.0)
    max_score = scoring_adjustment.get('max_score', 10.0)
    
    # 确保评分不为None或负数
    if score is None or score < 0:
        return min_score
    
    # 应用最低和最高评分限制
    return max(min_score, min(score, max_score))

# 为所有分析师定义基础指标要求（最小化但关键的指标）
ANALYST_CORE_METRICS = {
    'warren_buffett': ['revenue', 'net_income', 'roe', 'debt_to_equity', 'operating_margin'],
    'charlie_munger': ['revenue', 'net_income', 'roe', 'roic', 'operating_margin'],
    'peter_lynch': ['revenue', 'net_income', 'revenue_growth_rate', 'price_to_earnings'],
    'phil_fisher': ['revenue', 'net_income', 'gross_margin', 'research_and_development'],
    'michael_burry': ['total_assets', 'total_liabilities', 'book_value', 'price_to_book'],
    'cathie_wood': ['revenue', 'revenue_growth_rate', 'gross_margin', 'research_and_development'],
    'ben_graham': ['current_assets', 'current_liabilities', 'book_value', 'price_to_book'],
    'aswath_damodaran': ['revenue', 'operating_income', 'free_cash_flow', 'total_assets'],
    'bill_ackman': ['revenue', 'operating_income', 'roe', 'roic'],
    'stanley_druckenmiller': ['revenue', 'net_income', 'free_cash_flow', 'revenue_growth_rate'],
    'rakesh_jhunjhunwala': ['revenue', 'net_income', 'roe', 'price_to_earnings'],
    'technical_analyst': ['price', 'volume', 'moving_averages', 'technical_indicators']
}