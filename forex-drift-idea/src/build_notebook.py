"""Assemble research.ipynb from the cell list below, then execute it.

Keeping the notebook as a script makes it diff-able and rebuildable:
    .venv/bin/python src/build_notebook.py          # build + execute
Edit prose in src/notebook_text.py (interpretation lives there).
"""
from pathlib import Path

import nbformat as nbf

from notebook_text import TEXT

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(key_or_text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(TEXT.get(key_or_text, key_or_text).strip("\n")))


def code(src: str) -> None:
    cells.append(nbf.v4.new_code_cell(src.strip("\n")))


# =============================================================================
md("title")
md("tldr")
md("final")
code(r'''
# Self-contained so this summary runs on its own; uses the same engine as section 6.
import sys, warnings
sys.path.insert(0, "src"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import fxlib as fx
fx.set_style(); pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

P0 = fx.build_panel(); S0 = fx.proposal_signals(P0)
FINAL = {
    "1. CORE: carry + trade-balance basket (17 ccy)": fx.run_basket(P0, S0["core"])[0],
    "1b. Core, G10-only (retail / CME futures)":      fx.run_basket(P0, S0["core_g10"])[0],
    "    benchmark: carry only":                        fx.run_basket(P0, S0["carry_only"])[0],
    "2. SATELLITE: short JPY, paused after MoF":       fx.run_single(P0, "JPY", S0["jpy_rule"], -1),
    "    benchmark: always short JPY":                  fx.run_single(P0, "JPY", S0["jpy_always"], -1),
    "3. WATCH: long INR while RBI reserves rising":    fx.run_single(P0, "INR", S0["inr_rule"], +1),
    "    benchmark: always long INR":                   fx.run_single(P0, "INR", S0["inr_always"], +1),
}
summary = fx.perf_table(FINAL)[["Ann. return %", "Ann. vol %", "Sharpe", "Max drawdown %", "Worst month %"]]
summary["Sharpe 2000-12"] = [fx.perf(r[:"2012"])["Sharpe"] for r in FINAL.values()]
summary["Sharpe 2013-26"] = [fx.perf(r["2013":])["Sharpe"] for r in FINAL.values()]
summary["Sharpe last 5y"] = [fx.perf(r[r.index[-1] - pd.DateOffset(years=5):])["Sharpe"] for r in FINAL.values()]
summary["% months invested"] = [100 * (r != 0).mean() for r in FINAL.values()]
print(f"All figures NET of costs, monthly, Jan 2000 - {P0['spot'].index[-1]:%b %Y}. Unlevered.")
summary
''')
code(r'''
k = list(FINAL)
fig, ax = plt.subplots(2, 2, figsize=(13, 8.2))
def cum(r): return 100 * (np.exp(r.cumsum()) - 1)
def dd(r):  e = r.cumsum(); return 100 * (np.exp(e - e.cummax()) - 1)
def endlab(a, s):
    a.annotate(f"{s.iloc[-1]:+.0f}%", (s.index[-1], s.iloc[-1]), xytext=(3, 0), textcoords="offset points", fontsize=8.5, color=fx.INK2, va="center")

for key, col, lw, lab in [(k[0], fx.INK, 2.2, "Core: carry + trade balance"), (k[2], fx.BLUE, 1.3, "Carry only"), (k[1], fx.AQUA, 1.3, "Core, G10-only (retail)")]:
    s = cum(FINAL[key]); ax[0, 0].plot(s.index, s, color=col, lw=lw, label=lab); endlab(ax[0, 0], s)
    d = dd(FINAL[key]); ax[0, 1].plot(d.index, d, color=col, lw=lw, label=lab)
ax[0, 0].set_title("1. Core trade: cumulative return"); ax[0, 0].set_ylabel("%"); ax[0, 0].legend(loc="upper left")
ax[0, 1].set_title("1. Core trade: drawdowns (smaller is better)"); ax[0, 1].set_ylabel("%"); ax[0, 1].legend(loc="lower left")

for a, rule, bench, col, title in [(ax[1, 0], k[3], k[4], fx.BLUE, "2. Short JPY: rule vs. always short"),
                                   (ax[1, 1], k[5], k[6], fx.ORANGE, "3. Long INR: rule vs. always long")]:
    sb, sr = cum(FINAL[bench]), cum(FINAL[rule])
    a.plot(sb.index, sb, color=fx.GRAY, lw=1.2, label="Always in"); endlab(a, sb)
    a.plot(sr.index, sr, color=col, lw=2.0, label="Rule"); endlab(a, sr)
    a.axhline(0, color=fx.GRAY, lw=0.8); a.set_title(title); a.set_ylabel("%"); a.legend(loc="upper left")
fig.suptitle("Final proposal: backtests net of costs, Jan 2000 - Sep 2026 (unlevered)", x=0.01, ha="left", fontsize=13.5, fontweight="bold")
fx.source_note(ax[1, 0], "Costs: G10 4bp / EM 12bp per trade + monthly forward roll. Signals use only data published at the time.")
fig.tight_layout(); fx.save(fig, "00_final_proposal_backtests"); plt.show()
''')
code(r'''
# What each trade says TODAY (latest published data)
w = S0["core"].iloc[-1]; w = w[w.abs() > 1e-9].sort_values()
pos = pd.DataFrame({"Core weight": w, "Side": np.where(w > 0, "LONG", "SHORT"),
                    "Rate gap vs USD %": 100 * P0["carry"].ffill().iloc[-1].reindex(w.index),
                    "Trade bal % of trade": P0["trade"].ffill().iloc[-1].reindex(w.index)})
res = P0["reserves"]["INR"].dropna()
gap_now = -100 * P0["carry"]["JPY"].ffill().iloc[-1]
last_buy = fx.yen_buying_months(P0["spot"].index); last_buy = last_buy[last_buy > 0].index[-1]
print(f"CORE basket positions for next month (as of {P0['spot'].index[-1]:%b %Y}):"); display(pos.round(2))
print(f"SATELLITE (short JPY): US-Japan gap = {gap_now:.2f}pp (> 2 needed). Last MoF yen-buying month: {last_buy:%b %Y} "
      f"-> {'PAUSED until ' + (last_buy + pd.offsets.MonthEnd(3)).strftime('%b %Y') + ' ends' if P0['spot'].index[-1] <= last_buy + pd.offsets.MonthEnd(3) else 'ACTIVE'}")
chg = 100 * np.log(res.iloc[-1] / res.iloc[-4])
print(f"WATCH (long INR): RBI reserves (latest reading, {(res.index[-1] - pd.offsets.MonthEnd(1)):%b %Y} data) 3m change = {chg:+.1f}% -> {'ON' if chg > 0 else 'OFF'} "
      "(but the rise is mostly FCNR(B) swap inflows - borrowed dollars, treat as weak)")
''')
md("final_after")
md("toc")
md("neutrality")

# ---------------------------------------------------------------- 1. setup
md("s1")
code(r'''
import sys, warnings
sys.path.insert(0, "src"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import fxlib as fx
from fxlib import BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED, GRAY, LIGHTGRAY, INK, INK2
fx.set_style()
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
pd.set_option("display.max_columns", 30); pd.set_option("display.width", 220)
DIVERGING = LinearSegmentedColormap.from_list("div", [RED, "#f0efec", BLUE])

P = fx.build_panel()                     # monthly panel, look-ahead-safe lags applied
spot, carry, rx, ds, tb, ca = (P[k] for k in ["spot", "carry", "rx", "ds", "trade", "ca"])
jd = fx.spot_daily("JPY").dropna()        # daily USDJPY
ind = fx.spot_daily("INR").dropna()       # daily USDINR
print(f"Panel: {spot.shape[1]} currencies, {spot.index[0]:%b %Y} to {spot.index[-1]:%b %Y}  "
      f"| daily USDJPY to {jd.index[-1]:%d %b %Y}, USDINR to {ind.index[-1]:%d %b %Y}")
''')
md("s1_sources")
code(r'''
def last(s):
    i = s.last_valid_index(); return "-" if i is None else f"{i:%Y-%m}"
coverage = pd.DataFrame({
    "Group": {c.code: c.group for c in fx.UNIVERSE},
    "FX regime (context only)": {c.code: c.regime for c in fx.UNIVERSE},
    "Spot from": {c: f"{spot[c].first_valid_index():%Y-%m}" for c in spot},
    "Short rate used": {c.code: c.rates[0] for c in fx.UNIVERSE},
    "Rates through": {c: last(P["rate"][c]) for c in spot},
    "Trade data through*": {c: last(tb[c]) for c in spot},
    "FX reserves data": {c.code: "yes" if c.reserves else "-" for c in fx.UNIVERSE},
})
coverage
''')
md("s1_conventions")

