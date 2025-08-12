import os, json, glob, datetime
from typing import List, Dict

import pandas as pd

# Env vars
EXCEL_PATH = os.getenv("EXCEL_PATH", "data/assets.xlsx")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "public/datafeed.json")
MAX_ASSETS = int(os.getenv("MAX_ASSETS", "12"))

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Try to locate an Excel file if the configured path is missing
if not os.path.exists(EXCEL_PATH):
    candidates: List[str] = []
    for pat in ("data/*.xlsx", "*.xlsx", "**/*.xlsx"):
        candidates.extend(glob.glob(pat, recursive=True))
    if candidates:
        EXCEL_PATH = sorted(candidates)[0]

# Load the first non empty sheet
assets: List[Dict] = []
if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_name = None
    for sn in xls.sheet_names:
        df = xls.parse(sn)
        if df.dropna(how="all").shape[0] > 0:
            sheet_name = sn
            break
    if sheet_name is None:
        df = pd.DataFrame()
    else:
        df = xls.parse(sheet_name)
else:
    df = pd.DataFrame()

# Normalize headers
if not df.empty:
    df.columns = [str(c).strip() for c in df.columns]

# Map columns to asset fields
name_cols = ["Asset Name","Asset","Name","Site","Location Name"]
sector_cols = ["Sector","Industry","CI Sector"]

seen = set()
for _, row in df.iterrows():
    name = None
    for c in name_cols:
        if c in df.columns and pd.notna(row.get(c)):
            v = str(row.get(c)).strip()
            if v and v.lower() not in ("nan","none"):
                name = v
                break
    if not name:
        continue
    if name in seen:
        continue
    seen.add(name)

    sector = None
    for c in sector_cols:
        if c in df.columns and pd.notna(row.get(c)):
            sector = str(row.get(c)).strip()
            break

    assets.append({"name": name, "sector": sector})

# Fallback demo assets if Excel is missing or empty
if not assets:
    assets = [
        {"name":"Water Treatment Plant 1","sector":"Water and Wastewater Systems"},
        {"name":"Substation Delta","sector":"Energy"},
        {"name":"HQ and SCADA","sector":"Information Technology"},
        {"name":"Cold Chain Hub North","sector":"Healthcare and Public Health"},
        {"name":"Corridor B Crossing","sector":"Transportation Systems"},
        {"name":"Port Gate 3","sector":"Transportation Systems"},
    ]

assets = assets[:MAX_ASSETS]

# Build signals referencing known assets
now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
get = lambda i, fallback: assets[i]["name"] if len(assets) > i else fallback

signals = [
    {
        "type": "incident",
        "assetId": get(0, "Water Treatment Plant 1"),
        "severity": 3,
        "summary": f"Unauthorized access attempt detected at {get(0, 'Asset-1')}.",
        "source": "soc-ticket-demo"
    },
    {
        "type": "intel",
        "severity": 4,
        "summary": f"Regional threat bulletin mentions critical infrastructure near {get(1, 'Asset-2')}.",
        "source": "analyst-brief-demo"
    },
    {
        "type": "cve",
        "severity": 5,
        "product": "VendorX Gateway 3.2",
        "cvss": 9.8,
        "kev": True,
        "summary": "Critical RCE with public exploit. Review perimeter devices at sites handling remote access.",
        "source": "nvd-cve-2025-12345",
        "url": "https://example.org/cve/2025-12345"
    },
    {
        "type": "access",
        "severity": 3,
        "route": "Corridor B",
        "status": "restricted",
        "summary": "Two new checkpoints and an extended curfew window impacting deliveries.",
        "source": "cluster-update-demo"
    },
    {
        "type": "weather",
        "severity": 2,
        "summary": f"Flood watch near logistics route serving {get(2, 'Asset-3')} for the next 48 hours.",
        "source": "met-service-demo"
    },
    {
        "type": "economic",
        "severity": 2,
        "summary": "Fuel prices up 12 percent week over week in Region West.",
        "source": "national-stats-demo"
    }
]

feed = {
    "updated": now,
    "signals": signals,
    "indicators": {
        "acled_proximity_high": [get(0, "Asset-1"), get(1, "Asset-2")],
        "kev_products": ["VendorX Gateway 3.2"],
        "fx_reserve_months": 1.8
    }
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(feed, f, indent=2)

print(f"Wrote {OUTPUT_PATH} with {len(signals)} signals and {len(assets)} referenced assets")