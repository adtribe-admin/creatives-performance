## Apify (web scraping)

Use the Apify REST API directly with curl. The token is available as `$APIFY_TOKEN`.
Do not write DIY scraping scripts; run Apify actors and process their datasets.

**Quick run (actors that finish under 5 min):**
```bash
curl -X POST "https://api.apify.com/v2/actors/USERNAME~ACTOR_NAME/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ ...actor input... }'
```

**Long runs (start, poll, fetch):**
```bash
# start
curl -X POST "https://api.apify.com/v2/actors/USERNAME~ACTOR_NAME/runs" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" -d '{ ...input... }'
# poll data.status until SUCCEEDED
curl -H "Authorization: Bearer $APIFY_TOKEN" "https://api.apify.com/v2/actor-runs/RUN_ID"
# fetch results (defaultDatasetId from the run object)
curl -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/datasets/DATASET_ID/items?format=json&limit=1000"
```

**Notes:**
- Actor ID format is `username~actor-name` (tilde, not slash).
- Check an actor's input schema first: `https://apify.com/USERNAME/ACTOR_NAME/input-schema`
- Use `fields=` on dataset requests to keep responses small; filter and rank locally with Python.
- If `$APIFY_TOKEN` is empty, the session is not using the shared AdTribe cloud environment; ask the user to select it (it also allowlists `api.apify.com`).

**Proven actors (AdTribe):**
- X posts: `apidojo~tweet-scraper` (advanced-search queries, `min_faves:` floors, cheap)
- TikTok: `clockworks~tiktok-scraper` (MOST_LIKED + PAST_WEEK; still filter dates locally)
- Reddit: `trudax~reddit-scraper-lite` (subreddit top/?t=week URLs; slow, ~20 min)
- LinkedIn posts: `harvestapi~linkedin-post-search` (no cookies needed)
- Instagram: weak for recent windows; use a 2-4 week trending-reels lens instead
