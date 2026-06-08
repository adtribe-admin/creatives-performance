#!/usr/bin/env python3
"""Refresh both brand data.json files from the 2026-06-08 GoMarble pulls.

Window for both brands: 2026-05-09 → 2026-06-07 (last_30d).
Adds video_3s + thruplays per ad → hook_rate and hold_rate per ad.

Xtrema C1 (Purchase Scaling, 22 ads) was too big to return inline, saved by the
MCP harness to disk; we parse that file. Everything else is embedded below as
a compact pipe-separated string per ad. Field count is fixed at 13 trailing
fields after ad_name, so ad_name can safely contain pipes.

Per-ad row format (split by `|`, last 13 fields are the schema):
  ad_id | ad_name (may contain pipes) | spend | imp | clk | ctr | cpm | cpc
       | purch | rev | roas | vid3s | thru | thumb

Each row is paired with a campaign block (one block per campaign-adset combo):
  campaign_id | campaign_name (may contain pipes) | adset_id | adset_name (may contain pipes)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def derive_asset(thumb_url):
    """Heuristically derive (asset_url, asset_type) from a GoMarble thumb URL.
    Video posters look like `<uuid>_<uuid>.jpg` → mp4 lives at `<uuid1>.mp4`.
    Single-UUID `.jpg` → it's an image; asset_url == thumb_url.
    """
    if not thumb_url:
        return None, None
    basename = thumb_url.rsplit("/", 1)[-1]
    if basename.endswith(".jpg"):
        stem = basename[:-4]
        parts = stem.split("_")
        if len(parts) == 2 and UUID_RE.match(parts[0]) and UUID_RE.match(parts[1]):
            prefix = thumb_url.rsplit("/", 1)[0]
            return f"{prefix}/{parts[0]}.mp4", "video"
        return thumb_url, "image"
    if basename.endswith(".mp4"):
        return thumb_url, "video"
    return thumb_url, "image"
XTREMA_C1_PATH = Path("/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1780911726284.txt")

# Slumberkins campaign-adset blocks (single adset per campaign in this window)
SL_C1 = "120244725358790256|PRS | Flip Out Testing | May 7, 2026|120244725358770256|PRS |  Flip Out | Open + Exclusions | 7DC 1DV"
SL_C2 = "120244149688310256|PRS | Mixed Creatures Testing | April 28, 2026|120244149688150256|PRS |  Mixed | Open + Exclusions | 7DC 1DV"
SL_C3 = "120235968232540256|PH | PRS | Creature Full of Feelings | 11/5/25 | 4094|120235974945040256|PRS |  Lifestyle IMGs & Top Ads | Open + Exclusions | 7DC 1DV | 4094"
SL_C4 = "120231573215710256|PH | RTG | August 19, 2025|120243825621750256|PH - ATC - 14D | 3862"
SL_C5 = "120236792394450256|PH | PRS | ASC | XL Hammerhead | 11/19/25 | 4136|120236792395750256|PRS |  Top Ads | IMGs & Vids | No Exclusions | 7DC 1DV | 4136"
SL_C6 = "120244724714600256|PRS | Keychains Testing | May 7, 2026|120244724714390256|PRS |  Keychains | Open + Exclusions | 7DC 1DV"
SL_C7 = "120246125603750256|PRS | Unicorn Testing | May 27, 2026|120246125603740256|PRS |  Unicorn | Open + Exclusions | 7DC 1DV"

# Xtrema campaign-adset blocks (C4 has multiple adsets, separate block each)
XT_C2 = "120235361670130350|P | New One Campaign | Flexi Ads|120235361670150350|New One Campaign | Flexi Ads | EX PUR 180 D"
XT_C3 = "120239145232560350|P | Creator Partnership Campaign|120239145232570350|Creator Partnership | Excluding PUR 180D"
XT_C4_BCH1 = "120214101753260350|P | BCH | Bid Cap Campaign | $105 cost|120214101753240350|BCH1 | Broad | $105 cost"
XT_C4_BCH3 = "120214101753260350|P | BCH | Bid Cap Campaign | $105 cost|120218990152640350|BCH3 | Broad | $105 cost | New Ads"
XT_C4_BCH4 = "120214101753260350|P | BCH | Bid Cap Campaign | $105 cost|120228835862310350|BCH4 | Broad | $105 cost | New Ads May"
XT_C4_BCH5 = "120214101753260350|P | BCH | Bid Cap Campaign | $105 cost|120239542266870350|BCH5 | Broad | $105 cost | New Ads Q4"
XT_C5 = "120247852351670350|SCC | Mother's Day Campaign|120247852351660350|SCC | Mother's Day Campaign"

ROWS = [
    # ===== Slumberkins =====
    # C1 Flip Out (8 ads)
    ("slumberkins", SL_C1, "120244725413400256|video (SB-FOHH-ColourUSPGraphicsV2_IMG_VID_AD_GIF) – copy (flipout)|1287.18|106881|295|0.276008|12.043113|4.363322|7|851.6|0.661601|51660|51660|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0c7a7ba2-b430-4a92-aebb-e4e2d29d2aa2_cfddc1e3-55ae-4de6-9cda-59bda85b1238.jpg"),
    ("slumberkins", SL_C1, "120244725413410256|video (@kaylastravelmagic) – copy (flipout)|225.91|6208|68|1.095361|36.390142|3.322206|64|45436.28|201.125581|965|162|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe01107c-ec8e-4ec6-abcb-d1a93a473ff7_9972cdff-d524-4528-97a1-110550cc0ee0.jpg"),
    ("slumberkins", SL_C1, "120245002556780256|static (circles) – copy (flipout_old_single)|139.67|6554|36|0.549283|21.31065|3.879722|1|114.04|0.816496|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2807d037-00fc-4c10-8e82-88b821e8b921.jpg"),
    ("slumberkins", SL_C1, "120244725413430256|video (ttVideo-@athenclay-Jun-16-2025-12-07-AM-7516332041877654814-erkxtgbkk) – copy (flipout)|42.05|1510|38|2.516556|27.847682|1.106579|1|117.17|2.786445|356|61|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/39159f3c-bd81-4a45-bacf-9fcd892d1565_ff81c4ae-3008-49aa-8e6e-55deaa6b28a7.jpg"),
    ("slumberkins", SL_C1, "120244725413440256|video (snarkandlemons.mp4) – copy (flipout)|27.49|999|21|2.102102|27.517518|1.309048|1|90.44|3.289924|236|38|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/7ac8b821-d4cf-409a-b20f-13dd9ca482ad_d5f49820-9095-4d96-bf83-b5def5101071.jpg"),
    ("slumberkins", SL_C1, "120244725413420256|image (SB-FOHH-ColourUSPGraphicsV2_IMG_VID_AD_v2) — copy (flipout)|24.12|984|16|1.626016|24.512195|1.5075|3|78.17|3.240879|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9c014f02-322a-4dad-895a-99b8ee737c31.jpg"),
    ("slumberkins", SL_C1, "120245002451270256|static (collage) – copy (flipout_old_single)|16.37|976|8|0.819672|16.772541|2.04625|0|0|0|1|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/27f204e3-6e7a-43e0-aa03-9ccd62d6223d.jpg"),
    ("slumberkins", SL_C1, "120244725413390256|flexible video (Affiliatecontent-Flexiblemedia-3862-Akinforthat) – copy (flipout)|5.23|389|3|0.771208|13.44473|1.743333|0|0|0|64|12|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d6799a9e-18d0-483a-84df-632743d3d762_d2c0180b-b2ac-4b07-90c9-9b7728d19d14.jpg"),
    # C2 Mixed Creatures (6 ads)
    ("slumberkins", SL_C2, "120244150751700256|video (gif_what_about) — copies (slumberkins_general)|870.17|89739|796|0.887017|9.696676|1.093178|12|883.31|1.015101|10228|2182|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/48661b03-1510-450c-bfb4-14a58c28b041_eda08f7a-7d0e-424b-babf-eb7d99699ac5.jpg"),
    ("slumberkins", SL_C2, "120244616420370256|image carousel (your_love_letter_ugc) — copies (slumberkins_general) – Copy|315.54|28657|119|0.415256|11.010922|2.651597|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/8dcb4827-a862-47b7-8cb4-01264ac87e13.jpg"),
    ("slumberkins", SL_C2, "120244150294500256|image (set) — copies (slumberkins_general)|244.56|26708|144|0.539164|9.156807|1.698333|2|188.57|0.771058|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/7988e4b7-be55-4663-b078-991d1d5420da.jpg"),
    ("slumberkins", SL_C2, "120244616137230256|image carousel (your_love_letter_arrow) — copies (slumberkins_general)|165.87|16217|75|0.462478|10.228156|2.2116|8|1047.43|6.314765|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3b61b662-bcb8-4302-a329-0ad695ee2733.jpg"),
    ("slumberkins", SL_C2, "120244150666710256|image (every_feeling_emotions) — copies (slumberkins_general)|92.93|10027|64|0.638277|9.267976|1.452031|1|61.42|0.660928|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4b7095ba-1a46-4a14-92e7-a61a6f62db26.jpg"),
    ("slumberkins", SL_C2, "120244149688140256|image carousel (in-stock_creatures) — copies (slumberkins_general)|11.09|799|1|0.125156|13.87985|11.09|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c2d9e587-190c-4de4-877b-9a2aacdab022.jpg"),
    # C3 Creature Full of Feelings (5 ads)
    ("slumberkins", SL_C3, "120242913171760256|Carousel_V2|1116.83|46929|585|1.246564|23.798291|1.909111|18|2986.41|2.674006|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f0b07453-8904-4d77-b965-db02c976bf07.jpg"),
    ("slumberkins", SL_C3, "120237937752360256|DSC_9231|357.64|16314|246|1.507907|21.922275|1.453821|67|2822.39|7.891707|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0687a993-55bd-405b-8c81-29cfa649aed4.jpg"),
    ("slumberkins", SL_C3, "120237937585980256|@diy.withthewears 8|52.47|1683|37|2.198455|31.176471|1.418108|1|108.62|2.070135|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/cf26ad6c-8652-4cee-b904-4ecb7ff12ab5.jpg"),
    ("slumberkins", SL_C3, "120237937605660256|@diy.withthewears 3|20.82|995|7|0.703518|20.924623|2.974286|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/28969fb9-fa6b-4f59-8318-d0b1233868e1.jpg"),
    ("slumberkins", SL_C3, "120237065739150256|Carousel_V3 | 4094|2.54|131|0|0|19.389313|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d7c58bfe-37e9-4d1f-bb84-8f5c381c9a97.jpg"),
    # C4 RTG August (6 ads, all in 14D adset)
    ("slumberkins", SL_C4, "120244727093860256|catalog (carousel) — copies (new_rt_042026)|618.44|34275|519|1.514223|18.043472|1.191599|32|4088.08|6.61031|10|3|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2909d41a-bf35-4be9-8224-d9e98e2842f8.jpg"),
    ("slumberkins", SL_C4, "120243825621700256|@katelynmcc_Video|198.88|9367|271|2.893135|21.231985|0.733875|4|1449.66|7.289119|1352|505|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f17e40a9-ce18-412b-a2c9-14859131330e_1c4c48af-7bfc-4342-ad5b-cbf81ddb34b8.jpg"),
    ("slumberkins", SL_C4, "120244617223950256|static  (kids_bedtime_got_easy) — copies (new_rt_042026) – Copy|96.39|5421|64|1.180594|17.780852|1.506094|4|375.25|3.893039|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/93bf1fbd-4c47-49b7-98d8-510715e3b5bb.jpg"),
    ("slumberkins", SL_C4, "120243825621680256|Carousel_V3|37.18|1793|19|1.059677|20.736196|1.956842|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b620eb0b-4624-4199-917f-e235040f5a66.jpg"),
    ("slumberkins", SL_C4, "120244726981280256|static carousel  (quotes) — copies (new_rt_042026) – Copy|17.25|911|12|1.317234|18.935236|1.4375|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/558b7fd4-8b79-47f2-b4d2-b2ba3cacc009.jpg"),
    ("slumberkins", SL_C4, "120244616584900256|static carousel  (quotes) — copies (new_rt_042026)|8.28|331|5|1.510574|25.015106|1.656|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/558b7fd4-8b79-47f2-b4d2-b2ba3cacc009.jpg"),
    # C5 XL Hammerhead (10 ads)
    ("slumberkins", SL_C5, "120242887065210256|FounderStory_VID_JB_3|303.22|7411|179|2.415329|40.914856|1.693966|4|369.72|1.219313|1326|300|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/9ea681e0-3274-467b-b681-4bb7f66f30f3_54efdcd0-1582-48fa-a29a-646536c9b197.jpg"),
    ("slumberkins", SL_C5, "120236793178590256|story-oxmxl-13-Nov-2025|176.26|8970|112|1.248606|19.649944|1.57375|0|0|0|1|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/cad357e9-6918-4c67-83a8-7738409e63e7.jpg"),
    ("slumberkins", SL_C5, "120242886993210256|FounderStory_VID_JB_2|2.17|64|4|6.25|33.90625|0.5425|0|0|0|9|4|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/6d817621-ad44-494a-b7c5-7b893e0acb55_f4f9a2bf-1edc-41a8-a48c-a822475b7577.jpg"),
    ("slumberkins", SL_C5, "120236793023450256|image2 (2)|1.67|83|2|2.409639|20.120482|0.835|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/976696e3-db9c-4e79-9191-67b12472b1bf.jpg"),
    ("slumberkins", SL_C5, "120240727045540256|LenaSophiaPhotography-9816|1.59|37|0|0|42.972973|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ec6e1a77-814e-4aa2-a4f3-772f9da057b2.jpg"),
    ("slumberkins", SL_C5, "120240493054850256|Carousel 4 | Hammerhead Growth System | Static | Conflict Resolution Collection | Re-ordered|1.03|43|0|0|23.953488|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/aec1e584-88c8-4a1f-b96f-fdfedaed80e0.jpg"),
    ("slumberkins", SL_C5, "120240841975680256|SB-Testimonials-CFF&XLHH_IMG_AD_v3|0.94|25|0|0|37.6|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b654e127-aacc-49a3-bf5f-d7678c37e1c4.jpg"),
    ("slumberkins", SL_C5, "120237065709090256|LenaSophiaPhotography-9979|0.66|27|0|0|24.444444|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/dbad5275-4ebc-425e-b25d-7da375a4d761.jpg"),
    ("slumberkins", SL_C5, "120240172797580256|Carousel 3 | Lifestyle | Static|0.29|41|0|0|7.073171|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2b7b3fe1-16a1-4ab8-891b-62cb1b57c597.jpg"),
    ("slumberkins", SL_C5, "120237065692470256|LenaSophiaPhotography-9040|0.11|10|0|0|11|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4f457c3b-efdf-4f4d-aafd-7c9542b831f4.jpg"),
    # C6 Keychains Testing (5 ads)
    ("slumberkins", SL_C6, "120244725205780256|video (Bag Charms but Different) — copy (keychains)|203.57|12227|189|1.545759|16.649219|1.07709|0|0|0|3003|414|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c8e97e6e-9a16-4d79-ba8e-324860d454fe_2e473d17-9aed-4f21-8819-8885d3d03bd4.jpg"),
    ("slumberkins", SL_C6, "120244725205770256|video (Blind Unboxing) — copy (keychains)|113.24|4600|94|2.043478|24.617391|1.204681|0|0|0|1423|421|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/a1b18305-4a67-4116-acc1-b1a5948c0ac9_28f9bf38-3daf-460a-8f1b-2cde13fc2f35.jpg"),
    ("slumberkins", SL_C6, "120244724774100256|static product card (Slumberkins_Keychains_PDP_Finals-17) — copy (keychains)|47.88|2553|51|1.99765|18.754407|0.938824|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/37f3a332-e7d2-4687-8d16-d1f9bf772932.jpg"),
    ("slumberkins", SL_C6, "120244724774110256|static product card (Slumberkins_Keychains_PDP_Finals-14) — copy (keychains)|0.89|48|0|0|18.541667|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fe3488ad-738c-4054-bb8e-3938c5d7946f.jpg"),
    ("slumberkins", SL_C6, "120244724774120256|static (keychains_chaos_at_house) — copy (keychains)|0|1|0|0|0|0|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0d41cfd6-b088-4879-a830-4ab97b9bd3fb.jpg"),
    # C7 Unicorn Testing (6 ads)
    ("slumberkins", SL_C7, "120246125880340256|PH-PRS-IMG-PROD-UnicornKin-02/09/23 – Copy|191.26|12519|134|1.070373|15.277578|1.427313|8|212.72|1.112203|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d591779f-10be-4f4c-b3f9-1b2cd8804b4a.jpg"),
    ("slumberkins", SL_C7, "120246127283170256|video (reel_unicorn-use-case) – copy (for_child_worrying)|53.58|1940|15|0.773196|27.618557|3.572|0|0|0|457|37|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ea2b1879-2331-453c-ac18-5dea77958ec3_964190b4-9374-485f-a0e3-e4216bf47295.jpg"),
    ("slumberkins", SL_C7, "120246125880330256|PH-PRS-IMG-PROD-UnicornKin-02/09/23 – Copy|21.09|1338|10|0.747384|15.762332|2.109|1|77.63|3.680891|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0f1a94c4-febf-48fd-93a6-444ac5f4e82b.jpg"),
    ("slumberkins", SL_C7, "120246126728870256|static carousel (product_images) — copies (unicorn_ad_old_copy)|8.52|532|1|0.18797|16.015038|8.52|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/491b15dd-3933-49fb-a9d1-bca68497fc0c.jpg"),
    ("slumberkins", SL_C7, "120246126424500256|static carousel (Ashley Robertson) — copies (unicorn_ad_old_copy)|5.77|510|3|0.588235|11.313725|1.923333|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/35d72acb-34c6-4445-b9a8-83d6227569c8.jpg"),
    ("slumberkins", SL_C7, "120246127480930256|Handwriting_Unicorn_Static – Copy|3.55|144|0|0|24.652778|0|0|0|0|0|0|"),

    # ===== Xtrema =====
    # C2 Flexi Ads (3 ads)
    ("xtrema", XT_C2, "120247616301350350|XTR799 | Video | Dynamic Copy | Home Page |  Spring Cleaning|5064.56|203068|3630|1.787579|24.940217|1.395196|33|8367.82|1.65223|35715|7256|"),
    ("xtrema", XT_C2, "120247616873540350|XTR801 | Video | Dynamic Copy | Home Page | Modern Healthy Kitchen|1080.11|49424|973|1.968679|21.853958|1.110082|11|3037.58|2.812288|8651|1816|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fcb4084e-a575-40a7-a812-5b4d72d2f46f.jpg"),
    ("xtrema", XT_C2, "120235684414240350|XTR689 | Flexible Videos | Non-Stick Switch V1 | Home Page - Copy|261.16|15008|302|2.01226|17.401386|0.864768|1|14.97|0.057321|2726|599|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/936e6f8c-7018-45eb-90ec-840a278ace26_67f91e11-e924-4173-9b55-b103f1d92453.jpg"),
    # C3 Creator Partnership (5 ads)
    ("xtrema", XT_C3, "120244608721000350|Kayla Young- Video 2- February 2026|3611.94|148660|7398|4.976456|24.29665|0.488232|29|11706.72|3.241117|43882|14281|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/08b446fe-5a1a-4203-b6bf-bef0644a1b3e.jpg"),
    ("xtrema", XT_C3, "120245911506150350|Kayla Young- Video 3 - February 2026|440.43|27072|1397|5.160313|16.268839|0.315268|3|224.18|0.509003|7955|1605|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c7ed6a83-77f1-44ad-92c0-d8297b58c5a0.jpg"),
    ("xtrema", XT_C3, "120250401283650350|Test - Jasmin Shannon - Banana Pancakes Video - May 2026|361.08|15818|487|3.078771|22.827159|0.741437|1|402|1.113327|4316|1333|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/69f1bf3a-fd8a-4190-a964-c856f311f784_f25dcfc9-d4c5-4ac7-8c45-ccdde0956424.jpg"),
    ("xtrema", XT_C3, "120245494330330350|Aroshaliny Feb 2026|325.52|16229|818|5.04036|20.057921|0.397946|6|2241.28|6.88523|4103|1321|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c2b48afb-43d1-4c3a-80f3-ccc8bfbe757b.jpg"),
    ("xtrema", XT_C3, "120250401283640350|Test - Jasmin Shannon - Chocolate Chip Cookie Video - May 2026|313.45|16616|430|2.587867|18.864348|0.728953|2|378.87|1.20871|5321|1361|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fcb0dd7b-2ccf-4ec3-89ea-0169b8fb468e_f2fcbb68-52db-4e24-88bd-e73dd5f81845.jpg"),
    # C4 BCH Bid Cap (12 ads across 4 adsets)
    ("xtrema", XT_C4_BCH1, "120214102064870350|XTR201 | Image | Ceramics have been | Sale Page|570.27|73079|289|0.395462|7.803473|1.973253|15|4555.56|7.988427|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/74fa106e-1101-4a88-9417-2392b1dbb4e7.jpg"),
    ("xtrema", XT_C4_BCH3, "120221091184920350|XTR451 | Image | Dynamic copy | Sale Page - Copy|468.63|55591|309|0.555845|8.429962|1.516602|4|2433.82|5.193479|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/22b7e6fd-6cad-462b-94f7-7d0c808ec3c9.jpg"),
    ("xtrema", XT_C4_BCH5, "120239542295930350|XTR704 | Flexible Videos | Flaking Non-stick Pans UGC | Home Page - Copy|324.82|28240|583|2.064448|11.502125|0.557153|9|2940.5|9.052706|3134|1168|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/21ff1d02-f55e-4cb2-be56-c7091a7d7422.jpg"),
    ("xtrema", XT_C4_BCH4, "120228835903820350|XTR549 | Video | H5B1CTA2 | Sale Page - Copy|171.97|13983|216|1.544733|12.298505|0.796157|2|475.17|2.763098|1946|535|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e2c2a379-91b9-4ab8-9cfc-9ec1b255d0a4_7e0cb999-1a95-4332-8986-fc8ed0c098d7.jpg"),
    ("xtrema", XT_C4_BCH1, "120214101984320350|XTR200 | Image | Ceramics have been | Sale Page|85.23|9686|43|0.44394|8.799298|1.982093|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3b382fa5-7ed8-48c7-a254-e833af7a83da.jpg"),
    ("xtrema", XT_C4_BCH1, "120214101753250350|XTR199 | Image | Ceramics have been | Sale Page|55.32|6725|24|0.356877|8.226022|2.305|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/5e960a9d-e8d2-4504-9dac-902688c6bf66.jpg"),
    ("xtrema", XT_C4_BCH1, "120214102107910350|XTR202 | Image | Ceramics have been | Sale Page|54.54|6235|31|0.497193|8.747394|1.759355|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/19df8b25-8f9b-4963-8f03-bdaac6182df7.jpg"),
    ("xtrema", XT_C4_BCH3, "120221091184910350|XTR454 | Image | Dynamic copy | Sale Page - Copy|45.84|5769|27|0.468019|7.945918|1.697778|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/8fc8e4b0-bae0-451e-9e65-6f1362efc360.jpg"),
    ("xtrema", XT_C4_BCH3, "120218990180820350|XTR422 | Image | Dynamic copy | Sale Page - Copy|28.03|3084|18|0.583658|9.088846|1.557222|1|205.11|7.317517|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4656093a-c421-427b-b926-c36492f3c3ac.jpg"),
    ("xtrema", XT_C4_BCH1, "120214102144480350|XTR204 | Video | Ceramics have been | Sale Page|8.19|747|12|1.606426|10.963855|0.6825|0|0|0|73|25|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e7ea0508-e14a-41c8-a2c7-42a3e92113c8_2fc7cb59-70c1-40b8-bbc0-33894247e958.jpg"),
    ("xtrema", XT_C4_BCH3, "120218990180810350|XTR403 | Image | Dynamic copy | Sale Page - Copy|5.73|644|2|0.310559|8.897516|2.865|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/01aaa86f-0803-476f-8347-515b64964148.jpg"),
    ("xtrema", XT_C4_BCH4, "120228835903830350|XTR497 | Video | Dynamic copy | Sale Page - Copy|2.11|179|2|1.117318|11.78771|1.055|0|0|0|15|1|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/6e5692fb-3267-43de-b1c5-cde05e226f0e_7a26e298-896d-494f-b549-853833f6c784.jpg"),
    # C5 Mother's Day (1 ad)
    ("xtrema", XT_C5, "120247852351700350|XTR803 | Flexible Images | Dynamic Copy | Home Page | Mother's Day Campaign|372.7|22270|211|0.947463|16.735519|1.766351|7|2230.56|5.984867|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/bed8afe1-b2bf-43b8-8aa0-6a19c716641c.jpg"),
]


def split_block(s):
    """Split campaign block into (cid, cname, asid, asname) — pipes may appear in names.
    Anchors: cid is the first part, asid is the next long all-digit part."""
    parts = s.split("|")
    cid = parts[0]
    asid_idx = next((i for i in range(1, len(parts)) if parts[i].strip().isdigit() and len(parts[i].strip()) > 10), None)
    if asid_idx is None:
        return cid, "|".join(parts[1:]).strip(), "", ""
    return cid, "|".join(parts[1:asid_idx]).strip(), parts[asid_idx].strip(), "|".join(parts[asid_idx + 1:]).strip()


def parse_ad(brand_slug, cb, ab):
    """Parse one ad row. Last 13 fields are the schema; ad_name fills the middle (may contain pipes)."""
    cid, cname, asid, asname = split_block(cb)
    parts = ab.split("|")
    if len(parts) < 14:
        raise ValueError(f"Row has {len(parts)} parts (need ≥14): {ab[:120]}")
    ad_id = parts[0]
    # 12 fixed fields after ad_name: spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, vid3s, thru, thumb
    tail = parts[-12:]
    ad_name = "|".join(parts[1:-12]).strip()
    spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, vid3s, thru, thumb = tail
    spend_f = float(spend) if spend else 0.0
    purch_i = int(purch) if purch else 0
    rev_f = float(rev) if rev else 0.0
    vid3s_i = int(vid3s) if vid3s else 0
    thru_i = int(thru) if thru else 0
    imp_i = int(imp) if imp else 0
    thumb_clean = thumb.strip() or None
    asset_url, asset_type = derive_asset(thumb_clean)
    # If we have video_3s > 0 but heuristic says image, override to video
    if vid3s_i > 0 and asset_type != "video":
        asset_type = "video" if asset_url else None
    return {
        "ad_id": ad_id, "ad_name": ad_name,
        "campaign_id": cid, "campaign_name": cname,
        "adset_id": asid, "adset_name": asname,
        "spend": round(spend_f, 2),
        "impressions": imp_i,
        "clicks": int(clk) if clk else 0,
        "ctr_pct": round(float(ctr), 4) if ctr else 0,
        "cpm": round(float(cpm), 4) if cpm else 0,
        "cpc": round(float(cpc), 4) if cpc else 0,
        "purchases": purch_i,
        "revenue": round(rev_f, 2),
        "roas": round(float(roas), 4) if roas else 0,
        "cpa": round(spend_f / purch_i, 2) if purch_i else 0,
        "video_3s": vid3s_i,
        "thruplays": thru_i,
        "hook_rate": (vid3s_i / imp_i) if imp_i else 0,
        "hold_rate": (thru_i / vid3s_i) if vid3s_i else 0,
        "thumb_url": thumb_clean,
        "asset_url": asset_url,
        "asset_type": asset_type,
        "_brand_slug": brand_slug,
    }


def parse_xtrema_c1():
    """Parse the saved Xtrema C1 (Purchase Scaling) response from disk."""
    outer = json.loads(XTREMA_C1_PATH.read_text())
    inner = json.loads(outer["content"]) if isinstance(outer.get("content"), str) else outer
    out = []
    for r in inner["data"]:
        actions = r.get("actions") or []
        avs = r.get("action_values") or []
        proas = r.get("purchase_roas") or []
        thru_arr = r.get("video_thruplay_watched_actions") or []
        purch = next((int(float(a["value"])) for a in actions if a.get("action_type") == "omni_purchase"), 0)
        rev = next((float(a["value"]) for a in avs if a.get("action_type") == "omni_purchase"), 0.0)
        roas = next((float(a["value"]) for a in proas if a.get("action_type") == "omni_purchase"), 0.0)
        vid3s = next((int(float(a["value"])) for a in actions if a.get("action_type") == "video_view"), 0)
        thru = next((int(float(a["value"])) for a in thru_arr if a.get("action_type") == "video_view"), 0)
        spend = float(r.get("spend", 0))
        imp = int(r.get("impressions", 0))
        out.append({
            "ad_id": r.get("ad_id"),
            "ad_name": r.get("ad_name"),
            "campaign_id": r.get("campaign_id"),
            "campaign_name": r.get("campaign_name"),
            "adset_id": r.get("adset_id"),
            "adset_name": r.get("adset_name"),
            "spend": round(spend, 2),
            "impressions": imp,
            "clicks": int(r.get("clicks", 0)),
            "ctr_pct": round(float(r.get("ctr", 0)), 4),
            "cpm": round(float(r.get("cpm", 0)), 4),
            "cpc": round(float(r.get("cpc", 0)), 4),
            "purchases": purch,
            "revenue": round(rev, 2),
            "roas": round(roas, 4),
            "cpa": round(spend / purch, 2) if purch else 0,
            "video_3s": vid3s,
            "thruplays": thru,
            "hook_rate": (vid3s / imp) if imp else 0,
            "hold_rate": (thru / vid3s) if vid3s else 0,
            "thumb_url": r.get("cdn_thumbnail_url") or None,
            "asset_url": r.get("cdn_asset_url") or r.get("cdn_thumbnail_url") or None,
            "asset_type": (
                "video" if (r.get("cdn_asset_url") or "").endswith(".mp4")
                else ("image" if r.get("cdn_thumbnail_url") else None)
            ),
            "_brand_slug": "xtrema",
        })
    return out


def write_brand(slug, name, account_id, ads):
    total_spend = sum(a["spend"] for a in ads)
    total_imp = sum(a["impressions"] for a in ads)
    total_purch = sum(a["purchases"] for a in ads)
    total_rev = sum(a["revenue"] for a in ads)
    total_vid3s = sum(a["video_3s"] for a in ads)
    total_thru = sum(a["thruplays"] for a in ads)
    test_count = sum(1 for a in ads if "test" in (a.get("ad_name") or "").lower())
    out = {
        "account": {"id": account_id, "name": name},
        "generated_at": "2026-06-08T11:55:00Z",
        "date_range": {"since": "2026-05-09", "until": "2026-06-07", "label": "Last 30 days"},
        "totals": {
            "ad_count": len(ads),
            "total_spend": round(total_spend, 2),
            "total_impressions": total_imp,
            "total_purchases": total_purch,
            "total_revenue": round(total_rev, 2),
            "avg_cpa": round(total_spend / total_purch, 2) if total_purch else 0,
            "avg_roas": round(total_rev / total_spend, 4) if total_spend else 0,
            "test_count": test_count,
            "test_pct": round(test_count / len(ads), 4) if ads else 0,
            "blended_hook_rate": round(total_vid3s / total_imp, 4) if total_imp else 0,
            "blended_hold_rate": round(total_thru / total_vid3s, 4) if total_vid3s else 0,
        },
        "ads": ads,
    }
    path = ROOT / "brands" / slug / "data.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"{slug}: {len(ads)} ads | ${total_spend:,.2f} | ROAS {out['totals']['avg_roas']:.2f}x | tests {test_count} | hook {out['totals']['blended_hook_rate']*100:.1f}% | hold {out['totals']['blended_hold_rate']*100:.1f}%")


def main():
    slum_ads = []
    xtr_ads = []
    for brand, cb, ab in ROWS:
        r = parse_ad(brand, cb, ab)
        (slum_ads if brand == "slumberkins" else xtr_ads).append(r)
    xtr_ads = parse_xtrema_c1() + xtr_ads
    write_brand("slumberkins", "Slumberkins", "act_1939402463050546", slum_ads)
    write_brand("xtrema", "Xtrema Cookware Official", "act_1597243657678825", xtr_ads)


if __name__ == "__main__":
    main()
