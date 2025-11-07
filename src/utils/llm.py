"""Helper functions for LLM"""

import json
import logging
import re
from typing import Any, Dict, Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ValidationError

from src.graph.state import AgentState
from src.llm.models import get_model, get_model_info, ModelProvider
from src.utils.progress import progress

# 全局常量 - 默认模型名称
DEFAULT_MODEL_NAME = "qwen3:0.6b"

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def call_llm(
    prompt: any,
    pydantic_model: type[BaseModel],
    agent_name: str | None = None,
    state: AgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
) -> BaseModel:
    """
    调用LLM并解析为Pydantic模型，带有数据增强功能
    """
    ticker = None
    if state and "data" in state:
        tickers = state["data"].get("tickers", [])
        ticker = tickers[0] if tickers else None
    
    # 增强提示词，添加可用的财务数据
    enhanced_prompt = enhance_prompt_with_data(prompt, state, ticker, agent_name)
    
    # 调用原有的LLM逻辑
    return _call_llm_internal(
        enhanced_prompt, pydantic_model, agent_name, state, max_retries, default_factory, ticker
    )


def enhance_prompt_with_data(prompt: any, state: AgentState, ticker: str, agent_name: str) -> any:
    """
    增强提示词，主动添加可用的财务数据
    """
    if not state or not ticker:
        return prompt
    
    try:
        # 获取增强的财务数据
        unified_data_accessor = state["data"].get("unified_data_accessor")
        prefetched_data = state["data"].get("prefetched_data", {})
        
        if not unified_data_accessor or not prefetched_data:
            return prompt
        
        # 获取可用数据
        enhanced_data = unified_data_accessor.get_enhanced_data(ticker, prefetched_data)
        financial_data = enhanced_data.get('enhanced_financial_data', {})
        market_cap = enhanced_data.get('market_cap')
        
        # 获取其他数据
        comprehensive_data = unified_data_accessor.data_prefetcher.get_comprehensive_data(ticker, prefetched_data)
        company_news = comprehensive_data.get('company_news', [])
        price_data = comprehensive_data.get('prices', [])
        
        # 使用分析师数据提供器创建定制化数据摘要
        from src.utils.analyst_data_provider import analyst_data_provider
        
        # 提取分析师名称（去掉_agent后缀）
        clean_agent_name = agent_name.replace('_agent', '') if agent_name else 'unknown'
        
        # 获取分析师特定的数据摘要
        analyst_data_summary = analyst_data_provider.get_analyst_specific_data(
            clean_agent_name, financial_data, market_cap, ticker
        )
        
        # 创建通用数据摘要作为备份
        general_data_summary = create_data_summary(financial_data, market_cap, company_news, price_data, ticker)
        
        # 增强提示词
        if hasattr(prompt, 'messages') and len(prompt.messages) > 0:
            # 如果是ChatPromptTemplate
            enhanced_messages = []
            for message in prompt.messages:
                # 正确访问message对象的类型和内容
                message_type = message.type if hasattr(message, 'type') else str(type(message).__name__).lower()
                message_content = message.content if hasattr(message, 'content') else str(message)
                
                if message_type == "human":
                    # 在human消息中添加数据
                    enhanced_content = f"""{message_content}

=== 专用财务数据 ===
{analyst_data_summary}

=== 补充数据信息 ===
{_create_supplementary_data_info(company_news, price_data)}

=== 分析指导 ===
- 请基于以上提供的具体数据进行分析
- 不要说"数据缺失"或"无法获取数据"
- 如果某些指标确实缺失，请基于可用数据进行合理推断
- 重点关注与您的投资风格相关的指标
- 提供具体的数值引用以支持您的结论
- 必须返回有效的JSON格式：{{"signal": "bullish/bearish/neutral", "confidence": 数字, "reasoning": "分析原因"}}"""
                    
                    # 重新创建消息对象
                    from langchain_core.messages import HumanMessage
                    enhanced_messages.append(HumanMessage(content=enhanced_content))
                else:
                    # 保持其他消息不变
                    enhanced_messages.append(message)
            
            # 创建新的ChatPromptTemplate
            from langchain_core.prompts import ChatPromptTemplate
            return ChatPromptTemplate(messages=enhanced_messages)
        
        logger.info(f"[{agent_name}] 为 {ticker} 增强了提示词，添加了分析师定制数据")
        
    except Exception as e:
        logger.warning(f"[{agent_name}] 提示词增强失败: {e}")
        import traceback
        logger.warning(f"详细错误: {traceback.format_exc()}")
    
    return prompt