# ---------------------------------------------------------------- 2. primer
md("s2")
code(r'''
def uip_path(code, start):
    s = spot[code][start:].dropna()
    c = carry[code].reindex(s.index).ffill()
    implied = s.iloc[0] * np.exp((c.shift(1).fillna(0) / 12).cumsum())
    return s, implied

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
for ax, code in zip(axes, ["JPY", "INR"]):
    s, imp = uip_path(code, "2012-01-31")
    col = fx.CCY_COLOR[code]
    ax.plot(s.index, s, color=col, label=f"Actual USD{code}")
    ax.plot(imp.index, imp, color=GRAY, lw=1.4, ls="--", label="Path implied by UIP (interest-rate gap)")
    ax.fill_between(s.index, s, imp, color=col, alpha=0.08)
    ax.annotate(f"{s.iloc[-1]:.1f}", (s.index[-1], s.iloc[-1]), xytext=(4, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    ax.annotate(f"{imp.iloc[-1]:.1f}", (imp.index[-1], imp.iloc[-1]), xytext=(4, 0), textcoords="offset points", color=GRAY, fontsize=9, va="center")
    gap = 100 * np.log(s.iloc[-1] / imp.iloc[-1])
    ax.set_title(f"USD{code}: actual vs. UIP-implied path since Jan 2012  (gap {gap:+.0f}%)")
    ax.set_ylabel(f"{code} per USD"); ax.legend(loc="upper left")
fx.source_note(axes[0], "Source: Fed H.10 spot (FRED); OECD 3M interbank / call-money rates. UIP path compounds the monthly rate gap from Jan 2012.")
fig.tight_layout(); fx.save(fig, "02_uip_vs_actual_jpy_inr"); plt.show()
''')
md("s2_read")

# ---------------------------------------------------------------- 3. Japan
md("s3")
md("s3_1")
code(r'''
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.5, 6.8), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
a1.plot(jd["1995":], color=BLUE, lw=1.0)
a1.set_title("USDJPY (yen per dollar); up = weaker yen"); a1.set_ylabel("JPY per USD")
for d, txt in [("1998-08-11", "1998: 147\n(LTCM / carry unwind)"), ("2011-10-31", "2011: record-strong yen\n(75.3)"),
               ("2024-07-10", "2024: 161.9"), ("2026-07-29", "2026: ~164")]:
    t = jd.index[jd.index.searchsorted(pd.Timestamp(d))]
    a1.annotate(txt, (t, jd[t]), xytext=(0, 14), textcoords="offset points", ha="center", fontsize=8, color=INK2)
us, jp = P["us_rate"], P["rate"]["JPY"]
a2.plot(us["1995":].index, us["1995":], color=GRAY, label="US 3M rate")
a2.plot(jp["1995":].index, jp["1995":], color=BLUE, label="Japan 3M / call rate")
a2.fill_between(us["1995":].index, jp["1995":], us["1995":], color=BLUE, alpha=0.08, label="Gap (US minus Japan) = what a short-yen carry trade earns")
a2.set_ylabel("% per year"); a2.legend(loc="upper right", ncol=1); a2.set_title("Short-term interest rates")
fx.source_note(a2, "Source: FRED DEXJPUS (daily), IR3TIB01USM156N, IR3TIB01JPM156N / IRSTCI01JPM156N.")
fig.tight_layout(); fx.save(fig, "03a_usdjpy_and_rates"); plt.show()

g = (us - jp).dropna(); s12 = 100 * np.log(spot["JPY"]).diff(12)
print("Correlation of 12m change in USDJPY with 12m change in the US-Japan rate gap:",
      f"{s12.corr(g.diff(12)):.2f}  (1999-2026, overlapping monthly obs)")
''')
md("s3_1_read")

md("s3_2")
code(r'''
iv = fx.intervention_table()
yen_ops = pd.concat([iv[iv.direction != "non-yen"], fx.REPORTED_2026]).sort_values("date").reset_index(drop=True)
yen_ops["signed_tn"] = np.where(yen_ops.direction == "buy JPY", 1, -1) * yen_ops.yen_tn
ops_m = yen_ops.set_index("date").signed_tn.resample("ME").sum()
jp_tb_raw = fx.trade_ratio("JP")                          # unlagged, for description
jp_ca = fx.wb_annual("current_account_pct_gdp")["JPN"].dropna()

fig, axes = plt.subplots(3, 1, figsize=(11.5, 8.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.5, 1.5]})
axes[0].plot(jd["1991":], color=BLUE, lw=0.9); axes[0].set_ylabel("JPY per USD")
axes[0].set_title("USDJPY, Japan's trade balance, and every official MoF intervention (1991-2026)")
x = jp_tb_raw["1991":]
axes[1].plot(x.index, x, color=INK2, lw=1.2, label="Merchandise trade balance, % of total trade (12m)")
axes[1].fill_between(x.index, 0, x, where=x >= 0, color=BLUE, alpha=0.25, label="Net exporter")
axes[1].fill_between(x.index, 0, x, where=x < 0, color=RED, alpha=0.25, label="Net importer")
cai = pd.Series(jp_ca.values, index=pd.to_datetime([f"{y}-07-01" for y in jp_ca.index]))
axes[1].plot(cai["1991":].index, cai["1991":], color=VIOLET, lw=1.4, drawstyle="steps-mid", label="Current account, % GDP (annual)")
axes[1].axhline(0, color=GRAY, lw=0.8); axes[1].set_ylabel("%"); axes[1].legend(loc="lower left", ncol=2, fontsize=8)
o = ops_m["1991":]
axes[2].bar(o.index, o.clip(lower=0), width=40, color=BLUE, label="MoF BUYS yen (fights yen weakness)")
axes[2].bar(o.index, o.clip(upper=0), width=40, color=RED, label="MoF SELLS yen (fights yen strength)")
axes[2].axhline(0, color=GRAY, lw=0.8); axes[2].set_ylabel("¥ trillion / month"); axes[2].legend(loc="lower left", fontsize=8)
fx.source_note(axes[2], "Source: Japan MoF intervention record (daily, 1991-Jun 2026); Jul-2026 joint operation from MoF monthly total and press reports; OECD MEI trade; World Bank current account.")
fig.tight_layout(); fx.save(fig, "03b_japan_trade_vs_intervention_direction"); plt.show()

yr = yen_ops.assign(year=yen_ops.date.dt.year).groupby("year").agg(
    days=("yen_tn", "size"),
    yen_bought_tn=("signed_tn", lambda v: v[v > 0].sum()),
    yen_sold_tn=("signed_tn", lambda v: -v[v < 0].sum()))
yr["trade bal % (yr avg)"] = jp_tb_raw.groupby(jp_tb_raw.index.year).mean().reindex(yr.index)
yr["current acct % GDP"] = jp_ca.reindex(yr.index)
yr
''')
md("s3_2_read")

