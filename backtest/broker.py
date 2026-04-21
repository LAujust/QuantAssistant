"""
模拟经纪商：处理订单、计算手续费和滑点
"""
from typing import Dict, Optional, Tuple

from config.settings import BACKTEST_CONFIG


class Broker:
    """模拟经纪商"""

    def __init__(
        self,
        commission_rate: Optional[float] = None,
        min_commission: Optional[float] = None,
        slippage: Optional[float] = None,
    ):
        self.commission_rate = commission_rate if commission_rate is not None else BACKTEST_CONFIG["commission_rate"]
        self.min_commission = min_commission if min_commission is not None else BACKTEST_CONFIG["min_commission"]
        self.slippage = slippage if slippage is not None else BACKTEST_CONFIG["slippage"]

    def execute_order(
        self,
        code: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        price: float,
        order_type: str = "market",
    ) -> Tuple[bool, float, float]:
        """
        执行订单
        返回: (是否成功, 成交价, 实际成本/收入)
        buy:  cost = 成交金额 + 手续费 + 滑点
        sell: revenue = 成交金额 - 手续费 - 滑点
        """
        if quantity <= 0:
            return False, 0.0, 0.0

        # 滑点处理：买入时价格上浮，卖出时价格下浮
        if side == "buy":
            executed_price = price * (1 + self.slippage)
            amount = quantity * executed_price
            commission = max(amount * self.commission_rate, self.min_commission)
            total_cost = amount + commission
            return True, executed_price, total_cost
        elif side == "sell":
            executed_price = price * (1 - self.slippage)
            amount = quantity * executed_price
            commission = max(amount * self.commission_rate, self.min_commission)
            revenue = amount - commission
            return True, executed_price, revenue
        else:
            return False, 0.0, 0.0

    def get_trade_detail(
        self,
        code: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Dict:
        """获取交易明细（用于记录）"""
        success, executed_price, cost_or_revenue = self.execute_order(code, side, quantity, price)
        return {
            "code": code,
            "side": side,
            "quantity": quantity,
            "price": price,
            "executed_price": executed_price,
            "cost_or_revenue": cost_or_revenue,
            "success": success,
        }
