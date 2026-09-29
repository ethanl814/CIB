"""All markdown for research.ipynb, keyed by cell id (see build_notebook.py).

Framing cells (theory, what-would-support / what-would-refute) were written
BEFORE looking at results. The "*_read" cells are the interpretation written
after running the notebook.
"""

PENDING = "> _Interpretation pending — run the notebook._"

TEXT = {}

TEXT["title"] = r"""
# Forex Drift Idea — Carry, Intervention & the Trade Balance
### CIB Quant Research · Japan & India case studies + 17-currency panel · data through Sept 2026

**The question.** Interest-rate differentials *should* pin down where exchange rates drift (uncovered interest parity, UIP). But countries often lean against that drift — Japan and the US bought yen in 2024 and 2026, India's RBI spent reserves and subsidised FCNR(B) deposits in 2013 and 2026. Is there a **repeatable, tradable pattern** in *when* currencies deviate from their UIP-implied path, and does a country's **trade position** (net importer vs. exporter) tell us which way policymakers will lean and whether it works?

This notebook is meant to be mined for slides: every figure is also saved as a PNG in `figures/`, and every section ends with a plain-English "what this means" box.
"""

TEXT["tldr"] = PENDING

TEXT["toc"] = r"""
### Contents
1. **Setup & data** — sources, coverage, conventions
2. **Primer** — UIP, carry, and the "forward premium puzzle" in one chart
3. **Japan deep dive** — rates vs. yen · trade balance vs. intervention direction · intervention event study · BoJ hikes · valuation · positioning
4. **India deep dive** — UIP by year · managed volatility · RBI reserves · FCNR(B) 2013 vs 2026 · carry P&L
5. **Cross-country panel (17 currencies)** — UIP regressions · carry vs crash risk · **the core trade-balance test** · who defends their currency · signal horse race · crash anatomy
6. **Strategy design & backtests** — candidate strategies, robustness, holdings, single-currency rules, retail implementation
7. **Where things stand now (Sept 2026)** — signal dashboard
8. **Synthesis** — theory scorecard, interpretation, presentation storyline, caveats, next steps, references
"""

TEXT["neutrality"] = r"""
### How to read this notebook (neutrality protocol)
The team's starting intuition is that *net importers with high interest rates* (currencies UIP says should depreciate) get defended by their central banks, creating a tradable deviation. To avoid confirmation bias:

* **Every theory is stated up front with what would support it *and* what would refute it**, before the results.
* The **same data and the same test** are applied to all 17 currencies — Japan and India are case studies, not the evidence base.
* Results are shown **raw and dollar-neutral**, **full-sample and split in two halves** (2000–12 / 2013–26), and **with/without outliers** (TRY, BRL).
* Signals are built with **publication lags** (trade data +2 months, reserves +1 month, annual current account from April of the following year), so nothing uses information that wasn't available at the time.
* We tested many variants. The more you try, the more likely something looks good by chance — so treat any single Sharpe ratio skeptically and look for results that are consistent across variants.

Interpretation boxes are marked **🔎 What this means** — those are my reading of the evidence; please challenge them.
"""

# ------------------------------------------------------------------ 1
TEXT["s1"] = r"""
---
## 1. Setup & data
All raw data is cached in `data/raw/` by `src/fetch_data.py` (re-run with `--force` to refresh). Helper code lives in `src/fxlib.py` so cells here stay short.
"""

TEXT["s1_sources"] = r"""
| Data | Source | Frequency | Used for |
|---|---|---|---|
| Spot FX (15 ccys) | Federal Reserve H.10 via FRED (`DEX…`) | daily | returns, event studies |
| Spot FX (TRY, IDR) | Yahoo Finance (bad ticks filtered) | daily | returns |
| Short rates | OECD MEI 3M interbank (`IR3TIB01…`), call-money (`IRSTCI01…`), ECB/SONIA fallbacks | monthly | carry / UIP |
| Merchandise trade | OECD MEI (`XTNTVA01…`, `XTEXVA01…`) | monthly | net importer/exporter |
| Current account | World Bank WDI (`BN.CAB.XOKA.GD.ZS`) | annual | alternative external-balance measure |
| FX reserves ex gold | IMF IFS via FRED (`TRESEG…`) | monthly | "leaning against the wind" |
| Real/nominal effective FX | BIS via FRED (`RB…BIS`, `NB…BIS`) | monthly | valuation |
| Japan intervention | **Japan MoF official daily record 1991–Jun 2026** + monthly releases | daily | event study |
| Speculator positioning | CFTC Commitments of Traders (legacy) | weekly | crowding |
| VIX | CBOE via FRED | daily | risk regime |

*Trade data for EUR ends 2023 and KRW mid-2025 in the OECD feed; those currencies drop out of trade-based signals after that (see table).*
"""

TEXT["s1_conventions"] = r"""
**Conventions (important — these trip people up):**
* Spot **S = units of foreign currency per 1 USD** (USDJPY = 157, USDINR = 95.8). **S up ⇒ foreign currency weaker.**
* **Carry / rate gap** = foreign short rate − US short rate. JPY carry is negative (Japan's rates are lower); INR carry is positive.
* **Carry-trade excess return** of being *long* the foreign currency, funded in USD, over month *t→t+1*: `rx = gap_t/12 − Δln S_{t+1}`. UIP says **E[rx] = 0**: whatever you earn in interest you lose in depreciation. A "short yen carry trade" is simply `−rx_JPY`.
* We use interbank / call-money rates as a proxy for forward points (covered interest parity). For INR this *understates* the true forward premium when dollar funding is tight — in 2026 banks paid ~280–300bp/yr to hedge USD into INR, versus a ~170bp policy-rate gap.
"""

# ------------------------------------------------------------------ 2
TEXT["s2"] = r"""
---
## 2. Primer: what UIP says vs. what happened
**Uncovered interest parity:** `E[ΔlnS] = i_foreign − i_US`. If US rates are 4% and Japan's 0%, investors should *expect* the yen to **appreciate** ~4%/yr — otherwise everyone would borrow yen and buy dollars for free money. In practice, high-rate currencies tend to depreciate **less** than UIP says (or even appreciate). Economists call this the **forward premium puzzle** (Fama 1984), and it is why the **carry trade** has historically paid.

The chart below compounds each month's rate gap from January 2012 to show the path UIP "predicted", and compares it with what actually happened.
"""
TEXT["s2_read"] = PENDING

