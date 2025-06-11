import os
import json
import webbrowser
import locale
from datetime import datetime
from .analysts import ANALYST_ORDER


def sort_agent_signals(signals):
    """Sort agent signals in a consistent order."""
    # Create order mapping from ANALYST_ORDER
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    analyst_order["Risk Management"] = len(ANALYST_ORDER)  # Add Risk Management at the end

    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def detect_gui_language():
    """检测GUI界面语言设置"""
    # 第一优先级：检查环境变量 GUI_LANGUAGE（由分析进程设置）
    env_language = os.environ.get("GUI_LANGUAGE")
    if env_language and env_language in ["en", "zh"]:
        return env_language
    
    try:
        # 尝试读取GUI配置文件 - 修复：使用正确的配置文件名
        config_files = ["hedge_fund_config.json", "gui_config.json"]
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    language = config.get('language', 'en')
                    if language:  # 如果找到有效语言设置，直接返回
                        return language
    except:
        pass
    
    # 回退到系统语言检测
    try:
        # 检查环境变量
        lang_vars = ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']
        for var in lang_vars:
            lang = os.environ.get(var, '')
            if lang and ('zh' in lang.lower() or 'chinese' in lang.lower()):
                return "zh"
        
        # 使用locale模块
        try:
            locale.setlocale(locale.LC_ALL, '')
            system_locale = locale.getlocale()[0]
        except:
            try:
                system_locale = locale.getdefaultlocale()[0]
            except:
                system_locale = None
                
        if system_locale:
            system_locale = system_locale.lower()
            if ('zh' in system_locale or 'chinese' in system_locale or 
                'cn' in system_locale or 'taiwan' in system_locale):
                return "zh"
                
        # Windows系统特殊检测
        if os.name == 'nt':
            try:
                import ctypes
                lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                chinese_lang_ids = [1028, 2052, 3076, 4100, 5124]
                if lang_id in chinese_lang_ids:
                    return "zh"
            except:
                pass
                
    except Exception:
        pass
    
    return "en"  # 默认英文


def get_translations():
    """获取多语言翻译"""
    return {
        "en": {
            "trading_analysis_report": "Trading Analysis Report",
            "comprehensive_ai_driven_analysis": "Comprehensive AI-Driven Market Analysis",
            "analysis_completed_successfully": "Analysis completed successfully for",
            "tickers": "ticker(s)",
            "portfolio_summary": "Portfolio Summary",
            "trading_decisions_overview": "Trading Decisions Overview",
            "total_tickers": "Total Tickers",
            "average_confidence": "Average Confidence",
            "orders": "Orders",
            "portfolio_strategy": "Portfolio Strategy",
            "analysis": "Analysis",
            "agent_signals": "Agent Signals",
            "agent": "Agent",
            "signal": "Signal",
            "confidence": "Confidence",
            "reasoning": "Reasoning",
            "trading_decision": "Trading Decision",
            "action": "Action",
            "quantity": "Quantity",
            "report_generated_on": "Report generated on",
            "powered_by": "Powered by AI Hedge Fund Analysis System",
            "backtest_results_report": "Backtest Results Report",
            "historical_performance_analysis": "Historical Performance Analysis",
            "backtest_completed_with": "Backtest completed with",
            "transactions": "transactions",
            "portfolio_performance_summary": "Portfolio Performance Summary",
            "final_portfolio_status": "Final Portfolio Status",
            "cash_balance": "Cash Balance",
            "position_value": "Position Value",
            "total_value": "Total Value",
            "return": "Return",
            "sharpe_ratio": "Sharpe Ratio",
            "sortino_ratio": "Sortino Ratio",
            "max_drawdown": "Max Drawdown",
            "trading_history": "Trading History",
            "date": "Date",
            "ticker": "Ticker",
            "price": "Price",
            "shares": "Shares",
            "position_value_short": "Position Value",
            "bullish": "Bullish",
            "bearish": "Bearish",
            "neutral": "Neutral",
            "powered_by_backtest": "Powered by AI Hedge Fund Backtesting System"
        },
        "zh": {
            "trading_analysis_report": "交易分析报告",
            "comprehensive_ai_driven_analysis": "全面的AI驱动市场分析",
            "analysis_completed_successfully": "分析成功完成",
            "tickers": "只股票",
            "portfolio_summary": "投资组合摘要",
            "trading_decisions_overview": "交易决策概览",
            "total_tickers": "总股票数",
            "average_confidence": "平均置信度",
            "orders": "订单",
            "portfolio_strategy": "投资组合策略",
            "analysis": "分析",
            "agent_signals": "分析师信号",
            "agent": "分析师",
            "signal": "信号",
            "confidence": "置信度",
            "reasoning": "推理",
            "trading_decision": "交易决策",
            "action": "操作",
            "quantity": "数量",
            "report_generated_on": "报告生成时间",
            "powered_by": "由267278466@qq.com提供支持",
            "backtest_results_report": "回测结果报告",
            "historical_performance_analysis": "历史表现分析",
            "backtest_completed_with": "回测完成，共有",
            "transactions": "笔交易",
            "portfolio_performance_summary": "投资组合表现摘要",
            "final_portfolio_status": "最终投资组合状态",
            "cash_balance": "现金余额",
            "position_value": "持仓价值",
            "total_value": "总价值",
            "return": "收益率",
            "sharpe_ratio": "夏普比率",
            "sortino_ratio": "索提诺比率",
            "max_drawdown": "最大回撤",
            "trading_history": "交易历史",
            "date": "日期",
            "ticker": "股票代码",
            "price": "价格",
            "shares": "股数",
            "position_value_short": "持仓价值",
            "bullish": "看涨",
            "bearish": "看跌",
            "neutral": "中性",
            "powered_by_backtest": "由267278466@qq.com提供支持"
        }
    }


