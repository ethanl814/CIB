"""Download and cache every raw dataset the research notebook uses.

Run from the project root:  .venv/bin/python src/fetch_data.py [--force]

Everything lands in data/raw/. The notebook only reads from that cache, so it
re-runs offline and everyone in the group sees the same numbers. Pass --force to
re-download (e.g. to pick up new months of data).
"""
from __future__ import annotations

import concurrent.futures as cf
import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
FORCE = "--force" in sys.argv
UA = {"User-Agent": "Mozilla/5.0 (research; CIB forex-drift-idea)"}

# --------------------------------------------------------------------------
# FRED series (no API key needed via the fredgraph CSV endpoint)
# --------------------------------------------------------------------------
FRED = {
    # Daily spot FX, Fed H.10 (noon NY buying rates)
    "DEXJPUS": "JPY per USD", "DEXINUS": "INR per USD", "DEXCHUS": "CNY per USD",
    "DEXKOUS": "KRW per USD", "DEXBZUS": "BRL per USD", "DEXMXUS": "MXN per USD",
    "DEXUSAL": "USD per AUD", "DEXUSEU": "USD per EUR", "DEXUSUK": "USD per GBP",
    "DEXCAUS": "CAD per USD", "DEXSZUS": "CHF per USD", "DEXNOUS": "NOK per USD",
    "DEXSDUS": "SEK per USD", "DEXUSNZ": "USD per NZD", "DEXSFUS": "ZAR per USD",
    "DEXDNUS": "DKK per USD", "DEXTHUS": "THB per USD", "DEXSIUS": "SGD per USD",
    "DEXTAUS": "TWD per USD",
    # 3-month interbank rates (OECD MEI), % p.a., monthly
    "IR3TIB01USM156N": "US 3M", "IR3TIB01JPM156N": "JP 3M", "IR3TIB01AUM156N": "AU 3M",
    "IR3TIB01GBM156N": "GB 3M", "IR3TIB01EZM156N": "EZ 3M", "IR3TIB01CAM156N": "CA 3M",
    "IR3TIB01CHM156N": "CH 3M", "IR3TIB01NOM156N": "NO 3M", "IR3TIB01SEM156N": "SE 3M",
    "IR3TIB01NZM156N": "NZ 3M", "IR3TIB01ZAM156N": "ZA 3M", "IR3TIB01MXM156N": "MX 3M",
    "IR3TIB01KRM156N": "KR 3M", "IR3TIB01CNM156N": "CN 3M", "IR3TIB01DKM156N": "DK 3M",
    # Overnight / call-money rates (fallbacks and EM where no 3M exists)
    "IRSTCI01USM156N": "US call", "IRSTCI01JPM156N": "JP call", "IRSTCI01INM156N": "IN call",
    "IRSTCI01BRM156N": "BR call", "IRSTCI01TRM156N": "TR call", "IRSTCI01IDM156N": "ID call",
    "IRSTCI01ZAM156N": "ZA call", "IRSTCI01MXM156N": "MX call", "IRSTCI01KRM156N": "KR call",
    "IRSTCI01CNM156N": "CN call", "IRSTCI01GBM156N": "GB call", "IRSTCI01EZM156N": "EZ call",
    "IRSTCI01CAM156N": "CA call", "IRSTCI01CHM156N": "CH call", "IRSTCI01NOM156N": "NO call",
    "IRSTCI01SEM156N": "SE call", "IRSTCI01NZM156N": "NZ call", "IRSTCI01AUM156N": "AU call",
    "IRSTCI01DKM156N": "DK call",
    # Policy-rate fallbacks for series the OECD stopped updating
    "ECBDFR": "ECB deposit facility rate (daily)", "IUDSOIA": "SONIA (daily)",
    "DFF": "Fed funds effective (daily)", "DTB3": "US 3M T-bill (daily)",
    # Long rates
    "IRLTLT01JPM156N": "JP 10Y", "IRLTLT01USM156N": "US 10Y", "INDIRLTLT01STM": "IN 10Y",
    "DGS10": "US 10Y daily", "DGS2": "US 2Y daily",
    # Monthly merchandise trade (OECD MEI, national currency): net, exports
    **{f"XTNTVA01{c}M664S": f"{c} trade balance" for c in
       "AU GB CA CH NO SE NZ ZA MX KR BR CN TR ID IN JP US DK DE EZ".split()},
    **{f"XTEXVA01{c}M664S": f"{c} exports" for c in
       "AU GB CA CH NO SE NZ ZA MX KR BR CN TR ID IN JP US DK DE EZ".split()},
    # FX reserves ex-gold (IMF IFS via FRED), USD millions
    **{f"TRESEG{c}M052N": f"{c} reserves ex gold" for c in
       "AU GB CA CH NO SE NZ ZA MX KR BR CN TR ID IN JP DK".split()},
    # BIS effective exchange rates (real broad, nominal broad)
    **{f"RB{c}BIS": f"{c} REER" for c in
       "JP IN CN US GB XM CH AU CA NZ NO SE KR BR MX ZA TR ID DK".split()},
    "NBJPBIS": "JP NEER", "NBINBIS": "IN NEER",
    # Risk regime
    "VIXCLS": "VIX", "DTWEXBGS": "Broad USD index",
    # CPI YoY (OECD)
    "CPALTT01JPM659N": "JP CPI yoy", "CPALTT01INM659N": "IN CPI yoy",
    "CPALTT01USM659N": "US CPI yoy", "CPIAUCSL": "US CPI index",
    "BOPGSTB": "US goods & services trade balance",
}