# ------------------------------------------------------------------ 3
TEXT["s3"] = r"""
---
## 3. Japan deep dive
Theories tested in this section:

| # | Theory | Would be **supported** if… | Would be **refuted** if… |
|---|---|---|---|
| T1 | A country's trade position predicts **which way** it intervenes | Japan sold yen while a net exporter and bought yen once it became a net importer | Intervention direction unrelated to trade position |
| T3 | Intervention only "sticks" when monetary policy agrees | Episodes where the rate gap subsequently moved MoF's way show lasting moves; others fade | Interventions work (or fail) regardless of policy |
| T6 | Intervention clusters at round-number "lines in the sand" | Operations begin near 145/150/160 etc. | No pattern in trigger levels |
| T7 | The yen is extremely cheap (mean-reversion potential) | Real effective FX at historic lows | — (descriptive) |
| T5 | Crowded short-yen positioning precedes reversals | Most-short positioning quintile is followed by yen strength | No relationship, or the opposite |
"""
TEXT["s3_1"] = "### 3.1 The yen and the interest-rate gap"
TEXT["s3_1_read"] = PENDING
TEXT["s3_2"] = r"""
### 3.2 Trade position vs. **direction** of intervention (T1)
Japan is the cleanest natural experiment: it ran trade surpluses for decades, then flipped to persistent deficits after the 2011 earthquake (energy imports) — while keeping a **current-account surplus** thanks to income on its huge overseas investments. If trade position drives policy preferences, the *direction* of intervention should flip too.
"""
TEXT["s3_2_read"] = PENDING
TEXT["s3_3"] = r"""
### 3.3 Intervention event study (T3, T6)
For each intervention episode (operations clustered within 45 days), we measure how far USDJPY moved **in the direction the MoF wanted** after 1, 5, 20, 60 and 120 trading days. We also measure the **"policy tailwind"**: whether the US–Japan rate gap moved in MoF's favour over the following 3 months (narrowed when buying yen, widened when selling yen).

*Caveat: the tailwind uses future information — it's a diagnostic of **why** interventions work, not a trading signal by itself. Sample size is small (~25 episodes, most from the 1990s–2000s).*
"""
TEXT["s3_3_read"] = PENDING
TEXT["s3_4"] = r"""
### 3.4 2025–26 close-up: rate hikes that *weakened* the yen
The slides note the yen **fell ~0.5%** after the BoJ's 18 Sept 2026 hike to 1.25%. Is that a one-off or a pattern? If markets price hikes in advance, and the hikes are smaller than the Fed's moves, "buy the rumour, sell the fact" is plausible.
"""
TEXT["s3_4_read"] = PENDING
TEXT["s3_5"] = "### 3.5 Valuation: how cheap is the yen? (T7)"
TEXT["s3_5_read"] = PENDING
TEXT["s3_6"] = "### 3.6 Crowding: speculator positioning in yen futures (T5)"
TEXT["s3_6_read"] = PENDING

# ------------------------------------------------------------------ 4
TEXT["s4"] = r"""
---
## 4. India deep dive
India is the team's "net importer with a higher interest rate" archetype: persistent trade deficits (oil ≈ 89% imported), policy rates above the US, and a central bank known for smoothing the rupee.

| # | Theory | Supported if… | Refuted if… |
|---|---|---|---|
| T2 | **Managed carry** — RBI smoothing makes INR carry "up the stairs, down the elevator": steady gains, rare sharp losses | Low vol, positive carry return, negative skew, losses concentrated in stress episodes | INR moves like any free-floating EM currency |
| T1b | Net importers defend **against depreciation** more than they resist appreciation | Reserves fall sharply when INR weakens, rise less when it strengthens | Symmetric or no reserve response |
| T8 | The **FCNR(B) swap window** is a reliable turning point for the rupee (2013 precedent) | Rupee recovered strongly after both 2013 and 2026 windows opened | 2026 doesn't repeat 2013 |
| — | "INR normally depreciates ~4%/yr" (slide 11) | Long-run average close to 4% and close to the rate gap | Materially different |
"""
TEXT["s4_1"] = "### 4.1 The rupee's path, and UIP year by year"
TEXT["s4_1_read"] = PENDING
TEXT["s4_2"] = "### 4.2 Managed volatility (T2)"
TEXT["s4_2_read"] = PENDING
TEXT["s4_3"] = "### 4.3 RBI reserves: leaning against the wind (T1b)"
TEXT["s4_3_read"] = PENDING
TEXT["s4_4"] = r"""
### 4.4 FCNR(B) swap windows: 2013 vs 2026 (T8)
Both times, the RBI offered banks a **subsidised USD/INR swap** for new foreign-currency deposits from non-resident Indians, absorbing the hedging cost so banks could pay NRIs high dollar rates. 2013: announced 4 Sept 2013 (Rajan's first day), window to 30 Nov 2013, raised ~$34bn. 2026: deposits from 8 June 2026, window **closed early** on 31 Aug 2026 after raising **$52.3bn**.
"""
TEXT["s4_4_read"] = PENDING
TEXT["s4_5"] = r"""
### 4.5 Carry P&L decomposition: where do the returns actually come from?
Split each trade into **interest earned** vs. **spot FX gain/loss**. UIP says these should cancel out.
"""
TEXT["s4_5_read"] = PENDING

# ------------------------------------------------------------------ 5
TEXT["s5"] = r"""
---
## 5. Cross-country panel: does the pattern generalise?
Japan and India are two data points. To test the idea properly we need many currencies over many years. **Universe:** 9 G10 currencies (JPY, EUR, GBP, CHF, CAD, AUD, NZD, NOK, SEK) + 8 EM (INR, CNY, KRW, BRL, MXN, ZAR, TRY, IDR), monthly, 1999–2026.

| # | Theory | Supported if… | Refuted if… |
|---|---|---|---|
| T0 | UIP fails (baseline, well known) | Fama β < 1 | β ≈ 1 |
| T1 | **Team thesis:** net-importer high-yielders are "defended", so they deviate from UIP (depreciate *less*) and carry pays *more* on them | Net-importer β lower than net-exporter β; high-carry net importers earn more carry return | The opposite: net importers track UIP more closely / earn less |
| T1b | Net importers spend reserves to fight depreciation more than exporters | Defence intensity higher for deficit countries | No relationship |
| T2 | Carry = crash risk | Higher carry ↔ more negative skew; carry loses when VIX spikes | No relationship |
| T4 | **UIP "tension"** — a big cumulative gap between actual and UIP path predicts reversal | Currencies far *above* their UIP path subsequently underperform | No predictive power |
| T5 | Crowding predicts reversals | Contrarian positioning portfolio earns positive returns | Zero / negative |
| T7 | Valuation mean-reverts | Cheap-REER currencies outperform | Zero / negative |
"""
TEXT["s5_1"] = "### 5.1 The universe at a glance (2000–2026 averages)"
TEXT["s5_2"] = r"""
### 5.2 UIP ('Fama') regressions (T0, T1)
Regress next month's depreciation on today's rate gap. **β = 1** means UIP holds; **β = 0** means the rate gap tells you nothing about future FX moves (so the carry is "free"); **β < 0** means high-rate currencies actually appreciate.
"""
TEXT["s5_2_read"] = PENDING
TEXT["s5_3"] = "### 5.3 Carry vs. return vs. crash risk (T2)"
TEXT["s5_3_read"] = PENDING
TEXT["s5_4"] = r"""
### 5.4 ⭐ The core test: carry × trade balance (T1)
Each month, split currencies into **high carry / low carry** (above/below the median rate gap that month) and **net exporter / net importer** (sign of the 12-month trade balance, lagged 2 months). Then compare next-month carry-trade returns across the four buckets.

The team's thesis is about the **High carry × Net importer** bucket (currencies that UIP says should fall *and* that trade flows push down, but that central banks defend).
"""
TEXT["s5_4_read"] = PENDING
TEXT["s5_5"] = r"""
### 5.5 Who defends their currency? (T1b)
Monthly change in FX reserves regressed separately on **depreciation** and **appreciation** months, controlling for moves in the broad dollar (reserves held in EUR/JPY lose USD value when the dollar rises, which would otherwise look like "intervention").
"""
TEXT["s5_5_read"] = PENDING
TEXT["s5_6"] = r"""
### 5.6 Signal horse race (T4, T5, T7 vs. carry and trade balance)
Same recipe for every signal: each month go **long the top third** of currencies and **short the bottom third**, hold one month. No costs yet.
"""
TEXT["s5_6_read"] = PENDING
TEXT["s5_7"] = "### 5.7 Crash anatomy: what happens in carry's worst months?"
TEXT["s5_7_read"] = PENDING

