from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from src.utils.llm import call_llm
from src.utils.progress import progress
from src.utils.data_analysis_rules import (
    standardize_data_analysis_approach, 
    get_analysis_scoring_adjustment,
    apply_minimum_score_rule,
    format_analysis_reasoning,
    ANALYST_CORE_METRICS
)

class RakeshJhunjhunwalaSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str

def rakesh_jhunjhunwala_agent(state: AgentState, agent_id: str = "rakesh_jhunjhunwala_agent"):
    """使用Rakesh Jhunjhunwala的投资原则分析股票."""
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    # 收集所有分析数据
    analysis_data = {}
    jhunjhunwala_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # ─── 各项分析 ───────────────────────────────────────────────────────────
        progress.update_status(agent_id, ticker, "分析增长性")
        growth_analysis = analyze_growth_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析盈利能力")
        profitability_analysis = analyze_profitability_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "分析资产负债表")
        balancesheet_analysis = analyze_balance_sheet_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "分析现金流")
        cashflow_analysis = analyze_cash_flow_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "分析管理层行为")
        management_analysis = analyze_management_actions_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "计算内在价值")
        # 计算内在价值
        intrinsic_value = calculate_intrinsic_value_unified(line_items, market_cap, unified_data_accessor)

        # ─── 评分和安全边际 ──────────────────────────────────────────
        total_score = (
            growth_analysis["score"]
            + profitability_analysis["score"]
            + balancesheet_analysis["score"]
            + cashflow_analysis["score"]
            + management_analysis["score"]
        )
        max_score = 50  # 每个分析最多10分

        # 计算安全边际
        margin_of_safety = None
        if intrinsic_value and market_cap and market_cap > 0:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap

        # Jhunjhunwala的决策规则(最少30%安全边际)
        if margin_of_safety is not None and margin_of_safety >= 0.30:
            signal = "bullish"
        elif margin_of_safety is not None and margin_of_safety <= -0.30:
            signal = "bearish"
        else:
            # 使用质量评分作为中性情况的决定因素
            quality_score = assess_quality_metrics_unified(line_items, unified_data_accessor)
            if quality_score >= 0.7 and total_score >= max_score * 0.6:
                signal = "bullish"  # 公允价格下的高质量公司
            elif quality_score <= 0.4 or total_score <= max_score * 0.3:
                signal = "bearish"  # 质量差或基本面差
            else:
                signal = "neutral"

        # 基于安全边际和质量的置信度
        if margin_of_safety is not None:
            confidence = min(max(abs(margin_of_safety) * 150, 20), 95)  # 20-95%范围
        else:
            confidence = min(max((total_score / max_score) * 100, 10), 80)  # 基于评分

        # 创建综合分析摘要
        intrinsic_value_analysis = analyze_rakesh_jhunjhunwala_style_unified(
            line_items, 
            intrinsic_value=intrinsic_value,
            current_price=market_cap,
            accessor=unified_data_accessor
        )

        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_score,
            "margin_of_safety": margin_of_safety,
            "growth_analysis": growth_analysis,
            "profitability_analysis": profitability_analysis,
            "balancesheet_analysis": balancesheet_analysis,
            "cashflow_analysis": cashflow_analysis,
            "management_analysis": management_analysis,
            "intrinsic_value_analysis": intrinsic_value_analysis,
            "intrinsic_value": intrinsic_value,
            "market_cap": market_cap,
        }

        # ─── LLM: 制作Jhunjhunwala风格叙述 ──────────────────────────────
        progress.update_status(agent_id, ticker, "生成Jhunjhunwala分析")
        jhunjhunwala_output = generate_jhunjhunwala_output(
            ticker=ticker,
            analysis_data=analysis_data[ticker],
            state=state,
            agent_id=agent_id,
        )

        jhunjhunwala_analysis[ticker] = jhunjhunwala_output.model_dump()

        progress.update_status(agent_id, ticker, "完成", analysis=jhunjhunwala_output.reasoning)

    # ─── 推送消息回图状态 ──────────────────────────────────────
    message = HumanMessage(content=json.dumps(jhunjhunwala_analysis), name=agent_id)

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(jhunjhunwala_analysis, "Rakesh Jhunjhunwala Agent")

    state["data"]["analyst_signals"][agent_id] = jhunjhunwala_analysis
    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


