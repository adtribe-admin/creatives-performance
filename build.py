#!/usr/bin/env python3
"""Unified Creatives Performance dashboard.

Reads brands/<slug>/data.json files (one per client) and renders ONE
index.html with a tab strip:

  [ All brands ] [ Slumberkins ] [ Xtrema ] ...

- All brands tab (default): agency-wide KPIs, brand summary table,
  cross-brand creatives table, cross-brand top-N charts, combined DQ.
- Per-brand tab: KPI row + creatives table + top-N charts + DQ for
  that brand only.

KPI #5 ("Tests shipped") counts ads whose `ad_name` contains "test"
(case-insensitive). Replaces the previous "creative_name populated" KPI.
"""
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
BRANDS_DIR = ROOT / "brands"

# ---- Load brand data ----
BRANDS = []
for bf in sorted(BRANDS_DIR.glob("*/data.json")):
    d = json.loads(bf.read_text())
    slug = bf.parent.name
    ads = d.get("ads") or []
    for a in ads:
        a["_brand_slug"] = slug
        a["_brand_name"] = d["account"]["name"]
    BRANDS.append({
        "slug": slug,
        "account": d["account"],
        "meta": d.get("meta") or {},
        "date_range": d.get("date_range") or {"label": "Last 30 days"},
        "generated_at": d.get("generated_at"),
        "totals": d.get("totals") or {},
        "campaigns": d.get("campaigns") or [],
        "campaign_count_total": d.get("campaign_count_total", 0),
        "campaign_error": d.get("campaign_error"),
        "ads": ads,
    })

# Sort brands by spend descending (most active first)
def _brand_spend(b):
    t = b["totals"]
    return t.get("total_spend_from_ads", 0) or t.get("total_spend", 0) or 0
BRANDS.sort(key=_brand_spend, reverse=True)

ALL_ADS = [a for b in BRANDS for a in b["ads"]]


# ---- Formatters ----
def usd(v):
    if v is None or v == 0:
        return "$0.00"
    return f"${v:,.2f}"


def intf(v):
    if v is None:
        return "—"
    return f"{int(v):,}"


def pct(v, dec=1):
    if v is None:
        return "—"
    return f"{v*100:.{dec}f}%"


def num(v, dec=2):
    if v is None:
        return "—"
    return f"{v:,.{dec}f}"


def short(s, n=48):
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"


# ---- "Tests shipped" = ads whose ad_name contains "test" (case-insensitive)
def count_tests(ads):
    return sum(1 for a in ads if "test" in (a.get("ad_name") or "").lower())


# ---- Aggregate totals for any ads list ----
def totals_for(ads):
    spend = sum(a["spend"] for a in ads)
    purch = sum(a["purchases"] for a in ads)
    rev = sum(a["revenue"] for a in ads)
    tests = count_tests(ads)
    n = len(ads)
    return {
        "ad_count": n,
        "total_spend": spend,
        "total_impressions": sum(a["impressions"] for a in ads),
        "total_purchases": purch,
        "total_revenue": rev,
        "avg_cpa": (spend / purch) if purch else 0,
        "avg_roas": (rev / spend) if spend else 0,  # spend-weighted, confirmed
        "test_count": tests,
        "test_pct": (tests / n) if n else 0,
    }


AGG_ADS = totals_for(ALL_ADS)
# Agency-wide aggregate also rolls in brand-level totals from perf rollups for brands without ads
AGG = {
    **AGG_ADS,
    "total_spend": sum(b["totals"].get("total_spend", 0) or 0 for b in BRANDS),
    "total_revenue": sum(b["totals"].get("total_revenue", 0) or 0 for b in BRANDS),
    "total_purchases": sum(b["totals"].get("total_purchases", 0) or 0 for b in BRANDS),
}
AGG["avg_cpa"] = (AGG["total_spend"] / AGG["total_purchases"]) if AGG["total_purchases"] else 0
AGG["avg_roas"] = (AGG["total_revenue"] / AGG["total_spend"]) if AGG["total_spend"] else 0

# Per-brand agg: use ad-level if available, else fall back to perf-rollup totals
for b in BRANDS:
    if b["ads"]:
        b["agg"] = totals_for(b["ads"])
    else:
        t = b["totals"]
        b["agg"] = {
            "ad_count": 0,
            "total_spend": t.get("total_spend", 0) or 0,
            "total_impressions": 0,
            "total_purchases": t.get("total_purchases", 0) or 0,
            "total_revenue": t.get("total_revenue", 0) or 0,
            "avg_cpa": t.get("avg_cpa", 0) or 0,
            "avg_roas": t.get("avg_roas", 0) or 0,
            "test_count": 0,
            "test_pct": 0,
        }


# ---- ROAS color helpers ----
def roas_class(roas):
    if roas is None or roas == 0:
        return "neu"
    if roas >= 2:
        return "pos"
    if roas >= 1:
        return "warn"
    return "neg"


def bar_color(roas):
    if roas is None or roas == 0:
        return "rgba(255,255,255,0.18)"
    if roas >= 3:
        return "var(--lime)"
    if roas >= 2:
        return "#9ad400"
    if roas >= 1:
        return "var(--purple-2)"
    return "var(--bad)"


# ---- KPI row ----
def kpi_card(label, value, meta="", accent=False):
    acc = " accent" if accent else ""
    m = f'<div class="meta">{html.escape(meta)}</div>' if meta else ""
    return f'<div class="kpi{acc}"><div class="label">{html.escape(label)}</div><div class="value">{value}</div>{m}</div>'