# ------------------------------------------------------------------ 6
TEXT["s6"] = r"""
---
## 6. Strategy design & backtests
Candidates, all monthly-rebalanced and **net of assumed costs** (G10 4bp / EM 12bp per unit traded, plus a monthly forward-roll cost):

* **A. Carry** — long top-third rate gap, short bottom-third (the classic benchmark).
* **B. Trade balance** — long top-third net exporters, short bottom-third net importers.
* **C. 50/50 blend of A and B** — the "carry + external balance" idea.
* **D. Composite** — rank on z(carry) + z(trade balance).
* **E/F. G10-only** versions — what a retail trader can realistically execute with CME futures.
* **G. Long-only EM carry** — buy the 3 highest-yielders vs USD (what most retail "carry" products do).
"""
TEXT["s6_read1"] = PENDING
TEXT["s6_2"] = "### 6.2 Robustness and holdings"
TEXT["s6_2_read"] = PENDING
TEXT["s6_3"] = r"""
### 6.3 Single-currency rules for JPY and INR
Simple, explainable rules a retail trader could follow for the two case-study currencies. Each filter is added one at a time so you can see what it contributes.
"""
TEXT["s6_3_read"] = PENDING
TEXT["s6_4"] = PENDING

# ------------------------------------------------------------------ 7
TEXT["s7"] = r"""
---
## 7. Where things stand now (September 2026)
"""
TEXT["s7_read"] = PENDING

# ------------------------------------------------------------------ 8
TEXT["s8"] = "---\n## 8. Synthesis"
TEXT["s8_scorecard"] = PENDING
TEXT["s8_interpretation"] = PENDING
TEXT["s8_presentation"] = PENDING
TEXT["s8_caveats"] = PENDING
TEXT["s8_next"] = PENDING
TEXT["s8_refs"] = PENDING


# =============================================================================
# INTERPRETATION (written after running the notebook on data through 25 Sep 2026)
# =============================================================================
BOX = "#### 🔎 What this means\n"

TEXT["tldr"] = r"""
### TL;DR — what the data says (details and caveats below)
1. **UIP fails, as expected, and the failure is our raw material.** Across 17 currencies the "Fama β" is **0.25** (UIP says 1.0). Since 2012 USDJPY has ended **~96% (log) above** the path the rate gap implied; USDINR ended **~5% below** its UIP path, so rupee carry roughly broke even over 14 years.
2. **The team's exact thesis gets mixed-to-negative support in the cross-section.** High-yielding **net importers** are *not* the ones that pay. They track UIP **more** closely (β 0.41 vs −0.20 for exporters; interaction t = 2.0) and earn **less** carry (+0.6% vs +3.0%/yr dollar-neutral) with **much worse crash risk** (skew −1.4 vs −0.4). Central-bank defence doesn't stop net-importer currencies from eventually sliding.
3. **But the trade balance is a genuinely useful *second* signal.** Going long net exporters and short net importers earns **~2%/yr with *positive* skew**, and it holds in both halves of the sample. Its correlation with carry is **−0.32**, and it tends to make money in carry's crash months (8 of carry's 10 worst). A trade balance that is *improving vs. its own 5-year history* works even better (Sharpe 0.52), so it's not just a static country tilt.
4. **Best candidate strategy: a 50/50 blend of carry + trade balance** (strategy C). Net of costs it has **Sharpe 0.73, max drawdown −10%**, Sharpe 0.79 in 2000–12 vs 0.68 in 2013–26, and 0.61–0.79 across 12 recipe variations. Returns are modest unlevered (~2.9%/yr at 4% vol). A G10-only version a retail trader can run with CME futures gets Sharpe ≈ 0.47.
5. **Japan confirms the intuition about *which way* policymakers lean.** Every yen-*selling* intervention (1993–2011) happened while Japan ran trade surpluses; every yen-*buying* one since 2022 happened during trade deficits. But intervention alone doesn't fix the trend: 68% of episodes "worked" at 60 days, the April 2026 one failed, and BoJ hikes weakened the yen on the day in 4 of 6 cases.
6. **India: "managed carry" is real but no longer pays.** The RBI clearly spends reserves against depreciation (corr −0.50). The rupee is the 2nd-least-volatile currency in the panel (6.7% vol), and it fell less than UIP predicted in 17 of 25 years. But the big years (2008, 2011, 2013, 2018, 2022, 2025–26) wiped out the gains: long-INR carry has returned ~0.6%/yr since 2013. **A simple "only hold INR while RBI reserves are rising" filter roughly doubles the Sharpe (0.20 → 0.38) and halves the drawdown.**
7. **2026 is not 2013 (yet).** The 2013 FCNR(B) window marked the rupee's top (−8% during the window, −12% a year later). The 2026 window raised more money ($52bn vs $34bn) but the rupee is **unchanged** (+0.2% during the window). A key difference: in 2013 the Fed *delayed* tapering, while in 2026 the Fed is *hiking*.
"""

TEXT["s2_read"] = BOX + r"""
* **Yen:** UIP said the yen should have *strengthened* (from ~76 to ~60 per dollar) because Japan's rates were below America's. It did the opposite, weakening to ~157. That ~96% gap is the profit of the classic "borrow yen, buy dollars" carry trade, and the reason MoF/US Treasury are now intervening.
* **Rupee:** the rupee *did* depreciate, roughly as much as the rate gap predicted. The long-run drift is consistent with UIP; the carry trade's profit is just the small gap between the two lines. What differs from UIP is the *path*: long flat stretches (RBI smoothing) punctuated by sharp jumps (2013, 2018, 2022, 2025–26).
* **Takeaway for the pitch:** "FX drift follows rate gaps" is roughly true for India over long horizons and badly false for Japan. Our strategy has to explain *which* currencies deviate and *when*.
"""

TEXT["s3_1_read"] = BOX + r"""
* The yen's big moves line up with the US–Japan rate gap. 1999–2007: wide gap, yen weak. 2008–12: gap collapses to ~0, yen hits a record-strong 75. 2022–26: Fed hikes, gap ~4–5pp, yen weakens past 160. Correlation of 12-month changes is modest (0.23) because a lot of the action is in *levels*.
* This is the **opposite** of UIP. A *wider* gap in the dollar's favour came with a *weaker* yen, when UIP says it should mean yen appreciation ahead. That's the forward premium puzzle in its purest form.
* Implication: as long as the gap stays wide (Fed at 3.75–4.00%, BoJ at 1.25%), the carry motive for shorting yen persists. **A real reversal probably needs the gap to shrink** (Fed cuts or much faster BoJ hikes), not just intervention.
"""

TEXT["s3_2_read"] = BOX + r"""
* **Direction lines up with the trade position (supports T1 for Japan).** 1993–2011: Japan ran trade surpluses of ~2–20% of trade and **sold** yen in every intervention (¥35tn in 2003–04 alone) to protect exporters. From 2011 Japan's goods trade flipped to deficit, and every intervention since 2022 has been **yen-buying** (¥9tn 2022, ¥15tn 2024, ~¥27tn in 2026 including the reported July joint operation). A weak yen now mainly raises import (energy, food) costs.
* **But it's the *trade* balance, not the *current account*, that lines up.** Japan's current account stayed positive the whole time (2–5% of GDP) because of income on overseas investments. That's worth saying in the pitch: *"net importer"* should mean **goods trade**, which is what drives the domestic political pain of a weak currency.
* **Confounds to be honest about:** (1) The level of the yen matters too. Yen-buying happened when USDJPY was ~128–165, yen-selling below ~125. Weak-yen periods and trade deficits partly go together (energy bills are priced in dollars). (2) 1992 and 1997–98 were yen-buying episodes during surpluses, driven by the Asian crisis and a banking crisis. (3) It's one country. §5.5 checks whether the pattern generalises.
"""

