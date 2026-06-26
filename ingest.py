#!/usr/bin/env python3
"""Ingest GoMarble ad-level insights responses into per-brand data.json files.

Handles two input shapes:
- Disk-saved MCP responses (auto-saved by harness when too big to return inline)
- Inline ad records (manually extracted slim records when responses came back inline)

For each ad, derives video_3s, thruplays, hook_rate, hold_rate, asset_url, asset_type
and writes to brands/<slug>/data.json under the `ads` key. Existing keys preserved.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
BRANDS_DIR = ROOT / "brands"
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


# (slug, file_path) — disk-saved big responses from this batch
DISK_FILES = [
    ("cherieattire", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782481909786.txt"),
    ("rvezy", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782481923829.txt"),
    ("pet-supplies", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782481943561.txt"),
    ("pet-supplies", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782481949767.txt"),
    # ----- Batch 2: tool-saved big responses -----
    ("cameron-hanes", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482668561.txt"),
    ("sophistiplate", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482681473.txt"),
    ("sophistiplate", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482687697.txt"),
    ("sophistiplate", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482691691.txt"),
    ("yahmo", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482702134.txt"),
    ("yahmo", "/Users/ilya/.claude/projects/-Users-ilya/72234306-b770-475b-b8e7-be3e6e27eb98/tool-results/mcp-41eb6bcb-8fcd-4a36-99a2-0db123a599b5-facebook_get_adaccount_insights-1782482709690.txt"),
    # ----- Batch 2: inline responses written to raw/per_ad/ -----
    ("cameron-hanes", "/Users/ilya/creative-perf-lite/raw/per_ad/cameron-hanes_120251149922270348.json"),
    ("cameron-hanes", "/Users/ilya/creative-perf-lite/raw/per_ad/cameron-hanes_120232027180000348.json"),
    ("cameron-hanes", "/Users/ilya/creative-perf-lite/raw/per_ad/cameron-hanes_120252345513870348.json"),
    ("sophistiplate", "/Users/ilya/creative-perf-lite/raw/per_ad/sophistiplate_6542929634294.json"),
    ("sophistiplate", "/Users/ilya/creative-perf-lite/raw/per_ad/sophistiplate_6919434762294.json"),
    ("sophistiplate", "/Users/ilya/creative-perf-lite/raw/per_ad/sophistiplate_6955449199294.json"),
    ("yahmo", "/Users/ilya/creative-perf-lite/raw/per_ad/yahmo_120246201644110774.json"),
    ("yahmo", "/Users/ilya/creative-perf-lite/raw/per_ad/yahmo_120246217885220774.json"),
    ("yahmo", "/Users/ilya/creative-perf-lite/raw/per_ad/yahmo_120243302861720774.json"),
    ("yahmo", "/Users/ilya/creative-perf-lite/raw/per_ad/yahmo_120233906545900774.json"),
]


# Pipe-delimited inline ads (last 13 fields fixed; ad_name may contain pipes).
# Format: slug|ad_id|ad_name|campaign_id|campaign_name|adset_id|adset_name|spend|imp|clk|ctr|cpm|cpc|purch|rev|roas|vid3s|thru|thumb
INLINE_ROWS = [
    # ----- Cherie US/AU | RM | Conversions (6 ads) -----
    "cherieattire|120244550777120413|Carousel ad | Collections|120238899887740413|US/AU | RM | Conversions|120244550777050413|US | RM 180d | IG | Collections | Catalog | New|24989.93|22108|1381|6.246608|1130.356884|18.095532|7|95442.78|3.81925|139|65|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ad1a08c7-f66f-4cb2-a8f4-b1af7e6c44d8.jpg",
    "cherieattire|120244067016700413|Catalog | Carousel | Collections|120238899887740413|US/AU | RM | Conversions|120244067016720413|AU | RM 180d | IG | Collections | Catalog | New pixel|14412.45|23841|1337|5.607986|604.52372|10.779693|5|74570.86|5.174059|213|61|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/920e2890-f017-491f-ad46-2dd8df396cc7.jpg",
    "cherieattire|120244550777070413|Catalog | Carousel | PRIMAVERA|120238899887740413|US/AU | RM | Conversions|120244550777050413|US | RM 180d | IG | Collections | Catalog | New|2306.18|2355|98|4.161359|979.269639|23.532449|0|0|0|5|4|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/31213da9-80a3-45ef-ad26-c5ce18403fb6.jpg",
    "cherieattire|120246458490440413|Catalog ad | A Study in Lace|120238899887740413|US/AU | RM | Conversions|120244067016720413|AU | RM 180d | IG | Collections | Catalog | New pixel|1785.41|3034|98|3.230059|588.46737|18.218469|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/31ebfcbe-c437-4724-8fc0-319da464096b.jpg",
    "cherieattire|120246458403610413|Catalog ad | A study in lace|120238899887740413|US/AU | RM | Conversions|120244550777050413|US | RM 180d | IG | Collections | Catalog | New|1330.9|1140|30|2.631579|1167.45614|44.363333|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/31ebfcbe-c437-4724-8fc0-319da464096b.jpg",
    "cherieattire|120244067016710413|Catalog | Carousel | PRIMAVERA|120238899887740413|US/AU | RM | Conversions|120244067016720413|AU | RM 180d | IG | Collections | Catalog | New pixel|338.16|558|17|3.046595|606.021505|19.891765|0|0|0|15|2|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/b4b00577-caf5-4147-b06c-16575a8e23a5.jpg",
    # ----- Cherie UK/CA Prospecting (8 ads) -----
    "cherieattire|120246458375870413|Image ad | A study in lace | Charlotte Halter Top - Copy 2|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|9359.7|15433|853|5.527117|606.473142|10.972685|5|52747.05|5.635549|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f623d1fd-29b8-4247-af5c-2c1f55b358c7.jpg",
    "cherieattire|120245064264600413|Test - Image ad | Bianca Top - PRIMAVERA -|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|5359.18|10515|222|2.11127|509.669995|24.14045|3|38856.15|7.250391|1|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/a3512e73-571e-4647-a038-e72e4a5ead52.jpg",
    "cherieattire|120245064264590413|Image ad | Esperanza maxi dress -|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|3185.48|4537|257|5.664536|702.111527|12.394864|1|15430.76|4.844093|2|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/99a70307-37c6-47f1-a31f-65ce033b9c4e.jpg",
    "cherieattire|120245064264320413|Test - Image ad | Bianca Top - PRIMAVERA -|120245063568930413|UK/CA | Prospecting | Conversions|120245063568250413|UK, CA | INT | W, 20-35|2152.72|5216|58|1.111963|412.714724|37.115862|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3a2d2567-d584-4dd8-846f-8c16f5ab0092.jpg",
    "cherieattire|120245064264310413|Image ad | Esperanza maxi dress -|120245063568930413|UK/CA | Prospecting | Conversions|120245063568250413|UK, CA | INT | W, 20-35|2126.71|5349|47|0.878669|397.590204|45.249149|0|0|0|1|1|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/99a70307-37c6-47f1-a31f-65ce033b9c4e.jpg",
    "cherieattire|120246458375860413|Image ad | A study in lace | Sonia Corset Top Black - Copy 2|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|348.28|669|29|4.334828|520.597907|12.009655|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ec9b5932-c540-4c9c-a2bb-e69d0b1239c5.jpg",
    "cherieattire|120247216766180413|Video ad | A study in lace|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|247.75|441|11|2.494331|561.791383|22.522727|0|0|0|74|7|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d1beb95f-2391-4fb6-93c2-7d1f05d1368a_d673cfa6-c068-4ea4-a0f8-83c0322de4a9.jpg",
    "cherieattire|120246458375850413|Image ad | A study in lace | Charlotte Halter Top v2 - Copy 2|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|216.71|398|20|5.025126|544.497487|10.8355|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/07af5b72-6c96-4664-9cfe-a01100bdc1d8.jpg",
    "cherieattire|120246458375880413|Image ad | A study in lace | Fleur Long Sleeve Corset Top Ivory - Copy 2|120245063568930413|UK/CA | Prospecting | Conversions|120245063568240413|UK, CA | Broad | W, 20-35|177.83|234|8|3.418803|759.957265|22.22875|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/2a3e0e89-304e-431f-afce-cee3451571a3.jpg",
    # ----- Cherie UK/CA/US/AU Engagement (3 ads) -----
    "cherieattire|120245531802480413|Engagement Ad | Video ad | PRIMAVERA|120245531125490413|UK/CA/US/AU Engagement|120245531125500413|Engagement Ad Set|6628.06|37079|3748|10.108147|178.75509|1.768426|0|0|0|7415|507|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/70125563-a1d8-4ce6-bd64-1758ed9f4272_28fc4983-3345-4e00-98f1-ceb98b0da8de.jpg",
    "cherieattire|120245532903760413|Engagement Ad | Video ad | Elena Mini Dress|120245531125490413|UK/CA/US/AU Engagement|120245531125500413|Engagement Ad Set|9.95|63|6|9.52381|157.936508|1.658333|0|0|0|10|5|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3f962b17-f59e-4462-b030-031ef6362c26_c7200ee4-7dd5-469a-9036-7991cd95099d.jpg",
    "cherieattire|120247215059680413|Engagement Ad | @snejanajens in bianca top|120245531125490413|UK/CA/US/AU Engagement|120245531125500413|Engagement Ad Set|0.1|1|0|0|100|0|0|0|0|0|0|",
    # ----- Rvezy Owner 4-Locations 2026 (3 ads) -----
    "rvezy|6872224440062|Static Ad | Laissez votre VR - french - Copy|6868593589662|FACEBOOK+CAN+Owner+4-Locations+2026|6868593587662|Quebec - French | Application Submit | Broad - 25+|9899.24|1099161|20319|1.848592|9.006178|0.487191|8|9294.24|0.938884|458|244|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/03a1a3e0-1742-457e-a407-6e3cb1553d18.jpg",
    "rvezy|6937985791262|VIDEO: Entrepreneur V2|6868593589662|FACEBOOK+CAN+Owner+4-Locations+2026|6868593587662|Quebec - French | Application Submit | Broad - 25+|2452.81|202268|3686|1.822335|12.126535|0.66544|5|6234.36|2.541722|52592|10505|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/7e7a4415-f0aa-41bd-83f7-ea0bb879746f_0ee22957-1f7f-47a6-aa1a-2349cb637fa8.jpg",
    "rvezy|6921103096662|VIDEO: Podcast Ad #1 - Side Hustle - French|6868593589662|FACEBOOK+CAN+Owner+4-Locations+2026|6868593587662|Quebec - French | Application Submit | Broad - 25+|2098.73|123105|2436|1.978799|17.048292|0.861548|0|0|0|34055|7259|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ec949349-d238-4e80-b19d-8c1402bcdeb2_e00244b5-6421-4b88-93b7-dc4d42273d4d.jpg",
    "rvezy|6937985434462|VIDEO: Entrepreneur V!|6868593589662|FACEBOOK+CAN+Owner+4-Locations+2026|6868593587662|Quebec - French | Application Submit | Broad - 25+|1851.9|134602|2564|1.904875|13.758339|0.72227|2|3397.41|1.834554|37163|7312|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/0975f752-a379-445d-8f85-4f66f3756760_d3497335-4240-4852-999b-952fd5fbb911.jpg",
    # ----- Rvezy Renter Prospecting Conversions June 2026 (5 ads) -----
    "rvezy|6951902377462|VIDEO: Boys Trip - v2|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|3464.57|195010|6502|3.334188|17.766115|0.532847|34|50127.18|14.468514|49167|12210|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ee1b81d7-8f6a-42f5-af1a-215ef49bfc70_3df710cf-3aec-43d3-8842-004543ce7683.jpg",
    "rvezy|6944656762262|VIDEO: Concert|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|2618.1|146446|8095|5.527635|17.877579|0.323422|19|23555.97|8.997353|43064|19091|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/23f24f89-0265-4801-b4f8-39b0f053743d_cc71054c-d9b3-414a-9192-87aa7cd30a40.jpg",
    "rvezy|6944656508862|VIDEO: Boys Trip|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|1632.49|87707|3826|4.362252|18.612996|0.426683|27|35040.36|21.464364|22974|9961|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/d2b1b676-e994-4299-a5e3-5117d7fbe1fb_f601d9e5-d1b9-4b1a-ac37-7f1e19f98cf5.jpg",
    "rvezy|6944656973062|VIDEO: Couple|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|809.57|48427|1698|3.506308|16.717327|0.476779|3|2899.49|3.581519|11046|3711|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/28bc6542-74c8-4b0e-8cf1-f4fe3e7a82bb_297850c0-15c6-4ef8-bd5a-b33b96abd0b7.jpg",
    "rvezy|6944655620862|vid-ugc1-58s-jul24-can-web-adj|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|446.77|26429|1194|4.517765|16.904537|0.374179|2|1224.17|2.740045|7817|2590|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/8acb39ef-f4e5-4374-8bd0-9656c9d09404_52208b84-a9fc-48f8-83d6-72b330291a1f.jpg",
    "rvezy|6944655620662|Carousel-Ad1|6944567544462|FACEBOOK+CAN+Renter+Prospecting+Conversions+June-2026|6944655621062|broad-cold-ca-25plus-purch-7dc|173.96|11370|357|3.139842|15.299912|0.487283|3|3432.33|19.73057|1042|611|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/db0cf668-762b-43d6-bf63-923a8437e644.jpg",
    # ----- Rvezy Renter Retargeting Sales May 2025 (2 ads) -----
    "rvezy|6856094810062|vid-ugc1-15s-jul24-ca-web-4x5 - Copy|6856071894462|FACEBOOK+CAN+Renter+Retargeting+Sales+May+2025|6856079836862|ca-IG/FB-engagers-25plus-purch-7dc - Copy|2990.5|385692|4411|1.143659|7.753596|0.677964|173|228065.12|76.263207|48402|8320|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3eb2436b-c50e-47b1-a22d-5e513dfc91cc_7c1ac7fd-e0aa-416a-b8fd-d8cdc537201f.jpg",
    "rvezy|6856081384062|vid-ugc1-15s-jul24-ca-web-4x5|6856071894462|FACEBOOK+CAN+Renter+Retargeting+Sales+May+2025|6856071894062|ca-rental-visitors-180d-25plus-purch-7dc|2987.37|228411|4092|1.791507|13.078924|0.730051|539|641791.87|214.835079|34165|8772|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3eb2436b-c50e-47b1-a22d-5e513dfc91cc_7c1ac7fd-e0aa-416a-b8fd-d8cdc537201f.jpg",
    # ----- Rvezy Renter APP iOS14 Prospecting Jan 2026 (6 ads) -----
    "rvezy|6556198910062|vid-ugc1-30s-jul24-can-app-ios-adj|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|1602.64|144049|1879|1.304417|11.125659|0.852922|0|0|0|48708|9619|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/f0d633e9-6fe5-4d50-ac7a-627377f37eb6_4c4f1739-95f8-4d28-a4a6-a213d68f5ba6.jpg",
    "rvezy|6559063160062|app-img-071224-can-v1-iOS|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|791|98902|725|0.733049|7.997816|1.091034|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3d977f40-b8bb-41a2-aa83-eeee15b22b75.jpg",
    "rvezy|6556198910462|vid-ugc1-15s-jul24-can-app-ios-adj|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|350.44|33514|381|1.136838|10.456526|0.91979|0|0|0|11289|1523|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4d0e6a5c-e2c7-4587-8347-f431bbf68426_0361f110-d2c2-4da1-8fd4-a57809e60242.jpg",
    "rvezy|6556198910862|vid-ugc1-45s-jul24-can-app-ios-adj|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|224.76|16842|245|1.454697|13.345208|0.917388|0|0|0|6126|1458|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e9054e72-0035-4681-92d9-39a0385e0201_f905b3cd-54bd-43a2-9bda-b877bcb99422.jpg",
    "rvezy|6559063159862|app-img-071224-can-v3-iOS|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|33.41|3499|61|1.743355|9.548442|0.547705|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/ac4d682a-42f3-4ff3-bd85-a84e4770eb5f.jpg",
    "rvezy|6559063160262|app-img-071224-can-v2-iOS|6553447348262|FACEBOOK+CAn+Renter+APP+iOS14+Prospecting-Jan2026|6556198555062|broad-cold-adv-ca-35plus-installs|7.49|1188|7|0.589226|6.304714|1.07|0|0|0|0|0|https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/5ac46643-d05c-4066-ab13-27ba36bc373a.jpg",
]


def derive_asset(thumb_url):
    if not thumb_url:
        return None, None
    basename = thumb_url.rsplit("/", 1)[-1]
    if basename.endswith(".jpg"):
        stem = basename[:-4]
        parts = stem.split("_")
        if len(parts) == 2 and UUID_RE.match(parts[0]) and UUID_RE.match(parts[1]):
            return f"{thumb_url.rsplit('/', 1)[0]}/{parts[0]}.mp4", "video"
        return thumb_url, "image"
    if basename.endswith(".mp4"):
        return thumb_url, "video"
    return thumb_url, "image"


def slim_from_raw(r, brand_slug):
    """Extract slim ad record from a raw GoMarble insights row."""
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
    thumb = r.get("cdn_thumbnail_url") or None
    asset_from_raw = r.get("cdn_asset_url") or None
    if asset_from_raw and asset_from_raw.endswith(".mp4"):
        asset_url, asset_type = asset_from_raw, "video"
    elif thumb:
        asset_url, asset_type = derive_asset(thumb)
    else:
        asset_url, asset_type = None, None
    return {
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
        "thumb_url": thumb,
        "asset_url": asset_url,
        "asset_type": asset_type,
        "_brand_slug": brand_slug,
    }


def parse_disk(path):
    outer = json.loads(Path(path).read_text())
    inner = json.loads(outer["content"]) if isinstance(outer.get("content"), str) else outer
    return inner.get("data", [])


def parse_inline(row):
    """Parse a pipe-separated inline row. Schema: ad_name may contain pipes,
    everything else is fixed-position."""
    parts = row.split("|")
    # 18 schema parts: slug, ad_id, ad_name (variable), campaign_id, campaign_name,
    # adset_id, adset_name, spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, vid3s, thru, thumb
    # campaign_id is the first digits-only long string after ad_id
    slug = parts[0]
    ad_id = parts[1]
    # Find campaign_id index — first all-digit long string starting from idx 3
    cid_idx = next(i for i in range(3, len(parts)) if parts[i].strip().isdigit() and len(parts[i].strip()) > 10)
    ad_name = "|".join(parts[2:cid_idx]).strip()
    # After cid: cname (variable pipes), asid, asname (variable pipes), then 12 fixed numeric fields + thumb = 13
    cid = parts[cid_idx].strip()
    # asid_idx = next long digit after cid
    asid_idx = next(i for i in range(cid_idx + 1, len(parts)) if parts[i].strip().isdigit() and len(parts[i].strip()) > 10)
    cname = "|".join(parts[cid_idx + 1:asid_idx]).strip()
    asid = parts[asid_idx].strip()
    # 12 fixed fields after asname: spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, vid3s, thru, thumb
    tail = parts[-12:]
    asname = "|".join(parts[asid_idx + 1:-12]).strip()
    spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, vid3s, thru, thumb = tail
    spend_f = float(spend) if spend else 0.0
    purch_i = int(purch) if purch else 0
    rev_f = float(rev) if rev else 0.0
    imp_i = int(imp) if imp else 0
    vid3s_i = int(vid3s) if vid3s else 0
    thru_i = int(thru) if thru else 0
    thumb = thumb.strip() or None
    asset_url, asset_type = derive_asset(thumb)
    return slug, {
        "ad_id": ad_id, "ad_name": ad_name,
        "campaign_id": cid, "campaign_name": cname,
        "adset_id": asid, "adset_name": asname,
        "spend": round(spend_f, 2), "impressions": imp_i,
        "clicks": int(clk) if clk else 0,
        "ctr_pct": round(float(ctr), 4) if ctr else 0,
        "cpm": round(float(cpm), 4) if cpm else 0,
        "cpc": round(float(cpc), 4) if cpc else 0,
        "purchases": purch_i, "revenue": round(rev_f, 2),
        "roas": round(float(roas), 4) if roas else 0,
        "cpa": round(spend_f / purch_i, 2) if purch_i else 0,
        "video_3s": vid3s_i, "thruplays": thru_i,
        "hook_rate": (vid3s_i / imp_i) if imp_i else 0,
        "hold_rate": (thru_i / vid3s_i) if vid3s_i else 0,
        "thumb_url": thumb,
        "asset_url": asset_url, "asset_type": asset_type,
        "_brand_slug": slug,
    }


def main():
    by_slug = {}

    # Disk-saved (the big ones)
    for slug, path in DISK_FILES:
        for raw in parse_disk(path):
            by_slug.setdefault(slug, []).append(slim_from_raw(raw, slug))

    # Inline
    for row in INLINE_ROWS:
        slug, ad = parse_inline(row)
        by_slug.setdefault(slug, []).append(ad)

    # Update brand data.json files (preserve all non-ad fields)
    for slug, ads in by_slug.items():
        path = BRANDS_DIR / slug / "data.json"
        if not path.exists():
            print(f"warn: no existing data.json for {slug}; skipping")
            continue
        data = json.loads(path.read_text())
        data["ads"] = ads
        # Recompute ad-based totals
        t = data.get("totals", {})
        spend = sum(a["spend"] for a in ads)
        purch = sum(a["purchases"] for a in ads)
        rev = sum(a["revenue"] for a in ads)
        imp = sum(a["impressions"] for a in ads)
        v3s = sum(a["video_3s"] for a in ads)
        thru = sum(a["thruplays"] for a in ads)
        tests = sum(1 for a in ads if "test" in (a.get("ad_name") or "").lower())
        t.update({
            "ad_count": len(ads),
            "total_spend_from_ads": round(spend, 2),
            "total_impressions": imp,
            "total_purchases_from_ads": purch,
            "total_revenue_from_ads": round(rev, 2),
            "avg_cpa_from_ads": round(spend / purch, 2) if purch else 0,
            "avg_roas_from_ads": round(rev / spend, 4) if spend else 0,
            "test_count": tests,
            "test_pct": round(tests / len(ads), 4) if ads else 0,
            "blended_hook_rate": round(v3s / imp, 4) if imp else 0,
            "blended_hold_rate": round(thru / v3s, 4) if v3s else 0,
        })
        data["totals"] = t
        path.write_text(json.dumps(data, indent=2))
        print(f"{slug}: wrote {len(ads)} ads | spend ${spend:,.2f} | purch {purch} | rev ${rev:,.2f}")


if __name__ == "__main__":
    main()
