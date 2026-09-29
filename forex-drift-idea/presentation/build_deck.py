"""Build the EXAMPLE pitch deck (example_deck.pptx) from the research figures.

This is a model for the team's real deck. It reads PNGs from ../figures and
hard-codes headline numbers taken from research.ipynb (data through 25 Sep 2026).
It never modifies the research itself.

    .venv/bin/python presentation/build_deck.py
"""
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
OUT = HERE / "example_deck.pptx"

# ---- palette: navy dominates; blue = Japan/yen, orange = India/rupee, red = negative
NAVY = RGBColor(0x14, 0x21, 0x3D)
NAVY_2 = RGBColor(0x22, 0x33, 0x58)
INK = RGBColor(0x1F, 0x29, 0x37)
BODY = RGBColor(0x37, 0x41, 0x51)
MUTED = RGBColor(0x6B, 0x72, 0x80)
CARD = RGBColor(0xF1, 0xF3, 0xF6)
LINE = RGBColor(0xE5, 0xE7, 0xEB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xC9, 0xD4, 0xE8)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
RED = RGBColor(0xE3, 0x49, 0x48)
GREEN = RGBColor(0x1B, 0x8F, 0x5F)
GRAY = RGBColor(0x9C, 0xA3, 0xAF)

HEAD, BODYF = "Cambria", "Calibri"
W, H = 13.333, 7.5
FOOT = "EXAMPLE DECK · numbers from forex-drift-idea/research.ipynb (data through 25 Sep 2026)"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


# ============================================================ helpers
def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def text(slide, x, y, w, h, paras, size=16, color=BODY, font=BODYF, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space_after=6, italic=False):
    """paras: str, or list of str / dicts {t, size, color, bold, font, italic}."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        p = {"t": p} if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = Pt(p.get("space_after", space_after))
        r = para.add_run()
        r.text = p["t"]
        f = r.font
        f.size = Pt(p.get("size", size))
        f.bold = p.get("bold", bold)
        f.italic = p.get("italic", italic)
        f.name = p.get("font", font)
        f.color.rgb = p.get("color", color)
    return tb


def box(slide, x, y, w, h, fill=CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06, line=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


def badge(slide, x, y, label, fill=NAVY, color=WHITE, d=0.62, size=16):
    """Numbered circle: the deck's repeating visual motif."""
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(size), True, BODYF, color
    return c


def header(slide, kicker, title, dark=False, kicker_color=BLUE):
    text(slide, 0.6, 0.42, 12, 0.3, kicker.upper(), size=12, bold=True,
         color=ICE if dark else kicker_color)
    text(slide, 0.6, 0.72, 12.1, 0.9, title, size=32, bold=True, font=HEAD,
         color=WHITE if dark else INK)


def footer(slide, n, source=None, dark=False):
    col = ICE if dark else MUTED
    if source:
        text(slide, 0.6, 6.78, 9.5, 0.25, "Source: " + source, size=9, color=col)
    text(slide, 0.6, 7.05, 10, 0.25, FOOT, size=9, color=col, italic=True)
    text(slide, 12.1, 7.05, 0.63, 0.25, str(n), size=10, color=col, align=PP_ALIGN.RIGHT)


def picture(slide, name, x, y, w=None, h=None):
    from PIL import Image
    iw, ih = Image.open(FIG / name).size
    ar = iw / ih
    if w is not None and h is not None:          # fit inside box, keep aspect, centre
        if w / h > ar:
            nw = h * ar
            x, w = x + (w - nw) / 2, nw
        else:
            nh = w / ar
            y, h = y + (h - nh) / 2, nh
    elif w is not None:
        h = w / ar
    else:
        w = h * ar
    slide.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), Inches(w), Inches(h))
    return x, y, w, h


def stat(slide, x, y, w, big, label, color=NAVY, big_size=40, card=True, h=1.45):
    if card:
        box(slide, x, y, w, h)
    pad = 0.25 if card else 0
    text(slide, x + pad, y + 0.14, w - 2 * pad, 0.7, big, size=big_size, bold=True, font=HEAD, color=color)
    text(slide, x + pad, y + 0.82, w - 2 * pad, h - 0.9, label, size=13, color=BODY)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def style_chart(ch, legend=True, value_fmt='0.0', gridlines=True):
    ch.font.name = BODYF
    ch.font.size = Pt(12)
    ch.font.color.rgb = BODY
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(12)
    va = ch.value_axis
    va.has_major_gridlines = gridlines
    if gridlines:
        va.major_gridlines.format.line.color.rgb = LINE
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(11)
    va.tick_labels.font.color.rgb = MUTED
    va.tick_labels.number_format = value_fmt
    va.tick_labels.number_format_is_linked = False
    ca = ch.category_axis
    ca.format.line.color.rgb = LINE
    ca.tick_labels.font.size = Pt(12)
    ca.tick_labels.font.color.rgb = BODY
    ca.has_major_gridlines = False
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW


