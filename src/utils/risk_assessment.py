#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风险评估模块，提供多维度风险分析功能"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)

class RiskAssessment:
    """风险评估类，提供多维度风险分析"""
    
    def __init__(self):
        self.risk_weights = {
            "market_risk": 0.3,      # 市场风险权重
            "stock_risk": 0.4,       # 个股风险权重
            "industry_risk": 0.2,    # 行业风险权重
            "financial_risk": 0.1    # 财务风险权重
        }
    
    def assess_comprehensive_risk(self, stock_data: Dict[str, Any], market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """综合风险评估
        
        Args:
            stock_data: 股票数据
            market_data: 市场数据
            
        Returns:
            综合风险评估结果
        """
        try:
            risk_assessment = {
                "overall_risk_score": 0,
                "risk_level": "中等",
                "market_risk": self.assess_market_risk(market_data),
                "stock_risk": self.assess_stock_risk(stock_data),
                "industry_risk": self.assess_industry_risk(stock_data),
                "financial_risk": self.assess_financial_risk(stock_data),
                "risk_factors": [],
                "risk_mitigation": [],
                "confidence_level": 0
            }
            
            # 计算综合风险得分
            total_score = 0
            valid_components = 0
            
            for risk_type, weight in self.risk_weights.items():
                risk_data = risk_assessment.get(risk_type, {})
                if risk_data and isinstance(risk_data, dict):
                    score = risk_data.get("risk_score", 50)
                    total_score += score * weight
                    valid_components += weight
            
            if valid_components > 0:
                risk_assessment["overall_risk_score"] = round(total_score / valid_components, 1)
            else:
                risk_assessment["overall_risk_score"] = 50  # 默认中等风险
            
            # 确定风险等级
            risk_assessment["risk_level"] = self.determine_risk_level(risk_assessment["overall_risk_score"])
            
            # 收集风险因素
            risk_assessment["risk_factors"] = self.collect_risk_factors(risk_assessment)
            
            # 生成风险缓解建议
            risk_assessment["risk_mitigation"] = self.generate_risk_mitigation(risk_assessment)
            
            # 计算置信度
            risk_assessment["confidence_level"] = self.calculate_confidence_level(risk_assessment)
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"综合风险评估失败: {e}")
            return self.get_default_risk_assessment()
    
    def assess_market_risk(self, market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """评估市场风险"""
        try:
            market_risk = {
                "risk_score": 50,
                "volatility_risk": 50,
                "liquidity_risk": 50,
                "sentiment_risk": 50,
                "macro_risk": 50,
                "risk_description": "市场风险中等"
            }
            
            if not market_data:
                return market_risk
            
            risk_factors = []
            
            # 市场波动率风险
            market_volatility = market_data.get("market_volatility", 0.02)
            if market_volatility > 0.04:  # 高波动
                market_risk["volatility_risk"] = 75
                risk_factors.append("市场波动率较高")
            elif market_volatility > 0.03:
                market_risk["volatility_risk"] = 60
                risk_factors.append("市场波动率偏高")
            elif market_volatility < 0.015:
                market_risk["volatility_risk"] = 30
            else:
                market_risk["volatility_risk"] = 45
            
            # 流动性风险
            total_turnover = market_data.get("total_turnover", 0)
            if total_turnover > 0:
                if total_turnover < 500000000000:  # 5000亿以下
                    market_risk["liquidity_risk"] = 65
                    risk_factors.append("市场流动性不足")
                elif total_turnover > 1000000000000:  # 1万亿以上
                    market_risk["liquidity_risk"] = 35
                else:
                    market_risk["liquidity_risk"] = 45
            
            # 市场情绪风险
            limit_up_count = market_data.get("limit_up_count", 0)
            limit_down_count = market_data.get("limit_down_count", 0)
            
            if limit_down_count > limit_up_count * 2:
                market_risk["sentiment_risk"] = 70
                risk_factors.append("市场情绪悲观")
            elif limit_up_count > limit_down_count * 2:
                market_risk["sentiment_risk"] = 35
            else:
                market_risk["sentiment_risk"] = 50
            
            # 宏观经济风险（简化处理）
            market_risk["macro_risk"] = 50  # 默认中等
            
            # 计算综合市场风险得分
            market_risk["risk_score"] = round((
                market_risk["volatility_risk"] * 0.3 +
                market_risk["liquidity_risk"] * 0.3 +
                market_risk["sentiment_risk"] * 0.3 +
                market_risk["macro_risk"] * 0.1
            ), 1)
            
            # 生成风险描述
            if market_risk["risk_score"] >= 70:
                market_risk["risk_description"] = "市场风险较高：" + "、".join(risk_factors)
            elif market_risk["risk_score"] >= 55:
                market_risk["risk_description"] = "市场风险偏高：" + "、".join(risk_factors)
            elif market_risk["risk_score"] <= 35:
                market_risk["risk_description"] = "市场风险较低，市场环境相对稳定"
            else:
                market_risk["risk_description"] = "市场风险中等"
            
            return market_risk
            
        except Exception as e:
            logger.error(f"市场风险评估失败: {e}")
            return {"risk_score": 50, "risk_description": "市场风险评估失败"}
    
    def assess_stock_risk(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估个股风险"""
        try:
            stock_risk = {
                "risk_score": 50,
                "price_volatility": 50,
                "volume_risk": 50,
                "technical_risk": 50,
                "momentum_risk": 50,
                "risk_description": "个股风险中等"
            }
            
            risk_factors = []
            
            # 获取风险指标数据
            risk_indicators = stock_data.get("risk_indicators", {})
            price_data = stock_data.get("price_data")
            
            # 价格波动率风险
            volatility = risk_indicators.get("volatility", 0.02)
            if volatility > 0.06:  # 年化波动率超过6%
                stock_risk["price_volatility"] = 80
                risk_factors.append("价格波动率过高")
            elif volatility > 0.04:
                stock_risk["price_volatility"] = 65
                risk_factors.append("价格波动率偏高")
            elif volatility < 0.02:
                stock_risk["price_volatility"] = 30
            else:
                stock_risk["price_volatility"] = 45
            
            # 最大回撤风险
            max_drawdown = risk_indicators.get("max_drawdown", 0.1)
            if max_drawdown > 0.3:  # 最大回撤超过30%
                stock_risk["momentum_risk"] = 85
                risk_factors.append("历史最大回撤过大")
            elif max_drawdown > 0.2:
                stock_risk["momentum_risk"] = 65
                risk_factors.append("历史回撤较大")
            elif max_drawdown < 0.1:
                stock_risk["momentum_risk"] = 35
            else:
                stock_risk["momentum_risk"] = 50
            
            # VaR风险
            var_95 = risk_indicators.get("var_95", 0.03)
            if var_95 > 0.05:  # VaR超过5%
                risk_factors.append("单日最大损失风险较高")
            
            # 成交量风险（基于价格数据分析）
            if price_data is not None and not price_data.empty:
                try:
                    # 计算成交量变异系数
                    volume_cv = price_data['成交量'].std() / price_data['成交量'].mean()
                    if volume_cv > 1.5:
                        stock_risk["volume_risk"] = 70
                        risk_factors.append("成交量波动过大")
                    elif volume_cv > 1.0:
                        stock_risk["volume_risk"] = 55
                    else:
                        stock_risk["volume_risk"] = 40
                except Exception:
                    stock_risk["volume_risk"] = 50
            
            # 技术面风险（基于价格趋势）
            if price_data is not None and not price_data.empty and len(price_data) >= 20:
                try:
                    # 计算20日移动平均线趋势
                    ma20 = price_data['收盘'].rolling(20).mean()
                    current_price = price_data['收盘'].iloc[-1]
                    ma20_current = ma20.iloc[-1]
                    
                    if current_price < ma20_current * 0.9:  # 价格远低于MA20
                        stock_risk["technical_risk"] = 75
                        risk_factors.append("技术面走势疲弱")
                    elif current_price < ma20_current * 0.95:
                        stock_risk["technical_risk"] = 60
                    elif current_price > ma20_current * 1.1:  # 价格远高于MA20
                        stock_risk["technical_risk"] = 65
                        risk_factors.append("技术面存在回调风险")
                    else:
                        stock_risk["technical_risk"] = 45
                except Exception:
                    stock_risk["technical_risk"] = 50
            
            # 计算综合个股风险得分
            stock_risk["risk_score"] = round((
                stock_risk["price_volatility"] * 0.3 +
                stock_risk["volume_risk"] * 0.2 +
                stock_risk["technical_risk"] * 0.3 +
                stock_risk["momentum_risk"] * 0.2
            ), 1)
            
            # 生成风险描述
            if stock_risk["risk_score"] >= 70:
                stock_risk["risk_description"] = "个股风险较高：" + "、".join(risk_factors)
            elif stock_risk["risk_score"] >= 55:
                stock_risk["risk_description"] = "个股风险偏高：" + "、".join(risk_factors)
            elif stock_risk["risk_score"] <= 35:
                stock_risk["risk_description"] = "个股风险较低，价格走势相对稳定"
            else:
                stock_risk["risk_description"] = "个股风险中等"
            
            return stock_risk
            
        except Exception as e:
            logger.error(f"个股风险评估失败: {e}")
            return {"risk_score": 50, "risk_description": "个股风险评估失败"}
    
    def assess_industry_risk(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估行业风险"""
        try:
            industry_risk = {
                "risk_score": 50,
                "industry_concentration": 50,
                "policy_risk": 50,
                "competition_risk": 50,
                "cycle_risk": 50,
                "risk_description": "行业风险中等"
            }
            
            # 获取行业信息
            industry_data = stock_data.get("industry_data", {})
            industry_name = industry_data.get("industry", "")
            
            risk_factors = []
            
            # 基于行业特征评估风险
            if industry_name:
                # 高风险行业
                high_risk_industries = [
                    "房地产", "钢铁", "煤炭", "有色金属", "化工", "建筑", "水泥",
                    "玻璃", "造纸", "纺织", "服装", "家具", "汽车零部件"
                ]
                
                # 中高风险行业
                medium_high_risk_industries = [
                    "银行", "保险", "证券", "汽车", "机械", "电力", "石油",
                    "航空", "航运", "旅游", "餐饮", "零售"
                ]
                
                # 低风险行业
                low_risk_industries = [
                    "医药", "食品饮料", "公用事业", "电信", "软件", "互联网",
                    "教育", "医疗服务", "消费电子"
                ]
                
                if any(industry in industry_name for industry in high_risk_industries):
                    industry_risk["cycle_risk"] = 75
                    industry_risk["policy_risk"] = 65
                    risk_factors.append("属于周期性强的行业")
                    risk_factors.append("政策敏感度较高")
                elif any(industry in industry_name for industry in medium_high_risk_industries):
                    industry_risk["cycle_risk"] = 60
                    industry_risk["policy_risk"] = 55
                elif any(industry in industry_name for industry in low_risk_industries):
                    industry_risk["cycle_risk"] = 35
                    industry_risk["policy_risk"] = 40
                else:
                    industry_risk["cycle_risk"] = 50
                    industry_risk["policy_risk"] = 50
            
            # 竞争风险评估（简化）
            industry_risk["competition_risk"] = 50  # 默认中等竞争风险
            
            # 行业集中度风险（简化）
            industry_risk["industry_concentration"] = 50  # 默认中等集中度
            
            # 计算综合行业风险得分
            industry_risk["risk_score"] = round((
                industry_risk["industry_concentration"] * 0.2 +
                industry_risk["policy_risk"] * 0.3 +
                industry_risk["competition_risk"] * 0.2 +
                industry_risk["cycle_risk"] * 0.3
            ), 1)
            
            # 生成风险描述
            if industry_risk["risk_score"] >= 70:
                industry_risk["risk_description"] = f"行业风险较高（{industry_name}）：" + "、".join(risk_factors)
            elif industry_risk["risk_score"] >= 55:
                industry_risk["risk_description"] = f"行业风险偏高（{industry_name}）：" + "、".join(risk_factors)
            elif industry_risk["risk_score"] <= 35:
                industry_risk["risk_description"] = f"行业风险较低（{industry_name}），行业发展相对稳定"
            else:
                industry_risk["risk_description"] = f"行业风险中等（{industry_name}）"
            
            return industry_risk
            
        except Exception as e:
            logger.error(f"行业风险评估失败: {e}")
            return {"risk_score": 50, "risk_description": "行业风险评估失败"}
    
    def assess_financial_risk(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估财务风险"""
        try:
            financial_risk = {
                "risk_score": 50,
                "debt_risk": 50,
                "liquidity_risk": 50,
                "profitability_risk": 50,
                "growth_risk": 50,
                "risk_description": "财务风险中等"
            }
            
            # 获取财务数据
            financial_data = stock_data.get("financial_data", {})
            risk_indicators = stock_data.get("risk_indicators", {})
            
            risk_factors = []
            
            # 债务风险
            debt_ratio = risk_indicators.get("debt_ratio")
            if debt_ratio is not None:
                try:
                    debt_ratio = float(debt_ratio)
                    if debt_ratio > 70:  # 资产负债率超过70%
                        financial_risk["debt_risk"] = 80
                        risk_factors.append("资产负债率过高")
                    elif debt_ratio > 50:
                        financial_risk["debt_risk"] = 60
                        risk_factors.append("资产负债率偏高")
                    elif debt_ratio < 20:
                        financial_risk["debt_risk"] = 30
                    else:
                        financial_risk["debt_risk"] = 45
                except (ValueError, TypeError):
                    financial_risk["debt_risk"] = 50
            
            # 流动性风险
            current_ratio = risk_indicators.get("current_ratio")
            if current_ratio is not None:
                try:
                    current_ratio = float(current_ratio)
                    if current_ratio < 1.0:  # 流动比率小于1
                        financial_risk["liquidity_risk"] = 75
                        risk_factors.append("流动比率过低")
                    elif current_ratio < 1.5:
                        financial_risk["liquidity_risk"] = 60
                        risk_factors.append("流动比率偏低")
                    elif current_ratio > 3.0:
                        financial_risk["liquidity_risk"] = 45  # 过高也可能表示资金利用效率低
                    else:
                        financial_risk["liquidity_risk"] = 35
                except (ValueError, TypeError):
                    financial_risk["liquidity_risk"] = 50
            
            # 盈利能力风险（简化评估）
            financial_indicators = financial_data.get("financial_indicators")
            if financial_indicators is not None and not financial_indicators.empty:
                try:
                    latest_data = financial_indicators.iloc[0]
                    
                    # ROE评估
                    if 'ROE' in latest_data:
                        roe = float(latest_data['ROE'])
                        if roe < 5:  # ROE低于5%
                            financial_risk["profitability_risk"] = 70
                            risk_factors.append("ROE过低")
                        elif roe < 10:
                            financial_risk["profitability_risk"] = 55
                        elif roe > 25:
                            financial_risk["profitability_risk"] = 45  # 过高可能不可持续
                        else:
                            financial_risk["profitability_risk"] = 35
                    
                    # 营收增长率评估
                    if '营业收入增长率' in latest_data:
                        growth_rate = float(latest_data['营业收入增长率'])
                        if growth_rate < -10:  # 营收负增长超过10%
                            financial_risk["growth_risk"] = 75
                            risk_factors.append("营收大幅下滑")
                        elif growth_rate < 0:
                            financial_risk["growth_risk"] = 60
                            risk_factors.append("营收负增长")
                        elif growth_rate > 50:
                            financial_risk["growth_risk"] = 50  # 过高增长可能不可持续
                        else:
                            financial_risk["growth_risk"] = 35
                            
                except (ValueError, TypeError, KeyError):
                    pass
            
            # 计算综合财务风险得分
            financial_risk["risk_score"] = round((
                financial_risk["debt_risk"] * 0.3 +
                financial_risk["liquidity_risk"] * 0.3 +
                financial_risk["profitability_risk"] * 0.25 +
                financial_risk["growth_risk"] * 0.15
            ), 1)
            
            # 生成风险描述
            if financial_risk["risk_score"] >= 70:
                financial_risk["risk_description"] = "财务风险较高：" + "、".join(risk_factors)
            elif financial_risk["risk_score"] >= 55:
                financial_risk["risk_description"] = "财务风险偏高：" + "、".join(risk_factors)
            elif financial_risk["risk_score"] <= 35:
                financial_risk["risk_description"] = "财务风险较低，财务状况良好"
            else:
                financial_risk["risk_description"] = "财务风险中等"
            
            return financial_risk
            
        except Exception as e:
            logger.error(f"财务风险评估失败: {e}")
            return {"risk_score": 50, "risk_description": "财务风险评估失败"}
    
    def determine_risk_level(self, risk_score: float) -> str:
        """根据风险得分确定风险等级"""
        if risk_score >= 80:
            return "极高"
        elif risk_score >= 70:
            return "高"
        elif risk_score >= 55:
            return "偏高"
        elif risk_score >= 45:
            return "中等"
        elif risk_score >= 30:
            return "偏低"
        else:
            return "低"
    
    def collect_risk_factors(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """收集主要风险因素"""
        risk_factors = []
        
        # 从各个风险维度收集风险因素
        for risk_type in ["market_risk", "stock_risk", "industry_risk", "financial_risk"]:
            risk_data = risk_assessment.get(risk_type, {})
            if isinstance(risk_data, dict) and risk_data.get("risk_score", 50) >= 60:
                description = risk_data.get("risk_description", "")
                if description and "：" in description:
                    factors = description.split("：")[1]
                    if factors:
                        risk_factors.extend(factors.split("、"))
        
        # 去重并限制数量
        unique_factors = list(dict.fromkeys(risk_factors))  # 保持顺序的去重
        return unique_factors[:5]  # 最多返回5个主要风险因素
    
    def generate_risk_mitigation(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """生成风险缓解建议"""
        mitigation_strategies = []
        overall_score = risk_assessment.get("overall_risk_score", 50)
        
        # 基于整体风险水平的建议
        if overall_score >= 70:
            mitigation_strategies.append("建议降低仓位或暂时观望")
            mitigation_strategies.append("设置严格的止损位")
        elif overall_score >= 55:
            mitigation_strategies.append("建议适当控制仓位")
            mitigation_strategies.append("密切关注风险指标变化")
        
        # 基于具体风险类型的建议
        market_risk = risk_assessment.get("market_risk", {})
        if market_risk.get("risk_score", 50) >= 60:
            mitigation_strategies.append("关注市场整体走势，考虑分散投资")
        
        stock_risk = risk_assessment.get("stock_risk", {})
        if stock_risk.get("risk_score", 50) >= 60:
            mitigation_strategies.append("加强个股技术分析，设置动态止损")
        
        industry_risk = risk_assessment.get("industry_risk", {})
        if industry_risk.get("risk_score", 50) >= 60:
            mitigation_strategies.append("关注行业政策变化，考虑行业轮动")
        
        financial_risk = risk_assessment.get("financial_risk", {})
        if financial_risk.get("risk_score", 50) >= 60:
            mitigation_strategies.append("重点关注财务报表，避免财务风险较高的个股")
        
        # 通用建议
        if overall_score <= 40:
            mitigation_strategies.append("风险相对较低，可适当增加仓位")
        
        mitigation_strategies.append("建议定期重新评估风险状况")
        
        return mitigation_strategies[:6]  # 最多返回6条建议
    
    def calculate_confidence_level(self, risk_assessment: Dict[str, Any]) -> float:
        """计算风险评估的置信度"""
        try:
            # 基于数据完整性计算置信度
            data_completeness = 0
            total_components = 4  # 四个风险维度
            
            for risk_type in ["market_risk", "stock_risk", "industry_risk", "financial_risk"]:
                risk_data = risk_assessment.get(risk_type, {})
                if isinstance(risk_data, dict) and "risk_score" in risk_data:
                    data_completeness += 1
            
            base_confidence = (data_completeness / total_components) * 100
            
            # 根据风险评估的一致性调整置信度
            risk_scores = []
            for risk_type in ["market_risk", "stock_risk", "industry_risk", "financial_risk"]:
                risk_data = risk_assessment.get(risk_type, {})
                if isinstance(risk_data, dict) and "risk_score" in risk_data:
                    risk_scores.append(risk_data["risk_score"])
            
            if len(risk_scores) >= 2:
                # 计算风险得分的标准差，标准差越小，一致性越高
                std_dev = np.std(risk_scores)
                consistency_factor = max(0.7, 1 - (std_dev / 50))  # 标准差调整因子
                base_confidence *= consistency_factor
            
            return round(min(95, max(30, base_confidence)), 1)  # 置信度范围30-95%
            
        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return 60.0  # 默认置信度
    
    def get_default_risk_assessment(self) -> Dict[str, Any]:
        """获取默认风险评估结果"""
        return {
            "overall_risk_score": 50,
            "risk_level": "中等",
            "market_risk": {"risk_score": 50, "risk_description": "市场风险数据不足"},
            "stock_risk": {"risk_score": 50, "risk_description": "个股风险数据不足"},
            "industry_risk": {"risk_score": 50, "risk_description": "行业风险数据不足"},
            "financial_risk": {"risk_score": 50, "risk_description": "财务风险数据不足"},
            "risk_factors": ["数据不足，无法准确评估风险"],
            "risk_mitigation": ["建议谨慎投资", "等待更多数据后再做决策"],
            "confidence_level": 30.0
        }

# 创建全局实例
risk_assessor = RiskAssessment()

def assess_stock_risk(stock_data: Dict[str, Any], market_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """评估股票风险的便捷函数"""
    return risk_assessor.assess_comprehensive_risk(stock_data, market_data)