TEXT["s3_3_read"] = BOX + r"""
* **Short-term, interventions "work".** Modern yen-buying operations move USDJPY 2–3% in the intended direction within 1–5 days. **68% of episodes** were still in the intended direction after 60 trading days, and all three of 2022–24 were (+9.5%, +2.3%, +8.4%).
* **But not always:** the **April–May 2026** operation (¥11.7tn at ~160) was fully reversed within 60 days (−2.1%). The yen went on to ~164, which triggered the larger **joint US–Japan** operation on 30–31 July 2026 (+2.9% at 20 days so far).
* **T3 ("it sticks only if policy helps") is *not* supported** by this crude test. The correlation between later rate-gap moves and 60-day success is **negative** (−0.44). Episodes with a policy tailwind succeeded 57% of the time vs. 79% without. This is probably confounded: panics like Sept 2001 and Sept 2022 bring both big FX reversals *and* policy moves the "wrong" way. With ~28 episodes, mostly from the 1990s, I wouldn't lean on it either way.
* **T6 (round-number lines):** trigger levels **drift upward** each cycle: ~145 (1998, 2022) → ~158–162 (2024) → ~160–164 (2026). There is no fixed line. The more useful rule is *"MoF acts after a fast move to a new multi-decade high"*, which is when a short-yen position is most exposed to a sudden 2–5% drop.
* **Tradable read:** intervention is a **risk to manage** for short-yen positions (see the "pause after intervention" rule in §6.3), not an alpha signal by itself.
"""

TEXT["s3_4_read"] = BOX + r"""
* The slide's observation generalises: **in 4 of the 6 BoJ hikes since 2024 the yen *weakened* on the day** (Mar 2024, Dec 2025, Jun 2026, Sep 2026). Hikes were well telegraphed and small relative to the US–Japan gap, and the guidance was often read as dovish ("buy the rumour, sell the fact").
* The two exceptions matter. **July 2024** (−2.2% on the day, −6.2% after 20 days) coincided with a weak US jobs report and the **August 2024 carry unwind**. **January 2025** was followed by a −10% move over 60 days. A BoJ hike moves the yen a lot only when it lines up with a *US* shock that squeezes the gap from both sides.
* Practical point for the presentation: BoJ hikes alone haven't been a good reason to cover a short-yen position.
"""

TEXT["s3_5_read"] = BOX + r"""
* In real (inflation-adjusted, trade-weighted) terms the yen is at the **very bottom of the BIS series** (0.3rd percentile since 1994), about **54% below** its 1994–2007 average.
* Cheapness is a **slow** force. §5.6 shows a REER-value signal had essentially no predictive power at one-month horizons in our panel. The yen has been "cheap" for four years and got cheaper. Treat this as the reason the *eventual* reversal could be large, not as a timing tool.
"""

TEXT["s3_6_read"] = BOX + r"""
* Speculators were heavily net short yen before the 2007 and August 2024 unwinds, and those unwinds were violent (USDJPY −12% from July to August 2024).
* **But extreme positioning is not a reliable contrarian signal (T5 not supported).** The most-short quintile was followed by *further* yen weakness on average (−0.24%/1m, −0.77%/3m), not a reversal. Crowding tells you the **size** of the move when a trigger arrives, not **when**.
* **Notable right now:** positioning swung from **−36% of open interest (late July 2026)** to **net long +19–22%** in mid-September. Speculative yen longs doubled in the week of the Fed hike (16 Sept) and BoJ hike (18 Sept). The crowded short that fuelled the 2024 unwind is not there today.
"""

TEXT["s4_1_read"] = BOX + r"""
* **The "INR depreciates ~4%/yr" rule of thumb (slide 11) is too high.** 2001–2025 the rupee fell **2.6%/yr on average** (median 2.5%), while the rate gap implied **4.5%/yr**. The rupee depreciated **less than UIP predicted in 17 of 25 years**, and that is the carry profit.
* The losses cluster: **2008 (+21%), 2011 (+17%), 2013 (+12%), 2018 (+9%), 2022 (+11%)**, and now **2025 (+4.9%) and 2026 YTD (+6.4%, 90.2 → 95.8)**. The last two are well above the ~1.8% gap, which has shrunk as US rates rose. So INR carry currently pays little and the rupee is falling faster than UIP. That is the "elevator" phase.
"""

TEXT["s4_2_read"] = BOX + r"""
* **T2 supported on volatility.** Since 2010 the rupee's realised vol is **6.7%**, second-lowest in the panel after the CNY (3.4%). That's about half of free-floating EM peers (BRL 14.5%, ZAR 14.9%, IDR 15.9%) and below even the yen (9.4%). The rolling chart shows the RBI keeps INR vol pinned below ~5% except during stress.
* **Vol compression before the break:** in 2023–24 the RBI held rupee vol around **2% (median; range 1–5%)**, effectively a soft peg. The 2025–26 slide began as that grip loosened. For a managed currency, *unusually* low vol is a sign of heavy intervention (and reserves being used), not of safety.
* Low vol makes INR carry *look* safe: a 2–4% rate gap on a 5% vol asset is an attractive ratio. The risk is in the jumps (monthly skew +0.3, i.e. a fat tail of rupee *depreciation*). This is the textbook profile of "picking up nickels in front of a steamroller".
"""

TEXT["s4_3_read"] = BOX + r"""
* **T1b supported for India.** 3-month reserve changes and 3-month depreciation are strongly negatively correlated (**−0.50**). When the rupee is under pressure the RBI sells dollars, as in 2008, 2013, 2018, 2022 and 2024–26. It rebuilds reserves in calm, inflow-heavy periods.
* This also makes reserves a **real-time stress gauge**. Falling reserves mean the RBI is actively defending and pressure is building. §6.3 turns this into a filter for the long-INR trade.
"""

TEXT["s4_4_read"] = BOX + r"""
* **2013:** the window opened a week after the rupee's all-time low at the time (68.8). The rupee rallied **8.3% during the window** and was **~12% stronger a year later**. It is widely cited as the policy that ended the taper tantrum. But the timing was lucky too: on **18 Sept 2013 the Fed surprised by *not* tapering**, a major global tailwind.
* **2026:** the window raised **more** money ($52.3bn, closed early on 31 Aug) and the rupee is **flat** (95.0 → 95.8). The global backdrop is the opposite of 2013: the Fed *hiked* on 16 Sept 2026, oil is ~$100, and portfolio outflows continue.
* **T8 verdict: not supported so far.** The same tool worked in 2013 alongside a global tailwind and hasn't worked in 2026 without one. This fits the Japan evidence: **domestic defence buys time; global rates decide the trend.**
* One more angle: the FCNR deposits are **3–5-year** dollar liabilities that the RBI has swapped. When they mature (2029–31) the RBI must deliver dollars back, a known future outflow the market may start to price.
"""

TEXT["s4_5_read"] = BOX + r"""
* **Long INR** (2000–26): the rupee paid **+114% (log) in interest** but lost **−79% on the exchange rate**, for a total of **+35%**. That's 1.3%/yr at 6.5% vol (Sharpe 0.20), and **almost nothing since 2018**.
* **Short JPY** (2000–26): **+53% interest *plus* +43% from the yen weakening**, for **+96%** (Sharpe 0.34 overall, **0.66 since 2013**). Here both parts of the trade paid, which is exactly what UIP says shouldn't happen.
* So the *funding* side (short yen) has been the better half of the carry trade for a decade. Since 2013, the rupee's high yield has been almost completely offset by its depreciation.
"""

TEXT["s5_2_read"] = BOX + r"""
* **T0 confirmed:** every currency's β is below 1, and the pooled β is **0.25** (t = −5.1 against UIP). Many are negative (high-rate currencies *appreciated* on average). The point estimates are noisy per currency; the pooled result is the reliable one.
* **T1 (team thesis) — the opposite of what we hypothesised.** Net importers have a **higher** β (**0.41**) than net exporters (**−0.20**). The interaction term is +0.61 (t = 2.0), and the current-account split shows the same pattern. **Deficit currencies follow UIP *more* closely**: when they offer high rates, they tend to depreciate by more of the rate gap. Surplus currencies with high rates tend to hold up or appreciate.
* Economic intuition: a deficit country *needs* capital inflows, and part of its high rate is **compensation for depreciation/crash risk**, which then shows up. A surplus country with high rates (BRL and IDR in commodity booms, NOK) is paying a rate that isn't needed to fund an external gap, so the carry is closer to "free".
"""

