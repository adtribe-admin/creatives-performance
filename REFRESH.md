# Creatives Performance — Weekly Refresh Procedure

This file is read by the scheduled Claude agent every Monday. The agent has access to:
- GoMarble MCP tools (`facebook_*`)
- The `gh` CLI for cloning/pushing this repo
- The `adtribe-admin/accounts-performance-weekly` repo for the canonical accounts list

## Goal

Refresh the per-brand `data.json` files in `brands/<slug>/` and rebuild `index.html`,
then commit and push so GitHub Pages serves the latest data at
https://adtribe-admin.github.io/creatives-performance/

## Steps

1. **Clone or pull this repo:**
   ```bash
   gh repo clone adtribe-admin/creatives-performance /tmp/cpl || (cd /tmp/cpl && git pull --rebase)
   ```

2. **Refresh the accounts master file** from the sibling repo (this is the source
   of truth for which Meta accounts to include and their POD/budget metadata):
   ```bash
   gh api repos/adtribe-admin/accounts-performance-weekly/contents/data/accounts.json \
     --jq '.content' | base64 -d > /tmp/cpl/raw/accounts_master.json
   ```

3. **For each Meta + covered account in `accounts_master.json`**, pull last-30d
   campaigns via GoMarble MCP:
   ```
   facebook_get_adaccount_insights(
     act_id="act_<gomarble_id>",
     level="campaign",
     date_preset="last_30d",
     fields=["campaign_id", "campaign_name", "spend"],
     filtering=[{"field":"impressions","operator":"GREATER_THAN","value":0}],
     sort="spend_descending",
   )
   ```
   Save the combined result into `raw/campaigns_YYYY-MM-DD.json` matching the
   shape of the existing file (one block per account, indexed by act_id).

4. **For each (account, campaign) pair**, pull ad-level insights:
   ```
   facebook_get_adaccount_insights(
     act_id, level="ad", date_preset="last_30d",
     fields=["ad_name","spend","impressions","clicks","ctr","cpm","cpc",
             "actions","action_values","purchase_roas","video_thruplay_watched_actions"],
     filtering=[{"field":"campaign.id","operator":"EQUAL","value":<campaign_id>},
                {"field":"impressions","operator":"GREATER_THAN","value":0}],
     sort="spend_descending",
   )
   ```
   Big-spend campaigns (>$10k) will exceed the inline token limit and auto-save
   to disk — parse from the saved file path returned in the error message.

5. **Enrich each account with creative metadata:**
   ```
   facebook_get_ad_creative_details(act_id, ad_ids=[<all ad_ids for this account>])
   ```
   This populates `creative_id`, `creative_name`, and the templated-name flag.

6. **For each ad row**, derive:
   - `video_3s` = `video_view` value from `actions[]`
   - `thruplays` = `video_view` value from `video_thruplay_watched_actions[]`
   - `hook_rate` = `video_3s / impressions`
   - `hold_rate` = `thruplays / video_3s`
   - `asset_url`, `asset_type` from the response's `cdn_asset_url` and
     `cdn_thumbnail_url` (mp4 = video, jpg = image; `<uuid>_<uuid>.jpg` thumb
     means the mp4 asset lives at `<uuid1>.mp4`)

7. **Run the pipeline** to write per-brand `data.json` files:
   ```bash
   cd /tmp/cpl && python3 pipeline.py
   ```
   `pipeline.py` reads `raw/accounts_master.json` and `raw/campaigns_*.json`,
   merges with any per-ad data the agent prepared, and writes brand files.

8. **Rebuild the dashboard:**
   ```bash
   python3 build.py
   ```

9. **Sanity checks before pushing:**
   - `len(brands/*/data.json)` should equal the number of Meta+covered accounts in master
   - At least the high-spend brands should have non-zero `total_spend`
   - `index.html` should be 100KB+
   - Tab strip in HTML should show all brand names

10. **Commit and push:**
    ```bash
    cd /tmp/cpl
    git add -A
    git commit -m "Refresh data through $(date -u +%Y-%m-%d)" || echo "no changes"
    git push
    ```

11. **GitHub Pages auto-deploys** within ~30 seconds. The live URL is
    https://adtribe-admin.github.io/creatives-performance/

## What NOT to change

- Do NOT edit `index.html` directly — `build.py` regenerates it every run.
- Do NOT edit `brands/<slug>/data.json` directly — `pipeline.py` regenerates them.
- The brand slug derived from `accounts_master.json` "name" field is authoritative.
  If a brand's master name changes, the agent should rename the folder accordingly.

## Known caveats

- The upstream `accounts-performance-weekly` master file occasionally has identical
  perf arrays across multiple brands (BrooklynMade, Dododots, Wholesale Jewelry
  shared the same 4-week spend at first pull). When in doubt, trust ad-level
  totals over perf rollups — the per-ad data takes precedence in `pipeline.py`.
- Some accounts return a transient `(#200) permission denied` error. Retry once;
  if it persists, leave that brand's `campaign_error` field set in `data.json`
  and notify the human via the activity log.
- The full per-ad pull across all 37 accounts is ~250 MCP calls. Chunk into
  parallel batches of 10–15 to avoid rate limits.
