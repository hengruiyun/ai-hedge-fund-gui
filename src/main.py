import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from dotenv import load_dotenv
    from langchain_core.messages import HumanMessage
    from langgraph.graph import END, StateGraph
    from colorama import Fore, Style, init
    import questionary
    from src.agents.portfolio_manager import portfolio_management_agent
    from src.agents.risk_manager import risk_management_agent
    from src.graph.state import AgentState
    from src.utils.display import print_trading_output
    from src.utils.analysts import ANALYST_ORDER, get_analyst_nodes
    from src.utils.progress import progress
    from src.llm.models import LLM_ORDER, OLLAMA_LLM_ORDER, get_model_info, ModelProvider
    from src.utils.ollama import ensure_ollama_and_model
    
    import argparse
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from src.utils.visualize import save_graph_as_png
    import json
    
    # Load environment variables from .env file
    load_dotenv()
    init(autoreset=True)
    
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    print("🔧 请确保已安装所有依赖:")
    print("   poetry install")
    print("   或者")
    print("   pip install -r requirements.txt")
    print("   或者使用 gui.bat 启动，它将自动安装所需依赖")
    sys.exit(1)


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


##### Run the Hedge Fund #####
def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] = [],
    model_name: str = "gpt-4o",
    model_provider: str = "OpenAI",
):
    # Start progress tracking
    progress.start()

    try:
        # Create a new workflow if analysts are customized
        if selected_analysts:
            workflow = create_workflow(selected_analysts)
            agent = workflow.compile()
        else:
            # 使用默认的所有分析师
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
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        return {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }
    finally:
        # Stop progress tracking
        progress.stop()


def start(state: AgentState):
    """Initialize the workflow with the input message."""
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
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    # Connect selected analysts to risk management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)

    workflow.set_entry_point("start_node")
    return workflow