def kpi_row(t, scope_label):
    return "\n".join([
        kpi_card("Ads (delivered)", intf(t["ad_count"]), meta=scope_label),
        kpi_card("Total spend", usd(t["total_spend"]), meta=f"{intf(t['total_purchases'])} purchases"),
        kpi_card("Avg CPA", usd(t["avg_cpa"]), meta=f"{usd(t['total_revenue'])} revenue"),
        kpi_card("Avg ROAS", f"{num(t['avg_roas'], 2)}x", meta="spend-weighted", accent=t["avg_roas"] >= 2.0),
        kpi_card("Tests shipped", intf(t["test_count"]), meta=f'{pct(t["test_pct"])} of creatives · ad_name contains "test"'),
    ])


# ---- Creatives table ----
def render_ads_table(ads, table_id, show_brand=False):
    brand_th = '<th data-sort="brand" data-type="text">Brand</th>' if show_brand else ""
    rows = []
    for a in ads:
        ad_name = a["ad_name"] or "(unnamed)"
        is_test = "test" in (a.get("ad_name") or "").lower()
        cn = a.get("creative_name") or ""
        templ_tag = '<span class="tag templ">templated</span>' if a.get("creative_name_is_templated") else ""
        test_tag = '<span class="tag test">test</span>' if is_test else ""
        thumb = a.get("thumb_url")
        asset_url = a.get("asset_url") or thumb or ""
        asset_type = a.get("asset_type") or ("video" if a.get("video_3s", 0) > 0 else "image")
        if thumb and asset_url:
            thumb_html = (
                f'<button type="button" class="thumb-btn" '
                f'data-asset-url="{html.escape(asset_url)}" '
                f'data-asset-type="{html.escape(asset_type)}" '
                f'data-thumb-url="{html.escape(thumb)}" '
                f'data-ad-name="{html.escape(ad_name)}" '
                f'data-brand="{html.escape(a["_brand_name"])}" '
                f'data-campaign="{html.escape(a["campaign_name"])}" '
                f'data-spend="{a["spend"]}" '
                f'data-roas="{a["roas"]}" '
                f'data-purch="{a["purchases"]}" '
                f'aria-label="Preview creative">'
                f'<img class="thumb" src="{html.escape(thumb)}" alt="" loading="lazy" />'
                f'<span class="thumb-play" aria-hidden="true">{"▶" if asset_type == "video" else "⤢"}</span>'
                f'</button>'
            )
        else:
            thumb_html = '<div class="thumb empty"></div>'
        roas_cls = roas_class(a["roas"])
        cpa_str = usd(a["cpa"]) if a["purchases"] > 0 else "—"
        brand_cell = (
            f'<td><span class="brand-pill b-{a["_brand_slug"]}">{html.escape(a["_brand_name"])}</span></td>'
            if show_brand
            else ""
        )
        rows.append(f"""
        <tr data-name="{html.escape(ad_name)}" data-brand="{html.escape(a['_brand_name'])}" data-cn="{html.escape(cn)}" data-campaign="{html.escape(a['campaign_name'])}">
          <td class="creative-cell">
            {thumb_html}
            <div class="creative-meta">
              <div class="ad-name" title="{html.escape(ad_name)}">{html.escape(short(ad_name, 70))} {test_tag}</div>
              <div class="cn">{html.escape(short(cn, 70))} {templ_tag}</div>
              <div class="cmp">{html.escape(short(a['campaign_name'], 64))}</div>
            </div>
          </td>
          {brand_cell}
          <td>{usd(a['spend'])}</td>
          <td>{intf(a['impressions'])}</td>
          <td>{intf(a['clicks'])}</td>
          <td>{num(a['ctr_pct'], 2)}%</td>
          <td>{usd(a['cpc'])}</td>
          <td>{usd(a['cpm'])}</td>
          <td>{pct(a.get('hook_rate', 0), 1) if a.get('video_3s', 0) > 0 else '—'}</td>
          <td>{pct(a.get('hold_rate', 0), 1) if a.get('video_3s', 0) > 0 else '—'}</td>
          <td>{a['purchases']}</td>
          <td>{cpa_str}</td>
          <td class="{roas_cls}">{num(a['roas'], 2)}x</td>
          <td>{usd(a['revenue'])}</td>
        </tr>
        """)
    return f"""
    <div class="scroll">
      <table id="{table_id}" class="ads-table">
        <thead>
          <tr>
            <th data-sort="name" data-type="text">Creative</th>
            {brand_th}
            <th data-sort="spend" data-type="num" class="sort-desc">Spend</th>
            <th data-sort="impressions" data-type="num">Impr</th>
            <th data-sort="clicks" data-type="num">Clicks</th>
            <th data-sort="ctr" data-type="num">CTR</th>
            <th data-sort="cpc" data-type="num">CPC</th>
            <th data-sort="cpm" data-type="num">CPM</th>
            <th data-sort="hook" data-type="num">Hook %</th>
            <th data-sort="hold" data-type="num">Hold %</th>
            <th data-sort="purchases" data-type="num">Purch</th>
            <th data-sort="cpa" data-type="num">CPA</th>
            <th data-sort="roas" data-type="num">ROAS</th>
            <th data-sort="revenue" data-type="num">Revenue</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


# ---- Bar chart helpers ----
def bar(label, value_label, width_pct, color, sub="", brand=""):
    sub_html = f'<span class="bar-sub">{html.escape(sub)}</span>' if sub else ""
    brand_html = f'<span class="bar-brand">{html.escape(brand)}</span>' if brand else ""
    return f"""
      <div class="bar-row">
        <div class="bar-label" title="{html.escape(label)}">{html.escape(short(label, 36))}{brand_html} {sub_html}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{width_pct:.1f}%; background:{color};"></div></div>
        <div class="bar-value">{value_label}</div>
      </div>
    """


def render_top_panels(ads, show_brand=False):
    top_spend = sorted(ads, key=lambda a: a["spend"], reverse=True)[:15]
    top_roas = sorted([a for a in ads if a["spend"] >= 50], key=lambda a: a["roas"], reverse=True)[:15]
    max_s = max((a["spend"] for a in top_spend), default=1) or 1
    max_r = max((a["roas"] for a in top_roas), default=1) or 1
    spend_bars = "\n".join(
        bar(a["ad_name"] or "(unnamed)", usd(a["spend"]), (a["spend"] / max_s) * 100, bar_color(a["roas"]),
            sub=f"ROAS {num(a['roas'], 2)}x", brand=a["_brand_name"] if show_brand else "")
        for a in top_spend
    )
    roas_bars = "\n".join(
        bar(a["ad_name"] or "(unnamed)", f"{num(a['roas'], 2)}x", (a["roas"] / max_r) * 100, bar_color(a["roas"]),
            sub=usd(a["spend"]), brand=a["_brand_name"] if show_brand else "")
        for a in top_roas
    ) or '<div class="empty-note">No ads with $50+ spend.</div>'

    return f"""
    <div class="panel">
      <div class="panel-h">
        <h2>Top 15 creatives by spend</h2>
        <span class="note">color = ROAS (lime ≥ 3x, purple ≥ 1x, red &lt; 1x)</span>
      </div>
      <div class="bar-wrap">{spend_bars}</div>
    </div>
    <div class="panel">
      <div class="panel-h">
        <h2>Top 15 creatives by ROAS (min $50 spend)</h2>
        <span class="note">{len(top_roas)} creatives qualify</span>
      </div>
      <div class="bar-wrap">{roas_bars}</div>
    </div>
    """


# ---- DQ panel ----
def render_dq(ads):
    n = len(ads)
    nulls = {
        col: sum(1 for a in ads if not a.get(col))
        for col in ["ad_name", "creative_id", "creative_name", "thumb_url", "campaign_name", "adset_name"]
    }
    name_counts = Counter(a["creative_name"] for a in ads if a.get("creative_name"))
    dup_names = {nm: c for nm, c in name_counts.items() if c > 1}
    ad_name_counts = Counter(a["ad_name"] for a in ads)
    dup_ad_names = {nm: c for nm, c in ad_name_counts.items() if c > 1}
    tests = count_tests(ads)
    templated = sum(1 for a in ads if a.get("creative_name_is_templated"))
    templated_spend = sum(a["spend"] for a in ads if a.get("creative_name_is_templated"))
    total_spend = sum(a["spend"] for a in ads) or 1

    null_rows = "".join(
        f"<tr><td>{html.escape(c)}</td><td>{x}</td><td>{pct(x/n) if n else '—'}</td></tr>"
        for c, x in nulls.items()
    )
    dup_cn_rows = "".join(
        f"<tr><td>{html.escape(short(nm, 80))}</td><td>{c}</td></tr>"
        for nm, c in sorted(dup_names.items(), key=lambda x: -x[1])[:10]
    ) or '<tr><td colspan="2" class="empty-note">No duplicate creative names</td></tr>'
    dup_an_rows = "".join(
        f"<tr><td>{html.escape(short(nm, 80))}</td><td>{c}</td></tr>"
        for nm, c in sorted(dup_ad_names.items(), key=lambda x: -x[1])[:10]
    ) or '<tr><td colspan="2" class="empty-note">No duplicate ad names</td></tr>'

    return f"""
    <div class="panel">
      <div class="panel-h"><h2>Data quality</h2><span class="note">what's missing, what's duplicated</span></div>
      <div class="dq-grid">
        <div class="dq-cell">
          <h3>Null counts per column</h3>
          <table><thead><tr><th>Column</th><th>Nulls</th><th>%</th></tr></thead>
          <tbody>{null_rows}</tbody></table>
        </div>
        <div class="dq-cell">
          <h3>Duplicate creative_name (top 10)</h3>
          <table><thead><tr><th>creative_name</th><th>×</th></tr></thead>
          <tbody>{dup_cn_rows}</tbody></table>
        </div>
        <div class="dq-cell">
          <h3>Duplicate ad_name (top 10)</h3>
          <table><thead><tr><th>ad_name</th><th>×</th></tr></thead>
          <tbody>{dup_an_rows}</tbody></table>
        </div>
        <div class="dq-cell">
          <h3>Summary</h3>
          <table><tbody>
            <tr><td>Tests shipped</td><td><strong>{tests}</strong> ({pct(tests/n if n else 0)})</td></tr>
            <tr><td>Templated creative_name</td><td>{templated} ({pct(templated/n if n else 0)})</td></tr>
            <tr><td>Templated by spend</td><td>{pct(templated_spend/total_spend)}</td></tr>
            <tr><td>Ads with purchases &gt; 0</td><td>{sum(1 for a in ads if a['purchases'] > 0)}</td></tr>
          </tbody></table>
        </div>
      </div>
    </div>
    """


# ---- Brands summary table (all-brands tab only) ----
def render_brands_summary():
    rows = []
    for b in BRANDS:
        t = b["agg"]
        rows.append(f"""
        <tr class="brand-row" data-brand="{b['slug']}">
          <td><strong>{html.escape(b['account']['name'])}</strong> <span class="muted">{html.escape(b['account']['id'])}</span></td>
          <td>{intf(t['ad_count'])}</td>
          <td>{usd(t['total_spend'])}</td>
          <td>{intf(t['total_purchases'])}</td>
          <td>{usd(t['total_revenue'])}</td>
          <td>{usd(t['avg_cpa'])}</td>
          <td class="{roas_class(t['avg_roas'])}">{num(t['avg_roas'], 2)}x</td>
          <td>{intf(t['test_count'])}</td>
          <td class="muted">{html.escape(b['date_range']['label'])}</td>
        </tr>
        """)
    return f"""
    <div class="panel">
      <div class="panel-h"><h2>Brands</h2><span class="note">click a row to drill in</span></div>
      <div class="scroll">
        <table class="brands-table">
          <thead><tr>
            <th>Brand</th><th>Ads</th><th>Spend</th><th>Purch</th><th>Revenue</th>
            <th>CPA</th><th>ROAS</th><th>Tests</th><th>Window</th>
          </tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    """


# ---- Tab content ----
def render_all_brands_tab():
    return f"""
    <div class="tab-panel active" id="tab-all">
      <div class="kpis">{kpi_row(AGG, f"across {len(BRANDS)} brands")}</div>
      {render_brands_summary()}
      <div class="panel">
        <div class="panel-h">
          <h2>All creatives (across brands)</h2>
          <span class="note">click a column header to sort</span>
        </div>
        <div class="toolbar">
          <input type="search" class="search-input" data-target="table-all" placeholder="Filter by ad name, brand, creative name, campaign…" />
          <span class="count" data-count-for="table-all">{len(ALL_ADS)} creatives</span>
        </div>
        {render_ads_table(ALL_ADS, "table-all", show_brand=True)}
      </div>
      {render_top_panels(ALL_ADS, show_brand=True)}
      {render_dq(ALL_ADS)}
    </div>
    """


def render_brand_meta_banner(b):
    m = b.get("meta") or {}
    if not any(m.values()):
        return ""
    bits = []
    if m.get("media_buyer"):
        bits.append(f'<span><strong>Media buyer:</strong> {html.escape(m["media_buyer"])}</span>')
    if m.get("pod_leader"):
        bits.append(f'<span><strong>POD lead:</strong> {html.escape(m["pod_leader"])}</span>')
    if m.get("tab"):
        bits.append(f'<span><strong>Type:</strong> {html.escape(m["tab"])}</span>')
    if m.get("target_type") and m.get("target_value"):
        bits.append(f'<span><strong>Target:</strong> {html.escape(m["target_type"])} {m["target_value"]}</span>')
    if m.get("budget"):
        bits.append(f'<span><strong>Budget:</strong> ${m["budget"]:,}/mo</span>')
    return f'<div class="brand-banner">{" · ".join(bits)}</div>'


def render_campaigns_table(campaigns, table_id, total_count):
    if not campaigns:
        return '<div class="empty-note" style="padding: 24px;">No campaigns delivered in window.</div>'
    rows = []
    for c in campaigns:
        rows.append(f"""
        <tr>
          <td>{html.escape(c.get('name') or '')}</td>
          <td>{usd(c.get('spend', 0))}</td>
        </tr>
        """)
    note = ""
    if total_count > len(campaigns):
        note = f' <span class="muted">(top {len(campaigns)} of {total_count})</span>'
    return f"""
    <div class="scroll">
      <table id="{table_id}" class="campaigns-table">
        <thead><tr><th>Campaign{note}</th><th>30d spend</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    """


def render_brand_tab(b):
    has_ads = bool(b["ads"])
    meta_banner = render_brand_meta_banner(b)
    if has_ads:
        kpis = kpi_row(b['agg'], f"{b['date_range']['label']} · {b['account']['id']}")
        body = f"""
        <div class="panel">
          <div class="panel-h">
            <h2>All creatives</h2>
            <span class="note">click a column header to sort</span>
          </div>
          <div class="toolbar">
            <input type="search" class="search-input" data-target="table-{b['slug']}" placeholder="Filter by ad name, creative name, campaign…" />
            <span class="count" data-count-for="table-{b['slug']}">{len(b['ads'])} creatives</span>
          </div>
          {render_ads_table(b['ads'], f"table-{b['slug']}", show_brand=False)}
        </div>
        {render_top_panels(b['ads'], show_brand=False)}
        {render_dq(b['ads'])}
        """
    else:
        # KPI row from perf totals (no ad_count/test_count/hook/hold)
        t = b["totals"]
        kpis = "\n".join([
            kpi_card("Total spend", usd(t.get("total_spend", 0)), meta=b['date_range']['label']),
            kpi_card("Purchases / conversions", intf(t.get("total_purchases", 0)), meta=f"from {t.get('perf_weeks_used', 0)}-week rollup"),
            kpi_card("Revenue", usd(t.get("total_revenue", 0))),
            kpi_card("Avg CPA", usd(t.get("avg_cpa", 0))),
            kpi_card("Avg ROAS", f"{num(t.get('avg_roas', 0), 2)}x", meta="spend-weighted", accent=t.get("avg_roas", 0) >= 2.0),
        ])
        body = f"""
        <div class="panel">
          <div class="panel-h">
            <h2>Campaigns</h2>
            <span class="note">last 30 days · {b['campaign_count_total']} total</span>
          </div>
          {render_campaigns_table(b['campaigns'], f"table-{b['slug']}", b['campaign_count_total'])}
        </div>
        <div class="panel">
          <div class="panel-h"><h2>Per-creative data</h2><span class="note">pending</span></div>
          <div class="empty-note" style="padding: 24px;">
            Per-ad creative metrics (thumbnails, hook/hold rate, test status) populate via the scheduled Monday refresh agent.
            Once that runs, this brand will show the same creative table as Slumberkins / Xtrema.
          </div>
        </div>
        """
    return f"""
    <div class="tab-panel" id="tab-{b['slug']}">
      {meta_banner}
      <div class="kpis">{kpis}</div>
      {body}
    </div>
    """


# ---- Tab strip ----
def _tab_badge_text(b):
    """Show ad count if available, else spend (in $k)."""
    if b["ads"]:
        return intf(len(b["ads"]))
    s = b["agg"].get("total_spend", 0) or 0
    if s >= 1000:
        return f"${s/1000:.0f}k"
    return f"${s:.0f}"


def render_tab_strip():
    tabs = [('all', 'All brands', f'{len(BRANDS)}', True)]
    for b in BRANDS:
        tabs.append((b["slug"], b["account"]["name"], _tab_badge_text(b), False))
    return "\n".join(
        f'<button class="tab{" active" if active else ""}" data-tab="{slug}">{html.escape(label)} <span class="tab-badge">{count}</span></button>'
        for slug, label, count, active in tabs
    )


# ---- Sniff oldest generated_at for footer ----
generated = max((b["generated_at"] or "" for b in BRANDS), default="")

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Creatives Performance</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --black: #010101;
    --purple: #6c2fce;
    --purple-2: #8b56e3;
    --lime: #c7f300;
    --white: #ffffff;
    --bg: var(--black);
    --panel: #0a0a0c;
    --panel-2: #111114;
    --border: rgba(255,255,255,0.08);
    --border-2: rgba(255,255,255,0.14);
    --text: var(--white);
    --muted: rgba(255,255,255,0.55);
    --muted-2: rgba(255,255,255,0.38);
    --accent: var(--purple);
    --good: var(--lime);
    --warn: #ffb84d;
    --bad: #ff5b5b;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background:
      radial-gradient(900px 500px at 85% -10%, rgba(108,47,206,0.18) 0%, transparent 60%),
      radial-gradient(700px 400px at 0% 110%, rgba(199,243,0,0.05) 0%, transparent 55%),
      var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 36px 24px 64px;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }}
  .wrap {{ max-width: 1500px; margin: 0 auto; }}
  header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; gap: 16px; flex-wrap: wrap; }}
  h1 {{ font-size: 24px; margin: 0; letter-spacing: -0.02em; font-weight: 600; }}
  h1 .accent {{ color: var(--lime); }}
  .sub {{ color: var(--muted); font-size: 13px; }}
  .badge {{
    display: inline-block; padding: 4px 10px; border-radius: 999px;
    background: rgba(108,47,206,0.18); color: var(--lime);
    font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    border: 1px solid rgba(108,47,206,0.35);
  }}

  /* Tab strip */
  .tabstrip {{
    display: flex; gap: 6px; padding: 4px; background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; margin-bottom: 22px; flex-wrap: wrap;
  }}
  .tab {{
    background: transparent; border: 0; color: var(--muted); font-family: inherit; font-size: 13px;
    font-weight: 500; padding: 9px 14px; border-radius: 8px; cursor: pointer;
    display: inline-flex; align-items: center; gap: 8px; transition: background 120ms, color 120ms;
  }}
  .tab:hover {{ color: var(--text); background: rgba(255,255,255,0.03); }}
  .tab.active {{ background: var(--purple); color: var(--white); }}
  .tab.active .tab-badge {{ background: rgba(255,255,255,0.18); color: var(--white); }}
  .tab-badge {{
    background: rgba(255,255,255,0.06); color: var(--muted); font-size: 10px;
    padding: 2px 7px; border-radius: 999px; font-weight: 600; letter-spacing: 0.04em;
  }}

  /* Tab panels */
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  /* KPIs */
  .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 24px; }}
  @media (max-width: 1000px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  .kpi {{
    background: linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
    border: 1px solid var(--border); border-radius: 14px; padding: 18px 18px 16px;
    position: relative; overflow: hidden;
  }}
  .kpi::before {{
    content: ""; position: absolute; inset: 0;
    background: radial-gradient(300px 120px at 110% 0%, rgba(108,47,206,0.10), transparent 70%);
    pointer-events: none;
  }}
  .kpi .label {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 8px; font-weight: 500; }}
  .kpi .value {{ font-size: 26px; font-weight: 600; letter-spacing: -0.025em; }}
  .kpi .meta {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
  .kpi.accent .value {{ color: var(--lime); }}

  /* Panels */
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }}
  .panel + .panel {{ margin-top: 20px; }}
  .panel-h {{
    padding: 16px 20px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
  }}
  .panel-h h2 {{ margin: 0; font-size: 14px; font-weight: 600; letter-spacing: -0.01em; }}
  .panel-h .note {{ color: var(--muted); font-size: 12px; }}

  /* Toolbar */
  .toolbar {{ display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }}
  .toolbar input[type=search] {{
    background: var(--panel-2); border: 1px solid var(--border-2); color: var(--text);
    font-family: inherit; font-size: 13px; padding: 7px 10px; border-radius: 8px; outline: none; min-width: 280px;
  }}
  .toolbar input[type=search]:focus {{ border-color: var(--purple-2); }}
  .toolbar .count {{ color: var(--muted); font-size: 12px; margin-left: auto; }}

  /* Tables */
  .scroll {{ overflow-x: auto; }}
  table.ads-table, table.brands-table {{ width: 100%; border-collapse: collapse; min-width: 1100px; }}
  th, td {{ padding: 10px 12px; text-align: right; font-variant-numeric: tabular-nums; font-size: 13px; white-space: nowrap; vertical-align: middle; }}
  th:first-child, td:first-child {{ text-align: left; position: sticky; left: 0; background: var(--panel); z-index: 1; }}
  thead th:first-child {{ background: var(--panel-2); }}
  thead th {{
    color: var(--muted); font-size: 10px; font-weight: 600;
    letter-spacing: 0.10em; text-transform: uppercase;
    border-bottom: 1px solid var(--border); background: var(--panel-2);
    cursor: pointer; user-select: none;
  }}
  thead th.sort-asc::after {{ content: " ↑"; color: var(--lime); }}
  thead th.sort-desc::after {{ content: " ↓"; color: var(--lime); }}
  tbody tr {{ border-bottom: 1px solid var(--border); }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody tr:hover td {{ background: rgba(108,47,206,0.06); }}
  tbody tr:hover td:first-child {{ background: rgba(108,47,206,0.06); }}

  .pos {{ color: var(--lime); font-weight: 500; }}
  .warn {{ color: var(--warn); font-weight: 500; }}
  .neg {{ color: var(--bad); font-weight: 500; }}
  .neu {{ color: var(--muted); }}
  .muted {{ color: var(--muted-2); font-weight: 400; font-size: 11px; }}

  /* Creative cell */
  .creative-cell {{ display: flex; align-items: center; gap: 12px; max-width: 460px; min-width: 360px; }}
  .thumb {{ width: 56px; height: 56px; object-fit: cover; border-radius: 8px; background: #050507; border: 1px solid var(--border); flex-shrink: 0; }}
  .thumb.empty {{ background: repeating-linear-gradient(45deg, #111114, #111114 4px, #0a0a0c 4px, #0a0a0c 8px); }}
  .creative-meta {{ display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
  .ad-name {{ font-weight: 500; color: var(--text); font-size: 13px; overflow: hidden; text-overflow: ellipsis; }}
  .cn {{ font-size: 11px; color: var(--muted); }}
  .cmp {{ font-size: 11px; color: var(--muted-2); }}

  /* Brand pill (in cross-brand table) */
  .brand-pill {{
    display: inline-block; font-size: 11px; padding: 3px 8px; border-radius: 999px;
    background: rgba(108,47,206,0.16); color: #c8b3ff; border: 1px solid rgba(108,47,206,0.32);
    font-weight: 500;
  }}

  /* Tags */
  .tag {{
    display: inline-block; font-size: 9px; padding: 2px 6px; border-radius: 4px;
    font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-left: 6px;
  }}
  .tag.templ {{ background: rgba(255,184,77,0.16); color: var(--warn); border: 1px solid rgba(255,184,77,0.32); }}
  .tag.test {{ background: rgba(199,243,0,0.14); color: var(--lime); border: 1px solid rgba(199,243,0,0.32); }}

  /* Brands summary table */
  .brands-table tbody tr {{ cursor: pointer; }}
  .brands-table tbody tr:hover {{ background: rgba(108,47,206,0.06); }}

  /* Bar charts */
  .bar-wrap {{ display: grid; gap: 8px; padding: 18px 20px 22px; }}
  .bar-row {{ display: grid; grid-template-columns: 260px 1fr 120px; align-items: center; gap: 12px; font-size: 13px; }}
  .bar-label {{ color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .bar-sub {{ color: var(--muted-2); font-size: 11px; margin-left: 6px; }}
  .bar-brand {{
    display: inline-block; font-size: 9px; padding: 2px 6px; border-radius: 4px; margin-left: 6px;
    background: rgba(108,47,206,0.16); color: #c8b3ff; border: 1px solid rgba(108,47,206,0.32);
    font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
  }}
  .bar-track {{ height: 16px; background: rgba(255,255,255,0.04); border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; transition: width 200ms ease; }}
  .bar-value {{ text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }}

  /* DQ */
  .dq-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
  @media (max-width: 900px) {{ .dq-grid {{ grid-template-columns: 1fr; }} }}
  .dq-cell {{ padding: 16px 20px; border-top: 1px solid var(--border); }}
  .dq-cell + .dq-cell {{ border-left: 1px solid var(--border); }}
  .dq-cell h3 {{ margin: 0 0 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.10em; color: var(--muted); font-weight: 600; }}
  .dq-cell table {{ min-width: auto; }}
  .dq-cell th, .dq-cell td {{ padding: 6px 8px; text-align: left; }}
  .empty-note {{ color: var(--muted-2); font-style: italic; padding: 10px 4px; }}

  footer {{ margin-top: 32px; color: var(--muted-2); font-size: 12px; }}

  /* Brand info banner */
  .brand-banner {{
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 10px;
    padding: 10px 14px; font-size: 12px; color: var(--muted);
    display: flex; gap: 18px; flex-wrap: wrap; margin-bottom: 16px;
  }}
  .brand-banner strong {{ color: var(--text); font-weight: 500; }}

  /* Campaigns table */
  table.campaigns-table {{ width: 100%; border-collapse: collapse; }}
  table.campaigns-table th, table.campaigns-table td {{
    padding: 10px 14px; text-align: right; font-variant-numeric: tabular-nums; font-size: 13px;
  }}
  table.campaigns-table th:first-child, table.campaigns-table td:first-child {{ text-align: left; }}
  table.campaigns-table thead th {{
    color: var(--muted); font-size: 10px; font-weight: 600; letter-spacing: 0.10em; text-transform: uppercase;
    border-bottom: 1px solid var(--border); background: var(--panel-2);
  }}
  table.campaigns-table tbody tr {{ border-bottom: 1px solid var(--border); }}
  table.campaigns-table tbody tr:hover td {{ background: rgba(108,47,206,0.06); }}

  /* Thumb button (clickable creative) */
  .thumb-btn {{
    position: relative; padding: 0; border: 0; background: transparent;
    cursor: pointer; border-radius: 8px; flex-shrink: 0; display: block; line-height: 0;
  }}
  .thumb-btn .thumb {{ display: block; transition: transform 120ms, box-shadow 120ms; }}
  .thumb-btn:hover .thumb {{ transform: scale(1.04); box-shadow: 0 4px 16px rgba(108,47,206,0.32); }}
  .thumb-btn:focus-visible {{ outline: 2px solid var(--lime); outline-offset: 2px; }}
  .thumb-play {{
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    color: var(--white); font-size: 20px; text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    background: linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,0.32) 100%);
    border-radius: 8px; opacity: 0.85; pointer-events: none;
  }}
  .thumb-btn:hover .thumb-play {{ opacity: 1; }}

  /* Modal */
  .modal-backdrop {{
    position: fixed; inset: 0; background: rgba(1,1,1,0.84);
    backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
    display: none; align-items: center; justify-content: center;
    z-index: 1000; padding: 24px;
  }}
  .modal-backdrop.open {{ display: flex; }}
  .modal {{
    background: var(--panel); border: 1px solid var(--border-2); border-radius: 14px;
    max-width: 1100px; width: 100%; max-height: 90vh; overflow: hidden;
    display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr); gap: 0;
    box-shadow: 0 24px 72px rgba(0,0,0,0.6);
  }}
  @media (max-width: 800px) {{ .modal {{ grid-template-columns: 1fr; max-height: 95vh; overflow-y: auto; }} }}
  .modal-media {{ background: #000; display: flex; align-items: center; justify-content: center; min-height: 320px; max-height: 80vh; }}
  .modal-media video, .modal-media img {{ max-width: 100%; max-height: 80vh; display: block; object-fit: contain; }}
  .modal-info {{ padding: 22px 24px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }}
  .modal-info h3 {{ margin: 0; font-size: 16px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.3; }}
  .modal-info .meta-line {{ color: var(--muted); font-size: 12px; }}
  .modal-info .brand-pill {{ align-self: flex-start; }}
  .modal-stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 4px; }}
  .modal-stat {{ background: var(--panel-2); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }}
  .modal-stat .lbl {{ color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.10em; }}
  .modal-stat .val {{ font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; margin-top: 2px; }}
  .modal-close {{
    position: absolute; top: 16px; right: 16px; width: 36px; height: 36px;
    border-radius: 999px; border: 1px solid var(--border-2); background: rgba(10,10,12,0.85);
    color: var(--white); font-size: 18px; cursor: pointer; z-index: 1001;
    display: flex; align-items: center; justify-content: center;
  }}
  .modal-close:hover {{ background: var(--purple); border-color: var(--purple-2); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>Creatives <span class="accent">Performance</span></h1>
      <div class="sub">Multi-brand dashboard · {len(BRANDS)} brand{'s' if len(BRANDS) != 1 else ''} · generated {html.escape(generated)}</div>
    </div>
    <div>
      <span class="badge">Feasibility test · v2</span>
    </div>
  </header>

  <div class="tabstrip" role="tablist">{render_tab_strip()}</div>

  {render_all_brands_tab()}
  {''.join(render_brand_tab(b) for b in BRANDS)}

  <div class="modal-backdrop" id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <button type="button" class="modal-close" id="modal-close" aria-label="Close">✕</button>
    <div class="modal" role="document">
      <div class="modal-media" id="modal-media"></div>
      <div class="modal-info">
        <span class="brand-pill" id="modal-brand"></span>
        <h3 id="modal-title"></h3>
        <div class="meta-line" id="modal-campaign"></div>
        <div class="modal-stats">
          <div class="modal-stat"><div class="lbl">Spend</div><div class="val" id="modal-spend"></div></div>
          <div class="modal-stat"><div class="lbl">ROAS</div><div class="val" id="modal-roas"></div></div>
          <div class="modal-stat"><div class="lbl">Purchases</div><div class="val" id="modal-purch"></div></div>
          <div class="modal-stat"><div class="lbl">Asset type</div><div class="val" id="modal-type"></div></div>
        </div>
        <div class="meta-line" id="modal-asset-url" style="word-break: break-all; font-size: 11px;"></div>
      </div>
    </div>
  </div>

  <footer>
    Source: GoMarble MCP · facebook_get_adaccount_insights (level=ad, last_30d, per-campaign) + facebook_get_ad_creative_details.
    {' · '.join(f"{html.escape(b['account']['name'])}: {html.escape(b['account']['id'])}" for b in BRANDS)}.
  </footer>
</div>

<script>
(function () {{
  // --- Tab switching ---
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-panel');
  function activate(slug) {{
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === slug));
    panels.forEach(p => p.classList.toggle('active', p.id === 'tab-' + slug));
    // Persist in hash so reloads remember the tab
    if (history && history.replaceState) history.replaceState(null, '', '#' + slug);
  }}
  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));
  // Restore from URL hash
  const hash = (location.hash || '').replace('#', '');
  if (hash) {{
    const tab = document.querySelector('.tab[data-tab="' + hash + '"]');
    if (tab) activate(hash);
  }}

  // Brand summary row → jump to that brand's tab
  document.querySelectorAll('.brand-row').forEach(r => {{
    r.addEventListener('click', () => activate(r.dataset.brand));
  }});

  // --- Sortable tables ---
  function readCell(row, idx, type) {{
    const cell = row.cells[idx];
    if (!cell) return type === 'num' ? -Infinity : '';
    if (type === 'num') {{
      const t = cell.textContent.replace(/[$,x%]/g, '').trim();
      const n = parseFloat(t);
      return isNaN(n) ? -Infinity : n;
    }}
    return cell.textContent.trim().toLowerCase();
  }}
  document.querySelectorAll('table.ads-table').forEach(tbl => {{
    const tbody = tbl.tBodies[0];
    const headers = tbl.tHead.rows[0].cells;
    let current = {{ idx: -1, asc: false }};
    // Find which column is initially marked sort-desc
    for (let i = 0; i < headers.length; i++) {{
      if (headers[i].classList.contains('sort-desc')) {{ current = {{ idx: i, asc: false }}; break; }}
    }}
    function sortBy(idx, type) {{
      const rows = Array.from(tbody.rows);
      const asc = current.idx === idx ? !current.asc : false;
      rows.sort((a, b) => {{
        const va = readCell(a, idx, type);
        const vb = readCell(b, idx, type);
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
      }});
      rows.forEach(r => tbody.appendChild(r));
      for (let i = 0; i < headers.length; i++) headers[i].classList.remove('sort-asc', 'sort-desc');
      headers[idx].classList.add(asc ? 'sort-asc' : 'sort-desc');
      current = {{ idx, asc }};
    }}
    for (let i = 0; i < headers.length; i++) {{
      const type = headers[i].dataset.type || 'text';
      headers[i].addEventListener('click', () => sortBy(i, type));
    }}
  }});

  // --- Creative preview modal ---
  const modal = document.getElementById('modal');
  const modalMedia = document.getElementById('modal-media');
  function openModal(btn) {{
    const url = btn.dataset.assetUrl;
    const type = btn.dataset.assetType;
    const thumb = btn.dataset.thumbUrl;
    document.getElementById('modal-title').textContent = btn.dataset.adName || '';
    document.getElementById('modal-campaign').textContent = btn.dataset.campaign || '';
    document.getElementById('modal-brand').textContent = btn.dataset.brand || '';
    const spend = parseFloat(btn.dataset.spend || '0');
    const roas = parseFloat(btn.dataset.roas || '0');
    document.getElementById('modal-spend').textContent = '$' + spend.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
    document.getElementById('modal-roas').textContent = roas.toFixed(2) + 'x';
    document.getElementById('modal-purch').textContent = btn.dataset.purch || '0';
    document.getElementById('modal-type').textContent = type === 'video' ? 'Video' : 'Image';
    document.getElementById('modal-asset-url').textContent = url;
    modalMedia.innerHTML = '';
    if (type === 'video') {{
      const v = document.createElement('video');
      v.src = url;
      v.controls = true;
      v.autoplay = true;
      v.playsInline = true;
      v.preload = 'metadata';
      if (thumb) v.poster = thumb;
      modalMedia.appendChild(v);
    }} else {{
      const img = document.createElement('img');
      img.src = url;
      img.alt = '';
      modalMedia.appendChild(img);
    }}
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }}
  function closeModal() {{
    modal.classList.remove('open');
    modalMedia.innerHTML = '';  // stops any playing video
    document.body.style.overflow = '';
  }}
  document.querySelectorAll('.thumb-btn').forEach(btn => {{
    btn.addEventListener('click', () => openModal(btn));
  }});
  document.getElementById('modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', e => {{ if (e.target === modal) closeModal(); }});
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape' && modal.classList.contains('open')) closeModal(); }});

  // --- Search filters ---
  document.querySelectorAll('.search-input').forEach(input => {{
    const targetId = input.dataset.target;
    const tbl = document.getElementById(targetId);
    if (!tbl) return;
    const counter = document.querySelector('[data-count-for="' + targetId + '"]');
    const total = tbl.tBodies[0].rows.length;
    input.addEventListener('input', () => {{
      const q = input.value.toLowerCase().trim();
      let visible = 0;
      for (const row of tbl.tBodies[0].rows) {{
        const text = row.textContent.toLowerCase();
        const match = !q || text.includes(q);
        row.style.display = match ? '' : 'none';
        if (match) visible++;
      }}
      if (counter) counter.textContent = q ? (visible + ' of ' + total + ' creatives') : (total + ' creatives');
    }});
  }});
}})();
</script>
</body>
</html>
"""

(ROOT / "index.html").write_text(HTML)
print(f"Wrote index.html ({len(HTML):,} chars)")
print(f"Brands: {[b['account']['name'] for b in BRANDS]}")
print(f"Aggregate: {AGG['ad_count']} ads, ${AGG['total_spend']:,.2f} spend, {AGG['avg_roas']:.2f}x ROAS")
print(f"Tests shipped (across all brands): {AGG['test_count']} ({AGG['test_pct']*100:.0f}%)")
for b in BRANDS:
    t = b["agg"]
    print(f"  · {b['account']['name']}: {t['ad_count']} ads, ${t['total_spend']:,.2f}, ROAS {t['avg_roas']:.2f}x, tests {t['test_count']}")