md("s3_3")
code(r'''
# Cluster operations into episodes (a new episode starts after a 45-day gap or a direction flip)
ops = yen_ops.copy()
ops["episode"] = ((ops.date.diff().dt.days > 45) | (ops.direction != ops.direction.shift())).cumsum()
ep = ops.groupby("episode").agg(start=("date", "min"), end=("date", "max"), direction=("direction", "first"),
                                days=("date", "size"), size_tn=("yen_tn", "sum")).reset_index(drop=True)

def ev_path(t0, pre=20, post=120):
    i = jd.index.searchsorted(t0); lo = max(0, i - pre)
    seg = jd.iloc[lo:i + post + 1]
    return pd.Series(100 * np.log(seg.values / jd.iloc[i - 1]), index=np.arange(len(seg)) - (i - lo))

gap_m = fx.short_rate(fx.US_RATE) - fx.short_rate(fx.U["JPY"].rates)   # full history back to 1985 (panel starts 1999)
rows, paths = [], {}
for _, e in ep.iterrows():
    # +ve = move in the direction MoF wanted: USDJPY down when buying yen, up when selling yen
    raw = ev_path(e.start); intended = -raw if e.direction == "buy JPY" else raw
    paths[e.start] = intended
    m0 = gap_m.index.searchsorted(e.start) - 1
    dgap = gap_m.iloc[m0 + 3] - gap_m.iloc[m0] if 0 <= m0 and m0 + 3 < len(gap_m) and not np.isnan(gap_m.iloc[m0 + 3]) else np.nan
    rows.append({"start": e.start.date(), "direction": e.direction, "days": e.days, "size ¥tn": e.size_tn,
                 "USDJPY day before": jd.iloc[jd.index.searchsorted(e.start) - 1],
                 **{f"+{h}d %": intended.get(h, np.nan) for h in (1, 5, 20, 60, 120)},
                 "policy tailwind (pp, next 3m)": (-dgap if e.direction == "buy JPY" else dgap)})
evt = pd.DataFrame(rows)
print("Event study: % move in the direction the MoF WANTED (positive = intervention 'worked'), measured from the close before day 0")
evt
''')
code(r'''
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), sharey=True)
for ax, dirn, col, title in [(axes[0], "sell JPY", RED, "Selling yen (1991-2011, Japan a net exporter)"),
                              (axes[1], "buy JPY", BLUE, "Buying yen (1992-98, 2022-26)")]:
    starts = ep[ep.direction == dirn].start
    mat = pd.DataFrame({s: paths[s] for s in starts})
    for s in starts:
        recent = s.year >= 2022
        ax.plot(mat.index, mat[s], color=col if recent else LIGHTGRAY, lw=1.3 if recent else 0.8, alpha=1 if recent else 0.9)
        if recent:
            v = mat[s].dropna(); ax.annotate(f"{s:%b %Y}", (v.index[-1], v.iloc[-1]), xytext=(3, 0), textcoords="offset points", fontsize=7.5, color=INK2, va="center")
    ax.plot(mat.index, mat.median(axis=1), color=INK, lw=2.2, label=f"Median of {len(starts)} episodes")
    ax.axhline(0, color=GRAY, lw=0.8); ax.axvline(0, color=GRAY, lw=0.8)
    ax.set_title(title); ax.set_xlabel("Trading days from first intervention day"); ax.legend(loc="upper left")
axes[0].set_ylabel("% move in the direction MoF wanted")
fx.source_note(axes[0], "Gray = individual older episodes; colored = 2022+ episodes; black = median. Source: MoF, FRED DEXJPUS.")
fig.tight_layout(); fx.save(fig, "03c_intervention_event_study"); plt.show()

e2 = evt.dropna(subset=["+60d %", "policy tailwind (pp, next 3m)"])
fig, ax = plt.subplots(figsize=(7.5, 4.8))
for _, r in e2.iterrows():
    c = BLUE if r.direction == "buy JPY" else RED
    ax.scatter(r["policy tailwind (pp, next 3m)"], r["+60d %"], s=40, color=c, edgecolor="white", linewidth=1.5, zorder=3)
    if r.start.year >= 2022 or abs(r["+60d %"]) > 6 or abs(r["policy tailwind (pp, next 3m)"]) > 0.4:
        ax.annotate(f"{r.start:%b %y}", (r["policy tailwind (pp, next 3m)"], r["+60d %"]), xytext=(4, 3), textcoords="offset points", fontsize=7.5, color=INK2)
ax.axhline(0, color=GRAY, lw=0.8); ax.axvline(0, color=GRAY, lw=0.8)
ax.set_xlabel("Rate-gap tailwind over next 3 months (pp; +ve = rates moved the way MoF wanted)")
ax.set_ylabel("60-day move in MoF's intended direction (%)")
ax.set_title("Did interventions stick when monetary policy helped?")
ax.scatter([], [], color=BLUE, label="Bought yen"); ax.scatter([], [], color=RED, label="Sold yen"); ax.legend(loc="lower left")
c = e2["policy tailwind (pp, next 3m)"].corr(e2["+60d %"])
fx.source_note(ax, f"Correlation = {c:.2f} across {len(e2)} episodes. Ex-post diagnostic only: the tailwind uses FUTURE rate moves.")
fig.tight_layout(); fx.save(fig, "03d_intervention_vs_policy_tailwind"); plt.show()
print(f"Share of episodes with a positive +60d move: {(e2['+60d %']>0).mean():.0%};  "
      f"with tailwind>0: {(e2.loc[e2['policy tailwind (pp, next 3m)']>0,'+60d %']>0).mean():.0%}  vs  tailwind<=0: {(e2.loc[e2['policy tailwind (pp, next 3m)']<=0,'+60d %']>0).mean():.0%}")
''')
md("s3_3_read")

md("s3_4")
code(r'''
hikes = {"2024-03-19": "end of negative rates (0-0.1%)", "2024-07-31": "0.25%", "2025-01-24": "0.50%",
         "2025-12-19": "0.75%", "2026-06-16": "1.00%", "2026-09-18": "1.25%"}
rows = []
for d, lvl in hikes.items():
    i = jd.index.searchsorted(pd.Timestamp(d)); b = jd.iloc[i - 1]
    rows.append({"BoJ hike": d, "new rate": lvl, "USDJPY before": b,
                 **{f"+{h}d %": (100 * np.log(jd.iloc[i + h] / b) if i + h < len(jd) else np.nan) for h in (0, 5, 20, 60)}})
bojt = pd.DataFrame(rows)
print("USDJPY % change after each BoJ hike (positive = yen WEAKENED despite the hike). Day 0 = Fed H.10 noon-NY fix on decision day.")
display(bojt)

z = jd["2025-01-01":]
fig, ax = plt.subplots(figsize=(11.5, 4.8))
ax.plot(z.index, z, color=BLUE, lw=1.3)
for d, lvl in hikes.items():
    t = pd.Timestamp(d)
    if t >= z.index[0]:
        ax.axvline(t, color=VIOLET, lw=0.9); ax.annotate(f"BoJ → {lvl}", (t, z.max() + 0.5), rotation=90, fontsize=7.5, color=VIOLET, ha="right", va="top")
for _, o in yen_ops[yen_ops.date >= "2025-01-01"].iterrows():
    t = jd.index[min(jd.index.searchsorted(o.date), len(jd) - 1)]
    ax.scatter(t, jd[t], s=10 + 9 * o.yen_tn, color=INK, edgecolor="white", linewidth=1.5, zorder=4)
ax.scatter([], [], color=INK, s=40, label="Yen-buying intervention (size ∝ ¥)"); ax.plot([], [], color=VIOLET, lw=0.9, label="BoJ rate hike")
ax.axvline(pd.Timestamp("2026-09-16"), color=GRAY, lw=0.9); ax.annotate("Fed hikes to 3.75-4.00%", (pd.Timestamp("2026-09-16"), z.min()), rotation=90, fontsize=7.5, color=INK2, ha="right", va="bottom")
ax.legend(loc="lower center"); ax.set_ylabel("JPY per USD"); ax.set_title("2025-26 close-up: USDJPY, BoJ hikes and yen-buying interventions")
fx.source_note(ax, "Source: FRED DEXJPUS; MoF; BoJ decisions (press). Jul 30-31 2026 marks are the reported joint US-Japan operation.")
fig.tight_layout(); fx.save(fig, "03e_2025_2026_closeup"); plt.show()
''')
md("s3_4_read")

md("s3_5")
code(r'''
reer = fx.monthly_last(fx.fred("RBJPBIS")); neer = fx.monthly_last(fx.fred("NBJPBIS"))
fig, ax = plt.subplots(figsize=(11.5, 4.3))
ax.plot(reer.index, reer, color=BLUE, label="Real effective exchange rate (inflation-adjusted, vs. trading partners)")
ax.plot(neer.index, neer, color=GRAY, lw=1.2, label="Nominal effective exchange rate")
ax.axhline(100, color=LIGHTGRAY, lw=0.8)
ax.annotate(f"{reer.iloc[-1]:.0f} ({reer.index[-1]:%b %Y})\nlowest in the BIS series", (reer.index[-1], reer.iloc[-1]), xytext=(-150, -8), textcoords="offset points", fontsize=8.5, color=INK2)
ax.set_title("The yen is historically cheap in real terms (index, 2020 = 100)"); ax.legend(loc="upper right")
fx.source_note(ax, "Source: BIS broad effective exchange rates via FRED (RBJPBIS, NBJPBIS). Monthly averages.")
fig.tight_layout(); fx.save(fig, "03f_jpy_reer"); plt.show()
print(f"Current REER percentile vs. 1994-today: {(reer <= reer.iloc[-1]).mean():.1%}")
''')
md("s3_5_read")

