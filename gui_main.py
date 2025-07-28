#!/usr/bin/env python3
"""
AI对冲基金 - Windows GUI界面
一个使用Windows经典风格的图形界面
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
try:
    from src.utils.analysts import ANALYST_CONFIG, get_agents_list
    from src.llm.models import AVAILABLE_MODELS, OLLAMA_MODELS, ModelProvider
    from src.main import run_hedge_fund, create_workflow
    from src.utils.ollama import is_ollama_installed, is_ollama_server_running, get_locally_available_models
    from dotenv import load_dotenv
except ImportError as e:
    messagebox.showerror("导入错误", f"无法导入必要的模块: {e}\n请确保所有依赖已正确安装。")
    sys.exit(1)

# 加载环境变量
load_dotenv()

class HedgeFundGUI:
    def __init__(self):
        # 创建主窗口 - 使用Windows经典风格
        self.root = tk.Tk()
        self.root.title("AI对冲基金 - 智能交易决策系统")
        self.root.geometry("1000x750")
        self.root.iconbitmap("mrcai.ico") if os.path.exists("mrcai.ico") else None
        
        # 配置窗口
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f0f0')  # Windows经典背景色
        
        # 初始化变量
        self.selected_analysts = []
        self.selected_model = None
        self.settings_file = "gui_settings.json"
        
        # 设置默认值
        self.default_settings = {
            "tickers": "AAPL,MSFT,GOOGL",
            "start_date_days": 90,  # 90天前
            "end_date_days": 0,     # 今天
            "initial_investment": "100000",
            "selected_analysts": [],
            "selected_model": "",
            "model_provider": "",
            "max_portfolio_size": "10000",
            "enable_short_selling": False,
            "cash_buffer": "5000",
            "max_position_size": "2000",
            "minimum_roi": "0.05",
            "window_geometry": "1000x750"
        }
        self.selected_provider = None
        self.results_data = None
        self.is_running = False
        
        # 分析师中文名称映射
        self.analyst_chinese_names = {
            "aswath_damodaran": "阿斯瓦斯·达莫达兰 (估值教父)",
            "ben_graham": "本杰明·格雷厄姆 (价值投资之父)", 
            "bill_ackman": "比尔·阿克曼 (激进投资者)",
            "cathie_wood": "凯茜·伍德 (成长投资女王)",
            "charlie_munger": "查理·芒格 (理性思考者)",
            "michael_burry": "迈克尔·伯里 (大空头)",
            "peter_lynch": "彼得·林奇 (十倍股猎手)",
            "phil_fisher": "菲利普·费雪 (成长投资先驱)",
            "rakesh_jhunjhunwala": "拉凯什·朱恩朱瓦拉 (印度股神)",
            "stanley_druckenmiller": "斯坦利·德鲁肯米勒 (宏观投资大师)",
            "warren_buffett": "沃伦·巴菲特 (股神)",
            "technical_analyst": "技术分析师 (图表专家)",
            "fundamentals_analyst": "基本面分析师 (财务专家)", 
            "sentiment_analyst": "情绪分析师 (市场心理学家)",
            "valuation_analyst": "估值分析师 (价值评估专家)"
        }
        
        # 分析师中文描述映射
        self.analyst_chinese_descriptions = {
            "aswath_damodaran": "估值教父，专注内在价值分析",
            "ben_graham": "价值投资之父，寻找安全边际",
            "bill_ackman": "激进投资者，推动企业变革", 
            "cathie_wood": "成长投资女王，专注颠覆性创新",
            "charlie_munger": "理性思考者，偏好优质企业",
            "michael_burry": "大空头，逆向投资专家",
            "peter_lynch": "十倍股猎手，投资身边熟悉企业",
            "phil_fisher": "成长投资先驱，深度研究企业",
            "rakesh_jhunjhunwala": "印度股神，新兴市场专家",
            "stanley_druckenmiller": "宏观投资大师，把握经济周期",
            "warren_buffett": "股神，寻找护城河企业",
            "technical_analyst": "技术分析师，研究图表趋势",
            "fundamentals_analyst": "基本面分析师，深入财务分析",
            "sentiment_analyst": "情绪分析师，分析市场心理",
            "valuation_analyst": "估值分析师，计算企业价值"
        }
        
        # 加载保存的设置
        self.saved_settings = self.load_settings()
        
        self.setup_ui()
        
        # 应用保存的设置
        self.root.after(100, lambda: self.apply_settings(self.saved_settings))
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(
            main_frame, 
            text="AI对冲基金 - 智能交易决策系统",
            font=("Microsoft YaHei", 16, "bold"),
            bg='#f0f0f0',
            fg='#000080'
        )
        title_label.pack(pady=(0, 15))
        
        # 创建笔记本控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基础配置页面
        basic_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(basic_frame, text="基础配置")
        
        # 分析师选择页面
        analysts_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(analysts_frame, text="分析师选择")
        
        # 模型设置页面
        model_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(model_frame, text="模型设置")
        
        # 高级选项页面
        advanced_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(advanced_frame, text="高级选项")
        
        # 结果页面
        results_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(results_frame, text="分析结果")
        
        # 设置各个页面
        self.setup_basic_page(basic_frame)
        self.setup_analysts_page(analysts_frame)
        self.setup_model_page(model_frame)
        self.setup_advanced_page(advanced_frame)
        self.setup_results_page(results_frame)
        
    def setup_basic_page(self, parent):
        """设置基础配置页面"""
        main_frame = tk.Frame(parent, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. 股票选择区域
        stock_frame = tk.LabelFrame(main_frame, text="股票选择", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        stock_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(stock_frame, text="股票代码 (用逗号分隔):", bg='#f0f0f0', font=('Microsoft YaHei', 9)).pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.stock_entry = tk.Entry(stock_frame, font=('Microsoft YaHei', 10), width=50)
        self.stock_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.stock_entry.insert(0, "AAPL,MSFT,NVDA")
        
        # 2. 日期选择区域
        date_frame = tk.LabelFrame(main_frame, text="分析时间范围", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        date_container = tk.Frame(date_frame, bg='#f0f0f0')
        date_container.pack(fill=tk.X, padx=10, pady=10)
        
        # 开始日期
        start_frame = tk.Frame(date_container, bg='#f0f0f0')
        start_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(start_frame, text="开始日期:", bg='#f0f0f0', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
        self.start_date_entry = tk.Entry(start_frame, font=('Microsoft YaHei', 10))
        self.start_date_entry.pack(fill=tk.X, pady=(5, 0))
        # 设置默认为3个月前
        default_start = datetime.now() - relativedelta(months=3)
        self.start_date_entry.insert(0, default_start.strftime("%Y-%m-%d"))
        
        # 结束日期
        end_frame = tk.Frame(date_container, bg='#f0f0f0')
        end_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(end_frame, text="结束日期:", bg='#f0f0f0', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
        self.end_date_entry = tk.Entry(end_frame, font=('Microsoft YaHei', 10))
        self.end_date_entry.pack(fill=tk.X, pady=(5, 0))
        # 设置默认为今天
        self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 3. 投资组合设置
        portfolio_frame = tk.LabelFrame(main_frame, text="投资组合设置", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        portfolio_frame.pack(fill=tk.X, pady=(0, 15))
        
        portfolio_container = tk.Frame(portfolio_frame, bg='#f0f0f0')
        portfolio_container.pack(fill=tk.X, padx=10, pady=10)
        
        # 初始资金
        cash_frame = tk.Frame(portfolio_container, bg='#f0f0f0')
        cash_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(cash_frame, text="初始资金 ($):", bg='#f0f0f0', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
        self.cash_entry = tk.Entry(cash_frame, font=('Microsoft YaHei', 10))
        self.cash_entry.pack(fill=tk.X, pady=(5, 0))
        self.cash_entry.insert(0, "100000")
        
        # 保证金要求
        margin_frame = tk.Frame(portfolio_container, bg='#f0f0f0')
        margin_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(margin_frame, text="保证金要求 ($):", bg='#f0f0f0', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
        self.margin_entry = tk.Entry(margin_frame, font=('Microsoft YaHei', 10))
        self.margin_entry.pack(fill=tk.X, pady=(5, 0))
        self.margin_entry.insert(0, "0")
        
        # 4. Ollama快速状态检查
        ollama_frame = tk.LabelFrame(main_frame, text="本地模型状态 (Ollama)", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        ollama_frame.pack(fill=tk.X, pady=(0, 15))
        
        ollama_container = tk.Frame(ollama_frame, bg='#f0f0f0')
        ollama_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Ollama状态显示
        self.ollama_status_var = tk.StringVar(value="检查中...")
        ollama_status_label = tk.Label(ollama_container, textvariable=self.ollama_status_var, bg='#f0f0f0', font=('Microsoft YaHei', 9))
        ollama_status_label.pack(anchor=tk.W)
        
        # 刷新状态按钮
        refresh_btn = tk.Button(
            ollama_container,
            text="刷新状态",
            command=self.refresh_ollama_status,
            bg='#6c757d',
            fg='white',
            font=('Microsoft YaHei', 9),
            width=10
        )
        refresh_btn.pack(anchor=tk.W, pady=(5, 0))
        
        # 初始检查Ollama状态
        self.refresh_ollama_status()
        
        # 运行按钮
        run_frame = tk.Frame(main_frame, bg='#f0f0f0')
        run_frame.pack(fill=tk.X, pady=20)
        
        self.run_button = tk.Button(
            run_frame,
            text="开始分析",
            command=self.run_analysis,
            font=('Microsoft YaHei', 12, 'bold'),
            bg='#0078d4',
            fg='white',
            width=15,
            height=2
        )
        self.run_button.pack(anchor=tk.CENTER)
        
        # 进度条
        self.progress_var = tk.StringVar(value="准备就绪")
        self.progress_label = tk.Label(run_frame, textvariable=self.progress_var, bg='#f0f0f0', font=('Microsoft YaHei', 9))
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(
            run_frame,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10), padx=50)
    
    def setup_analysts_page(self, parent):
        """设置分析师选择页面"""
        main_frame = tk.Frame(parent, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 分析师选择区域
        analysts_frame = tk.LabelFrame(main_frame, text="AI分析师选择", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        analysts_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明和按钮
        info_frame = tk.Frame(analysts_frame, bg='#f0f0f0')
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(info_frame, text="选择分析师 (可多选):", bg='#f0f0f0', font=('Microsoft YaHei', 9, 'bold')).pack(anchor=tk.W)
        
        # 全选/清空按钮
        buttons_frame = tk.Frame(info_frame, bg='#f0f0f0')
        buttons_frame.pack(anchor=tk.W, pady=(5, 0))
        
        select_all_btn = tk.Button(
            buttons_frame, 
            text="全选", 
            command=self.select_all_analysts,
            bg='#28a745',
            fg='white',
            font=('Microsoft YaHei', 9),
            width=8
        )
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_all_btn = tk.Button(
            buttons_frame, 
            text="清空", 
            command=self.clear_all_analysts,
            bg='#6c757d',
            fg='white',
            font=('Microsoft YaHei', 9),
            width=8
        )
        clear_all_btn.pack(side=tk.LEFT)
        
        # 创建滚动框架
        canvas = tk.Canvas(analysts_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(analysts_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=(0, 10))
        scrollbar.pack(side="right", fill="y", pady=(0, 10))
        
        # 分析师容器
        analysts_container = tk.Frame(scrollable_frame, bg='#f0f0f0')
        analysts_container.pack(fill=tk.X, padx=10, pady=5)
        
        # 分成三列显示
        left_col = tk.Frame(analysts_container, bg='#f0f0f0')
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        middle_col = tk.Frame(analysts_container, bg='#f0f0f0')
        middle_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_col = tk.Frame(analysts_container, bg='#f0f0f0')
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建分析师复选框
        self.analyst_vars = {}
        analyst_items = list(ANALYST_CONFIG.items())
        
        for i, (key, config) in enumerate(analyst_items):
            var = tk.BooleanVar()
            self.analyst_vars[key] = var
            
            # 根据索引分配到不同列
            if i % 3 == 0:
                container = left_col
            elif i % 3 == 1:
                container = middle_col
            else:
                container = right_col
            
            # 创建框架包含复选框和描述
            item_frame = tk.Frame(container, bg='#f0f0f0', relief=tk.RIDGE, bd=1)
            item_frame.pack(fill=tk.X, pady=2, padx=2)
            
            # 复选框
            chinese_name = self.analyst_chinese_names.get(key, config["display_name"])
            cb = tk.Checkbutton(
                item_frame,
                text=chinese_name,
                variable=var,
                bg='#f0f0f0',
                font=('Microsoft YaHei', 9, 'bold'),
                fg='#000080'
            )
            cb.pack(anchor=tk.W, padx=5, pady=(5, 2))
            
            # 描述文本
            chinese_desc = self.analyst_chinese_descriptions.get(key, config['description'])
            desc_label = tk.Label(
                item_frame,
                text=chinese_desc,
                font=('Microsoft YaHei', 8),
                fg='#666666',
                bg='#f0f0f0',
                wraplength=180,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # 默认选择所有分析师
        self.select_all_analysts()
    
    def setup_model_page(self, parent):
        """设置模型设置页面"""
        main_frame = tk.Frame(parent, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 模型选择区域
        model_frame = tk.LabelFrame(main_frame, text="AI模型选择", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        model_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(model_frame, text="选择AI模型:", bg='#f0f0f0', font=('Microsoft YaHei', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var,
            state="readonly",
            font=('Microsoft YaHei', 10),
            width=60
        )
        self.model_combo.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        # 刷新模型列表按钮
        refresh_frame = tk.Frame(model_frame, bg='#f0f0f0')
        refresh_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        refresh_btn = tk.Button(
            refresh_frame,
            text="刷新模型列表",
            command=self.refresh_model_list,
            bg='#6c757d',
            fg='white',
            font=('Microsoft YaHei', 9),
            width=12
        )
        refresh_btn.pack(anchor=tk.E)
        
        # 初始化模型列表
        self.refresh_model_list()
        
        # 模型说明区域
        info_frame = tk.LabelFrame(main_frame, text="模型说明", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        info_text = tk.Text(info_frame, bg='white', font=('Microsoft YaHei', 9), wrap=tk.WORD, state=tk.DISABLED, height=15)
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        info_scrollbar.pack(side="right", fill="y", pady=10)
        
        # 添加模型信息
        model_info = """支持的AI模型提供商：

