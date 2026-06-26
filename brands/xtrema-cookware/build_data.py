#!/usr/bin/env python3
"""Xtrema (act_1597243657678825) — assemble data.json from per-campaign
GoMarble insights + creative_details_slim enrichment.

Source: facebook_get_adaccount_insights (level=ad, last_30d) per campaign,
2026-06-08 pull for window 2026-05-09 → 2026-06-07.
- Campaign 1 (Purchase Scaling, $12,098): response was too big to return
  inline (>40KB token cap) — saved by MCP harness to disk and parsed into
  raw/c1_slim.json by parse_inputs.py.
- Campaigns 2-5: extracted inline from MCP responses and embedded below.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent
C1_PATH = ROOT / "raw" / "c1_slim.json"
DETAILS_PATH = ROOT / "raw" / "creative_details_slim.json"


# Campaigns 2-5 inline. Tuple order:
# ad_id, ad_name, campaign_id, campaign_name, adset_id, adset_name,
# spend, impressions, clicks, ctr_pct, cpm, cpc,
# purchases, revenue, roas, thumb_url
C2_C5_ADS = [
    # ---- C2: P | New One Campaign | Flexi Ads (3 ads, $6,405.77) ----
    ("120247616301350350", "XTR799 | Video | Dynamic Copy | Home Page |  Spring Cleaning", "120235361670130350", "P | New One Campaign | Flexi Ads", "120235361670150350", "New One Campaign | Flexi Ads | EX PUR 180 D", 5064.50, 203066, 3630, 1.787596, 24.940167, 1.395179, 33, 8367.82, 1.65225, None),
    ("120247616873540350", "XTR801 | Video | Dynamic Copy | Home Page | Modern Healthy Kitchen", "120235361670130350", "P | New One Campaign | Flexi Ads", "120235361670150350", "New One Campaign | Flexi Ads | EX PUR 180 D", 1080.11, 49424, 973, 1.968679, 21.853958, 1.110082, 11, 3037.58, 2.812288, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fcb4084e-a575-40a7-a812-5b4d72d2f46f.jpg"),
    ("120235684414240350", "XTR689 | Flexible Videos | Non-Stick Switch V1 | Home Page - Copy", "120235361670130350", "P | New One Campaign | Flexi Ads", "120235361670150350", "New One Campaign | Flexi Ads | EX PUR 180 D", 261.16, 15008, 302, 2.01226, 17.401386, 0.864768, 1, 14.97, 0.057321, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/936e6f8c-7018-45eb-90ec-840a278ace26_67f91e11-e924-4173-9b55-b103f1d92453.jpg"),
    # ---- C3: P | Creator Partnership Campaign (5 ads, $5,052.40) ----
    ("120244608721000350", "Kayla Young- Video 2- February 2026", "120239145232560350", "P | Creator Partnership Campaign", "120239145232570350", "Creator Partnership | Excluding PUR 180D", 3611.92, 148659, 7398, 4.97649, 24.296679, 0.488229, 29, 11706.72, 3.241135, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/08b446fe-5a1a-4203-b6bf-bef0644a1b3e.jpg"),
    ("120245911506150350", "Kayla Young- Video 3 - February 2026", "120239145232560350", "P | Creator Partnership Campaign", "120239145232570350", "Creator Partnership | Excluding PUR 180D", 440.43, 27072, 1397, 5.160313, 16.268839, 0.315268, 3, 224.18, 0.509003, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c7ed6a83-77f1-44ad-92c0-d8297b58c5a0.jpg"),
    ("120250401283650350", "Test - Jasmin Shannon - Banana Pancakes Video - May 2026", "120239145232560350", "P | Creator Partnership Campaign", "120239145232570350", "Creator Partnership | Excluding PUR 180D", 361.08, 15818, 487, 3.078771, 22.827159, 0.741437, 1, 402.00, 1.113327, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/69f1bf3a-fd8a-4190-a964-c856f311f784_f25dcfc9-d4c5-4ac7-8c45-ccdde0956424.jpg"),
    ("120245494330330350", "Aroshaliny Feb 2026", "120239145232560350", "P | Creator Partnership Campaign", "120239145232570350", "Creator Partnership | Excluding PUR 180D", 325.52, 16229, 818, 5.04036, 20.057921, 0.397946, 6, 2241.28, 6.88523, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/c2b48afb-43d1-4c3a-80f3-ccc8bfbe757b.jpg"),
    ("120250401283640350", "Test - Jasmin Shannon - Chocolate Chip Cookie Video - May 2026", "120239145232560350", "P | Creator Partnership Campaign", "120239145232570350", "Creator Partnership | Excluding PUR 180D", 313.45, 16616, 430, 2.587867, 18.864348, 0.728953, 2, 378.87, 1.20871, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/fcb0dd7b-2ccf-4ec3-89ea-0169b8fb468e_f2fcbb68-52db-4e24-88bd-e73dd5f81845.jpg"),
    # ---- C4: P | BCH | Bid Cap Campaign | $105 cost (12 ads, $1,820.68) ----
    ("120214102064870350", "XTR201 | Image | Ceramics have been | Sale Page", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120214101753240350", "BCH1 | Broad | $105 cost", 570.27, 73079, 289, 0.395462, 7.803473, 1.973253, 15, 4555.56, 7.988427, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/74fa106e-1101-4a88-9417-2392b1dbb4e7.jpg"),
    ("120221091184920350", "XTR451 | Image | Dynamic copy | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120218990152640350", "BCH3 | Broad | $105 cost | New Ads", 468.63, 55591, 309, 0.555845, 8.429962, 1.516602, 4, 2433.82, 5.193479, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/22b7e6fd-6cad-462b-94f7-7d0c808ec3c9.jpg"),
    ("120239542295930350", "XTR704 | Flexible Videos | Flaking Non-stick Pans UGC | Home Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120239542266870350", "BCH5 | Broad | $105 cost | New Ads Q4", 324.82, 28240, 583, 2.064448, 11.502125, 0.557153, 9, 2940.50, 9.052706, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/21ff1d02-f55e-4cb2-be56-c7091a7d7422.jpg"),
    ("120228835903820350", "XTR549 | Video | H5B1CTA2 | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120228835862310350", "BCH4 | Broad | $105 cost | New Ads May", 171.97, 13983, 216, 1.544733, 12.298505, 0.796157, 2, 475.17, 2.763098, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e2c2a379-91b9-4ab8-9cfc-9ec1b255d0a4_7e0cb999-1a95-4332-8986-fc8ed0c098d7.jpg"),
    ("120214101984320350", "XTR200 | Image | Ceramics have been | Sale Page", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120214101753240350", "BCH1 | Broad | $105 cost", 85.23, 9686, 43, 0.44394, 8.799298, 1.982093, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/3b382fa5-7ed8-48c7-a254-e833af7a83da.jpg"),
    ("120214101753250350", "XTR199 | Image | Ceramics have been | Sale Page", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120214101753240350", "BCH1 | Broad | $105 cost", 55.32, 6725, 24, 0.356877, 8.226022, 2.305, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/5e960a9d-e8d2-4504-9dac-902688c6bf66.jpg"),
    ("120214102107910350", "XTR202 | Image | Ceramics have been | Sale Page", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120214101753240350", "BCH1 | Broad | $105 cost", 54.54, 6235, 31, 0.497193, 8.747394, 1.759355, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/19df8b25-8f9b-4963-8f03-bdaac6182df7.jpg"),
    ("120221091184910350", "XTR454 | Image | Dynamic copy | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120218990152640350", "BCH3 | Broad | $105 cost | New Ads", 45.84, 5769, 27, 0.468019, 7.945918, 1.697778, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/8fc8e4b0-bae0-451e-9e65-6f1362efc360.jpg"),
    ("120218990180820350", "XTR422 | Image | Dynamic copy | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120218990152640350", "BCH3 | Broad | $105 cost | New Ads", 28.03, 3084, 18, 0.583658, 9.088846, 1.557222, 1, 205.11, 7.317517, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/4656093a-c421-427b-b926-c36492f3c3ac.jpg"),
    ("120214102144480350", "XTR204 | Video | Ceramics have been | Sale Page", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120214101753240350", "BCH1 | Broad | $105 cost", 8.19, 747, 12, 1.606426, 10.963855, 0.6825, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/e7ea0508-e14a-41c8-a2c7-42a3e92113c8_2fc7cb59-70c1-40b8-bbc0-33894247e958.jpg"),
    ("120218990180810350", "XTR403 | Image | Dynamic copy | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120218990152640350", "BCH3 | Broad | $105 cost | New Ads", 5.73, 644, 2, 0.310559, 8.897516, 2.865, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/01aaa86f-0803-476f-8347-515b64964148.jpg"),
    ("120228835903830350", "XTR497 | Video | Dynamic copy | Sale Page - Copy", "120214101753260350", "P | BCH | Bid Cap Campaign | $105 cost", "120228835862310350", "BCH4 | Broad | $105 cost | New Ads May", 2.11, 179, 2, 1.117318, 11.78771, 1.055, 0, 0, 0, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/6e5692fb-3267-43de-b1c5-cde05e226f0e_7a26e298-896d-494f-b549-853833f6c784.jpg"),
    # ---- C5: SCC | Mother's Day Campaign (1 ad, $372.70) ----
    ("120247852351700350", "XTR803 | Flexible Images | Dynamic Copy | Home Page | Mother's Day Campaign", "120247852351670350", "SCC | Mother's Day Campaign", "120247852351660350", "SCC | Mother's Day Campaign", 372.70, 22270, 211, 0.947463, 16.735519, 1.766351, 7, 2230.56, 5.984867, "https://assets-organizer-cdn.gomarble.ai/mcp-agent/ad-assets/bed8afe1-b2bf-43b8-8aa0-6a19c716641c.jpg"),
]


def main():
    # Load C1 from disk (parsed earlier from MCP harness's saved file)
    c1 = json.loads(C1_PATH.read_text())
    # Load creative enrichment
    details = {d["ad_id"]: d for d in json.loads(DETAILS_PATH.read_text())}

    ads = list(c1)
    for row in C2_C5_ADS:
        ad_id, ad_name, cid, cname, asid, asname, spend, imp, clk, ctr, cpm, cpc, purch, rev, roas, thumb = row
        ads.append({
            "ad_id": ad_id, "ad_name": ad_name,
            "campaign_id": cid, "campaign_name": cname,
            "adset_id": asid, "adset_name": asname,
            "spend": round(spend, 2), "impressions": int(imp),
            "clicks": int(clk), "ctr_pct": round(ctr, 4),
            "cpm": round(cpm, 4), "cpc": round(cpc, 4),
            "purchases": int(purch), "revenue": round(rev, 2),
            "roas": round(roas, 4), "thumb_url": thumb,
        })

    # Join creative details + compute CPA
    for a in ads:
        det = details.get(a["ad_id"], {})
        a["ad_status"] = det.get("ad_status")
        a["ad_effective_status"] = det.get("ad_effective_status")
        a["creative_id"] = det.get("creative_id")
        a["creative_name"] = det.get("creative_name")
        a["creative_name_is_templated"] = bool(det.get("creative_name") and "{{" in det["creative_name"])
        a["cpa"] = round(a["spend"] / a["purchases"], 2) if a["purchases"] else 0.0

    # Totals
    total_spend = sum(a["spend"] for a in ads)
    total_imp = sum(a["impressions"] for a in ads)
    total_purch = sum(a["purchases"] for a in ads)
    total_rev = sum(a["revenue"] for a in ads)
    avg_cpa = (total_spend / total_purch) if total_purch else 0.0
    avg_roas = (total_rev / total_spend) if total_spend else 0.0
    named_pct = sum(1 for a in ads if a["creative_name"]) / len(ads)
    templated_pct = sum(1 for a in ads if a["creative_name_is_templated"]) / len(ads)

    out = {
        "account": {"id": "act_1597243657678825", "name": "Xtrema Cookware Official"},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "date_range": {"since": "2026-05-09", "until": "2026-06-07", "label": "Last 30 days"},
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
    print(f"Total spend: ${total_spend:,.2f}  |  purchases: {total_purch}  |  revenue: ${total_rev:,.2f}")
    print(f"Avg CPA: ${avg_cpa:.2f}  |  Avg ROAS: {avg_roas:.2f}x")
    print(f"creative_name populated: {named_pct*100:.0f}%  |  templated: {templated_pct*100:.0f}%")


if __name__ == "__main__":
    main()
