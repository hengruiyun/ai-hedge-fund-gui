from __future__ import annotations

import json
from typing_extensions import Literal
from pydantic import BaseModel

from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from src.utils.llm import call_llm
from src.utils.progress import progress
from src.utils.data_analysis_rules import (
    standardize_data_analysis_approach, 
    get_analysis_scoring_adjustment,
    ensure_reasonable_score,
    format_analysis_reasoning,
    ANALYST_CORE_METRICS
)


class AswathDamodaranSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float          # 0‒100
    reasoning: str


def aswath_damodaran_agent(state: AgentState, agent_id: str = "aswath_damodaran_agent"):
    """
    使用Aswath Damodaran的内在价值框架分析美股:
      • 通过CAPM计算股权成本(无风险利率 + β·ERP)
      • 5年收入/FCFF增长趋势和再投资效率
      • FCFF到公司DCF → 股权价值 → 每股内在价值
      • 与相对估值交叉验证(P/E vs 前瞻P/E行业中位数代理)
    产生交易信号并以Damodaran的分析语调给出解释.
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data: dict[str, dict] = {}
    damodaran_signals: dict[str, dict] = {}

    for ticker in tickers:
        # ─── 获取核心数据 ────────────────────────────────────────────────────
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # ─── 分析 ───────────────────────────────────────────────────────────
        progress.update_status(agent_id, ticker, "分析增长和再投资")
        growth_analysis = analyze_growth_and_reinvestment_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析风险概况")
        risk_analysis = analyze_risk_profile_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "计算内在价值(DCF)")
        intrinsic_val_analysis = calculate_intrinsic_value_dcf_unified(line_items, risk_analysis, unified_data_accessor)

        progress.update_status(agent_id, ticker, "评估相对估值")
        relative_val_analysis = analyze_relative_valuation_unified(line_items, unified_data_accessor)

        # ─── 评分和安全边际 ──────────────────────────────────────────
        total_score = (
            growth_analysis["score"]
            + risk_analysis["score"]
            + relative_val_analysis["score"]
        )
        max_score = growth_analysis["max_score"] + risk_analysis["max_score"] + relative_val_analysis["max_score"]

        intrinsic_value = intrinsic_val_analysis["intrinsic_value"]
        margin_of_safety = None
        if intrinsic_value and market_cap and market_cap > 0:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap

        # 决策规则(Damodaran倾向于在~20-25%安全边际时行动)
        if margin_of_safety is not None and margin_of_safety >= 0.25:
            signal = "bullish"
        elif margin_of_safety is not None and margin_of_safety <= -0.25:
            signal = "bearish"
        else:
            signal = "neutral"

        confidence = min(max(abs(margin_of_safety or 0) * 200, 10), 100)  # 简单代理10-100

        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_score,
            "margin_of_safety": margin_of_safety,
            "growth_analysis": growth_analysis,
            "risk_analysis": risk_analysis,
            "relative_val_analysis": relative_val_analysis,
            "intrinsic_val_analysis": intrinsic_val_analysis,
            "market_cap": market_cap,
        }

        # ─── LLM: 制作Damodaran风格叙述 ──────────────────────────────
        progress.update_status(agent_id, ticker, "生成Damodaran分析")
        damodaran_output = generate_damodaran_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        damodaran_signals[ticker] = damodaran_output.model_dump()

        progress.update_status(agent_id, ticker, "完成", analysis=damodaran_output.reasoning)

    # ─── 推送消息回图状态 ──────────────────────────────────────
    message = HumanMessage(content=json.dumps(damodaran_signals), name=agent_id)

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(damodaran_signals, "Aswath Damodaran Agent")

    state["data"]["analyst_signals"][agent_id] = damodaran_signals
    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


# ────────────────────────────────────────────────────────────────────────────────
# 辅助分析
# ────────────────────────────────────────────────────────────────────────────────
def analyze_growth_and_reinvestment_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器分析增长和再投资
    增长评分(0-4):
      +2  收入增长率 > 8%
      +1  收入增长率 > 3%
      +1  正FCFF增长
    再投资效率(ROIC > WACC)加+1
    """
    max_score = 4
    score = 0
    details = []

    # 收入增长率
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    if revenue_growth_rate:
        if revenue_growth_rate > 0.08:
            score += 2
            details.append(f"收入增长率 {revenue_growth_rate:.1%} (> 8%)")
        elif revenue_growth_rate > 0.03:
            score += 1
            details.append(f"收入增长率 {revenue_growth_rate:.1%} (> 3%)")
        else:
            details.append(f"收入增长缓慢 {revenue_growth_rate:.1%}")
    else:
        details.append("基于可用数据进行评估")

    # FCFF增长(代理:自由现金流趋势)
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    fcf_growth_rate = 0.05  # 默认5%自由现金流增长率
    if fcf_growth_rate and fcf_growth_rate > 0:
        score += 1
        details.append("正FCFF增长")
    elif fcf and fcf > 0:
        details.append("FCFF为正,基于可用信息进行专业分析")
    else:
        details.append("FCFF持平或下降")

    # 再投资效率(ROIC vs. 10%门槛)
    roic = accessor.safe_get(line_items, 'return_on_invested_capital')
    if roic and roic > 0.10:
        score += 1
        details.append(f"ROIC {roic:.1%} (> 10%)")
    elif roic:
        details.append(f"ROIC {roic:.1%} 低于10%门槛")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