md("s3_6")
code(r'''
cot = pd.read_csv("data/raw/cftc_currency_cot.csv", parse_dates=["date"])
cot["net_pct_oi"] = 100 * (cot.nc_long - cot.nc_short) / cot.oi
pos_w = cot.pivot(index="date", columns="ccy", values="net_pct_oi")
pos = pos_w.resample("ME").last().reindex(spot.index)

fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.5, 6.2), sharex=True, gridspec_kw={"height_ratios": [2, 1.5]})
a1.plot(jd["2000":], color=BLUE, lw=0.9); a1.set_ylabel("JPY per USD"); a1.set_title("Speculator positioning in yen futures vs. USDJPY")
pj = pos_w["JPY"]
a2.fill_between(pj.index, 0, pj, where=pj >= 0, color=BLUE, alpha=0.35, label="Speculators net LONG yen")
a2.fill_between(pj.index, 0, pj, where=pj < 0, color=RED, alpha=0.35, label="Speculators net SHORT yen (carry trade)")
a2.axhline(0, color=GRAY, lw=0.8); a2.set_ylabel("net % of open interest"); a2.legend(loc="lower left", fontsize=8)
for d0, d1, lbl in [("2007-06-01", "2007-08-31", "2007"), ("2024-07-01", "2024-08-10", "Aug 2024")]:
    for a in (a1, a2): a.axvspan(pd.Timestamp(d0), pd.Timestamp(d1), color=LIGHTGRAY, alpha=0.6, lw=0)
    a1.annotate(f"{lbl} unwind", (pd.Timestamp(d0), jd[d0:d1].max()), xytext=(0, 8), textcoords="offset points", fontsize=8, color=INK2, ha="center")
fx.source_note(a2, "Source: CFTC Commitments of Traders (legacy, futures only), CME yen futures; non-commercial positions.")
fig.tight_layout(); fx.save(fig, "03g_jpy_positioning"); plt.show()

d = pd.DataFrame({"positioning": pos["JPY"], "next 1m JPY spot %": 100 * -ds["JPY"].shift(-1),
                  "next 3m JPY spot %": 100 * -np.log(spot["JPY"]).diff(3).shift(-3)}).dropna()
tbl = d.groupby(pd.qcut(d.positioning, 5, labels=["Q1 most short", "Q2", "Q3", "Q4", "Q5 most long"])).mean()
tbl["months"] = d.groupby(pd.qcut(d.positioning, 5)).size().values
print("Average NEXT-period yen move (positive = yen strengthened) by speculator-positioning quintile, 2000-2026")
tbl
''')
md("s3_6_read")

# ---------------------------------------------------------------- 4. India
md("s4")
md("s4_1")
code(r'''
fig, ax = plt.subplots(figsize=(11.5, 4.4))
z = ind["2000":]
ax.plot(z.index, z, color=ORANGE, lw=1.1)
for d0, d1, lbl in [("2008-09-01", "2009-03-31", "GFC"), ("2013-05-22", "2013-09-04", "Taper tantrum"),
                    ("2018-04-01", "2018-10-15", "2018 EM/oil"), ("2022-02-24", "2022-10-20", "Fed hikes/oil"),
                    ("2025-01-01", "2026-05-20", "2025-26 slide")]:
    ax.axvspan(pd.Timestamp(d0), pd.Timestamp(d1), color=LIGHTGRAY, alpha=0.5, lw=0)
    ax.annotate(lbl, (pd.Timestamp(d0), z[d0:d1].max()), xytext=(0, 6), textcoords="offset points", fontsize=8, color=INK2)
ax.set_ylabel("INR per USD"); ax.set_title("USDINR since 2000: a managed crawl punctuated by stress episodes")
fx.source_note(ax, "Source: FRED DEXINUS (Fed H.10).")
fig.tight_layout(); fx.save(fig, "04a_usdinr_history"); plt.show()

yr_dep = 100 * np.log(ind.resample("YE").last()).diff()
yr_gap = (P["rate"]["INR"] - P["us_rate"]).resample("YE").mean()
yrs = pd.DataFrame({"Rupee depreciation % (actual)": yr_dep, "UIP-predicted depreciation % (= rate gap)": yr_gap}).loc["2001":]
yrs.index = yrs.index.year
yrs["Actual minus UIP"] = yrs.iloc[:, 0] - yrs.iloc[:, 1]
fig, ax = plt.subplots(figsize=(11.5, 4.2))
x = np.arange(len(yrs)); w = 0.38
ax.bar(x - w / 2, yrs.iloc[:, 0], width=w, color=ORANGE, label="Actual rupee depreciation vs USD")
ax.bar(x + w / 2, yrs.iloc[:, 1], width=w, color=GRAY, label="What UIP predicted (India minus US short rate)")
ax.set_xticks(x); ax.set_xticklabels(yrs.index, rotation=90, fontsize=8); ax.axhline(0, color=GRAY, lw=0.8)
ax.set_ylabel("% per year"); ax.legend(loc="upper left"); ax.set_title("Each year: how much did the rupee fall vs. what the rate gap implied?")
fx.source_note(ax, f"2026 is year-to-date through {ind.index[-1]:%d %b}. Source: FRED DEXINUS, IRSTCI01INM156N, IR3TIB01USM156N.")
fig.tight_layout(); fx.save(fig, "04b_inr_actual_vs_uip_by_year"); plt.show()
full = yrs.loc[2001:2025]
print(f"2001-2025 average: actual depreciation {full.iloc[:,0].mean():.2f}%/yr, UIP-implied {full.iloc[:,1].mean():.2f}%/yr, "
      f"median actual {full.iloc[:,0].median():.2f}%; years actual < UIP: {(full['Actual minus UIP']<0).sum()} of {len(full)}")
yrs.round(2).T
''')
md("s4_1_read")

md("s4_2")
code(r'''
daily = {c: fx.spot_daily(c).dropna() for c in spot.columns}
vol = pd.Series({c: 100 * np.log(s["2010":]).diff().std() * np.sqrt(252) for c, s in daily.items()})
skw = pd.Series({c: np.log(s["2010":].resample("ME").last()).diff().skew() for c, s in daily.items()})
vol = vol.sort_values()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.6))
cols = [fx.CCY_COLOR.get(c, LIGHTGRAY) if c in ("INR", "JPY") else "#b9b8b3" for c in vol.index]
a1.barh(vol.index, vol, color=cols, height=0.7); a1.set_xlabel("Annualised daily vol since 2010, %"); a1.set_title("Realised volatility vs USD")
for i, v in enumerate(vol): a1.annotate(f"{v:.1f}", (v, i), xytext=(3, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
r1 = pd.DataFrame({c: 100 * np.log(daily[c]).diff().rolling(63).std() * np.sqrt(252) for c in ["INR", "JPY", "KRW", "BRL"]})["2005":]
for c, col in zip(r1, [ORANGE, BLUE, AQUA, YELLOW]):
    a2.plot(r1.index, r1[c], color=col, lw=1.0 if c != "INR" else 1.6, label=c)
a2.set_title("Rolling 3-month realised vol, % (axis capped at 30; 2008 peaks ~55)"); a2.set_ylim(0, 30); a2.legend(loc="upper left", ncol=4)
fx.source_note(a1, "Source: FRED H.10 daily spot (TRY, IDR from Yahoo Finance). INR = orange, JPY = blue.")
fig.tight_layout(); fx.save(fig, "04c_inr_volatility"); plt.show()
print("Monthly-return skewness since 2010 (positive = fat tail of foreign-currency DEPRECIATION):"); print(skw.round(2).sort_values().to_dict())
''')
md("s4_2_read")

md("s4_3")
code(r'''
resv = fx.monthly_last(fx.fred("TRESEGINM052N")) / 1e3
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.5, 6.2), sharex=True)
a1.plot(resv["2005":].index, resv["2005":], color=ORANGE); a1.set_ylabel("USD bn"); a1.set_title("RBI foreign-exchange reserves (ex gold)")
d3r = 100 * np.log(resv).diff(3); d3s = 100 * np.log(spot["INR"]).diff(3)
dd = pd.DataFrame({"res": d3r, "dep": d3s}).dropna()["2005":]
a2.bar(dd.index, dd.res, width=25, color=[BLUE if v >= 0 else RED for v in dd.res], label="3m % change in reserves")
a2.plot(dd.index, dd.dep, color=INK, lw=1.2, label="3m % rupee depreciation")
a2.axhline(0, color=GRAY, lw=0.8); a2.legend(loc="upper left", ncol=2); a2.set_ylabel("%")
a2.set_title("Reserves fall when the rupee is under pressure: the RBI leans against depreciation")
fx.source_note(a2, "Source: IMF IFS via FRED (TRESEGINM052N); FRED DEXINUS. Reserve changes also include valuation effects.")
fig.tight_layout(); fx.save(fig, "04d_rbi_reserves"); plt.show()
print(f"Corr(3m reserve change, 3m depreciation) = {dd.res.corr(dd.dep):.2f}")
''')
md("s4_3_read")

