"""
分析师数据提供器
为不同的分析师提供定制化的财务数据，确保每个分析师都能获得充足的数据进行分析
"""

from typing import Dict, Any, List, Optional
import logging
from src.utils.data_analysis_rules import calculate_data_completeness_score

logger = logging.getLogger(__name__)


class AnalystDataProvider:
    """为不同投资分析师提供定制化的财务数据"""
    
    def __init__(self):
        # 定义每个分析师关注的核心数据
        self.analyst_data_requirements = {
            'warren_buffett': {
                'core_metrics': [
                    'revenue', 'net_income', 'shareholders_equity', 'total_debt', 
                    'free_cash_flow', 'operating_cash_flow', 'roe', 'roa',
                    'debt_to_equity', 'current_ratio', 'book_value_per_share'
                ],
                'growth_metrics': [
                    'revenue_growth_rate', 'net_income_growth_rate', 'fcf_growth_rate'
                ],
                'valuation_metrics': [
                    'price_to_earnings', 'price_to_book', 'price_to_sales',
                    'enterprise_value', 'ev_to_ebitda'
                ]
            },
            'charlie_munger': {
                'core_metrics': [
                    'revenue', 'net_income', 'operating_margin', 'net_margin',
                    'roe', 'roic', 'current_ratio', 'debt_to_equity'
                ],
                'moat_metrics': [
                    'gross_margin', 'operating_margin', 'net_margin',
                    'asset_turnover', 'inventory_turnover'
                ],
                'quality_metrics': [
                    'debt_to_total_capital', 'interest_coverage_ratio',
                    'working_capital', 'cash_and_equivalents'
                ]
            },
            'peter_lynch': {
                'core_metrics': [
                    'revenue', 'net_income', 'earnings_per_share',
                    'price_to_earnings', 'revenue_growth_rate', 'eps_growth_rate'
                ],
                'growth_metrics': [
                    'peg_ratio', 'revenue_growth_rate', 'net_income_growth_rate',
                    'eps_growth_rate', 'fcf_growth_rate'
                ],
                'value_metrics': [
                    'price_to_earnings', 'price_to_book', 'price_to_sales',
                    'dividend_yield', 'earnings_yield'
                ]
            },
            'phil_fisher': {
                'core_metrics': [
                    'revenue', 'net_income', 'research_and_development',
                    'gross_margin', 'operating_margin', 'net_margin'
                ],
                'growth_metrics': [
                    'revenue_growth_rate', 'net_income_growth_rate',
                    'rd_to_revenue_ratio', 'capex_to_revenue_ratio'
                ],
                'innovation_metrics': [
                    'research_and_development', 'rd_to_revenue_ratio',
                    'patent_count', 'r_and_d_growth_rate'
                ]
            },
            'michael_burry': {
                'core_metrics': [
                    'total_assets', 'total_liabilities', 'book_value',
                    'tangible_book_value', 'working_capital'
                ],
                'value_metrics': [
                    'price_to_book', 'price_to_tangible_book',
                    'enterprise_value', 'ev_to_sales', 'ev_to_ebitda'
                ],
                'distress_metrics': [
                    'debt_to_equity', 'current_ratio', 'quick_ratio',
                    'interest_coverage_ratio', 'debt_service_coverage'
                ]
            },
            'cathie_wood': {
                'core_metrics': [
                    'revenue', 'revenue_growth_rate', 'research_and_development',
                    'gross_margin', 'operating_margin'
                ],
                'innovation_metrics': [
                    'rd_to_revenue_ratio', 'patent_count', 'r_and_d_growth_rate',
                    'capex_to_revenue_ratio'
                ],
                'growth_metrics': [
                    'revenue_growth_rate', 'gross_margin_trend',
                    'tam_growth_rate', 'market_penetration'
                ]
            },
            'bill_ackman': {
                'core_metrics': [
                    'revenue', 'operating_income', 'net_income', 'free_cash_flow',
                    'roic', 'roe', 'operating_margin'
                ],
                'quality_metrics': [
                    'gross_margin', 'operating_margin', 'fcf_margin',
                    'asset_turnover', 'capital_efficiency'
                ],
                'activist_metrics': [
                    'management_efficiency', 'capital_allocation_score',
                    'shareholder_returns', 'dividend_policy'
                ]
            },
            'stanley_druckenmiller': {
                'core_metrics': [
                    'revenue', 'net_income', 'free_cash_flow',
                    'revenue_growth_rate', 'operating_leverage'
                ],
                'macro_metrics': [
                    'beta', 'correlation_to_market', 'sector_performance',
                    'economic_sensitivity'
                ],
                'momentum_metrics': [
                    'price_momentum', 'earnings_momentum', 'revision_momentum',
                    'relative_strength'
                ]
            },
            'aswath_damodaran': {
                'core_metrics': [
                    'revenue', 'operating_income', 'net_income', 'free_cash_flow',
                    'total_assets', 'shareholders_equity', 'total_debt'
                ],
                'valuation_metrics': [
                    'dcf_value', 'terminal_value', 'wacc', 'cost_of_equity',
                    'enterprise_value', 'equity_value'
                ],
                'risk_metrics': [
                    'beta', 'debt_to_equity', 'interest_coverage_ratio',
                    'operating_leverage', 'financial_leverage'
                ]
            },
            'rakesh_jhunjhunwala': {
                'core_metrics': [
                    'revenue', 'net_income', 'operating_cash_flow',
                    'roe', 'roic', 'debt_to_equity'
                ],
                'growth_metrics': [
                    'revenue_growth_rate', 'net_income_growth_rate',
                    'dividend_growth_rate', 'book_value_growth_rate'
                ],
                'value_metrics': [
                    'price_to_earnings', 'price_to_book',
                    'dividend_yield', 'earnings_yield'
                ]
            },
            'ben_graham': {
                'core_metrics': [
                    'current_assets', 'current_liabilities', 'total_debt',
                    'working_capital', 'book_value', 'tangible_book_value'
                ],
                'safety_metrics': [
                    'current_ratio', 'quick_ratio', 'debt_to_equity',
                    'interest_coverage_ratio', 'net_current_assets'
                ],
                'value_metrics': [
                    'price_to_book', 'price_to_tangible_book',
                    'graham_number', 'ncav_per_share'
                ]
            }
        }
    
    def get_analyst_specific_data(self, analyst_name: str, financial_data: Dict[str, Any], 
                                 market_cap: float, ticker: str) -> str:
        """
        为特定分析师生成定制化的数据摘要
        
        Args:
            analyst_name: 分析师名称
            financial_data: 财务数据字典
            market_cap: 市值
            ticker: 股票代码
            
        Returns:
            格式化的数据摘要字符串
        """
        # 获取分析师的数据需求
        requirements = self.analyst_data_requirements.get(analyst_name, {})
        
        summary_lines = [f"=== {analyst_name.upper()} 专用数据摘要 ==="]
        summary_lines.append(f"股票代码: {ticker}")
        
        if market_cap:
            summary_lines.append(f"市值: {market_cap:,.0f}")
        
        # 按类别组织数据
        for category, metrics in requirements.items():
            if not metrics:
                continue
                
            category_name = {
                'core_metrics': '核心财务指标',
                'growth_metrics': '增长指标', 
                'valuation_metrics': '估值指标',
                'moat_metrics': '护城河指标',
                'quality_metrics': '质量指标',
                'value_metrics': '价值指标',
                'innovation_metrics': '创新指标',
                'distress_metrics': '风险指标',
                'activist_metrics': '激进投资指标',
                'macro_metrics': '宏观指标',
                'momentum_metrics': '动量指标',
                'risk_metrics': '风险度量',
                'safety_metrics': '安全指标'
            }.get(category, category)
            
            summary_lines.append(f"\n{category_name}:")
            
            found_metrics = 0
            for metric in metrics:
                value = financial_data.get(metric)
                if value is not None and value != 0:
                    formatted_value = self._format_metric_value(metric, value)
                    metric_label = self._get_metric_label(metric)
                    summary_lines.append(f"  {metric_label}: {formatted_value}")
                    found_metrics += 1
            
            if found_metrics == 0:
                summary_lines.append(f"  注意: {category_name}数据有限")
        
        # 添加计算的衍生指标
        calculated_metrics = self._calculate_analyst_specific_metrics(
            analyst_name, financial_data, market_cap
        )
        
        if calculated_metrics:
            summary_lines.append("\n计算指标:")
            for metric, value in calculated_metrics.items():
                if value is not None:
                    formatted_value = self._format_metric_value(metric, value)
                    metric_label = self._get_metric_label(metric)
                    summary_lines.append(f"  {metric_label}: {formatted_value}")
        
        # 数据完整性评估
        requirements = self.analyst_data_requirements.get(analyst_name, {})
        all_required_metrics = []
        for category_metrics in requirements.values():
            all_required_metrics.extend(category_metrics)
        
        available_required, total_required, completeness_percentage = calculate_data_completeness_score(
            financial_data, 
            all_required_metrics
        )
        
        summary_lines.append(f"\n数据基础: 基于{available_required}项核心财务指标进行专业分析")
        
        # 分析师特定的建议
        analyst_specific_notes = self._get_analyst_specific_notes(
            analyst_name, financial_data, available_required, total_required
        )
        if analyst_specific_notes:
            summary_lines.append(f"\n{analyst_name}分析要点:")
            summary_lines.extend(analyst_specific_notes)
        
        return '\n'.join(summary_lines)
    
    def _format_metric_value(self, metric: str, value: Any) -> str:
        """格式化指标值"""
        if not isinstance(value, (int, float)):
            return str(value)
        
        # 百分比指标
        if any(keyword in metric.lower() for keyword in ['ratio', 'margin', 'yield', 'growth_rate', 'roe', 'roa']):
            if abs(value) < 1:
                return f"{value * 100:.2f}%"
            else:
                return f"{value:.2f}%"
        
        # 大额数值
        if abs(value) > 1000000000:
            return f"{value / 1000000000:.2f}B"
        elif abs(value) > 1000000:
            return f"{value / 1000000:.2f}M"
        elif abs(value) > 1000:
            return f"{value:,.0f}"
        else:
            return f"{value:.2f}"
    
    def _get_metric_label(self, metric: str) -> str:
        """获取指标的中文标签"""
        labels = {
            'revenue': '营业收入',
            'net_income': '净利润',
            'total_assets': '总资产',
            'shareholders_equity': '股东权益',
            'total_debt': '总负债',
            'free_cash_flow': '自由现金流',
            'operating_cash_flow': '经营现金流',
            'current_ratio': '流动比率',
            'debt_to_equity': '债务权益比',
            'roe': 'ROE',
            'roa': 'ROA',
            'roic': 'ROIC',
            'gross_margin': '毛利率',
            'operating_margin': '经营利润率',
            'net_margin': '净利率',
            'price_to_earnings': 'P/E比率',
            'price_to_book': 'P/B比率',
            'price_to_sales': 'P/S比率',
            'earnings_per_share': '每股收益',
            'book_value_per_share': '每股净资产',
            'revenue_growth_rate': '收入增长率',
            'net_income_growth_rate': '净利润增长率',
            'peg_ratio': 'PEG比率',
            'research_and_development': '研发费用',
            'rd_to_revenue_ratio': '研发收入比',
            'enterprise_value': '企业价值',
            'ev_to_ebitda': 'EV/EBITDA',
            'working_capital': '营运资金',
            'quick_ratio': '速动比率',
            'interest_coverage_ratio': '利息保障倍数'
        }
        return labels.get(metric, metric.replace('_', ' ').title())
    
    def _calculate_analyst_specific_metrics(self, analyst_name: str, financial_data: Dict[str, Any], 
                                          market_cap: float) -> Dict[str, Any]:
        """为特定分析师计算专门的指标"""
        calculated = {}
        
        revenue = financial_data.get('revenue')
        net_income = financial_data.get('net_income')
        total_assets = financial_data.get('total_assets')
        equity = financial_data.get('shareholders_equity')
        
        if analyst_name == 'warren_buffett':
            # 巴菲特关注的指标
            if net_income and equity and equity > 0:
                calculated['roe_calculated'] = (net_income / equity) * 100
            
            if net_income and total_assets and total_assets > 0:
                calculated['roa_calculated'] = (net_income / total_assets) * 100
        
        elif analyst_name == 'peter_lynch':
            # 林奇关注PEG比率
            eps = financial_data.get('earnings_per_share')
            pe_ratio = financial_data.get('price_to_earnings')
            growth_rate = financial_data.get('eps_growth_rate') or financial_data.get('revenue_growth_rate')
            
            if pe_ratio and growth_rate and growth_rate > 0:
                calculated['peg_ratio_calculated'] = pe_ratio / growth_rate
        
        elif analyst_name == 'ben_graham':
            # 格雷厄姆数
            eps = financial_data.get('earnings_per_share')
            book_value_per_share = financial_data.get('book_value_per_share')
            
            if eps and book_value_per_share and eps > 0 and book_value_per_share > 0:
                calculated['graham_number'] = (22.5 * eps * book_value_per_share) ** 0.5
        
        return calculated
    
    def _get_analyst_specific_notes(self, analyst_name: str, financial_data: Dict[str, Any],
                                   available_metrics: int, total_metrics: int) -> List[str]:
        """获取分析师特定的分析要点"""
        notes = []
        
        if analyst_name == 'warren_buffett':
            roe = financial_data.get('roe')
            debt_to_equity = financial_data.get('debt_to_equity')
            
            if roe and roe > 15:
                notes.append("- ROE超过15%，符合巴菲特优质企业标准")
            elif roe and roe < 10:
                notes.append("- ROE低于10%，需要谨慎评估盈利能力")
            
            if debt_to_equity and debt_to_equity < 0.3:
                notes.append("- 债务水平较低，财务状况稳健")
            elif debt_to_equity and debt_to_equity > 0.6:
                notes.append("- 债务水平较高，需要关注财务风险")
        
        elif analyst_name == 'peter_lynch':
            pe_ratio = financial_data.get('price_to_earnings')
            growth_rate = financial_data.get('revenue_growth_rate')
            
            if pe_ratio and growth_rate:
                peg = pe_ratio / growth_rate if growth_rate > 0 else None
                if peg and peg < 1:
                    notes.append("- PEG比率低于1，可能存在投资机会")
                elif peg and peg > 2:
                    notes.append("- PEG比率过高，估值可能偏贵")
        
        elif analyst_name == 'ben_graham':
            current_ratio = financial_data.get('current_ratio')
            pb_ratio = financial_data.get('price_to_book')
            
            if current_ratio and current_ratio > 2:
                notes.append("- 流动比率大于2，流动性充足")
            elif current_ratio and current_ratio < 1.5:
                notes.append("- 流动比率偏低，需要关注短期偿债能力")
            
            if pb_ratio and pb_ratio < 1:
                notes.append("- P/B比率低于1，可能存在价值投资机会")
        
        # 移除数据完整性抱怨，基于现有数据进行正面分析
        if available_metrics > 0:
            notes.append(f"- 基于{available_metrics}项关键财务指标进行深度分析")
        
        return notes


# 创建全局实例
analyst_data_provider = AnalystDataProvider()