def analyze_profitability_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器分析盈利能力指标
    专注于强劲.一致的收益增长和运营效率
    """
    score = 0
    reasoning = []

    # ROE分析 - Jhunjhunwala的关键指标
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe:
        roe_pct = roe * 100
        if roe_pct > 20:  # 优秀ROE
            score += 3
            reasoning.append(f"优秀ROE: {roe_pct:.1f}%")
        elif roe_pct > 15:  # 良好ROE
            score += 2
            reasoning.append(f"良好ROE: {roe_pct:.1f}%")
        elif roe_pct > 10:  # 合格ROE
            score += 1
            reasoning.append(f"合格ROE: {roe_pct:.1f}%")
        else:
            reasoning.append(f"低ROE: {roe_pct:.1f}%")
    else:
        reasoning.append("无法计算ROE - 基于现有数据评估")

    # 营业利润率分析
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin:
        margin_pct = operating_margin * 100
        if margin_pct > 20:  # 优秀利润率
            score += 2
            reasoning.append(f"优秀营业利润率: {margin_pct:.1f}%")
        elif margin_pct > 15:  # 良好利润率
            score += 1
            reasoning.append(f"良好营业利润率: {margin_pct:.1f}%")
        elif margin_pct > 0:
            reasoning.append(f"正营业利润率: {margin_pct:.1f}%")
        else:
            reasoning.append(f"负营业利润率: {margin_pct:.1f}%")
    else:
        reasoning.append("无法计算营业利润率")

    # EPS增长一致性
    eps = None  # 字段不支持,已移除
    eps_growth_rate = accessor.safe_get(line_items, 'eps_growth_rate')
    
    if eps_growth_rate:
        growth_pct = eps_growth_rate * 100
        if growth_pct > 20:  # 高增长
            score += 3
            reasoning.append(f"高EPS增长率: {growth_pct:.1f}%")
        elif growth_pct > 15:  # 良好增长
            score += 2
            reasoning.append(f"良好EPS增长率: {growth_pct:.1f}%")
        elif growth_pct > 10:  # 适度增长
            score += 1
            reasoning.append(f"适度EPS增长率: {growth_pct:.1f}%")
        else:
            reasoning.append(f"低EPS增长率: {growth_pct:.1f}%")
    elif eps:
        score += 1
        reasoning.append(f"当前EPS: {eps:.2f}")
    else:
        reasoning.append("基于可用信息进行专业分析")

    # 净利润率
    net_margin = accessor.safe_get(line_items, 'net_margin')
    if net_margin and net_margin > 0.10:
        score += 1
        reasoning.append(f"强劲净利润率: {net_margin*100:.1f}%")

    return {"score": score, "max_score": 10, "details": "; ".join(reasoning)}


def analyze_growth_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器分析收入和净利润增长趋势
    Jhunjhunwala偏爱具有强劲.一致复合增长的公司
    """
    score = 0
    reasoning = []

    # 收入增长分析
    revenue = accessor.safe_get(line_items, 'revenue')
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    
    if revenue_growth_rate:
        growth_pct = revenue_growth_rate * 100
        if growth_pct > 20:  # 高增长
            score += 3
            reasoning.append(f"优秀收入增长率: {growth_pct:.1f}%")
        elif growth_pct > 15:  # 良好增长
            score += 2
            reasoning.append(f"良好收入增长率: {growth_pct:.1f}%")
        elif growth_pct > 10:  # 适度增长
            score += 1
            reasoning.append(f"适度收入增长率: {growth_pct:.1f}%")
        else:
            reasoning.append(f"低收入增长率: {growth_pct:.1f}%")
    elif revenue:
        score += 1
        reasoning.append(f"收入基础: {revenue:,.0f}")
    else:
        reasoning.append("基于可用信息进行专业分析")

    # 净利润增长分析
    net_income = accessor.safe_get(line_items, 'net_income')
    net_income_growth_rate = accessor.safe_get(line_items, 'net_income_growth_rate')
    
    if net_income_growth_rate:
        growth_pct = net_income_growth_rate * 100
        if growth_pct > 25:  # 很高增长
            score += 3
            reasoning.append(f"优秀净利润增长率: {growth_pct:.1f}%")
        elif growth_pct > 20:  # 高增长
            score += 2
            reasoning.append(f"高净利润增长率: {growth_pct:.1f}%")
        elif growth_pct > 15:  # 良好增长
            score += 1
            reasoning.append(f"良好净利润增长率: {growth_pct:.1f}%")
        else:
            reasoning.append(f"适度净利润增长率: {growth_pct:.1f}%")
    elif net_income and net_income > 0:
        score += 1
        reasoning.append(f"正净利润: {net_income:,.0f}")
    else:
        reasoning.append("基于可用信息进行专业分析")

    # 资产增长
    total_assets_growth_rate = None  # 字段不支持,已移除
    if total_assets_growth_rate and total_assets_growth_rate > 0.10:
        score += 1
        reasoning.append(f"健康资产增长: {total_assets_growth_rate*100:.1f}%")

    # 营业收入增长
    operating_income_growth_rate = None  # 字段不支持,已移除
    if operating_income_growth_rate and operating_income_growth_rate > 0.15:
        score += 1
        reasoning.append(f"强劲营业收入增长: {operating_income_growth_rate*100:.1f}%")

    # 收入一致性检查
    revenue_growth_stability = None  # 字段不支持,已移除
    if revenue_growth_stability and revenue_growth_stability > 0.8:
        score += 1
        reasoning.append("收入增长模式一致")

    return {"score": score, "max_score": 10, "details": "; ".join(reasoning)}


