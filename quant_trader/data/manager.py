from datetime import date

import pandas as pd

from .sources.base import DataSource
from .storage import Storage


class DataManager:
    """数据管理器：统筹数据获取、缓存、存储"""

    def __init__(self, source: DataSource, storage: Storage | None = None):
        self.source = source
        self.storage = storage or Storage()

    def get_daily(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        refresh: bool = False,
    ) -> pd.DataFrame:
        if not refresh:
            cached = self.storage.load_daily(
                symbol,
                start=str(start) if start else None,
                end=str(end) if end else None,
            )
            if not cached.empty:
                return cached

        df = self.source.get_daily(symbol, start, end)
        if not df.empty:
            self.storage.save_daily(symbol, df)
        return df
