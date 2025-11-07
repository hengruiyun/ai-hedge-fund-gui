#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI基金大师GUI界面 - PyQt5简化单线程版本
去除类结构，使用函数式编程，避免多线程问题
"""

import sys
import os
import json
import time
import tempfile
import webbrowser
from datetime import datetime, timedelta
from io import StringIO

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QProgressBar, QGroupBox, QGridLayout, QScrollArea,
    QMessageBox, QFileDialog, QFrame, QSplitter, QDateEdit
)
from PyQt5.QtCore import Qt, QTimer, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 导入原有的功能模块
from src.utils.ollama_utils import (
    is_ollama_installed, 
    is_ollama_server_running, 
    get_locally_available_models,
    start_ollama_server,
    ensure_ollama_and_model
)
from src.tools.api import set_api_interrupt, clear_api_interrupt
from src.utils.html_report import generate_html_report
from src.utils.display import format_trading_output

# 导入核心分析模块
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from src.agents.portfolio_manager import portfolio_management_agent
from src.graph.state import AgentState
from src.utils.analysts import get_analyst_nodes
from src.utils.unified_data_accessor import unified_data_accessor
from src.utils.progress import progress
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Load environment variables from .env file
load_dotenv()

# 全局常量 - 默认模型名称
DEFAULT_MODEL_NAME = "qwen3:0.6b"

# 全局变量存储UI组件和状态
g_widgets = {}
g_state = {
    'config_file': "gui_config.json",
    'current_html_content': None,
    'current_result_data': None,
    'analysis_start_time': None,
    'total_analysts': 0,
    'completed_analysts': 0,
    'original_stdout': sys.stdout,
    'is_analyzing': False,
    'worker_thread': None  # 存储工作线程
}

# 数据缓存字典，按股票代码存储数据
g_data_cache = {}

# 多线程工作类
class AnalysisWorkerThread(QThread):
    """
    分析工作线程 - 用于在后台执行分析任务
    """
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度更新信号
    output_updated = pyqtSignal(str)  # 输出更新信号
    analysis_completed = pyqtSignal(object)  # 分析完成信号
    analysis_failed = pyqtSignal(str)  # 分析失败信号
    
    def __init__(self, analysis_type, **kwargs):
        super().__init__()
        self.analysis_type = analysis_type  # 'smart' 或 'master'
        self.kwargs = kwargs
        self.is_cancelled = False
    
    def cancel(self):
        """取消分析"""
        self.is_cancelled = True
        set_api_interrupt()
    
    def run(self):
        """线程主执行函数"""
        try:
            if self.analysis_type == 'smart':
                self._run_smart_analysis()
            elif self.analysis_type == 'master':
                self._run_master_analysis()
        except Exception as e:
            self.analysis_failed.emit(f"分析过程中发生错误: {str(e)}")
    
    def _run_smart_analysis(self):
        """执行智能分析"""
        try:
            # 获取参数
            config = self.kwargs.get('config', {})
            
            self.progress_updated.emit(10, "配置完成，开始分析...")
            self.output_updated.emit("=== 开始智能分析 ===")
            
            if self.is_cancelled:
                return
            
            # 第一步：获取数据
            self.progress_updated.emit(20, "第一步：获取股票数据...")
            self.output_updated.emit("=== 第一步：获取数据 ===")
            
            # 验证数据获取（使用缓存）
            from src.tools.api import get_prices
            for ticker in config['tickers']:
                if self.is_cancelled:
                    return
                
                try:
                    # 生成缓存键
                    cache_key = f"{ticker}_{config['start_date']}_{config['end_date']}"
                    
                    # 检查缓存
                    if cache_key in g_data_cache:
                        self.output_updated.emit(f"📋 使用缓存数据 {ticker} ({len(g_data_cache[cache_key])} 条记录)")
                    else:
                        # 获取新数据并缓存
                        prices = get_prices(ticker, config['start_date'], config['end_date'])
                        if prices:
                            g_data_cache[cache_key] = prices
                            self.output_updated.emit(f"✓ 成功获取 {ticker} 的价格数据 ({len(prices)} 条记录)")
                        else:
                            self.output_updated.emit(f"⚠ {ticker} 的价格数据为空")
                except Exception as e:
                    self.output_updated.emit(f"✗ 获取 {ticker} 数据失败: {str(e)}")
            
            if self.is_cancelled:
                return
            
            # 第二步：智能分析
            self.progress_updated.emit(40, "第二步：智能分析...")
            self.output_updated.emit("=== 第二步：智能分析 ===")
            
            from src.utils.enhanced_smart_analysis import generate_smart_analysis_report
            smart_analysis_result = generate_smart_analysis_report(
                config['tickers'], 
                config['start_date'], 
                config['end_date'],
                data_cache=g_data_cache
            )
            
            if self.is_cancelled:
                return
            
            self.progress_updated.emit(100, "智能分析完成")
            self.output_updated.emit("=== 智能分析完成 ===")
            
            # 发送完成信号
            self.analysis_completed.emit({
                'type': 'smart',
                'result': smart_analysis_result,
                'config': config
            })
            
        except Exception as e:
            self.analysis_failed.emit(f"智能分析失败: {str(e)}")
    
    def _run_master_analysis(self):
        """执行投资大师分析"""
        try:
            # 获取参数
            tickers = self.kwargs.get('tickers', [])
            start_date = self.kwargs.get('start_date', '')
            end_date = self.kwargs.get('end_date', '')
            portfolio = self.kwargs.get('portfolio', {})
            show_reasoning = self.kwargs.get('show_reasoning', False)
            selected_analysts = self.kwargs.get('selected_analysts', [])
            model_name = self.kwargs.get('model_name', '')
            model_provider = self.kwargs.get('model_provider', '')
            
            self.progress_updated.emit(10, "准备LLM分析")
            self.output_updated.emit("开始投资大师分析...")
            
            if self.is_cancelled:
                return
            
            self.progress_updated.emit(30, "执行LLM分析")
            
            # 运行原有的LLM分析
            result = run_hedge_fund(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                portfolio=portfolio,
                show_reasoning=show_reasoning,
                selected_analysts=selected_analysts,
                model_name=model_name,
                model_provider=model_provider
            )
            
            if self.is_cancelled:
                return
            
            self.progress_updated.emit(100, "投资大师分析完成")
            
            # 发送完成信号
            self.analysis_completed.emit({
                'type': 'master',
                'result': result
            })
            
        except Exception as e:
            self.analysis_failed.emit(f"投资大师分析失败: {str(e)}")

# 分析师配置
g_analyst_configs = {
    "warren_buffett": "沃伦·巴菲特 - 价值投资大师",
    "charlie_munger": "查理·芒格 - 理性投资者", 
    "peter_lynch": "彼得·林奇 - 成长股猎手",
    "phil_fisher": "菲利普·费雪 - 成长投资先驱",
    "ben_graham": "本杰明·格雷厄姆 - 价值投资之父",
    "aswath_damodaran": "阿斯沃斯·达摩达兰 - 估值教授",
    "bill_ackman": "比尔·阿克曼 - 激进投资者",
    "cathie_wood": "凯茜·伍德 - 创新投资女王",
    "michael_burry": "迈克尔·伯里 - 逆向投资专家",
    "stanley_druckenmiller": "斯坦利·德鲁肯米勒 - 宏观交易大师",
    "rakesh_jhunjhunwala": "拉凯什·琼琼瓦拉 - 印度巴菲特",
    "technical_analyst": "技术面分析师 - 图表分析专家"
}


def parse_hedge_fund_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}\nResponse: {repr(response)}")
        return None


def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] = [],
    model_name: str = DEFAULT_MODEL_NAME,
    model_provider: str = "OpenAI",
):
    """运行AI基金分析"""
    try:
        # Create a new workflow if analysts are customized
        if selected_analysts:
            workflow = create_workflow(selected_analysts)
            agent = workflow.compile()
        else:
            # 如果没有指定分析师，使用所有分析师
            workflow = create_workflow()
            agent = workflow.compile()

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                    "unified_data_accessor": unified_data_accessor,
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )
        
        # Parse the final portfolio manager response
        portfolio_decisions = parse_hedge_fund_response(final_state["messages"][-1].content)
        
        # Safety check: ensure we have valid decisions
        if portfolio_decisions is None:
            print("Warning: Failed to parse portfolio manager response, creating default decisions")
            portfolio_decisions = {ticker: {"action": "hold", "quantity": 0, "confidence": 50.0, "reasoning": "Error parsing portfolio manager response"} for ticker in tickers}

        # 使用统一的分析师名称映射器确保一致性
        from src.utils.analyst_name_mapper import ensure_chinese_analyst_names
        analyst_signals = ensure_chinese_analyst_names(final_state["data"]["analyst_signals"])

        return {
            "decisions": portfolio_decisions,
            "analyst_signals": analyst_signals,
        }
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise


def start(state: AgentState):
    """Initialize the workflow with the input message and prefetch all data."""
    from src.utils.data_prefetch import data_prefetcher
    
    # 获取分析参数
    data = state["data"]
    tickers = data["tickers"]
    end_date = data["end_date"]
    start_date = data["start_date"]
    
    # 预获取所有分析师需要的数据
    prefetched_data = data_prefetcher.prefetch_all_data(tickers, end_date, start_date)
    
    # 将预获取的数据和数据预取器存储到状态中
    state["data"]["prefetched_data"] = prefetched_data
    state["data"]["data_prefetcher"] = data_prefetcher
    
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    else:
        # 过滤掉已删除或不存在的分析师
        selected_analysts = [analyst for analyst in selected_analysts if analyst in analyst_nodes]
        if not selected_analysts:
            # 如果过滤后没有有效分析师，使用默认配置
            selected_analysts = list(analyst_nodes.keys())
    
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Add portfolio management
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    # Connect selected analysts directly to portfolio management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "portfolio_manager")

    workflow.add_edge("portfolio_manager", END)

    workflow.set_entry_point("start_node")
    return workflow


def append_output_text(text):
    """添加输出文本"""
    try:
        if 'output_text' in g_widgets:
            g_widgets['output_text'].append(text)
            # 确保滚动到底部
            cursor = g_widgets['output_text'].textCursor()
            cursor.movePosition(cursor.End)
            g_widgets['output_text'].setTextCursor(cursor)
    except Exception as e:
        print(f"输出文本追加失败: {e}")


def update_progress(progress_percent, status_text):
    """更新进度"""
    try:
        if 'progress_bar' in g_widgets:
            g_widgets['progress_bar'].setValue(progress_percent)
        if 'status_label' in g_widgets:
            g_widgets['status_label'].setText(status_text)
        
        # 强制更新UI
        QApplication.processEvents()
    except Exception as e:
        print(f"更新进度失败: {e}")


def run_analysis_sync():
    """运行分析 - 支持单线程和多线程模式"""
    if g_state['is_analyzing']:
        QMessageBox.warning(None, "警告", "分析正在进行中，请等待完成")
        return
    
    # 检查是否启用多线程
    enable_multithreading = g_widgets['enable_multithreading_checkbox'].isChecked()
    
    if enable_multithreading:
        run_analysis_multithreaded()
    else:
        run_analysis_sync_original()


def run_analysis_multithreaded():
    """多线程运行分析"""
    try:
        print("=== 开始多线程分析 ===")
        
        # 解析股票代码
        import re
        tickers_input = g_widgets['tickers_edit'].text()
        tickers = [t.strip().upper() for t in re.split(r'[,;\s\t\n]+', tickers_input) if t.strip()]
        if not tickers:
            QMessageBox.critical(None, "错误", "请输入至少一个股票代码")
            return
            
        # 检查股票数量限制
        if len(tickers) > 4:
            QMessageBox.warning(None, "股票数量限制", f"股票数量过多，最多支持4支股票。\n当前输入了{len(tickers)}支股票，请减少股票数量。")
            return
        
        # 设置分析状态
        g_state['is_analyzing'] = True
        g_state['analysis_start_time'] = time.time()
        
        # 切换到运行标签页
        g_widgets['tab_widget'].setCurrentIndex(2)
        
        # 禁用按钮
        g_widgets['run_button'].setEnabled(False)
        g_widgets['bottom_run_button'].setEnabled(False)
        g_widgets['master_analysis_tab_button'].setEnabled(False)
        g_widgets['stop_button'].setEnabled(True)
        
        # 清空输出和进度
        g_widgets['output_text'].clear()
        update_progress(0, "正在初始化...")
        
        # 清空缓存
        try:
            from src.data.cache import get_cache
            cache = get_cache()
            cache.clear_cache()
            append_output_text("数据缓存已清理")
        except Exception as e:
            append_output_text(f"清理缓存失败（忽略）: {e}")
        
        # 清除API中断标志
        clear_api_interrupt()
        append_output_text("开始AI基金大师多线程分析...")
        
        # 准备配置
        config = {
            'tickers': tickers,
            'start_date': g_widgets['start_date_edit'].date().toString("yyyy-MM-dd"),
            'end_date': g_widgets['end_date_edit'].date().toString("yyyy-MM-dd"),
            'show_reasoning': g_widgets['show_reasoning_checkbox'].isChecked()
        }
        
        append_output_text(f"分析配置: {config}")
        
        # 创建并启动工作线程
        g_state['worker_thread'] = AnalysisWorkerThread('smart', config=config)
        
        # 连接信号
        g_state['worker_thread'].progress_updated.connect(on_analysis_progress_updated)
        g_state['worker_thread'].output_updated.connect(on_analysis_output_updated)
        g_state['worker_thread'].analysis_completed.connect(on_analysis_completed)
        g_state['worker_thread'].analysis_failed.connect(on_analysis_failed)
        
        # 启动线程
        g_state['worker_thread'].start()
        
    except Exception as e:
        error_msg = f"启动多线程分析失败: {str(e)}"
        append_output_text(f"ERROR: {error_msg}")
        QMessageBox.critical(None, "分析错误", f"{error_msg}\n\n详细信息请查看运行日志。")
        
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)


# 多线程信号处理函数
def on_analysis_progress_updated(progress, status):
    """处理分析进度更新信号"""
    update_progress(progress, status)

def on_analysis_output_updated(text):
    """处理分析输出更新信号"""
    append_output_text(text)

def on_analysis_completed(result_data):
    """处理分析完成信号"""
    try:
        result_type = result_data.get('type', '')
        
        if result_type == 'smart':
            # 智能分析完成
            smart_analysis_result = result_data.get('result', {})
            config = result_data.get('config', {})
            
            # 保存智能分析结果和配置
            g_state['smart_analysis_result'] = smart_analysis_result
            g_state['analysis_config'] = config
            
            # 显示智能分析结果
            show_smart_analysis_results(smart_analysis_result)
            
            # 计算总时间
            total_time = time.time() - g_state['analysis_start_time']
            if total_time < 60:
                time_str = f"{total_time:.0f}秒"
            else:
                time_str = f"{total_time/60:.1f}分钟"
            
            update_progress(100, f"多线程分析完成 - 总耗时: {time_str}")
            
            # 显示完成提示
            QMessageBox.information(
                None, "✅ 多线程分析完成", 
                "🎉 多线程智能分析已成功完成！\n\n" +
                "📊 请查看'分析结果'标签页获取详细报告\n" +
                "🧠 点击'投资大师分析'按钮进行深度LLM分析\n" +
                "💾 可使用'保存结果'按钮保存分析报告"
            )
            
        elif result_type == 'master':
            # 投资大师分析完成
            result = result_data.get('result', {})
            show_analysis_results(result)
            
            update_progress(100, "多线程投资大师分析完成")
            
            QMessageBox.information(
                None, "✅ 多线程投资大师分析完成", 
                "🎉 多线程投资大师分析已成功完成！\n\n" +
                "📊 请查看'分析结果'标签页获取详细报告\n" +
                "💾 可使用'保存结果'按钮保存分析报告"
            )
        
    except Exception as e:
        append_output_text(f"ERROR: 处理分析完成信号时出错: {str(e)}")
    finally:
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)
        g_state['worker_thread'] = None

def on_analysis_failed(error_message):
    """处理分析失败信号"""
    try:
        append_output_text(f"ERROR: {error_message}")
        QMessageBox.critical(None, "多线程分析错误", f"{error_message}\n\n详细信息请查看运行日志。")
    finally:
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)
        g_state['worker_thread'] = None


def run_analysis_sync_original():
    """原始的同步运行分析 - 三步流程：获取数据 -> 智能分析 -> 完成"""
    
    try:
        print("=== 开始分析验证 ===")
        
        # 解析股票代码
        import re
        tickers_input = g_widgets['tickers_edit'].text()
        tickers = [t.strip().upper() for t in re.split(r'[,;\s\t\n]+', tickers_input) if t.strip()]
        if not tickers:
            QMessageBox.critical(None, "错误", "请输入至少一个股票代码")
            return
            
        # 检查股票数量限制
        if len(tickers) > 4:
            QMessageBox.warning(None, "股票数量限制", f"股票数量过多，最多支持4支股票。\n当前输入了{len(tickers)}支股票，请减少股票数量。")
            return
        
        # 设置分析状态
        g_state['is_analyzing'] = True
        g_state['analysis_start_time'] = time.time()
        
        # 切换到运行标签页
        g_widgets['tab_widget'].setCurrentIndex(2)
        
        # 禁用按钮
        g_widgets['run_button'].setEnabled(False)
        g_widgets['bottom_run_button'].setEnabled(False)
        g_widgets['master_analysis_tab_button'].setEnabled(False)
        g_widgets['stop_button'].setEnabled(True)
        
        # 投资大师分析按钮保持可见
        
        # 清空输出和进度
        g_widgets['output_text'].clear()
        update_progress(0, "正在初始化...")
        
        # 清空缓存
        try:
            from src.data.cache import get_cache
            cache = get_cache()
            cache.clear_cache()
            append_output_text("数据缓存已清理")
        except Exception as e:
            append_output_text(f"清理缓存失败（忽略）: {e}")
        
        # 清除API中断标志
        clear_api_interrupt()
        append_output_text("开始AI基金大师分析...")
        
        # 准备配置
        config = {
            'tickers': tickers,
            'start_date': g_widgets['start_date_edit'].date().toString("yyyy-MM-dd"),
            'end_date': g_widgets['end_date_edit'].date().toString("yyyy-MM-dd"),
            'show_reasoning': g_widgets['show_reasoning_checkbox'].isChecked()
        }
        
        append_output_text(f"分析配置: {config}")
        update_progress(10, "配置完成，开始分析...")
        
        # 第一步：获取数据（使用缓存机制）
        update_progress(20, "第一步：获取股票数据...")
        append_output_text("=== 第一步：获取数据 ===")
        
        # 验证数据获取（使用缓存）
        from src.tools.api import get_prices
        for ticker in config['tickers']:
            try:
                # 生成缓存键
                cache_key = f"{ticker}_{config['start_date']}_{config['end_date']}"
                
                # 检查缓存
                if cache_key in g_data_cache:
                    append_output_text(f"📋 使用缓存数据 {ticker} ({len(g_data_cache[cache_key])} 条记录)")
                else:
                    # 获取新数据并缓存
                    prices = get_prices(ticker, config['start_date'], config['end_date'])
                    if prices:
                        g_data_cache[cache_key] = prices
                        append_output_text(f"✓ 成功获取 {ticker} 的价格数据 ({len(prices)} 条记录)")
                    else:
                        append_output_text(f"⚠ {ticker} 的价格数据为空")
            except Exception as e:
                append_output_text(f"✗ 获取 {ticker} 数据失败: {str(e)}")
        
        # 第二步：智能分析
        update_progress(40, "第二步：智能分析...")
        append_output_text("=== 第二步：智能分析 ===")
        
        from src.utils.enhanced_smart_analysis import generate_smart_analysis_report
        smart_analysis_result = generate_smart_analysis_report(
            config['tickers'], 
            config['start_date'], 
            config['end_date'],
            data_cache=g_data_cache
        )
        
        # 保存智能分析结果和配置
        g_state['smart_analysis_result'] = smart_analysis_result
        g_state['analysis_config'] = config
        
        # 显示智能分析结果
        show_smart_analysis_results(smart_analysis_result)
        
        update_progress(80, "智能分析完成")
        append_output_text("=== 智能分析完成 ===")
        
        # 计算总时间
        total_time = time.time() - g_state['analysis_start_time']
        if total_time < 60:
            time_str = f"{total_time:.0f}秒"
        else:
            time_str = f"{total_time/60:.1f}分钟"
        
        update_progress(100, f"基础分析完成 - 总耗时: {time_str}")
        
        # 投资大师分析按钮已永远可见
        
        # 显示完成提示
        QMessageBox.information(
            None, "✅ 基础分析完成", 
            "🎉 智能分析已成功完成！\n\n" +
            "📊 请查看'分析结果'标签页获取详细报告\n" +
            "🧠 点击'投资大师分析'按钮进行深度LLM分析\n" +
            "💾 可使用'保存结果'按钮保存分析报告"
        )
        
    except Exception as e:
        error_msg = f"分析过程中发生错误: {str(e)}"
        append_output_text(f"ERROR: {error_msg}")
        import traceback
        full_traceback = traceback.format_exc()
        append_output_text(f"错误堆栈: {full_traceback}")
        
        QMessageBox.critical(None, "分析错误", f"{error_msg}\n\n详细信息请查看运行日志。")
        
    finally:
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)
        
        # 清理
        try:
            clear_api_interrupt()
        except:
            pass


def stop_analysis():
    """停止分析"""
    if not g_state['is_analyzing']:
        return
    
    print("用户请求停止分析")
    try:
        # 如果有工作线程，先停止线程
        if g_state['worker_thread'] and g_state['worker_thread'].isRunning():
            g_state['worker_thread'].cancel()
            g_state['worker_thread'].wait(3000)  # 等待最多3秒
            g_state['worker_thread'] = None
        
        set_api_interrupt()
        update_progress(0, "已停止")
        
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)
        
        append_output_text("分析已被用户停止")
        
    except Exception as e:
        print(f"停止分析时出错: {e}")


def run_master_analysis():
    """运行投资大师分析 - 支持单线程和多线程模式"""
    if g_state['is_analyzing']:
        QMessageBox.warning(None, "警告", "分析正在进行中，请等待完成")
        return
    
    # 检查是否启用多线程
    enable_multithreading = g_widgets['enable_multithreading_checkbox'].isChecked()
    
    if enable_multithreading:
        run_master_analysis_multithreaded()
    else:
        run_master_analysis_original()


def run_master_analysis_multithreaded():
    """多线程运行投资大师分析"""
    try:
        print("=== 开始多线程投资大师分析 ===")
        
        # 验证LLM配置
        provider = g_widgets['provider_combo'].currentText()
        model = g_widgets['model_combo'].currentText()
        
        if provider == "DeepSeek":
            api_key = g_widgets['apikey_edit'].text().strip()
            if not api_key:
                QMessageBox.critical(None, "配置错误", "请在配置页面设置DeepSeek API Key")
                return
        elif provider == "Ollama":
            # 检查Ollama状态
            if not is_ollama_server_running():
                QMessageBox.critical(None, "配置错误", "Ollama服务未运行，请先启动Ollama")
                return
        
        # 获取选中的分析师
        selected_analysts = get_selected_analysts()
        if not selected_analysts:
            QMessageBox.warning(None, "分析师选择", "请至少选择一个分析师")
            return
        
        # 设置分析状态
        g_state['is_analyzing'] = True
        g_state['analysis_start_time'] = time.time()
        
        # 切换到运行标签页
        g_widgets['tab_widget'].setCurrentIndex(2)
        
        # 禁用按钮
        g_widgets['run_button'].setEnabled(False)
        g_widgets['bottom_run_button'].setEnabled(False)
        g_widgets['master_analysis_button'].setEnabled(False)
        g_widgets['master_analysis_tab_button'].setEnabled(False)
        g_widgets['stop_button'].setEnabled(True)
        
        append_output_text("开始多线程投资大师分析...")
        
        # 解析股票代码
        import re
        tickers_input = g_widgets['tickers_edit'].text()
        tickers = [t.strip().upper() for t in re.split(r'[,;\s\t\n]+', tickers_input) if t.strip()]
        
        # 获取日期范围
        start_date = g_widgets['start_date_edit'].date().toString("yyyy-MM-dd")
        end_date = g_widgets['end_date_edit'].date().toString("yyyy-MM-dd")
        
        # 获取交易参数
        show_reasoning = g_widgets['show_reasoning_checkbox'].isChecked()
        
        portfolio = {
            "cash": 100000.0,  # 默认资金
            "positions": {}
        }
        
        append_output_text(f"股票代码: {', '.join(tickers)}")
        append_output_text(f"分析师: {', '.join([g_analyst_configs.get(a, a) for a in selected_analysts])}")
        append_output_text(f"LLM模型: {provider} - {model}")
        
        # 创建并启动工作线程
        g_state['worker_thread'] = AnalysisWorkerThread(
            'master',
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=show_reasoning,
            selected_analysts=selected_analysts,
            model_name=get_actual_model_name(model, provider),
            model_provider=provider
        )
        
        # 连接信号
        g_state['worker_thread'].progress_updated.connect(on_analysis_progress_updated)
        g_state['worker_thread'].output_updated.connect(on_analysis_output_updated)
        g_state['worker_thread'].analysis_completed.connect(on_analysis_completed)
        g_state['worker_thread'].analysis_failed.connect(on_analysis_failed)
        
        # 启动线程
        g_state['worker_thread'].start()
        
    except Exception as e:
        error_msg = f"启动多线程投资大师分析失败: {str(e)}"
        append_output_text(f"ERROR: {error_msg}")
        QMessageBox.critical(None, "分析错误", f"{error_msg}\n\n详细信息请查看运行日志。")
        
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)


def run_master_analysis_original():
    """原始的投资大师分析"""
    # 投资大师分析可以独立运行，不需要前置条件
    
    try:
        print("=== 开始投资大师分析 ===")
        
        # 验证LLM配置
        provider = g_widgets['provider_combo'].currentText()
        model = g_widgets['model_combo'].currentText()
        
        if provider == "DeepSeek":
            api_key = g_widgets['apikey_edit'].text().strip()
            if not api_key:
                QMessageBox.critical(None, "配置错误", "请在配置页面设置DeepSeek API Key")
                return
        elif provider == "Ollama":
            # 检查Ollama状态
            if not is_ollama_server_running():
                # 检查Ollama是否已安装
                if is_ollama_installed():
                    # 询问用户是否自动启动Ollama
                    reply = QMessageBox.question(None, "Ollama未启动", 
                                                "检测到Ollama已安装但未启动，是否自动启动Ollama服务？",
                                                QMessageBox.Yes | QMessageBox.No,
                                                QMessageBox.Yes)
                    if reply == QMessageBox.Yes:
                        # 自动启动Ollama
                        append_output_text("正在启动Ollama服务...")
                        success = start_ollama_server()
                        if success:
                            append_output_text("Ollama服务启动成功")
                            # 等待服务完全启动
                            time.sleep(3)
                            # 确保默认模型可用
                            try:
                                ensure_ollama_and_model(DEFAULT_MODEL_NAME)
                                append_output_text(f"已设置默认模型: {DEFAULT_MODEL_NAME}")
                            except Exception as e:
                                append_output_text(f"设置默认模型失败: {str(e)}")
                        else:
                            QMessageBox.critical(None, "启动失败", "Ollama服务启动失败，请手动启动")
                            return
                    else:
                        return
                else:
                    QMessageBox.critical(None, "配置错误", "Ollama未安装，请先安装Ollama")
                    return
        
        # 获取选中的分析师
        selected_analysts = get_selected_analysts()
        if not selected_analysts:
            QMessageBox.warning(None, "分析师选择", "请至少选择一个分析师")
            return
        
        # 设置分析状态
        g_state['is_analyzing'] = True
        g_state['analysis_start_time'] = time.time()
        
        # 切换到运行标签页
        g_widgets['tab_widget'].setCurrentIndex(2)
        
        # 禁用按钮
        g_widgets['run_button'].setEnabled(False)
        g_widgets['bottom_run_button'].setEnabled(False)
        g_widgets['master_analysis_button'].setEnabled(False)
        g_widgets['master_analysis_tab_button'].setEnabled(False)
        g_widgets['stop_button'].setEnabled(True)
        
        append_output_text("开始投资大师分析...")
        update_progress(10, "准备LLM分析")
        
        # 解析股票代码
        import re
        tickers_input = g_widgets['tickers_edit'].text()
        tickers = [t.strip().upper() for t in re.split(r'[,;\s\t\n]+', tickers_input) if t.strip()]
        
        # 获取日期范围
        start_date = g_widgets['start_date_edit'].date().toString("yyyy-MM-dd")
        end_date = g_widgets['end_date_edit'].date().toString("yyyy-MM-dd")
        
        # 获取交易参数
        show_reasoning = g_widgets['show_reasoning_checkbox'].isChecked()
        
        portfolio = {
            "cash": 100000.0,  # 默认资金
            "positions": {}
        }
        
        append_output_text(f"股票代码: {', '.join(tickers)}")
        append_output_text(f"分析师: {', '.join([g_analyst_configs.get(a, a) for a in selected_analysts])}")
        append_output_text(f"LLM模型: {provider} - {model}")
        
        update_progress(30, "执行LLM分析")
        
        # 运行原有的LLM分析
        result = run_hedge_fund(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=show_reasoning,
            selected_analysts=selected_analysts,
            model_name=get_actual_model_name(model, provider),
            model_provider=provider
        )
        
        update_progress(90, "生成分析报告")
        
        # 显示LLM分析结果
        show_analysis_results(result)
        
        update_progress(100, "投资大师分析完成")
        
        # 显示完成提示
        QMessageBox.information(
            None, "✅ 投资大师分析完成", 
            "🎉 投资大师分析已成功完成！\n\n" +
            "📊 请查看'分析结果'标签页获取详细报告\n" +
            "💾 可使用'保存结果'按钮保存分析报告"
        )
        
    except Exception as e:
        error_msg = f"投资大师分析过程中发生错误: {str(e)}"
        append_output_text(f"ERROR: {error_msg}")
        import traceback
        full_traceback = traceback.format_exc()
        append_output_text(f"错误堆栈: {full_traceback}")
        
        QMessageBox.critical(None, "分析错误", f"{error_msg}\n\n详细信息请查看运行日志。")
        
    finally:
        # 恢复UI状态
        g_state['is_analyzing'] = False
        g_widgets['run_button'].setEnabled(True)
        g_widgets['bottom_run_button'].setEnabled(True)
        g_widgets['master_analysis_button'].setEnabled(True)
        g_widgets['master_analysis_tab_button'].setEnabled(True)
        g_widgets['stop_button'].setEnabled(False)
        
        # 清理
        try:
            clear_api_interrupt()
        except:
            pass


def show_analysis_results(result):
    """显示分析结果"""
    try:
        # 切换到结果标签页
        g_widgets['tab_widget'].setCurrentIndex(3)
        
        # 验证结果
        if not isinstance(result, dict):
            error_msg = f"接收到无效的结果类型: {type(result).__name__}，期望字典类型"
            g_widgets['html_preview'].setPlainText(f"❌ 结果类型错误: {error_msg}")
            g_widgets['results_text'].setPlainText(f"❌ 结果类型错误: {error_msg}")
            return
        
        # 存储结果数据
        g_state['current_result_data'] = result
        
        # 生成HTML报告
        try:
            g_state['current_html_content'] = generate_html_report(result)
            # 显示HTML报告的文本预览版本
            html_preview_text = convert_html_to_preview_text(result)
            g_widgets['html_preview'].setPlainText(html_preview_text)
        except Exception as e:
            g_widgets['html_preview'].setPlainText(f"HTML报告生成失败: {str(e)}")
        
        # 格式化并显示原始结果数据
        try:
            formatted_result = format_trading_output(result)
            g_widgets['results_text'].setPlainText(formatted_result)
        except Exception as e:
            g_widgets['results_text'].setPlainText(f"结果格式化失败: {str(e)}")
            
    except Exception as e:
        error_msg = f"显示分析结果时发生错误: {str(e)}"
        print(f"ERROR: {error_msg}")
        QMessageBox.critical(None, "错误", error_msg)


def show_smart_analysis_results(smart_result):
    """显示智能分析结果"""
    try:
        # 切换到结果标签页
        g_widgets['tab_widget'].setCurrentIndex(3)
        
        # 保存智能分析结果
        g_state['current_result_data'] = smart_result
        
        # 检查是否有完整的HTML报告
        full_html_report = smart_result.get('html_report')
        if full_html_report:
            # 使用完整的HTML报告作为当前内容
            g_state['current_html_content'] = full_html_report
            g_widgets['html_preview'].setHtml(full_html_report)
        else:
            # 如果没有完整报告，则使用原有的简化预览逻辑
            append_output_text("警告: 未找到完整的HTML报告，使用简化预览")
        
            # 生成智能分析的HTML预览（仅在没有完整报告时使用）
            html_preview = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .stock-section {{ background: #f8f9fa; }}
                    .metric {{ margin: 5px 0; }}
                    .positive {{ color: #27ae60; font-weight: bold; }}
                    .negative {{ color: #e74c3c; font-weight: bold; }}
                    .neutral {{ color: #34495e; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>智能分析报告（简化预览）</h1>
                    <p>基于AKShare数据的详细分析</p>
                </div>
            """
        
            # 获取个股分析数据
            individual_analysis = smart_result.get('individual_analysis', {})
            
            # 添加每只股票的分析
            for stock_code, analysis in individual_analysis.items():
                html_preview += f"""
                <div class="section stock-section">
                    <h2>📊 {stock_code} 分析报告</h2>
                
                    <h3>基本信息</h3>
                    <div class="metric">股票代码: {analysis.get('ticker', stock_code)}</div>
                    <div class="metric">市场: {analysis.get('market', 'N/A')}</div>
                    <div class="metric">分析日期: {analysis.get('analysis_date', 'N/A')}</div>
                """
            
                # 价格分析
                if 'price_analysis' in analysis and 'error' not in analysis['price_analysis']:
                    price_analysis = analysis['price_analysis']
                    html_preview += "<h3>价格分析</h3>"
                    
                    current_price = price_analysis.get('current_price')
                    if current_price:
                        html_preview += f'<div class="metric">当前价格: {current_price}</div>'
                    
                    price_change = price_analysis.get('price_change_percent')
                    if price_change is not None:
                        css_class = 'positive' if price_change > 0 else 'negative' if price_change < 0 else 'neutral'
                        html_preview += f'<div class="metric {css_class}">期间涨跌: {price_change:+.2f}%</div>'
                    
                    volatility = price_analysis.get('volatility_annual')
                    if volatility:
                        html_preview += f'<div class="metric">年化波动率: {volatility:.2f}%</div>'
                    
                    # 移动平均线
                    ma_data = price_analysis.get('moving_averages', {})
                    if ma_data:
                        html_preview += "<h4>移动平均线</h4>"
                        for ma_type, ma_value in ma_data.items():
                            if ma_value:
                                html_preview += f'<div class="metric">{ma_type.upper()}: {ma_value}</div>'
                
                # 财务分析
                if 'financial_analysis' in analysis and 'error' not in analysis['financial_analysis']:
                    financial_analysis = analysis['financial_analysis']
                    html_preview += "<h3>财务分析</h3>"
                    
                    financial_summary = financial_analysis.get('financial_summary')
                    if financial_summary:
                        html_preview += f'<div class="metric">{financial_summary}</div>'
                
                # 估值分析
                if 'valuation_analysis' in analysis and 'error' not in analysis['valuation_analysis']:
                    valuation_analysis = analysis['valuation_analysis']
                    html_preview += "<h3>估值分析</h3>"
                    
                    valuation_summary = valuation_analysis.get('valuation_summary')
                    if valuation_summary:
                        html_preview += f'<div class="metric">{valuation_summary}</div>'
                    
                    valuation_rating = valuation_analysis.get('valuation_rating')
                    if valuation_rating:
                        html_preview += f'<div class="metric">估值评级: {valuation_rating}</div>'
                
                # 风险分析
                if 'risk_analysis' in analysis and 'error' not in analysis['risk_analysis']:
                    risk_analysis = analysis['risk_analysis']
                    html_preview += "<h3>风险分析</h3>"
                    
                    risk_summary = risk_analysis.get('risk_summary')
                    if risk_summary:
                        html_preview += f'<div class="metric">{risk_summary}</div>'
                
                # 综合评分
                if 'overall_score' in analysis:
                    overall_score = analysis['overall_score']
                    html_preview += "<h3>综合评分</h3>"
                    
                    total_score = overall_score.get('total_score')
                    rating = overall_score.get('rating')
                    if total_score is not None and rating:
                        html_preview += f'<div class="metric">综合评分: {total_score}/100 ({rating})</div>'
                
                # 分析摘要
                analysis_summary = analysis.get('analysis_summary')
                if analysis_summary:
                    html_preview += "<h3>分析摘要</h3>"
                    html_preview += f'<div class="metric">{analysis_summary}</div>'
                    
                html_preview += "</div>"
        
            # 添加市场总览
            if 'market_overview' in smart_result:
                market_overview = smart_result['market_overview']
                html_preview += f"""
            <div class="section">
                <h2>📋 市场总览</h2>
                <div class="metric">分析股票总数: {market_overview.get('total_stocks_analyzed', 'N/A')}</div>
                <div class="metric">成功分析数: {market_overview.get('successful_analysis', 'N/A')}</div>
                <div class="metric">平均评分: {market_overview.get('average_score', 'N/A')}</div>
                <div class="metric">市场情绪: {market_overview.get('market_sentiment', 'N/A')}</div>
            </div>
            """
        
            html_preview += "</body></html>"
        
            # 显示HTML预览
            g_widgets['html_preview'].setHtml(html_preview)
            g_state['current_html_content'] = html_preview
        
            # 不再自动保存HTML报告
        
        # 显示原始数据
        import json
        formatted_result = json.dumps(smart_result, ensure_ascii=False, indent=2)
        g_widgets['results_text'].setPlainText(formatted_result)
        
        append_output_text("智能分析结果已显示在'分析结果'标签页")
        
    except Exception as e:
        error_msg = f"显示智能分析结果时发生错误: {str(e)}"
        append_output_text(f"ERROR: {error_msg}")
        import traceback
        full_traceback = traceback.format_exc()
        append_output_text(f"错误堆栈: {full_traceback}")