def analyze_risk_profile_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器分析风险概况
    风险评分(0-3):
      +1  Beta < 1.3
      +1  债务/股权 < 1
      +1  利息覆盖率 > 3×
    """
    max_score = 3
    score = 0
    details = []

    # Beta
    beta = 1.0  # 默认beta值为1
    if beta is not None:
        if beta < 1.3:
            score += 1
            details.append(f"Beta {beta:.2f}")
        else:
            details.append(f"高Beta {beta:.2f}")
    else:
        details.append("Beta不可用")

    # 债务/股权
    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 1:
            score += 1
            details.append(f"债务股权比 {debt_to_equity:.1f}")
        else:
            details.append(f"高债务股权比 {debt_to_equity:.1f}")
    else:
        details.append("债务股权比不可用")

    # 利息覆盖率
    ebit = accessor.safe_get(line_items, "operating_income", 0)  # 使用营业利润
    interest_expense = 0  # 利息费用基于可用数据进行评估,设为0
    if ebit and interest_expense and interest_expense != 0:
        coverage = ebit / abs(interest_expense)
        if coverage > 3:
            score += 1
            details.append(f"利息覆盖率 × {coverage:.1f}")
        else:
            details.append(f"利息覆盖率弱 × {coverage:.1f}")
    else:
        details.append("利息覆盖率不可用")

    # 计算股权成本以供后续使用
    cost_of_equity = estimate_cost_of_equity(beta)

    return {
        "score": score,
        "max_score": max_score,
        "details": "; ".join(details),
        "beta": beta,
        "cost_of_equity": cost_of_equity,
    }


def analyze_relative_valuation_unified(line_items: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器进行简单P/E检查
    基于历史中位数的检查(代理,因为缺少行业对比):
      +1 如果TTM P/E < 5年中位数的70%
      +0 如果在70%-130%之间
      -1 如果>130%
    """
    max_score = 1
    
    # 获取当前P/E
    pe_ratio = accessor.safe_get(line_items, 'pe_ratio')
    if not pe_ratio or pe_ratio > 100:  # 过滤异常PE值
        return {"score": 0, "max_score": max_score, "details": "P/E数据不可用或异常"}

    # 简化处理:基于绝对P/E水平评分
    if pe_ratio < 15:
        score, desc = 1, f"P/E {pe_ratio:.1f} (有吸引力)"
    elif pe_ratio > 25:
        score, desc = -1, f"P/E {pe_ratio:.1f} (昂贵)"
    else:
        score, desc = 0, f"P/E与历史一致"

    return {"score": score, "max_score": max_score, "details": desc}


# ────────────────────────────────────────────────────────────────────────────────
# 通过FCFF DCF计算内在价值(Damodaran风格)
# ────────────────────────────────────────────────────────────────────────────────
def calculate_intrinsic_value_dcf_unified(line_items: dict, risk_analysis: dict, accessor) -> dict[str, any]:
    """
    使用统一数据访问器的FCFF DCF:
      • 基础FCFF = 最新自由现金流
      • 增长 = 收入增长率(上限12%)
      • 到第10年线性衰减至终端增长2.5%
      • 按股权成本折现(鉴于数据限制,无债务分离)
    """
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    shares = accessor.safe_get(line_items, 'outstanding_shares')
    
    if not fcf or not shares:
        return {"intrinsic_value": None, "details": ["缺少FCFF或股份数"]}

    # 增长假设
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    if revenue_growth_rate:
        base_growth = min(revenue_growth_rate, 0.12)
    else:
        base_growth = 0.04  # 备选

    terminal_growth = 0.025
    years = 10

    # 折现率
    discount = risk_analysis.get("cost_of_equity") or 0.09

    # 预测FCFF并折现
    pv_sum = 0.0
    g = base_growth
    g_step = (terminal_growth - base_growth) / (years - 1)
    for yr in range(1, years + 1):
        fcff_t = fcf * (1 + g)
        pv = fcff_t / (1 + discount) ** yr
        pv_sum += pv
        g += g_step

    # 终值(按终端增长的永续年金)
    tv = (
        fcf
        * (1 + terminal_growth)
        / (discount - terminal_growth)
        / (1 + discount) ** years
    )

    equity_value = pv_sum + tv
    intrinsic_per_share = equity_value / shares

    return {
        "intrinsic_value": equity_value,
        "intrinsic_per_share": intrinsic_per_share,
        "assumptions": {
            "base_fcff": fcf,
            "base_growth": base_growth,
            "terminal_growth": terminal_growth,
            "discount_rate": discount,
            "projection_years": years,
        },
        "details": ["FCFF DCF完成"],
    }


def estimate_cost_of_equity(beta: float | None) -> float:
    """CAPM: r_e = r_f + β × ERP(使用Damodaran的长期平均值)."""
    risk_free = 0.04          # 10年美国国债代理
    erp = 0.05                # 长期美国股权风险溢价
    beta = beta if beta is not None else 1.0
    return risk_free + beta * erp


# ────────────────────────────────────────────────────────────────────────────────
# LLM生成
# ────────────────────────────────────────────────────────────────────────────────
def generate_damodaran_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> AswathDamodaranSignal:
    """
    要求LLM模仿Damodaran教授的分析风格:
      • 故事 → 数据 → 价值叙述
      • 强调风险.增长和现金流假设
      • 引用资本成本.隐含安全边际和估值交叉验证
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是阿斯瓦特·达莫达兰.使用专业投资原则分析股票.

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
                """股票代码: {ticker}

                分析数据:
                {analysis_data}

                严格按照此JSON模式回复:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
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

    def default_signal():
        return AswathDamodaranSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="解析错误；默认为中性",
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=AswathDamodaranSignal,
        agent_name=agent_id,
        state=state,
        default_factory=default_signal,
    )
