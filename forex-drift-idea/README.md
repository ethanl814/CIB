# Forex Drift Idea

CIB quant research on carry, currency intervention and the trade balance. Japan and India are the case studies, tested against a 17-currency panel with data through September 2026.

Built off the Japan and India slides in GM #2 (22 Sep 2026).

## What's here
| Path | What it is |
|---|---|
| `research.ipynb` | **The main notebook.** Theories, tests, ~26 charts, backtests, current signals and interpretation. Start with the TL;DR at the top. |
| `figures/` | Every chart as a PNG, numbered by notebook section, ready to drop into slides. |
| `src/fetch_data.py` | Downloads and caches all raw data into `data/raw/`. |
| `src/fxlib.py` | Shared loaders, panel construction, stats and plot style. |
| `src/build_notebook.py` | Builds `research.ipynb` from code. `src/notebook_text.py` holds all the prose. |
| `data/raw/` | Cached raw data: FRED, Japan MoF interventions, CFTC positioning, World Bank, Yahoo. |

## Rerun / refresh
```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python src/fetch_data.py --force      # pull latest data (omit --force to use cache)
.venv/bin/python src/build_notebook.py          # rebuild notebook from source
.venv/bin/jupyter nbconvert --to notebook --execute --inplace research.ipynb
```
You can also just open `research.ipynb` in Jupyter or VS Code with the `.venv` kernel and run all cells.

## Headline findings (details, caveats and the scorecard are in the notebook)
- UIP fails, with a pooled β of 0.25. USDJPY has ended ~96% (log) above its UIP-implied path since 2012.
- The original thesis ("defended net-importer high-yielders pay") is **reversed** in the data. Net-importer carry earns less and crashes harder.
- Trade balance is a **separate signal** that diversifies carry: −0.32 correlation, and it made money in 8 of carry's 10 worst months.
- **Strategy C** (50/50 carry + trade balance) has a net Sharpe of ~0.73 and a max drawdown of −10%. It holds up in both halves of the sample and across 12 recipe variants.
- Japan: the trade balance lines up with the *direction* of intervention. India: RBI reserves are a useful on/off filter for rupee carry.
