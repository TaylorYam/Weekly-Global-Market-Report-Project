# Shared assistant workflow

This is a personal research and engineering project for informational and educational purposes only. It is not investment advice and is not affiliated with, sponsored by, or endorsed by my employer.

AI assists implementation, source discovery, organization and drafting. A human verifies sources, selects news, interprets relevance, reviews the rendered report and approves any publication.

## Report workflow

1. Confirm reporting date, data interval, generic watchlist and any user-supplied context. Do not invent a personal market view.
2. Collect structured market data when requested. Check cutoff dates, comparison dates and missing values.
3. Research current candidate news, sentiment and dated upcoming events. Record event date separately from article date. Prefer primary sources.
4. Present candidates for human selection. Draft only selected items; separate verified facts from interpretation and omit unsupported claims.
5. Record source URLs and review status when available. A URL or search snippet alone does not prove a claim.
6. Render and preview HTML. Check dates, figures, missing fields and mobile readability.
7. Wait for explicit human approval before publication. Never publish automatically.

## News selection

Use the Monday-reader freshness rule: weekend and Friday-after-close events receive priority, then major Thursday/Friday developments. Ongoing policy events and market-leading earnings may remain relevant. Single-day price moves belong in market data, not a duplicate news item. See `news-selection.md` for the full ranking scheme.

## Portfolio demo

Run `python src/build_report.py examples/sample_week.json`. Keep this generated demo's values fictional. The demo writes `examples/sample_output.html`; it has no network, analytics or credential dependency.

The separately labeled `examples/historical/20260914.html` is an owner-approved historical output, not synthetic input. Preserve its data, securities, views and source limitations. Document any approved safety edits in `examples/historical/README.md`. Validate the fixed snapshot with `python scripts/check_historical.py`; never regenerate it from live data.
