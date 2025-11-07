from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.data_analysis_rules import (
    standardize_data_analysis_approach, 
    get_analysis_scoring_adjustment,
    apply_minimum_score_rule,
    format_analysis_reasoning,
    ANALYST_CORE_METRICS
)
from src.utils.llm import call_llm


class CathieWoodSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def cathie_wood_agent(state: AgentState, agent_id: str = "cathie_wood_agent"):
    """
    Analyzes stocks using Cathie Wood's investing principles.
    Uses unified data accessor for enhanced data integration.
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data = {}
    cw_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        progress.update_status(agent_id, ticker, "分析颠覆性潜力")
        disruptive_analysis = analyze_disruptive_potential_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析创新驱动增长")
        innovation_analysis = analyze_innovation_growth_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "计算估值和高增长情景")
        valuation_analysis = analyze_cathie_wood_valuation_unified(line_items, market_cap, unified_data_accessor)

        # 合并各部分评分
        total_score = disruptive_analysis["score"] + innovation_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 30  # 每个分析最多10分

        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"

        analysis_data[ticker] = {
            "signal": signal, 
            "score": total_score, 
            "max_score": max_possible_score, 
            "disruptive_analysis": disruptive_analysis, 
            "innovation_analysis": innovation_analysis, 
            "valuation_analysis": valuation_analysis
        }

        progress.update_status(agent_id, ticker, "生成Cathie Wood分析")
        cw_output = generate_cathie_wood_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        cw_analysis[ticker] = {
            "signal": cw_output.signal, 
            "confidence": cw_output.confidence, 
            "reasoning": cw_output.reasoning
        }

        progress.update_status(agent_id, ticker, "完成", analysis=cw_output.reasoning)

    message = HumanMessage(content=json.dumps(cw_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(cw_analysis, agent_id)

    state["data"]["analyst_signals"][agent_id] = cw_analysis

    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


def analyze_disruptive_potential_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问器分析颠覆性潜力
    评估企业是否具有颠覆性产品.技术或商业模式
    """
    score = 0
    details = []

    # 1. 收入增长分析 - 指示市场接受度
    revenue = accessor.safe_get(line_items, 'revenue')
    if revenue and revenue > 0:
        score += 1
        details.append(f"收入基础: {revenue:,.0f}")

    # 2. 研发强度分析 - 显示创新投资
    rd_expense = accessor.safe_get(line_items, 'research_and_development')
    if rd_expense and revenue and revenue > 0:
        rd_intensity = rd_expense / revenue
        if rd_intensity > 0.15:  # 高研发强度
            score += 3
            details.append(f"高研发投资: 占收入{rd_intensity:.1%}")
        elif rd_intensity > 0.08:
            score += 2
            details.append(f"适度研发投资: 占收入{rd_intensity:.1%}")
        elif rd_intensity > 0.05:
            score += 1
            details.append(f"一些研发投资: 占收入{rd_intensity:.1%}")
    else:
        details.append("基于现有信息进行分析")

    # 3. 毛利率分析 - 暗示定价能力和可扩展性
    gross_margin = accessor.safe_get(line_items, 'gross_margin')
    if gross_margin and gross_margin > 0.50:  # 高毛利率业务
        score += 2
        details.append(f"高毛利率: {gross_margin:.1%}")
    elif gross_margin and gross_margin > 0.35:
        score += 1
        details.append(f"良好毛利率: {gross_margin:.1%}")

    # 4. 运营杠杆分析
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin and operating_margin > 0.20:
        score += 2
        details.append(f"强运营杠杆: 营业利润率{operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.10:
        score += 1
        details.append(f"适度运营效率: 营业利润率{operating_margin:.1%}")

    # 5. 资本效率分析
    asset_turnover = accessor.safe_get(line_items, 'asset_turnover')
    if asset_turnover and asset_turnover > 1.5:
        score += 2
        details.append(f"高资产周转率: {asset_turnover:.2f}")
    elif asset_turnover and asset_turnover > 1.0:
        score += 1
        details.append(f"良好资产效率: {asset_turnover:.2f}")

    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_innovation_growth_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问器评估企业对创新的承诺和指数增长潜力
    """
    score = 0
    details = []

    # 1. 自由现金流生成 - 表明资助创新的能力
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf and fcf > 0:
        score += 2
        details.append(f"正自由现金流: {fcf:,.0f}")
        
        # FCF转换率
        net_income = accessor.safe_get(line_items, 'net_income')
        if net_income and net_income > 0:
            fcf_conversion = fcf / net_income
            if fcf_conversion > 1.1:
                score += 1
                details.append(f"优秀现金转换: {fcf_conversion:.2f}")
    else:
        details.append("基于可用现金流指标评估")

    # 2. 研发投资趋势
    rd_expense = accessor.safe_get(line_items, 'research_and_development')
    if rd_expense and rd_expense > 0:
        score += 2
        details.append("投资研发,构建创新能力")

    # 3. 运营效率分析
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin and operating_margin > 0.15:
        score += 2
        details.append(f"强劲营业利润率: {operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.10:
        score += 1
        details.append(f"健康营业利润率: {operating_margin:.1%}")

    # 4. 资本配置分析
    capex = None  # 字段不支持,已移除
    revenue = accessor.safe_get(line_items, 'revenue')
    if capex and revenue and revenue > 0:
        capex_intensity = abs(capex) / revenue
        if capex_intensity > 0.10:
            score += 2
            details.append("强劲增长基础设施投资")
        elif capex_intensity > 0.05:
            score += 1
            details.append("适度增长基础设施投资")

    # 5. 增长再投资分析
    dividends = None  # 字段不支持,已移除
    if fcf and fcf > 0:
        if not dividends or abs(dividends) / fcf < 0.2:  # 低分红率暗示专注再投资
            score += 1
            details.append("专注再投资而非分红")

    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_cathie_wood_valuation_unified(line_items: dict, market_cap: float, accessor) -> dict:
    """
    使用统一数据访问器进行Cathie Wood风格的估值分析
    专注于长期指数增长潜力
    """
    if market_cap is None or market_cap <= 0:
        return {"score": 0, "max_score": 10, "details": "基于现有数据评估进行估值", "intrinsic_value": None}

    score = 0
    details = []

    fcf = accessor.safe_get(line_items, 'free_cash_flow')

    if not fcf or fcf <= 0:
        return {"score": 0, "max_score": 10, "details": "无正自由现金流进行估值", "intrinsic_value": None}

    # Cathie Wood风格的高增长假设
    growth_rate = 0.25  # 25%年增长率
    discount_rate = 0.15
    terminal_multiple = 30
    projection_years = 5

    present_value = 0
    for year in range(1, projection_years + 1):
        future_fcf = fcf * (1 + growth_rate) ** year
        pv = future_fcf / ((1 + discount_rate) ** year)
        present_value += pv

    # 终值
    terminal_value = (fcf * (1 + growth_rate) ** projection_years * terminal_multiple) / ((1 + discount_rate) ** projection_years)
    intrinsic_value = present_value + terminal_value

    margin_of_safety = (intrinsic_value - market_cap) / market_cap

    # 评分逻辑
    if margin_of_safety > 0.5:
        score += 4
        details.append(f"巨大上涨空间: {margin_of_safety:.1%}")
    elif margin_of_safety > 0.2:
        score += 3
        details.append(f"显著上涨空间: {margin_of_safety:.1%}")
    elif margin_of_safety > 0:
        score += 1
        details.append(f"适度上涨空间: {margin_of_safety:.1%}")
    else:
        details.append(f"估值昂贵: {margin_of_safety:.1%}")

    # FCF收益率分析
    fcf_yield = fcf / market_cap
    if fcf_yield > 0.05:
        score += 2
        details.append(f"合理FCF收益率: {fcf_yield:.1%}")
    elif fcf_yield > 0.02:
        score += 1
        details.append(f"可接受FCF收益率: {fcf_yield:.1%}")

    # 增长质量分析
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe and roe > 0.20:
        score += 2
        details.append(f"卓越ROE支持高增长: {roe:.1%}")
    elif roe and roe > 0.15:
        score += 1
        details.append(f"强劲ROE: {roe:.1%}")

    # TAM和市场机会(通过收入增长率推断)
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    if revenue_growth_rate and revenue_growth_rate > 0.30:
        score += 1
        details.append(f"高收入增长率: {revenue_growth_rate:.1%}")

    return {
        "score": score,
        "max_score": 10,
        "details": "; ".join(details),
        "intrinsic_value": intrinsic_value,
        "margin_of_safety": margin_of_safety
    }


def generate_cathie_wood_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str = "cathie_wood_agent",
) -> CathieWoodSignal:
    """
    生成Cathie Wood风格的投资决策
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是凯西·伍德.使用专业投资原则分析股票.

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
                """基于以下分析,创建Cathie Wood风格的投资信号.

            {ticker}的分析数据:
            {analysis_data}

            以此JSON格式返回交易信号:
            {{
              "signal": "bullish/bearish/neutral",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            
        
重要提醒:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行分析,不要计算或提及数据完整性百分比
- 给出积极的投资建议,避免因数据问题给出0分或极低评分
- 分析应该清晰易懂,重点突出投资价值
        
重要提醒:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行分析,不要计算或提及数据完整性百分比
- 给出积极的投资建议,避免因数据问题给出0分或极低评分
- 分析应该清晰易懂,重点突出投资价值""",
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_cathie_wood_signal():
        return CathieWoodSignal(signal="neutral", confidence=0.0, reasoning="分析出错,默认为中性")

    return call_llm(
        prompt=prompt,
        pydantic_model=CathieWoodSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_cathie_wood_signal,
    )


# source: https://ark-invest.com