def generate_html_style():
    """Generate CSS styles for HTML output with business theme"""
    return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .header {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            padding: 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: 1px;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            font-weight: 300;
        }
        
        .content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 40px;
            background: white;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid #e8e8e8;
        }
        
        .section-title {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
            position: relative;
            font-weight: 400;
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 50px;
            height: 2px;
            background: #e74c3c;
        }
        
        .ticker-section {
            border-left: 4px solid #3498db;
            margin-bottom: 30px;
        }
        
        .ticker-title {
            color: #2c3e50;
            font-size: 1.5em;
            margin-bottom: 15px;
            font-weight: 500;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        
        th {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 500;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #f1f3f4;
            color: #2c3e50;
            font-size: 0.95em;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e3f2fd;
            transform: translateY(-1px);
            transition: all 0.2s ease;
        }
        
        .signal-bullish {
            color: #27ae60;
            font-weight: 600;
            background: #d5f4e6;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .signal-bearish {
            color: #e74c3c;
            font-weight: 600;
            background: #fdeaea;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .signal-neutral {
            color: #f39c12;
            font-weight: 600;
            background: #fef9e7;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .action-buy, .action-cover {
            color: #27ae60;
            font-weight: 600;
            background: #d5f4e6;
            padding: 4px 12px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .action-sell, .action-short {
            color: #e74c3c;
            font-weight: 600;
            background: #fdeaea;
            padding: 4px 12px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .action-hold {
            color: #f39c12;
            font-weight: 600;
            background: #fef9e7;
            padding: 4px 12px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .ticker {
            color: #2980b9;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .confidence {
            text-align: right;
            font-weight: 600;
            color: #34495e;
        }
        
        .positive {
            color: #27ae60;
            font-weight: 600;
        }
        
        .negative {
            color: #e74c3c;
            font-weight: 600;
        }
        
        .neutral {
            color: #f39c12;
            font-weight: 600;
        }
        
        .reasoning {
            max-width: 400px;
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.5;
            color: #34495e;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }
        
        .portfolio-summary {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
            box-shadow: 0 6px 20px rgba(52, 73, 94, 0.3);
        }
        
        .portfolio-summary h3 {
            margin-bottom: 20px;
            font-size: 1.4em;
            font-weight: 400;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .summary-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        
        .summary-label {
            font-weight: 500;
            opacity: 0.9;
            font-size: 0.9em;
            margin-bottom: 5px;
            display: block;
        }
        
        .summary-value {
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .decision-table {
            background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
            border-radius: 6px;
            padding: 2px;
        }
        
        .decision-table table {
            background: white;
            margin: 0;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border: 1px solid #e8e8e8;
        }
        
        .metric-title {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .timestamp {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        
        .success-banner {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 6px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .warning-banner {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 6px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 8px;
            }
            
            .content {
                padding: 20px;
            }
            
            .section {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            table {
                font-size: 0.85em;
            }
            
            th, td {
                padding: 8px 4px;
            }
        }
    </style>
    """


def save_trading_output_html(result: dict, filename: str = None, auto_open: bool = True) -> str:
    """
    Generate HTML formatted trading results and save to file.

    Args:
        result (dict): Dictionary containing decisions and analyst signals for multiple tickers
        filename (str): Optional filename for the HTML output
        auto_open (bool): Whether to automatically open the HTML file in browser
        
    Returns:
        str: Path to the generated HTML file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_analysis_{timestamp}.html"
    
    # 检测语言
    language = detect_gui_language()
    translations = get_translations()[language]
    
    decisions = result.get("decisions")
    if not decisions:
        html_content = f"""
        <!DOCTYPE html>
        <html lang="{language}">
        <head>
            <title>{translations['trading_analysis_report']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        """ + generate_html_style() + """
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>""" + translations['trading_analysis_report'] + """</h1>
                    <p class="subtitle">""" + translations['comprehensive_ai_driven_analysis'] + """</p>
                </div>
                <div class="content">
                    <div class="warning-banner">
                        """ + translations['analysis_completed_successfully'] + """ 0 """ + translations['tickers'] + """
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        html_content = generate_trading_html(result, language, translations)
    
    # Save to file
    abs_path = os.path.abspath(filename)
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Auto-open in browser
    if auto_open:
        try:
            webbrowser.open(f'file://{abs_path}')
            print(f"Trading analysis saved to: {abs_path}")
            print("Opening in default browser...")
        except Exception as e:
            print(f"Trading analysis saved to: {abs_path}")
            print(f"Could not auto-open browser: {e}")
    else:
        print(f"Trading analysis saved to: {abs_path}")
    
    return abs_path


def generate_trading_html(result: dict, language: str, translations: dict) -> str:
    """Generate complete HTML content for trading results with improved layout"""
    decisions = result.get("decisions", {})
    analyst_signals = result.get("analyst_signals", {})
    
    # Get portfolio manager reasoning if available
    portfolio_reasoning = ""
    for ticker, decision in decisions.items():
        if decision.get("reasoning"):
            portfolio_reasoning = decision.get("reasoning")
            break
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <title>{translations['trading_analysis_report']}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + generate_html_style() + """
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>""" + translations['trading_analysis_report'] + """</h1>
                <p class="subtitle">""" + translations['comprehensive_ai_driven_analysis'] + """</p>
            </div>
            <div class="content">
    """
    
    # Success banner
    html_content += f"""
                <div class="success-banner">
                    {translations['analysis_completed_successfully']} {len(decisions)} {translations['tickers']}
                </div>
    """
    
    # Portfolio Summary (moved to top for better visibility)
    html_content += f"""
                <div class="section">
                    <h2 class="section-title">{translations['portfolio_summary']}</h2>
                    <div class="portfolio-summary">
                        <h3>{translations['trading_decisions_overview']}</h3>
                        <div class="summary-grid">
    """
    
    # Count actions
    action_counts = {}
    total_confidence = 0
    for ticker, decision in decisions.items():
        action = decision.get("action", "").upper()
        action_counts[action] = action_counts.get(action, 0) + 1
        total_confidence += decision.get("confidence", 0)
    
    avg_confidence = total_confidence / len(decisions) if decisions else 0
    
    html_content += f"""
                            <div class="summary-item">
                                <span class="summary-label">{translations['total_tickers']}</span>
                                <div class="summary-value">{len(decisions)}</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">{translations['average_confidence']}</span>
                                <div class="summary-value">{avg_confidence:.1f}%</div>
                            </div>
    """
    
    for action, count in action_counts.items():
        html_content += f"""
                            <div class="summary-item">
                                <span class="summary-label">{action} {translations['orders']}</span>
                                <div class="summary-value">{count}</div>
                            </div>
        """
    
    html_content += """
                        </div>
    """
    
    if portfolio_reasoning:
        html_content += f"""
                        <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 6px;">
                            <strong>{translations['portfolio_strategy']}:</strong><br>
                            {portfolio_reasoning}
                        </div>
        """
    
    html_content += """
                    </div>
                </div>
    """
    
    # Individual ticker analysis
    for ticker, decision in decisions.items():
        html_content += f"""
                <div class="section ticker-section">
                    <h2 class="ticker-title">{ticker} {translations['analysis']}</h2>
                    
                    <h3>{translations['agent_signals']}</h3>
        """
        
        # Prepare analyst signals table
        html_content += f"""
                    <table>
                        <thead>
                            <tr>
                                <th>{translations['agent']}</th>
                                <th>{translations['signal']}</th>
                                <th>{translations['confidence']}</th>
                                <th>{translations['reasoning']}</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        table_data = []
        for agent, signals in analyst_signals.items():
            if ticker not in signals or agent == "risk_management_agent":
                continue
                
            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()
            confidence = signal.get("confidence", 0)
            
            # Get reasoning
            reasoning_str = ""
            if "reasoning" in signal and signal["reasoning"]:
                reasoning = signal["reasoning"]
                if isinstance(reasoning, str):
                    reasoning_str = reasoning
                elif isinstance(reasoning, dict):
                    reasoning_str = json.dumps(reasoning, indent=2)
                else:
                    reasoning_str = str(reasoning)
            
            table_data.append((agent_name, signal_type, confidence, reasoning_str))
        
        # Sort signals
        table_data = sort_agent_signals(table_data)
        
        for agent_name, signal_type, confidence, reasoning in table_data:
            signal_class = f"signal-{signal_type.lower()}"
            html_content += f"""
                            <tr>
                                <td><strong>{agent_name}</strong></td>
                                <td><span class="{signal_class}">{signal_type}</span></td>
                                <td class="confidence">{confidence}%</td>
                                <td class="reasoning">{reasoning}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
        """
        
        # Trading Decision
        action = decision.get("action", "").upper()
        action_class = f"action-{action.lower()}"
        reasoning = decision.get("reasoning", "")
        
        html_content += f"""
                    <h3>{translations['trading_decision']}</h3>
                    <div class="decision-table">
                        <table>
                            <tbody>
                                <tr>
                                    <td><strong>{translations['action']}</strong></td>
                                    <td><span class="{action_class}">{action}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>{translations['quantity']}</strong></td>
                                    <td><strong>{decision.get('quantity')}</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>{translations['confidence']}</strong></td>
                                    <td class="confidence"><strong>{decision.get('confidence'):.1f}%</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>{translations['reasoning']}</strong></td>
                                    <td class="reasoning">{reasoning}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
        """
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content += f"""
                <div class="timestamp">
                    {translations['report_generated_on']}: {timestamp}<br>
                    {translations['powered_by']}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def save_backtest_results_html(table_rows: list, filename: str = None, auto_open: bool = True) -> str:
    """Generate HTML formatted backtest results and save to file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.html"
    
    # 检测语言
    language = detect_gui_language()
    translations = get_translations()[language]
    
    html_content = generate_backtest_html(table_rows, language, translations)
    
    # Save to file
    abs_path = os.path.abspath(filename)
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Auto-open in browser
    if auto_open:
        try:
            webbrowser.open(f'file://{abs_path}')
            print(f"Backtest results saved to: {abs_path}")
            print("Opening in default browser...")
        except Exception as e:
            print(f"Backtest results saved to: {abs_path}")
            print(f"Could not auto-open browser: {e}")
    else:
        print(f"Backtest results saved to: {abs_path}")
    
    return abs_path


def generate_backtest_html(table_rows: list, language: str, translations: dict) -> str:
    """Generate complete HTML content for backtest results with improved layout"""
    # Split rows into ticker rows and summary rows
    ticker_rows = []
    summary_rows = []

    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <title>{translations['backtest_results_report']}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + generate_html_style() + """
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>""" + translations['backtest_results_report'] + """</h1>
                <p class="subtitle">""" + translations['historical_performance_analysis'] + """</p>
            </div>
            <div class="content">
    """
    
    # Display latest portfolio summary
    if summary_rows:
        latest_summary = summary_rows[-1]
        
        # Extract values (remove HTML tags and commas)
        try:
            cash_str = latest_summary[7].split("$")[1].split("</span>")[0].replace(",", "") if "$" in str(latest_summary[7]) else "0"
            position_str = latest_summary[6].split("$")[1].split("</span>")[0].replace(",", "") if "$" in str(latest_summary[6]) else "0"
            total_str = latest_summary[8].split("$")[1].split("</span>")[0].replace(",", "") if "$" in str(latest_summary[8]) else "0"
            
            cash_val = float(cash_str)
            position_val = float(position_str)
            total_val = float(total_str)
        except (ValueError, IndexError):
            cash_val = position_val = total_val = 0
        
        html_content += f"""
                <div class="success-banner">
                    {translations['backtest_completed_with']} {len(ticker_rows)} {translations['transactions']}
                </div>
                
                <div class="section">
                    <h2 class="section-title">{translations['portfolio_performance_summary']}</h2>
                    <div class="portfolio-summary">
                        <h3>{translations['final_portfolio_status']}</h3>
                        <div class="summary-grid">
                            <div class="summary-item">
                                <span class="summary-label">{translations['cash_balance']}</span>
                                <div class="summary-value">${cash_val:,.2f}</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">{translations['position_value']}</span>
                                <div class="summary-value">${position_val:,.2f}</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">{translations['total_value']}</span>
                                <div class="summary-value">${total_val:,.2f}</div>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">{translations['return']}</span>
                                <div class="summary-value">{latest_summary[9]}</div>
                            </div>
        """
        
        # Add performance metrics if available
        if len(latest_summary) > 10 and latest_summary[10]: 
            html_content += f"""
                            <div class="summary-item">
                                <span class="summary-label">{translations['sharpe_ratio']}</span>
                                <div class="summary-value">{latest_summary[10]}</div>
                            </div>
            """
        if len(latest_summary) > 11 and latest_summary[11]:
            html_content += f"""
                            <div class="summary-item">
                                <span class="summary-label">{translations['sortino_ratio']}</span>
                                <div class="summary-value">{latest_summary[11]}</div>
                            </div>
            """
        if len(latest_summary) > 12 and latest_summary[12]:
            html_content += f"""
                            <div class="summary-item">
                                <span class="summary-label">{translations['max_drawdown']}</span>
                                <div class="summary-value">{latest_summary[12]}</div>
                            </div>
            """
        
        html_content += """
                        </div>
                    </div>
                </div>
        """
    
    # Trading history table
    html_content += f"""
                <div class="section">
                    <h2 class="section-title">{translations['trading_history']}</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>{translations['date']}</th>
                                <th>{translations['ticker']}</th>
                                <th>{translations['action']}</th>
                                <th>{translations['quantity']}</th>
                                <th>{translations['price']}</th>
                                <th>{translations['shares']}</th>
                                <th>{translations['position_value_short']}</th>
                                <th>{translations['bullish']}</th>
                                <th>{translations['bearish']}</th>
                                <th>{translations['neutral']}</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for row in ticker_rows:
        # Clean row data (remove any existing HTML/color codes)
        clean_row = []
        for cell in row:
            if isinstance(cell, str):
                # Remove any existing color codes or HTML tags
                clean_cell = cell
                # Basic cleanup - this might need adjustment based on actual data format
                import re
                clean_cell = re.sub(r'\x1b\[[0-9;]*m', '', clean_cell)  # Remove ANSI codes
                clean_cell = re.sub(r'<[^>]+>', '', clean_cell)  # Remove HTML tags
                clean_row.append(clean_cell)
            else:
                clean_row.append(str(cell))
        
        # Apply styling based on content
        if len(clean_row) >= 10:
            date, ticker, action, quantity, price, shares, position_value, bullish, bearish, neutral = clean_row[:10]
            
            action_class = ""
            if action.upper() in ["BUY", "COVER"]:
                action_class = "action-buy"
            elif action.upper() in ["SELL", "SHORT"]:
                action_class = "action-sell"
            elif action.upper() == "HOLD":
                action_class = "action-hold"
            
            html_content += f"""
                            <tr>
                                <td>{date}</td>
                                <td class="ticker">{ticker}</td>
                                <td><span class="{action_class}">{action.upper()}</span></td>
                                <td>{quantity}</td>
                                <td>${price}</td>
                                <td>{shares}</td>
                                <td class="neutral">{position_value}</td>
                                <td class="positive">{bullish}</td>
                                <td class="negative">{bearish}</td>
                                <td class="signal-neutral">{neutral}</td>
                            </tr>
            """
    
    html_content += """
                        </tbody>
                    </table>
                </div>
    """
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content += f"""
                <div class="timestamp">
                    {translations['report_generated_on']}: {timestamp}<br>
                    {translations['powered_by_backtest']}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list:
    """Format a row for the backtest results table (now returns clean data for HTML processing)"""
    
    if is_summary:
        return_class = "positive" if return_pct >= 0 else "negative"
        return [
            date,
            "PORTFOLIO SUMMARY",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Shares
            f"${total_position_value:,.2f}",  # Total Position Value
            f"${cash_balance:,.2f}",  # Cash Balance
            f"${total_value:,.2f}",  # Total Value
            f'<span class="{return_class}">{return_pct:+.2f}%</span>',  # Return
            f"{sharpe_ratio:.2f}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{sortino_ratio:.2f}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{abs(max_drawdown):.2f}%" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        return [
            date,
            ticker,
            action.upper(),
            f"{quantity:,.0f}",
            f"{price:,.2f}",
            f"{shares_owned:,.0f}",
            f"${position_value:,.2f}",
            str(bullish_count),
            str(bearish_count),
            str(neutral_count),
        ]


# Legacy function names for backward compatibility
def print_trading_output(result: dict) -> None:
    """
    Legacy function - now generates HTML file and opens in browser automatically.
    """
    save_trading_output_html(result, auto_open=True)


def print_backtest_results(table_rows: list) -> None:
    """
    Legacy function - now generates HTML file and opens in browser automatically.
    """
    save_backtest_results_html(table_rows, auto_open=True)
