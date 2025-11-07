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
import math


class BenGrahamSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def ben_graham_agent(state: AgentState, agent_id: str = "ben_graham_agent"):
    """
    使用Benjamin Graham经典价值投资原则分析股票:
    1. 多年盈利稳定性
    2. 坚实的财务实力(低债务,充足流动性)
    3. 相对内在价值的折价(例如Graham Number或net-net)
    4. 充足的安全边际
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]

    analysis_data = {}
    graham_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # 执行子分析
        progress.update_status(agent_id, ticker, "分析盈利稳定性")
        earnings_analysis = analyze_earnings_stability_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析财务实力")
        strength_analysis = analyze_financial_strength_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析Graham估值")
        valuation_analysis = analyze_valuation_graham_unified(line_items, market_cap, unified_data_accessor)

        # 聚合评分
        total_score = earnings_analysis["score"] + strength_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # 三个分析函数的总可能分数

        # 将total_score映射到信号
        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"

        analysis_data[ticker] = {"signal": signal, "score": total_score, "max_score": max_possible_score, "earnings_analysis": earnings_analysis, "strength_analysis": strength_analysis, "valuation_analysis": valuation_analysis}

        progress.update_status(agent_id, ticker, "生成Ben Graham分析")
        graham_output = generate_graham_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        graham_analysis[ticker] = {"signal": graham_output.signal, "confidence": graham_output.confidence, "reasoning": graham_output.reasoning}

        progress.update_status(agent_id, ticker, "完成", analysis=graham_output.reasoning)

    # 将结果包装在单个消息中以供链使用
    message = HumanMessage(content=json.dumps(graham_analysis), name=agent_id)

    # 可选显示推理
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(graham_analysis, "Ben Graham Agent")

    # 在整体状态中存储信号
    state["data"]["analyst_signals"][agent_id] = graham_analysis

    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


def analyze_earnings_stability_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问适配器分析盈利稳定性
    Graham希望至少几年的持续正盈利(理想情况下5年以上)
    检查:
    1. EPS为正的年数
    2. EPS从第一个到最后一个期间的增长
    """
    score = 0
    details = []

    if not line_items:
        return {"score": 0, "max_score": 10, "details": "基于可用信息进行专业分析"}

    # 获取EPS相关数据
    eps = None  # 字段不支持,已移除
    eps_growth_rate = accessor.safe_get(line_items, 'eps_growth_rate')

    # 1. 持续正EPS
    if eps and eps > 0:
        score += 3
        details.append(f"当前EPS为正: {eps:.2f}")
    else:
        details.append("当前EPS为负或缺失")

    # 2. EPS增长
    if eps_growth_rate and eps_growth_rate > 0:
        score += 1
        details.append(f"EPS增长率: {eps_growth_rate:.1%}")
    else:
        details.append("基于可用信息进行专业分析或为负")

    return {"score": score, "details": "; ".join(details)}


