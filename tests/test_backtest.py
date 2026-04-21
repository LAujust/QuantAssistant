"""
回测模块单元测试
"""
import numpy as np
import pandas as pd
import pytest

from backtest.broker import Broker
from backtest.engine import BacktestEngine
from backtest.metrics import calculate_metrics
from backtest.portfolio import Portfolio


class TestPortfolio:
    def test_initial_state(self):
        p = Portfolio(initial_cash=100000)
        assert p.cash == 100000
        assert p.total_value == 100000

    def test_buy_sell(self):
        p = Portfolio(initial_cash=100000)
        success = p.buy("A", 100, 10.0, 1005)
        assert success is True
        assert p.cash == 100000 - 1005
        pos = p.get_position("A")
        assert pos.quantity == 100
        assert pos.cost_price == 10.0

        success = p.sell("A", 50, 12.0, 594)
        assert success is True
        assert pos.quantity == 50
        assert p.cash == 100000 - 1005 + 594


class TestBroker:
    def test_buy_cost(self):
        b = Broker(commission_rate=0.001, min_commission=5, slippage=0)
        success, price, cost = b.execute_order("A", "buy", 100, 10.0)
        assert success is True
        # 成交金额 1000，手续费 = max(1000*0.001, 5) = 5
        assert cost == 100 * 10.0 + 5

    def test_sell_revenue(self):
        b = Broker(commission_rate=0.001, min_commission=5, slippage=0)
        success, price, revenue = b.execute_order("A", "sell", 100, 10.0)
        assert success is True
        assert revenue == 100 * 10.0 - 5


class TestEngine:
    def test_simple_backtest(self):
        dates = pd.date_range("2020-01-01", periods=100, freq="B")
        prices = pd.DataFrame({
            "A": np.cumsum(np.random.randn(100) * 0.01) + 10,
            "B": np.cumsum(np.random.randn(100) * 0.01) + 10,
        }, index=dates)
        # 等权信号
        signals = pd.DataFrame({
            "A": [0.5] * 100,
            "B": [0.5] * 100,
        }, index=dates)

        engine = BacktestEngine(initial_cash=100000)
        result = engine.run(prices, signals, rebalance_freq="M")
        assert len(result["nav_series"]) == 100
        assert result["nav_series"].iloc[-1] != 100000  # 应该有变化


class TestMetrics:
    def test_basic_metrics(self):
        nav = pd.Series([1.0, 1.1, 1.05, 1.2, 1.15], index=pd.date_range("2020-01-01", periods=5))
        m = calculate_metrics(nav)
        assert m["total_return"] == 0.15
        assert m["max_drawdown"] <= 0