def fred_one(sid: str) -> tuple[str, str]:
    out = RAW / "fred" / f"{sid}.csv"
    out.parent.mkdir(exist_ok=True)
    if out.exists() and not FORCE:
        return sid, "cached"
    try:
        r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
                         timeout=60, headers=UA)
        if r.status_code != 200:
            return sid, f"HTTP {r.status_code}"
        out.write_text(r.text)
        return sid, "ok"
    except Exception as e:  # network hiccups shouldn't kill the whole run
        return sid, f"ERR {e!s:.60}"


def fetch_fred() -> None:
    with cf.ThreadPoolExecutor(10) as ex:
        res = list(ex.map(fred_one, FRED))
    bad = [(s, m) for s, m in res if m not in ("ok", "cached")]
    print(f"FRED: {len(res) - len(bad)}/{len(res)} series available")
    for s, m in bad:
        print("   missing", s, m)
    (RAW / "fred" / "_catalog.json").write_text(json.dumps(FRED, indent=1))


# --------------------------------------------------------------------------
# Yahoo Finance: EM crosses not on H.10, plus recent daily data
# --------------------------------------------------------------------------
YF = ["TRY=X", "IDR=X", "PHP=X", "JPY=X", "INR=X", "^VIX", "6J=F"]


def fetch_yf() -> None:
    import yfinance as yf
    out = RAW / "yahoo"
    out.mkdir(exist_ok=True)
    for t in YF:
        f = out / f"{t.replace('=', '_').replace('^', '')}.csv"
        if f.exists() and not FORCE:
            continue
        d = yf.download(t, period="max", progress=False, auto_adjust=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        d.to_csv(f)
    print("Yahoo: done")


# --------------------------------------------------------------------------
# Japan MoF: official daily intervention record (1991-) + monthly releases
# --------------------------------------------------------------------------
MOF = "https://www.mof.go.jp/english/policy/international_policy/reference/feio/"


def fetch_mof() -> None:
    f = RAW / "mof_intervention.csv"
    if not f.exists() or FORCE:
        r = requests.get(MOF + "foreign_exchange_intervention_operations.csv", timeout=60, headers=UA)
        f.write_bytes(r.content)
    # Monthly totals are published before the daily breakdown; keep the latest ones.
    import re
    idx = requests.get(MOF + "monthly/index.html", timeout=60, headers=UA).text
    rows = []
    for page in sorted(set(re.findall(r"(\d{8})e\.html", idx))):
        if page < "20240101":
            continue
        resp = requests.get(f"{MOF}monthly/{page}e.html", timeout=60, headers=UA)
        resp.encoding = "utf-8"  # server omits charset; default latin-1 mangles the yen sign
        html = resp.text
        txt = re.sub(r"<[^>]+>", " ", html).replace("&yen;", "¥")
        txt = re.sub(r"\s+", " ", txt)
        per = re.search(r"period from (\w+ \d+, \d{4}) through (\w+ \d+, \d{4})", txt)
        amt = re.search(r"¥\s*([\d,\.]+)\s*billion", txt)
        if per and amt:
            rows.append({"release": page, "start": per.group(1), "end": per.group(2),
                         "yen_bn": float(amt.group(1).replace(",", ""))})
    pd.DataFrame(rows).to_csv(RAW / "mof_monthly_totals.csv", index=False)
    print(f"MoF: daily file + {len(rows)} monthly releases")


# --------------------------------------------------------------------------
# CFTC Commitments of Traders (legacy, futures only): speculator positioning
# --------------------------------------------------------------------------
CFTC_CODES = {  # CFTC contract market codes for CME currency futures
    "097741": "JPY", "099741": "EUR", "096742": "GBP", "092741": "CHF",
    "090741": "CAD", "232741": "AUD", "112741": "NZD", "095741": "MXN",
    "102741": "BRL", "122741": "ZAR",
}


def fetch_cftc() -> None:
    f = RAW / "cftc_currency_cot.csv"
    if f.exists() and not FORCE:
        print("CFTC: cached")
        return
    frames = []
    for yr in range(2000, 2027):
        try:
            r = requests.get(f"https://www.cftc.gov/files/dea/history/deacot{yr}.zip",
                             timeout=120, headers=UA)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            d = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        except Exception as e:
            print("   CFTC", yr, "failed:", e)
            continue
        d.columns = [c.strip() for c in d.columns]
        code_col = "CFTC Contract Market Code"
        d[code_col] = d[code_col].astype(str).str.strip().str.zfill(6)
        d = d[d[code_col].isin(CFTC_CODES)]
        date_col = [c for c in d.columns if c.startswith("As of Date in Form YYYY-MM-DD")][0]
        frames.append(pd.DataFrame({
            "date": pd.to_datetime(d[date_col]),
            "ccy": d[code_col].map(CFTC_CODES),
            "oi": d["Open Interest (All)"],
            "nc_long": d["Noncommercial Positions-Long (All)"],
            "nc_short": d["Noncommercial Positions-Short (All)"],
        }))
    out = pd.concat(frames).sort_values(["ccy", "date"]).drop_duplicates(["ccy", "date"])
    out.to_csv(f, index=False)
    print(f"CFTC: {len(out)} weekly rows, {out.date.min().date()} -> {out.date.max().date()}")


# --------------------------------------------------------------------------
# World Bank: annual current account (% GDP) - distinguishes "trade deficit"
# from "external deficit" (Japan: trade deficit but big income surplus)
# --------------------------------------------------------------------------
WB_COUNTRIES = "JPN;IND;USA;AUS;GBR;CAN;CHE;NOR;SWE;NZL;ZAF;MEX;KOR;BRA;CHN;TUR;IDN;DNK;EMU;THA;SGP"
WB_IND = {"BN.CAB.XOKA.GD.ZS": "current_account_pct_gdp",
          "NE.RSB.GNFS.ZS": "net_exports_pct_gdp",
          "FI.RES.TOTL.MO": "reserves_months_imports"}


def fetch_wb() -> None:
    f = RAW / "worldbank_annual.csv"
    if f.exists() and not FORCE:
        print("World Bank: cached")
        return
    rows = []
    for ind, name in WB_IND.items():
        url = (f"https://api.worldbank.org/v2/country/{WB_COUNTRIES}/indicator/{ind}"
               f"?format=json&per_page=20000&date=1990:2026")
        js = requests.get(url, timeout=120, headers=UA).json()
        for rec in js[1] or []:
            if rec["value"] is not None:
                rows.append({"iso3": rec["countryiso3code"], "year": int(rec["date"]),
                             "indicator": name, "value": rec["value"]})
    pd.DataFrame(rows).to_csv(f, index=False)
    print(f"World Bank: {len(rows)} rows")


if __name__ == "__main__":
    fetch_fred()
    fetch_yf()
    fetch_mof()
    fetch_wb()
    fetch_cftc()
