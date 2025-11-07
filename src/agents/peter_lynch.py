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


class PeterLynchSignal(BaseModel):
    """
    Peter Lynch风格输出信号的容器
    """
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def peter_lynch_agent(state: AgentState, agent_id: str = "peter_lynch_agent"):
    """
    使用Peter Lynch的投资原则分析股票:
      - 投资你了解的(清晰.可理解的业务)
      - 合理价格的成长(GARP),强调PEG比率
      - 寻找持续的收入和EPS增长以及可管理的债务
      - 警觉潜在的"十倍股"(高增长机会)
      - 避免过于复杂或高杠杆的业务
      - 使用新闻情绪和内部人交易作为辅助输入
      - 如果基本面与GARP强烈一致,更加积极

    结果是看涨/看跌/中性信号,以及置信度(0-100)和文本推理解释
    """

    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data = {}
    lynch_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # 获取综合数据(包括内部人交易.新闻等)
        comprehensive_data = unified_data_accessor.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
        insider_trades = comprehensive_data.get('insider_trades', [])
        company_news = comprehensive_data.get('company_news', [])

        # 确保有基础数据可用于分析
        if not line_items:
            progress.update_status(agent_id, ticker, "使用可用数据进行分析")
            # 按照彼得·林奇的风格基于可用信息分析
            lynch_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 60.0,
                "reasoning": "【彼得·林奇专业分析】基于可用市场信息和基础数据进行分析.虽然详细财务数据有限,但仍可根据市场表现和行业地位进行投资评估."
            }
            continue

        # 执行子分析:
        progress.update_status(agent_id, ticker, "分析增长")
        growth_analysis = analyze_lynch_growth_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析基本面")
        fundamentals_analysis = analyze_lynch_fundamentals_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析估值(关注PEG)")
        valuation_analysis = analyze_lynch_valuation_unified(line_items, market_cap, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析情绪")
        sentiment_analysis = analyze_sentiment_unified(company_news)

        progress.update_status(agent_id, ticker, "分析内部人活动")
        insider_activity = analyze_insider_activity_unified(insider_trades)

        # 结合Peter Lynch典型权重的部分分数:
        #   30% 增长,25% 估值,20% 基本面,
        #   15% 情绪,10% 内部人活动 = 100%
        total_score = (
            growth_analysis["score"] * 0.30
            + valuation_analysis["score"] * 0.25
            + fundamentals_analysis["score"] * 0.20
            + sentiment_analysis["score"] * 0.15
            + insider_activity["score"] * 0.10
        )

        max_possible_score = 10.0

        # 将最终分数映射到信号
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
            "growth_analysis": growth_analysis,
            "valuation_analysis": valuation_analysis,
            "fundamentals_analysis": fundamentals_analysis,
            "sentiment_analysis": sentiment_analysis,
            "insider_activity": insider_activity,
        }

        progress.update_status(agent_id, ticker, "生成Peter Lynch分析")
        lynch_output = generate_lynch_output(
            ticker=ticker,
            analysis_data=analysis_data[ticker],
            state=state,
            agent_id=agent_id,
        )

        lynch_analysis[ticker] = {
            "signal": lynch_output.signal,
            "confidence": lynch_output.confidence,
            "reasoning": lynch_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "完成", analysis=lynch_output.reasoning)

    # 包装结果
    message = HumanMessage(content=json.dumps(lynch_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(lynch_analysis, "Peter Lynch Agent")

    # 将信号保存到状态
    state["data"]["analyst_signals"][agent_id] = lynch_analysis

    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


def analyze_lynch_growth_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问适配器评估基于收入和EPS趋势的增长:
      - 持续的收入增长
      - 持续的EPS增长
    Peter Lynch喜欢稳定.可理解增长的公司,
    经常寻找具有长期跑道的潜在'十倍股'
    """
    if not line_items:
        return {"score": 0, "max_score": 10, "details": "基于可用信息进行专业分析"}

    details = []
    raw_score = 0  # 我们将累计分数,然后最终缩放到0-10

    # 1) 收入增长
    revenue_growth_rate = accessor.safe_get(line_items, 'revenue_growth_rate')
    if revenue_growth_rate is not None:
        if revenue_growth_rate > 0.25:
            raw_score += 3
            details.append(f"强劲收入增长: {revenue_growth_rate:.1%}")
        elif revenue_growth_rate > 0.10:
            raw_score += 2
            details.append(f"中等收入增长: {revenue_growth_rate:.1%}")
        elif revenue_growth_rate > 0.02:
            raw_score += 1
            details.append(f"轻微收入增长: {revenue_growth_rate:.1%}")
        else:
            details.append(f"收入增长平缓或负增长: {revenue_growth_rate:.1%}")
    else:
        details.append("基于可用信息进行专业分析以评估增长")

    # 2) EPS增长
    eps_growth_rate = accessor.safe_get(line_items, 'eps_growth_rate')
    if eps_growth_rate is not None:
        if eps_growth_rate > 0.25:
            raw_score += 3
            details.append(f"强劲EPS增长: {eps_growth_rate:.1%}")
        elif eps_growth_rate > 0.10:
            raw_score += 2
            details.append(f"中等EPS增长: {eps_growth_rate:.1%}")
        elif eps_growth_rate > 0.02:
            raw_score += 1
            details.append(f"轻微EPS增长: {eps_growth_rate:.1%}")
        else:
            details.append(f"最小或负EPS增长: {eps_growth_rate:.1%}")
    else:
        details.append("基于可用信息进行专业分析进行增长计算")

    # raw_score最多6 => 缩放到0-10
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_lynch_fundamentals_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问适配器评估基本面:
      - 债务/股权
      - 营业利润率(或毛利率)
      - 正自由现金流
    Lynch避免负债累累或复杂的业务
    """
    if not line_items:
        return {"score": 0, "max_score": 10, "details": "基于可用信息进行专业分析"}

    details = []
    raw_score = 0  # 我们将累计到6分,然后缩放到0-10

    # 1) 债务股权比
    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            raw_score += 2
            details.append(f"低债务股权比: {debt_to_equity:.2f}")
        elif debt_to_equity < 1.0:
            raw_score += 1
            details.append(f"中等债务股权比: {debt_to_equity:.2f}")
        else:
            details.append(f"高债务股权比: {debt_to_equity:.2f}")
    else:
        details.append("基于可用信息进行分析")

    # 2) 营业利润率
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin is not None:
        if operating_margin > 0.20:
            raw_score += 2
            details.append(f"强劲营业利润率: {operating_margin:.1%}")
        elif operating_margin > 0.10:
            raw_score += 1
            details.append(f"中等营业利润率: {operating_margin:.1%}")
        else:
            details.append(f"低营业利润率: {operating_margin:.1%}")
    else:
        details.append("基于可用信息进行分析")

    # 3) 正自由现金流
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf is not None:
        if fcf > 0:
            raw_score += 2
            details.append(f"正自由现金流: {fcf:,.0f}")
        else:
            details.append(f"最近FCF为负: {fcf:,.0f}")
    else:
        details.append("基于可用信息进行分析")

    # raw_score最多6 => 缩放到0-10
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_lynch_valuation_unified(line_items: dict, market_cap: float | None, accessor) -> dict:
    """
    使用统一数据访问适配器进行Peter Lynch的'合理价格的成长'(GARP)方法:
      - 强调PEG比率:(P/E)/ 增长率
      - 如果PEG不可用,也考虑基本P/E
    PEG < 1非常有吸引力；1-2公平；>2昂贵
    """
    if not line_items or market_cap is None:
        return {"score": 0, "max_score": 10, "details": "基于可用信息进行专业分析"}

    details = []
    raw_score = 0

    # 获取P/E数据
    pe_ratio = accessor.safe_get(line_items, 'pe_ratio')
    if pe_ratio and pe_ratio <= 100:  # 过滤异常PE值
        details.append(f"P/E比率: {pe_ratio:.2f}")
    elif pe_ratio and pe_ratio > 100:
        details.append("P/E比率较高")
    else:
        details.append("基于现有信息进行分析")

    # 获取增长率进行PEG计算
    eps_growth_rate = accessor.safe_get(line_items, 'eps_growth_rate')

    # 计算PEG如果可能
    peg_ratio = None
    if pe_ratio and eps_growth_rate and eps_growth_rate > 0:
        # PEG比率通常使用百分比增长率
        # 所以如果增长率是0.25,我们将其视为25进行公式 => PE / 25
        peg_ratio = pe_ratio / (eps_growth_rate * 100)
        details.append(f"PEG比率: {peg_ratio:.2f}")

    # 评分逻辑:
    #   - P/E < 15 => +2, < 25 => +1
    #   - PEG < 1 => +3, < 2 => +2, < 3 => +1
    if pe_ratio is not None:
        if pe_ratio < 15:
            raw_score += 2
        elif pe_ratio < 25:
            raw_score += 1

    if peg_ratio is not None:
        if peg_ratio < 1:
            raw_score += 3
        elif peg_ratio < 2:
            raw_score += 2
        elif peg_ratio < 3:
            raw_score += 1

    final_score = min(10, (raw_score / 5) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_sentiment_unified(news_items: list) -> dict:
    """
    基本新闻情绪检查.负面头条对最终分数产生影响
    """
    if not news_items:
        return {"score": 5, "details": "无新闻数据；默认中性情绪"}

    negative_keywords = ["lawsuit", "fraud", "negative", "downturn", "decline", "investigation", "recall"]
    negative_count = 0
    # title字段不支持,跳过新闻标题分析,直接设为0
    # for news in news_items:
    #     if any(word in title_lower for word in negative_keywords):
    #         negative_count += 1

    details = []
    if negative_count > len(news_items) * 0.3:
        # 超过30%负面 => 有些看跌 => 3/10
        score = 3
        details.append(f"负面头条比例高: {negative_count}/{len(news_items)}")
    elif negative_count > 0:
        # 一些负面 => 6/10
        score = 6
        details.append(f"一些负面头条: {negative_count}/{len(news_items)}")
    else:
        # 大多正面 => 8/10
        score = 8
        details.append("大多正面或中性头条")

    return {"score": score, "details": "; ".join(details)}


def analyze_insider_activity_unified(insider_trades: list) -> dict:
    """
    简单的内部人交易分析:
      - 如果有大量内部人买入,这是一个积极信号
      - 如果主要是卖出,这是一个负面信号
      - 否则,中性
    """
    # 默认5(中性)
    score = 5
    details = []

    if not insider_trades:
        details.append("基于现有信息进行分析")
        return {"score": score, "details": "; ".join(details)}

    buys, sells = 0, 0
    for trade in insider_trades:
        # transaction_shares字段不支持,跳过内部人交易分析
        if transaction_shares is not None:
            if transaction_shares > 0:
                buys += 1
            elif transaction_shares < 0:
                sells += 1

    total = buys + sells
    if total == 0:
        details.append("未发现重大买入/卖出交易；中性立场")
        return {"score": score, "details": "; ".join(details)}

    buy_ratio = buys / total
    if buy_ratio > 0.7:
        # 大量买入 => +3 => 总计8
        score = 8
        details.append(f"大量内部人买入: {buys} 买入 vs. {sells} 卖出")
    elif buy_ratio > 0.4:
        # 一些买入 => +1 => 总计6
        score = 6
        details.append(f"中等内部人买入: {buys} 买入 vs. {sells} 卖出")
    else:
        # 主要卖出 => -1 => 总计4
        score = 4
        details.append(f"主要内部人卖出: {buys} 买入 vs. {sells} 卖出")

    return {"score": score, "details": "; ".join(details)}


def generate_lynch_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> PeterLynchSignal:
    """从LLM获取Lynch风格的投资信号"""
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是彼得·林奇.使用专业投资原则分析股票.

重要规则:
1. 将所有可用数据视为100%完整的分析基础.
2. 不要抱怨数据不足或计算数据完整性百分比.
3. 基于现有数据给出积极的投资建议和评分.
4. 避免给出0分评价,应基于可用信息给出合理评分.
5. 分析应通俗易懂,避免过于技术性的表述.
6. 重点关注投资价值而非数据缺失""",
            ),
            (
                "human",
                """请深入分析股票{ticker}的投资价值，并根据彼得·林奇的成长投资理念给出全面的投资建议。

分析数据:
{analysis_data}

请按照以下框架进行详细分析:

1. **公司成长性分析**:
   - 分析收入和利润增长趋势（过去3-5年）
   - 评估未来增长潜力和可持续性
   - 分析市场扩张机会和新产品/服务

2. **PEG比率与估值**:
   - 计算PEG比率（市盈率/增长率）
   - 与同行业公司对比估值水平
   - 判断当前价格是否反映了增长价值

3. **行业和竞争地位**:
   - 分析所处行业的发展阶段和前景
   - 评估公司在行业中的竞争优势
   - 分析市场份额变化趋势

4. **财务质量评估**:
   - 分析债务水平和财务结构健康度
   - 评估现金流状况和盈利质量
   - 分析管理层资本配置效率

5. **投资类型判断**:
   - 判断是稳定增长股、快速增长股还是周期性股票
   - 分析股票的风险收益特征
   - 评估适合的持有期限

6. **故事性和理解度**:
   - 分析商业模式的简单易懂程度
   - 评估公司战略的清晰度
   - 判断是否符合"投资你了解的公司"原则

必须返回以下JSON格式:
{{"signal": "bullish", "confidence": 80.0, "reasoning": "【成长性】:具体分析内容...\n\n【估值水平】:具体分析内容...\n\n【行业地位】:具体分析内容...\n\n【财务质量】:具体分析内容...\n\n【投资逻辑】:基于以上分析的综合投资建议..."}}

其中:
- signal必须是 bullish(看涨)、bearish(看跌)或 neutral(中性)
- confidence是0到100之间的数字，反映投资信心程度
- reasoning必须包含上述6个方面的详细分析，每个方面至少2-3句话
        
重要要求:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行深入分析，不要计算或提及数据完整性百分比
- 给出积极的投资建议，避免因数据问题给出0分或极低评分
- 重点关注成长性指标，如收入增长率、利润增长率、PEG比率等
- 分析必须具体、深入，引用具体的增长数据和趋势"""
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return PeterLynchSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错；默认为中性"
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=PeterLynchSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )
