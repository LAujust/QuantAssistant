"""
技术因子实现
"""
import numpy as np
import pandas as pd

from factor.base import BaseFactor, FactorRegistry


@FactorRegistry.register("momentum_20")
class MomentumFactor(BaseFactor):
    """20日动量因子: (close / close.shift(20) - 1)"""

    def __init__(self, window: int = 20):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        return df["close"] / df["close"].shift(self.window) - 1


@FactorRegistry.register("momentum_60")
class MomentumFactor60(BaseFactor):
    """60日动量因子"""

    def __init__(self, window: int = 60):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        return df["close"] / df["close"].shift(self.window) - 1


@FactorRegistry.register("rsi")
class RSIFactor(BaseFactor):
    """RSI 相对强弱指标"""

    def __init__(self, window: int = 14):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(self.window, min_periods=1).mean()
        avg_loss = loss.rolling(self.window, min_periods=1).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


@FactorRegistry.register("macd")
class MACDFactor(BaseFactor):
    """MACD 因子: DIF 值"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        ema_fast = df["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        return dif


@FactorRegistry.register("bollinger")
class BollingerFactor(BaseFactor):
    """布林带位置因子: (close - lower) / (upper - lower)"""

    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        ma = df["close"].rolling(self.window).mean()
        std = df["close"].rolling(self.window).std()
        upper = ma + self.num_std * std
        lower = ma - self.num_std * std
        pos = (df["close"] - lower) / (upper - lower)
        return pos


@FactorRegistry.register("atr")
class ATRFactor(BaseFactor):
    """平均真实波幅因子"""

    def __init__(self, window: int = 14):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(self.window, min_periods=1).mean()
        return atr


@FactorRegistry.register("volatility")
class VolatilityFactor(BaseFactor):
    """波动率因子: 收益率标准差"""

    def __init__(self, window: int = 20):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change()
        vol = returns.rolling(self.window, min_periods=1).std() * np.sqrt(252)
        return vol