TEXT["s5_3_read"] = BOX + r"""
* **T2 confirmed across currencies:** a higher average rate gap goes with more negative skew (corr **−0.87** across all 17, −0.61 excluding TRY). High-yielders earn their premium by occasionally crashing.
* Average carry vs. average return is **~0 with TRY** (Turkey's 19% average rate gap came with a −4%/yr return) but **0.87 excluding TRY**. One hyperinflationary outlier can erase the whole premium. That's an argument for **diversified** carry and against concentrated single-currency carry.
"""

TEXT["s5_4_read"] = BOX + r"""
**This is the most important table for the thesis.**
* **The team's bucket (High carry × Net importer) is the *worst* way to harvest carry.** Dollar-neutral it earned **+0.6%/yr** vs **+3.0%/yr** for high-carry net exporters, with **skew −1.40 vs −0.44** and a worst month of **−27% vs −21%**.
* **Robust:** the exporter-minus-importer spread among high-carry currencies is positive in **both halves** (+2.2pp 2000–12, +2.9pp 2013–26), **excluding TRY** (+1.5pp) and **TRY & BRL** (+0.8pp), in **G10 only** (+0.7pp) and **EM only** (+2.9pp), and with the **current account** instead of trade (+2.3pp; G10-only CA is the one exception at −0.4pp). The effect is largest in EM.
* **Reframing the thesis:** central banks of net importers *do* defend (§4.3, §5.5), but the defence doesn't create a free lunch. It **delays** depreciation and then **concentrates** it into crashes. The profitable deviation from UIP is in the **net exporters**, whose high rates aren't needed to attract capital.
* So the pitch shifts from *"bet on defended net importers"* to ***"harvest carry where the trade balance supports it, avoid it where the trade balance undermines it"***, which is §6's strategy.
"""

TEXT["s5_5_read"] = BOX + r"""
* **Statistically significant downside defenders** (filled dots): **CNY, JPY, INR, KRW**. These are managed or intervention-prone regimes. Free floaters (MXN, ZAR, BRL, GBP, CAD) show nothing, as they should.
* **T1b (net importers defend more) is *not* supported in the cross-section.** The correlation between defence intensity and trade balance is +0.26 (if anything, exporters like CNY defend more), and India (deficit) and China (surplus) both defend. **Defence depends on the policy regime more than the trade position.** The trade position (Japan §3.2) shapes *which direction* a country cares about; whether it acts depends on its reserves and institutions.
* Caveats: 12 countries, monthly data, and reserve changes include interest income and non-USD valuation even after the USD control. AUD's high point estimate is not significant.
"""

TEXT["s5_6_read"] = BOX + r"""
* **Carry is the strongest single signal** (Sharpe 0.61, t = 3.2), but it has faded: 6.8%/yr in 2000–12 vs 2.9%/yr in 2013–26.
* **Trade-balance signals are the only other ones that work, and consistently:** level (Sharpe 0.35), **vs. own 5-year average (0.52, t = 2.6)** and 12-month change (0.33). All are positive in both halves. The "vs own 5-year average" version only uses each country's *own* time variation, which rules out "it's just always long Brazil, short UK". An **improving** trade balance predicts currency outperformance.
* **Current account does *not* work** (−0.27). It sorts differently: it goes long low-yielders with big investment-income surpluses (CHF, JPY, SEK) and so fights carry. For FX returns, **goods trade matters, not total external income.** That matches the Japan story.
* **Failed signals:** 12m/3m momentum, REER value, the UIP-"tension" reversal (T4) and contrarian positioning (T5) all have Sharpe ≈ 0 or negative here. Momentum and value work in other studies over longer samples and more currencies. Our 17-currency, 27-year panel just doesn't show them, so I'd leave them out of the pitch.
* **Diversification:** carry and trade balance are **−0.32 correlated**, which is what makes combining them attractive.
"""

TEXT["s5_7_read"] = BOX + r"""
* Carry's worst months are the famous risk-off episodes (Mar 2020, Oct 2008, Aug 2018 Turkey, May 2006, Aug 2015 China devaluation). Its monthly correlation with ΔVIX is **−0.31**, so carry is effectively short volatility.
* **In 8 of carry's 10 worst months the trade-balance portfolio made money** (e.g. +6.2% in Oct 2008, +5.7% in Aug 2018), and its correlation with ΔVIX is ~0. The trade-balance signal naturally shorts the deficit currencies that crash hardest in risk-off.
* A simple VIX filter (exit carry when VIX is in its top 20% vs. the past 10 years) was tried in exploratory work. It cut drawdowns but cut returns more (Sharpe 0.61 → 0.51), so it's left out. The trade-balance leg is a better "hedge" than a timing filter.
"""

TEXT["s6_read1"] = BOX + r"""
* **C (50/50 carry + trade balance) is the standout on risk-adjusted terms:** Sharpe **0.73** net of costs vs 0.44 for carry alone, max drawdown **−10%** vs −18%, worst month −6% vs −10%. It also holds up out of sample: **0.79 (2000–12) → 0.68 (2013–26)**, while carry alone decayed from 0.53 to 0.34.
* **Returns are small unlevered** (~2.9%/yr at 4% vol). To be interesting you'd **scale to a volatility target** (e.g. 8–10% vol ≈ 2–2.5× notional → roughly 6–7%/yr before financing). Leverage multiplies the tail risk too, so the −10% max drawdown becomes ~−25%.
* **D (single composite score)** is worse than the 50/50 blend. Keeping the two signals as separate sleeves diversifies better than merging them.
* **G (long-only EM carry)**, what most retail "carry" products do, had the highest raw return but **Sharpe 0.09 since 2013** and a −31% drawdown. It's mostly a bet on EM vs the dollar.
* **H\*** (the post-hoc "trade vs own history" variant) nets Sharpe 0.60, *below* C once its higher turnover is costed. Good news for honesty: the pre-specified strategy wins.
* **Last 5 years have been unusually good** for all versions (Sharpe 0.9–1.4), because of the high-rate era. Don't extrapolate that.
"""

TEXT["s6_2_read"] = BOX + r"""
* **Robustness:** C's Sharpe stays in a **0.61–0.79** band across long/short cut-offs (25/33/50%), rebalancing (monthly/quarterly) and trade-data lags (2 or 4 months). Carry alone stays at 0.40–0.48. The blend beats carry in all 12 variants, which suggests the result isn't an artifact of one parameter choice.
* **What it holds:** structurally **short GBP, JPY, INR, TRY** (100% of months) and usually NZD, SEK, CHF, EUR. Structurally **long BRL, IDR, NOK**, often ZAR and MXN. CNY/KRW/AUD rotate.
* **Heads-up for the pitch:** the model is **short INR**, the opposite of "long the defended net importer". INR's carry is middling, and its trade balance is the worst in the panel (−27% of trade). The strategy fits the Japan leg of the story (short yen) and treats India as the cautionary tale.
* Concentration risk: the long book leans on commodity-exporting EMs (BRL, NOK, IDR, ZAR). A global commodity bust is the scenario to stress-test.
"""