【云端模型】
• OpenAI (推荐)
  - GPT-4: 最强大的通用模型，适合复杂分析
  - GPT-4 Turbo: 更快的GPT-4版本
  - GPT-3.5 Turbo: 经济实惠，适合一般分析

• Anthropic
  - Claude-3 Sonnet: 平衡性能和成本
  - Claude-3 Haiku: 快速响应，适合简单任务

• Groq
  - 高速推理优化，响应更快
  - 特别适合需要快速结果的场景

• DeepSeek
  - 专业金融分析模型
  - 在投资分析方面表现优秀

• Google
  - Gemini Pro系列
  - 多模态能力强

【本地模型 - Ollama】
• Ollama (本地部署)
  - 支持多种开源大模型
  - 数据完全本地化，保护隐私
  - 无需API费用，一次部署长期使用
  - 需要先安装Ollama软件

使用建议：
- 首次使用建议选择OpenAI GPT-4
- 追求速度可选择Groq模型
- 预算有限可选择GPT-3.5 Turbo
- 专业金融分析可选择DeepSeek
- 注重隐私可选择Ollama本地模型

Ollama安装方法：
1. 下载: https://ollama.ai/
2. 安装后运行: ollama pull llama2
3. 启动GUI时选择Ollama模型"""
        
        info_text.config(state=tk.NORMAL)
        info_text.insert(tk.END, model_info)
        info_text.config(state=tk.DISABLED)
    
    def setup_advanced_page(self, parent):
        """设置高级选项页面"""
        main_frame = tk.Frame(parent, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 高级选项区域
        options_frame = tk.LabelFrame(main_frame, text="高级选项", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 显示推理过程选项
        self.show_reasoning_var = tk.BooleanVar()
        reasoning_cb = tk.Checkbutton(
            options_frame,
            text="显示分析师推理过程",
            variable=self.show_reasoning_var,
            bg='#f0f0f0',
            font=('Microsoft YaHei', 10),
            fg='#000080'
        )
        reasoning_cb.pack(anchor=tk.W, padx=10, pady=10)
        
        # API配置说明区域
        api_frame = tk.LabelFrame(main_frame, text="API配置说明", bg='#f0f0f0', fg='#000080', font=('Microsoft YaHei', 10, 'bold'))
        api_frame.pack(fill=tk.BOTH, expand=True)
        
        api_text = tk.Text(api_frame, bg='white', font=('Microsoft YaHei', 9), wrap=tk.WORD, state=tk.DISABLED, height=20)
        api_scrollbar = ttk.Scrollbar(api_frame, orient="vertical", command=api_text.yview)
        api_text.configure(yscrollcommand=api_scrollbar.set)
        
        api_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        api_scrollbar.pack(side="right", fill="y", pady=10)
        
        # 添加API配置信息
        api_info = """API密钥配置指南：

