"""
因子筛选与检验：IC分析、分层回测、相关性检测
"""
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data.storage import Storage


class FactorSelector:
    """因子筛选器"""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()

    def load_factor_data(
        self,
        factor_name: str,
        codes: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """加载因子数据，返回 wide format: index=date, columns=codes"""
        df = self.storage.load_factors(factor_name, codes, start, end)
        if df.empty:
            return pd.DataFrame()
        return df.pivot(index="date", columns="code", values="value")

    def load_return_data(
        self,
        codes: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """加载未来收益率数据（1日）"""
        from data.manager import DataManager
        dm = DataManager()
        prices = dm.get_panel_data(codes, field="close", start=start, end=end)
        returns = prices.pct_change().shift(-1)  # 未来1日收益
        return returns

    def ic_analysis(
        self,
        factor_name: str,
        codes: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        method: str = "spearman",
    ) -> Dict[str, float]:
        """
        IC 分析
        返回: mean_ic, ic_std, ir, ic_positive_ratio
        """
        factor_df = self.load_factor_data(factor_name, codes, start, end)
        returns_df = self.load_return_data(codes, start, end)

        if factor_df.empty or returns_df.empty:
            return {}

        common_dates = factor_df.index.intersection(returns_df.index)
        factor_df = factor_df.loc[common_dates]
        returns_df = returns_df.loc[common_dates]

        ics = []
        for date in common_dates:
            f = factor_df.loc[date].dropna()
            r = returns_df.loc[date].dropna()
            common_codes = f.index.intersection(r.index)
            if len(common_codes) < 3:
                continue
            if method == "spearman":
                ic = f.loc[common_codes].corr(r.loc[common_codes], method="spearman")
            else:
                ic = f.loc[common_codes].corr(r.loc[common_codes], method="pearson")
            if not np.isnan(ic):
                ics.append(ic)

        if not ics:
            return {}

        ics = pd.Series(ics)
        return {
            "mean_ic": round(ics.mean(), 4),
            "ic_std": round(ics.std(), 4),
            "ir": round(ics.mean() / ics.std(), 4) if ics.std() != 0 else np.nan,
            "ic_positive_ratio": round((ics > 0).mean(), 4),
            "ic_count": len(ics),
        }

    def layer_backtest(
        self,
        factor_name: str,
        codes: List[str],
        n_layers: int = 5,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        分层回测：按因子值分为 n_layers 层，每层等权持有，观察各层收益差异
        返回: index=date, columns=layer_1 ~ layer_n, values=daily_return
        """
        factor_df = self.load_factor_data(factor_name, codes, start, end)
        returns_df = self.load_return_data(codes, start, end)

        if factor_df.empty or returns_df.empty:
            return pd.DataFrame()

        common_dates = factor_df.index.intersection(returns_df.index)
        factor_df = factor_df.loc[common_dates]
        returns_df = returns_df.loc[common_dates]

        layer_returns = []
        for date in common_dates:
            f = factor_df.loc[date].dropna()
            r = returns_df.loc[date].dropna()
            common_codes = f.index.intersection(r.index)
            if len(common_codes) < n_layers:
                continue

            f = f.loc[common_codes]
            r = r.loc[common_codes]

            # 按因子值分层
            labels = [f"layer_{i+1}" for i in range(n_layers)]
            f_rank = pd.qcut(f, q=n_layers, labels=labels, duplicates="drop")

            day_return = {}
            for layer in labels:
                layer_codes = f_rank[f_rank == layer].index
                if len(layer_codes) > 0:
                    day_return[layer] = r.loc[layer_codes].mean()

            layer_returns.append(pd.Series(day_return, name=date))

        if not layer_returns:
            return pd.DataFrame()
        return pd.DataFrame(layer_returns)

    def factor_correlation(
        self,
        factor_names: List[str],
        codes: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        计算因子间的截面相关性均值
        """
        factor_data = {}
        for name in factor_names:
            df = self.load_factor_data(name, codes, start, end)
            if not df.empty:
                factor_data[name] = df

        if len(factor_data) < 2:
            return pd.DataFrame()

        corr_records = []
        for date in factor_data[factor_names[0]].index:
            row = {}
            for name in factor_names:
                if date in factor_data[name].index:
                    row[name] = factor_data[name].loc[date]
            if len(row) >= 2:
                corr_df = pd.DataFrame(row).corr()
                corr_records.append(corr_df)

        if not corr_records:
            return pd.DataFrame()
        return pd.concat(corr_records).groupby(level=0).mean()