def create_data_summary(financial_data: Dict, market_cap: float, company_news: list, price_data: list, ticker: str) -> str:
    """
    创建数据摘要，格式化为易于LLM理解的文本
    """
    summary_lines = [f"股票代码: {ticker}"]
    
    # 基本估值数据
    if market_cap:
        summary_lines.append(f"市值: {market_cap:,.0f}")
    
    # 关键财务指标
    key_metrics = {
        'revenue': '营业收入',
        'net_income': '净利润', 
        'total_assets': '总资产',
        'shareholders_equity': '股东权益',
        'total_debt': '总负债',
        'free_cash_flow': '自由现金流',
        'operating_cash_flow': '经营现金流',
        'current_ratio': '流动比率',
        'debt_to_equity': '债务权益比',
        'roe': 'ROE (%)',
        'roa': 'ROA (%)',
        'gross_margin': '毛利率 (%)',
        'net_profit_margin': '净利率 (%)',
        'price_to_earnings': 'P/E比率',
        'price_to_book': 'P/B比率',
        'earnings_per_share': '每股收益',
        'book_value_per_share': '每股净资产'
    }
    
    summary_lines.append("\n基本财务指标:")
    found_metrics = 0
    for key, label in key_metrics.items():
        if key in financial_data and financial_data[key] is not None:
            value = financial_data[key]
            if isinstance(value, (int, float)):
                if value > 1000000:
                    summary_lines.append(f"  {label}: {value:,.0f}")
                elif value > 1:
                    summary_lines.append(f"  {label}: {value:.2f}")
                else:
                    summary_lines.append(f"  {label}: {value:.4f}")
                found_metrics += 1
    
    if found_metrics == 0:
        summary_lines.append("  注意: 主要财务指标数据有限")
    
    # 计算衍生指标
    summary_lines.append("\n计算指标:")
    try:
        revenue = financial_data.get('revenue')
        net_income = financial_data.get('net_income')
        total_assets = financial_data.get('total_assets')
        equity = financial_data.get('shareholders_equity')
        
        # 计算一些基本比率
        if revenue and revenue > 0 and net_income is not None:
            net_margin = (net_income / revenue) * 100
            summary_lines.append(f"  净利润率: {net_margin:.2f}%")
        
        if net_income is not None and equity and equity > 0:
            roe = (net_income / equity) * 100
            summary_lines.append(f"  ROE: {roe:.2f}%")
        
        if net_income is not None and total_assets and total_assets > 0:
            roa = (net_income / total_assets) * 100
            summary_lines.append(f"  ROA: {roa:.2f}%")
            
    except Exception as e:
        summary_lines.append(f"  计算指标时出错: {e}")
    
    # 价格数据
    if price_data and len(price_data) > 0:
        try:
            latest_price = price_data[-1]
            close_price = getattr(latest_price, 'close', None) or getattr(latest_price, 'price', None)
            if close_price:
                summary_lines.append(f"\n当前股价: {close_price:.2f}")
        except:
            pass
    
    # 新闻数据
    if company_news and len(company_news) > 0:
        summary_lines.append(f"\n新闻数据: 共 {len(company_news)} 条新闻")
        recent_news = 0
        for news in company_news[:5]:  # 只看前5条
            title = getattr(news, 'title', None)
            if title:
                summary_lines.append(f"  - {title[:50]}...")
                recent_news += 1
        if recent_news == 0:
            summary_lines.append("  注意: 新闻标题数据有限")
    
    # 数据完整性评估
    total_fields = len(financial_data)
    non_null_fields = len([v for v in financial_data.values() if v is not None and v != 0])
    
    summary_lines.append(f"\n数据完整性: {non_null_fields}/{total_fields} 个字段有数据")
    
    if non_null_fields < 5:
        summary_lines.append("注意: 数据较为有限，请基于可用信息进行保守分析")
    elif non_null_fields < 10:
        summary_lines.append("注意: 数据中等完整，建议谨慎分析")
    else:
        summary_lines.append("数据较为完整，可进行详细分析")
    
    return '\n'.join(summary_lines)


