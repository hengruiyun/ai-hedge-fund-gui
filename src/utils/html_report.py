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

try:
    from .analysts import ANALYST_CONFIG
except ImportError:
    # 如果导入失败，使用默认配置
    ANALYST_CONFIG = {}


class DataValidator:
    """数据验证器"""
    
    def validate_and_clean(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理数据"""
        if not result:
            return {"decisions": {}, "analyst_signals": {}}
        
        cleaned_result = {
            "decisions": self._clean_decisions(result.get("decisions", {})),
            "analyst_signals": self._clean_analyst_signals(result.get("analyst_signals", {}))
        }
        
        return cleaned_result
    
    def _clean_decisions(self, decisions: Dict) -> Dict:
        """清理投资决策数据"""
        cleaned = {}
        for ticker, decision in decisions.items():
            if not isinstance(decision, dict):
                continue
            
            cleaned_decision = {
                "action": str(decision.get("action", "hold")).lower(),
                "quantity": self._safe_int(decision.get("quantity", 0)),
                "confidence": self._safe_float(decision.get("confidence", 0)),
                "reasoning": str(decision.get("reasoning", "无详细说明"))
            }
            
            # 验证action值
            valid_actions = ["buy", "sell", "hold", "short", "cover"]
            if cleaned_decision["action"] not in valid_actions:
                cleaned_decision["action"] = "hold"
            
            cleaned[ticker] = cleaned_decision
        
        return cleaned
    
    def _clean_analyst_signals(self, analyst_signals: Dict) -> Dict:
        """清理分析师信号数据"""
        cleaned = {}
        for analyst_id, signals in analyst_signals.items():
            if not isinstance(signals, dict):
                continue
            
            cleaned_signals = {}
            for ticker, signal_data in signals.items():
                if not isinstance(signal_data, dict):
                    continue
                
                cleaned_signal = {
                    "signal": str(signal_data.get("signal", "neutral")).lower(),
                    "confidence": self._safe_float(signal_data.get("confidence", 0)),
                    "reasoning": signal_data.get("reasoning", "无详细分析")
                }
                
                # 验证signal值
                valid_signals = ["bullish", "bearish", "neutral"]
                if cleaned_signal["signal"] not in valid_signals:
                    cleaned_signal["signal"] = "neutral"
                
                cleaned_signals[ticker] = cleaned_signal
            
            if cleaned_signals:  # 只保留有效信号的分析师
                cleaned[analyst_id] = cleaned_signals
        
        return cleaned
    
    def _safe_int(self, value) -> int:
        """安全转换为整数"""
        try:
            return int(float(value)) if value is not None else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value) -> float:
        """安全转换为浮点数"""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0


class ContentLocalizer:
    """内容本地化器"""
    
    def __init__(self):
        # 使用统一的分析师名称映射器
        from .analyst_name_mapper import get_all_analyst_mappings
        self.analyst_names = get_all_analyst_mappings()
        
        self.action_names = {
            "buy": "买入",
            "sell": "卖出",
            "hold": "持有",
            "short": "做空",
            "cover": "平仓"
        }
        
        self.signal_names = {
            "bullish": "看涨",
            "bearish": "看跌",
            "neutral": "中性"
        }
    
    def localize_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """本地化内容"""
        localized_result = result.copy()
        
        # 添加本地化映射
        localized_result["localization"] = {
            "analyst_names": self.analyst_names,
            "action_names": self.action_names,
            "signal_names": self.signal_names
        }
        
        return localized_result


class QualityController:
    """质量控制器"""
    
    def assess_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        decisions = result.get("decisions", {})
        analyst_signals = result.get("analyst_signals", {})
        
        # 使用analyst_signals计算平均信心度，与执行摘要保持一致
        avg_confidence = self._calculate_avg_confidence_from_signals(analyst_signals)
        
        quality_info = {
            "total_decisions": len(decisions),
            "total_analysts": len(analyst_signals),
            "avg_confidence": avg_confidence,
            "data_completeness": self._assess_completeness(decisions, analyst_signals),
            "quality_score": 0
        }
        
        # 计算质量分数
        quality_info["quality_score"] = self._calculate_quality_score(quality_info)
        
        result["quality_info"] = quality_info
        return result
    
    def _calculate_avg_confidence(self, decisions: Dict) -> float:
        """计算平均信心度（基于decisions）"""
        if not decisions:
            return 0.0
        
        total_confidence = 0
        count = 0
        
        for decision in decisions.values():
            if isinstance(decision, dict) and "confidence" in decision:
                total_confidence += decision.get("confidence", 0)
                count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _calculate_average_long_short_value(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """计算平均多空值（基于信心度大于60%的信号）"""
        high_confidence_values = []
        
        for analyst_id, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    if confidence > 60:
                        signal_type = signal.get("signal", "neutral")
                        if signal_type == "bullish":
                            high_confidence_values.append(confidence)
                        elif signal_type == "bearish":
                            high_confidence_values.append(-confidence)
                        # neutral信号不计入平均多空值
        
        if not high_confidence_values:
            return {
                "average_value": 0,
                "direction": "中性",
                "count": 0,
                "description": "无信心度大于60%的明确多空信号"
            }
        
        average_value = sum(high_confidence_values) / len(high_confidence_values)
        direction = "看多" if average_value > 0 else "看空" if average_value < 0 else "中性"
        
        return {
            "average_value": average_value,
            "direction": direction,
            "count": len(high_confidence_values),
            "description": f"基于{len(high_confidence_values)}个高信心度信号，平均多空值为{average_value:.1f}，整体倾向{direction}"
        }
    
    def _analyze_high_confidence_signals(self, analyst_signals: Dict[str, Any]) -> str:
        """分析信心度60%以上的分析师建议"""
        high_confidence_signals = []
        signal_translations = {
            "bullish": "看涨",
            "bearish": "看跌", 
            "neutral": "中性"
        }
        
        # 从ANALYST_CONFIG获取分析师显示名称
        for analyst_id, signals in analyst_signals.items():
            if isinstance(signals, dict):
                config_key = analyst_id.replace('_agent', '') if analyst_id.endswith('_agent') else analyst_id
                analyst_config = ANALYST_CONFIG.get(config_key, {})
                analyst_name = analyst_config.get('display_name', analyst_id)
                
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    if confidence >= 60:
                        signal_type = signal.get("signal", "neutral")
                        signal_text = signal_translations.get(signal_type, signal_type)
                        high_confidence_signals.append(f"{analyst_name}对{ticker}{signal_text}({confidence:.1f}%)")
        
        if not high_confidence_signals:
            return "当前无信心度达到60%以上的分析师建议"
        elif len(high_confidence_signals) <= 3:
            return "、".join(high_confidence_signals)
        else:
            top_three = "、".join(high_confidence_signals[:3])
            return f"共{len(high_confidence_signals)}个高信心度建议，包括{top_three}等"
    
    def _calculate_avg_confidence_from_signals(self, analyst_signals: Dict[str, Any]) -> float:
        """计算平均信心度（基于analyst_signals）"""
        total_confidence = 0
        count = 0
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal_data in signals.items():
                    if isinstance(signal_data, dict) and "confidence" in signal_data:
                        confidence = signal_data.get("confidence", 0)
                        total_confidence += confidence
                        count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _assess_completeness(self, decisions: Dict, analyst_signals: Dict) -> float:
        """评估数据完整性"""
        if not decisions and not analyst_signals:
            return 0.0
        
        completeness_score = 0
        
        # 检查决策数据完整性
        if decisions:
            decision_completeness = 0
            for decision in decisions.values():
                if decision.get("reasoning") and decision.get("reasoning") != "无详细说明":
                    decision_completeness += 1
            completeness_score += (decision_completeness / len(decisions)) * 50
        
        # 检查分析师信号完整性
        if analyst_signals:
            signal_completeness = 0
            total_signals = 0
            for signals in analyst_signals.values():
                for signal in signals.values():
                    total_signals += 1
                    if signal.get("reasoning") and signal.get("reasoning") != "无详细分析":
                        signal_completeness += 1
            
            if total_signals > 0:
                completeness_score += (signal_completeness / total_signals) * 50
        
        return min(completeness_score, 100.0)
    
    def _calculate_quality_score(self, quality_info: Dict) -> float:
        """计算整体质量分数"""
        score = 0
        
        # 数据量评分 (30%)
        data_volume_score = min((quality_info["total_decisions"] * 10 + quality_info["total_analysts"] * 5), 30)
        score += data_volume_score
        
        # 信心度评分 (35%)
        confidence_score = (quality_info["avg_confidence"] / 100) * 35
        score += confidence_score
        
        # 完整性评分 (35%)
        completeness_score = (quality_info["data_completeness"] / 100) * 35
        score += completeness_score
        
        return min(score, 100.0)


class ImprovedHTMLReportGenerator:
    """改进版HTML报告生成器"""
    
    def __init__(self):
        self.data_validator = DataValidator()
        self.content_localizer = ContentLocalizer()
        self.quality_controller = QualityController()
    
    def _analyze_high_confidence_signals(self, analyst_signals: Dict[str, Any]) -> str:
        """分析信心度高于60%的分析师建议"""
        high_confidence_signals = []
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal_data in signals.items():
                    if isinstance(signal_data, dict):
                        confidence = signal_data.get("confidence", 0)
                        signal = signal_data.get("signal", "neutral")
                        if confidence >= 60:
                            # 获取分析师显示名称
                            from src.utils.analysts import ANALYST_CONFIG
                            display_name = ANALYST_CONFIG.get(analyst_name, {}).get("display_name", analyst_name)
                            signal_text = {"bullish": "看涨", "bearish": "看跌", "neutral": "中性"}.get(signal, signal)
                            high_confidence_signals.append(f"{display_name}对{ticker}的{signal_text}建议(信心度{confidence}%)")
        
        if not high_confidence_signals:
            return "当前无信心度达到60%以上的分析师建议"
        elif len(high_confidence_signals) <= 3:
            return "、".join(high_confidence_signals)
        else:
            top_three = "、".join(high_confidence_signals[:3])
            return f"共{len(high_confidence_signals)}个高信心度建议，包括{top_three}等"
    
    def _calculate_signal_statistics(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """计算信号统计"""
        stats = {"bullish": 0, "bearish": 0, "neutral": 0}
        
        for signals in analyst_signals.values():
            if isinstance(signals, dict):
                for signal_data in signals.values():
                    if isinstance(signal_data, dict):
                        signal = signal_data.get("signal", "neutral")
                        if signal in stats:
                            stats[signal] += 1
        
        # 确定主导信号
        dominant_signal = max(stats, key=stats.get)
        signal_map = {"bullish": "看涨", "bearish": "看跌", "neutral": "中性"}
        stats["dominant_signal"] = signal_map.get(dominant_signal, "中性")
        
        return stats
    
    def _calculate_average_confidence(self, analyst_signals: Dict[str, Any]) -> float:
        """计算平均信心度"""
        total_confidence = 0
        count = 0
        
        for signals in analyst_signals.values():
            if isinstance(signals, dict):
                for signal_data in signals.values():
                    if isinstance(signal_data, dict):
                        confidence = signal_data.get("confidence", 0)
                        if isinstance(confidence, (int, float)):
                            total_confidence += confidence
                            count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _calculate_average_long_short_value(self, analyst_signals: Dict[str, Any]) -> Dict[str, Any]:
        """计算平均多空值（基于信心度大于60%的信号）"""
        bullish_values = []
        bearish_values = []
        
        for signals in analyst_signals.values():
            if isinstance(signals, dict):
                for signal_data in signals.values():
                    if isinstance(signal_data, dict):
                        confidence = signal_data.get("confidence", 0)
                        signal = signal_data.get("signal", "neutral")
                        
                        # 只考虑信心度大于60%的信号
                        if confidence > 60:
                            if signal == "bullish":
                                bullish_values.append(confidence)
                            elif signal == "bearish":
                                bearish_values.append(-confidence)  # 看跌为负值
        
        # 合并所有值
        all_values = bullish_values + bearish_values
        
        if not all_values:
            return {
                "average_value": 0,
                "direction": "中性",
                "count": 0,
                "description": "无信心度大于60%的信号，市场观点中性"
            }
        
        average_value = sum(all_values) / len(all_values)
        
        if average_value > 0:
            direction = "看多"
            description = f"基于{len(all_values)}个高信心度信号，平均多空值为{average_value:.1f}，整体偏向看多"
        elif average_value < 0:
            direction = "看空"
            description = f"基于{len(all_values)}个高信心度信号，平均多空值为{average_value:.1f}，整体偏向看空"
        else:
            direction = "中性"
            description = f"基于{len(all_values)}个高信心度信号，平均多空值为{average_value:.1f}，市场观点中性"
        
        return {
            "average_value": average_value,
            "direction": direction,
            "count": len(all_values),
            "description": description
        }
    
    def _sort_analysts_by_order(self, analyst_signals: Dict[str, Any]) -> List[tuple]:
        """按照ANALYST_CONFIG中的order字段排序分析师"""
        from .analyst_name_mapper import get_all_analyst_mappings
        
        # 创建中文名称到order的映射
        analyst_order = {}
        chinese_to_english = {v: k for k, v in get_all_analyst_mappings().items()}
        
        for key, config in ANALYST_CONFIG.items():
            # 获取中文名称
            chinese_name = config.get("display_name", key)
            analyst_order[chinese_name] = config.get("order", 999)
            
            # 也为可能的英文键名添加映射
            agent_key = f"{key}_agent"
            analyst_order[agent_key] = config.get("order", 999)
            analyst_order[key] = config.get("order", 999)
        
        # 对分析师按order排序
        def get_order(analyst_name):
            # 首先尝试直接匹配
            if analyst_name in analyst_order:
                return analyst_order[analyst_name]
            
            # 如果是中文名称，尝试反向查找英文键名
            if analyst_name in chinese_to_english:
                english_key = chinese_to_english[analyst_name]
                base_key = english_key.replace('_agent', '') if english_key.endswith('_agent') else english_key
                if base_key in ANALYST_CONFIG:
                    return ANALYST_CONFIG[base_key].get("order", 999)
            
            return 999  # 默认排在最后
        
        sorted_items = sorted(
            analyst_signals.items(),
            key=lambda x: get_order(x[0])
        )
        
        return sorted_items
    
    def _generate_key_metrics(self, decisions: Dict[str, Any]) -> str:
        """生成关键指标"""
        if not decisions:
            return ""
        
        # 计算关键指标
        total_positions = len(decisions)
        buy_count = sum(1 for d in decisions.values() if d.get("action") == "buy")
        sell_count = sum(1 for d in decisions.values() if d.get("action") == "sell")
        hold_count = sum(1 for d in decisions.values() if d.get("action") == "hold")
        
        avg_confidence = sum(d.get("confidence", 0) for d in decisions.values()) / total_positions if total_positions > 0 else 0
        
        return f"""
        <div class="section">
            <h2>关键指标</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_positions}</div>
                    <div class="metric-label">总持仓数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{buy_count}</div>
                    <div class="metric-label">买入建议</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{sell_count}</div>
                    <div class="metric-label">卖出建议</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_confidence:.1f}%</div>
                    <div class="metric-label">平均信心度</div>
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
                <div class="risk-item">
                    <h4>市场风险</h4>
                    <p>当前市场波动性较高，建议密切关注宏观经济指标变化。</p>
                </div>
                <div class="risk-item">
                    <h4>流动性风险</h4>
                    <p>部分小盘股可能存在流动性不足的风险，建议控制仓位规模。</p>
                </div>
                <div class="risk-item">
                    <h4>信用风险</h4>
                    <p>关注企业财务状况，避免投资高负债率公司。</p>
                </div>
            </div>
        </div>
         """
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
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
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .header .timestamp {
            font-size: 0.9em;
            margin-top: 15px;
            opacity: 0.8;
        }
        
        .section {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        
        .footer {
            background: #34495e;
            color: white;
            text-align: center;
            padding: 20px;
        }
        
        .bullish { color: #27ae60; }
        .bearish { color: #e74c3c; }
        .neutral { color: #95a5a6; }
        
        .signal-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .signal-badge.bullish {
            background: #d5f4e6;
            color: #27ae60;
        }
        
        .signal-badge.bearish {
            background: #fdeaea;
            color: #e74c3c;
        }
        
        .signal-badge.neutral {
            background: #f8f9fa;
            color: #6c757d;
        }
        """
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        function toggleReasoning(id) {
            const textDiv = document.getElementById('text_' + id);
            const fullDiv = document.getElementById('full_' + id);
            const button = event.target;
            
            if (fullDiv.style.display === 'none' || fullDiv.style.display === '') {
                textDiv.style.display = 'none';
                fullDiv.style.display = 'block';
                button.textContent = '收起';
            } else {
                textDiv.style.display = 'block';
                fullDiv.style.display = 'none';
                button.textContent = '展开';
            }
        }
        
        function toggleAnalystText(button) {
            const textDiv = button.previousElementSibling;
            const isExpanded = textDiv.classList.contains('expanded');
            
            if (isExpanded) {
                textDiv.classList.remove('expanded');
                button.textContent = '展开';
            } else {
                textDiv.classList.add('expanded');
                button.textContent = '收起';
            }
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化所有展开按钮的状态
            const expandButtons = document.querySelectorAll('.expand-btn');
            expandButtons.forEach(button => {
                const onclick = button.getAttribute('onclick');
                if (onclick && onclick.includes('toggleReasoning')) {
                    const match = onclick.match(/toggleReasoning\('([^']+)'\)/);
                    if (match) {
                        const id = match[1];
                        const fullDiv = document.getElementById('full_' + id);
                        if (fullDiv) {
                            fullDiv.style.display = 'none';
                        }
                    }
                }
            });
        });
        """
    
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
        localization = result.get("localization", {})
        
        # 先生成CSS样式避免f-string解析问题
        css_styles = self._get_css_styles()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI基金大师投资分析报告</title>
    <style>{css_styles}</style>

    <style>
        .analyst-text {{
            max-height: 100px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        .analyst-text.expanded {{
            max-height: none;
        }}
        .expand-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            margin-top: 5px;
            cursor: pointer;
            border-radius: 3px;
            font-size: 12px;
        }}
        .expand-btn:hover {{
            background: #0056b3;
        }}
    </style>
    <script>
        function toggleAnalystText(button) {{{{
            const textDiv = button.previousElementSibling;
            const isExpanded = textDiv.classList.contains('expanded');
            
            if (isExpanded) {{{{
                textDiv.classList.remove('expanded');
                button.textContent = '展开';
            }}}} else {{{{
                textDiv.classList.add('expanded');
                button.textContent = '收起';
            }}}}
        }}}}
    </script>
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_quality_assessment(quality_info)}
        {self._generate_executive_summary(decisions, analyst_signals)}
        {self._generate_investment_recommendations(decisions, localization)}
        {self._generate_analyst_insights(analyst_signals, localization)}
        {self._generate_footer()}
    </div>
    <script>{self._get_javascript()}</script>
</body>
</html>
"""
        return html_content
    
    def _generate_error_html(self, error_message: str) -> str:
        """生成错误页面HTML"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>分析报告 - 错误</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .error-container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }}
        .error-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        .error-title {{
            color: #e74c3c;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        .error-message {{
            color: #666;
            line-height: 1.6;
        }}
    </style>

    <style>
        .analyst-text {
            max-height: 100px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .analyst-text.expanded {
            max-height: none;
        }
        .expand-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            margin-top: 5px;
            cursor: pointer;
            border-radius: 3px;
            font-size: 12px;
        }
        .expand-btn:hover {
            background: #0056b3;
        }
    </style>
    <script>
        function toggleAnalystText(button) {{{{
            const textDiv = button.previousElementSibling;
            const isExpanded = textDiv.classList.contains('expanded');
            
            if (isExpanded) {{{{
                textDiv.classList.remove('expanded');
                button.textContent = '展开';
            }}}} else {{{{
                textDiv.classList.add('expanded');
                button.textContent = '收起';
            }}}}
        }}}}
    </script>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-title">报告生成失败</div>
        <div class="error-message">{error_message}</div>
    </div>
</body>
</html>
        """


    def _generate_header(self) -> str:
        """生成报告头部"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        return f"""
        <div class="header">
            <h1>AI基金大师投资分析报告</h1>
            <div class="subtitle">智能投资决策 · 多维度分析 · 风险控制</div>
            <div class="subtitle">作者:267278466@qq.com</div>
            <div class="timestamp">生成时间: {current_time}</div>
        </div>
        """
    
    def _generate_quality_assessment(self, quality_info: Dict[str, Any]) -> str:
        """生成数据质量评估"""
        if not quality_info:
            return ""
        
        quality_score = quality_info.get("quality_score", 0)
        data_completeness = quality_info.get("data_completeness", 0)
        avg_confidence = quality_info.get("avg_confidence", 0)
        
        quality_class = "high" if quality_score > 70 else "medium" if quality_score > 40 else "low"
        
        return f"""
        <div class="section">
            <h2>数据质量评估</h2>
            <div class="quality-assessment {quality_class}">
                <div class="quality-metrics">
                    <div class="quality-metric">
                        <div class="metric-label">整体质量分数</div>
                        <div class="metric-value">{quality_score:.1f}/100</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {quality_score}%"></div>
                        </div>
                    </div>
                    <div class="quality-metric">
                        <div class="metric-label">数据完整度</div>
                        <div class="metric-value">{data_completeness:.1f}%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {data_completeness}%"></div>
                        </div>
                    </div>
                    <div class="quality-metric">
                        <div class="metric-label">平均信心度</div>
                        <div class="metric-value">{avg_confidence:.1f}%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {avg_confidence}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_executive_summary(self, decisions: Dict[str, Any], analyst_signals: Dict[str, Any]) -> str:
        """生成执行摘要，增强分析师差异分析"""
        # 统计分析师观点
        signal_stats = self._calculate_signal_statistics(analyst_signals)
        
        # 计算平均多空值
        long_short_analysis = self._calculate_average_long_short_value(analyst_signals)
        
        # 获取主要股票
        tickers = list(decisions.keys()) if decisions else []
        ticker_count = len(tickers)
        
        # 确定多空值的显示颜色
        value_class = "bullish" if long_short_analysis["average_value"] > 0 else "bearish" if long_short_analysis["average_value"] < 0 else "neutral"
        
        # 获取分析师差异分析
        divergence = signal_stats.get('analyst_divergence', {})
        analyst_avg_confidence = signal_stats.get('analyst_avg_confidence', {})
        
        # 生成分析师差异详细信息
        divergence_section = ""
        if divergence:
            divergence_section = f"""
            <div class="analyst-divergence-analysis">
                <h3>分析师观点差异分析</h3>
                <div class="divergence-overview">
                    <p><strong>观点分歧概况:</strong> {divergence.get('divergence_summary', '暂无数据')}</p>
                </div>
                <div class="analyst-characteristics">
                    <div class="char-row">
                        <span class="char-label">最看涨分析师:</span>
                        <span class="char-value">{divergence.get('most_bullish_analyst', '暂无')}</span>
                    </div>
                    <div class="char-row">
                        <span class="char-label">最看跌分析师:</span>
                        <span class="char-value">{divergence.get('most_bearish_analyst', '暂无')}</span>
                    </div>
                    <div class="char-row">
                        <span class="char-label">最自信分析师:</span>
                        <span class="char-value">{divergence.get('most_confident_analyst', '暂无')}</span>
                    </div>
                </div>
            </div>
            """
        
        # 生成各分析师平均置信度信息
        confidence_section = ""
        if analyst_avg_confidence:
            confidence_items = ""
            for analyst, confidence in analyst_avg_confidence.items():
                confidence_items += f"""
                <div class="confidence-item">
                    <span class="analyst-name">{analyst}:</span>
                    <span class="confidence-value">{confidence:.1f}%</span>
                </div>
                """
            
            confidence_section = f"""
            <div class="analyst-confidence-analysis">
                <h3>各分析师平均置信度</h3>
                <div class="confidence-grid">
                    {confidence_items}
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>执行摘要</h2>
            <div class="executive-summary">
                <div class="summary-text">
                    <p>本次分析覆盖 <strong>{ticker_count}</strong> 只股票，基于多位AI投资专家的综合评估.</p>
                    <p>整体市场信心度偏向 <strong>{long_short_analysis['direction']}</strong>.</p>
                    <p><strong>平均多空值分析:</strong> {long_short_analysis['description']}</p>
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
                    <div class="stat-card {value_class}">
                        <div class="stat-number">{long_short_analysis['average_value']:.1f}</div>
                        <div class="stat-label">平均多空值</div>
                    </div>
                </div>
                
                {divergence_section}
                {confidence_section}
            </div>
            
            <div class="disclaimer">
                <strong>风险提示:</strong> 本报告为编程生成的模拟样本，不能作为真实使用.投资有风险，决策需谨慎.请根据自身情况做出投资决定.
            </div>
        </div>
        """
    
    def _generate_investment_recommendations(self, decisions: Dict[str, Any], localization: Dict[str, Any]) -> str:
        """生成投资建议"""
        if not decisions:
            return ""
        
        action_names = localization.get("action_names", {})
        
        recommendations_html = """
        <div class="section">
            <h2>投资建议</h2>
            <div class="recommendations-grid">
        """
        
        for ticker, decision in decisions.items():
            action = decision.get("action", "hold")
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning", "暂无详细分析")
            
            # 本地化动作描述
            action_text = action_names.get(action, action)
            
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
    
    def _generate_analyst_insights(self, analyst_signals: Dict[str, Any], localization: Dict[str, Any]) -> str:
        """生成分析师洞察"""
        if not analyst_signals:
            return """
            <div class="section">
                <h2>专家洞察</h2>
                <div class="no-data">暂无分析师数据</div>
            </div>
            """
        
        analyst_names = localization.get("analyst_names", {})
        signal_names = localization.get("signal_names", {})
        
        insights_html = """
        <div class="section">
            <h2>专家洞察</h2>
            <div class="insights-grid">
        """
        
        # 按照ANALYST_CONFIG中的order字段排序分析师
        sorted_analysts = self._sort_analysts_by_order(analyst_signals)
        
        for analyst_id, signals in sorted_analysts:
            # 使用统一的分析师名称映射器
            from .analyst_name_mapper import get_analyst_chinese_name
            analyst_name = get_analyst_chinese_name(analyst_id)
            
            insights_html += f"""
            <div class="analyst-card">
                <div class="analyst-header">
                    <h4>{analyst_name}</h4>
                </div>
                <div class="analyst-signals">
            """
            
            for ticker, signal in signals.items():
                signal_type = signal.get("signal", "neutral")
                confidence = signal.get("confidence", 0)
                
                # 对于技术分析师，优先使用detailed_reasoning字段
                if analyst_id == "technical_analyst" and "detailed_reasoning" in signal:
                    reasoning = signal.get("detailed_reasoning", "")
                    # 对于detailed_reasoning，不进行格式化，直接使用
                    formatted_reasoning = reasoning
                else:
                    reasoning = signal.get("reasoning", "")
                    # 格式化推理内容
                    formatted_reasoning = self._format_reasoning(reasoning, analyst_id)
                
                signal_text = signal_names.get(signal_type, signal_type)
                
                # 确定信心度样式类
                confidence_class = "low-confidence" if confidence < 50 else ""
                
                # 为长文本添加展开功能
                if len(formatted_reasoning) > 150:
                    short_reasoning = str(formatted_reasoning)[:150] + "..."
                    reasoning_html = f"""
                    <div class="signal-reasoning {confidence_class}">
                        <div class="reasoning-text" id="text_{analyst_id}_{ticker}">{short_reasoning}</div>
                        <div class="reasoning-full" id="full_{analyst_id}_{ticker}" style="display: none;">{formatted_reasoning}</div>
                        <button class="expand-btn" onclick="toggleReasoning('{analyst_id}_{ticker}')">展开</button>
                    </div>
                    """
                else:
                    reasoning_html = f'<div class="signal-reasoning {confidence_class}">{formatted_reasoning}</div>'
                
                insights_html += f"""
                <div class="signal-item {confidence_class}">
                    <div class="signal-header">
                        <span class="ticker">{ticker}</span>
                        <span class="signal-badge {signal_type}">{signal_text}</span>
                        <span class="confidence">{confidence:.1f}%</span>
                    </div>
                    {reasoning_html}
                </div>
                """
            
            insights_html += """
                </div>
            </div>
            """
        
        insights_html += """
            </div>
        </div>
        """
        
        return insights_html
    
    def _sort_analysts_by_order(self, analyst_signals: Dict[str, Any]) -> List[tuple]:
        """按照ANALYST_CONFIG中的order字段排序分析师"""
        from .analyst_name_mapper import get_all_analyst_mappings
        
        # 创建中文名称到order的映射
        analyst_order = {}
        chinese_to_english = {v: k for k, v in get_all_analyst_mappings().items()}
        
        for key, config in ANALYST_CONFIG.items():
            # 获取中文名称
            chinese_name = config.get("display_name", key)
            analyst_order[chinese_name] = config.get("order", 999)
            
            # 也为可能的英文键名添加映射
            agent_key = f"{key}_agent"
            analyst_order[agent_key] = config.get("order", 999)
            analyst_order[key] = config.get("order", 999)
        
        # 对分析师按order排序
        def get_order(analyst_name):
            # 首先尝试直接匹配
            if analyst_name in analyst_order:
                return analyst_order[analyst_name]
            
            # 如果是中文名称，尝试反向查找英文键名
            if analyst_name in chinese_to_english:
                english_key = chinese_to_english[analyst_name]
                base_key = english_key.replace('_agent', '') if english_key.endswith('_agent') else english_key
                if base_key in ANALYST_CONFIG:
                    return ANALYST_CONFIG[base_key].get("order", 999)
            
            return 999  # 默认排在最后
        
        sorted_items = sorted(
            analyst_signals.items(),
            key=lambda x: get_order(x[0])
        )
        
        return sorted_items
    
    def _format_reasoning(self, reasoning: Any, analyst_id: str) -> str:
        """格式化分析师推理内容"""
        if not reasoning:
            return "暂无详细分析"
        
        # 如果是字符串，直接处理
        if isinstance(reasoning, str):
            # 如果是英文内容，进行翻译或本地化
            if self._is_english_content(reasoning):
                return self._translate_to_chinese(reasoning)
            return str(reasoning)[:200] + "..." if len(str(reasoning)) > 200 else str(reasoning)
        
        # 如果是字典，根据分析师类型进行格式化
        if isinstance(reasoning, dict):
            return self._format_dict_reasoning(reasoning, analyst_id)
        
        # 其他类型转为字符串
        return str(reasoning)[:200] + "..." if len(str(reasoning)) > 200 else str(reasoning)
    
    def _format_dict_reasoning(self, reasoning: dict, analyst_id: str) -> str:
        """格式化字典类型的推理内容"""
        if analyst_id == "fundamentals_analyst_agent":
            return self._format_fundamentals_reasoning(reasoning)
        elif analyst_id == "sentiment_analyst_agent":
            return self._format_sentiment_reasoning(reasoning)
        elif analyst_id == "risk_management_agent":
            return self._format_risk_reasoning(reasoning)
        elif analyst_id == "technical_analyst":
            return self._format_technical_reasoning(reasoning)
        elif analyst_id == "bill_ackman_agent":
            return self._format_bill_ackman_reasoning(reasoning)
        else:
            # 默认格式化
            return self._format_default_reasoning(reasoning)
    
    def _format_fundamentals_reasoning(self, reasoning: dict) -> str:
        """格式化基本面分析师推理"""
        parts = []
        
        # 信号翻译映射
        signal_translations = {
            "bullish": "看涨",
            "bearish": "看跌", 
            "neutral": "中性"
        }
        
        if "profitability_signal" in reasoning:
            prof = reasoning["profitability_signal"]
            signal = prof.get("signal", "未知")
            signal_zh = signal_translations.get(signal, signal)
            details = prof.get("details", "")
            # 翻译details中的英文内容
            details_zh = self._translate_to_chinese(details) if self._is_english_content(details) else details
            parts.append(f"盈利能力: {signal_zh} ({details_zh})")
        
        if "growth_signal" in reasoning:
            growth = reasoning["growth_signal"]
            signal = growth.get("signal", "未知")
            signal_zh = signal_translations.get(signal, signal)
            details = growth.get("details", "")
            details_zh = self._translate_to_chinese(details) if self._is_english_content(details) else details
            parts.append(f"成长性: {signal_zh} ({details_zh})")
        
        if "financial_health_signal" in reasoning:
            health = reasoning["financial_health_signal"]
            signal = health.get("signal", "未知")
            signal_zh = signal_translations.get(signal, signal)
            details = health.get("details", "")
            details_zh = self._translate_to_chinese(details) if self._is_english_content(details) else details
            parts.append(f"财务健康: {signal_zh} ({details_zh})")
        
        if "price_ratios_signal" in reasoning:
            ratios = reasoning["price_ratios_signal"]
            signal = ratios.get("signal", "未知")
            signal_zh = signal_translations.get(signal, signal)
            details = ratios.get("details", "")
            details_zh = self._translate_to_chinese(details) if self._is_english_content(details) else details
            parts.append(f"估值水平: {signal_zh} ({details_zh})")
        
        return "; ".join(parts) if parts else "基本面分析完成，详细指标请参考财务数据"
    
    def _format_sentiment_reasoning(self, reasoning: dict) -> str:
        """格式化情绪分析师推理"""
        parts = []
        
        if "insider_trading" in reasoning:
            insider = reasoning["insider_trading"]
            signal = insider.get("signal", "未知")
            metrics = insider.get("metrics", {})
            total_trades = metrics.get("total_trades", 0)
            parts.append(f"内部交易: {signal} (共{total_trades}笔交易)")
        
        if "news_sentiment" in reasoning:
            news = reasoning["news_sentiment"]
            signal = news.get("signal", "未知")
            metrics = news.get("metrics", {})
            total_articles = metrics.get("total_articles", 0)
            parts.append(f"新闻情绪: {signal} (分析{total_articles}篇新闻)")
        
        if "combined_analysis" in reasoning:
            combined = reasoning["combined_analysis"]
            determination = combined.get("signal_determination", "")
            if determination:
                parts.append(f"综合判断: {determination}")
        
        return "; ".join(parts) if parts else "市场情绪分析完成，综合考虑内部交易和新闻情绪"
    
    def _format_risk_reasoning(self, reasoning: dict) -> str:
        """格式化风险管理分析师推理"""
        if "error" in reasoning:
            return f"风险分析错误: {reasoning['error']}"
        
        parts = []
        portfolio_value = reasoning.get("portfolio_value", 0)
        position_limit = reasoning.get("position_limit", 0)
        available_cash = reasoning.get("available_cash", 0)
        
        # 计算风险指标
        if portfolio_value > 0:
            position_ratio = (position_limit / portfolio_value) * 100
            cash_ratio = (available_cash / portfolio_value) * 100
            
            parts.append(f"组合总值: ${portfolio_value:,.0f}")
            parts.append(f"单股风险限额: ${position_limit:,.0f} ({position_ratio:.1f}%)")
            parts.append(f"可用现金: ${available_cash:,.0f} ({cash_ratio:.1f}%)")
            
            # 添加风险评估
            if cash_ratio > 80:
                parts.append("风险评估: 现金比例较高，建议适度增加投资")
            elif cash_ratio < 20:
                parts.append("风险评估: 现金比例较低，注意流动性风险")
            else:
                parts.append("风险评估: 资金配置合理，风险可控")
        else:
            parts.append("组合总值: $0")
            parts.append("风险评估: 尚未建立投资组合")
        
        return "; ".join(parts)
    
    def _format_technical_reasoning(self, reasoning: dict) -> str:
        """格式化技术面分析师推理"""
        parts = []
        
        # 信号翻译映射
        signal_translations = {
            "bullish": "看涨",
            "bearish": "看跌", 
            "neutral": "中性"
        }
        
        # 策略名称翻译
        strategy_translations = {
            "trend_following": "趋势跟踪",
            "mean_reversion": "均值回归",
            "momentum": "动量策略",
            "volatility": "波动率策略",
            "statistical_arbitrage": "统计套利"
        }
        
        for strategy, signal in reasoning.items():
            if strategy in strategy_translations:
                strategy_name = strategy_translations[strategy]
                if isinstance(signal, str) and signal in signal_translations:
                    signal_text = signal_translations[signal]
                    parts.append(f"{strategy_name}: {signal_text}")
                elif isinstance(signal, dict) and "signal" in signal:
                    signal_value = signal.get("signal", "neutral")
                    signal_text = signal_translations.get(signal_value, signal_value)
                    confidence = signal.get("confidence", "")
                    if confidence:
                        parts.append(f"{strategy_name}: {signal_text} (置信度: {confidence})")
                    else:
                        parts.append(f"{strategy_name}: {signal_text}")
        
        return "; ".join(parts) if parts else "技术面分析完成，基于多种技术指标综合判断"
    
    def _format_bill_ackman_reasoning(self, reasoning: dict) -> str:
        """格式化比尔·阿克曼分析师推理"""
        parts = []
        
        # 业务质量分析
        if "quality_analysis" in reasoning:
            quality = reasoning["quality_analysis"]
            score = quality.get("score", 0)
            max_score = quality.get("max_score", 10)
            details = quality.get("details", "")
            parts.append(f"业务质量评分: {score}/{max_score} ({details})")
        
        # 财务纪律分析
        if "balance_sheet_analysis" in reasoning:
            balance = reasoning["balance_sheet_analysis"]
            score = balance.get("score", 0)
            max_score = balance.get("max_score", 10)
            details = balance.get("details", "")
            parts.append(f"财务纪律评分: {score}/{max_score} ({details})")
        
        # Activism潜力分析
        if "activism_analysis" in reasoning:
            activism = reasoning["activism_analysis"]
            score = activism.get("score", 0)
            max_score = activism.get("max_score", 10)
            details = activism.get("details", "")
            parts.append(f"改善潜力评分: {score}/{max_score} ({details})")
        
        # 估值分析
        if "valuation_analysis" in reasoning:
            valuation = reasoning["valuation_analysis"]
            score = valuation.get("score", 0)
            max_score = valuation.get("max_score", 10)
            details = valuation.get("details", "")
            fcf_yield = valuation.get("fcf_yield")
            if fcf_yield:
                parts.append(f"估值评分: {score}/{max_score}, FCF收益率: {fcf_yield:.1%} ({details})")
            else:
                parts.append(f"估值评分: {score}/{max_score} ({details})")
        
        # 总体评分
        total_score = reasoning.get("score", 0)
        max_possible = reasoning.get("max_score", 40)
        if total_score and max_possible:
            parts.append(f"总体评分: {total_score}/{max_possible} ({total_score/max_possible:.1%})")
        
        return "; ".join(parts) if parts else "Ackman风格分析完成，基于业务质量、财务纪律、改善潜力和估值四个维度"
    
    def _format_default_reasoning(self, reasoning: dict) -> str:
        """默认字典格式化"""
        # 提取关键信息
        key_items = []
        for key, value in reasoning.items():
            if isinstance(value, (str, int, float)):
                key_items.append(f"{key}: {value}")
            elif isinstance(value, dict) and "signal" in value:
                signal = value.get("signal", "")
                key_items.append(f"{key}: {signal}")
        
        result = "; ".join(key_items[:3])  # 只显示前3个关键项
        return result if result else "分析完成"
    
    def _is_english_content(self, text: str) -> bool:
        """判断是否为英文内容"""
        if not text:
            return False
        # 简单判断：如果英文字符占比超过70%，认为是英文内容
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        return total_chars > 0 and english_chars / total_chars > 0.7
    
    def _translate_to_chinese(self, text: str) -> str:
        """将英文内容翻译为中文（简化版）"""
        # 这里可以集成翻译API，现在先做简单的关键词替换
        translations = {
            "bullish": "看涨",
            "bearish": "看跌",
            "neutral": "中性",
            "high": "高",
            "low": "低",
            "medium": "中等",
            "strong": "强劲",
            "weak": "疲弱",
            "positive": "积极",
            "negative": "消极",
            "growth": "增长",
            "decline": "下降",
            "ratio": "比率",
            "margin": "利润率",
            "debt": "债务",
            "equity": "股权",
            "revenue": "营收",
            "earnings": "盈利",
            "cash flow": "现金流",
            "P/E": "市盈率",
            "P/B": "市净率",
            "ROE": "净资产收益率",
            "The stock": "该股票",
            "The company": "该公司",
            "analysis": "分析",
            "indicates": "显示",
            "suggests": "表明",
            "shows": "显示",
            "based on": "基于",
            "due to": "由于",
            "however": "然而",
            "therefore": "因此",
            "overall": "总体而言"
        }
        
        result = text
        for en, zh in translations.items():
            result = result.replace(en, zh)
        
        # 截取长度
        return str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
    
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
        """计算信号统计，增强各分析师差异分析"""
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        # 新增：各分析师观点统计
        analyst_recommendations = {}
        analyst_confidence_levels = {}
        ticker_analyst_matrix = {}  # 每只股票的分析师观点矩阵
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                analyst_recommendations[analyst_name] = {}
                analyst_confidence_levels[analyst_name] = []
                
                for ticker, signal in signals.items():
                    signal_type = signal.get("signal", "neutral").lower()
                    confidence = signal.get("confidence", 0)
                    
                    # 基础统计
                    if signal_type == "bullish":
                        bullish_count += 1
                    elif signal_type == "bearish":
                        bearish_count += 1
                    else:
                        neutral_count += 1
                    
                    # 分析师观点统计
                    analyst_recommendations[analyst_name][ticker] = signal_type
                    analyst_confidence_levels[analyst_name].append(confidence)
                    
                    # 构建股票-分析师观点矩阵
                    if ticker not in ticker_analyst_matrix:
                        ticker_analyst_matrix[ticker] = {}
                    ticker_analyst_matrix[ticker][analyst_name] = {
                        'signal': signal_type,
                        'confidence': confidence
                    }
        
        # 确定主导信号
        if bullish_count > bearish_count and bullish_count > neutral_count:
            dominant_signal = "看涨"
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            dominant_signal = "看跌"
        else:
            dominant_signal = "中性"
        
        # 分析师观点差异分析
        analyst_divergence = self._analyze_analyst_divergence(ticker_analyst_matrix)
        
        # 计算各分析师平均置信度
        analyst_avg_confidence = {}
        for analyst, confidences in analyst_confidence_levels.items():
            if confidences:
                analyst_avg_confidence[analyst] = sum(confidences) / len(confidences)
        
        return {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count,
            "dominant_signal": dominant_signal,
            "analyst_recommendations": analyst_recommendations,
            "analyst_avg_confidence": analyst_avg_confidence,
            "analyst_divergence": analyst_divergence,
            "ticker_analyst_matrix": ticker_analyst_matrix
        }
    
    def _analyze_analyst_divergence(self, ticker_analyst_matrix: Dict[str, Dict]) -> Dict[str, Any]:
        """分析各分析师观点差异"""
        divergence_analysis = {
            "high_divergence_tickers": [],
            "consensus_tickers": [],
            "divergence_summary": "",
            "most_bullish_analyst": "",
            "most_bearish_analyst": "",
            "most_confident_analyst": ""
        }
        
        # 分析每只股票的观点分歧
        for ticker, analyst_views in ticker_analyst_matrix.items():
            signals = [view['signal'] for view in analyst_views.values()]
            unique_signals = set(signals)
            
            if len(unique_signals) > 1:
                divergence_analysis["high_divergence_tickers"].append(ticker)
            else:
                divergence_analysis["consensus_tickers"].append(ticker)
        
        # 统计各分析师倾向
        analyst_signal_counts = {}
        analyst_total_confidence = {}
        
        for ticker, analyst_views in ticker_analyst_matrix.items():
            for analyst, view in analyst_views.items():
                if analyst not in analyst_signal_counts:
                    analyst_signal_counts[analyst] = {'bullish': 0, 'bearish': 0, 'neutral': 0}
                    analyst_total_confidence[analyst] = []
                
                analyst_signal_counts[analyst][view['signal']] += 1
                analyst_total_confidence[analyst].append(view['confidence'])
        
        # 找出最看涨、最看跌、最自信的分析师（考虑置信度权重）
        max_weighted_bullish_score = 0
        max_weighted_bearish_score = 0
        max_avg_confidence = 0
        
        for analyst, counts in analyst_signal_counts.items():
            total = sum(counts.values())
            if total > 0:
                # 计算加权的看涨/看跌分数（信号比例 × 平均置信度）
                bullish_ratio = counts['bullish'] / total
                bearish_ratio = counts['bearish'] / total
                avg_confidence = sum(analyst_total_confidence[analyst]) / len(analyst_total_confidence[analyst])
                
                # 只有当平均置信度 >= 30% 时才考虑为有效的看涨/看跌分析师
                if avg_confidence >= 30:
                    weighted_bullish_score = bullish_ratio * avg_confidence
                    weighted_bearish_score = bearish_ratio * avg_confidence
                    
                    if weighted_bullish_score > max_weighted_bullish_score:
                        max_weighted_bullish_score = weighted_bullish_score
                        divergence_analysis["most_bullish_analyst"] = analyst
                    
                    if weighted_bearish_score > max_weighted_bearish_score:
                        max_weighted_bearish_score = weighted_bearish_score
                        divergence_analysis["most_bearish_analyst"] = analyst
                
                if avg_confidence > max_avg_confidence:
                    max_avg_confidence = avg_confidence
                    divergence_analysis["most_confident_analyst"] = analyst
        
        # 生成差异总结
        total_tickers = len(ticker_analyst_matrix)
        divergent_count = len(divergence_analysis["high_divergence_tickers"])
        consensus_count = len(divergence_analysis["consensus_tickers"])
        
        if divergent_count > consensus_count:
            divergence_analysis["divergence_summary"] = f"分析师观点存在较大分歧，{divergent_count}只股票观点不一致，{consensus_count}只股票达成共识"
        else:
            divergence_analysis["divergence_summary"] = f"分析师观点相对一致，{consensus_count}只股票达成共识，{divergent_count}只股票存在分歧"
        
        return divergence_analysis
    
    def _calculate_average_confidence(self, analyst_signals: Dict[str, Any]) -> float:
        """计算平均信心度（只使用大于60%的信心度）"""
        total_confidence = 0
        count = 0
        
        for analyst_name, signals in analyst_signals.items():
            if isinstance(signals, dict):
                for ticker, signal in signals.items():
                    confidence = signal.get("confidence", 0)
                    # 只使用信心度大于60%的信号
                    if confidence > 60:
                        total_confidence += confidence
                        count += 1
        
        return total_confidence / count if count > 0 else 0
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                overflow: hidden;
                animation: slideIn 0.8s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 40px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: rotate 20s linear infinite;
            }
            
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                position: relative;
                z-index: 1;
            }
            
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 15px;
                position: relative;
                z-index: 1;
            }
            
            .timestamp {
                font-size: 0.9em;
                opacity: 0.8;
                position: relative;
                z-index: 1;
            }
            
            .section {
                padding: 30px 40px;
                border-bottom: 1px solid #eee;
            }
            
            .section:last-child {
                border-bottom: none;
            }
            
            .section h2 {
                color: #2c3e50;
                margin-bottom: 25px;
                font-size: 1.8em;
                position: relative;
                padding-bottom: 10px;
            }
            
            .section h2::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 50px;
                height: 3px;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                border-radius: 2px;
            }
            
            /* 数据质量评估样式 */
            .quality-assessment {
                background: #f8f9fa;
                border-radius: 15px;
                padding: 25px;
                border-left: 5px solid #3498db;
            }
            
            .quality-assessment.high {
                border-left-color: #27ae60;
                background: linear-gradient(135deg, #d5f4e6 0%, #fafafa 100%);
            }
            
            .quality-assessment.medium {
                border-left-color: #f39c12;
                background: linear-gradient(135deg, #fef9e7 0%, #fafafa 100%);
            }
            
            .quality-assessment.low {
                border-left-color: #e74c3c;
                background: linear-gradient(135deg, #fadbd8 0%, #fafafa 100%);
            }
            
            .quality-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }
            
            .quality-metric {
                text-align: center;
            }
            
            .metric-label {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 8px;
            }
            
            .metric-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            .metric-bar {
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .metric-fill {
                height: 100%;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                border-radius: 4px;
                transition: width 1s ease-in-out;
            }
            
            /* 执行摘要样式 */
            .executive-summary {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
            }
            
            .summary-text {
                margin-bottom: 25px;
            }
            
            .summary-text p {
                margin-bottom: 10px;
                font-size: 1.1em;
                line-height: 1.7;
            }
            
            .summary-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
            }
            
            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .stat-card.bullish {
                border-top: 4px solid #27ae60;
            }
            
            .stat-card.bearish {
                border-top: 4px solid #e74c3c;
            }
            
            .stat-card.neutral {
                border-top: 4px solid #95a5a6;
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }
            
            .stat-label {
                font-size: 0.9em;
                color: #7f8c8d;
                margin-top: 5px;
            }
            
            /* 分析师差异分析样式 */
            .analyst-divergence-analysis {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-top: 20px;
                border-left: 4px solid #3498db;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .analyst-confidence-analysis {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-top: 20px;
                border-left: 4px solid #17a2b8;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .divergence-overview {
                margin-bottom: 15px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            
            .analyst-characteristics {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .char-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 12px;
                background: #f8f9fa;
                border-radius: 6px;
                border-left: 3px solid #e9ecef;
            }
            
            .char-label {
                font-weight: bold;
                color: #495057;
            }
            
            .char-value {
                color: #007bff;
                font-weight: 500;
            }
            
            .confidence-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
            }
            
            .confidence-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 3px solid #17a2b8;
            }
            
            .analyst-name {
                font-weight: bold;
                color: #495057;
            }
            
            .confidence-value {
                color: #17a2b8;
                font-weight: bold;
            }
            
            .analyst-divergence-analysis h3,
            .analyst-confidence-analysis h3 {
                margin-top: 0;
                margin-bottom: 15px;
                color: #2c3e50;
                font-size: 1.2em;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 8px;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 0.9em;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .disclaimer {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                font-size: 0.9em;
                color: #856404;
            }
            
            /* 投资建议样式 */
            .recommendations-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 25px;
            }
            
            .recommendation-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                overflow: hidden;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border-top: 4px solid #3498db;
            }
            
            .recommendation-card:hover {
                transform: translateY(-8px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            }
            
            .recommendation-card.buy {
                border-top-color: #27ae60;
            }
            
            .recommendation-card.sell {
                border-top-color: #e74c3c;
            }
            
            .recommendation-card.hold {
                border-top-color: #f39c12;
            }
            
            .recommendation-header {
                padding: 20px;
                background: #f8f9fa;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .recommendation-header h3 {
                color: #2c3e50;
                font-size: 1.3em;
            }
            
            .action-badge {
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .action-badge.buy {
                background: #d5f4e6;
                color: #27ae60;
            }
            
            .action-badge.sell {
                background: #fadbd8;
                color: #e74c3c;
            }
            
            .action-badge.hold {
                background: #fef9e7;
                color: #f39c12;
            }
            
            .recommendation-body {
                padding: 20px;
            }
            
            .confidence-section {
                margin-bottom: 20px;
            }
            
            .confidence-label {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 8px;
            }
            
            .confidence-bar {
                width: 100%;
                height: 10px;
                background: #e0e0e0;
                border-radius: 5px;
                overflow: hidden;
            }
            
            .confidence-fill {
                height: 100%;
                border-radius: 5px;
                transition: width 1.5s ease-in-out;
            }
            
            .confidence-fill.buy {
                background: linear-gradient(90deg, #27ae60, #2ecc71);
            }
            
            .confidence-fill.sell {
                background: linear-gradient(90deg, #e74c3c, #c0392b);
            }
            
            .confidence-fill.hold {
                background: linear-gradient(90deg, #f39c12, #e67e22);
            }
            
            .reasoning-section h4 {
                color: #2c3e50;
                margin-bottom: 10px;
                font-size: 1em;
            }
            
            .reasoning-section p {
                color: #555;
                line-height: 1.6;
            }
            
            /* 专家洞察样式 */
            .insights-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
            }
            
            .analyst-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                overflow: hidden;
                transition: transform 0.3s ease;
            }
            
            .analyst-card:hover {
                transform: translateY(-5px);
            }
            
            .analyst-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            
            .analyst-header h4 {
                font-size: 1.2em;
                margin: 0;
            }
            
            .analyst-signals {
                padding: 20px;
            }
            
            .signal-item {
                margin-bottom: 15px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #3498db;
            }
            
            .signal-item:last-child {
                margin-bottom: 0;
            }
            
            .signal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .ticker {
                font-weight: bold;
                color: #2c3e50;
                font-size: 1.1em;
            }
            
            .signal-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            .signal-badge.bullish {
                background: #d5f4e6;
                color: #27ae60;
            }
            
            .signal-badge.bearish {
                background: #fadbd8;
                color: #e74c3c;
            }
            
            .signal-badge.neutral {
                background: #e8f4f8;
                color: #34495e;
            }
            
            .confidence {
                font-size: 0.9em;
                color: #666;
                font-weight: bold;
            }
            
            .signal-reasoning {
                font-size: 0.9em;
                color: #555;
                line-height: 1.5;
            }
            
            /* 低信心度样式 */
            .signal-item.low-confidence {
                opacity: 0.6;
                background: #f5f5f5;
                border-left-color: #bdc3c7;
            }
            
            .signal-item.low-confidence .ticker,
            .signal-item.low-confidence .confidence,
            .signal-item.low-confidence .signal-reasoning {
                color: #95a5a6;
            }
            
            .signal-item.low-confidence .signal-badge {
                opacity: 0.7;
                background: #ecf0f1;
                color: #7f8c8d;
            }
            
            .no-data {
                text-align: center;
                color: #666;
                font-style: italic;
                padding: 40px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            
            /* 页脚样式 */
            .footer {
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }
            
            .footer p {
                margin: 0;
            }
            
            /* 响应式设计 */
            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }
                
                .container {
                    border-radius: 10px;
                }
                
                .header {
                    padding: 30px 20px;
                }
                
                .header h1 {
                    font-size: 2em;
                }
                
                .section {
                    padding: 20px;
                }
                
                .recommendations-grid,
                .insights-grid {
                    grid-template-columns: 1fr;
                }
                
                .summary-stats {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .signal-header {
                    flex-direction: column;
                    align-items: flex-start;
                }
            }
            
            /* 加载动画 */
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        """
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
            // 展开/收起分析理由的函数
            function toggleReasoning(id) {
                const textDiv = document.getElementById('text_' + id);
                const fullDiv = document.getElementById('full_' + id);
                const button = event.target;
                
                if (fullDiv.style.display === 'none') {
                    textDiv.style.display = 'none';
                    fullDiv.style.display = 'block';
                    button.textContent = '收起';
                } else {
                    textDiv.style.display = 'block';
                    fullDiv.style.display = 'none';
                    button.textContent = '展开';
                }
            }
            
            // 兼容旧版本的toggleAnalystText函数
            function toggleAnalystText(button) {
                const textDiv = button.previousElementSibling;
                const isExpanded = textDiv.classList.contains('expanded');
                
                if (isExpanded) {
                    textDiv.classList.remove('expanded');
                    button.textContent = '展开';
                } else {
                    textDiv.classList.add('expanded');
                    button.textContent = '收起';
                }
            }
            
            // 页面加载完成后的动画效果
            document.addEventListener('DOMContentLoaded', function() {
                // 延迟显示各个部分
                const sections = document.querySelectorAll('.section');
                sections.forEach((section, index) => {
                    section.style.opacity = '0';
                    section.style.transform = 'translateY(20px)';
                    
                    setTimeout(() => {
                        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                        section.style.opacity = '1';
                        section.style.transform = 'translateY(0)';
                    }, index * 200);
                });
                
                // 动画化进度条
                setTimeout(() => {
                    const progressBars = document.querySelectorAll('.metric-fill, .confidence-fill');
                    progressBars.forEach(bar => {
                        const width = bar.style.width;
                        bar.style.width = '0';
                        setTimeout(() => {
                            bar.style.width = width;
                        }, 100);
                    });
                }, 1000);
                
                // 添加卡片悬停效果
                const cards = document.querySelectorAll('.stat-card, .recommendation-card, .analyst-card');
                cards.forEach(card => {
                    card.addEventListener('mouseenter', function() {
                        this.style.transform = 'translateY(-8px) scale(1.02)';
                    });
                    
                    card.addEventListener('mouseleave', function() {
                        this.style.transform = 'translateY(0) scale(1)';
                    });
                });
                
                // 添加数字计数动画
                const numbers = document.querySelectorAll('.stat-number');
                numbers.forEach(number => {
                    const finalValue = parseInt(number.textContent);
                    let currentValue = 0;
                    const increment = finalValue / 50;
                    
                    const timer = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= finalValue) {
                            currentValue = finalValue;
                            clearInterval(timer);
                        }
                        number.textContent = Math.floor(currentValue);
                    }, 30);
                });
                
                // 添加平滑滚动
                const links = document.querySelectorAll('a[href^="#"]');
                links.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const target = document.querySelector(this.getAttribute('href'));
                        if (target) {
                            target.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                        }
                    });
                });
            });
            
            // 添加打印功能
            function printReport() {
                window.print();
            }
            
            // 添加导出功能（简化版）
            function exportReport() {
                const content = document.documentElement.outerHTML;
                const blob = new Blob([content], { type: 'text/html' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'investment_report.html';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        """


# 保持向后兼容性的函数
def generate_html_report(result):
    """
    生成精美的HTML分析报告（改进版）
    """
    try:
        # 预处理数据，确保分析师名称为中文
        from .analyst_name_mapper import preprocess_data_for_html
        processed_result = preprocess_data_for_html(result)
        
        # 优先使用功能更强大的改进版生成器
        generator = ImprovedHTMLReportGenerator()
        return generator.generate_report(processed_result)
    except Exception as e:
        print(f"使用改进版生成器失败: {e}")
        try:
            # 预处理数据
            from .analyst_name_mapper import preprocess_data_for_html
            processed_result = preprocess_data_for_html(result)
            
            # 备用方案：使用简化版报告生成器
            from .simple_html_report import generate_simple_html_report
            return generate_simple_html_report(processed_result)
        except Exception as e2:
            print(f"使用简化版生成器也失败: {e2}")
            return generate_error_html(f"报告生成失败: {str(e)}")


def get_css_styles():
    """获取CSS样式"""
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
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .header .timestamp {
            font-size: 0.9em;
            margin-top: 15px;
            opacity: 0.8;
        }
        
        .header .stock-info {
            font-size: 1.1em;
            margin-top: 10px;
            opacity: 0.9;
        }
        
        .section {
            padding: 25px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        
        /* 指标网格布局 */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        /* 投资建议样式 */
        .recommendation {
            background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #f39c12;
            margin: 20px 0;
        }
        
        .recommendation.buy {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
            border-color: #27ae60;
        }
        
        .recommendation.sell {
            background: linear-gradient(135deg, #ffeaea 0%, #fff0f0 100%);
            border-color: #e74c3c;
        }
        
        .recommendation.hold {
            background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%);
            border-color: #f39c12;
        }
        
        .recommendation h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        /* 策略评分 */
        .strategy-scores {
            margin-top: 20px;
        }
        
        .strategy-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .strategy-name {
            font-weight: 500;
        }
        
        .strategy-score {
            font-weight: bold;
            color: #3498db;
        }
        
        /* 价格变化颜色 */
        .price-up {
            color: #dc3545 !important;
            font-weight: bold;
        }
        
        .price-down {
            color: #28a745 !important;
            font-weight: bold;
        }
        
        .price-neutral {
            color: #6c757d !important;
            font-weight: bold;
        }
        
        /* 洞察列表 */
        .insights {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .insights ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .insights li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        
        .insights li:before {
            content: "💡";
            position: absolute;
            left: 0;
        }
        
        .executive-summary {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .bullish { color: #27ae60; }
        .bearish { color: #e74c3c; }
        .neutral { color: #f39c12; }
        
        .decisions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .decision-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .decision-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        
        .decision-header {
            padding: 20px;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .decision-header.buy { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .decision-header.sell { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .decision-header.hold { background: linear-gradient(135deg, #f39c12, #e67e22); }
        
        .decision-body {
            padding: 20px;
        }
        
        .decision-detail {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        .decision-detail:last-child {
            border-bottom: none;
        }
        
        .detail-label {
            font-weight: bold;
            color: #555;
        }
        
        .detail-value {
            color: #333;
        }
        
        .confidence-bar {
            background: #ecf0f1;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .confidence-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.8s ease;
        }
        
        .analysts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .analyst-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }
        
        .analyst-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .analyst-signals {
            space-y: 10px;
        }
        
        .signal-item {
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .signal-ticker {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .signal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        }
        
        .signal-badge.bullish {
            background: #d5f4e6;
            color: #27ae60;
        }
        
        .signal-badge.bearish {
            background: #fdeaea;
            color: #e74c3c;
        }
        
        .signal-badge.neutral {
            background: #fef9e7;
            color: #f39c12;
        }
        
        .reasoning {
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }
        
        .confidence-text {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .reasoning-preview {
            font-size: 0.85em;
            color: #777;
            margin-top: 8px;
            line-height: 1.4;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .disclaimer {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }
        
        .disclaimer strong {
            color: #d63031;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .animate-fade-in {
            animation: fadeInUp 0.6s ease forwards;
        }
    """


def generate_header(stock_info=None):
    """生成报告头部"""
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    stock_info_html = ""
    if stock_info:
        stock_info_html = f'<div class="stock-info">{stock_info}</div>'
    
    return f"""
    <div class="header">
        <h1>AI基金大师投资分析报告</h1>
        <div class="subtitle">智能投资决策 · 多维度分析 · 风险控制</div>
        {stock_info_html}
        <div class="timestamp">生成时间: {current_time}</div>
    </div>
    """


def generate_executive_summary(decisions):
    """生成执行摘要"""
    if not decisions:
        return ""
    
    # 统计决策分布
    action_counts = {"buy": 0, "sell": 0, "hold": 0, "short": 0, "cover": 0}
    total_confidence = 0
    total_decisions = len(decisions)
    
    for decision in decisions.values():
        action = decision.get("action", "hold").lower()
        if action in action_counts:
            action_counts[action] += 1
        confidence = decision.get("confidence", 0)
        total_confidence += confidence
    
    avg_confidence = total_confidence / total_decisions if total_decisions > 0 else 0
    
    return f"""
    <div class="section">
        <h2>📋 执行摘要</h2>
        <div class="executive-summary animate-fade-in">
            <p>基于多位AI投资专家的综合分析，我们对 <strong>{total_decisions}</strong> 只股票进行了全面评估.</p>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number bullish">{action_counts['buy']}</div>
                    <div class="stat-label">买入建议</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number bearish">{action_counts['sell']}</div>
                    <div class="stat-label">卖出建议</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number neutral">{action_counts['hold']}</div>
                    <div class="stat-label">持有建议</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_confidence:.1f}%</div>
                    <div class="stat-label">平均信心度</div>
                </div>
            </div>
        </div>
        
        <div class="disclaimer">
            <strong>⚠️ 风险提示:</strong> 本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议.投资有风险，决策需谨慎.请根据自身情况做出投资决定.
        </div>
    </div>
    """


def generate_investment_decisions(decisions):
    """生成投资决策部分"""
    if not decisions:
        return ""
    
    decision_cards = ""
    for ticker, decision in decisions.items():
        action = decision.get("action", "hold").lower()
        quantity = decision.get("quantity", 0)
        confidence = decision.get("confidence", 0)
        reasoning = decision.get("reasoning", "无详细说明")
        
        # 获取动作的中文描述
        action_map = {
            "buy": "买入",
            "sell": "卖出", 
            "hold": "持有",
            "short": "做空",
            "cover": "平仓"
        }
        action_text = action_map.get(action, action)
        
        # 确定置信度颜色
        if confidence >= 70:
            confidence_color = "#27ae60"
        elif confidence >= 40:
            confidence_color = "#f39c12"
        else:
            confidence_color = "#e74c3c"
        
        decision_cards += f"""
        <div class="decision-card animate-fade-in">
            <div class="decision-header {action}">
                <span>📈 {ticker}</span>
                <span style="float: right;">{action_text}</span>
            </div>
            <div class="decision-body">
                <div class="decision-detail">
                    <span class="detail-label">交易数量:</span>
                    <span class="detail-value">{quantity:,} 股</span>
                </div>
                <div class="decision-detail">
                    <span class="detail-label">信心度:</span>
                    <span class="detail-value">{confidence:.1f}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {confidence}%; background: {confidence_color};"></div>
                </div>
                <div class="decision-detail">
                    <span class="detail-label">分析理由:</span>
                </div>
                <div class="reasoning">{reasoning}</div>
            </div>
        </div>
        """
    
    return f"""
    <div class="section">
        <h2>💰 投资决策详情</h2>
        <div class="decisions-grid">
            {decision_cards}
        </div>
    </div>
    """


def generate_analyst_analysis(analyst_signals):
    """生成分析师分析部分"""
    if not analyst_signals:
        return ""
    
    # 使用统一的分析师名称映射器
    from .analyst_name_mapper import get_analyst_chinese_name
    
    analyst_cards = ""
    for analyst_id, signals in analyst_signals.items():
        # 获取分析师中文名称
        analyst_name = get_analyst_chinese_name(analyst_id)
        
        signal_items = ""
        for ticker, signal_data in signals.items():
            # 多重安全检查
            if not signal_data or not isinstance(signal_data, dict):
                continue
                
            # 安全获取每个字段，默认值处理None情况
            signal = signal_data.get("signal") if signal_data.get("signal") is not None else "neutral"
            confidence = signal_data.get("confidence") if signal_data.get("confidence") is not None else 0
            reasoning = signal_data.get("reasoning") if signal_data.get("reasoning") is not None else "无详细分析"
            
            # 确保数据类型正确
            try:
                confidence = float(confidence) if confidence is not None else 0.0
            except (ValueError, TypeError):
                confidence = 0.0
                
            if not isinstance(signal, str):
                signal = "neutral"
                
            if not isinstance(reasoning, str):
                reasoning = "无详细分析"
            
            signal_map = {
                "bullish": "看涨",
                "bearish": "看跌", 
                "neutral": "中性"
            }
            signal_text = signal_map.get(signal, signal)
            
            signal_items += f"""
            <div class="signal-item">
                <span class="signal-ticker">{ticker}</span>
                <span class="signal-badge {signal}">{signal_text}</span>
                <div class="confidence-text">信心度: {confidence:.1f}%</div>
                <div class="reasoning-preview">{str(reasoning)[:100]}{'...' if len(str(reasoning)) > 100 else ''}</div>
            </div>
            """
        
        # 如果没有有效的信号数据，跳过这个分析师
        if not signal_items:
            continue
            
        analyst_cards += f"""
        <div class="analyst-card animate-fade-in">
            <div class="analyst-name">{analyst_name}</div>
            <div class="analyst-signals">
                {signal_items}
            </div>
        </div>
        """
    
    return f"""
    <div class="section">
        <h2>🧠 AI分析师观点</h2>
        <div class="analysts-grid">
            {analyst_cards}
        </div>
    </div>
    """


def generate_footer():
    """生成报告底部"""
    return """
    <div class="footer">
        <p>🚀 AI基金大师  | 智能投资，理性决策</p>
        <p style="margin-top: 10px; font-size: 0.8em; opacity: 0.8;">
            本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议.投资决策请结合专业建议和个人情况.
        </p>
    </div>
    """


def generate_error_html(error_message):
    """生成错误页面HTML"""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>分析报告 - 错误</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .error-container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }}
        .error-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        .error-title {{
            color: #e74c3c;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        .error-message {{
            color: #666;
            line-height: 1.6;
        }}
    </style>

    <style>
        .analyst-text {
            max-height: 100px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .analyst-text.expanded {
            max-height: none;
        }
        .expand-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            margin-top: 5px;
            cursor: pointer;
            border-radius: 3px;
            font-size: 12px;
        }
        .expand-btn:hover {
            background: #0056b3;
        }
    </style>
    <script>
        function toggleAnalystText(button) {{{{
            const textDiv = button.previousElementSibling;
            const isExpanded = textDiv.classList.contains('expanded');
            
            if (isExpanded) {{{{
                textDiv.classList.remove('expanded');
                button.textContent = '展开';
            }}}} else {{{{
                textDiv.classList.add('expanded');
                button.textContent = '收起';
            }}}}
        }}}}
    </script>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-title">报告生成失败</div>
        <div class="error-message">{error_message}</div>
    </div>
</body>
</html>
    """


def get_javascript():
    """获取JavaScript代码"""
    return """
        // 页面加载动画
        document.addEventListener('DOMContentLoaded', function() {
            const elements = document.querySelectorAll('.animate-fade-in');
            elements.forEach((element, index) => {
                setTimeout(() => {
                    element.style.opacity = '0';
                    element.style.transform = 'translateY(30px)';
                    element.style.transition = 'all 0.6s ease';
                    
                    setTimeout(() => {
                        element.style.opacity = '1';
                        element.style.transform = 'translateY(0)';
                    }, 100);
                }, index * 200);
            });
        });
        
        // 置信度条动画
        document.addEventListener('DOMContentLoaded', function() {
            const confidenceBars = document.querySelectorAll('.confidence-fill');
            confidenceBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 500);
            });
        });
    """