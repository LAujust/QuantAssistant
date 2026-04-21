"""
数据管理模块：统一管理数据更新、校验、读取
"""
from typing import List, Optional

import pandas as pd

from config.settings import DEFAULT_ASSETS
from data.fetcher import DataFetcher
from data.storage import Storage


class DataManager:
    """数据管理器"""

    def __init__(self):
        self.storage = Storage()
        self.fetcher = DataFetcher()

    def init_assets(self):
        """初始化默认资产基本信息到数据库"""
        assets = [
            {
                "code": a["code"],
                "name": a["name"],
                "asset_type": a["asset_type"],
                "market": a.get("market", ""),
                "list_date": "",
            }
            for a in DEFAULT_ASSETS
        ]
        self.storage.save_assets(assets)
        print(f"[DataManager] 已初始化 {len(assets)} 条资产信息")

    def update_assets(
        self,
        asset_list: Optional[List[dict]] = None,
        start: str = "20200101",
        end: Optional[str] = None,
    ):
        """
        批量更新指定资产列表的数据
        asset_list: 如果不传，则使用 DEFAULT_ASSETS
        """
        if asset_list is None:
            asset_list = DEFAULT_ASSETS

        total = 0
        for asset in asset_list:
            code = asset["code"]
            asset_type = asset["asset_type"]
            market = asset.get("market")
            print(f"[DataManager] 正在更新 {code} ({asset_type}) ...")
            df = self.fetcher.fetch(code, asset_type, start, end, market)
            if df is not None and not df.empty:
                n = self.storage.save_quotes(df)
                total += n
                print(f"[DataManager] {code} 更新完成，新增 {n} 条")
            else:
                print(f"[DataManager] {code} 无数据或获取失败")
        print(f"[DataManager] 全部更新完成，共新增 {total} 条记录")

    def get_data(
        self,
        codes: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        asset_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        读取数据到 DataFrame
        如果数据库中数据不足，可在此扩展自动补全逻辑
        """
        df = self.storage.load_quotes(codes, start, end, asset_type)
        return df

    def get_panel_data(
        self,
        codes: List[str],
        field: str = "close",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取面板数据 (panel data)
        返回: index=date, columns=codes, values=field
        """
        df = self.get_data(codes=codes, start=start, end=end)
        if df.empty:
            return pd.DataFrame()
        panel = df.pivot(index="date", columns="code", values=field)
        return panel.sort_index()

    def check_data_integrity(self, codes: List[str]) -> pd.DataFrame:
        """
        检查数据完整性，返回各代码的数据统计
        """
        stats = []
        for code in codes:
            df = self.storage.load_quotes(codes=[code])
            if df.empty:
                stats.append({"code": code, "count": 0, "start": None, "end": None, "missing_pct": 1.0})
            else:
                count = len(df)
                start = df["date"].min().strftime("%Y-%m-%d")
                end = df["date"].max().strftime("%Y-%m-%d")
                # 简单估算缺失比例（按交易日250天/年）
                trading_days = pd.bdate_range(start, end)
                missing_pct = max(0, 1 - count / len(trading_days)) if len(trading_days) > 0 else 0
                stats.append({"code": code, "count": count, "start": start, "end": end, "missing_pct": missing_pct})
        return pd.DataFrame(stats)