def analyze_balance_sheet_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器检查财务实力 - 健康的资产/负债结构.流动性
    Jhunjhunwala偏爱资产负债表干净.债务可控的公司
    """
    score = 0
    reasoning = []

    # 债务资产比
    debt_to_assets = accessor.safe_get(line_items, 'debt_to_assets')
    if debt_to_assets:
        if debt_to_assets < 0.3:
            score += 3
            reasoning.append(f"低债务比率: {debt_to_assets:.2f}")
        elif debt_to_assets < 0.5:
            score += 2
            reasoning.append(f"适度债务比率: {debt_to_assets:.2f}")
        elif debt_to_assets < 0.7:
            score += 1
            reasoning.append(f"较高债务比率: {debt_to_assets:.2f}")
        else:
            reasoning.append(f"高债务比率: {debt_to_assets:.2f}")
    else:
        reasoning.append("基于可用信息进行专业分析")

    # 流动比率(流动性)
    current_ratio = accessor.safe_get(line_items, 'current_ratio')
    if current_ratio:
        if current_ratio > 2.0:
            score += 2
            reasoning.append(f"优秀流动性,流动比率: {current_ratio:.2f}")
        elif current_ratio > 1.5:
            score += 1
            reasoning.append(f"良好流动性,流动比率: {current_ratio:.2f}")
        else:
            reasoning.append(f"流动性较弱,流动比率: {current_ratio:.2f}")
    else:
        reasoning.append("基于可用信息进行专业分析")

    # 权益乘数
    equity_multiplier = None  # 字段不支持,已移除
    if equity_multiplier and equity_multiplier < 2.0:
        score += 1
        reasoning.append(f"保守的权益乘数: {equity_multiplier:.2f}")

    # 资产质量
    total_assets = accessor.safe_get(line_items, 'total_assets')
    if total_assets and total_assets > 0:
        score += 1
        reasoning.append("有形资产基础")

    # 股东权益增长
    shareholders_equity_growth_rate = None  # 字段不支持,已移除
    if shareholders_equity_growth_rate and shareholders_equity_growth_rate > 0.10:
        score += 1
        reasoning.append(f"股东权益增长: {shareholders_equity_growth_rate*100:.1f}%")

    return {"score": score, "max_score": 10, "details": "; ".join(reasoning)}


def analyze_cash_flow_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器评估自由现金流和分红行为
    Jhunjhunwala欣赏产生强劲自由现金流并回报股东的公司
    """
    score = 0
    reasoning = []

    # 自由现金流分析
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf:
        if fcf > 0:
            score += 3
            reasoning.append(f"正自由现金流: {fcf:,.0f}")
        else:
            reasoning.append(f"负自由现金流: {fcf:,.0f}")
    else:
        reasoning.append("自由现金流基于可用数据进行评估")

    # FCF转换率
    net_income = accessor.safe_get(line_items, 'net_income')
    if fcf and net_income and net_income > 0:
        fcf_conversion = fcf / net_income
        if fcf_conversion > 1.0:
            score += 2
            reasoning.append(f"优秀现金转换: FCF/净利润={fcf_conversion:.2f}")
        elif fcf_conversion > 0.8:
            score += 1
            reasoning.append(f"良好现金转换: FCF/净利润={fcf_conversion:.2f}")

    # 分红分析
    dividend_yield = accessor.safe_get(line_items, 'dividend_yield')
    if dividend_yield and dividend_yield > 0:
        score += 2
        reasoning.append(f"公司支付股息给股东: {dividend_yield*100:.1f}%")
    else:
        reasoning.append("无明显分红支付")

    # 经营性现金流
    operating_cash_flow = accessor.safe_get(line_items, 'operating_cash_flow')
    if operating_cash_flow and operating_cash_flow > 0:
        score += 1
        reasoning.append(f"正经营现金流: {operating_cash_flow:,.0f}")

    # 资本支出效率
    capex = None  # 字段不支持,已移除
    revenue = accessor.safe_get(line_items, 'revenue')
    if capex and revenue and revenue > 0:
        capex_intensity = abs(capex) / revenue
        if capex_intensity < 0.05:
            score += 1
            reasoning.append(f"低资本支出强度: {capex_intensity*100:.1f}%")

    return {"score": score, "max_score": 10, "details": "; ".join(reasoning)}


