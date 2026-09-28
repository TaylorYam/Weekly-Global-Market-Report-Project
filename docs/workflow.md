# 操作流程

本專案展示每週市場資訊整理方法。AI 協助研究與起草；人工負責來源核對、新聞取捨、市場解讀及發布核准。

## 離線示範

在專案根目錄執行：

```bash
python src/build_report.py examples/sample_week.json
```

輸出為 `examples/sample_output.html`。示範資料全部為虛構內容，不需連線或憑證。

## 行情資料流程（選用）

線上抓取範例使用 yfinance，須安裝 `requirements.txt` 並連線。`--date` 是資料截止日，也會作為報告日期骨架；請分開核對實際發布日、新聞期間與行情比較基準。

```bash
python -m pip install -r requirements.txt
python src/fetch_data.py --date 2026-09-25
```

抓取後人工核對前後交易日、休市、時區、期貨換月及缺值。不要把資料供應商輸出視為已完成事實查核。

## 編輯與生成

人工先選定新聞，並核對來源、事件日期及數字，再整理 JSON 中的 `news`、`sentiment`、`calendar`；`taylors_take` 為選填，沒有用戶提供或核准的觀點時省略。舊 `macro` 欄位可省略。

```bash
python src/build_report.py path/to/weekly_data.json
```

正式輸入會輸出至 `output/`。此展示專案不含正式發布工具或服務設定。公開展示請使用合成範例。HTML 文字是可信任輸入；請人工審核後再分享。
