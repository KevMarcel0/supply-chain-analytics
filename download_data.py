"""
Download the real DataCo Global supply chain dataset (free, public)
===================================================================
The raw file is ~91 MB, so it is NOT stored in this repo. Run this once to
fetch it into ./realdata/, then run analysis_real.py.

    python3 download_data.py

Dataset: "DataCo Smart Supply Chain for Big Data Analysis"
  - 180,519 real orders, 53 columns, 2015-2018
  - Source (free): Kaggle + public GitHub mirrors + Mendeley Data
  - Mendeley DOI: 10.17632/8gx2fvg2k6.3  (Fabian Constante et al., 2019)
"""

import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "realdata"
OUT.mkdir(exist_ok=True)

BASE = ("https://raw.githubusercontent.com/ashishpatel26/"
        "DataCo-SMART-SUPPLY-CHAIN-FOR-BIG-DATA-ANALYSIS/main/")

FILES = [
    "DataCoSupplyChainDataset.csv",       # the data (~91 MB)
    "DescriptionDataCoSupplyChain.csv",   # column descriptions
]

for name in FILES:
    target = OUT / name
    if target.exists():
        print(f"already have {name} ({target.stat().st_size/1e6:.1f} MB) — skipping")
        continue
    print(f"downloading {name} ...")
    urllib.request.urlretrieve(BASE + name, target)
    print(f"  saved {target.stat().st_size/1e6:.1f} MB")

print("Done. Now run:  python3 analysis_real.py")