md("s4_4")
code(r'''
windows = {"2013 FCNR(B) swap window": ("2013-09-04", "2013-11-30", ORANGE),
           "2026 FCNR(B) swap window": ("2026-06-08", "2026-08-31", VIOLET)}
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), gridspec_kw={"width_ratios": [1, 1, 1.3]})
for ax, (lbl, (a, b, col)) in zip(axes[:2], windows.items()):
    seg = ind[pd.Timestamp(a) - pd.Timedelta(days=150): pd.Timestamp(b) + pd.Timedelta(days=200)]
    ax.plot(seg.index, seg, color=col, lw=1.2); ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=LIGHTGRAY, alpha=0.6, lw=0)
    ax.set_title(lbl); ax.set_ylabel("INR per USD"); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    pk = seg[:b].idxmax(); ax.annotate(f"peak {seg[pk]:.2f}", (pk, seg[pk]), xytext=(5, -2), textcoords="offset points", fontsize=8, color=INK2)
ax = axes[2]
for lbl, (a, b, col) in windows.items():
    i = ind.index.searchsorted(pd.Timestamp(a)); base = ind.iloc[i - 1]
    seg = ind.iloc[i - 60:i + 250]
    ax.plot(np.arange(len(seg)) - 60, 100 * np.log(seg.values / base), color=col, lw=1.4, label=lbl[:4])
ax.axvline(0, color=GRAY, lw=0.8); ax.axhline(0, color=GRAY, lw=0.8)
ax.set_xlabel("Trading days from window opening"); ax.set_ylabel("% change in USDINR (down = rupee stronger)")
ax.set_title("Same policy, two outcomes so far"); ax.legend(loc="upper right")
fx.source_note(axes[0], "Shaded = eligible deposit window. Source: FRED DEXINUS; RBI circulars (2013, 2026).")
fig.tight_layout(); fx.save(fig, "04e_fcnr_2013_vs_2026"); plt.show()

rows = []
for lbl, (a, b, _) in windows.items():
    ia, ib = ind.index.searchsorted(pd.Timestamp(a)), ind.index.searchsorted(pd.Timestamp(b))
    pre_peak = ind[:a].iloc[-90:].max()
    f = lambda k: 100 * np.log(ind.iloc[k] / ind.iloc[ia - 1]) if k < len(ind) else np.nan
    rows.append({"window": lbl, "USDINR before": ind.iloc[ia - 1], "90d pre-window peak": pre_peak,
                 "% during window": f(ib), "% +3m after open": f(ia + 63), "% +6m": f(ia + 126), "% +12m": f(ia + 252),
                 "latest": ind.iloc[-1]})
pd.DataFrame(rows).set_index("window")
''')
md("s4_4_read")

md("s4_5")
code(r'''
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5))
for ax, code_, sign, title in [(axes[0], "INR", 1, "LONG rupee vs USD (earn India-US rate gap)"),
                                (axes[1], "JPY", -1, "SHORT yen vs USD (classic yen carry trade)")]:
    df = pd.DataFrame({"Interest earned": sign * carry[code_].shift(1) / 12, "Spot FX move": sign * -ds[code_]}).dropna()["2000":]
    cum = 100 * df.cumsum(); tot = cum.sum(axis=1)
    ax.plot(cum.index, cum["Interest earned"], color=GRAY, lw=1.3, label="Interest earned")
    ax.plot(cum.index, cum["Spot FX move"], color=fx.CCY_COLOR[code_], lw=1.3, label="Spot FX gain/loss")
    ax.plot(tot.index, tot, color=INK, lw=2.0, label="Total")
    for s, c in [(cum["Interest earned"], GRAY), (cum["Spot FX move"], fx.CCY_COLOR[code_]), (tot, INK)]:
        ax.annotate(f"{s.iloc[-1]:+.0f}%", (s.index[-1], s.iloc[-1]), xytext=(3, 0), textcoords="offset points", fontsize=8.5, color=INK2, va="center")
    ax.axhline(0, color=GRAY, lw=0.8); ax.set_title(title); ax.set_ylabel("cumulative log return, %"); ax.legend(loc="upper left")
fx.source_note(axes[0], "Unlevered, no costs, monthly rebalanced, rate gap from 3M interbank / call rates (a proxy for forward points).")
fig.tight_layout(); fx.save(fig, "04f_carry_decomposition_inr_jpy"); plt.show()
fx.perf_table({"Long INR carry": rx["INR"], "Short JPY carry": -rx["JPY"],
               "Long INR, 2013-26": rx["INR"]["2013":], "Short JPY, 2013-26": -rx["JPY"]["2013":]}).round(2)
''')
md("s4_5_read")

# ---------------------------------------------------------------- 5. panel
md("s5")
md("s5_1")
code(r'''
since = "2000"
char = pd.DataFrame({
    "Group": {c.code: c.group for c in fx.UNIVERSE},
    "Avg carry vs USD %": 100 * carry[since:].mean(),
    "Avg trade bal % of trade": tb[since:].mean(),
    "% months net exporter": 100 * (tb[since:] > 0).sum() / tb[since:].notna().sum(),
    "Avg current acct % GDP": ca[since:].mean(),
    "Carry-trade ann. return %": 1200 * rx[since:].mean(),
    "Ann. vol %": 100 * rx[since:].std() * np.sqrt(12),
    "Skew": rx[since:].skew(),
}).sort_values("Avg carry vs USD %")
char
''')
md("s5_2")
code(r'''
rows = {}
for c in spot:
    m = fx.nw_ols(ds[c].shift(-1) * 12, carry[c].rename("carry"))
    rows[c] = {"beta": m.params["carry"], "se": m.bse["carry"], "n": int(m.nobs)}
fama = pd.DataFrame(rows).T.sort_values("beta")
L = pd.DataFrame({"dsf": (ds.shift(-1) * 12).stack(), "carry": carry.stack(), "tb": tb.stack(), "ca": ca.stack()}).dropna()
pooled = {"All currency-months": fx.nw_ols(L.dsf, L[["carry"]])}
for nm, sub in [("Net exporters (trade > 0)", L[L.tb > 0]), ("Net importers (trade <= 0)", L[L.tb <= 0]),
                ("Current-account surplus", L[L.ca > 0]), ("Current-account deficit", L[L.ca <= 0])]:
    pooled[nm] = fx.nw_ols(sub.dsf, sub[["carry"]])
L["carry_x_deficit"] = L.carry * (L.tb <= 0); L["deficit"] = (L.tb <= 0).astype(float)
inter = fx.nw_ols(L.dsf, L[["carry", "carry_x_deficit", "deficit"]])

fig, ax = plt.subplots(figsize=(11.5, 4.6))
x = np.arange(len(fama))
cols = [fx.CCY_COLOR.get(c, "#9d9c97") if c in ("JPY", "INR") else "#9d9c97" for c in fama.index]
ax.errorbar(x, fama.beta, yerr=1.96 * fama.se, fmt="none", ecolor=LIGHTGRAY, elinewidth=2.5, capsize=0)
ax.scatter(x, fama.beta, color=cols, s=45, zorder=3, edgecolor="white", linewidth=1.5)
ax.axhline(1, color=GRAY, lw=1.1); ax.annotate("β = 1: UIP holds", (len(fama) - 0.5, 1), xytext=(0, 4), textcoords="offset points", ha="right", fontsize=8.5, color=INK2)
ax.axhline(0, color=LIGHTGRAY, lw=1.0); ax.annotate("β = 0: rate gap tells you nothing", (len(fama) - 0.5, 0), xytext=(0, -12), textcoords="offset points", ha="right", fontsize=8.5, color=INK2)
ax.set_xticks(x); ax.set_xticklabels(fama.index); ax.set_ylabel("β  (depreciation per 1pp rate gap)")
ax.set_title("UIP ('Fama') regression by currency, 1999-2026: β < 1 means high-rate currencies don't fall enough")
fx.source_note(ax, "Monthly: next-month annualised depreciation on today's rate gap. Bars = 95% CI (Newey-West).")
fig.tight_layout(); fx.save(fig, "05a_fama_betas"); plt.show()
out = pd.DataFrame({k: {"beta": m.params["carry"], "se": m.bse["carry"], "t-stat vs UIP (β=1)": (m.params["carry"] - 1) / m.bse["carry"], "obs": int(m.nobs)} for k, m in pooled.items()}).T
display(out)
print("Interaction model: dep = a + b·gap + c·(gap × net-importer) + d·net-importer")
print(pd.DataFrame({"coef": inter.params, "t": inter.tvalues}).round(2))
''')
md("s5_2_read")

