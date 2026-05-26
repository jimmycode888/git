from dataclasses import dataclass, field

from config.settings import INITIAL_CAPITAL, COMMISSION_RATE, SLIPPAGE
from .base import BrokerInterface


@dataclass
class PaperPosition:
    symbol: str
    size: int
    avg_cost: float


class PaperBroker(BrokerInterface):
    """模拟交易券商，可用于实盘前验证"""

    def __init__(self, initial_cash: float = INITIAL_CAPITAL):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions: dict[str, PaperPosition] = {}
        self.orders: list[dict] = []

    def buy(self, symbol: str, price: float, size: int) -> dict | None:
        fill_price = price * (1 + SLIPPAGE)
        cost = fill_price * size
        commission = max(cost * COMMISSION_RATE, 5.0)
        total = cost + commission
        if total > self.cash:
            return None
        self.cash -= total
        if symbol in self.positions:
            pos = self.positions[symbol]
            old_cost = pos.avg_cost * pos.size
            pos.size += size
            pos.avg_cost = (old_cost + cost) / pos.size
        else:
            self.positions[symbol] = PaperPosition(symbol=symbol, size=size, avg_cost=fill_price)
        order = {"symbol": symbol, "action": "buy", "price": fill_price, "size": size, "commission": commission}
        self.orders.append(order)
        return order

    def sell(self, symbol: str, price: float, size: int) -> dict | None:
        pos = self.positions.get(symbol)
        if not pos or pos.size < size:
            return None
        fill_price = price * (1 - SLIPPAGE)
        revenue = fill_price * size
        commission = max(revenue * COMMISSION_RATE, 5.0)
        pnl = (fill_price - pos.avg_cost) * size - commission
        self.cash += revenue - commission
        pos.size -= size
        if pos.size == 0:
            del self.positions[symbol]
        order = {"symbol": symbol, "action": "sell", "price": fill_price, "size": size, "commission": commission, "pnl": pnl}
        self.orders.append(order)
        return order

    def get_position(self, symbol: str) -> dict:
        pos = self.positions.get(symbol)
        if not pos:
            return {"symbol": symbol, "size": 0, "avg_cost": 0}
        return {"symbol": pos.symbol, "size": pos.size, "avg_cost": pos.avg_cost}

    def get_account(self) -> dict:
        return {"cash": self.cash, "initial_cash": self.initial_cash, "total_return_pct": (self.cash / self.initial_cash - 1) * 100}