def color_point(series, i, rgb):
    pt = series.points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = rgb
    dpt = pt._element if pt._element.tag == qn("c:dPt") else None
    if dpt is None:
        dpt = [d for d in series._element.findall(qn("c:dPt")) if d.find(qn("c:idx")).get("val") == str(i)][0]
    if dpt.find(qn("c:invertIfNegative")) is None:
        inv = etree.SubElement(dpt, qn("c:invertIfNegative")); inv.set("val", "0")
        dpt.remove(inv); dpt.find(qn("c:idx")).addnext(inv)


def labels(plot, fmt='+0.0;-0.0', size=12, pos=XL_LABEL_POSITION.OUTSIDE_END):
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.font.size = Pt(size)
    dl.font.bold = True
    dl.font.color.rgb = INK
    dl.position = pos


# ============================================================ 1. title
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.8, 1.2, 8, 0.35, "CIB QUANT RESEARCH  ·  EXAMPLE DECK", size=13, bold=True, color=ICE)
text(s, 0.8, 1.75, 8.2, 1.4, "Forex Drift", size=60, bold=True, font=HEAD, color=WHITE)
text(s, 0.8, 3.05, 7.6, 1.2, "Carry, intervention and the trade balance: what Japan and India teach us about trading currencies",
     size=20, color=ICE)
text(s, 0.8, 5.6, 7.5, 0.6, [
    {"t": "Capital Investments at Berkeley  ·  September 2026", "size": 14, "color": WHITE, "bold": True},
    {"t": "Draft template for the team's pitch: swap in your own words, keep the flow", "size": 12, "color": ICE, "italic": True},
])
badge(s, 9.4, 1.9, "JPY", fill=BLUE, d=2.2, size=34)
badge(s, 10.55, 3.55, "INR", fill=ORANGE, d=2.0, size=30)
badge(s, 9.2, 4.55, "USD", fill=NAVY_2, color=ICE, d=1.3, size=20)
notes(s, "Open with the question from GM #2: the yen and rupee both hit record lows in 2026 despite central banks fighting back. "
         "This deck is an EXAMPLE of how to present the forex-drift research; replace text as needed.")

# ============================================================ 2. the question
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "The question", "Rates should tell us where currencies drift. Do they?")
box(s, 0.6, 1.95, 5.6, 4.55, fill=NAVY)
text(s, 1.0, 2.35, 4.9, 3.8, [
    {"t": "The theory (uncovered interest parity)", "size": 14, "bold": True, "color": ICE, "space_after": 12},
    {"t": "A currency with higher interest rates should lose value by about the rate gap, so no one earns a free lunch.",
     "size": 20, "font": HEAD, "color": WHITE, "space_after": 18},
    {"t": "Governments often fight that drift. Our idea: find where the fight creates a tradable pattern.",
     "size": 16, "color": ICE},
])
text(s, 1.0, 5.55, 4.9, 0.7, [{"t": "Builds on GM #2 (22 Sep 2026)", "size": 12, "bold": True, "color": WHITE, "space_after": 2},
                              {"t": "Japan case study (slide 10) · India FCNR case study (slide 11)", "size": 12, "color": ICE}])
rows = [("1", BLUE, "Japan", "Yen at a 40-year low despite BoJ hikes and a rare joint US-Japan intervention (Jul 2026)."),
        ("2", ORANGE, "India", "Rupee at record lows despite RBI dollar sales and a $52bn FCNR(B) deposit scheme."),
        ("3", NAVY, "17 currencies", "Test whether the pattern generalises, then turn it into a strategy with rules.")]
for i, (n, col, head, body) in enumerate(rows):
    y = 2.0 + i * 1.55
    badge(s, 6.7, y, n, fill=col)
    text(s, 7.55, y - 0.02, 5.2, 1.4, [{"t": head, "size": 20, "bold": True, "font": HEAD, "color": INK, "space_after": 4},
                                       {"t": body, "size": 15, "color": BODY}])
