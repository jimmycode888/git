"""
量化交易系统 CLI 入口

用法:
  python main.py fetch --symbol 600519        # 下载数据
  python main.py backtest --symbol 600519      # 运行回测
  python main.py dashboard                     # 启动Web看板
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from datetime import date, timedelta

from data.manager import DataManager
from data.sources.akshare import AKShareSource
from data.storage import Storage
from backtest.engine import BacktestEngine
from strategy.examples.ma_cross import MACrossStrategy
from strategy.examples.rsi_mean_revert import RSIMeanRevertStrategy


def cmd_fetch(symbol: str, days: int = 365):
    """下载历史数据到本地"""
    dm = DataManager(AKShareSource(), Storage())
    end = date.today()
    start = end - timedelta(days=days)
    print(f"正在下载 {symbol} 历史数据...")
    df = dm.get_daily(symbol, start=start, end=end, refresh=True)
    if df.empty:
        print(f"下载失败，未获取到 {symbol} 的数据")
        return
    print(f"已存储 {len(df)} 条记录 ({df['date'].iloc[0]} ~ {df['date'].iloc[-1]})")
    print(f"最新收盘价: {df['close'].iloc[-1]}")


def cmd_backtest(symbol: str, strategy: str = "ma_cross", fast: int = 5, slow: int = 20, days: int = 365, lots: int = 100):
    """运行策略回测"""
    dm = DataManager(AKShareSource(), Storage())

    if strategy == "ma_cross":
        strat = MACrossStrategy(fast=fast, slow=slow, lots=lots)
        indicators = [f"sma_{fast}", f"sma_{slow}"]
    elif strategy == "rsi":
        strat = RSIMeanRevertStrategy(lots=lots)
        indicators = ["rsi_14"]
    else:
        print(f"未知策略: {strategy}")
        print(f"可用策略: ma_cross, rsi")
        return

    end = date.today()
    start = end - timedelta(days=days)

    engine = BacktestEngine(dm, strat)
    result = engine.run(symbol, start=start, end=end, indicators=indicators)

    if "error" in result:
        print(f"回测失败: {result['error']}")
        return

    print(f"\n{'='*50}")
    print(f"策略回测报告")
    print(f"{'='*50}")
    print(f"标的: {result['symbol']}")
    print(f"策略: {result['strategy']}")
    print(f"{'='*50}")

    m = result["metrics"]
    labels = {
        "total_return": "总收益率",
        "cagr": "年化收益率",
        "annual_volatility": "年化波动率",
        "sharpe_ratio": "夏普比率",
        "max_drawdown": "最大回撤",
        "calmar_ratio": "Calmar比率",
        "total_trades": "交易次数",
        "win_rate": "胜率",
        "avg_win": "平均盈利",
        "avg_loss": "平均亏损",
        "profit_factor": "盈亏比",
    }
    for key, label in labels.items():
        val = m.get(key, "N/A")
        suffix = "%" if key in ("total_return", "cagr", "annual_volatility", "max_drawdown", "win_rate") else ""
        print(f"  {label}: {val}{suffix}")


def cmd_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """启动Web看板"""
    from dashboard.app import app
    import uvicorn

    print(f"量化交易看板启动: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="量化交易系统")
    sub = parser.add_subparsers(dest="command")

    p_fetch = sub.add_parser("fetch", help="下载数据")
    p_fetch.add_argument("--symbol", default="600519", help="股票代码")
    p_fetch.add_argument("--days", type=int, default=365, help="下载天数")

    p_bt = sub.add_parser("backtest", help="运行回测")
    p_bt.add_argument("--symbol", default="600519", help="股票代码")
    p_bt.add_argument("--strategy", default="ma_cross", help="策略名称 (ma_cross / rsi)")
    p_bt.add_argument("--fast", type=int, default=5, help="快线周期")
    p_bt.add_argument("--slow", type=int, default=20, help="慢线周期")
    p_bt.add_argument("--days", type=int, default=365, help="回测天数")
    p_bt.add_argument("--lots", type=int, default=100, help="交易手数")

    p_dash = sub.add_parser("dashboard", help="启动Web看板")
    p_dash.add_argument("--host", default="127.0.0.1", help="监听地址")
    p_dash.add_argument("--port", type=int, default=8000, help="监听端口")

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args.symbol, args.days)
    elif args.command == "backtest":
        cmd_backtest(args.symbol, args.strategy, args.fast, args.slow, args.days, args.lots)
    elif args.command == "dashboard":
        cmd_dashboard(args.host, args.port)
    else:
        parser.print_help()
