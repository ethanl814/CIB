"""Shared data loading, panel construction, stats and plotting helpers.

The notebook imports this so its cells stay short and readable. Nothing here
downloads data - run src/fetch_data.py first to populate data/raw/.

Conventions used everywhere
---------------------------
* Spot `S` is always expressed as FOREIGN CURRENCY PER 1 USD (e.g. USDJPY=157).
  So S going UP means the foreign currency WEAKENED.
* "Carry" = foreign short rate minus US short rate (annualised, decimal).
* Excess return of a US investor who is LONG the foreign currency (funded in USD)
  over month t -> t+1:  rx = carry_t/12 - ln(S_{t+1}/S_t)
  This is the classic carry-trade return; UIP says its expected value is zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# Plot style: one validated categorical palette, thin marks, recessive grid.
# Colours follow the entity (JPY is always blue, INR always orange, ...).
# --------------------------------------------------------------------------
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = PALETTE
GRAY = "#8a8985"
LIGHTGRAY = "#d9d8d4"
INK = "#0b0b0b"
INK2 = "#52514e"
SURFACE = "#fcfcfb"
POS, NEG = BLUE, RED  # diverging poles (blue = good for the long-foreign-ccy trade)

CCY_COLOR = {"JPY": BLUE, "INR": ORANGE, "USD": GRAY}


def set_style() -> None:
    mpl.rcParams.update({
        "figure.figsize": (11, 4.6), "figure.dpi": 110, "savefig.dpi": 150,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": LIGHTGRAY, "axes.linewidth": 0.8, "axes.grid": True,
        "grid.color": "#ecebe8", "grid.linewidth": 0.7, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 10, "axes.labelcolor": INK2, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "lines.linewidth": 1.6, "legend.frameon": False, "legend.fontsize": 9,
        "axes.prop_cycle": mpl.cycler(color=PALETTE), "font.size": 10,
    })


def save(fig: plt.Figure, name: str) -> None:
    """Save every figure to figures/ so slides can grab a PNG directly."""
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")


def source_note(ax, text: str) -> None:
    ax.annotate(text, xy=(0, -0.13), xycoords="axes fraction", fontsize=7.5,
                color=GRAY, ha="left", va="top")


# --------------------------------------------------------------------------
# Raw loaders
# --------------------------------------------------------------------------
def fred(sid: str) -> pd.Series:
    f = RAW / "fred" / f"{sid}.csv"
    if not f.exists():
        return pd.Series(dtype=float, name=sid)
    d = pd.read_csv(f)
    d.columns = ["date", sid]
    d["date"] = pd.to_datetime(d["date"])
    s = pd.to_numeric(d[sid], errors="coerce")
    return pd.Series(s.values, index=d["date"], name=sid).dropna()


def yahoo(ticker: str) -> pd.Series:
    f = RAW / "yahoo" / f"{ticker.replace('=', '_').replace('^', '')}.csv"
    d = pd.read_csv(f, index_col=0, parse_dates=True)
    d = d[pd.to_numeric(d["Close"], errors="coerce").notna()]
    s = d["Close"].astype(float)
    s.index = pd.to_datetime(s.index)
    return s.rename(ticker)


def clean_spikes(s: pd.Series, thresh: float = 0.15) -> pd.Series:
    """Drop one-day prints that jump > thresh and immediately reverse (bad ticks
    are common in Yahoo EM FX history)."""
    r = np.log(s).diff()
    bad = (r.abs() > thresh) & (r.shift(-1).abs() > thresh) & (np.sign(r) != np.sign(r.shift(-1)))
    return s[~bad]


# --------------------------------------------------------------------------
# Currency universe
# --------------------------------------------------------------------------
@dataclass
class Ccy:
    code: str
    fx: str              # FRED id or "yahoo:TICKER"
    usd_per: bool        # True if the raw quote is USD per foreign unit (EUR, GBP, AUD, NZD)
    rates: list          # short-rate series in priority order
    trade: str | None    # OECD MEI country code for trade data
    reserves: str | None
    reer: str | None
    iso3: str
    group: str           # "G10" or "EM"
    regime: str          # rough FX regime label (for context only)


UNIVERSE = [
    Ccy("JPY", "DEXJPUS", False, ["IR3TIB01JPM156N", "IRSTCI01JPM156N"], "JP", "JP", "RBJPBIS", "JPN", "G10", "Free float, occasional intervention"),
    Ccy("EUR", "DEXUSEU", True, ["IR3TIB01EZM156N", "IRSTCI01EZM156N", "ECBDFR"], "EZ", None, "RBXMBIS", "EMU", "G10", "Free float"),
    Ccy("GBP", "DEXUSUK", True, ["IR3TIB01GBM156N", "IUDSOIA", "IRSTCI01GBM156N"], "GB", "GB", "RBGBBIS", "GBR", "G10", "Free float"),
    Ccy("CHF", "DEXSZUS", False, ["IR3TIB01CHM156N", "IRSTCI01CHM156N"], "CH", None, "RBCHBIS", "CHE", "G10", "Float; heavy intervention 2011-22"),
    Ccy("CAD", "DEXCAUS", False, ["IR3TIB01CAM156N", "IRSTCI01CAM156N"], "CA", "CA", "RBCABIS", "CAN", "G10", "Free float"),
    Ccy("AUD", "DEXUSAL", True, ["IR3TIB01AUM156N", "IRSTCI01AUM156N"], "AU", "AU", "RBAUBIS", "AUS", "G10", "Free float"),
    Ccy("NZD", "DEXUSNZ", True, ["IR3TIB01NZM156N", "IRSTCI01NZM156N"], "NZ", None, "RBNZBIS", "NZL", "G10", "Free float"),
    Ccy("NOK", "DEXNOUS", False, ["IR3TIB01NOM156N", "IRSTCI01NOM156N"], "NO", None, "RBNOBIS", "NOR", "G10", "Free float"),
    Ccy("SEK", "DEXSDUS", False, ["IR3TIB01SEM156N", "IRSTCI01SEM156N"], "SE", None, "RBSEBIS", "SWE", "G10", "Free float"),
    Ccy("INR", "DEXINUS", False, ["IRSTCI01INM156N"], "IN", "IN", "RBINBIS", "IND", "EM", "Managed float (heavy smoothing)"),
    Ccy("CNY", "DEXCHUS", False, ["IR3TIB01CNM156N", "IRSTCI01CNM156N"], "CN", "CN", "RBCNBIS", "CHN", "EM", "Crawl/managed, capital controls"),
    Ccy("KRW", "DEXKOUS", False, ["IR3TIB01KRM156N", "IRSTCI01KRM156N"], "KR", "KR", "RBKRBIS", "KOR", "EM", "Managed float"),
    Ccy("BRL", "DEXBZUS", False, ["IRSTCI01BRM156N"], "BR", "BR", "RBBRBIS", "BRA", "EM", "Free float"),
    Ccy("MXN", "DEXMXUS", False, ["IR3TIB01MXM156N", "IRSTCI01MXM156N"], "MX", "MX", "RBMXBIS", "MEX", "EM", "Free float"),
    Ccy("ZAR", "DEXSFUS", False, ["IR3TIB01ZAM156N", "IRSTCI01ZAM156N"], "ZA", "ZA", "RBZABIS", "ZAF", "EM", "Free float"),
    Ccy("TRY", "yahoo:TRY=X", False, ["IRSTCI01TRM156N"], "TR", "TR", "RBTRBIS", "TUR", "EM", "Managed, repeated crises"),
    Ccy("IDR", "yahoo:IDR=X", False, ["IRSTCI01IDM156N"], "ID", "ID", "RBIDBIS", "IDN", "EM", "Managed float"),
]
U = {c.code: c for c in UNIVERSE}
US_RATE = ["IR3TIB01USM156N", "IRSTCI01USM156N"]


def spot_daily(code: str) -> pd.Series:
    """Daily spot as foreign-per-USD."""
    c = U[code]
    if c.fx.startswith("yahoo:"):
        s = clean_spikes(yahoo(c.fx.split(":")[1]))
    else:
        s = fred(c.fx)
    s = 1.0 / s if c.usd_per else s
    return s.rename(code)


def monthly_last(s: pd.Series) -> pd.Series:
    return s.resample("ME").last()


def monthly_mean(s: pd.Series) -> pd.Series:
    return s.resample("ME").mean()


def short_rate(ids: list) -> pd.Series:
    """Combine rate series in priority order at monthly frequency (% p.a.)."""
    out = None
    for sid in ids:
        s = monthly_mean(fred(sid))
        out = s if out is None else out.combine_first(s)
    return out.ffill(limit=3)


def trade_ratio(cc: str, window: int = 12) -> pd.Series:
    """Rolling-12m merchandise trade balance / (exports + imports), in %.
    Unit-free, so comparable across countries. +ve = net exporter."""
    tb, ex = fred(f"XTNTVA01{cc}M664S"), fred(f"XTEXVA01{cc}M664S")
    tb, ex = monthly_last(tb), monthly_last(ex)
    im = ex - tb
    return 100 * tb.rolling(window).sum() / (ex + im).rolling(window).sum()


def wb_annual(indicator: str) -> pd.DataFrame:
    d = pd.read_csv(RAW / "worldbank_annual.csv")
    return d[d.indicator == indicator].pivot(index="year", columns="iso3", values="value")


def build_panel(start: str = "1999-01-01", trade_lag: int = 2, reserve_lag: int = 1) -> dict:
    """Monthly panel of every signal, aligned so row t only uses info available at t.

    trade_lag / reserve_lag: months of publication delay we impose so there is
    no look-ahead (trade data typically publishes 1-2 months after the month).
    """
    us = short_rate(US_RATE)
    spot, rate, tb, res, reer, ca = {}, {}, {}, {}, {}, {}
    ca_wb = wb_annual("current_account_pct_gdp")
    end = monthly_last(spot_daily("JPY")).index.max()

    def lagged(s: pd.Series, lag: int) -> pd.Series:
        # Extend to the panel's last month BEFORE shifting, so the newest print
        # lands `lag` months later instead of falling off the end of the series.
        s = s.dropna()
        return s.reindex(pd.date_range(s.index[0], max(end, s.index[-1]), freq="ME")).shift(lag)

    for c in UNIVERSE:
        spot[c.code] = monthly_last(spot_daily(c.code))
        rate[c.code] = short_rate(c.rates)
        if c.trade:
            tb[c.code] = lagged(trade_ratio(c.trade), trade_lag)
        if c.reserves:
            res[c.code] = lagged(monthly_last(fred(f"TRESEG{c.reserves}M052N")), reserve_lag)
        if c.reer:
            reer[c.code] = lagged(monthly_last(fred(c.reer)), 1)
        if c.iso3 in ca_wb:
            # Annual CA % GDP for year y is treated as known from April of y+1.
            a = ca_wb[c.iso3].dropna()
            idx = pd.to_datetime([f"{y + 1}-04-30" for y in a.index])
            ca[c.code] = pd.Series(a.values, index=idx)
    idx = pd.date_range(start, spot["JPY"].index.max(), freq="ME")
    P = {
        "spot": pd.DataFrame(spot).reindex(idx),
        "rate": pd.DataFrame(rate).reindex(idx).ffill(limit=3),   # latest month's print often lags
        "us_rate": us.reindex(idx).ffill(limit=3),
        "trade": pd.DataFrame(tb).reindex(idx).ffill(limit=3),
        "reserves": pd.DataFrame(res).reindex(idx),
        "reer": pd.DataFrame(reer).reindex(idx),
        "ca": pd.DataFrame(ca).reindex(pd.date_range("1990-01-31", idx[-1], freq="ME")).ffill().reindex(idx),
    }
    P["carry"] = P["rate"].sub(P["us_rate"], axis=0) / 100.0            # decimal p.a., known at t
    P["ds"] = np.log(P["spot"]).diff()                                    # +ve = foreign ccy weakened
    P["rx"] = P["carry"].shift(1) / 12.0 - P["ds"]                        # carry-trade excess return in month t
    P["spot_ret"] = -P["ds"]                                              # FX-only return of long foreign ccy
    return P


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------
def perf(r: pd.Series, freq: int = 12) -> dict:
    """Summary stats for a periodic (log) return series."""
    r = r.dropna()
    if len(r) < 6:
        return {}
    eq = r.cumsum()
    dd = eq - eq.cummax()
    return {
        "Ann. return %": 100 * r.mean() * freq,
        "Ann. vol %": 100 * r.std() * np.sqrt(freq),
        "Sharpe": r.mean() / r.std() * np.sqrt(freq) if r.std() > 0 else np.nan,
        "Skew": r.skew(),
        "Worst month %": 100 * r.min(),
        "Max drawdown %": 100 * (np.exp(dd.min()) - 1),
        "Hit rate %": 100 * (r > 0).mean(),
        "Months": len(r),
    }


def perf_table(d: dict | pd.DataFrame, freq: int = 12) -> pd.DataFrame:
    if isinstance(d, pd.DataFrame):
        d = {c: d[c] for c in d}
    return pd.DataFrame({k: perf(v, freq) for k, v in d.items()}).T


def nw_ols(y: pd.Series, X: pd.DataFrame | pd.Series, lags: int | None = None):
    """OLS with Newey-West (HAC) standard errors - needed because overlapping
    or autocorrelated FX returns make plain OLS t-stats far too optimistic."""
    import statsmodels.api as sm
    df = pd.concat([y, X], axis=1).dropna()
    yy, XX = df.iloc[:, 0], sm.add_constant(df.iloc[:, 1:])
    if lags is None:
        lags = int(4 * (len(df) / 100) ** (2 / 9))
    return sm.OLS(yy, XX).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def intervention_table() -> pd.DataFrame:
    """Parse Japan MoF's official daily intervention CSV (Shift-JIS, mixed JP/EN)."""
    raw = pd.read_csv(RAW / "mof_intervention.csv", encoding="shift_jis", header=None,
                      skiprows=0, dtype=str, on_bad_lines="skip", engine="python")
    rows = []
    year = month = None
    for _, r in raw.iterrows():
        y, mon, day, amt, desc = r[3], r[4], r[5], r[6], r[8]
        if isinstance(y, str) and y.strip().isdigit() and len(y.strip()) == 4:
            year = int(y)
        if isinstance(mon, str) and mon.strip()[:3].isalpha():
            month = mon.strip()[:3]          # continuation rows leave month blank
        if not (isinstance(day, str) and day.strip().isdigit()):
            continue                         # quarter-total and note rows
        if year is None or month is None or not isinstance(amt, str):
            continue
        try:
            d = pd.Timestamp(f"{year}-{month}-{int(day.strip())}")
        except ValueError:
            continue
        a = float(amt.replace(",", "")) * 1e8 / 1e12  # 100m yen units -> trillions
        desc = (desc or "").strip().lower()
        if "japanese yen (bought)" in desc:
            direction = "buy JPY"
        elif "japanese yen (sold)" in desc:
            direction = "sell JPY"
        else:
            direction = "non-yen"            # e.g. 1991 USD/DEM, 2011 EUR operations
        rows.append({"date": d, "yen_tn": a, "direction": direction, "pair": desc})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# Operations reported by MoF/press but not yet in the daily CSV (MoF publishes
# daily detail with a ~1 quarter lag). Amounts are estimates, flagged as such.
REPORTED_2026 = pd.DataFrame([
    {"date": pd.Timestamp("2026-07-30"), "yen_tn": 7.0, "direction": "buy JPY",
     "pair": "reported (BoJ account estimates; MoF monthly total Jul 30-Aug 26 = ¥15.4tn)"},
    {"date": pd.Timestamp("2026-07-31"), "yen_tn": 8.4, "direction": "buy JPY",
     "pair": "reported joint US-Japan operation (US Treasury sold EUR for JPY)"},
])