footer(s, 2)
notes(s, "Frame the pitch: theory says rates predict FX drift; policymakers push back; we look for a repeatable trade. "
         "Japan and India are the case studies from GM #2; the 17-currency panel is the real test.")

# ============================================================ 3. hook
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "The hook", "Rates said one thing. Currencies did another.")
picture(s, "02_uip_vs_actual_jpy_inr.png", 0.6, 1.72, w=12.1, h=3.45)
stats = [("+96%", "Yen weaker than its rate-implied path since 2012", BLUE),
         ("−5%", "Rupee vs its rate-implied path: roughly on track", ORANGE),
         ("β = 0.25", "How much FX follows rate gaps across 17 currencies (theory says 1.0)", NAVY)]
for i, (big, lab, col) in enumerate(stats):
    stat(s, 0.6 + i * 4.1, 5.35, 3.85, big, lab, color=col, big_size=30, h=1.3)
footer(s, 3, "FRED (Fed H.10 spot), OECD short rates; research.ipynb §2, §5.2")
notes(s, "Dashed line = where the currency 'should' be if it drifted by the rate gap. The yen went the opposite way, which is the "
         "profit of the yen carry trade. The rupee fell about as much as rates implied. Pooled across 17 currencies the "
         "slope is 0.25, not 1: rate gaps are a poor guide to FX drift.")

# ============================================================ 4. direction
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Japan", "The trade balance decides which way Tokyo fights")
picture(s, "03b_japan_trade_vs_intervention_direction.png", 0.6, 1.75, w=6.8, h=5.0)
cards = [("Net exporter  ·  1993–2011", RED, "MoF SOLD yen in every intervention to protect exporters (¥35tn in 2003–04 alone)."),
         ("Net importer  ·  2022–26", BLUE, "MoF BOUGHT yen every time: ¥9tn (2022), ¥15tn (2024), ~¥27tn (2026, incl. the joint US operation)."),
         ("The nuance", NAVY, "The current account stayed positive throughout. It's goods trade, where a weak yen raises energy and food bills, that lines up.")]
for i, (head, col, body) in enumerate(cards):
    y = 1.8 + i * 1.62
    box(s, 7.75, y, 5.0, 1.45)
    badge(s, 7.95, y + 0.2, str(i + 1), fill=col, d=0.5, size=14)
    text(s, 8.65, y + 0.17, 3.9, 1.2, [{"t": head, "size": 15, "bold": True, "color": INK, "space_after": 3},
                                       {"t": body, "size": 12.5, "color": BODY}])
footer(s, 4, "Japan Ministry of Finance intervention records 1991–2026; OECD trade; World Bank; research.ipynb §3.2")
notes(s, "This is the strongest support for the original intuition: the trade position tells you WHICH direction policymakers "
         "lean. Caveat: one country, and the yen's level (weak vs strong) also matters.")

# ============================================================ 5. does it work
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Japan", "Intervention buys weeks, not trends")
picture(s, "03e_2025_2026_closeup.png", 0.6, 1.8, w=8.2)
text(s, 0.6, 5.35, 8.1, 1.2, [
    {"t": "What to say", "size": 13, "bold": True, "color": BLUE, "space_after": 3},
    {"t": "Each operation knocks USDJPY down 2–3% within days. But the April 2026 round (¥11.7tn at ~160) was fully "
          "reversed, and the yen went on to ~164 before the July joint operation.", "size": 14, "color": BODY}])
for i, (big, lab, col) in enumerate([("68%", "of 28 intervention episodes still 'working' 60 trading days later", NAVY),
                                     ("4 of 6", "BoJ rate hikes since 2024 WEAKENED the yen on the day", BLUE),
                                     ("~164", "Where the 2026 line in the sand ended up (145 in 2022, ~160 in 2024)", RED)]):
    stat(s, 9.2, 1.8 + i * 1.62, 3.55, big, lab, color=col, big_size=32, h=1.45)
footer(s, 5, "Japan MoF; BoJ decisions; FRED DEXJPUS; research.ipynb §3.3–3.4")
notes(s, "Interventions work short-term but don't fix the trend while the US-Japan rate gap stays wide. BoJ hikes are "
         "telegraphed and small relative to the gap, so the yen often weakens on the day ('sell the fact').")