md("s5_3")
code(r'''
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
X = char["Avg carry vs USD %"]
for ax, ycol, ttl in [(a1, "Carry-trade ann. return %", "Average rate gap vs. average carry-trade return"),
                      (a2, "Skew", "Average rate gap vs. skewness (crash risk)")]:
    Y = char[ycol]
    for c in char.index:
        col = fx.CCY_COLOR.get(c, "#8f8e89") if c in ("JPY", "INR") else "#8f8e89"
        ax.scatter(X[c], Y[c], color=col, s=42, edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(c, (X[c], Y[c]), xytext=(4, 3), textcoords="offset points", fontsize=8, color=INK2)
    b = np.polyfit(X, Y, 1); xx = np.linspace(X.min(), X.max(), 10)
    ax.plot(xx, np.polyval(b, xx), color=LIGHTGRAY, lw=1.2); ax.axhline(0, color=LIGHTGRAY, lw=0.8)
    ax.set_xlabel("Average rate gap vs USD, % p.a. (2000-2026)"); ax.set_ylabel(ycol); ax.set_title(ttl)
    ax.annotate(f"corr = {X.corr(Y):.2f}   (excl. TRY: {X.drop('TRY').corr(Y.drop('TRY')):.2f})", xy=(0.02, 0.04), xycoords="axes fraction", fontsize=8.5, color=INK2)
fx.source_note(a1, "Each dot = one currency; carry-trade return = long that currency vs USD, monthly, no costs.")
fig.tight_layout(); fx.save(fig, "05b_carry_vs_return_and_skew"); plt.show()
''')
md("s5_3_read")

md("s5_4")
code(r'''
def two_by_two(r, key_df, excl=(), start=None, end=None, only=None):
    L2 = pd.DataFrame({"r": r.shift(-1).stack(), "carry": carry.stack(), "k": key_df.stack()}).dropna()
    cc = L2.index.get_level_values(1); dd = L2.index.get_level_values(0)
    keep = ~cc.isin(excl)
    if only is not None: keep &= cc.isin(only)
    if start: keep &= dd >= pd.Timestamp(start)
    if end: keep &= dd <= pd.Timestamp(end)
    L2 = L2[keep]
    hi = L2.groupby(level=0).carry.transform(lambda x: x > x.median())
    g = L2.groupby([np.where(hi, "High carry", "Low carry"), np.where(L2.k > 0, "Net exporter", "Net importer")]).r
    return pd.DataFrame({"Ann. return %": 1200 * g.mean(), "Ann. vol %": 100 * np.sqrt(12) * g.std(), "Skew": g.skew(),
                         "Worst month %": 100 * g.min(), "Currency-months": g.size()})

rx_dn = rx.sub(rx.mean(axis=1), axis=0)          # dollar-neutral: subtract the average currency each month
base = two_by_two(rx, tb); neutral = two_by_two(rx_dn, tb)
print("A) Raw carry-trade returns (long foreign ccy vs USD) by carry and trade-balance bucket"); display(base)
print("B) Same, dollar-neutral (removes the broad-USD trend that hits every currency at once)"); display(neutral)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=False)
for ax, tbl, ttl in [(axes[0], base, "Raw"), (axes[1], neutral, "Dollar-neutral")]:
    t = tbl["Ann. return %"].unstack()
    xx = np.arange(2); w = 0.36
    ax.bar(xx - w / 2, t["Net exporter"], width=w, color=BLUE, label="Net exporter (trade surplus)")
    ax.bar(xx + w / 2, t["Net importer"], width=w, color=RED, label="Net importer (trade deficit)")
    for i, c in enumerate(t.index):
        for off, col in [(-w / 2, "Net exporter"), (w / 2, "Net importer")]:
            v = t.loc[c, col]; ax.annotate(f"{v:+.1f}", (i + off, v), xytext=(0, 3 if v >= 0 else -11), textcoords="offset points", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(xx); ax.set_xticklabels(t.index); ax.axhline(0, color=GRAY, lw=0.8)
    ax.set_ylabel("Ann. return %, long foreign ccy"); ax.set_title(f"{ttl}: carry return by bucket"); ax.legend(loc="upper right", fontsize=8)
fx.source_note(axes[0], "High/low carry = above/below that month's cross-sectional median. Trade balance lagged 2 months. 17 currencies, 2000-2026.")
fig.tight_layout(); fx.save(fig, "05c_two_by_two_carry_trade_balance"); plt.show()

em = [c for c in spot if fx.U[c].group == "EM"]; g10 = [c for c in spot if fx.U[c].group == "G10"]
variants = {"Baseline": {}, "2000-2012": {"end": "2012-12-31"}, "2013-2026": {"start": "2013-01-01"},
            "Excl. TRY": {"excl": ("TRY",)}, "Excl. TRY & BRL": {"excl": ("TRY", "BRL")}, "G10 only": {"only": g10}, "EM only": {"only": em}}
rob = {}
for nm, kw in variants.items():
    for lab, key in [("trade balance", tb), ("current account", ca)]:
        t = two_by_two(rx_dn, key, **kw)["Ann. return %"]
        rob[(nm, lab)] = {"High carry: exporter minus importer (pp)": t.get(("High carry", "Net exporter"), np.nan) - t.get(("High carry", "Net importer"), np.nan),
                          "Low carry: exporter minus importer (pp)": t.get(("Low carry", "Net exporter"), np.nan) - t.get(("Low carry", "Net importer"), np.nan)}
print("C) Robustness: return spread between net exporters and net importers within each carry bucket (dollar-neutral, % p.a.)")
pd.DataFrame(rob).T
''')
md("s5_4_read")

md("s5_5")
code(r'''
usd = np.log(fx.monthly_last(fx.fred("DTWEXBGS"))).diff()
rows = {}
for c in [k for k in spot if fx.U[k].reserves]:
    r = np.log(fx.monthly_last(fx.fred(f"TRESEG{fx.U[c].reserves}M052N"))).diff()
    d = pd.DataFrame({"dres": r, "dep": ds[c].clip(lower=0), "app": ds[c].clip(upper=0), "usd": usd}).dropna()["2006":]
    m = fx.nw_ols(d.dres, d[["dep", "app", "usd"]])
    rows[c] = {"Defence: reserve % lost per 1% depreciation": -m.params["dep"], "t (defence)": -m.tvalues["dep"],
               # appreciation enters as a negative ds, so reserve build-up shows as a negative coefficient
               "Accumulation: reserve % gained per 1% appreciation": -m.params["app"], "t (accum.)": -m.tvalues["app"],
               "Avg trade bal %": tb[c]["2006":].mean(), "Avg CA % GDP": ca[c]["2006":].mean()}
lw = pd.DataFrame(rows).T
lw = lw.sort_values("Defence: reserve % lost per 1% depreciation", ascending=False)
display(lw)

fig, ax = plt.subplots(figsize=(8.5, 4.8))
for c, r in lw.iterrows():
    col = fx.CCY_COLOR.get(c, "#8f8e89") if c in ("JPY", "INR") else "#8f8e89"
    sig = r["t (defence)"] >= 2   # filled = statistically significant (t >= 2), hollow = not
    ax.scatter(r["Avg trade bal %"], r["Defence: reserve % lost per 1% depreciation"], s=45, color=col if sig else "white", edgecolor=col, linewidth=1.5, zorder=3)
    ax.annotate(c, (r["Avg trade bal %"], r["Defence: reserve % lost per 1% depreciation"]), xytext=(4, 3), textcoords="offset points", fontsize=8, color=INK2)
ax.axvline(0, color=LIGHTGRAY); ax.axhline(0, color=LIGHTGRAY)
ax.set_xlabel("Average trade balance, % of trade (2006-26)  ← net importer | net exporter →")
ax.set_ylabel("Downside defence intensity")
ax.set_title("Who spends reserves to stop depreciation?")
fx.source_note(ax, "Filled = significant (t ≥ 2); hollow = not. Monthly Δlog reserves on depreciation/appreciation, controlling for the broad USD index. 2006-26.")
fig.tight_layout(); fx.save(fig, "05d_defence_vs_trade_balance"); plt.show()
print(f"Correlation(defence intensity, avg trade balance) = {lw.iloc[:,0].corr(lw['Avg trade bal %']):.2f} (n={len(lw)})")
''')
md("s5_5_read")