def convert_html_to_preview_text(result):
    """将分析结果转换为可在Text控件中显示的预览文本"""
    if not result:
        return "❌ 没有可用的分析结果"
    
    preview_text = " AI基金大师投资分析报告\n"
    preview_text += "=" * 50 + "\n\n"
    
    # 生成时间
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    preview_text += f" 作者:267278466@qq.com \n"
    preview_text += f"📅 生成时间: {current_time}\n\n"
    
    # 执行摘要
    decisions = result.get("decisions", {})
    if decisions:
        preview_text += "📋 执行摘要\n"
        preview_text += "-" * 30 + "\n"
        
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
        
        preview_text += f"📊 分析股票数量: {total_decisions}\n"
        preview_text += f"📈 买入建议: {action_counts['buy']}\n"
        preview_text += f"📉 卖出建议: {action_counts['sell']}\n"
        preview_text += f"⏸️  持有建议: {action_counts['hold']}\n"
        preview_text += f"🎯 平均信心度: {avg_confidence:.1f}%\n\n"
    
    # 投资决策详情
    if decisions:
        preview_text += "💰 投资决策详情\n"
        preview_text += "-" * 30 + "\n"
        
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
            
            preview_text += f"\n📈 {ticker} - {action_text}\n"
            preview_text += f"   交易数量: {quantity:,} 股\n"
            preview_text += f"   信心度: {confidence:.1f}%\n"
            reasoning_str = str(reasoning)
            preview_text += f"   分析理由: {reasoning_str[:100]}{'...' if len(reasoning_str) > 100 else ''}\n"
    
    preview_text += "\n" + "=" * 50 + "\n"
    preview_text += "⚠️ 风险提示: 本报告为编程生成的模拟样本，不能作为真实使用，不构成投资建议。\n"
    preview_text += "投资有风险，决策需谨慎。请根据自身情况做出投资决定。\n"
    preview_text += "\n💡 完整的精美HTML报告请点击 '🌐 浏览器查看' 按钮。\n"
    
    return preview_text