# ============================================================ 6. India
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "India", "Rupee carry: up the stairs, down the elevator", kicker_color=ORANGE)
picture(s, "04b_inr_actual_vs_uip_by_year.png", 0.6, 1.72, w=12.1, h=3.5)
for i, (big, lab, col) in enumerate([("2.6%/yr", "Average rupee fall 2001–25, vs 4.5%/yr implied by rates", ORANGE),
                                     ("17 of 25", "Years the rupee fell LESS than rates implied: the 'stairs'", NAVY),
                                     ("5 crashes", "2008, 2011, 2013, 2018, 2022: +9–21% jumps (the 'elevator')", RED)]):
    stat(s, 0.6 + i * 4.1, 5.35, 3.85, big, lab, color=col, big_size=30, h=1.3)
footer(s, 6, "FRED DEXINUS, IRSTCI01INM156N; research.ipynb §4.1")
notes(s, "RBI smoothing makes rupee carry look safe (6.7% vol, 2nd lowest of 17), then the jumps arrive. Since 2013 long-rupee "
         "carry has earned ~0.6%/yr.")

# ============================================================ 7. FCNR
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "India", "Same rescue tool, two different outcomes", kicker_color=ORANGE)
picture(s, "04e_fcnr_2013_vs_2026.png", 0.6, 1.72, w=12.1, h=3.4)
for i, (yr, col, lines) in enumerate([
        ("2013", ORANGE, ["$34bn raised", "Rupee +8% stronger during the window, +12% a year later",
                          "Tailwind: the Fed surprised by NOT tapering (18 Sep 2013)"]),
        ("2026", NAVY, ["$52bn raised, window closed early (31 Aug)", "Rupee flat: 95.0 → 95.8",
                        "Headwind: the Fed HIKED (16 Sep 2026), oil ~$100"])]):
    x = 0.6 + i * 6.15
    box(s, x, 5.25, 5.95, 1.45)
    badge(s, x + 0.25, 5.47, yr, fill=col, d=0.95, size=16)
    text(s, x + 1.4, 5.37, 4.4, 1.25, [{"t": l, "size": 12.5, "color": BODY, "space_after": 3} for l in lines])
footer(s, 7, "FRED DEXINUS; RBI circulars; Business Standard; research.ipynb §4.4")
notes(s, "Domestic defence buys time; global rates decide the trend. That's the same lesson as Japan.")

# ============================================================ 8. the twist (native chart)
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "The twist", "Net-importer carry is the WORST carry", kicker_color=RED)
cd = CategoryChartData()
cd.categories = ["High-carry currencies", "Low-carry currencies"]
cd.add_series("Net exporters", (3.04, -1.38))
cd.add_series("Net importers", (0.57, -1.80))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.8), Inches(7.4), Inches(4.8), cd)
ch = gf.chart
style_chart(ch, value_fmt='0"%"')
ch.has_title = True
ch.chart_title.text_frame.text = "Carry-trade return, % per year (dollar-neutral, 2000–2026)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
plot = ch.plots[0]
plot.gap_width, plot.overlap = 80, -10
for ser, col in zip(plot.series, [BLUE, RED]):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = col
    ser.invert_if_negative = False
labels(plot, fmt='+0.0"%";-0.0"%"')
text(s, 8.5, 1.9, 4.25, 4.7, [
    {"t": "Our starting thesis", "size": 13, "bold": True, "color": MUTED, "space_after": 3},
    {"t": "High-rate net importers get defended by their central banks, so buy them.", "size": 16, "color": BODY, "space_after": 14},
    {"t": "What the data says", "size": 13, "bold": True, "color": RED, "space_after": 3},
    {"t": "They earn 0.6%/yr vs 3.0% for high-rate exporters, and crash harder (skew −1.4 vs −0.4). "
          "Holds in 13 of 14 robustness checks.", "size": 16, "color": INK, "space_after": 14},
    {"t": "Defence delays the fall, then concentrates it into a crash.", "size": 16, "italic": True, "font": HEAD, "color": NAVY},
])
footer(s, 8, "17-currency panel, monthly 2000–2026; research.ipynb §5.4")
notes(s, "Present this honestly: the original idea was reversed by the data. That's a strength of the pitch; it shows we tested it. "
         "Deficit currencies track the theory more closely (β 0.41 vs −0.20), so their high rates are real compensation for risk.")

