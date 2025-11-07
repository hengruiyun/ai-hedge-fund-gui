#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务计算模块

提供各种财务指标的计算函数，用于补充AKShare数据源中缺失的指标.
包括估值指标、盈利指标、效率指标等的计算逻辑.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


class FinancialCalculator:
    """财务计算器类，提供各种财务指标的计算方法"""
    
    @staticmethod
    def calculate_enterprise_value(market_cap: float, total_debt: float, cash: float) -> Optional[float]:
        """
        计算企业价值 (Enterprise Value)
        公式: EV = 市值 + 总债务 - 现金及现金等价物
        
        Args:
            market_cap: 市值
            total_debt: 总债务
            cash: 现金及现金等价物
            
        Returns:
            企业价值，如果数据不足则返回None
        """
        if market_cap is None:
            return None
        debt = total_debt or 0.0
        cash_amount = cash or 0.0
        return market_cap + debt - cash_amount
    
    @staticmethod
    def calculate_ev_to_ebitda(enterprise_value: float, ebitda: float) -> Optional[float]:
        """
        计算EV/EBITDA比率
        
        Args:
            enterprise_value: 企业价值
            ebitda: 息税折旧摊销前利润
            
        Returns:
            EV/EBITDA比率
        """
        if not enterprise_value or not ebitda or ebitda <= 0:
            return None
        return enterprise_value / ebitda
    
    @staticmethod
    def calculate_ev_to_sales(enterprise_value: float, revenue: float) -> Optional[float]:
        """
        计算EV/Sales比率
        
        Args:
            enterprise_value: 企业价值
            revenue: 营业收入
            
        Returns:
            EV/Sales比率
        """
        if not enterprise_value or not revenue or revenue <= 0:
            return None
        return enterprise_value / revenue
    
    @staticmethod
    def calculate_ebitda(operating_income: float, depreciation: float, amortization: float = 0) -> Optional[float]:
        """
        计算EBITDA (息税折旧摊销前利润)
        公式: EBITDA = 营业利润 + 折旧 + 摊销
        
        Args:
            operating_income: 营业利润
            depreciation: 折旧
            amortization: 摊销
            
        Returns:
            EBITDA
        """
        if operating_income is None:
            return None
        depreciation_amount = depreciation or 0.0
        amortization_amount = amortization or 0.0
        return operating_income + depreciation_amount + amortization_amount
    
    @staticmethod
    def estimate_ebitda_from_operating_income(operating_income: float, multiplier: float = 1.2) -> Optional[float]:
        """
        从营业利润估算EBITDA
        当缺少折旧摊销数据时的简化估算方法
        
        Args:
            operating_income: 营业利润
            multiplier: 估算倍数，默认1.2
            
        Returns:
            估算的EBITDA
        """
        if operating_income is None or operating_income <= 0:
            return None
        return operating_income * multiplier
    
    @staticmethod
    def calculate_ebitda_margin(ebitda: float, revenue: float) -> Optional[float]:
        """
        计算EBITDA利润率
        公式: EBITDA Margin = EBITDA / Revenue
        
        Args:
            ebitda: EBITDA
            revenue: 营业收入
            
        Returns:
            EBITDA利润率
        """
        if not ebitda or not revenue or revenue <= 0:
            return None
        return ebitda / revenue
    
    @staticmethod
    def calculate_working_capital(current_assets: float, current_liabilities: float) -> Optional[float]:
        """
        计算营运资金
        公式: Working Capital = 流动资产 - 流动负债
        
        Args:
            current_assets: 流动资产
            current_liabilities: 流动负债
            
        Returns:
            营运资金
        """
        if current_assets is None or current_liabilities is None:
            return None
        return current_assets - current_liabilities
    
    @staticmethod
    def calculate_free_cash_flow(operating_cash_flow: float, capital_expenditures: float) -> Optional[float]:
        """
        计算自由现金流
        公式: FCF = 经营现金流 - 资本支出
        
        Args:
            operating_cash_flow: 经营现金流
            capital_expenditures: 资本支出
            
        Returns:
            自由现金流
        """
        if operating_cash_flow is None or capital_expenditures is None:
            return None
        return operating_cash_flow - capital_expenditures
    
    @staticmethod
    def calculate_return_on_invested_capital(ebit: float, tax_rate: float, invested_capital: float) -> Optional[float]:
        """
        计算投入资本回报率 (ROIC)
        公式: ROIC = EBIT * (1 - 税率) / 投入资本
        
        Args:
            ebit: 息税前利润
            tax_rate: 税率
            invested_capital: 投入资本
            
        Returns:
            投入资本回报率
        """
        if not ebit or not invested_capital or invested_capital <= 0:
            return None
        tax_rate_val = tax_rate or 0.25  # 默认税率25%
        return (ebit * (1 - tax_rate_val)) / invested_capital
    
    @staticmethod
    def calculate_shares_outstanding(market_cap: float, stock_price: float) -> Optional[float]:
        """
        计算流通股数
        公式: Shares Outstanding = 市值 / 股价
        
        Args:
            market_cap: 市值
            stock_price: 股价
            
        Returns:
            流通股数
        """
        if not market_cap or not stock_price or stock_price <= 0:
            return None
        return market_cap / stock_price
    
    @staticmethod
    def estimate_tax_rate(tax_expense: float, pretax_income: float) -> float:
        """
        估算税率
        公式: Tax Rate = 税费 / 税前利润
        
        Args:
            tax_expense: 税费
            pretax_income: 税前利润
            
        Returns:
            税率，如果无法计算则返回默认值0.25
        """
        if not tax_expense or not pretax_income or pretax_income <= 0:
            return 0.25  # 默认税率25%
        return tax_expense / pretax_income
    
    @staticmethod
    def calculate_book_value_per_share(shareholders_equity: float, shares_outstanding: float) -> Optional[float]:
        """
        计算每股净资产
        公式: BVPS = 股东权益 / 流通股数
        
        Args:
            shareholders_equity: 股东权益
            shares_outstanding: 流通股数
            
        Returns:
            每股净资产
        """
        if not shareholders_equity or not shares_outstanding or shares_outstanding <= 0:
            return None
        return shareholders_equity / shares_outstanding
    
    @staticmethod
    def calculate_price_to_book_ratio(stock_price: float, book_value_per_share: float) -> Optional[float]:
        """
        计算市净率 (P/B)
        公式: P/B = 股价 / 每股净资产
        
        Args:
            stock_price: 股价
            book_value_per_share: 每股净资产
            
        Returns:
            市净率
        """
        if not stock_price or not book_value_per_share or book_value_per_share <= 0:
            return None
        return stock_price / book_value_per_share
    
    @staticmethod
    def calculate_price_to_sales_ratio(market_cap: float, revenue: float) -> Optional[float]:
        """
        计算市销率 (P/S)
        公式: P/S = 市值 / 营业收入
        
        Args:
            market_cap: 市值
            revenue: 营业收入
            
        Returns:
            市销率
        """
        if not market_cap or not revenue or revenue <= 0:
            return None
        return market_cap / revenue
    
    @staticmethod
    def calculate_peg_ratio(pe_ratio: float, earnings_growth_rate: float) -> Optional[float]:
        """
        计算PEG比率
        公式: PEG = 市盈率 / 盈利增长率(%)
        
        Args:
            pe_ratio: 市盈率
            earnings_growth_rate: 盈利增长率 (小数形式，如0.15表示15%)
            
        Returns:
            PEG比率
        """
        if not pe_ratio or not earnings_growth_rate or earnings_growth_rate <= 0:
            return None
        return pe_ratio / (earnings_growth_rate * 100)  # 增长率转换为百分比
    
    @staticmethod
    def calculate_debt_to_total_capital(total_debt: float, shareholders_equity: float) -> Optional[float]:
        """
        计算债务占总资本比率
        公式: Debt-to-Total Capital = 总债务 / (总债务 + 股东权益)
        
        Args:
            total_debt: 总债务
            shareholders_equity: 股东权益
            
        Returns:
            债务占总资本比率
        """
        if total_debt is None or shareholders_equity is None:
            return None
        total_capital = total_debt + shareholders_equity
        if total_capital <= 0:
            return None
        return total_debt / total_capital
    
    @staticmethod
    def calculate_return_on_assets(net_income: float, total_assets: float) -> Optional[float]:
        """
        计算总资产收益率 (ROA)
        公式: ROA = 净利润 / 总资产
        
        Args:
            net_income: 净利润
            total_assets: 总资产
            
        Returns:
            总资产收益率
        """
        if not net_income or not total_assets or total_assets <= 0:
            return None
        return net_income / total_assets
    
    @staticmethod
    def calculate_return_on_equity(net_income: float, shareholders_equity: float) -> Optional[float]:
        """
        计算股东权益回报率 (ROE)
        公式: ROE = 净利润 / 股东权益
        
        Args:
            net_income: 净利润
            shareholders_equity: 股东权益
            
        Returns:
            股东权益回报率
        """
        if not net_income or not shareholders_equity or shareholders_equity <= 0:
            return None
        return net_income / shareholders_equity
    
    @staticmethod
    def calculate_gross_margin(gross_profit: float, revenue: float) -> Optional[float]:
        """
        计算毛利率
        公式: Gross Margin = 毛利润 / 营业收入
        
        Args:
            gross_profit: 毛利润
            revenue: 营业收入
            
        Returns:
            毛利率
        """
        if not gross_profit or not revenue or revenue <= 0:
            return None
        return gross_profit / revenue
    
    @staticmethod
    def calculate_operating_margin(operating_income: float, revenue: float) -> Optional[float]:
        """
        计算营业利润率
        公式: Operating Margin = 营业利润 / 营业收入
        
        Args:
            operating_income: 营业利润
            revenue: 营业收入
            
        Returns:
            营业利润率
        """
        if not operating_income or not revenue or revenue <= 0:
            return None
        return operating_income / revenue
    
    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> Optional[float]:
        """
        计算净利润率
        公式: Net Margin = 净利润 / 营业收入
        
        Args:
            net_income: 净利润
            revenue: 营业收入
            
        Returns:
            净利润率
        """
        if not net_income or not revenue or revenue <= 0:
            return None
        return net_income / revenue
    
    @staticmethod
    def calculate_asset_turnover(revenue: float, total_assets: float) -> Optional[float]:
        """
        计算资产周转率
        公式: Asset Turnover = 营业收入 / 总资产
        
        Args:
            revenue: 营业收入
            total_assets: 总资产
            
        Returns:
            资产周转率
        """
        if not revenue or not total_assets or total_assets <= 0:
            return None
        return revenue / total_assets
    
    @staticmethod
    def calculate_inventory_turnover(cost_of_goods_sold: float, average_inventory: float) -> Optional[float]:
        """
        计算存货周转率
        公式: Inventory Turnover = 销售成本 / 平均存货
        
        Args:
            cost_of_goods_sold: 销售成本
            average_inventory: 平均存货
            
        Returns:
            存货周转率
        """
        if not cost_of_goods_sold or not average_inventory or average_inventory <= 0:
            return None
        return cost_of_goods_sold / average_inventory
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
        """
        计算流动比率
        公式: Current Ratio = 流动资产 / 流动负债
        
        Args:
            current_assets: 流动资产
            current_liabilities: 流动负债
            
        Returns:
            流动比率
        """
        if not current_assets or not current_liabilities or current_liabilities <= 0:
            return None
        return current_assets / current_liabilities
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Optional[float]:
        """
        计算速动比率
        公式: Quick Ratio = (流动资产 - 存货) / 流动负债
        
        Args:
            current_assets: 流动资产
            inventory: 存货
            current_liabilities: 流动负债
            
        Returns:
            速动比率
        """
        if not current_assets or not current_liabilities or current_liabilities <= 0:
            return None
        inventory_val = inventory or 0.0
        return (current_assets - inventory_val) / current_liabilities
    
    @staticmethod
    def calculate_debt_to_equity_ratio(total_debt: float, shareholders_equity: float) -> Optional[float]:
        """
        计算债务权益比率
        公式: D/E = 总债务 / 股东权益
        
        Args:
            total_debt: 总债务
            shareholders_equity: 股东权益
            
        Returns:
            债务权益比率
        """
        if not total_debt or not shareholders_equity or shareholders_equity <= 0:
            return None
        return total_debt / shareholders_equity
    
    @staticmethod
    def calculate_owner_earnings(net_income: float, depreciation: float, amortization: float, 
                               capex: float, working_capital_change: float = 0) -> Optional[float]:
        """
        计算巴菲特的所有者收益 (Owner Earnings)
        公式: Owner Earnings = 净利润 + 折旧摊销 - 维持性资本支出 - 营运资金变化
        
        Args:
            net_income: 净利润
            depreciation: 折旧
            amortization: 摊销
            capex: 资本支出
            working_capital_change: 营运资金变化
            
        Returns:
            所有者收益
        """
        if net_income is None:
            return None
        
        depreciation_val = depreciation or 0.0
        amortization_val = amortization or 0.0
        capex_val = abs(capex) if capex else 0.0  # 资本支出通常为负值
        wc_change = working_capital_change or 0.0
        
        # 估算维持性资本支出为总资本支出的85%（保守估计）
        maintenance_capex = capex_val * 0.85
        
        return net_income + depreciation_val + amortization_val - maintenance_capex - wc_change
    
    @staticmethod
    def calculate_fcf_yield(free_cash_flow: float, market_cap: float) -> Optional[float]:
        """
        计算自由现金流收益率 (FCF Yield)
        公式: FCF Yield = 自由现金流 / 市值
        
        Args:
            free_cash_flow: 自由现金流
            market_cap: 市值
            
        Returns:
            自由现金流收益率
        """
        if not free_cash_flow or not market_cap or market_cap <= 0:
            return None
        return free_cash_flow / market_cap
    
    @staticmethod
    def calculate_book_value_growth_rate(current_book_value: float, previous_book_value: float, 
                                       years: int = 1) -> Optional[float]:
        """
        计算账面价值增长率
        公式: Growth Rate = ((Current BV / Previous BV) ^ (1/years)) - 1
        
        Args:
            current_book_value: 当前账面价值
            previous_book_value: 之前账面价值
            years: 年数
            
        Returns:
            账面价值增长率
        """
        if not current_book_value or not previous_book_value or previous_book_value <= 0 or years <= 0:
            return None
        return ((current_book_value / previous_book_value) ** (1/years)) - 1
    
    @staticmethod
    def calculate_roic(ebit: float, tax_rate: float, invested_capital: float) -> Optional[float]:
        """
        计算投入资本回报率 (ROIC) - 芒格偏好的指标
        公式: ROIC = EBIT * (1 - 税率) / 投入资本
        
        Args:
            ebit: 息税前利润
            tax_rate: 税率
            invested_capital: 投入资本 (股东权益 + 有息债务)
            
        Returns:
            投入资本回报率
        """
        if not ebit or not invested_capital or invested_capital <= 0:
            return None
        tax_rate_val = tax_rate if tax_rate is not None else 0.25  # 默认税率25%
        return (ebit * (1 - tax_rate_val)) / invested_capital
    
    @staticmethod
    def calculate_invested_capital(shareholders_equity: float, total_debt: float) -> Optional[float]:
        """
        计算投入资本
        公式: Invested Capital = 股东权益 + 有息债务
        
        Args:
            shareholders_equity: 股东权益
            total_debt: 总债务
            
        Returns:
            投入资本
        """
        if shareholders_equity is None:
            return None
        debt_val = total_debt or 0.0
        return shareholders_equity + debt_val
    
    @staticmethod
    def calculate_earnings_growth_rate(current_earnings: float, previous_earnings: float, 
                                     years: int = 1) -> Optional[float]:
        """
        计算盈利增长率 (用于PEG计算)
        公式: Growth Rate = ((Current Earnings / Previous Earnings) ^ (1/years)) - 1
        
        Args:
            current_earnings: 当前盈利
            previous_earnings: 之前盈利
            years: 年数
            
        Returns:
            盈利增长率
        """
        if not current_earnings or not previous_earnings or previous_earnings <= 0 or years <= 0:
            return None
        return ((current_earnings / previous_earnings) ** (1/years)) - 1
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> Optional[float]:
        """
        计算债务股本比 (Debt-to-Equity)
        公式: D/E = 总债务 / 股东权益
        
        Args:
            total_debt: 总债务
            shareholders_equity: 股东权益
            
        Returns:
            债务股本比
        """
        if not shareholders_equity or shareholders_equity <= 0:
            return None
        debt_val = total_debt or 0.0
        return debt_val / shareholders_equity
    
    @classmethod
    def enhance_financial_metrics(cls, metrics_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强财务指标数据，计算缺失的指标
        
        Args:
            metrics_dict: 包含基础财务数据的字典
            
        Returns:
            增强后的财务指标字典
        """
        enhanced = metrics_dict.copy()
        
        # 获取基础数据
        market_cap = enhanced.get('market_cap')
        revenue = enhanced.get('revenue')
        net_income = enhanced.get('net_income')
        operating_income = enhanced.get('operating_income')
        gross_profit = enhanced.get('gross_profit')
        total_assets = enhanced.get('total_assets')
        total_liabilities = enhanced.get('total_liabilities')
        shareholders_equity = enhanced.get('shareholders_equity')
        total_debt = enhanced.get('total_debt')
        current_assets = enhanced.get('current_assets')
        current_liabilities = enhanced.get('current_liabilities')
        operating_cash_flow = enhanced.get('operating_cash_flow')
        capital_expenditures = enhanced.get('capital_expenditures')
        cash = enhanced.get('cash_and_cash_equivalents')
        stock_price = enhanced.get('stock_price')
        shares_outstanding = enhanced.get('shares_outstanding')
        
        # 计算企业价值
        if not enhanced.get('enterprise_value') and market_cap:
            enhanced['enterprise_value'] = cls.calculate_enterprise_value(market_cap, total_debt, cash)
        
        # 计算EBITDA
        if not enhanced.get('ebitda') and operating_income:
            enhanced['ebitda'] = cls.estimate_ebitda_from_operating_income(operating_income)
        
        # 计算EBITDA利润率
        if not enhanced.get('ebitda_margin'):
            ebitda = enhanced.get('ebitda')
            if ebitda and revenue:
                enhanced['ebitda_margin'] = cls.calculate_ebitda_margin(ebitda, revenue)
        
        # 计算EV比率
        enterprise_value = enhanced.get('enterprise_value')
        if enterprise_value:
            if not enhanced.get('ev_to_ebitda'):
                ebitda = enhanced.get('ebitda')
                if ebitda:
                    enhanced['ev_to_ebitda'] = cls.calculate_ev_to_ebitda(enterprise_value, ebitda)
            
            if not enhanced.get('ev_to_sales') and revenue:
                enhanced['ev_to_sales'] = cls.calculate_ev_to_sales(enterprise_value, revenue)
        
        # 计算营运资金
        if not enhanced.get('working_capital') and current_assets and current_liabilities:
            enhanced['working_capital'] = cls.calculate_working_capital(current_assets, current_liabilities)
        
        # 计算自由现金流
        if not enhanced.get('free_cash_flow') and operating_cash_flow and capital_expenditures:
            enhanced['free_cash_flow'] = cls.calculate_free_cash_flow(operating_cash_flow, capital_expenditures)
        
        # 计算流通股数
        if not enhanced.get('shares_outstanding') and market_cap and stock_price:
            enhanced['shares_outstanding'] = cls.calculate_shares_outstanding(market_cap, stock_price)
        
        # 计算各种比率
        if revenue:
            if not enhanced.get('gross_margin') and gross_profit:
                enhanced['gross_margin'] = cls.calculate_gross_margin(gross_profit, revenue)
            
            if not enhanced.get('operating_margin') and operating_income:
                enhanced['operating_margin'] = cls.calculate_operating_margin(operating_income, revenue)
            
            if not enhanced.get('net_margin') and net_income:
                enhanced['net_margin'] = cls.calculate_net_margin(net_income, revenue)
            
            if not enhanced.get('price_to_sales_ratio') and market_cap:
                enhanced['price_to_sales_ratio'] = cls.calculate_price_to_sales_ratio(market_cap, revenue)
        
        # 计算ROE和ROA
        if not enhanced.get('return_on_equity') and net_income and shareholders_equity:
            enhanced['return_on_equity'] = cls.calculate_return_on_equity(net_income, shareholders_equity)
        
        if not enhanced.get('return_on_assets') and net_income and total_assets:
            enhanced['return_on_assets'] = cls.calculate_return_on_assets(net_income, total_assets)
        
        # 计算债务比率
        if not enhanced.get('debt_to_total_capital') and total_debt is not None and shareholders_equity:
            enhanced['debt_to_total_capital'] = cls.calculate_debt_to_total_capital(total_debt, shareholders_equity)
        
        if not enhanced.get('debt_to_equity_ratio') and total_debt and shareholders_equity:
            enhanced['debt_to_equity_ratio'] = cls.calculate_debt_to_equity_ratio(total_debt, shareholders_equity)
        
        # 新增：计算债务股本比 (为伯里分析师)
        if not enhanced.get('debt_to_equity') and shareholders_equity:
            enhanced['debt_to_equity'] = cls.calculate_debt_to_equity(total_debt, shareholders_equity)
        
        # 新增：计算自由现金流收益率 (为伯里分析师)
        free_cash_flow = enhanced.get('free_cash_flow')
        if not enhanced.get('fcf_yield') and free_cash_flow and market_cap:
            enhanced['fcf_yield'] = cls.calculate_fcf_yield(free_cash_flow, market_cap)
        
        # 新增：计算所有者收益 (为巴菲特分析师)
        depreciation = enhanced.get('depreciation')
        amortization = enhanced.get('amortization')
        if not enhanced.get('owner_earnings') and net_income:
            enhanced['owner_earnings'] = cls.calculate_owner_earnings(
                net_income, depreciation, amortization, capital_expenditures
            )
        
        # 新增：计算投入资本 (为芒格分析师)
        if not enhanced.get('invested_capital') and shareholders_equity:
            enhanced['invested_capital'] = cls.calculate_invested_capital(shareholders_equity, total_debt)
        
        # 新增：计算ROIC (为芒格分析师)
        ebit = enhanced.get('ebit') or operating_income  # 使用EBIT或营业利润
        invested_capital = enhanced.get('invested_capital')
        tax_rate = enhanced.get('tax_rate')
        if not enhanced.get('roic') and ebit and invested_capital:
            enhanced['roic'] = cls.calculate_roic(ebit, tax_rate, invested_capital)
        
        # 新增：计算流动比率和速动比率
        if not enhanced.get('current_ratio') and current_assets and current_liabilities:
            enhanced['current_ratio'] = cls.calculate_current_ratio(current_assets, current_liabilities)
        
        inventory = enhanced.get('inventory')
        if not enhanced.get('quick_ratio') and current_assets and current_liabilities:
            enhanced['quick_ratio'] = cls.calculate_quick_ratio(current_assets, inventory, current_liabilities)
        
        # 新增：计算资产周转率
        if not enhanced.get('asset_turnover') and revenue and total_assets:
            enhanced['asset_turnover'] = cls.calculate_asset_turnover(revenue, total_assets)
        
        return enhanced
    
    @classmethod
    def enhance_with_historical_data(cls, current_data: Dict[str, Any], 
                                   historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        使用历史数据计算增长率和趋势指标
        
        Args:
            current_data: 当前期间的财务数据
            historical_data: 历史期间的财务数据列表 (按时间倒序)
            
        Returns:
            包含增长率和趋势指标的增强数据
        """
        enhanced = current_data.copy()
        
        if not historical_data or len(historical_data) < 2:
            return enhanced
        
        # 计算盈利增长率 (用于PEG比率)
        current_earnings = current_data.get('net_income')
        if current_earnings and len(historical_data) >= 1:
            previous_earnings = historical_data[0].get('net_income')
            if previous_earnings:
                earnings_growth = cls.calculate_earnings_growth_rate(current_earnings, previous_earnings)
                if earnings_growth is not None:
                    enhanced['earnings_growth_rate'] = earnings_growth
                    
                    # 计算PEG比率
                    pe_ratio = current_data.get('pe_ratio')
                    if pe_ratio and earnings_growth > 0:
                        enhanced['peg_ratio'] = cls.calculate_peg_ratio(pe_ratio, earnings_growth)
        
        # 计算账面价值增长率 (巴菲特偏好指标)
        current_book_value = current_data.get('shareholders_equity')
        if current_book_value and len(historical_data) >= 1:
            previous_book_value = historical_data[0].get('shareholders_equity')
            if previous_book_value:
                book_value_growth = cls.calculate_book_value_growth_rate(current_book_value, previous_book_value)
                if book_value_growth is not None:
                    enhanced['book_value_growth_rate'] = book_value_growth
        
        # 计算多年平均ROIC (芒格偏好指标)
        roic_values = []
        for period_data in [current_data] + historical_data[:4]:  # 最近5年
            roic = period_data.get('roic')
            if roic is not None:
                roic_values.append(roic)
        
        if len(roic_values) >= 3:
            enhanced['average_roic_5y'] = sum(roic_values) / len(roic_values)
            enhanced['roic_consistency'] = len([r for r in roic_values if r > 0.15]) / len(roic_values)
        
        # 计算收入增长率
        current_revenue = current_data.get('revenue')
        if current_revenue and len(historical_data) >= 1:
            previous_revenue = historical_data[0].get('revenue')
            if previous_revenue:
                revenue_growth = cls.calculate_earnings_growth_rate(current_revenue, previous_revenue)
                if revenue_growth is not None:
                    enhanced['revenue_growth_rate'] = revenue_growth
        
        # 计算自由现金流增长率
        current_fcf = current_data.get('free_cash_flow')
        if current_fcf and len(historical_data) >= 1:
            previous_fcf = historical_data[0].get('free_cash_flow')
            if previous_fcf:
                fcf_growth = cls.calculate_earnings_growth_rate(current_fcf, previous_fcf)
                if fcf_growth is not None:
                    enhanced['fcf_growth_rate'] = fcf_growth
        
        return enhanced


# 创建全局实例
financial_calculator = FinancialCalculator()