"""
策略模板：大类资产配置策略
"""
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class BaseStrategy:
    """策略基类"""

    def generate_weights(
        self,
        price_df: pd.DataFrame,
        current_date: pd.Timestamp,
        **kwargs
    ) -> pd.Series:
        """
        生成目标权重
        price_df: index=date, columns=codes
        返回: Series(index=codes, values=weights), sum(weights) 建议为 1
        """
        raise NotImplementedError


class EqualWeightStrategy(BaseStrategy):
    """等权重配置策略"""

    def generate_weights(self, price_df: pd.DataFrame, current_date: pd.Timestamp, **kwargs) -> pd.Series:
        codes = price_df.columns.tolist()
        n = len(codes)
        weights = pd.Series(1.0 / n, index=codes) if n > 0 else pd.Series()
        return weights


class MomentumRotationStrategy(BaseStrategy):
    """
    动量轮动策略
    每期选取过去 lookback 日涨幅最高的 top_n 个资产等权配置
    """

    def __init__(self, lookback: int = 60, top_n: int = 3):
        self.lookback = lookback
        self.top_n = top_n

    def generate_weights(self, price_df: pd.DataFrame, current_date: pd.Timestamp, **kwargs) -> pd.Series:
        # 获取当前日期前的数据
        hist = price_df.loc[:current_date]
        if len(hist) < self.lookback + 1:
            # 数据不足，等权
            codes = price_df.columns.tolist()
            n = len(codes)
            return pd.Series(1.0 / n, index=codes) if n > 0 else pd.Series()

        # 计算动量
        past = hist.iloc[-self.lookback - 1]
        current = hist.iloc[-1]
        momentum = current / past - 1
        momentum = momentum.dropna()

        # 选取 top_n
        top_codes = momentum.nlargest(self.top_n).index.tolist()
        if not top_codes:
            return pd.Series()

        weights = pd.Series(0.0, index=price_df.columns)
        weights.loc[top_codes] = 1.0 / len(top_codes)
        return weights


class RiskParityStrategy(BaseStrategy):
    """
    风险平价策略（简化版）
    按历史波动率倒数加权
    """

    def __init__(self, lookback: int = 60):
        self.lookback = lookback

    def generate_weights(self, price_df: pd.DataFrame, current_date: pd.Timestamp, **kwargs) -> pd.Series:
        hist = price_df.loc[:current_date]
        if len(hist) < self.lookback + 1:
            codes = price_df.columns.tolist()
            n = len(codes)
            return pd.Series(1.0 / n, index=codes) if n > 0 else pd.Series()

        returns = hist.iloc[-self.lookback:].pct_change().dropna()
        vol = returns.std()
        vol = vol.replace(0, np.nan).dropna()
        if vol.empty:
            codes = price_df.columns.tolist()
            n = len(codes)
            return pd.Series(1.0 / n, index=codes) if n > 0 else pd.Series()

        inv_vol = 1.0 / vol
        weights = inv_vol / inv_vol.sum()
        full_weights = pd.Series(0.0, index=price_df.columns)
        full_weights.loc[weights.index] = weights
        return full_weights