# ============================================================ 9. signal horse race (native chart)
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "The new signal", "The trade balance is a signal of its own, and it hedges carry")
sig = [("Current account", -0.27), ("Contrarian positioning", -0.16), ("Value (REER)", -0.11), ("UIP 'tension'", -0.04),
       ("Momentum 12m", 0.11), ("Trade balance, 12m change", 0.33), ("Trade balance", 0.35),
       ("Trade balance vs own 5y avg", 0.52), ("Carry (rate gap)", 0.61)]
cd = CategoryChartData()
cd.categories = [a for a, _ in sig]
cd.add_series("Sharpe ratio", [b for _, b in sig])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.8), Inches(7.6), Inches(4.85), cd)
ch = gf.chart
style_chart(ch, legend=False, value_fmt='0.0')
ch.has_title = True
ch.chart_title.text_frame.text = "Sharpe ratio of each long/short signal, 2000–2026 (no costs)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
plot = ch.plots[0]
plot.gap_width = 45
ser = plot.series[0]
ser.invert_if_negative = False
for i, (name, v) in enumerate(sig):
    color_point(ser, i, NAVY if "Carry" in name else (ORANGE if "Trade" in name else GRAY))
labels(plot, fmt='+0.00;-0.00', size=11)
stat(s, 8.6, 1.8, 4.15, "−0.32", "Correlation between the carry and trade-balance portfolios: they diversify", color=NAVY, big_size=34)
stat(s, 8.6, 3.4, 4.15, "8 of 10", "Of carry's worst months (2008, 2020...), the trade-balance portfolio made money", color=ORANGE, big_size=34)
stat(s, 8.6, 5.0, 4.15, "Both halves", "Works in 2000–12 AND 2013–26; momentum, value and positioning don't", color=GREEN, big_size=28)
footer(s, 9, "research.ipynb §5.6–5.7")
notes(s, "Goods trade matters, not the total current account (which is negative here). The 'vs own 5-year average' version "
         "rules out a static country bet: an IMPROVING trade balance predicts outperformance.")

# ============================================================ 10. proposal
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
header(s, "The proposal", "Three trades, one idea: carry where trade supports it", dark=True)
trades = [("01", "CORE", BLUE, "Carry + trade-balance basket",
           "Each month rank 17 currencies. Half: long high-rate / short low-rate. Half: long net exporters / short net importers.",
           "Primary recommendation"),
          ("02", "SATELLITE", BLUE, "Short yen, paused after intervention",
           "Short JPY while the US–Japan rate gap is above 2pp. Stand aside for 3 months after the MoF buys yen.",
           "Secondary · risk-managed"),
          ("03", "WATCH", ORANGE, "Long rupee only while the RBI accumulates",
           "Long INR only if RBI reserves rose over the last 3 months. A stress gauge more than a trade.",
           "Monitor, not a trade")]
for i, (n, tag, col, head, body, grade) in enumerate(trades):
    x = 0.6 + i * 4.1
    box(s, x, 1.95, 3.85, 4.6, fill=NAVY_2)
    badge(s, x + 0.3, 2.25, n, fill=col, d=0.75, size=18)
    text(s, x + 1.25, 2.4, 2.4, 0.4, tag, size=13, bold=True, color=ICE)
    text(s, x + 0.3, 3.25, 3.3, 0.95, head, size=19, bold=True, font=HEAD, color=WHITE)
    text(s, x + 0.3, 4.25, 3.3, 1.5, body, size=13.5, color=ICE)
    text(s, x + 0.3, 5.45, 3.3, 0.4, ["Sharpe 0.73 (carry alone 0.44)", "Sharpe 0.49 (always short 0.35)",
                                       "Sharpe 0.30 (always long 0.16)"][i], size=13, color=ICE)
    text(s, x + 0.3, 5.95, 3.3, 0.4, grade, size=13, bold=True, color=WHITE)
footer(s, 10, "research.ipynb ⭐ Final proposal", dark=True)
notes(s, "The reframed thesis: harvest the interest-rate gap only where the trade balance supports the currency; fund it with "
         "currencies whose trade balance is deteriorating. A central bank spending reserves is a warning, not a floor.")

