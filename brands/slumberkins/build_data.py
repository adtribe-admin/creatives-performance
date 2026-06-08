#!/usr/bin/env python3
"""Assemble data.json for creative-perf-lite from per-campaign GoMarble insights
   plus the creative_details_slim enrichment file.

Source: GoMarble MCP `facebook_get_adaccount_insights` (level=ad, last_30d) ran
per-campaign (the account-wide call hit Meta's 'reduce data' limit) on
2026-05-26 for act_1939402463050546 (Slumberkins), 2026-04-26 → 2026-05-25.
Creative IDs/names from `facebook_get_ad_creative_details` batch.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent
DETAILS_PATH = ROOT / "raw" / "creative_details_slim.json"

# Per-ad slim records: extracted manually from the 7 per-campaign insights
# responses. Fields: ad_id, ad_name, campaign_id, campaign_name, adset_id,
# adset_name, spend, impressions, clicks, ctr (decimal %), cpm, cpc,
# purchases (omni_purchase from actions or 0), revenue (omni_purchase from
# action_values or 0), roas (omni_purchase from purchase_roas or 0),
# thumb_url (cdn_thumbnail_url or empty).
ADS = [
    # ---- Campaign 1: PH | PRS | Creature Full of Feelings ----
    ("120242913171760256", "Carousel_V2", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 1054.67, 44082, 491, 1.113833, 23.925185, 2.148004, 41, 3167.97, 3.003755, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f0b07453-8904-4d77-b965-db02c976bf07.jpg"),
    ("120237065739150256", "Carousel_V3 | 4094", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 1040.92, 60205, 569, 0.945104, 17.289594, 1.829385, 14, 1319.96, 1.268071, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d7c58bfe-37e9-4d1f-bb84-8f5c381c9a97.jpg"),
    ("120237937752360256", "DSC_9231", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 417.83, 19672, 302, 1.535177, 21.239833, 1.383543, 67, 2869.16, 6.866812, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0687a993-55bd-405b-8c81-29cfa649aed4.jpg"),
    ("120237937585980256", "@diy.withthewears 8", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 369.06, 18473, 368, 1.992097, 19.978347, 1.00288, 6, 598.60, 1.621958, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/cf26ad6c-8652-4cee-b904-4ecb7ff12ab5.jpg"),
    ("120237937605660256", "@diy.withthewears 3", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 61.65, 3073, 30, 0.976245, 20.061829, 2.055, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/28969fb9-fa6b-4f59-8318-d0b1233868e1.jpg"),
    ("120235975064930256", "CFOF_Set_Social-13", "120235968232540256", "PH | PRS | Creature Full of Feelings | 11/5/25 | 4094", "120235974945040256", "PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094", 13.52, 679, 8, 1.178203, 19.911635, 1.69, 1, 118.50, 8.764793, ""),
    # ---- Campaign 2: PRS | Mixed Creatures Testing ----
    ("120244150294500256", "image (set) — copies (slumberkins_general)", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 363.94, 35336, 207, 0.585805, 10.299411, 1.758164, 2, 188.57, 0.518135, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/7988e4b7-be55-4663-b078-991d1d5420da.jpg"),
    ("120244150751700256", "video (gif_what_about) — copies (slumberkins_general)", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 361.05, 35533, 274, 0.771114, 10.160977, 1.317701, 7, 500.55, 1.386373, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/48661b03-1510-450c-bfb4-14a58c28b041_eda08f7a-7d0e-424b-babf-eb7d99699ac5.jpg"),
    ("120244616420370256", "image carousel (your_love_letter_ugc) — copies (slumberkins_general) – Copy", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 353.95, 32466, 133, 0.409659, 10.902175, 2.661278, 17, 547.75, 1.547535, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/8dcb4827-a862-47b7-8cb4-01264ac87e13.jpg"),
    ("120244616137230256", "image carousel (your_love_letter_arrow) — copies (slumberkins_general)", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 301.10, 29523, 125, 0.423399, 10.198828, 2.4088, 10, 2019.47, 6.706974, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3b61b662-bcb8-4302-a329-0ad695ee2733.jpg"),
    ("120244150666710256", "image (every_feeling_emotions) — copies (slumberkins_general)", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 165.65, 16869, 112, 0.66394, 9.819788, 1.479018, 1, 61.42, 0.370782, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4b7095ba-1a46-4a14-92e7-a61a6f62db26.jpg"),
    ("120244149688140256", "image carousel (in-stock_creatures) — copies (slumberkins_general)", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244149688150256", "PRS |  Mixed | Open + Exclusions | 7DC 1DV", 149.05, 12944, 74, 0.571693, 11.514988, 2.014189, 3, 313.27, 2.101778, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c2d9e587-190c-4de4-877b-9a2aacdab022.jpg"),
    ("120244362516430256", "Slumberkins_Keychains_PDP_Finals-44", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 78.35, 6088, 68, 1.116951, 12.86958, 1.152206, 0, 0, 0, ""),
    ("120244362516340256", "IMG_7869 2", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 14.39, 999, 31, 3.103103, 14.404404, 0.464194, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/458f44fa-db06-4557-9fb0-28e62eb64fbe_d580b24b-3ecf-44e1-953c-087cd55862da.jpg"),
    ("120244362516330256", "Slumberkins_Keychains_PDP_Finals-29", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 13.15, 963, 13, 1.349948, 13.655244, 1.011538, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9c6b025f-c4d8-47d1-b652-5dcfc6ec25fd.jpg"),
    ("120244362516360256", "Slumberkins_Keychains_Social_Finals-54", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 9.00, 729, 10, 1.371742, 12.345679, 0.9, 0, 0, 0, ""),
    ("120244362516420256", "Slumberkins_Keychains_PDP_Finals-14", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 4.40, 296, 2, 0.675676, 14.864865, 2.2, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe3488ad-738c-4054-bb8e-3938c5d7946f.jpg"),
    ("120244362516350256", "Slumberkins_Keychains_Social_Finals-19", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 3.43, 194, 4, 2.061856, 17.680412, 0.8575, 0, 0, 0, ""),
    ("120244362516240256", "Slumberkins_Keychains_Social_Finals-50", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 2.58, 192, 0, 0, 13.4375, 0, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/77594429-7a23-454b-8218-d1febeabf77c.jpg"),
    ("120244362516380256", "Slumberkins_Keychains_Social_Finals-18", "120244149688310256", "PRS | Mixed Creatures Testing | April 28, 2026", "120244362516230256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 1.23, 93, 1, 1.075269, 13.225806, 1.23, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3f8a206d-f8e8-4a19-8724-88598e32a636.jpg"),
    # ---- Campaign 3: PH | PRS | ASC | XL Hammerhead ----
    ("120242887065210256", "FounderStory_VID_JB_3", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 591.84, 16926, 360, 2.126905, 34.966324, 1.644, 9, 763.67, 1.290332, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9ea681e0-3274-467b-b681-4bb7f66f30f3_54efdcd0-1582-48fa-a29a-646536c9b197.jpg"),
    ("120242886929540256", "FounderStory_VID_JB_1", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 435.98, 14526, 292, 2.010189, 30.013768, 1.493082, 7, 705.34, 1.617827, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/bba70045-754a-43c7-8dcc-4f6639abc560.jpg"),
    ("120236793178590256", "story-oxmxl-13-Nov-2025", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 312.17, 17461, 210, 1.20268, 17.878128, 1.486524, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/cad357e9-6918-4c67-83a8-7738409e63e7.jpg"),
    ("120236793094610256", "image4 (3)", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 127.94, 8422, 104, 1.234861, 15.191166, 1.230192, 9, 284.90, 2.226825, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/669136b9-3053-4a37-ac19-14f378ca329d.jpg"),
    ("120236835746480256", "Slumberkins_XL_Hammerhead_Set_2025-17", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 126.33, 6792, 108, 1.590106, 18.599823, 1.169722, 1, 110.69, 0.876197, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/66bb127d-4409-481b-9a12-98c2ae1d3586.jpg"),
    ("120242886993210256", "FounderStory_VID_JB_2", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 29.26, 992, 16, 1.612903, 29.495968, 1.82875, 1, 36.68, 1.253589, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/6d817621-ad44-494a-b7c5-7b893e0acb55_f4f9a2bf-1edc-41a8-a48c-a822475b7577.jpg"),
    ("120240172797580256", "Carousel 3 | Lifestyle | Static", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 15.82, 2351, 33, 1.403658, 6.729051, 0.479394, 2, 233.86, 14.782554, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2b7b3fe1-16a1-4ab8-891b-62cb1b57c597.jpg"),
    ("120240727045540256", "LenaSophiaPhotography-9816", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 12.03, 781, 8, 1.024328, 15.403329, 1.50375, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ec6e1a77-814e-4aa2-a4f3-772f9da057b2.jpg"),
    ("120240841975680256", "SB-Testimonials-CFF&XLHH_IMG_AD_v3", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 8.80, 450, 1, 0.222222, 19.555556, 8.8, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b654e127-aacc-49a3-bf5f-d7678c37e1c4.jpg"),
    ("120236793023450256", "image2 (2)", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 6.50, 452, 6, 1.327434, 14.380531, 1.083333, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/976696e3-db9c-4e79-9191-67b12472b1bf.jpg"),
    ("120237065709090256", "LenaSophiaPhotography-9979", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 6.13, 417, 5, 1.199041, 14.70024, 1.226, 1, 399.06, 65.099511, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/dbad5275-4ebc-425e-b25d-7da375a4d761.jpg"),
    ("120237065692470256", "LenaSophiaPhotography-9040", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 5.75, 413, 3, 0.726392, 13.922518, 1.916667, 1, 912.00, 158.608696, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4f457c3b-efdf-4f4d-aafd-7c9542b831f4.jpg"),
    ("120240493054850256", "Carousel 4 | Hammerhead Growth System | Static | Conflict Resolution Collection | Re-ordered", "120236792394450256", "PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136", "120236792395750256", "PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136", 1.90, 107, 0, 0, 17.757009, 0, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/aec1e584-88c8-4a1f-b96f-fdfedaed80e0.jpg"),
    # ---- Campaign 4: PH | RTG | August 19, 2025 ----
    ("120244727093860256", "catalog (carousel) — copies (new_rt_042026)", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 374.42, 19294, 326, 1.689644, 19.406033, 1.148528, 19, 2403.20, 6.418461, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2909d41a-bf35-4be9-8224-d9e98e2842f8.jpg"),
    ("120243825621700256", "@katelynmcc_Video", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 232.25, 11480, 322, 2.804878, 20.230836, 0.721273, 4, 1449.66, 6.241808, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f17e40a9-ce18-412b-a2c9-14859131330e_1c4c48af-7bfc-4342-ad5b-cbf81ddb34b8.jpg"),
    ("120231573215720256", "@katelynmcc_Video", "120231573215710256", "PH | RTG | August 19, 2025", "120231573215740256", "PH - ATC - 180D | 3862", 138.34, 12859, 121, 0.940975, 10.758224, 1.143306, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f17e40a9-ce18-412b-a2c9-14859131330e_1c4c48af-7bfc-4342-ad5b-cbf81ddb34b8.jpg"),
    ("120244617223950256", "static  (kids_bedtime_got_easy) — copies (new_rt_042026) – Copy", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 128.92, 7465, 81, 1.085064, 17.269926, 1.591605, 4, 375.25, 2.91072, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/93bf1fbd-4c47-49b7-98d8-510715e3b5bb.jpg"),
    ("120243825621690256", "383E2DBF-495F-46AC-97D7-8100F08A925B", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 80.83, 4759, 46, 0.96659, 16.984661, 1.757174, 2, 302.46, 3.741928, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b7fe8b85-8da9-4256-a11d-1b1669708feb.jpg"),
    ("120243825621720256", "Affiliatecontent-Flexiblemedia-3862-Akinforthat - Copy", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 62.90, 3763, 111, 2.949774, 16.715387, 0.566667, 1, 95.56, 1.519237, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fde98808-2fc7-4d27-a282-9dc0e2e193b2.jpg"),
    ("120232052185930256", "Affiliatecontent-Flexiblemedia-3862-Akinforthat - Copy", "120231573215710256", "PH | RTG | August 19, 2025", "120231573215740256", "PH - ATC - 180D | 3862", 55.32, 5051, 58, 1.148287, 10.952287, 0.953793, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fde98808-2fc7-4d27-a282-9dc0e2e193b2.jpg"),
    ("120243825621680256", "Carousel_V3", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 52.50, 3047, 34, 1.115852, 17.230062, 1.544118, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b620eb0b-4624-4199-917f-e235040f5a66.jpg"),
    ("120239457726950256", "383E2DBF-495F-46AC-97D7-8100F08A925B", "120231573215710256", "PH | RTG | August 19, 2025", "120231573215740256", "PH - ATC - 180D | 3862", 18.27, 1706, 12, 0.7034, 10.709261, 1.5225, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b7fe8b85-8da9-4256-a11d-1b1669708feb.jpg"),
    ("120239295208160256", "Carousel_V3", "120231573215710256", "PH | RTG | August 19, 2025", "120231573215740256", "PH - ATC - 180D | 3862", 18.09, 1940, 27, 1.391753, 9.324742, 0.67, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b620eb0b-4624-4199-917f-e235040f5a66.jpg"),
    ("120244616584900256", "static carousel  (quotes) — copies (new_rt_042026)", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 17.58, 963, 9, 0.934579, 18.255452, 1.953333, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/558b7fd4-8b79-47f2-b4d2-b2ba3cacc009.jpg"),
    ("120244726981280256", "static carousel  (quotes) — copies (new_rt_042026) – Copy", "120231573215710256", "PH | RTG | August 19, 2025", "120243825621750256", "PH - ATC - 14D | 3862", 14.75, 787, 9, 1.143583, 18.742058, 1.638889, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/558b7fd4-8b79-47f2-b4d2-b2ba3cacc009.jpg"),
    # ---- Campaign 5: PRS | Flip Out Testing ----
    ("120244725413400256", "video (SB-FOHH-ColourUSPGraphicsV2_IMG_VID_AD_GIF) – copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 599.72, 47180, 131, 0.27766, 12.711318, 4.578015, 5, 598.75, 0.998383, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0c7a7ba2-b430-4a92-aebb-e4e2d29d2aa2_cfddc1e3-55ae-4de6-9cda-59bda85b1238.jpg"),
    ("120244725413410256", "video (@kaylastravelmagic) – copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 182.69, 5124, 55, 1.07338, 35.653786, 3.321636, 3, 502.37, 2.749849, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe01107c-ec8e-4ec6-abcb-d1a93a473ff7_9972cdff-d524-4528-97a1-110550cc0ee0.jpg"),
    ("120245002556780256", "static (circles) – copy (flipout_old_single)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 139.67, 6554, 36, 0.549283, 21.31065, 3.879722, 1, 114.04, 0.816496, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2807d037-00fc-4c10-8e82-88b821e8b921.jpg"),
    ("120244725413430256", "video (ttVideo-@athenclay-Jun-16-2025-12-07-AM-7516332041877654814-erkxtgbkk) – copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 39.55, 1442, 41, 2.843273, 27.427184, 0.964634, 1, 117.17, 2.962579, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/39159f3c-bd81-4a45-bacf-9fcd892d1565_ff81c4ae-3008-49aa-8e6e-55deaa6b28a7.jpg"),
    ("120244725413420256", "image (SB-FOHH-ColourUSPGraphicsV2_IMG_VID_AD_v2) — copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 24.01, 1149, 18, 1.56658, 20.896432, 1.333889, 3, 78.17, 3.255727, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9c014f02-322a-4dad-895a-99b8ee737c31.jpg"),
    ("120244725413440256", "video (snarkandlemons.mp4) – copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 21.70, 816, 14, 1.715686, 26.593137, 1.55, 1, 90.44, 4.167742, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/7ac8b821-d4cf-409a-b20f-13dd9ca482ad_d5f49820-9095-4d96-bf83-b5def5101071.jpg"),
    ("120245002451270256", "static (collage) – copy (flipout_old_single)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 13.89, 877, 6, 0.684151, 15.838084, 2.315, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/27f204e3-6e7a-43e0-aa03-9ccd62d6223d.jpg"),
    ("120244725413390256", "flexible video (Affiliatecontent-Flexiblemedia-3862-Akinforthat) – copy (flipout)", "120244725358790256", "PRS | Flip Out Testing | May 7, 2026", "120244725358770256", "PRS |  Flip Out | Open + Exclusions | 7DC 1DV", 6.63, 510, 3, 0.588235, 13.00, 2.21, 1, 96.45, 14.547511, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d6799a9e-18d0-483a-84df-632743d3d762_d2c0180b-b2ac-4b07-90c9-9b7728d19d14.jpg"),
    # ---- Campaign 6: PRS | Keychains Testing ----
    ("120244725205780256", "video (Bag Charms but Different) — copy (keychains)", "120244724714600256", "PRS | Keychains Testing | May 7, 2026", "120244724714390256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 209.80, 12519, 192, 1.533669, 16.758527, 1.092708, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c8e97e6e-9a16-4d79-ba8e-324860d454fe_2e473d17-9aed-4f21-8819-8885d3d03bd4.jpg"),
    ("120244725205770256", "video (Blind Unboxing) — copy (keychains)", "120244724714600256", "PRS | Keychains Testing | May 7, 2026", "120244724714390256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 172.32, 7110, 152, 2.137834, 24.236287, 1.133684, 1, 70.90, 0.411444, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/a1b18305-4a67-4116-acc1-b1a5948c0ac9_28f9bf38-3daf-460a-8f1b-2cde13fc2f35.jpg"),
    ("120244724774100256", "static product card (Slumberkins_Keychains_PDP_Finals-17) — copy (keychains)", "120244724714600256", "PRS | Keychains Testing | May 7, 2026", "120244724714390256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 51.74, 2842, 55, 1.935257, 18.205489, 0.940727, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/37f3a332-e7d2-4687-8d16-d1f9bf772932.jpg"),
    ("120244724774110256", "static product card (Slumberkins_Keychains_PDP_Finals-14) — copy (keychains)", "120244724714600256", "PRS | Keychains Testing | May 7, 2026", "120244724714390256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 3.59, 265, 3, 1.132075, 13.54717, 1.196667, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe3488ad-738c-4054-bb8e-3938c5d7946f.jpg"),
    ("120244724774120256", "static (keychains_chaos_at_house) — copy (keychains)", "120244724714600256", "PRS | Keychains Testing | May 7, 2026", "120244724714390256", "PRS |  Keychains | Open + Exclusions | 7DC 1DV", 1.94, 152, 0, 0, 12.763158, 0, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0d41cfd6-b088-4879-a830-4ab97b9bd3fb.jpg"),
    # ---- Campaign 7: PH | PRS | Colors Within ----
    ("120242526618750256", "Slumberkins_Keychains_PDP_Finals-15", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 60.42, 4437, 88, 1.983322, 13.617309, 0.686591, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c4ff5391-3d18-4f2f-9a26-627184f8381b.jpg"),
    ("120242526541410256", "Slumberkins_Keychains_PDP_Finals-29", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 48.38, 3779, 72, 1.905266, 12.802329, 0.671944, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9c6b025f-c4d8-47d1-b652-5dcfc6ec25fd.jpg"),
    ("120242526527860256", "Slumberkins_Keychains_PDP_Finals-44", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 15.19, 1095, 13, 1.187215, 13.872146, 1.168462, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/eecf281a-11ee-426d-ad62-03cadb28bbf4.jpg"),
    ("120242525574960256", "Slumberkins_Keychains_Social_Finals-54", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 14.02, 1228, 19, 1.547231, 11.416938, 0.737895, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0b080292-0a90-4335-b535-508582229f3d.jpg"),
    ("120242526452990256", "Slumberkins_Keychains_Social_Finals-19", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 11.87, 665, 14, 2.105263, 17.849624, 0.847857, 1, 122.47, 10.317607, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e2aa89a6-98b0-4d29-a5e2-69dc5f011491.jpg"),
    ("120242526436530256", "Slumberkins_Keychains_Social_Finals-50", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 3.42, 193, 5, 2.590674, 17.720207, 0.684, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/77594429-7a23-454b-8218-d1febeabf77c.jpg"),
    ("120242526641010256", "IMG_7869 2", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 1.54, 116, 2, 1.724138, 13.275862, 0.77, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/458f44fa-db06-4557-9fb0-28e62eb64fbe_d580b24b-3ecf-44e1-953c-087cd55862da.jpg"),
    ("120242526518600256", "Slumberkins_Keychains_Social_Finals-18", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 1.32, 123, 2, 1.626016, 10.731707, 0.66, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3f8a206d-f8e8-4a19-8724-88598e32a636.jpg"),
    ("120242526627860256", "Slumberkins_Keychains_PDP_Finals-14", "120242525575410256", "PH | PRS | Colors Within | April 3, 2026", "120242525575090256", "PRS |  Creative Testing | Open + Exclusions | 7DC 1DV", 0.58, 38, 0, 0, 15.263158, 0, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe3488ad-738c-4054-bb8e-3938c5d7946f.jpg"),
]


def main():
    details = {d["ad_id"]: d for d in json.loads(DETAILS_PATH.read_text())}

    ads = []
    for row in ADS:
        ad_id, ad_name, cid, cname, asid, asname, spend, imp, clk, ctr_pct, cpm, cpc, purch, rev, roas, thumb = row
        cpa = (spend / purch) if purch else 0.0
        det = details.get(ad_id, {})
        ads.append({
            "ad_id": ad_id,
            "ad_name": ad_name,
            "ad_status": det.get("ad_status"),
            "ad_effective_status": det.get("ad_effective_status"),
            "campaign_id": cid,
            "campaign_name": cname,
            "adset_id": asid,
            "adset_name": asname,
            "creative_id": det.get("creative_id"),
            "creative_name": det.get("creative_name"),
            "creative_name_is_templated": bool(det.get("creative_name") and "{{" in det["creative_name"]),
            "spend": round(spend, 2),
            "impressions": int(imp),
            "clicks": int(clk),
            "ctr_pct": round(ctr_pct, 4),
            "cpm": round(cpm, 4),
            "cpc": round(cpc, 4),
            "purchases": int(purch),
            "revenue": round(rev, 2),
            "roas": round(roas, 4),
            "cpa": round(cpa, 2),
            "thumb_url": thumb or None,
        })

    # Aggregate metrics for header
    total_spend = sum(a["spend"] for a in ads)
    total_imp = sum(a["impressions"] for a in ads)
    total_purch = sum(a["purchases"] for a in ads)
    total_rev = sum(a["revenue"] for a in ads)
    spenders = [a for a in ads if a["purchases"] > 0]
    avg_cpa = (total_spend / total_purch) if total_purch else 0.0
    avg_roas = (total_rev / total_spend) if total_spend else 0.0
    named_pct = sum(1 for a in ads if a["creative_name"]) / len(ads)
    templated_pct = sum(1 for a in ads if a["creative_name_is_templated"]) / len(ads)

    out = {
        "account": {
            "id": "act_1939402463050546",
            "name": "Slumberkins",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "date_range": {"since": "2026-04-26", "until": "2026-05-25", "label": "Last 30 days"},
        "totals": {
            "ad_count": len(ads),
            "total_spend": round(total_spend, 2),
            "total_impressions": total_imp,
            "total_purchases": total_purch,
            "total_revenue": round(total_rev, 2),
            "avg_cpa": round(avg_cpa, 2),
            "avg_roas": round(avg_roas, 4),
            "creative_name_populated_pct": round(named_pct, 4),
            "creative_name_templated_pct": round(templated_pct, 4),
        },
        "ads": ads,
    }
    (ROOT / "data.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(ads)} ads to data.json")
    print(f"Total spend: ${total_spend:,.2f} | purchases: {total_purch} | revenue: ${total_rev:,.2f}")
    print(f"Avg CPA: ${avg_cpa:.2f} | Avg ROAS: {avg_roas:.2f}x")
    print(f"creative_name populated: {named_pct*100:.0f}%  |  templated: {templated_pct*100:.0f}%")


if __name__ == "__main__":
    main()
