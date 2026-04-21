"""
数据获取接口：统一封装 akshare，支持多类资产
包含重试机制与多源备用接口，提升数据获取稳定性
"""
import functools
import os
import time
from typing import Callable, List, Optional

import akshare as ak
import pandas as pd

from utils.logger import get_logger

# 根据 AKShare 官方建议，在导入时清理代理环境变量，确保直连国内数据源
# 参考: AKShare_Error.md - 禁用环境变量中的代理设置
for _proxy_key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_proxy_key, None)
os.environ["NO_PROXY"] = "eastmoney.com,sina.com.cn,127.0.0.1,localhost"

logger = get_logger("data.fetcher")


def retry_on_network_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """指数退避重试装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        logger.warning(
                            f"[{func.__name__}] 第 {attempt} 次尝试失败: {e}, "
                            f"{delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        logger.error(f"[{func.__name__}] 全部 {max_retries} 次尝试均失败: {e}")
            raise last_exc
        return wrapper
    return decorator


class DataFetcher:
    """统一数据获取器（含重试与多源备用）"""

    # akshare 全球指数代码映射（内部标识 -> akshare 接口代码）
    GLOBAL_INDEX_MAP = {
        ".INX": ".INX",              # 标普500
        ".IXIC": ".IXIC",           # 纳斯达克
        "NKY": "日经225",           # 日经225 (index_global_hist_em 需中文名)
    }

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

        df = self._normalize_columns(df)
        df = self._filter_by_date(df, start, end)
        df["code"] = code
        df["asset_type"] = asset_type
        df["date"] = pd.to_datetime(df["date"])

        return df[["date", "code", "asset_type", "open", "high", "low", "close", "volume", "amount"]]

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Amount": "amount",
        }
        df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

        # 统一日期类型（sina 接口返回 datetime.date，em 接口返回字符串）
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "amount" not in df.columns:
            df["amount"] = 0.0
        else:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        df = df.dropna(subset=["date", "open", "high", "low", "close"])
        return df

    @staticmethod
    def _filter_by_date(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        """按日期范围过滤"""
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        return df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]

    @retry_on_network_error(max_retries=3, base_delay=1.0, backoff=2.0)
    def _fetch_a_share_etf(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取A股/港股ETF日线（东方财富主接口 + 新浪备用接口）"""
        try:
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date=start.replace("-", ""),
                end_date=end.replace("-", ""),
                adjust="qfq",
            )
            if df is not None and not df.empty:
                logger.info(f"[DataFetcher] fund_etf_hist_em 获取 {code} 成功")
                return df
        except Exception as e:
            logger.warning(f"[DataFetcher] fund_etf_hist_em 获取 {code} 失败: {e}")

        # 备用：新浪接口
        try:
            sina_symbol = f"{market.lower()}{code}"
            df = ak.fund_etf_hist_sina(symbol=sina_symbol)
            if df is not None and not df.empty:
                logger.info(f"[DataFetcher] fund_etf_hist_sina 获取 {code} 成功")
                return df
        except Exception as e:
            logger.error(f"[DataFetcher] fund_etf_hist_sina 获取 {code} 失败: {e}")
        return None

    @retry_on_network_error(max_retries=3, base_delay=1.0, backoff=2.0)
    def _fetch_global_index(self, code: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """获取全球指数日线（多接口适配）"""
        ak_code = self.GLOBAL_INDEX_MAP.get(code, code)

        # 美股指数通过 sina 接口（相对稳定）
        if ak_code in (".INX", ".IXIC", ".DJI"):
            try:
                df = ak.index_us_stock_sina(symbol=ak_code)
                if "date" not in [c.lower() for c in df.columns]:
                    df = df.reset_index()
                logger.info(f"[DataFetcher] index_us_stock_sina 获取 {code} 成功")
                return df
            except Exception as e:
                logger.error(f"[DataFetcher] index_us_stock_sina 获取 {code} 失败: {e}")
                return None

        # 其他全球指数通过 em 接口（带重试）
        try:
            df = ak.index_global_hist_em(symbol=ak_code)
            if df is not None and not df.empty:
                logger.info(f"[DataFetcher] index_global_hist_em 获取 {code} 成功")
                return df
        except Exception as e:
            logger.error(f"[DataFetcher] index_global_hist_em 获取 {code} 失败: {e}")
        return None

    def _fetch_commodity(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取商品（黄金ETF等）日线"""
        return self._fetch_a_share_etf(code, start, end, market)

    def _fetch_bond(self, code: str, start: str, end: str, market: str) -> Optional[pd.DataFrame]:
        """获取债券ETF日线"""
        return self._fetch_a_share_etf(code, start, end, market)

    @retry_on_network_error(max_retries=3, base_delay=1.0, backoff=2.0)
    def fetch_asset_list(self, asset_type: str) -> pd.DataFrame:
        """获取某类资产的代码列表"""
        if asset_type in ("a_share_etf", "hk_etf"):
            try:
                df = ak.fund_etf_spot_em()
                df = df[["代码", "名称"]].rename(columns={"代码": "code", "名称": "name"})
                df["asset_type"] = asset_type
                return df
            except Exception as e:
                logger.error(f"[DataFetcher] 获取ETF列表失败: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
