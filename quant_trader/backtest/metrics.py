import numpy as np
import pandas as pd


def compute_metrics(equity_curve: pd.Series, trades: list, risk_free_rate: float = 0.03) -> dict:
    """计算回测绩效指标"""
    if equity_curve.empty or len(equity_curve) < 2:
        return {}

    returns = equity_curve.pct_change().dropna()
    if returns.empty:
        return {}

    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    years = (equity_curve.index[-1] - equity_curve.index[0]).days / 365.25
    years = max(years, 1 / 252)
    cagr = (1 + total_return) ** (1 / years) - 1

    annual_vol = returns.std() * np.sqrt(252)
    sharpe = (cagr - risk_free_rate) / annual_vol if annual_vol > 0 else 0

    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # Calmar ratio
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    # Win rate
    win_trades = [t for t in trades if t.pnl > 0]
    loss_trades = [t for t in trades if t.pnl < 0]
    win_rate = len(win_trades) / len(trades) if trades else 0

    avg_win = np.mean([t.pnl for t in win_trades]) if win_trades else 0
    avg_loss = np.mean([t.pnl for t in loss_trades]) if loss_trades else 0
    profit_factor = abs(sum(t.pnl for t in win_trades) / sum(t.pnl for t in loss_trades)) if loss_trades else float("inf")

    return {
        "total_return": round(total_return * 100, 2),
        "cagr": round(cagr * 100, 2),
        "annual_volatility": round(annual_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "calmar_ratio": round(calmar, 2),
        "total_trades": len(trades),
        "win_rate": round(win_rate * 100, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "N/A",
    }