md("s5_6")
code(r'''
def hml(signal, q=1/3, min_n=6, cols=None):
    s = signal if cols is None else signal[cols]
    r = s.rank(axis=1, pct=True); fwd = rx[s.columns].shift(-1)
    out = fwd[r > 1 - q].mean(axis=1) - fwd[r <= q].mean(axis=1)
    out[s.notna().sum(axis=1) < min_n] = np.nan
    return out.shift(1).dropna()

reer_all = P["reer"]
signals = {
    "Carry (rate gap)": carry,
    "Trade balance": tb,
    "Trade balance vs own 5y avg (timing only)": tb - tb.rolling(60, min_periods=36).mean(),
    "Trade balance 12m change": tb.diff(12),
    "Current account": ca,
    "Value: REER vs 5y avg (cheap = long)": -np.log(reer_all / reer_all.rolling(60).mean()),
    "Momentum 12m": -ds.rolling(12).sum(),
    "Momentum 3m": -ds.rolling(3).sum(),
    "UIP 'tension' 36m (cum. deviation)": rx.rolling(36).sum(),
    "Contrarian positioning (CFTC)": -pos,
}
H = {k: hml(v) for k, v in signals.items()}
race = fx.perf_table(H)[["Ann. return %", "Ann. vol %", "Sharpe", "Skew", "Max drawdown %", "Months"]]
race["Ret 2000-12 %"] = [1200 * H[k][:"2012"].mean() for k in race.index]
race["Ret 2013-26 %"] = [1200 * H[k]["2013":].mean() for k in race.index]
race["t-stat"] = [H[k].mean() / H[k].std() * np.sqrt(len(H[k])) for k in race.index]
print("Long top-third / short bottom-third of currencies by each signal, rebalanced monthly, no costs:")
display(race.sort_values("Sharpe", ascending=False))

Hdf = pd.DataFrame(H).dropna()
cm = Hdf.corr()
fig, ax = plt.subplots(figsize=(7.8, 6.2))
im = ax.imshow(cm, cmap=DIVERGING, vmin=-1, vmax=1)
ax.set_xticks(range(len(cm))); ax.set_yticks(range(len(cm)))
short = [k.split(" (")[0].split(":")[0] for k in cm.index]
ax.set_xticklabels(short, rotation=45, ha="right", fontsize=8); ax.set_yticklabels(short, fontsize=8); ax.grid(False)
for i in range(len(cm)):
    for j in range(len(cm)):
        ax.text(j, i, f"{cm.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7.5, color=INK)
ax.set_title("Correlation between the signal portfolios"); fig.colorbar(im, ax=ax, shrink=0.75)
fig.tight_layout(); fx.save(fig, "05e_signal_correlations"); plt.show()

fig, ax = plt.subplots(figsize=(11.5, 4.5))
for k, col in zip(["Carry (rate gap)", "Trade balance", "Value: REER vs 5y avg (cheap = long)", "Momentum 12m", "Trade balance vs own 5y avg (timing only)"], [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]):
    s = 100 * H[k].cumsum(); ax.plot(s.index, s, color=col, label=k)
    ax.annotate(f"{s.iloc[-1]:+.0f}%", (s.index[-1], s.iloc[-1]), xytext=(3, 0), textcoords="offset points", fontsize=8.5, color=INK2, va="center")
ax.axhline(0, color=GRAY, lw=0.8); ax.legend(loc="upper left"); ax.set_ylabel("cumulative log return, %")
ax.set_title("Signal horse race: cumulative return of each long-short currency portfolio")
fx.source_note(ax, "17 currencies, monthly, equal-weight terciles, no costs.")
fig.tight_layout(); fx.save(fig, "05f_signal_horse_race"); plt.show()
''')
md("s5_6_read")

md("s5_7")
code(r'''
vix = fx.monthly_last(fx.fred("VIXCLS"))
dv = vix.diff().reindex(Hdf.index)
C, T = H["Carry (rate gap)"], H["Trade balance"]
worst = C.nsmallest(10).to_frame("Carry portfolio %").mul(100)
worst["Trade-balance portfolio %"] = 100 * T.reindex(worst.index)
worst["VIX change (pts)"] = dv.reindex(worst.index)
worst.index = worst.index.strftime("%b %Y")
print("The 10 worst months for the carry portfolio, and what the trade-balance portfolio did at the same time:")
display(worst)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.3), sharey=True)
for ax, s, col, nm in [(axes[0], C, BLUE, "Carry portfolio"), (axes[1], T, ORANGE, "Trade-balance portfolio")]:
    d = pd.DataFrame({"dv": dv, "r": 100 * s}).dropna()
    ax.scatter(d.dv, d.r, s=14, color=col, alpha=0.7, edgecolor="white", linewidth=0.5)
    b = np.polyfit(d.dv, d.r, 1); xx = np.linspace(d.dv.min(), d.dv.max(), 10); ax.plot(xx, np.polyval(b, xx), color=INK, lw=1.2)
    ax.axhline(0, color=LIGHTGRAY); ax.axvline(0, color=LIGHTGRAY)
    ax.set_title(f"{nm} vs. VIX change (corr {d.dv.corr(d.r):.2f})"); ax.set_xlabel("Monthly change in VIX (points)")
axes[0].set_ylabel("Monthly return, %")
fig.tight_layout(); fx.save(fig, "05g_crash_risk_vs_vix"); plt.show()
''')
md("s5_7_read")

# ---------------------------------------------------------------- 6. strategies
md("s6")
code(r'''
G10 = [c for c in spot if fx.U[c].group == "G10"]

tercile_w, zx = fx.tercile_w, fx.zx                       # shared engine in src/fxlib.py (same as the Final Proposal)
def run(w, start="2000-01-31"):
    return fx.run_basket(P, w, start)

W = {
    "A. Carry (17 ccy)": tercile_w(carry),
    "B. Trade balance (17 ccy)": tercile_w(tb),
    "C. 50/50 blend A+B": 0.5 * tercile_w(carry) + 0.5 * tercile_w(tb),
    "D. Composite z(carry)+z(trade)": tercile_w(zx(carry) + zx(tb)),
    "E. Carry, G10 only": tercile_w(carry[G10]),
    "F. 50/50 blend, G10 only": 0.5 * tercile_w(carry[G10]) + 0.5 * tercile_w(tb[G10]),
    "G. Long-only: top-3 carry vs USD": (lambda r: r.div(r.sum(1), axis=0).fillna(0))((carry.rank(axis=1, ascending=False) <= 3).astype(float)),
    # H was added AFTER seeing section 5.6 (post-hoc) - treat as exploratory, not as confirmed
    "H*. 50/50 carry + trade-vs-own-5y-avg (post-hoc)": 0.5 * tercile_w(carry) + 0.5 * tercile_w(tb - tb.rolling(60, min_periods=36).mean()),
}
R, TURN = {}, {}
for k, w in W.items():
    R[k], TURN[k] = run(w)
perf = fx.perf_table(R)[["Ann. return %", "Ann. vol %", "Sharpe", "Skew", "Worst month %", "Max drawdown %", "Hit rate %"]]
perf["Sharpe 2000-12"] = [fx.perf(R[k][:"2012"])["Sharpe"] for k in perf.index]
perf["Sharpe 2013-26"] = [fx.perf(R[k]["2013":])["Sharpe"] for k in perf.index]
perf["Sharpe last 5y"] = [fx.perf(R[k][R[k].index[-1] - pd.DateOffset(years=5):])["Sharpe"] for k in perf.index]
perf["Turnover x/yr"] = pd.Series(TURN)
print("Net of assumed costs (G10 4bp / EM 12bp per trade + monthly forward-roll cost). Monthly rebalance.")
perf
''')
code(r'''
show = ["A. Carry (17 ccy)", "B. Trade balance (17 ccy)", "C. 50/50 blend A+B", "E. Carry, G10 only", "G. Long-only: top-3 carry vs USD"]
cols = [BLUE, ORANGE, INK, AQUA, MAGENTA]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.5, 7.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.2]})
for k, col in zip(show, cols):
    s = 100 * (np.exp(R[k].cumsum()) - 1)
    a1.plot(s.index, s, color=col, lw=2.0 if k.startswith("C.") else 1.3, label=k)
    a1.annotate(f"{s.iloc[-1]:+.0f}%", (s.index[-1], s.iloc[-1]), xytext=(3, -7 if k.startswith("E.") else 3), textcoords="offset points", fontsize=8.5, color=INK2, va="center")
    eq = R[k].cumsum(); dd = 100 * (np.exp(eq - eq.cummax()) - 1)
    a2.plot(dd.index, dd, color=col, lw=2.0 if k.startswith("C.") else 1.0)
a1.axvline(pd.Timestamp("2013-01-01"), color=GRAY, lw=0.8); a1.annotate("  2013: second half of sample", (pd.Timestamp("2013-01-01"), a1.get_ylim()[1] * 0.92), fontsize=8, color=INK2)
a1.set_ylabel("cumulative return, % (unlevered)"); a1.legend(loc="upper left"); a1.set_title("Candidate strategies, net of costs")
a2.set_ylabel("drawdown, %"); a2.set_title("Drawdowns")
fx.source_note(a2, "Unlevered; each long-short leg sums to 100% notional. Costs: G10 4bp, EM 12bp per trade + forward-roll cost.")
fig.tight_layout(); fx.save(fig, "06a_strategy_backtests"); plt.show()

roll = pd.DataFrame({k: R[k].rolling(36).mean() / R[k].rolling(36).std() * np.sqrt(12) for k in ["A. Carry (17 ccy)", "B. Trade balance (17 ccy)", "C. 50/50 blend A+B"]})
fig, ax = plt.subplots(figsize=(11.5, 3.8))
for k, col in zip(roll, [BLUE, ORANGE, INK]): ax.plot(roll.index, roll[k], color=col, lw=2.0 if k.startswith("C.") else 1.2, label=k)
ax.axhline(0, color=GRAY, lw=0.8); ax.legend(loc="lower left", ncol=3); ax.set_title("Rolling 3-year Sharpe ratio"); ax.set_ylabel("Sharpe")
fig.tight_layout(); fx.save(fig, "06b_rolling_sharpe"); plt.show()
''')
md("s6_read1")
md("s6_2")
code(r'''
grid = {}
P4 = fx.build_panel(trade_lag=4)
for q in (0.25, 1 / 3, 0.5):
    for reb in (1, 3):
        for lag_nm, tbx in [("trade lag 2m", tb), ("trade lag 4m", P4["trade"])]:
            wA, wB = tercile_w(carry, q=q), tercile_w(tbx, q=q)
            if reb == 3:
                wA = wA.iloc[::3].reindex(wA.index).ffill(); wB = wB.iloc[::3].reindex(wB.index).ffill()
            ra, _ = run(wA); rc, _ = run(0.5 * wA + 0.5 * wB)
            grid[(f"top/bottom {q:.0%}", f"rebalance every {reb}m", lag_nm)] = {"Carry Sharpe": fx.perf(ra)["Sharpe"], "Blend Sharpe": fx.perf(rc)["Sharpe"],
                                                                                "Blend max DD %": fx.perf(rc)["Max drawdown %"]}
print("Does the result survive reasonable changes to the recipe? (net Sharpe ratios)")
pd.DataFrame(grid).T
''')
code(r'''
wC = W["C. 50/50 blend A+B"]
hold = pd.DataFrame({"% of months LONG": 100 * (wC > 0.01).mean(), "% of months SHORT": 100 * (wC < -0.01).mean(),
                     "Avg weight": wC.mean(), "Weight now": wC.iloc[-1]}).sort_values("Avg weight")
fig, ax = plt.subplots(figsize=(11.5, 4.8))
wy = wC.resample("YE").mean().T.loc[hold.index]
im = ax.imshow(wy.values, aspect="auto", cmap=DIVERGING, vmin=-0.34, vmax=0.34)
ax.set_yticks(range(len(wy))); ax.set_yticklabels(wy.index); ax.set_xticks(range(len(wy.columns))); ax.set_xticklabels([d.year for d in wy.columns], rotation=90, fontsize=8)
ax.grid(False); ax.set_title("What strategy C holds: average yearly weight (blue = long, red = short)"); fig.colorbar(im, ax=ax, shrink=0.8)
fig.tight_layout(); fx.save(fig, "06c_strategy_c_holdings"); plt.show()
hold.round(2)
''')
md("s6_2_read")

