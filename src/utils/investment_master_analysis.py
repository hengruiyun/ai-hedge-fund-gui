# -*- coding: utf-8 -*-
"""
投资大师技术分析模块
实现专业级别的技术分析算法
作者: 267278466@qq.com
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import akshare as ak
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class InvestmentMasterAnalysis:
    """
    投资大师技术分析类
    实现巴菲特、彼得林奇等投资大师的分析思路
    """
    
    def __init__(self):
        self.analysis_methods = {
            'trend_analysis': '趋势分析',
            'momentum_analysis': '动量分析', 
            'support_resistance': '支撑阻力分析',
            'volume_analysis': '成交量分析',
            'price_action': '价格行为分析',
            'value_analysis': '价值分析',
            'growth_analysis': '成长分析',
            'contrarian_analysis': '逆向分析'
        }
        
        # 投资大师策略映射（不使用LLM的技术方法）
        self.master_strategies = {
            'buffett': {
                'name': '巴菲特价值投资',
                'focus': ['长期趋势', '价格稳定性', '低波动率'],
                'weight': 0.3
            },
            'lynch': {
                'name': '彼得林奇成长投资',
                'focus': ['价格动量', '成交量确认', '短期趋势'],
                'weight': 0.25
            },
            'graham': {
                'name': '格雷厄姆价值投资',
                'focus': ['安全边际', '价格低估', '风险控制'],
                'weight': 0.2
            },
            'druckenmiller': {
                'name': '德鲁肯米勒趋势投资',
                'focus': ['趋势强度', '动量确认', '风险回报比'],
                'weight': 0.15
            },
            'burry': {
                'name': '迈克尔·伯里逆向投资',
                'focus': ['超卖反弹', '价值回归', '市场情绪'],
                'weight': 0.1
            }
        }
    
    def get_enhanced_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取增强的股票数据，包含多个数据源
        """
        try:
            # 获取基础价格数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                  start_date=start_date.replace('-', ''), 
                                  end_date=end_date.replace('-', ''), 
                                  adjust="qfq")
            
            if df.empty:
                return pd.DataFrame()
            
            # 重命名列
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'change_pct', 'change_amount', 'turnover_rate']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_master_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算投资大师级别的技术指标
        """
        if df.empty or len(df) < 20:
            return {}
        
        indicators = {}
        
        try:
            # 基础价格指标
            indicators['current_price'] = float(df['close'].iloc[-1])
            indicators['prev_price'] = float(df['close'].iloc[-2]) if len(df) > 1 else indicators['current_price']
            indicators['price_change'] = indicators['current_price'] - indicators['prev_price']
            indicators['price_change_pct'] = (indicators['price_change'] / indicators['prev_price']) * 100
            
            # 移动平均线系统
            indicators['ma5'] = float(df['close'].rolling(5).mean().iloc[-1]) if len(df) >= 5 else None
            indicators['ma10'] = float(df['close'].rolling(10).mean().iloc[-1]) if len(df) >= 10 else None
            indicators['ma20'] = float(df['close'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else None
            indicators['ma60'] = float(df['close'].rolling(60).mean().iloc[-1]) if len(df) >= 60 else None
            
            # 趋势强度指标
            if indicators['ma5'] and indicators['ma20']:
                indicators['trend_strength'] = ((indicators['ma5'] - indicators['ma20']) / indicators['ma20']) * 100
            
            # 价格位置指标
            recent_high = float(df['high'].tail(20).max())
            recent_low = float(df['low'].tail(20).min())
            indicators['price_position'] = ((indicators['current_price'] - recent_low) / (recent_high - recent_low)) * 100
            
            # 成交量指标
            indicators['avg_volume'] = float(df['volume'].tail(20).mean())
            indicators['current_volume'] = float(df['volume'].iloc[-1])
            indicators['volume_ratio'] = indicators['current_volume'] / indicators['avg_volume']
            
            # 波动率指标
            returns = df['close'].pct_change().dropna()
            indicators['volatility'] = float(returns.tail(20).std() * np.sqrt(252) * 100)  # 年化波动率
            
            # RSI指标
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = float(100 - (100 / (1 + rs.iloc[-1])))
            
            return indicators
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return indicators
    
    def analyze_trend_pattern(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        趋势模式分析 - 巴菲特风格的长期趋势判断
        """
        analysis = {
            'trend_direction': '未知',
            'trend_strength': '弱',
            'trend_reliability': 0,
            'key_levels': {},
            'analysis_summary': ''
        }
        
        if not indicators or df.empty:
            return analysis
    
    def analyze_master_strategies(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        综合投资大师策略分析
        基于11位投资大师的核心理念，不使用LLM
        """
        master_scores = {}
        
        if not indicators or df.empty:
            return {'overall_score': 50, 'master_insights': [], 'strategy_breakdown': {}}
        
        try:
            current_price = indicators.get('current_price', 0)
            volatility = indicators.get('volatility', 0)
            rsi = indicators.get('rsi', 50)
            volume_ratio = indicators.get('volume_ratio', 1)
            price_change_pct = indicators.get('price_change_pct', 0)
            
            # 巴菲特策略评分（价值投资）
            buffett_score = 50
            if volatility < 20:  # 低波动率
                buffett_score += 15
            if abs(price_change_pct) < 2:  # 价格稳定
                buffett_score += 10
            if len(df) >= 60:  # 长期数据可用
                long_term_trend = df['close'].tail(60).mean() / df['close'].head(10).mean()
                if 1.05 < long_term_trend < 1.3:  # 稳健增长
                    buffett_score += 15
            master_scores['buffett'] = min(100, max(0, buffett_score))
            
            # 彼得林奇策略评分（成长投资）
            lynch_score = 50
            if price_change_pct > 1:  # 正向动量
                lynch_score += 20
            if volume_ratio > 1.2:  # 成交量确认
                lynch_score += 15
            if rsi > 50 and rsi < 70:  # 健康的上升趋势
                lynch_score += 10
            master_scores['lynch'] = min(100, max(0, lynch_score))
            
            # 格雷厄姆策略评分（深度价值）
            graham_score = 50
            if rsi < 40:  # 可能被低估
                graham_score += 20
            if volatility > 15:  # 市场恐慌中的机会
                graham_score += 10
            if price_change_pct < -2:  # 价格下跌创造价值机会
                graham_score += 15
            master_scores['graham'] = min(100, max(0, graham_score))
            
            # 德鲁肯米勒策略评分（趋势投资）
            druckenmiller_score = 50
            ma5 = indicators.get('ma5')
            ma20 = indicators.get('ma20')
            if ma5 and ma20:
                trend_strength = abs((ma5 - ma20) / ma20 * 100)
                if trend_strength > 2:  # 强趋势
                    druckenmiller_score += 20
                if ma5 > ma20 and price_change_pct > 0:  # 趋势一致性
                    druckenmiller_score += 15
            master_scores['druckenmiller'] = min(100, max(0, druckenmiller_score))
            
            # 迈克尔·伯里策略评分（逆向投资）
            burry_score = 50
            if rsi < 30:  # 严重超卖
                burry_score += 25
            if price_change_pct < -5:  # 大幅下跌
                burry_score += 20
            if volatility > 30:  # 高波动率中的机会
                burry_score += 10
            master_scores['burry'] = min(100, max(0, burry_score))
            
            # 计算加权综合得分
            overall_score = 0
            for strategy, score in master_scores.items():
                weight = self.master_strategies[strategy]['weight']
                overall_score += score * weight
            
            # 生成投资大师洞察
            master_insights = []
            best_strategy = max(master_scores.items(), key=lambda x: x[1])
            strategy_name = self.master_strategies[best_strategy[0]]['name']
            
            if best_strategy[1] > 70:
                master_insights.append(f"当前最适合{strategy_name}策略（得分：{best_strategy[1]:.0f}）")
            
            if overall_score > 70:
                master_insights.append("多位投资大师策略显示积极信号")
            elif overall_score < 40:
                master_insights.append("投资大师策略建议谨慎观望")
            else:
                master_insights.append("投资大师策略显示中性信号")
            
            # 添加具体策略建议
            if master_scores['buffett'] > 65:
                master_insights.append("巴菲特价值投资：适合长期持有")
            if master_scores['lynch'] > 65:
                master_insights.append("彼得林奇成长投资：关注成长潜力")
            if master_scores['graham'] > 65:
                master_insights.append("格雷厄姆价值投资：发现低估机会")
            if master_scores['druckenmiller'] > 65:
                master_insights.append("德鲁肯米勒趋势投资：跟随强势趋势")
            if master_scores['burry'] > 65:
                master_insights.append("迈克尔·伯里逆向投资：逆向思维机会")
            
            return {
                'overall_score': round(overall_score, 1),
                'master_insights': master_insights,
                'strategy_breakdown': master_scores,
                'best_strategy': strategy_name,
                'analysis_method': '多投资大师策略综合分析'
            }
            
        except Exception as e:
            print(f"投资大师策略分析失败: {e}")
            return {
                'overall_score': 50,
                'master_insights': ['分析数据不足，建议谨慎投资'],
                'strategy_breakdown': {},
                'analysis_method': '基础投资大师理论'
            }
        
        try:
            # 趋势方向判断
            ma5 = indicators.get('ma5')
            ma20 = indicators.get('ma20')
            ma60 = indicators.get('ma60')
            current_price = indicators.get('current_price')
            
            if ma5 and ma20 and ma60 and current_price:
                if current_price > ma5 > ma20 > ma60:
                    analysis['trend_direction'] = '强势上涨'
                    analysis['trend_strength'] = '强'
                    analysis['trend_reliability'] = 85
                elif current_price > ma5 > ma20:
                    analysis['trend_direction'] = '上涨'
                    analysis['trend_strength'] = '中等'
                    analysis['trend_reliability'] = 70
                elif current_price < ma5 < ma20 < ma60:
                    analysis['trend_direction'] = '强势下跌'
                    analysis['trend_strength'] = '强'
                    analysis['trend_reliability'] = 85
                elif current_price < ma5 < ma20:
                    analysis['trend_direction'] = '下跌'
                    analysis['trend_strength'] = '中等'
                    analysis['trend_reliability'] = 70
                else:
                    analysis['trend_direction'] = '震荡'
                    analysis['trend_strength'] = '弱'
                    analysis['trend_reliability'] = 50
            
            # 关键价位分析
            recent_data = df.tail(60) if len(df) >= 60 else df
            analysis['key_levels'] = {
                'resistance': float(recent_data['high'].max()),
                'support': float(recent_data['low'].min()),
                'pivot': float((recent_data['high'].max() + recent_data['low'].min() + current_price) / 3)
            }
            
            # 生成分析摘要
            price_pos = indicators.get('price_position', 50)
            if price_pos > 80:
                position_desc = "接近阻力位"
            elif price_pos < 20:
                position_desc = "接近支撑位"
            else:
                position_desc = "中性位置"
            
            analysis['analysis_summary'] = f"当前趋势{analysis['trend_direction']}，强度{analysis['trend_strength']}，价格处于{position_desc}。"
            
        except Exception as e:
            print(f"趋势分析失败: {e}")
        
        return analysis
    
    def analyze_momentum_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        动量信号分析 - 彼得林奇风格的成长股分析
        """
        analysis = {
            'momentum_score': 0,
            'momentum_direction': '中性',
            'volume_confirmation': False,
            'rsi_signal': '中性',
            'price_momentum': 0,
            'analysis_summary': ''
        }
        
        if not indicators or df.empty:
            return analysis
        
        try:
            # RSI动量分析
            rsi = indicators.get('rsi', 50)
            if rsi > 70:
                analysis['rsi_signal'] = '超买'
                rsi_score = -20
            elif rsi < 30:
                analysis['rsi_signal'] = '超卖'
                rsi_score = 20
            elif 45 <= rsi <= 55:
                analysis['rsi_signal'] = '中性'
                rsi_score = 0
            elif rsi > 55:
                analysis['rsi_signal'] = '偏强'
                rsi_score = 10
            else:
                analysis['rsi_signal'] = '偏弱'
                rsi_score = -10
            
            # 价格动量分析
            price_change_pct = indicators.get('price_change_pct', 0)
            if abs(price_change_pct) > 5:
                momentum_score = min(30, abs(price_change_pct) * 3) * (1 if price_change_pct > 0 else -1)
            else:
                momentum_score = price_change_pct * 2
            
            analysis['price_momentum'] = price_change_pct
            
            # 成交量确认
            volume_ratio = indicators.get('volume_ratio', 1)
            analysis['volume_confirmation'] = volume_ratio > 1.5
            volume_score = min(20, (volume_ratio - 1) * 20) if volume_ratio > 1 else 0
            
            # 综合动量评分
            analysis['momentum_score'] = rsi_score + momentum_score + volume_score
            
            if analysis['momentum_score'] > 30:
                analysis['momentum_direction'] = '强势看涨'
            elif analysis['momentum_score'] > 10:
                analysis['momentum_direction'] = '看涨'
            elif analysis['momentum_score'] < -30:
                analysis['momentum_direction'] = '强势看跌'
            elif analysis['momentum_score'] < -10:
                analysis['momentum_direction'] = '看跌'
            else:
                analysis['momentum_direction'] = '中性'
            
            # 生成分析摘要
            volume_desc = "有成交量支撑" if analysis['volume_confirmation'] else "成交量偏弱"
            analysis['analysis_summary'] = f"动量{analysis['momentum_direction']}，RSI显示{analysis['rsi_signal']}，{volume_desc}。"
            
        except Exception as e:
            print(f"动量分析失败: {e}")
        
        return analysis
    
    def generate_investment_advice(self, trend_analysis: Dict, momentum_analysis: Dict, indicators: Dict) -> Dict:
        """
        生成投资建议 - 综合大师级分析
        """
        advice = {
            'recommendation': '观望',
            'confidence': 0,
            'risk_level': '中等',
            'entry_points': [],
            'stop_loss': None,
            'target_price': None,
            'reasoning': '',
            'master_insights': []
        }
        
        try:
            # 综合评分计算
            trend_score = trend_analysis.get('trend_reliability', 0)
            momentum_score = momentum_analysis.get('momentum_score', 0)
            
            # 趋势权重60%，动量权重40%
            if trend_analysis.get('trend_direction') in ['强势上涨', '上涨']:
                trend_weight = 1
            elif trend_analysis.get('trend_direction') in ['强势下跌', '下跌']:
                trend_weight = -1
            else:
                trend_weight = 0
            
            momentum_weight = 1 if momentum_score > 0 else -1 if momentum_score < 0 else 0
            
            total_score = (trend_score * trend_weight * 0.6) + (abs(momentum_score) * momentum_weight * 0.4)
            
            # 生成建议
            current_price = indicators.get('current_price', 0)
            support = trend_analysis.get('key_levels', {}).get('support', current_price * 0.95)
            resistance = trend_analysis.get('key_levels', {}).get('resistance', current_price * 1.05)
            
            if total_score > 40:
                advice['recommendation'] = '买入'
                advice['confidence'] = min(90, 50 + total_score * 0.5)
                advice['target_price'] = resistance * 1.1
                advice['stop_loss'] = support * 0.95
            elif total_score > 20:
                advice['recommendation'] = '谨慎买入'
                advice['confidence'] = min(75, 50 + total_score * 0.5)
                advice['target_price'] = resistance
                advice['stop_loss'] = support
            elif total_score < -40:
                advice['recommendation'] = '卖出'
                advice['confidence'] = min(90, 50 + abs(total_score) * 0.5)
                advice['stop_loss'] = resistance * 1.05
            elif total_score < -20:
                advice['recommendation'] = '谨慎卖出'
                advice['confidence'] = min(75, 50 + abs(total_score) * 0.5)
                advice['stop_loss'] = resistance
            else:
                advice['recommendation'] = '观望'
                advice['confidence'] = 50
            
            # 风险评估
            volatility = indicators.get('volatility', 20)
            if volatility > 40:
                advice['risk_level'] = '高'
            elif volatility < 15:
                advice['risk_level'] = '低'
            else:
                advice['risk_level'] = '中等'
            
            # 大师洞察
            advice['master_insights'] = [
                f"巴菲特观点: {trend_analysis.get('analysis_summary', '趋势分析不可用')}",
                f"彼得林奇观点: {momentum_analysis.get('analysis_summary', '动量分析不可用')}",
                f"风险提示: 当前波动率{volatility:.1f}%，属于{advice['risk_level']}风险水平"
            ]
            
            # 推理说明
            advice['reasoning'] = f"基于趋势分析({trend_analysis.get('trend_direction', '未知')})和动量分析({momentum_analysis.get('momentum_direction', '中性')})，综合评分{total_score:.1f}分。"
            
        except Exception as e:
            print(f"生成投资建议失败: {e}")
        
        return advice
    
    def generate_master_analysis_report(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        生成投资大师级技术分析报告
        """
        report = {
            'status': 'success',
            'symbol': symbol,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': f"{start_date} 至 {end_date}",
            'indicators': {},
            'trend_analysis': {},
            'momentum_analysis': {},
            'investment_advice': {},
            'summary': '',
            'disclaimer': '本分析仅供参考，投资有风险，决策需谨慎。'
        }
        
        try:
            # 获取数据
            df = self.get_enhanced_stock_data(symbol, start_date, end_date)
            if df.empty:
                # 当数据获取失败时，提供备用分析方案
                return self._generate_fallback_master_analysis(symbol, start_date, end_date, report)
            
            # 计算指标
            report['indicators'] = self.calculate_master_indicators(df)
            
            # 趋势分析
            report['trend_analysis'] = self.analyze_trend_pattern(df, report['indicators'])
            
            # 动量分析
            report['momentum_analysis'] = self.analyze_momentum_signals(df, report['indicators'])
            
            # 投资建议
            report['investment_advice'] = self.generate_investment_advice(
                report['trend_analysis'], 
                report['momentum_analysis'], 
                report['indicators']
            )
            
            # 生成总结
            current_price = report['indicators'].get('current_price', 0)
            recommendation = report['investment_advice'].get('recommendation', '观望')
            confidence = report['investment_advice'].get('confidence', 0)
            
            report['summary'] = f"股票{symbol}当前价格{current_price:.2f}元，投资建议：{recommendation}（置信度{confidence:.0f}%）。" + \
                              f"趋势分析显示{report['trend_analysis'].get('trend_direction', '未知')}，" + \
                              f"动量分析显示{report['momentum_analysis'].get('momentum_direction', '中性')}。"
            
        except Exception as e:
            report['status'] = 'error'
            report['error'] = f'分析过程出错: {str(e)}'
        
        return report
    
    def _generate_fallback_master_analysis(self, symbol: str, start_date: str, end_date: str, report: Dict) -> Dict:
        """
        当数据获取失败时的备用投资大师分析
        """
        try:
            # 尝试使用现有的API获取基础数据
            from src.tools.api import get_prices
            prices_data = get_prices(symbol, start_date, end_date)
            
            if prices_data and len(prices_data) > 0:
                # 使用获取到的基础数据进行简化分析
                current_price = prices_data[-1].close
                prev_price = prices_data[-2].close if len(prices_data) > 1 else current_price
                price_change = current_price - prev_price
                price_change_pct = (price_change / prev_price * 100) if prev_price > 0 else 0
                
                # 计算简化的移动平均线
                recent_prices = [p.close for p in prices_data[-20:] if p.close > 0]
                ma5 = sum(recent_prices[-5:]) / 5 if len(recent_prices) >= 5 else current_price
                ma20 = sum(recent_prices) / len(recent_prices) if recent_prices else current_price
                
                # 计算波动率
                if len(recent_prices) > 1:
                    returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] for i in range(1, len(recent_prices))]
                    volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 10.0
                else:
                    volatility = 10.0
                
                # 填充报告数据
                report['status'] = 'success'
                report['indicators'] = {
                    'current_price': current_price,
                    'prev_price': prev_price,
                    'price_change': price_change,
                    'price_change_pct': price_change_pct,
                    'ma5': ma5,
                    'ma20': ma20,
                    'volatility': volatility,
                    'data_source': 'fallback_api'
                }
                
                # 简化的趋势分析
                trend_direction = "上升" if ma5 > ma20 else "下降" if ma5 < ma20 else "横盘"
                trend_strength = abs((ma5 - ma20) / ma20 * 100) if ma20 > 0 else 0
                
                report['trend_analysis'] = {
                    'trend_direction': trend_direction,
                    'trend_strength': trend_strength,
                    'analysis_method': '巴菲特趋势分析（简化版）',
                    'key_insights': [
                        f"短期均线（MA5: {ma5:.2f}）{'高于' if ma5 > ma20 else '低于'}长期均线（MA20: {ma20:.2f}）",
                        f"趋势强度为{trend_strength:.1f}%，属于{'强势' if trend_strength > 2 else '温和' if trend_strength > 0.5 else '弱势'}趋势"
                    ]
                }
                
                # 简化的动量分析
                momentum_direction = "正向" if price_change_pct > 0 else "负向" if price_change_pct < 0 else "中性"
                momentum_strength = abs(price_change_pct)
                
                report['momentum_analysis'] = {
                    'momentum_direction': momentum_direction,
                    'momentum_strength': momentum_strength,
                    'analysis_method': '彼得林奇动量分析（简化版）',
                    'key_insights': [
                        f"价格变化{price_change_pct:+.2f}%，显示{momentum_direction}动量",
                        f"波动率{volatility:.1f}%，风险水平{'较高' if volatility > 30 else '中等' if volatility > 15 else '较低'}"
                    ]
                }
                
                # 添加投资大师策略分析
                df_simple = pd.DataFrame({
                    'close': [p.close for p in prices_data],
                    'volume': [getattr(p, 'volume', 0) for p in prices_data]
                })
                
                master_analysis = self.analyze_master_strategies(df_simple, report['indicators'])
                report['master_strategies'] = master_analysis
                
                # 生成投资建议（整合投资大师策略）
                master_score = master_analysis.get('overall_score', 50)
                base_confidence = min(85, max(50, 70 - abs(price_change_pct) * 2))
                
                # 根据投资大师综合得分调整建议
                if master_score > 70:
                    if trend_direction == "上升" and momentum_direction == "正向":
                        recommendation = "买入"
                        confidence = min(90, base_confidence + 15)
                    else:
                        recommendation = "买入"
                        confidence = min(85, base_confidence + 10)
                    risk_level = "中等"
                elif master_score < 40:
                    if trend_direction == "下降" and momentum_direction == "负向":
                        recommendation = "卖出"
                        confidence = min(85, base_confidence + 10)
                    else:
                        recommendation = "观望"
                        confidence = max(40, base_confidence - 10)
                    risk_level = "较高"
                else:
                    if trend_direction == "上升" and momentum_direction == "正向":
                        recommendation = "买入"
                        confidence = base_confidence
                    elif trend_direction == "下降" and momentum_direction == "负向":
                        recommendation = "卖出"
                        confidence = base_confidence
                    else:
                        recommendation = "观望"
                        confidence = max(50, base_confidence - 5)
                    risk_level = "中等"
                
                # 整合投资大师洞察
                master_insights = master_analysis.get('master_insights', [])
                best_strategy = master_analysis.get('best_strategy', '综合策略')
                
                report['investment_advice'] = {
                    'recommendation': recommendation,
                    'confidence': confidence,
                    'risk_level': risk_level,
                    'reasoning': f"基于{best_strategy}等多位投资大师策略，{trend_direction}趋势配合{momentum_direction}动量，综合得分{master_score:.1f}",
                    'master_insights': master_insights if master_insights else [
                        "巴菲特价值投资视角：关注长期趋势的可持续性",
                        "彼得林奇成长投资理念：重视价格动量和市场情绪",
                        "风险管理：建议分批建仓，控制单次投资比例"
                    ],
                    'strategy_scores': master_analysis.get('strategy_breakdown', {})
                }
                
                # 生成总结
                top_insights = master_insights[:2] if len(master_insights) >= 2 else master_insights
                insights_text = "，".join(top_insights) if top_insights else "多位投资大师策略综合分析"
                
                report['summary'] = f"迷你投资大师分析：股票{symbol}当前价格{current_price:.2f}元，" + \
                                  f"投资建议：{recommendation}（置信度{confidence:.0f}%）。" + \
                                  f"趋势分析显示{trend_direction}，动量分析显示{momentum_direction}。" + \
                                  f"{insights_text}。综合评分{master_score:.1f}/100。"
                
            else:
                # 完全无法获取数据时的最基础分析
                report['status'] = 'limited'
                report['error'] = '数据获取受限，提供基础分析框架'
                report['indicators'] = {'data_source': 'unavailable'}
                report['trend_analysis'] = {
                    'analysis_method': '投资大师理论框架',
                    'key_insights': [
                        "巴菲特投资原则：寻找被低估的优质企业",
                        "彼得林奇策略：关注成长性和市场机会"
                    ]
                }
                report['momentum_analysis'] = {
                    'analysis_method': '技术分析基础理论',
                    'key_insights': [
                        "价格趋势是投资决策的重要参考",
                        "成交量确认价格走势的有效性"
                    ]
                }
                report['investment_advice'] = {
                    'recommendation': '观望',
                    'confidence': 30,
                    'risk_level': '未知',
                    'reasoning': '数据不足，建议等待更多信息',
                    'master_insights': [
                        "投资前务必进行充分的基本面分析",
                        "技术分析需要配合基本面分析使用",
                        "风险控制是投资成功的关键"
                    ]
                }
                report['summary'] = f"迷你投资大师框架：针对{symbol}采用价值投资和成长投资相结合的策略，" + \
                                  "重点关注企业基本面和长期发展前景，遵循投资大师的核心理念。"
                
        except Exception as e:
            report['status'] = 'error'
            report['error'] = f'备用分析失败: {str(e)}'
            
        return report

# 使用示例
if __name__ == "__main__":
    analyzer = InvestmentMasterAnalysis()
    result = analyzer.generate_master_analysis_report("000776", "2024-01-01", "2024-01-31")
    print(result)
    analyzer = InvestmentMasterAnalysis()
    result = analyzer.generate_master_analysis_report("000776", "2024-01-01", "2024-01-31")
    print(result)