def get_selected_analysts():
    """获取选中的分析师"""
    selected = []
    for key, checkbox in g_widgets.get('analyst_checkboxes', {}).items():
        if checkbox.isChecked():
            selected.append(key)
    return selected


def select_all_analysts():
    """全选分析师"""
    for checkbox in g_widgets.get('analyst_checkboxes', {}).values():
        checkbox.setChecked(True)
    update_analysts_count()


def deselect_all_analysts():
    """取消全选分析师"""
    for checkbox in g_widgets.get('analyst_checkboxes', {}).values():
        checkbox.setChecked(False)
    update_analysts_count()


def set_recommended_analysts():
    """设置推荐的分析师配置"""
    recommended = {
        "warren_buffett": True,
        "charlie_munger": True, 
        "peter_lynch": True
    }
    
    # 先取消所有选择
    for checkbox in g_widgets.get('analyst_checkboxes', {}).values():
        checkbox.setChecked(False)
    
    # 然后只选择推荐的分析师
    for key, value in recommended.items():
        if key in g_widgets.get('analyst_checkboxes', {}):
            g_widgets['analyst_checkboxes'][key].setChecked(value)
    update_analysts_count()


def update_analysts_count():
    """更新分析师选择计数"""
    if 'analyst_checkboxes' in g_widgets and 'analysts_count_label' in g_widgets:
        selected = sum(1 for checkbox in g_widgets['analyst_checkboxes'].values() if checkbox.isChecked())
        total = len(g_widgets['analyst_checkboxes'])
        g_widgets['analysts_count_label'].setText(f"已选择: {selected}/{total}")


