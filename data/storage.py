"""
SQLite 数据库操作封装
提供连接管理、事务、CRUD 和批量插入功能
"""
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config.settings import DB_PATH


class Storage:
    """SQLite 存储封装类"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DB_PATH)
        self._init_schema()

    @contextmanager
    def _connect(self):
        """上下文管理器管理数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        """初始化数据库表结构"""
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            return
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        with self._connect() as conn:
            conn.executescript(sql)
            conn.commit()

    # ------------------------------------------------------------------
    # 通用 CRUD
    # ------------------------------------------------------------------
    def execute(self, sql: str, params: Tuple = ()) -> int:
        """执行单条 SQL，返回影响行数"""
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """查询单条记录，返回字典或 None"""
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """查询多条记录，返回字典列表"""
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def insert_many(self, table: str, records: List[Dict[str, Any]]) -> int:
        """批量插入数据，自动忽略重复记录"""
        if not records:
            return 0
        keys = list(records[0].keys())
        columns = ", ".join(keys)
        placeholders = ", ".join(["?"] * len(keys))
        sql = f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
        values = [tuple(r[k] for k in keys) for r in records]
        with self._connect() as conn:
            conn.executemany(sql, values)
            conn.commit()
            return conn.total_changes

    # ------------------------------------------------------------------
    # daily_quotes 专用接口
    # ------------------------------------------------------------------
    def save_quotes(self, df: pd.DataFrame) -> int:
        """将 DataFrame 存入 daily_quotes，要求列包含 date, code, asset_type, open, high, low, close, volume, amount"""
        if df.empty:
            return 0
        required = {"date", "code", "asset_type", "open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"缺少必要列: {missing}")
        # 确保 date 为字符串
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["amount"] = df.get("amount", 0)
        records = df[["date", "code", "asset_type", "open", "high", "low", "close", "volume", "amount"]].to_dict("records")
        return self.insert_many("daily_quotes", records)

    def load_quotes(
        self,
        codes: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        asset_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """从 daily_quotes 读取数据到 DataFrame"""
        conditions = []
        params = []
        if codes:
            placeholders = ", ".join(["?"] * len(codes))
            conditions.append(f"code IN ({placeholders})")
            params.extend(codes)
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)
        if asset_type:
            conditions.append("asset_type = ?")
            params.append(asset_type)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM daily_quotes {where_clause} ORDER BY date"
        rows = self.fetchall(sql, tuple(params))
        if not rows:
            return pd.DataFrame(columns=["date", "code", "asset_type", "open", "high", "low", "close", "volume", "amount"])
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def get_last_date(self, code: str) -> Optional[str]:
        """获取某代码最新的已有数据日期"""
        row = self.fetchone("SELECT MAX(date) as max_date FROM daily_quotes WHERE code = ?", (code,))
        return row["max_date"] if row and row["max_date"] else None

    # ------------------------------------------------------------------
    # asset_info 专用接口
    # ------------------------------------------------------------------
    def save_assets(self, assets: List[Dict[str, Any]]) -> int:
        """批量保存资产基本信息"""
        return self.insert_many("asset_info", assets)

    def load_assets(self, asset_type: Optional[str] = None) -> pd.DataFrame:
        """读取资产基本信息"""
        if asset_type:
            rows = self.fetchall("SELECT * FROM asset_info WHERE asset_type = ?", (asset_type,))
        else:
            rows = self.fetchall("SELECT * FROM asset_info")
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # factors 专用接口
    # ------------------------------------------------------------------
    def save_factors(self, df: pd.DataFrame) -> int:
        """保存因子数据，要求列包含 date, code, factor_name, value"""
        if df.empty:
            return 0
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        records = df[["date", "code", "factor_name", "value"]].to_dict("records")
        return self.insert_many("factors", records)

    def load_factors(
        self,
        factor_name: str,
        codes: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """读取因子数据"""
        conditions = ["factor_name = ?"]
        params = [factor_name]
        if codes:
            placeholders = ", ".join(["?"] * len(codes))
            conditions.append(f"code IN ({placeholders})")
            params.extend(codes)
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)
        where_clause = "WHERE " + " AND ".join(conditions)
        sql = f"SELECT date, code, value FROM factors {where_clause} ORDER BY date"
        rows = self.fetchall(sql, tuple(params))
        if not rows:
            return pd.DataFrame(columns=["date", "code", "value"])
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df

    # ------------------------------------------------------------------
    # backtest_results 专用接口
    # ------------------------------------------------------------------
    def save_backtest_result(
        self,
        run_id: str,
        strategy_name: str,
        start_date: str,
        end_date: str,
        metrics: Dict[str, Any],
        trades: List[Dict],
        nav_curve: List[Dict],
    ) -> int:
        """保存回测结果"""
        record = {
            "run_id": run_id,
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "metrics_json": json.dumps(metrics, ensure_ascii=False, default=str),
            "trades_json": json.dumps(trades, ensure_ascii=False, default=str),
            "nav_curve_json": json.dumps(nav_curve, ensure_ascii=False, default=str),
        }
        return self.insert_many("backtest_results", [record])

    def load_backtest_result(self, run_id: str) -> Optional[Dict[str, Any]]:
        """读取回测结果"""
        row = self.fetchone("SELECT * FROM backtest_results WHERE run_id = ?", (run_id,))
        if not row:
            return None
        result = dict(row)
        for key in ["metrics_json", "trades_json", "nav_curve_json"]:
            if result.get(key):
                result[key] = json.loads(result[key])
        return result
