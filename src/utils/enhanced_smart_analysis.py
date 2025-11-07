#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能分析模块 - 基于AKShare数据的深度分析报告
包含量价分析、趋势预测、买卖建议等功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.tools.api import (
    get_prices, get_financial_metrics, get_market_cap,
    get_volume_analysis_data, get_market_sentiment_data,
    get_technical_indicators_data, get_industry_analysis_data,
    _detect_market, _convert_cn_symbol
)
from src.utils.progress import progress
from .enhanced_report_generator import generate_enhanced_html_report
from .risk_assessment import assess_stock_risk


class EnhancedSmartAnalyzer:
    """
    增强智能分析器
    """
    
    def __init__(self):
        self.analysis_weights = {
            "technical": 0.3,
            "fundamental": 0.25,
            "volume": 0.2,
            "sentiment": 0.15,
            "industry": 0.1
        }
    
    def generate_enhanced_analysis_report(self, tickers: List[str], start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
        """
        生成增强版智能分析报告
        """
        progress.update_status("增强智能分析", "", "开始深度分析...", "正在进行多维度分析")
        
        analysis_results = {
            "individual_analysis": {},
            "market_overview": {},
            "analysis_summary": "",
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        for i, ticker in enumerate(tickers):
            try:
                progress.update_status("增强智能分析", ticker, f"分析进度 {i+1}/{len(tickers)}", f"正在深度分析 {ticker}")
                
                # 执行单股深度分析
                stock_analysis = self.analyze_single_stock_enhanced(ticker, start_date, end_date, data_cache, prefetched_data)
                analysis_results["individual_analysis"][ticker] = stock_analysis
                
            except Exception as e:
                print(f"分析股票 {ticker} 时出错: {e}")
                analysis_results["individual_analysis"][ticker] = {
                    "error": str(e),
                    "analysis_summary": "数据获取失败，无法进行分析"
                }
        
        # 生成市场概览
        analysis_results["market_overview"] = self.generate_market_overview_enhanced(analysis_results["individual_analysis"])
        
        # 生成总体分析摘要
        analysis_results["analysis_summary"] = self.generate_overall_summary(analysis_results)
        
        # 生成HTML报告
        html_report = generate_enhanced_html_report(analysis_results)
        
        return {
            'analysis_results': analysis_results,
            'html_report': html_report,
            'analysis_timestamp': analysis_results['analysis_timestamp']
        }
    
    def analyze_single_stock_enhanced(self, ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
        """
        单股增强分析
        """
        analysis = {
            "ticker": ticker,
            "market": _detect_market(ticker),
            "analysis_date": end_date,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        try:
            # 1. 基础价格分析
            price_analysis = self.analyze_price_trends_enhanced(ticker, start_date, end_date, data_cache, prefetched_data)
            analysis["price_analysis"] = price_analysis
            
            # 2. 量价关系分析
            volume_analysis = self.analyze_volume_price_relationship(ticker, start_date, end_date, data_cache, prefetched_data)
            analysis["volume_analysis"] = volume_analysis
            
            # 3. 技术指标分析
            technical_analysis = self.analyze_technical_indicators_enhanced(ticker, start_date, end_date)
            analysis["technical_analysis"] = technical_analysis
            
            # 4. 市场情绪分析
            sentiment_analysis = self.analyze_market_sentiment_enhanced(ticker)
            analysis["sentiment_analysis"] = sentiment_analysis
            
            # 5. 行业对比分析
            industry_analysis = self.analyze_industry_comparison(ticker)
            analysis["industry_analysis"] = industry_analysis
            
            # 6. 财务基本面分析
            fundamental_analysis = self.analyze_fundamentals_enhanced(ticker, end_date)
            analysis["fundamental_analysis"] = fundamental_analysis
            
            # 7. 趋势预测
            trend_prediction = self.predict_future_trends(ticker, start_date, end_date, data_cache, prefetched_data)
            analysis["trend_prediction"] = trend_prediction
            
            # 8. 买卖建议
            trading_signals = self.generate_trading_signals(analysis)
            analysis["trading_signals"] = trading_signals
            
            # 9. 风险评估
            risk_assessment = self.assess_comprehensive_risk(analysis)
            analysis["risk_assessment"] = risk_assessment
            
            # 10. 综合评分
            overall_score = self.calculate_comprehensive_score(analysis)
            analysis["overall_score"] = overall_score
            
            # 11. 生成分析摘要
            analysis["analysis_summary"] = self.generate_stock_analysis_summary(ticker, analysis)
            
        except Exception as e:
            analysis["error"] = str(e)
            analysis["analysis_summary"] = f"分析 {ticker} 时出现错误: {str(e)}"
        
        return analysis
    
    def analyze_price_trends_enhanced(self, ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
        """
        增强价格趋势分析
        """
        try:
            # 优先使用预获取的数据
            prices = None
            if prefetched_data:
                from src.utils.unified_data_accessor import unified_data_accessor
                prices = unified_data_accessor.get_prices(ticker, prefetched_data)
            elif data_cache:
                cache_key = f"{ticker}_{start_date}_{end_date}"
                prices = data_cache.get(cache_key)
            
            # 如果缓存中没有数据，则获取新数据
            if not prices:
                prices = get_prices(ticker, start_date, end_date)
                
            if not prices:
                return {"error": "无法获取价格数据"}
            
            # 转换为DataFrame
            df = pd.DataFrame([{
                'date': p.time,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            } for p in prices])
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 计算各种价格指标
            analysis = {
                "current_price": df['close'].iloc[-1] if not pd.isna(df['close'].iloc[-1]) else 0,
                "price_change_1d": (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100 if len(df) >= 2 and not pd.isna(df['close'].iloc[-1]) and not pd.isna(df['close'].iloc[-2]) and df['close'].iloc[-2] != 0 else 0,
                "price_change_5d": (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100 if len(df) >= 6 and not pd.isna(df['close'].iloc[-1]) and not pd.isna(df['close'].iloc[-6]) and df['close'].iloc[-6] != 0 else 0,
                "price_change_20d": (df['close'].iloc[-1] - df['close'].iloc[-21]) / df['close'].iloc[-21] * 100 if len(df) >= 21 and not pd.isna(df['close'].iloc[-1]) and not pd.isna(df['close'].iloc[-21]) and df['close'].iloc[-21] != 0 else 0,
                "volatility_20d": df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100 if len(df) >= 20 and not pd.isna(df['close'].pct_change().rolling(20).std().iloc[-1]) else 0,
                "max_drawdown": self.calculate_max_drawdown(df['close'].tolist()) or 0,
                "support_levels": self.identify_support_levels(df) or [],
                "resistance_levels": self.identify_resistance_levels(df) or [],
                "trend_strength": self.calculate_trend_strength(df) or 0,
                "momentum_score": self.calculate_momentum_score(df) or 0
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"价格趋势分析失败: {str(e)}"}
    
    def analyze_volume_price_relationship(self, ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
        """
        量价关系分析
        """
        try:
            # 获取成交量分析数据
            volume_data = get_volume_analysis_data(ticker, start_date, end_date)
            
            if "error" in volume_data:
                return volume_data
            
            # 获取价格数据进行量价关系分析
            prices = None
            if data_cache:
                cache_key = f"{ticker}_{start_date}_{end_date}"
                prices = data_cache.get(cache_key)
            
            if not prices:
                prices = get_prices(ticker, start_date, end_date)
            
            if not prices:
                return {"error": "无法获取价格数据进行量价分析"}
            
            # 分析量价关系
            analysis = {
                "volume_trend": self.analyze_volume_trend(volume_data),
                "price_volume_correlation": volume_data.get("price_volume_trend", 0),
                "volume_breakout_signals": self.detect_volume_breakouts(volume_data),
                "accumulation_distribution": self.calculate_accumulation_distribution(prices),
                "money_flow_index": self.calculate_money_flow_index(prices),
                "volume_weighted_average_price": self.calculate_vwap(prices),
                "volume_analysis_summary": self.generate_volume_analysis_summary(volume_data)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"量价关系分析失败: {str(e)}"}
    
    def analyze_technical_indicators_enhanced(self, ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        增强技术指标分析 - 投资大师级别分析
        优先使用投资大师分析算法，提供专业级别的技术分析
        """
        try:
            # 首先尝试使用投资大师分析模块
            try:
                from .investment_master_analysis import InvestmentMasterAnalysis
                master_analyzer = InvestmentMasterAnalysis()
                
                # 生成投资大师级分析报告
                master_report = master_analyzer.generate_master_analysis_report(ticker, start_date, end_date)
                
                if master_report['status'] == 'success':
                    # 转换为标准格式
                    analysis = {
                        "analysis_type": "investment_master",
                        "data_quality": {
                            "data_points": len(master_report.get('indicators', {})),
                            "date_range": master_report.get('data_period', '未知'),
                            "calculation_mode": "investment_master",
                            "reliability_score": 95
                        },
                        "master_indicators": {
                            **master_report.get('indicators', {}),
                            "investment_advice": master_report.get('investment_advice', {})
                        },
                        "trend_analysis": master_report.get('trend_analysis', {}),
                        "momentum_analysis": master_report.get('momentum_analysis', {}),
                        "investment_advice": master_report.get('investment_advice', {}),
                        "master_insights": master_report.get('investment_advice', {}).get('master_insights', []),
                        "technical_summary": master_report.get('summary', ''),
                        "analysis_methods": {
                            "description": "采用投资大师级别的技术分析方法",
                            "methods_used": [
                                "巴菲特趋势分析 - 长期价值投资视角的趋势判断",
                                "彼得林奇动量分析 - 成长股投资的动量评估",
                                "智能移动平均线系统 - 多时间周期趋势确认",
                                "高级RSI分析 - 超买超卖状态精确判断",
                                "价格行为分析 - 基于价格动作的市场心理分析",
                                "成交量确认分析 - 资金流向和市场参与度评估",
                                "支撑阻力位识别 - 关键价位和交易机会发现"
                            ],
                            "analysis_framework": [
                                "趋势识别: 采用大师级多层次趋势分析框架",
                                "动量评估: 结合价格和成交量的综合动量分析",
                                "风险评估: 基于波动率和技术形态的风险量化",
                                "信号生成: 多指标交叉验证的高可靠性信号",
                                "投资建议: 融合价值投资和技术分析的综合建议"
                            ]
                        },
                        "recommendation": {
                            "action": master_report.get('investment_advice', {}).get('recommendation', '观望'),
                            "confidence": master_report.get('investment_advice', {}).get('confidence', 50),
                            "risk_level": master_report.get('investment_advice', {}).get('risk_level', '中等'),
                            "reasoning": master_report.get('investment_advice', {}).get('reasoning', '')
                        }
                    }
                    return analysis
            except Exception as master_error:
                print(f"投资大师分析模块加载失败: {master_error}")
            
            # 如果投资大师分析失败，回退到原有逻辑
            indicators = get_technical_indicators_data(ticker, start_date, end_date)
            
            if "error" in indicators:
                # 提供详细的错误信息和建议
                error_analysis = {
                    "error": indicators["error"],
                    "error_type": "technical_data_unavailable",
                    "details": indicators.get("details", "技术指标数据获取失败"),
                    "suggestion": indicators.get("suggestion", "请检查股票代码和时间范围"),
                    "troubleshooting": indicators.get("troubleshooting", []),
                    "fallback_analysis": self._generate_fallback_technical_analysis(ticker, start_date, end_date),
                    "technical_methods_info": {
                        "description": "本系统使用多种专业技术分析方法",
                        "indicators_used": [
                            "移动平均线 (MA5, MA10, MA20, MA60) - 趋势分析",
                            "MACD (12,26,9) - 趋势动量分析",
                            "RSI (14) - 超买超卖分析",
                            "布林带 (20,2) - 价格通道分析",
                            "KDJ (9,3,3) - 随机指标分析",
                            "成交量指标 - 资金流向分析",
                            "波动率指标 - 风险评估"
                        ],
                        "analysis_framework": [
                            "趋势识别: 通过移动平均线系统判断主要趋势方向",
                            "动量分析: 使用MACD和RSI评估价格动量强度",
                            "支撑阻力: 通过布林带和历史价格确定关键价位",
                            "买卖信号: 综合多个指标生成交易信号",
                            "风险控制: 基于波动率和技术形态评估风险"
                        ]
                    }
                }
                return error_analysis
            
            # 验证指标数据完整性
            validation_result = self._validate_technical_indicators(indicators)
            if not validation_result["valid"]:
                return {
                    "error": "技术指标数据不完整",
                    "validation_issues": validation_result["issues"],
                    "partial_analysis": self._generate_partial_analysis(indicators)
                }
            
            # 分析技术指标信号
            analysis = {
                "data_quality": {
                    "data_points": indicators.get("data_points", 0),
                    "date_range": indicators.get("date_range", "未知"),
                    "calculation_mode": indicators.get("calculation_mode", "advanced"),
                    "reliability_score": self._calculate_data_reliability(indicators)
                },
                "moving_averages": self.analyze_moving_averages(indicators),
                "macd_analysis": self.analyze_macd_signals(indicators.get("macd", {})),
                "rsi_analysis": self.analyze_rsi_signals(indicators.get("rsi", 50)),
                "bollinger_analysis": self.analyze_bollinger_bands(indicators.get("bollinger_bands", {})),
                "kdj_analysis": self.analyze_kdj_signals(indicators.get("kdj", {})),
                "volume_analysis": self._analyze_volume_indicators(indicators),
                "volatility_analysis": self._analyze_volatility_indicators(indicators),
                "technical_score": self.calculate_technical_score(indicators),
                "signal_strength": self.calculate_signal_strength(indicators),
                "technical_summary": self.generate_technical_summary(indicators),
                "calculation_methods": indicators.get("calculation_methods", {}),
                "trading_signals": self._generate_comprehensive_trading_signals(indicators),
                "risk_assessment": self._assess_technical_risk(indicators)
            }
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"技术指标分析失败: {str(e)}",
                "error_type": "analysis_exception",
                "fallback_info": "系统将尝试使用基础分析方法",
                "basic_analysis": self._generate_basic_technical_analysis(ticker, start_date, end_date)
            }
    
    def _validate_technical_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证技术指标数据的完整性
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "completeness_score": 1.0
        }
        
        required_indicators = ["ma5", "ma20", "macd", "rsi"]
        optional_indicators = ["bollinger_bands", "kdj", "volume"]
        
        missing_required = []
        missing_optional = []
        
        # 检查必需指标
        for indicator in required_indicators:
            if indicator not in indicators or indicators[indicator] is None:
                missing_required.append(indicator)
                validation_result["issues"].append(f"缺少必需指标: {indicator}")
        
        # 检查可选指标
        for indicator in optional_indicators:
            if indicator not in indicators or indicators[indicator] is None:
                missing_optional.append(indicator)
        
        # 计算完整性得分
        total_indicators = len(required_indicators) + len(optional_indicators)
        missing_count = len(missing_required) + len(missing_optional)
        validation_result["completeness_score"] = max(0, (total_indicators - missing_count) / total_indicators)
        
        # 如果缺少必需指标，标记为无效
        if missing_required:
            validation_result["valid"] = False
            validation_result["issues"].append(f"缺少{len(missing_required)}个必需指标")
        
        # 如果完整性得分过低，也标记为无效
        if validation_result["completeness_score"] < 0.5:
            validation_result["valid"] = False
            validation_result["issues"].append("数据完整性不足50%")
        
        return validation_result
    
    def _generate_partial_analysis(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于部分可用数据生成分析
        """
        try:
            partial_analysis = {
                "status": "partial",
                "available_indicators": [],
                "analysis_summary": "",
                "limitations": []
            }
            
            # 检查可用指标
            if "ma5" in indicators and indicators["ma5"] is not None:
                partial_analysis["available_indicators"].append("短期移动平均线")
            
            if "ma20" in indicators and indicators["ma20"] is not None:
                partial_analysis["available_indicators"].append("长期移动平均线")
            
            if "rsi" in indicators and indicators["rsi"] is not None:
                partial_analysis["available_indicators"].append("相对强弱指数")
                rsi = indicators["rsi"]
                if rsi > 70:
                    partial_analysis["analysis_summary"] += "RSI显示超买状态。"
                elif rsi < 30:
                    partial_analysis["analysis_summary"] += "RSI显示超卖状态。"
                else:
                    partial_analysis["analysis_summary"] += "RSI处于正常范围。"
            
            if "macd" in indicators and indicators["macd"] is not None:
                partial_analysis["available_indicators"].append("MACD")
            
            # 添加限制说明
            if len(partial_analysis["available_indicators"]) < 4:
                partial_analysis["limitations"].append("技术指标数据不完整，分析结果可能不够准确")
            
            if not partial_analysis["analysis_summary"]:
                partial_analysis["analysis_summary"] = "基于有限的技术指标数据，无法提供详细分析。"
            
            return partial_analysis
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"部分分析生成失败: {str(e)}",
                "available_indicators": [],
                "analysis_summary": "无法生成部分分析"
            }
    
    def _generate_fallback_technical_analysis(self, ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        当主要技术指标获取失败时的备用分析方法
        直接获取价格数据并计算基础指标
        """
        try:
            from src.tools.api import get_prices
            from src.utils.technical_indicators import TechnicalIndicators
            
            # 尝试直接获取价格数据
            prices = get_prices(ticker, start_date, end_date)
            if not prices or len(prices) < 5:
                return {
                    "status": "failed",
                    "message": "无法获取足够的价格数据",
                    "suggestions": [
                        "检查股票代码是否正确",
                        "确认网络连接正常",
                        "验证AKShare数据源可用性"
                    ]
                }
            
            # 转换为DataFrame格式
            import pandas as pd
            df_data = []
            for price in prices:
                df_data.append({
                    'date': price.time,
                    'open': price.open,
                    'high': price.high,
                    'low': price.low,
                    'close': price.close,
                    'volume': price.volume
                })
            
            df = pd.DataFrame(df_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 计算基础技术指标
            tech_indicators = TechnicalIndicators.calculate_all_indicators(df)
            
            # 获取当前价格信息
            current_price = prices[-1].close
            prev_price = prices[-2].close if len(prices) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            # 计算简单移动平均线
            ma5 = df['close'].rolling(window=5).mean().iloc[-1] if len(df) >= 5 else None
            ma20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            
            # 计算波动率
            volatility = df['close'].pct_change().std() * 100 if len(df) > 1 else 0
            
            # 生成备用分析
            fallback_analysis = {
                "status": "fallback",
                "message": "使用备用方法生成的基础技术分析",
                "basic_indicators": {
                    "current_price": current_price,
                    "price_change": price_change,
                    "price_change_pct": price_change_pct,
                    "ma5": ma5,
                    "ma20": ma20,
                    "volatility": volatility,
                    "data_points": len(prices)
                },
                "analysis_summary": self._generate_basic_analysis_summary(current_price, ma5, ma20, price_change_pct, volatility),
                "data_acquisition_suggestions": [
                    "建议检查AKShare数据源连接",
                    "确认股票代码格式正确",
                    "验证网络连接稳定性",
                    "考虑使用其他数据源作为备用"
                ],
                "troubleshooting_steps": [
                    "1. 检查股票代码是否为有效的A股或港股代码",
                    "2. 确认日期范围设置合理（不超过当前日期）",
                    "3. 验证AKShare库是否正确安装和更新",
                    "4. 检查网络防火墙设置"
                ]
            }
            
            return fallback_analysis
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"备用技术分析生成失败: {str(e)}",
                "suggestions": [
                    "检查数据源连接",
                    "验证股票代码格式",
                    "确认系统依赖库完整"
                ]
            }
    
    def _generate_basic_analysis_summary(self, current_price: float, ma5: float, ma20: float, price_change_pct: float, volatility: float) -> str:
        """
        生成基础分析摘要
        """
        summary_parts = []
        
        # 价格变化分析
        if price_change_pct > 2:
            summary_parts.append("股价今日大幅上涨")
        elif price_change_pct > 0:
            summary_parts.append("股价今日小幅上涨")
        elif price_change_pct < -2:
            summary_parts.append("股价今日大幅下跌")
        elif price_change_pct < 0:
            summary_parts.append("股价今日小幅下跌")
        else:
            summary_parts.append("股价今日基本持平")
        
        # 移动平均线分析
        if ma5 and ma20:
            if current_price > ma5 > ma20:
                summary_parts.append("价格位于短期和长期均线之上，趋势向好")
            elif current_price < ma5 < ma20:
                summary_parts.append("价格位于短期和长期均线之下，趋势偏弱")
            elif ma5 > ma20:
                summary_parts.append("短期均线高于长期均线，短期趋势相对积极")
            else:
                summary_parts.append("短期均线低于长期均线，短期趋势相对消极")
        elif ma5:
            if current_price > ma5:
                summary_parts.append("价格高于短期均线")
            else:
                summary_parts.append("价格低于短期均线")
        
        # 波动率分析
        if volatility > 5:
            summary_parts.append("股价波动较大，风险较高")
        elif volatility > 2:
            summary_parts.append("股价波动适中")
        else:
            summary_parts.append("股价波动较小，相对稳定")
        
        return "。".join(summary_parts) + "。"
    
    def _generate_basic_technical_analysis(self, ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成基础技术分析作为备用方案
        """
        try:
            # 获取基础价格数据
            prices = get_prices(ticker, start_date, end_date)
            if not prices or len(prices) < 5:
                return {
                    "status": "error",
                    "message": "价格数据不足，无法进行基础技术分析",
                    "analysis": "数据不足"
                }
            
            # 计算基础指标
            current_price = prices[-1].get('close', 0)
            price_change = current_price - prices[-2].get('close', current_price) if len(prices) > 1 else 0
            price_change_pct = (price_change / prices[-2].get('close', current_price)) * 100 if len(prices) > 1 and prices[-2].get('close', 0) > 0 else 0
            
            # 计算简单移动平均线
            recent_prices = [p.get('close', 0) for p in prices[-5:]]
            ma5 = sum(recent_prices) / len(recent_prices) if recent_prices else current_price
            
            # 计算波动率
            price_changes = []
            for i in range(1, len(prices)):
                if prices[i-1].get('close', 0) > 0:
                    change = (prices[i].get('close', 0) - prices[i-1].get('close', 0)) / prices[i-1].get('close', 0)
                    price_changes.append(change)
            
            volatility = np.std(price_changes) * 100 if price_changes else 0
            
            # 生成基础分析
            trend = "上涨" if current_price > ma5 else "下跌"
            volatility_level = "高" if volatility > 3 else "中" if volatility > 1 else "低"
            
            analysis = f"基础技术分析：当前价格{current_price:.2f}，较前日{'上涨' if price_change > 0 else '下跌'}{abs(price_change_pct):.2f}%。"
            analysis += f"短期趋势{trend}，波动率{volatility_level}（{volatility:.2f}%）。"
            
            return {
                "status": "success",
                "current_price": current_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "ma5": ma5,
                "volatility": volatility,
                "trend": trend,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"基础技术分析失败: {str(e)}",
                "analysis": "无法生成基础分析"
            }
    
    def _generate_comprehensive_trading_signals(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成综合交易信号
        """
        try:
            signals = {
                "buy_signals": [],
                "sell_signals": [],
                "neutral_signals": [],
                "overall_signal": "中性",
                "signal_strength": 0.5
            }
            
            # 移动平均线信号
            if "ma5" in indicators and "ma20" in indicators:
                if indicators["ma5"] > indicators["ma20"]:
                    signals["buy_signals"].append("短期均线上穿长期均线")
                elif indicators["ma5"] < indicators["ma20"]:
                    signals["sell_signals"].append("短期均线下穿长期均线")
            
            # MACD信号
            macd_data = indicators.get("macd", {})
            if isinstance(macd_data, dict):
                if macd_data.get("signal") == "买入":
                    signals["buy_signals"].append("MACD金叉")
                elif macd_data.get("signal") == "卖出":
                    signals["sell_signals"].append("MACD死叉")
            
            # RSI信号
            rsi = indicators.get("rsi")
            if isinstance(rsi, (int, float)):
                if rsi < 30:
                    signals["buy_signals"].append("RSI超卖")
                elif rsi > 70:
                    signals["sell_signals"].append("RSI超买")
            
            # 布林带信号
            bollinger = indicators.get("bollinger_bands", {})
            if isinstance(bollinger, dict) and bollinger.get("signal"):
                if "突破上轨" in bollinger.get("signal", ""):
                    signals["sell_signals"].append("突破布林带上轨")
                elif "跌破下轨" in bollinger.get("signal", ""):
                    signals["buy_signals"].append("跌破布林带下轨")
            
            # 计算综合信号
            buy_count = len(signals["buy_signals"])
            sell_count = len(signals["sell_signals"])
            
            if buy_count > sell_count:
                signals["overall_signal"] = "买入"
                signals["signal_strength"] = min(0.8, 0.5 + (buy_count - sell_count) * 0.1)
            elif sell_count > buy_count:
                signals["overall_signal"] = "卖出"
                signals["signal_strength"] = max(0.2, 0.5 - (sell_count - buy_count) * 0.1)
            
            return signals
            
        except Exception as e:
            return {
                "error": f"交易信号生成失败: {str(e)}",
                "overall_signal": "中性",
                "signal_strength": 0.5
            }
    
    def _assess_technical_risk(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估技术风险
        """
        try:
            risk_assessment = {
                "risk_level": "中等",
                "risk_score": 0.5,
                "risk_factors": [],
                "risk_mitigation": []
            }
            
            # 波动率风险
            volatility = indicators.get("volatility", 0)
            if isinstance(volatility, (int, float)):
                if volatility > 5:
                    risk_assessment["risk_factors"].append("高波动率")
                    risk_assessment["risk_score"] += 0.2
                elif volatility < 1:
                    risk_assessment["risk_factors"].append("低流动性")
                    risk_assessment["risk_score"] += 0.1
            
            # RSI极值风险
            rsi = indicators.get("rsi")
            if isinstance(rsi, (int, float)):
                if rsi > 80 or rsi < 20:
                    risk_assessment["risk_factors"].append("RSI极值")
                    risk_assessment["risk_score"] += 0.15
            
            # 趋势一致性风险
            ma_analysis = indicators.get("moving_averages", {})
            if isinstance(ma_analysis, dict) and ma_analysis.get("trend_consistency") == "分歧":
                risk_assessment["risk_factors"].append("趋势分歧")
                risk_assessment["risk_score"] += 0.1
            
            # 确定风险等级
            if risk_assessment["risk_score"] > 0.7:
                risk_assessment["risk_level"] = "高"
                risk_assessment["risk_mitigation"].extend([
                    "建议降低仓位",
                    "设置严格止损",
                    "密切关注市场变化"
                ])
            elif risk_assessment["risk_score"] < 0.3:
                risk_assessment["risk_level"] = "低"
                risk_assessment["risk_mitigation"].append("可适当增加仓位")
            else:
                risk_assessment["risk_mitigation"].extend([
                    "保持正常仓位",
                    "设置合理止损"
                ])
            
            return risk_assessment
            
        except Exception as e:
            return {
                "error": f"风险评估失败: {str(e)}",
                "risk_level": "未知",
                "risk_score": 0.5
            }
    
    def analyze_market_sentiment_enhanced(self, ticker: str) -> Dict[str, Any]:
        """
        增强市场情绪分析
        """
        try:
            # 获取市场情绪数据
            sentiment_data = get_market_sentiment_data(ticker)
            
            if "error" in sentiment_data:
                return sentiment_data
            
            # 分析市场情绪
            analysis = {
                "money_flow_analysis": self.analyze_money_flow(sentiment_data.get("money_flow", {})),
                "institutional_activity": self.analyze_institutional_activity(sentiment_data),
                "market_attention": self.analyze_market_attention(sentiment_data),
                "sentiment_score": self.calculate_sentiment_score(sentiment_data),
                "sentiment_trend": self.determine_sentiment_trend(sentiment_data),
                "sentiment_summary": self.generate_sentiment_summary(sentiment_data)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"市场情绪分析失败: {str(e)}"}
    
    def predict_future_trends(self, ticker: str, start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
        """
        未来趋势预测
        """
        try:
            # 优先使用预获取的数据
            prices = None
            if prefetched_data:
                from src.utils.unified_data_accessor import unified_data_accessor
                prices = unified_data_accessor.get_prices(ticker, prefetched_data)
            elif data_cache:
                cache_key = f"{ticker}_{start_date}_{end_date}"
                prices = data_cache.get(cache_key)
            
            # 如果缓存中没有数据，则获取新数据
            if not prices:
                prices = get_prices(ticker, start_date, end_date)
            
            if not prices or len(prices) < 30:
                return {"error": "数据不足，无法进行趋势预测"}
            
            # 趋势预测分析
            prediction = {
                "short_term_trend": self.predict_short_term_trend(prices),
                "medium_term_trend": self.predict_medium_term_trend(prices),
                "long_term_trend": self.predict_long_term_trend(prices),
                "price_targets": self.calculate_price_targets(prices),
                "trend_reversal_signals": self.detect_trend_reversal_signals(prices),
                "confidence_level": self.calculate_prediction_confidence(prices),
                "prediction_summary": self.generate_prediction_summary(prices)
            }
            
            return prediction
            
        except Exception as e:
            return {"error": f"趋势预测失败: {str(e)}"}
    
    def generate_trading_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成买卖建议
        优先使用迷你投资大师的建议，如果没有则使用传统技术分析
        """
        try:
            signals = {
                "overall_signal": "持有",
                "signal_strength": 0,
                "entry_points": [],
                "exit_points": [],
                "stop_loss": None,
                "take_profit": None,
                "position_sizing": "中等",
                "time_horizon": "中期",
                "risk_level": "中等",
                "trading_strategy": "",
                "signal_details": {},
                "risk_reward_ratio": 0,
                "confidence_level": 0,
                "entry_strategy": "",
                "exit_strategy": "",
                "position_management": {}
            }
            
            # 获取基础数据
            current_price = analysis.get("price_analysis", {}).get("current_price", 0)
            technical_analysis = analysis.get("technical_analysis", {})
            sentiment_analysis = analysis.get("sentiment_analysis", {})
            trend_prediction = analysis.get("trend_prediction", {})
            volume_analysis = analysis.get("volume_analysis", {})
            
            # 检查是否有迷你投资大师分析结果
            master_indicators = technical_analysis.get("master_indicators", {})
            investment_advice = master_indicators.get("investment_advice", {})
            
            if investment_advice and investment_advice.get("recommendation"):
                # 优先使用迷你投资大师的建议
                master_recommendation = investment_advice.get("recommendation", "观望")
                master_confidence = investment_advice.get("confidence", 50)
                master_risk_level = investment_advice.get("risk_level", "中等")
                
                # 映射迷你投资大师建议到标准信号
                signal_mapping = {
                    "买入": "买入",
                    "强烈买入": "强烈买入", 
                    "谨慎买入": "买入",
                    "卖出": "卖出",
                    "强烈卖出": "强烈卖出",
                    "谨慎卖出": "卖出",
                    "观望": "持有",
                    "持有": "持有"
                }
                
                signals["overall_signal"] = signal_mapping.get(master_recommendation, "持有")
                signals["signal_strength"] = master_confidence
                signals["confidence_level"] = master_confidence
                signals["risk_level"] = master_risk_level
                
                # 根据迷你投资大师建议调整仓位
                if master_recommendation in ["买入", "强烈买入", "谨慎买入"]:
                    signals["position_sizing"] = "增仓" if master_confidence > 70 else "小幅增仓"
                elif master_recommendation in ["卖出", "强烈卖出", "谨慎卖出"]:
                    signals["position_sizing"] = "减仓" if master_confidence > 70 else "小幅减仓"
                else:
                    signals["position_sizing"] = "维持"
                
                # 使用迷你投资大师的综合评分作为信号强度
                total_score = master_confidence
                
            else:
                # 回退到传统技术分析
                technical_score = technical_analysis.get("technical_score", 50)
                sentiment_score = sentiment_analysis.get("sentiment_score", 50)
                trend_confidence = trend_prediction.get("confidence_level", 50)
                
                # 计算综合信号强度
                total_score = (
                    technical_score * self.analysis_weights["technical"] +
                    sentiment_score * self.analysis_weights["sentiment"] +
                    trend_confidence * 0.3
                )
                
                signals["signal_strength"] = total_score
                signals["confidence_level"] = trend_confidence
                
                # 确定交易信号和仓位大小
                signal_info = self.determine_trading_signal(total_score, technical_score, sentiment_score)
                signals.update(signal_info)
            
            # 计算入场和出场点位
            if current_price > 0:
                entry_exit_points = self.calculate_entry_exit_points(current_price, technical_analysis, trend_prediction)
                signals.update(entry_exit_points)
                
                # 计算动态止损止盈
                stop_take_levels = self.calculate_dynamic_stop_take_levels(
                    current_price, signals["overall_signal"], technical_analysis, volume_analysis
                )
                signals.update(stop_take_levels)
                
                # 计算风险收益比
                signals["risk_reward_ratio"] = self.calculate_risk_reward_ratio(
                    current_price, signals.get("stop_loss", 0), signals.get("take_profit", 0)
                )
            
            # 生成仓位管理策略
            signals["position_management"] = self.generate_position_management_strategy(
                signals["overall_signal"], signals["signal_strength"], signals["risk_level"]
            )
            
            # 生成入场和出场策略
            signals["entry_strategy"] = self.generate_entry_strategy(signals, technical_analysis)
            signals["exit_strategy"] = self.generate_exit_strategy(signals, technical_analysis)
            
            # 生成交易策略描述
            signals["trading_strategy"] = self.generate_enhanced_trading_strategy_description(signals, analysis)
            
            # 添加信号详情
            signals["signal_details"] = {
                "technical_contribution": technical_score * self.analysis_weights["technical"],
                "sentiment_contribution": sentiment_score * self.analysis_weights["sentiment"],
                "trend_contribution": trend_confidence * 0.3,
                "key_factors": self.identify_key_signal_factors(analysis)
            }
            
            return signals
            
        except Exception as e:
            return {"error": f"生成交易信号失败: {str(e)}"}
    
    # ==================== 交易信号辅助方法 ====================
    
    def determine_trading_signal(self, total_score: float, technical_score: float, sentiment_score: float) -> Dict[str, Any]:
        """确定交易信号和相关参数"""
        try:
            signal_info = {
                "overall_signal": "持有",
                "position_sizing": "中等",
                "risk_level": "中等",
                "time_horizon": "中期"
            }
            
            # 根据综合得分确定信号
            if total_score >= 75:
                signal_info["overall_signal"] = "强烈买入"
                signal_info["position_sizing"] = "较大"
                signal_info["risk_level"] = "较高"
                signal_info["time_horizon"] = "中长期"
            elif total_score >= 65:
                signal_info["overall_signal"] = "买入"
                signal_info["position_sizing"] = "中等"
                signal_info["risk_level"] = "中等"
                signal_info["time_horizon"] = "中期"
            elif total_score >= 55:
                signal_info["overall_signal"] = "谨慎买入"
                signal_info["position_sizing"] = "较小"
                signal_info["risk_level"] = "较低"
                signal_info["time_horizon"] = "短中期"
            elif total_score >= 45:
                signal_info["overall_signal"] = "持有"
                signal_info["position_sizing"] = "维持"
                signal_info["risk_level"] = "中等"
                signal_info["time_horizon"] = "中期"
            elif total_score >= 35:
                signal_info["overall_signal"] = "谨慎卖出"
                signal_info["position_sizing"] = "减仓"
                signal_info["risk_level"] = "较低"
                signal_info["time_horizon"] = "短期"
            elif total_score >= 25:
                signal_info["overall_signal"] = "卖出"
                signal_info["position_sizing"] = "大幅减仓"
                signal_info["risk_level"] = "中等"
                signal_info["time_horizon"] = "短期"
            else:
                signal_info["overall_signal"] = "强烈卖出"
                signal_info["position_sizing"] = "清仓"
                signal_info["risk_level"] = "高"
                signal_info["time_horizon"] = "立即"
            
            # 根据技术面和情绪面的一致性调整
            if abs(technical_score - sentiment_score) > 20:
                # 技术面和情绪面分歧较大，降低风险
                if signal_info["risk_level"] == "较高":
                    signal_info["risk_level"] = "中等"
                elif signal_info["risk_level"] == "中等":
                    signal_info["risk_level"] = "较低"
            
            return signal_info
        except Exception:
            return {"overall_signal": "持有", "position_sizing": "中等", "risk_level": "中等", "time_horizon": "中期"}
    
    def calculate_entry_exit_points(self, current_price: float, technical_analysis: Dict, trend_prediction: Dict) -> Dict[str, Any]:
        """计算入场和出场点位"""
        try:
            points = {
                "entry_points": [],
                "exit_points": []
            }
            
            # 获取技术指标
            ma_analysis = technical_analysis.get("moving_averages", {})
            bollinger = technical_analysis.get("bollinger_bands", {})
            price_targets = trend_prediction.get("price_targets", {})
            
            # 计算入场点位
            entry_points = []
            
            # 基于移动平均线的入场点
            ma5 = ma_analysis.get("ma5", current_price)
            ma10 = ma_analysis.get("ma10", current_price)
            ma20 = ma_analysis.get("ma20", current_price)
            
            if ma5 > 0 and ma10 > 0:
                # 回调到MA5附近买入
                entry_points.append({
                    "price": ma5 * 0.995,
                    "type": "MA5支撑",
                    "confidence": "中等"
                })
                
                # 回调到MA10附近买入
                entry_points.append({
                    "price": ma10 * 0.99,
                    "type": "MA10支撑",
                    "confidence": "较高"
                })
            
            # 基于布林带的入场点
            lower_band = bollinger.get("lower_band", 0)
            if lower_band > 0:
                entry_points.append({
                    "price": lower_band * 1.005,
                    "type": "布林下轨支撑",
                    "confidence": "高"
                })
            
            # 基于支撑位的入场点
            support = price_targets.get("support", 0)
            if support > 0:
                entry_points.append({
                    "price": support * 1.01,
                    "type": "关键支撑位",
                    "confidence": "高"
                })
            
            points["entry_points"] = sorted(entry_points, key=lambda x: x["price"], reverse=True)[:3]
            
            # 计算出场点位
            exit_points = []
            
            # 基于阻力位的出场点
            resistance = price_targets.get("resistance", 0)
            if resistance > 0:
                exit_points.append({
                    "price": resistance * 0.99,
                    "type": "阻力位",
                    "confidence": "高"
                })
            
            # 基于目标价的出场点
            target_price = price_targets.get("target_price", 0)
            if target_price > 0:
                exit_points.append({
                    "price": target_price * 0.95,
                    "type": "目标价位",
                    "confidence": "中等"
                })
            
            # 基于布林带上轨的出场点
            upper_band = bollinger.get("upper_band", 0)
            if upper_band > 0:
                exit_points.append({
                    "price": upper_band * 0.995,
                    "type": "布林上轨阻力",
                    "confidence": "中等"
                })
            
            points["exit_points"] = sorted(exit_points, key=lambda x: x["price"])[:3]
            
            return points
        except Exception:
            return {"entry_points": [], "exit_points": []}
    
    def calculate_dynamic_stop_take_levels(self, current_price: float, signal: str, technical_analysis: Dict, volume_analysis: Dict) -> Dict[str, float]:
        """计算动态止损止盈水平"""
        try:
            levels = {
                "stop_loss": 0,
                "take_profit": 0,
                "trailing_stop": 0
            }
            
            if current_price <= 0:
                return levels
            
            # 获取ATR（平均真实波幅）用于动态计算
            atr = technical_analysis.get("atr", current_price * 0.02)  # 默认2%
            volatility = volume_analysis.get("volatility", 0.02)  # 默认2%波动率
            
            # 根据信号类型调整止损止盈
            if signal in ["强烈买入", "买入", "谨慎买入"]:
                # 买入信号的止损止盈
                if signal == "强烈买入":
                    stop_loss_pct = max(0.05, volatility * 2.5)  # 最少5%止损
                    take_profit_pct = min(0.25, volatility * 6)   # 最多25%止盈
                elif signal == "买入":
                    stop_loss_pct = max(0.06, volatility * 3)
                    take_profit_pct = min(0.20, volatility * 5)
                else:  # 谨慎买入
                    stop_loss_pct = max(0.08, volatility * 4)
                    take_profit_pct = min(0.15, volatility * 4)
                
                levels["stop_loss"] = current_price * (1 - stop_loss_pct)
                levels["take_profit"] = current_price * (1 + take_profit_pct)
                levels["trailing_stop"] = current_price * (1 - stop_loss_pct * 0.7)
                
            elif signal in ["强烈卖出", "卖出", "谨慎卖出"]:
                # 卖出信号的止损止盈（做空逻辑）
                if signal == "强烈卖出":
                    stop_loss_pct = max(0.05, volatility * 2.5)
                    take_profit_pct = min(0.20, volatility * 5)
                elif signal == "卖出":
                    stop_loss_pct = max(0.06, volatility * 3)
                    take_profit_pct = min(0.15, volatility * 4)
                else:  # 谨慎卖出
                    stop_loss_pct = max(0.08, volatility * 4)
                    take_profit_pct = min(0.12, volatility * 3)
                
                levels["stop_loss"] = current_price * (1 + stop_loss_pct)
                levels["take_profit"] = current_price * (1 - take_profit_pct)
                levels["trailing_stop"] = current_price * (1 + stop_loss_pct * 0.7)
            
            else:
                # 持有信号的保护性止损
                levels["stop_loss"] = current_price * 0.90  # 10%保护性止损
                levels["take_profit"] = current_price * 1.10  # 10%获利了结
                levels["trailing_stop"] = current_price * 0.93  # 7%跟踪止损
            
            return levels
        except Exception:
            return {"stop_loss": 0, "take_profit": 0, "trailing_stop": 0}
    
    def calculate_risk_reward_ratio(self, current_price: float, stop_loss: float, take_profit: float) -> float:
        """计算风险收益比"""
        try:
            if current_price <= 0 or stop_loss <= 0 or take_profit <= 0:
                return 0.0
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            
            if risk > 0:
                return round(reward / risk, 2)
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def generate_position_management_strategy(self, signal: str, signal_strength: float, risk_level: str) -> Dict[str, Any]:
        """生成仓位管理策略"""
        try:
            strategy = {
                "initial_position": 0,
                "max_position": 0,
                "scaling_strategy": "",
                "risk_per_trade": 0,
                "portfolio_allocation": 0
            }
            
            # 根据信号强度确定初始仓位
            if signal in ["强烈买入", "强烈卖出"]:
                strategy["initial_position"] = 0.3  # 30%
                strategy["max_position"] = 0.6     # 最大60%
                strategy["risk_per_trade"] = 0.03  # 每笔交易风险3%
                strategy["portfolio_allocation"] = 0.15  # 组合配置15%
            elif signal in ["买入", "卖出"]:
                strategy["initial_position"] = 0.2  # 20%
                strategy["max_position"] = 0.4     # 最大40%
                strategy["risk_per_trade"] = 0.02  # 每笔交易风险2%
                strategy["portfolio_allocation"] = 0.10  # 组合配置10%
            elif signal in ["谨慎买入", "谨慎卖出"]:
                strategy["initial_position"] = 0.1  # 10%
                strategy["max_position"] = 0.2     # 最大20%
                strategy["risk_per_trade"] = 0.01  # 每笔交易风险1%
                strategy["portfolio_allocation"] = 0.05  # 组合配置5%
            else:  # 持有
                strategy["initial_position"] = 0.0
                strategy["max_position"] = 0.1
                strategy["risk_per_trade"] = 0.01
                strategy["portfolio_allocation"] = 0.03
            
            # 根据风险水平调整
            if risk_level == "高":
                strategy["initial_position"] *= 0.7
                strategy["max_position"] *= 0.7
                strategy["risk_per_trade"] *= 0.7
            elif risk_level == "较高":
                strategy["initial_position"] *= 0.85
                strategy["max_position"] *= 0.85
                strategy["risk_per_trade"] *= 0.85
            elif risk_level == "较低":
                strategy["initial_position"] *= 1.2
                strategy["max_position"] *= 1.2
                strategy["risk_per_trade"] *= 1.2
            
            # 确定加仓策略
            if signal_strength >= 70:
                strategy["scaling_strategy"] = "金字塔加仓：价格上涨时逐步加仓"
            elif signal_strength >= 60:
                strategy["scaling_strategy"] = "分批建仓：分3次建立仓位"
            elif signal_strength >= 50:
                strategy["scaling_strategy"] = "谨慎建仓：观察确认后小幅加仓"
            else:
                strategy["scaling_strategy"] = "保守策略：维持小仓位观望"
            
            return strategy
        except Exception:
            return {"initial_position": 0, "max_position": 0, "scaling_strategy": "保守策略", "risk_per_trade": 0.01, "portfolio_allocation": 0.03}
    
    def generate_entry_strategy(self, signals: Dict[str, Any], technical_analysis: Dict) -> str:
        """生成入场策略"""
        try:
            signal = signals.get("overall_signal", "持有")
            entry_points = signals.get("entry_points", [])
            
            if signal in ["强烈买入", "买入", "谨慎买入"]:
                strategy = "建议分批买入策略："
                if entry_points:
                    strategy += f"\n1. 首次买入：当价格回调至{entry_points[0]['price']:.2f}附近时建立初始仓位"
                    if len(entry_points) > 1:
                        strategy += f"\n2. 加仓机会：价格进一步回调至{entry_points[1]['price']:.2f}时可考虑加仓"
                    if len(entry_points) > 2:
                        strategy += f"\n3. 最后机会：{entry_points[2]['price']:.2f}是重要支撑位，可考虑最后一次买入"
                else:
                    strategy += "\n当前价位可考虑小仓位试探性买入，等待更好的入场时机"
                
                strategy += "\n注意：严格执行止损，控制单笔风险"
                
            elif signal in ["强烈卖出", "卖出", "谨慎卖出"]:
                strategy = "建议减仓或清仓策略："
                strategy += "\n1. 立即减仓：当前价位可考虑减少部分仓位"
                strategy += "\n2. 反弹卖出：如有反弹至阻力位附近，坚决卖出"
                strategy += "\n3. 止损保护：设置严格止损，防止进一步亏损"
                
            else:
                strategy = "持有策略：维持现有仓位，密切关注市场变化，等待明确的买卖信号"
            
            return strategy
        except Exception:
            return "入场策略生成失败，建议谨慎操作"
    
    def generate_exit_strategy(self, signals: Dict[str, Any], technical_analysis: Dict) -> str:
        """生成出场策略"""
        try:
            signal = signals.get("overall_signal", "持有")
            exit_points = signals.get("exit_points", [])
            take_profit = signals.get("take_profit", 0)
            stop_loss = signals.get("stop_loss", 0)
            
            strategy = "出场策略："
            
            if signal in ["强烈买入", "买入", "谨慎买入"]:
                if take_profit > 0:
                    strategy += f"\n1. 获利了结：价格达到{take_profit:.2f}时分批获利了结"
                
                if exit_points:
                    strategy += f"\n2. 阻力位减仓：价格接近{exit_points[0]['price']:.2f}阻力位时可考虑部分获利"
                
                if stop_loss > 0:
                    strategy += f"\n3. 止损保护：价格跌破{stop_loss:.2f}时严格止损"
                
                strategy += "\n4. 跟踪止损：价格上涨过程中逐步提高止损位，保护利润"
                
            elif signal in ["强烈卖出", "卖出", "谨慎卖出"]:
                strategy += "\n1. 立即出场：建议尽快减仓或清仓"
                if stop_loss > 0:
                    strategy += f"\n2. 反弹止损：如有反弹至{stop_loss:.2f}以上，坚决止损"
                strategy += "\n3. 分批出场：避免一次性大量卖出对价格造成冲击"
                
            else:
                strategy += "\n1. 维持观望：暂时持有现有仓位"
                strategy += "\n2. 设置保护：设置适当的止损位保护资金"
                strategy += "\n3. 灵活应对：根据市场变化及时调整策略"
            
            return strategy
        except Exception:
            return "出场策略生成失败，建议设置保护性止损"
    
    def generate_enhanced_trading_strategy_description(self, signals: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """生成增强的交易策略描述"""
        try:
            signal = signals.get("overall_signal", "持有")
            signal_strength = signals.get("signal_strength", 0)
            risk_reward_ratio = signals.get("risk_reward_ratio", 0)
            confidence_level = signals.get("confidence_level", 0)
            
            strategy = f"交易建议：{signal}（信号强度：{signal_strength:.1f}分）\n"
            
            # 添加置信度信息
            if confidence_level >= 70:
                strategy += "预测可信度：高，建议积极操作\n"
            elif confidence_level >= 50:
                strategy += "预测可信度：中等，建议谨慎操作\n"
            else:
                strategy += "预测可信度：较低，建议保守操作\n"
            
            # 添加风险收益比信息
            if risk_reward_ratio > 0:
                strategy += f"风险收益比：1:{risk_reward_ratio}\n"
                if risk_reward_ratio >= 2:
                    strategy += "风险收益比良好，值得考虑\n"
                elif risk_reward_ratio >= 1.5:
                    strategy += "风险收益比一般，需谨慎评估\n"
                else:
                    strategy += "风险收益比偏低，建议观望\n"
            
            # 添加具体操作建议
            position_management = signals.get("position_management", {})
            initial_position = position_management.get("initial_position", 0)
            
            if initial_position > 0:
                strategy += f"建议仓位：{initial_position*100:.0f}%\n"
                strategy += f"风险控制：单笔风险不超过{position_management.get('risk_per_trade', 0.02)*100:.1f}%\n"
            
            # 添加时间框架
            time_horizon = signals.get("time_horizon", "中期")
            strategy += f"持有周期：{time_horizon}\n"
            
            # 添加关键因素
            signal_details = signals.get("signal_details", {})
            key_factors = signal_details.get("key_factors", [])
            if key_factors:
                strategy += f"关键因素：{', '.join(key_factors[:3])}\n"
            
            return strategy.strip()
        except Exception:
            return "交易策略生成失败"
    
    def identify_key_signal_factors(self, analysis: Dict[str, Any]) -> List[str]:
        """识别关键信号因素"""
        try:
            factors = []
            
            # 技术面因素
            technical = analysis.get("technical_analysis", {})
            if technical.get("technical_score", 50) > 60:
                factors.append("技术面偏强")
            elif technical.get("technical_score", 50) < 40:
                factors.append("技术面偏弱")
            
            # 量价因素
            volume = analysis.get("volume_analysis", {})
            if volume.get("volume_ratio", 1) > 1.5:
                factors.append("成交量放大")
            elif volume.get("volume_ratio", 1) < 0.7:
                factors.append("成交量萎缩")
            
            # 情绪因素
            sentiment = analysis.get("sentiment_analysis", {})
            if sentiment.get("sentiment_score", 50) > 60:
                factors.append("市场情绪乐观")
            elif sentiment.get("sentiment_score", 50) < 40:
                factors.append("市场情绪悲观")
            
            # 趋势因素
            trend = analysis.get("trend_prediction", {})
            short_term = trend.get("short_term_trend", "")
            if short_term in ["上涨", "强势上涨"]:
                factors.append("短期趋势向上")
            elif short_term in ["下跌", "强势下跌"]:
                factors.append("短期趋势向下")
            
            return factors[:5]  # 返回最多5个关键因素
        except Exception:
            return []
    
    # ==================== 辅助分析方法 ====================
    
    def calculate_max_drawdown(self, prices: List[float]) -> float:
        """计算最大回撤"""
        try:
            if len(prices) < 2:
                return 0.0
            
            peak = prices[0]
            max_dd = 0.0
            
            for price in prices[1:]:
                if price > peak:
                    peak = price
                else:
                    drawdown = (peak - price) / peak
                    max_dd = max(max_dd, drawdown)
            
            return max_dd * 100
        except Exception:
            return 0.0
    
    def analyze_volume_trend(self, volume_data: Dict[str, Any]) -> str:
        """分析成交量趋势"""
        try:
            volume_trend = volume_data.get("volume_trend", 0)
            if volume_trend > 0.2:
                return "放量上涨"
            elif volume_trend > 0:
                return "温和放量"
            elif volume_trend > -0.2:
                return "正常"
            else:
                return "缩量下跌"
        except Exception:
            return "未知"
    
    def detect_volume_breakouts(self, volume_data: Dict[str, Any]) -> List[str]:
        """检测成交量突破信号"""
        try:
            signals = []
            volume_spikes = volume_data.get("volume_spikes", 0)
            
            if volume_spikes > 3:
                signals.append("异常放量")
            elif volume_spikes > 1:
                signals.append("温和放量")
            
            return signals
        except Exception:
            return []
    
    def calculate_accumulation_distribution(self, prices: List[Dict]) -> float:
        """计算累积/派发线"""
        try:
            if not prices or len(prices) < 2:
                return 0.0
            
            ad_line = 0.0
            for price_data in prices:
                high = price_data.get('high', 0)
                low = price_data.get('low', 0)
                close = price_data.get('close', 0)
                volume = price_data.get('volume', 0)
                
                if high != low:
                    money_flow_multiplier = ((close - low) - (high - close)) / (high - low)
                    money_flow_volume = money_flow_multiplier * volume
                    ad_line += money_flow_volume
            
            return ad_line
        except Exception:
            return 0.0
    
    def calculate_money_flow_index(self, prices: List[Dict]) -> float:
        """计算资金流量指标"""
        try:
            if not prices or len(prices) < 14:
                return 50.0
            
            positive_flow = 0
            negative_flow = 0
            
            for i in range(1, min(len(prices), 15)):
                current = prices[i]
                previous = prices[i-1]
                
                current_price = (current.get('high', 0) + current.get('low', 0) + current.get('close', 0)) / 3
                previous_price = (previous.get('high', 0) + previous.get('low', 0) + previous.get('close', 0)) / 3
                
                raw_money_flow = current_price * current.get('volume', 0)
                
                if current_price > previous_price:
                    positive_flow += raw_money_flow
                elif current_price < previous_price:
                    negative_flow += raw_money_flow
            
            if negative_flow == 0:
                return 100.0
            
            money_ratio = positive_flow / negative_flow
            mfi = 100 - (100 / (1 + money_ratio))
            
            return mfi
        except Exception:
            return 50.0
    
    def calculate_vwap(self, prices: List[Dict]) -> float:
        """计算成交量加权平均价格"""
        try:
            if not prices:
                return 0.0
            
            total_volume = 0
            total_price_volume = 0
            
            for price_data in prices:
                price = (price_data.get('high', 0) + price_data.get('low', 0) + price_data.get('close', 0)) / 3
                volume = price_data.get('volume', 0)
                
                total_price_volume += price * volume
                total_volume += volume
            
            if total_volume == 0:
                return 0.0
            
            return total_price_volume / total_volume
        except Exception:
            return 0.0
    
    def generate_volume_analysis_summary(self, volume_data: Dict[str, Any]) -> str:
        """生成量价分析摘要"""
        try:
            volume_trend = self.analyze_volume_trend(volume_data)
            breakouts = self.detect_volume_breakouts(volume_data)
            
            summary = f"成交量呈现{volume_trend}态势"
            if breakouts:
                summary += f"，出现{', '.join(breakouts)}信号"
            
            return summary
        except Exception:
            return "量价分析数据不足"
    
    def analyze_moving_averages(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析移动平均线"""
        try:
            ma5 = indicators.get("ma5", 0)
            ma10 = indicators.get("ma10", 0)
            ma20 = indicators.get("ma20", 0)
            ma60 = indicators.get("ma60", 0)
            current_price = indicators.get("current_price", 0)
            
            analysis = {
                "trend": "震荡",
                "support_level": min(ma5, ma10, ma20, ma60) if all([ma5, ma10, ma20, ma60]) else 0,
                "resistance_level": max(ma5, ma10, ma20, ma60) if all([ma5, ma10, ma20, ma60]) else 0,
                "position": "中性"
            }
            
            # 判断趋势
            if ma5 > ma10 > ma20 > ma60:
                analysis["trend"] = "强势上涨"
            elif ma5 > ma10 > ma20:
                analysis["trend"] = "上涨"
            elif ma5 < ma10 < ma20 < ma60:
                analysis["trend"] = "强势下跌"
            elif ma5 < ma10 < ma20:
                analysis["trend"] = "下跌"
            
            # 判断价格位置
            if current_price > ma5:
                analysis["position"] = "强势"
            elif current_price > ma20:
                analysis["position"] = "偏强"
            elif current_price < ma60:
                analysis["position"] = "弱势"
            else:
                analysis["position"] = "偏弱"
            
            return analysis
        except Exception:
            return {"trend": "未知", "support_level": 0, "resistance_level": 0, "position": "未知"}
    
    def analyze_macd_signals(self, macd_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析MACD信号"""
        try:
            macd = macd_data.get("macd", 0)
            signal = macd_data.get("signal", 0)
            histogram = macd_data.get("histogram", 0)
            
            analysis = {
                "signal": "中性",
                "trend": "震荡",
                "strength": "一般"
            }
            
            # MACD信号判断
            if macd > signal and histogram > 0:
                analysis["signal"] = "买入"
                analysis["trend"] = "上涨"
            elif macd < signal and histogram < 0:
                analysis["signal"] = "卖出"
                analysis["trend"] = "下跌"
            
            # 信号强度
            if abs(histogram) > 0.5:
                analysis["strength"] = "强"
            elif abs(histogram) > 0.2:
                analysis["strength"] = "中等"
            else:
                analysis["strength"] = "弱"
            
            return analysis
        except Exception:
            return {"signal": "未知", "trend": "未知", "strength": "未知"}
    
    def analyze_rsi_signals(self, rsi: float) -> Dict[str, Any]:
        """分析RSI信号"""
        try:
            analysis = {
                "level": "正常",
                "signal": "中性",
                "overbought": False,
                "oversold": False
            }
            
            if rsi >= 70:
                analysis["level"] = "超买"
                analysis["signal"] = "卖出"
                analysis["overbought"] = True
            elif rsi <= 30:
                analysis["level"] = "超卖"
                analysis["signal"] = "买入"
                analysis["oversold"] = True
            elif rsi >= 60:
                analysis["level"] = "偏强"
                analysis["signal"] = "谨慎"
            elif rsi <= 40:
                analysis["level"] = "偏弱"
                analysis["signal"] = "关注"
            
            return analysis
        except Exception:
            return {"level": "未知", "signal": "未知", "overbought": False, "oversold": False}
    
    def analyze_bollinger_bands(self, bollinger_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析布林带信号"""
        try:
            upper = bollinger_data.get("upper", 0)
            middle = bollinger_data.get("middle", 0)
            lower = bollinger_data.get("lower", 0)
            current_price = bollinger_data.get("current_price", 0)
            
            analysis = {
                "position": "中轨附近",
                "signal": "中性",
                "volatility": "正常"
            }
            
            if current_price >= upper:
                analysis["position"] = "上轨附近"
                analysis["signal"] = "超买"
            elif current_price <= lower:
                analysis["position"] = "下轨附近"
                analysis["signal"] = "超卖"
            elif current_price > middle:
                analysis["position"] = "中轨上方"
                analysis["signal"] = "偏强"
            else:
                analysis["position"] = "中轨下方"
                analysis["signal"] = "偏弱"
            
            # 计算波动率
            if upper > 0 and lower > 0:
                band_width = (upper - lower) / middle
                if band_width > 0.2:
                    analysis["volatility"] = "高"
                elif band_width < 0.1:
                    analysis["volatility"] = "低"
            
            return analysis
        except Exception:
            return {"position": "未知", "signal": "未知", "volatility": "未知"}
    
    def analyze_kdj_signals(self, kdj_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析KDJ信号"""
        try:
            k = kdj_data.get("k", 50)
            d = kdj_data.get("d", 50)
            j = kdj_data.get("j", 50)
            
            analysis = {
                "signal": "中性",
                "trend": "震荡",
                "overbought": False,
                "oversold": False
            }
            
            # KDJ信号判断
            if k > 80 and d > 80:
                analysis["signal"] = "卖出"
                analysis["overbought"] = True
            elif k < 20 and d < 20:
                analysis["signal"] = "买入"
                analysis["oversold"] = True
            elif k > d:
                analysis["signal"] = "偏多"
                analysis["trend"] = "上涨"
            elif k < d:
                analysis["signal"] = "偏空"
                analysis["trend"] = "下跌"
            
            return analysis
        except Exception:
            return {"signal": "未知", "trend": "未知", "overbought": False, "oversold": False}
    
    def calculate_technical_score(self, indicators: Dict[str, Any]) -> float:
        """计算技术分析得分"""
        try:
            score = 50.0  # 基础分数
            
            # MACD得分
            macd_data = indicators.get("macd", {})
            if macd_data.get("histogram", 0) > 0:
                score += 10
            elif macd_data.get("histogram", 0) < 0:
                score -= 10
            
            # RSI得分
            rsi = indicators.get("rsi", 50)
            if 30 <= rsi <= 70:
                score += 5
            elif rsi > 70:
                score -= 15
            elif rsi < 30:
                score += 15
            
            # 移动平均线得分
            ma5 = indicators.get("ma5", 0)
            ma20 = indicators.get("ma20", 0)
            current_price = indicators.get("current_price", 0)
            
            if current_price > ma5 > ma20:
                score += 15
            elif current_price < ma5 < ma20:
                score -= 15
            
            return max(0, min(100, score))
        except Exception:
            return 50.0
    
    def calculate_signal_strength(self, indicators: Dict[str, Any]) -> float:
        """计算信号强度"""
        try:
            strength = 0.0
            
            # MACD强度
            macd_data = indicators.get("macd", {})
            histogram = abs(macd_data.get("histogram", 0))
            strength += min(histogram * 20, 30)
            
            # RSI强度
            rsi = indicators.get("rsi", 50)
            if rsi > 70 or rsi < 30:
                strength += abs(rsi - 50)
            
            # 成交量强度
            volume_ratio = indicators.get("volume_ratio", 1.0)
            if volume_ratio > 1.5:
                strength += 20
            elif volume_ratio > 1.2:
                strength += 10
            
            return min(strength, 100)
        except Exception:
            return 0.0
    
    def generate_technical_summary(self, indicators: Dict[str, Any]) -> str:
        """生成详细的技术分析摘要"""
        try:
            score = self.calculate_technical_score(indicators)
            summary_parts = []
            
            # 基础评分描述
            if score >= 70:
                base_desc = "技术面表现强势，多项指标显示买入信号"
            elif score >= 60:
                base_desc = "技术面偏强，整体趋势向好"
            elif score >= 40:
                base_desc = "技术面中性，建议观望"
            elif score >= 30:
                base_desc = "技术面偏弱，存在下跌风险"
            else:
                base_desc = "技术面疲弱，建议谨慎"
            
            summary_parts.append(f"{base_desc}（综合得分：{score:.1f}）")
            
            # 均线分析
            if 'ma5' in indicators and 'ma20' in indicators and 'ma60' in indicators:
                ma_analysis = self.analyze_moving_averages(indicators)
                if ma_analysis.get('trend') == 'bullish':
                    summary_parts.append("均线系统呈多头排列，短期趋势向上")
                elif ma_analysis.get('trend') == 'bearish':
                    summary_parts.append("均线系统呈空头排列，短期趋势向下")
                else:
                    summary_parts.append("均线系统交织，趋势不明确")
            
            # MACD分析
            if 'macd' in indicators:
                macd_analysis = self.analyze_macd_signals(indicators['macd'])
                if macd_analysis.get('signal') == 'bullish':
                    summary_parts.append("MACD指标显示买入信号")
                elif macd_analysis.get('signal') == 'bearish':
                    summary_parts.append("MACD指标显示卖出信号")
            
            # RSI分析
            if 'rsi' in indicators:
                rsi_analysis = self.analyze_rsi_signals(indicators['rsi'])
                if rsi_analysis.get('condition') == 'overbought':
                    summary_parts.append("RSI指标显示超买状态")
                elif rsi_analysis.get('condition') == 'oversold':
                    summary_parts.append("RSI指标显示超卖状态")
                elif rsi_analysis.get('condition') == 'neutral':
                    summary_parts.append("RSI指标处于正常区间")
            
            # 布林带分析
            if 'bollinger' in indicators:
                bb_analysis = self.analyze_bollinger_bands(indicators['bollinger'])
                if bb_analysis.get('position') == 'upper':
                    summary_parts.append("价格接近布林带上轨，存在回调风险")
                elif bb_analysis.get('position') == 'lower':
                    summary_parts.append("价格接近布林带下轨，可能存在反弹机会")
            
            # KDJ分析
            if 'kdj' in indicators:
                kdj_analysis = self.analyze_kdj_signals(indicators['kdj'])
                if kdj_analysis.get('signal') == 'golden_cross':
                    summary_parts.append("KDJ指标出现金叉信号")
                elif kdj_analysis.get('signal') == 'death_cross':
                    summary_parts.append("KDJ指标出现死叉信号")
            
            return "；".join(summary_parts) + "。"
            
        except Exception as e:
            return f"技术分析数据处理异常：{str(e)}，建议重新获取数据后分析"
    
    def identify_support_levels(self, df: pd.DataFrame) -> List[float]:
        """识别支撑位"""
        try:
            if len(df) < 20:
                return []
            
            lows = df['low'].rolling(window=5, center=True).min()
            support_levels = []
            
            for i in range(2, len(df) - 2):
                if df['low'].iloc[i] == lows.iloc[i] and df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i+1]:
                    support_levels.append(float(df['low'].iloc[i]))
            
            # 返回最近的3个支撑位
            return sorted(support_levels)[-3:] if support_levels else []
        except Exception:
            return []
    
    def identify_resistance_levels(self, df: pd.DataFrame) -> List[float]:
        """识别阻力位"""
        try:
            if len(df) < 20:
                return []
            
            highs = df['high'].rolling(window=5, center=True).max()
            resistance_levels = []
            
            for i in range(2, len(df) - 2):
                if df['high'].iloc[i] == highs.iloc[i] and df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i+1]:
                    resistance_levels.append(float(df['high'].iloc[i]))
            
            # 返回最近的3个阻力位
            return sorted(resistance_levels)[-3:] if resistance_levels else []
        except Exception:
            return []
    
    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """计算趋势强度"""
        try:
            if len(df) < 20:
                return 0.0
            
            # 使用线性回归计算趋势强度
            x = np.arange(len(df))
            y = df['close'].values
            
            correlation = np.corrcoef(x, y)[0, 1]
            return abs(correlation) * 100
        except Exception:
            return 0.0
    
    def calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """计算动量得分"""
        try:
            if len(df) < 10:
                return 0.0
            
            # 计算多个时间周期的动量
            momentum_5d = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] if len(df) >= 6 else 0
            momentum_10d = (df['close'].iloc[-1] - df['close'].iloc[-11]) / df['close'].iloc[-11] if len(df) >= 11 else 0
            momentum_20d = (df['close'].iloc[-1] - df['close'].iloc[-21]) / df['close'].iloc[-21] if len(df) >= 21 else 0
            
            # 加权平均
            momentum_score = (momentum_5d * 0.5 + momentum_10d * 0.3 + momentum_20d * 0.2) * 100
            
            # 标准化到0-100
            return max(0, min(100, 50 + momentum_score * 10))
        except Exception:
            return 50.0
    
    def generate_stock_analysis_summary(self, ticker: str, analysis: Dict[str, Any]) -> str:
        """生成股票分析摘要"""
        try:
            summary_parts = []
            
            # 基本信息
            current_price = analysis.get("price_analysis", {}).get("current_price", 0)
            if current_price > 0:
                summary_parts.append(f"{ticker} 当前价格: {current_price:.2f}元")
            
            # 技术面总结
            technical_score = analysis.get("technical_analysis", {}).get("technical_score", 0)
            if technical_score > 0:
                tech_level = "强势" if technical_score >= 70 else "中性" if technical_score >= 40 else "弱势"
                summary_parts.append(f"技术面: {tech_level} (得分: {technical_score:.0f})")
            
            # 交易建议
            trading_signal = analysis.get("trading_signals", {}).get("overall_signal", "持有")
            signal_strength = analysis.get("trading_signals", {}).get("signal_strength", 0)
            summary_parts.append(f"交易建议: {trading_signal} (信号强度: {signal_strength:.0f})")
            
            # 风险评估
            risk_level = analysis.get("risk_assessment", {}).get("overall_risk", "中等")
            summary_parts.append(f"风险等级: {risk_level}")
            
            return " | ".join(summary_parts)
        except Exception:
            return f"{ticker} 分析摘要生成失败"
    
    # ==================== 市场情绪分析方法 ====================
    
    def analyze_money_flow(self, money_flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析资金流向"""
        try:
            main_inflow = money_flow_data.get("main_inflow", 0)
            retail_inflow = money_flow_data.get("retail_inflow", 0)
            total_flow = main_inflow + retail_inflow
            
            analysis = {
                "trend": "中性",
                "strength": "一般",
                "main_participation": "正常"
            }
            
            if total_flow > 0:
                analysis["trend"] = "资金净流入"
                if total_flow > 10000000:  # 1000万
                    analysis["strength"] = "强"
                elif total_flow > 5000000:  # 500万
                    analysis["strength"] = "中等"
            elif total_flow < 0:
                analysis["trend"] = "资金净流出"
                if abs(total_flow) > 10000000:
                    analysis["strength"] = "强"
                elif abs(total_flow) > 5000000:
                    analysis["strength"] = "中等"
            
            # 主力参与度
            if abs(main_inflow) > abs(retail_inflow) * 2:
                analysis["main_participation"] = "高"
            elif abs(main_inflow) < abs(retail_inflow) * 0.5:
                analysis["main_participation"] = "低"
            
            return analysis
        except Exception:
            return {"trend": "未知", "strength": "未知", "main_participation": "未知"}
    
    def analyze_institutional_activity(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析机构活动"""
        try:
            dragon_tiger_data = sentiment_data.get("dragon_tiger", {})
            
            analysis = {
                "activity_level": "正常",
                "net_position": "中性",
                "participation": "一般"
            }
            
            buy_amount = dragon_tiger_data.get("buy_amount", 0)
            sell_amount = dragon_tiger_data.get("sell_amount", 0)
            net_amount = buy_amount - sell_amount
            
            if abs(net_amount) > 50000000:  # 5000万
                analysis["activity_level"] = "活跃"
            elif abs(net_amount) > 20000000:  # 2000万
                analysis["activity_level"] = "较活跃"
            
            if net_amount > 0:
                analysis["net_position"] = "净买入"
            elif net_amount < 0:
                analysis["net_position"] = "净卖出"
            
            return analysis
        except Exception:
            return {"activity_level": "未知", "net_position": "未知", "participation": "未知"}
    
    def analyze_market_attention(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场关注度"""
        try:
            analysis = {
                "attention_level": "正常",
                "trend": "稳定"
            }
            
            # 这里可以根据实际数据源添加关注度分析
            # 例如：搜索热度、新闻提及次数、社交媒体讨论等
            
            return analysis
        except Exception:
            return {"attention_level": "未知", "trend": "未知"}
    
    def calculate_sentiment_score(self, sentiment_data: Dict[str, Any]) -> float:
        """计算市场情绪得分"""
        try:
            score = 50.0  # 基础分数
            
            # 资金流向得分
            money_flow = sentiment_data.get("money_flow", {})
            main_inflow = money_flow.get("main_inflow", 0)
            if main_inflow > 0:
                score += min(main_inflow / 10000000 * 10, 20)  # 最多加20分
            else:
                score += max(main_inflow / 10000000 * 10, -20)  # 最多减20分
            
            # 机构活动得分
            dragon_tiger = sentiment_data.get("dragon_tiger", {})
            net_amount = dragon_tiger.get("buy_amount", 0) - dragon_tiger.get("sell_amount", 0)
            if net_amount > 0:
                score += min(net_amount / 50000000 * 15, 15)  # 最多加15分
            else:
                score += max(net_amount / 50000000 * 15, -15)  # 最多减15分
            
            return max(0, min(100, score))
        except Exception:
            return 50.0
    
    def determine_sentiment_trend(self, sentiment_data: Dict[str, Any]) -> str:
        """确定情绪趋势"""
        try:
            score = self.calculate_sentiment_score(sentiment_data)
            
            if score >= 70:
                return "乐观"
            elif score >= 60:
                return "偏乐观"
            elif score >= 40:
                return "中性"
            elif score >= 30:
                return "偏悲观"
            else:
                return "悲观"
        except Exception:
            return "中性"
    
    def generate_sentiment_summary(self, sentiment_data: Dict[str, Any]) -> str:
        """生成情绪分析摘要"""
        try:
            trend = self.determine_sentiment_trend(sentiment_data)
            money_flow_analysis = self.analyze_money_flow(sentiment_data.get("money_flow", {}))
            
            summary = f"市场情绪{trend}"
            if money_flow_analysis["trend"] != "中性":
                summary += f"，{money_flow_analysis['trend']}"
            
            return summary
        except Exception:
            return "市场情绪分析数据不足"
    
    # ==================== 趋势预测方法 ====================
    
    def predict_short_term_trend(self, prices: List[Dict]) -> str:
        """预测短期趋势（1-5天）"""
        try:
            if len(prices) < 5:
                return "数据不足"
            
            recent_prices = [p.get('close', 0) for p in prices[-5:]]
            
            # 计算短期趋势
            trend_score = 0
            for i in range(1, len(recent_prices)):
                if recent_prices[i] > recent_prices[i-1]:
                    trend_score += 1
                elif recent_prices[i] < recent_prices[i-1]:
                    trend_score -= 1
            
            if trend_score >= 3:
                return "上涨"
            elif trend_score <= -3:
                return "下跌"
            elif trend_score > 0:
                return "偏强"
            elif trend_score < 0:
                return "偏弱"
            else:
                return "震荡"
        except Exception:
            return "未知"
    
    def predict_medium_term_trend(self, prices: List[Dict]) -> str:
        """预测中期趋势（5-20天）"""
        try:
            if len(prices) < 20:
                return "数据不足"
            
            # 使用移动平均线判断中期趋势
            recent_prices = [p.get('close', 0) for p in prices[-20:]]
            ma5 = sum(recent_prices[-5:]) / 5
            ma10 = sum(recent_prices[-10:]) / 10
            ma20 = sum(recent_prices) / 20
            current_price = recent_prices[-1]
            
            if current_price > ma5 > ma10 > ma20:
                return "强势上涨"
            elif current_price > ma5 > ma10:
                return "上涨"
            elif current_price < ma5 < ma10 < ma20:
                return "强势下跌"
            elif current_price < ma5 < ma10:
                return "下跌"
            else:
                return "震荡"
        except Exception:
            return "未知"
    
    def predict_long_term_trend(self, prices: List[Dict]) -> str:
        """预测长期趋势（20-60天）"""
        try:
            if len(prices) < 60:
                return "数据不足"
            
            # 使用长期移动平均线和趋势线分析
            all_prices = [p.get('close', 0) for p in prices]
            ma20 = sum(all_prices[-20:]) / 20
            ma60 = sum(all_prices[-60:]) / 60
            
            # 计算长期趋势强度
            x = np.arange(60)
            y = np.array(all_prices[-60:])
            
            try:
                slope = np.polyfit(x, y, 1)[0]
                
                if slope > 0.1:
                    return "长期上涨"
                elif slope > 0.05:
                    return "温和上涨"
                elif slope < -0.1:
                    return "长期下跌"
                elif slope < -0.05:
                    return "温和下跌"
                else:
                    return "长期震荡"
            except:
                # 备用方法：比较移动平均线
                if ma20 > ma60 * 1.05:
                    return "长期上涨"
                elif ma20 < ma60 * 0.95:
                    return "长期下跌"
                else:
                    return "长期震荡"
        except Exception:
            return "未知"
    
    def calculate_price_targets(self, prices: List[Dict]) -> Dict[str, float]:
        """计算价格目标"""
        try:
            if not prices:
                return {"support": 0, "resistance": 0, "target_price": 0}
            
            recent_prices = [p.get('close', 0) for p in prices[-20:] if p.get('close', 0) > 0]
            if not recent_prices:
                return {"support": 0, "resistance": 0, "target_price": 0}
            
            current_price = recent_prices[-1]
            high_20d = max(recent_prices)
            low_20d = min(recent_prices)
            
            # 简单的支撑阻力计算
            support = low_20d * 0.98
            resistance = high_20d * 1.02
            
            # 目标价格（基于技术分析）
            price_range = high_20d - low_20d
            if current_price > (high_20d + low_20d) / 2:
                target_price = current_price + price_range * 0.618  # 黄金分割
            else:
                target_price = current_price + price_range * 0.382
            
            return {
                "support": support,
                "resistance": resistance,
                "target_price": target_price
            }
        except Exception:
            return {"support": 0, "resistance": 0, "target_price": 0}
    
    def detect_trend_reversal_signals(self, prices: List[Dict]) -> List[str]:
        """检测趋势反转信号"""
        try:
            if len(prices) < 10:
                return []
            
            signals = []
            recent_prices = [p.get('close', 0) for p in prices[-10:]]
            
            # 检测双顶/双底
            if len(recent_prices) >= 5:
                highs = [recent_prices[i] for i in range(1, len(recent_prices)-1) 
                        if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]]
                lows = [recent_prices[i] for i in range(1, len(recent_prices)-1) 
                       if recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]]
                
                if len(highs) >= 2 and abs(highs[-1] - highs[-2]) / highs[-1] < 0.02:
                    signals.append("双顶形态")
                
                if len(lows) >= 2 and abs(lows[-1] - lows[-2]) / lows[-1] < 0.02:
                    signals.append("双底形态")
            
            # 检测背离
            if len(recent_prices) >= 6:
                price_trend = recent_prices[-1] - recent_prices[-6]
                if abs(price_trend) / recent_prices[-6] > 0.05:
                    if price_trend > 0:
                        signals.append("价格创新高")
                    else:
                        signals.append("价格创新低")
            
            return signals
        except Exception:
            return []
    
    def calculate_prediction_confidence(self, prices: List[Dict]) -> float:
        """计算预测置信度"""
        try:
            if len(prices) < 20:
                return 30.0  # 数据不足，低置信度
            
            confidence = 50.0  # 基础置信度
            
            # 数据质量评分
            if len(prices) >= 60:
                confidence += 20
            elif len(prices) >= 30:
                confidence += 10
            
            # 趋势一致性评分
            recent_prices = [p.get('close', 0) for p in prices[-10:]]
            trend_consistency = 0
            for i in range(1, len(recent_prices)):
                if (recent_prices[i] > recent_prices[i-1]) == (recent_prices[-1] > recent_prices[0]):
                    trend_consistency += 1
            
            consistency_score = (trend_consistency / (len(recent_prices) - 1)) * 20
            confidence += consistency_score
            
            # 波动率评分（波动率越低，置信度越高）
            if len(recent_prices) > 1:
                volatility = np.std(recent_prices) / np.mean(recent_prices)
                if volatility < 0.02:
                    confidence += 10
                elif volatility > 0.05:
                    confidence -= 10
            
            return max(20, min(90, confidence))
        except Exception:
            return 50.0
    
    def generate_prediction_summary(self, prices: List[Dict]) -> str:
        """生成预测摘要"""
        try:
            short_term = self.predict_short_term_trend(prices)
            medium_term = self.predict_medium_term_trend(prices)
            confidence = self.calculate_prediction_confidence(prices)
            
            summary = f"短期趋势{short_term}，中期趋势{medium_term}"
            
            if confidence >= 70:
                summary += "，预测可信度较高"
            elif confidence >= 50:
                summary += "，预测可信度一般"
            else:
                summary += "，预测可信度较低"
            
            return summary
        except Exception:
            return "趋势预测数据不足"
    
    def generate_trading_strategy_description(self, signals: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """生成交易策略描述"""
        try:
            signal = signals.get("overall_signal", "持有")
            position_sizing = signals.get("position_sizing", "中等")
            time_horizon = signals.get("time_horizon", "中期")
            
            strategy = f"建议{signal}，采用{position_sizing}仓位，{time_horizon}持有"
            
            # 添加具体建议
            if signal in ["买入", "强烈买入"]:
                strategy += "。建议分批建仓，控制风险"
            elif signal in ["卖出", "强烈卖出"]:
                strategy += "。建议及时止损，保护资金"
            else:
                strategy += "。建议观望，等待明确信号"
            
            return strategy
        except Exception:
            return "交易策略生成失败"
        # 简化实现
        return 0.0
    
    def calculate_money_flow_index(self, prices: List) -> float:
        """计算资金流量指数"""
        # 简化实现
        return 50.0
    
    def calculate_vwap(self, prices: List) -> float:
        """计算成交量加权平均价格"""
        # 简化实现
        if prices:
            return sum(p.close for p in prices) / len(prices)
        return 0.0
    
    def generate_volume_analysis_summary(self, volume_data: Dict) -> str:
        """生成成交量分析摘要"""
        trend = self.analyze_volume_trend(volume_data)
        return f"成交量分析: {trend}"
    
    def analyze_moving_averages(self, indicators: Dict) -> Dict:
        """分析移动平均线"""
        ma5 = indicators.get("ma5", 0)
        ma10 = indicators.get("ma10", 0)
        ma20 = indicators.get("ma20", 0)
        
        analysis = {
            "trend": "上升" if ma5 > ma10 > ma20 else "下降" if ma5 < ma10 < ma20 else "震荡",
            "signal": "多头排列" if ma5 > ma10 > ma20 else "空头排列" if ma5 < ma10 < ma20 else "均线纠缠"
        }
        return analysis
    
    def analyze_macd_signals(self, macd_data: Dict) -> Dict:
        """分析MACD信号"""
        macd_line = macd_data.get("macd_line", 0)
        signal_line = macd_data.get("signal_line", 0)
        histogram = macd_data.get("histogram", 0)
        
        analysis = {
            "signal": "金叉" if macd_line > signal_line and histogram > 0 else "死叉" if macd_line < signal_line and histogram < 0 else "中性",
            "trend": "向上" if histogram > 0 else "向下"
        }
        return analysis
    
    def analyze_rsi_signals(self, rsi: float) -> Dict:
        """分析RSI信号"""
        analysis = {
            "level": "超买" if rsi > 70 else "超卖" if rsi < 30 else "正常",
            "signal": "卖出" if rsi > 80 else "买入" if rsi < 20 else "持有"
        }
        return analysis
    
    def analyze_bollinger_bands(self, bb_data: Dict) -> Dict:
        """分析布林带"""
        position = bb_data.get("position", 0.5)
        
        analysis = {
            "position": "上轨附近" if position > 0.8 else "下轨附近" if position < 0.2 else "中轨附近",
            "signal": "超买" if position > 0.9 else "超卖" if position < 0.1 else "正常"
        }
        return analysis
    
    def analyze_kdj_signals(self, kdj_data: Dict) -> Dict:
        """分析KDJ信号"""
        k = kdj_data.get("k", 50)
        d = kdj_data.get("d", 50)
        j = kdj_data.get("j", 50)
        
        analysis = {
            "signal": "金叉" if k > d and j > 50 else "死叉" if k < d and j < 50 else "中性",
            "level": "超买" if k > 80 else "超卖" if k < 20 else "正常"
        }
        return analysis
    
    def calculate_technical_score(self, indicators: Dict) -> float:
        """计算技术面综合得分"""
        score = 50.0  # 基础分数
        
        # RSI评分
        rsi = indicators.get("rsi", 50)
        if 30 <= rsi <= 70:
            score += 10
        elif rsi < 30:
            score += 5  # 超卖可能反弹
        
        # MACD评分
        macd_data = indicators.get("macd", {})
        if macd_data.get("histogram", 0) > 0:
            score += 15
        
        # 布林带评分
        bb_data = indicators.get("bollinger_bands", {})
        position = bb_data.get("position", 0.5)
        if 0.2 <= position <= 0.8:
            score += 10
        
        return min(100, max(0, score))
    
    def calculate_signal_strength(self, indicators: Dict) -> float:
        """计算信号强度"""
        return self.calculate_technical_score(indicators)
    
    def generate_technical_summary(self, indicators: Dict) -> str:
        """生成技术面摘要"""
        score = self.calculate_technical_score(indicators)
        level = "强势" if score >= 70 else "中性" if score >= 40 else "弱势"
        return f"技术面{level}，综合得分{score:.0f}"
    
    def analyze_money_flow(self, money_flow_data: Dict) -> Dict:
        """分析资金流向"""
        if "error" in money_flow_data:
            return {"trend": "数据获取失败"}
        
        main_inflow_rate = money_flow_data.get("main_net_inflow_rate", 0)
        analysis = {
            "trend": "资金净流入" if main_inflow_rate > 0 else "资金净流出",
            "strength": "强" if abs(main_inflow_rate) > 5 else "中" if abs(main_inflow_rate) > 2 else "弱"
        }
        return analysis
    
    def analyze_institutional_activity(self, sentiment_data: Dict) -> Dict:
        """分析机构活动"""
        lhb_activity = sentiment_data.get("lhb_activity", 0)
        analysis = {
            "activity_level": "高" if lhb_activity > 5 else "中" if lhb_activity > 0 else "低",
            "attention": "机构关注" if lhb_activity > 0 else "关注度一般"
        }
        return analysis
    
    def analyze_market_attention(self, sentiment_data: Dict) -> Dict:
        """分析市场关注度"""
        return {"level": "中等"}
    
    def calculate_sentiment_score(self, sentiment_data: Dict) -> float:
        """计算情绪得分"""
        score = 50.0
        
        money_flow = sentiment_data.get("money_flow", {})
        if "error" not in money_flow:
            main_inflow_rate = money_flow.get("main_net_inflow_rate", 0)
            score += main_inflow_rate * 2  # 资金流入提升情绪
        
        lhb_activity = sentiment_data.get("lhb_activity", 0)
        if lhb_activity > 0:
            score += 10  # 龙虎榜活跃提升情绪
        
        return min(100, max(0, score))
    
    def determine_sentiment_trend(self, sentiment_data: Dict) -> str:
        """确定情绪趋势"""
        score = self.calculate_sentiment_score(sentiment_data)
        if score >= 60:
            return "乐观"
        elif score >= 40:
            return "中性"
        else:
            return "悲观"
    
    def generate_sentiment_summary(self, sentiment_data: Dict) -> str:
        """生成情绪摘要"""
        trend = self.determine_sentiment_trend(sentiment_data)
        score = self.calculate_sentiment_score(sentiment_data)
        return f"市场情绪{trend}，情绪得分{score:.0f}"
    
    def analyze_industry_comparison(self, ticker: str) -> Dict:
        """行业对比分析"""
        try:
            industry_data = get_industry_analysis_data(ticker)
            if "error" in industry_data:
                return industry_data
            
            analysis = {
                "industry": industry_data.get("industry", "未知"),
                "concept": industry_data.get("concept", "未知"),
                "industry_performance": self.analyze_industry_performance(industry_data),
                "relative_strength": self.calculate_relative_strength(industry_data)
            }
            return analysis
        except Exception as e:
            return {"error": f"行业分析失败: {str(e)}"}
    
    def analyze_industry_performance(self, industry_data: Dict) -> str:
        """分析行业表现"""
        industry_flow = industry_data.get("industry_flow", {})
        if "error" in industry_flow:
            return "行业数据获取失败"
        
        net_inflow_rate = industry_flow.get("net_inflow_rate", 0)
        if net_inflow_rate > 2:
            return "行业资金净流入，表现强势"
        elif net_inflow_rate > 0:
            return "行业资金小幅流入"
        elif net_inflow_rate > -2:
            return "行业资金小幅流出"
        else:
            return "行业资金大幅流出，表现疲弱"
    
    def calculate_relative_strength(self, industry_data: Dict) -> float:
        """计算相对强度"""
        industry_flow = industry_data.get("industry_flow", {})
        if "error" in industry_flow:
            return 50.0
        
        rank = industry_flow.get("rank", 50)
        # 假设总共100个行业，排名越靠前相对强度越高
        return max(0, min(100, 100 - rank))
    
    def analyze_fundamentals_enhanced(self, ticker: str, end_date: str) -> Dict:
        """增强基本面分析"""
        try:
            # 获取财务数据
            financial_metrics = get_financial_metrics(ticker, end_date)
            
            if not financial_metrics:
                return {"error": "无法获取财务数据"}
            
            latest_metrics = financial_metrics[0] if financial_metrics else None
            if not latest_metrics:
                return {"error": "财务数据为空"}
            
            analysis = {
                "profitability": self.analyze_profitability_enhanced(latest_metrics),
                "financial_health": self.analyze_financial_health_enhanced(latest_metrics),
                "growth_potential": self.analyze_growth_potential_enhanced(latest_metrics),
                "valuation": self.analyze_valuation_enhanced(latest_metrics),
                "fundamental_score": self.calculate_fundamental_score(latest_metrics)
            }
            
            return analysis
        except Exception as e:
            return {"error": f"基本面分析失败: {str(e)}"}
    
    def analyze_profitability_enhanced(self, metrics) -> Dict:
        """增强盈利能力分析"""
        return {
            "roe": getattr(metrics, 'return_on_equity', 0),
            "roa": getattr(metrics, 'return_on_assets', 0),
            "gross_margin": getattr(metrics, 'gross_profit_margin', 0),
            "net_margin": getattr(metrics, 'net_profit_margin', 0),
            "profitability_trend": "稳定"  # 简化实现
        }
    
    def analyze_financial_health_enhanced(self, metrics) -> Dict:
        """增强财务健康分析"""
        return {
            "debt_ratio": getattr(metrics, 'debt_to_equity_ratio', 0),
            "current_ratio": getattr(metrics, 'current_ratio', 0),
            "quick_ratio": getattr(metrics, 'quick_ratio', 0),
            "cash_flow": getattr(metrics, 'operating_cash_flow', 0),
            "financial_strength": "良好"  # 简化实现
        }
    
    def analyze_growth_potential_enhanced(self, metrics) -> Dict:
        """增强成长潜力分析"""
        return {
            "revenue_growth": getattr(metrics, 'revenue_growth', 0),
            "earnings_growth": getattr(metrics, 'earnings_growth', 0),
            "book_value_growth": 0,  # 简化实现
            "growth_sustainability": "中等"  # 简化实现
        }
    
    def analyze_valuation_enhanced(self, metrics) -> Dict:
        """增强估值分析"""
        return {
            "pe_ratio": getattr(metrics, 'price_to_earnings_ratio', 0),
            "pb_ratio": getattr(metrics, 'price_to_book_ratio', 0),
            "ps_ratio": getattr(metrics, 'price_to_sales_ratio', 0),
            "peg_ratio": getattr(metrics, 'peg_ratio', 0),
            "valuation_level": "合理"  # 简化实现
        }
    
    def calculate_fundamental_score(self, metrics) -> float:
        """计算基本面得分"""
        score = 50.0
        
        # ROE评分
        roe = getattr(metrics, 'return_on_equity', 0)
        if roe > 15:
            score += 15
        elif roe > 10:
            score += 10
        elif roe > 5:
            score += 5
        
        # PE评分
        pe = getattr(metrics, 'price_to_earnings_ratio', 0)
        if 10 <= pe <= 25:
            score += 10
        elif 5 <= pe <= 35:
            score += 5
        
        return min(100, max(0, score))
    
    def predict_short_term_trend(self, prices: List) -> str:
        """预测短期趋势"""
        if len(prices) < 10:
            return "数据不足"
        
        recent_prices = [p.close for p in prices[-10:]]
        trend = "上升" if recent_prices[-1] > recent_prices[0] else "下降"
        return f"短期{trend}趋势"
    
    def predict_medium_term_trend(self, prices: List) -> str:
        """预测中期趋势"""
        if len(prices) < 30:
            return "数据不足"
        
        recent_prices = [p.close for p in prices[-30:]]
        trend = "上升" if recent_prices[-1] > recent_prices[0] else "下降"
        return f"中期{trend}趋势"
    
    def predict_long_term_trend(self, prices: List) -> str:
        """预测长期趋势"""
        if len(prices) < 60:
            return "数据不足"
        
        recent_prices = [p.close for p in prices[-60:]]
        trend = "上升" if recent_prices[-1] > recent_prices[0] else "下降"
        return f"长期{trend}趋势"
    
    def calculate_price_targets(self, prices: List) -> Dict:
        """计算价格目标"""
        if not prices:
            return {"support": 0, "resistance": 0}
        
        current_price = prices[-1].close
        return {
            "support": current_price * 0.95,
            "resistance": current_price * 1.05,
            "target_price": current_price * 1.1
        }
    
    def detect_trend_reversal_signals(self, prices: List) -> List[str]:
        """检测趋势反转信号"""
        signals = []
        if len(prices) >= 20:
            # 简化的反转信号检测
            recent_high = max(p.high for p in prices[-10:])
            recent_low = min(p.low for p in prices[-10:])
            current_price = prices[-1].close
            
            if current_price < recent_low * 1.02:
                signals.append("可能触底反弹")
            elif current_price > recent_high * 0.98:
                signals.append("可能见顶回调")
        
        return signals
    
    def calculate_prediction_confidence(self, prices: List) -> float:
        """计算预测置信度"""
        if len(prices) < 20:
            return 30.0
        
        # 基于数据质量和趋势一致性计算置信度
        volatility = np.std([p.close for p in prices[-20:]]) / np.mean([p.close for p in prices[-20:]])
        confidence = max(30, min(90, 80 - volatility * 1000))
        return confidence
    
    def generate_prediction_summary(self, prices: List) -> str:
        """生成预测摘要"""
        short_term = self.predict_short_term_trend(prices)
        confidence = self.calculate_prediction_confidence(prices)
        return f"{short_term}，预测置信度{confidence:.0f}%"
    
    def assess_comprehensive_risk(self, analysis: Dict) -> Dict:
        """综合风险评估 - 使用增强的风险评估模块"""
        try:
            # 准备股票数据
            stock_data = {
                "price_data": analysis.get("price_analysis", {}).get("price_data"),
                "financial_data": analysis.get("fundamental_analysis", {}),
                "industry_data": analysis.get("industry_analysis", {}),
                "risk_indicators": {
                    "volatility": analysis.get("price_analysis", {}).get("volatility_20d", 0) / 100,
                    "max_drawdown": analysis.get("price_analysis", {}).get("max_drawdown", 0.1),
                    "var_95": analysis.get("price_analysis", {}).get("var_95", 0.03),
                    "debt_ratio": analysis.get("fundamental_analysis", {}).get("debt_ratio"),
                    "current_ratio": analysis.get("fundamental_analysis", {}).get("current_ratio")
                }
            }
            
            # 准备市场数据（如果有的话）
            market_data = analysis.get("market_data", {})
            
            # 调用新的风险评估模块
            risk_assessment = assess_stock_risk(stock_data, market_data)
            
            return risk_assessment
            
        except Exception as e:
            # 如果新模块失败，返回简化的风险评估
            return {
                "overall_risk_score": 50,
                "risk_level": "中等",
                "market_risk": {"risk_score": 50, "risk_description": "市场风险评估失败"},
                "stock_risk": {"risk_score": 50, "risk_description": "个股风险评估失败"},
                "industry_risk": {"risk_score": 50, "risk_description": "行业风险评估失败"},
                "financial_risk": {"risk_score": 50, "risk_description": "财务风险评估失败"},
                "risk_factors": [f"风险评估出错: {str(e)}"],
                "risk_mitigation": ["建议谨慎投资"],
                "confidence_level": 30.0
            }
    
    def calculate_comprehensive_score(self, analysis: Dict) -> Dict:
        """计算综合评分"""
        scores = {
            "technical": analysis.get("technical_analysis", {}).get("technical_score", 50) or 50,
            "fundamental": analysis.get("fundamental_analysis", {}).get("fundamental_score", 50) or 50,
            "sentiment": analysis.get("sentiment_analysis", {}).get("sentiment_score", 50) or 50,
            "industry": analysis.get("industry_analysis", {}).get("relative_strength", 50) or 50,
            "trend": analysis.get("trend_prediction", {}).get("confidence_level", 50) or 50
        }
        
        # 加权计算总分
        total_score = (
            scores["technical"] * self.analysis_weights["technical"] +
            scores["fundamental"] * self.analysis_weights["fundamental"] +
            scores["sentiment"] * self.analysis_weights["sentiment"] +
            scores["industry"] * self.analysis_weights["industry"] +
            scores["trend"] * 0.1
        )
        
        rating = "优秀" if total_score >= 80 else "良好" if total_score >= 60 else "一般" if total_score >= 40 else "较差"
        
        return {
            "total_score": total_score,
            "rating": rating,
            "component_scores": scores,
            "score_summary": f"综合评分: {total_score:.0f} ({rating})"
        }
    
    def generate_trading_strategy_description(self, signals: Dict, analysis: Dict) -> str:
        """生成交易策略描述"""
        signal = signals.get("overall_signal", "持有")
        strength = signals.get("signal_strength", 0)
        
        if signal in ["强烈买入", "买入"]:
            return f"建议{signal}，信号强度{strength:.0f}，适合{signals.get('time_horizon', '中期')}持有"
        elif signal in ["强烈卖出", "卖出"]:
            return f"建议{signal}，信号强度{strength:.0f}，注意风险控制"
        else:
            return f"建议{signal}，等待更明确的交易信号"
    
    def generate_market_overview_enhanced(self, individual_analysis: Dict) -> Dict:
        """生成增强版市场概览"""
        if not individual_analysis:
            return {"error": "无个股分析数据"}
        
        # 统计各项指标
        total_stocks = len(individual_analysis)
        buy_signals = sum(1 for analysis in individual_analysis.values() 
                         if analysis.get("trading_signals", {}).get("overall_signal", "") in ["买入", "强烈买入"])
        sell_signals = sum(1 for analysis in individual_analysis.values() 
                          if analysis.get("trading_signals", {}).get("overall_signal", "") in ["卖出", "强烈卖出"])
        
        avg_technical_score = np.mean([analysis.get("technical_analysis", {}).get("technical_score", 50) or 50
                                      for analysis in individual_analysis.values()])
        avg_sentiment_score = np.mean([analysis.get("sentiment_analysis", {}).get("sentiment_score", 50) or 50
                                      for analysis in individual_analysis.values()])
        
        market_sentiment = "乐观" if avg_sentiment_score >= 60 else "悲观" if avg_sentiment_score <= 40 else "中性"
        technical_trend = "强势" if avg_technical_score >= 60 else "弱势" if avg_technical_score <= 40 else "震荡"
        
        overview = {
            "total_analyzed": total_stocks,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": total_stocks - buy_signals - sell_signals,
            "market_sentiment": market_sentiment,
            "technical_trend": technical_trend,
            "avg_technical_score": avg_technical_score,
            "avg_sentiment_score": avg_sentiment_score,
            "market_summary": f"市场整体{market_sentiment}，技术面{technical_trend}"
        }
        
        return overview
    
    def generate_overall_summary(self, analysis_results: Dict) -> str:
        """生成总体分析摘要"""
        individual_analysis = analysis_results.get("individual_analysis", {})
        market_overview = analysis_results.get("market_overview", {})
        
        if not individual_analysis:
            return "分析数据不足，无法生成摘要"
        
        total_stocks = len(individual_analysis)
        buy_signals = market_overview.get("buy_signals", 0)
        market_sentiment = market_overview.get("market_sentiment", "中性")
        
        # 基础市场概况
        summary = f"本次分析了{total_stocks}只股票，其中{buy_signals}只显示买入信号。"
        summary += f"市场整体情绪{market_sentiment}。"
        
        # 分析各股票的迷你投资大师建议差异
        master_recommendations = {}
        confidence_levels = []
        risk_assessments = {}
        
        for ticker, analysis in individual_analysis.items():
            if 'error' in analysis:
                continue
                
            # 提取迷你投资大师建议
            technical_analysis = analysis.get('technical_analysis', {})
            master_indicators = technical_analysis.get('master_indicators', {})
            investment_advice = master_indicators.get('investment_advice', {})
            
            if investment_advice:
                recommendation = investment_advice.get('recommendation', '观望')
                confidence = investment_advice.get('confidence', 50)
                risk_level = investment_advice.get('risk_level', '中等')
                
                master_recommendations[ticker] = recommendation
                confidence_levels.append(confidence)
                risk_assessments[ticker] = risk_level
        
        # 分析师建议分布统计
        if master_recommendations:
            from collections import Counter
            rec_counts = Counter(master_recommendations.values())
            risk_counts = Counter(risk_assessments.values())
            avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 50
            
            summary += f"\n\n【迷你投资大师分析差异】\n"
            summary += f"• 建议分布: "
            for rec, count in rec_counts.most_common():
                summary += f"{rec}({count}只) "
            
            summary += f"\n• 平均置信度: {avg_confidence:.1f}%"
            summary += f"\n• 风险评估: "
            for risk, count in risk_counts.most_common():
                summary += f"{risk}风险({count}只) "
            
            # 分析师观点差异分析
            if len(set(master_recommendations.values())) > 1:
                summary += f"\n• 观点分歧: 各股票间存在明显分歧，体现了不同投资理念的差异化判断"
                
                # 详细差异分析
                bullish_stocks = [t for t, r in master_recommendations.items() if r in ['买入', '强烈买入', '谨慎买入']]
                bearish_stocks = [t for t, r in master_recommendations.items() if r in ['卖出', '强烈卖出', '谨慎卖出']]
                neutral_stocks = [t for t, r in master_recommendations.items() if r in ['观望', '持有']]
                
                if bullish_stocks:
                    summary += f"\n  - 看多标的({len(bullish_stocks)}只): 主要基于技术面向好、趋势确认等因素"
                if bearish_stocks:
                    summary += f"\n  - 看空标的({len(bearish_stocks)}只): 主要基于技术面走弱、风险增加等因素"
                if neutral_stocks:
                    summary += f"\n  - 中性标的({len(neutral_stocks)}只): 主要基于趋势不明、等待确认等因素"
            else:
                summary += f"\n• 观点一致: 各股票分析结果较为一致，反映当前市场趋势相对明确"
        
        # 市场机会评估
        if buy_signals > total_stocks * 0.6:
            summary += "\n\n【投资建议】多数股票显示积极信号，市场机会较多，可适当增加仓位。"
        elif buy_signals < total_stocks * 0.3:
            summary += "\n\n【投资建议】多数股票信号偏弱，建议谨慎操作，控制风险。"
        else:
            summary += "\n\n【投资建议】市场分化明显，需要精选个股，重点关注高置信度标的。"
        
        return summary


# 创建全局分析器实例
enhanced_analyzer = EnhancedSmartAnalyzer()


# 兼容性函数，保持与原有接口一致
def generate_smart_analysis_report(tickers: List[str], start_date: str, end_date: str, data_cache: Dict = None, prefetched_data: Dict = None) -> Dict[str, Any]:
    """
    生成智能分析报告（兼容性接口）
    """
    return enhanced_analyzer.generate_enhanced_analysis_report(tickers, start_date, end_date, data_cache, prefetched_data)