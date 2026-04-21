"""
数据获取接口：统一封装 akshare，支持多类资产
"""
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd


class DataFetcher:
    """统一数据获取器"""

    def fetch(
        self,
        code: str,
        asset_type: str,
        start: str = "20200101",
        end: Optional[str] = None,
        market: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取指定资产的历史日线数据
        返回标准化的 DataFrame，列: date, code, asset_type, open, high, low, close, volume, amount
        """
        if end is None:
            end = pd.Timestamp.now().strftime("%Y%m%d")

        if asset_type in ("a_share_etf", "hk_etf"):
            df = self._fetch_a_share_etf(code, start, end, market or "SH")
        elif asset_type == "global_index":
            df = self._fetch_global_index(code, start, end)
        elif asset_type == "commodity":
            df = self._fetch_commodity(code, start, end, market or "SH")
        elif asset_type == "bond":
            df = self._fetch_bond(code, start, end, market or "SH")
        else:
            raise ValueError(f"不支持的资产类型: {asset_type}")

        if df is None or df.empty:
            return pd.DataFrame()

        # 标准化列名
        df = df.rename(
            columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
            }
        )
        # 处理英文列名（部分接口返回英文）
        column_map = {
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Amount": "amount",
        }
        df = df.rename(columns={c: column_map.get(c, c) for c in df.columns})

        # 确保数值类型
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "amount" not in df.columns:
            df["amount"] = 0.0
        else:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        # 过滤无效行
        df = df.dropna(subset=["date", "open", "high", "low", "close"])
        df["code"] = code
        df["asset_type"] = asset_type
        df["date"] = pd.to_datetime(df["date"])

        return df[["date", "code", "asset_type", "open", "high", "low", "close", "volume", "amount"]]

    def _fetch_a_share_etf(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取A股/港股ETF日线"""
        try:
            # akshare fund_etf_hist_em 接口需要6位代码和period
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date=start.replace("-", ""),
                end_date=end.replace("-", ""),
                adjust="qfq",  # 前复权
            )
            return df
        except Exception as e:
            print(f"[DataFetcher] 获取A股ETF {code} 数据失败: {e}")
            return None

    def _fetch_global_index(self, code: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """获取全球指数日线"""
        try:
            # 美股指数通过 sina 接口
            if code in ("SPX", "IXIC", "DJI"):
                df = ak.index_us_stock_sina(symbol=code)
                if "date" not in df.columns.str.lower():
                    df = df.reset_index()
                return df
            # 日经等通过全球指数接口
            symbol_map = {
                "N225": "N225",
                "HSI": "HSI",
            }
            symbol = symbol_map.get(code, code)
            df = ak.index_global_hist(symbol=symbol)
            return df
        except Exception as e:
            print(f"[DataFetcher] 获取全球指数 {code} 数据失败: {e}")
            return None

    def _fetch_commodity(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取商品（黄金ETF等）日线"""
        # 国内黄金ETF通过ETF接口获取
        return self._fetch_a_share_etf(code, start, end, market)

    def _fetch_bond(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取债券ETF日线"""
        # 国内债券ETF通过ETF接口获取
        return self._fetch_a_share_etf(code, start, end, market)

    def fetch_asset_list(self, asset_type: str) -> pd.DataFrame:
        """获取某类资产的代码列表"""
        if asset_type in ("a_share_etf", "hk_etf"):
            try:
                df = ak.fund_etf_spot_em()
                df = df[["代码", "名称"]].rename(columns={"代码": "code", "名称": "name"})
                df["asset_type"] = asset_type
                return df
            except Exception as e:
                print(f"[DataFetcher] 获取ETF列表失败: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