# ============================================================ 11. backtest chart
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Backtest", "27 years, net of costs, no hindsight in the signals")
picture(s, "00_final_proposal_backtests.png", 0.6, 1.7, w=7.9, h=5.0)
for i, (big, lab, col) in enumerate([("0.73", "Core Sharpe ratio vs 0.44 for plain carry", NAVY),
                                     ("−10%", "Core worst drawdown vs −18% for plain carry", GREEN),
                                     ("0.79 → 0.68", "Sharpe in 2000–12 vs 2013–26: stable across both halves", BLUE)]):
    stat(s, 8.9, 1.75 + i * 1.62, 3.85, big, lab, color=col, big_size=32 if i < 2 else 28, h=1.45)
footer(s, 11, "Monthly Jan 2000–Sep 2026; costs 4bp G10 / 12bp EM + forward roll; research.ipynb ⭐ Final proposal")
notes(s, "How it was tested: monthly, only data published at the time (trade lagged 2 months, reserves 1), return = interest + FX "
         "move, realistic costs. Sharpe stays 0.61–0.79 across 12 recipe variations.")

# ============================================================ 12. results table
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Results", "The rules win on risk, not on raw return")
rows = [("Trade", "Return %/yr", "Volatility %", "Sharpe", "Worst drawdown", "Sharpe 2000–12", "Sharpe 2013–26"),
        ("1. Core: carry + trade basket", "2.9", "4.0", "0.73", "−10%", "0.79", "0.68"),
        ("    benchmark: carry only", "3.4", "7.7", "0.44", "−18%", "0.53", "0.34"),
        ("1b. Core, G10-only (retail)", "1.7", "3.6", "0.47", "−9%", "0.63", "0.31"),
        ("2. Short yen, intervention pause", "2.8", "5.8", "0.49", "−24%", "0.37", "0.64"),
        ("    benchmark: always short yen", "3.4", "9.5", "0.35", "−35%", "0.05", "0.66"),
        ("3. Long rupee while reserves rise", "1.3", "4.4", "0.30", "−11%", "0.46", "0.10"),
        ("    benchmark: always long rupee", "1.1", "6.6", "0.16", "−21%", "0.26", "0.06")]
tbl = s.shapes.add_table(len(rows), len(rows[0]), Inches(0.6), Inches(1.8), Inches(12.1), Inches(3.7)).table
tbl.columns[0].width = Inches(4.0)
for j in range(1, len(rows[0])):
    tbl.columns[j].width = Inches(8.1 / 6)
for i, row in enumerate(rows):
    bench = row[0].startswith("    ")
    for j, v in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY if i == 0 else (WHITE if bench else CARD)
        c.margin_left = c.margin_right = Inches(0.1)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
        r = p.add_run()
        r.text = v.strip() if j == 0 and bench else v
        r.font.name = BODYF
        r.font.size = Pt(13)
        r.font.bold = i == 0 or (not bench and j in (0, 3))
        r.font.italic = bench
        r.font.color.rgb = WHITE if i == 0 else (MUTED if bench else INK)
box(s, 0.6, 5.75, 12.1, 0.85, fill=CARD)
text(s, 0.85, 5.85, 11.6, 0.7, [
    {"t": "Say this out loud: unlevered, plain carry earns more (3.4% vs 2.9%/yr). At the SAME risk the core would earn ~5.6%/yr vs 3.4%, "
          "with a similar worst drawdown (−19% vs −18%).", "size": 14, "color": INK}], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 12, "Net of costs, monthly Jan 2000–Sep 2026; research.ipynb ⭐ Final proposal")
notes(s, "Be precise here; this is where judges will probe. The two-halves split shows stability, not a true out-of-sample test, "
         "because the strategy was chosen after seeing the full sample.")

# ============================================================ 13. positions now (native chart)
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Where we stand", "What the model says today (end of September 2026)")
pos = [("GBP", -0.12), ("NZD", -0.12), ("JPY", -0.10), ("CAD", -0.10), ("SEK", -0.10), ("INR", -0.04), ("TRY", -0.04),
       ("MXN", 0.08), ("IDR", 0.08), ("NOK", 0.10), ("BRL", 0.18), ("ZAR", 0.18)]
