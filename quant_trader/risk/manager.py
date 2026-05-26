from dataclasses import dataclass

from strategy.base import Signal, Action, Context
from config.settings import RISK_PER_TRADE


@dataclass
class RiskRule:
    name: str
    description: str

    def check(self, signal: Signal, ctx: Context) -> tuple[bool, str]:
        """返回 (通过, 原因)"""
        return True, ""


class MaxPositionSize(RiskRule):
    """单笔最大仓位限制"""

    def __init__(self, max_pct: float = 0.25):
        super().__init__(
            name="max_position_size",
            description=f"单笔不超过{max_pct*100}%总资金",
        )
        self.max_pct = max_pct

    def check(self, signal: Signal, ctx: Context) -> tuple[bool, str]:
        if signal.action != Action.BUY:
            return True, ""
        trade_value = (signal.price or ctx.current_price) * signal.size
        if trade_value > ctx.total_value * self.max_pct:
            return False, f"超单笔仓位限制({self.max_pct*100}%)"
        return True, ""


class MaxDrawdownStop(RiskRule):
    """回撤熔断"""

    def __init__(self, max_dd_pct: float = 0.20):
        super().__init__(
            name="max_drawdown_stop",
            description=f"回撤超过{max_dd_pct*100}%中止交易",
        )
        self.max_dd_pct = max_dd_pct
        self.peak_value = 0.0

    def check(self, signal: Signal, ctx: Context) -> tuple[bool, str]:
        if ctx.total_value > self.peak_value:
            self.peak_value = ctx.total_value
        if self.peak_value > 0:
            dd = (self.peak_value - ctx.total_value) / self.peak_value
            if dd > self.max_dd_pct:
                return False, f"回撤熔断({dd*100:.1f}% > {self.max_dd_pct*100}%)"
        return True, ""


class StopLoss(RiskRule):
    """固定止损"""

    def __init__(self, stop_pct: float = 0.05):
        super().__init__(
            name="stop_loss",
            description=f"亏损{stop_pct*100}%止损",
        )
        self.stop_pct = stop_pct

    def check(self, signal: Signal, ctx: Context) -> tuple[bool, str]:
        if signal.action != Action.SELL:
            return True, ""
        if ctx.position > 0 and ctx.avg_cost > 0:
            loss_pct = (ctx.current_price - ctx.avg_cost) / ctx.avg_cost
            if loss_pct <= -self.stop_pct:
                return True, ""  # 止损单总是通过
        return True, ""


class RiskManager:
    """风险管理器：组合多条风控规则"""

    def __init__(self, rules: list[RiskRule] | None = None):
        self.rules = rules or [
            MaxPositionSize(0.25),
            MaxDrawdownStop(0.20),
        ]

    def check(self, signal: Signal, ctx: Context) -> tuple[bool, str]:
        for rule in self.rules:
            passed, reason = rule.check(signal, ctx)
            if not passed:
                return False, f"[{rule.name}] {reason}"
        return True, "OK"
