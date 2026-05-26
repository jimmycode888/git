from dataclasses import dataclass, field

from config.settings import COMMISSION_RATE, SLIPPAGE, INITIAL_CAPITAL


@dataclass
class Trade:
    date: str
    symbol: str
    action: str
    price: float
    size: int
    commission: float
    pnl: float = 0.0


@dataclass
class Position:
    symbol: str
    size: int
    avg_cost: float


class Broker:
    """模拟券商：处理成交、佣金、滑点"""

    def __init__(
        self,
        initial_cash: float = INITIAL_CAPITAL,
        commission_rate: float = COMMISSION_RATE,
        slippage: float = SLIPPAGE,
    ):
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.cash = initial_cash
        self.position = Position(symbol="", size=0, avg_cost=0.0)
        self.trades: list[Trade] = []

    def apply_slippage(self, price: float, is_buy: bool) -> float:
        if is_buy:
            return price * (1 + self.slippage)
        return price * (1 - self.slippage)

    def buy(self, symbol: str, price: float, size: int, date: str) -> Trade | None:
        fill_price = self.apply_slippage(price, is_buy=True)
        max_affordable = int(self.cash / (fill_price * (1 + self.commission_rate)) - 1)
        size = min(size, max_affordable)
        if size <= 0:
            return None
        cost = fill_price * size
        commission = max(cost * self.commission_rate, 5.0)
        self.cash -= cost + commission
        old_total_cost = self.position.avg_cost * self.position.size
        self.position.size += size
        self.position.avg_cost = (old_total_cost + cost) / self.position.size if self.position.size else 0
        self.position.symbol = symbol
        trade = Trade(date=date, symbol=symbol, action="buy", price=fill_price, size=size, commission=commission)
        self.trades.append(trade)
        return trade

    def sell(self, price: float, size: int, date: str) -> Trade | None:
        if size > self.position.size:
            size = self.position.size
        if size == 0:
            return None
        fill_price = self.apply_slippage(price, is_buy=False)
        revenue = fill_price * size
        commission = max(revenue * self.commission_rate, 5.0)
        pnl = (fill_price - self.position.avg_cost) * size - commission
        self.cash += revenue - commission
        self.position.size -= size
        if self.position.size == 0:
            self.position.avg_cost = 0
        trade = Trade(
            date=date,
            symbol=self.position.symbol,
            action="sell",
            price=fill_price,
            size=size,
            commission=commission,
            pnl=pnl,
        )
        self.trades.append(trade)
        return trade

    @property
    def equity(self) -> float:
        pos_value = self.position.size * self.position.avg_cost
        return self.cash + pos_value
