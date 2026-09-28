"""
週報 HTML 生成器
用法：python src/build_report.py output/weekly_data_YYYYMMDD.json

功能：
  讀取 JSON 數據檔，將所有 {{佔位符}} 替換為實際數據，
  輸出 report_weekly_{YYYYMMDD}_web.html
"""

import json
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_DIR, TEMPLATE_DIR


def format_value(val, ticker=None):
    """格式化數值顯示"""
    if val is None:
        return "N/A"
    if ticker == "^VIX":
        return f"{val:.1f}"
    if ticker in ("CL=F", "GC=F", "BZ=F"):
        return f"${val:,.0f}" if val >= 100 else f"${val:.1f}"
    if abs(val) >= 1000:
        return f"{val:,.0f}"
    return f"{val:,.2f}"


def format_change(pct, ticker=None):
    """格式化漲跌幅"""
    if pct is None:
        return "N/A"
    arrow = "▲" if pct >= 0 else "▼"
    return f"{arrow} {pct:+.1f}%"


def get_direction(pct):
    """CSS class: up / dn"""
    if pct is None:
        return "neu"
    return "up" if pct >= 0 else "dn"


def build_report(json_path: str):
    """主流程：讀取 JSON，填充模板，輸出 HTML"""

    json_path = Path(json_path)
    if not json_path.exists():
        print(f"[ERROR] 找不到數據檔：{json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["meta"]
    market = data["market"]
    sectors = data["sectors_ranked"]
    news = data["news"]
    macro = data.get("macro", [])  # Deprecated; retained for older JSON files.
    sentiment = data["sentiment"]
    calendar = data["calendar"]
    vix_note = data.get("vix_note", "正常")

    # ── 讀取模板 ──
    web_path = Path(TEMPLATE_DIR) / "weekly-template-web.html"
    if not web_path.exists():
        print(f"[ERROR] 模板不存在：{web_path}")
        sys.exit(1)

    web_html = web_path.read_text(encoding="utf-8")

    # ── 板塊最大值（供 bar width 計算）──
    all_pcts = [abs(s["pct_change"]) for s in sectors["top3_up"] + sectors["top3_dn"] if "pct_change" in s]
    max_abs_pct = max(all_pcts) if all_pcts else 1

    # ══════════════════════════════════════════
    # Web 版替換
    # ══════════════════════════════════════════
    web_filled = web_html

    # Header
    web_filled = web_filled.replace("{{DATE_MAIN}}", meta["date_main"])
    web_filled = web_filled.replace("{{DATE_SUB}}", meta["date_sub"])
    web_filled = web_filled.replace("{{BADGE_CLASS}}", meta["badge_class"])
    web_filled = web_filled.replace("{{BADGE_TEXT}}", meta["badge_text"])
    web_filled = web_filled.replace("{{FOOTER_DATE}}", meta["date_main"])

    # 報告標籤：依「今天」與「資料週」的關係判斷
    # 週一或已達發布日 → 上週概覽；其餘 → 本週概覽
    from datetime import datetime, timedelta
    try:
        pub_date = datetime.strptime(meta["report_date"], "%Y-%m-%d").date()
        today = datetime.now().date()
        weekday = pub_date.weekday()  # 用 report_date 判斷是否為週一報告
        if weekday == 0 or today >= pub_date:  # 週一報告或資料週已過
            report_label = "上週概覽"
        else:
            report_label = "本週概覽"
        # 計算追蹤期間
        if weekday == 0:
            t_start = pub_date - timedelta(days=7)
            t_end   = pub_date - timedelta(days=3)
        else:
            t_start = pub_date - timedelta(days=weekday)
            t_end   = pub_date - timedelta(days=1)
        tracked_period = f"{t_start.month}/{t_start.day}—{t_end.month}/{t_end.day}"
    except Exception:
        report_label = "本週概覽"
        pub_date = None
        weekday = -1
        t_start = t_end = None
        tracked_period = ""
    heatmap_period = "上週" if weekday == 0 else "本週"
    web_filled = web_filled.replace("{{REPORT_LABEL}}", report_label)
    web_filled = web_filled.replace("{{TRACKED_PERIOD}}", tracked_period)
    web_filled = web_filled.replace("{{HEATMAP_PERIOD}}", heatmap_period)

    # 市場概覽
    for ticker_key, mkt in market.items():
        if "error" in mkt:
            continue
        val_str = format_value(mkt["curr_close"], ticker_key)
        chg_str = format_change(mkt["pct_change"], ticker_key)
        dir_str = get_direction(mkt["pct_change"])
        web_filled = web_filled.replace(f"{{{{{mkt['tmpl_val']}}}}}", val_str)
        # Dynamic label for flex picks (e.g., OIL_LABEL)
        web_filled = web_filled.replace(f"{{{{{mkt['tmpl_val']}_LABEL}}}}", mkt.get("label", ""))
        if ticker_key == "^VIX":
            web_filled = web_filled.replace(f"{{{{{mkt['tmpl_chg']}}}}}", vix_note)
        else:
            web_filled = web_filled.replace(f"{{{{{mkt['tmpl_chg']}}}}}", chg_str)
            web_filled = web_filled.replace(f"{{{{{mkt['tmpl_dir']}}}}}", dir_str)

    # 新聞
    for i, item in enumerate(news, 1):
        web_filled = web_filled.replace(f"{{{{NEWS{i}_TITLE}}}}", item.get("title", ""))
        web_filled = web_filled.replace(f"{{{{NEWS{i}_BODY}}}}", item.get("body", ""))
        web_filled = web_filled.replace(f"{{{{NEWS{i}_BADGE_CLASS}}}}", item.get("badge_class", "b-info"))
        web_filled = web_filled.replace(f"{{{{NEWS{i}_BADGE}}}}", item.get("badge_text", ""))

    # 清除未使用的新聞佔位符（支援少於 4 則新聞）
    import re
    for j in range(len(news) + 1, 5):  # 清 news+1 到 4
        pattern = rf'<div class="news-item">\s*<div class="news-title">\{{{{NEWS{j}_TITLE\}}}}'
        web_filled = re.sub(pattern + r'.*?</div>\s*</div>', '', web_filled, flags=re.DOTALL)

    # 板塊
    for i, sector in enumerate(sectors["top3_up"], 1):
        bar_width = round(abs(sector["pct_change"]) / max_abs_pct * 95)
        pct = sector["pct_change"]
        if pct >= 0:
            bar_class, pct_class = "bar-up", "up"
            name = sector["name_zh"]
            pct_str = f"+{pct:.1f}%"
        else:
            bar_class, pct_class = "bar-neu", "neu"
            name = sector["name_zh"]
            pct_str = f"{pct:.1f}%"
        web_filled = web_filled.replace(f"{{{{UP{i}_NAME}}}}", name)
        web_filled = web_filled.replace(f"{{{{UP{i}_BAR}}}}", str(bar_width))
        web_filled = web_filled.replace(f"{{{{UP{i}_BAR_CLASS}}}}", bar_class)
        web_filled = web_filled.replace(f"{{{{UP{i}_PCT}}}}", pct_str)
        web_filled = web_filled.replace(f"{{{{UP{i}_PCT_CLASS}}}}", pct_class)

    for i, sector in enumerate(sectors["top3_dn"], 1):
        bar_width = round(abs(sector["pct_change"]) / max_abs_pct * 95)
        web_filled = web_filled.replace(f"{{{{DN{i}_NAME}}}}", sector["name_zh"])
        web_filled = web_filled.replace(f"{{{{DN{i}_BAR}}}}", str(bar_width))
        web_filled = web_filled.replace(f"{{{{DN{i}_PCT}}}}", f"{sector['pct_change']:.1f}%")

    # 宏觀
    for i, item in enumerate(macro, 1):
        web_filled = web_filled.replace(f"{{{{MACRO{i}_DESC}}}}", item.get("desc", ""))
        web_filled = web_filled.replace(f"{{{{MACRO{i}_BADGE_CLASS}}}}", item.get("badge_class", "b-info"))
        web_filled = web_filled.replace(f"{{{{MACRO{i}_BADGE}}}}", item.get("badge_text", ""))

    # 情緒（動態生成，依實際項目數）
    sent_html = ""
    for item in sentiment:
        sent_val = item.get("value", item.get("pct", ""))
        sent_html += (
            f'<div class="sent-item">'
            f'<div class="sent-label"><span>{item.get("label","")}</span><span class="sent-val" style="color:{item.get("color","#888")}">{sent_val}</span></div>'
            f'<div class="sent-bar"><div class="sent-fill" style="width:{item.get("pct",0)}%;background:{item.get("color","#888")}"></div></div>'
            f'<div class="sent-desc">{item.get("desc","")}</div>'
            f'</div>\n      '
        )
    web_filled = web_filled.replace("{{SENTIMENT_ITEMS}}", sent_html)

    # 美股觀察清單（動態生成）
    tracked_stocks = data.get("tracked_stocks", [])
    tracked_html = ""
    for stock in tracked_stocks:
        ticker  = stock.get("ticker", "")
        name    = stock.get("name", "")
        is_etf  = stock.get("is_etf", False)
        curr    = stock.get("curr_close", 0)
        pct     = stock.get("pct_change", 0)
        note    = stock.get("news_note", "")
        dir_cls = "up" if pct >= 0 else "dn"
        arrow   = "▲" if pct >= 0 else "▼"
        sign    = "+" if pct >= 0 else ""
        etf_tag = '<span class="track-etf-label">ETF</span>' if is_etf else ""
        tracked_html += (
            f'<div class="track-row">'
            f'<div class="track-ticker">{ticker}</div>'
            f'<div class="track-name">{name}{etf_tag}</div>'
            f'<div class="track-price">${curr:,.2f}</div>'
            f'<div class="track-chg {dir_cls}">{arrow} {sign}{pct:.2f}%</div>'
            f'</div>\n'
        )
        if note and not is_etf and weekday == 0:
            # 週一報告才顯示個股新聞，且只顯示當週新聞
            news_date_str = stock.get("news_date", "")
            show_note = False
            if news_date_str and t_start and t_end:
                try:
                    nd = datetime.strptime(news_date_str, "%Y-%m-%d").date()
                    show_note = t_start <= nd <= pub_date
                except Exception:
                    show_note = True
            else:
                show_note = bool(note)
            if show_note:
                tracked_html += f'<div class="track-note">📌 {note}</div>\n'
    web_filled = web_filled.replace("{{TRACKED_STOCKS_HTML}}", tracked_html)

    # Taylor 的看法（置頂動態生成，無內容時移除整個區塊）
    take = data.get("taylors_take", {})
    take_html = ""
    if take and (take.get("main") or take.get("points") or take.get("conclusion")):
        main_text = take.get("main", "")
        if main_text:
            take_html += f'<div style="margin-bottom:10px;">{main_text}</div>\n'
        for pt in take.get("points", []):
            take_html += f'<div class="take-point">{pt}</div>\n'
        conclusion = take.get("conclusion", "")
        if conclusion:
            take_html += f'<div class="take-conclusion">{conclusion.replace(chr(10), "<br>")}</div>\n'
        web_filled = web_filled.replace("{{TAYLORS_TAKE}}", take_html)
    else:
        # 無觀點：移除置頂區塊
        import re
        web_filled = re.sub(
            r'<!-- Taylor 的看法（置頂） -->.*?</div>\s*(?=\s*<!-- 1 · 市場概覽 -->)',
            '', web_filled, flags=re.DOTALL
        )

    # 日程（非週一報告隱藏整個區塊）
    if weekday == 0:
        web_filled = web_filled.replace("{{NEXT_WEEK_RANGE}}", calendar.get("next_week_range", ""))
        for i, item in enumerate(calendar.get("items", []), 1):
            web_filled = web_filled.replace(f"{{{{CAL{i}}}}}", item)
        # 清掉未使用的 CAL 佔位符（日程項目數不足 6 時）
        for i in range(1, 7):
            web_filled = web_filled.replace(f"{{{{CAL{i}}}}}", "")
        _rn = calendar.get("risk_note", "")
        _rn_parts = _rn.split("\n")
        _rn_title = _rn_parts[0]
        _rn_items = "".join(f"<li>{l}</li>" for l in _rn_parts[1:] if l.strip())
        _rn_html = f'<span class="risk-title">{_rn_title}</span><ul class="risk-list">{_rn_items}</ul>'
        web_filled = web_filled.replace("{{RISK_NOTE}}", _rn_html)
    else:
        # 非週一：移除整個日程區塊
        import re
        web_filled = re.sub(
            r'<!-- 6 · 短期重要日程 -->.*?</div>\s*(?=</div><!-- end content -->)',
            '', web_filled, flags=re.DOTALL
        )

    # ── 輸出 HTML ──
    date_str = meta["report_date"].replace("-", "")
    if meta.get("demo") is True:
        # Keep synthetic data out of the production archive and disable telemetry.
        web_filled = re.sub(r'<script\b[^>]*>.*?</script>', '', web_filled, flags=re.DOTALL)
        web_filled = '\n'.join(line.rstrip() for line in web_filled.splitlines()) + '\n'
        web_filled = web_filled.replace('<body>', '<body><p style="text-align:center;font-weight:700;">SYNTHETIC DEMO — All values and events are artificial. 模擬資料，非實際行情。</p>', 1)
        web_out = json_path.parent / "sample_output.html"
    else:
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        web_out = Path(OUTPUT_DIR) / f"report_weekly_{date_str}_web.html"
    web_out.write_text(web_filled, encoding="utf-8")
    print(f"[OK] {web_out}")
    print()

    # ── 輸出草稿摘要 ──
    print("=" * 50)
    print("  週報草稿摘要")
    print("=" * 50)
    print(f"日期：{meta['date_main']}（{meta['date_sub']}）")
    print(f"Badge：{meta['badge_text']}")
    print()

    print("【市場概覽】")
    for ticker_key, mkt in market.items():
        if "error" not in mkt:
            print(f"  {mkt['label']:10s} {format_value(mkt['curr_close'], ticker_key):>10s}  {format_change(mkt['pct_change'], ticker_key)}")
    print()

    print("【板塊漲跌幅】")
    up3 = "  |  ".join(f"{s['name_zh']} {s['pct_change']:+.1f}%" for s in sectors['top3_up'])
    dn3 = "  |  ".join(f"{s['name_zh']} {s['pct_change']:+.1f}%" for s in sectors['top3_dn'])
    print(f"  up {up3}")
    print(f"  dn {dn3}")
    print()

    has_news = any(n.get("title") for n in news)

    if has_news:
        print("【新聞】")
        for i, n in enumerate(news, 1):
            if n.get("title"):
                print(f"  {i}. {n['title']}")
        print()

    if not has_news:
        print("[WARNING] 以下欄位需要補充：")
        print("  - news (重大新聞)")
        if not any(s.get("label") for s in sentiment):
            print("  - sentiment (情緒指標)")
        if not any(calendar.get("items", [])):
            print("  - calendar (短期重要日程 + risk_note)")
        print()
        print("請用 web search 補充後，重新跑 build_report.py")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        # 自動找最新的 JSON
        jsons = sorted(Path(OUTPUT_DIR).glob("weekly_data_*.json"), reverse=True)
        if not jsons:
            print("[ERROR] output/ 裡找不到 weekly_data_*.json")
            print("請先跑：python src/fetch_data.py")
            sys.exit(1)
        json_path = str(jsons[0])
        print(f"[自動] {json_path}")
    else:
        json_path = sys.argv[1]

    build_report(json_path)
