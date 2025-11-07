from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from .data_accuracy_validator import data_accuracy_validator
    ACCURACY_VALIDATION_ENABLED = True
except ImportError:
    data_accuracy_validator = None
    ACCURACY_VALIDATION_ENABLED = False
    logger.warning("数据准确性验证器未找到，将跳过准确性验证")

class DataEnhancer:
    """
    数据增强器 - 专门用于解决分析师数据缺失问题
    通过多种方法补充和计算缺失的财务数据
    """
    
    def __init__(self, akshare_adapter=None):
        from .data_quality_fix import DataQualityFixer
        self.data_quality_fixer = DataQualityFixer()
        self.calculation_methods = {
            # 基础财务指标计算方法
            'enterprise_value': self._calculate_enterprise_value,
            'ebitda': self._estimate_ebitda,
            'ev_to_ebitda': self._calculate_ev_ebitda,
            'ev_to_sales': self._calculate_ev_sales,
            'free_cash_flow': self._calculate_free_cash_flow,
            'working_capital': self._calculate_working_capital,
            'debt_to_equity': self._calculate_debt_to_equity,
            'current_ratio': self._calculate_current_ratio,
            'quick_ratio': self._calculate_quick_ratio,
            'roic': self._calculate_roic,
            'roe': self._calculate_roe,
            'roa': self._calculate_roa,
            'gross_margin': self._calculate_gross_margin,
            'operating_margin': self._calculate_operating_margin,
            'net_margin': self._calculate_net_margin,
            'asset_turnover': self._calculate_asset_turnover,
            'inventory_turnover': self._calculate_inventory_turnover,
            'fcf_yield': self._calculate_fcf_yield,
            'book_value_per_share': self._calculate_book_value_per_share,
            'earnings_per_share': self._calculate_eps,
            'price_to_book': self._calculate_price_to_book,
            'price_to_earnings': self._calculate_price_to_earnings,
            'pe_ratio': self._calculate_price_to_earnings,
            'price_to_sales': self._calculate_price_to_sales,
            'peg_ratio': self._calculate_peg_ratio,
            'owner_earnings': self._calculate_owner_earnings,
            'invested_capital': self._calculate_invested_capital,
            'maintenance_capex': self._estimate_maintenance_capex,
            'intrinsic_value': self._calculate_intrinsic_value,
            'graham_number': self._calculate_graham_number,
            'ncav': self._calculate_ncav,
            'debt_to_total_capital': self._calculate_debt_to_total_capital,
            'interest_coverage': self._calculate_interest_coverage,
            'operating_cash_flow_ratio': self._calculate_ocf_ratio,
            'cash_ratio': self._calculate_cash_ratio,
            'revenue_growth_rate': self._calculate_revenue_growth_rate,
            'beta_coefficient': self._calculate_beta_coefficient,
            'sharpe_ratio': self._calculate_sharpe_ratio,
        }
        
        # 集成AKShare适配器
        self.akshare_adapter = akshare_adapter
        if self.akshare_adapter is None:
            try:
                from .akshare_adapter import akshare_adapter
                self.akshare_adapter = akshare_adapter
            except ImportError:
                # 如果无法导入AKShare适配器，继续使用基本功能
                pass
    
    def enhance_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强财务数据，计算缺失的指标
        
        Args:
            data: 原始财务数据
            
        Returns:
            增强后的财务数据
        """
        if not data:
            return data
            
        enhanced_data = data.copy()
        
        # 记录增强前的字段数量
        original_fields = len([v for v in enhanced_data.values() if v is not None and v != 0])
        
        print(f"[Data Enhancer] 开始数据增强，原始字段: {original_fields}")
        
        # 1. 数据质量修复
        try:
            enhanced_data = self.data_quality_fixer.fix_invalid_data(enhanced_data)
            enhanced_data = self.data_quality_fixer.fix_missing_data(enhanced_data, enhanced_data.get('ticker', 'UNKNOWN'))
        except Exception as e:
            logger.warning(f"数据质量修复失败: {e}")
        
        # 2. 计算基础财务指标
        calculated_count = 0
        for metric_name, calc_func in self.calculation_methods.items():
            try:
                if metric_name not in enhanced_data or enhanced_data[metric_name] is None:
                    calculated_value = calc_func(enhanced_data)
                    if calculated_value is not None and calculated_value != 0:
                        enhanced_data[metric_name] = calculated_value
                        calculated_count += 1
            except Exception as e:
                logger.debug(f"计算 {metric_name} 失败: {e}")
        
        # 3. 添加常用的财务比率和指标
        try:
            # 确保关键字段存在
            self._ensure_key_fields(enhanced_data)
            
            # 计算衍生指标
            self._calculate_derived_metrics(enhanced_data)
            
        except Exception as e:
            logger.warning(f"计算衍生指标失败: {e}")
        
        # 4. 标准化字段名
        try:
            enhanced_data = self._standardize_field_names(enhanced_data)
        except Exception as e:
            logger.warning(f"字段名标准化失败: {e}")
        
        # 5. 数据准确性验证（如果启用）
        if ACCURACY_VALIDATION_ENABLED and data_accuracy_validator:
            try:
                print(f"[Data Enhancer] 开始准确性验证...")
                validated_data = data_accuracy_validator.validate_enhanced_data(data, enhanced_data)
                
                # 记录验证结果
                validation_meta = validated_data.get('_validation_meta', {})
                removed_count = validation_meta.get('removed_fields', 0)
                if removed_count > 0:
                    print(f"[Data Enhancer] 准确性验证完成，移除了 {removed_count} 个偏差过大的字段")
                else:
                    print(f"[Data Enhancer] 准确性验证完成，所有数据通过验证")
                
                enhanced_data = validated_data
            except Exception as e:
                logger.warning(f"数据准确性验证失败: {e}")
                print(f"[Data Enhancer] 准确性验证出错，继续使用未验证数据")
        
        # 记录增强后的字段数量
        final_fields = len([v for v in enhanced_data.values() if v is not None and v != 0])
        added_fields = final_fields - original_fields
        
        print(f"[Data Enhancer] 数据增强完成，新增字段: {added_fields}, 总字段: {final_fields}")
        
        return enhanced_data
    
    def enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """enhance_data方法的别名，调用enhance_financial_data"""
        return self.enhance_financial_data(data)
    
    def _safe_divide(self, numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """安全除法，避免除零错误"""
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator
    
    def _safe_get(self, data: Dict[str, Any], key: str, default: Optional[float] = None) -> Optional[float]:
        """安全获取数据，支持多种键名变体"""
        # 直接键名
        if key in data and data[key] is not None:
            # 特殊处理列表类型数据（如历史价格）
            if isinstance(data[key], list):
                return data[key] # 直接返回列表，不转换为float

        # 常见的键名变体映射
            try:
                return float(data[key])
            except (ValueError, TypeError):
                return default
        
        # 常见的键名变体映射
        key_variants = {
            'revenue': ['营业收入', 'total_revenue', 'sales'],
            'net_income': ['净利润', '归母净利润', 'net_earnings'],
            'total_assets': ['资产总计', 'total_asset'],
            'total_liabilities': ['负债合计', 'total_liability'],
            'shareholders_equity': ['股东权益合计', '所有者权益', 'stockholders_equity'],
            'current_assets': ['流动资产合计', 'current_asset'],
            'current_liabilities': ['流动负债合计', 'current_liability'],
            'cash_and_cash_equivalents': ['货币资金', 'cash', 'cash_and_equivalents'],
            'operating_cash_flow': ['经营活动产生的现金流量净额', 'operating_cash_flows'],
            'capital_expenditures': ['购建固定资产、无形资产和其他长期资产支付的现金', 'capex'],
            'total_debt': ['总债务', 'debt'],
            'operating_income': ['营业利润', 'operating_profit'],
            'gross_profit': ['毛利润', 'gross_income'],
            'depreciation': ['折旧', 'depreciation_and_amortization'],
            'shares_outstanding': ['流通股数', 'outstanding_shares'],
            'inventory': ['存货', 'inventories'],
            'research_and_development': ['研发费用', 'rd_expense'],
        }
        
        # 尝试变体键名
        for variant in key_variants.get(key, []):
            if variant in data and data[variant] is not None:
                # 特殊处理列表类型数据
                if isinstance(data[variant], list):
                    return data[variant]
                try:
                    return float(data[variant])
                except (ValueError, TypeError):
                    continue
        
        return default
    
    # 企业价值计算 - 增强版
    def _calculate_enterprise_value(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_enterprise_value_enhanced(data)
    
    def _calculate_enterprise_value_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版企业价值计算"""
        
        # 方法1: 标准计算 (最准确)
        market_cap = self._safe_get(data, 'market_cap')
        total_debt = self._safe_get(data, 'total_debt', 0)
        cash = self._safe_get(data, 'cash_and_cash_equivalents', 0)
        
        if market_cap is not None:
            return market_cap + total_debt - cash
        
        # 方法2: 从股价和股数计算市值
        stock_price = self._safe_get(data, 'current_price')
        shares_outstanding = self._safe_get(data, 'shares_outstanding')
        
        if stock_price is not None and shares_outstanding is not None:
            calculated_market_cap = stock_price * shares_outstanding
            return calculated_market_cap + total_debt - cash
        
        # 方法3: 从账面价值估算 (最后选择)
        book_value = self._safe_get(data, 'total_equity')
        if book_value is not None:
            # 使用市净率估算，假设市净率为1.5
            estimated_market_cap = book_value * 1.5
            return estimated_market_cap + total_debt - cash
        
        return None
    
    # EBITDA估算
    def _estimate_ebitda(self, data: Dict[str, Any]) -> Optional[float]:
        operating_income = self._safe_get(data, 'operating_income')
        depreciation = self._safe_get(data, 'depreciation')
        
        if operating_income is None:
            return None
        
        # 如果有折旧数据，直接相加
        if depreciation is not None:
            return operating_income + depreciation
        
        # 否则估算折旧为营业利润的8-12%
        estimated_depreciation = operating_income * 0.10
        return operating_income + estimated_depreciation
    
    # EV/EBITDA计算
    def _calculate_ev_ebitda(self, data: Dict[str, Any]) -> Optional[float]:
        enterprise_value = self._safe_get(data, 'enterprise_value')
        ebitda = self._safe_get(data, 'ebitda')
        
        return self._safe_divide(enterprise_value, ebitda)
    
    # EV/Sales计算
    def _calculate_ev_sales(self, data: Dict[str, Any]) -> Optional[float]:
        enterprise_value = self._safe_get(data, 'enterprise_value')
        revenue = self._safe_get(data, 'revenue')
        
        return self._safe_divide(enterprise_value, revenue)
    
    # 自由现金流计算 - 增强版
    def _calculate_free_cash_flow(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_free_cash_flow_enhanced(data)
    
    def _calculate_free_cash_flow_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版自由现金流计算，支持多种计算方法"""
        
        # 方法1: 直接计算 (最准确)
        operating_cash_flow = self._safe_get(data, 'operating_cash_flow')
        capex = self._safe_get(data, 'capital_expenditures')
        
        if operating_cash_flow is not None and capex is not None:
            return operating_cash_flow - abs(capex)
        
        # 方法2: 从净利润估算 (次选)
        net_income = self._safe_get(data, 'net_income')
        depreciation = self._safe_get(data, 'depreciation')
        working_capital_change = self._safe_get(data, 'working_capital_change', 0)
        
        if net_income is not None:
            # 估算折旧
            if depreciation is None:
                depreciation = net_income * 0.08  # 估算为净利润的8%
            
            # 估算资本支出
            if capex is None:
                capex = depreciation * 1.2  # 估算为折旧的120%
            
            return net_income + depreciation - working_capital_change - abs(capex)
        
        # 方法3: 从EBITDA估算 (最后选择)
        ebitda = self._safe_get(data, 'ebitda')
        if ebitda is not None:
            # 简化估算: FCF ≈ EBITDA * 0.6
            return ebitda * 0.6
        
        # 方法4: 从营业现金流估算 (如果只有营业现金流)
        if operating_cash_flow is not None:
            # 估算资本支出为营业现金流的15%
            estimated_capex = operating_cash_flow * 0.15
            return operating_cash_flow - estimated_capex
        
        return None
    
    # 营运资金计算
    def _calculate_working_capital(self, data: Dict[str, Any]) -> Optional[float]:
        current_assets = self._safe_get(data, 'current_assets')
        current_liabilities = self._safe_get(data, 'current_liabilities')
        
        if current_assets is None or current_liabilities is None:
            return None
        
        return current_assets - current_liabilities
    
    # 债务股权比计算
    def _calculate_debt_to_equity(self, data: Dict[str, Any]) -> Optional[float]:
        total_debt = self._safe_get(data, 'total_debt')
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        
        if total_debt is None:
            total_debt = 0  # 假设无债务
        
        return self._safe_divide(total_debt, shareholders_equity)
    
    # 流动比率计算
    def _calculate_current_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        current_assets = self._safe_get(data, 'current_assets')
        current_liabilities = self._safe_get(data, 'current_liabilities')
        
        return self._safe_divide(current_assets, current_liabilities)
    
    # 速动比率计算
    def _calculate_quick_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        current_assets = self._safe_get(data, 'current_assets')
        inventory = self._safe_get(data, 'inventory', 0)
        current_liabilities = self._safe_get(data, 'current_liabilities')
        
        if current_assets is None or current_liabilities is None:
            return None
        
        quick_assets = current_assets - inventory
        return self._safe_divide(quick_assets, current_liabilities)
    
    # ROIC计算 - 增强版
    def _calculate_roic(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_roic_enhanced(data)
    
    def _calculate_roic_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版ROIC计算"""
        
        # 计算NOPAT (税后营业利润)
        operating_income = self._safe_get(data, 'operating_income')
        tax_rate = self._safe_get(data, 'effective_tax_rate', 0.25)  # 默认25%税率
        
        if operating_income is not None:
            nopat = operating_income * (1 - tax_rate)
        else:
            # 从净利润估算NOPAT
            net_income = self._safe_get(data, 'net_income')
            interest_expense = self._safe_get(data, 'interest_expense', 0)
            if net_income is not None:
                nopat = net_income + interest_expense * (1 - tax_rate)
            else:
                return None
        
        # 计算投入资本
        invested_capital = self._calculate_invested_capital_enhanced(data)
        
        return self._safe_divide(nopat, invested_capital)
    
    # ROE计算
    def _calculate_roe(self, data: Dict[str, Any]) -> Optional[float]:
        net_income = self._safe_get(data, 'net_income')
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        
        return self._safe_divide(net_income, shareholders_equity)
    
    # ROA计算
    def _calculate_roa(self, data: Dict[str, Any]) -> Optional[float]:
        net_income = self._safe_get(data, 'net_income')
        total_assets = self._safe_get(data, 'total_assets')
        
        return self._safe_divide(net_income, total_assets)
    
    # 毛利率计算
    def _calculate_gross_margin(self, data: Dict[str, Any]) -> Optional[float]:
        gross_profit = self._safe_get(data, 'gross_profit')
        revenue = self._safe_get(data, 'revenue')
        
        return self._safe_divide(gross_profit, revenue)
    
    # 营业利润率计算
    def _calculate_operating_margin(self, data: Dict[str, Any]) -> Optional[float]:
        operating_income = self._safe_get(data, 'operating_income')
        revenue = self._safe_get(data, 'revenue')
        
        return self._safe_divide(operating_income, revenue)
    
    # 净利率计算
    def _calculate_net_margin(self, data: Dict[str, Any]) -> Optional[float]:
        net_income = self._safe_get(data, 'net_income')
        revenue = self._safe_get(data, 'revenue')
        
        return self._safe_divide(net_income, revenue)
    
    # 资产周转率计算
    def _calculate_asset_turnover(self, data: Dict[str, Any]) -> Optional[float]:
        revenue = self._safe_get(data, 'revenue')
        total_assets = self._safe_get(data, 'total_assets')
        
        return self._safe_divide(revenue, total_assets)
    
    # 存货周转率计算
    def _calculate_inventory_turnover(self, data: Dict[str, Any]) -> Optional[float]:
        revenue = self._safe_get(data, 'revenue')
        inventory = self._safe_get(data, 'inventory')
        
        return self._safe_divide(revenue, inventory)
    
    # 自由现金流收益率计算
    def _calculate_fcf_yield(self, data: Dict[str, Any]) -> Optional[float]:
        free_cash_flow = self._safe_get(data, 'free_cash_flow')
        market_cap = self._safe_get(data, 'market_cap')
        
        return self._safe_divide(free_cash_flow, market_cap)
    
    # 每股账面价值计算
    def _calculate_book_value_per_share(self, data: Dict[str, Any]) -> Optional[float]:
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        shares_outstanding = self._safe_get(data, 'shares_outstanding')
        
        return self._safe_divide(shareholders_equity, shares_outstanding)
    
    # 每股收益计算
    def _calculate_eps(self, data: Dict[str, Any]) -> Optional[float]:
        net_income = self._safe_get(data, 'net_income')
        shares_outstanding = self._safe_get(data, 'shares_outstanding')
        
        return self._safe_divide(net_income, shares_outstanding)
    
    # 市净率计算
    def _calculate_price_to_book(self, data: Dict[str, Any]) -> Optional[float]:
        market_cap = self._safe_get(data, 'market_cap')
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        
        return self._safe_divide(market_cap, shareholders_equity)
    
    # 市盈率计算
    def _calculate_price_to_earnings(self, data: Dict[str, Any]) -> Optional[float]:
        """计算市盈率 (P/E)"""
        
        # 方法1: 使用市值和净利润
        market_cap = self._safe_get(data, 'market_cap')
        net_income = self._safe_get(data, 'net_income')
        
        if market_cap is not None and net_income is not None and net_income > 0:
            pe_ratio = market_cap / net_income
            # 检查PE比率是否合理（0-100）
            if 0 < pe_ratio <= 100:
                return pe_ratio
            else:
                print(f"[Data Enhancer] 过滤异常PE比率: {pe_ratio:.2f} (方法1)")
                return None
        
        # 方法2: 使用股价和每股收益
        current_price = self._safe_get(data, 'current_price')
        eps = self._safe_get(data, 'earnings_per_share')
        if eps is None or isinstance(eps, list):
            eps = self._safe_get(data, 'eps')
        
        if (current_price is not None and not isinstance(current_price, list) and 
            eps is not None and not isinstance(eps, list) and eps > 0):
            pe_ratio = current_price / eps
            # 检查PE比率是否合理（0-100）
            if 0 < pe_ratio <= 100:
                return pe_ratio
            else:
                print(f"[Data Enhancer] 过滤异常PE比率: {pe_ratio:.2f} (方法2)")
                return None
        
        # 方法3: 计算每股收益然后计算P/E
        if current_price is not None and net_income is not None and net_income > 0:
            shares_outstanding = self._safe_get(data, 'shares_outstanding')
            if shares_outstanding is not None and shares_outstanding > 0:
                calculated_eps = net_income / shares_outstanding
                if calculated_eps > 0:
                    pe_ratio = current_price / calculated_eps
                    # 检查PE比率是否合理（0-100）
                    if 0 < pe_ratio <= 100:
                        return pe_ratio
                    else:
                        print(f"[Data Enhancer] 过滤异常PE比率: {pe_ratio:.2f} (方法3)")
                        return None
        
        return None
    
    # 市销率计算
    def _calculate_price_to_sales(self, data: Dict[str, Any]) -> Optional[float]:
        market_cap = self._safe_get(data, 'market_cap')
        revenue = self._safe_get(data, 'revenue')
        
        return self._safe_divide(market_cap, revenue)
    
    # PEG比率计算 - 增强版
    def _calculate_peg_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_peg_ratio_enhanced(data)
    
    def _calculate_peg_ratio_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版PEG比率计算"""
        
        # 尝试多种PE比率字段名
        pe_ratio = self._safe_get(data, 'price_to_earnings_ratio')
        if pe_ratio is None or isinstance(pe_ratio, list):
            pe_ratio = self._safe_get(data, 'pe_ratio')
        if pe_ratio is None or isinstance(pe_ratio, list):
            pe_ratio = self._safe_get(data, 'p_e_ratio')
        
        if pe_ratio is None or isinstance(pe_ratio, list):
            # 计算P/E比率
            price = self._safe_get(data, 'current_price')
            eps = self._safe_get(data, 'earnings_per_share')
            if eps is None or isinstance(eps, list):
                eps = self._safe_get(data, 'eps')
            
            if (price is not None and not isinstance(price, list) and 
                eps is not None and not isinstance(eps, list) and eps > 0):
                pe_ratio = price / eps
            else:
                return None
        
        # 获取增长率
        growth_rate = self._safe_get(data, 'earnings_growth_rate')
        if growth_rate is None or isinstance(growth_rate, list):
            growth_rate = self._safe_get(data, 'revenue_growth_rate')
        if growth_rate is None or isinstance(growth_rate, list):
            growth_rate = self._safe_get(data, 'net_income_growth_rate')
        
        if growth_rate is None or isinstance(growth_rate, list) or growth_rate <= 0:
            return None
        
        # 转换为百分比形式（如果是小数形式）
        if growth_rate < 1:
            growth_rate = growth_rate * 100
        
        return pe_ratio / growth_rate
    
    # 巴菲特所有者收益计算
    def _calculate_owner_earnings(self, data: Dict[str, Any]) -> Optional[float]:
        net_income = self._safe_get(data, 'net_income')
        depreciation = self._safe_get(data, 'depreciation')
        maintenance_capex = self._safe_get(data, 'maintenance_capex')
        working_capital_change = self._safe_get(data, 'working_capital_change', 0)
        
        if net_income is None:
            return None
        
        if depreciation is None:
            depreciation = 0
        
        if maintenance_capex is None:
            # 估算维护性资本支出为折旧的80%
            maintenance_capex = depreciation * 0.8 if depreciation > 0 else net_income * 0.05
        
        return net_income + depreciation - maintenance_capex - working_capital_change
    
    # 投入资本计算 - 增强版
    def _calculate_invested_capital(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_invested_capital_enhanced(data)
    
    def _calculate_invested_capital_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版投入资本计算"""
        
        # 方法1: 直接计算 (最准确)
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        total_debt = self._safe_get(data, 'total_debt', 0)
        cash = self._safe_get(data, 'cash_and_cash_equivalents', 0)
        
        if shareholders_equity is not None:
            return shareholders_equity + total_debt - cash
        
        # 方法2: 从资产负债表计算
        total_assets = self._safe_get(data, 'total_assets')
        current_liabilities = self._safe_get(data, 'current_liabilities')
        non_interest_bearing_liabilities = self._safe_get(data, 'accounts_payable', 0)
        
        if total_assets is not None and current_liabilities is not None:
            # 投入资本 = 总资产 - 非付息负债 - 现金
            return total_assets - non_interest_bearing_liabilities - cash
        
        # 方法3: 从净营运资本估算
        working_capital = self._safe_get(data, 'working_capital')
        fixed_assets = self._safe_get(data, 'fixed_assets')
        
        if working_capital is not None and fixed_assets is not None:
            return working_capital + fixed_assets
        
        return None
    
    # 维护性资本支出估算
    def _estimate_maintenance_capex(self, data: Dict[str, Any]) -> Optional[float]:
        depreciation = self._safe_get(data, 'depreciation')
        revenue = self._safe_get(data, 'revenue')
        
        if depreciation is not None:
            # 方法1：基于折旧的80%
            return depreciation * 0.8
        elif revenue is not None:
            # 方法2：基于收入的2-3%
            return revenue * 0.025
        
        return None
    
    # 内在价值计算（简化DCF）
    def _calculate_intrinsic_value(self, data: Dict[str, Any]) -> Optional[float]:
        owner_earnings = self._safe_get(data, 'owner_earnings')
        shares_outstanding = self._safe_get(data, 'shares_outstanding')
        
        if owner_earnings is None or shares_outstanding is None:
            return None
        
        # 简化DCF：假设5%增长率，10%贴现率
        growth_rate = 0.05
        discount_rate = 0.10
        
        # 永续增长模型
        terminal_value = owner_earnings * (1 + growth_rate) / (discount_rate - growth_rate)
        
        return terminal_value / shares_outstanding
    
    # 格雷厄姆数字计算 - 增强版
    def _calculate_graham_number(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_graham_number_enhanced(data)
    
    def _calculate_graham_number_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版格雷厄姆数值计算"""
        
        eps = self._safe_get(data, 'earnings_per_share')
        book_value_per_share = self._safe_get(data, 'book_value_per_share')
        
        # 如果没有直接的每股收益，尝试计算
        if eps is None or isinstance(eps, list):
            net_income = self._safe_get(data, 'net_income')
            shares_outstanding = self._safe_get(data, 'shares_outstanding')
            if (net_income is not None and not isinstance(net_income, list) and 
                shares_outstanding is not None and not isinstance(shares_outstanding, list) and 
                shares_outstanding > 0):
                eps = net_income / shares_outstanding
            else:
                eps = None
        
        # 如果没有直接的每股账面价值，尝试计算
        if book_value_per_share is None or isinstance(book_value_per_share, list):
            shareholders_equity = self._safe_get(data, 'shareholders_equity')
            shares_outstanding = self._safe_get(data, 'shares_outstanding')
            if (shareholders_equity is not None and not isinstance(shareholders_equity, list) and 
                shares_outstanding is not None and not isinstance(shares_outstanding, list) and 
                shares_outstanding > 0):
                book_value_per_share = shareholders_equity / shares_outstanding
            else:
                book_value_per_share = None
        
        if (eps is None or isinstance(eps, list) or 
            book_value_per_share is None or isinstance(book_value_per_share, list)):
            return None
        
        if eps <= 0 or book_value_per_share <= 0:
            return None
        
        # 格雷厄姆数值 = √(22.5 × EPS × BVPS)
        import math
        return math.sqrt(22.5 * eps * book_value_per_share)
    
    # 净流动资产价值计算 - 增强版
    def _calculate_ncav(self, data: Dict[str, Any]) -> Optional[float]:
        return self._calculate_ncav_enhanced(data)
    
    def _calculate_ncav_enhanced(self, data: Dict[str, Any]) -> Optional[float]:
        """增强版净流动资产价值计算"""
        
        current_assets = self._safe_get(data, 'current_assets')
        total_liabilities = self._safe_get(data, 'total_liabilities')
        shares_outstanding = self._safe_get(data, 'shares_outstanding')
        
        # 如果没有流动资产，尝试从总资产估算
        if current_assets is None:
            total_assets = self._safe_get(data, 'total_assets')
            if total_assets is not None:
                # 估算流动资产为总资产的40%
                current_assets = total_assets * 0.4
        
        # 如果没有总负债，尝试从流动负债估算
        if total_liabilities is None:
            current_liabilities = self._safe_get(data, 'current_liabilities')
            if current_liabilities is not None:
                # 估算总负债为流动负债的1.5倍
                total_liabilities = current_liabilities * 1.5
        
        if current_assets is None or total_liabilities is None:
            return None
        
        # 如果有股数，返回每股NCAV；否则返回总NCAV
        ncav_total = current_assets - total_liabilities
        
        if shares_outstanding is not None and shares_outstanding > 0:
            return ncav_total / shares_outstanding
        else:
            return ncav_total
    
    # 债务占总资本比率计算
    def _calculate_debt_to_total_capital(self, data: Dict[str, Any]) -> Optional[float]:
        total_debt = self._safe_get(data, 'total_debt', 0)
        shareholders_equity = self._safe_get(data, 'shareholders_equity')
        
        if shareholders_equity is None:
            return None
        
        total_capital = total_debt + shareholders_equity
        return self._safe_divide(total_debt, total_capital)
    
    # 利息覆盖率计算
    def _calculate_interest_coverage(self, data: Dict[str, Any]) -> Optional[float]:
        operating_income = self._safe_get(data, 'operating_income')
        interest_expense = self._safe_get(data, 'interest_expense')
        
        return self._safe_divide(operating_income, interest_expense)
    
    # 经营现金流比率计算
    def _calculate_ocf_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        operating_cash_flow = self._safe_get(data, 'operating_cash_flow')
        current_liabilities = self._safe_get(data, 'current_liabilities')
        
        return self._safe_divide(operating_cash_flow, current_liabilities)
    
    # 现金比率
    def _calculate_cash_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        cash = self._safe_get(data, 'cash_and_cash_equivalents')
        current_liabilities = self._safe_get(data, 'current_liabilities')
        
        return self._safe_divide(cash, current_liabilities)
    
    # 贝塔系数计算
    def _calculate_beta_coefficient(self, data: Dict[str, Any]) -> Optional[float]:
        """计算贝塔系数"""
        
        # 尝试从数据中获取已计算的贝塔值
        beta = self._safe_get(data, 'beta')
        if beta is not None and not isinstance(beta, list):
            return beta
        
        # 如果有历史价格数据，计算贝塔系数
        stock_prices = self._safe_get(data, 'historical_prices')
        market_prices = self._safe_get(data, 'market_historical_prices')
        
        if (stock_prices is not None and isinstance(stock_prices, list) and 
            market_prices is not None and isinstance(market_prices, list)):
            return self._calculate_beta_from_prices(stock_prices, market_prices)
        
        # 如果没有历史数据，使用行业平均贝塔估算
        industry_beta = self._safe_get(data, 'industry_beta')
        if industry_beta is not None and not isinstance(industry_beta, list):
            return industry_beta
        
        # 默认贝塔值
        return 1.0
    
    def _calculate_beta_from_prices(self, stock_prices: list, market_prices: list) -> Optional[float]:
        """从价格数据计算贝塔系数"""
        
        if len(stock_prices) != len(market_prices) or len(stock_prices) < 20:
            return None
        
        # 计算收益率
        stock_returns = []
        market_returns = []
        
        for i in range(1, len(stock_prices)):
            if stock_prices[i-1] > 0 and market_prices[i-1] > 0:
                stock_return = (stock_prices[i] / stock_prices[i-1]) - 1
                market_return = (market_prices[i] / market_prices[i-1]) - 1
                stock_returns.append(stock_return)
                market_returns.append(market_return)
        
        if len(stock_returns) < 10:
            return None
        
        # 计算协方差和方差
        try:
            import statistics
            
            stock_mean = statistics.mean(stock_returns)
            market_mean = statistics.mean(market_returns)
            
            covariance = sum((s - stock_mean) * (m - market_mean) for s, m in zip(stock_returns, market_returns)) / (len(stock_returns) - 1)
            market_variance = statistics.variance(market_returns)
            
            if market_variance == 0:
                return None
            
            return covariance / market_variance
        except Exception:
            return None
    
    # 收入增长率计算 - 第二优先级
    def _calculate_revenue_growth_rate(self, data: Dict[str, Any]) -> Optional[float]:
        """计算收入增长率 (年化)"""
        
        # 方法1: 从历史收入数据计算
        current_revenue = self._safe_get(data, 'total_revenue')
        previous_revenue = self._safe_get(data, 'previous_year_revenue')
        
        if current_revenue is not None and previous_revenue is not None and previous_revenue > 0:
            return (current_revenue - previous_revenue) / previous_revenue
        
        # 方法2: 从季度数据估算年增长率
        quarterly_revenue = self._safe_get(data, 'quarterly_revenue')
        previous_quarter_revenue = self._safe_get(data, 'previous_quarter_revenue')
        
        if quarterly_revenue is not None and previous_quarter_revenue is not None and previous_quarter_revenue > 0:
            quarterly_growth = (quarterly_revenue - previous_quarter_revenue) / previous_quarter_revenue
            # 年化增长率 = (1 + 季度增长率)^4 - 1
            return (1 + quarterly_growth) ** 4 - 1
        
        # 方法3: 从多年平均增长率估算
        revenue_3_years_ago = self._safe_get(data, 'revenue_3_years_ago')
        if current_revenue is not None and revenue_3_years_ago is not None and revenue_3_years_ago > 0:
            # 3年复合年增长率
            return (current_revenue / revenue_3_years_ago) ** (1/3) - 1
        
        # 方法4: 行业平均估算 (最后选择)
        industry_avg_growth = self._safe_get(data, 'industry_avg_growth_rate')
        if industry_avg_growth is not None:
            return industry_avg_growth
        
        return None
    
    # 夏普比率计算
    def _calculate_sharpe_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        """计算夏普比率"""
        
        # 获取股票收益率
        stock_return = self._safe_get(data, 'annual_return')
        if stock_return is None:
            # 尝试从价格变化计算
            current_price = self._safe_get(data, 'current_price')
            previous_price = self._safe_get(data, 'previous_year_price')
            if current_price is not None and previous_price is not None and previous_price > 0:
                stock_return = (current_price / previous_price) - 1
        
        if stock_return is None:
            return None
        
        # 获取无风险利率（默认使用3%）
        risk_free_rate = self._safe_get(data, 'risk_free_rate', 0.03)
        
        # 获取收益率标准差
        return_volatility = self._safe_get(data, 'return_volatility')
        if return_volatility is None:
            # 如果没有波动率数据，使用行业平均估算
            return_volatility = self._safe_get(data, 'industry_volatility', 0.2)  # 默认20%
        
        if return_volatility <= 0:
            return None
        
        # 夏普比率 = (股票收益率 - 无风险利率) / 收益率标准差
        return (stock_return - risk_free_rate) / return_volatility

    def calculate_financial_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算财务比率"""
        ratios = {}
        
        # 获取基础数据
        revenue = data.get('revenue') or data.get('total_revenue') or data.get('sales')
        net_income = data.get('net_income') or data.get('net_earnings')
        total_assets = data.get('total_assets') or data.get('total_asset')
        shareholders_equity = data.get('shareholders_equity') or data.get('stockholders_equity')
        current_assets = data.get('current_assets') or data.get('current_asset')
        current_liabilities = data.get('current_liabilities') or data.get('current_liability')
        operating_income = data.get('operating_income') or data.get('operating_profit')
        total_debt = data.get('total_debt') or data.get('debt')
        
        # 1. 盈利能力比率
        if revenue and revenue != 0:
            if net_income is not None:
                ratios['net_margin'] = net_income / revenue
            if operating_income is not None:
                ratios['operating_margin'] = operating_income / revenue
        
        # 如果没有operating_income，尝试从其他数据计算
        if 'operating_margin' not in ratios and revenue and net_income:
            # 估算运营利润率为净利润率的1.2-1.5倍（粗略估算）
            estimated_operating_margin = (net_income / revenue) * 1.3
            ratios['operating_margin'] = estimated_operating_margin
        
        if shareholders_equity and shareholders_equity != 0:
            if net_income is not None:
                ratios['return_on_equity'] = net_income / shareholders_equity
                ratios['roe'] = net_income / shareholders_equity
        
        if total_assets and total_assets != 0:
            if net_income is not None:
                ratios['return_on_assets'] = net_income / total_assets
                ratios['roa'] = net_income / total_assets
            if revenue is not None:
                ratios['asset_turnover'] = revenue / total_assets
        
        # 2. 流动性比率
        if current_liabilities and current_liabilities != 0:
            if current_assets is not None:
                ratios['current_ratio'] = current_assets / current_liabilities
        
        # 如果没有流动资产/负债数据，尝试估算
        if 'current_ratio' not in ratios:
            if total_assets and total_debt is not None:
                # 假设流动资产约占总资产的30-40%，流动负债约占总负债的60-70%
                estimated_current_assets = total_assets * 0.35
                estimated_current_liabilities = total_debt * 0.65 if total_debt > 0 else total_assets * 0.2
                if estimated_current_liabilities > 0:
                    ratios['current_ratio'] = estimated_current_assets / estimated_current_liabilities
        
        # 3. 杠杆比率
        if shareholders_equity and shareholders_equity != 0:
            if total_debt is not None:
                ratios['debt_to_equity'] = total_debt / shareholders_equity
        
        # 如果没有债务数据，设为0（假设低杠杆）
        if 'debt_to_equity' not in ratios:
            ratios['debt_to_equity'] = 0.0
        
        # 4. 估算自由现金流（如果没有的话）
        if 'free_cash_flow' not in data and net_income is not None:
            # 简单估算：净利润的80-90%作为自由现金流
            ratios['free_cash_flow'] = net_income * 0.85
        
        return ratios

    def _ensure_key_fields(self, data: Dict[str, Any]) -> None:
        """确保关键字段存在，为缺失的字段提供估算值"""
        
        # 获取基础数据
        revenue = self._safe_get_numeric(data, 'revenue')
        net_income = self._safe_get_numeric(data, 'net_income')
        total_assets = self._safe_get_numeric(data, 'total_assets')
        equity = self._safe_get_numeric(data, 'shareholders_equity')
        market_cap = self._safe_get_numeric(data, 'market_cap')
        
        # 确保基础比率存在
        if not data.get('roe') and net_income and equity and equity > 0:
            data['roe'] = net_income / equity
            data['return_on_equity'] = data['roe']
        
        if not data.get('roa') and net_income and total_assets and total_assets > 0:
            data['roa'] = net_income / total_assets
            data['return_on_assets'] = data['roa']
        
        # 确保利润率存在
        if revenue and revenue > 0:
            if not data.get('net_margin') and net_income is not None:
                data['net_margin'] = net_income / revenue
                data['net_profit_margin'] = data['net_margin']
            
            # 如果没有运营利润率，基于净利润率估算
            if not data.get('operating_margin') and net_income is not None:
                if net_income > 0:
                    # 运营利润通常比净利润高20-40%
                    estimated_operating_margin = (net_income * 1.3) / revenue
                    data['operating_margin'] = min(estimated_operating_margin, 0.5)  # 最高50%
            
            # 如果没有毛利率，基于净利润率估算
            if not data.get('gross_margin') and net_income is not None:
                if net_income > 0:
                    # 毛利率通常是净利润率的2-4倍
                    estimated_gross_margin = (net_income * 3) / revenue
                    data['gross_margin'] = min(estimated_gross_margin, 0.7)  # 最高70%
        
        # 确保估值指标存在
        if market_cap and market_cap > 0:
            if not data.get('pe_ratio') and net_income and net_income > 0:
                data['pe_ratio'] = market_cap / net_income
                data['price_to_earnings'] = data['pe_ratio']
            
            if not data.get('price_to_book') and equity and equity > 0:
                data['price_to_book'] = market_cap / equity
        
        # 确保现金流指标存在
        if not data.get('free_cash_flow') and net_income and net_income > 0:
            # FCF通常是净利润的70-90%
            data['free_cash_flow'] = net_income * 0.8
        
        # 确保债务指标存在
        total_debt = self._safe_get_numeric(data, 'total_debt')
        if total_debt is not None and equity and equity > 0:
            if not data.get('debt_to_equity'):
                data['debt_to_equity'] = total_debt / equity
        
        # 确保流动性指标存在
        current_assets = self._safe_get_numeric(data, 'current_assets')
        current_liabilities = self._safe_get_numeric(data, 'current_liabilities')
        if current_assets and current_liabilities and current_liabilities > 0:
            if not data.get('current_ratio'):
                data['current_ratio'] = current_assets / current_liabilities
        elif not data.get('current_ratio'):
            # 如果没有流动性数据，给予行业平均值
            data['current_ratio'] = 1.2
        
        # 确保资产周转率存在
        if not data.get('asset_turnover') and revenue and total_assets and total_assets > 0:
            data['asset_turnover'] = revenue / total_assets
        
        # 为大型公司提供护城河基础分
        if market_cap and market_cap > 1e10:  # 100亿以上
            if not data.get('moat_score'):
                data['moat_score'] = 2.0  # 大公司基础护城河分
        elif market_cap and market_cap > 1e9:  # 10亿以上
            if not data.get('moat_score'):
                data['moat_score'] = 1.0
    def _calculate_derived_metrics(self, data: Dict[str, Any]) -> None:
        """计算衍生的财务指标"""
        
        # 获取关键数据
        revenue = self._safe_get_numeric(data, 'revenue')
        net_income = self._safe_get_numeric(data, 'net_income')
        total_assets = self._safe_get_numeric(data, 'total_assets')
        equity = self._safe_get_numeric(data, 'shareholders_equity')
        market_cap = self._safe_get_numeric(data, 'market_cap')
        
        # 计算利润率
        if revenue and revenue > 0:
            if net_income is not None:
                data['net_profit_margin'] = net_income / revenue * 100
            
            # 毛利润率
            gross_profit = self._safe_get_numeric(data, 'gross_profit')
            if gross_profit is not None:
                data['gross_profit_margin'] = gross_profit / revenue * 100
        
        # 计算ROE
        if net_income is not None and equity and equity > 0:
            data['roe'] = net_income / equity * 100
        
        # 计算ROA
        if net_income is not None and total_assets and total_assets > 0:
            data['roa'] = net_income / total_assets * 100
        
        # 计算P/E比率
        shares = self._safe_get_numeric(data, 'shares_outstanding')
        if market_cap and shares and shares > 0 and net_income and net_income > 0:
            eps = net_income / shares
            data['earnings_per_share'] = eps
            current_price = market_cap / shares
            data['price_to_earnings'] = current_price / eps
        
        # 计算P/B比率
        if market_cap and equity and equity > 0:
            data['price_to_book'] = market_cap / equity
        
        # 计算流动比率
        current_assets = self._safe_get_numeric(data, 'current_assets')
        current_liabilities = self._safe_get_numeric(data, 'current_liabilities')
        if current_assets and current_liabilities and current_liabilities > 0:
            data['current_ratio'] = current_assets / current_liabilities
        
        # 计算债务权益比
        total_debt = self._safe_get_numeric(data, 'total_debt')
        if total_debt is not None and equity and equity > 0:
            data['debt_to_equity'] = total_debt / equity
    
    def _safe_get_numeric(self, data: Dict[str, Any], key: str) -> Optional[float]:
        """安全地获取数值数据"""
        value = data.get(key)
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _standardize_field_names(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化字段名，确保分析师能找到所需数据"""
        
        # 字段名映射
        field_mapping = {
            # 收入相关
            'total_revenue': 'revenue',
            'sales': 'revenue',
            'turnover': 'revenue',
            
            # 利润相关
            'profit': 'net_income',
            'earnings': 'net_income',
            'net_profit': 'net_income',
            
            # 资产相关
            'assets': 'total_assets',
            
            # 权益相关
            'equity': 'shareholders_equity',
            'stockholders_equity': 'shareholders_equity',
            
            # 债务相关
            'debt': 'total_debt',
            'long_term_debt': 'total_debt',
            
            # 股数相关
            'outstanding_shares': 'shares_outstanding',
            'common_shares_outstanding': 'shares_outstanding',
            
            # 现金流相关
            'cash_from_operations': 'operating_cash_flow',
            'fcf': 'free_cash_flow',
        }
        
        standardized_data = {}
        
        # 应用映射
        for key, value in data.items():
            standard_key = field_mapping.get(key, key)
            
            # 如果标准化键已存在且不为空，保留现有值
            if standard_key in standardized_data and standardized_data[standard_key] is not None:
                continue
                
            standardized_data[standard_key] = value
        
        return standardized_data


# 创建全局实例
data_enhancer = DataEnhancer()