md("s6_3")
code(r'''
gapj = (P["us_rate"] - P["rate"]["JPY"]) / 100
short_jpy = -rx["JPY"]
trend_up = (spot["JPY"] > spot["JPY"].rolling(12).mean())
buy_ops_m = yen_ops[yen_ops.direction == "buy JPY"].set_index("date").yen_tn.resample("ME").sum().reindex(spot.index).fillna(0)
cooldown = buy_ops_m.rolling(3, min_periods=1).max() > 0
volj = (-ds["JPY"]).rolling(6).std() * np.sqrt(12)
calm = volj < volj.expanding(36).median()
rules = {"Always short JPY": pd.Series(True, index=spot.index),
         "Short JPY if US-JP gap > 2%": gapj > 0.02,
         "Gap > 2% + USDJPY above 12m avg (trend)": (gapj > 0.02) & trend_up,
         "Gap > 2% + pause 3m after MoF buys yen": (gapj > 0.02) & ~cooldown,
         "Gap > 2% + only in calm (low-vol) regimes": (gapj > 0.02) & calm}
JR = {k: (v.astype(float).shift(1) * short_jpy).dropna()["2000":] for k, v in rules.items()}
jt = fx.perf_table(JR)[["Ann. return %", "Ann. vol %", "Sharpe", "Skew", "Worst month %", "Max drawdown %"]]
jt["% months invested"] = [100 * rules[k].shift(1)["2000":].mean() for k in jt.index]
print("Single-currency rule: SHORT yen vs USD (no costs; monthly signals, act next month)"); display(jt)

res_in = P["reserves"]["INR"]
long_inr = rx["INR"]
volr = long_inr.rolling(12).std()
irules = {"Always long INR": pd.Series(True, index=spot.index),
          "Long if RBI reserves rose over last 3m": np.log(res_in).diff(3) > 0,
          "Long if rupee vol below its median (calm)": volr < volr.expanding(36).median(),
          "Long if India trade balance improved (6m)": tb["INR"].diff(6) > 0,
          "Long if reserves rising AND calm": (np.log(res_in).diff(3) > 0) & (volr < volr.expanding(36).median())}
IR = {k: (v.astype(float).shift(1) * long_inr).dropna()["2000":] for k, v in irules.items()}
it = fx.perf_table(IR)[["Ann. return %", "Ann. vol %", "Sharpe", "Skew", "Worst month %", "Max drawdown %"]]
it["% months invested"] = [100 * irules[k].shift(1)["2000":].mean() for k in it.index]
print("Single-currency rule: LONG rupee vs USD (no costs)"); display(it)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.3))
for ax, D, base_col in [(a1, JR, BLUE), (a2, IR, ORANGE)]:
    for (k, s), col in zip(D.items(), [LIGHTGRAY, GRAY, base_col, VIOLET, AQUA]):
        c = 100 * s.cumsum(); ax.plot(c.index, c, color=col, lw=1.3, label=k)
    ax.axhline(0, color=GRAY, lw=0.8); ax.legend(loc="upper left", fontsize=7.5); ax.set_ylabel("cumulative log return, %")
a1.set_title("Short-yen rules"); a2.set_title("Long-rupee rules")
fig.tight_layout(); fx.save(fig, "06d_single_currency_rules"); plt.show()
''')
md("s6_3_read")
md("s6_4")

# ---------------------------------------------------------------- 7. snapshot
md("s7")
code(r'''
asof = spot.index[-1]
def latest(df):
    return df.ffill(limit=4).iloc[-1]
snap = pd.DataFrame({
    "Carry vs USD %": 100 * latest(carry),
    "Trade bal % of trade": latest(tb),
    "Current acct % GDP": latest(ca),
    "REER vs 5y avg %": 100 * latest(np.log(P["reer"] / P["reer"].rolling(60).mean())),
    "12m spot move %": 100 * latest(-ds.rolling(12).sum()),
    "UIP gap 36m %": 100 * latest(rx.rolling(36).sum()),
    "Spec positioning % OI": latest(pos),
    "Strategy C weight": W["C. 50/50 blend A+B"].iloc[-1],
}).sort_values("Strategy C weight")
Z = snap.apply(lambda c: (c - c.mean()) / c.std())
fig, ax = plt.subplots(figsize=(11.5, 7.2))
ax.imshow(Z.values.astype(float), cmap=DIVERGING, vmin=-2.2, vmax=2.2, aspect="auto")
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        v = snap.iloc[i, j]
        if pd.notna(v): ax.text(j, i, f"{v:+.2f}" if j == Z.shape[1] - 1 else f"{v:+.1f}", ha="center", va="center", fontsize=8, color=INK)
ax.set_xticks(range(Z.shape[1])); ax.set_xticklabels(Z.columns, rotation=30, ha="right", fontsize=8.5)
ax.set_yticks(range(Z.shape[0])); ax.set_yticklabels(Z.index); ax.grid(False)
ax.set_title(f"Signal dashboard as of {asof:%b %Y} (colour = z-score across currencies; blue = high)")
fx.source_note(ax, "Positive UIP gap = currency has done BETTER than UIP predicted over 36m. REER negative = cheap vs own 5y history. Positioning only for CME-listed ccys.")
fig.tight_layout(); fx.save(fig, "07a_signal_dashboard_now"); plt.show()
snap.round(2)
''')
md("s7_read")

# ---------------------------------------------------------------- 8. synthesis
md("s8")
md("s8_scorecard")
md("s8_interpretation")
md("s8_presentation")
md("s8_caveats")
md("s8_next")
md("s8_refs")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = ROOT / "research.ipynb"
nbf.write(nb, out)
print(f"wrote {out} ({len(cells)} cells)")
