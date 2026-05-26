import pandas as pd
from strategy.base import Strategy, Context, Signal, Action


class RSIMeanRevertStrategy(Strategy):
    """RSI均值回归策略：RSI<30超卖买入，RSI>70超买卖出"""

    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70, lots: int = 100):
        super().__init__(name=f"RSI_{rsi_period}")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.lots = lots

    def on_bar(self, row, ctx: Context) -> Signal:
        close = row["close"]
        rsi_val = row.get(f"rsi_{self.rsi_period}")
        if rsi_val is None or pd.isna(rsi_val):
            return Signal(Action.HOLD)

        if rsi_val < self.oversold and ctx.position == 0:
            return Signal(Action.BUY, size=self.lots, price=close, reason=f"RSI超卖({rsi_val:.1f})")
        if rsi_val > self.overbought and ctx.position > 0:
            return Signal(Action.SELL, size=ctx.position, price=close, reason=f"RSI超买({rsi_val:.1f})")

        return Signal(Action.HOLD)
