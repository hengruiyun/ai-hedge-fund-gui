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


class BillAckmanSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def bill_ackman_agent(state: AgentState, agent_id: str = "bill_ackman_agent"):
    """
    Analyzes stocks using Bill Ackman's investing principles.
    Uses unified data accessor for enhanced data integration.
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]
    
    analysis_data = {}
    ackman_analysis = {}
    
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')
        
        progress.update_status(agent_id, ticker, "分析业务质量")
        quality_analysis = analyze_business_quality_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "分析财务纪律和资本结构")
        balance_sheet_analysis = analyze_financial_discipline_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "分析activism潜力")
        activism_analysis = analyze_activism_potential_unified(line_items, unified_data_accessor)
        
        progress.update_status(agent_id, ticker, "计算内在价值和安全边际")
        valuation_analysis = analyze_valuation_unified(line_items, market_cap, unified_data_accessor)
        
        # 合并各部分评分
        total_score = (
            quality_analysis["score"]
            + balance_sheet_analysis["score"]
            + activism_analysis["score"]
            + valuation_analysis["score"]
        )
        max_possible_score = 40  # 每个分析最多10分
        
        # 生成简单的买入/持有/卖出信号
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
            "quality_analysis": quality_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "activism_analysis": activism_analysis,
            "valuation_analysis": valuation_analysis
        }
        
        progress.update_status(agent_id, ticker, "生成Ackman风格分析")
        ackman_output = generate_ackman_output(
            ticker=ticker, 
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )
        
        ackman_analysis[ticker] = {
            "signal": ackman_output.signal,
            "confidence": ackman_output.confidence,
            "reasoning": ackman_output.reasoning
        }
        
        progress.update_status(agent_id, ticker, "完成", analysis=ackman_output.reasoning)
    
    # 将结果封装在单个消息中
    message = HumanMessage(
        content=json.dumps(ackman_analysis),
        name=agent_id
    )
    
    # 如果需要显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(ackman_analysis, "Bill Ackman Agent")
    
    # 添加信号到整体状态
    state["data"]["analyst_signals"][agent_id] = ackman_analysis

    progress.update_status(agent_id, None, "完成")

    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_business_quality_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问器分析业务质量
    评估高质量业务的关键特征:持续现金流生成.竞争护城河.品牌价值
    """
    score = 0
    details = []
    
    # 1. 收入增长分析
    revenue = accessor.safe_get(line_items, 'revenue')
    if revenue and revenue > 0:
        score += 2
        details.append(f"稳定收入基础: {revenue:,.0f}")
    
    # 2. 营业利润率分析
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    if operating_margin and operating_margin > 0.15:
        score += 3
        details.append(f"高营业利润率: {operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.10:
        score += 2
        details.append(f"良好营业利润率: {operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.05:
        score += 1
        details.append(f"适度营业利润率: {operating_margin:.1%}")
    
    # 3. 自由现金流生成能力
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf and fcf > 0:
        score += 2
        details.append(f"正自由现金流: {fcf:,.0f}")
        
        # FCF转换率分析
        net_income = accessor.safe_get(line_items, 'net_income')
        if net_income and net_income > 0:
            fcf_conversion = fcf / net_income
            if fcf_conversion > 1.0:
                score += 2
                details.append(f"优秀现金转换: FCF/净利润={fcf_conversion:.2f}")
            elif fcf_conversion > 0.8:
                score += 1
                details.append(f"良好现金转换: FCF/净利润={fcf_conversion:.2f}")
    else:
        details.append("基于可用现金流指标评估")
    
    # 4. ROE分析(使用计算值)
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe and roe > 0.15:
        score += 2
        details.append(f"高ROE显示竞争优势: {roe:.1%}")
    elif roe and roe > 0.10:
        score += 1
        details.append(f"适度ROE: {roe:.1%}")
    
    # 5. 品牌价值分析(通过毛利率体现)
    gross_margin = accessor.safe_get(line_items, 'gross_margin')
    if gross_margin and gross_margin > 0.40:
        score += 1
        details.append(f"高毛利率显示品牌价值: {gross_margin:.1%}")
    
    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_financial_discipline_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问器分析财务纪律和资本配置智慧
    """
    score = 0
    details = []
    
    # 1. 债务管理分析
    total_debt = accessor.safe_get(line_items, 'total_debt')
    equity = accessor.safe_get(line_items, 'shareholders_equity')
    
    if total_debt is not None and equity and equity > 0:
        debt_ratio = total_debt / equity
        if debt_ratio < 0.5:
            score += 3
            details.append(f"保守债务管理: 债务股权比{debt_ratio:.2f}")
        elif debt_ratio < 1.0:
            score += 2
            details.append(f"审慎债务管理: 债务股权比{debt_ratio:.2f}")
        elif debt_ratio < 2.0:
            score += 1
            details.append(f"适度债务水平: 债务股权比{debt_ratio:.2f}")
        else:
            details.append(f"高债务水平: 债务股权比{debt_ratio:.2f}")
    else:
        details.append("基于现有数据评估")
    
    # 2. 资本回报分析
    dividends = None  # 字段不支持,已移除
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    
    if dividends and fcf and fcf > 0:
        payout_ratio = abs(dividends) / fcf
        if 0.3 <= payout_ratio <= 0.6:
            score += 2
            details.append(f"平衡的分红政策: 派息率{payout_ratio:.1%}")
        elif payout_ratio < 0.3:
            score += 1
            details.append(f"保守分红,更多资本留存: 派息率{payout_ratio:.1%}")
        else:
            details.append(f"高派息率: {payout_ratio:.1%}")
    
    # 3. 现金管理
    cash = None  # 字段不支持,已移除
    total_assets = accessor.safe_get(line_items, 'total_assets')
    
    if cash and total_assets and total_assets > 0:
        cash_ratio = cash / total_assets
        if 0.05 <= cash_ratio <= 0.20:
            score += 2
            details.append(f"合理现金水平: 现金资产比{cash_ratio:.1%}")
        elif cash_ratio > 0.20:
            score += 1
            details.append(f"充足现金储备: 现金资产比{cash_ratio:.1%}")
    
    # 4. 股份回购分析
    shares = accessor.safe_get(line_items, 'outstanding_shares')
    if shares and shares > 0:
        score += 1
        details.append("股份数量信息可用,便于回购分析")
    
    # 5. 运营效率
    asset_turnover = accessor.safe_get(line_items, 'asset_turnover')
    if asset_turnover and asset_turnover > 1.0:
        score += 2
        details.append(f"高资产周转率: {asset_turnover:.2f}")
    elif asset_turnover and asset_turnover > 0.5:
        score += 1
        details.append(f"适度资产周转率: {asset_turnover:.2f}")
    
    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_activism_potential_unified(line_items: dict, accessor) -> dict:
    """
    使用统一数据访问器分析activism潜力
    Ackman经常在看到运营改善机会时进行activism投资
    """
    score = 0
    details = []
    
    # 1. 收入增长但利润率偏低的机会
    revenue = accessor.safe_get(line_items, 'revenue')
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    
    if revenue and operating_margin:
        if operating_margin < 0.08:  # 低运营利润率
            score += 2
            details.append(f"运营利润率较低({operating_margin:.1%}),存在改善空间")
        elif operating_margin < 0.12:
            score += 1
            details.append(f"运营利润率适中({operating_margin:.1%}),有改善潜力")
    
    # 2. 资产效率分析
    asset_turnover = accessor.safe_get(line_items, 'asset_turnover')
    if asset_turnover and asset_turnover < 0.8:
        score += 2
        details.append(f"资产周转率较低({asset_turnover:.2f}),可能需要资产优化")
    elif asset_turnover and asset_turnover < 1.2:
        score += 1
        details.append(f"资产周转率适中({asset_turnover:.2f})")
    
    # 3. 成本结构分析
    gross_margin = accessor.safe_get(line_items, 'gross_margin')
    if gross_margin and operating_margin:
        overhead_ratio = gross_margin - operating_margin
        if overhead_ratio > 0.20:
            score += 2
            details.append(f"高管理费用比率({overhead_ratio:.1%}),可能存在成本削减机会")
        elif overhead_ratio > 0.15:
            score += 1
            details.append(f"管理费用比率适中({overhead_ratio:.1%})")
    
    # 4. 资本配置效率
    roic = accessor.safe_get(line_items, 'return_on_invested_capital')
    if roic and roic < 0.08:
        score += 2
        details.append(f"ROIC较低({roic:.1%}),资本配置需要改善")
    elif roic and roic < 0.12:
        score += 1
        details.append(f"ROIC适中({roic:.1%})")
    
    # 5. 现金转换机会
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    net_income = accessor.safe_get(line_items, 'net_income')
    
    if fcf and net_income and net_income > 0:
        fcf_conversion = fcf / net_income
        if fcf_conversion < 0.7:
            score += 1
            details.append(f"现金转换率较低({fcf_conversion:.2f}),营运资本管理可改善")
    
    return {"score": score, "max_score": 10, "details": "; ".join(details)}


def analyze_valuation_unified(line_items: dict, market_cap: float, accessor) -> dict:
    """
    使用统一数据访问器进行Ackman风格的价值评估
    寻找以合理价格交易的高质量企业,重视安全边际
    """
    score = 0
    details = []
    
    if market_cap is None or market_cap <= 0:
        return {"score": 0, "max_score": 10, "details": "基于现有数据评估", "intrinsic_value": None}
    
    # 1. 自由现金流估值
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    
    if not fcf or fcf <= 0:
        return {"score": 0, "max_score": 10, "details": "基于可用现金流指标评估", "intrinsic_value": None}
    
    # 计算FCF收益率
    fcf_yield = fcf / market_cap
    
    if fcf_yield > 0.08:
        score += 4
        details.append(f"优秀FCF收益率: {fcf_yield:.1%}")
    elif fcf_yield > 0.05:
        score += 3
        details.append(f"良好FCF收益率: {fcf_yield:.1%}")
    elif fcf_yield > 0.03:
        score += 1
        details.append(f"公允FCF收益率: {fcf_yield:.1%}")
    else:
        details.append(f"FCF收益率较低: {fcf_yield:.1%}")
    
    # 2. P/E估值
    pe_ratio = accessor.safe_get(line_items, 'price_to_earnings')
    if pe_ratio and pe_ratio <= 100:  # 过滤异常PE值
        if pe_ratio < 15:
            score += 2
            details.append(f"有吸引力的P/E: {pe_ratio:.1f}")
        elif pe_ratio < 25:
            score += 1
            details.append(f"合理的P/E: {pe_ratio:.1f}")
        else:
            details.append(f"P/E较高: {pe_ratio:.1f}")
    elif pe_ratio and pe_ratio > 100:
        details.append("P/E比率异常高")
    else:
        details.append("P/E数据不可用")
    
    # 3. EV/EBITDA估值
    ev_ebitda = None  # 字段不支持,已移除
    if ev_ebitda:
        if ev_ebitda < 12:
            score += 2
            details.append(f"有吸引力的EV/EBITDA: {ev_ebitda:.1f}")
        elif ev_ebitda < 20:
            score += 1
            details.append(f"合理的EV/EBITDA: {ev_ebitda:.1f}")
        else:
            details.append(f"EV/EBITDA较高: {ev_ebitda:.1f}")
    
    # 4. 价值vs质量分析
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe and pe_ratio:
        peg_like_ratio = pe_ratio / (roe * 100)  # PE相对于ROE
        if peg_like_ratio < 1.5:
            score += 2
            details.append(f"质量调整后估值有吸引力: PE/ROE={peg_like_ratio:.2f}")
        elif peg_like_ratio < 2.5:
            score += 1
            details.append(f"质量调整后估值合理: PE/ROE={peg_like_ratio:.2f}")
    
    # 简单内在价值估算(保守DCF)
    conservative_value = fcf * 12  # 12倍FCF
    reasonable_value = fcf * 18   # 18倍FCF
    optimistic_value = fcf * 25   # 25倍FCF
    
    # 安全边际分析
    upside_to_reasonable = (reasonable_value - market_cap) / market_cap
    
    if upside_to_reasonable > 0.3:
        score += 1
        details.append(f"显著安全边际: 相对合理价值有{upside_to_reasonable:.1%}上涨空间")
    elif upside_to_reasonable > 0.1:
        details.append(f"适度安全边际: 相对合理价值有{upside_to_reasonable:.1%}上涨空间")
    else:
        details.append(f"安全边际有限: 相对合理价值{upside_to_reasonable:.1%}")
    
    return {
        "score": score,
        "max_score": 10,
        "details": "; ".join(details),
        "intrinsic_value_range": {
            "conservative": conservative_value,
            "reasonable": reasonable_value,
            "optimistic": optimistic_value
        },
        "fcf_yield": fcf_yield,
        "fcf": fcf
    }


def generate_ackman_output(
    ticker: str,
    analysis_data: dict[str, any],
    state: AgentState,
    agent_id: str,
) -> BillAckmanSignal:
    """
    生成Ackman风格的投资决策
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是Bill Ackman AI投资分析师,使用他的投资原则进行决策:

            1. 寻找具有持久竞争优势(护城河)的高质量企业,通常是知名消费或服务品牌
            2. 优先考虑持续的自由现金流和长期增长潜力
            3. 倡导强有力的财务纪律(合理杠杆.高效资本配置)
            4. 重视估值:寻求具有安全边际的内在价值
            5. 考虑通过activism改善管理或运营以释放重大上涨空间的机会
            6. 专注于少数几个高确定性投资

            在你的推理中:
            - 强调品牌实力.护城河或独特市场定位
            - 审查自由现金流生成和利润率趋势作为关键信号
            - 分析杠杆.股份回购和分红作为资本纪律指标
            - 提供有数字支撑的估值评估(DCF.倍数等)
            - 识别activism或价值创造的催化剂(如成本削减.更好的资本配置)
            - 在讨论弱点或机会时使用自信.分析性.有时对抗性的语调

            返回你的最终建议(signal: bullish, neutral, 或 bearish),置信度0-100,以及详尽的推理部分.
            """
        ),
        (
            "human",
            """基于以下分析,创建Ackman风格的投资信号.

            {ticker}的分析数据:
            {analysis_data}

            以严格有效的JSON格式返回:
            {{
              "signal": "bullish" | "bearish" | "neutral",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            """
        )
    ])

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    def create_default_bill_ackman_signal():
        return BillAckmanSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错,默认为中性"
        )

    return call_llm(
        prompt=prompt, 
        pydantic_model=BillAckmanSignal, 
        agent_name=agent_id, 
        state=state,
        default_factory=create_default_bill_ackman_signal,
    )
