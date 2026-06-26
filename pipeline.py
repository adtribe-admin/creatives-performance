#!/usr/bin/env python3
"""Data pipeline for the multi-brand creatives performance dashboard.

Inputs (in raw/):
- accounts_master.json — agency-wide accounts list from accounts-performance-weekly
  repo (https://github.com/adtribe-admin/accounts-performance-weekly). Includes
  weekly perf rollups per brand for last 13 weeks.
- campaigns_<date>.json — campaign lists pulled today via GoMarble MCP, one
  block per account with campaign_id / campaign_name / spend.

Outputs (in brands/<slug>/data.json):
- One file per Meta-and-covered brand with: account info, totals (computed
  from last 4 weeks of perf), campaigns array (top by spend), optional `ads`
  array if a per-ad creative pull is available.

Brands that already have richer per-ad data (Slumberkins, Xtrema) keep their
existing `ads` arrays; this pipeline only refreshes totals + campaigns and
preserves whatever's already there.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
BRANDS_DIR = ROOT / "brands"
WEEKS_FOR_30D = 4  # sum last 4 weeks of weekly perf for the 30-day KPI window


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def meta_accounts():
    """Iterate the Meta + GoMarble-covered accounts from the master file."""
    master = json.loads((RAW / "accounts_master.json").read_text())
    for a in master:
        if a.get("platform") != "Meta" or not a.get("covered"):
            continue
        raw_id = a.get("gomarble_id", "") or ""
        norm = raw_id[4:] if raw_id.startswith("act_") else raw_id
        if not norm:
            continue
        yield {
            "act_id": f"act_{norm}",
            "name": a["name"],
            "slug": slugify(a["name"]),
            "tab": a.get("tab"),
            "media_buyer": a.get("media_buyer"),
            "pod_leader": a.get("pod_leader"),
            "target_type": a.get("target_type"),
            "target_value": a.get("target_value"),
            "budget": a.get("budget"),
            "currency": a.get("currency"),
            "perf": a.get("perf", {}),
        }


def totals_from_perf(perf):
    """Compute trailing-30d totals from the weekly perf arrays."""
    perf = perf or {}
    weeks = perf.get("weeks", [])
    spend_w = perf.get("spend", [])
    rev_w = perf.get("rev", [])
    conv_w = perf.get("conv", [])
    roas_w = perf.get("roas", [])
    # Take last N complete weeks
    n = min(WEEKS_FOR_30D, len(spend_w))
    if n == 0:
        return {
            "total_spend": 0, "total_revenue": 0, "total_purchases": 0,
            "avg_cpa": 0, "avg_roas": 0,
            "perf_weeks_used": 0, "perf_window": None,
        }
    spend = sum(x or 0 for x in spend_w[-n:])
    rev = sum(x or 0 for x in rev_w[-n:])
    conv = sum(x or 0 for x in conv_w[-n:])
    window = None
    if weeks:
        window = {"from": weeks[-n], "to_week_starting": weeks[-1]}
    return {
        "total_spend": round(spend, 2),
        "total_revenue": round(rev, 2),
        "total_purchases": int(conv),
        "avg_cpa": round(spend / conv, 2) if conv else 0,
        "avg_roas": round(rev / spend, 4) if spend else 0,
        "perf_weeks_used": n,
        "perf_window": window,
    }


def main():
    accounts = list(meta_accounts())
    campaigns_blob = json.loads((RAW / "campaigns_2026-06-25.json").read_text())
    camp_by_account = campaigns_blob["accounts"]

    for acct in accounts:
        slug = acct["slug"]
        brand_dir = BRANDS_DIR / slug
        brand_dir.mkdir(parents=True, exist_ok=True)
        existing = brand_dir / "data.json"
        prior = {}
        if existing.exists():
            try:
                prior = json.loads(existing.read_text())
            except json.JSONDecodeError:
                prior = {}

        totals = totals_from_perf(acct["perf"])

        camp_entry = camp_by_account.get(acct["act_id"], {})
        campaigns = camp_entry.get("campaigns", [])
        campaign_error = camp_entry.get("error")

        # Sort campaigns desc by spend and keep top 25 for the table
        campaigns_sorted = sorted(campaigns, key=lambda c: c.get("spend", 0), reverse=True)[:25]

        # Preserve any prior per-ad data (Slumberkins, Xtrema)
        ads = prior.get("ads", [])
        # If we have ads, recompute totals/test count from them (more accurate for those brands)
        if ads:
            total_spend = sum(a.get("spend", 0) for a in ads)
            total_purch = sum(a.get("purchases", 0) for a in ads)
            total_rev = sum(a.get("revenue", 0) for a in ads)
            total_imp = sum(a.get("impressions", 0) for a in ads)
            total_v3s = sum(a.get("video_3s", 0) for a in ads)
            total_thru = sum(a.get("thruplays", 0) for a in ads)
            tests = sum(1 for a in ads if "test" in (a.get("ad_name") or "").lower())
            ad_totals = {
                "ad_count": len(ads),
                "total_spend_from_ads": round(total_spend, 2),
                "total_impressions": total_imp,
                "total_purchases_from_ads": total_purch,
                "total_revenue_from_ads": round(total_rev, 2),
                "avg_cpa_from_ads": round(total_spend / total_purch, 2) if total_purch else 0,
                "avg_roas_from_ads": round(total_rev / total_spend, 4) if total_spend else 0,
                "test_count": tests,
                "test_pct": round(tests / len(ads), 4) if ads else 0,
                "blended_hook_rate": round(total_v3s / total_imp, 4) if total_imp else 0,
                "blended_hold_rate": round(total_thru / total_v3s, 4) if total_v3s else 0,
            }
        else:
            ad_totals = {"ad_count": 0, "test_count": 0, "test_pct": 0}

        out = {
            "account": {"id": acct["act_id"], "name": acct["name"]},
            "meta": {
                "tab": acct["tab"],
                "media_buyer": acct["media_buyer"],
                "pod_leader": acct["pod_leader"],
                "target_type": acct["target_type"],
                "target_value": acct["target_value"],
                "budget": acct["budget"],
                "currency": acct["currency"],
            },
            "generated_at": "2026-06-26T16:15:00Z",
            "date_range": prior.get("date_range") or {
                "since": "2026-05-27", "until": "2026-06-25", "label": "Last 30 days (campaign + last-4-weeks rollup)"
            },
            "totals": {**totals, **ad_totals},
            "campaigns": campaigns_sorted,
            "campaign_count_total": len(campaigns),
            "campaign_error": campaign_error,
            "ads": ads,  # may be empty for brands without a per-ad pull
        }
        (brand_dir / "data.json").write_text(json.dumps(out, indent=2))

    print(f"Wrote {len(accounts)} brand data.json files.")
    # Quick summary
    total_spend = sum(totals_from_perf(a["perf"])["total_spend"] for a in accounts)
    print(f"Agency 30d spend (from perf rollups): ${total_spend:,.0f}")
    print("Top 10 brands by spend:")
    bs = sorted([(a["name"], totals_from_perf(a["perf"])["total_spend"]) for a in accounts], key=lambda x: -x[1])
    for n, s in bs[:10]:
        print(f"  ${s:>10,.0f}  {n}")


if __name__ == "__main__":
    main()
