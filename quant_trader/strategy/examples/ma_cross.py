import pandas as pd
from strategy.base import Strategy, Context, Signal, Action
from strategy.signals import sma


class MACrossStrategy(Strategy):
    """双均线策略：短期均线上穿长期均线买入，下穿卖出"""

    def __init__(self, fast: int = 5, slow: int = 20, lots: int = 100):
        super().__init__(name=f"MA_Cross_{fast}_{slow}")
        self.fast = fast
        self.slow = slow
        self.lots = lots
        self._prev_fast = None
        self._prev_slow = None

    def on_bar(self, row, ctx: Context) -> Signal:
        close = row["close"]
        # 这里需要外部计算好均线值传入，在回测引擎中预处理
        fast_ma = row.get(f"ma_{self.fast}")
        slow_ma = row.get(f"ma_{self.slow}")
        if fast_ma is None or slow_ma is None or pd.isna(fast_ma) or pd.isna(slow_ma):
            return Signal(Action.HOLD)

        prev_fast = self._prev_fast
        prev_slow = self._prev_slow
        self._prev_fast = fast_ma
        self._prev_slow = slow_ma

        if prev_fast is None:
            return Signal(Action.HOLD)

        # 金叉：快线上穿慢线
        if prev_fast <= prev_slow and fast_ma > slow_ma and ctx.position == 0:
            return Signal(Action.BUY, size=self.lots, price=close, reason="金叉买入")
        # 死叉：快线下穿慢线
        if prev_fast >= prev_slow and fast_ma < slow_ma and ctx.position > 0:
            return Signal(Action.SELL, size=ctx.position, price=close, reason="死叉卖出")

        return Signal(Action.HOLD)

    def reset(self):
        self._prev_fast = None
        self._prev_slow = None
