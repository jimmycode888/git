from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum

import pandas as pd


class Market(Enum):
    A_SHARE = "a_share"
    CRYPTO = "crypto"
    US_STOCK = "us_stock"
    FUTURE = "future"


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MINUTE = "minute"


@dataclass
class Instrument:
    symbol: str
    name: str
    market: Market
    type: str  # stock, etf, index, future


class DataSource(ABC):
    """数据源抽象基类，所有数据源实现统一接口"""

    @abstractmethod
    def get_daily(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> pd.DataFrame:
        """获取日线数据，返回列: date, open, high, low, close, volume"""
        ...

    @abstractmethod
    def get_instruments(self, market: Market) -> list[Instrument]:
        """获取可交易标的列表"""
        ...

    def get_realtime(self, symbol: str) -> dict | None:
        """获取实时行情，可选实现"""
        return None
