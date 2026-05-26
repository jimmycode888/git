from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from data.manager import DataManager
from data.sources.akshare import AKShareSource
from data.storage import Storage
from backtest.engine import BacktestEngine
from strategy.examples.ma_cross import MACrossStrategy
from strategy.examples.rsi_mean_revert import RSIMeanRevertStrategy

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="量化交易系统")

app.mount("/static", __import__("fastapi.staticfiles").staticfiles.StaticFiles(directory=str(STATIC_DIR)), name="static")

jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), cache_size=0)


def render(name: str, **ctx) -> HTMLResponse:
    template = jinja_env.get_template(name)
    return HTMLResponse(template.render(**ctx))


source = AKShareSource()
storage = Storage()
dm = DataManager(source=source, storage=storage)

STRATEGIES = {
    "ma_cross": MACrossStrategy,
    "rsi_revert": RSIMeanRevertStrategy,
}


@app.get("/", response_class=HTMLResponse)
def index():
    return render("index.html")


@app.get("/backtest", response_class=HTMLResponse)
def backtest_page():
    return render("backtest.html", strategies=list(STRATEGIES.keys()))


@app.get("/api/backtest/run")
def api_backtest_run(
    symbol: str = Query(default="600519"),
    strategy: str = Query(default="ma_cross"),
    fast: int = Query(default=5),
    slow: int = Query(default=20),
    days: int = Query(default=365),
):
    strat_cls = STRATEGIES.get(strategy)
    if not strat_cls:
        return {"error": f"未知策略: {strategy}"}

    if strategy == "ma_cross":
        strat = strat_cls(fast=fast, slow=slow, lots=100)
        indicators = [f"sma_{fast}", f"sma_{slow}"]
    elif strategy == "rsi_revert":
        strat = strat_cls(rsi_period=14, lots=100)
        indicators = ["rsi_14"]
    else:
        return {"error": "不支持的策略"}

    end = date.today()
    start = end - timedelta(days=days)

    engine = BacktestEngine(dm, strat)
    result = engine.run(symbol, start=start, end=end, indicators=indicators)
    return result


@app.get("/api/data/info")
def api_data_info(symbol: str = Query(default="600519")):
    end = date.today()
    start = end - timedelta(days=30)
    df = dm.get_daily(symbol, start=start, end=end, refresh=True)
    if df.empty:
        return {"error": "无数据"}
    latest = df.iloc[-1]
    return {
        "symbol": symbol,
        "latest_date": str(latest["date"].date()) if hasattr(latest["date"], "date") else str(latest["date"]),
        "latest_close": float(latest["close"]),
        "count": len(df),
    }


@app.get("/api/equity")
def api_equity(symbol: str = Query(default="600519"), days: int = Query(default=365)):
    end = date.today()
    start = end - timedelta(days=days)
    df = dm.get_daily(symbol, start=start, end=end)
    if df.empty:
        return []
    data = []
    for _, row in df.iterrows():
        data.append({
            "date": str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"]),
            "close": float(row["close"]),
        })
    return data