def _create_supplementary_data_info(company_news: list, price_data: list) -> str:
    """创建补充数据信息"""
    info_lines = []
    
    # 新闻情况
    if company_news and len(company_news) > 0:
        info_lines.append(f"新闻数据: 共{len(company_news)}条相关新闻")
        
        # 分析新闻情绪
        positive_keywords = ['增长', '盈利', '上涨', '成功', '突破', '合作', '创新']
        negative_keywords = ['下跌', '亏损', '风险', '问题', '困难', '挑战', '裁员']
        
        positive_count = 0
        negative_count = 0
        
        for news in company_news[:10]:  # 只分析前10条
            title = getattr(news, 'title', '') or ''
            if any(keyword in title for keyword in positive_keywords):
                positive_count += 1
            elif any(keyword in title for keyword in negative_keywords):
                negative_count += 1
        
        if positive_count > negative_count:
            info_lines.append("  新闻情绪偏向: 积极")
        elif negative_count > positive_count:
            info_lines.append("  新闻情绪偏向: 消极")
        else:
            info_lines.append("  新闻情绪偏向: 中性")
    else:
        info_lines.append("新闻数据: 无可用新闻数据")
    
    # 价格数据情况
    if price_data and len(price_data) > 0:
        info_lines.append(f"价格数据: 共{len(price_data)}个交易日数据")
        try:
            latest_price = price_data[-1]
            current_price = getattr(latest_price, 'close', None) or getattr(latest_price, 'price', None)
            if current_price:
                info_lines.append(f"  最新价格: {current_price:.2f}")
            
            # 计算简单趋势
            if len(price_data) >= 5:
                recent_prices = []
                for p in price_data[-5:]:
                    price = getattr(p, 'close', None) or getattr(p, 'price', None)
                    if price:
                        recent_prices.append(price)
                
                if len(recent_prices) >= 2:
                    if recent_prices[-1] > recent_prices[0]:
                        info_lines.append("  近期趋势: 上涨")
                    elif recent_prices[-1] < recent_prices[0]:
                        info_lines.append("  近期趋势: 下跌")
                    else:
                        info_lines.append("  近期趋势: 横盘")
        except:
            pass
    else:
        info_lines.append("价格数据: 无可用价格数据")
    
    return '\n'.join(info_lines)


