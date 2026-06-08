# Creatives Performance

Multi-brand creative performance dashboard. Single HTML page with a tab strip:
**All brands** (agency-wide aggregate) plus one tab per client brand.

Live at: https://adtribe-admin.github.io/creatives-performance/

## What's in it

- KPI cards: ads delivered, total spend, avg CPA, avg ROAS, tests shipped
- Brands summary table (click a row to drill in)
- Sortable creatives table with thumbnails, hook %, hold %, ROAS, CPA, revenue
- Click any thumbnail to preview the full video / image in a modal
- Top 15 by spend, top 15 by ROAS (min $50 spend)
- Data quality panel: null counts, duplicate names, tests shipped, templated %

## Files

- `index.html` — the dashboard (generated; do not edit by hand)
- `build.py` — renders `index.html` from the per-brand `data.json` files
- `refresh.py` — refreshes per-brand `data.json` from GoMarble MCP pulls (run locally with MCP access)
- `brands/<slug>/data.json` — slim per-brand performance data
- `brands/<slug>/build_data.py` — historical per-brand build script (kept for reference)

## Manual rebuild

```bash
python3 build.py
```

## Refreshing data

`refresh.py` consumes GoMarble MCP responses embedded inline + a saved disk file
(for the one campaign too big to return inline). To refresh, run the GoMarble
pulls via the MCP, update `refresh.py` with the new ad data, then:

```bash
python3 refresh.py
python3 build.py
```

## Source

GoMarble MCP · `facebook_get_adaccount_insights` (level=ad, last_30d, per-campaign) +
`facebook_get_ad_creative_details`.
