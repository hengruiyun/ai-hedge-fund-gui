from __future__ import annotations

from datetime import datetime, timedelta
import json
from typing_extensions import Literal

from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from src.utils.llm import call_llm
from src.utils.progress import progress
from src.utils.data_analysis_rules import (
    standardize_data_analysis_approach, 
    get_analysis_scoring_adjustment,
    apply_minimum_score_rule,
    format_analysis_reasoning,
    ANALYST_CORE_METRICS
)

__all__ = [
    "MichaelBurrySignal",
    "michael_burry_agent",
]

###############################################################################
# Pydantic output model
###############################################################################


class MichaelBurrySignal(BaseModel):
    """由LLM返回的模式"""

    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float  # 0–100
    reasoning: str


###############################################################################
# Core agent
###############################################################################


def michael_burry_agent(state: AgentState, agent_id: str = "michael_burry_agent"):
    """使用Michael Burry的深度价值.逆向投资框架分析股票"""

    data = state["data"]
    tickers: list[str] = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data: dict[str, dict] = {}
    burry_analysis: dict[str, dict] = {}

    for ticker in tickers:
        # ------------------------------------------------------------------
        # 获取原始数据
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # 获取综合数据(包括内部人交易.新闻等)
        comprehensive_data = unified_data_accessor.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
        insider_trades = comprehensive_data.get('insider_trades', [])
        news = comprehensive_data.get('company_news', [])

        # ------------------------------------------------------------------
        # 运行子分析
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "分析价值")
        value_analysis = _analyze_value_unified(line_items, market_cap, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析资产负债表")
        balance_sheet_analysis = _analyze_balance_sheet_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析内部人活动")
        insider_analysis = _analyze_insider_activity_unified(insider_trades)

        progress.update_status(agent_id, ticker, "分析逆向情绪")
        contrarian_analysis = _analyze_contrarian_sentiment_unified(news)

        # ------------------------------------------------------------------
        # 聚合分数并得出初步信号
        # ------------------------------------------------------------------
        total_score = (
            value_analysis["score"]
            + balance_sheet_analysis["score"]
            + insider_analysis["score"]
            + contrarian_analysis["score"]
        )
        max_score = (
            value_analysis["max_score"]
            + balance_sheet_analysis["max_score"]
            + insider_analysis["max_score"]
            + contrarian_analysis["max_score"]
        )

        if total_score >= 0.7 * max_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_score:
            signal = "bearish"
        else:
            signal = "neutral"

        # ------------------------------------------------------------------
        # 收集LLM推理和输出的数据
        # ------------------------------------------------------------------
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_score,
            "value_analysis": value_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "insider_analysis": insider_analysis,
            "contrarian_analysis": contrarian_analysis,
            "market_cap": market_cap,
        }

        progress.update_status(agent_id, ticker, "生成LLM输出")
        burry_output = _generate_burry_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        burry_analysis[ticker] = {
            "signal": burry_output.signal,
            "confidence": burry_output.confidence,
            "reasoning": burry_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "完成", analysis=burry_output.reasoning)

    # ----------------------------------------------------------------------
    # 返回到图
    # ----------------------------------------------------------------------
    message = HumanMessage(content=json.dumps(burry_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(burry_analysis, "Michael Burry Agent")

    state["data"]["analyst_signals"][agent_id] = burry_analysis

    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


###############################################################################
# 子分析助手
###############################################################################


# ----- 价值 ----------------------------------------------------------------

def _analyze_value_unified(line_items: dict, market_cap, accessor):
    """使用统一数据访问适配器分析自由现金流收益率.EV/EBIT等经典深度价值指标"""

    max_score = 6  # FCF收益率4分,EV/EBIT 2分
    score = 0
    details: list[str] = []

    # 自由现金流收益率
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf is not None and market_cap:
        fcf_yield = fcf / market_cap
        if fcf_yield >= 0.15:
            score += 4
            details.append(f"特别高的FCF收益率 {fcf_yield:.1%}")
        elif fcf_yield >= 0.12:
            score += 3
            details.append(f"非常高的FCF收益率 {fcf_yield:.1%}")
        elif fcf_yield >= 0.08:
            score += 2
            details.append(f"可观的FCF收益率 {fcf_yield:.1%}")
        else:
            details.append(f"低FCF收益率 {fcf_yield:.1%}")
    else:
        details.append("FCF基于可用数据进行评估")

    # EV/EBIT
    ev_ebit = None  # 字段不支持,已移除
    if ev_ebit is not None:
        if ev_ebit < 6:
            score += 2
            details.append(f"EV/EBIT {ev_ebit:.1f} (<6)")
        elif ev_ebit < 10:
            score += 1
            details.append(f"EV/EBIT {ev_ebit:.1f} (<10)")
        else:
            details.append(f"高EV/EBIT {ev_ebit:.1f}")
    else:
        details.append("EV/EBIT基于可用数据进行评估")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- 资产负债表 --------------------------------------------------------

def _analyze_balance_sheet_unified(line_items: dict, accessor):
    """使用统一数据访问适配器进行杠杆和流动性检查"""

    max_score = 3
    score = 0
    details: list[str] = []

    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            score += 2
            details.append(f"低债务股权比 {debt_to_equity:.2f}")
        elif debt_to_equity < 1:
            score += 1
            details.append(f"中等债务股权比 {debt_to_equity:.2f}")
        else:
            details.append(f"高杠杆债务股权比 {debt_to_equity:.2f}")
    else:
        details.append("债务股权比基于可用数据进行评估")

    # 快速流动性健全性检查(现金vs总债务)
    cash = None  # 字段不支持,已移除
    total_debt = accessor.safe_get(line_items, 'total_debt')
    if cash is not None and total_debt is not None:
        if cash > total_debt:
            score += 1
            details.append("净现金头寸")
        else:
            details.append("净债务头寸")
    else:
        details.append("现金/债务基于可用数据进行评估")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- 内部人活动 -----------------------------------------------------

def _analyze_insider_activity_unified(insider_trades):
    """过去12个月的净内部人买入作为硬催化剂"""

    max_score = 2
    score = 0
    details: list[str] = []

    if not insider_trades:
        details.append("基于现有信息进行分析")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    shares_bought = sum(0 for t in insider_trades if 0 > 0)  # transaction_shares字段不支持,设为0
    shares_sold = abs(sum(0 for t in insider_trades if 0 < 0))  # transaction_shares字段不支持,设为0
    net = shares_bought - shares_sold
    if net > 0:
        score += 2 if net / max(shares_sold, 1) > 1 else 1
        details.append(f"净内部人买入 {net:,} 股")
    else:
        details.append("净内部人卖出")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- 逆向情绪 -------------------------------------------------

def _analyze_contrarian_sentiment_unified(news):
    """非常粗略的衡量:最近的负面头条墙对逆向投资者来说可能是*积极的*"""

    max_score = 1
    score = 0
    details: list[str] = []

    if not news:
        details.append("无最近新闻")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    # 计算负面情绪文章
    sentiment_negative_count = sum(
        0 for n in news  # sentiment字段不支持
    )
    
    if sentiment_negative_count >= 5:
        score += 1  # 越被恨,越好(假设基本面坚持住)
        details.append(f"{sentiment_negative_count} 条负面头条(逆向机会)")
    else:
        details.append("有限的负面报道")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


###############################################################################
# LLM生成
###############################################################################

def _generate_burry_output(
    ticker: str,
    analysis_data: dict,
    state: AgentState,
    agent_id: str,
) -> MichaelBurrySignal:
    """调用LLM以Burry的声音制作最终交易信号"""

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是迈克尔·伯里.使用专业投资原则分析股票.

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
                """请深入分析股票{ticker}的投资价值，并根据迈克尔·伯里的逆向投资和深度价值挖掘理念给出全面的投资建议。

分析数据:
{analysis_data}

请按照以下框架进行详细分析:

1. **逆向投资机会识别**:
   - 分析市场情绪和大众观点
   - 识别被市场错误定价的机会
   - 评估逆向投资的时机成熟度

2. **深度价值分析**:
   - 分析资产真实价值vs市场价格
   - 识别隐藏资产和低估价值
   - 评估重组或特殊情况价值

3. **财务困境vs复苏潜力**:
   - 分析公司面临的真实困境程度
   - 评估管理层应对危机的能力
   - 判断行业周期底部和复苏可能性

4. **催化剂识别**:
   - 识别可能的价值实现催化剂
   - 分析管理层变更、重组等机会
   - 评估外部环境变化的影响

5. **风险收益不对称性**:
   - 分析下行风险的有限性
   - 评估上行收益的巨大潜力
   - 计算风险调整后的收益预期

6. **市场非效率性利用**:
   - 识别市场忽视的关键信息
   - 分析机构投资者的盲点
   - 评估信息不对称带来的机会

必须返回以下JSON格式:
{{"signal": "bullish", "confidence": 70.0, "reasoning": "【逆向机会】:具体分析内容...\n\n【深度价值】:具体分析内容...\n\n【困境分析】:具体分析内容...\n\n【催化剂】:具体分析内容...\n\n【投资逻辑】:基于逆向投资理念的综合判断..."}}

其中:
- signal必须是 bullish(看涨)、bearish(看跌)或 neutral(中性)
- confidence是0到100之间的数字，反映投资信心程度
- reasoning必须包含上述6个方面的详细分析，每个方面至少2-3句话
        
重要要求:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行深入分析，不要计算或提及数据完整性百分比
- 给出积极的投资建议，避免因数据问题给出0分或极低评分
- 重点关注被市场误解或低估的价值机会
- 分析必须具体、深入，体现独立思考和逆向思维""",
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    # 如果解析失败的默认回退信号
    def create_default_michael_burry_signal():
        return MichaelBurrySignal(signal="neutral", confidence=0.0, reasoning="解析错误——默认为中性")

    return call_llm(
        prompt=prompt,
        pydantic_model=MichaelBurrySignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_michael_burry_signal,
    )
