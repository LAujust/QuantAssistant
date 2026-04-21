"""
账户与持仓管理
"""
from typing import Dict, List, Optional


class Position:
    """单个持仓"""

    def __init__(self, code: str, quantity: float = 0.0, cost_price: float = 0.0):
        self.code = code
        self.quantity = quantity          # 持仓数量
        self.cost_price = cost_price      # 成本价
        self.market_value = 0.0           # 市值

    def update_price(self, price: float):
        """更新最新价格"""
        self.market_value = self.quantity * price

    @property
    def pnl(self) -> float:
        """浮动盈亏"""
        if self.quantity == 0:
            return 0.0
        return self.market_value - self.quantity * self.cost_price


class Portfolio:
    """投资组合"""

    def __init__(self, initial_cash: float = 1_000_000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash          # 可用现金
        self.positions: Dict[str, Position] = {}  # code -> Position
        self.total_value = initial_cash   # 总市值

    def get_position(self, code: str) -> Position:
        """获取或创建持仓对象"""
        if code not in self.positions:
            self.positions[code] = Position(code)
        return self.positions[code]

    def update_market_value(self, prices: Dict[str, float]):
        """根据最新价格更新所有持仓市值和总市值"""
        total_position_value = 0.0
        for code, pos in self.positions.items():
            price = prices.get(code)
            if price is None or price != price:  # 跳过缺失或 NaN 价格
                total_position_value += pos.market_value
                continue
            pos.update_price(price)
            total_position_value += pos.market_value
        self.total_value = self.cash + total_position_value

    def buy(self, code: str, quantity: float, price: float, cost: float) -> bool:
        """
        买入操作
        quantity: 买入数量
        price: 成交价
        cost: 总成本（含手续费、滑点）
        """
        if cost > self.cash:
            return False
        pos = self.get_position(code)
        # 更新成本价（加权平均）
        total_cost = pos.quantity * pos.cost_price + quantity * price
        pos.quantity += quantity
        pos.cost_price = total_cost / pos.quantity if pos.quantity > 0 else 0.0
        pos.update_price(price)
        self.cash -= cost
        self.total_value = self.cash + sum(p.market_value for p in self.positions.values())
        return True

    def sell(self, code: str, quantity: float, price: float, revenue: float) -> bool:
        """
        卖出操作
        quantity: 卖出数量
        price: 成交价
        revenue: 实际到账金额（扣除手续费、滑点）
        """
        pos = self.get_position(code)
        if pos.quantity < quantity:
            return False
        pos.quantity -= quantity
        if pos.quantity == 0:
            pos.cost_price = 0.0
            pos.market_value = 0.0
        else:
            pos.update_price(price)
        self.cash += revenue
        self.total_value = self.cash + sum(p.market_value for p in self.positions.values())
        return True

    @property
    def position_ratio(self) -> Dict[str, float]:
        """各持仓占总市值比例"""
        if self.total_value == 0:
            return {}
        return {
            code: pos.market_value / self.total_value
            for code, pos in self.positions.items()
            if pos.market_value > 0
        }

    def to_dict(self) -> dict:
        return {
            "cash": round(self.cash, 2),
            "total_value": round(self.total_value, 2),
            "positions": {
                code: {
                    "quantity": pos.quantity,
                    "cost_price": round(pos.cost_price, 4),
                    "market_value": round(pos.market_value, 2),
                    "pnl": round(pos.pnl, 2),
                }
                for code, pos in self.positions.items()
                if pos.quantity != 0
            },
        }
