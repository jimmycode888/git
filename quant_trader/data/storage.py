import sqlite3

import pandas as pd

from config.settings import DB_PATH


class Storage:
    """SQLite本地存储，管理行情数据"""

    def __init__(self, db_path: str | None = None):
        self.db_path = str(db_path or DB_PATH)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (symbol, date)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS instruments (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    market TEXT,
                    type TEXT
                )
            """)
            conn.commit()

    def save_daily(self, symbol: str, df: pd.DataFrame):
        if df.empty:
            return
        df = df.copy()
        df["symbol"] = symbol
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            for _, row in df.iterrows():
                conn.execute(
                    """INSERT OR REPLACE INTO daily_prices
                       (symbol, date, open, high, low, close, volume)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (symbol, row["date"], row.get("open"), row.get("high"),
                     row.get("low"), row.get("close"), row.get("volume")),
                )
            conn.commit()

    def load_daily(self, symbol: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        query = "SELECT date, open, high, low, close, volume FROM daily_prices WHERE symbol = ?"
        params = [symbol]
        if start:
            query += " AND date >= ?"
            params.append(start)
        if end:
            query += " AND date <= ?"
            params.append(end)
        query += " ORDER BY date ASC"
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
        df["date"] = pd.to_datetime(df["date"])
        return df
