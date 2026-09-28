"""
週報常數與板塊對照表
"""
from datetime import datetime, timedelta

# ── 板塊 ETF 對照表 ──
SECTOR_ETFS = {
    "XLE":  "能源",
    "XLU":  "公用事業",
    "XLB":  "原物料",
    "XLP":  "必需消費品",
    "XLI":  "工業",
    "XLRE": "房地產",
    "XLC":  "通訊服務",
    "XLV":  "醫療保健",
    "XLK":  "科技",
    "XLY":  "非必需消費品",
    "XLF":  "金融",
}

# ── 市場概覽指標 ──
# 前 3 格固定，後 3 格由 CC 根據當週市場熱度從 FLEX_TICKERS 中選 3 個
FIXED_TICKERS = {
    "^GSPC": {"label": "S&P 500",  "tmpl_val": "SP500", "tmpl_chg": "SP500_CHG", "tmpl_dir": "SP500_DIR"},
    "^IXIC": {"label": "Nasdaq",   "tmpl_val": "NDX",   "tmpl_chg": "NDX_CHG",   "tmpl_dir": "NDX_DIR"},
    "^N225": {"label": "日經 225",  "tmpl_val": "NKY",   "tmpl_chg": "NKY_CHG",   "tmpl_dir": "NKY_DIR"},
}

FLEX_TICKERS = {
    "CL=F":    {"label": "WTI 原油",     "tmpl_val": "OIL",   "tmpl_chg": "OIL_CHG",   "tmpl_dir": "OIL_DIR"},
    "GC=F":    {"label": "黃金",         "tmpl_val": "GOLD",  "tmpl_chg": "GOLD_CHG",  "tmpl_dir": "GOLD_DIR"},
    "^VIX":    {"label": "VIX",          "tmpl_val": "VIX",   "tmpl_chg": "VIX_NOTE",  "tmpl_dir": "VIX_NOTE"},
    "^DJI":    {"label": "Dow Jones",    "tmpl_val": "DJI",   "tmpl_chg": "DJI_CHG",   "tmpl_dir": "DJI_DIR"},
    "^TNX":    {"label": "10Y 殖利率",   "tmpl_val": "TNX",   "tmpl_chg": "TNX_CHG",   "tmpl_dir": "TNX_DIR"},
    "DX-Y.NYB":{"label": "美元指數",     "tmpl_val": "DXY",   "tmpl_chg": "DXY_CHG",   "tmpl_dir": "DXY_DIR"},
    "BTC-USD": {"label": "Bitcoin",      "tmpl_val": "BTC",   "tmpl_chg": "BTC_CHG",   "tmpl_dir": "BTC_DIR"},
}

# 預設後 3 格（CC 可覆蓋）
DEFAULT_FLEX_PICKS = ["CL=F", "GC=F", "^VIX"]

# 合併用（fetch_data.py 會抓全部 FIXED + 選中的 FLEX）
MARKET_TICKERS = {**FIXED_TICKERS, **{k: v for k, v in FLEX_TICKERS.items() if k in DEFAULT_FLEX_PICKS}}

# ── U.S. Equity Watchlist example (generic market observation only) ──
TRACKED_STOCKS = [
    {"ticker": "SPY", "name": "Broad market ETF", "is_etf": True},
    {"ticker": "QQQ", "name": "Large-cap growth ETF", "is_etf": True},
    {"ticker": "XLK", "name": "Technology sector ETF", "is_etf": True},
    {"ticker": "XLF", "name": "Financial sector ETF", "is_etf": True},
    {"ticker": "XLE", "name": "Energy sector ETF", "is_etf": True},
]

# ── VIX 門檻 ──
VIX_HIGH_THRESHOLD = 20

# ── 輸出設定 ──
OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"


def get_week_dates():
    """取得最近一個完整交易週的週五日期（本週五與上週五）"""
    today = datetime.now()
    # 找到最近的週五（含今天）
    days_since_friday = (today.weekday() - 4) % 7
    this_friday = today - timedelta(days=days_since_friday)
    last_friday = this_friday - timedelta(days=7)
    return last_friday.date(), this_friday.date()


def get_week_number(date):
    """取得 ISO 週次"""
    return date.isocalendar()[1]


def format_date_main(date):
    """格式化日期：2026年3月20日"""
    return f"{date.year}年{date.month}月{date.day}日"


def format_date_sub(date):
    """格式化副標日期：第12週｜3月16—20日"""
    week_num = get_week_number(date)
    monday = date - timedelta(days=date.weekday())
    friday = monday + timedelta(days=4)
    return f"第{week_num}週｜{monday.month}月{monday.day}—{friday.day}日"
