#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析模块 - 基于AKShare数据的详细分析报告
不依赖LLM，纯数据驱动的分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.tools.api import (
    get_prices, get_financial_metrics, get_market_cap,
    _detect_market, _convert_cn_symbol
)
from src.utils.progress import progress


def generate_smart_analysis_report(tickers: List[str], start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
    """
    生成基于AKShare数据的智能分析报告
    
    Args:
        tickers: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        data_cache: 数据缓存字典
        prefetched_data: 预取数据字典
    
    Returns:
        包含详细分析结果的字典
    """
    progress.update_status("智能分析", "", "开始智能分析...", "正在分析股票数据")
    
    analysis_results = {}
    
    for i, ticker in enumerate(tickers):
        try:
            progress.update_status("智能分析", ticker, f"分析进度 {i+1}/{len(tickers)}", f"正在分析 {ticker}")
            
            # 获取基础数据
            stock_analysis = analyze_single_stock(ticker, start_date, end_date, data_cache, prefetched_data)
            analysis_results[ticker] = stock_analysis
            
        except Exception as e:
            print(f"分析股票 {ticker} 时出错: {e}")
            analysis_results[ticker] = {
                "error": str(e),
                "analysis_summary": "数据获取失败，无法进行分析"
            }
    
    # 生成整体市场分析
    market_analysis = generate_market_overview(analysis_results)
    
    progress.update_status("智能分析", "", "智能分析完成", "分析报告已生成")
    
    return {
        "individual_analysis": analysis_results,
        "market_overview": market_analysis,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def analyze_single_stock(ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
    """
    分析单只股票的详细数据
    """
    analysis = {
        "ticker": ticker,
        "market": _detect_market(ticker),
        "analysis_date": end_date
    }
    
    try:
        # 1. 价格分析
        price_analysis = analyze_price_trends(ticker, start_date, end_date, data_cache, prefetched_data)
        analysis["price_analysis"] = price_analysis
        
        # 2. 财务指标分析
        financial_analysis = analyze_financial_metrics(ticker, end_date)
        analysis["financial_analysis"] = financial_analysis
        
        # 3. 估值分析
        valuation_analysis = analyze_valuation(ticker, end_date)
        analysis["valuation_analysis"] = valuation_analysis
        
        # 4. 风险分析
        risk_analysis = analyze_risk_metrics(ticker, start_date, end_date, data_cache, prefetched_data)
        analysis["risk_analysis"] = risk_analysis
        
        # 5. 综合评分
        overall_score = calculate_overall_score(price_analysis, financial_analysis, valuation_analysis, risk_analysis)
        analysis["overall_score"] = overall_score
        
        # 6. 生成分析摘要
        analysis["analysis_summary"] = generate_analysis_summary(ticker, analysis)
        
    except Exception as e:
        analysis["error"] = str(e)
        analysis["analysis_summary"] = f"分析 {ticker} 时出现错误: {str(e)}"
    
    return analysis


def analyze_price_trends(ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
    """
    分析价格趋势
    """
    try:
        # 优先从预取数据获取
        prices = None
        if prefetched_data:
            prices = prefetched_data.get('prices', {}).get(ticker)
        
        # 其次从缓存获取数据
        if not prices and data_cache:
            cache_key = f"{ticker}_{start_date}_{end_date}"
            prices = data_cache.get(cache_key)
        
        # 最后直接获取新数据
        if not prices:
            prices = get_prices(ticker, start_date, end_date)
            
        if not prices:
            return {"error": "无法获取价格数据"}
        
        # 转换为DataFrame便于分析
        df = pd.DataFrame([{
            "date": p.time,
            "close": p.close,
            "volume": p.volume,
            "high": p.high,
            "low": p.low
        } for p in prices])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 计算技术指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # 计算收益率
        df['daily_return'] = df['close'].pct_change()
        
        current_price = df['close'].iloc[-1]
        start_price = df['close'].iloc[0]
        
        # 价格变化分析
        price_change = (current_price - start_price) / start_price * 100
        
        # 波动率分析
        volatility = df['daily_return'].std() * np.sqrt(252) * 100  # 年化波动率
        
        # 趋势分析
        trend_analysis = analyze_trend(df)
        
        # 支撑阻力位分析
        support_resistance = analyze_support_resistance(df)
        
        return {
            "current_price": round(current_price, 2),
            "price_change_percent": round(price_change, 2),
            "volatility_annual": round(volatility, 2),
            "trend_analysis": trend_analysis,
            "support_resistance": support_resistance,
            "moving_averages": {
                "ma5": round(df['ma5'].iloc[-1], 2) if not pd.isna(df['ma5'].iloc[-1]) else None,
                "ma20": round(df['ma20'].iloc[-1], 2) if not pd.isna(df['ma20'].iloc[-1]) else None,
                "ma60": round(df['ma60'].iloc[-1], 2) if not pd.isna(df['ma60'].iloc[-1]) else None
            },
            "volume_analysis": analyze_volume_trends(df)
        }
        
    except Exception as e:
        return {"error": f"价格分析失败: {str(e)}"}


def analyze_financial_metrics(ticker: str, end_date: str) -> Dict[str, Any]:
    """
    分析财务指标
    """
    try:
        metrics = get_financial_metrics(ticker, end_date)
        if not metrics:
            return {"error": "无法获取财务数据"}
        
        metric = metrics[0]  # 取最新的财务数据
        
        # 盈利能力分析
        profitability = {
            "gross_margin": metric.gross_margin,
            "operating_margin": metric.operating_margin,
            "net_margin": metric.net_margin,
            "roe": metric.return_on_equity,
            "roa": metric.return_on_assets
        }
        
        # 财务健康度分析
        financial_health = {
            "current_ratio": metric.current_ratio,
            "debt_to_equity": metric.debt_to_equity,
            "interest_coverage": metric.interest_coverage
        }
        
        # 成长性分析
        growth = {
            "revenue_growth": metric.revenue_growth,
            "earnings_growth": metric.earnings_growth,
            "book_value_growth": metric.book_value_growth
        }
        
        # 财务指标评分
        financial_score = calculate_financial_score(profitability, financial_health, growth)
        
        return {
            "profitability": profitability,
            "financial_health": financial_health,
            "growth": growth,
            "financial_score": financial_score,
            "financial_summary": generate_financial_summary(profitability, financial_health, growth)
        }
        
    except Exception as e:
        return {"error": f"财务分析失败: {str(e)}"}


def analyze_valuation(ticker: str, end_date: str) -> Dict[str, Any]:
    """
    分析估值指标
    """
    try:
        metrics = get_financial_metrics(ticker, end_date)
        if not metrics:
            return {"error": "无法获取估值数据"}
        
        metric = metrics[0]
        
        valuation_metrics = {
            "pe_ratio": metric.price_to_earnings_ratio,
            "pb_ratio": metric.price_to_book_ratio,
            "ps_ratio": metric.price_to_sales_ratio,
            "peg_ratio": metric.peg_ratio,
            "ev_ebitda": metric.enterprise_value_to_ebitda_ratio
        }
        
        # 估值评级
        valuation_rating = rate_valuation(valuation_metrics)
        
        return {
            "valuation_metrics": valuation_metrics,
            "valuation_rating": valuation_rating,
            "valuation_summary": generate_valuation_summary(valuation_metrics, valuation_rating)
        }
        
    except Exception as e:
        return {"error": f"估值分析失败: {str(e)}"}


def analyze_risk_metrics(ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
    """
    分析风险指标
    """
    try:
        # 优先从预取数据获取
        prices = None
        if prefetched_data:
            prices = prefetched_data.get('prices', {}).get(ticker)
        
        # 其次从缓存获取数据
        if not prices and data_cache:
            cache_key = f"{ticker}_{start_date}_{end_date}"
            prices = data_cache.get(cache_key)
        
        # 最后直接获取新数据
        if not prices:
            prices = get_prices(ticker, start_date, end_date)
            
        if not prices:
            return {"error": "无法获取价格数据进行风险分析"}
        
        # 计算收益率
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i].close - prices[i-1].close) / prices[i-1].close
            returns.append(daily_return)
        
        if not returns:
            return {"error": "数据不足，无法计算风险指标"}
        
        returns = np.array(returns)
        
        # 风险指标计算
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        max_drawdown = calculate_max_drawdown([p.close for p in prices])
        var_95 = np.percentile(returns, 5)  # 95% VaR
        
        # 风险评级
        risk_level = assess_risk_level(volatility, max_drawdown)
        
        return {
            "volatility": round(volatility * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "var_95": round(var_95 * 100, 2),
            "risk_level": risk_level,
            "risk_summary": generate_risk_summary(volatility, max_drawdown, risk_level)
        }
        
    except Exception as e:
        return {"error": f"风险分析失败: {str(e)}"}


def calculate_overall_score(price_analysis: Dict, financial_analysis: Dict, 
                          valuation_analysis: Dict, risk_analysis: Dict) -> Dict[str, Any]:
    """
    计算综合评分
    """
    scores = {
        "price_score": 0,
        "financial_score": 0,
        "valuation_score": 0,
        "risk_score": 0
    }
    
    # 价格趋势评分 (0-25分)
    if "trend_analysis" in price_analysis and "trend_strength" in price_analysis["trend_analysis"]:
        trend_strength = price_analysis["trend_analysis"]["trend_strength"]
        if trend_strength == "强势上涨":
            scores["price_score"] = 25
        elif trend_strength == "温和上涨":
            scores["price_score"] = 20
        elif trend_strength == "横盘整理":
            scores["price_score"] = 15
        elif trend_strength == "温和下跌":
            scores["price_score"] = 10
        else:
            scores["price_score"] = 5
    
    # 财务评分 (0-25分)
    if "financial_score" in financial_analysis:
        scores["financial_score"] = min(25, financial_analysis["financial_score"])
    
    # 估值评分 (0-25分)
    if "valuation_rating" in valuation_analysis:
        rating = valuation_analysis["valuation_rating"]
        if rating == "严重低估":
            scores["valuation_score"] = 25
        elif rating == "低估":
            scores["valuation_score"] = 20
        elif rating == "合理":
            scores["valuation_score"] = 15
        elif rating == "高估":
            scores["valuation_score"] = 10
        else:
            scores["valuation_score"] = 5
    
    # 风险评分 (0-25分，风险越低分数越高)
    if "risk_level" in risk_analysis:
        risk_level = risk_analysis["risk_level"]
        if risk_level == "低风险":
            scores["risk_score"] = 25
        elif risk_level == "中等风险":
            scores["risk_score"] = 15
        else:
            scores["risk_score"] = 5
    
    total_score = sum(scores.values())
    
    # 评级
    if total_score >= 80:
        rating = "强烈推荐"
    elif total_score >= 65:
        rating = "推荐"
    elif total_score >= 50:
        rating = "中性"
    elif total_score >= 35:
        rating = "谨慎"
    else:
        rating = "不推荐"
    
    return {
        "scores": scores,
        "total_score": total_score,
        "rating": rating,
        "max_score": 100
    }


def generate_analysis_summary(ticker: str, analysis: Dict) -> str:
    """
    生成分析摘要
    """
    summary_parts = []
    
    # 基本信息
    market = analysis.get("market", "未知")
    summary_parts.append(f"股票代码: {ticker} ({market}市场)")
    
    # 价格分析摘要
    if "price_analysis" in analysis and "error" not in analysis["price_analysis"]:
        price_data = analysis["price_analysis"]
        current_price = price_data.get("current_price", "N/A")
        price_change = price_data.get("price_change_percent", 0)
        summary_parts.append(f"当前价格: {current_price}元，期间涨跌: {price_change:+.2f}%")
    
    # 财务分析摘要
    if "financial_analysis" in analysis and "financial_summary" in analysis["financial_analysis"]:
        summary_parts.append(analysis["financial_analysis"]["financial_summary"])
    
    # 估值分析摘要
    if "valuation_analysis" in analysis and "valuation_summary" in analysis["valuation_analysis"]:
        summary_parts.append(analysis["valuation_analysis"]["valuation_summary"])
    
    # 风险分析摘要
    if "risk_analysis" in analysis and "risk_summary" in analysis["risk_analysis"]:
        summary_parts.append(analysis["risk_analysis"]["risk_summary"])
    
    # 综合评分
    if "overall_score" in analysis:
        score_data = analysis["overall_score"]
        total_score = score_data.get("total_score", 0)
        rating = score_data.get("rating", "未评级")
        summary_parts.append(f"综合评分: {total_score}/100 ({rating})")
    
    return "\n".join(summary_parts)


def generate_market_overview(analysis_results: Dict) -> Dict[str, Any]:
    """
    生成市场整体分析
    """
    total_stocks = len(analysis_results)
    successful_analysis = sum(1 for result in analysis_results.values() if "error" not in result)
    
    # 统计评级分布
    rating_distribution = {}
    score_distribution = []
    
    for result in analysis_results.values():
        if "overall_score" in result:
            rating = result["overall_score"].get("rating", "未评级")
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
            score_distribution.append(result["overall_score"].get("total_score", 0))
    
    avg_score = np.mean(score_distribution) if score_distribution else 0
    
    return {
        "total_stocks_analyzed": total_stocks,
        "successful_analysis": successful_analysis,
        "rating_distribution": rating_distribution,
        "average_score": round(avg_score, 1),
        "market_sentiment": determine_market_sentiment(rating_distribution, avg_score)
    }


# 辅助函数
def analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """分析价格趋势"""
    if len(df) < 20:
        return {"trend_direction": "数据不足", "trend_strength": "无法判断"}
    
    current_price = df['close'].iloc[-1]
    ma20 = df['ma20'].iloc[-1]
    ma60 = df['ma60'].iloc[-1]
    
    # 趋势方向判断
    if current_price > ma20 > ma60:
        trend_direction = "上涨"
        if (current_price - ma20) / ma20 > 0.05:
            trend_strength = "强势上涨"
        else:
            trend_strength = "温和上涨"
    elif current_price < ma20 < ma60:
        trend_direction = "下跌"
        if (ma20 - current_price) / ma20 > 0.05:
            trend_strength = "强势下跌"
        else:
            trend_strength = "温和下跌"
    else:
        trend_direction = "横盘"
        trend_strength = "横盘整理"
    
    return {
        "trend_direction": trend_direction,
        "trend_strength": trend_strength
    }


def analyze_support_resistance(df: pd.DataFrame) -> Dict[str, Any]:
    """分析支撑阻力位"""
    if len(df) < 20:
        return {"support": None, "resistance": None}
    
    recent_data = df.tail(20)
    support = recent_data['low'].min()
    resistance = recent_data['high'].max()
    
    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2)
    }


def analyze_volume_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """分析成交量趋势"""
    if len(df) < 10:
        return {"volume_trend": "数据不足"}
    
    recent_volume = df['volume'].tail(5).mean()
    historical_volume = df['volume'].head(-5).mean()
    
    if recent_volume > historical_volume * 1.2:
        volume_trend = "放量"
    elif recent_volume < historical_volume * 0.8:
        volume_trend = "缩量"
    else:
        volume_trend = "正常"
    
    return {"volume_trend": volume_trend}


def calculate_financial_score(profitability: Dict, financial_health: Dict, growth: Dict) -> int:
    """计算财务评分"""
    score = 0
    
    # 盈利能力评分 (0-10分)
    if profitability.get("roe") and profitability["roe"] > 0.15:
        score += 3
    elif profitability.get("roe") and profitability["roe"] > 0.10:
        score += 2
    elif profitability.get("roe") and profitability["roe"] > 0.05:
        score += 1
    
    if profitability.get("net_margin") and profitability["net_margin"] > 0.10:
        score += 3
    elif profitability.get("net_margin") and profitability["net_margin"] > 0.05:
        score += 2
    elif profitability.get("net_margin") and profitability["net_margin"] > 0:
        score += 1
    
    # 财务健康度评分 (0-8分)
    if financial_health.get("current_ratio") and financial_health["current_ratio"] > 2:
        score += 2
    elif financial_health.get("current_ratio") and financial_health["current_ratio"] > 1.5:
        score += 1
    
    if financial_health.get("debt_to_equity") and financial_health["debt_to_equity"] < 0.3:
        score += 3
    elif financial_health.get("debt_to_equity") and financial_health["debt_to_equity"] < 0.6:
        score += 2
    elif financial_health.get("debt_to_equity") and financial_health["debt_to_equity"] < 1:
        score += 1
    
    # 成长性评分 (0-7分)
    if growth.get("revenue_growth") and growth["revenue_growth"] > 0.20:
        score += 3
    elif growth.get("revenue_growth") and growth["revenue_growth"] > 0.10:
        score += 2
    elif growth.get("revenue_growth") and growth["revenue_growth"] > 0:
        score += 1
    
    if growth.get("earnings_growth") and growth["earnings_growth"] > 0.20:
        score += 2
    elif growth.get("earnings_growth") and growth["earnings_growth"] > 0.10:
        score += 1
    
    return min(25, score)  # 最高25分


def rate_valuation(valuation_metrics: Dict) -> str:
    """评估估值水平"""
    pe = valuation_metrics.get("pe_ratio")
    pb = valuation_metrics.get("pb_ratio")
    
    if not pe or not pb:
        return "数据不足"
    
    # 简化的估值评级逻辑
    if pe < 10 and pb < 1:
        return "严重低估"
    elif pe < 15 and pb < 1.5:
        return "低估"
    elif pe < 25 and pb < 3:
        return "合理"
    elif pe < 40 and pb < 5:
        return "高估"
    else:
        return "严重高估"


def calculate_max_drawdown(prices: List[float]) -> float:
    """计算最大回撤"""
    if len(prices) < 2:
        return 0
    
    peak = prices[0]
    max_drawdown = 0
    
    for price in prices[1:]:
        if price > peak:
            peak = price
        else:
            drawdown = (peak - price) / peak
            max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown


def assess_risk_level(volatility: float, max_drawdown: float) -> str:
    """评估风险水平"""
    if volatility < 0.2 and max_drawdown < 0.1:
        return "低风险"
    elif volatility < 0.4 and max_drawdown < 0.2:
        return "中等风险"
    else:
        return "高风险"


def generate_financial_summary(profitability: Dict, financial_health: Dict, growth: Dict) -> str:
    """生成财务摘要"""
    summary_parts = []
    
    # 盈利能力
    roe = profitability.get("roe")
    if roe:
        if roe > 0.15:
            summary_parts.append("盈利能力优秀")
        elif roe > 0.10:
            summary_parts.append("盈利能力良好")
        else:
            summary_parts.append("盈利能力一般")
    
    # 财务健康度
    debt_ratio = financial_health.get("debt_to_equity")
    if debt_ratio:
        if debt_ratio < 0.3:
            summary_parts.append("财务结构稳健")
        elif debt_ratio < 0.6:
            summary_parts.append("财务结构合理")
        else:
            summary_parts.append("负债水平较高")
    
    # 成长性
    revenue_growth = growth.get("revenue_growth")
    if revenue_growth:
        if revenue_growth > 0.20:
            summary_parts.append("高速成长")
        elif revenue_growth > 0.10:
            summary_parts.append("稳定成长")
        elif revenue_growth > 0:
            summary_parts.append("温和成长")
        else:
            summary_parts.append("收入下滑")
    
    return "，".join(summary_parts) if summary_parts else "财务数据不足"


def generate_valuation_summary(valuation_metrics: Dict, rating: str) -> str:
    """生成估值摘要"""
    pe = valuation_metrics.get("pe_ratio")
    pb = valuation_metrics.get("pb_ratio")
    
    if pe and pb:
        return f"估值水平: {rating} (PE: {pe:.1f}, PB: {pb:.1f})"
    else:
        return f"估值水平: {rating}"


def generate_risk_summary(volatility: float, max_drawdown: float, risk_level: str) -> str:
    """生成风险摘要"""
    return f"风险水平: {risk_level} (波动率: {volatility*100:.1f}%, 最大回撤: {max_drawdown*100:.1f}%)"


def determine_market_sentiment(rating_distribution: Dict, avg_score: float) -> str:
    """判断市场情绪"""
    if avg_score >= 70:
        return "乐观"
    elif avg_score >= 50:
        return "中性"
    else:
        return "谨慎"