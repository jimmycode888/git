from datetime import date, timedelta

import pandas as pd

from .base import DataSource, Instrument, Market


class AKShareSource(DataSource):
    """AKShare数据源，支持A股、指数、期货"""

    def get_daily(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> pd.DataFrame:
        import time
        import akshare as ak

        if end is None:
            end = date.today()
        if start is None:
            start = end - timedelta(days=365)

        all_dfs = []
        chunk_start = start
        max_retries = 3

        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=90), end)

            for attempt in range(max_retries):
                try:
                    df = ak.stock_zh_a_hist(
                        symbol=symbol,
                        period="daily",
                        start_date=chunk_start.strftime("%Y%m%d"),
                        end_date=chunk_end.strftime("%Y%m%d"),
                        adjust="qfq",
                    )
                    if not df.empty:
                        all_dfs.append(df)
                    break
                except Exception:
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                    else:
                        pass

            chunk_start = chunk_end + timedelta(days=1)

        if not all_dfs:
            return pd.DataFrame()

        df = pd.concat(all_dfs, ignore_index=True)
        df = df.drop_duplicates(subset=["日期"])

        df = df.rename(
            columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }
        )
        df["date"] = pd.to_datetime(df["date"])
        cols = ["date", "open", "high", "low", "close", "volume"]
        return df[[c for c in cols if c in df.columns]].sort_values("date")

    def get_instruments(self, market: Market) -> list[Instrument]:
        result = []
        if market == Market.A_SHARE:
            import akshare as ak

            try:
                df = ak.stock_zh_a_spot_em()
                for _, row in df.head(500).iterrows():
                    result.append(
                        Instrument(
                            symbol=row["代码"],
                            name=row["名称"],
                            market=Market.A_SHARE,
                            type="stock",
                        )
                    )
            except Exception:
                pass
        return result
