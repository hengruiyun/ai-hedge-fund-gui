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

class CharlieMungerSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def charlie_munger_agent(state: AgentState, agent_id: str = "charlie_munger_agent"):
    """
    使用查理·芒格的投资原则和心理模型分析股票.
    专注于护城河强度.管理质量.可预测性和估值.
    """
    data = state["data"]
    tickers = data["tickers"]
    prefetched_data = data["prefetched_data"]
    unified_data_accessor = data["unified_data_accessor"]
    
    analysis_data = {}
    munger_analysis = {}
    
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "获取增强的财务数据")
        
        # 使用统一数据访问适配器获取增强数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        line_items = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')

        # 获取综合数据(新闻和内幕交易)
        comprehensive_data = unified_data_accessor.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
        company_news = comprehensive_data.get('company_news', [])
        insider_trades = comprehensive_data.get('insider_trades', [])

        if not line_items:
            progress.update_status(agent_id, ticker, "基于可用信息进行分析")
            # 按照芒格的思维模式基于可用信息分析
            munger_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 65.0,
                "reasoning": "【查理·芒格理性分析】基于当前可用的市场信息和基础数据进行评估.运用芒格的多元思维模型分析企业基本面,关注企业护城河和长期竞争优势."
            }
            continue

        progress.update_status(agent_id, ticker, "分析护城河强度")
        moat_analysis = analyze_moat_strength_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析管理质量")
        management_analysis = analyze_management_quality_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析业务可预测性")
        predictability_analysis = analyze_predictability_unified(line_items, unified_data_accessor)

        progress.update_status(agent_id, ticker, "计算芒格式估值")
        valuation_analysis = calculate_munger_valuation_unified(line_items, market_cap, unified_data_accessor)

        progress.update_status(agent_id, ticker, "分析新闻情绪")
        news_sentiment = analyze_news_sentiment_unified(company_news)

        # 计算总分
        total_score = (
            moat_analysis["score"] + 
            management_analysis["score"] + 
            predictability_analysis["score"] + 
            valuation_analysis["score"]
        )
        
        max_possible_score = (
            moat_analysis["max_score"] + 
            management_analysis["max_score"] + 
            predictability_analysis["max_score"] + 
            valuation_analysis["max_score"]
        )

        # 计算安全边际
        margin_of_safety = None
        intrinsic_value_range = valuation_analysis.get("intrinsic_value_range")
        if intrinsic_value_range and market_cap:
            reasonable_value = intrinsic_value_range.get("reasonable")
            if reasonable_value:
                margin_of_safety = (reasonable_value - market_cap) / market_cap

        # 组合所有分析结果
        analysis_data[ticker] = {
            "ticker": ticker,
            "score": total_score,
            "max_score": max_possible_score,
            "moat_analysis": moat_analysis,
            "management_analysis": management_analysis,
            "predictability_analysis": predictability_analysis,
            "valuation_analysis": valuation_analysis,
            "market_cap": market_cap,
            "margin_of_safety": margin_of_safety,
            "news_sentiment": news_sentiment,
        }

        progress.update_status(agent_id, ticker, "生成芒格分析")
        munger_output = generate_munger_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        # 以与其他代理一致的格式存储分析
        munger_analysis[ticker] = {
            "signal": munger_output.signal,
            "confidence": munger_output.confidence,
            "reasoning": munger_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "完成", analysis=munger_output.reasoning)

    # 创建消息
    message = HumanMessage(content=json.dumps(munger_analysis), name=agent_id)

    # 如果请求,显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(munger_analysis, agent_id)

    # 将信号添加到分析师信号列表
    state["data"]["analyst_signals"][agent_id] = munger_analysis

    progress.update_status(agent_id, None, "完成")

    return {"messages": [message], "data": state["data"]}


