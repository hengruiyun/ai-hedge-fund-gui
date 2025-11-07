"""技术指标计算模块

提供完整的技术分析指标计算功能，包括趋势、动量、波动率和成交量指标.
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_all_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算所有技术指标
        
        Args:
            prices_df: 包含OHLCV数据的DataFrame
            
        Returns:
            包含所有技术指标的字典
        """
        indicators = {}
        
        # 趋势指标
        indicators.update(TechnicalIndicators.calculate_trend_indicators(prices_df))
        
        # 动量指标
        indicators.update(TechnicalIndicators.calculate_momentum_indicators(prices_df))
        
        # 波动率指标
        indicators.update(TechnicalIndicators.calculate_volatility_indicators(prices_df))
        
        # 成交量指标
        indicators.update(TechnicalIndicators.calculate_volume_indicators(prices_df))
        
        # 支撑阻力指标
        indicators.update(TechnicalIndicators.calculate_support_resistance_indicators(prices_df))
        
        return indicators
    
    @staticmethod
    def calculate_trend_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算趋势指标"""
        indicators = {}
        
        # 移动平均线
        indicators['sma_5'] = prices_df['close'].rolling(5).mean().iloc[-1]
        indicators['sma_10'] = prices_df['close'].rolling(10).mean().iloc[-1]
        indicators['sma_20'] = prices_df['close'].rolling(20).mean().iloc[-1]
        indicators['sma_50'] = prices_df['close'].rolling(50).mean().iloc[-1]
        indicators['sma_200'] = prices_df['close'].rolling(200).mean().iloc[-1]
        
        # 指数移动平均线
        indicators['ema_12'] = prices_df['close'].ewm(span=12).mean().iloc[-1]
        indicators['ema_26'] = prices_df['close'].ewm(span=26).mean().iloc[-1]
        indicators['ema_50'] = prices_df['close'].ewm(span=50).mean().iloc[-1]
        
        # MACD
        macd_data = TechnicalIndicators._calculate_macd(prices_df)
        indicators.update(macd_data)
        
        # ADX (平均趋向指数)
        adx_data = TechnicalIndicators._calculate_adx(prices_df)
        indicators.update(adx_data)
        
        # 抛物线SAR
        sar_data = TechnicalIndicators._calculate_sar(prices_df)
        indicators['parabolic_sar'] = sar_data
        
        # 一目均衡表
        ichimoku_data = TechnicalIndicators._calculate_ichimoku(prices_df)
        indicators.update(ichimoku_data)
        
        return indicators
    
    @staticmethod
    def calculate_momentum_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算动量指标"""
        indicators = {}
        
        # RSI
        indicators['rsi_14'] = TechnicalIndicators._calculate_rsi(prices_df, 14).iloc[-1]
        indicators['rsi_21'] = TechnicalIndicators._calculate_rsi(prices_df, 21).iloc[-1]
        
        # 随机指标
        stoch_data = TechnicalIndicators._calculate_stochastic(prices_df)
        indicators.update(stoch_data)
        
        # 威廉指标
        indicators['williams_r'] = TechnicalIndicators._calculate_williams_r(prices_df).iloc[-1]
        
        # CCI (商品通道指数)
        indicators['cci'] = TechnicalIndicators._calculate_cci(prices_df).iloc[-1]
        
        # ROC (变动率)
        indicators['roc_10'] = TechnicalIndicators._calculate_roc(prices_df, 10).iloc[-1]
        indicators['roc_20'] = TechnicalIndicators._calculate_roc(prices_df, 20).iloc[-1]
        
        # 动量指标
        indicators['momentum_10'] = TechnicalIndicators._calculate_momentum(prices_df, 10).iloc[-1]
        
        return indicators
    
    @staticmethod
    def calculate_volatility_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算波动率指标"""
        indicators = {}
        
        # 布林带
        bb_data = TechnicalIndicators._calculate_bollinger_bands(prices_df)
        indicators.update(bb_data)
        
        # ATR (真实波动幅度)
        indicators['atr_14'] = TechnicalIndicators._calculate_atr(prices_df, 14).iloc[-1]
        indicators['atr_21'] = TechnicalIndicators._calculate_atr(prices_df, 21).iloc[-1]
        
        # 历史波动率
        indicators['historical_volatility_20'] = TechnicalIndicators._calculate_historical_volatility(prices_df, 20)
        indicators['historical_volatility_60'] = TechnicalIndicators._calculate_historical_volatility(prices_df, 60)
        
        # 肯特纳通道
        keltner_data = TechnicalIndicators._calculate_keltner_channels(prices_df)
        indicators.update(keltner_data)
        
        return indicators
    
    @staticmethod
    def calculate_volume_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算成交量指标"""
        indicators = {}
        
        if 'volume' not in prices_df.columns:
            return indicators
        
        # 成交量移动平均
        indicators['volume_sma_20'] = prices_df['volume'].rolling(20).mean().iloc[-1]
        indicators['volume_sma_50'] = prices_df['volume'].rolling(50).mean().iloc[-1]
        
        # OBV (能量潮)
        indicators['obv'] = TechnicalIndicators._calculate_obv(prices_df).iloc[-1]
        
        # A/D线 (累积/派发线)
        indicators['ad_line'] = TechnicalIndicators._calculate_ad_line(prices_df).iloc[-1]
        
        # 成交量比率
        indicators['volume_ratio'] = prices_df['volume'].iloc[-1] / prices_df['volume'].rolling(20).mean().iloc[-1]
        
        # VWAP (成交量加权平均价)
        indicators['vwap'] = TechnicalIndicators._calculate_vwap(prices_df)
        
        return indicators
    
    @staticmethod
    def calculate_support_resistance_indicators(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """计算支撑阻力指标"""
        indicators = {}
        
        # 枢轴点
        pivot_data = TechnicalIndicators._calculate_pivot_points(prices_df)
        indicators.update(pivot_data)
        
        # 斐波那契回撤
        fib_data = TechnicalIndicators._calculate_fibonacci_retracements(prices_df)
        indicators.update(fib_data)
        
        return indicators
    
    # 私有方法实现具体指标计算
    
    @staticmethod
    def _calculate_macd(prices_df: pd.DataFrame, fast=12, slow=26, signal=9) -> Dict[str, float]:
        """计算MACD"""
        ema_fast = prices_df['close'].ewm(span=fast).mean()
        ema_slow = prices_df['close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.iloc[-1],
            'macd_signal': signal_line.iloc[-1],
            'macd_histogram': histogram.iloc[-1]
        }
    
    @staticmethod
    def _calculate_adx(prices_df: pd.DataFrame, period=14) -> Dict[str, float]:
        """计算ADX"""
        # 计算真实波动幅度
        high_low = prices_df['high'] - prices_df['low']
        high_close = abs(prices_df['high'] - prices_df['close'].shift())
        low_close = abs(prices_df['low'] - prices_df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # 计算方向性移动
        up_move = prices_df['high'] - prices_df['high'].shift()
        down_move = prices_df['low'].shift() - prices_df['low']
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # 计算DI
        plus_di = 100 * (pd.Series(plus_dm).ewm(span=period).mean() / tr.ewm(span=period).mean())
        minus_di = 100 * (pd.Series(minus_dm).ewm(span=period).mean() / tr.ewm(span=period).mean())
        
        # 计算ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period).mean()
        
        return {
            'adx': adx.iloc[-1],
            'plus_di': plus_di.iloc[-1],
            'minus_di': minus_di.iloc[-1]
        }
    
    @staticmethod
    def _calculate_rsi(prices_df: pd.DataFrame, period=14) -> pd.Series:
        """计算RSI"""
        delta = prices_df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_stochastic(prices_df: pd.DataFrame, k_period=14, d_period=3) -> Dict[str, float]:
        """计算随机指标"""
        lowest_low = prices_df['low'].rolling(k_period).min()
        highest_high = prices_df['high'].rolling(k_period).max()
        k_percent = 100 * ((prices_df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(d_period).mean()
        
        return {
            'stoch_k': k_percent.iloc[-1],
            'stoch_d': d_percent.iloc[-1]
        }
    
    @staticmethod
    def _calculate_williams_r(prices_df: pd.DataFrame, period=14) -> pd.Series:
        """计算威廉指标"""
        highest_high = prices_df['high'].rolling(period).max()
        lowest_low = prices_df['low'].rolling(period).min()
        williams_r = -100 * ((highest_high - prices_df['close']) / (highest_high - lowest_low))
        return williams_r
    
    @staticmethod
    def _calculate_cci(prices_df: pd.DataFrame, period=20) -> pd.Series:
        """计算商品通道指数"""
        typical_price = (prices_df['high'] + prices_df['low'] + prices_df['close']) / 3
        sma = typical_price.rolling(period).mean()
        mean_deviation = typical_price.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma) / (0.015 * mean_deviation)
        return cci
    
    @staticmethod
    def _calculate_roc(prices_df: pd.DataFrame, period=10) -> pd.Series:
        """计算变动率"""
        roc = ((prices_df['close'] - prices_df['close'].shift(period)) / prices_df['close'].shift(period)) * 100
        return roc
    
    @staticmethod
    def _calculate_momentum(prices_df: pd.DataFrame, period=10) -> pd.Series:
        """计算动量指标"""
        momentum = prices_df['close'] - prices_df['close'].shift(period)
        return momentum
    
    @staticmethod
    def _calculate_bollinger_bands(prices_df: pd.DataFrame, period=20, std_dev=2) -> Dict[str, float]:
        """计算布林带"""
        sma = prices_df['close'].rolling(period).mean()
        std = prices_df['close'].rolling(period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        # 计算布林带位置
        bb_position = (prices_df['close'].iloc[-1] - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
        
        return {
            'bb_upper': upper_band.iloc[-1],
            'bb_middle': sma.iloc[-1],
            'bb_lower': lower_band.iloc[-1],
            'bb_width': (upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1],
            'bb_position': bb_position
        }
    
    @staticmethod
    def _calculate_atr(prices_df: pd.DataFrame, period=14) -> pd.Series:
        """计算真实波动幅度"""
        high_low = prices_df['high'] - prices_df['low']
        high_close = abs(prices_df['high'] - prices_df['close'].shift())
        low_close = abs(prices_df['low'] - prices_df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    @staticmethod
    def _calculate_historical_volatility(prices_df: pd.DataFrame, period=20) -> float:
        """计算历史波动率"""
        returns = prices_df['close'].pct_change()
        volatility = returns.rolling(period).std() * math.sqrt(252)
        return volatility.iloc[-1]
    
    @staticmethod
    def _calculate_keltner_channels(prices_df: pd.DataFrame, period=20, multiplier=2) -> Dict[str, float]:
        """计算肯特纳通道"""
        ema = prices_df['close'].ewm(span=period).mean()
        atr = TechnicalIndicators._calculate_atr(prices_df, period)
        upper_channel = ema + (multiplier * atr)
        lower_channel = ema - (multiplier * atr)
        
        return {
            'keltner_upper': upper_channel.iloc[-1],
            'keltner_middle': ema.iloc[-1],
            'keltner_lower': lower_channel.iloc[-1]
        }
    
    @staticmethod
    def _calculate_sar(prices_df: pd.DataFrame, acceleration=0.02, maximum=0.2) -> float:
        """计算抛物线SAR"""
        # 简化的SAR计算
        high = prices_df['high']
        low = prices_df['low']
        close = prices_df['close']
        
        # 这里使用简化版本，实际实现会更复杂
        sar = close.rolling(10).min()  # 简化计算
        return sar.iloc[-1]
    
    @staticmethod
    def _calculate_ichimoku(prices_df: pd.DataFrame) -> Dict[str, float]:
        """计算一目均衡表"""
        # 转换线 (9日)
        conversion_line = (prices_df['high'].rolling(9).max() + prices_df['low'].rolling(9).min()) / 2
        
        # 基准线 (26日)
        base_line = (prices_df['high'].rolling(26).max() + prices_df['low'].rolling(26).min()) / 2
        
        # 先行带A
        leading_span_a = ((conversion_line + base_line) / 2).shift(26)
        
        # 先行带B
        leading_span_b = ((prices_df['high'].rolling(52).max() + prices_df['low'].rolling(52).min()) / 2).shift(26)
        
        # 滞后线
        lagging_span = prices_df['close'].shift(-26)
        
        return {
            'ichimoku_conversion': conversion_line.iloc[-1],
            'ichimoku_base': base_line.iloc[-1],
            'ichimoku_span_a': leading_span_a.iloc[-1] if not pd.isna(leading_span_a.iloc[-1]) else 0,
            'ichimoku_span_b': leading_span_b.iloc[-1] if not pd.isna(leading_span_b.iloc[-1]) else 0
        }
    
    @staticmethod
    def _calculate_obv(prices_df: pd.DataFrame) -> pd.Series:
        """计算能量潮"""
        obv = pd.Series(index=prices_df.index, dtype=float)
        obv.iloc[0] = prices_df['volume'].iloc[0]
        
        for i in range(1, len(prices_df)):
            if prices_df['close'].iloc[i] > prices_df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + prices_df['volume'].iloc[i]
            elif prices_df['close'].iloc[i] < prices_df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - prices_df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def _calculate_ad_line(prices_df: pd.DataFrame) -> pd.Series:
        """计算累积/派发线"""
        clv = ((prices_df['close'] - prices_df['low']) - (prices_df['high'] - prices_df['close'])) / (prices_df['high'] - prices_df['low'])
        ad_line = (clv * prices_df['volume']).cumsum()
        return ad_line
    
    @staticmethod
    def _calculate_vwap(prices_df: pd.DataFrame) -> float:
        """计算成交量加权平均价"""
        typical_price = (prices_df['high'] + prices_df['low'] + prices_df['close']) / 3
        vwap = (typical_price * prices_df['volume']).sum() / prices_df['volume'].sum()
        return vwap
    
    @staticmethod
    def _calculate_pivot_points(prices_df: pd.DataFrame) -> Dict[str, float]:
        """计算枢轴点"""
        high = prices_df['high'].iloc[-1]
        low = prices_df['low'].iloc[-1]
        close = prices_df['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            'pivot_point': pivot,
            'resistance_1': r1,
            'support_1': s1,
            'resistance_2': r2,
            'support_2': s2
        }
    
    @staticmethod
    def _calculate_fibonacci_retracements(prices_df: pd.DataFrame, period=50) -> Dict[str, float]:
        """计算斐波那契回撤"""
        recent_data = prices_df.tail(period)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        diff = high - low
        
        return {
            'fib_0': high,
            'fib_23_6': high - 0.236 * diff,
            'fib_38_2': high - 0.382 * diff,
            'fib_50': high - 0.5 * diff,
            'fib_61_8': high - 0.618 * diff,
            'fib_100': low
        }


# 全局实例
technical_indicators = TechnicalIndicators()