def _call_llm_internal(
    prompt: any,
    pydantic_model: type[BaseModel],
    agent_name: str | None = None,
    state: AgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
    ticker: str = None,
) -> BaseModel:
    """
    内部LLM调用实现，包含重试逻辑和错误处理
    """
    model_name = DEFAULT_MODEL_NAME  # 默认模型
    model_provider = ModelProvider.OLLAMA  # 默认提供商（使用枚举）
    
    if state and "metadata" in state:
        model_name = state["metadata"].get("model_name", model_name)
        provider_value = state["metadata"].get("model_provider", "OLLAMA")
        
        # 正确转换字符串为ModelProvider枚举
        if isinstance(provider_value, str):
            try:
                # 直接使用原始值进行匹配，因为枚举值保持原始大小写
                model_provider = ModelProvider(provider_value)
            except ValueError:
                # 如果直接匹配失败，尝试通过枚举名称匹配
                try:
                    # 通过枚举名称匹配（大写）
                    for provider in ModelProvider:
                        if provider.name == provider_value.upper():
                            model_provider = provider
                            break
                    else:
                        raise ValueError(f"No matching provider found")
                except ValueError:
                    print(f"Unknown model provider: {provider_value}, using OLLAMA")
                    model_provider = ModelProvider.OLLAMA
        else:
            model_provider = provider_value

    # 获取模型
    model = get_model(model_name, model_provider)
    if not model:
        print(f"Failed to get model {model_name} from {model_provider}")
        if default_factory:
            return default_factory()
        return create_default_response(pydantic_model)

    # 进行重试循环
    for attempt in range(max_retries):
        try:
            if agent_name:
                progress.update_status(agent_name, ticker, f"调用LLM - 尝试 {attempt + 1}/{max_retries}")

            # 调用模型
            response = model.invoke(prompt.messages if hasattr(prompt, 'messages') else prompt)
            content = response.content

            # 尝试解析响应为Pydantic模型
            try:
                # 首先尝试直接解析JSON
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    parsed_json = json.loads(content)
                    return pydantic_model(**parsed_json)
                
                # 尝试提取JSON
                extracted_json = extract_json_from_response(content)
                if extracted_json:
                    return pydantic_model(**extracted_json)
                else:
                    print(f"No valid JSON found in response for {agent_name}")
                    print(f"Response content: {content[:200]}...")
                    if default_factory:
                        print(f"Using default factory for {agent_name} due to JSON extraction failure")
                        return default_factory()
                    print(f"Creating default response for {agent_name} due to JSON extraction failure")
                    return create_default_response(pydantic_model)

            except (ValidationError, TypeError, ValueError) as e:
                print(f"Pydantic validation failed for {agent_name}: {e}")
                print(f"Response content: {content[:200]}...")
                
                # 尝试提取JSON的其他方法
                extracted_json = extract_json_from_response(content)
                if extracted_json:
                    try:
                        return pydantic_model(**extracted_json)
                    except Exception:
                        pass
                
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，使用默认响应
                    if default_factory:
                        print(f"Using default factory for {agent_name} due to validation failure")
                        return default_factory()
                    print(f"Creating default response for {agent_name} due to validation failure")
                    return create_default_response(pydantic_model)
                else:
                    # 如果JSON parsing fails, try to create a reasonable default
                    print(f"Failed to parse JSON from LLM response for {agent_name}")
                    print(f"Full response content: {content}")
                    if default_factory:
                        print(f"Using default factory for {agent_name} due to JSON parsing failure")
                        return default_factory()
                    print(f"Creating default response for {agent_name} due to JSON parsing failure")
                    return create_default_response(pydantic_model)

        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, ticker, f"Error - retry {attempt + 1}/{max_retries}")

            print(f"Error in LLM call (attempt {attempt + 1}) for {agent_name}: {e}")
            
            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts for {agent_name}: {e}")
                # Use default_factory if provided, otherwise create a basic default
                if default_factory:
                    print(f"Using default factory for {agent_name} due to LLM error")
                    return default_factory()
                print(f"Creating default response for {agent_name} due to LLM error")
                return create_default_response(pydantic_model)

    # This should never be reached due to the retry logic above
    return create_default_response(pydantic_model)