def check_ollama_status():
    """检查Ollama状态"""
    print("正在检查Ollama状态...")
    try:
        installed = is_ollama_installed()
        print(f"Ollama安装状态: {installed}")
        running = is_ollama_server_running() if installed else False
        print(f"Ollama运行状态: {running}")
        models = get_locally_available_models() if running else []
        print(f"可用模型数量: {len(models)}")
        
        update_ollama_status(installed, running, models)
    except Exception as e:
        print(f"检查Ollama状态时出错: {e}")
        update_ollama_status(False, False, [], str(e))


def update_ollama_status(installed, running, models, error=None):
    """更新Ollama状态显示"""
    if 'ollama_status_label' not in g_widgets:
        return
        
    if error:
        status_text = f"Ollama状态检查失败: {error}"
    elif not installed:
        status_text = "Ollama未安装 - 请先安装Ollama"
    elif not running:
        status_text = "Ollama已安装但未运行"
    else:
        status_text = f"Ollama正在运行 - 可用模型: {len(models)}个"
        
    g_widgets['ollama_status_label'].setText(status_text)
    
    # 更新模型选择框（仅当当前供应商是Ollama时）
    if g_widgets['provider_combo'].currentText() == "Ollama":
        # 保存当前选择的模型
        current_model = g_widgets['model_combo'].currentText()
        
        g_widgets['model_combo'].clear()
        if models:
            g_widgets['model_combo'].addItems(models)
            
            # 如果当前模型在新列表中，保持选择
            if current_model and current_model in models:
                index = models.index(current_model)
                g_widgets['model_combo'].setCurrentIndex(index)
                print(f"保持已选择的模型: {current_model}")
            # 优先选择默认模型
            elif DEFAULT_MODEL_NAME in models:
                index = models.index(DEFAULT_MODEL_NAME)
                g_widgets['model_combo'].setCurrentIndex(index)
                print(f"设置默认模型: {DEFAULT_MODEL_NAME}")
            elif models:
                g_widgets['model_combo'].setCurrentIndex(0)
                print(f"设置第一个可用模型: {models[0]}")