def run_hedge_fund_gui(
    tickers: list[str],
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    margin_requirement: float = 0.0,
    show_reasoning: bool = False,
    selected_analysts: list[str] = None,
    model_name: str = "gpt-4o",
    model_provider: str = "OpenAI",
    show_agent_graph: bool = False
):
    """
    专门为GUI调用设计的函数，避免交互式选择
    基于virattt/ai-hedge-fund项目: https://github.com/virattt/ai-hedge-fund
    """
    print("🚀 AI对冲基金分析系统启动")
    print("=" * 60)
    
    try:
        # 解析股票代码
        if isinstance(tickers, str):
            tickers = [ticker.strip() for ticker in tickers.split(",")]
        
        print(f"📈 分析股票: {', '.join(tickers)}")
        
        # 使用传入的分析师列表
        if not selected_analysts:
            # 如果没有传入分析师，使用默认的所有分析师
            try:
                from src.utils.analysts import ANALYST_ORDER
                selected_analysts = [value for display, value in ANALYST_ORDER]
            except ImportError:
                print("⚠️  使用默认分析师配置")
                selected_analysts = ["warren_buffett", "peter_lynch", "technical_analyst"]
        
        # 显示选择的分析师
        print(f"🧠 选定分析师: {len(selected_analysts)}位")
        
        # 显示模型配置
        print(f"🤖 使用模型: {model_provider} - {model_name}")
        
        # 如果选择的是Ollama供应商，自动启用本地模式
        use_ollama = (model_provider == "Ollama")
        if use_ollama:
            print("🏠 启用本地Ollama模式")
            print(f"🤖 使用模型: {model_name}")
            # 输出选择的Ollama模型信息，不检查模型是否存在
            # 注意：不检查模型是否存在，由用户自行确保模型可用

        # 验证日期格式
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("开始日期必须为YYYY-MM-DD格式")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("结束日期必须为YYYY-MM-DD格式")

        # 设置开始和结束日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # 计算3个月前
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")

        print(f"📅 分析时间段: {start_date} 至 {end_date}")
        print(f"💰 初始资金: ${initial_cash:,.2f}")

        # 创建工作流
        print("⚙️  正在创建分析工作流...")
        
        # 增加错误处理，确保分析师存在
        try:
            workflow = create_workflow(selected_analysts)
            app = workflow.compile()
        except Exception as workflow_error:
            print(f"⚠️  工作流创建失败: {workflow_error}")
            print("尝试使用默认分析师...")
            
            # 使用最小的默认分析师集合
            default_analysts = ["warren_buffett", "peter_lynch", "technical_analyst"]
            workflow = create_workflow(default_analysts)
            app = workflow.compile()
            selected_analysts = default_analysts

        # 生成工作流图
        if show_agent_graph:
            try:
                file_path = ""
                if selected_analysts:
                    for selected_analyst in selected_analysts:
                        file_path += selected_analyst + "_"
                    file_path += "graph.png"
                save_graph_as_png(app, file_path)
                print(f"📊 工作流图已保存: {file_path}")
            except Exception as e:
                print(f"⚠️  工作流图生成失败: {e}")

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

        print("\n🔄 开始运行AI分析...")
        print("-" * 60)

        # 运行对冲基金分析
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
        
        print("\n" + "=" * 60)
        print("📊 分析完成，生成投资建议")
        print("=" * 60)
        print_trading_output(result)
        
        return result
        
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
        import traceback
        print("\n详细错误信息:")
        print(traceback.format_exc())
        
        # 返回错误信息，而不是引发异常
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--initial-cash", type=float, default=100000.0, help="Initial cash position. Defaults to 100000.0)")
    parser.add_argument("--margin-requirement", type=float, default=0.0, help="Initial margin requirement. Defaults to 0.0")
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock ticker symbols")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 3 months before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--show-agent-graph", action="store_true", help="Show the agent graph")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama for local LLM inference")

    args = parser.parse_args()

    # Parse tickers from comma-separated string
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]

    # Select analysts
    selected_analysts = None
    choices = questionary.checkbox(
        "Select your AI analysts.",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction="\n\nInstructions: \n1. Press Space to select/unselect analysts.\n2. Press 'a' to select/unselect all.\n3. Press Enter when done to run the hedge fund.\n",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    else:
        selected_analysts = choices
        print(f"\nSelected analysts: {', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}\n")

    # Select LLM model based on whether Ollama is being used
    model_name = ""
    model_provider = ""

    if args.ollama:
        print(f"{Fore.CYAN}Using Ollama for local LLM inference.{Style.RESET_ALL}")

        # Select from Ollama-specific models
        model_name: str = questionary.select(
            "Select your Ollama model:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_name:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)

        if model_name == "-":
            model_name = questionary.text("Enter the custom model name:").ask()
            if not model_name:
                print("\n\nInterrupt received. Exiting...")
                sys.exit(0)

        # 输出选择的Ollama模型信息，不检查模型是否存在
        # 注意：不检查模型是否存在，由用户自行确保模型可用

        model_provider = ModelProvider.OLLAMA.value
        print(f"\nSelected {Fore.CYAN}Ollama{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}提示: 请确保Ollama服务正在运行且模型已下载{Style.RESET_ALL}\n")
    else:
        # Use the standard cloud-based LLM selection
        model_choice = questionary.select(
            "Select your LLM model:",
            choices=[questionary.Choice(display, value=(name, provider)) for display, name, provider in LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_choice:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)

        model_name, model_provider = model_choice

        # Get model info using the helper function
        model_info = get_model_info(model_name, model_provider)
        if model_info:
            if model_info.is_custom():
                model_name = questionary.text("Enter the custom model name:").ask()
                if not model_name:
                    print("\n\nInterrupt received. Exiting...")
                    sys.exit(0)

            print(f"\nSelected {Fore.CYAN}{model_provider}{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n")
        else:
            model_provider = "Unknown"
            print(f"\nSelected model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n")

    # Create the workflow with selected analysts
    workflow = create_workflow(selected_analysts)
    app = workflow.compile()

    if args.show_agent_graph:
        file_path = ""
        if selected_analysts is not None:
            for selected_analyst in selected_analysts:
                file_path += selected_analyst + "_"
            file_path += "graph.png"
        save_graph_as_png(app, file_path)

    # Validate dates if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")

    # Set the start and end dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    if not args.start_date:
        # Calculate 3 months before end_date
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date

    # Initialize portfolio with cash amount and stock positions
    portfolio = {
        "cash": args.initial_cash,  # Initial cash amount
        "margin_requirement": args.margin_requirement,  # Initial margin requirement
        "margin_used": 0.0,  # total margin usage across all short positions
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            }
            for ticker in tickers
        },
    }

    # Run the hedge fund
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_name,
        model_provider=model_provider,
    )
    print_trading_output(result)

# 在文件末尾添加一个辅助函数，用于从GUI调用
def run_from_gui(args_dict):
    """从GUI调用主函数的简化接口"""
    try:
        return run_hedge_fund_gui(**args_dict)
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
