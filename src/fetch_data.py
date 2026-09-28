"""
週報數據抓取器
用法：python src/fetch_data.py [--date YYYY-MM-DD]

功能：
  1. yfinance 抓取市場指數 + 板塊 ETF 的週漲跌幅（精確數值）
  2. 輸出 JSON 骨架，其中新聞/情緒/日程欄位留空（macro 為舊版相容欄位）
  3. Claude Code 用 web search 補充文字內容後，再跑 build_report.py

輸出：output/weekly_data_{YYYYMMDD}.json
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 加入 src/ 到 path
sys.path.insert(0, str(Path(__file__).parent))
from config import SECTOR_ETFS, FIXED_TICKERS, FLEX_TICKERS, DEFAULT_FLEX_PICKS, VIX_HIGH_THRESHOLD, OUTPUT_DIR, TRACKED_STOCKS, get_week_dates, format_date_main, format_date_sub

try:
    import yfinance as yf
except ImportError:
    print("[ERROR] 請先安裝 yfinance: pip install yfinance")
    sys.exit(1)


def fetch_weekly_change(ticker: str, start_date, end_date) -> dict:
    """抓取指定 ticker 在兩個日期之間的收盤價與漲跌幅"""
    try:
        # 多抓幾天以確保涵蓋交易日
        fetch_start = start_date - timedelta(days=5)
        fetch_end = end_date + timedelta(days=3)

        data = yf.download(
            ticker,
            start=fetch_start.isoformat(),
            end=fetch_end.isoformat(),
            progress=False,
            auto_adjust=True,
        )

        if data.empty:
            return {"error": f"無數據: {ticker}"}

        # 處理 MultiIndex columns（yfinance 有時會返回 MultiIndex）
        if hasattr(data.columns, 'levels'):
            data.columns = data.columns.get_level_values(0)

        # Yahoo 偶爾會先建立尚未填入價格的最新交易日列；若不移除，
        # 週末製作報告時會把最後一列 NaN 當成最新收盤價。
        close = data["Close"].dropna()

        if close.empty:
            return {"error": f"無有效收盤價: {ticker}"}

        # 找最接近 start_date 和 end_date 的交易日
        dates_available = close.index

        prev_close = None
        curr_close = None

        for d in sorted(dates_available):
            d_date = d.date() if hasattr(d, 'date') else d
            if d_date <= start_date:
                prev_close = float(close.loc[d])
                prev_date = d_date
            if d_date <= end_date:
                curr_close = float(close.loc[d])
                curr_date = d_date

        if prev_close is None or curr_close is None:
            return {"error": f"找不到交易日數據: {ticker}"}

        pct_change = (curr_close - prev_close) / prev_close * 100

        return {
            "ticker": ticker,
            "prev_close": round(prev_close, 2),
            "prev_date": str(prev_date),
            "curr_close": round(curr_close, 2),
            "curr_date": str(curr_date),
            "pct_change": round(pct_change, 2),
        }
    except Exception as e:
        return {"error": f"{ticker}: {str(e)}"}


def fetch_all_data(end_date=None, start_date=None):
    """抓取所有週報需要的數值數據"""

    last_fri, this_fri = get_week_dates()
    if end_date:
        this_fri = end_date
        last_fri = this_fri - timedelta(days=7)
    if start_date:
        last_fri = start_date

    print(f"[數據期間] {last_fri} → {this_fri}")
    print()

    # ── 1. 市場概覽（固定 3 + 全部彈性候選）──
    print("[1/2] 抓取市場概覽指標...")
    market_data = {}
    ALL_MARKET = {**FIXED_TICKERS, **FLEX_TICKERS}

    for ticker, info in ALL_MARKET.items():
        result = fetch_weekly_change(ticker, last_fri, this_fri)
        result["label"] = info["label"]
        result["tmpl_val"] = info["tmpl_val"]
        result["tmpl_chg"] = info["tmpl_chg"]
        result["tmpl_dir"] = info["tmpl_dir"]
        result["is_fixed"] = ticker in FIXED_TICKERS
        market_data[ticker] = result

        tag = "★" if ticker in FIXED_TICKERS else "○"
        if "error" not in result:
            direction = "▲" if result["pct_change"] >= 0 else "▼"
            print(f"  {tag} {info['label']:12s} {result['curr_close']:>10,.2f}  {direction} {result['pct_change']:+.2f}%")
        else:
            print(f"  {tag} {info['label']:12s}  {result['error']}")

    print()

    # ── 2. 板塊 ETF（11 個）──
    print("[2/2] 抓取板塊 ETF...")
    sector_data = {}

    for etf, name_zh in SECTOR_ETFS.items():
        result = fetch_weekly_change(etf, last_fri, this_fri)
        result["name_zh"] = name_zh
        sector_data[etf] = result

        if "error" not in result:
            direction = "▲" if result["pct_change"] >= 0 else "▼"
            print(f"  {name_zh:6s} ({etf:4s})  {result['curr_close']:>8.2f}  {direction} {result['pct_change']:+.2f}%")
        else:
            print(f"  {name_zh:6s} ({etf:4s})  {result['error']}")

    # ── 排序板塊 ──
    valid_sectors = {k: v for k, v in sector_data.items() if "error" not in v}
    sorted_sectors = sorted(valid_sectors.items(), key=lambda x: x[1]["pct_change"], reverse=True)

    top3_up = sorted_sectors[:3]
    top3_dn = sorted_sectors[-3:][::-1]  # 最差的 3 個，由小到大反轉

    print()
    print("▲ 漲幅前三：", " | ".join(f"{v['name_zh']} {v['pct_change']:+.2f}%" for _, v in top3_up))
    print("▼ 跌幅前三：", " | ".join(f"{v['name_zh']} {v['pct_change']:+.2f}%" for _, v in top3_dn))

    # ── 3. 美股觀察清單 ──
    print("[3/3] 抓取美股觀察清單...")

    # 日期邏輯：週一報 → 上週五收盤；其他 → 昨日收盤
    today = datetime.now().date() if not end_date else end_date
    weekday = today.weekday()  # 0=Mon
    # 找「追蹤期間基準點」（prev）= 上上個交易結束日
    if start_date:
        track_prev = start_date
        track_curr = this_fri
    elif weekday == 0:  # 週一：prev=上上週五, curr=上週五
        track_prev = this_fri - timedelta(days=7)
        track_curr = this_fri
    else:             # 其他：prev=上週五, curr=昨日
        track_prev = last_fri
        days_back = 1 if weekday > 1 else 3  # 週一前一天是週五
        track_curr = today - timedelta(days=1)

    print(f"  追蹤期間：{track_prev} → {track_curr}")

    tracked_stocks_data = []
    for stock in TRACKED_STOCKS:
        t = stock["ticker"]
        result = fetch_weekly_change(t, track_prev, track_curr)
        entry = {
            "ticker":     t,
            "name":       stock["name"],
            "is_etf":     stock["is_etf"],
            "curr_close": result.get("curr_close", 0),
            "pct_change": result.get("pct_change", 0),
            "news_note":  "",   # 由 CC web search 填入
            "news_date":  "",   # 填入新聞日期（YYYY-MM-DD），用於過濾舊消息
        }
        if "error" in result:
            entry["error"] = result["error"]
            print(f"  ✗ {t}: {result['error']}")
        else:
            arrow = "▲" if result["pct_change"] >= 0 else "▼"
            print(f"  {'ETF' if stock['is_etf'] else '   '} {t:6s} {stock['name']:8s} {result['curr_close']:>8.2f}  {arrow} {result['pct_change']:+.2f}%")
        tracked_stocks_data.append(entry)

    print()

    # ── 計算 badge ──
    spx = market_data.get("^GSPC", {})
    spx_chg = spx.get("pct_change", 0)
    if spx_chg >= 0:
        badge_class = "badge-up"
        badge_text = f"▲ 上漲週 +{spx_chg:.1f}%"
    else:
        badge_class = "badge-dn"
        badge_text = f"▼ 下跌週 {spx_chg:.1f}%"

    # ── VIX 判斷 ──
    vix_data = market_data.get("^VIX", {})
    vix_val = vix_data.get("curr_close", 0)
    vix_note = "偏高" if vix_val > VIX_HIGH_THRESHOLD else "正常"

    # ── 組裝 JSON ──
    report_date = this_fri
    output = {
        "meta": {
            "report_type": "weekly",
            "report_date": str(report_date),
            "date_main": format_date_main(report_date),
            "date_sub": format_date_sub(report_date),
            "badge_class": badge_class,
            "badge_text": badge_text,
            "mode": "B",
            "fixed_tickers": list(FIXED_TICKERS.keys()),
            "flex_picks": DEFAULT_FLEX_PICKS,
            "flex_picks_note": "CC 可根據當週市場熱度修改此欄位，從 FLEX_TICKERS 候選池中選 3 個",
        },
        "market": market_data,
        "sectors": sector_data,
        "sectors_ranked": {
            "top3_up": [{"etf": k, **v} for k, v in top3_up],
            "top3_dn": [{"etf": k, **v} for k, v in top3_dn],
        },
        "vix_note": vix_note,

        "tracked_stocks": tracked_stocks_data,

        # ── 以下欄位由 Claude Code 用 web search 補充 ──
        "news": [
            {"title": "", "body": "", "badge_class": "b-hot", "badge_text": ""},
            {"title": "", "body": "", "badge_class": "b-warn", "badge_text": ""},
            {"title": "", "body": "", "badge_class": "b-warn", "badge_text": ""},
            {"title": "", "body": "", "badge_class": "b-info", "badge_text": ""},
        ],
        "macro": [
            {"desc": "", "badge_class": "b-info", "badge_text": ""},
            {"desc": "", "badge_class": "b-warn", "badge_text": ""},
            {"desc": "", "badge_class": "b-hot", "badge_text": ""},
            {"desc": "", "badge_class": "b-warn", "badge_text": ""},
        ],
        "sentiment": [
            {"label": "", "pct": 0, "color": "#a12020", "desc": ""},
            {"label": "", "pct": 0, "color": "#a12020", "desc": ""},
            {"label": "", "pct": 0, "color": "#a12020", "desc": ""},
            {"label": "", "pct": 0, "color": "#a12020", "desc": ""},
        ],
        "calendar": {
            "next_week_range": "",
            "items": ["", "", "", "", "", ""],
            "risk_note": "",
        },
    }

    # ── 寫入 JSON ──
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    date_str = report_date.strftime("%Y%m%d") if hasattr(report_date, 'strftime') else str(report_date).replace("-", "")
    json_path = Path(OUTPUT_DIR) / f"weekly_data_{date_str}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 數據已存入：{json_path}")
    print(f"\n[下一步] AI 助手請用 web search 補充 news / sentiment / calendar 欄位並交人工查核，")
    print(f"         然後跑：python src/build_report.py {json_path}")

    return output, json_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="週報數據抓取")
    parser.add_argument("--date", type=str, help="指定週五日期 YYYY-MM-DD（預設自動偵測）")
    parser.add_argument("--start-date", type=str, help="指定資料區間起日 YYYY-MM-DD（選填）")
    args = parser.parse_args()

    end_date = None
    if args.date:
        end_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    start_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()

    fetch_all_data(end_date, start_date)
