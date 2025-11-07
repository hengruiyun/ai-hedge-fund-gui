# -*- coding: utf-8 -*-
"""
简化版HTML报告生成器
融合mini.py的设计优点，提供更清晰的报告结构
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


def generate_simple_html_report(result: Dict[str, Any]) -> str:
    """
    生成简化版HTML报告
    融合mini.py的设计理念
    """
    try:
        # 预处理数据，确保分析师名称为中文
        from .analyst_name_mapper import preprocess_data_for_html
        processed_result = preprocess_data_for_html(result)
        
        decisions = processed_result.get('decisions', {})
        analyst_signals = processed_result.get('analyst_signals', {})
        
        # 提取股票信息
        stock_info = ""
        if decisions:
            tickers = list(decisions.keys())
            if len(tickers) == 1:
                stock_info = f"分析标的: {tickers[0]}"
            else:
                stock_info = f"分析标的: {', '.join(tickers[:3])}{'等' if len(tickers) > 3 else ''}"
        
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI基金大师投资分析报告</title>
            <style>{get_enhanced_css_styles()}</style>
        </head>
        <body>
            <div class="container">
                {generate_enhanced_header(stock_info)}
                {generate_summary_section(decisions, analyst_signals)}
                {generate_recommendation_section(decisions)}
                {generate_indicators_section(analyst_signals)}
                {generate_master_analysis_section(analyst_signals)}
                {generate_enhanced_footer()}
            </div>
            <script>{get_enhanced_javascript()}</script>
        </body>
        </html>
        """
    except Exception as e:
        return generate_enhanced_error_html(f"生成报告时发生错误: {str(e)}")