TEXT["s6_3_read"] = BOX + r"""
**Short-yen rules** (small samples, no costs, so treat as illustrative):
* *Always short JPY* made 3.6%/yr but with a **−35%** drawdown (2007–12).
* Only shorting when the **US–Japan gap > 2%** keeps most of the return (2.7%/yr) at lower vol (Sharpe 0.42, drawdown −24%). This is the most defensible rule: it's the carry logic itself.
* Adding **"pause 3 months after MoF buys yen"** lifts the Sharpe from 0.42 to **0.52** (3.0%/yr) by skipping the choppy post-intervention months. The max drawdown is unchanged (−24%; it comes from 2007–08, not from interventions). The evidence rests on the handful of 2022–26 episodes, so it's thin, but it's also the rule with the clearest economic logic.
* Trend (0.28) and low-vol (0.22) filters **hurt**. Don't add them.

**Long-rupee rules:**
* *Always long INR* made 1.3%/yr, Sharpe 0.20, drawdown −21%.
* **"Only when RBI reserves rose over the last 3 months"** raises the Sharpe to **0.38** and halves the drawdown (**−10%**), while staying invested 70% of the time. This is the cleanest "use the central bank's own behaviour" signal we found, and it follows directly from §4.3.
* Vol and trade-improvement filters don't help for INR on their own.
"""

TEXT["s6_4"] = r"""
### 6.4 Retail implementation guide (for the "how would someone actually do this" slide)
| Question | Suggested answer (based on the evidence above) |
|---|---|
| **What to trade** | **Core:** strategy C/F, a basket long top-third / short bottom-third by (a) rate gap and (b) trade balance, 50/50. **Satellite:** short JPY vs USD when the US–JP gap > 2%, paused 3 months after MoF yen-buying (Sharpe 0.52 vs 0.38 always-short); long INR only while RBI reserves rose over the last 3 months (Sharpe 0.38 vs 0.20). |
| **Instruments** | **G10:** CME currency futures, including **micro** contracts for JPY, EUR, GBP, AUD, CAD, CHF (carry is embedded in the futures price, so no broker financing spread). **EM:** CME BRL/MXN/ZAR futures, or spot FX at a broker with competitive financing. **INR:** not practical for most US retail. Onshore/NDF access is limited and INR futures trade mainly on Indian exchanges (NSE / GIFT City); NRIs can use FCNR(B)/NRE deposits. *Verify current product availability before presenting.* |
| **Rebalancing** | Monthly (quarterly also works; §6.2). Use trade data with a 2-month lag, rates as of month-end. |
| **Sizing** | Volatility-target the whole book (e.g. 8% annualised) using trailing 6–12m realised vol; cap any single currency at ~20% of gross. |
| **Holding period / horizon** | Signals are slow; evaluate over **3–5 years**, not months. Carry had multi-year flat periods (2013–19). |
| **When it works best** | Stable or falling global volatility, wide cross-country rate dispersion, and trade balances that diverge clearly across countries. |
| **When to be careful** | Global risk-off (VIX spikes), commodity crashes (the long book is commodity-heavy), coordinated interventions (JPY), and the approach to an FCNR-style defence *without* a global tailwind (INR 2026). |
| **Costs that kill retail carry** | Broker financing spreads of 1–2%/yr on spot FX can wipe out a 2–3% carry. Prefer futures or brokers that pass through benchmark rates. |
| **Realistic expectations** | Unlevered ~3%/yr at ~4% vol. At 8–10% vol, perhaps 5–7%/yr before fees, with drawdowns of ~20–25% in a 2008-type year. |
"""

TEXT["s7_read"] = BOX + r"""
* **Strategy C today:** **long BRL, ZAR (+0.18 each), NOK (+0.10), IDR, MXN (+0.08)**; **short NZD, GBP (−0.12), SEK, CAD, JPY (−0.10), INR, TRY (−0.04)**. (EUR, KRW and MXN have stale OECD trade data, so they sit only in the carry sleeve.)
* **Yen:** carry still says short (gap −2.8pp). But the yen is **14% cheap vs its own 5-year average**, has **undershot its UIP path by ~17% over 36 months** (the largest shortfall in the panel), and **speculators are now net long** (+19% OI). Two rounds of intervention in 2026 (the second coordinated with the US) add event risk. **The carry case is intact; the asymmetry has worsened.** The satellite rule (gap > 2%, paused 3 months after MoF yen-buying) is **flat through October 2026** and re-enters in November if the gap is still > 2%.
* **Rupee — the signals disagree, which is itself informative.** The cross-sectional model is **short INR**: worst trade balance in the panel (−28% of trade), a thin rate gap (+1.7pp), and 7.6% weaker over 12 months. It is also **~10% cheap** in REER terms. Meanwhile the **RBI-reserves filter has just switched ON**: July reserves jumped from $566bn to $588bn. But that jump is largely **FCNR(B) swap inflows**, i.e. borrowed dollars the RBI owes back in 3–5 years, not organic strength. I'd treat it as a weak "on" signal and watch whether reserves keep rising once the window's inflows stop (August–October prints).
"""

TEXT["s8_scorecard"] = r"""
### 8.1 Theory scorecard
| # | Theory | Verdict | Key evidence |
|---|---|---|---|
| T0 | UIP fails (baseline) | ✅ **Supported** | Pooled β 0.25 (t = −5.1 vs 1); USDJPY 96% above UIP path since 2012 |
| T1 | Net importers' high rates are *defended*, so carry pays more on them | ❌ **Refuted (reversed)** | Net-importer β 0.41 vs exporter −0.20; high-carry importers earn +0.6% vs +3.0%, skew −1.40 vs −0.44; robust across 13/14 variants |
| T1 (Japan) | Trade position sets the **direction** of intervention | ✅ **Supported (1 country)** | All yen-selling in surplus years (1993–2011); all yen-buying in deficit years (2022–26); CA stayed positive throughout |
| T1b | Net importers defend against depreciation more | ⚠️ **Mixed** | Strong for INR (−0.50 corr); cross-section corr +0.26: defenders are managed regimes (CNY, JPY, INR, KRW) regardless of trade |
| T2 | Managed/high carry = "stairs up, elevator down" | ✅ **Supported** | Carry vs skew −0.87; INR vol 6.7% with big losing years; carry corr with ΔVIX −0.31 |
| T3 | Intervention sticks only with a policy tailwind | ❌ **Not supported (small n)** | Corr −0.44 across 28 episodes; likely confounded |
| T4 | UIP "tension" predicts reversal | ❌ **Not supported** | Sharpe −0.04 (36m); −0.05 (60m) |
| T5 | Crowded positioning predicts reversal | ❌ **Not supported** | Contrarian Sharpe −0.16; most-short yen quintile followed by *more* weakness |
| T6 | Interventions cluster at fixed round numbers | ⚠️ **Partly** | Triggers drift upward each cycle (145 → 160 → 164); "new multi-decade high" fits better than a fixed line |
| T7 | Cheap currencies mean-revert | ⚠️ **Not at 1–12m horizons** | REER-value Sharpe ≈ −0.1; yen at record cheapness and still falling |
| T8 | FCNR(B) windows mark rupee bottoms | ⚠️ **1 for 2 so far** | 2013: −12% USDINR a year later; 2026: flat so far |
| **New** | **Trade balance is a stand-alone FX signal and diversifies carry** | ✅ **Supported** | Sharpe 0.35–0.52 across three constructions, both halves; −0.32 corr with carry; positive in 8 of carry's 10 worst months |
"""