def extract_json_from_response(content: str) -> dict:
    """
    从LLM响应中提取JSON，支持多种格式和容错处理
    特别针对qwen3模型的<think>标签输出进行优化
    """
    if not content:
        return None
    
    # 清理内容
    content = content.strip()
    
    # 方法0：特别处理qwen3模型的<think>标签
    # qwen3模型会输出 <think>思考过程</think> 然后是实际的JSON
    if '<think>' in content and '</think>' in content:
        # 提取</think>之后的内容
        think_end = content.find('</think>')
        if think_end != -1:
            post_think_content = content[think_end + len('</think>'):].strip()
            # 递归处理提取出的内容
            extracted = extract_json_from_response(post_think_content)
            if extracted:
                return extracted
    
    # 方法1：直接尝试解析整个内容
    try:
        return json.loads(content)
    except:
        pass
    
    # 方法2：查找JSON代码块
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',  # ```json {...} ```
        r'```\s*(\{.*?\})\s*```',      # ``` {...} ```
        r'`(\{.*?\})`',                # `{...}`
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    
    # 方法3：查找第一个完整的JSON对象
    brace_count = 0
    start_idx = -1
    
    for i, char in enumerate(content):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                try:
                    json_str = content[start_idx:i+1]
                    return json.loads(json_str)
                except:
                    start_idx = -1
                    continue
    
    # 方法4：尝试修复常见的JSON格式问题
    json_like_patterns = [
        # 查找像JSON的结构
        r'signal["\s]*[:=]["\s]*(bullish|bearish|neutral)["\s]*',
        r'confidence["\s]*[:=]["\s]*(\d+(?:\.\d+)?)["\s]*',
        r'reasoning["\s]*[:=]["\s]*["]([^"]*)["]'
    ]
    
    signal = None
    confidence = None
    reasoning = None
    
    for line in content.split('\n'):
        line = line.strip().lower()
        
        # 查找signal
        if 'signal' in line:
            for word in ['bullish', 'bearish', 'neutral']:
                if word in line:
                    signal = word
                    break
        
        # 查找confidence
        if 'confidence' in line:
            numbers = re.findall(r'\d+(?:\.\d+)?', line)
            if numbers:
                try:
                    conf = float(numbers[0])
                    if 0 <= conf <= 100:
                        confidence = conf
                except:
                    pass
        
        # 查找reasoning
        if 'reasoning' in line or '原因' in line or '分析' in line:
            # 提取引号中的内容
            quote_match = re.search(r'["""]([^"""]+)["""]', line)
            if quote_match:
                reasoning = quote_match.group(1)
            elif len(line) > 20:  # 如果这行足够长，可能就是reasoning
                reasoning = line
    
    # 如果找到了一些信息，构造JSON
    if signal:
        result = {
            "signal": signal,
            "confidence": confidence if confidence is not None else 50.0,
            "reasoning": reasoning if reasoning else f"基于{signal}信号的分析"
        }
        return result
    
    # 方法5：最后尝试从中文回答中提取
    chinese_patterns = {
        'bullish': ['看涨', '看好', '买入', '增持', '乐观'],
        'bearish': ['看跌', '看空', '卖出', '减持', '悲观'],
        'neutral': ['中性', '持有', '观望', '平稳']
    }
    
    content_lower = content.lower()
    for signal_type, keywords in chinese_patterns.items():
        for keyword in keywords:
            if keyword in content_lower:
                return {
                    "signal": signal_type,
                    "confidence": 60.0,
                    "reasoning": f"从文本中识别到{keyword}信号"
                }
    
    return None


def create_default_response(pydantic_model: type[BaseModel]) -> BaseModel:
    """
    为Pydantic模型创建默认响应
    """
    try:
        # 获取模型的字段
        fields = pydantic_model.model_fields if hasattr(pydantic_model, 'model_fields') else {}
        
        # 创建默认值
        default_values = {}
        
        for field_name, field_info in fields.items():
            if field_name == 'signal':
                default_values[field_name] = 'neutral'
            elif field_name == 'confidence':
                default_values[field_name] = 0.0
            elif field_name == 'reasoning':
                default_values[field_name] = '分析出错，默认为中性'
            else:
                # 尝试从类型推断默认值
                field_type = field_info.annotation if hasattr(field_info, 'annotation') else str
                
                if field_type == str:
                    default_values[field_name] = ''
                elif field_type == float:
                    default_values[field_name] = 0.0
                elif field_type == int:
                    default_values[field_name] = 0
                elif field_type == bool:
                    default_values[field_name] = False
                else:
                    default_values[field_name] = None
        
        return pydantic_model(**default_values)
    
    except Exception as e:
        print(f"创建默认响应失败: {e}")
        # 如果上面的方法失败，尝试最基本的创建
        try:
            return pydantic_model(signal='neutral', confidence=0.0, reasoning='分析出错，默认为中性')
        except:
            # 最后的备用方案
            return pydantic_model()


def get_agent_model_config(state, agent_name):
    """
    Get model configuration for a specific agent from the state.
    Falls back to global model configuration if agent-specific config is not available.
    Always returns valid model_name and model_provider values.
    """
    request = state.get("metadata", {}).get("request")
    
    if request and hasattr(request, 'get_agent_model_config'):
        # Get agent-specific model configuration
        model_name, model_provider = request.get_agent_model_config(agent_name)
        # Ensure we have valid values
        if model_name and model_provider:
            return model_name, model_provider.value if hasattr(model_provider, 'value') else str(model_provider)
    
    # Fall back to global configuration (system defaults)
    model_name = state.get("metadata", {}).get("model_name") or DEFAULT_MODEL_NAME
    model_provider = state.get("metadata", {}).get("model_provider") or "OPENAI"
    
    # Convert enum to string if necessary
    if hasattr(model_provider, 'value'):
        model_provider = model_provider.value
    
    return model_name, model_provider