def get_enhanced_css_styles() -> str:
    """
    获取增强版CSS样式
    融合mini.py的简洁设计
    """
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
        
        .header .stock-info {
            font-size: 1.1em;
            margin-top: 10px;
            opacity: 0.9;
            background: rgba(255,255,255,0.1);
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-block;
        }
        
        .header .timestamp {
            font-size: 0.9em;
            margin-top: 15px;
            opacity: 0.8;
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
        
        /* 摘要卡片 */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .summary-number {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .summary-label {
            font-size: 0.9em;
            color: #666;
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
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
            margin: 15px 0;
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
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .strategy-name {
            font-weight: 500;
        }
        
        .strategy-score {
            font-weight: bold;
            color: #3498db;
            background: #e3f2fd;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.9em;
        }
        
        /* 分析师网格 */
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
            transition: transform 0.3s ease;
        }
        
        .analyst-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .analyst-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            text-align: center;
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
        
        .reasoning-container {
            margin-top: 8px;
        }
        
        .reasoning-full {
            color: #777;
            font-size: 0.85em;
            line-height: 1.4;
            margin-top: 8px;
        }
        
        .expand-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            cursor: pointer;
            margin-top: 8px;
            transition: background-color 0.3s ease;
        }
        
        .expand-btn:hover {
            background: #0056b3;
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
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .section {
                padding: 15px;
            }
            
            .summary-grid,
            .metrics-grid,
            .analysts-grid {
                grid-template-columns: 1fr;
            }
        }
    """


def generate_enhanced_header(stock_info: str = "") -> str:
    """
    生成增强版报告头部
    """
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


def generate_summary_section(decisions: Dict[str, Any], analyst_signals: Dict[str, Any]) -> str:
    """
    生成摘要部分
    """
    if not decisions and not analyst_signals:
        return ""
    
    # 统计决策分布
    action_counts = {"buy": 0, "sell": 0, "hold": 0}
    total_confidence = 0
    total_decisions = len(decisions)
    
    for decision in decisions.values():
        action = decision.get("action", "hold").lower()
        if action in action_counts:
            action_counts[action] += 1
        confidence = decision.get("confidence", 0)
        total_confidence += confidence
    
    avg_confidence = total_confidence / total_decisions if total_decisions > 0 else 0
    
    # 统计分析师观点
    analyst_count = len(analyst_signals)
    
    return f"""
    <div class="section">
        <h2>分析摘要</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-number">{action_counts['buy']}</div>
                <div class="summary-label">买入建议</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{action_counts['sell']}</div>
                <div class="summary-label">卖出建议</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{action_counts['hold']}</div>
                <div class="summary-label">持有建议</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{avg_confidence:.1f}%</div>
                <div class="summary-label">平均信心度</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{analyst_count}</div>
                <div class="summary-label">分析师观点</div>
            </div>
        </div>
    </div>
    """


def generate_recommendation_section(decisions: Dict[str, Any]) -> str:
    """
    生成投资建议部分
    """
    if not decisions:
        return ""
    
    html = '<div class="section"><h2>投资建议</h2>'
    
    for ticker, decision in decisions.items():
        action = decision.get('action', 'hold').lower()
        confidence = decision.get('confidence', 0)
        reasoning = decision.get('reasoning', '暂无分析')
        
        action_text = {
            'buy': '买入建议',
            'sell': '卖出建议',
            'hold': '持有建议'
        }.get(action, '持有建议')
        
        html += f"""
        <div class="recommendation {action}">
            <h3>{ticker} - {action_text}</h3>
            <div class="metric-card">
                <div class="metric-label">信心度</div>
                <div class="metric-value">{confidence}%</div>
            </div>
            <div class="insights">
                <p><strong>分析理由:</strong></p>
                <p>{reasoning}</p>
            </div>
        </div>
        """
    
    html += '</div>'
    return html


def generate_indicators_section(analyst_signals: Dict[str, Any]) -> str:
    """
    生成技术指标部分
    """
    if not analyst_signals:
        return ""
    
    # 提取关键指标
    indicators = []
    
    for analyst_id, signals in analyst_signals.items():
        if isinstance(signals, dict):
            for ticker, signal_data in signals.items():
                if isinstance(signal_data, dict):
                    confidence = signal_data.get('confidence', 0)
                    action = signal_data.get('action', 'hold')
                    
                    analyst_name = {
                        'warren_buffett': '巴菲特策略',
                        'peter_lynch': '林奇策略',
                        'technical': '技术分析',
                        'fundamentals': '基本面分析'
                    }.get(analyst_id, analyst_id)
                    
                    indicators.append({
                        'name': analyst_name,
                        'value': f"{confidence:.1f}%",
                        'action': action
                    })
    
    if not indicators:
        return ""
    
    html = '<div class="section"><h2>关键指标</h2><div class="metrics-grid">'
    
    for indicator in indicators[:8]:  # 限制显示数量
        html += f"""
        <div class="metric-card">
            <div class="metric-label">{indicator['name']}</div>
            <div class="metric-value">{indicator['value']}</div>
        </div>
        """
    
    html += '</div></div>'
    return html


def generate_master_analysis_section(analyst_signals: Dict[str, Any]) -> str:
    """
    生成投资大师分析部分
    """
    if not analyst_signals:
        return ""
    
    # 使用统一的分析师名称映射器
    from .analyst_name_mapper import get_analyst_chinese_name
    
    # 计算策略评分
    strategy_scores = []
    for analyst_id, signals in analyst_signals.items():
        # 使用统一的分析师名称映射器
        analyst_name = get_analyst_chinese_name(analyst_id)
        
        if isinstance(signals, dict):
            total_confidence = 0
            count = 0
            for ticker, signal_data in signals.items():
                if isinstance(signal_data, dict):
                    confidence = signal_data.get('confidence', 0)
                    total_confidence += confidence
                    count += 1
            
            if count > 0:
                avg_confidence = total_confidence / count
                strategy_scores.append((analyst_name, avg_confidence))
    
    html = '<div class="section"><h2>投资大师分析</h2>'
    
    # 显示策略评分
    if strategy_scores:
        html += '<div class="strategy-scores"><h3>策略评分排名</h3>'
        strategy_scores.sort(key=lambda x: x[1], reverse=True)
        
        for name, score in strategy_scores:
            html += f"""
            <div class="strategy-item">
                <span class="strategy-name">{name}</span>
                <span class="strategy-score">{score:.1f}分</span>
            </div>
            """
        html += '</div>'
    
    # 显示详细分析
    html += '<div class="analysts-grid">'
    for analyst_id, signals in analyst_signals.items():
        # 使用统一的分析师名称映射器
        analyst_name = get_analyst_chinese_name(analyst_id)
        
        html += f'<div class="analyst-card"><div class="analyst-name">{analyst_name}</div>'
        
        if isinstance(signals, dict):
            for ticker, signal_data in signals.items():
                if isinstance(signal_data, dict):
                    action = signal_data.get('action', 'hold')
                    confidence = signal_data.get('confidence', 0)
                    reasoning = signal_data.get('reasoning', '暂无分析')
                    
                    signal_class = {
                        'buy': 'bullish',
                        'sell': 'bearish',
                        'hold': 'neutral'
                    }.get(action.lower(), 'neutral')
                    
                    action_text = {
                        'buy': '买入',
                        'sell': '卖出',
                        'hold': '持有'
                    }.get(action.lower(), action)
                    
                    reasoning_str = str(reasoning)
                    
                    # 为长文本添加展开功能
                    if len(reasoning_str) > 100:
                        reasoning_preview = reasoning_str[:100] + '...'
                        reasoning_html = f"""
                        <div class="reasoning-container">
                            <div class="reasoning-preview" id="preview_{analyst_id}_{ticker}">{reasoning_preview}</div>
                            <div class="reasoning-full" id="full_{analyst_id}_{ticker}" style="display: none;">{reasoning_str}</div>
                            <button class="expand-btn" onclick="toggleReasoning('{analyst_id}_{ticker}')">展开</button>
                        </div>
                        """
                    else:
                        reasoning_html = f'<div class="reasoning-preview">{reasoning_str}</div>'
                    
                    html += f"""
                    <div class="signal-item">
                        <span class="signal-ticker">{ticker}</span>
                        <span class="signal-badge {signal_class}">{action_text}</span>
                        <div class="confidence-text">信心度: {confidence}%</div>
                        {reasoning_html}
                    </div>
                    """
        
        html += '</div>'
    
    html += '</div></div>'
    return html


def generate_enhanced_footer() -> str:
    """
    生成增强版页脚
    """
    return """
    <div class="footer">
        <p>AI基金大师 | 智能投资，理性决策</p>
        <div class="disclaimer">
            <strong>风险提示:</strong> 本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议。投资有风险，决策需谨慎。请根据自身情况做出投资决定。
        </div>
    </div>
    """


def generate_enhanced_error_html(error_message: str) -> str:
    """
    生成增强版错误页面
    """
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
                color: #e74c3c;
                margin-bottom: 20px;
            }}
            .error-title {{
                font-size: 1.5em;
                color: #2c3e50;
                margin-bottom: 15px;
            }}
            .error-message {{
                color: #666;
                line-height: 1.6;
            }}
        </style>
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


def get_enhanced_javascript() -> str:
    """
    获取增强版JavaScript
    """
    return """
        // 展开/收起分析理由的函数
        function toggleReasoning(id) {
            const previewDiv = document.getElementById('preview_' + id);
            const fullDiv = document.getElementById('full_' + id);
            const button = event.target;
            
            if (fullDiv.style.display === 'none') {
                previewDiv.style.display = 'none';
                fullDiv.style.display = 'block';
                button.textContent = '收起';
            } else {
                previewDiv.style.display = 'block';
                fullDiv.style.display = 'none';
                button.textContent = '展开';
            }
        }
        
        // 添加动画效果
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.metric-card, .analyst-card, .recommendation');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-fade-in');
                    }
                });
            });
            
            cards.forEach(card => {
                observer.observe(card);
            });
        });
        
        // 添加交互效果
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.metric-card, .analyst-card');
            
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-5px)';
                    this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
                });
                
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                    this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                });
            });
        });
    """