#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI对冲基金分析软件 - GUI启动器 v1.0
作者: HenghuiYun
基于: virattt/ai-hedge-fund (https://github.com/virattt/ai-hedge-fund)
功能: 为股票分析软件提供图形界面，支持配置保存和一键启动
增强: 依赖检查、错误处理、完整的故障诊断
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
import traceback
import warnings

# 抑制pydantic相关的UserWarning
warnings.filterwarnings("ignore", 
                       message=".*is not a Python type.*", 
                       category=UserWarning, 
                       module="pydantic.*")
warnings.filterwarnings("ignore", 
                       message=".*built-in function any.*", 
                       category=UserWarning, 
                       module="pydantic.*")

# 基础导入
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from datetime import datetime, timedelta
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 第一步：检查基础Python环境
def check_python_environment():
    """检查Python环境是否满足要求"""
    # 检查Python版本 - 推荐3.10
    if sys.version_info < (3, 10):
        print(f"[错误] Python版本过低: {sys.version}")
        print("   需要Python 3.10或更高版本")
        print("   推荐使用Python 3.10版本以获得最佳兼容性")
        return False
    elif sys.version_info >= (3, 10):
        print(f"[通过] Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (推荐版本)")
    else:
        print(f"[警告] Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (建议升级到3.10)")
    
    return True

# 第二步：检查和导入必要的基础模块
def import_basic_modules():
    """导入基础GUI模块"""
    
    try:
        global tk, ttk, messagebox, scrolledtext
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext
        
        global json, subprocess, threading, datetime, argparse
        import json
        import subprocess
        import threading
        from datetime import datetime, timedelta
        import argparse
        
        return True
    except ImportError as e:
        print(f"[错误] 基础模块导入失败: {e}")
        return False

# 第三步：检查AI相关依赖
def check_ai_dependencies():
    """检查AI相关依赖是否可用"""
    
    required_modules = [
        'langchain',
        'langchain_core', 
        'langchain_openai',
        'langgraph',
        'openai',
        'pandas',
        'numpy',
        'colorama'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n[警告] 缺失关键依赖: {', '.join(missing_modules)}")
        return False, missing_modules
    
    return True, []

# 第四步：依赖安装提示
def prompt_install_dependencies(missing_modules):
    """提示用户安装缺失的依赖"""
    print("\n" + "="*60)
    print("[提示] 检测到缺失的依赖包")
    print("="*60)
    
    # 创建一个简单的文本界面询问
    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        message = f"""检测到以下依赖包缺失：
{', '.join(missing_modules)}

软件需要这些包才能正常运行。

点击"是"自动安装依赖
点击"否"手动处理
点击"取消"退出程序"""
        
        result = messagebox.askyesnocancel("依赖缺失", message)
        root.destroy()
        
        if result is True:  # 用户选择"是"
            return install_dependencies()
        elif result is False:  # 用户选择"否"
            messagebox.showinfo("手动安装", 
                               "请在命令行运行以下命令安装依赖：\n\n"
                               "pip install -r requirements.txt\n\n"
                               "或者运行依赖检查工具：\n"
                               "python dependency_checker.py")
            return False
        else:  # 用户选择"取消"
            return False
            
    except Exception as e:
        # 命令行备用方案
        try:
            choice = input("\n是否自动安装缺失的依赖？(y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                return install_dependencies()
            else:
                print("请手动安装依赖: pip install -r requirements.txt")
                return False
        except:
            return False

def install_dependencies():
    """安装依赖包"""
    print("[进度] 开始安装依赖...")
    
    try:
        # 检查是否使用UV包管理器
        is_uv = False
        try:
            import shutil
            uv_path = shutil.which("uv")
            if uv_path:
                is_uv = True
        except:
            pass
        
        # 首先尝试使用requirements.txt
        req_file = Path(__file__).parent / "requirements.txt"
        if req_file.exists():
            # 设置环境变量，强制使用UTF-8编码
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            if is_uv:
                result = subprocess.run([
                    "uv", "pip", "install", "-r", str(req_file)
                ], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
            else:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', str(req_file)
                ], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
            
            if result.returncode == 0:
                print("[成功] 依赖安装成功")
                return True
            else:
                print(f"[错误] 依赖安装失败: {result.stderr}")
        
        # 备用方案：安装核心包
        core_packages = [
            'langchain==0.3.0',
            'langchain-core==0.3.63', 
            'langchain-openai==0.3.18',
            'langgraph==0.2.56',
            'openai==1.82.1',
            'pandas==2.2.3',
            'numpy==1.26.4',
            'python-dotenv==1.0.0',
            'colorama==0.4.6'
        ]
        
        # 设置环境变量，强制使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        for package in core_packages:
            if is_uv:
                result = subprocess.run([
                    "uv", "pip", "install", package
                ], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
            else:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
            
            if result.returncode != 0:
                print(f"[错误] 安装失败: {package}")
                return False
        
        print("[成功] 核心依赖安装完成")
        return True
        
    except Exception as e:
        print(f"[错误] 安装过程出错: {e}")
        return False

# 可选依赖导入
def import_optional_modules():
    """导入可选依赖"""
    global load_dotenv
    try:
        from dotenv import load_dotenv
        # 尝试加载.env文件，如果出现空字符错误则清理文件
        try:
            load_dotenv()
        except ValueError as e:
            if "embedded null character" in str(e):
                print("[警告] .env文件包含空字符，正在清理...")
                clean_env_file()
                # 重新尝试加载
                load_dotenv()
            else:
                raise e
    except ImportError:
        def load_dotenv():
            pass

def clean_env_file():
    """清理.env文件中的空字符"""
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            # 读取文件内容并移除空字符
            with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 移除空字符和其他不可见字符
            cleaned_content = content.replace('\x00', '').replace('\r\n', '\n')
            
            # 重新写入清理后的内容
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print("[成功] .env文件已清理")
        except Exception as e:
            print(f"[警告] 清理.env文件失败: {e}")
            # 如果清理失败，创建新的.env文件
            create_env_from_template()

def create_env_from_template():
    """从模板创建.env文件"""
    
    # 获取Ollama配置
    ollama_url = get_ollama_base_url()
    
    env_template = f"""# AI对冲基金分析软件 - 环境变量配置
# 请填入您的API密钥 (至少需要一个)

# OpenAI API配置 (支持GPT-4o, GPT-4o-mini等模型)
# 获取地址: https://platform.openai.com/account/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Groq API配置 (支持Llama, Mixtral等模型)  
# 获取地址: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Anthropic API配置 (支持Claude系列模型)
# 获取地址: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# DeepSeek API配置 (支持DeepSeek Chat和Coder模型)
# 获取地址: https://platform.deepseek.com/
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Google AI API配置 (支持Gemini系列模型)
# 获取地址: https://ai.google.dev/
GOOGLE_API_KEY=your_google_api_key_here

# 金融数据API配置 (用于高级股票数据分析)
# 获取地址: https://financialdatasets.ai/
FINANCIAL_DATASETS_API_KEY=your_financial_datasets_api_key_here

# Ollama配置 (本地模型，无需API密钥)
OLLAMA_BASE_URL={ollama_url}
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_template)
        return True
    except Exception as e:
        print(f"[错误] 创建.env文件失败: {e}")
        return False

def get_ollama_base_url():
    """获取Ollama Base URL - 按优先级：.env文件的OLLAMA_BASE_URL → 环境变量OLLAMA_HOST+OLLAMA_PORT → 默认值"""
    
    # 第一优先级：从.env文件读取OLLAMA_BASE_URL
    env_base_url = None
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OLLAMA_BASE_URL=') and not line.startswith('#'):
                        env_base_url = line.split('=', 1)[1].strip()
                        if env_base_url and not env_base_url.startswith('your_'):
                            print(f"[配置] 使用.env文件中的OLLAMA_BASE_URL: {env_base_url}")
                            return env_base_url
                        break
        except Exception as e:
            print(f"[警告] 读取.env文件失败: {e}")
    
    # 第二优先级：从环境变量OLLAMA_HOST+OLLAMA_PORT组合
    ollama_host = os.getenv('OLLAMA_HOST')
    ollama_port = os.getenv('OLLAMA_PORT')
    
    if ollama_host:
        if ollama_port:
            env_url = f"http://{ollama_host}:{ollama_port}"
        else:
            env_url = f"http://{ollama_host}:11434"  # 默认端口
        print(f"[配置] 使用环境变量OLLAMA_HOST+OLLAMA_PORT: {env_url}")
        return env_url
    
    # 第三优先级：默认值
    default_url = "http://localhost:11434"
    print(f"[配置] 使用默认OLLAMA_BASE_URL: {default_url}")
    return default_url

def check_ollama_availability():
    """检测Ollama是否可用 - 仅检查服务运行状态，不检查模型"""
    
    ollama_url = get_ollama_base_url()
    
    try:
        import requests
        
        # 检查Ollama根路径，通常返回"Ollama is running"
        response = requests.get(ollama_url, timeout=3)
        
        if response.status_code == 200:
            response_text = response.text.strip()
            if "Ollama is running" in response_text:
                print(f"[成功] Ollama服务运行正常: {ollama_url}")
                return True, ollama_url
            else:
                print(f"[信息] Ollama服务响应异常: {response_text}")
                return False, ollama_url
        else:
            print(f"[信息] Ollama服务不可用 (HTTP {response.status_code})")
            return False, ollama_url
            
    except requests.exceptions.ConnectionError:
        print(f"[信息] 无法连接到Ollama服务: {ollama_url}")
        return False, ollama_url
    except requests.exceptions.Timeout:
        print(f"[信息] 连接Ollama服务超时: {ollama_url}")
        return False, ollama_url
    except ImportError:
        print("[警告] requests模块未安装，无法检测Ollama")
        return False, ollama_url
    except Exception as e:
        print(f"[警告] 检测Ollama时出错: {e}")
        return False, ollama_url

def check_and_fix_environment():
    """检查并修复环境问题"""
    
    issues = []
    fixes = []
    
    # 检查.env文件
    if not os.path.exists('.env'):
        issues.append("缺少.env配置文件")
        fixes.append("将从模板创建.env文件")
    
    # 检查API密钥
    load_dotenv()
    api_keys = ['OPENAI_API_KEY', 'GROQ_API_KEY', 'ANTHROPIC_API_KEY', 'DEEPSEEK_API_KEY', 'GOOGLE_API_KEY','FINANCIAL_DATASETS_API_KEY']
    missing_keys = []
    for key in api_keys:
        if not os.getenv(key) or os.getenv(key) == f'your_{key.lower()}_here' or os.getenv(key).startswith('your_'):
            missing_keys.append(key)
    
    if missing_keys:
        issues.append(f"缺少有效API密钥: {', '.join(missing_keys[:3])}{'...' if len(missing_keys) > 3 else ''}")
        fixes.append("需要在GUI的'API密钥配置'选项卡中配置有效的API密钥")
    
    # 检查Ollama可用性
    ollama_available, ollama_url = check_ollama_availability()
    if not ollama_available:
        issues.append(f"Ollama服务不可用 ({ollama_url})")
        fixes.append("如需使用本地模型，请确保Ollama服务正在运行")
    else:
        print(f"[成功] Ollama服务运行正常: {ollama_url}")
    
    # 检查依赖版本冲突
    try:
        import yfinance
        if hasattr(yfinance, '__version__') and yfinance.__version__.startswith('0.2.45'):
            issues.append("yfinance版本0.2.45存在已知问题")
            fixes.append("建议降级到yfinance==0.2.40")
    except:
        pass
    
    if issues:
        print(f"[警告] 发现 {len(issues)} 个环境问题:")
        for i, issue in enumerate(issues):
            print(f"  {i+1}. {issue}")
        
        print(f"\n[建议] 建议修复:")
        for i, fix in enumerate(fixes):
            print(f"  {i+1}. {fix}")
        
        return False
    else:
        return True

# GUI主类
class HedgeFundGUI:
    def __init__(self, root):
        print("[初始化] 初始化GUI界面...")
        self.root = root
        
        # 初始化变量
        self.config_file = "hedge_fund_config.json"
        self.language_var = tk.StringVar(value="en")  # 默认英文
        self.init_translations()
        
        # 完整初始化
        self.setup_variables()
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.load_settings()
        print("[完成] GUI界面初始化完成")
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title(self.get_translation("title"))
        # 强制设置窗口大小，不依赖center_window的逻辑
        self.root.geometry("700x400")
        self.root.minsize(600, 400)  # 设置最小尺寸
        self.root.resizable(True, True)  # 允许调整大小
        self.root.configure(bg='#f0f0f0')
        
        # 手动居中但不改变大小
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - 350  # 700/2 = 350
        y = (screen_height // 2) - 200  # 400/2 = 200
        self.root.geometry(f"700x400+{x}+{y}")
        
    def center_window(self, window=None):
        """将窗口居中显示"""
        if window is None:
            window = self.root
            
        window.update_idletasks()
        
        # 获取窗口尺寸
        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()
        
        # 对于主窗口，强制使用700x400
        if window == self.root:
            window_width = 700
            window_height = 400
        else:
            # 对于其他窗口，使用默认值
            if window_width <= 1:
                window_width = 400
            if window_height <= 1:
                window_height = 300
            
        # 计算居中位置
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def setup_variables(self):
        """设置变量"""
        self.ticker_var = tk.StringVar(value="AAPL,MSFT,NVDA")
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.initial_cash_var = tk.StringVar(value="100000.0")
        self.margin_requirement_var = tk.StringVar(value="0.0")
        self.show_reasoning_var = tk.BooleanVar(value=False)
        self.show_graph_var = tk.BooleanVar(value=True)
        
        # API Keys
        self.openai_key_var = tk.StringVar()
        self.groq_key_var = tk.StringVar()
        self.anthropic_key_var = tk.StringVar()
        self.deepseek_key_var = tk.StringVar()
        self.google_key_var = tk.StringVar()
        self.financial_datasets_key_var = tk.StringVar()
        
        # 模型配置
        self.model_provider_var = tk.StringVar(value="OpenAI")
        self.model_name_var = tk.StringVar(value="gpt-4o")
        
        # 分析师选择变量
        self.analyst_vars = {}
        
        # 分析师配置（中文翻译）
        self.analysts_config = [
            ("aswath_damodaran", "阿斯瓦斯·达摩达兰"),
            ("ben_graham", "本杰明·格雷厄姆"),
            ("bill_ackman", "比尔·阿克曼"),
            ("cathie_wood", "凯茜·伍德"),
            ("charlie_munger", "查理·芒格"),
            ("michael_burry", "迈克尔·伯里"),
            ("peter_lynch", "彼得·林奇"),
            ("phil_fisher", "菲利普·费雪"),
            ("stanley_druckenmiller", "斯坦利·德鲁肯米勒"),
            ("warren_buffett", "沃伦·巴菲特"),
            ("technical_analyst", "技术分析师"),
            ("fundamentals_analyst", "基本面分析师"),
            ("sentiment_analyst", "情绪分析师"),
            ("valuation_analyst", "估值分析师")
        ]
        
        # 模型供应商和对应模型
        self.model_providers = {
            "OpenAI": ["o3","gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "Groq": ["llama-4-scout-17b-16e-instruct","llama-3.3-70b-versatile","llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "Anthropic": ["claude-4-sonnet","claude-3-7-sonnet","claude-3-5-sonnet"],
            "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
            "Google": ["gemini-2.5-pro-preview", "gemini-2.5-flash","gemini-2.0-pro", "gemini-2.0-flash"],
            "Ollama": ["deepseek-r1","deepseek-r1:32b", "qwen3", "qwen3:32b", "gemma3",  "gemma3:27b", "llama4",  "devstral", "Customize"]
        }
        
        # 初始化分析师选择变量
        for key, name in self.analysts_config:
            self.analyst_vars[key] = tk.BooleanVar(value=False)  # 默认不选择
            
    def init_translations(self):
        """初始化多语言翻译"""
        self.translations = {
            "en": {
                "title": "AI Hedge Fund Analysis Software -GUI v1.0",
                "run_now": "Run Now",
                "exit": "Exit",
                "tabs": {
                    "analysts": "Analysts",
                    "params": "Parameters",
                    "api": "API Keys",
                    "model": "Model Config"
                },
                "analyst_actions": {
                    "select_all": "Select All",
                    "deselect_all": "Deselect All"
                },
                "params": {
                    "ticker": "Stock Ticker:",
                    "ticker_hint": "(comma separated)",
                    "start_date": "Start Date:",
                    "start_date_hint": "(YYYY-MM-DD, empty for auto)",
                    "end_date": "End Date:",
                    "end_date_hint": "(YYYY-MM-DD, empty for today)",
                    "initial_cash": "Initial Cash:",
                    "initial_cash_hint": "(USD)",
                    "margin_req": "Margin Requirement:",
                    "margin_req_hint": "(ratio between 0-1)",
                    "show_reasoning": "Show Reasoning Process",
                    "financial_api": "Financial Datasets API Key:",
                    "financial_api_hint": "(optional)"
                },
                "api": {
                    "openai": "OpenAI API Key:",
                    "groq": "Groq API Key:",
                    "anthropic": "Anthropic API Key:",
                    "deepseek": "DeepSeek API Key:",
                    "google": "Google API Key:",
                    "financial": "Financial Datasets API Key:"
                },
                "model": {
                    "provider": "Model Provider:",
                    "name": "Model Name:",
                    "custom": "Custom Model:",
                    "ollama_hint": "Note: Selecting Ollama provider enables the --ollama parameter"
                },
                "progress": {
                    "title": "Analysis in Progress",
                    "analyzing": "AI analysis in progress...",
                    "terminal_output": "Analysis results will be displayed in the terminal window",
                    "check_terminal": "Please check the command line window for detailed output",
                    "analysis_start": "🚀 Starting AI Hedge Fund Analysis",
                    "analysis_complete": "✅ AI Hedge Fund Analysis Complete",
                    "stock_codes": "📊 Stock Codes",
                    "initial_funds": "💰 Initial Funds",
                    "ai_model": "🤖 AI Model",
                    "analysts": "👥 Analysts",
                    "analysis_success": "🎉 Analysis results are displayed above, please check detailed recommendations",
                    "analysis_complete_msg": "AI hedge fund analysis completed!",
                    "analysis_complete_detail": "Detailed analysis results are displayed in the terminal window that started the GUI.\nPlease check the command line for investment recommendations.",
                    "analysis_error": "❌ Error occurred during analysis",
                    "suggestion": "💡 Suggestion"
                }
            },
            "zh": {
                "title": "AI对冲基金分析软件 - GUI启动器 v1.0",
                "run_now": "立即运行",
                "exit": "退出",
                "tabs": {
                    "analysts": "分析师选择",
                    "params": "参数设置",
                    "api": "API密钥",
                    "model": "模型设置"
                },
                "analyst_actions": {
                    "select_all": "全选",
                    "deselect_all": "全不选"
                },
                "params": {
                    "ticker": "股票代码:",
                    "ticker_hint": "(用逗号分隔)",
                    "start_date": "开始日期:",
                    "start_date_hint": "(YYYY-MM-DD，留空自动)",
                    "end_date": "结束日期:",
                    "end_date_hint": "(YYYY-MM-DD，留空今天)",
                    "initial_cash": "初始资金:",
                    "initial_cash_hint": "(美元)",
                    "margin_req": "保证金要求:",
                    "margin_req_hint": "(0-1之间的比例)",
                    "show_reasoning": "显示推理过程",
                },
                "api": {
                    "openai": "OpenAI API密钥:",
                    "groq": "Groq API密钥:",
                    "anthropic": "Anthropic API密钥:",
                    "deepseek": "DeepSeek API密钥:",
                    "google": "Google API密钥:",
                    "financial": "Financial API密钥:"
                },
                "model": {
                    "provider": "模型供应商:",
                    "name": "模型名称:",
                    "custom": "自定义模型:",
                    "ollama_hint": "提示：选择Ollama供应商时，等同于启用--ollama参数"
                },
                "progress": {
                    "title": "分析进行中",
                    "analyzing": "正在进行AI分析...",
                    "terminal_output": "分析结果将在启动GUI的终端窗口中显示",
                    "check_terminal": "请查看命令行窗口获取详细输出",
                    "analysis_start": "🚀 开始AI对冲基金分析",
                    "analysis_complete": "✅ AI对冲基金分析完成",
                    "stock_codes": "📊 股票代码",
                    "initial_funds": "💰 初始资金",
                    "ai_model": "🤖 AI模型",
                    "analysts": "👥 分析师",
                    "analysis_success": "🎉 分析结果已在上方显示，请查看详细建议",
                    "analysis_complete_msg": "AI对冲基金分析已完成！",
                    "analysis_complete_detail": "详细分析结果已在启动GUI的终端窗口中显示。\n请查看命令行获取投资建议。",
                    "analysis_error": "❌ 分析过程中发生错误",
                    "suggestion": "💡 建议"
                }
            }
        }
        
    def setup_styles(self):
        """设置ttk样式"""
        self.style = ttk.Style()
        
        # 设置默认字体
        default_font = ("Arial", 11)
        
        # 为各种ttk部件设置字体
        self.style.configure("TLabel", font=default_font)
        self.style.configure("TButton", font=default_font)
        self.style.configure("TCheckbutton", font=default_font)
        self.style.configure("TRadiobutton", font=default_font)
        self.style.configure("TCombobox", font=default_font)
        self.style.configure("TEntry", font=default_font)
        
        # 设置标题字体
        self.style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        
        # 设置提示文本字体
        self.style.configure("Hint.TLabel", font=("Arial", 10))
        
        # 设置链接字体
        self.style.configure("Link.TLabel", font=default_font, foreground="blue")
        
        # 自定义选项卡字体
        self.style.configure("TNotebook.Tab", font=default_font, padding=[10, 5])
        
    def create_widgets(self):
        """创建界面控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # 选项卡区域应该扩展
        
        # 顶部框架 - 包含标题和语言选择
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 3))
        top_frame.columnconfigure(0, weight=1)
        
        # 标题 - 放在左侧
        self.title_label = ttk.Label(top_frame, text=self.get_translation("title"), 
                                  style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky=tk.W, pady=(10, 10))
        
        # 语言选择下拉框 - 放在右侧
        lang_frame = ttk.Frame(top_frame)
        lang_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(lang_frame, text="Language:").grid(row=0, column=0, padx=(0, 5))
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                values=["en", "zh"], state="readonly", width=5)
        lang_combo.grid(row=0, column=1)
        lang_combo.bind('<<ComboboxSelected>>', self.change_language)
        
        # 创建选项卡 - 直接在标题下方
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(3, 5))
        
        # 创建四个选项卡页面
        self.create_analyst_tab()
        self.create_params_tab()
        self.create_api_tab()
        self.create_model_tab()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 5))
        button_frame.columnconfigure(0, weight=1)
        
        # 创建左下角的HengruiYun链接
        left_buttons = ttk.Frame(button_frame)
        left_buttons.grid(row=0, column=0, sticky=tk.W)
        
        hengrui_label = ttk.Label(left_buttons, text="HengruiYun", 
                                style="Link.TLabel", cursor="hand2")
        hengrui_label.grid(row=0, column=0, padx=(0, 10))
        # 点击时打开浏览器
        hengrui_label.bind("<Button-1>", lambda e: self.open_browser("https://github.com/hengruiyun/ai-hedge-fund-gui/"))
        
        # 右下角按钮
        right_buttons = ttk.Frame(button_frame)
        right_buttons.grid(row=0, column=1, sticky=tk.E)
        
        self.run_btn = ttk.Button(right_buttons, text=self.get_translation("run_now"), 
                               command=self.run_analysis)
        self.run_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.exit_btn = ttk.Button(right_buttons, text=self.get_translation("exit"), 
                                command=self.quit_app)
        self.exit_btn.grid(row=0, column=1)
    
    def get_translation(self, key, section=None):
        """获取翻译文本"""
        lang = self.language_var.get()
        
        if section:
            try:
                return self.translations[lang][section][key]
            except (KeyError, TypeError):
                # 如果没有找到翻译，返回英文版
                try:
                    return self.translations["en"][section][key]
                except (KeyError, TypeError):
                    return f"{key}"
        else:
            try:
                return self.translations[lang][key]
            except (KeyError, TypeError):
                # 如果没有找到翻译，返回英文版
                try:
                    return self.translations["en"][key]
                except (KeyError, TypeError):
                    return f"{key}"

    def change_language(self, event=None):
        """切换语言"""
        # 更新标题
        self.title_label.config(text=self.get_translation("title"))
        self.root.title(self.get_translation("title"))
        
        # 更新按钮文本
        self.run_btn.config(text=self.get_translation("run_now"))
        self.exit_btn.config(text=self.get_translation("exit"))
        
        # 更新选项卡标题 - 修复参数顺序
        self.notebook.tab(0, text=self.get_translation("analysts", "tabs"))
        self.notebook.tab(1, text=self.get_translation("params", "tabs"))
        self.notebook.tab(2, text=self.get_translation("api", "tabs"))
        self.notebook.tab(3, text=self.get_translation("model", "tabs"))
        
        # 重建选项卡内容
        self.rebuild_tabs()

    def rebuild_tabs(self):
        """重建所有选项卡内容"""
        # 保存当前选中的选项卡
        current_tab = self.notebook.index(self.notebook.select())
        
        # 先更新分析师选择页的按钮文本（如果已创建）
        if hasattr(self, 'select_all_btn'):
            self.select_all_btn.config(text=self.get_translation("select_all", "analyst_actions"))
        if hasattr(self, 'deselect_all_btn'):
            self.deselect_all_btn.config(text=self.get_translation("deselect_all", "analyst_actions"))
        
        # 更新分析师复选框文本
        if hasattr(self, 'analyst_checkbuttons'):
            for key, cb in self.analyst_checkbuttons:
                display_name = self.analysts_config[self.get_analyst_index(key)][1] if self.language_var.get() == "zh" else self.get_english_analyst_name(key)
                cb.config(text=display_name)
        
        # 更新参数选项卡的标签文本
        if hasattr(self, 'param_labels'):
            for label, key in self.param_labels:
                label.config(text=self.get_translation(key, "params"))
        
        if hasattr(self, 'param_hint_labels'):
            for label, key in self.param_hint_labels:
                label.config(text=self.get_translation(key, "params"))
        
        # 更新API选项卡的标签文本
        if hasattr(self, 'api_labels'):
            for label, key in self.api_labels:
                label.config(text=self.get_translation(key, "api"))
        
        # 更新模型选项卡的标签文本
        if hasattr(self, 'model_labels'):
            for label, key in self.model_labels:
                label.config(text=self.get_translation(key, "model"))
        
        if hasattr(self, 'ollama_hint_label'):
            self.ollama_hint_label.config(text=self.get_translation("ollama_hint", "model"))
        
        # 更新复选框文本
        if hasattr(self, 'show_reasoning_cb'):
            self.show_reasoning_cb.config(text=self.get_translation("show_reasoning", "params"))
        
        # 重建各个选项卡（如果需要完全重建）
        if not hasattr(self, 'analyst_checkbuttons'):
            # 如果需要完全重建选项卡
            for i, tab_frame in enumerate(self.notebook.winfo_children()):
                tab_frame.destroy()
            
            self.create_analyst_tab()
            self.create_params_tab()
            self.create_api_tab()
            self.create_model_tab()
        
        # 恢复选中的选项卡
        self.notebook.select(current_tab)
    
    def create_analyst_tab(self):
        """创建分析师选择选项卡"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=self.get_translation("analysts", "tabs"))
        
        # 全选/全不选按钮
        button_frame = ttk.Frame(tab_frame)
        button_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 保存按钮引用以便语言切换时更新
        self.select_all_btn = ttk.Button(button_frame, text=self.get_translation("select_all", "analyst_actions"), 
                                      command=self.select_all_analysts)
        self.select_all_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.deselect_all_btn = ttk.Button(button_frame, text=self.get_translation("deselect_all", "analyst_actions"), 
                                        command=self.deselect_all_analysts)
        self.deselect_all_btn.grid(row=0, column=1)
        
        # 分析师复选框 - 使用更紧凑的布局
        self.analyst_checkbuttons = []  # 保存引用以便语言切换时更新
        for i, (key, name) in enumerate(self.analysts_config):
            row_pos = (i // 2) + 1
            col_pos = i % 2
            # 根据当前语言选择显示名称
            display_name = name if self.language_var.get() == "zh" else self.get_english_analyst_name(key)
            cb = ttk.Checkbutton(tab_frame, text=display_name, variable=self.analyst_vars[key])
            cb.grid(row=row_pos, column=col_pos, sticky=tk.W, padx=(0, 20), pady=2)
            # 保存分析师名称和对应的复选框，以便语言切换时更新
            self.analyst_checkbuttons.append((key, cb))
    
    def get_english_analyst_name(self, key):
        """获取分析师的英文名称"""
        english_names = {
            "aswath_damodaran": "Aswath Damodaran",
            "ben_graham": "Benjamin Graham",
            "bill_ackman": "Bill Ackman",
            "cathie_wood": "Cathie Wood",
            "charlie_munger": "Charlie Munger",
            "michael_burry": "Michael Burry",
            "peter_lynch": "Peter Lynch",
            "phil_fisher": "Philip Fisher",
            "stanley_druckenmiller": "Stanley Druckenmiller",
            "warren_buffett": "Warren Buffett",
            "technical_analyst": "Technical Analyst",
            "fundamentals_analyst": "Fundamentals Analyst",
            "sentiment_analyst": "Sentiment Analyst",
            "valuation_analyst": "Valuation Analyst"
        }
        return english_names.get(key, key.replace("_", " ").title())
    
    def create_params_tab(self):
        """创建基本参数配置选项卡"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=self.get_translation("params", "tabs"))
        
        # 存储标签引用以便语言切换
        self.param_labels = []
        self.param_hint_labels = []
        
        # 股票代码
        ticker_label = ttk.Label(tab_frame, text=self.get_translation("ticker", "params"))
        ticker_label.grid(row=0, column=0, sticky=tk.W, pady=3)
        self.param_labels.append((ticker_label, "ticker"))
        
        ticker_entry = ttk.Entry(tab_frame, textvariable=self.ticker_var, width=30)
        ticker_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        ticker_hint = ttk.Label(tab_frame, text=self.get_translation("ticker_hint", "params"), 
                             style="Hint.TLabel")
        ticker_hint.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        self.param_hint_labels.append((ticker_hint, "ticker_hint"))
        
        # 日期范围
        start_date_label = ttk.Label(tab_frame, text=self.get_translation("start_date", "params"))
        start_date_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        self.param_labels.append((start_date_label, "start_date"))
        
        start_date_entry = ttk.Entry(tab_frame, textvariable=self.start_date_var, width=15)
        start_date_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        start_date_hint = ttk.Label(tab_frame, text=self.get_translation("start_date_hint", "params"), 
                                 style="Hint.TLabel")
        start_date_hint.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        self.param_hint_labels.append((start_date_hint, "start_date_hint"))
        
        end_date_label = ttk.Label(tab_frame, text=self.get_translation("end_date", "params"))
        end_date_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        self.param_labels.append((end_date_label, "end_date"))
        
        end_date_entry = ttk.Entry(tab_frame, textvariable=self.end_date_var, width=15)
        end_date_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        end_date_hint = ttk.Label(tab_frame, text=self.get_translation("end_date_hint", "params"), 
                               style="Hint.TLabel")
        end_date_hint.grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        self.param_hint_labels.append((end_date_hint, "end_date_hint"))
        
        # 资金设置
        cash_label = ttk.Label(tab_frame, text=self.get_translation("initial_cash", "params"))
        cash_label.grid(row=3, column=0, sticky=tk.W, pady=3)
        self.param_labels.append((cash_label, "initial_cash"))
        
        cash_entry = ttk.Entry(tab_frame, textvariable=self.initial_cash_var, width=15)
        cash_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        cash_hint = ttk.Label(tab_frame, text=self.get_translation("initial_cash_hint", "params"), 
                           style="Hint.TLabel")
        cash_hint.grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
        self.param_hint_labels.append((cash_hint, "initial_cash_hint"))
        
        margin_label = ttk.Label(tab_frame, text=self.get_translation("margin_req", "params"))
        margin_label.grid(row=4, column=0, sticky=tk.W, pady=3)
        self.param_labels.append((margin_label, "margin_req"))
        
        margin_entry = ttk.Entry(tab_frame, textvariable=self.margin_requirement_var, width=15)
        margin_entry.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        margin_hint = ttk.Label(tab_frame, text=self.get_translation("margin_req_hint", "params"), 
                             style="Hint.TLabel")
        margin_hint.grid(row=4, column=2, sticky=tk.W, padx=(5, 0))
        self.param_hint_labels.append((margin_hint, "margin_req_hint"))
        
        # 其他选项
        self.show_reasoning_cb = ttk.Checkbutton(tab_frame, text=self.get_translation("show_reasoning", "params"), 
                                              variable=self.show_reasoning_var)
        self.show_reasoning_cb.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
    
    def create_api_tab(self):
        """创建API密钥配置选项卡"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=self.get_translation("api", "tabs"))
        
        # 存储标签引用以便语言切换
        self.api_labels = []
        
        # API Key输入框
        api_keys = ["openai", "groq", "anthropic", "deepseek", "google", "financial"]
        
        for i, key in enumerate(api_keys):
            label = ttk.Label(tab_frame, text=self.get_translation(key, "api"))
            label.grid(row=i, column=0, sticky=tk.W, pady=3)
            self.api_labels.append((label, key))
            
            var_name = f"{key}_key_var"
            if key == "financial":
                var_name = "financial_datasets_key_var"
                
            entry = ttk.Entry(tab_frame, textvariable=getattr(self, var_name), width=40)
            entry.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    def create_model_tab(self):
        """创建模型配置选项卡"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=self.get_translation("model", "tabs"))
        
        # 存储标签引用以便语言切换
        self.model_labels = []
        
        # 模型供应商选择
        provider_label = ttk.Label(tab_frame, text=self.get_translation("provider", "model"))
        provider_label.grid(row=0, column=0, sticky=tk.W, pady=3)
        self.model_labels.append((provider_label, "provider"))
        
        provider_combo = ttk.Combobox(tab_frame, textvariable=self.model_provider_var, 
                                     values=list(self.model_providers.keys()), 
                                     state="readonly", width=20)
        provider_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_changed)
        
        # 模型名称选择
        model_name_label = ttk.Label(tab_frame, text=self.get_translation("name", "model"))
        model_name_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        self.model_labels.append((model_name_label, "name"))
        
        self.model_combo = ttk.Combobox(tab_frame, textvariable=self.model_name_var, 
                                       state="readonly", width=30)
        self.model_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # 自定义模型名称输入框（仅Ollama时显示）
        custom_model_label = ttk.Label(tab_frame, text=self.get_translation("custom", "model"))
        custom_model_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        self.model_labels.append((custom_model_label, "custom"))
        
        self.custom_model_entry = ttk.Entry(tab_frame, width=30)
        self.custom_model_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # 说明文本
        self.ollama_hint_label = ttk.Label(tab_frame, text=self.get_translation("ollama_hint", "model"), 
                                        style="Hint.TLabel", foreground="blue")
        self.ollama_hint_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # 初始化模型列表
        self.on_provider_changed()
    
    def on_provider_changed(self, event=None):
        """当模型供应商改变时更新模型列表"""
        provider = self.model_provider_var.get()
        models = self.model_providers.get(provider, [])
        
        self.model_combo['values'] = models
        if models:
            self.model_name_var.set(models[0])
        
        # 显示/隐藏自定义模型输入框
        if provider == "Ollama":
            self.custom_model_entry.grid()
        else:
            self.custom_model_entry.grid_remove()
        
    def select_all_analysts(self):
        """全选分析师"""
        for var in self.analyst_vars.values():
            var.set(True)
            
    def deselect_all_analysts(self):
        """全不选分析师"""
        for var in self.analyst_vars.values():
            var.set(False)
            
    def check_dependencies(self):
        """检查依赖按钮回调"""
        # 在新线程中运行依赖检查
        def run_check():
            lang = self.language_var.get()
            try:
                # 运行依赖检查工具
                result = subprocess.run([
                    sys.executable, "dependency_checker.py"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    message = "[通过] All dependencies check passed!"
                    if lang == "zh":
                        message = "[通过] 所有依赖检查通过！"
                    messagebox.showinfo(
                        "Dependency Check" if lang == "en" else "依赖检查", 
                        message)
                else:
                    message = f"[警告] Dependency check found issues:\n{result.stdout}"
                    if lang == "zh":
                        message = f"[警告] 依赖检查发现问题:\n{result.stdout}"
                    messagebox.showwarning(
                        "Dependency Check" if lang == "en" else "依赖检查", 
                        message)
            except FileNotFoundError:
                message = "Dependency checker not found, please ensure dependency_checker.py exists"
                if lang == "zh":
                    message = "依赖检查工具未找到，请确保dependency_checker.py存在"
                messagebox.showinfo(
                    "Dependency Check" if lang == "en" else "依赖检查", 
                    message)
            except subprocess.TimeoutExpired:
                message = "Dependency check timed out"
                if lang == "zh":
                    message = "依赖检查超时"
                messagebox.showerror(
                    "Dependency Check" if lang == "en" else "依赖检查", 
                    message)
            except Exception as e:
                message = f"Dependency check error: {str(e)}"
                if lang == "zh":
                    message = f"依赖检查出错: {str(e)}"
                messagebox.showerror(
                    "Dependency Check" if lang == "en" else "依赖检查", 
                    message)
        
        threading.Thread(target=run_check, daemon=True).start()
            
    def validate_inputs(self):
        """验证输入"""
        lang = self.language_var.get()
        
        # 检查股票代码
        if not self.ticker_var.get().strip():
            message = "Please enter stock ticker(s)."
            if lang == "zh":
                message = "请输入股票代码"
            messagebox.showerror("Error" if lang == "en" else "错误", message)
            return False
            
        # 检查是否选择了至少一个分析师
        selected_analysts = [key for key, var in self.analyst_vars.items() if var.get()]
        if not selected_analysts:
            message = "Please select at least one analyst."
            if lang == "zh":
                message = "请至少选择一个分析师"
            messagebox.showerror("Error" if lang == "en" else "错误", message)
            return False
            
        # 检查初始资金
        try:
            cash = float(self.initial_cash_var.get())
            if cash <= 0:
                message = "Initial cash must be greater than 0."
                if lang == "zh":
                    message = "初始资金必须大于0"
                messagebox.showerror("Error" if lang == "en" else "错误", message)
                return False
        except ValueError:
            message = "Invalid initial cash format."
            if lang == "zh":
                message = "初始资金格式不正确"
            messagebox.showerror("Error" if lang == "en" else "错误", message)
            return False
            
        # 检查保证金要求
        try:
            margin = float(self.margin_requirement_var.get())
            if margin < 0 or margin > 1:
                message = "Margin requirement must be between 0 and 1."
                if lang == "zh":
                    message = "保证金要求必须在0-1之间"
                messagebox.showerror("Error" if lang == "en" else "错误", message)
                return False
        except ValueError:
            message = "Invalid margin requirement format."
            if lang == "zh":
                message = "保证金要求格式不正确"
            messagebox.showerror("Error" if lang == "en" else "错误", message)
            return False
            
        # 检查日期格式
        if self.start_date_var.get().strip():
            try:
                datetime.strptime(self.start_date_var.get().strip(), "%Y-%m-%d")
            except ValueError:
                message = "Invalid start date format. Please use YYYY-MM-DD."
                if lang == "zh":
                    message = "开始日期格式不正确，请使用YYYY-MM-DD格式"
                messagebox.showerror("Error" if lang == "en" else "错误", message)
                return False
                
        if self.end_date_var.get().strip():
            try:
                datetime.strptime(self.end_date_var.get().strip(), "%Y-%m-%d")
            except ValueError:
                message = "Invalid end date format. Please use YYYY-MM-DD."
                if lang == "zh":
                    message = "结束日期格式不正确，请使用YYYY-MM-DD格式"
                messagebox.showerror("Error" if lang == "en" else "错误", message)
                return False
        
        return True
        
    def create_env_file(self):
        """创建或更新.env文件 - GUI输入优先，智能合并现有配置"""
        print("[保存] 保存API密钥到.env文件...")
        
        # 读取现有.env文件内容
        existing_env = {}
        if os.path.exists('.env'):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_env[key.strip()] = value.strip()
                print("[成功] 读取现有.env文件成功")
            except Exception as e:
                print(f"[警告] 读取现有.env文件时出错: {e}")
        
        # 准备API密钥 - GUI输入优先
        gui_api_keys = {
            "OPENAI_API_KEY": self.openai_key_var.get().strip(),
            "GROQ_API_KEY": self.groq_key_var.get().strip(),
            "ANTHROPIC_API_KEY": self.anthropic_key_var.get().strip(),
            "DEEPSEEK_API_KEY": self.deepseek_key_var.get().strip(),
            "GOOGLE_API_KEY": self.google_key_var.get().strip(),
            "FINANCIAL_DATASETS_API_KEY": self.financial_datasets_key_var.get().strip()
        }
        
        # 智能合并：GUI有效输入优先，否则保留现有值
        updated_count = 0
        for key, gui_value in gui_api_keys.items():  # 修改这里，使用正确的变量名 gui_api_keys
            if gui_value and not gui_value.startswith("your_") and gui_value != "":
                # GUI有有效输入，使用GUI值
                existing_env[key] = gui_value
                print(f"[更新] 使用GUI输入更新 {key}")
                updated_count += 1
            elif key not in existing_env or not existing_env[key] or existing_env[key].startswith("your_"):
                # GUI无输入且现有值无效，设置模板值
                existing_env[key] = f"your_{key.lower()}_here"
            # else: 保留现有有效值
        
        # 确保有Ollama配置 - 使用新的获取函数
        if 'OLLAMA_BASE_URL' not in existing_env:
            existing_env['OLLAMA_BASE_URL'] = get_ollama_base_url()
        
        # 写入.env文件
        try:
            env_content = []
            lang = self.language_var.get()
            if lang == "en":
                env_content.append("# AI Hedge Fund Analysis Software - Environment Configuration")
                env_content.append("# Automatically generated and updated by GUI")
            else:
                env_content.append("# AI对冲基金分析软件 - 环境配置")
                env_content.append("# 由GUI自动生成和更新")
            env_content.append("")
            
            # 按优先级排序API密钥
            priority_keys = [
                'OPENAI_API_KEY', 'GROQ_API_KEY', 'ANTHROPIC_API_KEY', 
                'DEEPSEEK_API_KEY', 'GOOGLE_API_KEY', 'FINANCIAL_DATASETS_API_KEY',
                'OLLAMA_BASE_URL'
            ]
            
            for key in priority_keys:
                if key in existing_env:
                    env_content.append(f"{key}={existing_env[key]}")
            
            # 添加其他现有配置
            for key, value in existing_env.items():
                if key not in priority_keys:
                    env_content.append(f"{key}={value}")
            
            # 写入文件
            with open('.env', 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            print("[成功] .env文件已更新")
            if updated_count > 0:
                print(f"[成功] 从GUI更新了 {updated_count} 个API密钥")
            
            # 重新加载环境变量
            try:
                load_dotenv(override=True)
                print("[成功] 环境变量已重新加载")
            except:
                print("[警告] 无法重新加载环境变量")
            
            # 验证API密钥
            valid_keys = []
            for key in ['OPENAI_API_KEY', 'GROQ_API_KEY', 'ANTHROPIC_API_KEY', 
                       'DEEPSEEK_API_KEY', 'GOOGLE_API_KEY', 'FINANCIAL_DATASETS_API_KEY']:
                if key in existing_env and existing_env[key] and not existing_env[key].startswith('your_'):
                    valid_keys.append(key)
            
            if not valid_keys:
                message = "No valid API keys detected."
                if lang == "zh":
                    message = "[警告] 未检测到有效的API密钥。\n\n请在'API密钥配置'选项卡中输入至少一个有效的API密钥，否则软件将无法正常工作。\n\n如果使用本地Ollama模型，请切换到'模型配置'选项卡选择Ollama。"
                else:
                    message = "[警告] No valid API keys detected.\n\nPlease enter at least one valid API key in the 'API Keys' tab, otherwise the software will not work properly.\n\nIf you are using a local Ollama model, please switch to the 'Model Config' tab and select Ollama."
                
                messagebox.showwarning("API Key Warning", message)
            else:
                print(f"[成功] 检测到 {len(valid_keys)} 个有效API密钥: {', '.join(valid_keys)}")
                
        except Exception as e:
            print(f"[错误] 保存.env文件失败: {e}")
            
            message = f"Error saving .env file: {str(e)}"
            if self.language_var.get() == "zh":
                message = f"保存.env文件时出错：{str(e)}"
            
            messagebox.showerror("Save Failed", message)
        
    def run_analysis(self):
        """运行分析并显示结果 - 输出到原始终端"""
        
        # 验证输入
        if not self.validate_inputs():
            return
            
        # 创建或更新.env文件
        self.create_env_file()
        
        # 检查API密钥（如果不是使用Ollama）
        if self.model_provider_var.get() != "Ollama" and not self.has_api_key_configured():
            messagebox.showerror(
                "API密钥缺失", 
                "至少需要一个API密钥才能运行分析。\n请在API配置选项卡中填写至少一个API密钥。\n\n如果您使用本地Ollama模型，请在模型配置选项卡中选择Ollama。"
            )
            return
            
        # 检查是否选择了分析师
        selected_analysts = []
        for key, var in self.analyst_vars.items():
            if var.get():
                selected_analysts.append(key)
        
        if not selected_analysts:
            messagebox.showerror(
                "未选择分析师", 
                "请至少选择一位分析师进行分析。"
            )
            return
            
        # 收集股票代码、日期和其他参数
        stock_codes = self.ticker_var.get().strip()
        if not stock_codes:
            messagebox.showerror(
                "未输入股票代码", 
                "请输入至少一个股票代码进行分析。"
            )
            return
            
        try:
            # 解析参数
            initial_cash = float(self.initial_cash_var.get())
            margin_req = float(self.margin_requirement_var.get())
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            model_provider = self.model_provider_var.get()
            model_name = self.model_name_var.get()
            show_reasoning = self.show_reasoning_var.get()
            show_graph = self.show_graph_var.get()
            
            # 保存设置（在运行前保存设置以保存此次配置）
            self.save_settings()
            
            # 显示简单的进度提示
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title(self.get_translation("title", "progress"))
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            progress_dialog.geometry("400x200")
            progress_dialog.resizable(False, False)
            self.center_window(progress_dialog)
            
            # 设置对话框样式
            progress_dialog.configure(bg="#f0f0f0")
            frame = ttk.Frame(progress_dialog, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # 添加进度信息
            ttk.Label(frame, text=self.get_translation("analyzing", "progress"), font=("Arial", 12, "bold")).pack(pady=10)
            ttk.Label(frame, text=self.get_translation("terminal_output", "progress"), font=("Arial", 10)).pack(pady=5)
            ttk.Label(frame, text=self.get_translation("check_terminal", "progress"), font=("Arial", 10)).pack(pady=5)
            
            # 进度条
            progress_bar = ttk.Progressbar(frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=10)
            progress_bar.start()
            
            # 定义线程函数 - 直接输出到终端
            def run_analysis_thread():
                try:
                    print("\n" + "="*60)
                    print(self.get_translation("analysis_start", "progress"))
                    print("="*60)
                    print(f"{self.get_translation('stock_codes', 'progress')}: {stock_codes}")
                    print(f"{self.get_translation('initial_funds', 'progress')}: ${initial_cash:,.2f}")
                    print(f"{self.get_translation('ai_model', 'progress')}: {model_provider} - {model_name}")
                    print(f"{self.get_translation('analysts', 'progress')}: {len(selected_analysts)} 位" if self.language_var.get() == "zh" else f"{self.get_translation('analysts', 'progress')}: {len(selected_analysts)} analysts")
                    print("="*60)
                    
                    # 使用新的接口运行分析
                    from src.main import run_from_gui
                    
                    # 准备参数字典
                    args_dict = {
                        "tickers": [code.strip() for code in stock_codes.split(",")],
                        "start_date": start_date,
                        "end_date": end_date,
                        "initial_cash": initial_cash,
                        "margin_requirement": margin_req,
                        "show_reasoning": show_reasoning,
                        "selected_analysts": selected_analysts,
                        "model_name": model_name,
                        "model_provider": model_provider,
                        "show_agent_graph": show_graph
                    }
                    
                    # 直接运行分析，输出到原始终端
                    result = run_from_gui(args_dict)
                    
                    print("\n" + "="*60)
                    print(self.get_translation("analysis_complete", "progress"))
                    print("="*60)
                    
                    # 检查结果中是否有错误
                    if isinstance(result, dict) and "error" in result:
                        error_msg = result['error']
                        print(f"{self.get_translation('analysis_error', 'progress')}: {error_msg}")
                        
                        # 提供针对性的错误建议
                        suggestion = self.get_error_suggestion(error_msg)
                        if suggestion:
                            print(f"{self.get_translation('suggestion', 'progress')}: {suggestion}")
                        
                        messagebox.showerror(
                            "分析失败" if self.language_var.get() == "zh" else "Analysis Failed",
                            f"AI分析过程中出现错误:\n\n{error_msg}\n\n{suggestion if suggestion else ''}" if self.language_var.get() == "zh" else f"Error occurred during AI analysis:\n\n{error_msg}\n\n{suggestion if suggestion else ''}"
                        )
                    else:
                        print(self.get_translation("analysis_success", "progress"))
                        messagebox.showinfo(
                            "分析完成" if self.language_var.get() == "zh" else "Analysis Complete",
                            f"{self.get_translation('analysis_complete_msg', 'progress')}\n\n{self.get_translation('analysis_complete_detail', 'progress')}"
                        )
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"\n{self.get_translation('analysis_error', 'progress')}: {error_msg}")
                    traceback.print_exc()
                    
                    # 提供针对性的错误建议
                    suggestion = self.get_error_suggestion(error_msg)
                    if suggestion:
                        print(f"{self.get_translation('suggestion', 'progress')}: {suggestion}")
                    
                    messagebox.showerror(
                        "运行出错" if self.language_var.get() == "zh" else "Execution Error",
                        f"分析过程中发生错误:\n\n{error_msg}\n\n{suggestion if suggestion else '请查看终端窗口获取详细错误信息。'}" if self.language_var.get() == "zh" else f"Error occurred during analysis:\n\n{error_msg}\n\n{suggestion if suggestion else 'Please check the terminal window for detailed error information.'}"
                    )
                finally:
                    # 关闭进度对话框
                    try:
                        progress_dialog.destroy()
                    except:
                        pass
            
            # 启动线程
            threading.Thread(target=run_analysis_thread, daemon=True).start()
            
        except ValueError as e:
            messagebox.showerror(
                "输入错误", 
                f"请检查输入参数格式:\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "运行出错", 
                f"发生未知错误:\n{str(e)}"
            )
            traceback.print_exc()
        
    def save_settings(self):
        """保存设置到配置文件"""
        settings = {
            "language": self.language_var.get(),
            "ticker": self.ticker_var.get(),
            "start_date": self.start_date_var.get(),
            "end_date": self.end_date_var.get(),
            "initial_cash": self.initial_cash_var.get(),
            "margin_requirement": self.margin_requirement_var.get(),
            "show_reasoning": self.show_reasoning_var.get(),
            "model_provider": self.model_provider_var.get(),
            "model_name": self.model_name_var.get(),
            "custom_model": self.custom_model_entry.get() if hasattr(self, 'custom_model_entry') else "",
            "openai_key": self.openai_key_var.get(),
            "groq_key": self.groq_key_var.get(),
            "anthropic_key": self.anthropic_key_var.get(),
            "deepseek_key": self.deepseek_key_var.get(),
            "google_key": self.google_key_var.get(),
            "financial_datasets_key": self.financial_datasets_key_var.get(),
            "analysts": {key: var.get() for key, var in self.analyst_vars.items()}
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
            
        # 如果从配置文件加载了不同的语言，需要更新界面
        self.change_language()
        
    def load_settings(self):
        """从配置文件加载设置，API Key加载顺序：设置保存 → .env文件 → 环境变量"""
        settings = {}
            
        # 第一步：尝试从配置文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                print("[成功] 已从配置文件加载设置")
            except Exception as e:
                print(f"[警告] 加载配置文件失败: {e}")
        
        # 加载语言设置
        self.language_var.set(settings.get("language", "en"))  # 默认英文
        
        # 恢复基本设置
        self.ticker_var.set(settings.get("ticker", "AAPL,MSFT,NVDA"))
        self.start_date_var.set(settings.get("start_date", ""))
        self.end_date_var.set(settings.get("end_date", ""))
        self.initial_cash_var.set(settings.get("initial_cash", "100000.0"))
        self.margin_requirement_var.set(settings.get("margin_requirement", "0.0"))
        self.show_reasoning_var.set(settings.get("show_reasoning", False))
        
        # 恢复模型配置
        self.model_provider_var.set(settings.get("model_provider", "OpenAI"))
        # 先更新模型列表，再设置模型名称
        self.on_provider_changed()
        model_name = settings.get("model_name", "gpt-4o")
        custom_model = settings.get("custom_model", "")
        
        # 如果是Ollama且有自定义模型名称，优先使用自定义模型
        if self.model_provider_var.get() == "Ollama":
            available_models = self.model_providers.get("Ollama", [])
            if custom_model and custom_model.strip():
                # 有自定义模型，设置为自定义模型选项
                self.model_name_var.set("自定义模型")
                if hasattr(self, 'custom_model_entry'):
                    self.custom_model_entry.delete(0, tk.END)
                    self.custom_model_entry.insert(0, custom_model)
            elif model_name in available_models:
                # 模型在列表中，直接设置
                self.model_name_var.set(model_name)
                if hasattr(self, 'custom_model_entry'):
                    self.custom_model_entry.delete(0, tk.END)
            elif model_name and model_name != "自定义模型":
                # 模型不在列表中，作为自定义模型处理
                self.model_name_var.set("自定义模型")
                if hasattr(self, 'custom_model_entry'):
                    self.custom_model_entry.delete(0, tk.END)
                    self.custom_model_entry.insert(0, model_name)
            else:
                # 默认选择第一个模型
                if available_models:
                    self.model_name_var.set(available_models[0])
                if hasattr(self, 'custom_model_entry'):
                    self.custom_model_entry.delete(0, tk.END)
        else:
            # 非Ollama提供商
            self.model_name_var.set(model_name)
            if hasattr(self, 'custom_model_entry'):
                self.custom_model_entry.delete(0, tk.END)
                if custom_model:
                    self.custom_model_entry.insert(0, custom_model)
        
        # API Keys加载顺序：1. 配置文件 → 2. .env文件 → 3. 环境变量
        api_keys = {
            "openai_key": ("openai_key", "OPENAI_API_KEY"),
            "groq_key": ("groq_key", "GROQ_API_KEY"),
            "anthropic_key": ("anthropic_key", "ANTHROPIC_API_KEY"),
            "deepseek_key": ("deepseek_key", "DEEPSEEK_API_KEY"),
            "google_key": ("google_key", "GOOGLE_API_KEY"),
            "financial_datasets_key": ("financial_datasets_key", "FINANCIAL_DATASETS_API_KEY")
        }
        
        # 先从.env文件读取
        env_keys = {}
        if os.path.exists('.env'):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_keys[key.strip()] = value.strip()
            except Exception as e:
                print(f"[警告] 读取.env文件失败: {e}")
        
        for var_name, (setting_key, env_key) in api_keys.items():
            key_value = ""
            source = ""
            
            # 1. 优先从配置文件加载（如果有效）
            config_value = settings.get(setting_key, "")
            if config_value and not config_value.startswith("your_") and config_value != "":
                key_value = config_value
                source = "配置文件"
            
            # 2. 如果配置文件无效，从.env文件加载
            elif env_key in env_keys and env_keys[env_key] and not env_keys[env_key].startswith("your_"):
                key_value = env_keys[env_key]
                source = ".env文件"
            
            # 3. 最后从环境变量加载
            elif os.getenv(env_key) and not os.getenv(env_key).startswith("your_"):
                key_value = os.getenv(env_key)
                source = "环境变量"
            
            # 设置到对应变量
            if hasattr(self, f"{var_name}_var"):
                getattr(self, f"{var_name}_var").set(key_value)
                if key_value and source:
                    print(f"[成功] 已从{source}加载 {env_key}")
            else:
                print(f"[警告] 没有找到变量: {var_name}_var")
        
        # 恢复分析师选择
        analysts = settings.get("analysts", {})
        for key, var in self.analyst_vars.items():
            var.set(analysts.get(key, False))
        
        print("[完成] 设置加载完成")
        
        # 如果从配置文件加载了不同的语言，需要更新界面
        self.change_language()
        
    def quit_app(self):
        """退出应用"""
        self.save_settings()
        self.root.quit()
        self.root.destroy()

    def open_browser(self, url):
        """打开浏览器访问指定URL"""
        import webbrowser
        webbrowser.open(url)

    def get_analyst_index(self, key):
        """获取分析师在analysts_config中的索引"""
        for i, (k, name) in enumerate(self.analysts_config):
            if k == key:
                return i
        return 0

    def has_api_key_configured(self):
        """检查是否配置了至少一个API密钥"""
        # 检查是否至少有一个API密钥
        api_keys = [
            self.openai_key_var.get().strip(),
            self.groq_key_var.get().strip(),
            self.anthropic_key_var.get().strip(),
            self.google_key_var.get().strip(),
            self.deepseek_key_var.get().strip()
        ]
        return any(key for key in api_keys)

    def get_error_suggestion(self, error_msg):
        """根据错误信息提供建议"""
        error_msg_lower = error_msg.lower()
        
        # API 403 错误 - 权限被拒绝
        if "403" in error_msg or "forbidden" in error_msg_lower or "request not allowed" in error_msg_lower:
            return ("API密钥权限问题：\n"
                   "1. 检查API密钥是否正确\n"
                   "2. 确认API密钥有足够的权限\n"
                   "3. 尝试重新生成API密钥\n"
                   "4. 考虑切换到其他AI服务商")
        
        # API 402 错误 - 余额不足  
        elif "402" in error_msg or "insufficient credits" in error_msg_lower or "balance" in error_msg_lower:
            return ("API余额不足：\n"
                   "1. 检查API账户余额\n"
                   "2. 为API账户充值\n"
                   "3. 切换到有余额的其他API服务商\n"
                   "4. 考虑使用免费的本地Ollama模型")
        
        # API 401 错误 - 认证失败
        elif "401" in error_msg or "unauthorized" in error_msg_lower or "invalid api key" in error_msg_lower:
            return ("API密钥无效：\n"
                   "1. 检查API密钥是否正确输入\n"
                   "2. 确认API密钥未过期\n"
                   "3. 重新获取有效的API密钥\n"
                   "4. 检查是否选择了正确的AI服务商")
        
        # API 429 错误 - 请求频率过高
        elif "429" in error_msg or "rate limit" in error_msg_lower or "too many requests" in error_msg_lower:
            return ("API请求频率过高：\n"
                   "1. 等待几分钟后重试\n"
                   "2. 减少同时分析的股票数量\n"
                   "3. 升级API账户以获得更高限额\n"
                   "4. 切换到其他AI服务商")
        
        # 网络连接问题
        elif "connection" in error_msg_lower or "network" in error_msg_lower or "timeout" in error_msg_lower:
            return ("网络连接问题：\n"
                   "1. 检查网络连接是否正常\n"
                   "2. 尝试使用VPN或代理\n"
                   "3. 稍后重试\n"
                   "4. 检查防火墙设置")
        
        # 通用API错误
        elif "api" in error_msg_lower and ("error" in error_msg_lower or "failed" in error_msg_lower):
            return ("API服务问题：\n"
                   "1. 检查API服务状态\n"
                   "2. 尝试切换到其他AI服务商\n"
                   "3. 稍后重试\n"
                   "4. 考虑使用本地Ollama模型")
        
        return None

# 添加系统语言检测功能
def detect_system_language():
    """检测系统语言"""
    try:
        import locale
        # 替换已弃用的 getdefaultlocale 方法
        try:
            # 现代方法
            locale.setlocale(locale.LC_ALL, '')
            system_locale = locale.getlocale()[0]
        except (AttributeError, locale.Error):
            # 回退到旧方法，处理某些系统上的兼容性问题
            system_locale = locale.getdefaultlocale()[0]
            
        if system_locale:
            if system_locale.startswith('zh'):
                return "zh"
    except Exception:
        pass
    return "en"  # 默认英文

def test_package_integrity():
    """测试打包完整性 - 当以--test-mode参数运行时使用"""
    print("=" * 60)
    print("[测试] AI对冲基金分析软件-GUI - 打包完整性测试")
    print("=" * 60)
    print()
    
    # 基本Python版本检查
    print(f"[通过] Python版本: {sys.version}")
    
    # 检查重要目录
    print(f"[通过] 当前工作目录: {os.getcwd()}")
    print(f"[通过] 脚本所在目录: {os.path.dirname(os.path.abspath(__file__))}")
    
    # 检查关键依赖是否可用
    dependencies_status = []
    for module_name in ["tkinter", "json", "pandas", "numpy", "langchain_core", "openai"]:
        try:
            importlib.import_module(module_name)
            dependencies_status.append(f"[通过] {module_name}")
        except ImportError as e:
            dependencies_status.append(f"[失败] {module_name} ({str(e)})")
    
    print("\n模块导入测试:")
    for status in dependencies_status:
        print(f"  {status}")
    
    # 检查源代码文件
    print("\n源代码文件检查:")
    
    source_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'),
        os.path.join(os.getcwd(), 'src')
    ]
    
    src_found = False
    for src_path in source_paths:
        if os.path.exists(src_path):
            src_found = True
            print(f"[通过] 找到src目录: {src_path}")
            
            # 检查关键文件
            main_file = os.path.join(src_path, 'main.py')
            if os.path.exists(main_file):
                print(f"[通过] 找到main.py: {main_file}")
            else:
                print(f"[失败] 未找到main.py: {main_file}")
    
    if not src_found:
        print("[失败] 未找到src目录")
    
    # 尝试导入关键模块
    print("\n关键模块导入测试:")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            from src.main import run_hedge_fund_gui
            print("[通过] 成功导入run_hedge_fund_gui函数")
        except ImportError as e:
            print(f"[失败] 导入run_hedge_fund_gui函数失败: {str(e)}")
    except Exception as e:
        print(f"[失败] 模块导入测试失败: {str(e)}")
    
    # 测试结果汇总
    print("\n测试结果汇总:")
    success_count = sum(1 for s in dependencies_status if s.startswith("[通过]"))
    print(f"- 依赖模块检查: {success_count}/{len(dependencies_status)} 通过")
    print(f"- 源代码文件检查: {'通过' if src_found else '失败'}")
    
    overall_success = src_found and success_count >= len(dependencies_status) - 1
    
    print("\n" + "=" * 60)
    if overall_success:
        print("[成功] 打包完整性测试通过！")
    else:
        print("[失败] 打包完整性测试存在问题，可能无法正常运行")
    print("=" * 60)
    
    return 0 if overall_success else 1

def main():
    """主函数 - 完整的初始化流程"""
    # 处理命令行参数
    if '--test-mode' in sys.argv:
        return test_package_integrity()
        
    # 检查是否跳过依赖检查
    skip_deps_check = False
    if '--skip-deps-check' in sys.argv:
        skip_deps_check = True
    
    # 第一步：检查Python环境
    if not check_python_environment():
        input("按任意键退出...")
        sys.exit(1)
    
    # 第二步：导入基础模块
    if not import_basic_modules():
        input("按任意键退出...")
        sys.exit(1)
    
    # 第三步：环境检测和修复 - 如果未跳过依赖检查
    if not skip_deps_check:
        if not os.path.exists('.env'):
            create_env_from_template()
    
        # 第四步：检查AI依赖
        deps_ok, missing = check_ai_dependencies()
        if not deps_ok:
            if not prompt_install_dependencies(missing):
                input("按任意键退出...")
                sys.exit(1)
            
            # 重新检查依赖
            deps_ok, missing = check_ai_dependencies()
            if not deps_ok:
                input("按任意键退出...")
                sys.exit(1)
    
    # 第五步：导入可选模块
    import_optional_modules()
    
    # 第六步：完整环境检测
    if not skip_deps_check:
        check_and_fix_environment()
    
    # 获取系统语言
    system_lang = detect_system_language()
    
    # 第七步：启动GUI
    try:
        root = tk.Tk()
        
        # 强制显示窗口
        root.lift()
        root.focus_force()
        root.attributes('-topmost', True)
        root.after(1000, lambda: root.attributes('-topmost', False))
        
        app = HedgeFundGUI(root)
        
        # 设置默认语言 (如果没有从配置文件加载)
        if not os.path.exists(app.config_file):
            app.language_var.set(system_lang)
            app.change_language()  # 应用语言变更
        
        # 设置退出处理
        root.protocol("WM_DELETE_WINDOW", app.quit_app)
        
        root.mainloop()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("按任意键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()