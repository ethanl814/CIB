# Example deck (template to model the real pitch on)

`example_deck.pptx` is a **15-slide example presentation** built from the forex-drift research. It's a model for the team's final deck: structure, flow, slide styles and talking points. It is not a finished pitch.

- **Open it:** download `example_deck.pptx` and open it in PowerPoint or Keynote. For Google Slides, go to File → Import slides.
- **Speaker notes:** every slide has talking points in its notes.
- **Charts:** the bar charts on slides 8, 9 and 13 are native, so they're editable in PowerPoint (right-click → Edit Data). The other charts are PNGs from `../figures/`.
- **Numbers:** these are copied from `../research.ipynb` (data through 25 Sep 2026). If the notebook is re-run with new data, update the numbers here too.

## Storyline
| # | Slide | Built from |
|---|---|---|
| 1 | Title | — |
| 2 | The question (links back to GM #2 slides 10–11) | — |
| 3 | Hook: rates said one thing, currencies did another | `02_uip_vs_actual_jpy_inr.png` |
| 4 | Japan: the trade balance sets the direction of intervention | `03b_…png` |
| 5 | Japan: intervention buys weeks, not trends | `03e_…png` |
| 6 | India: stairs up, elevator down | `04b_…png` |
| 7 | India: FCNR 2013 vs 2026 | `04e_…png` |
| 8 | The twist: net-importer carry is the worst carry | native chart (§5.4) |
| 9 | Trade balance as its own signal | native chart (§5.6) |
| 10 | The proposal: three trades | ⭐ Final proposal |
| 11 | Backtest chart | `00_final_proposal_backtests.png` |
| 12 | Results table | ⭐ Final proposal |
| 13 | Current positions | native chart (§7) |
| 14 | Risks and kill criteria | §8.4 |
| 15 | Takeaways and Q&A | — |

## Rebuild after edits to the script
```bash
uv pip install --python .venv/bin/python python-pptx   # one-time, from forex-drift-idea/
.venv/bin/python presentation/build_deck.py
```
