from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class Action(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    action: Action
    size: int = 0
    price: float | None = None
    reason: str = ""


@dataclass
class Context:
    """策略上下文：当前持仓、现金等"""
    cash: float = 0.0
    position: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def market_value(self) -> float:
        return self.position * self.current_price

    @property
    def total_value(self) -> float:
        return self.cash + self.market_value


class Strategy(ABC):
    """策略基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def on_bar(self, row, ctx: Context) -> Signal:
        """接收一根K线，返回交易信号"""
        ...

    def on_trade(self, signal: Signal, fill_price: float):
        """成交回调"""
        pass

    def reset(self):
        """重置策略状态"""
        pass
