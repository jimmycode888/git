from abc import ABC, abstractmethod


class BrokerInterface(ABC):
    """交易接口抽象，真实交易和模拟交易均实现此接口"""

    @abstractmethod
    def buy(self, symbol: str, price: float, size: int) -> dict | None:
        ...

    @abstractmethod
    def sell(self, symbol: str, price: float, size: int) -> dict | None:
        ...

    @abstractmethod
    def get_position(self, symbol: str) -> dict:
        ...

    @abstractmethod
    def get_account(self) -> dict:
        ...
