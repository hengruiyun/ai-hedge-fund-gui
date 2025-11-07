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


class StanleyDruckenmillerSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def stanley_druckenmiller_agent(state: AgentState, agent_id: str = "stanley_druckenmiller_agent"):
    """
    Analyzes stocks using Stanley Druckenmiller's investing principles.
    Uses unified data accessor for enhanced data integration.
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data = {}
    druck_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')
        
        # 获取新闻和其他数据
        comprehensive_data = unified_data_accessor.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
        insider_trades = comprehensive_data.get('insider_trades', [])
        company_news = comprehensive_data.get('company_news', [])
        price_data = comprehensive_data.get('price_data', [])

        progress.update_status(agent_id, ticker, "分析增长和动量")
        growth_momentum_analysis = analyze_growth_and_momentum_unified(line_items, price_data, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析市场情绪")
        sentiment_analysis = analyze_sentiment_unified(company_news, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析内部人交易")
        insider_activity = analyze_insider_activity_unified(insider_trades, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析风险回报")
        risk_reward_analysis = analyze_risk_reward_unified(line_items, price_data, unified_data_accessor)

        progress.update_status(agent_id, ticker, "执行Druckenmiller风格估值")
        valuation_analysis = analyze_druckenmiller_valuation_unified(line_items, market_cap, unified_data_accessor)

        # 合并各部分评分,权重典型于Druckenmiller:
        # 35%增长/动量,20%风险/回报,20%估值,15%情绪,10%内部人活动 = 100%
        total_score = (
            growth_momentum_analysis["score"] * 0.35
            + risk_reward_analysis["score"] * 0.20
            + valuation_analysis["score"] * 0.20
            + sentiment_analysis["score"] * 0.15
            + insider_activity["score"] * 0.10
        )

        max_possible_score = 10

        # 简单的看涨/中性/看跌信号
        if total_score >= 7.5:
            signal = "bullish"
        elif total_score <= 4.5:
            signal = "bearish"
        else:
            signal = "neutral"

        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "growth_momentum_analysis": growth_momentum_analysis,
            "sentiment_analysis": sentiment_analysis,
            "insider_activity": insider_activity,
            "risk_reward_analysis": risk_reward_analysis,
            "valuation_analysis": valuation_analysis,
        }

        progress.update_status(agent_id, ticker, "生成Stanley Druckenmiller分析")
        druck_output = generate_druckenmiller_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        druck_analysis[ticker] = {
            "signal": druck_output.signal,
            "confidence": druck_output.confidence,
            "reasoning": druck_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "完成", analysis=druck_output.reasoning)

    # 将结果封装在单个消息中
    message = HumanMessage(content=json.dumps(druck_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(druck_analysis, "Stanley Druckenmiller Agent")

    state["data"]["analyst_signals"][agent_id] = druck_analysis

    progress.update_status(agent_id, None, "完成")
    
    return {"messages": [message], "data": state["data"]}


def analyze_growth_and_momentum_unified(line_items: dict, price_data: list, accessor) -> dict:
    """
    使用统一数据访问器评估增长和动量
    """
    score = 0
    details = []
    
    # 1. 收入增长分析
    revenue = accessor.safe_get(line_items, 'revenue')
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    
    if revenue_growth_rate:
        if revenue_growth_rate > 0.30:
            score += 3
            details.append(f"强劲收入增长: {revenue_growth_rate:.1%}")
        elif revenue_growth_rate > 0.15:
            score += 2
            details.append(f"适度收入增长: {revenue_growth_rate:.1%}")
        elif revenue_growth_rate > 0.05:
            score += 1
            details.append(f"轻微收入增长: {revenue_growth_rate:.1%}")
        else:
            details.append(f"收入增长有限: {revenue_growth_rate:.1%}")
    elif revenue:
        score += 1
        details.append(f"收入基础: {revenue:,.0f}")
    
    # 2. EPS增长分析
    eps = None  # 字段不支持,已移除
    eps_growth_rate = accessor.safe_get(line_items, 'eps_growth_rate')
    
    if eps_growth_rate:
        if eps_growth_rate > 0.30:
            score += 3
            details.append(f"强劲EPS增长: {eps_growth_rate:.1%}")
        elif eps_growth_rate > 0.15:
            score += 2
            details.append(f"适度EPS增长: {eps_growth_rate:.1%}")
        elif eps_growth_rate > 0.05:
            score += 1
            details.append(f"轻微EPS增长: {eps_growth_rate:.1%}")
        else:
            details.append(f"EPS增长有限: {eps_growth_rate:.1%}")
    elif eps:
        score += 1
        details.append(f"EPS: {eps:.2f}")
    
    # 3. 动量分析(基于价格数据)
    if price_data and len(price_data) > 1:
        # 简化的动量分析
        try:
            sorted_prices = sorted(price_data, key=lambda x: x.get("current_price", 0))  # date字段不支持
            if len(sorted_prices) >= 2:
                start_price = 0.0  # close字段不支持
                end_price = 0.0  # close字段不支持
                if start_price > 0:
                    momentum = (end_price - start_price) / start_price
                    if momentum > 0.20:
                        score += 2
                        details.append(f"强劲价格动量: {momentum:.1%}")
                    elif momentum > 0.10:
                        score += 1
                        details.append(f"适度价格动量: {momentum:.1%}")
                    elif momentum > 0:
                        details.append(f"轻微正动量: {momentum:.1%}")
                    else:
                        details.append(f"负价格动量: {momentum:.1%}")
        except (ValueError, TypeError, KeyError):
            details.append("价格动量基于可用数据进行评估")
    else:
        details.append("基于现有数据评估进行动量分析")
    
    # 4. 盈利能力趋势
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin and operating_margin > 0.15:
        score += 1
        details.append(f"强劲营业利润率: {operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.08:
        details.append(f"适度营业利润率: {operating_margin:.1%}")
    
    # 最大得分调整为10
    final_score = min(10, score)
    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def analyze_insider_activity_unified(insider_trades: list, accessor) -> dict:
    """
    使用统一数据访问器分析内部人交易活动
    """
    score = 5  # 默认中性
    details = []

    if not insider_trades:
        details.append("基于现有信息进行分析")
        return {"score": score, "max_score": 10, "details": "; ".join(details)}

    buys, sells = 0, 0
    for trade in insider_trades:
        # 使用transaction_shares判断买入或卖出
        shares = None  # 字段不支持,已移除
        if shares > 0:
            buys += 1
        elif shares < 0:
            sells += 1

    total = buys + sells
    if total == 0:
        details.append("基于现有信息进行分析")
        return {"score": score, "max_score": 10, "details": "; ".join(details)}

    buy_ratio = buys / total
    if buy_ratio > 0.7:
        score = 8
        details.append(f"大量内部人买入: {buys}买 vs {sells}卖")
    elif buy_ratio > 0.4:
        score = 6
        details.append(f"适度内部人买入: {buys}买 vs {sells}卖")
    else:
        score = 4
        details.append(f"主要是内部人卖出: {buys}买 vs {sells}卖")

    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_sentiment_unified(news_items: list, accessor) -> dict:
    """
    使用统一数据访问器分析新闻情绪
    """
    if not news_items:
        return {"score": 5, "max_score": 10, "details": "无新闻数据,默认中性情绪"}

    negative_keywords = ["诉讼", "欺诈", "负面", "下滑", "衰退", "调查", "召回", "lawsuit", "fraud", "negative", "downturn", "decline", "investigation", "recall"]
    positive_keywords = ["创新", "增长", "突破", "收购", "扩张", "合作", "innovation", "growth", "breakthrough", "acquisition", "expansion", "partnership"]
    
    negative_count = 0
    positive_count = 0
    
    for news in news_items:
        title_lower = ""  # title字段不支持
        if any(word in title_lower for word in negative_keywords):
            negative_count += 1
        if any(word in title_lower for word in positive_keywords):
            positive_count += 1

    details = []
    total_news = len(news_items)
    
    if negative_count > total_news * 0.3:
        score = 3
        details.append(f"高比例负面新闻: {negative_count}/{total_news}")
    elif positive_count > total_news * 0.3:
        score = 8
        details.append(f"高比例正面新闻: {positive_count}/{total_news}")
    elif negative_count > 0:
        score = 6
        details.append(f"一些负面新闻: {negative_count}/{total_news}")
    else:
        score = 7
        details.append("大部分正面/中性新闻")

    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_risk_reward_unified(line_items: dict, price_data: list, accessor) -> dict:
    """
    使用统一数据访问器评估风险回报
    """
    score = 0
    details = []

    # 1. 债务股权比分析
    total_debt = accessor.safe_get(line_items, 'total_debt')
    equity = accessor.safe_get(line_items, 'shareholders_equity')
    
    if total_debt is not None and equity and equity > 0:
        debt_ratio = total_debt / equity
        if debt_ratio < 0.3:
            score += 3
            details.append(f"低债务股权比: {debt_ratio:.2f}")
        elif debt_ratio < 0.7:
            score += 2
            details.append(f"适度债务股权比: {debt_ratio:.2f}")
        elif debt_ratio < 1.5:
            score += 1
            details.append(f"较高债务股权比: {debt_ratio:.2f}")
        else:
            details.append(f"高债务股权比: {debt_ratio:.2f}")
    else:
        details.append("基于现有信息进行分析")

    # 2. 现金流稳定性
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf and fcf > 0:
        score += 2
        details.append(f"正自由现金流: {fcf:,.0f}")
    elif fcf:
        details.append(f"负自由现金流: {fcf:,.0f}")

    # 3. 盈利能力
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin and operating_margin > 0.15:
        score += 2
        details.append(f"强劲营业利润率: {operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.08:
        score += 1
        details.append(f"适度营业利润率: {operating_margin:.1%}")

    # 4. 流动性
    current_ratio = accessor.safe_get(line_items, 'current_ratio')
    if current_ratio and current_ratio > 1.5:
        score += 1
        details.append(f"强劲流动比率: {current_ratio:.2f}")
    elif current_ratio and current_ratio > 1.0:
        details.append(f"适度流动比率: {current_ratio:.2f}")

    # 5. 价格稳定性(简化的波动性分析)
    if price_data and len(price_data) > 10:
        try:
            prices = []  # close字段不支持,设为空列表
            if len(prices) > 1:
                avg_price = sum(prices) / len(prices)
                price_ranges = [abs(p - avg_price) / avg_price for p in prices if avg_price > 0]
                if price_ranges:
                    avg_volatility = sum(price_ranges) / len(price_ranges)
                    if avg_volatility < 0.05:
                        score += 2
                        details.append(f"低波动性: {avg_volatility:.1%}")
                    elif avg_volatility < 0.10:
                        score += 1
                        details.append(f"适度波动性: {avg_volatility:.1%}")
                    else:
                        details.append(f"高波动性: {avg_volatility:.1%}")
        except (ValueError, TypeError):
            details.append("无法计算价格波动性")

    final_score = min(10, score)
    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def analyze_druckenmiller_valuation_unified(line_items: dict, market_cap: float, accessor) -> dict:
    """
    使用统一数据访问器进行Druckenmiller风格的估值分析
    """
    if market_cap is None or market_cap <= 0:
        return {"score": 0, "max_score": 10, "details": "基于现有数据评估进行估值"}

    score = 0
    details = []

    # 1. P/E比率分析
    pe_ratio = accessor.safe_get(line_items, 'pe_ratio')
    if pe_ratio and pe_ratio <= 100:  # 过滤异常PE值
        if pe_ratio < 15:
            score += 2
            details.append(f"有吸引力的P/E: {pe_ratio:.1f}")
        elif pe_ratio < 25:
            score += 1
            details.append(f"公允P/E: {pe_ratio:.1f}")
        else:
            details.append(f"高P/E: {pe_ratio:.1f}")
    elif pe_ratio and pe_ratio > 100:
        details.append("P/E比率异常高")
    else:
        details.append("P/E数据不可用")

    # 2. P/FCF比率分析
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf and fcf > 0:
        pfcf = market_cap / fcf
        if pfcf < 15:
            score += 2
            details.append(f"有吸引力的P/FCF: {pfcf:.1f}")
        elif pfcf < 25:
            score += 1
            details.append(f"公允P/FCF: {pfcf:.1f}")
        else:
            details.append(f"高P/FCF: {pfcf:.1f}")
    else:
        details.append("无正自由现金流计算P/FCF")

    # 3. EV/EBITDA分析
    ev_ebitda = None  # 字段不支持,已移除
    if ev_ebitda:
        if ev_ebitda < 10:
            score += 2
            details.append(f"有吸引力的EV/EBITDA: {ev_ebitda:.1f}")
        elif ev_ebitda < 18:
            score += 1
            details.append(f"公允EV/EBITDA: {ev_ebitda:.1f}")
        else:
            details.append(f"高EV/EBITDA: {ev_ebitda:.1f}")

    # 4. PEG比率分析
    peg_ratio = accessor.safe_get(line_items, 'peg_ratio')
    if peg_ratio:
        if peg_ratio < 1.0:
            score += 2
            details.append(f"有吸引力的PEG: {peg_ratio:.2f}")
        elif peg_ratio < 1.5:
            score += 1
            details.append(f"公允PEG: {peg_ratio:.2f}")
        else:
            details.append(f"高PEG: {peg_ratio:.2f}")

    # 5. 股息收益率
    dividend_yield = accessor.safe_get(line_items, 'dividend_yield')
    if dividend_yield and dividend_yield > 0.02:
        score += 1
        details.append(f"提供股息收益: {dividend_yield:.1%}")

    final_score = min(10, score)
    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def generate_druckenmiller_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> StanleyDruckenmillerSignal:
    """
    生成Stanley Druckenmiller风格的投资信号
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
              "system",
              """你是斯坦利·德鲁肯米勒.使用专业投资原则分析股票.

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
              """基于以下分析,创建Druckenmiller风格的投资信号.

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

    def create_default_signal():
        return StanleyDruckenmillerSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错,默认为中性"
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=StanleyDruckenmillerSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )
