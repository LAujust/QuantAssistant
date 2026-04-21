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


class BollingerRotationStrategy(BaseStrategy):
    """布林带多因子轮动策略"""

    def __init__(
        self,
        safe_assets: Optional[List[str]] = None,
        risk_assets: Optional[List[str]] = None,
        window: int = 20,
        n_std: float = 2.0,
        val_window: int = 252 * 3,
        mom_window: int = 20,
        vol_window: int = 20,
        trend_window: int = 60,
        w_val: float = 0.5,
        w_mom: float = 0.2,
        w_vol: float = 0.1,
        w_trend: float = 0.2,
        buy_quantile: float = 0.2,
        sell_quantile: float = 0.8,
    ):
        self.safe_assets = frozenset(safe_assets or [])
        self.risk_assets = frozenset(risk_assets or [])
        self.window = window
        self.n_std = n_std
        self.val_window = val_window
        self.mom_window = mom_window
        self.vol_window = vol_window
        self.trend_window = trend_window
        self.w_val = w_val
        self.w_mom = w_mom
        self.w_vol = w_vol
        self.w_trend = w_trend
        self.buy_quantile = buy_quantile
        self.sell_quantile = sell_quantile
        self._precomputed = False
        self._bands: Dict[str, tuple] = {}
        self._val_scores: Dict[str, pd.Series] = {}
        self._mom_scores: Dict[str, pd.Series] = {}
        self._vol_scores: Dict[str, pd.Series] = {}
        self._trend_scores: Dict[str, pd.Series] = {}
        self._quantiles: Dict[str, pd.Series] = {}

    def _precompute_factors(self, price_df: pd.DataFrame) -> None:
        for a in price_df.columns:
            series = price_df[a]
            if series.dropna().empty:
                continue

            ma = series.rolling(self.window).mean()
            std = series.rolling(self.window).std()
            self._bands[a] = (ma + self.n_std * std, ma - self.n_std * std)

            rolling_min = series.rolling(self.val_window, min_periods=1).min()
            rolling_max = series.rolling(self.val_window, min_periods=1).max()
            self._val_scores[a] = 1 - (series - rolling_min) / (rolling_max - rolling_min + 1e-6)

            ret = series / series.shift(self.mom_window) - 1
            self._mom_scores[a] = (-ret).clip(-1, 1)

            vol = series.pct_change().rolling(self.vol_window, min_periods=1).std()
            self._vol_scores[a] = (vol - vol.min()) / (vol.max() - vol.min() + 1e-6)

            self._trend_scores[a] = series.pct_change(self.trend_window)
            self._quantiles[a] = series.rank(pct=True)

        self._precomputed = True

    def _signal_logic(self, a: str, price: float, up: float, low: float, quantile: float):
        is_safe = a in self.safe_assets
        is_risk = a in self.risk_assets
        buy = False
        sell = False
        if is_risk:
            buy = price < low or quantile <= self.buy_quantile
            sell = price > up or quantile >= self.sell_quantile
        elif is_safe:
            buy = price < low
            sell = price > up
        return buy, sell

    def generate_weights(
        self, price_df: pd.DataFrame, current_date: pd.Timestamp, **kwargs
    ) -> pd.Series:
        if not self._precomputed:
            self._precompute_factors(price_df)

        if current_date not in price_df.index:
            return pd.Series(0.0, index=price_df.columns)

        scores = pd.Series(0.0, index=price_df.columns)

        for a in price_df.columns:
            if a not in self._bands:
                continue

            upper, lower = self._bands[a]
            up = upper.loc[current_date]
            low = lower.loc[current_date]
            if np.isnan(up) or np.isnan(low):
                continue

            price = price_df.loc[current_date, a]
            quantile = self._quantiles[a].loc[current_date]
            buy_signal, sell_signal = self._signal_logic(a, price, up, low, quantile)

            if sell_signal:
                continue
            if buy_signal:
                v = self._val_scores[a].loc[current_date]
                m = self._mom_scores[a].loc[current_date]
                vol = self._vol_scores[a].loc[current_date]
                trend = self._trend_scores[a].loc[current_date]

                score = (
                    self.w_val * v
                    + self.w_mom * max(m, 0)
                    + self.w_vol * vol * (1 + vol)
                    + self.w_trend * max(trend, 0)
                )
                scores[a] = max(score, 0.01)

        if self.risk_assets:
            avg_trend = np.nanmean([
                self._trend_scores[a].loc[current_date]
                for a in self.risk_assets
                if a in self._trend_scores and current_date in self._trend_scores[a].index
            ])
            if avg_trend < 0:
                for a in scores.index:
                    if a in self.risk_assets:
                        scores[a] *= 0.5
                    elif a in self.safe_assets:
                        scores[a] *= 2.0

        total = scores.sum()
        if total > 0:
            return scores / total
        return scores

    def generate_signals(
        self,
        price_df: pd.DataFrame,
        as_of_date: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        if not self._precomputed:
            self._precompute_factors(price_df)

        if as_of_date is None:
            as_of_date = price_df.index[-1]
        as_of_date = pd.Timestamp(as_of_date)

        results = []
        for a in price_df.columns:
            series = price_df[a].dropna()
            if as_of_date not in series.index:
                continue

            price = series.loc[as_of_date]
            upper, lower = self._bands[a]
            up = upper.loc[as_of_date]
            low = lower.loc[as_of_date]
            quantile = self._quantiles[a].loc[as_of_date]

            buy_signal, sell_signal = self._signal_logic(a, price, up, low, quantile)
            reasons = []
            if buy_signal:
                reasons.append("Lower Band" if a in self.safe_assets else "Undervalued / Lower Band")
            if sell_signal:
                reasons.append("Upper Band" if a in self.safe_assets else "Overvalued / Upper Band")

            signal = "HOLD"
            if buy_signal and not sell_signal:
                signal = "BUY"
            elif sell_signal and not buy_signal:
                signal = "SELL"

            results.append({
                "date": as_of_date,
                "asset": a,
                "price": price,
                "quantile": quantile,
                "valuation": self._val_scores[a].loc[as_of_date],
                "momentum": self._mom_scores[a].loc[as_of_date],
                "volatility": self._vol_scores[a].loc[as_of_date],
                "trend": self._trend_scores[a].loc[as_of_date],
                "boll_upper": up,
                "boll_lower": low,
                "signal": signal,
                "signal_reason": "; ".join(reasons),
            })

        return pd.DataFrame(results)
