"""
回测报告生成
"""
import json
from typing import Any, Dict, List

import pandas as pd

from backtest.metrics import calculate_metrics, max_drawdown_series
from data.storage import Storage


class Report:
    """回测报告"""

    def __init__(self):
        self.storage = Storage()

    def generate(
        self,
        run_id: str,
        strategy_name: str,
        start_date: str,
        end_date: str,
        nav_series: pd.Series,
        trades: List[Dict],
        benchmark_series: pd.Series = None,
    ) -> Dict[str, Any]:
        """
        生成完整回测报告
        """
        metrics = calculate_metrics(nav_series, benchmark_series)
        dd_series = max_drawdown_series(nav_series)

        nav_curve = [
            {"date": str(d)[:10], "nav": float(v), "drawdown": float(dd_series.get(d, 0))}
            for d, v in nav_series.items()
        ]

        report = {
            "run_id": run_id,
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
            "trade_count": len(trades),
            "nav_curve": nav_curve,
        }

        # 保存到数据库
        self.storage.save_backtest_result(
            run_id=run_id,
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            trades=trades,
            nav_curve=nav_curve,
        )
        return report

    def load(self, run_id: str) -> Dict[str, Any]:
        """从数据库加载报告"""
        return self.storage.load_backtest_result(run_id)
