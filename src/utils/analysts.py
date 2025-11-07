"""Constants and utilities related to analysts configuration."""

import sys
import os

# Add project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.agents import portfolio_manager
    from src.agents.aswath_damodaran import aswath_damodaran_agent
    from src.agents.ben_graham import ben_graham_agent
    from src.agents.bill_ackman import bill_ackman_agent
    from src.agents.cathie_wood import cathie_wood_agent
    from src.agents.charlie_munger import charlie_munger_agent
    from src.agents.michael_burry import michael_burry_agent
    from src.agents.phil_fisher import phil_fisher_agent
    from src.agents.peter_lynch import peter_lynch_agent
    from src.agents.stanley_druckenmiller import stanley_druckenmiller_agent
    from src.agents.technicals import technical_analyst_agent
    from src.agents.warren_buffett import warren_buffett_agent
    from src.agents.rakesh_jhunjhunwala import rakesh_jhunjhunwala_agent
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    "warren_buffett": {
        "display_name": "沃伦·巴菲特",
        "description": "奥马哈先知",
        "investing_style": "value_investing",
        "agent_func": warren_buffett_agent,
        "type": "analyst",
        "order": 0,
    },
    "charlie_munger": {
        "display_name": "查理·芒格",
        "description": "理性思考者",
        "investing_style": "value_investing",
        "agent_func": charlie_munger_agent,
        "type": "analyst",
        "order": 1,
    },
    "peter_lynch": {
        "display_name": "彼得·林奇",
        "description": "十倍股投资者",
        "investing_style": "growth_investing",
        "agent_func": peter_lynch_agent,
        "type": "analyst",
        "order": 2,
    },
    "stanley_druckenmiller": {
        "display_name": "斯坦利·德鲁肯米勒",
        "description": "宏观投资者",
        "investing_style": "macro_global",
        "agent_func": stanley_druckenmiller_agent,
        "type": "analyst",
        "order": 3,
    },
    "michael_burry": {
        "display_name": "迈克尔·伯里",
        "description": "大空头逆势投资者",
        "investing_style": "contrarian_activist",
        "agent_func": michael_burry_agent,
        "type": "analyst",
        "order": 4,
    },
    "cathie_wood": {
        "display_name": "凯西·伍德",
        "description": "成长投资女王",
        "investing_style": "growth_investing",
        "agent_func": cathie_wood_agent,
        "type": "analyst",
        "order": 5,
    },
    "ben_graham": {
        "display_name": "本杰明·格雷厄姆",
        "description": "价值投资之父",
        "investing_style": "value_investing",
        "agent_func": ben_graham_agent,
        "type": "analyst",
        "order": 6,
    },
    "aswath_damodaran": {
        "display_name": "阿斯瓦特·达莫达兰",
        "description": "估值学教授",
        "investing_style": "quantitative_analytical",
        "agent_func": aswath_damodaran_agent,
        "type": "analyst",
        "order": 7,
    },
    "bill_ackman": {
        "display_name": "比尔·阿克曼",
        "description": "激进投资者",
        "investing_style": "contrarian_activist",
        "agent_func": bill_ackman_agent,
        "type": "analyst",
        "order": 8,
    },
    "rakesh_jhunjhunwala": {
        "display_name": "拉克什·金君瓦拉",
        "description": "印度大牛",
        "investing_style": "macro_global",
        "agent_func": rakesh_jhunjhunwala_agent,
        "type": "analyst",
        "order": 9,
    },
    "phil_fisher": {
        "display_name": "菲利普·费雪",
        "description": "闲聊投资法大师",
        "investing_style": "growth_investing",
        "agent_func": phil_fisher_agent,
        "type": "analyst",
        "order": 10,
    },
    "technical_analyst": {
        "display_name": "技术面分析师",
        "description": "图表模式专家",
        "investing_style": "technical_analysis",
        "agent_func": technical_analyst_agent,
        "type": "analyst",
        "order": 11,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}


def get_agents_list():
    """Get the list of agents for API responses."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "investing_style": config["investing_style"],
            "order": config["order"]
        }
        for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
    ]


def get_investing_styles():
    """Get all unique investing styles."""
    return list(set(config["investing_style"] for config in ANALYST_CONFIG.values()))


def get_investing_style_display_names():
    """Get display names for investing styles."""
    return {
        "value_investing": "价值投资",
        "growth_investing": "成长投资", 
        "contrarian_activist": "逆势/激进投资",
        "macro_global": "宏观/全球投资",
        "technical_analysis": "技术分析",
        "quantitative_analytical": "量化/分析"
    }


def get_agents_by_investing_style():
    """Get agents grouped by investing style."""
    groups = {}
    for key, config in ANALYST_CONFIG.items():
        style = config["investing_style"]
        if style not in groups:
            groups[style] = []
        groups[style].append({
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "order": config["order"]
        })
    
    # Sort agents within each group by order
    for style in groups:
        groups[style].sort(key=lambda x: x["order"])
    
    return groups
