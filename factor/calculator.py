"""
因子计算引擎：批量计算多因子并存储
"""
from typing import List, Optional

import pandas as pd

from data.storage import Storage
from factor.base import BaseFactor, FactorRegistry


class FactorCalculator:
    """因子计算引擎"""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()

    def calculate_for_asset(
        self,
        code: str,
        factor_names: List[str],
        df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        为单只资产计算多个因子
        如果 df 为 None，则从数据库读取
        返回 DataFrame: columns = [date, code, factor_name, value]
        """
        if df is None:
            from data.manager import DataManager
            dm = DataManager()
            df = dm.get_data(codes=[code])
        if df.empty:
            return pd.DataFrame(columns=["date", "code", "factor_name", "value"])

        df = df.sort_values("date").copy()
        results = []
        for name in factor_names:
            factor_cls = FactorRegistry.get(name)
            factor = factor_cls()
            values = factor.calculate(df)
            factor_df = pd.DataFrame({
                "date": df["date"].values,
                "code": code,
                "factor_name": name,
                "value": values.values,
            })
            results.append(factor_df)

        return pd.concat(results, ignore_index=True)

    def calculate_for_assets(
        self,
        codes: List[str],
        factor_names: List[str],
    ) -> pd.DataFrame:
        """
        为多只资产批量计算因子
        """
        all_results = []
        for code in codes:
            df = self.calculate_for_asset(code, factor_names)
            if not df.empty:
                all_results.append(df)
        if not all_results:
            return pd.DataFrame(columns=["date", "code", "factor_name", "value"])
        return pd.concat(all_results, ignore_index=True)

    def calculate_and_save(
        self,
        codes: List[str],
        factor_names: List[str],
    ) -> int:
        """
        计算并保存到数据库
        """
        df = self.calculate_for_assets(codes, factor_names)
        if df.empty:
            return 0
        df = df.dropna(subset=["value"])
        return self.storage.save_factors(df)
