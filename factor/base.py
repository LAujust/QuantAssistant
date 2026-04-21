"""
因子基类与注册机制
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Type

import pandas as pd


class BaseFactor(ABC):
    """因子基类"""

    name: str = "base"

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        计算因子值
        df: 单只资产的日线数据，要求包含 open, high, low, close, volume
        返回: index 与 df 对齐的 Series
        """
        pass


class FactorRegistry:
    """因子注册器"""

    _factors: Dict[str, Type[BaseFactor]] = {}

    @classmethod
    def register(cls, name: str) -> Callable:
        """装饰器注册因子"""
        def wrapper(factor_cls: Type[BaseFactor]) -> Type[BaseFactor]:
            cls._factors[name] = factor_cls
            factor_cls.name = name
            return factor_cls
        return wrapper

    @classmethod
    def get(cls, name: str) -> Type[BaseFactor]:
        if name not in cls._factors:
            raise KeyError(f"未注册的因子: {name}")
        return cls._factors[name]

    @classmethod
    def list_factors(cls) -> Dict[str, Type[BaseFactor]]:
        return cls._factors.copy()