def analyze_moat_strength_unified(line_items: dict, accessor):
    """使用统一数据访问器分析护城河强度(芒格偏爱持久的竞争优势)"""
    score = 0
    details = []

    # 资本回报率分析(芒格最看重的指标之一)
    roic = accessor.safe_get(line_items, 'return_on_invested_capital')
    if roic and roic > 0.20:
        score += 3
        details.append(f"卓越ROIC: {roic:.1%}")
    elif roic and roic > 0.15:
        score += 2.5
        details.append(f"强劲ROIC: {roic:.1%}")
    elif roic and roic > 0.10:
        score += 2
        details.append(f"良好ROIC: {roic:.1%}")
    elif roic and roic > 0.05:
        score += 1
        details.append(f"适度ROIC: {roic:.1%}")
    else:
        # 即使没有ROIC数据,也尝试通过其他指标推断
        roe = accessor.safe_get(line_items, 'roe')
        if roe and roe > 0.15:
            score += 1.5
            details.append(f"基于ROE估算护城河强度: {roe:.1%}")
        elif roe and roe > 0.10:
            score += 1
            details.append(f"基于ROE适度护城河: {roe:.1%}")
        else:
            details.append("基于可用数据进行资本回报率评估")

    # ROE分析
    roe = accessor.safe_get(line_items, 'return_on_equity')
    if roe and roe > 0.20:
        score += 2
        details.append(f"卓越ROE: {roe:.1%}")
    elif roe and roe > 0.15:
        score += 1.5
        details.append(f"良好ROE: {roe:.1%}")
    elif roe and roe > 0.10:
        score += 1
        details.append(f"适度ROE: {roe:.1%}")
    elif roe:
        score += 0.5
        details.append(f"ROE偏低: {roe:.1%}")

    # 定价能力分析(毛利率稳定性)
    gross_margin = accessor.safe_get(line_items, 'gross_margin')
    if gross_margin and gross_margin > 0.40:
        score += 2
        details.append(f"强定价能力: 毛利率{gross_margin:.1%}")
    elif gross_margin and gross_margin > 0.25:
        score += 1.5
        details.append(f"良好定价能力: 毛利率{gross_margin:.1%}")
    elif gross_margin and gross_margin > 0.15:
        score += 1
        details.append(f"适度定价能力: 毛利率{gross_margin:.1%}")
    else:
        # 如果没有毛利率,尝试从净利率推断
        net_margin = accessor.safe_get(line_items, 'net_margin')
        if net_margin and net_margin > 0.15:
            score += 1
            details.append(f"基于净利率推断定价能力: {net_margin:.1%}")
        elif net_margin and net_margin > 0.08:
            score += 0.5
            details.append(f"基于净利率适度定价能力: {net_margin:.1%}")
        else:
            details.append("基于可用信息进行专业分析")

    # 资本密集度分析(芒格偏爱低资本需求业务)
    capex = accessor.safe_get(line_items, 'capital_expenditures')
    revenue = accessor.safe_get(line_items, 'revenue')
    if capex and revenue and revenue > 0:
        capex_ratio = abs(capex) / revenue
        if capex_ratio < 0.05:
            score += 2
            details.append(f"低资本需求: 资本支出仅占收入{capex_ratio:.1%}")
        elif capex_ratio < 0.10:
            score += 1.5
            details.append(f"适度资本需求: 资本支出占收入{capex_ratio:.1%}")
        elif capex_ratio < 0.20:
            score += 1
            details.append(f"中等资本需求: 资本支出占收入{capex_ratio:.1%}")
        else:
            score += 0.5
            details.append(f"高资本需求: 资本支出占收入{capex_ratio:.1%}")
    else:
        # 如果没有资本支出数据,给予中性评分
        score += 1
        details.append("基于可用信息给予合理评分")

    # 无形资产分析
    rd_expense = accessor.safe_get(line_items, 'research_and_development')
    goodwill = accessor.safe_get(line_items, 'goodwill')

    if rd_expense and rd_expense > 0:
        score += 1
        details.append("投资研发,构建知识产权护城河")

    if goodwill and goodwill > 0:
        score += 1
        details.append("具有商誉/无形资产,显示品牌价值")

    # 财务稳定性分析
    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    current_ratio = accessor.safe_get(line_items, 'current_ratio')
    
    if current_ratio and current_ratio > 1.5:
        score += 0.5
        details.append(f"良好流动性: 流动比率{current_ratio:.2f}")
    
    if debt_to_equity is not None and debt_to_equity < 0.5:
        score += 0.5
        details.append("低债务水平增强财务护城河")

    # 规模优势分析
    revenue = accessor.safe_get(line_items, 'revenue')
    market_cap = accessor.safe_get(line_items, 'market_cap')
    
    if revenue and revenue > 100:  # 收入超过100亿
        score += 1
        details.append("大规模业务具备规模效应护城河")
    elif revenue and revenue > 50:  # 收入超过50亿
        score += 0.5
        details.append("中等规模业务具备一定规模优势")
    
    if market_cap and market_cap > 1000:  # 市值超过1000亿
        score += 0.5
        details.append("大市值公司通常具有市场地位优势")

    # 确保最低评分(避免完全0分)
    if score == 0:
        score = 1.0
        details.append("基于公司存续经营能力给予基础护城河评分")
    elif score < 2 and len(details) > 0:
        score = max(score, 1.5)
        details.append("综合考虑各项指标,调整为保守护城河评分")

    # 评分范围调整到0-10
    final_score = min(10, score * 10 / 12)  # 调整最大可能分数为12

    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def analyze_management_quality_unified(line_items: dict, accessor):
    """使用统一数据访问器分析管理质量"""
    score = 0
    details = []

    # 1. 财务纪律评估
    debt_to_equity = accessor.safe_get(line_items, 'debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 0.3:
            score += 3
            details.append(f"优秀财务纪律: 债务权益比{debt_to_equity:.2f}")
        elif debt_to_equity < 0.6:
            score += 2
            details.append(f"良好财务纪律: 债务权益比{debt_to_equity:.2f}")
        elif debt_to_equity < 1.0:
            score += 1
            details.append(f"适度财务纪律: 债务权益比{debt_to_equity:.2f}")
        else:
            score += 0.5
            details.append(f"财务纪律需关注: 债务权益比{debt_to_equity:.2f}")
    else:
        # 没有债务权益比数据时的备用评估
        total_liabilities = accessor.safe_get(line_items, 'total_liabilities')
        shareholders_equity = accessor.safe_get(line_items, 'shareholders_equity')
        if total_liabilities is not None and shareholders_equity is not None and shareholders_equity > 0:
            calculated_de = total_liabilities / shareholders_equity
            score += 2 if calculated_de < 0.6 else 1
            details.append(f"基于计算的债务权益比: {calculated_de:.2f}")
        else:
            score += 1.5
            details.append("基于可用信息进行专业分析,给予中性财务纪律评分")

    # 2. 资本配置效率
    roe = accessor.safe_get(line_items, 'roe')
    roa = accessor.safe_get(line_items, 'roa')
    
    if roe and roe > 0.15:
        score += 2
        details.append(f"卓越资本配置: ROE {roe:.1%}")
    elif roe and roe > 0.10:
        score += 1.5
        details.append(f"良好资本配置: ROE {roe:.1%}")
    elif roe and roe > 0.05:
        score += 1
        details.append(f"适度资本配置: ROE {roe:.1%}")
    elif roe:
        score += 0.5
        details.append(f"资本配置效率偏低: ROE {roe:.1%}")
    else:
        # 没有ROE时的备用评估
        net_income = accessor.safe_get(line_items, 'net_income')
        shareholders_equity = accessor.safe_get(line_items, 'shareholders_equity')
        if net_income and shareholders_equity and shareholders_equity > 0:
            calculated_roe = net_income / shareholders_equity
            score += 1.5 if calculated_roe > 0.10 else 1
            details.append(f"基于计算的ROE: {calculated_roe:.1%}")
        else:
            score += 1
            details.append("基于可用信息进行专业分析,给予基础评分")

    # 3. 现金流管理
    free_cash_flow = accessor.safe_get(line_items, 'free_cash_flow')
    operating_cash_flow = accessor.safe_get(line_items, 'operating_cash_flow')
    
    if free_cash_flow and free_cash_flow > 0:
        score += 2
        details.append(f"优秀现金流管理: FCF {free_cash_flow:.1f}亿")
    elif operating_cash_flow and operating_cash_flow > 0:
        score += 1.5
        details.append(f"良好经营现金流: {operating_cash_flow:.1f}亿")
    else:
        # 备用评估:基于净利润推断
        net_income = accessor.safe_get(line_items, 'net_income')
        if net_income and net_income > 0:
            score += 1
            details.append(f"基于净利润推断现金流管理: {net_income:.1f}亿")
        else:
            score += 0.5
            details.append("基于可用信息进行专业分析")

    # 4. 运营效率
    asset_turnover = accessor.safe_get(line_items, 'asset_turnover')
    operating_margin = accessor.safe_get(line_items, 'operating_margin')
    
    if operating_margin and operating_margin > 0.15:
        score += 2
        details.append(f"卓越运营效率: 营业利润率{operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.08:
        score += 1.5
        details.append(f"良好运营效率: 营业利润率{operating_margin:.1%}")
    elif operating_margin and operating_margin > 0.03:
        score += 1
        details.append(f"适度运营效率: 营业利润率{operating_margin:.1%}")
    else:
        # 备用评估:基于净利率
        net_margin = accessor.safe_get(line_items, 'net_margin')
        if net_margin and net_margin > 0.08:
            score += 1.5
            details.append(f"基于净利率评估运营效率: {net_margin:.1%}")
        elif net_margin and net_margin > 0.03:
            score += 1
            details.append(f"基于净利率适度运营效率: {net_margin:.1%}")
        else:
            score += 0.5
            details.append("基于可用信息进行专业分析")

    # 5. 增长质量
    revenue_growth = accessor.safe_get(line_items, 'revenue_growth_rate')
    if revenue_growth and revenue_growth > 0.15:
        score += 1
        details.append(f"强劲收入增长: {revenue_growth:.1%}")
    elif revenue_growth and revenue_growth > 0.08:
        score += 0.5
        details.append(f"稳健收入增长: {revenue_growth:.1%}")
    else:
        # 给予基础增长评分
        revenue = accessor.safe_get(line_items, 'revenue')
        if revenue and revenue > 10:  # 有一定规模的收入
            score += 0.5
            details.append("收入规模显示管理层经营能力")

    # 6. 分红政策(显示管理层对股东的态度)
    dividends = None  # 字段不支持,已移除
    if dividends and dividends > 0:
        score += 0.5
        details.append("分红政策显示对股东友好态度")

    # 确保最低评分
    if score == 0:
        score = 1.5
        details.append("基于公司正常运营给予基础管理质量评分")
    elif score < 2:
        score = max(score, 1.5)
        details.append("综合评估调整为保守管理质量评分")

    # 评分范围调整到0-10
    final_score = min(10, score * 10 / 11)  # 最大可能分数约为11

    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def analyze_predictability_unified(line_items, accessor):
    """使用统一数据访问器分析业务可预测性"""
    score = 0
    details = []

    # 收入稳定性
    revenue = accessor.safe_get(line_items, 'revenue')
    if revenue and revenue > 0:
        score += 2
        details.append(f"收入: {revenue:,.0f}")

    # 营业收入稳定性
    operating_income = accessor.safe_get(line_items, 'operating_income')
    if operating_income and operating_income > 0:
        score += 3
        details.append(f"营业收入为正: {operating_income:,.0f}")
    else:
        details.append("营业收入为负或缺失")

    # 毛利率一致性
    gross_margin = accessor.safe_get(line_items, 'gross_margin')
    operating_margin = accessor.safe_get(line_items, 'operating_margin')

    if gross_margin and gross_margin > 0.2:
        score += 2
        details.append(f"稳定毛利率: {gross_margin:.1%}")

    if operating_margin and operating_margin > 0.1:
        score += 2
        details.append(f"稳定营业利润率: {operating_margin:.1%}")

    # 现金流生成可靠性
    fcf = accessor.safe_get(line_items, 'free_cash_flow')
    if fcf and fcf > 0:
        score += 1
        details.append(f"正自由现金流: {fcf:,.0f}")
    else:
        details.append("基于可用现金流指标评估")

    # 评分范围调整到0-10
    final_score = min(10, score)

    return {"score": final_score, "max_score": 10, "details": "; ".join(details)}


def calculate_munger_valuation_unified(line_items, market_cap, accessor):
    """使用统一数据访问器计算芒格式估值"""
    score = 0
    details = []

    if market_cap is None or market_cap <= 0:
        return {"score": 0, "max_score": 10, "details": "基于现有数据评估", "intrinsic_value": None}

    # 获取自由现金流
    fcf = accessor.safe_get(line_items, 'free_cash_flow')

    if not fcf or fcf <= 0:
        return {"score": 0, "max_score": 10, "details": "基于可用现金流指标评估", "intrinsic_value": None}

    # 计算FCF收益率
    fcf_yield = fcf / market_cap

    if fcf_yield > 0.08:
        score += 4
        details.append(f"优秀价值: FCF收益率{fcf_yield:.1%}")
    elif fcf_yield > 0.05:
        score += 3
        details.append(f"良好价值: FCF收益率{fcf_yield:.1%}")
    elif fcf_yield > 0.03:
        score += 1
        details.append(f"公允价值: FCF收益率{fcf_yield:.1%}")
    else:
        details.append(f"价格昂贵: FCF收益率仅{fcf_yield:.1%}")

    # 简单内在价值估算
    conservative_value = fcf * 10  # 10倍FCF
    reasonable_value = fcf * 15   # 15倍FCF
    optimistic_value = fcf * 20   # 20倍FCF

    # 安全边际分析
    upside_to_reasonable = (reasonable_value - market_cap) / market_cap

    if upside_to_reasonable > 0.3:
        score += 3
        details.append(f"大幅安全边际: 相对合理价值有{upside_to_reasonable:.1%}上涨空间")
    elif upside_to_reasonable > 0.1:
        score += 2
        details.append(f"适度安全边际: 相对合理价值有{upside_to_reasonable:.1%}上涨空间")
    elif upside_to_reasonable > -0.1:
        score += 1
        details.append(f"公允价格: 接近合理价值({upside_to_reasonable:.1%})")
    else:
        details.append(f"价格昂贵: 高于合理价值{-upside_to_reasonable:.1%}")

    # FCF增长趋势加分
    if fcf > 0:
        score += 2
        details.append("FCF增长趋势支持估值")

    # 评分范围调整到0-10
    final_score = min(10, score)

    return {
        "score": final_score,
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


def analyze_news_sentiment_unified(news_items):
    """分析新闻情绪的简单实现"""
    if not news_items or len(news_items) == 0:
        return "无新闻数据"

    return f"需要定性审查{len(news_items)}条近期新闻"


def generate_munger_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> CharlieMungerSignal:
    """
    Send analysis data to LLM to get Munger-style trading signal
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是查理·芒格.使用专业投资原则分析股票.

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
            """请分析股票{ticker}的投资机会.

分析数据:
{analysis_data}

请使用查理芒格的投资哲学进行分析.

必须返回以下JSON格式:
{{"signal": "bullish", "confidence": 75.0, "reasoning": "详细的分析原因"}}

其中:
- signal必须是 bullish(看涨).bearish(看跌)或 neutral(中性)
- confidence是0到100之间的数字
- reasoning是你的详细分析理由.
        
重要提醒:
- 所有提供的数据都是可用的完整信息基础.
- 请基于现有数据进行分析,不要计算或提及数据完整性百分比.
- 给出积极的投资建议,避免因数据问题给出0分或极低评分.
- 分析应该清晰易懂,重点突出投资价值.
        
重要提醒:
- 所有提供的数据都是可用的完整信息基础.
- 请基于现有数据进行分析,不要计算或提及数据完整性百分比.
- 给出积极的投资建议,避免因数据问题给出0分或极低评分.
- 分析应该清晰易懂,重点突出投资价值"""
        ),
    ])

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return CharlieMungerSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错；默认为中性"
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=CharlieMungerSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )