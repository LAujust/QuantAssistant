"""
回测引擎：支持向量化回测
事件驱动回测预留扩展接口
"""
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import numpy as np

from backtest.broker import Broker
from backtest.portfolio import Portfolio


class BacktestEngine:
    """
    向量化回测引擎
    适用于多因子、大类资产配置等策略的快速回测
    """

    def __init__(
        self,
        initial_cash: float = 1_000_000.0,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage: float = 0.001,
    ):
        self.initial_cash = initial_cash
        self.broker = Broker(commission_rate, min_commission, slippage)
        self.portfolio: Optional[Portfolio] = None
        self.nav_series: pd.Series = pd.Series(dtype=float)
        self.trades: List[Dict] = []

    def run(
        self,
        price_df: pd.DataFrame,
        signal_df: pd.DataFrame,
        rebalance_freq: str = "M",  # "D" 日频, "W" 周频, "M" 月频
    ) -> Dict[str, Any]:
        """
        执行向量化回测

        Parameters
        ----------
        price_df : DataFrame
            价格数据，index=date, columns=codes, values=close price
        signal_df : DataFrame
            目标权重信号，index=date, columns=codes, values=weight (0~1)
            行和可以不等于1，引擎会自动归一化
        rebalance_freq : str
            调仓频率，默认月频 "M"

        Returns
        -------
        dict: 包含 nav_series, trades, final_portfolio
        """
        if price_df.empty or signal_df.empty:
            return {}

        self.portfolio = Portfolio(self.initial_cash)
        self.trades = []
        nav_records = []

        # 统一索引
        common_dates = price_df.index.intersection(signal_df.index)
        price_df = price_df.loc[common_dates]
        signal_df = signal_df.loc[common_dates]

        # 生成调仓日
        if rebalance_freq == "D":
            rebalance_dates = common_dates
        elif rebalance_freq == "W":
            rebalance_dates = price_df.resample("W-FRI").last().dropna().index
        else:  # 默认月频，月末调仓
            rebalance_dates = price_df.resample("ME").last().dropna().index

        last_weights = pd.Series(0.0, index=price_df.columns)

        for date in common_dates:
            prices_today = price_df.loc[date].dropna()

            # 更新持仓市值
            self.portfolio.update_market_value(prices_today.to_dict())

            # 调仓日：根据信号重新平衡
            if date in rebalance_dates:
                signal_today = signal_df.loc[date].dropna()
                signal_today = signal_today[signal_today.index.isin(prices_today.index)]
                if not signal_today.empty:
                    target_weights = self._normalize_weights(signal_today)
                    self._rebalance(date, prices_today, target_weights)
                    last_weights = target_weights

            nav_records.append({"date": date, "nav": self.portfolio.total_value})

        self.nav_series = pd.Series(
            [r["nav"] for r in nav_records],
            index=[r["date"] for r in nav_records],
        )

        return {
            "nav_series": self.nav_series,
            "trades": self.trades,
            "final_portfolio": self.portfolio.to_dict(),
        }

    def _normalize_weights(self, weights: pd.Series) -> pd.Series:
        """归一化权重，使其和为1"""
        total = weights.abs().sum()
        if total == 0:
            return weights
        return weights / total

    def _rebalance(
        self,
        date: pd.Timestamp,
        prices: pd.Series,
        target_weights: pd.Series,
    ):
        """执行再平衡操作"""
        total_value = self.portfolio.total_value
        current_ratios = self.portfolio.position_ratio

        for code in target_weights.index:
            target_value = total_value * target_weights[code]
            price = prices.get(code, 0.0)
            if price <= 0:
                continue

            target_quantity = target_value / price
            current_qty = self.portfolio.get_position(code).quantity
            diff = target_quantity - current_qty

            if diff > 0:
                # 买入
                success, executed_price, cost = self.broker.execute_order(
                    code, "buy", diff, price
                )
                if success and cost <= self.portfolio.cash:
                    self.portfolio.buy(code, diff, executed_price, cost)
                    self.trades.append({
                        "date": str(date)[:10],
                        "code": code,
                        "side": "buy",
                        "quantity": diff,
                        "price": executed_price,
                        "cost": cost,
                    })
            elif diff < 0:
                # 卖出
                sell_qty = abs(diff)
                success, executed_price, revenue = self.broker.execute_order(
                    code, "sell", sell_qty, price
                )
                if success:
                    self.portfolio.sell(code, sell_qty, executed_price, revenue)
                    self.trades.append({
                        "date": str(date)[:10],
                        "code": code,
                        "side": "sell",
                        "quantity": sell_qty,
                        "price": executed_price,
                        "revenue": revenue,
                    })