1. 创建 .env 文件
在项目根目录创建名为 .env 的文件，添加以下内容：

# 至少设置一个LLM API密钥
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 金融数据API密钥（可选）
FINANCIAL_DATASETS_API_KEY=your_financial_datasets_api_key

# Ollama本地配置（可选）
# OLLAMA_HOST=localhost
# OLLAMA_BASE_URL=http://localhost:11434

2. 获取API密钥链接：

• OpenAI API: https://platform.openai.com/api-keys
• Groq API: https://console.groq.com/keys
• Anthropic API: https://console.anthropic.com/
• DeepSeek API: https://platform.deepseek.com/api_keys
• Financial Datasets API: https://financialdatasets.ai/

3. Ollama本地模型配置：

• 下载安装: https://ollama.ai/
• 安装模型: ollama pull llama2
• 查看已安装模型: ollama list
• 启动服务: ollama serve (通常自动启动)
• 默认端口: 11434

4. 重要说明：

• 云端模型需要至少设置一个LLM API密钥
• Ollama本地模型不需要API密钥，但需要安装Ollama
• 对于AAPL、GOOGL、MSFT、NVDA、TSLA股票，不需要金融数据API密钥
• 分析其他股票需要设置 FINANCIAL_DATASETS_API_KEY
• 请妥善保管API密钥，不要泄露给他人

