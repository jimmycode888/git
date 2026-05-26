from datetime import date

import pandas as pd
import numpy as np

from config.settings import INITIAL_CAPITAL
from data.manager import DataManager
from strategy.base import Strategy, Context, Action
from strategy.signals import sma, ema, rsi, macd, bollinger_bands
from .broker import Broker
from .metrics import compute_metrics


class BacktestEngine:
    """事件驱动回测引擎"""

    def __init__(
        self,
        data_manager: DataManager,
        strategy: Strategy,
        initial_cash: float = INITIAL_CAPITAL,
    ):
        self.data_manager = data_manager
        self.strategy = strategy
        self.broker = Broker(initial_cash=initial_cash)
        self.equity_curve: list[dict] = []

    def run(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        indicators: list[str] | None = None,
    ) -> dict:
        self.strategy.reset()
        self.broker = Broker(initial_cash=self.broker.initial_cash)
        self.equity_curve = []

        # 加载数据
        df = self.data_manager.get_daily(symbol, start, end)
        if df.empty:
            return {"error": "没有获取到数据"}

        # 预计算指标
        close = df["close"]
        if indicators is None:
            indicators = []
        df = self._precompute_indicators(df, close, indicators)

        # 回测主循环
        for _, row in df.iterrows():
            price = row["close"]
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])

            ctx = Context(
                cash=self.broker.cash,
                position=self.broker.position.size,
                avg_cost=self.broker.position.avg_cost,
                current_price=price,
            )

            signal = self.strategy.on_bar(row, ctx)

            if signal.action == Action.BUY and signal.size > 0:
                trade = self.broker.buy(symbol, signal.price or price, signal.size, date_str)
                if trade:
                    self.strategy.on_trade(signal, trade.price)
            elif signal.action == Action.SELL and signal.size > 0:
                trade = self.broker.sell(signal.price or price, signal.size, date_str)
                if trade:
                    self.strategy.on_trade(signal, trade.price)

            self.equity_curve.append({
                "date": date_str,
                "equity": self.broker.equity,
                "position": self.broker.position.size,
            })

        equity_df = pd.DataFrame(self.equity_curve)
        equity_df["date"] = pd.to_datetime(equity_df["date"])
        equity_series = equity_df.set_index("date")["equity"]

        metrics = compute_metrics(equity_series, self.broker.trades)

        return {
            "symbol": symbol,
            "strategy": self.strategy.name,
            "metrics": metrics,
            "equity_curve": equity_df.to_dict("records"),
            "trades": [
                {
                    "date": t.date,
                    "action": t.action,
                    "price": round(t.price, 2),
                    "size": t.size,
                    "commission": round(t.commission, 2),
                    "pnl": round(t.pnl, 2),
                }
                for t in self.broker.trades
            ],
        }

    def _precompute_indicators(self, df: pd.DataFrame, close: pd.Series, indicators: list[str]) -> pd.DataFrame:
        df = df.copy()
        for ind in indicators:
            if ind.startswith("sma_"):
                period = int(ind.split("_")[1])
                df[f"ma_{period}"] = sma(close, period)
            elif ind.startswith("ema_"):
                period = int(ind.split("_")[1])
                df[f"ema_{period}"] = ema(close, period)
            elif ind.startswith("rsi_"):
                period = int(ind.split("_")[1])
                df[f"rsi_{period}"] = rsi(close, period)
            elif ind == "macd":
                macd_df = macd(close)
                df["macd"] = macd_df["macd"]
                df["macd_signal"] = macd_df["signal"]
                df["macd_hist"] = macd_df["histogram"]
            elif ind.startswith("bb_"):
                parts = ind.split("_")
                period = int(parts[1]) if len(parts) > 1 else 20
                std = float(parts[2]) if len(parts) > 2 else 2.0
                bb = bollinger_bands(close, period, std)
                df["bb_middle"] = bb["middle"]
                df["bb_upper"] = bb["upper"]
                df["bb_lower"] = bb["lower"]
        return df