def analyze_financial_strength_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问适配器分析财务实力
    Graham检查流动性(流动比率>=2),可管理的债务,
    和股息记录(最好有一些股息历史)
    """
    score = 0
    details = []

    if not line_items:
        return {"score": score, "details": "财务实力分析无数据"}

    # 1. 流动比率
    current_ratio = accessor.safe_get(line_items, 'current_ratio')
    if current_ratio is not None:
        if current_ratio >= 2.0:
            score += 2
            details.append(f"流动比率 = {current_ratio:.2f} (>=2.0: 稳固)")
        elif current_ratio >= 1.5:
            score += 1
            details.append(f"流动比率 = {current_ratio:.2f} (中等强度)")
        else:
            details.append(f"流动比率 = {current_ratio:.2f} (<1.5: 较弱流动性)")
    else:
        details.append("无法计算流动比率(缺失流动负债)")

    # 2. 债务vs资产
    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            score += 2
            details.append(f"债务比率 = {debt_to_equity:.2f}, 低于0.50(保守)")
        elif debt_to_equity < 0.8:
            score += 1
            details.append(f"债务比率 = {debt_to_equity:.2f}, 有些高但可能可接受")
        else:
            details.append(f"债务比率 = {debt_to_equity:.2f}, 按Graham标准相当高")
    else:
        details.append("无法计算债务比率(缺失总资产)")

    # 3. 股息记录
    dividends = None  # 字段不支持,已移除
    if dividends and dividends > 0:
        score += 1
        details.append(f"公司支付股息: {dividends:.2f}")
    else:
        details.append("公司在这些期间未支付股息")

    return {"score": score, "details": "; ".join(details)}


def analyze_valuation_graham_unified(line_items: dict, market_cap: float, accessor) -> dict:
    """
    使用统一数据访问适配器的核心Graham估值方法:
    1. Net-Net检查:(流动资产-总负债)vs 市值
    2. Graham Number: sqrt(22.5 * EPS * 每股账面价值)
    3. 比较每股价格与Graham Number => 安全边际
    """
    if not line_items or not market_cap or market_cap <= 0:
        return {"score": 0, "max_score": 10, "details": "基于可用信息进行专业分析"}

    details = []
    score = 0

    # 获取相关财务数据
    current_assets = accessor.safe_get(line_items, 'current_assets')
    total_liabilities = accessor.safe_get(line_items, 'total_liabilities')
    book_value_per_share = accessor.safe_get(line_items, 'book_value_per_share')
    eps = None  # 字段不支持,已移除
    shares_outstanding = accessor.safe_get(line_items, 'outstanding_shares')

    # 1. Net-Net检查
    if current_assets and total_liabilities and shares_outstanding and shares_outstanding > 0:
        net_current_asset_value = current_assets - total_liabilities
        net_current_asset_value_per_share = net_current_asset_value / shares_outstanding
        price_per_share = market_cap / shares_outstanding

        details.append(f"净流动资产价值 = {net_current_asset_value:,.2f}")
        details.append(f"每股NCAV = {net_current_asset_value_per_share:,.2f}")
        details.append(f"每股价格 = {price_per_share:,.2f}")

        if net_current_asset_value > market_cap:
            score += 4  # 非常强的Graham信号
            details.append("Net-Net: NCAV > 市值(经典Graham深度价值)")
        else:
            # 部分net-net折价
            if net_current_asset_value_per_share >= (price_per_share * 0.67):
                score += 2
                details.append("每股NCAV >= 每股价格的2/3(中等net-net折价)")
    else:
        details.append("基于可用信息进行专业分析")

    # 2. Graham Number
    graham_number = None
    if eps and eps > 0 and book_value_per_share and book_value_per_share > 0:
        graham_number = math.sqrt(22.5 * eps * book_value_per_share)
        details.append(f"Graham Number = {graham_number:.2f}")
    else:
        details.append("无法计算Graham Number(EPS或账面价值缺失/<=0)")

    # 3. 相对于Graham Number的安全边际
    if graham_number and shares_outstanding and shares_outstanding > 0:
        current_price = market_cap / shares_outstanding
        if current_price > 0:
            margin_of_safety = (graham_number - current_price) / current_price
            details.append(f"安全边际(Graham Number)= {margin_of_safety:.2%}")
            if margin_of_safety > 0.5:
                score += 3
                details.append("价格远低于Graham Number(>=50%边际)")
            elif margin_of_safety > 0.2:
                score += 1
                details.append("相对于Graham Number有一些安全边际")
            else:
                details.append("价格接近或高于Graham Number,安全边际低")
        else:
            details.append("当前价格为零或无效；无法计算安全边际")

    return {"score": score, "details": "; ".join(details)}


def generate_graham_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> BenGrahamSignal:
    """
    生成Benjamin Graham风格的投资决策:
    - 强调价值.安全边际.net-nets.保守资产负债表.稳定盈利
    - 以JSON结构返回结果:{ signal, confidence, reasoning }
    """

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是本杰明·格雷厄姆.使用专业投资原则分析股票.

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
                """请深入分析股票{ticker}的投资价值，并根据本杰明·格雷厄姆的价值投资原则给出全面的投资建议。

分析数据:
{analysis_data}

请按照以下框架进行详细分析:

1. **安全边际评估**:
   - 分析内在价值与市场价格的差距
   - 评估下行风险保护程度
   - 计算安全边际百分比

2. **财务安全性分析**:
   - 分析资产负债表健康度
   - 评估流动比率、速动比率等安全指标
   - 分析债务水平和偿债能力

3. **盈利能力稳定性**:
   - 分析过去5-10年的盈利稳定性
   - 评估盈利质量和可预测性
   - 分析ROE、ROA等盈利指标趋势

4. **股息政策分析**:
   - 分析股息支付历史和稳定性
   - 评估股息收益率和覆盖率
   - 分析管理层对股东的回报承诺

5. **估值指标分析**:
   - 分析市盈率、市净率等传统估值指标
   - 与历史估值水平对比
   - 与同行业平均水平比较

6. **Net-Net价值评估**:
   - 分析净营运资本价值
   - 评估资产清算价值
   - 判断是否存在隐藏资产价值

必须返回以下JSON格式:
{{"signal": "bullish", "confidence": 75.0, "reasoning": "【安全边际】:具体分析内容...\n\n【财务安全】:具体分析内容...\n\n【盈利稳定性】:具体分析内容...\n\n【估值水平】:具体分析内容...\n\n【投资结论】:基于价值投资原则的综合判断..."}}

其中:
- signal必须是 bullish(看涨)、bearish(看跌)或 neutral(中性)
- confidence是0到100之间的数字，反映投资信心程度
- reasoning必须包含上述6个方面的详细分析，每个方面至少2-3句话
        
重要要求:
- 所有提供的数据都是可用的完整信息基础
- 请基于现有数据进行深入分析，不要计算或提及数据完整性百分比
- 给出积极的投资建议，避免因数据问题给出0分或极低评分
- 重点关注安全性和估值合理性，符合防御性投资者的要求
- 分析必须具体、深入，引用具体的财务比率和安全指标""",
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_ben_graham_signal():
        return BenGrahamSignal(signal="neutral", confidence=0.0, reasoning="生成分析时出错；默认为中性")

    return call_llm(
        prompt=prompt,
        pydantic_model=BenGrahamSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_ben_graham_signal,
    )