5. 费用说明：

• OpenAI: 按使用量收费，GPT-4相对较贵
• Groq: 目前免费或收费很低
• Anthropic: 按使用量收费
• DeepSeek: 价格相对便宜
• Ollama: 完全免费，本地运行
• Financial Datasets: 有免费额度"""
        
        api_text.config(state=tk.NORMAL)
        api_text.insert(tk.END, api_info)
        api_text.config(state=tk.DISABLED)
        
    def setup_results_page(self, parent):
        """设置结果页面"""
        # 结果显示区域
        results_container = tk.Frame(parent, bg='#f0f0f0')
        results_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            results_container,
            text="分析结果",
            font=("Microsoft YaHei", 14, "bold"),
            bg='#f0f0f0',
            fg='#000080'
        )
        title_label.pack(pady=(0, 15))
        
        # 创建文本显示区域
        text_frame = tk.Frame(results_container, bg='#f0f0f0')
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 结果文本框
        self.results_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="white",
            fg="#000000",
            insertbackground="#000000",
            relief=tk.SUNKEN,
            bd=2
        )
        
        # 滚动条
        scrollbar_results = ttk.Scrollbar(text_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar_results.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        scrollbar_results.pack(side="right", fill="y")
        
        # 操作按钮
        buttons_frame = tk.Frame(results_container, bg='#f0f0f0')
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 保存结果按钮
        save_btn = tk.Button(
            buttons_frame,
            text="保存结果",
            command=self.save_results,
            bg='#28a745',
            fg='white',
            font=('Microsoft YaHei', 10),
            width=12
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空结果按钮
        clear_btn = tk.Button(
            buttons_frame,
            text="清空结果",
            command=self.clear_results,
            bg='#6c757d',
            fg='white',
            font=('Microsoft YaHei', 10),
            width=12
        )
        clear_btn.pack(side=tk.LEFT)
        
    def select_all_analysts(self):
        """选择所有分析师"""
        for var in self.analyst_vars.values():
            var.set(True)
    
    def clear_all_analysts(self):
        """清空所有分析师选择"""
        for var in self.analyst_vars.values():
            var.set(False)
    
    def refresh_ollama_status(self):
        """刷新Ollama状态"""
        try:
            if not is_ollama_installed():
                self.ollama_status_var.set("❌ Ollama未安装 - 请访问 https://ollama.ai/ 下载")
                return
                
            if not is_ollama_server_running():
                self.ollama_status_var.set("⚠️ Ollama已安装但服务未运行 - 请运行: ollama serve")
                return
                
            # 获取已安装的模型
            available_models = get_locally_available_models()
            if available_models:
                models_str = ", ".join(available_models[:3])  # 只显示前3个
                if len(available_models) > 3:
                    models_str += f" 等{len(available_models)}个模型"
                self.ollama_status_var.set(f"✅ Ollama运行正常 - 已安装模型: {models_str}")
            else:
                self.ollama_status_var.set("✅ Ollama运行正常但无已安装模型 - 运行: ollama pull llama3.1")
                
        except Exception as e:
            self.ollama_status_var.set(f"❌ 检查Ollama状态时出错: {str(e)}")
        
        # 同时刷新模型列表
        if hasattr(self, 'model_combo'):
            self.refresh_model_list()
    
    def refresh_model_list(self):
        """刷新模型列表，动态获取可用的Ollama模型"""
        model_options = []
        
        # 添加云端模型
        for model in AVAILABLE_MODELS:
            model_options.append(f"{model.display_name} ({model.provider.value})")
        
        # 动态获取Ollama本地模型
        try:
            if is_ollama_installed() and is_ollama_server_running():
                available_models = get_locally_available_models()
                if available_models:
                    model_options.append("--- 本地模型 (Ollama) ---")
                    for model_name in available_models:
                        # 显示模型名称，格式化为用户友好的名称
                        display_name = model_name.replace(':', ' ').title()
                        model_options.append(f"{display_name} (Ollama)")
        except Exception as e:
            print(f"获取Ollama模型时出错: {e}")
        
        # 更新下拉框选项
        current_selection = self.model_var.get()
        self.model_combo['values'] = model_options
        
        # 尝试保持当前选择，如果不存在则选择第一个
        if current_selection in model_options:
            self.model_combo.set(current_selection)
        elif model_options:
            self.model_combo.set(model_options[0])
    
    def get_selected_analysts(self):
        """获取选中的分析师"""
        return [key for key, var in self.analyst_vars.items() if var.get()]
    
    def get_selected_model_info(self):
        """获取选中的模型信息"""
        selected = self.model_var.get()
        if not selected:
            return None, None
        
        # 跳过分隔符
        if selected.startswith("---"):
            return None, None
        
        # 解析云端模型
        for model in AVAILABLE_MODELS:
            if f"{model.display_name} ({model.provider.value})" == selected:
                return model.model_name, model.provider.value
        
        # 解析Ollama本地模型
        if selected.endswith("(Ollama)"):
            model_display = selected.replace(" (Ollama)", "")
            # 将显示名称转换回实际的模型名称
            # 例如: "Llama3 1 8B Instruct" -> "llama3.1:8b-instruct"
            try:
                available_models = get_locally_available_models()
                # 尝试通过显示名称匹配实际模型名称
                for model_name in available_models:
                    formatted_display = model_name.replace(':', ' ').title()
                    if formatted_display == model_display:
                        return model_name, "Ollama"
                # 如果没有找到精确匹配，尝试模糊匹配
                for model_name in available_models:
                    if model_display.lower().replace(' ', '') in model_name.lower().replace(':', '').replace('-', ''):
                        return model_name, "Ollama"
            except Exception as e:
                print(f"解析Ollama模型时出错: {e}")
                # 作为备选，直接将显示名称转换为小写并用冒号分隔
                model_name = model_display.lower().replace(' ', ':')
                return model_name, "Ollama"
        
        return None, None
    
    def validate_inputs(self):
        """验证输入"""
        # 检查股票代码
        tickers = self.stock_entry.get().strip()
        if not tickers:
            messagebox.showerror("输入错误", "请输入股票代码")
            return False
        
        # 检查日期
        try:
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("输入错误", "日期格式不正确，请使用 YYYY-MM-DD 格式")
            return False
        
        # 检查资金
        try:
            float(self.cash_entry.get())
            float(self.margin_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "初始资金和保证金要求必须是数字")
            return False
        
        # 检查分析师选择
        if not self.get_selected_analysts():
            messagebox.showerror("选择错误", "请至少选择一个分析师")
            return False
        
        # 检查模型选择
        model_name, provider = self.get_selected_model_info()
        if not model_name:
            messagebox.showerror("选择错误", "请选择一个AI模型")
            return False
        
        # 如果选择了Ollama模型，检查Ollama是否可用
        if provider == "Ollama":
            if not is_ollama_installed():
                messagebox.showerror("Ollama错误", 
                    "Ollama未安装\n请访问 https://ollama.ai/ 下载安装\n\n安装后请重启本程序")
                return False
                
            if not is_ollama_server_running():
                messagebox.showerror("Ollama错误", 
                    "Ollama服务未运行\n请在命令行中运行: ollama serve\n或重启Ollama应用")
                return False
                
            # 检查所选模型是否已下载
            available_models = get_locally_available_models()
            if model_name not in available_models:
                response = messagebox.askyesno("模型未找到", 
                    f"模型 {model_name} 未在本地找到\n\n是否现在下载？\n(可能需要几分钟到几小时，取决于模型大小)")
                if response:
                    messagebox.showinfo("下载提示", 
                        f"请在命令行中运行:\nollama pull {model_name}\n\n下载完成后重新开始分析")
                return False
        
        return True
    
    def run_analysis(self):
        """运行分析"""
        if self.is_running:
            messagebox.showwarning("警告", "分析正在进行中，请等待完成")
            return
        
        if not self.validate_inputs():
            return
        
        # 启动分析线程
        self.is_running = True
        self.run_button.config(state="disabled", text="分析中...")
        self.progress_var.set("正在准备分析...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._run_analysis_thread)
        thread.daemon = True
        thread.start()
    
    def _run_analysis_thread(self):
        """分析线程"""
        try:
            # 获取输入参数
            tickers = [t.strip().upper() for t in self.stock_entry.get().split(",")]
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            initial_cash = float(self.cash_entry.get())
            margin_requirement = float(self.margin_entry.get())
            selected_analysts = self.get_selected_analysts()
            model_name, model_provider = self.get_selected_model_info()
            show_reasoning = self.show_reasoning_var.get()
            
            # 更新状态
            self.root.after(0, lambda: self.progress_var.set("正在初始化投资组合..."))
            
            # 初始化投资组合
            portfolio = {
                "cash": initial_cash,
                "margin_requirement": margin_requirement,
                "margin_used": 0.0,
                "positions": {
                    ticker: {
                        "long": 0,
                        "short": 0,
                        "long_cost_basis": 0.0,
                        "short_cost_basis": 0.0,
                        "short_margin_used": 0.0,
                    }
                    for ticker in tickers
                },
                "realized_gains": {
                    ticker: {
                        "long": 0.0,
                        "short": 0.0,
                    }
                    for ticker in tickers
                },
            }
            
            # 更新状态
            self.root.after(0, lambda: self.progress_var.set("正在运行AI分析..."))
            
            # 运行分析
            result = run_hedge_fund(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                portfolio=portfolio,
                show_reasoning=show_reasoning,
                selected_analysts=selected_analysts,
                model_name=model_name,
                model_provider=model_provider,
            )
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self._analysis_completed(result))
            
        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            self.root.after(0, lambda: self._analysis_failed(error_msg))
    
    def _analysis_completed(self, result):
        """分析完成回调"""
        self.is_running = False
        self.run_button.config(state="normal", text="开始分析")
        self.progress_bar.stop()
        self.progress_var.set("分析完成")
        
        # 保存结果
        self.results_data = result
        
        # 显示结果
        self.display_results(result)
        
        # 切换到结果页面
        self.notebook.select(4)  # 选择结果页面（索引4）
    
    def _analysis_failed(self, error_msg):
        """分析失败回调"""
        self.is_running = False
        self.run_button.config(state="normal", text="开始分析")
        self.progress_bar.stop()
        self.progress_var.set("分析失败")
        
        messagebox.showerror("分析错误", error_msg)
    
    def display_results(self, result):
        """显示分析结果"""
        self.results_text.delete(1.0, tk.END)
        
        if not result:
            self.results_text.insert(tk.END, "没有分析结果\n")
            return
        
        # 格式化显示结果
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("AI对冲基金分析结果")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        # 显示交易决策
        if "decisions" in result and result["decisions"]:
            decisions = result["decisions"]
            output_lines.append("📊 投资组合决策:")
            output_lines.append("-" * 40)
            
            if "reasoning" in decisions:
                output_lines.append(f"决策理由: {decisions['reasoning']}")
                output_lines.append("")
            
            if "actions" in decisions:
                output_lines.append("📈 推荐操作:")
                for i, action in enumerate(decisions["actions"], 1):
                    output_lines.append(f"{i}. {action}")
                output_lines.append("")
            
            if "portfolio_summary" in decisions:
                summary = decisions["portfolio_summary"]
                output_lines.append("💰 投资组合摘要:")
                output_lines.append(f"总价值: ${summary.get('total_value', 'N/A'):.2f}" if isinstance(summary.get('total_value'), (int, float)) else f"总价值: {summary.get('total_value', 'N/A')}")
                output_lines.append(f"现金: ${summary.get('cash', 'N/A'):.2f}" if isinstance(summary.get('cash'), (int, float)) else f"现金: {summary.get('cash', 'N/A')}")
                output_lines.append(f"收益率: {summary.get('return_pct', 'N/A'):.2f}%" if isinstance(summary.get('return_pct'), (int, float)) else f"收益率: {summary.get('return_pct', 'N/A')}")
                output_lines.append("")
        
        # 显示分析师信号
        if "analyst_signals" in result and result["analyst_signals"]:
            output_lines.append("🤖 分析师信号:")
            output_lines.append("-" * 40)
            
            for analyst, signal in result["analyst_signals"].items():
                output_lines.append(f"{analyst}:")
                if isinstance(signal, dict):
                    for key, value in signal.items():
                        output_lines.append(f"  {key}: {value}")
                else:
                    output_lines.append(f"  {signal}")
                output_lines.append("")
        
        # 显示在文本框中
        full_text = "\n".join(output_lines)
        self.results_text.insert(tk.END, full_text)
        
        # 滚动到顶部
        self.results_text.see(1.0)
    
    def save_results(self):
        """保存结果到文件"""
        if not self.results_data:
            messagebox.showwarning("警告", "没有结果可保存")
            return
        
        # 选择保存位置
        filename = filedialog.asksaveasfilename(
            title="保存分析结果",
            defaultextension=".html",
            filetypes=[
                ("HTML files", "*.html"),
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                if filename.endswith('.html'):
                    html_content = self.generate_html_report()
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                elif filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.results_data, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.results_text.get(1.0, tk.END))
                
                messagebox.showinfo("成功", f"结果已保存到: {filename}")
                
                # 如果是HTML文件，询问是否打开
                if filename.endswith('.html'):
                    if messagebox.askyesno("打开文件", "是否在浏览器中打开生成的HTML报告？"):
                        import webbrowser
                        webbrowser.open(f"file://{os.path.abspath(filename)}")
                        
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def generate_html_report(self):
        """生成美观的HTML分析报告"""
        if not self.results_data:
            return "<html><body><h1>没有分析结果</h1></body></html>"
        
        # 获取当前配置信息
        tickers = self.stock_entry.get().strip()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        initial_cash = self.cash_entry.get()
        selected_analysts = self.get_selected_analysts()
        model_name, model_provider = self.get_selected_model_info()
        
        # 获取选中的分析师中文名称
        selected_analyst_names = []
        for analyst_key in selected_analysts:
            chinese_name = self.analyst_chinese_names.get(analyst_key, analyst_key)
            selected_analyst_names.append(chinese_name)
        
        result = self.results_data
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI对冲基金分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 30px;
            border-left: 5px solid #2a5298;
        }}
        
        .section h2 {{
            color: #2a5298;
            font-size: 1.8rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}
        
        .section h2::before {{
            content: '';
            width: 8px;
            height: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-right: 15px;
            border-radius: 4px;
        }}
        
        .config-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .config-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .config-item h3 {{
            color: #2a5298;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }}
        
        .config-item p {{
            color: #666;
            font-size: 1rem;
        }}
        
        .highlight {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .actions-list {{
            list-style: none;
            padding: 0;
        }}
        
        .actions-list li {{
            background: white;
            margin: 10px 0;
            padding: 15px 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        .portfolio-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .summary-card h4 {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .summary-card .value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #2a5298;
        }}
        
        .analyst-signals {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .analyst-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-top: 4px solid #667eea;
        }}
        
        .analyst-card h4 {{
            color: #2a5298;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }}
        
        .signal-content {{
            color: #555;
            line-height: 1.6;
        }}
        
        .emoji {{
            font-size: 1.5rem;
            margin-right: 10px;
        }}
        
        .timestamp {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            color: #666;
        }}
        
        .analysts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        
        .analyst-tag {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            text-align: center;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            .content {{
                padding: 20px;
            }}
            .section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI对冲基金分析报告</h1>
            <div class="subtitle">智能投资决策系统 · 专业分析报告</div>
        </div>
        
        <div class="content">
            <!-- 配置信息 -->
            <div class="section">
                <h2><span class="emoji">⚙️</span>分析配置</h2>
                <div class="config-grid">
                    <div class="config-item">
                        <h3>📈 分析标的</h3>
                        <p><span class="highlight">{tickers}</span></p>
                    </div>
                    <div class="config-item">
                        <h3>📅 分析时间范围</h3>
                        <p>{start_date} 至 {end_date}</p>
                    </div>
                    <div class="config-item">
                        <h3>💰 初始资金</h3>
                        <p><span class="highlight">${initial_cash}</span></p>
                    </div>
                    <div class="config-item">
                        <h3>🤖 AI模型</h3>
                        <p>{model_name} <small>({model_provider})</small></p>
                    </div>
                </div>
                
                <h3>🧠 参与分析的AI分析师 ({len(selected_analyst_names)}位)</h3>
                <div class="analysts-grid">"""
        
        # 添加分析师标签
        for analyst_name in selected_analyst_names:
            html_content += f'<div class="analyst-tag">{analyst_name}</div>'
        
        html_content += """
                </div>
            </div>"""
        
        # 添加投资决策部分
        if "decisions" in result and result["decisions"]:
            decisions = result["decisions"]
            html_content += f"""
            <!-- 投资决策 -->
            <div class="section">
                <h2><span class="emoji">📊</span>投资组合决策</h2>"""
            
            if "reasoning" in decisions:
                html_content += f"""
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #17a2b8;">
                    <h4 style="color: #17a2b8; margin-bottom: 10px;">💡 决策理由</h4>
                    <p style="line-height: 1.6;">{decisions['reasoning']}</p>
                </div>"""
            
            if "actions" in decisions:
                html_content += f"""
                <h3 style="color: #2a5298; margin: 20px 0;">📋 推荐操作</h3>
                <ul class="actions-list">"""
                for action in decisions["actions"]:
                    html_content += f"<li>✅ {action}</li>"
                html_content += "</ul>"
            
            if "portfolio_summary" in decisions:
                summary = decisions["portfolio_summary"]
                html_content += f"""
                <h3 style="color: #2a5298; margin: 30px 0 20px 0;">💼 投资组合摘要</h3>
                <div class="portfolio-summary">
                    <div class="summary-card">
                        <h4>总价值</h4>
                        <div class="value">${summary.get('total_value', 'N/A'):.2f if isinstance(summary.get('total_value'), (int, float)) else summary.get('total_value', 'N/A')}</div>
                    </div>
                    <div class="summary-card">
                        <h4>现金余额</h4>
                        <div class="value">${summary.get('cash', 'N/A'):.2f if isinstance(summary.get('cash'), (int, float)) else summary.get('cash', 'N/A')}</div>
                    </div>
                    <div class="summary-card">
                        <h4>收益率</h4>
                        <div class="value" style="color: {'#28a745' if isinstance(summary.get('return_pct'), (int, float)) and summary.get('return_pct', 0) > 0 else '#dc3545'}">{summary.get('return_pct', 'N/A'):.2f if isinstance(summary.get('return_pct'), (int, float)) else summary.get('return_pct', 'N/A')}%</div>
                    </div>
                </div>"""
            
            html_content += "</div>"
        
        # 添加分析师信号部分
        if "analyst_signals" in result and result["analyst_signals"]:
            html_content += f"""
            <!-- 分析师信号 -->
            <div class="section">
                <h2><span class="emoji">🧠</span>分析师专业意见</h2>
                <div class="analyst-signals">"""
            
            for analyst, signal in result["analyst_signals"].items():
                # 获取分析师中文名称
                chinese_name = self.analyst_chinese_names.get(analyst, analyst)
                html_content += f"""
                <div class="analyst-card">
                    <h4>🎯 {chinese_name}</h4>
                    <div class="signal-content">"""
                
                if isinstance(signal, dict):
                    for key, value in signal.items():
                        html_content += f"<p><strong>{key}:</strong> {value}</p>"
                else:
                    html_content += f"<p>{signal}</p>"
                
                html_content += """
                    </div>
                </div>"""
            
            html_content += """
                </div>
            </div>"""
        
        # 添加时间戳
        from datetime import datetime
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        html_content += f"""
            <div class="timestamp">
                <p>📅 报告生成时间: {current_time}</p>
                <p style="margin-top: 10px; font-size: 0.9rem;">
                    ⚠️ <strong>投资有风险，决策需谨慎</strong> - 本报告仅供参考，不构成投资建议
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    def save_settings(self):
        """保存当前设置到文件"""
        try:
            settings = {
                "tickers": self.tickers_entry.get(),
                "start_date_days": self.calculate_days_from_date(self.start_date_entry.get()),
                "end_date_days": self.calculate_days_from_date(self.end_date_entry.get()),
                "initial_investment": self.portfolio_entry.get(),
                "selected_analysts": [analyst for analyst, var in self.analyst_vars.items() if var.get()],
                "selected_model": self.model_combobox.get(),
                "model_provider": getattr(self, 'selected_provider', ''),
                "max_portfolio_size": self.max_portfolio_entry.get(),
                "enable_short_selling": self.short_selling_var.get(),
                "cash_buffer": self.cash_buffer_entry.get(),
                "max_position_size": self.max_position_entry.get(),
                "minimum_roi": self.roi_entry.get(),
                "window_geometry": self.root.geometry()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"保存设置时出错: {e}")
    
    def load_settings(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 恢复窗口大小和位置
                if "window_geometry" in settings:
                    self.root.geometry(settings["window_geometry"])
                
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"加载设置时出错: {e}")
            return self.default_settings.copy()
    
    def apply_settings(self, settings):
        """应用设置到GUI控件"""
        try:
            # 基础配置
            if hasattr(self, 'tickers_entry'):
                self.tickers_entry.delete(0, tk.END)
                self.tickers_entry.insert(0, settings.get("tickers", "AAPL,MSFT,GOOGL"))
            
            if hasattr(self, 'start_date_entry'):
                start_date = self.calculate_date_from_days(settings.get("start_date_days", 90))
                self.start_date_entry.delete(0, tk.END)
                self.start_date_entry.insert(0, start_date)
            
            if hasattr(self, 'end_date_entry'):
                end_date = self.calculate_date_from_days(settings.get("end_date_days", 0))
                self.end_date_entry.delete(0, tk.END)
                self.end_date_entry.insert(0, end_date)
                
            if hasattr(self, 'portfolio_entry'):
                self.portfolio_entry.delete(0, tk.END)
                self.portfolio_entry.insert(0, settings.get("initial_investment", "100000"))
            
            # 分析师选择
            if hasattr(self, 'analyst_vars'):
                selected_analysts = settings.get("selected_analysts", [])
                for analyst, var in self.analyst_vars.items():
                    var.set(analyst in selected_analysts)
            
            # 模型选择
            if hasattr(self, 'model_combobox'):
                selected_model = settings.get("selected_model", "")
                if selected_model and selected_model in self.model_combobox['values']:
                    self.model_combobox.set(selected_model)
            
            # 高级选项
            if hasattr(self, 'max_portfolio_entry'):
                self.max_portfolio_entry.delete(0, tk.END)
                self.max_portfolio_entry.insert(0, settings.get("max_portfolio_size", "10000"))
                
            if hasattr(self, 'short_selling_var'):
                self.short_selling_var.set(settings.get("enable_short_selling", False))
                
            if hasattr(self, 'cash_buffer_entry'):
                self.cash_buffer_entry.delete(0, tk.END)
                self.cash_buffer_entry.insert(0, settings.get("cash_buffer", "5000"))
                
            if hasattr(self, 'max_position_entry'):
                self.max_position_entry.delete(0, tk.END)
                self.max_position_entry.insert(0, settings.get("max_position_size", "2000"))
                
            if hasattr(self, 'roi_entry'):
                self.roi_entry.delete(0, tk.END)
                self.roi_entry.insert(0, settings.get("minimum_roi", "0.05"))
                
        except Exception as e:
            print(f"应用设置时出错: {e}")
    
    def calculate_days_from_date(self, date_str):
        """计算日期字符串距离今天的天数"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            return (today - date_obj).days
        except:
            return 0
    
    def calculate_date_from_days(self, days):
        """根据天数计算日期字符串"""
        try:
            target_date = datetime.now() - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        self.save_settings()
        self.root.destroy()
    
    def clear_results(self):
        """清空结果"""
        self.results_text.delete(1.0, tk.END)
        self.results_data = None
    
    def run(self):
        """运行GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.save_settings()
            self.root.quit()

def check_dependencies():
    """检查依赖"""
    missing_deps = []
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing_deps.append("python-dotenv")
    
    if missing_deps:
        messagebox.showerror(
            "依赖缺失", 
            f"缺少以下依赖包：\n{', '.join(missing_deps)}\n\n请运行以下命令安装：\npip install {' '.join(missing_deps)}"
        )
        return False
    
    return True

def main():
    """主函数"""
    if not check_dependencies():
        return
    
    # 创建并运行GUI
    app = HedgeFundGUI()
    app.run()

if __name__ == "__main__":
    main() 