TEXT["s8_interpretation"] = r"""
### 8.2 My interpretation
**The original idea contains the right ingredients, combined the other way round.** We started from: *"rates imply drift, governments fight it, net importers are the ones fighting — trade that."* The data agrees that (a) rate-implied drift doesn't happen reliably, (b) governments fight it, and (c) the trade position tells you which side they fight on. But **fighting doesn't make the net importer's currency a good buy.** Defence smooths the path and then fails in a crash, and deficit currencies end up depreciating roughly in line with their rate gap (β closer to 1). The profitable deviation from UIP is in the **surplus** high-yielders, which don't need their high rates to attract capital.

**So the investable version of the thesis is:**
> *Harvest the interest-rate gap only where the trade balance supports the currency; fund it with the currencies whose trade balance is deteriorating. When a net-importer's central bank starts spending reserves, that's a warning, not a floor.*

This is a two-factor currency strategy, **carry + external balance**, where the second factor is both a return source and a crash hedge. It gives a clean story, a robust backtest (Sharpe ~0.7 net, both halves, 12 variants) and a direct link to the two case studies:
* **Japan** = the funding leg. Low rates, a goods-trade deficit and a cheap, heavily-shorted currency: the short-yen trade *worked* for a decade. Now intervention (including the rare US joint action) and positioning have made it riskier, which our satellite rule handles with a post-intervention pause.
* **India** = the cautionary tale. The team's archetype (high rate, net importer, defended) delivered the "stairs up, elevator down" profile. Its long-run return is barely positive, and the 2026 defence hasn't worked yet. The one thing that improved it was **following the central bank's reserves**: be long only while the RBI is *accumulating*, not defending.

**What I'm least sure about:** (1) the trade-balance signal partly overlaps with a commodity-exporter tilt (BRL, NOK, IDR, ZAR), even though the "vs own history" version suggests it's more than that; (2) the intervention analyses rest on a few dozen episodes from one country; (3) our carry proxy uses interbank rates, not forward points, which likely understates INR carry during stress (2026 hedging cost ~280–300bp vs a ~170bp rate gap).
"""

TEXT["s8_presentation"] = r"""
### 8.3 Suggested presentation storyline (figures in `figures/`)
1. **Hook — "rates should predict FX, but…"** → `02_uip_vs_actual_jpy_inr.png` (yen 96% off its UIP path; rupee roughly on it).
2. **Governments fight the drift, and the trade balance says which way** → `03b_japan_trade_vs_intervention_direction.png`.
3. **Does fighting work?** → `03c_intervention_event_study.png` + `03e_2025_2026_closeup.png` (works for weeks; April 2026 failed; BoJ hikes weaken the yen) and `04e_fcnr_2013_vs_2026.png` (2013 worked with a Fed tailwind; 2026 hasn't).
4. **India = stairs up, elevator down** → `04b_inr_actual_vs_uip_by_year.png` + `04f_carry_decomposition_inr_jpy.png`.
5. **Test the thesis on 17 currencies — the twist** → `05c_two_by_two_carry_trade_balance.png` (net importers are the *worst* carry) + `05a_fama_betas.png`.
6. **The trade balance is its own signal and hedges carry** → `05f_signal_horse_race.png` + `05e_signal_correlations.png` + the worst-months table (§5.7).
7. **Strategy** → `06a_strategy_backtests.png` + `06b_rolling_sharpe.png` + robustness table (§6.2); rules and instruments from §6.4.
8. **Where we are now** → `07a_signal_dashboard_now.png`: long BRL/ZAR/NOK, short GBP/NZD/JPY/INR; the yen trade is paused post-intervention; INR signals conflict (reserves up on FCNR inflows, fundamentals weak).
9. **Risks & what would change our mind** → §8.4.
"""

TEXT["s8_caveats"] = r"""
### 8.4 Caveats & limitations (please read before presenting numbers)
* **Carry proxy.** We use 3M interbank / call-money rates instead of actual forward points. Covered interest parity mostly holds for G10, but EM forwards (especially INR, TRY, BRL, IDR) can diverge a lot in stress, and onshore/offshore (NDF) markets differ. Real INR carry in 2026 was larger than our proxy.
* **Data gaps.** OECD trade data ends 2023 for the euro area and mid-2025 for Korea (these drop out of the trade signal). TRY and IDR spot come from Yahoo Finance (cleaned for bad ticks). Pre-2002 Japanese 3M rates are call-money rates.
* **Look-ahead control is approximate.** We lag trade by 2 months, reserves by 1, annual current account to April of the next year. Some data gets revised after first release; we use today's vintage.
* **Costs are stylised** (G10 4bp, EM 12bp per trade + roll). Retail spreads and financing can be much worse. Futures help.
* **Multiple testing.** We tried ~10 signals and ~8 strategies plus variants. C was specified before seeing strategy results, and its consistency across halves and variants is reassuring, but a Sharpe of 0.7 on ~27 years of data has wide error bars (roughly ±0.4).
* **Small event samples.** ~28 Japanese intervention episodes, 6 BoJ hikes, 2 FCNR windows. Treat those sections as case evidence, not statistics.
* **2026 intervention amounts** for 30–31 July are estimates from MoF's monthly total (¥15.4tn for 30 Jul–26 Aug) and press reports. Daily detail will appear in MoF's Q3 release (early November).
* **Regime risk.** The carry and trade-balance relationships held across 2000–2026, but that period includes zero-rate policy, QE and a commodity super-cycle. A different regime (e.g. a sustained dollar bear market) could change them.
"""

TEXT["s8_next"] = r"""
### 8.5 Suggested next steps for the team
1. **Replace rate-gap carry with forward points** for G10 (e.g. from futures basis) and check the INR NDF vs onshore forward.
2. **Extend the universe** to ~30 currencies (PLN, HUF, CZK, CLP, COP, PHP, THB, MYR, ILS, SGD) to test the trade-balance result out of sample. This is the single best robustness check.
3. **Separate commodity from non-commodity exporters** to see how much of the trade signal is a commodity-cycle bet.
4. **Replicate with CME futures prices** (JPY, EUR, GBP, AUD, CAD, CHF, MXN, BRL, ZAR) to get a genuinely tradable retail backtest including roll.
5. **Monitor live:** MoF's Q3 intervention release (early Nov 2026), RBI weekly reserves (the INR filter), and the monthly strategy weights from §7.
"""

TEXT["s8_refs"] = r"""
### 8.6 References & sources
**Academic**
* Fama, E. (1984). "Forward and spot exchange rates." *Journal of Monetary Economics* — the forward premium puzzle.
* Lustig, H., Roussanov, N. & Verdelhan, A. (2011). "Common risk factors in currency markets." *Review of Financial Studies*.
* Brunnermeier, M., Nagel, S. & Pedersen, L. (2008). "Carry trades and currency crashes." *NBER Macroeconomics Annual*.
* Della Corte, P., Riddiough, S. & Sarno, L. (2016). "Currency premia and global imbalances." *Review of Financial Studies* — external-imbalance risk premium, closely related to our trade-balance signal.
* Menkhoff, L., Sarno, L., Schmeling, M. & Schrimpf, A. (2012). "Carry trades and global foreign exchange volatility." *Journal of Finance*.
* Asness, C., Moskowitz, T. & Pedersen, L. (2013). "Value and momentum everywhere." *Journal of Finance*.

**Data**: FRED (Federal Reserve H.10, OECD MEI, IMF IFS, BIS), Japan Ministry of Finance intervention records, CFTC Commitments of Traders, World Bank WDI, Yahoo Finance.

**2026 events (news)**
* CNBC — [U.S., Japan confirm coordinated yen intervention (3 Aug 2026)](https://www.cnbc.com/2026/08/03/yen-intervention-us-japan-trump-bessent-katayama.html); [U.S. Treasury intervenes to support yen (1 Aug 2026)](https://www.cnbc.com/2026/08/01/us-treasury-intervenes-to-support-yen-after-japan-steps-in-ft.html)
* Wikipedia — [2026 U.S.–Japan yen intervention](https://en.wikipedia.org/wiki/2026_U.S.%E2%80%93Japan_yen_intervention)
* Bloomberg — [BOJ data point to $34bn Japan FX intervention (3 Aug 2026)](https://www.bloomberg.com/news/articles/2026-08-03/boj-data-point-to-34-billion-japanese-fx-intervention-on-friday)
* CNBC — [BoJ raises rates to 1.25%, 31-year high (18 Sep 2026)](https://www.cnbc.com/2026/09/18/japan-raises-rates-30-year-high-yen-jgb.html); [BoJ hikes to 1% (16 Jun 2026)](https://www.cnbc.com/2026/06/16/boj-rate-hike-historic-inflation.html); [BoJ to 0.75% (19 Dec 2025)](https://www.cnbc.com/2025/12/19/bank-of-japan-boj-rate-cpi-inflation-takaichi-ueda.html)
* Business Standard — [RBI opens FCNR(B) swap window (9 Jun 2026)](https://www.business-standard.com/finance/news/rbi-opens-fcnr-b-swap-window-to-attract-foreign-currency-deposits-126060900723_1.html); [FCNR(B) window explained / early close (17 Aug 2026)](https://www.business-standard.com/finance/news/rbi-fcnr-b-window-nri-dollar-swap-deposit-scheme-deadline-forex-126081700609_1.html)
* Bloomberg — [RBI intervenes as rupee drops to record low (20 May 2026)](https://www.bloomberg.com/news/articles/2026-05-20/inr-usd-indian-central-bank-intervenes-as-rupee-drops-to-record-low)
* Japan MoF — [Foreign Exchange Intervention Operations](https://www.mof.go.jp/english/policy/international_policy/reference/feio/index.html)
"""


