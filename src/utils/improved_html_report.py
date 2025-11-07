#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版HTML报告生成器
解决原版本中的数据质量、语言一致性和用户体验问题
"""

from datetime import datetime
import json
from typing import Dict, List, Any, Optional
import re


class ImprovedHTMLReportGenerator:
    """改进版HTML报告生成器"""
    
    def __init__(self):
        self.data_validator = DataValidator()
        self.content_localizer = ContentLocalizer()
        self.quality_controller = QualityController()
    
    def generate_report(self, result: Dict[str, Any]) -> str:
        """生成改进版HTML报告"""
        if not result:
            return self._generate_error_html("没有可用的分析结果")
        
        # 数据验证和清理
        validated_result = self.data_validator.validate_and_clean(result)
        
        # 内容本地化
        localized_result = self.content_localizer.localize_content(validated_result)
        
        # 质量控制
        quality_result = self.quality_controller.assess_quality(localized_result)
        
        # 生成HTML
        return self._render_html(quality_result)
    
    def _render_html(self, result: Dict[str, Any]) -> str:
        """渲染HTML内容"""
        decisions = result.get("decisions", {})
        analyst_signals = result.get("analyst_signals", {})
        quality_info = result.get("quality_info", {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI基金大师投资分析报告</title>
    <style>{self._get_improved_css()}</style>
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_quality_assessment(quality_info)}
        {self._generate_executive_summary(decisions, analyst_signals)}
        {self._generate_investment_recommendations(decisions)}
        {self._generate_key_metrics(decisions, analyst_signals)}
        {self._generate_risk_analysis(analyst_signals)}
        {self._generate_analyst_insights(analyst_signals)}
        {self._generate_footer()}
    </div>
    <script>{self._get_improved_javascript()}</script>
</body>
</html>
"""
        return html_content
    
    def _generate_header(self) -> str:
        """生成报告头部"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        return f"""
        <div class="header">
            <h1>AI基金大师投资分析报告</h1>
            <div class="subtitle">智能投资决策 · 多维度分析 · 风险控制</div>
            <div class="timestamp">生成时间: {current_time}</div>
        </div>
        """
    
    def _generate_quality_assessment(self, quality_info: Dict[str, Any]) -> str:
        """生成数据质量评估"""
        if not quality_info:
            return ""
        
        data_completeness = quality_info.get("data_completeness", 0)
        analysis_quality = quality_info.get("analysis_quality", 0)
        confidence_level = quality_info.get("confidence_level", 0)
        
        quality_class = "high" if data_completeness > 80 else "medium" if data_completeness > 50 else "low"
        
        return f"""
        <div class="section">
            <h2>数据质量评估</h2>
            <div class="quality-assessment {quality_class}">
                <div class="quality-metrics">
                    <div class="quality-metric">
                        <div class="metric-label">数据完整度</div>
                        <div class="metric-value">{data_completeness:.1f}%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {data_completeness}%"></div>
                        </div>
                    </div>
                    <div class="quality-metric">
                        <div class="metric-label">分析质量</div>
                        <div class="metric-value">{analysis_quality:.1f}%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {analysis_quality}%"></div>
                        </div>
                    </div>
                    <div class="quality-metric">
                        <div class="metric-label">整体信心度</div>
                        <div class="metric-value">{confidence_level:.1f}%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {confidence_level}%"></div>
                        </div>
                    </div>
                </div>
                {self._generate_quality_alerts(quality_info)}
            </div>
        </div>
        """
    
    def _generate_quality_alerts(self, quality_info: Dict[str, Any]) -> str:
        """生成质量警告"""
        alerts = quality_info.get("alerts", [])
        if not alerts:
            return ""
        
        alert_html = '<div class="quality-alerts">'
        for alert in alerts:
            alert_type = alert.get("type", "warning")
            message = alert.get("message", "")
            alert_html += f'<div class="alert {alert_type}">{message}</div>'
        alert_html += '</div>'
        
        return alert_html
    
    def _generate_executive_summary(self, decisions: Dict[str, Any], analyst_signals: Dict[str, Any]) -> str:
        """生成执行摘要"""
        # 统计分析师观点
        signal_stats = self._calculate_signal_statistics(analyst_signals)
        
        # 计算平均信心度
        avg_confidence = self._calculate_average_confidence(analyst_signals)
        
        # 获取主要股票
        tickers = list(decisions.keys()) if decisions else []
        ticker_count = len(tickers)
        
        return f"""
        <div class="section">
            <h2>执行摘要</h2>
            <div class="executive-summary">
                <div class="summary-text">
                    <p>本次分析覆盖 <strong>{ticker_count}</strong> 只股票，基于多位AI投资专家的综合评估.</p>
                    <p>整体市场观点偏向 <strong>{signal_stats['dominant_signal']}</strong>，平均信心度为 <strong>{avg_confidence:.1f}%</strong>.</p>
                </div>
                
                <div class="summary-stats">
                    <div class="stat-card bullish">
                        <div class="stat-number">{signal_stats['bullish']}</div>
                        <div class="stat-label">看涨信号</div>
                    </div>
                    <div class="stat-card bearish">
                        <div class="stat-number">{signal_stats['bearish']}</div>
                        <div class="stat-label">看跌信号</div>
                    </div>
                    <div class="stat-card neutral">
                        <div class="stat-number">{signal_stats['neutral']}</div>
                        <div class="stat-label">中性信号</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_confidence:.1f}%</div>
                        <div class="stat-label">平均信心度</div>
                    </div>
                </div>
            </div>
            
            <div class="disclaimer">
                <strong>风险提示:</strong> 本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议.投资有风险，决策需谨慎.请根据自身情况做出投资决定.
            </div>
        </div>
        """
    
    def _generate_investment_recommendations(self, decisions: Dict[str, Any]) -> str:
        """生成投资建议"""
        if not decisions:
            return ""
        
        recommendations_html = """
        <div class="section">
            <h2>投资建议</h2>
            <div class="recommendations-grid">
        """
        
        for ticker, decision in decisions.items():
            action = decision.get("action", "hold").lower()
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning", "暂无详细分析")
            
            # 本地化动作描述
            action_map = {
                "buy": "买入",
                "sell": "卖出",
                "hold": "持有",
                "short": "做空",
                "cover": "平仓"
            }
            action_text = action_map.get(action, action)
            
            # 生成具体建议
            specific_advice = self._generate_specific_advice(ticker, decision)
            
            recommendations_html += f"""
            <div class="recommendation-card {action}">
                <div class="recommendation-header">
                    <h3>{ticker}</h3>
                    <div class="action-badge {action}">{action_text}</div>
                </div>
                <div class="recommendation-body">
                    <div class="confidence-section">
                        <div class="confidence-label">信心度: {confidence:.1f}%</div>
                        <div class="confidence-bar">
                            <div class="confidence-fill {action}" style="width: {confidence}%"></div>
                        </div>
                    </div>
                    {specific_advice}
                    <div class="reasoning-section">
                        <h4>分析理由</h4>
                        <p>{reasoning}</p>
                    </div>
                </div>
            </div>
            """
        
        recommendations_html += """
            </div>
        </div>
        """
        
        return recommendations_html
    
    def _generate_specific_advice(self, ticker: str, decision: Dict[str, Any]) -> str:
        """生成具体投资建议"""
        action = decision.get("action", "hold").lower()
        confidence = decision.get("confidence", 0)
        
        if action == "buy":
            return f"""
            <div class="specific-advice buy">
                <div class="advice-item">
                    <span class="advice-label">建议买入价格:</span>
                    <span class="advice-value">当前价格下方3-5%</span>
                </div>
                <div class="advice-item">
                    <span class="advice-label">目标收益:</span>
                    <span class="advice-value">15-25%</span>
                </div>
                <div class="advice-item">
                    <span class="advice-label">止损位:</span>
                    <span class="advice-value">买入价下方8-10%</span>
                </div>
            </div>
            """
        elif action == "sell":
            return f"""
            <div class="specific-advice sell">
                <div class="advice-item">
                    <span class="advice-label">建议卖出:</span>
                    <span class="advice-value">分批减仓</span>
                </div>
                <div class="advice-item">
                    <span class="advice-label">卖出比例:</span>
                    <span class="advice-value">50-80%</span>
                </div>
            </div>
            """
        else:  # hold
            return f"""
            <div class="specific-advice hold">
                <div class="advice-item">
                    <span class="advice-label">持有策略:</span>
                    <span class="advice-value">继续观察</span>
                </div>
                <div class="advice-item">
                    <span class="advice-label">关注点:</span>
                    <span class="advice-value">基本面变化</span>
                </div>
            </div>
            """
    
    def _generate_key_metrics(self, decisions: Dict[str, Any], analyst_signals: Dict[str, Any]) -> str:
        """生成关键指标"""
        return """
        <div class="section">
            <h2>关键指标</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>市场情绪</h4>
                    <div class="sentiment-indicator positive">偏乐观</div>
                </div>
                <div class="metric-card">
                    <h4>风险等级</h4>
                    <div class="risk-indicator medium">中等</div>
                </div>
                <div class="metric-card">
                    <h4>投资时机</h4>
                    <div class="timing-indicator neutral">观望</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_risk_analysis(self, analyst_signals: Dict[str, Any]) -> str:
        """生成风险分析"""
        return """
        <div class="section">
            <h2>风险分析</h2>
            <div class="risk-analysis">
                <div class="risk-category">
                    <h4>市场风险</h4>
                    <div class="risk-level medium">中等</div>
                    <p>当前市场波动性适中，需关注宏观经济变化.</p>
                </div>
                <div class="risk-category">
                    <h4>个股风险</h4>
                    <div class="risk-level low">较低</div>
                    <p>所选股票基本面相对稳健，但需注意估值水平.</p>
                </div>
                <div class="risk-category">
                    <h4>流动性风险</h4>
                    <div class="risk-level low">较低</div>
                    <p>主要标的流动性良好，交易活跃.</p>
                </div>
            </div>
        </div>
        """
    
    def _generate_analyst_insights(self, analyst_signals: Dict[str, Any]) -> str:
        """生成分析师洞察（精选高质量分析）"""
        if not analyst_signals:
            return ""
        
        # 筛选高质量分析
        high_quality_analyses = self._filter_high_quality_analyses(analyst_signals)
        
        insights_html = """
        <div class="section">
            <h2>专家洞察</h2>
            <div class="insights-grid">
        """
        
        for analyst_name, signals in high_quality_analyses.items():
            insights_html += self._generate_analyst_card(analyst_name, signals)
        
        insights_html += """
            </div>
        </div>
        """
        
        return insights_html
    
    def _filter_high_quality_analyses(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """筛选高质量分析"""
        high_quality = {}
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    reasoning = signal.get("reasoning", "")
                    
                    # 降低过滤门槛，确保技术面分析师不被过滤
                    # 技术面分析师特殊处理：只要有信号就显示
                    if analyst_name == "technical_analyst" or analyst_name == "技术面分析师":
                        if analyst_name not in high_quality:
                            high_quality[analyst_name] = {}
                        high_quality[analyst_name][ticker] = signal
                    # 其他分析师：信心度>20%且有基本分析内容
                    elif confidence > 20 and len(str(reasoning)) > 20 and "无详细分析" not in str(reasoning):
                        if analyst_name not in high_quality:
                            high_quality[analyst_name] = {}
                        high_quality[analyst_name][ticker] = signal
        
        return high_quality
    
    def _generate_analyst_card(self, analyst_name: str, signals: Dict[str, Any]) -> str:
        """生成分析师卡片"""
        # 本地化分析师名称
        localized_name = self.content_localizer.localize_analyst_name(analyst_name)
        
        card_html = f"""
        <div class="analyst-card">
            <div class="analyst-header">
                <h4>{localized_name}</h4>
            </div>
            <div class="analyst-signals">
        """
        
        for ticker, signal in signals.items():
            signal_type = signal.get("signal", "neutral")
            confidence = signal.get("confidence", 0)
            
            # 对于技术分析师，优先使用detailed_reasoning（支持本地化后的名称）
            if (analyst_name == "technical_analyst" or analyst_name == "技术面分析师") and "detailed_reasoning" in signal:
                reasoning = signal.get("detailed_reasoning", "")
            else:
                reasoning = signal.get("reasoning", "")
            
            # 截取推理内容
            short_reasoning = reasoning[:150] + "..." if len(reasoning) > 150 else reasoning
            
            card_html += f"""
            <div class="signal-item">
                <div class="signal-header">
                    <span class="ticker">{ticker}</span>
                    <span class="signal-badge {signal_type}">{self._get_signal_text(signal_type)}</span>
                    <span class="confidence">{confidence:.1f}%</span>
                </div>
                <div class="signal-reasoning">{short_reasoning}</div>
            </div>
            """
        
        card_html += """
            </div>
        </div>
        """
        
        return card_html
    
    def _get_signal_text(self, signal: str) -> str:
        """获取信号文本"""
        signal_map = {
            "bullish": "看涨",
            "bearish": "看跌",
            "neutral": "中性"
        }
        return signal_map.get(signal.lower(), signal)
    
    def _generate_footer(self) -> str:
        """生成页脚"""
        return """
        <div class="footer">
            <p>AI基金大师 | 智能投资，理性决策</p>
            <p style="margin-top: 10px; font-size: 0.8em; opacity: 0.8;">
                本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议.投资决策请结合专业建议和个人情况.
            </p>
        </div>
        """
    
    def _calculate_signal_statistics(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """计算信号统计"""
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    signal_type = signal.get("signal", "neutral").lower()
                    if signal_type == "bullish":
                        bullish_count += 1
                    elif signal_type == "bearish":
                        bearish_count += 1
                    else:
                        neutral_count += 1
        
        # 确定主导信号
        if bullish_count > bearish_count and bullish_count > neutral_count:
            dominant_signal = "看涨"
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            dominant_signal = "看跌"
        else:
            dominant_signal = "中性"
        
        return {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count,
            "dominant_signal": dominant_signal
        }
    
    def _calculate_average_confidence(self, analyst_signals: Dict[str, Any]) -> float:
        """计算平均信心度"""
        total_confidence = 0
        count = 0
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    total_confidence += confidence
                    count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _get_improved_css(self) -> str:
        """获取改进版CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .section {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        
        .section h2 {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }
        
        .quality-assessment {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .quality-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .quality-metric {
            text-align: center;
        }
        
        .metric-bar {
            background: #ecf0f1;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .metric-fill {
            height: 100%;
            background: #3498db;
            border-radius: 4px;
            transition: width 0.8s ease;
        }
        
        .recommendations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .recommendation-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        
        .recommendation-header {
            padding: 20px;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .action-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            color: white;
        }
        
        .action-badge.buy { background: #27ae60; }
        .action-badge.sell { background: #e74c3c; }
        .action-badge.hold { background: #f39c12; }
        
        .specific-advice {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .advice-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .analyst-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }
        
        .signal-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .signal-badge.bullish { background: #d5f4e6; color: #27ae60; }
        .signal-badge.bearish { background: #fdeaea; color: #e74c3c; }
        .signal-badge.neutral { background: #fef9e7; color: #f39c12; }
        
        .disclaimer {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        """
    
    def _get_improved_javascript(self) -> str:
        """获取改进版JavaScript"""
        return """
        // 页面加载动画
        document.addEventListener('DOMContentLoaded', function() {
            // 渐进式加载动画
            const sections = document.querySelectorAll('.section');
            sections.forEach((section, index) => {
                section.style.opacity = '0';
                section.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    section.style.transition = 'all 0.6s ease';
                    section.style.opacity = '1';
                    section.style.transform = 'translateY(0)';
                }, index * 200);
            });
            
            // 进度条动画
            const fills = document.querySelectorAll('.metric-fill, .confidence-fill');
            fills.forEach(fill => {
                const width = fill.style.width;
                fill.style.width = '0%';
                setTimeout(() => {
                    fill.style.width = width;
                }, 1000);
            });
        });
        
        // 交互功能
        function toggleDetails(element) {
            const details = element.nextElementSibling;
            if (details.style.display === 'none') {
                details.style.display = 'block';
            } else {
                details.style.display = 'none';
            }
        }
        """
    
    def _generate_error_html(self, error_message: str) -> str:
        """生成错误页面"""
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>报告生成错误</title>
            <style>
                body {{ font-family: 'Microsoft YaHei', sans-serif; padding: 50px; text-align: center; }}
                .error {{ color: #e74c3c; font-size: 1.2em; }}
            </style>
        </head>
        <body>
            <h1>报告生成失败</h1>
            <div class="error">{error_message}</div>
        </body>
        </html>
        """


class DataValidator:
    """数据验证器"""
    
    def validate_and_clean(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理数据"""
        cleaned_result = result.copy()
        
        # 验证决策数据
        if "decisions" in cleaned_result:
            cleaned_result["decisions"] = self._clean_decisions(cleaned_result["decisions"])
        
        # 验证分析师信号
        if "analyst_signals" in cleaned_result:
            cleaned_result["analyst_signals"] = self._clean_analyst_signals(cleaned_result["analyst_signals"])
        
        return cleaned_result
    
    def _clean_decisions(self, decisions: Dict[str, Any]) -> Dict[str, Any]:
        """清理决策数据"""
        cleaned = {}
        for ticker, decision in decisions.items():
            if isinstance(decision, dict):
                cleaned_decision = {
                    "action": decision.get("action", "hold"),
                    "confidence": max(0, min(100, decision.get("confidence", 0))),
                    "reasoning": decision.get("reasoning", "暂无详细分析")
                }
                cleaned[ticker] = cleaned_decision
        return cleaned
    
    def _clean_analyst_signals(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """清理分析师信号"""
        cleaned = {}
        for analyst, signals in analyst_signals.items():
            if isinstance(signals, dict):
                cleaned_signals = {}
                for ticker, signal in signals.items():
                    if isinstance(signal, dict):
                        cleaned_signal = {
                            "signal": signal.get("signal", "neutral"),
                            "confidence": max(0, min(100, signal.get("confidence", 0))),
                            "reasoning": signal.get("reasoning", "暂无详细分析")
                        }
                        # 保留detailed_reasoning字段（如果存在）
                        if "detailed_reasoning" in signal:
                            cleaned_signal["detailed_reasoning"] = signal["detailed_reasoning"]
                        cleaned_signals[ticker] = cleaned_signal
                cleaned[analyst] = cleaned_signals
        return cleaned


class ContentLocalizer:
    """内容本地化器"""
    
    def localize_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """本地化内容"""
        localized_result = result.copy()
        
        # 本地化分析师信号中的英文内容
        if "analyst_signals" in localized_result:
            localized_result["analyst_signals"] = self._localize_analyst_signals(
                localized_result["analyst_signals"]
            )
        
        return localized_result
    
    def _localize_analyst_signals(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """本地化分析师信号"""
        localized = {}
        for analyst, signals in analyst_signals.items():
            localized_analyst = self.localize_analyst_name(analyst)
            if isinstance(signals, dict):
                localized_signals = {}
                for ticker, signal in signals.items():
                    if isinstance(signal, dict):
                        localized_signal = signal.copy()

                        # 本地化推理内容
                        reasoning = signal.get("reasoning", "")
                        if reasoning and self._is_english_content(reasoning):
                            localized_signal["reasoning"] = self._translate_to_chinese(reasoning)
                        localized_signals[ticker] = localized_signal
                localized[localized_analyst] = localized_signals
        return localized
    
    def localize_analyst_name(self, analyst_name: str) -> str:
        """本地化分析师名称"""
        from .analyst_name_mapper import get_analyst_chinese_name
        return get_analyst_chinese_name(analyst_name)
    
    def _is_english_content(self, text) -> bool:
        """判断是否为英文内容"""
        if not text:
            return False
        
        # 确保text是字符串类型
        if not isinstance(text, str):
            text = str(text)
        
        # 简单判断：如果英文字符占比超过50%，认为是英文内容
        try:
            english_chars = sum(1 for c in text if c.isalpha() and len(c) == 1 and ord(c) < 128)
            total_chars = len([c for c in text if c.isalpha()])
            return total_chars > 0 and english_chars / total_chars > 0.5
        except (TypeError, ValueError):
            return False
    
    def _translate_to_chinese(self, text) -> str:
        """翻译为中文（简化版本）"""
        # 确保text是字符串类型
        if not isinstance(text, str):
            if text is None:
                return ""
            text = str(text)
        
        # 这里可以集成真正的翻译API
        # 目前只做简单的关键词替换
        translations = {
            "bullish": "看涨",
            "bearish": "看跌",
            "neutral": "中性",
            "buy": "买入",
            "sell": "卖出",
            "hold": "持有",
            "The company": "该公司",
            "shows": "显示",
            "analysis": "分析",
            "data": "数据",
            "insufficient": "不足",
            "unavailable": "不可用"
        }
        
        result = text
        for en, zh in translations.items():
            result = result.replace(en, zh)
        
        return result


class QualityController:
    """质量控制器"""
    
    def assess_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """评估质量"""
        quality_info = {
            "data_completeness": self._assess_data_completeness(result),
            "analysis_quality": self._assess_analysis_quality(result),
            "confidence_level": self._assess_confidence_level(result),
            "alerts": self._generate_alerts(result)
        }
        
        result["quality_info"] = quality_info
        return result
    
    def _assess_data_completeness(self, result: Dict[str, Any]) -> float:
        """评估数据完整度"""
        total_fields = 0
        complete_fields = 0
        
        decisions = result.get("decisions", {})
        for ticker, decision in decisions.items():
            total_fields += 3  # action, confidence, reasoning
            if decision.get("action"):
                complete_fields += 1
            if decision.get("confidence", 0) > 0:
                complete_fields += 1
            if decision.get("reasoning") and "暂无" not in decision.get("reasoning", ""):
                complete_fields += 1
        
        return (complete_fields / total_fields * 100) if total_fields > 0 else 0
    
    def _assess_analysis_quality(self, result: Dict[str, Any]) -> float:
        """评估分析质量"""
        analyst_signals = result.get("analyst_signals", {})
        total_analyses = 0
        quality_analyses = 0
        
        for analyst, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    total_analyses += 1
                    reasoning = signal.get("reasoning", "")
                    confidence = signal.get("confidence", 0)
                    
                    # 质量标准：推理长度>50字符，信心度>30%，不包含"无详细分析"
                    if (len(reasoning) > 50 and 
                        confidence > 30 and 
                        "无详细分析" not in reasoning and
                        "Error" not in reasoning):
                        quality_analyses += 1
        
        return (quality_analyses / total_analyses * 100) if total_analyses > 0 else 0
    
    def _assess_confidence_level(self, result: Dict[str, Any]) -> float:
        """评估整体信心度"""
        analyst_signals = result.get("analyst_signals", {})
        total_confidence = 0
        count = 0
        
        for analyst, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    total_confidence += confidence
                    count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _generate_alerts(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成质量警告"""
        alerts = []
        
        # 检查数据完整度
        data_completeness = self._assess_data_completeness(result)
        if data_completeness < 50:
            alerts.append({
                "type": "warning",
                "message": f"数据完整度较低({data_completeness:.1f}%)，可能影响分析准确性"
            })
        
        # 检查分析质量
        analysis_quality = self._assess_analysis_quality(result)
        if analysis_quality < 30:
            alerts.append({
                "type": "error",
                "message": f"分析质量不佳({analysis_quality:.1f}%)，建议重新获取数据"
            })
        
        # 检查信心度
        confidence_level = self._assess_confidence_level(result)
        if confidence_level < 40:
            alerts.append({
                "type": "info",
                "message": f"整体信心度偏低({confidence_level:.1f}%)，投资决策需谨慎"
            })
        
        return alerts


# 便捷函数
def generate_improved_html_report(result: Dict[str, Any]) -> str:
    """生成改进版HTML报告的便捷函数"""
    generator = ImprovedHTMLReportGenerator()
    return generator.generate_report(result)


if __name__ == "__main__":
    # 测试代码
    test_result = {
        "decisions": {
            "600519": {
                "action": "hold",
                "confidence": 65.0,
                "reasoning": "贵州茅台基本面稳健，但当前估值偏高，建议持有观望"
            }
        },
        "analyst_signals": {
            "warren_buffett_agent": {
                "600519": {
                    "signal": "neutral",
                    "confidence": 70.0,
                    "reasoning": "公司具有良好的护城河，但需要关注估值水平"
                }
            }
        }
    }
    
    html_report = generate_improved_html_report(test_result)
    print("改进版HTML报告生成成功！")