"""
统一的分析师名称映射器
确保在所有地方都能正确将英文键名转换为中文名称
"""

from typing import Dict, Optional

# 完整的分析师名称映射表
ANALYST_NAME_MAP: Dict[str, str] = {
    # 投资大师 - 带_agent后缀
    "warren_buffett_agent": "沃伦·巴菲特",
    "charlie_munger_agent": "查理·芒格",
    "peter_lynch_agent": "彼得·林奇",
    "stanley_druckenmiller_agent": "斯坦利·德鲁肯米勒",
    "michael_burry_agent": "迈克尔·伯里",
    "cathie_wood_agent": "凯茜·伍德",
    "ben_graham_agent": "本杰明·格雷厄姆",
    "benjamin_graham_agent": "本杰明·格雷厄姆",
    "aswath_damodaran_agent": "阿斯沃特·达莫达兰",
    "bill_ackman_agent": "比尔·阿克曼",
    "rakesh_jhunjhunwala_agent": "拉凯什·琼琼瓦拉",
    "phil_fisher_agent": "菲利普·费雪",
    
    # 投资大师 - 不带_agent后缀
    "warren_buffett": "沃伦·巴菲特",
    "charlie_munger": "查理·芒格",
    "peter_lynch": "彼得·林奇",
    "stanley_druckenmiller": "斯坦利·德鲁肯米勒",
    "michael_burry": "迈克尔·伯里",
    "cathie_wood": "凯茜·伍德",
    "ben_graham": "本杰明·格雷厄姆",
    "benjamin_graham": "本杰明·格雷厄姆",
    "aswath_damodaran": "阿斯沃特·达莫达兰",
    "bill_ackman": "比尔·阿克曼",
    "rakesh_jhunjhunwala": "拉凯什·琼琼瓦拉",
    "phil_fisher": "菲利普·费雪",
    
    # 专业分析师 - 带_agent后缀
    "technical_analyst_agent": "技术面分析师",
    "fundamentals_analyst_agent": "基本面分析师",
    "sentiment_analyst_agent": "情绪分析师",
    "valuation_analyst_agent": "估值分析师",
    "risk_management_agent": "风险管理",
    "fundamentals_agent": "基本面分析师",
    "sentiment_agent": "情绪分析师",
    "valuation_agent": "估值分析师",
    
    # 专业分析师 - 不带_agent后缀
    "technical_analyst": "技术面分析师",
    "fundamentals_analyst": "基本面分析师",
    "sentiment_analyst": "情绪分析师",
    "valuation_analyst": "估值分析师",
    "risk_management": "风险管理",
    "fundamentals": "基本面分析师",
    "sentiment": "情绪分析师",
    "valuation": "估值分析师",
    
    # 其他可能的变体
    "technicals": "技术面分析师",
    "technicals_agent": "技术面分析师",
    "risk": "风险评估",
    "risk_agent": "风险评估",
}


def get_analyst_chinese_name(analyst_id: str) -> str:
    """
    获取分析师的中文名称
    
    Args:
        analyst_id: 分析师ID（英文键名）
        
    Returns:
        str: 中文名称，如果找不到映射则返回格式化的英文名称
    """
    if not analyst_id:
        return "未知分析师"
    
    # 首先尝试直接匹配
    if analyst_id in ANALYST_NAME_MAP:
        return ANALYST_NAME_MAP[analyst_id]
    
    # 如果没找到，尝试去掉_agent后缀再匹配
    if analyst_id.endswith('_agent'):
        base_id = analyst_id[:-6]  # 去掉'_agent'
        if base_id in ANALYST_NAME_MAP:
            return ANALYST_NAME_MAP[base_id]
    
    # 如果还是没找到，尝试添加_agent后缀再匹配
    agent_id = f"{analyst_id}_agent"
    if agent_id in ANALYST_NAME_MAP:
        return ANALYST_NAME_MAP[agent_id]
    
    # 最后的备用方案：格式化英文名称
    formatted_name = analyst_id.replace('_agent', '').replace('_', ' ').title()
    return formatted_name


def is_english_analyst_key(analyst_id: str) -> bool:
    """
    判断是否为英文分析师键名
    
    Args:
        analyst_id: 分析师ID
        
    Returns:
        bool: 如果是英文键名返回True，否则返回False
    """
    if not analyst_id:
        return False
    
    # 如果包含中文字符，则不是英文键名
    if any('\u4e00' <= char <= '\u9fff' for char in analyst_id):
        return False
    
    # 如果包含下划线或在映射表中，则是英文键名
    return '_' in analyst_id or analyst_id in ANALYST_NAME_MAP


def ensure_chinese_analyst_names(analyst_signals: Dict) -> Dict:
    """
    确保分析师信号中的所有键名都是中文名称
    
    Args:
        analyst_signals: 原始的分析师信号字典
        
    Returns:
        Dict: 键名转换为中文的分析师信号字典
    """
    if not analyst_signals:
        return {}
    
    chinese_signals = {}
    
    for analyst_id, signals in analyst_signals.items():
        chinese_name = get_analyst_chinese_name(analyst_id)
        chinese_signals[chinese_name] = signals
    
    return chinese_signals


def preprocess_data_for_html(result: Dict) -> Dict:
    """
    预处理数据，确保HTML报告生成时不会出现英文键名
    
    Args:
        result: 原始结果数据
        
    Returns:
        Dict: 预处理后的数据
    """
    if not result:
        return result
    
    processed_result = result.copy()
    
    # 处理分析师信号
    if "analyst_signals" in processed_result:
        processed_result["analyst_signals"] = ensure_chinese_analyst_names(
            processed_result["analyst_signals"]
        )
    
    return processed_result


def get_all_analyst_mappings() -> Dict[str, str]:
    """
    获取所有分析师映射关系
    
    Returns:
        Dict[str, str]: 完整的映射字典
    """
    return ANALYST_NAME_MAP.copy()
