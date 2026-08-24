# ESG Momentum Engine 2.0

**PolyFinTech100 Hackathon 2026 · CGS International · Category: ESG**

*From static scores to dynamic intelligence — find the Hidden Winners the market hasn't priced yet.*

---

## The one-sentence pitch

Traditional ESG asks *"what is your score today?"* — a backward-looking number. This engine asks *"where are you going?"* by blending alternative data (hiring, AI adoption, news sentiment, controversy) into a single forward-looking **Momentum 2.0 score**, then plots every company on a 2×2 matrix so a fund manager can spot **Hidden Winners** — low ESG today, strong momentum — on Monday morning.

## What a judge sees in 90 seconds

1. **The Matrix** — 24 ASEAN companies on one 2×2 chart. Four quadrants, live-reweightable. The top-left (Hidden Winners) is the money.
2. **Company Drilldown** — click any name to see the exact signal breakdown that produced its score. Nothing is a black box.
3. **My Portfolio** — a 5-question risk profile turns into a concrete, weighted basket drawn only from the two *improving* quadrants.

---

## How the score works

Each company gets a **Momentum 2.0 score (0-100)** from **four labelled axes** — E, S, G and
Innovation. Innovation is scored and shown separately, never folded into Social: three of the
seven signals in v1 were "is this company adopting AI?", which is an innovation signal wearing
an S costume.

```
Momentum_2.0 = W_E(sector,stage)*E_momentum
             + W_S(sector,stage)*S_momentum
             + W_G(sector,stage)*G_momentum
             + W_I(sector,stage)*Innovation_momentum
             + sentiment_trend
             - say_do_gap            (greenwashing penalty)
```

**The weights come from a lookup table, not one global formula.** `weights.py` holds 12 cells
keyed on (sector group, stage), each with a one-sentence rationale. A carbon-intensive mature
company puts 50% of its weight on E; a bank puts 45% on G. You can disagree with a number
instead of with a model.

**Normalisation is sector-relative by default.** An oil company will always score below a solar
company, and that comparison tells you nothing. Every signal is z-scored within its sector, then
shrunk toward the universe z-score by `n/(n+5)` so a sector holding two names never gets a
fabricated percentile. `python scoring.py --mode universe --compare` flips to universe-relative
and prints how far each company moves — that re-ranking is the argument, made visually.

**The Say-Do Gap** compares stated ESG commitments against outcomes a company cannot edit:
environmental fines, pillar deterioration, and satellite-measured emissions from Climate TRACE.

### Data provenance

Every column has a real provider behind it (`pipeline/providers/`): Yahoo/Sustainalytics for
per-pillar ESG scores and history, GDELT for the E/S/G controversy split, Climate TRACE for
independent emissions, Wikirate for disclosed metrics, yfinance for financials. Anything a
provider does not answer falls back to a calibrated value, and `data/provenance.csv` records
which is which, per company per column.

```
python pipeline/build_master_data.py          # frozen, no network, reproducible
python pipeline/build_master_data.py --live   # providers first, fall back per cell
```

## Project layout

```
esg_momentum_engine/
├── app.py                     ← the Streamlit decision tool (run this)
├── scoring.py                 ← four-axis scoring, sector-relative normalisation, quadrants
├── weights.py                 ← the (sector, stage) → pillar weight lookup table
├── requirements.txt
├── README.md                  ← you are here
├── data/
│   ├── master_data.csv        ← the 24-company dataset the app reads
│   ├── provenance.csv         ← per column: measured or calibrated
│   └── scores.csv             ← per-pillar sub-scores, weights used, rationale
└── pipeline/
    ├── build_master_data.py   ← live-first pipeline → master_data.csv + provenance.csv
    ├── universe.py            ← the 24 companies and their calibrated fallbacks
    ├── providers/             ← Yahoo ESG, GDELT, Climate TRACE, Wikirate, yfinance
    ├── anchors.py             ← shared config for the 5 real-data anchor companies
    ├── task1_financials.py    ← revenue + sector (yfinance, USD-converted)
    ├── task2_hiring.py        ← hiring momentum (deterministic estimate)
    ├── task3_sentiment.py     ← news sentiment + trend (TextBlob + Google News)
    ├── task4_controversy.py   ← controversy flags (keyword families over news)
    └── task5_ai_signals.py    ← NEW: AI job %, patents, earnings-call mentions
```

### Two paths, on purpose

- **Demo path (default):** the app reads the frozen `data/master_data.csv`, so it is **identical on every run** — safe for a recording, no live API can break mid-pitch.
- **Production path:** `pipeline/task1..task5` show *how each column is sourced live*. Run them to prove to a judge the data is real-sourceable; they degrade gracefully (fallback FX rates, neutral sentiment, Low-Confidence flags) and never crash.

`build_master_data.py` is the consolidation of all five tasks over one shared universe — it's the single clean pipeline that emits the dataset.

---

## Run it

```bash
cd esg_momentum_engine
pip install -r requirements.txt
streamlit run app.py
```

To (re)generate the dataset or run a live task:

```bash
cd pipeline
python build_master_data.py          # rebuild the frozen master_data.csv
python task5_ai_signals.py           # demo the AI-signal method
python task1_financials.py --write   # pull live revenue and merge it in
```

---

## Improvements made over the original task 1–4 scripts

- **Universe expanded 5 → 24** ASEAN companies so the matrix populates all four quadrants convincingly (was too sparse to read with 5 dots).
- **Shared config (`anchors.py`)** — the four scripts had duplicated, drifting ticker tables; now one source of truth.
- **Robustness** — every network call has retry + documented fallback, so a blocked feed or rate-limit degrades gracefully instead of crashing.
- **Determinism** — mock signals are seeded/calibrated and fully explainable ("why does Sea hire more than PTTEP?").
- **The missing half built** — added `task5_ai_signals.py` (AI job %, patents, earnings-call mentions), the **Momentum 2.0 composite score + quadrant logic** (`scoring.py`), and the entire **Streamlit app** (matrix, drilldown, questionnaire, personalized basket).
- **Consolidated** into one clean pipeline (`build_master_data.py`) while keeping the individual, well-documented task scripts as the production-path evidence.

---

## How this maps to the judging criteria

1. **Solves a real investor problem** — outputs a concrete Monday-morning basket, not just analysis.
2. **Simple, clear output** — one 2×2 matrix, one score, one ranking.
3. **Meaningful insight** — surfaces Hidden Winners (e.g. **FPT**, **Sea Limited**) the market prices on their past, not their trajectory.
4. **Original thinking** — reframes ESG from a *level* to a *derivative*; triangulates three AI signals so the AI leg is hard to fake.
5. **Practical & buildable** — a working proof-of-concept that runs on sample data today.

## Honesty note

All figures in `master_data.csv` are **illustrative and calibrated** for the demo (real companies, real sectors, plausible magnitudes). They are not real ESG ratings and are not investment advice. The pipeline scripts show exactly how each column would be replaced with live-sourced data in production.