# =============================================================================
# FINAL PROPOSAL (top-of-notebook summary for slides)
# =============================================================================
TEXT["final"] = r"""
---
## ⭐ Final proposal: the trades we'd put forward
*One-page summary for the presentation. Everything below is computed from the same data and backtest engine as §6 (`src/fxlib.py`), **net of costs**.*

| | Trade | Rule (checked once a month) | Why it should work | How to trade it | Grade |
|---|---|---|---|---|---|
| **1** | **CORE: carry + trade-balance basket** | Rank 17 currencies. **50%:** long top third by interest-rate gap vs USD, short bottom third. **50%:** long top third by trade balance (net exporters), short bottom third (net importers). Rebalance monthly. | Carry is the classic FX premium (UIP fails, §5.2). The trade balance separates high-yielders that hold up (exporters) from ones that crash (importers, §5.4), and it made money in 8 of carry's 10 worst months (§5.7). | CME futures / FX forwards. **Retail:** G10-only version (1b) with CME micro futures. Vol-target ~8%. | **Primary recommendation** |
| **2** | **SATELLITE: short yen, with an intervention pause** | Short JPY vs USD while the US–Japan short-rate gap is **> 2pp**. **Stand aside for 3 months** after any MoF yen-buying. | The widest, most persistent UIP failure in the panel (§2, §3.1). Interventions cause sharp 2–5% reversals that usually fade (§3.3), so avoid the post-intervention window rather than fight it. | CME yen futures (6J / micro MJY), or short yen ETF/spot. | **Secondary**: risk-managed, few events |
| **3** | **WATCH: long rupee only while the RBI is accumulating** | Long INR vs USD only if RBI FX reserves rose over the last 3 months. | The RBI spends reserves to defend the rupee (§4.3). Falling reserves = stress building, rising = calm inflows. | Hard for US retail (INR futures are mainly on NSE / GIFT City; NRIs via FCNR/NRE deposits). | **Monitor, not a trade**: weak recent record |

The table and charts below are the evidence; the notes after them explain how to read it.
"""

TEXT["final_after"] = r"""
#### How these were backtested
* **Period and frequency:** monthly, **Jan 2000 – Sep 2026** (~320 months), 17 currencies (9 G10 + 8 EM).
* **No look-ahead:** each month's decision uses only data published by then (trade data lagged 2 months, reserves 1 month, rates as of month-end). Positions are set at month-end *t* and earn the return over month *t+1*.
* **Return = interest earned + currency move:** the full P&L of holding the currency against USD (`rx = rate gap/12 − Δlog spot`), not just the price change.
* **Costs:** 4bp (G10) / 12bp (EM) per unit traded plus a monthly forward-roll cost (0.5bp / 2bp). The same cost model is applied to all three trades and their benchmarks.
* **Benchmarks:** each rule is shown next to its naive version (carry only, always short yen, always long rupee), so the value added by the rule is visible.
* **Stability checks (§6.2):** the core trade's Sharpe stays in a **0.61–0.79** range across 12 variations (how many currencies to hold, monthly vs quarterly rebalancing, 2- vs 4-month trade-data lag). The two halves of the sample (2000–12 / 2013–26) are shown separately.

#### Honest verdict per trade
> **Read the charts correctly: the rules win on *risk*, not on raw return.** Unlevered, carry-only ends *higher* than the core trade (+145% vs +118%), and always-short-yen ends higher than the yen rule (+144% vs +111%). The rules earn a bit less but with much smaller swings. **At equal risk** (scaling the core to carry's 7.7% volatility) the core would have returned about **5.6%/yr vs 3.4%/yr** for carry alone, with a similar worst drawdown (about -19% vs -18%). Same risk, roughly 65% more return: that comparison is the fair one for the pitch.

* **Core (1):** the strongest result. Sharpe **0.73** vs 0.44 for carry alone, **max drawdown −10% vs −18%**, similar in both halves (0.79 / 0.68). Returns are modest unlevered (~2.9%/yr at 4% vol); at an 8% vol target that's roughly **6%/yr** with drawdowns of ~20%. **Caveat:** we chose this design after seeing the full-sample results in §5, so the half-sample split shows the result is *stable*, not that it's truly *out-of-sample*. Paper-trading from Oct 2026 and adding more currencies are the real tests.
* **Yen (2):** improves on "always short yen" (Sharpe **0.49 vs 0.35**, drawdown **−24% vs −35%**), mostly by skipping post-intervention months. But the pause rule relies on ~5 modern interventions. Present it as **risk management for an existing carry view**, not proven alpha.
* **Rupee (3):** the filter roughly doubles the Sharpe (**0.30 vs 0.16**) and halves the drawdown. But even filtered, the trade has barely paid since 2013 (Sharpe 0.10) and lost over the last 5 years, because the rate gap shrank as US rates rose. **We would not propose it as a live trade.** Its value is as a **stress gauge** for the India story, and it's the cautionary tale behind the core trade's "avoid net-importer carry" rule.

#### What would make us stop / change our mind (kill criteria)
* **Core:** a drawdown beyond **−15%** (1.5× the historical maximum) or a negative rolling 3-year Sharpe → pause and re-examine. Also watch for a global commodity crash, because the long book leans on commodity exporters (BRL, NOK, ZAR, IDR).
* **Yen:** the US–Japan gap falling below 2pp (Fed cuts and/or faster BoJ hikes) switches the trade off automatically. Another *coordinated* US–Japan intervention restarts the 3-month pause.
* **Rupee:** stays on watch. It would only graduate to a trade if the rate gap widens again (> ~3pp) *and* reserves rise from organic inflows rather than FCNR swaps.
"""

# costs are now included in the final section; label the older no-cost numbers
TEXT["s6_4"] = TEXT["s6_4"].replace("(Sharpe 0.52 vs 0.38 always-short)", "(Sharpe 0.49 vs 0.35 always-short, net of costs)").replace(
    "(Sharpe 0.38 vs 0.20)", "(Sharpe 0.30 vs 0.16 net of costs; weak since 2013, so monitor rather than trade)")
TEXT["s6_3"] = TEXT["s6_3"] + "\n*These tables are **before costs**. The ⭐ Final Proposal section at the top shows the same rules **net of costs**.*\n"
TEXT["tldr"] = TEXT["tldr"].replace("roughly doubles the Sharpe (0.20 → 0.38) and halves the drawdown.**",
    "roughly doubles the Sharpe (0.16 → 0.30 net of costs) and halves the drawdown**, but even filtered it has barely paid since 2013, so we treat it as a watch signal, not a trade.")
TEXT["toc"] = TEXT["toc"].replace("### Contents\n", "### Contents\n0. **⭐ Final proposal** (above) — the three trades, backtests net of costs, current signals\n")
