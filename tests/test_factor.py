"""
因子模块单元测试
"""
import numpy as np
import pandas as pd
import pytest

from factor.technical import MomentumFactor, RSIFactor, MACDFactor, BollingerFactor


class TestFactors:
    def _make_df(self, n=100):
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=n, freq="B")
        close = np.cumsum(np.random.randn(n) * 0.5) + 100
        df = pd.DataFrame({
            "date": dates,
            "open": close + np.random.randn(n) * 0.2,
            "high": close + abs(np.random.randn(n)) * 0.5,
            "low": close - abs(np.random.randn(n)) * 0.5,
            "close": close,
            "volume": np.random.randint(1000, 10000, n),
        })
        return df

    def test_momentum(self):
        df = self._make_df()
        f = MomentumFactor(window=20)
        result = f.calculate(df)
        assert len(result) == len(df)
        assert result.iloc[:20].isna().sum() == 20
        assert not result.iloc[20:].isna().any()

    def test_rsi(self):
        df = self._make_df()
        f = RSIFactor(window=14)
        result = f.calculate(df)
        assert len(result) == len(df)
        assert result.min() >= 0
        assert result.max() <= 100

    def test_macd(self):
        df = self._make_df()
        f = MACDFactor()
        result = f.calculate(df)
        assert len(result) == len(df)

    def test_bollinger(self):
        df = self._make_df()
        f = BollingerFactor(window=20)
        result = f.calculate(df)
        assert len(result) == len(df)
        # 布林带位置应该在 0~1 附近（可能超出一点）