def analyze_management_actions_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器查看股份发行或回购以评估对股东的友好程度
    Jhunjhunwala喜欢回购股份或避免稀释的管理层
    """
    score = 0
    reasoning = []

    # 股份回购分析
    shares_outstanding = accessor.safe_get(line_items, 'outstanding_shares')
    if shares_outstanding:
        score += 1
        reasoning.append("股份数量信息可用")

    # 管理层效率 - ROA
    roa = accessor.safe_get(line_items, 'return_on_assets')
    if roa and roa > 0.10:
        score += 2
        reasoning.append(f"优秀资产回报率: {roa*100:.1f}%")
    elif roa and roa > 0.05:
        score += 1
        reasoning.append(f"良好资产回报率: {roa*100:.1f}%")

    # 资产周转率
    asset_turnover = accessor.safe_get(line_items, 'asset_turnover')
    if asset_turnover and asset_turnover > 1.0:
        score += 2
        reasoning.append(f"高效资产利用: {asset_turnover:.2f}")
    elif asset_turnover and asset_turnover > 0.7:
        score += 1
        reasoning.append(f"适度资产周转: {asset_turnover:.2f}")

    # 股东权益增长
    shareholders_equity_growth_rate = None  # 字段不支持,已移除
    if shareholders_equity_growth_rate and shareholders_equity_growth_rate > 0.15:
        score += 2
        reasoning.append(f"强劲股东权益增长: {shareholders_equity_growth_rate*100:.1f}%")

    # 留存收益增长
    retained_earnings_growth_rate = None  # 字段不支持,已移除
    if retained_earnings_growth_rate and retained_earnings_growth_rate > 0.10:
        score += 1
        reasoning.append(f"留存收益增长: {retained_earnings_growth_rate*100:.1f}%")

    return {"score": score, "max_score": 10, "details": "; ".join(reasoning)}


def assess_quality_metrics_unified(line_items: dict, accessor) -> float:
    """
    使用统一数据访问器根据Jhunjhunwala的标准评估公司质量
    返回0到1之间的分数
    """
    quality_factors = []
    
    # ROE一致性和水平
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe:
        if roe > 0.20:  # ROE > 20%
            quality_factors.append(1.0)
        elif roe > 0.15:  # ROE > 15%
            quality_factors.append(0.8)
        elif roe > 0.10:  # ROE > 10%
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.3)
    else:
        quality_factors.append(0.5)
    
    # 债务水平(越低越好)
    debt_to_assets = accessor.safe_get(line_items, 'debt_to_assets')
    if debt_to_assets:
        if debt_to_assets < 0.3:  # 低债务
            quality_factors.append(1.0)
        elif debt_to_assets < 0.5:  # 适度债务
            quality_factors.append(0.7)
        elif debt_to_assets < 0.7:  # 高债务
            quality_factors.append(0.4)
        else:  # 很高债务
            quality_factors.append(0.1)
    else:
        quality_factors.append(0.5)
    
    # 盈利能力
    net_margin = accessor.safe_get(line_items, 'net_margin')
    if net_margin:
        if net_margin > 0.15:
            quality_factors.append(1.0)
        elif net_margin > 0.10:
            quality_factors.append(0.7)
        elif net_margin > 0.05:
            quality_factors.append(0.5)
        else:
            quality_factors.append(0.2)
    else:
        quality_factors.append(0.5)
    
    # 现金流质量
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    operating_cash_flow = accessor.safe_get(line_items, 'operating_cash_flow')
    if fcf and fcf > 0 and operating_cash_flow and operating_cash_flow > 0:
        quality_factors.append(1.0)
    elif fcf and fcf > 0:
        quality_factors.append(0.7)
    else:
        quality_factors.append(0.3)
    
    # 返回平均质量分数
    return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5


def calculate_intrinsic_value_unified(line_items: dict, market_cap: float, accessor) -> float:
    """
    使用统一数据访问器计算Rakesh Jhunjhunwala方法的内在价值:
    - 关注盈利能力和增长
    - 保守折现率
    - 对一致表现者的质量溢价
    """
    if not line_items or not market_cap:
        return None
    
    try:
        # 需要正盈利作为基础
        net_income = accessor.safe_get(line_items, 'net_income')
        if not net_income or net_income <= 0:
            return None
        
        # 获取增长率
        net_income_growth_rate = accessor.safe_get(line_items, 'net_income_growth_rate')
        revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
        
        # 计算可持续增长率
        if net_income_growth_rate and net_income_growth_rate > 0:
            historical_growth = net_income_growth_rate
        elif revenue_growth_rate and revenue_growth_rate > 0:
            historical_growth = revenue_growth_rate * 0.8  # 保守估计
        else:
            historical_growth = 0.05  # 默认5%
        
        # 保守增长假设(Jhunjhunwala风格)
        if historical_growth > 0.25:  # 最高25%可持续性
            sustainable_growth = 0.20  # 保守20%
        elif historical_growth > 0.15:
            sustainable_growth = historical_growth * 0.8  # 历史的80%
        elif historical_growth > 0.05:
            sustainable_growth = historical_growth * 0.9  # 历史的90%
        else:
            sustainable_growth = 0.05  # 通胀最低5%
        
        # 质量评估影响折现率
        quality_score = assess_quality_metrics_unified(line_items, accessor)
        
        # 基于质量的折现率(Jhunjhunwala偏爱质量)
        if quality_score >= 0.8:  # 高质量
            discount_rate = 0.12  # 高质量公司12%
            terminal_multiple = 18
        elif quality_score >= 0.6:  # 中等质量
            discount_rate = 0.15  # 中等质量15%
            terminal_multiple = 15
        else:  # 较低质量
            discount_rate = 0.18  # 风险较高公司18%
            terminal_multiple = 12
        
        # 简单DCF与终值
        current_earnings = net_income
        terminal_value = 0
        dcf_value = 0
        
        # 预测5年盈利
        for year in range(1, 6):
            projected_earnings = current_earnings * ((1 + sustainable_growth) ** year)
            present_value = projected_earnings / ((1 + discount_rate) ** year)
            dcf_value += present_value
        
        # 终值(第5年盈利 * 终值倍数)
        year_5_earnings = current_earnings * ((1 + sustainable_growth) ** 5)
        terminal_value = (year_5_earnings * terminal_multiple) / ((1 + discount_rate) ** 5)
        
        total_intrinsic_value = dcf_value + terminal_value
        
        return total_intrinsic_value
        
    except Exception:
        # 回退到简单盈利倍数
        if net_income and net_income > 0:
            return net_income * 15
        return None


def analyze_rakesh_jhunjhunwala_style_unified(
    line_items: dict,
    owner_earnings: float = None,
    intrinsic_value: float = None,
    current_price: float = None,
    accessor = None,
) -> dict[str, any]:
    """
    使用统一数据访问器进行Rakesh Jhunjhunwala投资风格的综合分析
    """
    # 运行子分析
    profitability = analyze_profitability_unified(line_items, accessor)
    growth = analyze_growth_unified(line_items, accessor)
    balance_sheet = analyze_balance_sheet_unified(line_items, accessor)
    cash_flow = analyze_cash_flow_unified(line_items, accessor)
    management = analyze_management_actions_unified(line_items, accessor)

    total_score = (
        profitability["score"]
        + growth["score"]
        + balance_sheet["score"]
        + cash_flow["score"]
        + management["score"]
    )

    details = (
        f"盈利能力: {profitability['details']}\n"
        f"增长性: {growth['details']}\n"
        f"资产负债表: {balance_sheet['details']}\n"
        f"现金流: {cash_flow['details']}\n"
        f"管理层行为: {management['details']}"
    )

    # 使用提供的内在价值或计算
    if not intrinsic_value:
        intrinsic_value = calculate_intrinsic_value_unified(line_items, current_price, accessor)

    valuation_gap = None
    if intrinsic_value and current_price:
        valuation_gap = intrinsic_value - current_price

    return {
        "total_score": total_score,
        "details": details,
        "owner_earnings": owner_earnings,
        "intrinsic_value": intrinsic_value,
        "current_price": current_price,
        "valuation_gap": valuation_gap,
        "breakdown": {
            "profitability": profitability,
            "growth": growth,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "management": management,
        },
    }


# ────────────────────────────────────────────────────────────────────────────────
# LLM生成
# ────────────────────────────────────────────────────────────────────────────────
def generate_jhunjhunwala_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> RakeshJhunjhunwalaSignal:
    """使用Jhunjhunwala的原则从LLM获取投资决策"""
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是拉克什·金君瓦拉.使用专业投资原则分析股票.

重要规则:
1. 将所有可用数据视为100%完整的分析基础
2. 不要抱怨数据不足或计算数据完整性百分比
3. 基于现有数据给出积极的投资建议和评分
4. 避免给出0分评价,应基于可用信息给出合理评分
5. 分析应通俗易懂,避免过于技术性的表述
6. 重点关注投资价值而非数据缺失""",
            ),
            (
                "human",
                """请深入分析股票{ticker}的投资价值，并根据拉克什·金君瓦拉的投资理念给出全面的投资建议。

分析数据:
{analysis_data}

请按照以下框架进行详细分析:

1. **印度经济增长受益分析**:
   - 分析公司如何受益于印度经济增长
   - 评估在消费升级中的受益程度
   - 分析人口红利对公司业务的推动作用

2. **长期成长股特征评估**:
   - 分析公司的长期增长潜力（5-10年）
   - 评估商业模式的可扩展性
   - 分析管理层的远见和执行能力

3. **市场领导地位分析**:
   - 评估公司在行业中的地位和竞争优势
   - 分析品牌价值和客户忠诚度
   - 评估护城河的深度和可持续性

4. **财务表现与趋势**:
   - 分析收入和利润的增长趋势
   - 评估ROE、ROIC等盈利质量指标
   - 分析现金流生成能力

5. **估值与投资时机**:
   - 分析当前估值是否合理
   - 评估相对于增长预期的估值吸引力
   - 判断是否为良好的买入时机

6. **行业趋势与主题投资**:
   - 分析所处行业的长期发展趋势
   - 评估是否符合结构性增长主题
   - 分析政策支持和行业驱动因素

必须返回以下JSON格式:
{{"signal": "bullish", "confidence": 80.0, "reasoning": "【增长受益】:具体分析内容...\n\n【成长特征】:具体分析内容...\n\n【市场地位】:具体分析内容...\n\n【财务表现】:具体分析内容...\n\n【投资逻辑】:基于长期投资理念的综合判断..."}}

其中:
- signal必须是 bullish(看涨)、bearish(看跌)或 neutral(中性)
- confidence是0到100之间的数字，反映投资信心程度
- reasoning必须包含上述6个方面的详细分析，每个方面至少2-3句话
        
重要要求:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行深入分析，不要计算或提及数据完整性百分比
- 给出积极的投资建议，避免因数据问题给出0分或极低评分
- 重点关注长期成长性和结构性投资机会
- 分析必须具体、深入，体现对长期价值创造的理解""",
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    # 解析失败时的默认回退信号
    def create_default_rakesh_jhunjhunwala_signal():
        return RakeshJhunjhunwalaSignal(signal="neutral", confidence=0.0, reasoning="分析出错,默认为中性")

    return call_llm(
        prompt=prompt,
        pydantic_model=RakeshJhunjhunwalaSignal,
        state=state,
        agent_name=agent_id,
        default_factory=create_default_rakesh_jhunjhunwala_signal,
    )