def start_ollama():
    """启动Ollama服务"""
    try:
        print("正在启动Ollama服务...")
        if 'ollama_status_label' in g_widgets:
            g_widgets['ollama_status_label'].setText("正在启动Ollama服务...")
        
        success = start_ollama_server()
        if success:
            print("SUCCESS: Ollama服务启动成功")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("Ollama服务启动成功")
            QTimer.singleShot(2000, check_ollama_status)
        else:
            print("ERROR: Ollama服务启动失败")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("Ollama服务启动失败")
    except Exception as e:
        print(f"ERROR: 启动Ollama服务时出错: {e}")
        if 'ollama_status_label' in g_widgets:
            g_widgets['ollama_status_label'].setText(f"启动失败: {str(e)}")


def install_ollama():
    """安装Ollama"""
    try:
        import subprocess
        
        # 首先尝试运行InstOlla.exe
        exe_path = os.path.join(os.getcwd(), "InstOlla.exe")
        bat_path = os.path.join(os.getcwd(), "InstallOllama.bat")
        
        if os.path.exists(exe_path):
            print("正在运行InstOlla.exe安装Ollama...")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("正在运行InstOlla.exe安装Ollama...")
            subprocess.Popen([exe_path], shell=True)
            print("InstOlla.exe已启动，请按照安装向导完成安装")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("InstOlla.exe已启动，请按照安装向导完成安装")
        elif os.path.exists(bat_path):
            print("正在运行InstallOllama.bat安装Ollama...")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("正在运行InstallOllama.bat安装Ollama...")
            subprocess.Popen([bat_path], shell=True)
            print("InstallOllama.bat已启动，请按照安装向导完成安装")
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText("InstallOllama.bat已启动，请按照安装向导完成安装")
        else:
            error_msg = "错误：未找到InstOlla.exe或InstallOllama.bat文件"
            print(error_msg)
            if 'ollama_status_label' in g_widgets:
                g_widgets['ollama_status_label'].setText(error_msg)
            QMessageBox.warning(None, "文件未找到", "未找到InstOlla.exe或InstallOllama.bat文件，请确保文件存在于程序目录中")
            
    except Exception as e:
        error_msg = f"安装Ollama时出错: {str(e)}"
        print(f"ERROR: {error_msg}")
        if 'ollama_status_label' in g_widgets:
            g_widgets['ollama_status_label'].setText(error_msg)
        QMessageBox.critical(None, "安装错误", error_msg)


def on_provider_changed():
    """当供应商改变时的处理"""
    provider = g_widgets['provider_combo'].currentText()
    
    if provider == "Ollama":
        # 隐藏BaseUrl和API Key（Ollama使用本地服务）
        g_widgets['baseurl_widget'].setVisible(False)
        g_widgets['apikey_widget'].setVisible(False)
        # 显示Ollama相关控件
        g_widgets['ollama_widget'].setVisible(True)
        # 显示Ollama按钮
        if 'start_ollama_btn' in g_widgets:
            g_widgets['start_ollama_btn'].setVisible(True)
        if 'install_ollama_btn' in g_widgets:
            g_widgets['install_ollama_btn'].setVisible(True)
        check_ollama_status()
    else:
        # 隐藏Ollama相关控件
        g_widgets['ollama_widget'].setVisible(False)
        # 隐藏Ollama按钮
        if 'start_ollama_btn' in g_widgets:
            g_widgets['start_ollama_btn'].setVisible(False)
        if 'install_ollama_btn' in g_widgets:
            g_widgets['install_ollama_btn'].setVisible(False)
        # 显示BaseUrl和API Key
        g_widgets['baseurl_widget'].setVisible(True)
        g_widgets['apikey_widget'].setVisible(True)
        # 加载API模型列表
        load_api_models()
    
    # 设置默认配置
    set_provider_defaults()


def set_provider_defaults():
    """设置供应商默认配置"""
    provider = g_widgets['provider_combo'].currentText()
    
    if provider == "DeepSeek":
        # 只在没有已保存配置时设置默认值
        if not g_widgets['baseurl_edit'].text():
            g_widgets['baseurl_edit'].setText("https://api.deepseek.com")
    elif provider == "Ollama":
        # Ollama使用本地服务，不需要设置BaseUrl和API Key
        pass


def load_api_models():
    """加载API模型列表"""
    try:
        from src.llm.models import load_models_from_json
        import os
        
        # 读取API模型配置
        api_models_file = os.path.join("src", "llm", "api_models.json")
        if os.path.exists(api_models_file):
            models = load_models_from_json(api_models_file)
            provider = g_widgets['provider_combo'].currentText()
            
            # 过滤当前供应商的模型
            filtered_models = [model.display_name for model in models if model.provider == provider]
            
            g_widgets['model_combo'].clear()
            g_widgets['model_combo'].addItems(filtered_models)
            if filtered_models:
                g_widgets['model_combo'].setCurrentIndex(0)
        else:
            print(f"API模型配置文件不存在: {api_models_file}")
            
    except Exception as e:
        print(f"加载API模型列表时出错: {e}")
        g_widgets['model_combo'].clear()


def get_actual_model_name(display_name: str, provider: str) -> str:
    """根据display_name和provider获取实际的model_name"""
    try:
        from src.llm.models import load_models_from_json
        import os
        
        # 读取API模型配置
        api_models_file = os.path.join("src", "llm", "api_models.json")
        if os.path.exists(api_models_file):
            models = load_models_from_json(api_models_file)
            
            # 查找匹配的模型
            for model in models:
                if model.display_name == display_name and model.provider == provider:
                    return model.model_name
                    
        return display_name  # 如果找不到，返回原始名称
        
    except Exception as e:
        print(f"获取实际模型名称时出错: {e}")
        return display_name


def open_html_in_browser():
    """在浏览器中打开HTML报告"""
    if not g_state['current_html_content']:
        QMessageBox.warning(None, "警告", "没有可用的HTML报告")
        return
    
    try:
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(g_state['current_html_content'])
            temp_file = f.name
        
        # 在浏览器中打开
        webbrowser.open(f'file://{temp_file}')
        
        # 延迟删除临时文件
        def cleanup():
            try:
                os.unlink(temp_file)
            except:
                pass
        
        QTimer.singleShot(5000, cleanup)  # 5秒后删除临时文件
        
    except Exception as e:
        QMessageBox.critical(None, "错误", f"无法在浏览器中打开HTML报告: {str(e)}")


def save_results():
    """保存结果到文件"""
    if not g_widgets['results_text'].toPlainText().strip():
        QMessageBox.warning(None, "警告", "没有结果可保存")
        return
        
    filename, _ = QFileDialog.getSaveFileName(
        None, "保存结果", "", "文本文件 (*.txt);;所有文件 (*.*)"
    )
    
    if filename:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(g_widgets['results_text'].toPlainText())
            QMessageBox.information(None, "成功", f"结果已保存到: {filename}")
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存失败: {str(e)}")