cd = CategoryChartData()
cd.categories = [a for a, _ in pos]
cd.add_series("Core weight", [100 * b for _, b in pos])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.8), Inches(6.9), Inches(4.85), cd)
ch = gf.chart
style_chart(ch, legend=False, value_fmt='0"%"')
ch.has_title = True
ch.chart_title.text_frame.text = "Core basket weights (% of each leg; + long, − short)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
plot = ch.plots[0]
plot.gap_width = 45
ser = plot.series[0]
ser.invert_if_negative = False
for i, (_, v) in enumerate(pos):
    color_point(ser, i, BLUE if v > 0 else RED)
labels(plot, fmt='+0;-0', size=11)
for i, (tag, col, head, body) in enumerate([
        ("02", BLUE, "Short yen: PAUSED", "Rate gap 2.8pp (above 2 ✓), but the MoF bought yen in July. Re-enter in November if the gap holds."),
        ("03", ORANGE, "Rupee watch: weak ON", "Reserves +2.2% over 3 months, but mostly borrowed FCNR dollars. Fundamentals still weak."),
        ("!", NAVY, "Long book is commodity-heavy", "BRL, ZAR, NOK, IDR: a commodity crash is the scenario to stress-test.")]):
    y = 1.8 + i * 1.62
    box(s, 7.9, y, 4.85, 1.45)
    badge(s, 8.1, y + 0.2, tag, fill=col, d=0.55, size=13)
    text(s, 8.85, y + 0.16, 3.7, 1.2, [{"t": head, "size": 15, "bold": True, "color": INK, "space_after": 3},
                                       {"t": body, "size": 12.5, "color": BODY}])
footer(s, 13, "research.ipynb §7 and ⭐ Final proposal (signals as of Sep 2026)")
notes(s, "Update this slide right before presenting: re-run the notebook to refresh positions.")

# ============================================================ 14. risks
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
header(s, "Risks", "What would make us change our mind")
risks = [("Core drawdown beyond −15%", "1.5× the historical worst, or a negative 3-year Sharpe: pause and re-examine.", NAVY),
         ("Global commodity crash", "The long book leans on commodity exporters (BRL, ZAR, NOK, IDR).", ORANGE),
         ("US–Japan gap below 2pp", "Fed cuts or faster BoJ hikes switch the yen trade off automatically.", BLUE),
         ("Not truly out-of-sample", "Chosen after seeing the data. Real test: paper-trade from Oct 2026 and add ~13 more currencies.", RED)]
for i, (head, body, col) in enumerate(risks):
    x = 0.6 + (i % 2) * 6.15
    y = 2.0 + (i // 2) * 2.2
    box(s, x, y, 5.95, 1.9)
    badge(s, x + 0.3, y + 0.3, str(i + 1), fill=col, d=0.65, size=17)
    text(s, x + 1.2, y + 0.32, 4.5, 1.65, [{"t": head, "size": 18, "bold": True, "font": HEAD, "color": INK, "space_after": 6},
                                           {"t": body, "size": 14, "color": BODY}])
footer(s, 14, "research.ipynb §8.4 and ⭐ kill criteria")
notes(s, "Other caveats worth one sentence: carry is measured with interest rates rather than forward prices; the intervention "
         "evidence rests on a few dozen episodes; July 2026 intervention sizes are still estimates.")

# ============================================================ 15. close
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.8, 0.9, 11, 0.4, "TAKEAWAYS", size=13, bold=True, color=ICE)
for i, (n, col, t) in enumerate([
        ("1", BLUE, "Rates don't predict where currencies drift, and governments' fights rarely change the trend."),
        ("2", ORANGE, "Defended net-importer currencies are the worst place to earn carry."),
        ("3", GREEN, "Carry + trade balance: Sharpe 0.73 vs 0.44, half the drawdown, stable across 27 years.")]):
    y = 1.6 + i * 1.3
    badge(s, 0.8, y, n, fill=col, d=0.75, size=18)
    text(s, 1.85, y, 10.9, 0.75, t, size=20, font=HEAD, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.8, 5.6, 11.5, 0.9, [
    {"t": "Questions?", "size": 30, "bold": True, "font": HEAD, "color": WHITE, "space_after": 4},
    {"t": "Full research, data and code: github.com/ethanl814/CIB  →  forex-drift-idea/", "size": 14, "color": ICE}])
text(s, 0.8, 7.05, 11, 0.25, FOOT, size=9, color=ICE, italic=True)
notes(s, "Close on the reframed thesis and invite questions. Point people to the repo for the notebook.")

prs.save(OUT)
print(f"wrote {OUT} ({len(prs.slides)} slides)")
