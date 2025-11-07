import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.llm import call_llm
from src.utils.price_fixer import price_fixer


class PortfolioDecision(BaseModel):
    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(description="要交易的股票数量")
    confidence: float = Field(description="决策的置信度,介于0.0和100.0之间")
    reasoning: str = Field(description="决策的推理")


class PortfolioManagerOutput(BaseModel):
    decisions: dict[str, PortfolioDecision] = Field(description="股票代码到交易决策的字典")


##### 投资组合管理代理 #####
def portfolio_management_agent(state: AgentState, agent_id: str = "portfolio_manager"):
    """为多个股票代码做出最终交易决策并生成订单"""

    # 获取投资组合和分析师信号
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]
    
    # 获取预取的数据用于价格信息
    prefetched_data = state["data"].get("prefetched_data", {})

    # 为每个股票代码获取持仓限制.当前价格和信号
    position_limits = {}
    current_prices = {}
    max_shares = {}
    signals_by_ticker = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "处理分析师信号")

        # 尝试从多个来源获取当前价格
        current_price = 0
        
        # 方法1: 从预取数据中获取价格
        if ticker in prefetched_data:
            ticker_data = prefetched_data[ticker]
            current_price = price_fixer.fix_price_data(ticker_data, ticker)
        
        # 方法2: 从状态数据中获取已有的价格信息
        if not current_price and "current_prices" in state["data"]:
            existing_price = state["data"]["current_prices"].get(ticker, 0)
            if existing_price and existing_price > 0:
                current_price = existing_price
        
        # 最终确保有效价格
        if not current_price or current_price <= 0:
            current_price = price_fixer._get_fallback_price(ticker)
            print(f"[Portfolio Manager] 使用后备价格: {ticker} = {current_price:.2f}")

        current_prices[ticker] = current_price

        # 设置默认的持仓限制(基于可用现金的合理比例)
        available_cash = portfolio.get('cash', 0)  # 获取当前现金，无现金时为0
        max_position_value = available_cash * 0.2  # 单只股票最多占20%
        position_limits[ticker] = max_position_value

        # 根据持仓限制和价格计算允许的最大股数
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0

        # 获取该股票代码的信号
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            # 跳过所有风险管理代理(它们有不同的信号结构)
            if not agent.startswith("risk_management_agent") and ticker in signals:
                ticker_signals[agent] = {"signal": signals[ticker]["signal"], "confidence": signals[ticker]["confidence"]}
        signals_by_ticker[ticker] = ticker_signals

    # 将current_prices添加到状态数据中,以便在整个工作流程中可用
    state["data"]["current_prices"] = current_prices

    progress.update_status(agent_id, None, "生成交易决策")

    # 生成交易决策
    result = generate_trading_decision(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        agent_id=agent_id,
        state=state,
    )

    # 创建投资组合管理消息
    message = HumanMessage(
        content=json.dumps({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}),
        name=agent_id,
    )

    # 如果设置了标志,打印决策
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}, "Portfolio Manager")

    progress.update_status(agent_id, None, "完成")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def generate_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
    agent_id: str,
    state: AgentState,
) -> PortfolioManagerOutput:
    """尝试通过重试逻辑从LLM获取决策"""
    # 创建提示模板
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是一个投资组合管理器,基于多个股票代码做出最终交易决策.

              重要:你正在管理一个现有投资组合,其中包含当前持仓.portfolio_positions显示:
              - "long": 当前持有的多头股数
              - "short": 当前持有的空头股数
              - "long_cost_basis": 多头股票的平均买入价
              - "short_cost_basis": 空头股票的平均卖出价
              
              交易规则:
              - 对于多头持仓:
                * 只有在有可用现金时才能买入
                * 只有在当前持有该股票代码的多头股票时才能卖出
                * 卖出数量必须 ≤ 当前多头持仓股数
                * 买入数量应当合理控制
              
              - 对于持仓管理:
                * 基于分析师综合评估进行投资决策
                * 重点关注基本面分析和估值水平
                * 采用谨慎的风险管理策略
                * 避免过度集中投资单一标的
              
              - 基于分析师综合评估进行投资决策
              - 采用稳健的风险管理策略

              可用操作:
              - "buy": 买入或增加持仓
              - "sell": 卖出或减少持仓(仅当你当前持有该股票时)
              - "hold": 维持当前持仓不做任何更改(对于hold,数量应为0)

              输入:
              - signals_by_ticker: 股票代码 → 信号的字典
              - portfolio_cash: 投资组合中的当前现金
              - portfolio_positions: 当前持仓情况
              - current_prices: 每个股票代码的当前价格
              """,
            ),
            (
                "human",
                """基于团队的分析,为每个股票代码做出你的交易决策.

              以下是按股票代码分组的信号:
              {signals_by_ticker}

              当前价格:
              {current_prices}

              投资组合现金: {portfolio_cash}
              当前持仓: {portfolio_positions}

              重要决策规则:
              - 如果你当前持有该股票,你可以:
                * HOLD: 保持你的当前持仓(数量 = 0)
                * SELL: 减少/卖出你的持仓(数量 = 要卖出的股数)
                * BUY: 增加你的持仓(数量 = 要买入的额外股数)
                
              - 如果你当前不持有该股票,你可以:
                * HOLD: 保持不参与该持仓(数量 = 0)
                * BUY: 开立新的持仓(数量 = 要买入的股数)

              严格以JSON格式输出,结构如下:
              {{
                "decisions": {{
                  "TICKER1": {{
                    "action": "buy/sell/hold",
                    "quantity": integer,
                    "confidence": float between 0 and 100,
                    "reasoning": "解释你的决策的字符串,考虑当前持仓"
                  }},
                  "TICKER2": {{
                    ...
                  }},
                  ...
                }}
              }}
              """,
            ),
        ]
    )

    # 生成提示
    prompt_data = {
        "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
        "current_prices": json.dumps(current_prices, indent=2),
        "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
        "portfolio_positions": json.dumps(portfolio.get("positions", {}), indent=2),
    }
    
    prompt = template.invoke(prompt_data)

    # 为PortfolioManagerOutput创建默认工厂
    def create_default_portfolio_output():
        # 计算分析师平均置信度
        average_confidence = 50.0  # 默认值
        if signals_by_ticker:
            all_confidences = []
            for ticker_signals in signals_by_ticker.values():
                for signal_data in ticker_signals.values():
                    if isinstance(signal_data, dict) and 'confidence' in signal_data:
                        conf = signal_data['confidence']
                        if isinstance(conf, (int, float)) and 0 <= conf <= 100:
                            all_confidences.append(conf)
            
            if all_confidences:
                average_confidence = sum(all_confidences) / len(all_confidences)
        
        # 创建决策字典
        decisions = {}
        for ticker in tickers:
            # 分析该股票的信号趋势
            ticker_signals = signals_by_ticker.get(ticker, {})
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            confidences = []
            analyst_names = []
            
            for agent_name, signal_data in ticker_signals.items():
                if isinstance(signal_data, dict):
                    signal = signal_data.get('signal', 'neutral')
                    confidence = signal_data.get('confidence', 50)
                    
                    # 只考虑信心度大于等于60%的分析师意见
                    if confidence >= 60:
                        confidences.append(confidence)
                        analyst_names.append(agent_name.replace('_agent', ''))
                        
                        if signal in ['bullish', 'buy']:
                            bullish_count += 1
                        elif signal in ['bearish', 'sell']:
                            bearish_count += 1
                        else:
                            neutral_count += 1
            
            # 计算该股票的平均置信度
            avg_confidence = sum(confidences) / len(confidences) if confidences else 50
            total_analysts = len(analyst_names)
            
            # 根据分析师信号确定行动和推理
            if bullish_count > bearish_count:
                action = "buy"
                action_confidence = min(avg_confidence + 10, 95)
                reasoning = f"经过{total_analysts}位分析师综合评估,{bullish_count}位看多.{bearish_count}位看空.{neutral_count}位中性.多数分析师认为当前价格{current_prices.get(ticker, 0):.2f}具有投资价值,建议适量建仓.平均置信度{avg_confidence:.1f}%."
            elif bearish_count > bullish_count:
                action = "sell" if portfolio.get("positions", {}).get(ticker, {}).get("long", 0) > 0 else "hold"
                action_confidence = avg_confidence
                reasoning = f"经过{total_analysts}位分析师综合评估,{bearish_count}位看空.{bullish_count}位看多.{neutral_count}位中性.多数分析师对当前价格{current_prices.get(ticker, 0):.2f}持谨慎态度,"
                if action == "sell":
                    reasoning += f"建议减持现有持仓.平均置信度{avg_confidence:.1f}%."
                else:
                    reasoning += f"建议暂时观望.平均置信度{avg_confidence:.1f}%."
            else:
                action = "hold"
                action_confidence = avg_confidence
                reasoning = f"经过{total_analysts}位分析师综合评估,{bullish_count}位看多.{bearish_count}位看空.{neutral_count}位中性.分析师意见相对分化,当前价格{current_prices.get(ticker, 0):.2f},建议维持现状待观察.平均置信度{avg_confidence:.1f}%."
            
            decisions[ticker] = PortfolioDecision(
                action=action,
                quantity=0,  # 数量由LLM在实际运行时确定
                confidence=action_confidence,
                reasoning=reasoning
            )
        
        return PortfolioManagerOutput(decisions=decisions)

    # 添加详细的调试日志
    print(f"[Portfolio Manager] 生成投资决策:")
    print(f"  - 股票数量: {len(tickers)}")
    print(f"  - 分析师信号: {len(signals_by_ticker)} 个股票")
    print(f"  - 当前价格: {len(current_prices)} 个股票")
    print(f"  - 最大股数: {max_shares}")
    print(f"  - 投资组合现金: {portfolio.get('cash', 0)}")
    
    # 验证数据质量
    data_quality_issues = []
    for ticker in tickers:
        if ticker not in signals_by_ticker:
            data_quality_issues.append(f"{ticker}: 缺少分析师信号")
        elif not signals_by_ticker[ticker]:
            data_quality_issues.append(f"{ticker}: 分析师信号为空")
        
        if ticker not in current_prices or current_prices[ticker] <= 0:
            data_quality_issues.append(f"{ticker}: 缺少有效价格数据")
    
    if data_quality_issues:
        print(f"[Portfolio Manager] 数据质量问题:")
        for issue in data_quality_issues:
            print(f"  - {issue}")

    return call_llm(
        prompt=prompt,
        pydantic_model=PortfolioManagerOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_portfolio_output,
    )