def save_html_report():
    """保存HTML报告到文件"""
    if not g_state['current_html_content']:
        QMessageBox.warning(None, "警告", "没有可用的HTML报告")
        return
    
    default_filename = f"AI基金大师分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filename, _ = QFileDialog.getSaveFileName(
        None, "保存HTML报告", default_filename, "HTML文件 (*.html);;所有文件 (*.*)"
    )
    
    if filename:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(g_state['current_html_content'])
            QMessageBox.information(None, "成功", f"HTML报告已保存到: {filename}")
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存失败: {str(e)}")


def clear_results():
    """清空结果"""
    g_widgets['results_text'].clear()
    g_widgets['html_preview'].clear()
    g_state['current_html_content'] = None
    g_state['current_result_data'] = None


def save_config():
    """保存当前配置到文件 - 增强版，保存所有AI相关设置"""
    try:
        # AI模型相关配置
        provider = g_widgets['provider_combo'].currentText()
        model = g_widgets['model_combo'].currentText()
        base_url = g_widgets['baseurl_edit'].text()
        api_key = g_widgets['apikey_edit'].text()
        
        # 分析师选择配置
        selected_analysts = {}
        if 'analyst_checkboxes' in g_widgets:
            selected_analysts = {key: checkbox.isChecked() for key, checkbox in g_widgets['analyst_checkboxes'].items()}
        
        # 交易参数配置
        tickers = g_widgets['tickers_edit'].text()
        show_reasoning = g_widgets['show_reasoning_checkbox'].isChecked()
        enable_multithreading = g_widgets['enable_multithreading_checkbox'].isChecked()
        
        # 日期范围配置
        start_date = g_widgets['start_date_edit'].date().toString("yyyy-MM-dd")
        end_date = g_widgets['end_date_edit'].date().toString("yyyy-MM-dd")
        
        # 构建完整配置
        config = {
            # AI模型配置
            "ai_config": {
                "provider": provider,
                "model": model,
                "base_url": base_url,
                "api_key": api_key,
                "last_updated": datetime.now().isoformat()
            },
            
            # 分析师配置
            "analysts_config": {
                "selected_analysts": selected_analysts,
                "total_selected": sum(1 for selected in selected_analysts.values() if selected)
            },
            
            # 交易参数配置
            "trading_config": {
                "tickers": tickers,
                "start_date": start_date,
                "end_date": end_date,
                "show_reasoning": show_reasoning,
                "enable_multithreading": enable_multithreading
            },
            
            # 界面配置
            "ui_config": {
                "window_geometry": None  # 可以后续添加窗口位置大小
            },
            
            # 兼容性配置（保持向后兼容）
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "api_key": api_key,
            "selected_analysts": selected_analysts,
            "tickers": tickers,
            "show_reasoning": show_reasoning,
            
            # 元数据
            "config_version": "2.0",
            "saved_at": datetime.now().isoformat(),
            "app_version": "3.1.0"
        }
        
        # 保存配置文件
        with open(g_state['config_file'], 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 输出保存信息
        analyst_count = config["analysts_config"]["total_selected"]
        print(f"✅ 配置保存成功!")
        print(f"   AI供应商: {provider}")
        print(f"   AI模型: {model}")
        print(f"   选中分析师: {analyst_count}位")
        print(f"   股票代码: {tickers}")
        print(f"   日期范围: {start_date} 至 {end_date}")
        print(f"   配置文件: {g_state['config_file']}")
        
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


def load_config():
    """从文件加载配置 - 增强版，支持新旧配置格式"""
    try:
        if not os.path.exists(g_state['config_file']):
            print(f"配置文件不存在: {g_state['config_file']}")
            print("将使用默认配置")
            set_recommended_analysts()
            return
            
        with open(g_state['config_file'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📁 加载配置文件: {g_state['config_file']}")
        
        # 检查配置版本
        config_version = config.get("config_version", "1.0")
        print(f"配置版本: {config_version}")
        
        # 恢复AI模型配置 - 支持新旧格式
        ai_config = config.get("ai_config", {})
        provider = ai_config.get("provider") or config.get("provider", "")
        model = ai_config.get("model") or config.get("model", "")
        base_url = ai_config.get("base_url") or config.get("base_url", "")
        api_key = ai_config.get("api_key") or config.get("api_key", "")
        
        # 恢复供应商配置（不触发change事件避免重复检查）
        if provider:
            if provider in ["DeepSeek", "Ollama", "OpenAI"]:
                # 临时断开信号连接，避免触发on_provider_changed
                g_widgets['provider_combo'].blockSignals(True)
                g_widgets['provider_combo'].setCurrentText(provider)
                g_widgets['provider_combo'].blockSignals(False)
                print(f"✅ 恢复AI供应商: {provider}")
            else:
                print(f"⚠️  未知的AI供应商: {provider}")
        
        # 恢复模型配置
        if model:
            # 延迟设置模型，确保在供应商切换后再恢复
            QTimer.singleShot(500, lambda: g_widgets['model_combo'].setCurrentText(model))
            print(f"✅ 准备恢复AI模型: {model}")
        
        # 恢复API配置
        if base_url:
            g_widgets['baseurl_edit'].setText(base_url)
            print(f"✅ 恢复API地址: {base_url}")
        
        if api_key:
            # 只显示API密钥的前几位和后几位
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            g_widgets['apikey_edit'].setText(api_key)
            print(f"✅ 恢复API密钥: {masked_key}")
        
        # 恢复分析师选择 - 支持新旧格式
        analysts_config = config.get("analysts_config", {})
        selected_analysts = analysts_config.get("selected_analysts") or config.get("selected_analysts", {})
        
        if selected_analysts:
            if isinstance(selected_analysts, list):
                # 兼容旧格式：列表转换为字典
                selected_analysts = {analyst: True for analyst in selected_analysts}
            elif not isinstance(selected_analysts, dict):
                selected_analysts = {}
            
            # 只恢复仍然存在的分析师配置
            restored_count = 0
            for key, value in selected_analysts.items():
                if key in g_widgets.get('analyst_checkboxes', {}):
                    g_widgets['analyst_checkboxes'][key].setChecked(value)
                    if value:
                        restored_count += 1
            
            update_analysts_count()
            print(f"✅ 恢复分析师选择: {restored_count}位")
        
        # 恢复交易参数配置 - 支持新旧格式
        trading_config = config.get("trading_config", {})
        tickers = trading_config.get("tickers") or config.get("tickers", "")
        show_reasoning = trading_config.get("show_reasoning")
        if show_reasoning is None:
            show_reasoning = config.get("show_reasoning", False)
        start_date = trading_config.get("start_date", "")
        end_date = trading_config.get("end_date", "")
        
        if tickers:
            g_widgets['tickers_edit'].setText(tickers)
            print(f"✅ 恢复股票代码: {tickers}")
        
        g_widgets['show_reasoning_checkbox'].setChecked(show_reasoning)
        print(f"✅ 恢复推理显示: {'开启' if show_reasoning else '关闭'}")
        
        # 恢复多线程选项
        enable_multithreading = trading_config.get("enable_multithreading", False)
        g_widgets['enable_multithreading_checkbox'].setChecked(enable_multithreading)
        print(f"✅ 恢复多线程模式: {'开启' if enable_multithreading else '关闭'}")
        
        # 恢复日期范围配置
        if start_date:
            try:
                date_obj = QDate.fromString(start_date, "yyyy-MM-dd")
                if date_obj.isValid():
                    g_widgets['start_date_edit'].setDate(date_obj)
                    print(f"✅ 恢复开始日期: {start_date}")
                else:
                    # 如果日期格式无效，使用默认日期（2个月前）
                    g_widgets['start_date_edit'].setDate(QDate.currentDate().addMonths(-2))
                    print(f"⚠️  开始日期格式无效，使用默认日期: 2个月前")
            except Exception as e:
                print(f"⚠️  恢复开始日期失败: {e}")
                # 出错时也使用默认日期
                g_widgets['start_date_edit'].setDate(QDate.currentDate().addMonths(-2))
        else:
            # 如果没有保存的开始日期，使用默认日期（2个月前）
            g_widgets['start_date_edit'].setDate(QDate.currentDate().addMonths(-2))
            print(f"✅ 使用默认开始日期: 2个月前")
        
        if end_date:
            try:
                date_obj = QDate.fromString(end_date, "yyyy-MM-dd")
                if date_obj.isValid():
                    g_widgets['end_date_edit'].setDate(date_obj)
                    print(f"✅ 恢复结束日期: {end_date}")
            except Exception as e:
                print(f"⚠️  恢复结束日期失败: {e}")
        
        # 恢复界面配置
        ui_config = config.get("ui_config", {})
        # 不再保存和恢复标签页索引，让用户每次都从第一个标签页开始
        
        # 显示配置加载摘要
        saved_at = config.get("saved_at", "未知时间")
        print(f"🎉 配置加载完成! (保存于: {saved_at})")
            
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        print("将使用默认配置")
        set_recommended_analysts()
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        # 配置加载失败时，设置默认推荐配置
        set_recommended_analysts()


def safe_exit(window):
    """安全退出程序 - 确保配置被保存"""
    try:
        print("🚪 准备退出程序...")
        
        # 检查是否有正在进行的分析
        if g_state.get('is_analyzing', False):
            reply = QMessageBox.question(
                window, 
                "确认退出", 
                "分析正在进行中，确定要退出吗？\n\n退出将中断当前分析并保存配置。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
            # 中断分析
            set_api_interrupt()
            g_state['is_analyzing'] = False
        
        # 保存配置
        print("💾 正在保存配置...")
        save_config()
        
        # 清理资源
        print("🧹 正在清理资源...")
        if 'output_text' in g_widgets:
            g_widgets['output_text'].clear()
        if 'results_text' in g_widgets:
            g_widgets['results_text'].clear()
        
        # 清空缓存
        global g_data_cache
        g_data_cache.clear()
        
        print("✅ 程序安全退出")
        QApplication.quit()
        
    except Exception as e:
        print(f"❌ 退出时发生错误: {e}")
        # 即使出错也要退出
        QApplication.quit()


def setup_window_close_event(window):
    """设置窗口关闭事件处理"""
    original_close_event = window.closeEvent
    
    def closeEvent(event):
        """重写窗口关闭事件"""
        try:
            # 检查是否有正在进行的分析
            if g_state.get('is_analyzing', False):
                reply = QMessageBox.question(
                    window, 
                    "确认退出", 
                    "分析正在进行中，确定要退出吗？\n\n退出将中断当前分析并保存配置。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    event.ignore()
                    return
                
                # 中断分析
                set_api_interrupt()
                g_state['is_analyzing'] = False
            
            # 自动保存配置
            print("🔄 窗口关闭时自动保存配置...")
            save_config()
            
            # 接受关闭事件
            event.accept()
            print("👋 程序已退出")
            
        except Exception as e:
            print(f"❌ 窗口关闭时发生错误: {e}")
            # 即使出错也要关闭
            event.accept()
    
    # 替换窗口的closeEvent方法
    window.closeEvent = closeEvent



def create_analysts_tab():
    """创建分析师选择标签页"""
    tab = QWidget()
    g_widgets['tab_widget'].addTab(tab, "🧠 投资大师")
    
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # 标题和统计
    title_layout = QHBoxLayout()
    title_label = QLabel("选择AI分析师")
    title_font = QFont()
    title_font.setPointSize(12)
    title_font.setBold(True)
    title_label.setFont(title_font)
    title_layout.addWidget(title_label)
    
    title_layout.addStretch()
    
    g_widgets['analysts_count_label'] = QLabel("已选择: 0/12")
    title_layout.addWidget(g_widgets['analysts_count_label'])
    
    layout.addLayout(title_layout)
    
    # 快捷操作按钮
    button_layout = QHBoxLayout()
    
    select_all_btn = QPushButton("✅ 全选")
    select_all_btn.clicked.connect(select_all_analysts)
    button_layout.addWidget(select_all_btn)
    
    deselect_all_btn = QPushButton("❌ 全不选")
    deselect_all_btn.clicked.connect(deselect_all_analysts)
    button_layout.addWidget(deselect_all_btn)
    
    recommended_btn = QPushButton("⭐ 推荐配置")
    recommended_btn.clicked.connect(set_recommended_analysts)
    button_layout.addWidget(recommended_btn)
    
    button_layout.addStretch()
    layout.addLayout(button_layout)
    
    # 分析师选择区域
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMinimumHeight(400)
    
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    
    # 投资大师分组
    masters_group = QGroupBox("💼 投资大师")
    masters_layout = QGridLayout(masters_group)
    
    # 专业分析师分组
    analysts_group = QGroupBox("📊 专业分析师")
    analysts_layout = QGridLayout(analysts_group)
    
    # 创建分析师复选框
    g_widgets['analyst_checkboxes'] = {}
    
    # 投资大师（前11个）
    master_analysts = list(g_analyst_configs.items())[:11]
    for i, (key, name) in enumerate(master_analysts):
        checkbox = QCheckBox(name)
        checkbox.setChecked(True)  # 默认选中
        checkbox.stateChanged.connect(update_analysts_count)
        g_widgets['analyst_checkboxes'][key] = checkbox
        masters_layout.addWidget(checkbox, i // 2, i % 2)
    
    # 专业分析师（技术分析师）
    tech_analysts = list(g_analyst_configs.items())[11:]
    for i, (key, name) in enumerate(tech_analysts):
        checkbox = QCheckBox(name)
        checkbox.setChecked(True)  # 默认选中
        checkbox.stateChanged.connect(update_analysts_count)
        g_widgets['analyst_checkboxes'][key] = checkbox
        analysts_layout.addWidget(checkbox, i // 2, i % 2)
    
    scroll_layout.addWidget(masters_group)
    scroll_layout.addWidget(analysts_group)
    
    # 股票参数区
    stock_params_group = QGroupBox("📈 股票参数")
    stock_params_layout = QGridLayout(stock_params_group)
    
    # 股票代码
    stock_params_layout.addWidget(QLabel("股票代码:"), 0, 0)
    g_widgets['tickers_edit'] = QLineEdit("AAPL,GOOGL,MSFT,TSLA,AMZN")
    g_widgets['tickers_edit'].setPlaceholderText("输入股票代码，用逗号分隔")
    stock_params_layout.addWidget(g_widgets['tickers_edit'], 0, 1, 1, 2)
    
    scroll_layout.addWidget(stock_params_group)
    scroll_layout.addStretch()
    
    scroll_area.setWidget(scroll_widget)
    layout.addWidget(scroll_area)
    
    # 更新初始计数
    update_analysts_count()


def create_config_tab():
    """创建配置标签页"""
    tab = QWidget()
    g_widgets['tab_widget'].addTab(tab, "⚙️ 配置")
    
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # LLM模型配置
    llm_group = QGroupBox("🤖 LLM模型配置")
    llm_layout = QVBoxLayout(llm_group)
    
    # 供应商和模型选择
    provider_model_layout = QHBoxLayout()
    provider_model_layout.addWidget(QLabel("供应商:"))
    
    g_widgets['provider_combo'] = QComboBox()
    g_widgets['provider_combo'].addItems(["DeepSeek", "Ollama"])
    g_widgets['provider_combo'].setCurrentIndex(0)  # 默认选择DeepSeek
    g_widgets['provider_combo'].currentTextChanged.connect(on_provider_changed)
    provider_model_layout.addWidget(g_widgets['provider_combo'])
    
    provider_model_layout.addWidget(QLabel("模型:"))
    
    g_widgets['model_combo'] = QComboBox()
    g_widgets['model_combo'].setMinimumWidth(200)
    provider_model_layout.addWidget(g_widgets['model_combo'])
    provider_model_layout.addStretch()
    
    llm_layout.addLayout(provider_model_layout)
    
    # BaseUrl配置
    g_widgets['baseurl_widget'] = QWidget()
    baseurl_layout = QHBoxLayout(g_widgets['baseurl_widget'])
    baseurl_layout.setContentsMargins(0, 0, 0, 0)
    baseurl_layout.addWidget(QLabel("Base URL:"))
    g_widgets['baseurl_edit'] = QLineEdit()
    g_widgets['baseurl_edit'].setPlaceholderText("输入API基础URL")
    baseurl_layout.addWidget(g_widgets['baseurl_edit'])
    llm_layout.addWidget(g_widgets['baseurl_widget'])
    
    # API Key配置
    g_widgets['apikey_widget'] = QWidget()
    apikey_layout = QHBoxLayout(g_widgets['apikey_widget'])
    apikey_layout.setContentsMargins(0, 0, 0, 0)
    apikey_layout.addWidget(QLabel("API Key:"))
    g_widgets['apikey_edit'] = QLineEdit()
    g_widgets['apikey_edit'].setEchoMode(QLineEdit.Password)
    g_widgets['apikey_edit'].setPlaceholderText("输入API密钥")
    apikey_layout.addWidget(g_widgets['apikey_edit'])
    llm_layout.addWidget(g_widgets['apikey_widget'])
    
    # Ollama相关控件
    g_widgets['ollama_widget'] = QWidget()
    ollama_widget_layout = QVBoxLayout(g_widgets['ollama_widget'])
    ollama_widget_layout.setContentsMargins(0, 0, 0, 0)
    
    # Ollama状态
    g_widgets['ollama_status_label'] = QLabel("正在检查Ollama状态...")
    ollama_widget_layout.addWidget(g_widgets['ollama_status_label'])
    
    # Ollama按钮
    ollama_btn_layout = QHBoxLayout()
    
    check_status_btn = QPushButton("🔄 检查状态")
    check_status_btn.clicked.connect(check_ollama_status)
    ollama_btn_layout.addWidget(check_status_btn)
    
    g_widgets['start_ollama_btn'] = QPushButton("▶️ 启动Ollama")
    g_widgets['start_ollama_btn'].clicked.connect(start_ollama)
    ollama_btn_layout.addWidget(g_widgets['start_ollama_btn'])
    
    g_widgets['install_ollama_btn'] = QPushButton("📥 安装Ollama")
    g_widgets['install_ollama_btn'].clicked.connect(install_ollama)
    ollama_btn_layout.addWidget(g_widgets['install_ollama_btn'])
    
    ollama_btn_layout.addStretch()
    ollama_widget_layout.addLayout(ollama_btn_layout)
    
    llm_layout.addWidget(g_widgets['ollama_widget'])
    layout.addWidget(llm_group)
    
    # 交易参数
    trading_group = QGroupBox("💰 交易参数")
    trading_layout = QGridLayout(trading_group)
    
    # 日期范围
    trading_layout.addWidget(QLabel("开始日期:"), 0, 0)
    g_widgets['start_date_edit'] = QDateEdit()
    g_widgets['start_date_edit'].setDate(QDate.currentDate().addMonths(-2))
    g_widgets['start_date_edit'].setCalendarPopup(True)
    trading_layout.addWidget(g_widgets['start_date_edit'], 0, 1)
    
    trading_layout.addWidget(QLabel("结束日期:"), 0, 2)
    g_widgets['end_date_edit'] = QDateEdit()
    g_widgets['end_date_edit'].setDate(QDate.currentDate())
    g_widgets['end_date_edit'].setCalendarPopup(True)
    trading_layout.addWidget(g_widgets['end_date_edit'], 0, 3)
    
    # 资金配置部分已删除
    
    layout.addWidget(trading_group)
    
    # 分析选项
    options_group = QGroupBox("🔧 分析选项")
    options_layout = QVBoxLayout(options_group)
    
    g_widgets['show_reasoning_checkbox'] = QCheckBox("显示详细分析推理过程")
    g_widgets['show_reasoning_checkbox'].setChecked(True)
    options_layout.addWidget(g_widgets['show_reasoning_checkbox'])
    
    # 多线程选项
    g_widgets['enable_multithreading_checkbox'] = QCheckBox("启用安全多线程模式（实验性功能）")
    g_widgets['enable_multithreading_checkbox'].setChecked(False)  # 默认关闭
    g_widgets['enable_multithreading_checkbox'].setToolTip("启用多线程可以提高分析速度，但可能存在稳定性风险。建议在单线程模式稳定运行后再尝试。")
    options_layout.addWidget(g_widgets['enable_multithreading_checkbox'])
    
    layout.addWidget(options_group)
    layout.addStretch()


def create_run_tab():
    """创建运行标签页"""
    tab = QWidget()
    g_widgets['tab_widget'].addTab(tab, "▶️ 运行")
    
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # 分析控制台
    control_group = QGroupBox("🎮 分析控制台")
    control_layout = QVBoxLayout(control_group)
    
    # 按钮区域
    button_layout = QHBoxLayout()
    
    g_widgets['master_analysis_tab_button'] = QPushButton("🧠 投资大师分析")
    g_widgets['master_analysis_tab_button'].clicked.connect(run_master_analysis)
    button_layout.addWidget(g_widgets['master_analysis_tab_button'])
    
    g_widgets['run_button'] = QPushButton("📊 智能分析")
    g_widgets['run_button'].clicked.connect(run_analysis_sync)
    button_layout.addWidget(g_widgets['run_button'])
    
    g_widgets['stop_button'] = QPushButton("⏹️ 停止分析")
    g_widgets['stop_button'].clicked.connect(stop_analysis)
    g_widgets['stop_button'].setEnabled(False)
    button_layout.addWidget(g_widgets['stop_button'])
    
    button_layout.addStretch()
    
    # 状态信息
    status_layout = QHBoxLayout()
    status_layout.addWidget(QLabel("分析状态:"))
    
    g_widgets['status_label'] = QLabel("准备就绪")
    g_widgets['status_label'].setStyleSheet("font-weight: bold;")
    status_layout.addWidget(g_widgets['status_label'])
    status_layout.addStretch()
    
    button_layout.addLayout(status_layout)
    control_layout.addLayout(button_layout)
    
    # 进度条
    progress_layout = QHBoxLayout()
    progress_layout.addWidget(QLabel("进度:"))
    
    g_widgets['progress_bar'] = QProgressBar()
    g_widgets['progress_bar'].setRange(0, 100)
    progress_layout.addWidget(g_widgets['progress_bar'])
    
    control_layout.addLayout(progress_layout)
    layout.addWidget(control_group)
    
    # 输出区域
    output_group = QGroupBox("📊 实时分析日志")
    output_layout = QVBoxLayout(output_group)
    
    g_widgets['output_text'] = QTextEdit()
    # 设置等宽字体
    try:
        output_font = QFont()
        output_font.setFamily("Consolas")
        output_font.setPointSize(9)
        output_font.setStyleHint(QFont.Monospace)
        g_widgets['output_text'].setFont(output_font)
    except Exception as e:
        print(f"设置输出文本字体失败: {e}")
        g_widgets['output_text'].setFont(QFont())
    
    g_widgets['output_text'].setStyleSheet("""
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #c0c0c0;
        }
    """)
    output_layout.addWidget(g_widgets['output_text'])
    
    # 添加调试信息
    append_output_text("=== AI基金大师单线程版本已启用 ===")
    append_output_text(f"GUI初始化完成，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    append_output_text("使用单线程模式，避免多线程崩溃问题")
    
    layout.addWidget(output_group)


def create_results_tab():
    """创建结果标签页"""
    tab = QWidget()
    g_widgets['tab_widget'].addTab(tab, "📊 结果")
    
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # 结果控制区域
    control_layout = QHBoxLayout()
    
    browser_btn = QPushButton("🌐 浏览器查看")
    browser_btn.clicked.connect(open_html_in_browser)
    control_layout.addWidget(browser_btn)
    
    save_btn = QPushButton("💾 保存报告")
    save_btn.clicked.connect(save_results)
    control_layout.addWidget(save_btn)
    
    save_html_btn = QPushButton("📄 保存HTML")
    save_html_btn.clicked.connect(save_html_report)
    control_layout.addWidget(save_html_btn)
    
    clear_btn = QPushButton("🗑️ 清空")
    clear_btn.clicked.connect(clear_results)
    control_layout.addWidget(clear_btn)
    
    control_layout.addStretch()
    layout.addLayout(control_layout)
    
    # 结果显示区域
    results_tab_widget = QTabWidget()
    
    # HTML报告标签页
    html_tab = QWidget()
    results_tab_widget.addTab(html_tab, "📊 精美报告")
    
    html_layout = QVBoxLayout(html_tab)
    html_group = QGroupBox("分析报告预览")
    html_group_layout = QVBoxLayout(html_group)
    
    g_widgets['html_preview'] = QTextEdit()
    # 设置中文字体
    try:
        preview_font = QFont()
        preview_font.setFamily("Microsoft YaHei")
        preview_font.setPointSize(10)
        preview_font.setStyleHint(QFont.SansSerif)
        g_widgets['html_preview'].setFont(preview_font)
    except Exception as e:
        print(f"设置HTML预览字体失败: {e}")
        g_widgets['html_preview'].setFont(QFont())
    
    g_widgets['html_preview'].setStyleSheet("""
        QTextEdit {
            background-color: #f8f9fa;
            border: none;
        }
    """)
    html_group_layout.addWidget(g_widgets['html_preview'])
    html_layout.addWidget(html_group)
    
    # 原始数据标签页
    raw_tab = QWidget()
    results_tab_widget.addTab(raw_tab, "📋 详细数据")
    
    raw_layout = QVBoxLayout(raw_tab)
    raw_group = QGroupBox("原始分析数据")
    raw_group_layout = QVBoxLayout(raw_group)
    
    g_widgets['results_text'] = QTextEdit()
    # 设置等宽字体
    try:
        results_font = QFont()
        results_font.setFamily("Consolas")
        results_font.setPointSize(9)
        results_font.setStyleHint(QFont.Monospace)
        g_widgets['results_text'].setFont(results_font)
    except Exception as e:
        print(f"设置结果文本字体失败: {e}")
        g_widgets['results_text'].setFont(QFont())
    
    raw_group_layout.addWidget(g_widgets['results_text'])
    raw_layout.addWidget(raw_group)
    
    layout.addWidget(results_tab_widget)


def create_main_window():
    """创建主窗口"""
    window = QMainWindow()
    window.setWindowTitle("AI基金大师 v3.1 - 267278466@qq.com")
    window.setGeometry(100, 100, 1000, 700)
    
    # 设置窗口图标
    try:
        window.setWindowIcon(QIcon("mrcai.ico"))
    except Exception as e:
        print(f"设置图标失败: {e}")
    
    # 设置应用样式
    window.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #c0c0c0;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #c0c0c0;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 6px 12px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QPushButton:disabled {
            background-color: #f0f0f0;
            color: #808080;
        }
    """)
    
    # 创建中央窗口部件
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # 创建主布局
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    
    # 创建标题
    title_label = QLabel(" AI基金大师")
    title_label.setAlignment(Qt.AlignCenter)
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    title_label.setFont(title_font)
    main_layout.addWidget(title_label)
    
    # 创建标签页
    g_widgets['tab_widget'] = QTabWidget()
    main_layout.addWidget(g_widgets['tab_widget'])
    
    # 创建各个标签页
    create_analysts_tab()
    create_config_tab()
    create_run_tab()
    create_results_tab()
    
    # 创建底部按钮
    bottom_layout = QHBoxLayout()
    
    # 左下角添加GitHub链接
    github_label = QLabel('<a href="https://github.com/hengruiyun" style="color: #0066cc; text-decoration: none;">HengruiYun</a>')
    github_label.setOpenExternalLinks(True)
    github_label.setStyleSheet("QLabel { font-size: 12px; color: #666; }")
    bottom_layout.addWidget(github_label)
    
    bottom_layout.addStretch()
    
    # 投资大师分析按钮（永远可见，在左边）
    g_widgets['master_analysis_button'] = QPushButton("🧠 AI投资大师分析")
    g_widgets['master_analysis_button'].clicked.connect(run_master_analysis)
    bottom_layout.addWidget(g_widgets['master_analysis_button'])
    
    # 智能分析按钮
    g_widgets['bottom_run_button'] = QPushButton("📊 智能分析")
    g_widgets['bottom_run_button'].clicked.connect(run_analysis_sync)
    bottom_layout.addWidget(g_widgets['bottom_run_button'])
    
    # 退出按钮
    exit_button = QPushButton("🚪 退出")
    exit_button.clicked.connect(lambda: safe_exit(window))
    bottom_layout.addWidget(exit_button)
    
    main_layout.addLayout(bottom_layout)
    
    # 设置窗口关闭事件处理
    setup_window_close_event(window)
    
    return window


def exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许 KeyboardInterrupt 正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    import traceback
    error_msg = f"未捕获的异常: {exc_type.__name__}: {exc_value}"
    traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    print(f"FATAL ERROR: {error_msg}")
    print(f"Traceback: {traceback_str}")
    
    # 尝试显示错误对话框
    try:
        if QApplication.instance():
            QMessageBox.critical(
                None, 
                "严重错误", 
                f"程序遇到严重错误:\n\n{error_msg}\n\n程序将退出。\n\n详细信息请查看控制台输出。"
            )
    except:
        pass


def main():
    """主函数"""
    # 设置全局异常处理器
    sys.excepthook = exception_handler
    
    # 设置Qt应用属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("AI基金大师")
    app.setApplicationVersion("3.1.0")
    app.setOrganizationName("AI Fund Master")
    
    # 设置默认字体
    try:
        default_font = QFont()
        default_font.setFamily("Microsoft YaHei")
        default_font.setPointSize(9)
        default_font.setStyleHint(QFont.SansSerif)
        app.setFont(default_font)
    except Exception as e:
        print(f"设置默认字体失败: {e}")
    
    try:
        print("=== AI基金大师单线程版启动 ===")
        #print(f"Qt版本: {Qt.qVersion()}")
        print(f"Python版本: {sys.version}")
        
        # 创建主窗口
        window = create_main_window()
        
        # 加载配置
        load_config()
        
        # 延迟执行供应商初始化
        QTimer.singleShot(100, on_provider_changed)
        
        # 显示窗口
        window.show()
        
        print("GUI界面显示完成，进入主循环")
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"GUI启动失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        try:
            QMessageBox.critical(None, "启动错误", f"GUI启动失败:\n{e}\n\n详细信息请查看控制台输出。")
        except:
            print("无法显示错误对话框")
        sys.exit(1)


if __name__ == "__main__":
    main()
