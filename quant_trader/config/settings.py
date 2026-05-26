from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data_storage"
DB_PATH = DATA_DIR / "market.db"

COMMISSION_RATE = 0.0003  # 万分之三
SLIPPAGE = 0.001          # 0.1% 滑点
INITIAL_CAPITAL = 100_000
RISK_PER_TRADE = 0.02     # 单笔最大亏损2%

DATA_DIR.mkdir(exist_ok=True)
